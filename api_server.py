"""
FlightAI REST API Server
FastAPI wrapper for existing Python backend logic
Exposes endpoints for Next.js frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Import existing backend modules
from core import get_trip_dates
from iata_extractor import extract_iata_from_query, get_indian_airports_list
from amadeus_flights import AmadeusFlightSearch, get_airline_name, get_airline_website

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="FlightAI API",
    description="Premium AI-powered flight search backend",
    version="2.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://flightai-sigma.vercel.app"  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Amadeus client
amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

if amadeus_client_id and amadeus_client_secret:
    amadeus_searcher = AmadeusFlightSearch()
else:
    amadeus_searcher = None


# ==================== REQUEST/RESPONSE MODELS ====================

class TripExtractionRequest(BaseModel):
    origin_iata: str
    user_query: str
    fallback_days: int = 7

class TripExtractionResponse(BaseModel):
    success: bool
    origin_iata: str
    origin_city: str
    destination_iata: Optional[str]
    destination_city: Optional[str]
    iata_confidence: str
    duration_days: int
    departure_date: str
    return_date: str
    model_used: str
    used_fallback: bool
    error: Optional[str]

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    adults: int = 1
    max_results: int = 10
    currency: str = "INR"
    travel_class: Optional[str] = None
    non_stop: bool = False
    max_stops: Optional[int] = None

class AirportInfo(BaseModel):
    iata: str
    city: str
    name: str
    country: str = "India"


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """API Health check"""
    return {
        "status": "online",
        "service": "FlightAI API",
        "version": "2.0.0",
        "endpoints": [
            "/airports",
            "/extract-trip",
            "/search-flights",
            "/airline-info/{code}"
        ]
    }

@app.get("/airports", response_model=List[AirportInfo])
async def get_airports():
    """Get list of available Indian airports"""
    try:
        airports_raw = get_indian_airports_list()
        airport_list = []
        
        # airports_raw is a list of dicts: [{"code": "BOM", "label": "Mumbai (BOM) - Airport Name"}, ...]
        for airport_dict in airports_raw:
            try:
                iata_code = airport_dict.get("code", "").strip().upper()
                label = airport_dict.get("label", "")
                
                # Validate IATA code
                if not iata_code or len(iata_code) != 3:
                    continue
                
                # Parse label: "Mumbai (BOM) - Chhatrapati Shivaji..."
                # Extract city (before first parenthesis) and airport name (after dash)
                if " - " in label:
                    city_part = label.split(" - ")[0]
                    name_part = label.split(" - ")[1] if len(label.split(" - ")) > 1 else ""
                    
                    # Remove IATA code from city part if present
                    if "(" in city_part:
                        city_name = city_part.split("(")[0].strip()
                    else:
                        city_name = city_part.strip()
                    
                    full_name = name_part.strip() if name_part else city_name
                else:
                    # Fallback if no dash
                    city_name = label.split("(")[0].strip() if "(" in label else label
                    full_name = city_name
                
                airport_list.append(AirportInfo(
                    iata=iata_code,
                    city=city_name,
                    name=full_name,
                    country="India"
                ))
                
            except Exception as parse_error:
                print(f"WARNING: Could not parse airport: {airport_dict} - {parse_error}")
                continue
        
        return airport_list
        
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in get_airports: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching airports: {str(e)}")

@app.post("/extract-trip", response_model=TripExtractionResponse)
async def extract_trip_details(request: TripExtractionRequest):
    """
    Extract trip details from natural language query
    Uses AI to extract destination and duration
    """
    try:
        # Extract IATA code
        iata_result = extract_iata_from_query(request.user_query)
        
        if not iata_result or not iata_result.get('iata_code'):
            return TripExtractionResponse(
                success=False,
                origin_iata=request.origin_iata,
                origin_city="",
                destination_iata=None,
                destination_city=None,
                iata_confidence="low",
                duration_days=request.fallback_days,
                departure_date="",
                return_date="",
                model_used="none",
                used_fallback=True,
                error="Could not extract destination from query"
            )
        
        # Extract duration and dates
        duration_result = get_trip_dates(
            request.origin_iata,
            request.user_query,
            fallback_days=request.fallback_days
        )
        
        # Get origin city from airports list
        airports = get_indian_airports_list()
        origin_city = ""
        for airport_dict in airports:
            if airport_dict.get("code") == request.origin_iata:
                # Extract city from label: "Mumbai (BOM) - Airport Name"
                label = airport_dict.get("label", "")
                if "(" in label:
                    origin_city = label.split("(")[0].strip()
                else:
                    origin_city = label.split(" - ")[0].strip() if " - " in label else label
                break
        
        return TripExtractionResponse(
            success=True,
            origin_iata=request.origin_iata,
            origin_city=origin_city,
            destination_iata=iata_result.get('iata_code'),
            destination_city=iata_result.get('destination_city'),
            iata_confidence=iata_result.get('confidence', 'low'),
            duration_days=duration_result.get('duration_days', request.fallback_days),
            departure_date=duration_result.get('departure_date').strftime('%Y-%m-%d') if duration_result.get('departure_date') else "",
            return_date=duration_result.get('return_date').strftime('%Y-%m-%d') if duration_result.get('return_date') else "",
            model_used=duration_result.get('model_used', 'none'),
            used_fallback=duration_result.get('used_fallback', True),
            error=duration_result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting trip: {str(e)}")

@app.post("/search-flights")
async def search_flights(request: FlightSearchRequest):
    """
    Search for real-time flight offers
    Connects to Amadeus API
    """
    try:
        if not amadeus_searcher:
            raise HTTPException(
                status_code=503,
                detail="Flight search service unavailable. Check Amadeus credentials."
            )
        
        # Call Amadeus search
        result = amadeus_searcher.search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            adults=request.adults,
            max_results=request.max_results,
            currency=request.currency,
            travel_class=request.travel_class,
            non_stop=request.non_stop
        )
        
        # Apply client-side max stops filter if specified
        if request.max_stops is not None and result.get('success') and result.get('flights'):
            filtered_flights = []
            for flight in result['flights']:
                outbound_stops = flight['outbound']['stops']
                return_stops = flight.get('return', {}).get('stops', 0)
                
                if outbound_stops <= request.max_stops and return_stops <= request.max_stops:
                    filtered_flights.append(flight)
            
            result['flights'] = filtered_flights
            result['total_offers'] = len(filtered_flights)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching flights: {str(e)}")

@app.get("/airline-info/{carrier_code}")
async def get_airline_info(carrier_code: str):
    """Get airline name and website from carrier code"""
    try:
        airline_name = get_airline_name(carrier_code)
        airline_website = get_airline_website(carrier_code)
        
        return {
            "carrier_code": carrier_code,
            "airline_name": airline_name,
            "website": airline_website,
            "has_direct_booking": airline_website is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching airline info: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "amadeus_configured": amadeus_searcher is not None,
        "google_api_configured": os.getenv("GOOGLE_API_KEY") is not None,
        "timestamp": datetime.now().isoformat()
    }


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
