# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.1.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.0.0: First modular version – config, fonts, themes extracted
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message
# ===========================================

# src/output.py
"""Filename generation and poster saving logic."""

from datetime import datetime
from pathlib import Path
from .config import POSTERS_DIR


def generate_output_filename(city: str, theme_name: str, output_format: str) -> Path:
    """
    Generate timestamped, slug-safe filename inside posters/ directory.
    
    Why relative Path object? Makes printing and logging cleaner.
    """
    POSTERS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(" ", "_").replace(",", "").replace("'", "")
    filename = f"{city_slug}_{theme_name}_{timestamp}.{output_format.lower()}"
    return POSTERS_DIR / filename