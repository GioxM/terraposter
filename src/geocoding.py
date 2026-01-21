# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.2.1
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.0.0: First modular version – config, fonts, themes extracted
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message + map_data.py & styling.py + poster.py rendering core
# - 2026-01-20 v2.1.1: Added distance clamping (min 1500m, max 60000m) with user feedback messages
# - 2026-01-20 v2.2.0: Added rate-limiting & retry logic for Nominatim and OSMnx calls to improve robustness
# - 2026-01-20 v2.2.1: Extracted retry logic into src/utils.py for reuse across network-heavy modules
# ===========================================

# src/geocoding.py

import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from .utils import retry_call


def get_coordinates(city: str, country: str) -> tuple[float, float]:
    """
    Fetch latitude/longitude for city + country using Nominatim with retries.
    """
    geolocator = Nominatim(user_agent="city_map_poster_generator", timeout=10)
    
    query = f"{city}, {country}"
    
    print("Looking up coordinates...")
    
    # Use the shared retry helper — clean and reusable
    location = retry_call(
        lambda: geolocator.geocode(query),
        max_retries=4,  # slightly more generous for geocoding
        base_sleep=1.5,
        exceptions=(GeocoderTimedOut, GeocoderUnavailable, Exception)
    )
    
    if location is None:
        raise ValueError(f"Could not find coordinates for '{query}'")
    
    print(f"✓ Found: {location.address}")
    print(f"✓ Coordinates: {location.latitude:.6f}, {location.longitude:.6f}")
    
    return (location.latitude, location.longitude)