"""Interior Modular Props Kits for Prefab Chunks (15 High-Quality Low-Poly Models).

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
PAL_INTERIOR_GENERAL = [
    (0.35, 0.22, 0.14),  # 0: Dark Wood (Mahogany / Teak)
    (0.65, 0.52, 0.38),  # 1: Light Wood (Pine / Oak)
    (0.78, 0.78, 0.80),  # 2: Metal / Steel / Chrome
    (0.20, 0.20, 0.22),  # 3: Dark Metal / Plastic / Black
    (0.85, 0.85, 0.85),  # 4: White Plastic / Ceramic / Paper
    (0.70, 0.18, 0.15),  # 5: Fabric Red / Accent
    (0.18, 0.42, 0.65),  # 6: Blue Accent / Screen Glow
    (0.88, 0.75, 0.25),  # 7: Brass / Gold / Warning Yellow
]


# ==============================================================================
# SHOP / COMMERCIAL PROPS
# ==============================================================================

def build_interior_quidland_checkout():
    """Pound shop checkout counter with till, scanner & conveyor."""
    bm = bmesh.new()
    faces = []
    # Counter Body: 2.2m long, 0.9m wide, 0.9m high
    faces += mkit.make_cuboid(bm, 2.2, 0.9, 0.85, center=(0, 0, 0.425), color_idx=4)
    # Counter top trim
    faces += mkit.make_cuboid(bm, 2.3, 0.95, 0.05, center=(0, 0, 0.875), color_idx=3)
    # Black rubber conveyor belt
    faces += mkit.make_cuboid(bm, 1.2, 0.5, 0.02, center=(-0.4, 0, 0.91), color_idx=3)
    # Cash Register / POS Till
    faces += mkit.make_cuboid(bm, 0.45, 0.45, 0.25, center=(0.6, 0, 1.02), color_idx=3)
    # Till Screen
    faces += mkit.make_cuboid(bm, 0.3, 0.05, 0.25, center=(0.6, 0.2, 1.25), color_idx=6)
    # Cash drawer base
    faces += mkit.make_cuboid(bm, 0.48, 0.48, 0.1, center=(0.6, 0, 0.95), color_idx=2)
    # Perspex divider screen
    faces += mkit.make_cuboid(bm, 1.4, 0.02, 0.7, center=(-0.2, 0.35, 1.25), color_idx=2)

    mkit.apply_bmesh_and_export("interior_quidland_checkout", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_quidland_aisle_shelf():
    """Double-sided metal supermarket/pound shop shelving unit with stacked goods."""
    bm = bmesh.new()
    faces = []
    # Metal Upright Frame: 2.4m long, 0.8m wide, 2.0m high
    # End panels
    faces += mkit.make_cuboid(bm, 0.08, 0.8, 2.0, center=(-1.2, 0, 1.0), color_idx=2)
    faces += mkit.make_cuboid(bm, 0.08, 0.8, 2.0, center=(1.2, 0, 1.0), color_idx=2)
    # Central divider
    faces += mkit.make_cuboid(bm, 2.4, 0.05, 1.9, center=(0, 0, 1.0), color_idx=2)
    
    # 4 Shelving tiers on both sides (-Y and +Y)
    for sz in (0.3, 0.75, 1.2, 1.65):
        # Shelf planks
        faces += mkit.make_cuboid(bm, 2.35, 0.75, 0.04, center=(0, 0, sz), color_idx=4)
        # Shelf price tag lip
        faces += mkit.make_cuboid(bm, 2.35, 0.02, 0.05, center=(0, -0.38, sz + 0.02), color_idx=7)
        faces += mkit.make_cuboid(bm, 2.35, 0.02, 0.05, center=(0, 0.38, sz + 0.02), color_idx=7)
        
        # Stock boxes / cans on shelves
        for bx in (-0.8, -0.3, 0.3, 0.8):
            faces += mkit.make_cuboid(bm, 0.35, 0.28, 0.25, center=(bx, -0.2, sz + 0.15), color_idx=5)
            faces += mkit.make_cuboid(bm, 0.35, 0.28, 0.25, center=(bx, 0.2, sz + 0.15), color_idx=6)

    mkit.apply_bmesh_and_export("interior_quidland_aisle_shelf", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_fusports_rack():
    """Sports shop apparel and equipment display rack."""
    bm = bmesh.new()
    faces = []
    # Steel frame stand: 2.0m long, 0.6m wide, 1.8m high
    faces += mkit.make_cuboid(bm, 2.0, 0.6, 0.1, center=(0, 0, 0.05), color_idx=3)
    # Side poles
    faces += mkit.make_cuboid(bm, 0.06, 0.06, 1.7, center=(-0.95, 0, 0.95), color_idx=2)
    faces += mkit.make_cuboid(bm, 0.06, 0.06, 1.7, center=(0.95, 0, 0.95), color_idx=2)
    # Top hanging rail
    faces += mkit.make_cuboid(bm, 1.9, 0.04, 0.04, center=(0, 0, 1.75), color_idx=2)
    
    # Hanging Tracksuits & Jerseys (5 items)
    for jx, col in ((-0.6, 5), (-0.3, 6), (0.0, 3), (0.3, 5), (0.6, 6)):
        # Hanger
        faces += mkit.make_cuboid(bm, 0.4, 0.02, 0.08, center=(jx, 0, 1.7), color_idx=2)
        # Jersey body
        faces += mkit.make_cuboid(bm, 0.45, 0.15, 0.75, center=(jx, 0, 1.25), color_idx=col)
        
    # Lower Shelf with Boxing Gloves & Trainers
    faces += mkit.make_cuboid(bm, 1.8, 0.5, 0.03, center=(0, 0, 0.4), color_idx=1)
    for gx in (-0.5, 0.5):
        faces += mkit.make_cuboid(bm, 0.25, 0.35, 0.18, center=(gx, 0, 0.5), color_idx=5)

    mkit.apply_bmesh_and_export("interior_fusports_rack", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_weapon_pegboard():
    """Wall-mounted black pegboard rack loaded with melee weapons and batons."""
    bm = bmesh.new()
    faces = []
    # Backing Pegboard: 2.0m wide, 0.06m deep, 1.5m high
    faces += mkit.make_cuboid(bm, 2.0, 0.06, 1.5, center=(0, 0, 1.2), color_idx=3)
    # Metal frame rim
    faces += mkit.make_cuboid(bm, 2.08, 0.08, 1.58, center=(0, 0, 1.2), color_idx=7)
    
    # 2x Mounted Machetes / Large Blades
    for my, mx in ((1.6, -0.4), (1.3, -0.4)):
        # Steel blade
        faces += mkit.make_cuboid(bm, 0.9, 0.02, 0.1, center=(mx, -0.05, my), color_idx=2)
        # Handle
        faces += mkit.make_cuboid(bm, 0.25, 0.04, 0.08, center=(mx - 0.5, -0.05, my), color_idx=3)
        
    # 2x Police Batons
    for by in ((1.6, 0.5), (1.3, 0.5)):
        faces += mkit.make_cylinder(bm, 0.03, 0.75, segs=6, center=(by[1], -0.06, by[0]), color_idx=3)
        
    # Lower Hook Shelf with Knuckledusters / Ammo boxes
    faces += mkit.make_cuboid(bm, 1.8, 0.25, 0.04, center=(0, -0.15, 0.65), color_idx=3)
    for ax in (-0.6, -0.2, 0.2, 0.6):
        faces += mkit.make_cuboid(bm, 0.25, 0.18, 0.15, center=(ax, -0.15, 0.75), color_idx=7)

    mkit.apply_bmesh_and_export("interior_weapon_pegboard", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


# ==============================================================================
# CIVIC / POLICE STATION PROPS
# ==============================================================================

def build_interior_police_desk():
    """Police workstation with desk, CRT monitor, keyboard, lamp & swivel chair."""
    bm = bmesh.new()
    faces = []
    # Main Desk: 1.6m wide, 0.8m deep, 0.75m high
    faces += mkit.make_cuboid(bm, 1.6, 0.8, 0.05, center=(0, 0, 0.725), color_idx=1)
    # Side drawer pedestals
    faces += mkit.make_cuboid(bm, 0.45, 0.75, 0.7, center=(-0.55, 0, 0.35), color_idx=2)
    faces += mkit.make_cuboid(bm, 0.45, 0.75, 0.7, center=(0.55, 0, 0.35), color_idx=2)
    
    # CRT Computer Monitor
    faces += mkit.make_cuboid(bm, 0.42, 0.38, 0.35, center=(-0.2, 0.15, 0.95), color_idx=4)
    # CRT Screen
    faces += mkit.make_cuboid(bm, 0.34, 0.02, 0.26, center=(-0.2, -0.04, 0.95), color_idx=6)
    # Keyboard
    faces += mkit.make_cuboid(bm, 0.45, 0.18, 0.03, center=(-0.2, -0.22, 0.765), color_idx=4)
    
    # Case Files / Dossier Folders (Right side)
    faces += mkit.make_cuboid(bm, 0.35, 0.28, 0.08, center=(0.45, 0.1, 0.79), color_idx=7)
    
    # Swivel Chair behind desk (at Y: -0.65)
    # Base star & post
    faces += mkit.make_cylinder(bm, 0.04, 0.4, segs=6, center=(0, -0.65, 0.2), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.55, 0.55, 0.05, center=(0, -0.65, 0.05), color_idx=3)
    # Seat cushion & backrest
    faces += mkit.make_cuboid(bm, 0.5, 0.5, 0.08, center=(0, -0.65, 0.44), color_idx=6)
    faces += mkit.make_cuboid(bm, 0.5, 0.08, 0.5, center=(0, -0.86, 0.7), color_idx=6)

    mkit.apply_bmesh_and_export("interior_police_desk", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_police_cell():
    """Police station iron-bar jail cell front with sliding gate and wooden bench."""
    bm = bmesh.new()
    faces = []
    # Cell Outer Frame: 3.0m wide, 0.15m deep, 2.6m high
    faces += mkit.make_cuboid(bm, 3.0, 0.15, 0.15, center=(0, 0, 2.525), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.15, 0.15, 2.6, center=(-1.425, 0, 1.3), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.15, 0.15, 2.6, center=(1.425, 0, 1.3), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.15, 0.15, 2.6, center=(0.1, 0, 1.3), color_idx=3)
    
    # Vertical Iron Bars across fixed cell section (Left side, X: -1.4 to 0.0)
    for bx in (-1.25, -1.05, -0.85, -0.65, -0.45, -0.25, -0.05):
        faces += mkit.make_cylinder(bm, 0.025, 2.4, segs=6, center=(bx, 0, 1.25), color_idx=2)
        
    # Sliding Gate Section (Right side, X: 0.1 to 1.4)
    faces += mkit.make_cuboid(bm, 1.25, 0.1, 0.1, center=(0.75, 0.05, 2.35), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.25, 0.1, 0.1, center=(0.75, 0.05, 0.1), color_idx=3)
    for gx in (0.3, 0.5, 0.7, 0.9, 1.1, 1.3):
        faces += mkit.make_cylinder(bm, 0.025, 2.2, segs=6, center=(gx, 0.05, 1.25), color_idx=2)
    # Heavy mechanical lockbox
    faces += mkit.make_cuboid(bm, 0.15, 0.18, 0.25, center=(0.15, 0.05, 1.2), color_idx=7)
    
    # Cell Wooden Bench behind bars
    faces += mkit.make_cuboid(bm, 2.0, 0.6, 0.06, center=(-0.4, 1.0, 0.45), color_idx=0)
    faces += mkit.make_cuboid(bm, 0.08, 0.55, 0.42, center=(-1.2, 1.0, 0.21), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.08, 0.55, 0.42, center=(0.4, 1.0, 0.21), color_idx=3)

    mkit.apply_bmesh_and_export("interior_police_cell", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_cityhall_dais():
    """Civic Council Dais / Mayor's Bench with podium, microphones and flags."""
    bm = bmesh.new()
    faces = []
    # Raised Wooden Platform: 3.5m wide, 2.0m deep, 0.3m high
    faces += mkit.make_cuboid(bm, 3.5, 2.0, 0.3, center=(0, 0, 0.15), color_idx=0)
    
    # Curved / Paneled Councillor Bench
    faces += mkit.make_cuboid(bm, 3.0, 0.7, 0.85, center=(0, -0.3, 0.725), color_idx=0)
    # Gold decorative inlay moulding
    faces += mkit.make_cuboid(bm, 2.9, 0.02, 0.75, center=(0, -0.66, 0.725), color_idx=7)
    
    # Central Speaker's Lectern / Podium
    faces += mkit.make_cuboid(bm, 0.7, 0.6, 1.15, center=(0, -0.35, 0.875), color_idx=0)
    faces += mkit.make_cuboid(bm, 0.75, 0.65, 0.05, center=(0, -0.35, 1.46), color_idx=7)
    
    # High-backed Mayor's Leather Chair
    faces += mkit.make_cuboid(bm, 0.7, 0.65, 0.1, center=(0, 0.4, 0.55), color_idx=5)
    faces += mkit.make_cuboid(bm, 0.7, 0.12, 1.0, center=(0, 0.7, 1.05), color_idx=5)
    faces += mkit.make_cuboid(bm, 0.74, 0.14, 0.1, center=(0, 0.7, 1.58), color_idx=7)

    mkit.apply_bmesh_and_export("interior_cityhall_dais", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_office_filing():
    """Bank of 3 metal filing cabinets with open drawers & archive boxes."""
    bm = bmesh.new()
    faces = []
    # 3x Metal Cabinets side by side: 1.5m total wide, 0.6m deep, 1.4m high
    for cx in (-0.5, 0.0, 0.5):
        faces += mkit.make_cuboid(bm, 0.48, 0.6, 1.38, center=(cx, 0, 0.69), color_idx=2)
        # 4 Drawer fronts
        for dz in (0.2, 0.52, 0.84, 1.16):
            faces += mkit.make_cuboid(bm, 0.44, 0.02, 0.28, center=(cx, -0.31, dz), color_idx=3)
            # Chrome handle
            faces += mkit.make_cuboid(bm, 0.15, 0.03, 0.03, center=(cx, -0.33, dz), color_idx=4)
            
    # Open drawer in middle cabinet
    faces += mkit.make_cuboid(bm, 0.42, 0.35, 0.24, center=(0, -0.45, 0.84), color_idx=2)
    # File tabs
    faces += mkit.make_cuboid(bm, 0.38, 0.3, 0.05, center=(0, -0.45, 0.98), color_idx=7)
    
    # Stacked Cardboard Archive Boxes on top
    faces += mkit.make_cuboid(bm, 0.4, 0.45, 0.3, center=(-0.5, 0, 1.54), color_idx=1)
    faces += mkit.make_cuboid(bm, 0.4, 0.45, 0.3, center=(0.5, 0, 1.54), color_idx=1)

    mkit.apply_bmesh_and_export("interior_office_filing", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


# ==============================================================================
# PUB / THE WINCHESTER PROPS
# ==============================================================================

def build_interior_pub_bar():
    """Polished mahogany pub bar counter with draught beer pumps and brass footrail."""
    bm = bmesh.new()
    faces = []
    # Main Bar Counter: 3.0m wide, 0.9m deep, 1.1m high
    faces += mkit.make_cuboid(bm, 3.0, 0.8, 1.05, center=(0, 0, 0.525), color_idx=0)
    # Overhanging polished mahogany counter top
    faces += mkit.make_cuboid(bm, 3.1, 0.95, 0.08, center=(0, 0, 1.09), color_idx=0)
    
    # Brass Footrail along bottom front
    faces += mkit.make_cylinder(bm, 0.025, 3.0, segs=6, center=(0, -0.5, 0.18), color_idx=7)
    
    # 2x Traditional British Draught Beer Pump Sets (3 pumps each)
    for px_group in (-0.7, 0.7):
        # Chrome drip tray
        faces += mkit.make_cuboid(bm, 0.7, 0.25, 0.03, center=(px_group, -0.15, 1.14), color_idx=2)
        for pi in (-0.2, 0.0, 0.2):
            # Pump pillar
            faces += mkit.make_cylinder(bm, 0.03, 0.28, segs=6, center=(px_group + pi, -0.15, 1.28), color_idx=2)
            # Pump handle
            faces += mkit.make_cylinder(bm, 0.02, 0.2, segs=6, center=(px_group + pi, -0.15, 1.48), color_idx=7)
            # Beer badge / roundel
            faces += mkit.make_cuboid(bm, 0.08, 0.02, 0.08, center=(px_group + pi, -0.18, 1.35), color_idx=5)

    mkit.apply_bmesh_and_export("interior_pub_bar", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_pub_backshelf():
    """Mirrored back-bar bottle shelving unit with optic dispensers."""
    bm = bmesh.new()
    faces = []
    # Wooden Back Cabinet: 2.6m wide, 0.45m deep, 2.4m high
    faces += mkit.make_cuboid(bm, 2.6, 0.45, 0.9, center=(0, 0, 0.45), color_idx=0)
    faces += mkit.make_cuboid(bm, 2.6, 0.35, 1.5, center=(0, 0.05, 1.65), color_idx=0)
    
    # Mirror back panels
    faces += mkit.make_cuboid(bm, 2.4, 0.02, 1.3, center=(0, 0.18, 1.65), color_idx=6)
    
    # 3x Glass shelves with bottles
    for sz in (1.2, 1.6, 2.0):
        faces += mkit.make_cuboid(bm, 2.4, 0.25, 0.03, center=(0, 0.05, sz), color_idx=2)
        # Array of spirit bottles
        for bx in (-1.0, -0.6, -0.2, 0.2, 0.6, 1.0):
            faces += mkit.make_cylinder(bm, 0.04, 0.25, segs=6, center=(bx, 0.05, sz + 0.14), color_idx=5)
            
    # Optic Spirit Dispensers along lower shelf
    for ox in (-0.8, -0.4, 0.0, 0.4, 0.8):
        faces += mkit.make_cuboid(bm, 0.08, 0.12, 0.2, center=(ox, -0.05, 1.15), color_idx=2)

    mkit.apply_bmesh_and_export("interior_pub_backshelf", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_pub_table():
    """Round British pub table with 3 bar stools and pint glasses."""
    bm = bmesh.new()
    faces = []
    # Cast iron pedestal & round wooden tabletop: 1.0m diameter, 0.78m high
    faces += mkit.make_cylinder(bm, 0.28, 0.04, segs=8, center=(0, 0, 0.02), color_idx=3)
    faces += mkit.make_cylinder(bm, 0.04, 0.72, segs=6, center=(0, 0, 0.38), color_idx=3)
    faces += mkit.make_cylinder(bm, 0.5, 0.05, segs=10, center=(0, 0, 0.76), color_idx=0)
    
    # 2x Pint Glasses on Table
    faces += mkit.make_cylinder(bm, 0.045, 0.14, segs=6, center=(-0.15, 0.1, 0.85), color_idx=7)
    faces += mkit.make_cylinder(bm, 0.045, 0.14, segs=6, center=(0.12, -0.08, 0.85), color_idx=7)
    
    # 3x Traditional British Pub Stools around table
    for ang in (0.5, 2.6, 4.7):
        import math
        sx = 0.75 * math.cos(ang)
        sy = 0.75 * math.sin(ang)
        # 4 Stool legs
        for leg_ang in (0.7, 2.3, 3.8, 5.4):
            lx = sx + 0.15 * math.cos(leg_ang)
            ly = sy + 0.15 * math.sin(leg_ang)
            faces += mkit.make_cylinder(bm, 0.02, 0.48, segs=4, center=(lx, ly, 0.24), color_idx=0)
        # Red velvet padded round seat
        faces += mkit.make_cylinder(bm, 0.18, 0.08, segs=8, center=(sx, sy, 0.5), color_idx=5)

    mkit.apply_bmesh_and_export("interior_pub_table", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_pub_fruitmachine():
    """Classic British Pub Fruit Machine / Slot Machine ('Puggy')."""
    bm = bmesh.new()
    faces = []
    # Cabinet Body: 0.8m wide, 0.7m deep, 1.85m high
    faces += mkit.make_cuboid(bm, 0.8, 0.7, 1.8, center=(0, 0, 0.9), color_idx=3)
    
    # Top Illuminated Jackpot Display
    faces += mkit.make_cuboid(bm, 0.74, 0.05, 0.5, center=(0, -0.36, 1.5), color_idx=7)
    
    # Slanted Reel Glass Window & 3 Reels
    faces += mkit.make_cuboid(bm, 0.7, 0.1, 0.45, center=(0, -0.32, 1.05), color_idx=6)
    for rx in (-0.18, 0.0, 0.18):
        faces += mkit.make_cylinder(bm, 0.06, 0.14, segs=6, center=(rx, -0.3, 1.05), color_idx=4)
        
    # Button Shelf / Console
    faces += mkit.make_cuboid(bm, 0.76, 0.25, 0.08, center=(0, -0.42, 0.8), color_idx=5)
    # Buttons (Hold, Nudge, Spin)
    for bx, col in ((-0.25, 7), (-0.1, 7), (0.05, 7), (0.25, 5)):
        faces += mkit.make_cylinder(bm, 0.03, 0.04, segs=6, center=(bx, -0.42, 0.86), color_idx=col)
        
    # Bottom Coin Payout Tray
    faces += mkit.make_cuboid(bm, 0.4, 0.15, 0.15, center=(0, -0.36, 0.25), color_idx=2)

    mkit.apply_bmesh_and_export("interior_pub_fruitmachine", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


# ==============================================================================
# RESIDENTIAL / FLAT PROPS
# ==============================================================================

def build_interior_flat_sofa_tv():
    """Living room set: 2-seater sofa, coffee table & CRT TV on stand."""
    bm = bmesh.new()
    faces = []
    # 2-Seater Fabric Sofa (Width: 1.8m, Depth: 0.9m, Height: 0.85m) at X: 0, Y: 0.8
    # Base cushion
    faces += mkit.make_cuboid(bm, 1.8, 0.9, 0.4, center=(0, 0.8, 0.2), color_idx=5)
    # Backrest
    faces += mkit.make_cuboid(bm, 1.8, 0.25, 0.55, center=(0, 1.15, 0.65), color_idx=5)
    # Left & Right Armrests
    faces += mkit.make_cuboid(bm, 0.25, 0.9, 0.35, center=(-0.8, 0.8, 0.5), color_idx=5)
    faces += mkit.make_cuboid(bm, 0.25, 0.9, 0.35, center=(0.8, 0.8, 0.5), color_idx=5)
    
    # Coffee Table in front (at Y: 0.0)
    faces += mkit.make_cuboid(bm, 1.1, 0.6, 0.04, center=(0, 0.0, 0.4), color_idx=1)
    for leg_x in (-0.45, 0.45):
        for leg_y in (-0.22, 0.22):
            faces += mkit.make_cylinder(bm, 0.025, 0.38, segs=4, center=(leg_x, leg_y, 0.19), color_idx=0)
    # Ceramic mug on table
    faces += mkit.make_cylinder(bm, 0.04, 0.09, segs=6, center=(-0.2, 0.0, 0.46), color_idx=4)
    
    # TV Wooden Stand & CRT TV (at Y: -1.0)
    faces += mkit.make_cuboid(bm, 1.0, 0.5, 0.45, center=(0, -1.0, 0.225), color_idx=0)
    faces += mkit.make_cuboid(bm, 0.65, 0.45, 0.45, center=(0, -1.0, 0.675), color_idx=3)
    # TV Screen facing sofa
    faces += mkit.make_cuboid(bm, 0.52, 0.02, 0.36, center=(0, -0.78, 0.675), color_idx=6)

    mkit.apply_bmesh_and_export("interior_flat_sofa_tv", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_flat_kitchen():
    """Fitted kitchenette counter with sink, taps, stovetop and overhead cupboards."""
    bm = bmesh.new()
    faces = []
    # Base Counter: 2.4m wide, 0.65m deep, 0.9m high
    faces += mkit.make_cuboid(bm, 2.4, 0.65, 0.86, center=(0, 0, 0.43), color_idx=4)
    faces += mkit.make_cuboid(bm, 2.45, 0.68, 0.04, center=(0, 0, 0.88), color_idx=0)
    
    # Stainless Steel Sink & Faucet (Left side)
    faces += mkit.make_cuboid(bm, 0.55, 0.45, 0.02, center=(-0.65, 0, 0.91), color_idx=2)
    faces += mkit.make_cylinder(bm, 0.02, 0.25, segs=6, center=(-0.65, 0.15, 1.02), color_idx=2)
    
    # Stovetop 4-Ring Hob (Right side)
    faces += mkit.make_cuboid(bm, 0.6, 0.5, 0.03, center=(0.65, 0, 0.91), color_idx=3)
    for hx in (0.5, 0.8):
        for hy in (-0.12, 0.12):
            faces += mkit.make_cylinder(bm, 0.08, 0.02, segs=6, center=(hx, hy, 0.93), color_idx=3)
            
    # Overhead Wall Cupboards (Z: 1.6 to 2.2)
    faces += mkit.make_cuboid(bm, 2.4, 0.35, 0.65, center=(0, 0.15, 1.9), color_idx=4)
    # Cupboard handles
    for cx in (-0.9, -0.3, 0.3, 0.9):
        faces += mkit.make_cuboid(bm, 0.02, 0.03, 0.1, center=(cx, -0.04, 1.7), color_idx=2)

    mkit.apply_bmesh_and_export("interior_flat_kitchen", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


def build_interior_flat_bed_wardrobe():
    """Bedroom furniture set: double bed with duvet, side table with lamp, wardrobe."""
    bm = bmesh.new()
    faces = []
    # Double Bed: 1.6m wide, 2.1m long, 0.55m high (at X: -0.4, Y: 0)
    # Wooden bedframe & headboard
    faces += mkit.make_cuboid(bm, 1.6, 2.1, 0.25, center=(-0.4, 0, 0.125), color_idx=0)
    faces += mkit.make_cuboid(bm, 1.6, 0.1, 0.9, center=(-0.4, 1.0, 0.45), color_idx=0)
    # Mattress
    faces += mkit.make_cuboid(bm, 1.5, 1.95, 0.25, center=(-0.4, -0.05, 0.35), color_idx=4)
    # Duvet blanket
    faces += mkit.make_cuboid(bm, 1.52, 1.4, 0.15, center=(-0.4, -0.3, 0.42), color_idx=6)
    # 2x Pillows
    faces += mkit.make_cuboid(bm, 0.6, 0.4, 0.12, center=(-0.8, 0.7, 0.52), color_idx=4)
    faces += mkit.make_cuboid(bm, 0.6, 0.4, 0.12, center=(0.0, 0.7, 0.52), color_idx=4)
    
    # Bedside Table & Lamp (at X: -1.5, Y: 0.8)
    faces += mkit.make_cuboid(bm, 0.45, 0.45, 0.55, center=(-1.5, 0.8, 0.275), color_idx=0)
    faces += mkit.make_cylinder(bm, 0.02, 0.25, segs=6, center=(-1.5, 0.8, 0.675), color_idx=7)
    faces += mkit.make_cylinder(bm, 0.14, 0.18, segs=8, center=(-1.5, 0.8, 0.85), color_idx=4)
    
    # Wardrobe (at X: 1.2, Y: 0.0)
    faces += mkit.make_cuboid(bm, 1.0, 0.6, 2.0, center=(1.2, 0.0, 1.0), color_idx=0)
    faces += mkit.make_cuboid(bm, 0.02, 0.04, 0.15, center=(1.15, -0.32, 1.0), color_idx=7)

    mkit.apply_bmesh_and_export("interior_flat_bed_wardrobe", bm, faces, PAL_INTERIOR_GENERAL, "interiors")


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("--- BUILDING ALL 15 INTERIOR PROPS MODELS (<1500 TRIS) ---")
    build_interior_quidland_checkout()
    build_interior_quidland_aisle_shelf()
    build_interior_fusports_rack()
    build_interior_weapon_pegboard()
    build_interior_police_desk()
    build_interior_police_cell()
    build_interior_cityhall_dais()
    build_interior_office_filing()
    build_interior_pub_bar()
    build_interior_pub_backshelf()
    build_interior_pub_table()
    build_interior_pub_fruitmachine()
    build_interior_flat_sofa_tv()
    build_interior_flat_kitchen()
    build_interior_flat_bed_wardrobe()
    print("--- ALL 15 INTERIOR ASSETS COMPLETE ---")


if __name__ == "__main__":
    main()
