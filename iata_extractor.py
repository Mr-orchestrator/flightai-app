"""
IATA Code Extraction using Gemini AI
Extracts destination airport codes from natural language queries
"""
import os
import json
import time
import re

try:
    import google.generativeai as genai
except Exception:
    genai = None

# Major Indian International Airports
INDIAN_AIRPORTS = {
    "DEL": {"name": "Indira Gandhi International Airport", "city": "New Delhi"},
    "BOM": {"name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai"},
    "BLR": {"name": "Kempegowda International Airport", "city": "Bangalore"},
    "HYD": {"name": "Rajiv Gandhi International Airport", "city": "Hyderabad"},
    "MAA": {"name": "Chennai International Airport", "city": "Chennai"},
    "CCU": {"name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata"},
    "COK": {"name": "Cochin International Airport", "city": "Kochi"},
    "AMD": {"name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad"},
    "PNQ": {"name": "Pune Airport", "city": "Pune"},
    "GOI": {"name": "Goa International Airport", "city": "Goa"},
    "TRV": {"name": "Trivandrum International Airport", "city": "Thiruvananthapuram"},
    "IXC": {"name": "Chandigarh International Airport", "city": "Chandigarh"},
}

# Popular international destinations with IATA codes
POPULAR_DESTINATIONS = {
    # Europe
    "LHR": "London Heathrow", "CDG": "Paris Charles de Gaulle", "FRA": "Frankfurt",
    "AMS": "Amsterdam", "ZRH": "Zurich", "VIE": "Vienna", "FCO": "Rome",
    "BCN": "Barcelona", "MAD": "Madrid", "MUC": "Munich", "IST": "Istanbul",
    
    # Asia
    "DXB": "Dubai", "SIN": "Singapore", "HKG": "Hong Kong", "BKK": "Bangkok",
    "KUL": "Kuala Lumpur", "NRT": "Tokyo Narita", "ICN": "Seoul Incheon",
    "PEK": "Beijing", "PVG": "Shanghai Pudong", "DOH": "Doha", "AUH": "Abu Dhabi",
    
    # North America
    "JFK": "New York JFK", "LAX": "Los Angeles", "SFO": "San Francisco",
    "ORD": "Chicago", "YYZ": "Toronto", "YVR": "Vancouver", "MEX": "Mexico City",
    
    # Oceania
    "SYD": "Sydney", "MEL": "Melbourne", "AKL": "Auckland",
    
    # Africa
    "JNB": "Johannesburg", "CAI": "Cairo", "NBO": "Nairobi",
    
    # Middle East
    "RUH": "Riyadh", "JED": "Jeddah", "MCT": "Muscat", "BAH": "Bahrain",
}

MODEL_CANDIDATES = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]

SYSTEM_PROMPT_IATA = """You are an expert travel assistant that extracts destination information from natural language queries.

Your task: Extract the DESTINATION city/country/airport from the user's trip query and return its IATA airport code.

RETURN ONLY a JSON object with these fields:
{
  "destination_city": "<city or country name>",
  "iata_code": "<3-letter IATA code>",
  "confidence": "<high|medium|low>"
}

Examples:
Input: "plan trip to swiss for 7 days" => {"destination_city": "Zurich", "iata_code": "ZRH", "confidence": "high"}
Input: "weekend in paris" => {"destination_city": "Paris", "iata_code": "CDG", "confidence": "high"}
Input: "vacation in Dubai" => {"destination_city": "Dubai", "iata_code": "DXB", "confidence": "high"}
Input: "trip to Thailand" => {"destination_city": "Bangkok", "iata_code": "BKK", "confidence": "medium"}
Input: "visiting London" => {"destination_city": "London", "iata_code": "LHR", "confidence": "high"}

Rules:
- For countries, use the main/capital airport
- For Switzerland: ZRH (Zurich)
- For Thailand: BKK (Bangkok)
- For UK/England: LHR (London)
- For Japan: NRT (Tokyo)
- Always return valid 3-letter IATA codes
- If unsure, set confidence to "medium" or "low"

Return ONLY valid JSON, no markdown, no commentary."""

def safe_extract_text(resp):
    """Extract text from Gemini response"""
    if resp is None:
        return None
    
    # Try text attribute
    if hasattr(resp, 'text'):
        return resp.text.strip()
    
    # Try candidates
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

def call_gemini_for_iata(user_query, model_candidates=MODEL_CANDIDATES):
    """Call Gemini to extract IATA code"""
    if genai is None:
        return None, None, [("genai_missing", "google.generativeai not available")]
    
    errors = []
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content([SYSTEM_PROMPT_IATA, f"User query: {user_query}"])
            text = safe_extract_text(resp)
            if text:
                return text, model_name, errors
        except Exception as e:
            errors.append((model_name, repr(e)))
            time.sleep(0.25)
            continue
    
    return None, None, errors

def extract_iata_from_query(user_query):
    """
    Extract IATA code from natural language query
    Returns: {
        "destination_city": str,
        "iata_code": str,
        "confidence": str,
        "raw_output": str,
        "model_used": str,
        "used_fallback": bool,
        "error": str|None
    }
    """
    # Try Gemini first
    raw_text, model_used, errors = call_gemini_for_iata(user_query)
    
    result = {
        "destination_city": None,
        "iata_code": None,
        "confidence": "low",
        "raw_output": raw_text,
        "model_used": model_used,
        "used_fallback": False,
        "error": None
    }
    
    if raw_text:
        try:
            # Extract JSON from response
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1:
                json_str = raw_text[start:end+1]
                parsed = json.loads(json_str)
                
                result["destination_city"] = parsed.get("destination_city")
                result["iata_code"] = parsed.get("iata_code")
                result["confidence"] = parsed.get("confidence", "medium")
                
                # Validate IATA code format
                iata = result["iata_code"]
                if iata and isinstance(iata, str) and len(iata) == 3 and iata.isalpha():
                    result["iata_code"] = iata.upper()
                else:
                    result["error"] = f"Invalid IATA code format: {iata}"
                    result["iata_code"] = None
                    
        except Exception as e:
            result["error"] = f"JSON parse error: {repr(e)}"
    else:
        result["error"] = "No response from Gemini"
    
    # Fallback: try to find IATA code patterns in query
    if not result["iata_code"]:
        result["used_fallback"] = True
        
        # Check for explicit IATA codes in query
        iata_match = re.search(r'\b([A-Z]{3})\b', user_query.upper())
        if iata_match:
            result["iata_code"] = iata_match.group(1)
            result["confidence"] = "low"
            result["destination_city"] = "Unknown"
        
        # Check for popular city names
        query_lower = user_query.lower()
        for iata, city_name in POPULAR_DESTINATIONS.items():
            if city_name.lower() in query_lower or iata.lower() in query_lower:
                result["iata_code"] = iata
                result["destination_city"] = city_name
                result["confidence"] = "medium"
                break
    
    return result

def get_indian_airports_list():
    """Get formatted list of Indian airports for dropdown"""
    return [
        {"code": code, "label": f"{data['city']} ({code}) - {data['name']}"}
        for code, data in sorted(INDIAN_AIRPORTS.items(), key=lambda x: x[1]['city'])
    ]

# Test function
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and genai:
        genai.configure(api_key=api_key)
        print("Gemini configured\n")
    
    test_queries = [
        "plan trip to swiss for 7 days",
        "weekend in Dubai",
        "vacation in Thailand",
        "visiting London",
        "trip to Paris",
        "going to Singapore"
    ]
    
    for query in test_queries:
        result = extract_iata_from_query(query)
        print(f"Query: {query}")
        print(f"  Destination: {result['destination_city']}")
        print(f"  IATA: {result['iata_code']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Fallback: {result['used_fallback']}")
        print()
