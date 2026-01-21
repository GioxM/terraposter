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

# src/fonts.py
"""Font loading and management for consistent typography."""

import os
from matplotlib.font_manager import FontProperties

def load_fonts():
    """
    Load Roboto font family from the fonts/ directory.
    
    Returns:
        dict: font paths for different weights, or None if any is missing
    """
    fonts = {
        'bold':    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Roboto-Bold.ttf'),
        'regular': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Roboto-Regular.ttf'),
        'light':   os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Roboto-Light.ttf'),
    }
    
    # Defensive check – better to fail early with clear message
    missing = [path for weight, path in fonts.items() if not os.path.exists(path)]
    if missing:
        print("⚠️ Missing font files:")
        for p in missing:
            print(f"   {p}")
        print("Falling back to system monospace fonts.")
        return None
    
    return fonts


FONTS = load_fonts()  # module-level cache (loaded once)