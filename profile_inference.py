"""
Profile Intelligence Engine — Rule-Based User Inference
Deterministic inference from user travel history and preferences.
Runs BEFORE Amadeus calls, AFTER NLP extraction.
No LLM involvement.

Priority order: Explicit user input > NLP extraction > Profile defaults
"""

import logging
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

# MVP gateway mapping — configurable, easy to extract to config/DB later
COUNTRY_GATEWAYS = {
    # Asia
    "India": "DEL", "Thailand": "BKK", "Japan": "NRT", "Singapore": "SIN",
    "Malaysia": "KUL", "Indonesia": "DPS", "Vietnam": "SGN", "Philippines": "MNL",
    "South Korea": "ICN", "China": "PEK", "Hong Kong": "HKG", "Sri Lanka": "CMB",
    "Maldives": "MLE",
    # Middle East
    "UAE": "DXB", "Dubai": "DXB", "Qatar": "DOH", "Oman": "MCT",
    "Bahrain": "BAH", "Saudi Arabia": "RUH",
    # Europe
    "UK": "LHR", "England": "LHR", "France": "CDG", "Germany": "FRA",
    "Netherlands": "AMS", "Italy": "FCO", "Spain": "BCN", "Turkey": "IST",
    "Switzerland": "ZRH", "Austria": "VIE",
    # Americas
    "USA": "JFK", "Canada": "YYZ", "United States": "JFK",
    # Oceania
    "Australia": "SYD", "New Zealand": "AKL",
    # Africa
    "South Africa": "JNB", "Egypt": "CAI", "Kenya": "NBO",
}

# Interest-to-gateway overrides (when interest conflicts with default gateway)
INTEREST_GATEWAY_OVERRIDES = {
    "Canada": {
        "skiing": "YYC",    # Calgary for skiing
        "snow": "YYC",
        "winter sports": "YYC",
        "nature": "YVR",    # Vancouver for nature
        "mountains": "YVR",
    },
    "USA": {
        "beach": "MIA",     # Miami for beach
        "skiing": "DEN",    # Denver for skiing
        "tech": "SFO",      # SF for tech
        "entertainment": "LAX",
    },
    "Australia": {
        "beach": "OOL",     # Gold Coast for beach
        "nature": "CNS",    # Cairns for nature/reef
    },
}

# IATA code to country mapping (reverse lookup for history matching)
IATA_TO_COUNTRY = {
    "YYZ": "Canada", "YVR": "Canada", "YYC": "Canada", "YUL": "Canada",
    "JFK": "USA", "LAX": "USA", "SFO": "USA", "ORD": "USA", "MIA": "USA",
    "LHR": "UK", "CDG": "France", "FRA": "Germany", "AMS": "Netherlands",
    "FCO": "Italy", "BCN": "Spain", "MAD": "Spain", "IST": "Turkey",
    "DXB": "UAE", "DOH": "Qatar", "BKK": "Thailand", "SIN": "Singapore",
    "NRT": "Japan", "ICN": "South Korea", "SYD": "Australia", "MEL": "Australia",
    "DEL": "India", "BOM": "India", "BLR": "India", "MAA": "India",
    "HYD": "India", "CCU": "India", "GOI": "India", "COK": "India",
    "DPS": "Indonesia", "SGN": "Vietnam", "HAN": "Vietnam",
    "MLE": "Maldives", "CMB": "Sri Lanka", "JNB": "South Africa",
    "CAI": "Egypt", "NBO": "Kenya", "PEK": "China", "PVG": "China",
    "HKG": "Hong Kong", "KUL": "Malaysia", "MNL": "Philippines",
    "BAH": "Bahrain", "MCT": "Oman", "RUH": "Saudi Arabia",
    "ZRH": "Switzerland", "VIE": "Austria", "MUC": "Germany",
}


def compute_profile_strength(travel_history: list[dict]) -> int:
    """
    Compute profile confidence score.
    Only apply full inference if strength >= 2.

    +1 if at least one trip within last 24 months
    +1 if total trip count >= 3
    """
    strength = 0
    if len(travel_history) >= 3:
        strength += 1

    cutoff = datetime.utcnow() - timedelta(days=730)  # 24 months
    for trip in travel_history:
        searched_at = trip.get("searched_at")
        if searched_at:
            if isinstance(searched_at, str):
                try:
                    searched_at = datetime.fromisoformat(searched_at)
                except (ValueError, TypeError):
                    continue
            if searched_at > cutoff:
                strength += 1
                break

    return strength


def infer_origin(
    travel_history: list[dict],
    user_home_airport: Optional[str] = None,
) -> tuple[str, str]:
    """
    Infer departure airport.
    Returns: (iata_code, source) where source is "home_airport"|"history"|"default"
    """
    if user_home_airport:
        return user_home_airport, "home_airport"

    if travel_history:
        origins = [t.get("origin_iata") for t in travel_history if t.get("origin_iata")]
        if origins:
            most_common = Counter(origins).most_common(1)[0][0]
            return most_common, "history"

    return "BOM", "default"


def infer_destination(
    travel_history: list[dict],
    nlp_intent: dict,
    user_prefs: Optional[dict] = None,
) -> tuple[Optional[str], Optional[str], str]:
    """
    Resolve destination IATA code.
    Returns: (destination_city, destination_iata, source)
    Source: "explicit"|"nlp_city"|"history_country"|"interest_override"|"gateway"|"preferred"|None
    """
    # Priority 1: NLP extracted specific city with IATA
    if nlp_intent.get("destination_iata"):
        return nlp_intent.get("destination"), nlp_intent["destination_iata"], "nlp_city"

    # Priority 2: NLP extracted destination name (might be country or city)
    destination = nlp_intent.get("destination")
    if destination:
        # Check if it's a country
        country_key = destination.strip().title()
        if country_key in COUNTRY_GATEWAYS:
            # It's a country — check history first
            interests = nlp_intent.get("interests", [])

            # Check interest-based gateway override
            if country_key in INTEREST_GATEWAY_OVERRIDES and interests:
                for interest in interests:
                    interest_lower = interest.lower()
                    overrides = INTEREST_GATEWAY_OVERRIDES[country_key]
                    if interest_lower in overrides:
                        iata = overrides[interest_lower]
                        return destination, iata, "interest_override"

            # Check user history for past trips to this country
            if travel_history:
                country_trips = []
                for trip in travel_history:
                    dest_iata = trip.get("destination_iata")
                    if dest_iata and IATA_TO_COUNTRY.get(dest_iata) == country_key:
                        country_trips.append(dest_iata)

                if country_trips:
                    # Reuse most visited city in that country
                    most_visited = Counter(country_trips).most_common(1)[0][0]
                    return destination, most_visited, "history_country"

            # Fallback to default gateway for that country
            gateway = COUNTRY_GATEWAYS[country_key]
            return destination, gateway, "gateway"

        # Not a known country — might be a city name, let IATA extractor handle downstream
        return destination, None, "nlp_city_unresolved"

    # Priority 3: Use user's preferred destinations
    if user_prefs and user_prefs.get("preferred_destinations"):
        prefs = user_prefs["preferred_destinations"]
        # Filter out already-visited destinations
        visited = set()
        for trip in travel_history:
            if trip.get("destination_iata"):
                visited.add(trip["destination_iata"])

        for pref in prefs:
            pref_upper = pref.strip().upper()
            if len(pref_upper) == 3 and pref_upper not in visited:
                return None, pref_upper, "preferred"

    return None, None, "none"


def infer_duration(
    travel_history: list[dict],
    nlp_intent: dict,
) -> tuple[int, str]:
    """
    Infer trip duration.
    Returns: (days, source)
    """
    # Priority 1: NLP extracted duration
    if nlp_intent.get("duration_days"):
        return nlp_intent["duration_days"], "nlp"

    # Priority 2: Median from user history
    if travel_history:
        durations = [
            t["duration_days"] for t in travel_history
            if t.get("duration_days") and t["duration_days"] > 0
        ]
        if durations:
            durations.sort()
            median = durations[len(durations) // 2]
            return median, "history"

    return 7, "default"


def infer_cabin(travel_history: list[dict]) -> tuple[str, str]:
    """
    Infer preferred cabin class from history.
    Returns: (cabin_class, source)
    """
    if travel_history:
        cabins = [
            t.get("cabin_class") for t in travel_history
            if t.get("cabin_class")
        ]
        if cabins:
            most_common = Counter(cabins).most_common(1)[0][0]
            return most_common, "history"

    return "ECONOMY", "default"


def infer_hotel_preference(travel_history: list[dict]) -> tuple[int, str]:
    """
    Infer preferred hotel star rating.
    Returns: (star_rating, source)
    """
    if travel_history:
        ratings = [
            t.get("hotel_star_rating") for t in travel_history
            if t.get("hotel_star_rating")
        ]
        if ratings:
            most_common = Counter(ratings).most_common(1)[0][0]
            return most_common, "history"

    return 4, "default"


def infer_airline_preference(
    travel_history: list[dict],
    user_prefs: Optional[dict] = None,
) -> tuple[list[str], str]:
    """
    Infer preferred airlines.
    Returns: (carrier_codes, source)
    """
    # Priority 1: Explicit user preferences
    if user_prefs and user_prefs.get("preferred_airlines"):
        return user_prefs["preferred_airlines"], "preferences"

    # Priority 2: Top 3 most-used carriers from history
    if travel_history:
        carriers = [
            t.get("carrier") for t in travel_history
            if t.get("carrier")
        ]
        if carriers:
            top_3 = [code for code, _ in Counter(carriers).most_common(3)]
            return top_3, "history"

    return [], "default"


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

    Returns resolved dict with all travel parameters + inference sources for logging.
    """
    profile_strength = compute_profile_strength(travel_history)
    use_full_profile = profile_strength >= 2

    inference_log = {
        "profile_strength": profile_strength,
        "use_full_profile": use_full_profile,
    }

    # --- Origin ---
    if explicit_origin:
        origin, origin_source = explicit_origin, "explicit"
    elif use_full_profile:
        origin, origin_source = infer_origin(travel_history, user_home_airport)
    else:
        origin, origin_source = user_home_airport or "BOM", "home_airport" if user_home_airport else "default"
    inference_log["origin_source"] = origin_source

    # --- Destination ---
    if explicit_destination_iata:
        dest_city = explicit_destination or nlp_intent.get("destination")
        dest_iata = explicit_destination_iata
        dest_source = "explicit"
    elif explicit_destination:
        # Explicit city name but no IATA — let NLP/profile resolve IATA
        nlp_with_dest = {**nlp_intent, "destination": explicit_destination}
        if use_full_profile:
            dest_city, dest_iata, dest_source = infer_destination(
                travel_history, nlp_with_dest, user_prefs
            )
        else:
            dest_city, dest_iata, dest_source = infer_destination(
                [], nlp_with_dest, user_prefs
            )
        dest_source = f"explicit_name+{dest_source}"
    elif use_full_profile:
        dest_city, dest_iata, dest_source = infer_destination(
            travel_history, nlp_intent, user_prefs
        )
    else:
        dest_city, dest_iata, dest_source = infer_destination(
            [], nlp_intent, user_prefs
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
    budget = explicit_budget or nlp_intent.get("budget_inr")
    budget_source = "explicit" if explicit_budget else ("nlp" if budget else "none")
    inference_log["budget_source"] = budget_source

    # --- Cabin (profile only, no explicit/NLP field for this) ---
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

    # Log inference decisions
    logger.info(f"Profile inference: {inference_log}")

    return {
        "origin_iata": origin,
        "destination": dest_city,
        "destination_iata": dest_iata,
        "duration_days": duration,
        "budget_inr": budget,
        "cabin_preference": cabin,
        "hotel_star_preference": hotel_pref,
        "preferred_airlines": airlines,
        "inference_log": inference_log,
    }
