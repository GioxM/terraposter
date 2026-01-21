# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.3.0
# Date Created: 2026-01-21
# Last Modified: 2026-01-21
# Changelog:
# - 2026-01-20 v2.0.0: First modular version – config, fonts, themes extracted
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message + map_data.py & styling.py + poster.py rendering core
# - 2026-01-20 v2.1.1: Added distance clamping (min 1500m, max 60000m) with user feedback messages
# - 2026-01-20 v2.2.0: Added rate-limiting & retry logic for Nominatim and OSMnx calls to improve robustness
# - 2026-01-20 v2.2.1: Extracted retry logic into src/utils.py for reuse across network-heavy modules
# - 2026-01-21 v2.3.0: Added disk caching for map data (graph + features) to speed up repeated runs
# ===========================================

# src/cache.py
"""Simple disk-based caching for expensive OSMnx fetches."""

import hashlib
import pickle
from pathlib import Path
from typing import Tuple, Any

from .config import ROOT_DIR


CACHE_DIR = ROOT_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


# def _make_cache_key(city: str, country: str, distance: int) -> str:
def _make_cache_key(lat: float, lon: float, distance: int) -> str:
    """
    Create a deterministic, short cache key from inputs.
    Why hash? Prevents filename collisions and keeps keys clean.
    """
    input_str = f"{lat:.6f}|{lon:.6f}|{distance}"
    return hashlib.sha256(input_str.encode()).hexdigest()[:16]


# def get_cached_data(city: str, country: str, distance: int) -> Tuple[Any, Any, Any] | None:
def get_cached_data(lat: float, lon: float, distance: int) -> Tuple[Any, Any, Any] | None:
    """
    Try to load cached (G, water, parks) tuple.
    Returns None if cache miss or corrupted.
    """
    # key = _make_cache_key(city, country, distance)
    key = _make_cache_key(lat, lon, distance)
    cache_path = CACHE_DIR / f"{key}.pkl"

    if not cache_path.exists():
        return None

    try:
        with cache_path.open("rb") as f:
            data = pickle.load(f)
        print(f"✓ Using cached map data (key: {key[:8]}...)")
        return data
    except Exception as e:
        print(f"⚠ Cache load failed: {e} — fetching fresh data")
        return None


# def save_to_cache(city: str, country: str, distance: int, data: Tuple[Any, Any, Any]) -> None:
def save_to_cache(lat: float, lon: float, distance: int, data: Tuple[Any, Any, Any]) -> None:
    """
    Save (G, water, parks) to disk after successful fetch.
    Overwrites old cache silently.
    """
    # key = _make_cache_key(city, country, distance)
    key = _make_cache_key(lat, lon, distance)
    cache_path = CACHE_DIR / f"{key}.pkl"

    try:
        with cache_path.open("wb") as f:
            pickle.dump(data, f)
        print(f"✓ Cached map data for future runs (key: {key[:8]}...)")
    except Exception as e:
        print(f"⚠ Failed to save cache: {e} — continuing anyway")