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

class OwnershipParameters(BaseModel):
    workingInterest: float = Field(..., description="Working interest percentage as a decimal (e.g., 0.8 for 80%)")
    revenueInterest: float = Field(..., description="Revenue interest percentage as a decimal (e.g., 0.75 for 75%)")
    oilShrink: float = Field(0.0, description="Oil shrinkage percentage as a decimal")
    gasShrink: float = Field(0.0, description="Gas shrinkage percentage as a decimal")
    nglYield: float = Field(0.0, description="NGL yield in barrels per MMCF")

class DifferentialParameters(BaseModel):
    oilDifferential: float = Field(0.0, description="Oil differential in $/bbl")
    gasDifferential: float = Field(0.0, description="Gas differential in $/mmbtu")
    nglDifferential: float = Field(0.0, description="NGL differential as percentage of WTI")

class LOEParameters(BaseModel):
    fixedLOE: Optional[float] = Field(None, description="Fixed LOE in $/well/month")
    oilVariableLOE: Optional[float] = Field(None, description="Oil variable LOE in $/bbl")
    gasVariableLOE: Optional[float] = Field(None, description="Gas variable LOE in $/mcf")
    waterVariableLOE: Optional[float] = Field(None, description="Water variable LOE in $/bbl")

class GPTParameters(BaseModel):
    oilGPT: float = Field(0.0, description="Oil gathering, processing, and transport cost in $/bbl")
    gasGPT: float = Field(0.0, description="Gas gathering, processing, and transport cost in $/mcf")

class TaxParameters(BaseModel):
    oilSeverance: float = Field(0.0, description="Oil severance tax percentage as a decimal")
    gasSeverance: float = Field(0.0, description="Gas severance tax percentage as a decimal")
    nglSeverance: float = Field(0.0, description="NGL severance tax percentage as a decimal")
    adValorem: Optional[float] = Field(None, description="Ad valorem tax percentage as a decimal")

class PricePoint(BaseModel):
    date: str  # YYYY-MM format
    price: float

class PriceDeckParameters(BaseModel):
    oilPricePoints: Optional[List[PricePoint]] = None
    gasPricePoints: Optional[List[PricePoint]] = None
    nglPricePoints: Optional[List[PricePoint]] = None

class PricingParameters(BaseModel):
    oilPrice: Optional[float] = Field(None, description="Oil price in $/bbl for flat pricing")
    gasPrice: Optional[float] = Field(None, description="Gas price in $/mcf for flat pricing")
    nglPrice: Optional[float] = Field(None, description="NGL price in $/gal for flat pricing")
    useOilPriceDeck: bool = Field(False, description="Whether to use oil price deck")
    useGasPriceDeck: bool = Field(False, description="Whether to use gas price deck")
    useNglPriceDeck: bool = Field(False, description="Whether to use NGL price deck")
    priceDeck: Optional[PriceDeckParameters] = None

class PandAParameters(BaseModel):
    cost: float = Field(0.0, description="Plugging and abandonment cost in $/well")
    month: Optional[str] = Field(None, description="Month to apply P&A cost (YYYY-MM)")

class EconomicsRequest(BaseModel):
    well_id: str
    deal_id: str
    forecast_data: List[Dict[str, Any]] = Field(..., description="Forecast data with oil, gas, water rates and volumes")
    ownership: OwnershipParameters
    differentials: DifferentialParameters
    loe: LOEParameters
    gpt: GPTParameters
    taxes: TaxParameters
    pricing: PricingParameters
    pAndA: Optional[PandAParameters] = None
    discount_rate: float = Field(0.1, description="Annual discount rate as a decimal (e.g., 0.1 for 10%)")

# Output models
class CashFlowRow(BaseModel):
    date: str  # YYYY-MM format
    # Production volumes
    gross_oil: float
    gross_gas: float
    gross_water: float
    net_oil: float
    net_gas: float
    net_ngl: Optional[float] = None
    # Revenue
    oil_revenue: float
    gas_revenue: float
    ngl_revenue: Optional[float] = None
    total_revenue: float
    # Expenses
    fixed_loe: Optional[float] = None
    variable_oil_loe: Optional[float] = None
    variable_gas_loe: Optional[float] = None
    variable_water_loe: Optional[float] = None
    oil_gpt: float
    gas_gpt: float
    oil_severance: float
    gas_severance: float
    ngl_severance: Optional[float] = None
    ad_valorem: Optional[float] = None
    p_and_a: Optional[float] = None
    total_expenses: float
    # Cash flow
    net_cash_flow: float
    discounted_cash_flow: float
    cumulative_cash_flow: float

class EconomicsMetrics(BaseModel):
    npv: float
    irr: Optional[float] = None
    payout_months: Optional[int] = None
    roi: Optional[float] = None
    oil_breakeven: Optional[float] = None
    gas_breakeven: Optional[float] = None

class EconomicsResponse(BaseModel):
    cash_flow: List[CashFlowRow]
    metrics: EconomicsMetrics
    well_id: str
    deal_id: str

def get_days_in_month(date_str: str) -> int:
    """Get number of days in a month from various date formats"""
    try:
        date_parts = date_str.split('T')[0] if 'T' in date_str else date_str  # Handle ISO format
        parts = date_parts.split('-')
        
        if len(parts) >= 2:
            # Get the first two parts no matter how many there are
            year, month = int(parts[0]), int(parts[1])
            return calendar.monthrange(year, month)[1]
        else:
            print(f"Invalid date format: {date_str}")
            return 30  # Default
    except Exception as e:
        print(f"Error parsing date: {date_str} - {e}")
        return 30  # Default to 30 days if there's an error

def calculate_npv(cash_flows: List[float], dates: List[str], discount_rate: float) -> float:
    """Calculate NPV using monthly cash flows and discount rate"""
    if not cash_flows or not dates or len(cash_flows) != len(dates):
        return 0.0
        
    # Convert annual discount rate to monthly
    monthly_rate = (1 + discount_rate) ** (1/12) - 1
    
    # Helper function to parse dates in either format
    def parse_date(date_str):
        try:
            # First try parsing as ISO format (YYYY-MM-DDT00:00:00Z)
            if 'T' in date_str:
                date_part = date_str.split('T')[0]  # Get YYYY-MM-DD part
                # Try different formats, depending on how much detail is in the date
                if len(date_part.split('-')) >= 3:
                    return datetime.strptime(date_part, "%Y-%m-%d").replace(day=1)
                else:
                    # Handle YYYY-MM format within ISO string
                    return datetime.strptime(date_part.split('-')[0] + '-' + date_part.split('-')[1], "%Y-%m") 
            else:
                # Try to parse as YYYY-MM format
                try:
                    return datetime.strptime(date_str, "%Y-%m")
                except ValueError:
                    # Try full date format
                    return datetime.strptime(date_str, "%Y-%m-%d").replace(day=1)
        except Exception as e:
            print(f"Error parsing date in NPV calculation: {date_str} - {e}")
            # Default to current date if parsing fails
            return datetime.now().replace(day=1)
    
    # Use first date as reference
    base_date = parse_date(dates[0])
    
    npv = 0.0
    for i, cf in enumerate(cash_flows):
        # Calculate months from start
        current_date = parse_date(dates[i])
        months = (current_date.year - base_date.year) * 12 + (current_date.month - base_date.month)
        
        # Calculate present value
        if months == 0:  # First month doesn't need discounting
            npv += cf
        else:
            npv += cf / ((1 + monthly_rate) ** months)
            
    return npv

def calculate_irr(cash_flows: List[float]) -> Optional[float]:
    """Calculate IRR using monthly cash flows"""
    # Basic implementation - could be improved with numerical methods
    if not cash_flows or cash_flows[0] >= 0:  # Need initial negative cash flow
        return None
        
    # Simple guess-and-check method for demonstration
    # In production, use numerical methods like Newton-Raphson
    rates = [r/1200 for r in range(1, 1001)]  # 0.1% to 100% monthly rates
    
    for rate in rates:
        npv = 0.0
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + rate) ** i)
            
        if abs(npv) < 1000:  # Close enough to zero
            # Convert monthly rate to annual
            return ((1 + rate) ** 12) - 1
            
    return None  # No solution found

def calculate_payout(cash_flows: List[float]) -> Optional[int]:
    """Calculate payout period in months"""
    if not cash_flows:
        return None
        
    cumulative = 0.0
    for i, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0:
            return i
            
    return None  # Never reaches payout

@router.post("/calculate-economics", response_model=EconomicsResponse)
def calculate_economics(request: EconomicsRequest) -> EconomicsResponse:
    """Calculate detailed economic analysis based on forecast data and economic parameters"""
    
    print(f"Calculating economics for well {request.well_id} in deal {request.deal_id}")
    print(f"Forecast data points: {len(request.forecast_data)}")
    
    # Extract parameters
    well_id = request.well_id
    deal_id = request.deal_id
    forecast_data = request.forecast_data
    
    # Ownership parameters
    wi = request.ownership.workingInterest  # Working interest
    ri = request.ownership.revenueInterest  # Revenue interest
    oil_shrink = request.ownership.oilShrink
    gas_shrink = request.ownership.gasShrink
    ngl_yield = request.ownership.nglYield / 1000  # Convert from bbls/mmcf to bbls/mcf
    
    # Price and differential parameters
    oil_diff = request.differentials.oilDifferential
    gas_diff = request.differentials.gasDifferential
    ngl_diff = request.differentials.nglDifferential  # As percentage of oil price
    
    # Create price lookup dictionaries if using price decks
    oil_prices_by_date = {}
    gas_prices_by_date = {}
    ngl_prices_by_date = {}
    
    if request.pricing.useOilPriceDeck and request.pricing.priceDeck and request.pricing.priceDeck.oilPricePoints:
        oil_prices_by_date = {point.date: point.price for point in request.pricing.priceDeck.oilPricePoints}
    
    if request.pricing.useGasPriceDeck and request.pricing.priceDeck and request.pricing.priceDeck.gasPricePoints:
        gas_prices_by_date = {point.date: point.price for point in request.pricing.priceDeck.gasPricePoints}
    
    if request.pricing.useNglPriceDeck and request.pricing.priceDeck and request.pricing.priceDeck.nglPricePoints:
        ngl_prices_by_date = {point.date: point.price for point in request.pricing.priceDeck.nglPricePoints}
    
    # Default flat prices
    default_oil_price = request.pricing.oilPrice or 0.0
    default_gas_price = request.pricing.gasPrice or 0.0
    default_ngl_price = request.pricing.nglPrice or 0.0
    
    # LOE parameters
    fixed_loe = request.loe.fixedLOE
    oil_var_loe = request.loe.oilVariableLOE
    gas_var_loe = request.loe.gasVariableLOE
    water_var_loe = request.loe.waterVariableLOE
    
    # GPT parameters
    oil_gpt = request.gpt.oilGPT
    gas_gpt = request.gpt.gasGPT
    
    # Tax parameters
    oil_sev = request.taxes.oilSeverance / 100  # Convert from percentage to decimal
    gas_sev = request.taxes.gasSeverance / 100  # Convert from percentage to decimal
    ngl_sev = request.taxes.nglSeverance / 100  # Convert from percentage to decimal
    ad_val = request.taxes.adValorem / 100 if request.taxes.adValorem else None  # Convert from percentage to decimal
    
    # P&A parameters
    p_and_a_cost = request.pAndA.cost if request.pAndA else 0.0
    p_and_a_month = request.pAndA.month if request.pAndA else None
    
    # Discount rate
    discount_rate = request.discount_rate
    
    # Sort forecast data by date
    forecast_data.sort(key=lambda x: x.get('date', ''))
    
    # Process each row of forecast data to generate cash flow
    cash_flow_rows = []
    total_cash_flow = 0.0
    cash_flow_values = []
    cash_flow_dates = []
    
    for row in forecast_data:
        date = row.get('date', '')
        
        # Use forecast values first, then fall back to historical if needed
        gross_oil = row.get('oil_forecast') or row.get('oil_historical') or 0.0
        gross_gas = row.get('gas_forecast') or row.get('gas_historical') or 0.0
        gross_water = row.get('water_forecast') or row.get('water_historical') or 0.0
        
        # Get monthly volume or calculate if not available
        days_in_month = get_days_in_month(date)
        gross_oil_volume = row.get('oil_volume') or (gross_oil * days_in_month)
        gross_gas_volume = row.get('gas_volume') or (gross_gas * days_in_month)
        gross_water_volume = row.get('water_volume') or (gross_water * days_in_month)
        
        # Calculate net volumes adjusting for ownership and shrinkage
        net_oil = gross_oil_volume * ri * (1 - oil_shrink)
        net_gas = gross_gas_volume * ri * (1 - gas_shrink)
        net_ngl = net_gas * ngl_yield if ngl_yield > 0 else 0
        
        # Get prices for this date, defaulting to flat price if not in price deck
        oil_price = oil_prices_by_date.get(date, default_oil_price)
        gas_price = gas_prices_by_date.get(date, default_gas_price)
        ngl_price = ngl_prices_by_date.get(date, default_ngl_price)
        
        # Calculate revenue
        oil_revenue = net_oil * (oil_price - oil_diff)
        gas_revenue = net_gas * (gas_price - gas_diff)
        
        # Calculate NGL revenue based on whether we're using percentage of oil or direct pricing
        if ngl_yield > 0:
            if request.pricing.useNglPriceDeck:
                # When using a price deck, prices are absolute
                ngl_revenue = net_ngl * ngl_price
            else:
                # When using flat pricing, NGL price can be based on oil price with differential
                if ngl_diff != 0:
                    # Using percentage of oil price
                    ngl_revenue = net_ngl * (oil_price * ngl_diff / 100)
                else:
                    # Using flat NGL price
                    ngl_revenue = net_ngl * ngl_price
        else:
            ngl_revenue = 0
            
        total_revenue = oil_revenue + gas_revenue + ngl_revenue
        
        # Calculate expenses
        # Fixed LOE
        fixed_loe_expense = fixed_loe * wi if fixed_loe else 0
        
        # Variable LOE
        var_oil_loe = gross_oil_volume * oil_var_loe * wi if oil_var_loe else 0
        var_gas_loe = gross_gas_volume * gas_var_loe * wi if gas_var_loe else 0
        var_water_loe = gross_water_volume * water_var_loe * wi if water_var_loe else 0
        
        # GPT costs
        oil_gpt_cost = gross_oil_volume * oil_gpt * wi
        gas_gpt_cost = gross_gas_volume * gas_gpt * wi
        
        # Taxes
        oil_sev_tax = oil_revenue * oil_sev
        gas_sev_tax = gas_revenue * gas_sev
        ngl_sev_tax = ngl_revenue * ngl_sev if ngl_yield > 0 else 0
        ad_val_tax = total_revenue * ad_val if ad_val else 0
        
        # P&A cost (only apply in specified month)
        p_and_a_expense = p_and_a_cost * wi if p_and_a_month and date == p_and_a_month else 0
        
        # Total expenses
        total_expenses = (
            fixed_loe_expense + 
            var_oil_loe + var_gas_loe + var_water_loe + 
            oil_gpt_cost + gas_gpt_cost + 
            oil_sev_tax + gas_sev_tax + ngl_sev_tax + 
            (ad_val_tax or 0) + 
            p_and_a_expense
        )
        
        # Net cash flow
        net_cash_flow = total_revenue - total_expenses
        
        # Track cumulative cash flow
        total_cash_flow += net_cash_flow
        
        # Store values for metrics calculations
        cash_flow_values.append(net_cash_flow)
        cash_flow_dates.append(date)
        
        # Create cash flow row
        cash_flow_row = CashFlowRow(
            date=date,
            # Production
            gross_oil=gross_oil_volume,
            gross_gas=gross_gas_volume,
            gross_water=gross_water_volume,
            net_oil=net_oil,
            net_gas=net_gas,
            net_ngl=net_ngl if ngl_yield > 0 else None,
            # Revenue
            oil_revenue=oil_revenue,
            gas_revenue=gas_revenue,
            ngl_revenue=ngl_revenue if ngl_yield > 0 else None,
            total_revenue=total_revenue,
            # Expenses
            fixed_loe=fixed_loe_expense if fixed_loe else None,
            variable_oil_loe=var_oil_loe if oil_var_loe else None,
            variable_gas_loe=var_gas_loe if gas_var_loe else None,
            variable_water_loe=var_water_loe if water_var_loe else None,
            oil_gpt=oil_gpt_cost,
            gas_gpt=gas_gpt_cost,
            oil_severance=oil_sev_tax,
            gas_severance=gas_sev_tax,
            ngl_severance=ngl_sev_tax if ngl_yield > 0 else None,
            ad_valorem=ad_val_tax,
            p_and_a=p_and_a_expense if p_and_a_expense > 0 else None,
            total_expenses=total_expenses,
            # Cash flow
            net_cash_flow=net_cash_flow,
            discounted_cash_flow=0.0,  # Will be calculated after all rows are processed
            cumulative_cash_flow=total_cash_flow
        )
        
        cash_flow_rows.append(cash_flow_row)
    
    # Calculate NPV
    npv = calculate_npv(cash_flow_values, cash_flow_dates, discount_rate)
    
    # Calculate discounted cash flow for each period
    if cash_flow_rows:
        # Helper function to parse dates in either format
        def parse_date(date_str):
            try:
                # First try parsing as ISO format (YYYY-MM-DDT00:00:00Z)
                if 'T' in date_str:
                    date_part = date_str.split('T')[0]  # Get YYYY-MM-DD part
                    # Try different formats, depending on how much detail is in the date
                    if len(date_part.split('-')) >= 3:
                        return datetime.strptime(date_part, "%Y-%m-%d").replace(day=1)
                    else:
                        # Handle YYYY-MM format within ISO string
                        return datetime.strptime(date_part.split('-')[0] + '-' + date_part.split('-')[1], "%Y-%m") 
                else:
                    # Try to parse as YYYY-MM format
                    try:
                        return datetime.strptime(date_str, "%Y-%m")
                    except ValueError:
                        # Try full date format
                        return datetime.strptime(date_str, "%Y-%m-%d").replace(day=1)
            except Exception as e:
                print(f"Error parsing date in discounted cash flow calculation: {date_str} - {e}")
                # Default to current date if parsing fails
                return datetime.now().replace(day=1)
                
        # Use first date as reference
        base_date = parse_date(cash_flow_rows[0].date)
            
        monthly_rate = (1 + discount_rate) ** (1/12) - 1
        
        for i, row in enumerate(cash_flow_rows):
            # Calculate months from start using our helper
            current_date = parse_date(row.date)
            # Properly handle the calculation even if parse_date returns dates with different formats
            months = (current_date.year - base_date.year) * 12 + (current_date.month - base_date.month)
            
            if months == 0:
                row.discounted_cash_flow = row.net_cash_flow
            else:
                row.discounted_cash_flow = row.net_cash_flow / ((1 + monthly_rate) ** months)
    
    # Calculate other metrics
    irr = calculate_irr(cash_flow_values)
    payout_months = calculate_payout(cash_flow_values)
    
    # Calculate ROI if we have payout
    roi = None
    if payout_months is not None and payout_months < len(cash_flow_values):
        # ROI = (Total returns - Initial investment) / Initial investment
        initial_investment = abs(sum(cf for cf in cash_flow_values[:payout_months] if cf < 0))
        if initial_investment > 0:
            total_returns = sum(cash_flow_values[payout_months:])
            roi = total_returns / initial_investment
    
    # Create metrics object
    metrics = EconomicsMetrics(
        npv=npv,
        irr=irr,
        payout_months=payout_months,
        roi=roi,
        # Breakeven calculations would be more complex in practice
        oil_breakeven=None,
        gas_breakeven=None
    )
    
    # Return complete response
    return EconomicsResponse(
        cash_flow=cash_flow_rows,
        metrics=metrics,
        well_id=well_id,
        deal_id=deal_id
    )
