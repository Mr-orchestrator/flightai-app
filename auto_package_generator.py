"""
Auto Package Generator with Deterministic Pipeline
Architecture: Amadeus → Normalize → Tier Builder → LLM Narrative → Validator

LLM role: narrative text ONLY (names, taglines, itineraries, highlights).
LLM does NOT select flights/hotels, compute prices, or assign tiers.
"""

import os
import json
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

# Claude API (primary)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

# Gemini API (fallback)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from amadeus_flights import AmadeusFlightSearch, CITY_COORDINATES, get_airline_name
from package_pipeline import (
    normalize_amadeus_data, build_tiers, validate_llm_response,
    NormalizedData, TierSelection,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL_CANDIDATES = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]

# ==================== REAL-TIME DATA FETCHING ====================


def _fetch_real_flights(amadeus: AmadeusFlightSearch, origin: str, destination: str,
                        departure_date: str, return_date: str, adults: int = 1) -> dict:
    """Fetch real flight offers from Amadeus for multiple cabin classes."""
    flights_data = {"economy": [], "business": [], "all": []}
    errors = []

    for cabin in ["ECONOMY", "BUSINESS"]:
        try:
            result = amadeus.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                max_results=5,
                currency="INR",
                travel_class=cabin,
            )
            if result.get('success') and result.get('flights'):
                key = cabin.lower()
                for f in result['flights']:
                    flight_summary = {
                        "price_inr": float(f['price'].get('total', 0)),
                        "carrier": f['outbound'].get('carrier', ''),
                        "airline_name": get_airline_name(f['outbound'].get('carrier', '')),
                        "flight_number": f"{f['outbound'].get('carrier', '')}{f['outbound'].get('flight_number', '')}",
                        "cabin": cabin,
                        "stops": f['outbound'].get('stops', 0),
                        "duration": f['outbound'].get('duration', ''),
                        "departure_time": f['outbound']['departure'].get('time', ''),
                        "arrival_time": f['outbound']['arrival'].get('time', ''),
                        "data_source": "amadeus",
                        "offer_id": f.get("id"),  # Amadeus offer ID for booking
                    }
                    flights_data[key].append(flight_summary)
                    flights_data["all"].append(flight_summary)
        except Exception as e:
            errors.append(f"{cabin}: {str(e)}")

    return {
        "flights": flights_data,
        "total": len(flights_data["all"]),
        "errors": errors,
    }


def _fetch_real_hotels(amadeus: AmadeusFlightSearch, city_code: str,
                       check_in: str, check_out: str, adults: int = 1) -> dict:
    """Fetch real hotel data from Amadeus."""
    try:
        result = amadeus.search_hotels_by_city(
            city_code=city_code,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            ratings=[3, 4, 5],
            currency="INR",
            max_hotels=15,
        )
        if result.get('success') and result.get('hotels'):
            hotels = []
            for h in result['hotels']:
                hotels.append({
                    "hotel_id": h.get("hotel_id", ""),
                    "name": h['name'],
                    "star_rating": h.get('star_rating'),
                    "price_per_night_inr": h.get('price_per_night', 0),
                    "price_total_inr": h.get('price_total', 0),
                    "currency": h.get('currency', 'INR'),
                    "room_type": h.get('room_type', 'STANDARD'),
                    "nights": h.get('nights', 1),
                    "data_source": h.get("data_source", "amadeus"),
                })
            return {"hotels": hotels, "total": len(hotels), "error": None}
        return {"hotels": [], "total": 0, "error": result.get('error', 'No hotels found')}
    except Exception as e:
        return {"hotels": [], "total": 0, "error": str(e)}


def _fetch_real_activities(amadeus: AmadeusFlightSearch, iata_code: str) -> dict:
    """Fetch real activities/tours from Amadeus."""
    coords = amadeus.get_city_coordinates_with_fallback(iata_code)
    if not coords:
        return {"activities": [], "total": 0, "error": f"No coordinates for {iata_code}"}

    try:
        result = amadeus.search_activities(
            latitude=coords['lat'],
            longitude=coords['lon'],
            radius=20,
        )
        if result.get('success') and result.get('activities'):
            activities = []
            for a in result['activities']:
                activities.append({
                    "id": a.get("id"),
                    "name": a['name'],
                    "description": a.get('description', ''),
                    "price": a.get('price'),
                    "currency": a.get('currency', 'USD'),
                    "rating": a.get('rating'),
                    "category": a.get('category'),
                    "data_source": "amadeus",
                })
            return {"activities": activities, "total": len(activities), "error": None}
        return {"activities": [], "total": 0, "error": result.get('error', 'No activities found')}
    except Exception as e:
        return {"activities": [], "total": 0, "error": str(e)}


# ==================== LLM NARRATIVE PROMPT ====================

SYSTEM_PROMPT_NARRATIVE = """You are a premium travel copywriter. You receive 3 pre-built travel packages with selected flights, hotels, and activities. Your job is ONLY to write compelling narrative content. DO NOT change any selections or prices.

For each package, write:
1. A creative "name" for the package
2. A compelling "tagline" (one sentence)
3. A "daily_itinerary" — organize the provided activities across the trip days
4. An "inclusions" list (what's included based on the selected items)
5. A "highlights" list (3-4 selling points)

RETURN ONLY a JSON object:
{
  "packages": [
    {
      "tier": "budget" | "standard" | "premium",
      "name": "<creative package name>",
      "tagline": "<one-line description>",
      "daily_itinerary": [
        {
          "day": 1,
          "title": "<day title>",
          "activities": [
            {
              "time": "morning" | "afternoon" | "evening",
              "activity": "<use activity names from the PROVIDED list>",
              "estimated_cost_inr": <int from provided data>,
              "data_source": "amadeus" | "suggested"
            }
          ]
        }
      ],
      "inclusions": ["<string>", ...],
      "highlights": ["<string>", ...]
    }
  ],
  "personalization_note": "<explain why these packages suit this traveler>"
}

Rules:
- Create content for exactly 3 packages: budget, standard, premium
- Use ONLY the activity names provided in the SELECTED ACTIVITIES lists
- If not enough activities for all days, fill with "Free time / explore the city" marked as "suggested"
- DO NOT invent flights, hotels, or prices
- DO NOT modify any pricing
- Each day should have 2-3 activities (morning, afternoon, evening)
- Return ONLY valid JSON, no markdown fences"""


def _build_narrative_prompt(
    tier_selections: list[TierSelection],
    travel_history: list[dict],
    preferences: dict,
    destination: str,
    destination_iata: str,
    duration_days: int,
) -> str:
    """Build prompt for LLM narrative generation with pre-selected tier items."""

    # User context
    history_text = ""
    if travel_history:
        history_text = "TRAVELER'S HISTORY:\n"
        for trip in travel_history[-8:]:
            history_text += f"- {trip.get('origin_iata', '?')} to {trip.get('destination_iata', '?')}"
            if trip.get('destination_city'):
                history_text += f" ({trip['destination_city']})"
            history_text += "\n"

    pref_text = "TRAVELER'S PREFERENCES:\n"
    if preferences:
        if preferences.get("interests"):
            pref_text += f"- Interests: {', '.join(preferences['interests'])}\n"
        if preferences.get("travel_style"):
            pref_text += f"- Travel style: {preferences['travel_style']}\n"
        if preferences.get("travel_companions"):
            pref_text += f"- Traveling: {preferences['travel_companions']}\n"

    # Build per-tier item descriptions
    tiers_text = ""
    for sel in tier_selections:
        tiers_text += f"\n--- {sel.tier.upper()} TIER ---\n"
        tiers_text += f"Total budget: INR {sel.estimated_total_inr:,}\n"

        if sel.flight:
            tiers_text += (
                f"SELECTED FLIGHT: {sel.flight.airline_name} {sel.flight.flight_number} | "
                f"{sel.flight.cabin} | INR {sel.flight.total_price_inr:,.0f} | "
                f"{sel.flight.stops} stops | {sel.flight.duration}\n"
            )

        if sel.hotel:
            star = f"{sel.hotel.star_rating}-star" if sel.hotel.star_rating else ""
            tiers_text += (
                f"SELECTED HOTEL: {sel.hotel.name} | {star} | "
                f"INR {sel.hotel.price_per_night_inr:,.0f}/night\n"
            )

        if sel.activities:
            tiers_text += "SELECTED ACTIVITIES:\n"
            for act in sel.activities:
                tiers_text += f"  - {act.name}"
                if act.price_per_person_inr > 0:
                    tiers_text += f" (INR {act.price_per_person_inr:,.0f}/person)"
                tiers_text += "\n"

        if sel.limited_activity_data:
            tiers_text += "NOTE: Limited activity data available. Fill gaps with 'Free time / explore'.\n"

    prompt = f"""DESTINATION: {destination} ({destination_iata})
DURATION: {duration_days} days

{history_text}
{pref_text}

PRE-SELECTED PACKAGES (write narrative for these):
{tiers_text}

Write creative names, taglines, daily itineraries, inclusions, and highlights for each tier.
Use the selected activities to build day-by-day schedules."""

    return prompt


# ==================== LLM CALLERS ====================


def _call_claude(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str], list]:
    """Call Claude API. Returns (raw_text, model_name, errors)."""
    if not ANTHROPIC_AVAILABLE:
        return None, None, [("anthropic_missing", "anthropic library not installed")]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, None, [("no_api_key", "ANTHROPIC_API_KEY not set")]

    errors = []
    model = "claude-sonnet-4-5-20250929"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        if response.content and len(response.content) > 0:
            text = response.content[0].text
            if text and text.strip():
                return text.strip(), model, errors

        errors.append((model, "Empty response from Claude"))
        return None, None, errors

    except Exception as e:
        errors.append((model, repr(e)))
        return None, None, errors


def _safe_extract_text(resp):
    """Extract text from Gemini response."""
    if resp is None:
        return None
    if hasattr(resp, 'text'):
        return resp.text.strip()
    try:
        if hasattr(resp, 'candidates') and resp.candidates:
            first = resp.candidates[0]
            if hasattr(first, 'content'):
                content = first.content
                if hasattr(content, 'parts') and content.parts:
                    return content.parts[0].text.strip()
    except Exception:
        pass
    return str(resp).strip()


def _call_gemini_fallback(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str], list]:
    """Fallback: call Gemini API. Returns (raw_text, model_name, errors)."""
    if not GENAI_AVAILABLE:
        return None, None, [("genai_missing", "google.generativeai not available")]

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, None, [("gemini_no_key", "GOOGLE_API_KEY not set")]

    genai.configure(api_key=api_key)

    errors = []
    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content([system_prompt, user_prompt])
            text = _safe_extract_text(resp)
            if text:
                return text, model_name, errors
        except Exception as e:
            errors.append((model_name, repr(e)))
            time.sleep(0.25)
            continue

    return None, None, errors


# ==================== MAIN ENTRY POINT ====================


def generate_packages(
    travel_history: list[dict],
    preferences: dict,
    destination: Optional[str] = None,
    origin_iata: str = "BOM",
    duration_days: int = 7,
    budget_inr: Optional[int] = None,
    destination_iata: Optional[str] = None,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
    # Pre-fetched data (for parallel/cached calls from api_server)
    prefetched_flights: Optional[dict] = None,
    prefetched_hotels: Optional[dict] = None,
    prefetched_activities: Optional[dict] = None,
) -> dict:
    """
    Generate travel packages using deterministic pipeline + AI narrative.

    Pipeline:
    1. Resolve IATA / dates
    2. Fetch Amadeus data (or use prefetched)
    3. Normalize data
    4. Build tiers (deterministic)
    5. LLM narrative generation
    6. Validate and merge
    7. Return packages

    Returns dict with success, packages, data_quality, etc.
    """
    result = {
        "success": False,
        "packages": [],
        "personalization_note": "",
        "model_used": None,
        "used_fallback": False,
        "data_quality": "estimated",
        "data_quality_detail": {},
        "error": None,
        "amadeus_data": {"flights_found": 0, "hotels_found": 0, "activities_found": 0},
        "tier_totals": {},
        "validation_warnings": [],
    }

    # --- Step 1: Resolve destination ---
    if not destination_iata and destination:
        for code, info in CITY_COORDINATES.items():
            if info['city'].lower() == destination.lower():
                destination_iata = code
                break
        if not destination_iata:
            try:
                from iata_extractor import extract_iata_from_query
                iata_result = extract_iata_from_query(destination)
                if iata_result and iata_result.get('iata_code'):
                    destination_iata = iata_result['iata_code']
            except Exception:
                pass

    if not destination_iata:
        destination_iata = "DXB"
    if not destination:
        destination = AmadeusFlightSearch.get_city_name(destination_iata)

    # --- Step 1b: Calculate dates ---
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    if not return_date:
        try:
            dep = datetime.strptime(departure_date, "%Y-%m-%d")
            return_date = (dep + timedelta(days=duration_days)).strftime("%Y-%m-%d")
        except ValueError:
            return_date = (datetime.now() + timedelta(days=8 + duration_days)).strftime("%Y-%m-%d")

    nights = duration_days

    # --- Step 2: Fetch Amadeus data (or use prefetched) ---
    if prefetched_flights is not None:
        flights_data = prefetched_flights
    else:
        flights_data = {"flights": {"economy": [], "business": [], "all": []}, "total": 0, "errors": []}

    if prefetched_hotels is not None:
        hotels_data = prefetched_hotels
    else:
        hotels_data = {"hotels": [], "total": 0, "error": None}

    if prefetched_activities is not None:
        activities_data = prefetched_activities
    else:
        activities_data = {"activities": [], "total": 0, "error": None}

    # Fetch if not prefetched and credentials available
    amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if amadeus_client_id and amadeus_client_secret and prefetched_flights is None:
        amadeus = AmadeusFlightSearch()
        flights_data = _fetch_real_flights(amadeus, origin_iata, destination_iata, departure_date, return_date)
        hotels_data = _fetch_real_hotels(amadeus, destination_iata, departure_date, return_date)
        activities_data = _fetch_real_activities(amadeus, destination_iata)

    result["amadeus_data"] = {
        "flights_found": flights_data.get("total", 0),
        "hotels_found": hotels_data.get("total", 0),
        "activities_found": activities_data.get("total", 0),
    }

    # --- Step 3: Normalize ---
    normalized = normalize_amadeus_data(
        flights_data, hotels_data, activities_data,
        nights=nights, adults=1,
    )
    result["data_quality"] = normalized.data_quality.get("overall", "estimated")
    result["data_quality_detail"] = normalized.data_quality

    # --- Step 4: Build tiers (deterministic) ---
    tier_selections = build_tiers(
        normalized, nights=nights, adults=1,
        budget_inr=budget_inr, preferences=preferences,
    )

    result["tier_totals"] = {
        t.tier: t.estimated_total_inr for t in tier_selections
    }

    # --- Step 5: LLM narrative ---
    narrative_prompt = _build_narrative_prompt(
        tier_selections, travel_history, preferences,
        destination, destination_iata, duration_days,
    )

    raw_text, model_used, claude_errors = _call_claude(SYSTEM_PROMPT_NARRATIVE, narrative_prompt)

    if not raw_text:
        raw_text, model_used, gemini_errors = _call_gemini_fallback(SYSTEM_PROMPT_NARRATIVE, narrative_prompt)
        all_errors = claude_errors + gemini_errors
    else:
        all_errors = claude_errors

    result["model_used"] = model_used

    # Parse LLM JSON
    llm_json = {}
    if raw_text:
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1:
                llm_json = json.loads(raw_text[start:end + 1])
        except json.JSONDecodeError as e:
            logger.warning(f"LLM JSON parse error: {e}")

    # --- Step 6: Validate and merge ---
    validation = validate_llm_response(
        llm_json, tier_selections, destination, destination_iata, duration_days,
    )

    result["validation_warnings"] = validation.warnings

    if validation.corrected_packages:
        # Set data quality detail on each package
        for pkg in validation.corrected_packages:
            pkg["data_quality_detail"] = normalized.data_quality

        result["success"] = True
        result["packages"] = validation.corrected_packages
        result["personalization_note"] = llm_json.get("personalization_note", "")

        if not model_used:
            result["used_fallback"] = True
            result["personalization_note"] = "Packages generated with deterministic engine (AI narrative unavailable)"
    else:
        result["error"] = f"Pipeline failed. LLM errors: {all_errors}"
        result["used_fallback"] = True

    return result
