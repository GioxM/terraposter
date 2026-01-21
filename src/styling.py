# ===========================================
# Project: City Map Poster Generator
# Description: Command-line tool that creates stylized city street network posters using OpenStreetMap data
# Author: Noxxvii
# Version: v2.1.0
# Date Created: 2026-01-20
# Last Modified: 2026-01-20
# Changelog:
# - 2026-01-20 v2.1.0: Added output.py + explicit theme passing + verbose timing + final success message + map_data.py & styling.py
# ===========================================

# src/styling.py
"""Road hierarchy coloring, widths, and gradient fade effects."""

import numpy as np
import matplotlib.colors as mcolors
from matplotlib.font_manager import FontProperties


def get_edge_colors(G, theme: dict) -> list:
    """Assign hex color to each edge based on OSM highway type."""
    colors = []
    for _, _, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            colors.append(theme['road_motorway'])
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            colors.append(theme['road_primary'])
        elif highway in ['secondary', 'secondary_link']:
            colors.append(theme['road_secondary'])
        elif highway in ['tertiary', 'tertiary_link']:
            colors.append(theme['road_tertiary'])
        elif highway in ['residential', 'living_street', 'unclassified']:
            colors.append(theme['road_residential'])
        else:
            colors.append(theme['road_default'])
    return colors


def get_edge_widths(G) -> list:
    """Assign line width based on road importance (thicker = more important)."""
    widths = []
    for _, _, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            widths.append(1.2)
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            widths.append(1.0)
        elif highway in ['secondary', 'secondary_link']:
            widths.append(0.8)
        elif highway in ['tertiary', 'tertiary_link']:
            widths.append(0.6)
        else:
            widths.append(0.4)
    return widths


def create_gradient_fade(ax, color: str, location: str = 'bottom', zorder: int = 10):
    """
    Add subtle fade vignette at top or bottom of the map.
    Uses numpy to create alpha gradient — very efficient.
    """
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))
    
    rgb = mcolors.to_rgb(color)
    rgba = np.zeros((256, 4))
    rgba[:, :3] = rgb
    
    if location == 'bottom':
        rgba[:, 3] = np.linspace(1, 0, 256)
        y_start, y_end = 0.0, 0.25
    else:  # top
        rgba[:, 3] = np.linspace(0, 1, 256)
        y_start, y_end = 0.75, 1.0
    
    cmap = mcolors.ListedColormap(rgba)
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    
    ax.imshow(
        gradient,
        extent=[xlim[0], xlim[1], ylim[0] + y_range * y_start, ylim[0] + y_range * y_end],
        aspect='auto',
        cmap=cmap,
        zorder=zorder,
        origin='lower'
    )