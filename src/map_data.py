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

# src/map_data.py
"""Fetching street network, water and parks from OpenStreetMap via OSMnx with retries."""

import time
from tqdm import tqdm
import osmnx as ox

from .utils import retry_call


# def fetch_map_data(point: tuple[float, float], distance: int, use_cache: bool = True) -> tuple:
#     """
#     Download street network graph + water features + parks/green spaces with retries.
#     Uses tqdm for feedback and polite sleeps between requests.
#     """
#     print("\nFetching map data...")

#     with tqdm(total=3, desc="Fetching", unit="layer") as pbar:

#         # ── Street network ───────────────────────────────────────────────────
#         pbar.set_description("Street network")
#         def fetch_graph():
#             return ox.graph_from_point(
#                 point,
#                 dist=distance,
#                 dist_type='bbox',
#                 network_type='all',
#                 simplify=True,
#                 truncate_by_edge=True
#             )
#         G = retry_call(
#             fetch_graph,
#             max_retries=3,
#             base_sleep=1.5,
#             exceptions=(Exception,)  # OSMnx raises various errors → catch broadly
#         )
#         pbar.update(1)
#         time.sleep(1.5)  # polite pause between major calls

#         # ── Water features ───────────────────────────────────────────────────
#         pbar.set_description("Water features")
#         def fetch_water():
#             water = ox.features_from_point(
#                 point,
#                 tags={'natural': 'water', 'waterway': ['river', 'riverbank', 'canal']},
#                 dist=distance
#             )
#             if not water.empty:
#                 return water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
#             return None
#         water = retry_call(
#             fetch_water,
#             max_retries=3,
#             base_sleep=1.0,
#             exceptions=(Exception,)
#         )
#         pbar.update(1)
#         time.sleep(0.8)

#         # ── Parks / green spaces ─────────────────────────────────────────────
#         pbar.set_description("Parks & green spaces")
#         def fetch_parks():
#             parks = ox.features_from_point(
#                 point,
#                 tags={'leisure': 'park', 'landuse': ['grass', 'forest', 'recreation_ground']},
#                 dist=distance
#             )
#             if not parks.empty:
#                 return parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
#             return None
#         parks = retry_call(
#             fetch_parks,
#             max_retries=3,
#             base_sleep=1.0,
#             exceptions=(Exception,)
#         )
#         pbar.update(1)

#     print("✓ All map layers fetched successfully!")
#     return G, water, parks

def fetch_map_data(point: tuple[float, float], distance: int, use_cache: bool = True) -> tuple:
    """
    Download street network graph + water features + parks/green spaces with retries.
    Uses tqdm for feedback and polite sleeps between requests.
    """

    if use_cache:
        from .cache import get_cached_data, save_to_cache
        lat, lon = point
        cached = get_cached_data(lat=lat, lon=lon, distance=distance)
        if cached is not None:
            print("✓ Loaded map data from cache")
            return cached

    # ───────────────────────────────────────────────────────────────────────
    # EVERYTHING BELOW THIS LINE IS THE "FETCHING BLOCK"
    # ───────────────────────────────────────────────────────────────────────

    print("\nFetching map data...")

    with tqdm(total=3, desc="Fetching", unit="layer") as pbar:

        # ── Street network ───────────────────────────────────────────────────
        pbar.set_description("Street network")
        def fetch_graph():
            return ox.graph_from_point(
                point,
                dist=distance,
                dist_type='bbox',
                network_type='all',
                simplify=True,
                truncate_by_edge=True
            )
        G = retry_call(
            fetch_graph,
            max_retries=3,
            base_sleep=1.5,
            exceptions=(Exception,)
        )
        pbar.update(1)
        time.sleep(1.5)

        # ── Water features ───────────────────────────────────────────────────
        pbar.set_description("Water features")
        def fetch_water():
            water = ox.features_from_point(
                point,
                tags={'natural': 'water', 'waterway': ['river', 'riverbank', 'canal']},
                dist=distance
            )
            if not water.empty:
                return water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            return None
        water = retry_call(
            fetch_water,
            max_retries=3,
            base_sleep=1.0,
            exceptions=(Exception,)
        )
        pbar.update(1)
        time.sleep(0.8)

        # ── Parks / green spaces ─────────────────────────────────────────────
        pbar.set_description("Parks & green spaces")
        def fetch_parks():
            parks = ox.features_from_point(
                point,
                tags={'leisure': 'park', 'landuse': ['grass', 'forest', 'recreation_ground']},
                dist=distance
            )
            if not parks.empty:
                return parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            return None
        parks = retry_call(
            fetch_parks,
            max_retries=3,
            base_sleep=1.0,
            exceptions=(Exception,)
        )
        pbar.update(1)

    print("✓ All map layers fetched successfully!")
    result = (G, water, parks)

    if use_cache:
        save_to_cache(lat=lat, lon=lon, distance=distance, data=result)

    return result
