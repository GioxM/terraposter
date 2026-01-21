# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.0.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.0.0: Initial modular structure
# ===========================================

# src/themes.py
"""Theme loading, validation and listing logic."""

import json
import os
from pathlib import Path
from .config import THEMES_DIR

DEFAULT_THEME = {
    "name": "Feature-Based Shading (fallback)",
    "bg": "#FFFFFF",
    "text": "#000000",
    "gradient_color": "#FFFFFF",
    "water": "#C0C0C0",
    "parks": "#F0F0F0",
    "road_motorway": "#0A0A0A",
    "road_primary": "#1A1A1A",
    "road_secondary": "#2A2A2A",
    "road_tertiary": "#3A3A3A",
    "road_residential": "#4A4A4A",
    "road_default": "#3A3A3A"
}


def get_available_themes():
    """Return sorted list of theme names (without .json)."""
    if not THEMES_DIR.exists():
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        return []
    
    return sorted(
        p.stem for p in THEMES_DIR.glob("*.json")
    )


def load_theme(theme_name: str = "feature_based"):
    """
    Load theme configuration from JSON or return fallback.
    
    Args:
        theme_name: Name of the theme (filename without .json)
    
    Returns:
        dict: Theme configuration
    """
    theme_path = THEMES_DIR / f"{theme_name}.json"
    
    if not theme_path.exists():
        print(f"⚠ Theme '{theme_name}' not found → using fallback.")
        return DEFAULT_THEME.copy()
    
    try:
        with theme_path.open('r', encoding='utf-8') as f:
            theme = json.load(f)
        print(f"✓ Loaded theme: {theme.get('name', theme_name)}")
        if desc := theme.get('description'):
            print(f"  {desc}")
        return theme
    except Exception as e:
        print(f"✗ Failed to load theme '{theme_name}': {e}")
        return DEFAULT_THEME.copy()