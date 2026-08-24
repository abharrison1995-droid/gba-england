"""East York Chinese Architecture Modular Sets (4 Distinct Themes, 3 Buildings Each = 12 Models).

1600 Triangle Budget per asset.
Authentic Chinese architectural aesthetics:
- Set 1: Imperial Forbidden City Style (Yellow Glazed Tiles, Vermilion Pillars, Dougong Brackets)
- Set 2: Jiangnan Water Town Style (Suzhou White Walls, Black Tile Matou Firewalls, Moon Gates)
- Set 3: Lingnan / Cantonese Qilou Covered Arcade Shophouses & Chinatown (Colonnades, Green Glazed Tiles, Lanterns)
- Set 4: Modern Sino-Architecture (Contemporary Grey Masonry, Bronze Geometric Lattice, Sweeping Pagoda Roofs)

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
# S1: Imperial Forbidden City (Yellow & Vermilion)
PAL_EASTYORK_S1 = [
    (0.88, 0.68, 0.12),  # 0: Imperial Yellow Glazed Ceramic Roof Tile
    (0.76, 0.14, 0.10),  # 1: Imperial Vermilion Red Lacquer (Pillars/Doors/Walls)
    (0.92, 0.90, 0.86),  # 2: Carved White Hanbaiyu Marble Plinth / Steps
    (0.18, 0.45, 0.38),  # 3: Qing Dynasty Blue-Green Eave Painting Trim
    (0.85, 0.72, 0.22),  # 4: Gilded Gold Accents / Brass Door Studs
    (0.12, 0.12, 0.14),  # 5: Dark Lacquer Timber Framing
    (0.12, 0.16, 0.22),  # 6: Dark Window Glass / Paper Screen
    (0.92, 0.35, 0.12),  # 7: Festive Red Lantern
]

# S2: Jiangnan Water Town / Suzhou Classical (Black & White)
PAL_EASTYORK_S2 = [
    (0.92, 0.92, 0.90),  # 0: Whitewashed Lime Plaster Wall
    (0.20, 0.22, 0.24),  # 1: Charcoal Black / Dark Grey Clay Roof Tiles
    (0.32, 0.24, 0.18),  # 2: Dark Walnut / Teak Timber Framing & Windows
    (0.55, 0.52, 0.48),  # 3: Weathered River Stone Foundation Plinth
    (0.70, 0.16, 0.12),  # 4: Red Door / Courtyard Lantern
    (0.78, 0.75, 0.68),  # 5: Grey Brick Matou Wall Coping
    (0.12, 0.15, 0.20),  # 6: Dark Glass / Lattice Shadow
    (0.82, 0.68, 0.32),  # 7: Bamboo Gold Trim
]

# S3: Lingnan / Cantonese Qilou Shophouses & Chinatown (Arcade & Green Tile)
PAL_EASTYORK_S3 = [
    (0.82, 0.78, 0.72),  # 0: Cantonese Stucco / Light Grey Render Arcade
    (0.18, 0.50, 0.35),  # 1: Emerald Green Glazed Roof & Balcony Tiles
    (0.75, 0.16, 0.12),  # 2: Vibrant Chinese Red Columns & Frames
    (0.88, 0.75, 0.25),  # 3: Gilded Signboard Gold / Brass
    (0.22, 0.22, 0.24),  # 4: Wrought Iron Balcony Grille
    (0.15, 0.55, 0.75),  # 5: Manchurian Stained Glass Blue / Cyan
    (0.12, 0.14, 0.18),  # 6: Dark Glass
    (0.95, 0.28, 0.15),  # 7: Glowing Red Lantern
]

# S4: Modern Sino-Architecture (Contemporary Grey & Bronze)
PAL_EASTYORK_S4 = [
    (0.38, 0.40, 0.42),  # 0: Sleek Charcoal / Slate Grey Masonry
    (0.70, 0.52, 0.32),  # 1: Warm Bronze / Copper Lattice & Eaves
    (0.85, 0.84, 0.82),  # 2: Light Warm Grey Stone / Concrete
    (0.18, 0.18, 0.20),  # 3: Dark Metal Mullions & Flashing
    (0.72, 0.18, 0.14),  # 4: Modern Vermilion Portal Accent
    (0.25, 0.48, 0.44),  # 5: Jade-Tinted Glass Balconies
    (0.14, 0.20, 0.28),  # 6: Reflective Modern Glass
    (0.90, 0.78, 0.45),  # 7: Champagne Gold Trim
]


# ==============================================================================
# SET 1: IMPERIAL FORBIDDEN CITY STYLE
# ==============================================================================

def build_eastyork_s1_imperial_terrace():
    """10m wide 2-unit tileable Chinese Imperial terraced row with yellow glazed roofs."""
    bm = bmesh.new()
    faces = []
    # Marble foundation plinth (Z: 0 to 0.8)
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 0.8, center=(0, 0, 0.4), color_idx=2)
    # Vermilion main hall walls (Z: 0.8 to 6.8)
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 6.0, center=(0, 0, 3.8), color_idx=1)
    
    # Dougong Bracket Layer under eaves (Blue-green painted beam band)
    faces += mkit.make_cuboid(bm, 10.2, 8.2, 0.5, center=(0, 0, 6.85), color_idx=3)
    
    # Sweeping Imperial Yellow Pagoda Roof with upturned eaves
    faces += mkit.make_pagoda_roof(bm, 10.0, 8.0, 2.6, overhang=0.8, flare=0.5, center=(0, 0, 7.1), color_idx=0)
    
    # Intermediate eave awning between floors
    faces += mkit.make_pagoda_roof(bm, 10.2, 1.4, 0.6, overhang=0.4, flare=0.3, center=(0, -4.4, 3.8), color_idx=0)
    
    # 6x Vermilion Round Columns across front
    for cx in (-4.8, -2.8, -0.8, 0.8, 2.8, 4.8):
        faces += mkit.make_cylinder(bm, 0.18, 6.0, segs=8, center=(cx, -4.1, 3.8), color_idx=1)
        # Marble pillar base pedestal
        faces += mkit.make_cylinder(bm, 0.24, 0.3, segs=8, center=(cx, -4.1, 0.95), color_idx=2)
        
    # 2x Grand Imperial Double Doors with Gold Studs (Unit A at X: -2.8, Unit B at X: +2.8)
    for dx in (-2.8, 2.8):
        faces += mkit.make_cuboid(bm, 1.6, 0.1, 2.6, center=(dx, -4.02, 2.1), color_idx=1)
        # Gold frame & lintel
        faces += mkit.make_cuboid(bm, 1.8, 0.12, 0.2, center=(dx, -4.03, 3.45), color_idx=4)
        # 2x Hanging Red Lanterns beside doors
        faces += mkit.make_cylinder(bm, 0.16, 0.4, segs=6, center=(dx - 0.7, -4.4, 2.8), color_idx=7)
        faces += mkit.make_cylinder(bm, 0.16, 0.4, segs=6, center=(dx + 0.7, -4.4, 2.8), color_idx=7)
        
    # Upper Floor Traditional Chinese Lattice Windows (4 units)
    for wx in (-3.8, -1.8, 1.8, 3.8):
        faces += mkit.make_cuboid(bm, 1.5, 0.1, 1.8, center=(wx, -4.02, 5.4), color_idx=6)
        # Gold fretwork crossbars
        faces += mkit.make_cuboid(bm, 1.6, 0.12, 0.08, center=(wx, -4.03, 5.4), color_idx=4)
        faces += mkit.make_cuboid(bm, 0.08, 0.12, 1.8, center=(wx, -4.03, 5.4), color_idx=4)

    mkit.apply_bmesh_and_export("building_eastyork_s1_imperial_terrace", bm, faces, PAL_EASTYORK_S1, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s1_siheyuan_manor():
    """Grand Imperial Chinese Siheyuan Courtyard Manor with Hip-and-Gable Xieshan Roof."""
    bm = bmesh.new()
    faces = []
    # White marble terrace base (14m wide, 11m deep, 0.8m high)
    faces += mkit.make_cuboid(bm, 14.0, 11.0, 0.8, center=(0, 0, 0.4), color_idx=2)
    # Main palace walls
    faces += mkit.make_cuboid(bm, 14.0, 11.0, 6.4, center=(0, 0, 4.0), color_idx=1)
    
    # Dougong bracket cornice band
    faces += mkit.make_cuboid(bm, 14.4, 11.4, 0.6, center=(0, 0, 7.2), color_idx=3)
    
    # 2-Tier Grand Sweeping Yellow Glazed Pagoda Roofs
    faces += mkit.make_pagoda_roof(bm, 14.0, 11.0, 2.4, overhang=1.0, flare=0.6, center=(0, 0, 7.5), color_idx=0)
    faces += mkit.make_pagoda_roof(bm, 9.0, 7.0, 2.0, overhang=0.8, flare=0.5, center=(0, 0, 9.6), color_idx=0)
    
    # Central Grand Portico with 4 Imperial Red Pillars
    faces += mkit.make_cuboid(bm, 6.0, 2.2, 0.5, center=(0, -6.0, 0.25), color_idx=2)
    for px in (-2.4, -0.8, 0.8, 2.4):
        faces += mkit.make_cylinder(bm, 0.2, 3.6, segs=8, center=(px, -6.8, 1.8), color_idx=1)
    # Portico sweeping roof
    faces += mkit.make_pagoda_roof(bm, 6.4, 2.4, 1.4, overhang=0.6, flare=0.4, center=(0, -6.0, 3.6), color_idx=0)
    
    # Grand Double Vermilion Doors with Gold Lion Head Knockers
    faces += mkit.make_cuboid(bm, 2.2, 0.1, 3.0, center=(0, -5.52, 1.8), color_idx=1)
    faces += mkit.make_cuboid(bm, 2.4, 0.12, 0.25, center=(0, -5.53, 3.35), color_idx=4)
    
    # 2x Carved Guardian Stone Lion Pedestals in front of porch
    for lx in (-3.5, 3.5):
        faces += mkit.make_cuboid(bm, 0.8, 0.8, 0.8, center=(lx, -7.2, 0.4), color_idx=2)
        faces += mkit.make_cuboid(bm, 0.6, 0.6, 0.7, center=(lx, -7.2, 1.15), color_idx=2)
        
    # Large Chinese Lattice Palace Windows (4 units)
    for wx in (-4.8, 4.8):
        faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.2, center=(wx, -5.52, 2.2), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.0, center=(wx, -5.52, 5.6), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.8, 0.12, 0.1, center=(wx, -5.53, 2.2), color_idx=4)
        faces += mkit.make_cuboid(bm, 2.8, 0.12, 0.1, center=(wx, -5.53, 5.6), color_idx=4)

    mkit.apply_bmesh_and_export("building_eastyork_s1_siheyuan_manor", bm, faces, PAL_EASTYORK_S1, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s1_imperial_flats():
    """4-Storey Imperial Chinese Residential Block with Pagoda Balconies."""
    bm = bmesh.new()
    faces = []
    # 18m wide, 11m deep, 14m high
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 1.0, center=(0, 0, 0.5), color_idx=2) # Marble base
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 13.0, center=(0, 0, 7.5), color_idx=1) # Vermilion hall
    
    # Grand Imperial Pagoda Crown Roof
    faces += mkit.make_pagoda_roof(bm, 18.0, 11.0, 3.0, overhang=1.0, flare=0.6, center=(0, 0, 14.0), color_idx=0)
    
    # Cantilevered Pagoda Balconies across Floors 2, 3, and 4
    for bz in (4.5, 8.0, 11.5):
        # Continuous balcony platform
        faces += mkit.make_cuboid(bm, 16.0, 1.6, 0.3, center=(0, -6.3, bz), color_idx=1)
        # Red and gold balustrade
        faces += mkit.make_cuboid(bm, 16.0, 0.08, 0.9, center=(0, -7.05, bz + 0.55), color_idx=4)
        # Pagoda awning over balcony
        faces += mkit.make_pagoda_roof(bm, 16.2, 1.6, 0.6, overhang=0.4, flare=0.25, center=(0, -6.3, bz + 2.8), color_idx=0)
        
        # Sliding lattice doors along balcony (4 doors per floor)
        for dx in (-5.5, -1.8, 1.8, 5.5):
            faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.2, center=(dx, -5.52, bz + 1.2), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.9, 0.12, 0.08, center=(dx, -5.53, bz + 1.2), color_idx=4)
            
    # Ground Floor Imperial Entrance with Colonnade
    for px in (-7.0, -3.5, 0.0, 3.5, 7.0):
        faces += mkit.make_cylinder(bm, 0.22, 3.4, segs=8, center=(px, -5.8, 2.2), color_idx=1)
    faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.8, center=(0, -5.52, 1.7), color_idx=1)

    mkit.apply_bmesh_and_export("building_eastyork_s1_imperial_flats", bm, faces, PAL_EASTYORK_S1, "East York/modular_sets", tri_limit=1600)


# ==============================================================================
# SET 2: JIANGNAN WATER TOWN / SUZHOU CLASSICAL STYLE
# ==============================================================================

def build_eastyork_s2_jiangnan_terrace():
    """10m wide tileable Jiangnan terrace with stepped Matou horse-head firewalls & black tiles."""
    bm = bmesh.new()
    faces = []
    # River stone foundation
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 0.8, center=(0, 0, 0.4), color_idx=3)
    # Whitewashed plaster walls (Z: 0.8 to 7.0)
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 6.2, center=(0, 0, 3.9), color_idx=0)
    
    # Black clay tile pitched roof with flying eave tips
    faces += mkit.make_pagoda_roof(bm, 10.0, 8.0, 2.4, overhang=0.5, flare=0.35, center=(0, 0, 7.0), color_idx=1)
    
    # Stepped Matou Horse-Head Firewalls along Left & Right Party Walls (X=-5.0 and X=+5.0)
    for mx in (-5.0, 5.0):
        # Stepped firewall parapet (3 tiers)
        faces += mkit.make_cuboid(bm, 0.35, 8.2, 1.2, center=(mx, 0, 7.6), color_idx=0)
        faces += mkit.make_cuboid(bm, 0.4, 8.4, 0.2, center=(mx, 0, 8.25), color_idx=5)
        # High center step
        faces += mkit.make_cuboid(bm, 0.35, 4.0, 1.0, center=(mx, 0, 8.8), color_idx=0)
        faces += mkit.make_cuboid(bm, 0.4, 4.2, 0.2, center=(mx, 0, 9.35), color_idx=5)
        
    # 2x Dark Timber Framed Entrances with Black Tile Hoods
    for dx in (-3.2, 3.2):
        faces += mkit.make_cuboid(bm, 1.4, 0.1, 2.4, center=(dx, -4.02, 1.6), color_idx=4)
        # Black tile door canopy
        faces += mkit.make_pagoda_roof(bm, 1.8, 1.0, 0.5, overhang=0.2, flare=0.2, center=(dx, -4.4, 3.0), color_idx=1)
        # Red lantern
        faces += mkit.make_cylinder(bm, 0.14, 0.35, segs=6, center=(dx + 0.8, -4.4, 2.5), color_idx=4)
        
    # Dark Walnut Lattice Windows across Ground & 1st Floor
    for wx in (-1.0, 1.0):
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 1.8, center=(wx * 1.2, -4.02, 1.7), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.9, 0.12, 0.08, center=(wx * 1.2, -4.03, 1.7), color_idx=2)
    for ux in (-3.2, -1.0, 1.0, 3.2):
        faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.6, center=(ux, -4.02, 5.2), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.5, 0.12, 0.08, center=(ux, -4.03, 5.2), color_idx=2)

    mkit.apply_bmesh_and_export("building_eastyork_s2_jiangnan_terrace", bm, faces, PAL_EASTYORK_S2, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s2_suzhou_manor():
    """Suzhou Classical Scholar Garden Manor with Moon Gate Entrance & Black Tiles."""
    bm = bmesh.new()
    faces = []
    # Stone plinth
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 0.8, center=(0, 0, 0.4), color_idx=3)
    # Whitewashed pavilion walls
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 6.4, center=(0, 0, 4.0), color_idx=0)
    
    # 2-Tier Suzhou Sweeping Black Tile Roofs
    faces += mkit.make_pagoda_roof(bm, 13.0, 10.0, 2.4, overhang=0.9, flare=0.55, center=(0, 0, 7.2), color_idx=1)
    faces += mkit.make_pagoda_roof(bm, 8.5, 6.5, 1.8, overhang=0.7, flare=0.45, center=(0, 0, 9.2), color_idx=1)
    
    # Central Moon Gate (Yue Liang Men) Entrance Porch
    faces += mkit.make_cuboid(bm, 3.6, 1.8, 3.4, center=(0, -5.5, 1.7), color_idx=0)
    faces += mkit.make_pagoda_roof(bm, 4.0, 2.0, 1.0, overhang=0.4, flare=0.3, center=(0, -5.5, 3.4), color_idx=1)
    # Moon Gate Circular Portal
    faces += mkit.make_cylinder(bm, 0.95, 0.15, segs=10, center=(0, -6.35, 1.5), color_idx=2)
    faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.2, center=(0, -5.02, 1.2), color_idx=4)
    
    # Matou Firewalls on side gables
    for mx in (-6.5, 6.5):
        faces += mkit.make_cuboid(bm, 0.35, 10.2, 1.4, center=(mx, 0, 7.8), color_idx=0)
        faces += mkit.make_cuboid(bm, 0.4, 10.4, 0.2, center=(mx, 0, 8.55), color_idx=5)
        
    # Elaborate Dark Wood Lattice Windows
    for wx in (-4.2, 4.2):
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 2.0, center=(wx, -5.02, 2.0), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.4, 0.1, 1.8, center=(wx, -5.02, 5.2), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.5, 0.12, 0.08, center=(wx, -5.03, 2.0), color_idx=2)
        faces += mkit.make_cuboid(bm, 2.5, 0.12, 0.08, center=(wx, -5.03, 5.2), color_idx=2)

    mkit.apply_bmesh_and_export("building_eastyork_s2_suzhou_manor", bm, faces, PAL_EASTYORK_S2, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s2_jiangnan_flats():
    """3-Storey Jiangnan Water Town Residential Complex with Tiered Black Tile Awnings."""
    bm = bmesh.new()
    faces = []
    # 17m wide, 11m deep, 11.5m high
    faces += mkit.make_cuboid(bm, 17.0, 11.0, 1.0, center=(0, 0, 0.5), color_idx=3)
    faces += mkit.make_cuboid(bm, 17.0, 11.0, 10.5, center=(0, 0, 6.25), color_idx=0)
    
    # Roof with black tiles and flying corner eaves
    faces += mkit.make_pagoda_roof(bm, 17.0, 11.0, 2.6, overhang=0.8, flare=0.5, center=(0, 0, 11.5), color_idx=1)
    
    # Stepped Matou Firewalls dividing the facade into 3 bays
    for fx in (-8.5, -2.8, 2.8, 8.5):
        faces += mkit.make_cuboid(bm, 0.35, 11.2, 1.2, center=(fx, 0, 12.0), color_idx=0)
        faces += mkit.make_cuboid(bm, 0.4, 11.4, 0.2, center=(fx, 0, 12.65), color_idx=5)
        
    # Tiered Black Tile Awnings across Floors 2 & 3
    for bz in (4.2, 7.8):
        faces += mkit.make_pagoda_roof(bm, 17.2, 1.5, 0.5, overhang=0.3, flare=0.2, center=(0, -6.0, bz + 2.8), color_idx=1)
        # Dark wood balconies
        faces += mkit.make_cuboid(bm, 15.0, 1.4, 0.2, center=(0, -6.1, bz), color_idx=2)
        faces += mkit.make_cuboid(bm, 15.0, 0.08, 0.85, center=(0, -6.75, bz + 0.5), color_idx=2)
        
    # Windows & Entrances
    for floor_z in (1.8, 5.4, 9.0):
        for col_x in (-5.5, 0.0, 5.5):
            faces += mkit.make_cuboid(bm, 2.0, 0.1, 1.8, center=(col_x, -5.52, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 2.1, 0.12, 0.08, center=(col_x, -5.53, floor_z), color_idx=2)

    mkit.apply_bmesh_and_export("building_eastyork_s2_jiangnan_flats", bm, faces, PAL_EASTYORK_S2, "East York/modular_sets", tri_limit=1600)


# ==============================================================================
# SET 3: LINGNAN / CANTONESE QILOU ARCADE & CHINATOWN STYLE
# ==============================================================================

def build_eastyork_s3_qilou_terrace():
    """10m wide tileable Cantonese Qilou covered-arcade shophouse terrace with green glazed tiles."""
    bm = bmesh.new()
    faces = []
    # Ground floor covered pedestrian arcade (Z: 0 to 3.8, recessed front wall by 2.0m)
    # Upper floors (Z: 3.8 to 8.5) cantilevered forward over sidewalk
    faces += mkit.make_cuboid(bm, 10.0, 6.0, 3.8, center=(0, 1.0, 1.9), color_idx=0) # Recessed ground shop wall
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 4.7, center=(0, 0, 6.15), color_idx=0) # Upper cantilevered body
    
    # 4x Arcade Columns supporting upper facade (at front edge Y: -4.0)
    for col_x in (-4.8, -1.6, 1.6, 4.8):
        faces += mkit.make_cuboid(bm, 0.45, 0.45, 3.8, center=(col_x, -3.77, 1.9), color_idx=2) # Red pillars
    # Arched arcade lintel beam
    faces += mkit.make_cuboid(bm, 10.0, 0.5, 0.6, center=(0, -3.75, 3.5), color_idx=0)
    
    # Decorative Lingnan Parapet Pediment with Green Glazed Balusters
    faces += mkit.make_cuboid(bm, 10.0, 0.3, 1.2, center=(0, -4.0, 9.1), color_idx=0)
    faces += mkit.make_cuboid(bm, 10.0, 0.35, 0.2, center=(0, -4.0, 9.75), color_idx=1)
    # Green glazed tile eaves
    faces += mkit.make_pagoda_roof(bm, 10.0, 7.5, 1.8, overhang=0.4, flare=0.3, center=(0, 0.2, 8.5), color_idx=1)
    
    # 2x Ground Shopfronts under arcade (display glass, red doors, gold signs)
    for sx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.2, center=(sx, -1.95, 1.6), color_idx=6) # Glass
        faces += mkit.make_cuboid(bm, 1.0, 0.12, 2.2, center=(sx + 0.8, -1.94, 1.6), color_idx=2) # Red door
        faces += mkit.make_cuboid(bm, 2.2, 0.08, 0.4, center=(sx, -1.94, 2.95), color_idx=3) # Gold sign
        # Red lantern under arcade
        faces += mkit.make_cylinder(bm, 0.14, 0.35, segs=6, center=(sx, -3.0, 3.1), color_idx=7)
        
    # 1st & 2nd Floor Veranda Windows with Manchurian Cyan Stained Glass
    for floor_z in (5.0, 7.2):
        for wx in (-3.2, -1.0, 1.0, 3.2):
            faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.6, center=(wx, -4.02, floor_z), color_idx=5)
            faces += mkit.make_cuboid(bm, 1.5, 0.12, 0.1, center=(wx, -4.03, floor_z + 0.85), color_idx=2)

    mkit.apply_bmesh_and_export("building_eastyork_s3_qilou_terrace", bm, faces, PAL_EASTYORK_S3, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s3_cantonese_mansion():
    """Grand Lingnan Merchant Mansion with Green Glazed Roof and Dragon Ridge Caps."""
    bm = bmesh.new()
    faces = []
    # 13m wide, 10m deep, 7.8m high
    faces += mkit.make_cuboid(bm, 13.0, 10.0, 7.8, center=(0, 0, 3.9), color_idx=0)
    
    # Sweeping Green Glazed Ceramic Tile Roof
    faces += mkit.make_pagoda_roof(bm, 13.0, 10.0, 2.8, overhang=0.8, flare=0.5, center=(0, 0, 7.8), color_idx=1)
    
    # 2-Storey Central Veranda with Red Arches & Iron Railings
    faces += mkit.make_cuboid(bm, 5.0, 1.8, 7.8, center=(0, -5.5, 3.9), color_idx=0)
    # 4 Red Columns on Ground & 1st floor
    for px in (-2.0, -0.7, 0.7, 2.0):
        faces += mkit.make_cylinder(bm, 0.16, 7.4, segs=8, center=(px, -6.3, 3.7), color_idx=2)
    # Veranda floor slab & iron railing
    faces += mkit.make_cuboid(bm, 5.2, 1.8, 0.25, center=(0, -5.5, 3.9), color_idx=0)
    faces += mkit.make_cuboid(bm, 5.0, 0.08, 0.9, center=(0, -6.35, 4.45), color_idx=4)
    
    # Grand Double Door with Brass Trim
    faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.6, center=(0, -5.02, 1.5), color_idx=2)
    faces += mkit.make_cuboid(bm, 2.0, 0.12, 0.2, center=(0, -5.03, 2.9), color_idx=3)
    
    # Manchurian Stained Glass Windows
    for wx in (-4.2, 4.2):
        faces += mkit.make_cuboid(bm, 2.2, 0.1, 2.0, center=(wx, -5.02, 2.0), color_idx=5)
        faces += mkit.make_cuboid(bm, 2.2, 0.1, 2.0, center=(wx, -5.02, 5.4), color_idx=5)
        faces += mkit.make_cuboid(bm, 2.4, 0.12, 0.15, center=(wx, -5.03, 3.1), color_idx=2)
        faces += mkit.make_cuboid(bm, 2.4, 0.12, 0.15, center=(wx, -5.03, 6.5), color_idx=2)

    mkit.apply_bmesh_and_export("building_eastyork_s3_cantonese_mansion", bm, faces, PAL_EASTYORK_S3, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s3_chinatown_flats():
    """4-Storey Chinatown Mixed Commercial / Residential Block with Rooftop Pagoda Pavilion."""
    bm = bmesh.new()
    faces = []
    # 18m wide, 11m deep, 13.5m high
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 4.0, center=(0, 0, 2.0), color_idx=0) # Ground arcade
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 9.5, center=(0, 0, 8.75), color_idx=0) # Upper apartments
    
    # Rooftop Pagoda Pavilion Crown
    faces += mkit.make_cuboid(bm, 18.4, 11.4, 0.5, center=(0, 0, 13.75), color_idx=1)
    faces += mkit.make_pagoda_roof(bm, 10.0, 7.0, 2.2, overhang=0.8, flare=0.5, center=(0, 0, 14.0), color_idx=1)
    
    # Cantilevered Red Iron Balconies across Floors 2, 3, and 4
    for bz in (4.5, 7.8, 11.0):
        faces += mkit.make_cuboid(bm, 16.0, 1.4, 0.2, center=(0, -6.2, bz), color_idx=2)
        faces += mkit.make_cuboid(bm, 16.0, 0.08, 0.9, center=(0, -6.85, bz + 0.55), color_idx=4)
        # Windows/doors
        for dx in (-5.5, -1.8, 1.8, 5.5):
            faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.0, center=(dx, -5.52, bz + 1.1), color_idx=6)
            
    # Ground Floor Chinatown Restaurant & Tea Shop Frontages
    for sx in (-5.0, 0.0, 5.0):
        faces += mkit.make_cuboid(bm, 4.2, 0.1, 2.6, center=(sx, -5.52, 1.8), color_idx=6)
        faces += mkit.make_cuboid(bm, 3.6, 0.08, 0.5, center=(sx, -5.54, 3.3), color_idx=3) # Gold sign
        faces += mkit.make_cylinder(bm, 0.18, 0.45, segs=6, center=(sx - 1.6, -5.8, 3.1), color_idx=7)
        faces += mkit.make_cylinder(bm, 0.18, 0.45, segs=6, center=(sx + 1.6, -5.8, 3.1), color_idx=7)

    mkit.apply_bmesh_and_export("building_eastyork_s3_chinatown_flats", bm, faces, PAL_EASTYORK_S3, "East York/modular_sets", tri_limit=1600)


# ==============================================================================
# SET 4: MODERN SINO-ARCHITECTURE
# ==============================================================================

def build_eastyork_s4_modern_sino_terrace():
    """10m wide contemporary Chinese terrace with charcoal masonry & bronze pagoda eaves."""
    bm = bmesh.new()
    faces = []
    # Sleek dark masonry body: 10m wide, 8m deep, 7.0m high
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 7.0, center=(0, 0, 3.5), color_idx=0)
    
    # Contemporary Angular Bronze Pagoda Eaves
    faces += mkit.make_pagoda_roof(bm, 10.0, 8.0, 2.2, overhang=0.6, flare=0.4, center=(0, 0, 7.0), color_idx=1)
    
    # Modern Vermilion Entrance Portals with Bronze Grille Screen
    for dx in (-3.0, 3.0):
        faces += mkit.make_cuboid(bm, 2.2, 0.6, 3.2, center=(dx, -4.2, 1.6), color_idx=4)
        faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.4, center=(dx, -4.42, 1.3), color_idx=3)
        # Bronze Geometric Screen Panel
        faces += mkit.make_cuboid(bm, 0.6, 0.05, 2.4, center=(dx + 0.7, -4.42, 1.3), color_idx=1)
        
    # Large Modern Floor-to-Ceiling Windows with Bronze Chinese Fretwork
    for wx in (-3.0, 3.0):
        faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.2, center=(wx, -4.02, 5.0), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.7, 0.12, 0.08, center=(wx, -4.03, 5.0), color_idx=1)
        faces += mkit.make_cuboid(bm, 0.08, 0.12, 2.2, center=(wx, -4.03, 5.0), color_idx=1)
        
    for cx in (0.0,):
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.2, center=(cx, -4.02, 1.8), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.2, center=(cx, -4.02, 5.0), color_idx=6)

    mkit.apply_bmesh_and_export("building_eastyork_s4_modern_sino_terrace", bm, faces, PAL_EASTYORK_S4, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s4_contemporary_estate():
    """Modern Luxury Chinese Villa with Copper Eaves and Zen Entrance."""
    bm = bmesh.new()
    faces = []
    # 14m wide, 10m deep, 7.2m high
    faces += mkit.make_cuboid(bm, 14.0, 10.0, 7.2, center=(0, 0, 3.6), color_idx=0)
    
    # Sweeping Modern Copper / Bronze Pagoda Roof
    faces += mkit.make_pagoda_roof(bm, 14.0, 10.0, 2.5, overhang=0.9, flare=0.5, center=(0, 0, 7.2), color_idx=1)
    
    # Projecting Glass Pavilion Wing (Right side, X: 3.5)
    faces += mkit.make_cuboid(bm, 5.5, 2.0, 7.2, center=(3.5, -5.5, 3.6), color_idx=6)
    faces += mkit.make_pagoda_roof(bm, 5.8, 2.2, 1.2, overhang=0.4, flare=0.3, center=(3.5, -5.5, 7.2), color_idx=1)
    # Bronze vertical mullions on glass wing
    for mx in (1.5, 3.5, 5.5):
        faces += mkit.make_cuboid(bm, 0.08, 2.05, 7.2, center=(mx, -5.5, 3.6), color_idx=1)
        
    # Modern Vermilion & Stone Grand Entrance (Left side, X: -3.5)
    faces += mkit.make_cuboid(bm, 4.0, 1.8, 3.6, center=(-3.5, -5.5, 1.8), color_idx=2)
    faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.6, center=(-3.5, -6.32, 1.4), color_idx=4)
    # Bronze canopy
    faces += mkit.make_cuboid(bm, 4.4, 2.2, 0.15, center=(-3.5, -5.5, 3.65), color_idx=1)

    mkit.apply_bmesh_and_export("building_eastyork_s4_contemporary_estate", bm, faces, PAL_EASTYORK_S4, "East York/modular_sets", tri_limit=1600)


def build_eastyork_s4_sino_tower_flats():
    """4-Storey High-Density Modern Sino-Residential Complex with Jade Balconies."""
    bm = bmesh.new()
    faces = []
    # 18m wide, 11m deep, 14m high
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 14.0, center=(0, 0, 7.0), color_idx=0)
    
    # Modern Pagoda Crown Roof
    faces += mkit.make_pagoda_roof(bm, 18.0, 11.0, 2.6, overhang=0.8, flare=0.5, center=(0, 0, 14.0), color_idx=1)
    
    # Cantilevered Jade-Glass Balconies across Floors 2, 3, and 4
    for bz in (4.4, 7.8, 11.2):
        faces += mkit.make_cuboid(bm, 16.0, 1.5, 0.25, center=(0, -6.2, bz), color_idx=3)
        # Jade glass balustrade
        faces += mkit.make_cuboid(bm, 16.0, 0.06, 0.9, center=(0, -6.9, bz + 0.55), color_idx=5)
        # Bronze horizontal trim
        faces += mkit.make_cuboid(bm, 16.2, 0.08, 0.08, center=(0, -6.9, bz + 1.0), color_idx=1)
        
        # Floor-to-ceiling sliding glass doors
        for dx in (-5.5, -1.8, 1.8, 5.5):
            faces += mkit.make_cuboid(bm, 2.2, 0.1, 2.4, center=(dx, -5.52, bz + 1.3), color_idx=6)
            
    # Ground Floor Contemporary Portal & Lounge
    faces += mkit.make_cuboid(bm, 5.0, 1.0, 3.6, center=(0, -5.8, 1.8), color_idx=2)
    faces += mkit.make_cuboid(bm, 2.4, 0.1, 2.6, center=(0, -6.22, 1.4), color_idx=4)

    mkit.apply_bmesh_and_export("building_eastyork_s4_sino_tower_flats", bm, faces, PAL_EASTYORK_S4, "East York/modular_sets", tri_limit=1600)


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("--- BUILDING ALL 12 EAST YORK CHINESE ARCHITECTURE MODELS (<1600 TRIS) ---")
    # S1: Imperial Forbidden City
    build_eastyork_s1_imperial_terrace()
    build_eastyork_s1_siheyuan_manor()
    build_eastyork_s1_imperial_flats()
    # S2: Jiangnan Water Town / Suzhou Classical
    build_eastyork_s2_jiangnan_terrace()
    build_eastyork_s2_suzhou_manor()
    build_eastyork_s2_jiangnan_flats()
    # S3: Lingnan / Cantonese Qilou Arcade & Chinatown
    build_eastyork_s3_qilou_terrace()
    build_eastyork_s3_cantonese_mansion()
    build_eastyork_s3_chinatown_flats()
    # S4: Modern Sino-Architecture
    build_eastyork_s4_modern_sino_terrace()
    build_eastyork_s4_contemporary_estate()
    build_eastyork_s4_sino_tower_flats()
    print("--- ALL 12 EAST YORK ASSETS COMPLETE ---")


if __name__ == "__main__":
    main()
