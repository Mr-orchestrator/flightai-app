# gemini_duration.py
"""
Module to extract trip duration using Gemini (prefers AI extraction).
If Gemini can't produce a valid integer duration (1..365), falls back to a robust local extractor.
Returns a dict with:
  - duration_days (int)
  - departure_date (datetime.date)  # today + 8 days
  - return_date (datetime.date)
  - raw_model_output (str|None)
  - model_used (str|None)
  - used_fallback (bool)  # True when local extractor was used
  - error (str|None)
Requirements:
  pip install python-dotenv google-generativeai
Set GOOGLE_API_KEY in env or load via dotenv before calling.
"""
from datetime import datetime, timedelta
import os
import re
import json
import time

# Optional: import google.generativeai if you will call Gemini
try:
    import google.generativeai as genai
except Exception:
    genai = None

# --- Model candidates (from your project ListModels) ---
MODEL_CANDIDATES = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-pro-latest",
    "models/gemini-flash-latest",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-pro-latest",
    "gemini-flash-latest",
]

# --- Local robust extractor (fallback) ---
NUMBER_WORDS = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
    "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
    "sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,"twenty":20,
    "thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90,
    "hundred":100
}
def words_to_number(words):
    parts = words.lower().split()
    total, current = 0, 0
    for w in parts:
        if w not in NUMBER_WORDS:
            continue
        val = NUMBER_WORDS[w]
        if val == 100:
            current *= val
        else:
            current += val
    total += current
    return total if total > 0 else None

# robust full extractor (handles digits, words, weeks, ranges, weekend etc.)
def extract_duration_days_full(text, fallback=7):
    if not text:
        return fallback
    t = text.lower()

    # weekend -> 2 days
    if "weekend" in t:
        return 2

    # "a week and a half" or explicit halves
    if re.search(r"(?:a|one)\s+week\s+and\s+a\s+half", t):
        return 11  # 1.5 weeks = 10.5 days, round up to 11

    # weeks -> days
    m_week = re.search(r"(\d+|\w+)\s*(?:weeks|week)\b", t)
    if m_week:
        w = m_week.group(1)
        try:
            wv = int(w)
        except:
            wv = words_to_number(w) or 1
        return max(1, int(wv * 7))

    # range like "10-12 days" -> take lower bound
    m_range = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(?:days|day|nights|night)", t)
    if m_range:
        return int(m_range.group(1))

    # digit with day/night
    m_digits = re.search(r"(\d+)\s*(?:days|day|nights|night)\b", t)
    if m_digits:
        return int(m_digits.group(1))

    # number words followed by days
    m_words = re.search(
        r"\b(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)(?:\s+|[-])?){1,3}\b(?:\s*(?:days|day|nights|night))?",
        t)
    if m_words:
        candidate = m_words.group(0)
        num = words_to_number(candidate)
        if num:
            return num

    # fallback: any single digit in text
    m_any_digit = re.search(r"\b(\d{1,3})\b", t)
    if m_any_digit:
        v = int(m_any_digit.group(1))
        if 1 <= v <= 365:
            return v

    return fallback

# --- Helpers to call Gemini (robustly try candidate models) ---
def safe_extract_text_from_genai_response(resp):
    if resp is None:
        return None
    # try common attributes
    for attr in ("text", "content", "output", "result"):
        if hasattr(resp, attr):
            val = getattr(resp, attr)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, dict) and "text" in val:
                return val["text"].strip()
    # candidates
    try:
        candidates = getattr(resp, "candidates", None) or (resp.get("candidates") if isinstance(resp, dict) else None)
        if candidates and isinstance(candidates, (list, tuple)):
            first = candidates[0]
            if isinstance(first, dict):
                for k in ("content", "text"):
                    if k in first and isinstance(first[k], str):
                        return first[k].strip()
            else:
                for k in ("content", "text"):
                    if hasattr(first, k):
                        v = getattr(first, k)
                        if isinstance(v, str):
                            return v.strip()
    except Exception:
        pass
    try:
        return str(resp).strip()
    except Exception:
        return None

def call_gemini_json(system_prompt, user_prompt, model_candidates=MODEL_CANDIDATES, sleep_between_tries=0.25):
    """
    Try each model candidate until one returns text. Returns:
      (raw_text, used_model, errors)
    """
    if genai is None:
        return None, None, [("genai_missing", "google.generativeai library not available")]
    errors = []
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content([system_prompt, user_prompt])
            text = safe_extract_text_from_genai_response(resp)
            return text, model_name, errors
        except Exception as e:
            errors.append((model_name, repr(e)))
            time.sleep(sleep_between_tries)
            continue
    return None, None, errors

# --- System prompt used to ask Gemini for ONLY duration (JSON) ---
SYSTEM_PROMPT_DURATION = (
    "You are a short and strict extractor. The user has a trip request in plain English "
    "and an origin provided separately. Your job: infer the trip DURATION (in days) the user intends.\n\n"
    "RETURN ONLY a JSON object and NOTHING ELSE. The JSON must contain a single key:\n"
    '  "duration_days": <integer number of days>\n'
    "If you cannot determine it with confidence, still return a reasonable integer or the string 'UNKNOWN' for duration_days.\n\n"
    "Examples:\n"
    'Input: "plan trip to swiss for 7 days" => {"duration_days":7}\n'
    'Input: "trip for a week" => {"duration_days":7}\n'
    'Input: "weekend in paris" => {"duration_days":2}\n'
    "Do NOT include commentary, markdown, or extra fields. Return valid JSON only."
)

# --- Public API function ---
def get_trip_dates(origin_text, user_query, fallback_days=7, max_duration=365):
    """
    Use Gemini to extract duration. Returns:
      {
        "duration_days": int,
        "departure_date": date,
        "return_date": date,
        "raw_model_output": str|None,
        "model_used": str|None,
        "used_fallback": bool,
        "error": str|None
      }
    """
    today = datetime.today().date()
    departure = today + timedelta(days=8)

    # Prepare system/user prompt
    ctx_line = f"Origin: {origin_text}" if origin_text else ""
    user_prompt = f"User query: {user_query}"

    final_system = SYSTEM_PROMPT_DURATION + ("\n" + ctx_line if ctx_line else "")

    raw_text, used_model, errors = call_gemini_json(final_system, user_prompt)
    used_fallback = False
    duration_days = None
    error = None

    # Try to parse model output as JSON (strict)
    if raw_text:
        try:
            # extract first { .. } block
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_text[start:end+1]
                parsed = json.loads(candidate)
            else:
                parsed = json.loads(raw_text)
            # model may return string 'UNKNOWN' or number
            val = parsed.get("duration_days") if isinstance(parsed, dict) else None
            if isinstance(val, str) and val.strip().upper() == "UNKNOWN":
                duration_days = None
            elif isinstance(val, (int, float)):
                duration_days = int(val)
            elif isinstance(val, str) and re.fullmatch(r"\d+", val.strip()):
                duration_days = int(val.strip())
            else:
                duration_days = None
        except Exception as e:
            # parsing failed - keep raw_text for debugging and fallback
            error = f"Model JSON parse error: {repr(e)}"
            duration_days = None
    else:
        error = "No model text returned"
        duration_days = None

    # Validate duration number range
    if duration_days is not None:
        if not (1 <= duration_days <= max_duration):
            # invalid number from model -> fallback
            error = (error or "") + f" | invalid duration from model: {duration_days}"
            duration_days = None

    # If model failed or returned invalid, fallback to local parsing
    if duration_days is None:
        fallback_val = extract_duration_days_full(user_query, fallback=fallback_days)
        used_fallback = True
        duration_days = fallback_val

    # Compute return date
    return_date = departure + timedelta(days=duration_days)

    result = {
        "duration_days": int(duration_days),
        "departure_date": departure,
        "return_date": return_date,
        "raw_model_output": raw_text,
        "model_used": used_model,
        "used_fallback": used_fallback,
        "error": error
    }
    return result

# --- Example usage if run as a script ---
if __name__ == "__main__":
    # Load environment variables and configure Gemini
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment.")
        print("Please set it in .env file or environment variable.")
        exit(1)
    
    if genai:
        genai.configure(api_key=api_key)
        print("✓ Gemini API configured successfully\n")
    else:
        print("WARNING: google-generativeai not installed. Will use fallback extractor only.\n")
    
    origin = "Mumbai"
    queries = [
        "plan trip to swiss for 7 days",
        "a 10-day vacation in switzerland",
        "weekend in zurich",
        "trip for one and a half weeks",
        "just a few days in Geneva"
    ]
    for q in queries:
        out = get_trip_dates(origin, q)
        print("QUERY:", q)
        print("RESULT:", out)
        print("---")
