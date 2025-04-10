import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import databutton as db
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Initialize router with a unique prefix to avoid route conflicts
router = APIRouter(prefix="/enverus")

# Enverus API configuration
ENVERUS_API_URL = "https://api.enverus.com/v3/direct-access"

# Global token cache
API_TOKEN = None
TOKEN_EXPIRY = 0  # Unix timestamp when token expires


class EnverusAPIError(Exception):
    """Custom exception for Enverus API errors."""
    pass


# Pydantic models for API requests and responses
class QueryWellsRequest(BaseModel):
    api_numbers: List[str]


class WellHeader(BaseModel):
    api_number: str
    well_name: Optional[str] = None
    operator: Optional[str] = None
    first_production_date: Optional[str] = None
    formation: Optional[str] = None
    basin: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompletionData(BaseModel):
    lateral_length: Optional[float] = None
    frac_stages: Optional[int] = None
    proppant_amount: Optional[float] = None
    fluid_amount: Optional[float] = None
    completion_type: Optional[str] = None
    lateral_line: Optional[str] = None


class ProductionData(BaseModel):
    cumulative_oil: float = 0
    cumulative_gas: float = 0
    cumulative_water: float = 0
    monthly_production: List[Dict[str, Any]] = []


class WellResponse(BaseModel):
    api_number: str
    well_header: WellHeader
    completion_data: Optional[CompletionData] = None
    production_data: ProductionData
    raw_data: Optional[Dict[str, Any]] = None


class QueryWellsResponse(BaseModel):
    wells: List[WellResponse] = []
    not_found: List[str] = []
    errors: List[str] = []


def generate_token() -> None:
    """Generate a new token from the Enverus API and store it globally."""
    global API_TOKEN, TOKEN_EXPIRY
    
    try:
        secret_key = db.secrets.get("ENVERUS_SECRET_KEY")
        if not secret_key:
            raise EnverusAPIError("Enverus API key not configured")
        
        token_url = f"{ENVERUS_API_URL}/tokens"
        payload = {"secretKey": secret_key}
        
        # Add timeout and retry logic
        for attempt in range(3):  # Try 3 times
            try:
                response = requests.post(token_url, json=payload, timeout=10)  # 10 second timeout
                if response.status_code == 200:
                    token_data = response.json()
                    API_TOKEN = token_data.get("token")
                    # Set expiry to 1 hour before actual expiry to be safe (token is valid for 24 hours)
                    TOKEN_EXPIRY = time.time() + 23 * 3600  # 23 hours
                    print("Successfully generated new Enverus API token")
                    return
                else:
                    print(f"Token generation failed: {response.status_code} {response.text}")
                    if attempt < 2:  # Don't sleep on the last attempt
                        time.sleep(1 * (attempt + 1))  # Increasing sleep time
            except requests.exceptions.RequestException as e:
                print(f"Request error during token generation (attempt {attempt+1}): {str(e)}")
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
        
        # If we got here, all attempts failed
        raise EnverusAPIError("Failed to generate API token after multiple attempts")
    except Exception as e:
        API_TOKEN = None
        TOKEN_EXPIRY = 0
        raise EnverusAPIError(f"Token generation error: {str(e)}")


def get_token() -> str:
    """Retrieve the current token, generating a new one if necessary."""
    global API_TOKEN, TOKEN_EXPIRY
    
    # Check if token needs to be refreshed
    if not API_TOKEN or time.time() > TOKEN_EXPIRY:
        generate_token()
    
    if not API_TOKEN:
        raise EnverusAPIError("Failed to obtain API token")
    
    return API_TOKEN


def safe_api_call(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an API call with error handling and retries."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    for attempt in range(5):  # Try 5 times for better reliability
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)  # Reduced timeout for faster failure detection
            
            # Handle 401 (unauthorized) - token might have expired
            if response.status_code == 401:
                if attempt == 0:  # Only regenerate token on first 401
                    print("Token expired, regenerating...")
                    generate_token()
                    token = get_token()
                    headers["Authorization"] = f"Bearer {token}"
                    continue  # Try again with new token
            
            # Handle successful response
            if response.status_code == 200:
                return response.json()
            
            # Handle various error codes
            error_msg = f"API call failed: {response.status_code} {response.text}"
            print(error_msg)
            
            # Decide whether to retry based on status code
            if response.status_code in [429, 502, 503, 504]:
                if attempt < 4:  # Don't sleep on the last attempt
                    # Faster backoff with jitter for improved performance
                    sleep_time = 0.5 * (2 ** attempt)  # 0.5, 1, 2, 4 seconds
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                continue
            else:
                # Don't retry for other status codes
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt+1}): {str(e)}")
            if attempt < 2:  # Don't sleep on the last attempt
                time.sleep(2 ** attempt)
    
    # If we got here, all attempts failed
    raise EnverusAPIError(f"Failed to complete API call after multiple attempts: {url}")


def normalize_api_numbers(api_list: List[str]) -> List[str]:
    """Normalize API numbers by removing non-digit characters and validating length."""
    normalized = []
    for api in api_list:
        # Remove all non-digit characters
        api_clean = ''.join(filter(str.isdigit, str(api)))
        
        # Validate length
        if len(api_clean) >= 10:
            normalized.append(api_clean)
    
    return normalized


def split_list_for_url_length(api_list: List[str], max_apis_per_call: int = 1000) -> List[List[str]]:
    """Split API list into smaller chunks for better reliability and performance."""
    # Always use 1,000 wells per batch for consistent performance regardless of input size
    chunks = []
    
    # Create chunks of max_apis_per_call
    for i in range(0, len(api_list), max_apis_per_call):
        chunks.append(api_list[i:i + max_apis_per_call])
    
    return chunks


def fetch_well_headers(api_list: List[str]) -> pd.DataFrame:
    """Fetch well headers from the Enverus API for the given list of API numbers."""
    if not api_list:
        return pd.DataFrame()
    
    start_time = time.time()
    print(f"Fetching well headers for {len(api_list)} API numbers")
    
    # Normalize API numbers
    api_list = normalize_api_numbers(api_list)
    if not api_list:
        return pd.DataFrame()
    
    # Split into chunks to avoid URL length limitations
    all_chunks = split_list_for_url_length(api_list)
    print(f"Processing {len(all_chunks)} chunks for well headers")
    
    all_data = []
    for i, chunk in enumerate(all_chunks):
        try:
            url = f"{ENVERUS_API_URL}/well-headers"
            params = {"API_UWI_Unformatted": ",".join(chunk)}
            
            # Add minimal delay between API calls to avoid rate limiting
            if i > 0:
                time.sleep(0.1)  # Short delay between chunk requests
                
            # Make the API call
            print(f"Fetching well headers chunk {i+1}/{len(all_chunks)} with {len(chunk)} APIs")
            data = safe_api_call(url, params)
            
            # Append results
            if isinstance(data, list) and data:
                all_data.extend(data)
                print(f"Received {len(data)} well headers")
            elif isinstance(data, dict):
                # Handle case where response is a dict
                all_data.append(data)
                print("Received 1 well header")
            else:
                print(f"No well headers found for chunk {i+1}")
                
        except Exception as e:
            print(f"Error fetching well headers chunk {i+1}: {str(e)}")
    
    # Convert to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        elapsed = time.time() - start_time
        print(f"Successfully fetched {len(df)} well headers in {elapsed:.2f}s")
        return df
    else:
        print("No well headers found")
        return pd.DataFrame()


def fetch_production_data(api_list: List[str]) -> pd.DataFrame:
    """Fetch production data from the Enverus API for the given list of API numbers."""
    if not api_list:
        return pd.DataFrame()
    
    start_time = time.time()
    print(f"Fetching production data for {len(api_list)} API numbers")
    
    # Normalize API numbers
    api_list = normalize_api_numbers(api_list)
    if not api_list:
        return pd.DataFrame()
    
    # Split into chunks to avoid URL length limitations
    all_chunks = split_list_for_url_length(api_list)
    print(f"Processing {len(all_chunks)} chunks for production data")
    
    all_data = []
    for i, chunk in enumerate(all_chunks):
        try:
            url = f"{ENVERUS_API_URL}/production"
            params = {"API_UWI_Unformatted": ",".join(chunk)}
            
            # Add minimal delay between API calls to avoid rate limiting
            if i > 0:
                time.sleep(0.1)  # Short delay between chunk requests
                
            # Make the API call
            print(f"Fetching production data chunk {i+1}/{len(all_chunks)} with {len(chunk)} APIs")
            data = safe_api_call(url, params)
            
            # Append results
            if isinstance(data, list) and data:
                all_data.extend(data)
                print(f"Received {len(data)} production records")
            elif isinstance(data, dict):
                # Handle case where response is a dict
                all_data.append(data)
                print("Received 1 production record")
            else:
                print(f"No production data found for chunk {i+1}")
                
        except Exception as e:
            print(f"Error fetching production data chunk {i+1}: {str(e)}")
    
    # Convert to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        elapsed = time.time() - start_time
        print(f"Successfully fetched {len(df)} production records in {elapsed:.2f}s")
        return df
    else:
        print("No production data found")
        return pd.DataFrame()


def fetch_completion_headers(api_list: List[str]) -> pd.DataFrame:
    """Fetch completion header data from the Enverus API for the given list of API numbers."""
    if not api_list:
        return pd.DataFrame()
    
    start_time = time.time()
    print(f"Fetching completion headers for {len(api_list)} API numbers")
    
    # Normalize API numbers
    api_list = normalize_api_numbers(api_list)
    if not api_list:
        return pd.DataFrame()
    
    # Split into chunks to avoid URL length limitations
    all_chunks = split_list_for_url_length(api_list)
    print(f"Processing {len(all_chunks)} chunks for completion headers")
    
    all_data = []
    for i, chunk in enumerate(all_chunks):
        try:
            url = f"{ENVERUS_API_URL}/completion-headers"
            params = {"API_UWI_Unformatted": ",".join(chunk)}
            
            # Add minimal delay between API calls to avoid rate limiting
            if i > 0:
                time.sleep(0.1)  # Short delay between chunk requests
                
            # Make the API call
            print(f"Fetching completion headers chunk {i+1}/{len(all_chunks)} with {len(chunk)} APIs")
            data = safe_api_call(url, params)
            
            # Append results
            if isinstance(data, list) and data:
                all_data.extend(data)
                print(f"Received {len(data)} completion headers")
            elif isinstance(data, dict):
                # Handle case where response is a dict
                all_data.append(data)
                print("Received 1 completion header")
            else:
                print(f"No completion headers found for chunk {i+1}")
                
        except Exception as e:
            print(f"Error fetching completion headers chunk {i+1}: {str(e)}")
    
    # Convert to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        elapsed = time.time() - start_time
        print(f"Successfully fetched {len(df)} completion headers in {elapsed:.2f}s")
        return df
    else:
        print("No completion headers found")
        return pd.DataFrame()


def safe_float(value) -> Optional[float]:
    """Convert value to float safely, returning None for invalid values."""
    if pd.isna(value) or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value) -> Optional[int]:
    """Convert value to int safely, returning None for invalid values."""
    if pd.isna(value) or value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def format_date(date_value) -> Optional[str]:
    """Format date to ISO format string."""
    if pd.isna(date_value) or date_value is None:
        return None
        
    try:
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        elif isinstance(date_value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(date_value, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return date_value
    except Exception as e:
        print(f"Error formatting date {date_value}: {str(e)}")
        return None


def process_results(well_headers_df: pd.DataFrame, production_df: pd.DataFrame, completion_df: pd.DataFrame, api_numbers: List[str]) -> Dict:
    """Process the results from all API calls and format for response."""
    wells = []
    not_found = []
    errors = []
    
    # Normalize all requested API numbers for comparison
    normalized_request_apis = normalize_api_numbers(api_numbers)
    
    # Extract found API numbers from the well headers
    found_apis = set()
    if not well_headers_df.empty and 'API_UWI_Unformatted' in well_headers_df.columns:
        found_apis.update(well_headers_df['API_UWI_Unformatted'].unique())
    
    # Track original to normalized API mapping
    api_mapping = {}
    for original_api in api_numbers:
        normalized = ''.join(filter(str.isdigit, original_api))
        if len(normalized) >= 10:
            api_mapping[normalized] = original_api
    
    # Mark not found APIs
    for api in normalized_request_apis:
        if api not in found_apis:
            original_api = api_mapping.get(api, api)
            not_found.append(original_api)
    
    # If we have no well headers, return early
    if well_headers_df.empty:
        return {
            "wells": [],
            "not_found": not_found,
            "errors": ["No well data found"]
        }
    
    # Process well data
    for api_uwi, group in well_headers_df.groupby('API_UWI_Unformatted'):
        try:
            # Use the first row for each API number
            well_row = group.iloc[0]
            
            # Find the original API number
            original_api = api_mapping.get(api_uwi, api_uwi)
            
            # Create well header
            well_header = WellHeader(
                api_number=original_api,
                well_name=well_row.get('WellName'),
                operator=well_row.get('ENVOperator'),
                first_production_date=format_date(well_row.get('FirstProdDate')),
                spud_date=format_date(well_row.get('SpudDate')),
                formation=well_row.get('ENVInterval'),
                basin=well_row.get('ENVBasin'),
                county=well_row.get('County'),
                state=well_row.get('StateProvince'),
                status=well_row.get('ENVWellStatus'),
                latitude=safe_float(well_row.get('Latitude')),
                longitude=safe_float(well_row.get('Longitude'))
            )
            
            # Get completion data for this well
            well_completion_df = completion_df[
                completion_df['API_UWI_Unformatted'] == api_uwi
            ] if not completion_df.empty and 'API_UWI_Unformatted' in completion_df.columns else pd.DataFrame()
            
            # Create completion data if available
            completion_data = None
            if not well_completion_df.empty:
                # Get the most recent completion record
                comp_row = well_completion_df.iloc[0] if len(well_completion_df) > 0 else None
                if comp_row is not None:
                    completion_data = CompletionData(
                        lateral_length=safe_float(comp_row.get('LateralLength_ft')),
                        frac_stages=safe_int(comp_row.get('FracStages')),
                        proppant_amount=safe_float(comp_row.get('TotalProppant_lbs')),
                        fluid_amount=safe_float(comp_row.get('TotalFluid_gal')),
                        completion_type=comp_row.get('CompletionType'),
                        completion_date=format_date(well_row.get('CompletionDate')),
                        lateral_line=comp_row.get('LateralLine')
                    )
            
            # Get production data for this well
            well_production_df = production_df[
                production_df['API_UWI_Unformatted'] == api_uwi
            ] if not production_df.empty and 'API_UWI_Unformatted' in production_df.columns else pd.DataFrame()
            
            # Create production data
            monthly_production = []
            if not well_production_df.empty:
                # Calculate cumulative production
                cum_oil = well_production_df['LiquidsProd_BBL'].sum() if 'LiquidsProd_BBL' in well_production_df.columns else 0
                cum_gas = well_production_df['GasProd_MCF'].sum() if 'GasProd_MCF' in well_production_df.columns else 0
                cum_water = well_production_df['WaterProd_BBL'].sum() if 'WaterProd_BBL' in well_production_df.columns else 0
                
                # Create monthly production records
                for _, prod_row in well_production_df.iterrows():
                    month_data = {
                        'date': format_date(prod_row.get('ProducingMonth')),
                        # Use the daily rates directly from Enverus instead of calculating
                        'oil': safe_float(prod_row.get('CDLiquids_BBLPerDAY')),
                        'gas': safe_float(prod_row.get('CDGas_MCFPerDAY')), 
                        'water': safe_float(prod_row.get('CDWater_BBLPerDAY')),
                        'days_on': safe_int(prod_row.get('ProducingDays'))
                    }
                    monthly_production.append(month_data)
            else:
                cum_oil = 0
                cum_gas = 0
                cum_water = 0
            
            production_data = ProductionData(
                cumulative_oil=cum_oil,
                cumulative_gas=cum_gas,
                cumulative_water=cum_water,
                monthly_production=monthly_production
            )
            
            # Create the well response
            well_response = WellResponse(
                api_number=original_api,
                well_header=well_header,
                completion_data=completion_data,
                production_data=production_data,
                raw_data=well_row.to_dict() if hasattr(well_row, 'to_dict') else None
            )
            
            wells.append(well_response)
        except Exception as e:
            error_msg = f"Error processing well {api_uwi}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            not_found.append(api_mapping.get(api_uwi, api_uwi))
    
    return {
        "wells": wells,
        "not_found": not_found,
        "errors": errors
    }


@router.post("/query", response_model=QueryWellsResponse)
def query_wells(request: QueryWellsRequest) -> QueryWellsResponse:
    """Query wells by API numbers"""
    print("POST /enverus/query (started)")
    start_time = time.time()
    
    if not request.api_numbers:
        print("No API numbers provided")
        return QueryWellsResponse(errors=["No API numbers provided"])
    
    try:
        # Fetch all data types
        well_headers_df = fetch_well_headers(request.api_numbers)
        completion_df = fetch_completion_headers(request.api_numbers)
        production_df = fetch_production_data(request.api_numbers)
        
        # Process and combine the results
        results = process_results(well_headers_df, production_df, completion_df, request.api_numbers)
        
        elapsed = time.time() - start_time
        print(f"POST /enverus/query completed in {elapsed:.2f}s with {len(results['wells'])} wells found")
        
        return QueryWellsResponse(
            wells=results["wells"],
            not_found=results["not_found"],
            errors=results["errors"]
        )
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error processing request: {str(e)}"
        print(f"POST /enverus/query failed in {elapsed:.2f}s: {error_msg}")
        
        return QueryWellsResponse(
            not_found=request.api_numbers,
            errors=[error_msg]
        )
