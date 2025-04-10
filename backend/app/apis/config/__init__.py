from fastapi import APIRouter
from pydantic import BaseModel
import databutton as db

router = APIRouter(prefix="/config")

class TokenResponse(BaseModel):
    token: str

@router.get("/mapbox-token")
def get_mapbox_token() -> TokenResponse:
    """
    Retrieve the Mapbox access token for map displays
    """
    # Get the Mapbox token from secrets
    mapbox_token = db.secrets.get("MAPBOX_ACCESS_TOKEN")
    
    # Return the token (will be empty string if not set)
    return TokenResponse(token=mapbox_token or "")
