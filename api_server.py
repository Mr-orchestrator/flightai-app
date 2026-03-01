"""
FlightAI REST API Server
FastAPI wrapper for existing Python backend logic
Exposes endpoints for Next.js frontend
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
import uuid
import json
import asyncio
import time
import logging
from dotenv import load_dotenv

# Import existing backend modules
from core import get_trip_dates
from iata_extractor import extract_iata_from_query, get_indian_airports_list
from amadeus_flights import AmadeusFlightSearch, get_airline_name, get_airline_website

# Import new modules
from database import init_db, async_session, User, TravelHistory, UserPreferences, PackageSnapshot
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_optional_user
)
from auto_package_generator import generate_packages
from nlp_parser import extract_travel_intent
from profile_inference import resolve_all as resolve_profile

from sqlalchemy import select

logger = logging.getLogger(__name__)


# ==================== TTL CACHE ====================
# MVP in-memory cache. Replace with Redis for multi-instance deployment.

class TTLCache:
    """Simple in-memory cache with per-key TTL."""

    def __init__(self):
        self._store: dict[str, tuple[float, any]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def remaining_ttl(self, key: str) -> float:
        entry = self._store.get(key)
        if entry is None:
            return 0
        expires_at, _ = entry
        remaining = expires_at - time.time()
        return max(0, remaining)

    def set(self, key: str, value, ttl_seconds: int):
        self._store[key] = (time.time() + ttl_seconds, value)

    def clear_expired(self):
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


_cache = TTLCache()
CACHE_TTL_FLIGHTS = 900       # 15 minutes
CACHE_TTL_HOTELS = 7200       # 2 hours
CACHE_TTL_ACTIVITIES = 43200  # 12 hours

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
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
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
    budget_range_min: Optional[int] = None
    budget_range_max: Optional[int] = None
    travel_frequency: Optional[str] = None
    dietary_needs: Optional[List[str]] = None
    accessibility_needs: Optional[List[str]] = None
    preferred_airlines: Optional[List[str]] = None
    onboarding_step: Optional[int] = None

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
                if request.budget_range_min is not None:
                    existing.budget_range_min = request.budget_range_min
                if request.budget_range_max is not None:
                    existing.budget_range_max = request.budget_range_max
                if request.travel_frequency:
                    existing.travel_frequency = request.travel_frequency
                if request.dietary_needs is not None:
                    existing.dietary_needs = request.dietary_needs
                if request.accessibility_needs is not None:
                    existing.accessibility_needs = request.accessibility_needs
                if request.preferred_airlines is not None:
                    existing.preferred_airlines = request.preferred_airlines
                if request.onboarding_step is not None:
                    existing.onboarding_step = request.onboarding_step
                    if request.onboarding_step >= 5:
                        existing.onboarding_completed = True
                else:
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
                    budget_range_min=request.budget_range_min,
                    budget_range_max=request.budget_range_max,
                    travel_frequency=request.travel_frequency,
                    dietary_needs=request.dietary_needs or [],
                    accessibility_needs=request.accessibility_needs or [],
                    preferred_airlines=request.preferred_airlines or [],
                    onboarding_step=request.onboarding_step or 0,
                    onboarding_completed=request.onboarding_step is not None and request.onboarding_step >= 5,
                )
                session.add(new_prefs)

            await session.commit()

        return {"success": True, "message": "Preferences saved"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")


# ==================== AUTO PACKAGE HELPERS ====================

async def _load_user_context(user_id: str):
    """Load travel history, preferences, and user record for an authenticated user."""
    async with async_session() as session:
        result = await session.execute(
            select(TravelHistory)
            .where(TravelHistory.user_id == user_id)
            .order_by(TravelHistory.searched_at.desc())
            .limit(10)
        )
        history_rows = result.scalars().all()

        pref_result = await session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        user_prefs = pref_result.scalar_one_or_none()

        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

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

    prefs_dict = None
    if user_prefs:
        prefs_dict = {
            "interests": user_prefs.interests or [],
            "budget_level": user_prefs.budget_level,
            "travel_style": user_prefs.travel_style,
            "travel_companions": user_prefs.travel_companions,
            "accommodation_preference": user_prefs.accommodation_preference,
            "preferred_destinations": user_prefs.preferred_destinations or [],
            "preferred_airlines": user_prefs.preferred_airlines or [],
            "budget_range_min": user_prefs.budget_range_min,
            "budget_range_max": user_prefs.budget_range_max,
        }

    home_airport = user.home_airport if user else None
    return history_dicts, prefs_dict, home_airport


def _resolve_params(request: AutoPackageRequest, nlp_result: dict,
                    history_dicts: list, prefs_dict: dict, home_airport: str,
                    request_preferences: PreferencesInput):
    """Use profile intelligence to resolve all travel parameters."""
    resolved = resolve_profile(
        travel_history=history_dicts,
        nlp_intent=nlp_result if nlp_result.get("success") else {},
        user_home_airport=home_airport,
        user_prefs=prefs_dict,
        explicit_origin=None,
        explicit_destination=request.destination,
        explicit_destination_iata=request.destination_iata,
        explicit_duration=request.duration_days if request.duration_days != 7 else None,
        explicit_budget=request.budget_inr,
    )

    # Merge preferences: request > NLP > DB prefs > defaults
    interests = request_preferences.interests
    if not interests and nlp_result.get("interests"):
        interests = nlp_result["interests"]
    if not interests and prefs_dict:
        interests = prefs_dict.get("interests", [])

    travel_style = request_preferences.travel_style
    if travel_style == "mixed" and nlp_result.get("travel_style"):
        travel_style = nlp_result["travel_style"]
    if travel_style == "mixed" and prefs_dict:
        travel_style = prefs_dict.get("travel_style", "mixed")

    preferences = {
        "interests": interests or [],
        "budget_level": request_preferences.budget_level or (prefs_dict or {}).get("budget_level", "moderate"),
        "travel_style": travel_style,
        "travel_companions": (prefs_dict or {}).get("travel_companions"),
        "accommodation_preference": (prefs_dict or {}).get("accommodation_preference", "hotel"),
        "preferred_airlines": (prefs_dict or {}).get("preferred_airlines", []),
    }

    return resolved, preferences


def _make_cache_key(key_type: str, origin: str, dest: str, date: str,
                    adults: int = 1, cabin: str = "ECONOMY") -> str:
    return f"{key_type}:{origin}:{dest}:{date}:{adults}:{cabin}"


async def _save_snapshot(user_id: str, pkg_result: dict):
    """Save PackageSnapshot for each generated tier."""
    packages = pkg_result.get("packages", [])
    if not packages:
        return

    now = datetime.utcnow()
    async with async_session() as session:
        for pkg in packages:
            snapshot = PackageSnapshot(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tier=pkg.get("tier", "unknown"),
                destination_iata=pkg.get("destination_iata", ""),
                flight_offer_id=pkg.get("flight_offer_id"),
                hotel_offer_id=pkg.get("hotel_offer_id"),
                activity_ids=pkg.get("activity_ids", []),
                flight_price_inr=pkg.get("flight_price_inr"),
                hotel_total_inr=pkg.get("hotel_total_inr"),
                total_package_inr=pkg.get("estimated_total_inr"),
                fx_rate_used=pkg.get("fx_rate_used"),
                created_at=now,
                flight_expires_at=now + timedelta(minutes=15),
                hotel_expires_at=now + timedelta(hours=2),
            )
            session.add(snapshot)
        await session.commit()


# ==================== AUTO PACKAGE ENDPOINTS ====================

@app.post("/auto-packages")
async def get_auto_packages(
    request: AutoPackageRequest,
    current_user: dict = Depends(get_optional_user),
):
    """Generate AI-powered travel packages with real-time Amadeus data (non-streaming)."""
    try:
        # Parse NLP query
        nlp_result = {}
        if request.natural_language_query:
            nlp_result = extract_travel_intent(request.natural_language_query)

        # Load user context
        history_dicts, prefs_dict, home_airport = [], None, None
        if current_user:
            history_dicts, prefs_dict, home_airport = await _load_user_context(
                current_user["user_id"]
            )

        # Profile intelligence resolution
        resolved, preferences = _resolve_params(
            request, nlp_result, history_dicts, prefs_dict, home_airport,
            request.preferences,
        )

        origin = resolved["origin_iata"]
        destination = resolved["destination"]
        destination_iata = resolved["destination_iata"]
        duration = resolved["duration_days"]
        budget = resolved["budget_inr"]

        # Generate packages (blocking call via thread)
        pkg_result = await asyncio.to_thread(
            generate_packages,
            travel_history=history_dicts,
            preferences=preferences,
            destination=destination,
            origin_iata=origin,
            duration_days=duration,
            budget_inr=budget,
            destination_iata=destination_iata,
        )

        # Add inference log to response
        pkg_result["inference_log"] = resolved.get("inference_log", {})

        # Save snapshot if authenticated
        if current_user:
            try:
                await _save_snapshot(current_user["user_id"], pkg_result)
            except Exception as snap_err:
                logger.warning(f"Non-critical: snapshot save failed: {snap_err}")

        return pkg_result

    except Exception as e:
        logger.exception("Error generating packages")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating packages: {str(e)}"
        )


@app.post("/auto-packages-stream")
async def get_auto_packages_stream(
    request: AutoPackageRequest,
    current_user: dict = Depends(get_optional_user),
):
    """Generate travel packages with SSE progress updates."""

    async def event_stream():
        def send_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        try:
            # Step 1: NLP parsing
            yield send_event("progress", {
                "step": "nlp", "message": "Parsing your request...", "percent": 5
            })

            nlp_result = {}
            if request.natural_language_query:
                nlp_result = await asyncio.to_thread(
                    extract_travel_intent, request.natural_language_query
                )

            yield send_event("progress", {
                "step": "nlp", "message": "Request parsed", "percent": 10
            })

            # Step 2: Load user context + profile intelligence
            yield send_event("progress", {
                "step": "profile", "message": "Loading your profile...", "percent": 15
            })

            history_dicts, prefs_dict, home_airport = [], None, None
            if current_user:
                history_dicts, prefs_dict, home_airport = await _load_user_context(
                    current_user["user_id"]
                )

            resolved, preferences = _resolve_params(
                request, nlp_result, history_dicts, prefs_dict, home_airport,
                request.preferences,
            )

            origin = resolved["origin_iata"]
            destination = resolved["destination"]
            destination_iata = resolved["destination_iata"]
            duration = resolved["duration_days"]
            budget = resolved["budget_inr"]

            yield send_event("progress", {
                "step": "profile",
                "message": f"Resolved: {origin} → {destination_iata or destination}",
                "percent": 20
            })

            if not destination_iata:
                yield send_event("error", {
                    "message": "Could not determine destination. Please be more specific."
                })
                return

            # Step 3: Parallel Amadeus data fetch (with cache)
            dep_date = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d")
            ret_date = (datetime.utcnow() + timedelta(days=14 + duration)).strftime("%Y-%m-%d")

            flight_key = _make_cache_key("flights", origin, destination_iata, dep_date)
            hotel_key = _make_cache_key("hotels", destination_iata, destination_iata, dep_date)
            activity_key = _make_cache_key("activities", destination_iata, destination_iata, dep_date)

            cached_flights = _cache.get(flight_key)
            cached_hotels = _cache.get(hotel_key)
            cached_activities = _cache.get(activity_key)

            # Import fetch functions from auto_package_generator
            from auto_package_generator import (
                _fetch_real_flights, _fetch_real_hotels, _fetch_real_activities
            )

            # Create Amadeus client for parallel fetches
            _amadeus = AmadeusFlightSearch() if amadeus_searcher else None

            flights_data, hotels_data, activities_data = None, None, None

            async def fetch_flights():
                nonlocal flights_data
                if cached_flights:
                    flights_data = cached_flights
                    return
                if not _amadeus:
                    flights_data = {"flights": {"economy": [], "business": [], "all": []}, "total": 0, "errors": []}
                    return
                flights_data = await asyncio.to_thread(
                    _fetch_real_flights, _amadeus, origin, destination_iata, dep_date, ret_date, 1
                )
                if flights_data and flights_data.get("total", 0) > 0:
                    _cache.set(flight_key, flights_data, CACHE_TTL_FLIGHTS)

            async def fetch_hotels():
                nonlocal hotels_data
                if cached_hotels:
                    hotels_data = cached_hotels
                    return
                if not _amadeus:
                    hotels_data = {"hotels": [], "total": 0, "error": None}
                    return
                hotels_data = await asyncio.to_thread(
                    _fetch_real_hotels, _amadeus, destination_iata, dep_date, ret_date, 1
                )
                if hotels_data and hotels_data.get("total", 0) > 0:
                    _cache.set(hotel_key, hotels_data, CACHE_TTL_HOTELS)

            async def fetch_activities():
                nonlocal activities_data
                if cached_activities:
                    activities_data = cached_activities
                    return
                if not _amadeus:
                    activities_data = {"activities": [], "total": 0, "error": None}
                    return
                activities_data = await asyncio.to_thread(
                    _fetch_real_activities, _amadeus, destination_iata
                )
                if activities_data and activities_data.get("total", 0) > 0:
                    _cache.set(activity_key, activities_data, CACHE_TTL_ACTIVITIES)

            yield send_event("progress", {
                "step": "flights", "message": "Searching flights...", "percent": 25
            })

            # Run all 3 fetches in parallel with individual timeouts
            flight_task = asyncio.create_task(fetch_flights())
            hotel_task = asyncio.create_task(fetch_hotels())
            activity_task = asyncio.create_task(fetch_activities())

            # Wait for flights first (usually fastest to resolve UX)
            try:
                await asyncio.wait_for(flight_task, timeout=15)
            except asyncio.TimeoutError:
                logger.warning("Flight fetch timed out")
                flights_data = {"flights": {"economy": [], "business": [], "all": []}, "total": 0, "errors": ["timeout"]}

            flight_count = flights_data.get("total", 0) if isinstance(flights_data, dict) else 0
            yield send_event("progress", {
                "step": "flights",
                "message": f"Found {flight_count} flights" + (" (cached)" if cached_flights else ""),
                "percent": 40
            })

            yield send_event("progress", {
                "step": "hotels", "message": "Searching hotels...", "percent": 45
            })

            try:
                await asyncio.wait_for(hotel_task, timeout=15)
            except asyncio.TimeoutError:
                logger.warning("Hotel fetch timed out")
                hotels_data = {"hotels": [], "total": 0, "error": "timeout"}

            hotel_count = hotels_data.get("total", 0) if isinstance(hotels_data, dict) else 0
            yield send_event("progress", {
                "step": "hotels",
                "message": f"Found {hotel_count} hotels" + (" (cached)" if cached_hotels else ""),
                "percent": 55
            })

            yield send_event("progress", {
                "step": "activities", "message": "Finding activities...", "percent": 60
            })

            try:
                await asyncio.wait_for(activity_task, timeout=15)
            except asyncio.TimeoutError:
                logger.warning("Activity fetch timed out")
                activities_data = {"activities": [], "total": 0, "error": "timeout"}

            activity_count = activities_data.get("total", 0) if isinstance(activities_data, dict) else 0
            yield send_event("progress", {
                "step": "activities",
                "message": f"Found {activity_count} activities" + (" (cached)" if cached_activities else ""),
                "percent": 70
            })

            # Step 4: Generate packages (normalize + tier build + LLM narrative + validate)
            yield send_event("progress", {
                "step": "ai", "message": "AI curating your packages...", "percent": 75
            })

            pkg_result = await asyncio.to_thread(
                generate_packages,
                travel_history=history_dicts,
                preferences=preferences,
                destination=destination,
                origin_iata=origin,
                duration_days=duration,
                budget_inr=budget,
                destination_iata=destination_iata,
                prefetched_flights=flights_data,
                prefetched_hotels=hotels_data,
                prefetched_activities=activities_data,
            )

            yield send_event("progress", {
                "step": "validate", "message": "Validating packages...", "percent": 95
            })

            # Add inference log
            pkg_result["inference_log"] = resolved.get("inference_log", {})

            # Save snapshot
            if current_user:
                try:
                    await _save_snapshot(current_user["user_id"], pkg_result)
                except Exception as snap_err:
                    logger.warning(f"Snapshot save failed: {snap_err}")

            yield send_event("progress", {
                "step": "done", "message": "Packages ready!", "percent": 100
            })

            yield send_event("complete", pkg_result)

        except Exception as e:
            logger.exception("SSE stream error")
            yield send_event("error", {
                "message": f"Error generating packages: {str(e)}"
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
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
