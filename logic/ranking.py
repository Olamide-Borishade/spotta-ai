from datetime import datetime
from math import atan2, cos, radians, sin, sqrt

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SpottaAI/1.0 (POC project)"  # TODO: replace with a real contact if this goes beyond a POC


def geocode_destination(destination_text):
    """Converts a typed destination into (lat, lng) using OpenStreetMap Nominatim.

    Returns None if no match is found or the request fails.
    """
    if not destination_text:
        return None

    params = {
        "q": f"{destination_text}, Vancouver, BC, Canada",
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        return (lat, lng)
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def haversine_distance(lat1, lng1, lat2, lng2):
    """Returns distance in kilometers between two lat/lng points."""
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# Vancouver street meters are typically enforced roughly 9am-8pm Monday-Saturday
# and largely unrestricted on Sundays. Demand (and therefore how likely a spot
# is open) tends to peak on weekday middays and right after the workday ends.
ENFORCED_START_HOUR = 9
ENFORCED_END_HOUR = 20
PEAK_HOURS = ((11, 14), (16, 18))

# How much a spot's relative price (vs. others in the same result set) can
# pull its confidence down, since pricier meters tend to sit in higher-demand
# areas.
PRICE_DEMAND_WEIGHT = 0.25


def _time_of_day_base(now):
    if now.weekday() == 6:  # Sunday
        return 0.9

    hour = now.hour
    if hour < ENFORCED_START_HOUR or hour >= ENFORCED_END_HOUR:
        return 0.85
    if any(start <= hour < end for start, end in PEAK_HOURS):
        return 0.45
    return 0.65


def estimate_confidence(spot, price_range, now=None):
    """Estimates how likely a spot is to be open right now.

    Combines two real signals instead of a fixed or simulated number:
    time of day/day of week, and the spot's price relative to others in the
    current result set. This is still an estimate, not live occupancy data,
    and is recomputed on every request rather than stored.
    """
    now = now or datetime.now()
    base = _time_of_day_base(now)

    min_price, max_price = price_range
    if max_price > min_price:
        relative_price = (spot["price_per_hour"] - min_price) / (max_price - min_price)
    else:
        relative_price = 0.0

    demand_penalty = relative_price * PRICE_DEMAND_WEIGHT
    return max(0.0, min(1.0, base - demand_penalty))


def score_spot(spot):
    """Rule-based placeholder score, favoring close/cheap/confident spots.

    # TODO: replace with LLM/ML ranking model later
    """
    distance_score = 1 / (1 + spot["distance_km"])
    price_score = 1 / (1 + spot["price_per_hour"])
    confidence_score = spot["confidence"]

    return (distance_score * 0.4) + (price_score * 0.3) + (confidence_score * 0.3)


def rank_spots(spots):
    return sorted(spots, key=score_spot, reverse=True)
