from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import calendar
import json
import traceback
import sys

router = APIRouter()

# Input models
class ProductionPoint(BaseModel):
    date: str  # YYYY-MM format
    oil: float
    gas: float
    water: float
    days_on: int

class ArpsParameters(BaseModel):
    initialRate: float = Field(..., description="Initial production rate in units per day")
    initialDecline: float = Field(..., description="Initial decline rate in percentage (e.g., 45 for 45% per month")
    bFactor: float = Field(..., description="Hyperbolic exponent (0 for exponential, 1 for harmonic)")
    minDecline: float = Field(..., description="Minimum decline rate in percentage")
    economicLimit: float = Field(..., description="Economic limit (rate cutoff) in units per day")
    model: str = Field("hyperbolic", description="Model type: exponential, harmonic, hyperbolic, arps, arps-modified")
    enabled: Optional[bool] = Field(True, description="Whether this fluid forecast is enabled")

class ForecastRequest(BaseModel):
    well_id: str
    deal_id: str
    as_of_date: str  # YYYY-MM format
    historical_production: List[ProductionPoint]
    forecast_parameters: Dict[str, ArpsParameters] = Field(..., description="Dictionary with keys 'oil', 'gas', 'water' for each fluid's forecast parameters")
    forecast_horizon_months: int = 600  # Default to 50 years

# Output models
class ForecastRow(BaseModel):
    date: str  # YYYY-MM format
    well_id: str
    deal_id: str
    oil_historical: Optional[float] = None
    gas_historical: Optional[float] = None
    water_historical: Optional[float] = None
    oil_forecast: Optional[float] = None
    gas_forecast: Optional[float] = None
    water_forecast: Optional[float] = None
    oil_volume: Optional[float] = None
    gas_volume: Optional[float] = None
    water_volume: Optional[float] = None

class ForecastTableResponse(BaseModel):
    data: List[ForecastRow]
    well_id: str
    deal_id: str
    as_of_date: str

def get_days_in_month(date_str: str) -> int:
    """Get number of days in a month from YYYY-MM date string"""
    try:
        year, month = map(int, date_str.split('-'))
        return calendar.monthrange(year, month)[1]
    except ValueError as e:
        print(f"Error parsing date: {date_str} - {e}")
        return 30  # Default to 30 days if there's an error

def calculate_arps_rate(params: ArpsParameters, months_from_start: int) -> float:
    """Calculate production rate at a given time using Arps decline model"""
    qi = params.initialRate
    di = params.initialDecline / 100  # Convert percentage to decimal
    b = params.bFactor
    
    # Debug info
    print(f"Calculating Arps rate with: qi={qi}, di={di}, b={b}, months={months_from_start}")

    # Convert annual decline rate to monthly
    di_monthly = 1 - (1 - di) ** (1/12)

    # Ensure decline rate is not negative
    di_monthly = max(0.001, di_monthly)

    # Different formulas based on b value
    if b == 0:
        # Exponential decline (b = 0)
        return qi * (1 - di_monthly) ** months_from_start
    elif b == 1:
        # Harmonic decline (b = 1)
        return qi / (1 + di_monthly * months_from_start)
    else:
        # Hyperbolic decline (0 < b < 1 typically)
        return qi / ((1 + b * di_monthly * months_from_start) ** (1/b))

def generate_arps_forecast(params: ArpsParameters, start_date: str, num_months: int) -> List[Dict[str, Any]]:
    """Generate a full Arps decline curve forecast"""
    print(f"Generating Arps forecast starting from {start_date} for {num_months} months with params: initialRate={params.initialRate}, initialDecline={params.initialDecline}, bFactor={params.bFactor}, minDecline={params.minDecline}, economicLimit={params.economicLimit}, model={params.model}")
    year, month = map(int, start_date.split('-'))
    forecast = []

    # Initialize parameters
    current_rate = max(0.1, params.initialRate) # Ensure positive initial rate
    di = max(0.01, params.initialDecline / 100) # Ensure positive decline rate
    dmin = max(0.01, params.minDecline / 100)  # Ensure positive minimum decline rate
    economic_limit = params.economicLimit
    
    # Set model and b-factor based on model type
    model_type = params.model.lower() if params.model else "hyperbolic"
    
    if model_type == "exponential":
        b_factor = 0
    elif model_type == "harmonic":
        b_factor = 1
    elif model_type == "arps":
        # Classic Arps - use provided b-factor
        b_factor = params.bFactor
    elif model_type == "arps-modified":
        # Modified Arps with terminal decline
        b_factor = params.bFactor
    else:  # Default to hyperbolic
        b_factor = params.bFactor

    below_economic_limit = False
    
    for i in range(num_months):
        # Track if below economic limit but don't break the forecast
        if current_rate < economic_limit:
            below_economic_limit = True

        # Format date
        current_date = datetime(year, month, 1)
        current_date_str = current_date.strftime('%Y-%m')

        # Get days in this month
        days_in_month = get_days_in_month(current_date_str)

        # Calculate monthly volume
        monthly_volume = current_rate * days_in_month

        # Add to forecast
        forecast.append({
            "date": current_date_str,
            "months_from_start": i,
            "rate": current_rate,
            "volume": monthly_volume,
            "below_economic_limit": below_economic_limit
        })

        # Calculate next month's rate based on model type
        if b_factor == 0:
            # Exponential decline
            current_rate = current_rate * (1 - di/12)
        elif b_factor == 1:
            # Harmonic decline
            current_rate = current_rate / (1 + di/12)
        else:
            # Hyperbolic decline
            current_rate = current_rate / ((1 + b_factor * di/12) ** (1/b_factor))

        # Ensure minimum value for visualization
        current_rate = max(0.1, current_rate)

        # Apply minimum decline concept (terminal decline)
        if b_factor > 0:
            # Calculate effective decline rate
            effective_di = di / (1 + b_factor * di * i/12)
            # Switch to exponential if we hit minimum decline
            if effective_di < dmin:
                di = dmin
                b_factor = 0  # Switch to exponential model

        # Move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return forecast

@router.post("/generate-forecast-table", response_model=ForecastTableResponse)
def generate_forecast_table(request: ForecastRequest) -> ForecastTableResponse:
    print(f"Generating forecast for well {request.well_id} in deal {request.deal_id} starting from {request.as_of_date}")
    print(f"Historical data points: {len(request.historical_production)}")
    """
    Generate a forecast table that merges historical and forecast data.
    
    This endpoint takes historical production data for a well and ARPS forecast parameters
    for each fluid type (oil, gas, water), then generates a forecast table that combines
    both historical and forecast data. The forecast starts from the specified as-of date
    and extends for the requested forecast horizon.
    
    The output table includes both historical and forecast values, with columns for:
    - Historical rates (oil_historical, gas_historical, water_historical)
    - Forecast rates (oil_forecast, gas_forecast, water_forecast)
    - Monthly volumes (oil_volume, gas_volume, water_volume)
    
    Each row represents one month of data, and values can overlap (a month can have both
    historical and forecast data). This table serves as the single source of truth for
    generating charts and calculating economic metrics.
    
    Parameters:
    - well_id: Identifier for the well
    - deal_id: Identifier for the economic deal/scenario
    - as_of_date: The month (YYYY-MM) from which to start the forecast
    - historical_production: Array of historical production points
    - forecast_parameters: ARPS parameters for oil, gas and water forecasts
    - forecast_horizon_months: How many months to forecast (default 600 = 50 years)
    
    Returns:
    - A merged table with historical and forecast data for all months
    """
    well_id = request.well_id
    deal_id = request.deal_id
    as_of_date = request.as_of_date
    historical_data = request.historical_production
    forecast_parameters = request.forecast_parameters
    forecast_horizon = request.forecast_horizon_months

    # Sort historical data by date
    historical_data.sort(key=lambda x: x.date)
    
    # Print sample of historical data for debugging
    if historical_data:
        print(f"Sample historical data point: {historical_data[0].date}, oil={historical_data[0].oil}, gas={historical_data[0].gas}, water={historical_data[0].water}, days={historical_data[0].days_on}")

    # Initialize the merged data dictionary keyed by date
    merged_data = {}

    # Process historical data
    for point in historical_data:
        date = point.date
        # Use the daily rates directly from Enverus API
        oil_rate = point.oil if point.oil is not None else None
        gas_rate = point.gas if point.gas is not None else None
        water_rate = point.water if point.water is not None else None
        
        merged_data[date] = ForecastRow(
            date=date,
            well_id=well_id,
            deal_id=deal_id,
            oil_historical=oil_rate,
            gas_historical=gas_rate,
            water_historical=water_rate
        )

    # Generate forecast for each fluid type
    print(f"Generating forecasts for fluid types: {list(forecast_parameters.keys())}")
    for fluid_type, params in forecast_parameters.items():
        # Skip forecasting if this fluid is explicitly disabled
        if params.enabled is False:
            print(f"Skipping forecast for {fluid_type} as it is disabled")
            continue
            
        # Generate forecast
        forecast = generate_arps_forecast(params, as_of_date, forecast_horizon)

                # Add forecast data to merged data in batch for efficiency (no individual logging)
        print(f"Processing {len(forecast)} {fluid_type} forecast points...")
        forecast_count = 0
        
        # First pass - collect all points after the as_of_date
        future_points = [point for point in forecast if point["date"] > as_of_date]
        forecast_count = len(future_points)
        
        # Second pass - create entries for all future dates if needed
        for point in future_points:
            date = point["date"]
            if date not in merged_data:
                merged_data[date] = ForecastRow(
                    date=date,
                    well_id=well_id,
                    deal_id=deal_id
                )
        
        # Third pass - set all forecast values in batch by fluid type
        for point in future_points:
            date = point["date"]
            if fluid_type == "oil":
                merged_data[date].oil_forecast = point["rate"]
                merged_data[date].oil_volume = point["volume"]
            elif fluid_type == "gas":
                merged_data[date].gas_forecast = point["rate"]
                merged_data[date].gas_volume = point["volume"]
            elif fluid_type == "water":
                merged_data[date].water_forecast = point["rate"]
                merged_data[date].water_volume = point["volume"]
                
        # Log summary instead of individual points
        if forecast_count > 0 and future_points:
            first_point = future_points[0]
            last_point = future_points[-1]
            print(f"Added {forecast_count} {fluid_type} forecast points from {first_point['date']} to {last_point['date']}")
            
            # Log sample rates for verification
            print(f"First {fluid_type} forecast rate: {first_point['rate']}, Last {fluid_type} forecast rate: {last_point['rate']}")
        else:
            print(f"No {fluid_type} forecast points were added after as_of_date {as_of_date}")

    # Convert dictionary to sorted list
    merged_list = list(merged_data.values())
    merged_list.sort(key=lambda x: x.date)
    
    # Debug the forecast output
    print(f"Generated forecast with {len(merged_list)} total rows")
    
    # Check if forecast data was generated
    has_forecast = any(
        (row.oil_forecast is not None or 
         row.gas_forecast is not None or 
         row.water_forecast is not None) 
        for row in merged_list
    )
    print(f"Forecast includes forecast values: {has_forecast}")
    
    if merged_list:
        # Print a sample forecast value that should be after as_of_date
        future_data = [row for row in merged_list if row.date > as_of_date]
        if future_data:
            sample = future_data[0]
            print(f"Sample future data point: {sample.date}, oil_forecast={sample.oil_forecast}, gas_forecast={sample.gas_forecast}, water_forecast={sample.water_forecast}")
    
    return ForecastTableResponse(
        data=merged_list,
        well_id=well_id,
        deal_id=deal_id,
        as_of_date=as_of_date
    )