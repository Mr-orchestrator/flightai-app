"""
Auto Package Generator with Real-Time Amadeus Data
Fetches real flights, hotels, and activities from Amadeus APIs,
then uses Claude/Gemini to curate them into personalized 3-tier packages.
"""

import os
import json
import time
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
                    "name": h['name'],
                    "star_rating": h.get('star_rating'),
                    "price_per_night_inr": h.get('price_per_night', 0),
                    "price_total_inr": h.get('price_total', 0),
                    "currency": h.get('currency', 'INR'),
                    "room_type": h.get('room_type', 'STANDARD'),
                    "nights": h.get('nights', 1),
                    "data_source": "amadeus",
                })
            return {"hotels": hotels, "total": len(hotels), "error": None}
        return {"hotels": [], "total": 0, "error": result.get('error', 'No hotels found')}
    except Exception as e:
        return {"hotels": [], "total": 0, "error": str(e)}


def _fetch_real_activities(amadeus: AmadeusFlightSearch, iata_code: str) -> dict:
    """Fetch real activities/tours from Amadeus."""
    coords = AmadeusFlightSearch.get_city_coordinates(iata_code)
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


# ==================== LLM PROMPTS ====================

SYSTEM_PROMPT_REALTIME = """You are a premium travel package curator for an Indian travel platform. You are given REAL available flights, hotels, and activities from our booking system. Your job is to SELECT from these real options and organize them into 3 travel packages at different budget tiers.

RETURN ONLY a JSON object with this exact structure:
{
  "packages": [
    {
      "tier": "budget" | "standard" | "premium",
      "name": "<creative package name>",
      "tagline": "<one-line description>",
      "destination_city": "<city name>",
      "destination_iata": "<3-letter IATA code>",
      "duration_days": <int>,
      "estimated_total_inr": <int>,
      "hotel": {
        "name": "<hotel name from the AVAILABLE HOTELS list>",
        "star_rating": <int 1-5>,
        "price_per_night_inr": <int>,
        "area": "<neighborhood/area>",
        "data_source": "amadeus" | "estimated"
      },
      "flights": {
        "airline_name": "<airline name from AVAILABLE FLIGHTS>",
        "flight_number": "<flight number>",
        "travel_class": "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS",
        "price_inr": <int>,
        "stops": <int>,
        "duration": "<duration string>",
        "data_source": "amadeus" | "estimated"
      },
      "daily_itinerary": [
        {
          "day": <int>,
          "title": "<day title>",
          "activities": [
            {
              "time": "morning" | "afternoon" | "evening",
              "activity": "<activity name - use REAL activities from list when available>",
              "estimated_cost_inr": <int>,
              "data_source": "amadeus" | "suggested"
            }
          ]
        }
      ],
      "inclusions": ["<string>", ...],
      "highlights": ["<string>", ...]
    }
  ],
  "personalization_note": "<explain why these packages suit this traveler>",
  "data_quality": "full_realtime" | "partial_realtime" | "estimated"
}

Rules:
- Create exactly 3 packages: one budget, one standard, one premium
- USE REAL DATA from the provided lists wherever possible
- For budget tier: pick cheapest flights (economy) and cheapest hotels
- For standard tier: pick mid-range flights and 4-star hotels
- For premium tier: pick business class flights and most expensive hotels
- If real hotels/activities are not available, you may suggest realistic ones but mark data_source as "estimated" or "suggested"
- All prices in INR (Indian Rupees)
- Daily itinerary must cover ALL days. Use REAL activities from the list, supplement with suggestions if needed
- Each day should have 2-3 activities (morning, afternoon, evening)
- Return ONLY valid JSON, no markdown fences, no commentary outside the JSON"""


def _build_realtime_prompt(
    travel_history: list[dict],
    preferences: dict,
    destination: str,
    destination_iata: str,
    origin_iata: str,
    duration_days: int,
    budget_inr: Optional[int],
    flights_data: dict,
    hotels_data: dict,
    activities_data: dict,
) -> str:
    """Build the user prompt with real Amadeus data + user context."""

    # Build history context
    history_text = ""
    if travel_history:
        history_text = "TRAVELER'S HISTORY:\n"
        for trip in travel_history[-8:]:
            history_text += f"- {trip.get('origin_iata', '?')} to {trip.get('destination_iata', '?')}"
            if trip.get('destination_city'):
                history_text += f" ({trip['destination_city']})"
            if trip.get('duration_days'):
                history_text += f", {trip['duration_days']} days"
            history_text += "\n"

    # Build preferences context
    pref_text = "TRAVELER'S PREFERENCES:\n"
    if preferences:
        if preferences.get("interests"):
            interests = preferences["interests"]
            if isinstance(interests, list):
                pref_text += f"- Interests: {', '.join(interests)}\n"
        if preferences.get("budget_level"):
            pref_text += f"- Budget level: {preferences['budget_level']}\n"
        if preferences.get("travel_style"):
            pref_text += f"- Travel style: {preferences['travel_style']}\n"
        if preferences.get("travel_companions"):
            pref_text += f"- Traveling: {preferences['travel_companions']}\n"
        if preferences.get("accommodation_preference"):
            pref_text += f"- Accommodation preference: {preferences['accommodation_preference']}\n"

    # Format real flights data
    flights_text = "AVAILABLE FLIGHTS (REAL-TIME FROM AMADEUS):\n"
    if flights_data.get("total", 0) > 0:
        for f in flights_data["flights"]["all"][:10]:
            flights_text += (
                f"- {f['airline_name']} {f['flight_number']} | {f['cabin']} | "
                f"INR {f['price_inr']:,.0f} | {f['stops']} stops | {f.get('duration', 'N/A')}\n"
            )
    else:
        flights_text += "- No real-time flight data available. Use estimated prices.\n"

    # Format real hotels data
    hotels_text = "AVAILABLE HOTELS (REAL-TIME FROM AMADEUS):\n"
    if hotels_data.get("total", 0) > 0:
        for h in hotels_data["hotels"][:15]:
            star = f"{h['star_rating']}-star" if h.get('star_rating') else "unrated"
            flights_text_price = h.get('price_per_night_inr', 0)
            hotels_text += f"- {h['name']} | {star} | INR {flights_text_price:,.0f}/night\n"
    else:
        hotels_text += "- No real-time hotel data available. Suggest realistic hotels with estimated prices.\n"

    # Format real activities data
    activities_text = "AVAILABLE ACTIVITIES & TOURS (REAL-TIME FROM AMADEUS):\n"
    if activities_data.get("total", 0) > 0:
        for a in activities_data["activities"][:20]:
            price_str = f"{a['currency']} {a['price']}" if a.get('price') else "Free/TBD"
            activities_text += f"- {a['name']}: {a.get('description', '')[:80]}... | {price_str}\n"
    else:
        activities_text += f"- No real-time activity data. Suggest popular activities for {destination}.\n"

    prompt = f"""TRIP DETAILS:
- Origin: {origin_iata}
- Destination: {destination} ({destination_iata})
- Duration: {duration_days} days
{"- Budget cap: INR " + f"{budget_inr:,}" if budget_inr else "- No specific budget constraint"}

{history_text}
{pref_text}

{flights_text}

{hotels_text}

{activities_text}

Create 3 personalized travel packages (budget / standard / premium) using the REAL data above.
Select actual flights, hotels, and activities from the lists. Only invent data if real options are not available."""

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


# ==================== FALLBACK TEMPLATES ====================


def _generate_fallback_packages(
    destination: str, destination_iata: str, origin_iata: str,
    days: int, budget_inr: Optional[int] = None
) -> list[dict]:
    """Generate static template packages when both LLMs and Amadeus fail."""
    base_flight = 15000

    tiers = [
        {
            "tier": "budget",
            "name": f"Essential {destination}",
            "tagline": f"Explore {destination} without breaking the bank",
            "destination_city": destination,
            "destination_iata": destination_iata,
            "duration_days": days,
            "estimated_total_inr": base_flight + (3000 * days) + (2000 * days),
            "hotel": {
                "name": "Comfort Inn", "star_rating": 3,
                "price_per_night_inr": 3000, "area": "City Center",
                "data_source": "estimated"
            },
            "flights": {
                "airline_name": "IndiGo", "flight_number": "6E-XXX",
                "travel_class": "ECONOMY", "price_inr": base_flight,
                "stops": 0, "duration": "PT3H", "data_source": "estimated"
            },
            "daily_itinerary": [
                {
                    "day": d + 1, "title": f"Day {d + 1} - Explore",
                    "activities": [
                        {"time": "morning", "activity": "Visit local market and sightseeing", "estimated_cost_inr": 500, "data_source": "suggested"},
                        {"time": "afternoon", "activity": "Explore historical landmarks", "estimated_cost_inr": 800, "data_source": "suggested"},
                        {"time": "evening", "activity": "Local dining experience", "estimated_cost_inr": 1000, "data_source": "suggested"},
                    ]
                } for d in range(days)
            ],
            "inclusions": ["Round-trip economy flights", f"{days} nights at 3-star hotel", "Daily breakfast"],
            "highlights": ["Budget-friendly", "Local experiences", "Flexible itinerary"],
        },
        {
            "tier": "standard",
            "name": f"Classic {destination}",
            "tagline": "The perfect balance of comfort and value",
            "destination_city": destination,
            "destination_iata": destination_iata,
            "duration_days": days,
            "estimated_total_inr": (base_flight + 5000) + (6000 * days) + (4000 * days),
            "hotel": {
                "name": "Premium Hotel & Suites", "star_rating": 4,
                "price_per_night_inr": 6000, "area": "Premium District",
                "data_source": "estimated"
            },
            "flights": {
                "airline_name": "Air India", "flight_number": "AI-XXX",
                "travel_class": "ECONOMY", "price_inr": base_flight + 5000,
                "stops": 0, "duration": "PT3H", "data_source": "estimated"
            },
            "daily_itinerary": [
                {
                    "day": d + 1, "title": f"Day {d + 1} - Discover",
                    "activities": [
                        {"time": "morning", "activity": "Guided tour of top attractions", "estimated_cost_inr": 1500, "data_source": "suggested"},
                        {"time": "afternoon", "activity": "Cultural experience or shopping", "estimated_cost_inr": 2000, "data_source": "suggested"},
                        {"time": "evening", "activity": "Fine dining at popular restaurant", "estimated_cost_inr": 2500, "data_source": "suggested"},
                    ]
                } for d in range(days)
            ],
            "inclusions": ["Round-trip flights", f"{days} nights at 4-star hotel", "Daily breakfast", "Airport transfers"],
            "highlights": ["Comfortable stay", "Curated activities", "Great value"],
        },
        {
            "tier": "premium",
            "name": f"Luxury {destination}",
            "tagline": f"Experience {destination} in absolute luxury",
            "destination_city": destination,
            "destination_iata": destination_iata,
            "duration_days": days,
            "estimated_total_inr": (base_flight * 3) + (15000 * days) + (8000 * days),
            "hotel": {
                "name": "5-Star Grand Resort", "star_rating": 5,
                "price_per_night_inr": 15000, "area": "Premium Waterfront",
                "data_source": "estimated"
            },
            "flights": {
                "airline_name": "Emirates", "flight_number": "EK-XXX",
                "travel_class": "BUSINESS", "price_inr": base_flight * 3,
                "stops": 0, "duration": "PT3H", "data_source": "estimated"
            },
            "daily_itinerary": [
                {
                    "day": d + 1, "title": f"Day {d + 1} - Indulge",
                    "activities": [
                        {"time": "morning", "activity": "Private guided tour or spa session", "estimated_cost_inr": 3000, "data_source": "suggested"},
                        {"time": "afternoon", "activity": "Exclusive experience or luxury shopping", "estimated_cost_inr": 5000, "data_source": "suggested"},
                        {"time": "evening", "activity": "Fine dining experience", "estimated_cost_inr": 5000, "data_source": "suggested"},
                    ]
                } for d in range(days)
            ],
            "inclusions": ["Business class flights", f"{days} nights at 5-star resort", "All meals", "Private transfers", "Concierge service"],
            "highlights": ["Ultimate luxury", "Exclusive access", "Personal concierge"],
        },
    ]

    return tiers


# ==================== MAIN ENTRY POINT ====================


def generate_packages(
    travel_history: list[dict],
    preferences: dict,
    destination: Optional[str] = None,
    origin_iata: str = "BOM",
    duration_days: int = 7,
    budget_inr: Optional[int] = None,
    destination_iata: Optional[str] = None,
) -> dict:
    """
    Generate travel packages using real Amadeus data + AI curation.

    Flow:
    1. Determine destination IATA code
    2. Fetch real flights, hotels, activities from Amadeus
    3. Pass real data to Claude/Gemini for intelligent packaging
    4. Return 3 packages with real prices and data source indicators

    Returns:
        {
            "success": bool,
            "packages": [...],
            "personalization_note": str,
            "model_used": str | None,
            "used_fallback": bool,
            "data_quality": "full_realtime" | "partial_realtime" | "estimated",
            "error": str | None,
            "amadeus_data": { "flights_found": int, "hotels_found": int, "activities_found": int }
        }
    """
    result = {
        "success": False,
        "packages": [],
        "personalization_note": "",
        "model_used": None,
        "used_fallback": False,
        "data_quality": "estimated",
        "error": None,
        "amadeus_data": {"flights_found": 0, "hotels_found": 0, "activities_found": 0},
    }

    # Resolve destination IATA if not provided
    if not destination_iata and destination:
        # Try to find IATA from coordinates mapping
        for code, info in CITY_COORDINATES.items():
            if info['city'].lower() == destination.lower():
                destination_iata = code
                break
        if not destination_iata:
            # Use NLP extractor as last resort
            try:
                from iata_extractor import extract_iata_from_query
                iata_result = extract_iata_from_query(destination)
                if iata_result and iata_result.get('iata_code'):
                    destination_iata = iata_result['iata_code']
            except Exception:
                pass

    if not destination_iata:
        destination_iata = "DXB"  # Default to Dubai
    if not destination:
        destination = AmadeusFlightSearch.get_city_name(destination_iata)

    # Calculate travel dates
    departure_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=8 + duration_days)).strftime("%Y-%m-%d")

    # Initialize Amadeus client
    amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    flights_data = {"flights": {"economy": [], "business": [], "all": []}, "total": 0, "errors": []}
    hotels_data = {"hotels": [], "total": 0, "error": None}
    activities_data = {"activities": [], "total": 0, "error": None}

    if amadeus_client_id and amadeus_client_secret:
        amadeus = AmadeusFlightSearch()

        # Fetch real data from Amadeus
        flights_data = _fetch_real_flights(
            amadeus, origin_iata, destination_iata, departure_date, return_date
        )
        hotels_data = _fetch_real_hotels(
            amadeus, destination_iata, departure_date, return_date
        )
        activities_data = _fetch_real_activities(amadeus, destination_iata)

    result["amadeus_data"] = {
        "flights_found": flights_data.get("total", 0),
        "hotels_found": hotels_data.get("total", 0),
        "activities_found": activities_data.get("total", 0),
    }

    # Determine data quality
    has_flights = flights_data.get("total", 0) > 0
    has_hotels = hotels_data.get("total", 0) > 0
    has_activities = activities_data.get("total", 0) > 0

    if has_flights and has_hotels and has_activities:
        result["data_quality"] = "full_realtime"
    elif has_flights or has_hotels or has_activities:
        result["data_quality"] = "partial_realtime"
    else:
        result["data_quality"] = "estimated"

    # Build prompt with real data
    user_prompt = _build_realtime_prompt(
        travel_history, preferences, destination, destination_iata,
        origin_iata, duration_days, budget_inr,
        flights_data, hotels_data, activities_data,
    )

    # Try Claude first
    raw_text, model_used, claude_errors = _call_claude(SYSTEM_PROMPT_REALTIME, user_prompt)

    # If Claude failed, try Gemini
    if not raw_text:
        raw_text, model_used, gemini_errors = _call_gemini_fallback(SYSTEM_PROMPT_REALTIME, user_prompt)
        all_errors = claude_errors + gemini_errors
    else:
        all_errors = claude_errors

    result["model_used"] = model_used

    # Parse JSON from LLM response
    if raw_text:
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(raw_text[start:end + 1])
                packages = parsed.get("packages", [])
                if packages and isinstance(packages, list):
                    result["success"] = True
                    result["packages"] = packages
                    result["personalization_note"] = parsed.get("personalization_note", "")
                    if parsed.get("data_quality"):
                        result["data_quality"] = parsed["data_quality"]
                else:
                    result["error"] = "No packages array in response"
            else:
                result["error"] = "No JSON object found in LLM response"
        except json.JSONDecodeError as e:
            result["error"] = f"JSON parse error: {repr(e)}"
    else:
        result["error"] = f"No response from any LLM. Errors: {all_errors}"

    # Final fallback: static template packages
    if not result["success"]:
        result["used_fallback"] = True
        result["packages"] = _generate_fallback_packages(
            destination, destination_iata, origin_iata, duration_days, budget_inr
        )
        result["success"] = True
        result["data_quality"] = "estimated"
        result["personalization_note"] = "Generated using default templates (AI temporarily unavailable)"

    return result
