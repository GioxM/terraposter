# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.0.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.0.0: Initial modular structure – extracted config, fonts, themes
# ===========================================

# src/config.py
"""Central place for project-wide constants and paths."""

import os
from pathlib import Path

# Directories (relative to project root)
ROOT_DIR = Path(__file__).parent.parent
THEMES_DIR = ROOT_DIR / "themes"
FONTS_DIR = ROOT_DIR / "fonts"
POSTERS_DIR = ROOT_DIR / "posters"

# Ensure output directory exists when needed (done in output.py)