"""West York / Northern Architecture Modular Sets (4 Distinct Themes, 3 Buildings Each = 12 Models).

1500 Triangle Budget per asset.
Executes inside Blender via bpy_runner.py.
"""

import sys
from pathlib import Path
import bmesh
from mathutils import Vector

# Add parent path for mass_kit
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent.parent / "lib"))

import mass_kit as mkit

# ==============================================================================
# PALETTES
# ==============================================================================
# S1: Yorkshire Gritstone / Mill Town
PAL_WESTYORK_S1 = [
    (0.46, 0.44, 0.40),  # 0: Weathered Yorkshire Gritstone (Dark Buff Sandstone)
    (0.32, 0.30, 0.28),  # 1: Sooty Dark Stone
    (0.20, 0.22, 0.25),  # 2: Northern Slate
    (0.68, 0.65, 0.58),  # 3: Dressed Stone Lintels & Mullions
    (0.18, 0.25, 0.22),  # 4: Deep Hunter Green Door
    (0.85, 0.84, 0.80),  # 5: Mullioned Window Frame
    (0.10, 0.14, 0.18),  # 6: Dark Glass
    (0.55, 0.30, 0.18),  # 7: Terracotta Chimney Pot
]

# S2: Anglo-Asian Fusion / East York Hybrid
PAL_WESTYORK_S2 = [
    (0.50, 0.48, 0.44),  # 0: Gritstone Foundation / Base
    (0.72, 0.15, 0.12),  # 1: Imperial Red Lacquer Timber / Pillars
    (0.22, 0.35, 0.30),  # 2: Jade Glazed Roof Tiles
    (0.82, 0.70, 0.25),  # 3: Gilded Gold Accents & Cornice
    (0.15, 0.15, 0.15),  # 4: Charcoal Grey Timber / Door
    (0.88, 0.85, 0.78),  # 5: Rice Paper / Lattice Window Frame
    (0.14, 0.18, 0.22),  # 6: Window Glass
    (0.85, 0.40, 0.15),  # 7: Lantern Orange
]

# S3: Northern Industrial Redbrick & Slate
PAL_WESTYORK_S3 = [
    (0.52, 0.20, 0.16),  # 0: Dark Northern Redbrick
    (0.35, 0.15, 0.12),  # 1: Sooty Engineering Brick
    (0.18, 0.20, 0.24),  # 2: Welsh Blue Slate
    (0.75, 0.72, 0.66),  # 3: Sandstone Cills
    (0.12, 0.15, 0.28),  # 4: Navy Blue Door
    (0.90, 0.90, 0.88),  # 5: White Timber Sash
    (0.12, 0.16, 0.22),  # 6: Dark Glass
    (0.25, 0.25, 0.28),  # 7: Wrought Iron / Steel
]

# S4: Semi-Rural Tudor Revival & Render
PAL_WESTYORK_S4 = [
    (0.86, 0.84, 0.78),  # 0: Cream Stucco / Roughcast Render
    (0.15, 0.13, 0.12),  # 1: Dark Oak Half-Timber Beams
    (0.48, 0.45, 0.40),  # 2: Gritstone Plinth / Ground Floor
    (0.35, 0.24, 0.18),  # 3: Rosemary Clay Roof Tiles
    (0.20, 0.16, 0.14),  # 4: Studded Heavy Oak Door
    (0.80, 0.78, 0.72),  # 5: Leaded Diamond Window Frames
    (0.12, 0.15, 0.20),  # 6: Glass
    (0.60, 0.32, 0.18),  # 7: Twisted Chimney Terracotta
]


# ==============================================================================
# SET 1: YORKSHIRE GRITSTONE / MILL TOWN
# ==============================================================================

def build_westyork_s1_gritstone_terrace():
    """10m wide 2-unit tileable Yorkshire gritstone terraced row."""
    bm = bmesh.new()
    faces = []
    # 10m wide, 8m deep, 6.8m high (2 storeys)
    # Heavy gritstone masonry walls
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 6.8, center=(0, 0, 3.4), color_idx=0)
    
    # Continuous Northern Slate Roof
    faces += mkit.make_pitched_roof(bm, 10.0, 8.0, 2.6, overhang=0.0, center=(0, 0, 6.8), color_idx=2)
    
    # Heavy stone continuous lintel band
    faces += mkit.make_cuboid(bm, 10.0, 0.1, 0.25, center=(0, -4.05, 2.9), color_idx=3)
    faces += mkit.make_cuboid(bm, 10.0, 0.1, 0.25, center=(0, -4.05, 5.8), color_idx=3)
    
    # 2x Recessed Front Entrances with Stone Hoods
    for dx in (-3.5, 3.5):
        faces += mkit.make_cuboid(bm, 1.6, 0.8, 2.8, center=(dx, -4.1, 1.4), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -4.02, 1.1), color_idx=4)
        
    # Stone Mullioned Windows (Ground & 1st Floor)
    for wx in (-1.0, 1.0):
        # 3-light mullioned ground window
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(wx * 1.5, -4.02, 1.6), color_idx=6)
        faces += mkit.make_cuboid(bm, 0.15, 0.14, 1.8, center=(wx * 1.5 - 0.6, -4.03, 1.6), color_idx=3)
        faces += mkit.make_cuboid(bm, 0.15, 0.14, 1.8, center=(wx * 1.5 + 0.6, -4.03, 1.6), color_idx=3)
        
    for floor_z in (4.6,):
        for wx in (-3.5, -1.2, 1.2, 3.5):
            faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.6, center=(wx, -4.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 0.15, 0.14, 1.6, center=(wx, -4.03, floor_z), color_idx=3)
            
    # Substantial Stone Party Chimney
    faces += mkit.make_cuboid(bm, 1.4, 1.6, 2.2, center=(0, 0, 9.4), color_idx=0)
    faces += mkit.make_cuboid(bm, 1.6, 1.8, 0.3, center=(0, 0, 10.5), color_idx=3)
    for py in (-0.4, 0.4):
        faces += mkit.make_cylinder(bm, 0.14, 0.6, segs=6, center=(0, py, 10.9), color_idx=7)

    mkit.apply_bmesh_and_export("building_westyork_s1_gritstone_terrace", bm, faces, PAL_WESTYORK_S1, "West York/modular_sets")


def build_westyork_s1_millowner_manor():
    """Large Yorkshire Stone Mill-Owner Manor."""
    bm = bmesh.new()
    faces = []
    # 13m wide, 10m deep, 7.5m high
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 7.5, center=(0, 0, 3.75), color_idx=0)
    
    # Roof with cross gables
    faces += mkit.make_pitched_roof(bm, 13.0, 10.0, 3.2, overhang=0.3, center=(0, 0, 7.5), color_idx=2)
    
    # 2x Projecting Front Stone Gables (Left & Right)
    for gx in (-4.0, 4.0):
        faces += mkit.make_cuboid(bm, 4.0, 1.5, 7.5, center=(gx, -5.25, 3.75), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 1.5, 4.0, 2.2, overhang=0.2, center=(gx, -5.25, 7.5), color_idx=2)
        # Stone mullion 4-light windows
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 2.0, center=(gx, -6.02, 2.0), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(gx, -6.02, 5.2), color_idx=6)
        
    # Central Stone Porch & Heavy Door
    faces += mkit.make_cuboid(bm, 3.0, 1.5, 3.4, center=(0, -5.25, 1.7), color_idx=3)
    faces += mkit.make_pitched_roof(bm, 3.0, 1.5, 1.0, overhang=0.1, center=(0, -5.25, 3.4), color_idx=2)
    faces += mkit.make_cuboid(bm, 1.4, 0.1, 2.4, center=(0, -6.02, 1.2), color_idx=4)
    
    # Massive Ashlar Chimneys
    for cx in (-5.0, 5.0):
        faces += mkit.make_cuboid(bm, 1.5, 1.5, 3.2, center=(cx, 0, 9.2), color_idx=0)
        faces += mkit.make_cuboid(bm, 1.7, 1.7, 0.3, center=(cx, 0, 10.8), color_idx=3)

    mkit.apply_bmesh_and_export("building_westyork_s1_millowner_manor", bm, faces, PAL_WESTYORK_S1, "West York/modular_sets")


def build_westyork_s1_mill_flats():
    """Converted 3-Storey Yorkshire Stone Mill / Warehouse Flats."""
    bm = bmesh.new()
    faces = []
    # 17m wide, 11m deep, 11.5m high
    faces += mkit.make_cuboid(bm, 17.0, 11.0, 11.5, center=(0, 0, 5.75), color_idx=0)
    
    # Quoin stone corners
    faces += mkit.make_cuboid(bm, 17.2, 11.2, 0.6, center=(0, 0, 11.8), color_idx=3)
    faces += mkit.make_pitched_roof(bm, 17.0, 11.0, 3.5, overhang=0.2, center=(0, 0, 11.5), color_idx=2)
    
    # Central Loading Bay Column / Glass Stairwell with Crane Hood
    faces += mkit.make_cuboid(bm, 3.0, 0.8, 12.5, center=(0, -5.5, 6.25), color_idx=3)
    faces += mkit.make_pitched_roof(bm, 3.4, 1.2, 1.2, overhang=0.2, center=(0, -5.5, 12.5), color_idx=2)
    # Timber crane jib
    faces += mkit.make_cuboid(bm, 0.3, 1.8, 0.3, center=(0, -6.2, 12.0), color_idx=1)
    
    # Windows array (6 columns per floor, arched lintels)
    for floor_z in (2.2, 5.6, 9.0):
        for col_x in (-6.5, -4.2, -2.0, 2.0, 4.2, 6.5):
            faces += mkit.make_cuboid(bm, 1.3, 0.1, 1.8, center=(col_x, -5.52, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.5, 0.15, 0.25, center=(col_x, -5.54, floor_z + 1.0), color_idx=3)
            
    # Ground Entrance
    faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.6, center=(0, -5.92, 1.3), color_idx=4)

    mkit.apply_bmesh_and_export("building_westyork_s1_mill_flats", bm, faces, PAL_WESTYORK_S1, "West York/modular_sets")


# ==============================================================================
# SET 2: ANGLO-ASIAN FUSION / EAST YORK HYBRID
# ==============================================================================

def build_westyork_s2_fusion_terrace():
    """10m wide 2-unit tileable Anglo-Asian hybrid terrace with pagoda eaves."""
    bm = bmesh.new()
    faces = []
    # Stone plinth
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 1.0, center=(0, 0, 0.5), color_idx=0)
    # Red timber & masonry walls
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 5.8, center=(0, 0, 3.9), color_idx=0)
    
    # Red timber post frames
    for px in (-5.0, -2.5, 0.0, 2.5, 5.0):
        faces += mkit.make_cuboid(bm, 0.3, 0.3, 6.0, center=(px, -4.05, 3.5), color_idx=1)
        
    # Flared Pagoda Roof with Jade Tiles
    faces += mkit.make_pagoda_roof(bm, 10.0, 8.0, 2.4, overhang=0.6, flare=0.4, center=(0, 0, 6.8), color_idx=2)
    
    # Intermediate eave canopy between storeys
    faces += mkit.make_pagoda_roof(bm, 10.0, 1.2, 0.6, overhang=0.4, flare=0.2, center=(0, -4.4, 3.6), color_idx=2)
    
    # 2x Imperial Red Lacquer Doors
    for dx in (-3.5, 3.5):
        faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.2, center=(dx, -4.02, 1.1), color_idx=1)
        # Gold door trim / frame
        faces += mkit.make_cuboid(bm, 1.4, 0.12, 2.4, center=(dx, -4.01, 1.2), color_idx=3)
        # Hanging lantern
        faces += mkit.make_cylinder(bm, 0.15, 0.35, segs=6, center=(dx + 0.9, -4.4, 2.6), color_idx=7)
        
    # Lattice Windows (Ground & 1st Floor)
    for floor_z in (1.8, 5.2):
        for wx in (-1.2, 1.2):
            faces += mkit.make_cuboid(bm, 1.6, 0.1, 1.8, center=(wx, -4.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.7, 0.12, 0.1, center=(wx, -4.03, floor_z), color_idx=5)
            faces += mkit.make_cuboid(bm, 0.1, 0.12, 1.8, center=(wx, -4.03, floor_z), color_idx=5)

    mkit.apply_bmesh_and_export("building_westyork_s2_fusion_terrace", bm, faces, PAL_WESTYORK_S2, "West York/modular_sets")


def build_westyork_s2_fusion_manor():
    """Large Anglo-Asian Fusion Courtyard Manor."""
    bm = bmesh.new()
    faces = []
    # 14m wide, 11m deep, 7.5m high
    faces += mkit.make_cuboid(bm, 14.0, 11.0, 1.2, center=(0, 0, 0.6), color_idx=0)
    faces += mkit.make_cuboid(bm, 14.0, 11.0, 6.3, center=(0, 0, 4.35), color_idx=0)
    
    # Tiered Pagoda Roof (2 tiers)
    faces += mkit.make_pagoda_roof(bm, 14.0, 11.0, 2.2, overhang=0.8, flare=0.5, center=(0, 0, 7.5), color_idx=2)
    faces += mkit.make_pagoda_roof(bm, 9.0, 7.0, 1.8, overhang=0.6, flare=0.4, center=(0, 0, 9.5), color_idx=2)
    
    # Grand Imperial Red Portico with 4 Columns
    faces += mkit.make_cuboid(bm, 5.0, 2.0, 0.4, center=(0, -6.0, 0.2), color_idx=0)
    for col_x in (-2.0, -0.7, 0.7, 2.0):
        faces += mkit.make_cylinder(bm, 0.16, 3.4, segs=8, center=(col_x, -6.8, 1.7), color_idx=1)
    # Portico pagoda roof
    faces += mkit.make_pagoda_roof(bm, 5.4, 2.2, 1.2, overhang=0.5, flare=0.3, center=(0, -6.0, 3.4), color_idx=2)
    # Grand double red doors with gold studs
    faces += mkit.make_cuboid(bm, 2.0, 0.1, 2.8, center=(0, -5.52, 1.6), color_idx=1)
    
    # Array of Lattice Screen Windows
    for floor_z in (2.0, 5.4):
        for wx in (-4.8, 4.8):
            faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(wx, -5.52, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 2.5, 0.12, 2.0, center=(wx, -5.53, floor_z), color_idx=3)

    mkit.apply_bmesh_and_export("building_westyork_s2_fusion_manor", bm, faces, PAL_WESTYORK_S2, "West York/modular_sets")


def build_westyork_s2_fusion_flats():
    """3-Storey High-Density Anglo-Asian Residential Complex."""
    bm = bmesh.new()
    faces = []
    # 18m wide, 11m deep, 11.5m high
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 11.5, center=(0, 0, 5.75), color_idx=0)
    
    # Pagoda Eaves along roof
    faces += mkit.make_pagoda_roof(bm, 18.0, 11.0, 2.5, overhang=0.8, flare=0.5, center=(0, 0, 11.5), color_idx=2)
    
    # Multi-tier Pagoda Balconies across Floors 2 and 3
    for bz in (4.5, 8.0):
        # Continuous cantilevered red timber balcony
        faces += mkit.make_cuboid(bm, 16.0, 1.5, 0.3, center=(0, -6.2, bz), color_idx=1)
        # Red timber railing
        faces += mkit.make_cuboid(bm, 16.0, 0.08, 0.9, center=(0, -6.9, bz + 0.55), color_idx=1)
        # Pagoda awning over balcony
        faces += mkit.make_pagoda_roof(bm, 16.2, 1.6, 0.6, overhang=0.3, flare=0.2, center=(0, -6.2, bz + 2.8), color_idx=2)
        
        # Sliding doors along balcony
        for dx in (-5.5, -1.8, 1.8, 5.5):
            faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.2, center=(dx, -5.52, bz + 1.2), color_idx=6)
            
    # Ground Floor Red Pillars & Entrances
    for px in (-7.0, -3.5, 0.0, 3.5, 7.0):
        faces += mkit.make_cylinder(bm, 0.2, 3.4, segs=8, center=(px, -5.8, 1.7), color_idx=1)
    faces += mkit.make_cuboid(bm, 2.4, 0.1, 2.6, center=(0, -5.52, 1.3), color_idx=1)

    mkit.apply_bmesh_and_export("building_westyork_s2_fusion_flats", bm, faces, PAL_WESTYORK_S2, "West York/modular_sets")


# ==============================================================================
# SET 3: NORTHERN INDUSTRIAL REDBRICK & SLATE
# ==============================================================================

def build_westyork_s3_redbrick_terrace():
    """10m wide tight northern industrial redbrick terrace with steep roof."""
    bm = bmesh.new()
    faces = []
    # 10m wide, 7.5m deep, 6.5m high (2 storeys)
    faces += mkit.make_cuboid(bm, 10.0, 7.5, 6.5, center=(0, 0, 3.25), color_idx=0)
    
    # Steep Northern Slate Pitch
    faces += mkit.make_pitched_roof(bm, 10.0, 7.5, 3.2, overhang=0.0, center=(0, 0, 6.5), color_idx=2)
    
    # 2x Symmetrical Navy Front Doors
    for dx in (-3.8, 3.8):
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -3.77, 1.1), color_idx=4)
        faces += mkit.make_cuboid(bm, 1.2, 0.15, 0.2, center=(dx, -3.78, 2.3), color_idx=3)
        
    # Large Multi-pane Industrial Sash Windows
    for floor_z in (1.6, 4.8):
        for wx in (-1.4, 1.4):
            faces += mkit.make_cuboid(bm, 1.8, 0.1, 1.8, center=(wx, -3.77, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 2.0, 0.15, 0.2, center=(wx, -3.78, floor_z + 1.0), color_idx=3)
            faces += mkit.make_cuboid(bm, 2.0, 0.15, 0.15, center=(wx, -3.78, floor_z - 1.0), color_idx=3)
            
    # 2x Steep Attic Dormer Windows
    for dx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 1.4, 1.2, 1.4, center=(dx, -3.0, 7.8), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 1.4, 1.2, 0.8, overhang=0.1, center=(dx, -3.0, 8.5), color_idx=2)
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 1.0, center=(dx, -3.62, 7.8), color_idx=6)
        
    # Central Tall Factory-style Chimney Stack
    faces += mkit.make_cuboid(bm, 1.0, 1.2, 2.4, center=(0, 0, 9.8), color_idx=1)

    mkit.apply_bmesh_and_export("building_westyork_s3_redbrick_terrace", bm, faces, PAL_WESTYORK_S3, "West York/modular_sets")


def build_westyork_s3_redbrick_detached():
    """Northern Industrialist Detached Villa."""
    bm = bmesh.new()
    faces = []
    # 12m wide, 9m deep, 7.5m high
    faces += mkit.make_cuboid(bm, 12.0, 9.0, 7.5, center=(0, 0, 3.75), color_idx=0)
    faces += mkit.make_hipped_roof(bm, 12.0, 9.0, 3.0, overhang=0.3, center=(0, 0, 7.5), color_idx=2)
    
    # Ground Floor Square Bay Windows (Left & Right)
    for bx in (-3.5, 3.5):
        faces += mkit.make_cuboid(bm, 2.8, 1.0, 3.0, center=(bx, -5.0, 1.5), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 2.8, 1.0, 0.6, overhang=0.1, center=(bx, -5.0, 3.0), color_idx=2)
        faces += mkit.make_cuboid(bm, 2.2, 0.1, 1.8, center=(bx, -5.52, 1.5), color_idx=6)
        
    # Central Porch & Arched Doorway
    faces += mkit.make_cuboid(bm, 2.4, 1.2, 3.2, center=(0, -5.0, 1.6), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.4, center=(0, -5.62, 1.2), color_idx=4)
    
    # 1st Floor Windows
    for wx in (-3.5, 0.0, 3.5):
        faces += mkit.make_cuboid(bm, 1.6, 0.1, 1.8, center=(wx, -4.52, 5.2), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.8, 0.15, 0.2, center=(wx, -4.54, 6.2), color_idx=3)
        
    # Twin Chimneys
    for cx in (-4.0, 4.0):
        faces += mkit.make_cuboid(bm, 1.2, 1.2, 2.8, center=(cx, 0, 9.0), color_idx=1)

    mkit.apply_bmesh_and_export("building_westyork_s3_redbrick_detached", bm, faces, PAL_WESTYORK_S3, "West York/modular_sets")


def build_westyork_s3_industrial_flats():
    """3-Storey Redbrick Industrial Block Flats with Steel Gangways."""
    bm = bmesh.new()
    faces = []
    # 16m wide, 10m deep, 10.5m high
    faces += mkit.make_cuboid(bm, 16.0, 10.0, 10.5, center=(0, 0, 5.25), color_idx=0)
    
    # Low-pitch industrial roof with skylights
    faces += mkit.make_pitched_roof(bm, 16.0, 10.0, 2.2, overhang=0.1, center=(0, 0, 10.5), color_idx=2)
    
    # Black Steel External Balcony Gangways (Floors 2 & 3)
    for bz in (4.2, 7.6):
        faces += mkit.make_cuboid(bm, 14.0, 1.4, 0.15, center=(0, -5.7, bz), color_idx=7)
        faces += mkit.make_cuboid(bm, 14.0, 0.06, 0.9, center=(0, -6.35, bz + 0.5), color_idx=7)
        # Steel vertical support pillars
        for sx in (-6.5, -2.2, 2.2, 6.5):
            faces += mkit.make_cuboid(bm, 0.1, 0.1, 10.0, center=(sx, -6.35, 5.0), color_idx=7)
            
    # Doors & Windows array
    for floor_z in (1.6, 5.0, 8.4):
        for col_x in (-5.0, -1.8, 1.8, 5.0):
            faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.8, center=(col_x, -5.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.5, 0.12, 0.15, center=(col_x, -5.03, floor_z + 1.0), color_idx=3)

    mkit.apply_bmesh_and_export("building_westyork_s3_industrial_flats", bm, faces, PAL_WESTYORK_S3, "West York/modular_sets")


# ==============================================================================
# SET 4: SEMI-RURAL / TUDOR REVIVAL & RENDER
# ==============================================================================

def build_westyork_s4_tudor_terrace():
    """10m wide tileable Mock-Tudor terrace with stone base & timber upper."""
    bm = bmesh.new()
    faces = []
    # Ground floor stone base (3m high)
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 3.0, center=(0, 0, 1.5), color_idx=2)
    # 1st floor jettied cream stucco (slightly projecting front by 0.3m)
    faces += mkit.make_cuboid(bm, 10.0, 8.3, 3.8, center=(0, -0.15, 4.9), color_idx=0)
    
    # Dark Oak Half-Timber Beams across 1st floor front
    # Horizontal top/bottom/middle beams
    faces += mkit.make_cuboid(bm, 10.0, 0.08, 0.2, center=(0, -4.32, 3.1), color_idx=1)
    faces += mkit.make_cuboid(bm, 10.0, 0.08, 0.2, center=(0, -4.32, 4.9), color_idx=1)
    faces += mkit.make_cuboid(bm, 10.0, 0.08, 0.2, center=(0, -4.32, 6.7), color_idx=1)
    # Vertical posts
    for vx in (-5.0, -3.3, -1.6, 0.0, 1.6, 3.3, 5.0):
        faces += mkit.make_cuboid(bm, 0.18, 0.08, 3.8, center=(vx, -4.32, 4.9), color_idx=1)
        
    # Steep Rosemary Clay Tile Roof
    faces += mkit.make_pitched_roof(bm, 10.0, 8.3, 2.8, overhang=0.2, center=(0, -0.15, 6.8), color_idx=3)
    
    # 2x Studded Oak Doors with Stone Surrounds
    for dx in (-3.5, 3.5):
        faces += mkit.make_cuboid(bm, 1.6, 0.2, 2.8, center=(dx, -4.02, 1.4), color_idx=2)
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -4.04, 1.1), color_idx=4)
        
    # Leaded Windows
    for wx in (-1.2, 1.2):
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 1.6, center=(wx, -4.02, 1.6), color_idx=6)
    for ux in (-3.5, -1.2, 1.2, 3.5):
        faces += mkit.make_cuboid(bm, 1.2, 0.1, 1.4, center=(ux, -4.32, 5.0), color_idx=6)
        
    # Twisted Tudor Brick Chimney
    faces += mkit.make_cuboid(bm, 1.2, 1.4, 2.2, center=(0, 0, 9.6), color_idx=7)

    mkit.apply_bmesh_and_export("building_westyork_s4_tudor_terrace", bm, faces, PAL_WESTYORK_S4, "West York/modular_sets")


def build_westyork_s4_tudor_manor():
    """Large Mock-Tudor Country Manor with Multiple Gables."""
    bm = bmesh.new()
    faces = []
    # 13m wide, 10m deep, 7.2m high
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 3.2, center=(0, 0, 1.6), color_idx=2) # Stone ground
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 4.0, center=(0, 0, 5.2), color_idx=0) # Stucco upper
    
    # Roof
    faces += mkit.make_pitched_roof(bm, 13.0, 10.0, 3.2, overhang=0.3, center=(0, 0, 7.2), color_idx=3)
    
    # 2x Projecting Half-Timber Front Gables
    for gx in (-3.8, 3.8):
        faces += mkit.make_cuboid(bm, 4.2, 1.6, 7.2, center=(gx, -5.3, 3.6), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 1.6, 4.2, 2.4, overhang=0.2, center=(gx, -5.3, 7.2), color_idx=3)
        # Timber framing on gables
        for vy in (-5.0, -4.0, 4.0):
            faces += mkit.make_cuboid(bm, 0.15, 0.08, 3.6, center=(gx, -6.12, 5.4), color_idx=1)
        faces += mkit.make_cuboid(bm, 4.2, 0.08, 0.15, center=(gx, -6.12, 7.2), color_idx=1)
        # Leaded bay windows
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(gx, -6.12, 1.8), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(gx, -6.12, 5.2), color_idx=6)
        
    # Central Timbered Porch
    faces += mkit.make_cuboid(bm, 2.8, 1.4, 3.0, center=(0, -5.2, 1.5), color_idx=1)
    faces += mkit.make_pitched_roof(bm, 2.8, 1.4, 1.0, overhang=0.1, center=(0, -5.2, 3.0), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.2, center=(0, -5.92, 1.1), color_idx=4)
    
    # Ornate Clustered Tudor Chimneys
    for cx in (-4.0, 4.0):
        faces += mkit.make_cuboid(bm, 1.2, 1.2, 2.6, center=(cx, 0, 9.0), color_idx=7)

    mkit.apply_bmesh_and_export("building_westyork_s4_tudor_manor", bm, faces, PAL_WESTYORK_S4, "West York/modular_sets")


def build_westyork_s4_tudor_flats():
    """3-Storey Tudor-Accented Residential Flats."""
    bm = bmesh.new()
    faces = []
    # 17m wide, 11m deep, 11.0m high
    faces += mkit.make_cuboid(bm, 17.0, 11.0, 3.6, center=(0, 0, 1.8), color_idx=2) # Stone ground
    faces += mkit.make_cuboid(bm, 17.0, 11.0, 7.4, center=(0, 0, 7.3), color_idx=0) # Stucco upper
    
    # Half-timbered horizontal beams across 1st & 2nd floors
    for bz in (3.6, 7.2, 10.8):
        faces += mkit.make_cuboid(bm, 17.2, 0.08, 0.2, center=(0, -5.52, bz), color_idx=1)
    for vx in (-8.0, -5.0, -2.0, 2.0, 5.0, 8.0):
        faces += mkit.make_cuboid(bm, 0.2, 0.08, 7.4, center=(vx, -5.52, 7.3), color_idx=1)
        
    # High-pitch Clay Roof with 3 Gables
    faces += mkit.make_pitched_roof(bm, 17.0, 11.0, 3.4, overhang=0.2, center=(0, 0, 11.0), color_idx=3)
    for gx in (-5.0, 0.0, 5.0):
        faces += mkit.make_cuboid(bm, 3.6, 1.2, 2.4, center=(gx, -5.0, 11.5), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 1.2, 3.6, 1.2, overhang=0.1, center=(gx, -5.0, 12.7), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 1.2, center=(gx, -5.62, 11.6), color_idx=6)
        
    # Communal Arched Entrance
    faces += mkit.make_cuboid(bm, 2.8, 0.8, 3.2, center=(0, -5.8, 1.6), color_idx=2)
    faces += mkit.make_cuboid(bm, 1.6, 0.1, 2.4, center=(0, -6.12, 1.3), color_idx=4)
    
    # Regular Windows across floors
    for floor_z in (2.0, 5.4, 8.8):
        for col_x in (-6.0, -3.5, 3.5, 6.0):
            faces += mkit.make_cuboid(bm, 1.6, 0.1, 1.8, center=(col_x, -5.52, floor_z), color_idx=6)

    mkit.apply_bmesh_and_export("building_westyork_s4_tudor_flats", bm, faces, PAL_WESTYORK_S4, "West York/modular_sets")


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("--- BUILDING ALL 12 WEST YORK ARCHITECTURE MODELS (<1500 TRIS) ---")
    # S1
    build_westyork_s1_gritstone_terrace()
    build_westyork_s1_millowner_manor()
    build_westyork_s1_mill_flats()
    # S2
    build_westyork_s2_fusion_terrace()
    build_westyork_s2_fusion_manor()
    build_westyork_s2_fusion_flats()
    # S3
    build_westyork_s3_redbrick_terrace()
    build_westyork_s3_redbrick_detached()
    build_westyork_s3_industrial_flats()
    # S4
    build_westyork_s4_tudor_terrace()
    build_westyork_s4_tudor_manor()
    build_westyork_s4_tudor_flats()
    print("--- ALL 12 WEST YORK ASSETS COMPLETE ---")


if __name__ == "__main__":
    main()
