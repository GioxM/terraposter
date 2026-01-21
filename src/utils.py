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

# src/utils.py
"""Shared utility functions used across the project (retries, helpers, etc.)."""

import time
from typing import Callable, Any


def retry_call(
    func: Callable[..., Any],
    max_retries: int = 3,
    base_sleep: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Execute a function with exponential backoff retries on specified exceptions.
    
    Args:
        func: The callable to retry
        max_retries: Maximum number of attempts (including the first)
        base_sleep: Initial sleep time in seconds
        backoff_factor: Multiplier for each subsequent wait (2.0 = 1s → 2s → 4s...)
        exceptions: Tuple of exception types to catch and retry on
    
    Returns:
        The result of func() on success
    
    Raises:
        Last caught exception after all retries are exhausted
    
    Why this design?
    - Reusable across any network call (Nominatim, OSMnx, future APIs)
    - Configurable backoff prevents hammering servers
    - Explicit exception tuple allows fine-grained control (e.g. only retry timeouts)
    """
    last_exc = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exc = e
            if attempt == max_retries:
                raise
            wait = base_sleep * (backoff_factor ** (attempt - 1))
            print(f"  ⚠ Retry {attempt}/{max_retries} after {wait:.1f}s: {type(e).__name__} - {str(e)}")
            time.sleep(wait)
    
    # Should never reach here if max_retries > 0
    raise last_exc