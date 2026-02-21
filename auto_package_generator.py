"""
Auto Package Generator using Claude AI (with Gemini fallback)
Generates personalized travel packages: flights + hotels + activities + day-by-day itinerary
"""

import os
import json
import time
from typing import Optional

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

# Gemini model candidates (reused from core.py / iata_extractor.py)
GEMINI_MODEL_CANDIDATES = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]

SYSTEM_PROMPT_PACKAGES = """You are a premium travel package designer for an Indian travel platform. Given the user's travel history, preferences, and desired destination, create 3 travel packages at different budget tiers.

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
        "name": "<realistic hotel name>",
        "star_rating": <int 1-5>,
        "price_per_night_inr": <int>,
        "area": "<neighborhood/area>"
      },
      "flights": {
        "travel_class": "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS",
        "estimated_price_inr": <int>
      },
      "daily_itinerary": [
        {
          "day": <int>,
          "title": "<day title>",
          "activities": [
            {
              "time": "morning" | "afternoon" | "evening",
              "activity": "<specific activity with location>",
              "estimated_cost_inr": <int>
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
- Create exactly 3 packages: one budget, one standard, one premium
- All prices in INR (Indian Rupees)
- Daily itinerary must cover ALL days of the trip
- Each day should have 2-3 activities (morning, afternoon, evening)
- Activities should be real, specific places/experiences at the destination
- If travel history shows preferences (beach, adventure, culture), lean into those
- Budget tier: 3-star hotels, economy flights, free/cheap activities
- Standard tier: 4-star hotels, economy or premium economy, balanced activities
- Premium tier: 5-star hotels, business class, exclusive experiences
- Return ONLY valid JSON, no markdown fences, no commentary outside the JSON"""


def build_package_prompt(
    travel_history: list[dict],
    preferences: dict,
    destination: Optional[str] = None,
    origin_iata: str = "BOM",
    duration_days: int = 7,
    budget_inr: Optional[int] = None,
) -> str:
    """Build the user prompt with travel context."""
    # Build history context
    history_text = ""
    if travel_history:
        history_text = "Previous trips:\n"
        for trip in travel_history[-8:]:  # Last 8 trips
            history_text += f"- {trip.get('origin_iata', '?')} to {trip.get('destination_iata', '?')}"
            if trip.get('destination_city'):
                history_text += f" ({trip['destination_city']})"
            if trip.get('duration_days'):
                history_text += f", {trip['duration_days']} days"
            if trip.get('searched_at'):
                history_text += f", on {str(trip['searched_at'])[:10]}"
            history_text += "\n"

    # Build preferences context
    pref_text = ""
    if preferences:
        parts = []
        if preferences.get("interests"):
            interests = preferences["interests"]
            if isinstance(interests, list):
                parts.append(f"Interests: {', '.join(interests)}")
        if preferences.get("budget_level"):
            parts.append(f"Budget preference: {preferences['budget_level']}")
        if preferences.get("travel_style"):
            parts.append(f"Travel style: {preferences['travel_style']}")
        pref_text = "\n".join(parts)

    user_prompt = f"""Origin airport: {origin_iata}
{"Destination: " + destination if destination else "Suggest a popular international destination based on history and preferences"}
Duration: {duration_days} days
{"Budget cap: INR " + str(budget_inr) if budget_inr else "No specific budget constraint"}

{history_text}
{pref_text}

Generate 3 personalized travel packages (budget / standard / premium)."""

    return user_prompt


def _call_claude(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str], list]:
    """
    Call Claude API. Returns (raw_text, model_name, errors).
    """
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

        # Extract text from response
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
    """Extract text from Gemini response (copied from iata_extractor.py)."""
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
    """
    Fallback: call Gemini API. Reuses pattern from core.py:150-168.
    Returns (raw_text, model_name, errors).
    """
    if not GENAI_AVAILABLE:
        return None, None, [("genai_missing", "google.generativeai not available")]

    # Configure Gemini API key (same pattern as core.py)
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


def _generate_fallback_packages(
    destination: str, origin_iata: str, days: int, budget_inr: Optional[int] = None
) -> list[dict]:
    """Generate static template packages when both LLMs fail."""
    base_flight = 15000

    tiers = [
        {
            "tier": "budget",
            "name": f"Essential {destination}",
            "tagline": f"Explore {destination} without breaking the bank",
            "destination_city": destination,
            "destination_iata": "DXB",
            "duration_days": days,
            "estimated_total_inr": base_flight + (3000 * days) + (2000 * days),
            "hotel": {
                "name": "Comfort Inn",
                "star_rating": 3,
                "price_per_night_inr": 3000,
                "area": "City Center"
            },
            "flights": {
                "travel_class": "ECONOMY",
                "estimated_price_inr": base_flight
            },
            "daily_itinerary": [
                {
                    "day": d + 1,
                    "title": f"Day {d + 1} - Explore",
                    "activities": [
                        {"time": "morning", "activity": "Visit local market and sightseeing", "estimated_cost_inr": 500},
                        {"time": "afternoon", "activity": "Explore historical landmarks", "estimated_cost_inr": 800},
                        {"time": "evening", "activity": "Local dining experience", "estimated_cost_inr": 1000},
                    ]
                }
                for d in range(days)
            ],
            "inclusions": ["Round-trip economy flights", f"{days} nights at 3-star hotel", "Daily breakfast"],
            "highlights": ["Budget-friendly", "Local experiences", "Flexible itinerary"],
        },
        {
            "tier": "standard",
            "name": f"Classic {destination}",
            "tagline": "The perfect balance of comfort and value",
            "destination_city": destination,
            "destination_iata": "DXB",
            "duration_days": days,
            "estimated_total_inr": (base_flight + 5000) + (6000 * days) + (4000 * days),
            "hotel": {
                "name": "Premium Hotel & Suites",
                "star_rating": 4,
                "price_per_night_inr": 6000,
                "area": "Premium District"
            },
            "flights": {
                "travel_class": "ECONOMY",
                "estimated_price_inr": base_flight + 5000
            },
            "daily_itinerary": [
                {
                    "day": d + 1,
                    "title": f"Day {d + 1} - Discover",
                    "activities": [
                        {"time": "morning", "activity": "Guided tour of top attractions", "estimated_cost_inr": 1500},
                        {"time": "afternoon", "activity": "Cultural experience or shopping", "estimated_cost_inr": 2000},
                        {"time": "evening", "activity": "Fine dining at popular restaurant", "estimated_cost_inr": 2500},
                    ]
                }
                for d in range(days)
            ],
            "inclusions": ["Round-trip flights", f"{days} nights at 4-star hotel", "Daily breakfast", "Airport transfers"],
            "highlights": ["Comfortable stay", "Curated activities", "Great value"],
        },
        {
            "tier": "premium",
            "name": f"Luxury {destination}",
            "tagline": f"Experience {destination} in absolute luxury",
            "destination_city": destination,
            "destination_iata": "DXB",
            "duration_days": days,
            "estimated_total_inr": (base_flight * 3) + (15000 * days) + (8000 * days),
            "hotel": {
                "name": "5-Star Grand Resort",
                "star_rating": 5,
                "price_per_night_inr": 15000,
                "area": "Premium Waterfront"
            },
            "flights": {
                "travel_class": "BUSINESS",
                "estimated_price_inr": base_flight * 3
            },
            "daily_itinerary": [
                {
                    "day": d + 1,
                    "title": f"Day {d + 1} - Indulge",
                    "activities": [
                        {"time": "morning", "activity": "Private guided tour or spa session", "estimated_cost_inr": 3000},
                        {"time": "afternoon", "activity": "Exclusive experience or luxury shopping", "estimated_cost_inr": 5000},
                        {"time": "evening", "activity": "Michelin-star dining experience", "estimated_cost_inr": 5000},
                    ]
                }
                for d in range(days)
            ],
            "inclusions": ["Business class flights", f"{days} nights at 5-star resort", "All meals", "Private transfers", "Concierge service"],
            "highlights": ["Ultimate luxury", "Exclusive access", "Personal concierge"],
        },
    ]

    return tiers


def generate_packages(
    travel_history: list[dict],
    preferences: dict,
    destination: Optional[str] = None,
    origin_iata: str = "BOM",
    duration_days: int = 7,
    budget_inr: Optional[int] = None,
) -> dict:
    """
    Generate travel packages using Claude AI (primary) with Gemini fallback.

    Returns:
        {
            "success": bool,
            "packages": [...],
            "personalization_note": str,
            "model_used": str | None,
            "used_fallback": bool,
            "error": str | None
        }
    """
    user_prompt = build_package_prompt(
        travel_history, preferences, destination,
        origin_iata, duration_days, budget_inr
    )

    result = {
        "success": False,
        "packages": [],
        "personalization_note": "",
        "model_used": None,
        "used_fallback": False,
        "error": None,
    }

    # Try Claude first
    raw_text, model_used, claude_errors = _call_claude(SYSTEM_PROMPT_PACKAGES, user_prompt)

    # If Claude failed, try Gemini
    if not raw_text:
        raw_text, model_used, gemini_errors = _call_gemini_fallback(SYSTEM_PROMPT_PACKAGES, user_prompt)
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
            destination or "Dubai",
            origin_iata,
            duration_days,
            budget_inr,
        )
        result["success"] = True
        result["personalization_note"] = "Generated using default templates (AI temporarily unavailable)"

    return result
