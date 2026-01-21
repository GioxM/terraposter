# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.1.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.0.0: First modular version – config, fonts, themes extracted
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message + map_data.py & styling.py + poster.py rendering core
# ===========================================

# src/poster.py

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors

from .fonts import FONTS
from .styling import get_edge_colors, get_edge_widths, create_gradient_fade
import osmnx as ox


def render_poster(
    city: str,
    country: str,
    point: tuple[float, float],
    G,
    water,
    parks,
    theme: dict,
    output_path: str | Path,
    output_format: str = "png",
    figsize: tuple[float, float] = (12, 16),
    add_text: bool = True,
    dpi: int | None = None,
) -> None:
    """
    Core rendering function: creates and saves the stylized city map poster.

    Args:
        city: City name for text overlay
        country: Country name for text overlay
        point: (lat, lon) center point (used only for coordinate text)
        G: OSMnx graph (street network)
        water: GeoDataFrame of water features (or None)
        parks: GeoDataFrame of parks/green spaces (or None)
        theme: Loaded theme dictionary with all color keys
        output_path: Where to save the file (Path or str)
        output_format: 'png', 'svg', or 'pdf'
        figsize: Matplotlib figure size in inches (width, height)
        add_text: Whether to render city name, country, coordinates, attribution

    Why explicit parameters?
    - Makes the function testable & reusable (no globals)
    - Easy to add preview mode, different sizes, text-less versions later
    """
    print("Rendering map...")

    # ── 1. Figure setup ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=figsize, facecolor=theme["bg"])
    ax.set_facecolor(theme["bg"])
    ax.set_position([0, 0, 1, 1])           # full-bleed – no margins
    ax.axis("off")                          # hide axes for clean poster look

    # ── 2. Plot background layers ────────────────────────────────────────────
    # Water first (lowest z-order)
    if water is not None and not water.empty:
        water_polys = water[water.geometry.type.isin(["Polygon", "MultiPolygon"])]
        if not water_polys.empty:
            water_polys.plot(
                ax=ax,
                facecolor=theme["water"],
                edgecolor="none",
                zorder=1
            )

    # Parks on top of water
    if parks is not None and not parks.empty:
        parks_polys = parks[parks.geometry.type.isin(["Polygon", "MultiPolygon"])]
        if not parks_polys.empty:
            parks_polys.plot(
                ax=ax,
                facecolor=theme["parks"],
                edgecolor="none",
                zorder=2
            )

    # ── 3. Plot road network with hierarchy styling ──────────────────────────
    print("Applying road hierarchy colors & widths...")
    edge_colors = get_edge_colors(G, theme)
    edge_widths = get_edge_widths(G)

    ox.plot_graph(
        G,
        ax=ax,
        bgcolor=theme["bg"],
        node_size=0,                    # no nodes – cleaner look
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        edge_alpha=1.0,
        show=False,
        close=False
    )

    # ── 4. Add subtle gradient fades (vignette effect) ───────────────────────
    create_gradient_fade(ax, theme["gradient_color"], location="bottom", zorder=10)
    create_gradient_fade(ax, theme["gradient_color"], location="top", zorder=10)

    # ── 5. Typography & attribution ──────────────────────────────────────────
    if add_text and FONTS:
        font_main   = FontProperties(fname=FONTS["bold"],    size=60)
        font_top    = FontProperties(fname=FONTS["bold"],    size=40)
        font_sub    = FontProperties(fname=FONTS["light"],   size=22)
        font_coords = FontProperties(fname=FONTS["regular"], size=14)
        font_attr   = FontProperties(fname=FONTS["light"],   size=8)
    else:
        # Fallback to system monospace if fonts missing
        font_main   = FontProperties(family="monospace", weight="bold", size=60)
        font_top    = FontProperties(family="monospace", weight="bold", size=40)
        font_sub    = FontProperties(family="monospace", size=22)
        font_coords = FontProperties(family="monospace", size=14)
        font_attr   = FontProperties(family="monospace", size=8)

    if add_text:
        # Dynamic font size for long city names
        base_size = 60
        char_count = len(city)
        if char_count > 10:
            scale = min(1.0, 10 / char_count)
            adjusted_size = max(base_size * scale, 24)  # min 24pt
        else:
            adjusted_size = base_size

        font_main_adjusted = FontProperties(
            fname=FONTS["bold"] if FONTS else None,
            family="monospace" if not FONTS else None,
            weight="bold",
            size=adjusted_size
        )

        spaced_city = "  ".join(city.upper())

        # Bottom text block
        ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
                color=theme["text"], ha="center", fontproperties=font_main_adjusted, zorder=11)

        ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
                color=theme["text"], ha="center", fontproperties=font_sub, zorder=11)

        lat, lon = point
        hem_ns = "N" if lat >= 0 else "S"
        hem_ew = "E" if lon >= 0 else "W"
        coords_str = f"{abs(lat):.4f}° {hem_ns} / {abs(lon):.4f}° {hem_ew}"
        ax.text(0.5, 0.07, coords_str, transform=ax.transAxes,
                color=theme["text"], alpha=0.7, ha="center", fontproperties=font_coords, zorder=11)

        # Decorative line
        ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes,
                color=theme["text"], linewidth=1, zorder=11)

        # Attribution (bottom right, small & subtle)
        ax.text(0.98, 0.02, "© OpenStreetMap contributors",
                transform=ax.transAxes, color=theme["text"], alpha=0.5,
                ha="right", va="bottom", fontproperties=font_attr, zorder=11)

    # ── 6. Save with format-aware settings ───────────────────────────────────
        # ── 6. Save with format-aware settings ───────────────────────────────────
    print(f"Saving to {output_path}...")

    save_kwargs = {
        "facecolor": theme["bg"],
        "bbox_inches": "tight",
        "pad_inches": 0.05,
    }

    fmt = output_format.lower()
    if fmt == "png":
        effective_dpi = dpi if dpi is not None else 300
        save_kwargs["dpi"] = effective_dpi
        print(f"  Using DPI: {effective_dpi} for PNG")
    elif fmt in ["svg", "pdf"]:
        if dpi is not None:
            print("  Note: DPI setting ignored for vector format (SVG/PDF)")
        save_kwargs["format"] = fmt

    plt.savefig(output_path, **save_kwargs)
    plt.close(fig)

    print(f"✓ Done! Poster saved as {output_path}")