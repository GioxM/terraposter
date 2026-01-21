# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.4.1
# Date Created: 2026-01-20
# Last Modified: 2026-01-22
# Changelog:
# - v2.4.0: Added output size presets, mobile portrait support, custom size handling, and automatic distance scaling based on output size
# - v2.4.1: Added output caching (remember already-generated posters) to skip redundant rendering
# ===========================================

# src/output_cache.py

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .config import ROOT_DIR

INDEX_FILE = ROOT_DIR / "generated_posters.json"


def _make_output_key(
    city: str,
    country: str,
    theme: str,
    distance: int,
    size: str,
    dpi: int,
    format: str,
) -> str:
    """Deterministic hash of all params that affect the visual output."""
    key_str = f"{city.lower()}|{country.lower()}|{theme.lower()}|{distance}|{size.lower()}|{dpi}|{format.lower()}"
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]


def load_output_index() -> Dict[str, Dict]:
    """Load or initialize the JSON index of previously generated posters."""
    if INDEX_FILE.exists():
        try:
            with INDEX_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print("⚠ Warning: generated_posters.json corrupted — starting fresh")
    return {}


def save_output_index(index: Dict[str, Dict]) -> None:
    """Save updated index back to file."""
    try:
        with INDEX_FILE.open("w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
    except Exception as e:
        print(f"⚠ Failed to save output index: {e}")


def check_previous_output(
    city: str, country: str, theme: str, distance: int, size: str, dpi: int, format: str
) -> Optional[Dict]:
    """Check if this exact combination was already rendered."""
    index = load_output_index()
    key = _make_output_key(city, country, theme, distance, size, dpi, format)

    if key in index:
        return index[key]
    return None


def record_new_output(
    city: str,
    country: str,
    theme: str,
    distance: int,
    size: str,
    dpi: int,
    format: str,
    output_path: Path,
) -> None:
    """Record a newly generated poster in the index."""
    index = load_output_index()
    key = _make_output_key(city, country, theme, distance, size, dpi, format)

    index[key] = {
        "path": str(output_path.relative_to(ROOT_DIR)),
        "generated_at": datetime.now().isoformat(),
        "city": city,
        "country": country,
        "theme": theme,
        "distance_m": distance,
        "size": size,
        "dpi": dpi,
        "format": format,
    }

    save_output_index(index)