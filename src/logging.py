# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.3.1
# Date Created: 2026-01-20
# Last Modified: 2026-01-21
# Changelog:
# - 2026-01-20 v2.0.0: First modular version – config, fonts, themes extracted
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message + map_data.py & styling.py + poster.py rendering core
# - 2026-01-20 v2.1.1: Added distance clamping (min 1500m, max 60000m) with user feedback messages
# - 2026-01-20 v2.2.0: Added rate-limiting & retry logic for Nominatim and OSMnx calls to improve robustness
# - 2026-01-20 v2.2.1: Extracted retry logic into src/utils.py for reuse across network-heavy modules
# - 2026-01-21 v2.3.0: Added disk caching for map data (graph + features) – fast re-runs + --no-cache flag
# - 2026-01-21 v2.3.1: Added structured logging to file (JSONL format) for run history and debugging
# ===========================================

# src/logging.py
"""Structured logging setup using built-in logging module."""

import logging
from datetime import datetime
from pathlib import Path
from .config import ROOT_DIR

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(city: str, verbose: bool = False) -> logging.Logger:
    """
    Set up a logger that writes structured JSON lines to file.
    
    Args:
        city: Used in filename for easy identification
        verbose: If True, also log to console
    
    Returns:
        Configured logger — use logger.info(dict(...)) for structured messages
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    city_slug = city.lower().replace(" ", "_")
    log_path = LOG_DIR / f"{timestamp}_{city_slug}.log.jsonl"

    logger = logging.getLogger("poster_generator")
    logger.setLevel(logging.INFO)

    # File handler for JSONL
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter('%(message)s'))  # plain – we format as JSON in log call
    logger.addHandler(file_handler)

    # Console handler if verbose
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    return logger