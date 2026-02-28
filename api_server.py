"""
FlightAI REST API Server
FastAPI wrapper for existing Python backend logic
Exposes endpoints for Next.js frontend
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
import uuid
from dotenv import load_dotenv

# Import existing backend modules
from core import get_trip_dates
from iata_extractor import extract_iata_from_query, get_indian_airports_list
from amadeus_flights import AmadeusFlightSearch, get_airline_name, get_airline_website

# Import new modules
from database import init_db, async_session, User, TravelHistory, UserPreferences
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_optional_user
)
from auto_package_generator import generate_packages
from nlp_parser import extract_travel_intent

from sqlalchemy import select

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="FlightAI API",
    description="Premium AI-powered flight search backend",
    version="3.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://flightai-sigma.vercel.app"
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


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup():
    await init_db()


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

# ---- Auth Models ----

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    home_airport: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str
    name: str

class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    home_airport: Optional[str]
    created_at: str

# ---- Auto Package Models ----

class PreferencesInput(BaseModel):
    interests: Optional[List[str]] = None
    budget_level: Optional[str] = "moderate"
    travel_style: Optional[str] = "mixed"

class AutoPackageRequest(BaseModel):
    destination: Optional[str] = None
    destination_iata: Optional[str] = None
    duration_days: int = 7
    budget_inr: Optional[int] = None
    preferences: PreferencesInput = PreferencesInput()
    natural_language_query: Optional[str] = None

class NLPParseRequest(BaseModel):
    query: str

class SavePreferencesRequest(BaseModel):
    interests: Optional[List[str]] = None
    budget_level: Optional[str] = "moderate"
    travel_style: Optional[str] = "mixed"
    preferred_destinations: Optional[List[str]] = None
    travel_companions: Optional[str] = None
    accommodation_preference: Optional[str] = "hotel"

class TravelHistoryResponse(BaseModel):
    id: int
    origin_iata: str
    destination_iata: str
    destination_city: Optional[str]
    duration_days: Optional[int]
    query_text: Optional[str]
    searched_at: str


# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Create a new user account"""
    async with async_session() as session:
        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            hashed_password=hash_password(request.password),
            name=request.name,
            home_airport=request.home_airport,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token(str(user.id), user.email, user.name)
        return AuthResponse(
            token=token,
            user_id=str(user.id),
            email=user.email,
            name=user.name,
        )


@app.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(str(user.id), user.email, user.name)
        return AuthResponse(
            token=token,
            user_id=str(user.id),
            email=user.email,
            name=user.name,
        )


@app.get("/auth/me", response_model=UserProfileResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user["user_id"])
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserProfileResponse(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            home_airport=user.home_airport,
            created_at=user.created_at.isoformat(),
        )


# ==================== TRAVEL HISTORY ENDPOINTS ====================

@app.get("/travel-history", response_model=List[TravelHistoryResponse])
async def get_travel_history(current_user: dict = Depends(get_current_user)):
    """Get authenticated user's travel search history"""
    async with async_session() as session:
        result = await session.execute(
            select(TravelHistory)
            .where(TravelHistory.user_id == current_user["user_id"])
            .order_by(TravelHistory.searched_at.desc())
            .limit(50)
        )
        history = result.scalars().all()

        return [
            TravelHistoryResponse(
                id=h.id,
                origin_iata=h.origin_iata,
                destination_iata=h.destination_iata,
                destination_city=h.destination_city,
                duration_days=h.duration_days,
                query_text=h.query_text,
                searched_at=h.searched_at.isoformat(),
            )
            for h in history
        ]


# ==================== NLP + PERSONALIZATION ENDPOINTS ====================

@app.post("/nlp-parse")
async def nlp_parse(request: NLPParseRequest):
    """Parse natural language travel query into structured intent."""
    try:
        result = extract_travel_intent(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP parse error: {str(e)}")


@app.get("/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """Check if user has completed personalization onboarding."""
    async with async_session() as session:
        pref_result = await session.execute(
            select(UserPreferences)
            .where(UserPreferences.user_id == current_user["user_id"])
        )
        prefs = pref_result.scalar_one_or_none()

        return {
            "onboarding_completed": prefs.onboarding_completed if prefs else False,
            "has_preferences": prefs is not None,
            "has_travel_history": False,  # filled below
        }


@app.post("/save-preferences")
async def save_preferences(
    request: SavePreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save user personalization preferences (onboarding)."""
    try:
        async with async_session() as session:
            pref_result = await session.execute(
                select(UserPreferences)
                .where(UserPreferences.user_id == current_user["user_id"])
            )
            existing = pref_result.scalar_one_or_none()

            if existing:
                if request.interests is not None:
                    existing.interests = request.interests
                if request.budget_level:
                    existing.budget_level = request.budget_level
                if request.travel_style:
                    existing.travel_style = request.travel_style
                if request.preferred_destinations is not None:
                    existing.preferred_destinations = request.preferred_destinations
                if request.travel_companions:
                    existing.travel_companions = request.travel_companions
                if request.accommodation_preference:
                    existing.accommodation_preference = request.accommodation_preference
                existing.onboarding_completed = True
            else:
                new_prefs = UserPreferences(
                    user_id=current_user["user_id"],
                    interests=request.interests or [],
                    budget_level=request.budget_level or "moderate",
                    travel_style=request.travel_style or "mixed",
                    preferred_destinations=request.preferred_destinations or [],
                    travel_companions=request.travel_companions,
                    accommodation_preference=request.accommodation_preference or "hotel",
                    onboarding_completed=True,
                )
                session.add(new_prefs)

            await session.commit()

        return {"success": True, "message": "Preferences saved"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")


# ==================== AUTO PACKAGE ENDPOINTS ====================

@app.post("/auto-packages")
async def get_auto_packages(
    request: AutoPackageRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate AI-powered travel packages with real-time Amadeus data."""
    try:
        destination = request.destination
        destination_iata = request.destination_iata
        duration = request.duration_days
        budget = request.budget_inr

        # If natural language query provided, parse it first
        if request.natural_language_query:
            nlp_result = extract_travel_intent(request.natural_language_query)
            if nlp_result.get("success"):
                if not destination and nlp_result.get("destination"):
                    destination = nlp_result["destination"]
                if not destination_iata and nlp_result.get("destination_iata"):
                    destination_iata = nlp_result["destination_iata"]
                if nlp_result.get("duration_days"):
                    duration = nlp_result["duration_days"]
                if nlp_result.get("budget_inr"):
                    budget = nlp_result["budget_inr"]
                # Merge NLP-extracted preferences
                if nlp_result.get("interests") and not request.preferences.interests:
                    request.preferences.interests = nlp_result["interests"]
                if nlp_result.get("travel_style") and request.preferences.travel_style == "mixed":
                    request.preferences.travel_style = nlp_result["travel_style"]

        # Fetch user's travel history from DB
        async with async_session() as session:
            result = await session.execute(
                select(TravelHistory)
                .where(TravelHistory.user_id == current_user["user_id"])
                .order_by(TravelHistory.searched_at.desc())
                .limit(10)
            )
            history_rows = result.scalars().all()

            # Fetch user preferences
            pref_result = await session.execute(
                select(UserPreferences)
                .where(UserPreferences.user_id == current_user["user_id"])
            )
            user_prefs = pref_result.scalar_one_or_none()

            # Get user's home airport
            user_result = await session.execute(
                select(User).where(User.id == current_user["user_id"])
            )
            user = user_result.scalar_one_or_none()

        # Convert DB rows to dicts
        history_dicts = [
            {
                "origin_iata": h.origin_iata,
                "destination_iata": h.destination_iata,
                "destination_city": h.destination_city,
                "duration_days": h.duration_days,
                "searched_at": h.searched_at.isoformat() if h.searched_at else None,
            }
            for h in history_rows
        ]

        # Merge DB preferences with request preferences
        preferences = {
            "interests": request.preferences.interests or (user_prefs.interests if user_prefs else []),
            "budget_level": request.preferences.budget_level or (user_prefs.budget_level if user_prefs else "moderate"),
            "travel_style": request.preferences.travel_style or (user_prefs.travel_style if user_prefs else "mixed"),
            "travel_companions": (user_prefs.travel_companions if user_prefs else None),
            "accommodation_preference": (user_prefs.accommodation_preference if user_prefs else "hotel"),
        }

        origin = user.home_airport if user and user.home_airport else "BOM"

        # Generate packages with real Amadeus data
        pkg_result = generate_packages(
            travel_history=history_dicts,
            preferences=preferences,
            destination=destination,
            origin_iata=origin,
            duration_days=duration,
            budget_inr=budget,
            destination_iata=destination_iata,
        )

        # Save preferences if provided
        if request.preferences.interests:
            async with async_session() as session:
                pref_result = await session.execute(
                    select(UserPreferences)
                    .where(UserPreferences.user_id == current_user["user_id"])
                )
                existing_prefs = pref_result.scalar_one_or_none()

                if existing_prefs:
                    existing_prefs.interests = request.preferences.interests
                    existing_prefs.budget_level = request.preferences.budget_level or existing_prefs.budget_level
                    existing_prefs.travel_style = request.preferences.travel_style or existing_prefs.travel_style
                else:
                    new_prefs = UserPreferences(
                        user_id=current_user["user_id"],
                        interests=request.preferences.interests,
                        budget_level=request.preferences.budget_level or "moderate",
                        travel_style=request.preferences.travel_style or "mixed",
                    )
                    session.add(new_prefs)

                await session.commit()

        return pkg_result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating packages: {str(e)}"
        )


# ==================== EXISTING ENDPOINTS ====================

@app.get("/")
async def root():
    """API Health check"""
    return {
        "status": "online",
        "service": "FlightAI API",
        "version": "3.0.0",
        "endpoints": [
            "/airports",
            "/extract-trip",
            "/search-flights",
            "/airline-info/{code}",
            "/auth/signup",
            "/auth/login",
            "/auth/me",
            "/travel-history",
            "/auto-packages",
            "/nlp-parse",
            "/onboarding-status",
            "/save-preferences",
        ]
    }

@app.get("/airports", response_model=List[AirportInfo])
async def get_airports():
    """Get list of available Indian airports"""
    try:
        airports_raw = get_indian_airports_list()
        airport_list = []

        for airport_dict in airports_raw:
            try:
                iata_code = airport_dict.get("code", "").strip().upper()
                label = airport_dict.get("label", "")

                if not iata_code or len(iata_code) != 3:
                    continue

                if " - " in label:
                    city_part = label.split(" - ")[0]
                    name_part = label.split(" - ")[1] if len(label.split(" - ")) > 1 else ""

                    if "(" in city_part:
                        city_name = city_part.split("(")[0].strip()
                    else:
                        city_name = city_part.strip()

                    full_name = name_part.strip() if name_part else city_name
                else:
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
    """Extract trip details from natural language query using AI"""
    try:
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

        duration_result = get_trip_dates(
            request.origin_iata,
            request.user_query,
            fallback_days=request.fallback_days
        )

        airports = get_indian_airports_list()
        origin_city = ""
        for airport_dict in airports:
            if airport_dict.get("code") == request.origin_iata:
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
async def search_flights(request: FlightSearchRequest, http_request: Request):
    """Search for real-time flight offers. Auto-saves to history if authenticated."""
    try:
        if not amadeus_searcher:
            raise HTTPException(
                status_code=503,
                detail="Flight search service unavailable. Check Amadeus credentials."
            )

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

        # Apply client-side max stops filter
        if request.max_stops is not None and result.get('success') and result.get('flights'):
            filtered_flights = []
            for flight in result['flights']:
                outbound_stops = flight['outbound']['stops']
                return_stops = flight.get('return', {}).get('stops', 0)
                if outbound_stops <= request.max_stops and return_stops <= request.max_stops:
                    filtered_flights.append(flight)
            result['flights'] = filtered_flights
            result['total_offers'] = len(filtered_flights)

        # Auto-save to travel history if user is authenticated
        user = get_optional_user(http_request)
        if user and result.get('success'):
            try:
                async with async_session() as session:
                    history_entry = TravelHistory(
                        user_id=user["user_id"],
                        origin_iata=request.origin,
                        destination_iata=request.destination,
                        destination_city=None,
                        duration_days=None,
                        query_text=None,
                        searched_at=datetime.utcnow(),
                    )
                    session.add(history_entry)
                    await session.commit()
            except Exception as save_err:
                print(f"Non-critical: Failed to save travel history: {save_err}")

        return result

    except HTTPException:
        raise
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
        "anthropic_configured": os.getenv("ANTHROPIC_API_KEY") is not None,
        "database_url_set": os.getenv("DATABASE_URL") is not None,
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
