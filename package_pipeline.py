"""
Package Pipeline — Normalization, Tier Builder, Validator
Core deterministic engine: no LLM involvement in pricing or tier selection.

Pipeline: Amadeus Data → Normalize → Build Tiers → (LLM Narrative) → Validate
"""

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)

# Currency conversion — TODO: Replace with daily FX rate API for production
USD_TO_INR = 83.5
EUR_TO_INR = 91.0
GBP_TO_INR = 105.0

CURRENCY_TO_INR = {
    "INR": 1.0,
    "USD": USD_TO_INR,
    "EUR": EUR_TO_INR,
    "GBP": GBP_TO_INR,
}


# ==================== NORMALIZED DATA MODELS ====================


@dataclass
class NormalizedFlight:
    """Flight option with all prices in total INR."""
    carrier: str
    airline_name: str
    flight_number: str
    cabin: str  # ECONOMY, BUSINESS
    total_price_inr: float
    stops: int
    duration: str
    departure_time: str
    arrival_time: str
    data_source: str
    offer_id: Optional[str] = None
    # Return flight fields
    return_carrier: str = ""
    return_airline_name: str = ""
    return_flight_number: str = ""
    return_duration: str = ""
    return_stops: int = 0
    return_departure_time: str = ""
    return_arrival_time: str = ""

    @property
    def sort_key(self):
        """Deterministic sort: price → duration_minutes → carrier"""
        dur_min = _duration_to_minutes(self.duration)
        return (self.total_price_inr, dur_min, self.carrier)


@dataclass
class NormalizedHotel:
    """Hotel option with price normalized to total stay INR."""
    hotel_id: str
    name: str
    star_rating: Optional[int]
    price_per_night_inr: float
    total_stay_price_inr: float
    nights: int
    room_type: str
    data_source: str

    @property
    def sort_key(self):
        """Deterministic sort: total_price → star_rating_desc → name"""
        return (self.total_stay_price_inr, -(self.star_rating or 0), self.name)


@dataclass
class NormalizedActivity:
    """Activity with price normalized to total INR per person."""
    activity_id: Optional[str]
    name: str
    description: str
    price_per_person_inr: float
    currency_original: str
    fx_rate_used: float
    rating: Optional[float]
    category: Optional[str]
    data_source: str

    @property
    def sort_key(self):
        """Deterministic sort: rating_desc → price → name"""
        return (-(self.rating or 0), self.price_per_person_inr, self.name)


@dataclass
class NormalizedData:
    """Container for all normalized Amadeus data."""
    flights: list[NormalizedFlight] = field(default_factory=list)
    hotels: list[NormalizedHotel] = field(default_factory=list)
    activities: list[NormalizedActivity] = field(default_factory=list)
    data_quality: dict = field(default_factory=dict)


# ==================== TIER SELECTION MODELS ====================


@dataclass
class TierSelection:
    """One tier's selected components — deterministic, no LLM."""
    tier: str  # "budget", "standard", "premium"
    flight: Optional[NormalizedFlight]
    hotel: Optional[NormalizedHotel]
    activities: list[NormalizedActivity]
    estimated_total_inr: int
    activity_budget_per_day_inr: int
    budget_warning: Optional[str] = None
    limited_activity_data: bool = False
    preference_matches: list[str] = field(default_factory=list)
    personalization_reasons: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of post-LLM validation."""
    valid: bool
    errors: list[str]
    warnings: list[str]
    corrected_packages: list[dict]


# ==================== HELPERS ====================


def _duration_to_minutes(duration_str: str) -> int:
    """Convert ISO duration (PT5H30M) to minutes for sorting."""
    if not duration_str:
        return 9999
    try:
        d = duration_str.replace("PT", "")
        hours = 0
        minutes = 0
        if "H" in d:
            parts = d.split("H")
            hours = int(parts[0])
            d = parts[1] if len(parts) > 1 else ""
        if "M" in d:
            minutes = int(d.replace("M", ""))
        return hours * 60 + minutes
    except (ValueError, IndexError):
        return 9999


def _convert_to_inr(amount: float, currency: str) -> tuple[float, float]:
    """Convert amount to INR. Returns (amount_inr, fx_rate_used)."""
    currency = (currency or "USD").upper()
    rate = CURRENCY_TO_INR.get(currency, USD_TO_INR)
    return amount * rate, rate


# ==================== LAYER 1: NORMALIZATION ====================


def normalize_amadeus_data(
    flights_data: dict,
    hotels_data: dict,
    activities_data: dict,
    nights: int,
    adults: int = 1,
    max_flights: int = 8,
    max_hotels: int = 10,
    max_activities: int = 15,
) -> NormalizedData:
    """
    Normalize all Amadeus data into uniform, comparable format.
    - Convert all prices to total INR
    - Sort deterministically
    - Limit to top N per category
    - Compute per-component data quality
    """
    # --- Flights ---
    norm_flights = []
    for f in flights_data.get("flights", {}).get("all", []):
        price = float(f.get("price_inr", 0))
        if price <= 0:
            continue
        norm_flights.append(NormalizedFlight(
            carrier=f.get("carrier", ""),
            airline_name=f.get("airline_name", f.get("carrier", "")),
            flight_number=f.get("flight_number", ""),
            cabin=f.get("cabin", "ECONOMY"),
            total_price_inr=price,
            stops=f.get("stops", 0),
            duration=f.get("duration", ""),
            departure_time=f.get("departure_time", ""),
            arrival_time=f.get("arrival_time", ""),
            data_source=f.get("data_source", "amadeus"),
            offer_id=f.get("offer_id"),
            return_carrier=f.get("return_carrier", ""),
            return_airline_name=f.get("return_airline_name", ""),
            return_flight_number=f.get("return_flight_number", ""),
            return_duration=f.get("return_duration", ""),
            return_stops=f.get("return_stops", 0),
            return_departure_time=f.get("return_departure_time", ""),
            return_arrival_time=f.get("return_arrival_time", ""),
        ))
    norm_flights.sort(key=lambda f: f.sort_key)
    norm_flights = norm_flights[:max_flights]

    # --- Hotels ---
    norm_hotels = []
    for h in hotels_data.get("hotels", []):
        ppn = float(h.get("price_per_night_inr", h.get("price_per_night", 0)))
        if ppn <= 0:
            continue
        # Hotel price is per-room, NOT multiplied by adults
        total_stay = ppn * max(nights, 1)
        norm_hotels.append(NormalizedHotel(
            hotel_id=h.get("hotel_id", ""),
            name=h.get("name", "Unknown Hotel"),
            star_rating=h.get("star_rating"),
            price_per_night_inr=ppn,
            total_stay_price_inr=total_stay,
            nights=max(nights, 1),
            room_type=h.get("room_type", "STANDARD"),
            data_source=h.get("data_source", "estimated"),
        ))
    norm_hotels.sort(key=lambda h: h.sort_key)
    norm_hotels = norm_hotels[:max_hotels]

    # --- Activities ---
    norm_activities = []
    for a in activities_data.get("activities", []):
        raw_price = float(a.get("price") or 0)
        currency = a.get("currency", "USD")
        if raw_price > 0:
            price_inr, fx_rate = _convert_to_inr(raw_price, currency)
            price_per_person = price_inr  # Amadeus activities are per-person
        else:
            price_per_person = 0.0
            fx_rate = 1.0
            currency = "INR"

        norm_activities.append(NormalizedActivity(
            activity_id=a.get("id"),
            name=a.get("name", "Unknown Activity"),
            description=(a.get("description", "") or "")[:100],  # Truncate for token control
            price_per_person_inr=price_per_person,
            currency_original=currency,
            fx_rate_used=fx_rate,
            rating=float(a.get("rating") or 0),
            category=a.get("category"),
            data_source=a.get("data_source", "amadeus"),
        ))
    norm_activities.sort(key=lambda a: a.sort_key)
    norm_activities = norm_activities[:max_activities]

    # --- Data Quality (deterministic rules) ---
    # "amadeus" = fully live (price + name from API)
    # "amadeus_list" = partial live (real name from API, estimated price)
    flights_quality = "live" if any(f.data_source == "amadeus" for f in norm_flights) else "none"
    hotels_live = any(h.data_source == "amadeus" for h in norm_hotels)
    hotels_partial = any(h.data_source == "amadeus_list" for h in norm_hotels)
    hotels_quality = (
        "live" if hotels_live
        else "estimated" if hotels_partial or norm_hotels
        else "none"
    )
    activities_quality = "live" if any(a.data_source == "amadeus" for a in norm_activities) else "none"

    # Overall quality
    none_count = sum(1 for q in [flights_quality, hotels_quality, activities_quality] if q == "none")
    if none_count >= 2:
        overall = "insufficient_data"
    elif flights_quality == "live" and hotels_quality == "live" and activities_quality == "live":
        overall = "full_realtime"
    elif flights_quality == "none":
        overall = "estimated"
    else:
        overall = "partial_realtime"

    data_quality = {
        "flights": flights_quality,
        "hotels": hotels_quality,
        "activities": activities_quality,
        "overall": overall,
    }

    return NormalizedData(
        flights=norm_flights,
        hotels=norm_hotels,
        activities=norm_activities,
        data_quality=data_quality,
    )


# ==================== LAYER 2: DETERMINISTIC TIER BUILDER ====================


def _pick_flight(flights: list[NormalizedFlight], tier: str,
                 preferences: Optional[dict] = None) -> Optional[NormalizedFlight]:
    """Pick flight for a tier. Preference-driven, then deterministic.

    If user has cabin_preference → ALL tiers prefer that cabin.
    If user has preferred_airlines → narrow pool to those airlines.
    Within the filtered pool, pick by tier price position.
    """
    if not flights:
        return None

    cabin_pref = preferences.get("cabin_preference") if preferences else None
    preferred_airlines = preferences.get("preferred_airlines", []) if preferences else []

    # Step 1: Filter by inferred cabin preference
    pool = flights
    if cabin_pref:
        cabin_matches = [f for f in flights if f.cabin == cabin_pref]
        if cabin_matches:
            pool = cabin_matches
    else:
        # No preference: use original tier-based cabin logic
        economy = [f for f in flights if f.cabin == "ECONOMY"]
        business = [f for f in flights if f.cabin == "BUSINESS"]
        if tier == "premium" and business:
            pool = business
        elif economy:
            pool = economy

    # Step 2: Narrow by preferred airlines (if any)
    if preferred_airlines:
        airline_matches = [f for f in pool if f.carrier in preferred_airlines]
        if airline_matches:
            pool = airline_matches

    # Step 3: Pick by tier price position from filtered pool
    pool_sorted = sorted(pool, key=lambda f: f.total_price_inr)
    if tier == "budget":
        return pool_sorted[0]  # Cheapest in preferred pool
    elif tier == "standard":
        return pool_sorted[len(pool_sorted) // 2]  # Mid
    else:  # premium
        return pool_sorted[-1]  # Most expensive in preferred pool


def _pick_hotel(hotels: list[NormalizedHotel], tier: str,
                preferences: Optional[dict] = None) -> Optional[NormalizedHotel]:
    """Pick hotel for a tier. Preference-driven, then deterministic.

    If user has hotel_star_preference → ALL tiers prefer that star rating.
    Within the filtered pool, pick by tier price position.
    """
    if not hotels:
        return None

    star_pref = preferences.get("hotel_star_preference") if preferences else None

    if star_pref:
        # User has a star preference — use it for ALL tiers
        preferred_star = [h for h in hotels if h.star_rating == star_pref]
        if tier == "premium":
            # Premium: try preferred stars or one star up
            premium_pool = [h for h in hotels if h.star_rating >= star_pref]
            pool = premium_pool if premium_pool else (preferred_star if preferred_star else hotels)
        else:
            pool = preferred_star if preferred_star else hotels
    else:
        # No preference: use original tier-based star logic
        if tier == "budget":
            three_star = [h for h in hotels if h.star_rating == 3]
            pool = three_star if three_star else hotels
        elif tier == "standard":
            four_star = [h for h in hotels if h.star_rating == 4]
            pool = four_star if four_star else hotels
        else:
            five_star = [h for h in hotels if h.star_rating == 5]
            pool = five_star if five_star else hotels

    pool_sorted = sorted(pool, key=lambda h: h.total_stay_price_inr)
    if tier == "budget":
        return pool_sorted[0]  # Cheapest in preferred pool
    elif tier == "standard":
        return pool_sorted[len(pool_sorted) // 2]  # Mid
    else:  # premium
        return pool_sorted[-1]  # Most expensive in preferred pool


def _select_activities(
    activities: list[NormalizedActivity],
    max_daily_budget_inr: int,
    days: int,
    adults: int = 1,
    max_per_day: int = 3,
) -> list[NormalizedActivity]:
    """Select activities that fit within budget. Max 3/day."""
    if not activities:
        return []

    total_budget = max_daily_budget_inr * days
    selected = []
    total_cost = 0
    max_total = max_per_day * days

    for act in activities:
        cost = act.price_per_person_inr * adults
        if total_cost + cost <= total_budget and len(selected) < max_total:
            selected.append(act)
            total_cost += cost
        elif act.price_per_person_inr == 0 and len(selected) < max_total:
            # Free activities always included
            selected.append(act)

    return selected


def _compute_total(
    flight: Optional[NormalizedFlight],
    hotel: Optional[NormalizedHotel],
    activities: list[NormalizedActivity],
    adults: int = 1,
) -> int:
    """Compute deterministic package total. No LLM arithmetic."""
    total = 0.0
    if flight:
        total += flight.total_price_inr * adults
    if hotel:
        total += hotel.total_stay_price_inr
    for act in activities:
        total += act.price_per_person_inr * adults
    return int(round(total))


def _apply_personalization_scoring(
    flights: list[NormalizedFlight],
    hotels: list[NormalizedHotel],
    activities: list[NormalizedActivity],
    preferences: Optional[dict] = None,
) -> tuple[list[NormalizedFlight], list[NormalizedHotel], list[NormalizedActivity], list[str]]:
    """
    Apply capped personalization boost (max 20%) before tier slicing.
    Does NOT change prices, only affects ranking.
    Returns the re-sorted lists + preference match descriptions.
    """
    matches = []
    if not preferences:
        return flights, hotels, activities, matches

    preferred_airlines = preferences.get("preferred_airlines", [])
    interests = preferences.get("interests", [])
    accommodation_pref = preferences.get("accommodation_preference")

    # Boost preferred airlines (max 15% influence via sorting position)
    if preferred_airlines and flights:
        def flight_score(f):
            base = f.sort_key
            boost = 0.85 if f.carrier in preferred_airlines else 1.0
            return (base[0] * boost, base[1], base[2])
        flights = sorted(flights, key=flight_score)
        matches.append(f"preferred airlines: {', '.join(preferred_airlines)}")

    # Boost interest-matching activities (max 20%)
    if interests and activities:
        interest_set = set(i.lower() for i in interests)

        def activity_score(a):
            base = a.sort_key
            cat = (a.category or "").lower()
            has_match = any(interest in cat or interest in a.name.lower() for interest in interest_set)
            boost = 0.8 if has_match else 1.0
            return (base[0] * boost, base[1], base[2])
        activities = sorted(activities, key=activity_score)
        matches.append(f"interests: {', '.join(interests)}")

    # Boost accommodation preference (max 10%)
    if accommodation_pref and hotels:
        pref_lower = accommodation_pref.lower()

        def hotel_score(h):
            base = h.sort_key
            name_lower = h.name.lower()
            has_match = pref_lower in name_lower or (
                pref_lower == "resort" and "resort" in name_lower
            )
            boost = 0.9 if has_match else 1.0
            return (base[0] * boost, base[1], base[2])
        hotels = sorted(hotels, key=hotel_score)
        matches.append(f"accommodation: {accommodation_pref}")

    return flights, hotels, activities, matches


def _generate_personalization_reasons(
    flight: Optional[NormalizedFlight],
    hotel: Optional[NormalizedHotel],
    preferences: Optional[dict],
    nights: int,
) -> list[str]:
    """
    Generate human-readable personalization reasons for a tier.
    These are displayed as gold tags on the UI tier cards.
    """
    if not preferences:
        return []

    reasons = []
    preferred_airlines = preferences.get("preferred_airlines", [])
    cabin_pref = preferences.get("cabin_preference")
    hotel_star_pref = preferences.get("hotel_star_preference")
    duration_source = preferences.get("duration_source")

    # Airline match
    if flight and preferred_airlines and flight.carrier in preferred_airlines:
        reasons.append(f"{flight.airline_name} \u2014 your preferred airline")

    # Cabin class match
    if flight and cabin_pref and flight.cabin == cabin_pref:
        reasons.append(f"{flight.cabin.replace('_', ' ').title()} class \u2014 your usual travel style")

    # Hotel star match
    if hotel and hotel_star_pref and hotel.star_rating == hotel_star_pref:
        reasons.append(f"{hotel.star_rating}\u2605 hotel matches your preference")

    # Duration inferred from history
    if duration_source == "history":
        reasons.append(f"{nights}-day trip matches your typical duration")

    return reasons


def build_tiers(
    data: NormalizedData,
    nights: int,
    adults: int = 1,
    budget_inr: Optional[int] = None,
    budget_min: Optional[int] = None,
    budget_max: Optional[int] = None,
    preferences: Optional[dict] = None,
) -> list[TierSelection]:
    """
    Deterministic tier assignment. LLM does NOT participate.

    Budget: cheapest economy + cheapest hotel (3-star) + INR 2,000/day activities
    Standard: median flight + mid-range hotel (4-star) + INR 4,000/day activities
    Premium: business class + best hotel (5-star) + INR 8,000/day activities

    Ordering enforced: budget.total < standard.total < premium.total
    Budget adaptation: only on budget tier, never on standard/premium.
    """
    # Apply personalization scoring before slicing
    flights, hotels, activities, pref_matches = _apply_personalization_scoring(
        data.flights, data.hotels, data.activities, preferences
    )

    limited_activity = len(activities) < nights  # Fewer activities than days

    tier_configs = [
        ("budget", 2000),
        ("standard", 4000),
        ("premium", 8000),
    ]

    tiers = []
    for tier_name, daily_cap in tier_configs:
        flight = _pick_flight(flights, tier_name, preferences)
        hotel = _pick_hotel(hotels, tier_name, preferences)
        acts = _select_activities(activities, daily_cap, nights, adults)
        total = _compute_total(flight, hotel, acts, adults)

        # Generate per-tier personalization reasons
        reasons = _generate_personalization_reasons(flight, hotel, preferences, nights)

        tiers.append(TierSelection(
            tier=tier_name,
            flight=flight,
            hotel=hotel,
            activities=acts,
            estimated_total_inr=total,
            activity_budget_per_day_inr=daily_cap,
            limited_activity_data=limited_activity,
            preference_matches=pref_matches if tier_name == "standard" else [],
            personalization_reasons=reasons,
        ))

    # Enforce ordering: sort by total, assign labels
    tiers.sort(key=lambda t: t.estimated_total_inr)
    tiers[0].tier = "budget"
    tiers[1].tier = "standard"
    tiers[2].tier = "premium"

    # Budget adaptation — use budget_min as ceiling for budget tier
    effective_budget = budget_min or budget_inr
    if effective_budget and tiers[0].estimated_total_inr > effective_budget:
        adapted = _adapt_budget_tier(tiers[0], data, nights, adults, effective_budget)
        if adapted:
            tiers[0] = adapted

    return tiers


def _adapt_budget_tier(
    tier: TierSelection,
    data: NormalizedData,
    nights: int,
    adults: int,
    budget_inr: int,
) -> Optional[TierSelection]:
    """
    Try to adapt budget tier to fit within user's budget.
    Strategy: downgrade hotel → switch flight → reduce activity budget.
    Only modifies budget tier. Returns None if no adaptation possible.
    """
    flights = sorted(data.flights, key=lambda f: f.sort_key)
    hotels = sorted(data.hotels, key=lambda h: h.sort_key)

    # Try cheapest flight
    cheapest_flight = flights[0] if flights else tier.flight
    # Try cheapest hotel (any star rating)
    cheapest_hotel = hotels[0] if hotels else tier.hotel
    # Try minimal activities (INR 1,000/day)
    minimal_acts = _select_activities(data.activities, 1000, nights, adults)

    total = _compute_total(cheapest_flight, cheapest_hotel, minimal_acts, adults)

    if total <= budget_inr:
        return TierSelection(
            tier="budget",
            flight=cheapest_flight,
            hotel=cheapest_hotel,
            activities=minimal_acts,
            estimated_total_inr=total,
            activity_budget_per_day_inr=1000,
            limited_activity_data=tier.limited_activity_data,
            preference_matches=tier.preference_matches,
            personalization_reasons=tier.personalization_reasons,
        )

    # Still over budget — add warning
    tier.budget_warning = (
        f"Minimum package (INR {tier.estimated_total_inr:,}) exceeds "
        f"your budget of INR {budget_inr:,}. "
        f"Consider adjusting dates or destination."
    )
    return tier


# ==================== LAYER 3: ITINERARY ACTIVITY VALIDATION ====================

# Freeform activities that are NOT from Amadeus data — always allowed
_FREEFORM_KEYWORDS = {
    "free time", "leisure", "explore", "departure", "arrival",
    "check-in", "check-out", "rest", "relax", "at leisure", "on your own",
    "travel day", "transfer", "airport",
}

ACT_TOKEN_PATTERN = re.compile(r"\[ACT-(\d+)\]")


def _validate_itinerary_activities(
    daily_itinerary: list[dict],
    valid_activities: dict,
    threshold: float = 0.6,
) -> tuple[list[dict], list[str]]:
    """
    Validate itinerary activities against known Amadeus activities.

    Two-step matching:
    1. Check for [ACT-N] ID token in activity text -> exact match by ID
    2. Fallback: fuzzy name matching via SequenceMatcher

    Args:
        daily_itinerary: LLM-generated daily itinerary (list of day dicts)
        valid_activities: dict of {act_id: canonical_name} from tier selection
        threshold: minimum SequenceMatcher ratio for fuzzy match (default 0.6)

    Returns:
        (corrected_itinerary, warnings)
    """
    if not daily_itinerary or not valid_activities:
        return daily_itinerary or [], []

    warnings = []
    corrected = []

    # Build reverse lookup: lowercase canonical name -> (act_id, canonical_name)
    name_lookup = {name.lower(): (act_id, name) for act_id, name in valid_activities.items()}
    # ID lookup: "1" -> canonical_name
    id_lookup = {str(act_id): name for act_id, name in valid_activities.items()}

    for day_entry in daily_itinerary:
        if not isinstance(day_entry, dict):
            corrected.append(day_entry)
            continue

        corrected_day = {**day_entry}
        day_activities = day_entry.get("activities", [])
        corrected_activities = []

        for act_entry in day_activities:
            if not isinstance(act_entry, dict):
                corrected_activities.append(act_entry)
                continue

            activity_text = act_entry.get("activity", "")
            activity_lower = activity_text.lower().strip()

            # Skip freeform activities (leisure, explore, departure, etc.)
            if any(kw in activity_lower for kw in _FREEFORM_KEYWORDS):
                corrected_activities.append(act_entry)
                continue

            matched = False

            # Step 1: Check for [ACT-N] token
            token_match = ACT_TOKEN_PATTERN.search(activity_text)
            if token_match:
                act_num = token_match.group(1)
                if act_num in id_lookup:
                    canonical_name = id_lookup[act_num]
                    # Keep the LLM's text but ensure it references the right activity
                    corrected_entry = {**act_entry}
                    # If the name is wildly different from canonical, correct it
                    clean_text = ACT_TOKEN_PATTERN.sub("", activity_text).strip(" -:")
                    ratio = SequenceMatcher(None, clean_text.lower(), canonical_name.lower()).ratio()
                    if ratio < 0.5:
                        # LLM used the ID token but changed the name significantly
                        corrected_entry["activity"] = f"[ACT-{act_num}] {canonical_name}"
                        warnings.append(
                            f"Day {day_entry.get('day', '?')}: corrected '{activity_text}' -> '{canonical_name}' (matched by ID)"
                        )
                    corrected_activities.append(corrected_entry)
                    matched = True
                else:
                    warnings.append(
                        f"Day {day_entry.get('day', '?')}: invalid ACT token [ACT-{act_num}] in '{activity_text}'"
                    )

            # Step 2: Fuzzy name match (if no ID token matched)
            if not matched:
                best_ratio = 0.0
                best_name = None
                best_id = None

                for name_lower, (act_id, canonical) in name_lookup.items():
                    ratio = SequenceMatcher(None, activity_lower, name_lower).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_name = canonical
                        best_id = act_id

                if best_ratio >= threshold:
                    corrected_entry = {**act_entry}
                    if best_ratio < 0.95:
                        # Near match — correct to canonical name
                        corrected_entry["activity"] = best_name
                        warnings.append(
                            f"Day {day_entry.get('day', '?')}: fuzzy-matched '{activity_text}' -> "
                            f"'{best_name}' (ratio={best_ratio:.2f})"
                        )
                    corrected_activities.append(corrected_entry)
                else:
                    # Both matching strategies failed — replace with free time
                    corrected_entry = {
                        **act_entry,
                        "activity": "Free time / explore the city",
                        "estimated_cost_inr": 0,
                        "data_source": "suggested",
                    }
                    corrected_activities.append(corrected_entry)
                    warnings.append(
                        f"Day {day_entry.get('day', '?')}: LLM-invented activity '{activity_text}' "
                        f"replaced with free time (best fuzzy={best_ratio:.2f})"
                    )

        corrected_day["activities"] = corrected_activities
        corrected.append(corrected_day)

    return corrected, warnings


# ==================== LAYER 3: POST-LLM VALIDATOR ====================


REQUIRED_PACKAGE_FIELDS = {
    "tier", "name", "tagline", "destination_city", "destination_iata",
    "duration_days", "estimated_total_inr", "hotel", "flights",
    "daily_itinerary", "inclusions", "highlights",
}

REQUIRED_HOTEL_FIELDS = {"name", "star_rating", "price_per_night_inr", "data_source"}
REQUIRED_FLIGHT_FIELDS = {"airline_name", "travel_class", "price_inr", "data_source"}


def validate_llm_response(
    raw_json: dict,
    tier_selections: list[TierSelection],
    destination: str,
    destination_iata: str,
    duration_days: int,
) -> ValidationResult:
    """
    Validate and auto-correct LLM response.
    The LLM writes narrative only — we overwrite all pricing/selection with tier data.
    """
    errors = []
    warnings = []
    corrected_packages = []

    llm_packages = raw_json.get("packages", [])
    if not isinstance(llm_packages, list):
        errors.append("packages is not a list")
        llm_packages = []

    # Build tier lookup
    tier_map = {t.tier: t for t in tier_selections}

    for tier_sel in tier_selections:
        # Find matching LLM narrative
        llm_pkg = None
        for lp in llm_packages:
            if isinstance(lp, dict) and lp.get("tier") == tier_sel.tier:
                llm_pkg = lp
                break

        if not llm_pkg:
            warnings.append(f"LLM did not generate narrative for {tier_sel.tier} tier — using defaults")
            llm_pkg = {}

        # Build corrected package: deterministic data + LLM narrative
        pkg = _build_corrected_package(tier_sel, llm_pkg, destination, destination_iata, duration_days)

        # Schema validation
        missing = REQUIRED_PACKAGE_FIELDS - set(pkg.keys())
        if missing:
            warnings.append(f"{tier_sel.tier}: missing fields {missing}, filled with defaults")

        # Validate itinerary activities against selected activities
        if pkg.get("daily_itinerary") and tier_sel.activities:
            valid_acts = {}
            for idx, act in enumerate(tier_sel.activities, start=1):
                valid_acts[str(idx)] = act.name
            corrected_itin, act_warnings = _validate_itinerary_activities(
                pkg["daily_itinerary"], valid_acts
            )
            pkg["daily_itinerary"] = corrected_itin
            warnings.extend(act_warnings)

        corrected_packages.append(pkg)

    # Verify tier ordering
    totals = [p["estimated_total_inr"] for p in corrected_packages]
    if totals != sorted(totals):
        warnings.append("Tier ordering was incorrect — re-sorted")
        corrected_packages.sort(key=lambda p: p["estimated_total_inr"])
        for i, label in enumerate(["budget", "standard", "premium"]):
            corrected_packages[i]["tier"] = label

    valid = len(errors) == 0
    return ValidationResult(
        valid=valid,
        errors=errors,
        warnings=warnings,
        corrected_packages=corrected_packages,
    )


def _build_corrected_package(
    tier_sel: TierSelection,
    llm_narrative: dict,
    destination: str,
    destination_iata: str,
    duration_days: int,
) -> dict:
    """Merge deterministic tier data with LLM narrative. Tier data always wins."""

    # Flight data (deterministic)
    flight_data = {}
    if tier_sel.flight:
        flight_data = {
            "airline_name": tier_sel.flight.airline_name,
            "flight_number": tier_sel.flight.flight_number,
            "travel_class": tier_sel.flight.cabin,
            "price_inr": int(tier_sel.flight.total_price_inr),
            "stops": tier_sel.flight.stops,
            "duration": tier_sel.flight.duration,
            "departure_time": tier_sel.flight.departure_time,
            "arrival_time": tier_sel.flight.arrival_time,
            "data_source": tier_sel.flight.data_source,
            "offer_id": tier_sel.flight.offer_id,
            # Return flight
            "return_carrier": tier_sel.flight.return_carrier,
            "return_airline_name": tier_sel.flight.return_airline_name,
            "return_flight_number": tier_sel.flight.return_flight_number,
            "return_duration": tier_sel.flight.return_duration,
            "return_stops": tier_sel.flight.return_stops,
            "return_departure_time": tier_sel.flight.return_departure_time,
            "return_arrival_time": tier_sel.flight.return_arrival_time,
        }
    else:
        flight_data = llm_narrative.get("flights", {
            "airline_name": "TBD", "travel_class": "ECONOMY",
            "price_inr": 0, "stops": 0, "duration": "", "data_source": "estimated",
        })

    # Hotel data (deterministic)
    hotel_data = {}
    if tier_sel.hotel:
        hotel_data = {
            "name": tier_sel.hotel.name,
            "hotel_id": tier_sel.hotel.hotel_id,
            "star_rating": tier_sel.hotel.star_rating,
            "price_per_night_inr": int(tier_sel.hotel.price_per_night_inr),
            "area": "",
            "data_source": tier_sel.hotel.data_source,
        }
    else:
        hotel_data = llm_narrative.get("hotel", {
            "name": "TBD", "star_rating": 3, "price_per_night_inr": 0,
            "area": "", "data_source": "estimated",
        })

    # Narrative from LLM (or defaults)
    return {
        "tier": tier_sel.tier,
        "name": llm_narrative.get("name", f"{tier_sel.tier.title()} {destination}"),
        "tagline": llm_narrative.get("tagline", f"Explore {destination}"),
        "destination_city": destination,
        "destination_iata": destination_iata,
        "duration_days": duration_days,
        "estimated_total_inr": tier_sel.estimated_total_inr,
        "hotel": hotel_data,
        "flights": flight_data,
        "daily_itinerary": llm_narrative.get("daily_itinerary", _default_itinerary(
            tier_sel.activities, duration_days
        )),
        "inclusions": llm_narrative.get("inclusions", _default_inclusions(tier_sel)),
        "highlights": llm_narrative.get("highlights", [
            f"{tier_sel.tier.title()} tier", f"{duration_days}-day trip", destination
        ]),
        "budget_warning": tier_sel.budget_warning,
        "limited_activity_data": tier_sel.limited_activity_data,
        "preference_matches": tier_sel.preference_matches,
        "personalization_reasons": tier_sel.personalization_reasons,
        "data_quality_detail": None,  # Set by caller
    }


def _default_itinerary(activities: list[NormalizedActivity], days: int) -> list[dict]:
    """Generate a basic itinerary from selected activities."""
    itinerary = []
    act_idx = 0
    times = ["morning", "afternoon", "evening"]

    for day in range(1, days + 1):
        day_activities = []
        for t in times:
            if act_idx < len(activities):
                act = activities[act_idx]
                day_activities.append({
                    "time": t,
                    "activity": act.name,
                    "estimated_cost_inr": int(act.price_per_person_inr),
                    "data_source": act.data_source,
                })
                act_idx += 1
            else:
                day_activities.append({
                    "time": t,
                    "activity": "Free time / explore the city",
                    "estimated_cost_inr": 0,
                    "data_source": "suggested",
                })

        itinerary.append({
            "day": day,
            "title": f"Day {day}",
            "activities": day_activities,
        })

    return itinerary


def _default_inclusions(tier_sel: TierSelection) -> list[str]:
    """Generate default inclusions from tier selection."""
    inclusions = []
    if tier_sel.flight:
        cabin = tier_sel.flight.cabin.replace("_", " ").title()
        inclusions.append(f"Round-trip {cabin} flights")
    if tier_sel.hotel:
        star = f"{tier_sel.hotel.star_rating}-star" if tier_sel.hotel.star_rating else ""
        inclusions.append(f"{tier_sel.hotel.nights} nights at {star} hotel")
    if tier_sel.activities:
        inclusions.append(f"{len(tier_sel.activities)} curated activities")
    return inclusions
