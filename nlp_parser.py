"""
NLP Travel Intent Parser using Gemini
Extracts structured travel intent from natural language queries:
  destination, IATA code, duration, budget, interests, travel style
"""

import os
import json
import time
from typing import Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from iata_extractor import extract_iata_from_query

GEMINI_MODEL_CANDIDATES = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]

NLP_SYSTEM_PROMPT = """You are a travel intent parser. Given a user's natural language travel query, extract structured information.

RETURN ONLY a JSON object with this exact structure:
{
  "destination": "<city or region name, or null if not specified>",
  "duration_days": <integer number of days, or null if not specified>,
  "budget_inr": <integer budget in INR, or null if not specified>,
  "departure_date": "<YYYY-MM-DD format date, or null if not specified>",
  "interests": ["<list of interests like beach, culture, adventure, food, shopping, nature, relaxation, nightlife, history, wildlife>"],
  "travel_style": "<one of: adventure, cultural, relaxation, luxury, backpacking, family, romantic, or mixed>",
  "travel_companions": "<one of: solo, couple, family, friends, or null if not specified>",
  "specific_requests": "<any specific requests like direct flights, 5-star hotel, vegan food, etc. or null>"
}

Rules:
- Extract as much information as possible from the query
- For budget: if they say "50k" or "50000", convert to integer 50000. If in USD/EUR, convert to approximate INR.
- For duration: "a week" = 7, "weekend" = 3, "10 days" = 10, "fortnight" = 14
- For departure_date: convert relative dates to YYYY-MM-DD. "next week" = next Monday. "in March" = first of March. "tomorrow" = tomorrow's date.
- For interests: infer from context. "beach vacation" → ["beach", "relaxation"]. "explore temples" → ["culture", "history"]
- If information is not in the query, use null (not empty string)
- Return ONLY valid JSON, no commentary"""


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


def extract_travel_intent(query: str) -> dict:
    """
    Extract structured travel intent from a natural language query.

    Args:
        query: Natural language travel query like
               "I want a relaxing beach vacation in Goa for a week under 50k"

    Returns:
        dict with keys: destination, destination_iata, duration_days, budget_inr,
                       interests, travel_style, travel_companions, specific_requests,
                       success, model_used, error
    """
    result = {
        "success": False,
        "destination": None,
        "destination_iata": None,
        "duration_days": None,
        "budget_inr": None,
        "departure_date": None,
        "interests": [],
        "travel_style": "mixed",
        "travel_companions": None,
        "specific_requests": None,
        "model_used": None,
        "error": None,
    }

    if not query or not query.strip():
        result["error"] = "Empty query"
        return result

    # Step 1: Use existing IATA extractor to get destination code
    iata_result = extract_iata_from_query(query)
    if iata_result and iata_result.get('iata_code'):
        result["destination_iata"] = iata_result['iata_code']
        result["destination"] = iata_result.get('destination_city')

    # Step 2: Use Gemini to extract full intent
    if not GENAI_AVAILABLE:
        result["error"] = "Gemini not available"
        # Still return partial results from IATA extraction
        if result["destination_iata"]:
            result["success"] = True
        return result

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        result["error"] = "GOOGLE_API_KEY not set"
        if result["destination_iata"]:
            result["success"] = True
        return result

    genai.configure(api_key=api_key)

    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content([
                NLP_SYSTEM_PROMPT,
                f"User query: {query}"
            ])
            text = _safe_extract_text(resp)
            if not text:
                continue

            # Parse JSON
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                continue

            parsed = json.loads(text[start:end + 1])

            # Merge parsed results
            if parsed.get("destination") and not result["destination"]:
                result["destination"] = parsed["destination"]
            if parsed.get("duration_days"):
                result["duration_days"] = int(parsed["duration_days"])
            if parsed.get("budget_inr"):
                result["budget_inr"] = int(parsed["budget_inr"])
            if parsed.get("interests"):
                result["interests"] = parsed["interests"]
            if parsed.get("travel_style"):
                result["travel_style"] = parsed["travel_style"]
            if parsed.get("travel_companions"):
                result["travel_companions"] = parsed["travel_companions"]
            if parsed.get("specific_requests"):
                result["specific_requests"] = parsed["specific_requests"]
            if parsed.get("departure_date"):
                result["departure_date"] = parsed["departure_date"]

            result["success"] = True
            result["model_used"] = model_name
            break

        except Exception as e:
            time.sleep(0.25)
            continue

    # If Gemini extracted a destination but IATA extractor didn't, try again
    if result["destination"] and not result["destination_iata"]:
        iata_retry = extract_iata_from_query(result["destination"])
        if iata_retry and iata_retry.get('iata_code'):
            result["destination_iata"] = iata_retry['iata_code']

    if not result["success"] and result["destination_iata"]:
        result["success"] = True

    return result
