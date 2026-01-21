# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.4.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-22
# Changelog:
# - v2.4.0: Added output size presets, mobile portrait support, custom size handling,
#           and automatic distance scaling based on output size
# ===========================================

# main.py (root level)

import argparse
import sys
import time
import traceback
import json
from pathlib import Path

from src.config import THEMES_DIR, POSTERS_DIR, ROOT_DIR
from src.themes import load_theme, get_available_themes
from src.geocoding import get_coordinates
from src.map_data import fetch_map_data
from src.output import generate_output_filename
from src.poster import render_poster
from src.cache import get_cached_data, save_to_cache, _make_cache_key, CACHE_DIR
from src.logging import setup_logger                     
from src.output_cache import check_previous_output, record_new_output


# ── Size presets ────────────────────────────────────────────────────────────
# Pixel-based presets → converted to inches via DPI at runtime
SIZE_PRESETS = {
    "default": {
        "figsize": (12, 16),
        "distance_mult": 1.0,
    },
    "desktop-fhd": {
        "pixels": (1920, 1080),
        "distance_mult": 1.2,
    },
    "desktop-qhd": {
        "pixels": (2560, 1440),
        "distance_mult": 1.5,
    },
    "desktop-4k": {
        "pixels": (3840, 2160),
        "distance_mult": 1.8,
    },
    "mobile-portrait": {
        "pixels": (1080, 1920),
        "distance_mult": 0.6,
    },
}


def print_examples():
    """Print helpful usage examples when no args or invalid input."""
    print("""
City Map Poster Generator
=========================

Usage:
  python main.py --city <city> --country <country> [options]

Examples:
  python main.py -c "Amsterdam" -C "Netherlands" -t blueprint -d 6000
  python main.py -c Paris -C France -t noir -s desktop-4k
  python main.py -c Tokyo -C Japan -s mobile-portrait
  python main.py -c Rome -C Italy -s custom:3000x5000
    """.strip())


def list_themes():
    """Display available themes with name and description."""
    themes = get_available_themes()
    if not themes:
        print("No themes found in 'themes/' directory.")
        return

    print("\nAvailable Themes:")
    print("-" * 60)
    for name in themes:
        path = THEMES_DIR / f"{name}.json"
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            display = data.get("name", name)
            desc = data.get("description", "")
        except Exception:
            display = name
            desc = ""

        print(f"  {name}")
        print(f"    {display}")
        if desc:
            print(f"    {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate beautiful stylized city map posters from OpenStreetMap data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples above — use --list-themes to see all styles."
    )

    parser.add_argument("--city", "-c", type=str, help="City name")
    parser.add_argument("--country", "-C", type=str, help="Country name")
    parser.add_argument("--theme", "-t", default="feature_based", help="Theme name")
    parser.add_argument("--distance", "-d", type=int, default=29000, help="Radius in meters")
    parser.add_argument("--format", "-f", default="png", choices=["png", "svg", "pdf"],
                        help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show timing and debug information")
    parser.add_argument("--list-themes", action="store_true",
                        help="List all available themes")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force fresh download — ignore and overwrite cache")
    parser.add_argument("--dpi", type=int, default=None,
                        help="Output DPI for raster formats (PNG). Default: 300. Ignored for SVG/PDF.")
    parser.add_argument("--quality", choices=["screen", "print", "high"], default="print",
                        help="Quality preset: screen (150 dpi), print (300 dpi), high (600 dpi)")
    parser.add_argument("--size","-s", type=str, default="default",
                        help="Output size preset or custom. Examples: desktop-fhd, desktop-4k, mobile-portrait, custom:1920x1080")

    args = parser.parse_args()

    # ── Distance validation & clamping ───────────────────────────────────────
    MIN_DISTANCE_METERS = 1500
    MAX_DISTANCE_METERS = 60000

    # Track whether distance was explicitly set by user
    distance_user_set = "--distance" in sys.argv or "-d" in sys.argv

    # ── Early exits ──────────────────────────────────────────────────────────
    if args.list_themes:
        list_themes()
        sys.exit(0)

    if len(sys.argv) == 1 or not (args.city and args.country):
        print("Error: --city and --country are required.\n")
        print_examples()
        sys.exit(1)

    # ── Main flow ────────────────────────────────────────────────────────────
    print("=" * 50)
    print("City Map Poster Generator — v2.4.0")
    print("=" * 50)

    start_time = time.perf_counter()

    try:
        # ── Setup logger ─────────────────────────────────────────────────────
        logger = setup_logger(args.city, verbose=args.verbose)
        logger.info({"event": "start", "args": vars(args)})

        # ── Resolve DPI ──────────────────────────────────────────────────────
        if args.dpi is not None:
            effective_dpi = args.dpi
        elif args.quality == "screen":
            effective_dpi = 150
        elif args.quality == "high":
            effective_dpi = 600
        else:
            effective_dpi = 300

        # ── Resolve size preset ──────────────────────────────────────────────
        if args.size.startswith("custom:"):
            try:
                w, h = map(int, args.size.split(":", 1)[1].split("x"))
                figsize_inches = (w / effective_dpi, h / effective_dpi)
                distance_mult = 1.0
            except Exception:
                print("Invalid custom size format — use custom:WIDTHxHEIGHT")
                sys.exit(1)
        else:
            preset = SIZE_PRESETS.get(args.size, SIZE_PRESETS["default"])  # ← added fallback to default
            if "pixels" in preset:
                w, h = preset["pixels"]
                figsize_inches = (w / effective_dpi, h / effective_dpi)
            else:
                figsize_inches = preset["figsize"]
            distance_mult = preset["distance_mult"]

        # ── Auto distance scaling ────────────────────────────────────────────
        if not distance_user_set:
            args.distance = int(args.distance * distance_mult)

        # Clamp distance (already present — kept unchanged)
        if args.distance < MIN_DISTANCE_METERS:
            args.distance = MIN_DISTANCE_METERS
        if args.distance > MAX_DISTANCE_METERS:
            args.distance = MAX_DISTANCE_METERS

        # ── Load theme ───────────────────────────────────────────────────────
        theme = load_theme(args.theme)
        logger.info({"event": "theme_loaded", "theme": args.theme})

        # ── Geocode ──────────────────────────────────────────────────────────
        point = get_coordinates(args.city, args.country)
        logger.info({"event": "geocode", "point": point})

        # ── Output path ──────────────────────────────────────────────────────
        output_path = generate_output_filename(args.city, args.theme, args.format)

        # ── Check if already generated ──────────────────────────────────────
        previous = check_previous_output(
            city=args.city,
            country=args.country,
            theme=args.theme,
            distance=args.distance,
            size=args.size,
            dpi=effective_dpi,
            format=args.format,
        )

        if previous is not None:
            existing_path = ROOT_DIR / previous["path"]
            if existing_path.exists():
                print("\n" + "═" * 50)
                print("Poster already generated — skipping render!")
                print(f"  City:      {args.city}, {args.country}")
                print(f"  Theme:     {theme.get('name', args.theme)}")
                print(f"  Size:      {args.size}")
                print(f"  DPI:       {effective_dpi}")
                print(f"  Distance:  {args.distance} m")
                print(f"  File:      {existing_path.relative_to(Path.cwd())}")
                print(f"  Generated: {previous['generated_at']}")
                print("═" * 50)
                if args.verbose:
                    print(f"  Duration:  {time.perf_counter() - start_time:.2f} seconds (cached)")
                sys.exit(0)
        
        # ── Cache handling ───────────────────────────────────────────────────
        
        if args.no_cache:
            key = _make_cache_key(point[0], point[1], args.distance)
            cache_path = CACHE_DIR / f"{key}.pkl"
            if cache_path.exists():
                cache_path.unlink()
                print("  ✓ Cache cleared due to --no-cache flag") 

        cached_data = get_cached_data(point[0], point[1], args.distance)       

        # ── Decide source once ───────────────────────────────────────────────
        if cached_data is not None:
            print("  ✓ Loaded from cache — skipping network fetch")
            logger.info({"event": "cache_hit"})
            G, water, parks = cached_data
        else:
            G, water, parks = fetch_map_data(point, args.distance)
            save_to_cache(point[0], point[1], args.distance, (G, water, parks))
            logger.info({"event": "cache_miss"})

        # ── Render ───────────────────────────────────────────────────────────
        render_poster(
            city=args.city,
            country=args.country,
            point=point,
            G=G,
            water=water,
            parks=parks,
            theme=theme,
            output_path=output_path,
            output_format=args.format,
            dpi=effective_dpi,
            figsize=figsize_inches,
        )
        # ── Record successful generation ────────────────────────────────────
        record_new_output(
            city=args.city,
            country=args.country,
            theme=args.theme,
            distance=args.distance,
            size=args.size,
            dpi=effective_dpi,
            format=args.format,
            output_path=output_path,
        )

        # ── Final output ─────────────────────────────────────────────────────
        duration = time.perf_counter() - start_time
        logger.info({"event": "end", "duration": duration})

        print("\n" + "═" * 50)
        print("Poster successfully created!")
        print(f"  City:      {args.city}, {args.country}")           # ← fixed alignment
        print(f"  Theme:     {theme.get('name', args.theme)}")
        print(f"  File:      {output_path.relative_to(Path.cwd())}")
        if args.verbose:
            print(f"  Distance:  {args.distance} m")
            print(f"  Size:      {figsize_inches[0]:.2f} × {figsize_inches[1]:.2f} inches")
            print(f"  DPI:       {effective_dpi}")
            print(f"  Duration:  {duration:.2f} seconds")
        print("═" * 50)

    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()