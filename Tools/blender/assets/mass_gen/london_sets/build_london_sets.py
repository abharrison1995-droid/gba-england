"""London Architecture Modular Sets (4 Distinct Themes, 3 Buildings Each = 12 Models).

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
# S1: Victorian Redbrick
PAL_LONDON_S1 = [
    (0.55, 0.22, 0.16),  # 0: Red Brick Base
    (0.42, 0.16, 0.12),  # 1: Dark Brick Trim
    (0.24, 0.26, 0.30),  # 2: Welsh Slate
    (0.82, 0.80, 0.74),  # 3: Portland Stone Trim / Lintels
    (0.12, 0.13, 0.15),  # 4: Black Gloss Door / Railings
    (0.92, 0.92, 0.90),  # 5: Window White
    (0.15, 0.20, 0.28),  # 6: Glass Dark
    (0.70, 0.35, 0.20),  # 7: Terracotta Chimney Pot
]

# S2: London Stock Yellow Brick / Grimy Georgian
PAL_LONDON_S2 = [
    (0.72, 0.62, 0.44),  # 0: London Stock Yellow Brick
    (0.40, 0.36, 0.30),  # 1: Soot Stained Brick
    (0.22, 0.24, 0.28),  # 2: Slate Roof
    (0.78, 0.75, 0.68),  # 3: Stucco / Stone Cornice
    (0.10, 0.22, 0.45),  # 4: Royal Blue Door
    (0.88, 0.88, 0.85),  # 5: Timber White
    (0.12, 0.16, 0.22),  # 6: Dark Glass
    (0.68, 0.32, 0.18),  # 7: Terracotta Pot
]

# S3: Post-War Council / Brutalist
PAL_LONDON_S3 = [
    (0.62, 0.60, 0.58),  # 0: Weathered Concrete
    (0.45, 0.44, 0.42),  # 1: Exposed Aggregate / Dark Concrete
    (0.50, 0.28, 0.22),  # 2: Utility Red Brick
    (0.30, 0.32, 0.34),  # 3: Bitumen / Felt Roof
    (0.15, 0.45, 0.25),  # 4: Council Green Door / Panels
    (0.75, 0.75, 0.75),  # 5: Metal Window Frames
    (0.14, 0.18, 0.24),  # 6: Glass
    (0.25, 0.25, 0.26),  # 7: Steel Railings
]

# S4: Modern Croydon Suburbia
PAL_LONDON_S4 = [
    (0.84, 0.82, 0.78),  # 0: Clean White/Cream Render
    (0.48, 0.32, 0.20),  # 1: Timber Cladding
    (0.52, 0.28, 0.22),  # 2: Modern Crisp Red Brick
    (0.20, 0.20, 0.22),  # 3: Dark Anthracite Roof Tiles
    (0.12, 0.12, 0.14),  # 4: Anthracite Composite Door / PVC
    (0.95, 0.95, 0.95),  # 5: Pure White Trim
    (0.16, 0.24, 0.32),  # 6: Reflective Modern Glass
    (0.65, 0.65, 0.68),  # 7: Brushed Steel Balconies
]


# ==============================================================================
# SET 1: VICTORIAN REDBRICK
# ==============================================================================

def build_london_s1_redbrick_terrace():
    """10m wide 2-unit tileable redbrick terraced pair."""
    bm = bmesh.new()
    faces = []
    # Main block: 10m wide (X: -5 to +5), 8m deep (Y: -4 to +4), 7m high (Z: 0 to 7)
    # Stucco basement/ground plinth
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 1.0, center=(0, 0, 0.5), color_idx=3)
    # Upper brick walls
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 6.0, center=(0, 0, 4.0), color_idx=0)
    
    # Roof (pitched along X, gables on sides, seamless for tiling)
    faces += mkit.make_pitched_roof(bm, 10.0, 8.0, 2.5, overhang=0.0, center=(0, 0, 7.0), color_idx=2)
    
    # 2x Ground-floor Canted Bay Windows (Unit A at X: -2.5, Unit B at X: +2.5)
    for bx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 2.2, 0.8, 2.8, center=(bx, -4.3, 1.9), color_idx=3)
        # Bay window glass
        faces += mkit.make_cuboid(bm, 1.8, 0.1, 1.8, center=(bx, -4.72, 2.1), color_idx=6)
        # Bay lead roof
        faces += mkit.make_pitched_roof(bm, 2.4, 0.9, 0.5, overhang=0.05, center=(bx, -4.3, 3.3), color_idx=2)
    
    # Upper floor Sash Windows (4 windows, front face Y=-4.0)
    for wx in (-3.8, -1.2, 1.2, 3.8):
        # Stone sill & lintel
        faces += mkit.make_cuboid(bm, 1.2, 0.15, 0.2, center=(wx, -4.05, 4.0), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.2, 0.15, 0.2, center=(wx, -4.05, 5.8), color_idx=3)
        # Window frame & glass
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 1.6, center=(wx, -4.03, 4.9), color_idx=6)
        faces += mkit.make_cuboid(bm, 0.1, 0.12, 1.6, center=(wx, -4.04, 4.9), color_idx=5)
        faces += mkit.make_cuboid(bm, 1.0, 0.12, 0.1, center=(wx, -4.04, 4.9), color_idx=5)
        
    # Front Doors (Unit A at X: -0.2, Unit B at X: +0.2)
    for dx, c_idx in ((-0.6, 4), (0.6, 4)):
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.4, center=(dx, -4.02, 1.7), color_idx=c_idx)
        # Door stone frame
        faces += mkit.make_cuboid(bm, 1.2, 0.15, 0.2, center=(dx, -4.04, 2.95), color_idx=3)
    
    # Central Shared Chimney Stack (X=0.0 on roof ridge)
    faces += mkit.make_cuboid(bm, 1.2, 1.4, 2.0, center=(0, 0, 9.5), color_idx=0)
    faces += mkit.make_cuboid(bm, 1.4, 1.6, 0.2, center=(0, 0, 10.5), color_idx=3)
    # 4 Chimney Pots
    for px in (-0.3, 0.3):
        for py in (-0.3, 0.3):
            faces += mkit.make_cylinder(bm, 0.12, 0.6, segs=6, center=(px, py, 10.9), color_idx=7)

    mkit.apply_bmesh_and_export("building_london_s1_redbrick_terrace", bm, faces, PAL_LONDON_S1, "london/modular_sets")


def build_london_s1_redbrick_villa():
    """Detached large Victorian redbrick villa with gables and porch."""
    bm = bmesh.new()
    faces = []
    # Main Body: 12m wide, 10m deep, 7.5m high
    faces += mkit.make_cuboid(bm, 12.0, 10.0, 1.2, center=(0, 0, 0.6), color_idx=3)
    faces += mkit.make_cuboid(bm, 12.0, 10.0, 6.3, center=(0, 0, 4.35), color_idx=0)
    
    # Main Roof (hipped)
    faces += mkit.make_hipped_roof(bm, 12.0, 10.0, 3.2, overhang=0.4, center=(0, 0, 7.5), color_idx=2)
    
    # Projecting Left Gable Wing (X: -3.5, 4.5m wide, projecting 1.5m out front)
    faces += mkit.make_cuboid(bm, 4.5, 2.0, 7.5, center=(-3.5, -5.5, 3.75), color_idx=0)
    faces += mkit.make_pitched_roof(bm, 2.0, 4.5, 2.0, overhang=0.3, center=(-3.5, -5.5, 7.5), color_idx=2)
    
    # 2-Storey Bay Window on Left Wing
    faces += mkit.make_cuboid(bm, 2.6, 0.8, 5.5, center=(-3.5, -6.6, 3.2), color_idx=3)
    # Bay windows
    faces += mkit.make_cuboid(bm, 2.0, 0.1, 2.0, center=(-3.5, -7.02, 2.2), color_idx=6)
    faces += mkit.make_cuboid(bm, 2.0, 0.1, 2.0, center=(-3.5, -7.02, 4.8), color_idx=6)
    
    # Ornate Entrance Porch (Right side at X: 2.0)
    faces += mkit.make_cuboid(bm, 3.0, 1.8, 0.4, center=(2.0, -5.5, 0.2), color_idx=3)
    # Porch Pillars
    faces += mkit.make_cylinder(bm, 0.15, 3.0, segs=6, center=(0.8, -6.0, 1.7), color_idx=3)
    faces += mkit.make_cylinder(bm, 0.15, 3.0, segs=6, center=(3.2, -6.0, 1.7), color_idx=3)
    # Porch Roof
    faces += mkit.make_hipped_roof(bm, 3.2, 1.8, 1.0, overhang=0.2, center=(2.0, -5.5, 3.2), color_idx=2)
    # Front Door
    faces += mkit.make_cuboid(bm, 1.4, 0.1, 2.6, center=(2.0, -5.02, 1.7), color_idx=4)
    
    # Right Upper Windows
    for wx in (1.0, 3.5):
        faces += mkit.make_cuboid(bm, 1.3, 0.1, 1.8, center=(wx, -5.02, 5.2), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.5, 0.15, 0.2, center=(wx, -5.04, 6.15), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.5, 0.15, 0.2, center=(wx, -5.04, 4.25), color_idx=3)
        
    # Dual Tall Chimneys
    for cx in (-4.0, 4.0):
        faces += mkit.make_cuboid(bm, 1.2, 1.2, 3.0, center=(cx, 1.0, 9.0), color_idx=0)
        faces += mkit.make_cuboid(bm, 1.4, 1.4, 0.3, center=(cx, 1.0, 10.5), color_idx=3)
        for px in (-0.25, 0.25):
            faces += mkit.make_cylinder(bm, 0.12, 0.7, segs=6, center=(cx + px, 1.0, 10.9), color_idx=7)

    mkit.apply_bmesh_and_export("building_london_s1_redbrick_villa", bm, faces, PAL_LONDON_S1, "london/modular_sets")


def build_london_s1_redbrick_flats():
    """3-Storey Victorian Redbrick Walkup Flats."""
    bm = bmesh.new()
    faces = []
    # 16m wide, 10m deep, 11m high
    faces += mkit.make_cuboid(bm, 16.0, 10.0, 1.4, center=(0, 0, 0.7), color_idx=3)
    faces += mkit.make_cuboid(bm, 16.0, 10.0, 9.6, center=(0, 0, 6.2), color_idx=0)
    
    # Mansard / pitched slate roof with stone parapet
    faces += mkit.make_cuboid(bm, 16.2, 10.2, 0.5, center=(0, 0, 11.25), color_idx=3)
    faces += mkit.make_hipped_roof(bm, 15.0, 9.0, 3.0, overhang=0.0, center=(0, 0, 11.5), color_idx=2)
    
    # Central arched communal entrance
    faces += mkit.make_cuboid(bm, 2.6, 0.8, 3.4, center=(0, -5.2, 1.7), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.6, center=(0, -5.3, 1.6), color_idx=4)
    
    # Array of Windows across 3 floors (6 columns)
    for fx, floor_z in enumerate((2.2, 5.5, 8.8)):
        for col_x in (-6.0, -3.6, -1.2, 1.2, 3.6, 6.0):
            if floor_z == 2.2 and abs(col_x) <= 1.5:
                continue # Skip above front entrance
            faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.8, center=(col_x, -5.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.6, 0.15, 0.2, center=(col_x, -5.04, floor_z + 0.95), color_idx=3)
            faces += mkit.make_cuboid(bm, 1.6, 0.15, 0.2, center=(col_x, -5.04, floor_z - 0.95), color_idx=3)
            
    # Dormer Windows on Roof
    for dx in (-4.5, 0.0, 4.5):
        faces += mkit.make_cuboid(bm, 1.8, 1.2, 1.6, center=(dx, -4.2, 12.3), color_idx=0)
        faces += mkit.make_pitched_roof(bm, 1.8, 1.2, 0.8, overhang=0.1, center=(dx, -4.2, 13.1), color_idx=2)
        faces += mkit.make_cuboid(bm, 1.2, 0.1, 1.0, center=(dx, -4.82, 12.3), color_idx=6)
        
    # Symmetrical Chimneys
    for cx in (-7.0, 7.0):
        faces += mkit.make_cuboid(bm, 1.2, 1.6, 2.5, center=(cx, 0, 13.5), color_idx=0)
        faces += mkit.make_cuboid(bm, 1.4, 1.8, 0.2, center=(cx, 0, 14.8), color_idx=3)

    mkit.apply_bmesh_and_export("building_london_s1_redbrick_flats", bm, faces, PAL_LONDON_S1, "london/modular_sets")


# ==============================================================================
# SET 2: LONDON STOCK YELLOW BRICK / GEORGIAN
# ==============================================================================

def build_london_s2_yellowstock_terrace():
    """10m wide 2-unit tileable London stock yellow brick terrace with parapet."""
    bm = bmesh.new()
    faces = []
    # Ground floor rusticated stucco
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 3.2, center=(0, 0, 1.6), color_idx=3)
    # Upper Yellow Stock Brick floors (2 storeys)
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 5.8, center=(0, 0, 6.1), color_idx=0)
    
    # Parapet wall hiding roof slope (characteristic Georgian/Victorian London look)
    faces += mkit.make_cuboid(bm, 10.0, 0.4, 0.8, center=(0, -4.0, 9.4), color_idx=3)
    faces += mkit.make_cuboid(bm, 10.0, 0.4, 0.8, center=(0, 4.0, 9.4), color_idx=3)
    faces += mkit.make_pitched_roof(bm, 10.0, 7.2, 1.8, overhang=0.0, center=(0, 0, 8.8), color_idx=2)
    
    # 2x Symmetrical Royal Blue Front Doors
    for dx in (-3.5, 3.5):
        # Arched fanlight doorway
        faces += mkit.make_cuboid(bm, 1.4, 0.2, 2.8, center=(dx, -4.02, 1.6), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -4.04, 1.4), color_idx=4)
        faces += mkit.make_cuboid(bm, 0.9, 0.08, 0.4, center=(dx, -4.04, 2.65), color_idx=6)
        
    # Ground Floor Large Windows
    for wx in (-1.2, 1.2):
        faces += mkit.make_cuboid(bm, 1.5, 0.1, 2.0, center=(wx, -4.02, 1.7), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.7, 0.15, 0.2, center=(wx, -4.04, 2.8), color_idx=3)
        
    # 1st & 2nd Floor Sash Windows (4 columns)
    for floor_z, h_win in ((4.8, 1.8), (7.4, 1.4)):
        for col_x in (-3.5, -1.2, 1.2, 3.5):
            faces += mkit.make_cuboid(bm, 1.2, 0.1, h_win, center=(col_x, -4.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.4, 0.15, 0.2, center=(col_x, -4.04, floor_z + h_win/2 + 0.1), color_idx=3)
            faces += mkit.make_cuboid(bm, 1.4, 0.15, 0.15, center=(col_x, -4.04, floor_z - h_win/2 - 0.1), color_idx=3)
            
    # Chimney stack on party wall
    faces += mkit.make_cuboid(bm, 1.2, 1.6, 2.2, center=(0, 0, 10.2), color_idx=0)
    for py in (-0.4, 0.4):
        faces += mkit.make_cylinder(bm, 0.14, 0.7, segs=6, center=(0, py, 11.5), color_idx=7)

    mkit.apply_bmesh_and_export("building_london_s2_yellowstock_terrace", bm, faces, PAL_LONDON_S2, "london/modular_sets")


def build_london_s2_georgian_townhouse():
    """Grand 3-storey detached London Georgian townhouse."""
    bm = bmesh.new()
    faces = []
    # 11m wide, 9m deep, 10.5m high
    faces += mkit.make_cuboid(bm, 11.0, 9.0, 3.4, center=(0, 0, 1.7), color_idx=3)
    faces += mkit.make_cuboid(bm, 11.0, 9.0, 7.1, center=(0, 0, 6.95), color_idx=0)
    
    # Parapet and Cornice
    faces += mkit.make_cuboid(bm, 11.4, 9.4, 0.4, center=(0, 0, 10.6), color_idx=3)
    faces += mkit.make_hipped_roof(bm, 10.0, 8.0, 2.2, overhang=0.0, center=(0, 0, 10.6), color_idx=2)
    
    # Grand Central Portico with 2 Roman columns
    faces += mkit.make_cuboid(bm, 3.0, 1.6, 0.3, center=(0, -5.0, 0.15), color_idx=3)
    faces += mkit.make_cylinder(bm, 0.18, 3.2, segs=8, center=(-1.1, -5.4, 1.7), color_idx=3)
    faces += mkit.make_cylinder(bm, 0.18, 3.2, segs=8, center=(1.1, -5.4, 1.7), color_idx=3)
    faces += mkit.make_cuboid(bm, 3.2, 1.8, 0.4, center=(0, -5.0, 3.4), color_idx=3)
    # Triangular pediment above portico
    faces += mkit.make_pitched_roof(bm, 3.2, 1.8, 0.8, overhang=0.1, center=(0, -5.0, 3.6), color_idx=3)
    # Grand Double Door
    faces += mkit.make_cuboid(bm, 1.6, 0.1, 2.8, center=(0, -4.52, 1.6), color_idx=4)
    
    # Symmetrical Windows across 3 storeys
    for floor_z, h_win in ((1.8, 2.0), (5.5, 2.2), (8.5, 1.6)):
        for col_x in (-3.6, 3.6):
            faces += mkit.make_cuboid(bm, 1.5, 0.1, h_win, center=(col_x, -4.52, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.8, 0.15, 0.25, center=(col_x, -4.54, floor_z + h_win/2 + 0.15), color_idx=3)
            faces += mkit.make_cuboid(bm, 1.8, 0.15, 0.2, center=(col_x, -4.54, floor_z - h_win/2 - 0.12), color_idx=3)
            
    # Central 1st Floor Window with Decorative Balconette
    faces += mkit.make_cuboid(bm, 1.8, 0.1, 2.2, center=(0, -4.52, 5.5), color_idx=6)
    faces += mkit.make_cuboid(bm, 2.0, 0.3, 0.6, center=(0, -4.7, 4.4), color_idx=1)
    
    # Twin Roof Chimneys
    for cx in (-4.0, 4.0):
        faces += mkit.make_cuboid(bm, 1.4, 1.4, 2.5, center=(cx, 0, 12.0), color_idx=0)
        for px in (-0.3, 0.3):
            faces += mkit.make_cylinder(bm, 0.13, 0.7, segs=6, center=(cx + px, 0, 13.4), color_idx=7)

    mkit.apply_bmesh_and_export("building_london_s2_georgian_townhouse", bm, faces, PAL_LONDON_S2, "london/modular_sets")


def build_london_s2_yellowstock_flats():
    """3-Storey Soot-Stained Stock Brick Tenement Block."""
    bm = bmesh.new()
    faces = []
    # 15m wide, 10m deep, 10.5m high
    faces += mkit.make_cuboid(bm, 15.0, 10.0, 1.0, center=(0, 0, 0.5), color_idx=1)
    faces += mkit.make_cuboid(bm, 15.0, 10.0, 9.5, center=(0, 0, 5.75), color_idx=0)
    
    # Cornice & Parapet
    faces += mkit.make_cuboid(bm, 15.4, 10.4, 0.4, center=(0, 0, 10.6), color_idx=3)
    faces += mkit.make_hipped_roof(bm, 14.0, 9.0, 2.6, overhang=0.0, center=(0, 0, 10.7), color_idx=2)
    
    # 2x Communal Arched Doors
    for dx in (-4.5, 4.5):
        faces += mkit.make_cuboid(bm, 1.8, 0.2, 2.6, center=(dx, -5.02, 1.5), color_idx=3)
        faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.2, center=(dx, -5.04, 1.3), color_idx=4)
        
    # Regular Fenestration (5 window columns per floor)
    for floor_z in (2.0, 5.2, 8.2):
        for col_x in (-6.0, -3.0, 0.0, 3.0, 6.0):
            if floor_z == 2.0 and (abs(col_x + 4.5) < 0.5 or abs(col_x - 4.5) < 0.5):
                continue
            faces += mkit.make_cuboid(bm, 1.3, 0.1, 1.7, center=(col_x, -5.02, floor_z), color_idx=6)
            faces += mkit.make_cuboid(bm, 1.5, 0.15, 0.2, center=(col_x, -5.04, floor_z + 0.95), color_idx=3)
            faces += mkit.make_cuboid(bm, 1.5, 0.15, 0.15, center=(col_x, -5.04, floor_z - 0.95), color_idx=3)
            
    # Rear External Steel Fire Escape / Stairwell
    faces += mkit.make_cuboid(bm, 3.0, 1.5, 8.0, center=(0, 5.5, 5.0), color_idx=1)
    faces += mkit.make_cuboid(bm, 3.2, 0.1, 0.9, center=(0, 6.2, 3.5), color_idx=1)
    faces += mkit.make_cuboid(bm, 3.2, 0.1, 0.9, center=(0, 6.2, 6.5), color_idx=1)
    faces += mkit.make_cuboid(bm, 3.2, 0.1, 0.9, center=(0, 6.2, 9.5), color_idx=1)

    mkit.apply_bmesh_and_export("building_london_s2_yellowstock_flats", bm, faces, PAL_LONDON_S2, "london/modular_sets")


# ==============================================================================
# SET 3: POST-WAR COUNCIL / BRUTALIST
# ==============================================================================

def build_london_s3_council_terrace():
    """10m wide 2-unit tileable Post-War Council Terrace with concrete panels."""
    bm = bmesh.new()
    faces = []
    # 10m wide, 7.5m deep, 6m high (2 storeys)
    # Brick base
    faces += mkit.make_cuboid(bm, 10.0, 7.5, 2.8, center=(0, 0, 1.4), color_idx=2)
    # Render/Concrete upper floor
    faces += mkit.make_cuboid(bm, 10.0, 7.5, 3.2, center=(0, 0, 4.4), color_idx=0)
    
    # Low-pitch tile roof
    faces += mkit.make_pitched_roof(bm, 10.0, 7.5, 1.5, overhang=0.2, center=(0, 0, 6.0), color_idx=3)
    
    # 2x Concrete Porch Hoods & Green Doors
    for dx in (-3.2, 3.2):
        faces += mkit.make_cuboid(bm, 1.6, 1.0, 0.15, center=(dx, -4.0, 2.5), color_idx=0)
        faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -3.77, 1.1), color_idx=4)
        
    # Wide 1960s Horizontal Windows
    for wx in (-0.8, 0.8):
        faces += mkit.make_cuboid(bm, 2.2, 0.1, 1.6, center=(wx * 2.0, -3.77, 1.4), color_idx=6)
        faces += mkit.make_cuboid(bm, 2.4, 0.12, 0.1, center=(wx * 2.0, -3.78, 0.55), color_idx=5)
        
    # Upper Floor Bedroom Windows (4 wide units)
    for ux in (-3.2, -1.2, 1.2, 3.2):
        faces += mkit.make_cuboid(bm, 1.6, 0.1, 1.4, center=(ux, -3.77, 4.5), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.7, 0.12, 0.1, center=(ux, -3.78, 3.75), color_idx=5)
        
    # Concrete party wall chimney
    faces += mkit.make_cuboid(bm, 0.8, 1.0, 1.4, center=(0, 0, 7.2), color_idx=0)

    mkit.apply_bmesh_and_export("building_london_s3_council_terrace", bm, faces, PAL_LONDON_S3, "london/modular_sets")


def build_london_s3_council_detached():
    """Detached Council / Caretaker House."""
    bm = bmesh.new()
    faces = []
    # 9m wide, 8m deep, 6.2m high
    faces += mkit.make_cuboid(bm, 9.0, 8.0, 3.0, center=(0, 0, 1.5), color_idx=2)
    faces += mkit.make_cuboid(bm, 9.0, 8.0, 3.2, center=(0, 0, 4.6), color_idx=0)
    
    # Hipped roof
    faces += mkit.make_hipped_roof(bm, 9.0, 8.0, 2.2, overhang=0.3, center=(0, 0, 6.2), color_idx=3)
    
    # Side attached outhouse/coal shed (Left side)
    faces += mkit.make_cuboid(bm, 2.5, 4.0, 2.6, center=(-5.5, 0, 1.3), color_idx=2)
    faces += mkit.make_pitched_roof(bm, 2.5, 4.0, 0.8, overhang=0.1, center=(-5.5, 0, 2.6), color_idx=3)
    
    # Front Porch & Entrance
    faces += mkit.make_cuboid(bm, 2.0, 1.2, 2.6, center=(1.5, -4.5, 1.3), color_idx=0)
    faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.1, center=(1.5, -5.12, 1.1), color_idx=4)
    
    # Living room front window
    faces += mkit.make_cuboid(bm, 2.8, 0.1, 1.7, center=(-2.0, -4.02, 1.6), color_idx=6)
    
    # 3x Upper Windows
    for ux in (-2.5, 0.5, 2.8):
        faces += mkit.make_cuboid(bm, 1.6, 0.1, 1.4, center=(ux, -4.02, 4.6), color_idx=6)
        faces += mkit.make_cuboid(bm, 1.7, 0.12, 0.1, center=(ux, -4.04, 3.85), color_idx=5)
        
    # Chimney stack
    faces += mkit.make_cuboid(bm, 0.8, 0.8, 1.6, center=(-2.5, 1.0, 7.6), color_idx=2)

    mkit.apply_bmesh_and_export("building_london_s3_council_detached", bm, faces, PAL_LONDON_S3, "london/modular_sets")


def build_london_s3_brutalist_flats():
    """4-Storey Deck-Access Brutalist Estate Block."""
    bm = bmesh.new()
    faces = []
    # 20m wide, 10m deep, 13m high
    # Concrete structural grid & brick infill
    faces += mkit.make_cuboid(bm, 20.0, 10.0, 13.0, center=(0, 0, 6.5), color_idx=0)
    
    # Flat roof with parapet & lift motor room
    faces += mkit.make_cuboid(bm, 20.2, 10.2, 0.6, center=(0, 0, 13.3), color_idx=1)
    faces += mkit.make_cuboid(bm, 4.0, 4.0, 2.2, center=(-6.0, 0, 14.4), color_idx=0)
    
    # External Cantilevered Access Decks (Floors 2, 3, 4)
    for floor_z in (3.5, 6.8, 10.1):
        # Deck walkway
        faces += mkit.make_cuboid(bm, 18.0, 1.4, 0.3, center=(0, -5.6, floor_z), color_idx=1)
        # Steel safety railing
        faces += mkit.make_cuboid(bm, 18.0, 0.08, 0.9, center=(0, -6.25, floor_z + 0.55), color_idx=7)
        # Front Doors along deck
        for dx in (-7.0, -3.5, 3.5, 7.0):
            faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.2, center=(dx, -5.02, floor_z + 1.2), color_idx=4)
            
    # Ground Floor Recessed Undercroft / Pilotis
    for px in (-8.0, -4.0, 0.0, 4.0, 8.0):
        faces += mkit.make_cuboid(bm, 0.8, 0.8, 3.2, center=(px, -4.5, 1.6), color_idx=1)
        
    # Vertical Stairwell & Glazed Lift Tower (Left side)
    faces += mkit.make_cuboid(bm, 3.5, 3.0, 14.5, center=(-8.5, -4.5, 7.25), color_idx=1)
    for sz in (3.0, 6.5, 10.0, 13.0):
        faces += mkit.make_cuboid(bm, 2.0, 0.1, 1.6, center=(-8.5, -6.02, sz), color_idx=6)

    mkit.apply_bmesh_and_export("building_london_s3_brutalist_flats", bm, faces, PAL_LONDON_S3, "london/modular_sets")


# ==============================================================================
# SET 4: MODERN CROYDON / SUBURBIA
# ==============================================================================

def build_london_s4_modern_terrace():
    """10m wide modern render & timber-clad tileable terrace."""
    bm = bmesh.new()
    faces = []
    # 10m wide, 8m deep, 6.8m high (2.5 storeys)
    # Ground floor crisp brick
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 3.0, center=(0, 0, 1.5), color_idx=2)
    # 1st floor white render
    faces += mkit.make_cuboid(bm, 10.0, 8.0, 3.8, center=(0, 0, 4.9), color_idx=0)
    
    # Modern Anthracite Pitched Roof
    faces += mkit.make_pitched_roof(bm, 10.0, 8.0, 2.2, overhang=0.1, center=(0, 0, 6.8), color_idx=3)
    
    # Timber Cladding Feature Panels around entrance
    for tx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 2.6, 0.1, 5.0, center=(tx, -4.05, 3.2), color_idx=1)
        # Modern Anthracite composite door
        faces += mkit.make_cuboid(bm, 1.1, 0.12, 2.4, center=(tx - 0.5, -4.08, 1.3), color_idx=4)
        # Narrow vertical hallway window
        faces += mkit.make_cuboid(bm, 0.4, 0.12, 2.4, center=(tx + 0.5, -4.08, 1.3), color_idx=6)
        
    # Large Modern Floor-to-Ceiling Windows
    for wx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 2.0, 0.1, 2.2, center=(wx, -4.06, 5.0), color_idx=6)
        # Anthracite window frame
        faces += mkit.make_cuboid(bm, 2.1, 0.12, 0.1, center=(wx, -4.07, 3.85), color_idx=4)
        faces += mkit.make_cuboid(bm, 2.1, 0.12, 0.1, center=(wx, -4.07, 6.15), color_idx=4)

    mkit.apply_bmesh_and_export("building_london_s4_modern_terrace", bm, faces, PAL_LONDON_S4, "london/modular_sets")


def build_london_s4_modern_detached():
    """Modern Executive Detached House with Garage."""
    bm = bmesh.new()
    faces = []
    # 13m wide, 9m deep, 7.2m high
    # Main House (8m wide, right side)
    faces += mkit.make_cuboid(bm, 8.0, 9.0, 6.8, center=(2.5, 0, 3.4), color_idx=0)
    faces += mkit.make_hipped_roof(bm, 8.0, 9.0, 2.8, overhang=0.2, center=(2.5, 0, 6.8), color_idx=3)
    
    # Integrated Single Garage (5m wide, left side)
    faces += mkit.make_cuboid(bm, 5.0, 7.0, 3.4, center=(-4.0, -1.0, 1.7), color_idx=2)
    faces += mkit.make_pitched_roof(bm, 5.0, 7.0, 1.6, overhang=0.15, center=(-4.0, -1.0, 3.4), color_idx=3)
    # Anthracite Sectional Garage Door
    faces += mkit.make_cuboid(bm, 3.2, 0.1, 2.4, center=(-4.0, -4.52, 1.3), color_idx=4)
    
    # Modern Porch Canopy & Front Door
    faces += mkit.make_cuboid(bm, 2.2, 1.2, 0.12, center=(0.5, -4.8, 2.8), color_idx=4)
    faces += mkit.make_cuboid(bm, 1.2, 0.1, 2.4, center=(0.5, -4.52, 1.3), color_idx=4)
    
    # Timber Cladding Accent Section
    faces += mkit.make_cuboid(bm, 3.6, 0.1, 3.0, center=(4.5, -4.52, 5.0), color_idx=1)
    
    # Large Windows
    faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.0, center=(4.5, -4.54, 1.8), color_idx=6)
    faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.0, center=(4.5, -4.54, 5.0), color_idx=6)
    faces += mkit.make_cuboid(bm, 1.4, 0.1, 1.6, center=(0.5, -4.54, 5.0), color_idx=6)

    mkit.apply_bmesh_and_export("building_london_s4_modern_detached", bm, faces, PAL_LONDON_S4, "london/modular_sets")


def build_london_s4_modern_flats():
    """Contemporary 3-Storey Low-Rise Apartment Complex."""
    bm = bmesh.new()
    faces = []
    # 18m wide, 11m deep, 10.5m high
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 3.4, center=(0, 0, 1.7), color_idx=2) # Brick ground floor
    faces += mkit.make_cuboid(bm, 18.0, 11.0, 7.1, center=(0, 0, 6.95), color_idx=0) # Render upper floors
    
    # Flat concealed roof with dark coping
    faces += mkit.make_cuboid(bm, 18.4, 11.4, 0.4, center=(0, 0, 10.6), color_idx=4)
    
    # Alternating Timber Cladding Vertical Bays
    for tx in (-5.5, 5.5):
        faces += mkit.make_cuboid(bm, 4.0, 0.2, 7.0, center=(tx, -5.55, 6.95), color_idx=1)
        
    # Glazed Communal Central Entrance
    faces += mkit.make_cuboid(bm, 3.2, 0.4, 3.0, center=(0, -5.6, 1.5), color_idx=4)
    faces += mkit.make_cuboid(bm, 2.6, 0.1, 2.6, center=(0, -5.7, 1.5), color_idx=6)
    
    # Steel & Glass Balconies (Floors 2 and 3)
    for bz in (4.8, 8.2):
        for bx in (-5.5, 0.0, 5.5):
            # Balcony slab
            faces += mkit.make_cuboid(bm, 3.2, 1.4, 0.2, center=(bx, -6.2, bz), color_idx=4)
            # Glass / steel railing
            faces += mkit.make_cuboid(bm, 3.2, 0.08, 0.9, center=(bx, -6.85, bz + 0.55), color_idx=7)
            faces += mkit.make_cuboid(bm, 0.08, 1.4, 0.9, center=(bx - 1.55, -6.2, bz + 0.55), color_idx=7)
            faces += mkit.make_cuboid(bm, 0.08, 1.4, 0.9, center=(bx + 1.55, -6.2, bz + 0.55), color_idx=7)
            # Sliding balcony door
            faces += mkit.make_cuboid(bm, 2.4, 0.1, 2.2, center=(bx, -5.52, bz + 1.2), color_idx=6)

    mkit.apply_bmesh_and_export("building_london_s4_modern_flats", bm, faces, PAL_LONDON_S4, "london/modular_sets")


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("--- BUILDING ALL 12 LONDON ARCHITECTURE MODELS (<1500 TRIS) ---")
    # S1
    build_london_s1_redbrick_terrace()
    build_london_s1_redbrick_villa()
    build_london_s1_redbrick_flats()
    # S2
    build_london_s2_yellowstock_terrace()
    build_london_s2_georgian_townhouse()
    build_london_s2_yellowstock_flats()
    # S3
    build_london_s3_council_terrace()
    build_london_s3_council_detached()
    build_london_s3_brutalist_flats()
    # S4
    build_london_s4_modern_terrace()
    build_london_s4_modern_detached()
    build_london_s4_modern_flats()
    print("--- ALL 12 LONDON ASSETS COMPLETE ---")


if __name__ == "__main__":
    main()
