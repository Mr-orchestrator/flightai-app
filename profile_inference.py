"""
Profile Intelligence Engine — Rule-Based User Inference
Deterministic inference from user booking history and engagement signals.
Runs BEFORE Amadeus calls, AFTER NLP extraction.
No LLM involvement.

Signal hierarchy:
  STRONG (1.0): BookingHistory — explicit "Save Trip" action
  MEDIUM (0.4): EngagementSignal — tier expand/view
  WEAK   (0.0): TravelHistory — search only (analytics, not used for inference)

Priority order: Explicit user input > NLP extraction > Profile defaults
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers: Timestamp parsing, recency weighting, weighted counter
# ---------------------------------------------------------------------------

def _parse_timestamp(ts) -> Optional[datetime]:
    """Parse a timestamp from string or datetime."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None
    return None


def _recency_weight(timestamp_str) -> float:
    """
    Exponential decay weight based on time since event.
    Half-life ~7 months.
    0 months: 1.0, 6 months: 0.55, 12 months: 0.30, 24 months: 0.09
    """
    if not timestamp_str:
        return 0.5  # Unknown date gets middle-ground weight
    ts = _parse_timestamp(timestamp_str)
    if not ts:
        return 0.5
    months_ago = max((datetime.utcnow() - ts).days / 30.0, 0)
    return math.exp(-0.1 * months_ago)


def _compute_weight(entry: dict) -> float:
    """
    Two-factor weight: recency × signal_strength.
    BookingHistory entries have signal_strength=1.0.
    EngagementSignal entries have signal_strength=0.4.
    """
    recency = _recency_weight(entry.get("booked_at") or entry.get("searched_at"))
    strength = entry.get("signal_strength", 1.0)
    return recency * strength


def _weighted_counter(items: list[tuple]) -> Optional[str]:
    """
    Return the key with highest total weight.
    Items: [(value, weight), ...]
    """
    if not items:
        return None
    weights: dict = {}
    for value, weight in items:
        if value is not None:
            key = str(value)
            weights[key] = weights.get(key, 0.0) + weight
    return max(weights, key=weights.get) if weights else None


def _weighted_top_n(items: list[tuple], n: int = 3) -> list[str]:
    """
    Return top N keys by total weight.
    Items: [(value, weight), ...]
    """
    if not items:
        return []
    weights: dict = {}
    for value, weight in items:
        if value:
            weights[value] = weights.get(value, 0.0) + weight
    sorted_keys = sorted(weights, key=weights.get, reverse=True)
    return sorted_keys[:n]


# ---------------------------------------------------------------------------
# Multi-candidate country gateway mapping
# ---------------------------------------------------------------------------

COUNTRY_GATEWAYS = {
    # Asia
    "India": ["DEL", "BOM", "BLR", "MAA", "HYD", "CCU"],
    "Thailand": ["BKK", "CNX", "HKT"],
    "Japan": ["NRT", "KIX", "HND"],
    "Singapore": ["SIN"],
    "Malaysia": ["KUL", "PEN", "LGK"],
    "Indonesia": ["DPS", "CGK"],
    "Vietnam": ["SGN", "HAN", "DAD"],
    "Philippines": ["MNL", "CEB"],
    "South Korea": ["ICN", "PUS"],
    "China": ["PEK", "PVG", "CAN"],
    "Hong Kong": ["HKG"],
    "Sri Lanka": ["CMB"],
    "Maldives": ["MLE"],
    # Middle East
    "UAE": ["DXB", "AUH"],
    "Dubai": ["DXB"],
    "Qatar": ["DOH"],
    "Oman": ["MCT"],
    "Bahrain": ["BAH"],
    "Saudi Arabia": ["RUH", "JED"],
    # Europe
    "UK": ["LHR", "MAN", "EDI", "LGW"],
    "England": ["LHR", "MAN", "LGW"],
    "France": ["CDG", "NCE", "LYS"],
    "Germany": ["FRA", "MUC", "TXL"],
    "Netherlands": ["AMS"],
    "Italy": ["FCO", "MXP", "VCE"],
    "Spain": ["BCN", "MAD", "PMI"],
    "Turkey": ["IST", "SAW", "AYT"],
    "Switzerland": ["ZRH", "GVA"],
    "Austria": ["VIE"],
    # Americas
    "USA": ["JFK", "LAX", "ORD", "MIA", "SFO", "DEN", "ATL"],
    "United States": ["JFK", "LAX", "ORD", "MIA", "SFO", "DEN", "ATL"],
    "Canada": ["YYZ", "YVR", "YUL", "YYC"],
    # Oceania
    "Australia": ["SYD", "MEL", "BNE", "PER"],
    "New Zealand": ["AKL", "CHC", "WLG"],
    # Africa
    "South Africa": ["JNB", "CPT"],
    "Egypt": ["CAI", "HRG"],
    "Kenya": ["NBO", "MBA"],
}

# Interest-to-gateway overrides (when interest conflicts with default gateway)
INTEREST_GATEWAY_OVERRIDES = {
    "Canada": {
        "skiing": "YYC", "snow": "YYC", "winter sports": "YYC",
        "nature": "YVR", "mountains": "YVR",
    },
    "USA": {
        "beach": "MIA", "skiing": "DEN", "tech": "SFO",
        "entertainment": "LAX", "nightlife": "LAX",
    },
    "Australia": {
        "beach": "OOL", "nature": "CNS",
    },
    "Thailand": {
        "beach": "HKT", "culture": "CNX", "history": "CNX",
    },
    "Japan": {
        "culture": "KIX", "history": "KIX",   # Osaka/Kyoto
    },
    "Spain": {
        "beach": "PMI",  # Mallorca
    },
    "Italy": {
        "shopping": "MXP", "fashion": "MXP",  # Milan
    },
    "Turkey": {
        "beach": "AYT",  # Antalya
    },
    "South Africa": {
        "nature": "CPT", "beach": "CPT",  # Cape Town
    },
    "Indonesia": {
        "culture": "CGK",  # Jakarta for culture
    },
}

# Origin region → country → preferred gateway (static route-awareness heuristic)
ORIGIN_ROUTE_AFFINITY = {
    ("IN", "Canada"): "YYZ",     # BOM/DEL → Toronto (direct Air Canada/AI)
    ("IN", "USA"): "JFK",        # BOM/DEL → JFK (direct flights)
    ("IN", "UK"): "LHR",         # BOM/DEL → Heathrow (direct AI/BA/VS)
    ("IN", "Australia"): "SYD",  # BOM → Sydney (direct AI)
    ("IN", "Japan"): "NRT",      # BOM → Narita
    ("IN", "Thailand"): "BKK",   # BOM → Bangkok (direct)
    ("IN", "Singapore"): "SIN",  # BOM → Singapore (direct)
    ("ME", "UK"): "LHR",         # DXB → Heathrow (Emirates hub)
    ("ME", "USA"): "JFK",        # DXB → JFK (Emirates)
    ("US", "Japan"): "NRT",      # LAX/SFO → Narita
    ("US", "UK"): "LHR",         # JFK → Heathrow
    ("EU", "Thailand"): "BKK",   # European hubs → Bangkok
    ("EU", "USA"): "JFK",        # EU → JFK
    ("APAC", "Australia"): "SYD",  # Singapore/BKK → Sydney
}

IATA_TO_REGION = {
    # India
    "BOM": "IN", "DEL": "IN", "BLR": "IN", "MAA": "IN", "HYD": "IN",
    "CCU": "IN", "GOI": "IN", "COK": "IN", "AMD": "IN", "PNQ": "IN",
    # Middle East
    "DXB": "ME", "DOH": "ME", "AUH": "ME", "RUH": "ME", "JED": "ME",
    "MCT": "ME", "BAH": "ME",
    # Americas
    "JFK": "US", "LAX": "US", "ORD": "US", "SFO": "US", "MIA": "US",
    "DEN": "US", "ATL": "US", "YYZ": "US", "YVR": "US", "YUL": "US",
    # Europe
    "LHR": "EU", "CDG": "EU", "FRA": "EU", "AMS": "EU", "FCO": "EU",
    "BCN": "EU", "MAD": "EU", "IST": "EU", "MUC": "EU", "ZRH": "EU",
    "VIE": "EU", "MAN": "EU",
    # Asia-Pacific
    "SIN": "APAC", "BKK": "APAC", "HKG": "APAC", "NRT": "APAC",
    "KIX": "APAC", "ICN": "APAC", "PEK": "APAC", "PVG": "APAC",
    "KUL": "APAC", "DPS": "APAC", "MNL": "APAC", "SGN": "APAC",
}

# City name to IATA mapping (for resolving preferred_destinations stored as names)
CITY_NAME_TO_IATA = {
    # India
    "New Delhi": "DEL", "Delhi": "DEL", "Mumbai": "BOM", "Bangalore": "BLR",
    "Bengaluru": "BLR", "Hyderabad": "HYD", "Chennai": "MAA", "Kolkata": "CCU",
    "Kochi": "COK", "Goa": "GOI", "Ahmedabad": "AMD", "Pune": "PNQ",
    "Jaipur": "JAI", "Varanasi": "VNS", "Srinagar": "SXR",
    # Middle East
    "Dubai": "DXB", "Abu Dhabi": "AUH", "Doha": "DOH", "Muscat": "MCT",
    "Riyadh": "RUH", "Jeddah": "JED", "Bahrain": "BAH",
    # Southeast Asia
    "Singapore": "SIN", "Bangkok": "BKK", "Kuala Lumpur": "KUL",
    "Hong Kong": "HKG", "Ho Chi Minh City": "SGN", "Hanoi": "HAN",
    "Manila": "MNL", "Bali": "DPS", "Phuket": "HKT", "Chiang Mai": "CNX",
    # East Asia
    "Tokyo": "NRT", "Seoul": "ICN", "Beijing": "PEK", "Shanghai": "PVG",
    "Osaka": "KIX",
    # Europe
    "London": "LHR", "Paris": "CDG", "Frankfurt": "FRA", "Amsterdam": "AMS",
    "Rome": "FCO", "Barcelona": "BCN", "Madrid": "MAD", "Istanbul": "IST",
    "Zurich": "ZRH", "Vienna": "VIE", "Munich": "MUC", "Milan": "MXP",
    "Nice": "NCE", "Venice": "VCE", "Edinburgh": "EDI", "Manchester": "MAN",
    "Geneva": "GVA",
    # Americas
    "New York": "JFK", "Los Angeles": "LAX", "San Francisco": "SFO",
    "Chicago": "ORD", "Miami": "MIA", "Toronto": "YYZ", "Vancouver": "YVR",
    "Montreal": "YUL",
    # Oceania
    "Sydney": "SYD", "Melbourne": "MEL", "Brisbane": "BNE", "Perth": "PER",
    "Auckland": "AKL",
    # Africa
    "Johannesburg": "JNB", "Cape Town": "CPT", "Cairo": "CAI",
    "Nairobi": "NBO",
    # Island
    "Maldives": "MLE", "Male": "MLE", "Colombo": "CMB",
}

# IATA code to country mapping (reverse lookup for history matching)
IATA_TO_COUNTRY = {
    "YYZ": "Canada", "YVR": "Canada", "YYC": "Canada", "YUL": "Canada",
    "JFK": "USA", "LAX": "USA", "SFO": "USA", "ORD": "USA", "MIA": "USA",
    "DEN": "USA", "ATL": "USA",
    "LHR": "UK", "MAN": "UK", "EDI": "UK", "LGW": "UK",
    "CDG": "France", "NCE": "France", "LYS": "France",
    "FRA": "Germany", "MUC": "Germany", "TXL": "Germany",
    "AMS": "Netherlands",
    "FCO": "Italy", "MXP": "Italy", "VCE": "Italy",
    "BCN": "Spain", "MAD": "Spain", "PMI": "Spain",
    "IST": "Turkey", "SAW": "Turkey", "AYT": "Turkey",
    "ZRH": "Switzerland", "GVA": "Switzerland",
    "VIE": "Austria",
    "DXB": "UAE", "AUH": "UAE",
    "DOH": "Qatar", "MCT": "Oman", "BAH": "Bahrain",
    "RUH": "Saudi Arabia", "JED": "Saudi Arabia",
    "BKK": "Thailand", "CNX": "Thailand", "HKT": "Thailand",
    "SIN": "Singapore",
    "NRT": "Japan", "KIX": "Japan", "HND": "Japan",
    "ICN": "South Korea", "PUS": "South Korea",
    "SYD": "Australia", "MEL": "Australia", "BNE": "Australia", "PER": "Australia",
    "AKL": "New Zealand", "CHC": "New Zealand", "WLG": "New Zealand",
    "DEL": "India", "BOM": "India", "BLR": "India", "MAA": "India",
    "HYD": "India", "CCU": "India", "GOI": "India", "COK": "India",
    "DPS": "Indonesia", "CGK": "Indonesia",
    "SGN": "Vietnam", "HAN": "Vietnam", "DAD": "Vietnam",
    "MNL": "Philippines", "CEB": "Philippines",
    "KUL": "Malaysia", "PEN": "Malaysia", "LGK": "Malaysia",
    "PEK": "China", "PVG": "China", "CAN": "China",
    "HKG": "Hong Kong",
    "MLE": "Maldives", "CMB": "Sri Lanka",
    "JNB": "South Africa", "CPT": "South Africa",
    "CAI": "Egypt", "HRG": "Egypt",
    "NBO": "Kenya", "MBA": "Kenya",
}


# ---------------------------------------------------------------------------
# Profile Strength
# ---------------------------------------------------------------------------

def compute_profile_strength(travel_history: list[dict]) -> int:
    """
    Compute profile confidence score from booking/engagement history.
    Apply inference at strength >= 1 (graduated confidence).

    +1 if at least 1 entry within last 24 months
    +1 if at least 2 entries within last 36 months

    strength=1 → inference with confidence="low"
    strength=2 → inference with confidence="high"
    """
    strength = 0
    cutoff_36mo = datetime.utcnow() - timedelta(days=1095)
    cutoff_24mo = datetime.utcnow() - timedelta(days=730)

    recent_entries = []
    has_recent_24mo = False

    for entry in travel_history:
        ts = _parse_timestamp(entry.get("booked_at") or entry.get("searched_at"))
        if ts:
            if ts > cutoff_36mo:
                recent_entries.append(entry)
            if ts > cutoff_24mo:
                has_recent_24mo = True

    if has_recent_24mo:
        strength += 1
    if len(recent_entries) >= 2:
        strength += 1

    return strength


# ---------------------------------------------------------------------------
# Inference Functions (all use weighted counters from booking history)
# ---------------------------------------------------------------------------

def infer_origin(
    travel_history: list[dict],
    user_home_airport: Optional[str] = None,
) -> tuple[str, str]:
    """
    Infer departure airport using recency-weighted booking history.
    Returns: (iata_code, source)
    """
    if user_home_airport:
        return user_home_airport, "home_airport"

    if travel_history:
        weighted = [
            (t["origin_iata"], _compute_weight(t))
            for t in travel_history if t.get("origin_iata")
        ]
        result = _weighted_counter(weighted)
        if result:
            return result, "history"

    return "BOM", "default"


def infer_destination(
    travel_history: list[dict],
    nlp_intent: dict,
    user_prefs: Optional[dict] = None,
    origin_iata: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], str]:
    """
    Resolve destination IATA code with multi-candidate airport selection.
    Returns: (destination_city, destination_iata, source)
    """
    # Priority 1: NLP extracted specific city with IATA
    if nlp_intent.get("destination_iata"):
        return nlp_intent.get("destination"), nlp_intent["destination_iata"], "nlp_city"

    # Priority 2: NLP extracted destination name (might be country or city)
    destination = nlp_intent.get("destination")
    if destination:
        country_key = destination.strip().title()
        if country_key in COUNTRY_GATEWAYS:
            gateway = _resolve_country_gateway(
                country_key, travel_history, nlp_intent, origin_iata
            )
            return destination, gateway[0], gateway[1]

        # Not a known country — might be a city name
        return destination, None, "nlp_city_unresolved"

    # Priority 3: Use user's preferred destinations
    if user_prefs and user_prefs.get("preferred_destinations"):
        prefs = user_prefs["preferred_destinations"]
        visited = set()
        for trip in travel_history:
            if trip.get("destination_iata"):
                visited.add(trip["destination_iata"])

        for pref in prefs:
            pref_stripped = pref.strip()
            pref_upper = pref_stripped.upper()
            # IATA code
            if len(pref_upper) == 3 and pref_upper not in visited:
                return pref_stripped, pref_upper, "preferred"
            # City name → IATA
            iata = CITY_NAME_TO_IATA.get(pref_stripped.title())
            if iata and iata not in visited:
                return pref_stripped, iata, "preferred"
            # Country name → gateway (multi-candidate)
            country_key = pref_stripped.title()
            if country_key in COUNTRY_GATEWAYS:
                gateway = _resolve_country_gateway(
                    country_key, travel_history, nlp_intent, origin_iata
                )
                if gateway[0] not in visited:
                    return pref_stripped, gateway[0], "preferred"

    return None, None, "none"


def _resolve_country_gateway(
    country_key: str,
    travel_history: list[dict],
    nlp_intent: dict,
    origin_iata: Optional[str] = None,
) -> tuple[str, str]:
    """
    Multi-candidate country-to-airport resolution.
    Selection order:
    1. Interest overrides
    2. Recency-weighted booking history for that country
    3. Route-aware affinity from origin
    4. Default (first candidate)

    Returns: (iata_code, source)
    """
    candidates = COUNTRY_GATEWAYS[country_key]
    interests = nlp_intent.get("interests", [])

    # Step 1: Interest override
    if country_key in INTEREST_GATEWAY_OVERRIDES and interests:
        overrides = INTEREST_GATEWAY_OVERRIDES[country_key]
        for interest in interests:
            if interest.lower() in overrides:
                return overrides[interest.lower()], "interest_override"

    # Step 2: Recency-weighted booking history for this country
    if travel_history:
        country_trips = [
            (trip["destination_iata"], _compute_weight(trip))
            for trip in travel_history
            if trip.get("destination_iata") and IATA_TO_COUNTRY.get(trip["destination_iata"]) == country_key
        ]
        if country_trips:
            best = _weighted_counter(country_trips)
            if best:
                return best, "history_country"

    # Step 3: Route-aware affinity from origin
    if origin_iata:
        region = IATA_TO_REGION.get(origin_iata)
        if region:
            affinity_key = (region, country_key)
            if affinity_key in ORIGIN_ROUTE_AFFINITY:
                preferred = ORIGIN_ROUTE_AFFINITY[affinity_key]
                if preferred in candidates:
                    return preferred, "route_affinity"

    # Step 4: Default first candidate
    return candidates[0], "gateway"


def infer_duration(
    travel_history: list[dict],
    nlp_intent: dict,
) -> tuple[int, str]:
    """
    Infer trip duration using weighted median from booking history.
    Returns: (days, source)
    """
    if nlp_intent.get("duration_days"):
        return nlp_intent["duration_days"], "nlp"

    if travel_history:
        entries = [
            (t["duration_days"], _compute_weight(t))
            for t in travel_history
            if t.get("duration_days") and t["duration_days"] > 0
        ]
        if entries:
            # Weighted median: sort by duration, find 50th percentile by weight
            entries.sort(key=lambda x: x[0])
            total_weight = sum(w for _, w in entries)
            if total_weight > 0:
                cumulative = 0
                for dur, w in entries:
                    cumulative += w
                    if cumulative >= total_weight / 2:
                        return dur, "history"

    return 7, "default"


def infer_cabin(travel_history: list[dict]) -> tuple[str, str]:
    """
    Infer preferred cabin class from recency-weighted booking history.
    Returns: (cabin_class, source)
    """
    if travel_history:
        weighted = [
            (t.get("cabin_class"), _compute_weight(t))
            for t in travel_history if t.get("cabin_class")
        ]
        if weighted:
            result = _weighted_counter(weighted)
            if result:
                return result, "history"

    return "ECONOMY", "default"


def infer_hotel_preference(travel_history: list[dict]) -> tuple[int, str]:
    """
    Infer preferred hotel star rating from recency-weighted booking history.
    Returns: (star_rating, source)
    """
    if travel_history:
        weighted = [
            (t.get("hotel_star_rating"), _compute_weight(t))
            for t in travel_history if t.get("hotel_star_rating")
        ]
        if weighted:
            result = _weighted_counter(weighted)
            if result:
                return int(result), "history"

    return 4, "default"


def infer_budget(
    travel_history: list[dict],
    nlp_intent: dict,
    user_prefs: Optional[dict] = None,
) -> tuple[Optional[int], Optional[int], str]:
    """
    Infer budget range from recency-weighted booking history.
    Returns: (budget_min, budget_max, source)

    Uses weighted 25th/75th percentiles of past total_price_inr.
    """
    # Priority 1: NLP extracted budget
    if nlp_intent.get("budget_inr"):
        b = nlp_intent["budget_inr"]
        return int(b * 0.8), int(b * 1.2), "nlp"

    # Priority 2: Explicit user preferences
    if user_prefs:
        bmin = user_prefs.get("budget_range_min")
        bmax = user_prefs.get("budget_range_max")
        if bmin and bmax:
            return bmin, bmax, "preferences"

    # Priority 3: Weighted percentiles from booking history
    if travel_history:
        entries = [
            (t["total_price_inr"], _compute_weight(t))
            for t in travel_history
            if t.get("total_price_inr") and t["total_price_inr"] > 0
        ]
        if len(entries) >= 2:
            entries.sort(key=lambda x: x[0])
            total_weight = sum(w for _, w in entries)
            if total_weight > 0:
                # Weighted 25th percentile
                cumulative = 0
                p25 = entries[0][0]
                for price, w in entries:
                    cumulative += w
                    if cumulative >= total_weight * 0.25:
                        p25 = price
                        break

                # Weighted 75th percentile
                cumulative = 0
                p75 = entries[-1][0]
                for price, w in entries:
                    cumulative += w
                    if cumulative >= total_weight * 0.75:
                        p75 = price
                        break

                return int(p25), int(p75), "history"

    return None, None, "default"


def infer_airline_preference(
    travel_history: list[dict],
    user_prefs: Optional[dict] = None,
) -> tuple[list[str], str]:
    """
    Infer preferred airlines from recency-weighted booking history.
    Returns: (carrier_codes, source)
    """
    # Priority 1: Explicit user preferences
    if user_prefs and user_prefs.get("preferred_airlines"):
        return user_prefs["preferred_airlines"], "preferences"

    # Priority 2: Top 3 recency-weighted carriers from history
    if travel_history:
        weighted_items = []
        for t in travel_history:
            weight = _compute_weight(t)
            # BookingHistory may have carrier_codes (list)
            codes = t.get("carrier_codes") or []
            if isinstance(codes, list):
                for code in codes:
                    if code:
                        weighted_items.append((code, weight))
            # Also check single carrier field
            carrier = t.get("carrier")
            if carrier:
                weighted_items.append((carrier, weight))

        if weighted_items:
            top_3 = _weighted_top_n(weighted_items, n=3)
            if top_3:
                return top_3, "history"

    return [], "default"


# ---------------------------------------------------------------------------
# Master Resolver
# ---------------------------------------------------------------------------

def resolve_all(
    travel_history: list[dict],
    nlp_intent: dict,
    user_home_airport: Optional[str] = None,
    user_prefs: Optional[dict] = None,
    explicit_origin: Optional[str] = None,
    explicit_destination: Optional[str] = None,
    explicit_destination_iata: Optional[str] = None,
    explicit_duration: Optional[int] = None,
    explicit_budget: Optional[int] = None,
) -> dict:
    """
    Master resolver: combines explicit input, NLP extraction, and profile inference.
    Priority: Explicit > NLP > Profile > Default

    travel_history should contain BookingHistory + EngagementSignal entries,
    each tagged with signal_strength (1.0 for bookings, 0.4 for engagement).

    Returns resolved dict with all travel parameters + inference sources for logging.
    """
    profile_strength = compute_profile_strength(travel_history)
    use_full_profile = profile_strength >= 1
    profile_confidence = "high" if profile_strength >= 2 else ("low" if profile_strength == 1 else "none")

    inference_log = {
        "profile_strength": profile_strength,
        "profile_confidence": profile_confidence,
        "use_full_profile": use_full_profile,
        "booking_count": sum(1 for t in travel_history if t.get("signal_strength", 1.0) >= 1.0),
        "engagement_count": sum(1 for t in travel_history if t.get("signal_strength", 1.0) < 1.0),
    }

    # --- Origin ---
    if explicit_origin:
        origin, origin_source = explicit_origin, "explicit"
    elif use_full_profile:
        origin, origin_source = infer_origin(travel_history, user_home_airport)
    else:
        origin = user_home_airport or "BOM"
        origin_source = "home_airport" if user_home_airport else "default"
    inference_log["origin_source"] = origin_source

    # --- Destination ---
    if explicit_destination_iata:
        dest_city = explicit_destination or nlp_intent.get("destination")
        dest_iata = explicit_destination_iata
        dest_source = "explicit"
    elif explicit_destination:
        nlp_with_dest = {**nlp_intent, "destination": explicit_destination}
        history_for_dest = travel_history if use_full_profile else []
        dest_city, dest_iata, dest_source = infer_destination(
            history_for_dest, nlp_with_dest, user_prefs, origin_iata=origin
        )
        dest_source = f"explicit_name+{dest_source}"
    elif use_full_profile:
        dest_city, dest_iata, dest_source = infer_destination(
            travel_history, nlp_intent, user_prefs, origin_iata=origin
        )
    else:
        dest_city, dest_iata, dest_source = infer_destination(
            [], nlp_intent, user_prefs, origin_iata=origin
        )
    inference_log["destination_source"] = dest_source

    # --- Duration ---
    if explicit_duration:
        duration, duration_source = explicit_duration, "explicit"
    elif use_full_profile:
        duration, duration_source = infer_duration(travel_history, nlp_intent)
    else:
        duration, duration_source = infer_duration([], nlp_intent)
    inference_log["duration_source"] = duration_source

    # --- Budget ---
    if explicit_budget:
        budget_min, budget_max = int(explicit_budget * 0.8), int(explicit_budget * 1.2)
        budget_source = "explicit"
    elif use_full_profile:
        budget_min, budget_max, budget_source = infer_budget(
            travel_history, nlp_intent, user_prefs
        )
    else:
        budget_min, budget_max, budget_source = infer_budget(
            [], nlp_intent, user_prefs
        )
    # Keep scalar budget for backward compat
    budget = explicit_budget or nlp_intent.get("budget_inr")
    inference_log["budget_source"] = budget_source
    inference_log["budget_range"] = [budget_min, budget_max]

    # --- Cabin ---
    if use_full_profile:
        cabin, cabin_source = infer_cabin(travel_history)
    else:
        cabin, cabin_source = "ECONOMY", "default"
    inference_log["cabin_source"] = cabin_source

    # --- Hotel preference ---
    if use_full_profile:
        hotel_pref, hotel_source = infer_hotel_preference(travel_history)
    else:
        hotel_pref, hotel_source = 4, "default"
    inference_log["hotel_preference_source"] = hotel_source

    # --- Airline preference ---
    if use_full_profile:
        airlines, airline_source = infer_airline_preference(travel_history, user_prefs)
    else:
        airlines, airline_source = [], "default"
    inference_log["airline_source"] = airline_source

    logger.info(f"Profile inference: {inference_log}")

    return {
        "origin_iata": origin,
        "destination": dest_city,
        "destination_iata": dest_iata,
        "duration_days": duration,
        "budget_inr": budget,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "cabin_preference": cabin,
        "hotel_star_preference": hotel_pref,
        "preferred_airlines": airlines,
        "inference_log": inference_log,
    }
