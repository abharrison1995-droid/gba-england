"""1970s London Council Estate Mid-Rise Block (Flats Variant 2).

Architectural Specs:
- 4-storey post-war London municipal estate block with exposed concrete floor slabs and deck-access balconies
- Facade: Weathered council brown brick with precast concrete lintels and horizontal access galleries
- Ground floor: Heavy steel security communal entrance door with electronic key fob/intercom, CCTV graphic, and louvred service/bin-store doors
- Upper floors: Cantilevered concrete access balconies with dark metal safety railings, flat entrance doors, and wide aluminium-framed estate windows
- Roof: Flat gravel roof with concrete parapet, rooftop lift motor room/tank housing, vent flues, and communal antenna mast
- Dimensions: 10.0m width x 7.5m depth x 11.2m total height (to lift core). Modular 10m grid.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_london_flats_02.py
"""

import math
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512

# --- Atlas Region Definitions (x, y, w, h) ---
R_BRICK_COUNCIL  = (0,   256, 256, 256)   # Weathered brown council brick
R_CONCRETE_SLAB  = (0,   128, 256, 128)   # Precast concrete floor slab & balconies
R_CONCRETE_DARK  = (0,   64,  256, 64)    # Weathered concrete & parapet coping
R_PAVEMENT       = (0,   0,   256, 64)    # Pavement flags
R_BRICK_SIDE     = (256, 256, 128, 256)   # Side party wall & stair core brick
R_DECK_CORRIDOR  = (256, 128, 128, 128)   # Deck access walkway with flat doors
R_LIFT_CORE      = (256, 64,  128, 64)    # Rooftop lift motor housing
R_ROOF_GRAVEL    = (256, 0,   128, 64)    # Flat roof bitumen/gravel
R_ESTATE_WINDOW  = (384, 384, 128, 128)   # 1970s wide aluminium estate window
R_DOOR_SECURITY  = (448, 128, 64,  128)   # Communal steel security door + intercom
R_DOOR_SERVICE   = (384, 128, 64,  128)   # Louvred bin-store / service door
R_RAILING_PANEL  = (448, 0,   64,  128)   # Metal balustrade / safety railing
R_VENT_PIPE      = (384, 0,   64,  128)   # Rooftop vent pipes & satellite graphics

# --- Palette Colors ---
COUNCIL_BRICK    = (0.42, 0.35, 0.28)
COUNCIL_MORTAR   = (0.58, 0.55, 0.50)
SIDE_BRICK       = (0.34, 0.28, 0.22)
CONCRETE_GREY    = (0.64, 0.63, 0.60)
CONCRETE_DARK    = (0.46, 0.45, 0.43)
CONCRETE_LIGHT   = (0.75, 0.74, 0.70)
STEEL_BLUE       = (0.16, 0.22, 0.28)
STEEL_DARK       = (0.10, 0.12, 0.14)
RAILING_BLACK    = (0.12, 0.12, 0.14)
GLASS_DARK       = (0.08, 0.11, 0.15)
GLASS_HIGHLIGHT  = (0.18, 0.24, 0.32)
ALU_FRAME        = (0.72, 0.74, 0.76)
BRASS_GOLD       = (0.86, 0.73, 0.24)
RED_ACCENT       = (0.68, 0.14, 0.12)
ROOF_GRAVEL_COL  = (0.36, 0.35, 0.34)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_council_atlas():
    a = Atlas(S, seed=305)

    # 1. Council Brown Brick Facade (R_BRICK_COUNCIL)
    x, y, w, h = R_BRICK_COUNCIL
    a.bricks(x, y, w, h, brick=COUNCIL_BRICK, mortar=COUNCIL_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.06, bottom=0.0)

    # 2. Side Brick (R_BRICK_SIDE)
    x, y, w, h = R_BRICK_SIDE
    a.bricks(x, y, w, h, brick=SIDE_BRICK, mortar=(0.50, 0.47, 0.43), bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.02)

    # 3. Concrete Slabs & Balconies (R_CONCRETE_SLAB)
    x, y, w, h = R_CONCRETE_SLAB
    a.rect(x, y, w, h, CONCRETE_GREY)
    # Formwork lines & weathering stains
    for ly in range(y, y + h, 24):
        a.rect(x, ly, w, 2, CONCRETE_DARK)
        a.rect(x, ly + 2, w, 1, CONCRETE_LIGHT)
    a.noise(x, y, w, h, 0.035)

    # 4. Deck Access Corridor Texture (R_DECK_CORRIDOR)
    x, y, w, h = R_DECK_CORRIDOR
    a.rect(x, y, w, h, (0.35, 0.32, 0.28))
    # 2 Flat Entrance Doors along the balcony walkway
    for door_x in [x + 16, x + 72]:
        a.rect(door_x, y + 8, 32, h - 16, STEEL_BLUE)
        a.rect(door_x + 2, y + 10, 28, h - 20, (0.24, 0.32, 0.40))
        # Vision glass slot
        a.rect(door_x + 10, y + h // 2 + 10, 12, 28, GLASS_DARK)
        # Stainless steel handle & door number plate
        a.rect(door_x + 24, y + h // 2 - 4, 3, 10, ALU_FRAME)
        a.rect(door_x + 10, y + h - 22, 12, 6, ALU_FRAME)
    a.noise(x, y, w, h, 0.02)

    # 5. Estate Window (R_ESTATE_WINDOW)
    x, y, w, h = R_ESTATE_WINDOW
    a.rect(x, y, w, h, COUNCIL_BRICK)
    a.noise(x, y, w, h, 0.03)
    # Precast concrete sill & lintel
    a.rect(x + 6, y + h - 14, w - 12, 12, CONCRETE_GREY)
    a.rect(x + 6, y + h - 14, w - 12, 2, CONCRETE_DARK)
    a.rect(x + 4, y + 4, w - 8, 10, CONCRETE_GREY)
    a.rect(x + 4, y + 4, w - 8, 2, CONCRETE_DARK)
    # Wide aluminium 3-pane window
    wx, wy, ww, wh = x + 10, y + 14, w - 20, h - 28
    a.rect(wx, wy, ww, wh, ALU_FRAME)
    gx, gy, gw, gh = wx + 4, wy + 4, ww - 8, wh - 8
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    # 2 vertical mullions (creating 3 panes)
    pw = gw // 3
    a.rect(gx + pw - 2, gy, 4, gh, ALU_FRAME)
    a.rect(gx + 2 * pw - 2, gy, 4, gh, ALU_FRAME)
    # Top horizontal hopper vent bar
    a.rect(gx, gy + gh - 18, gw, 3, ALU_FRAME)
    # Glass highlights & curtain shades
    a.rect(gx + 4, gy + 8, pw - 8, gh - 28, GLASS_HIGHLIGHT)
    a.rect(gx + 2 * pw + 4, gy + 8, pw - 8, gh - 28, GLASS_HIGHLIGHT)

    # 6. Communal Security Door (R_DOOR_SECURITY)
    x, y, w, h = R_DOOR_SECURITY
    a.rect(x, y, w, h, CONCRETE_GREY)
    dx, dy, dw, dh = x + 4, y, w - 8, h - 8
    a.rect(dx, dy, dw, dh, STEEL_DARK)
    # Heavy Blue Steel Security Door
    a.rect(dx + 2, dy + 2, dw - 4, dh - 4, STEEL_BLUE)
    # Reinforced wire-mesh glass panel
    a.rect(dx + 12, dy + dh // 2 - 10, dw - 24, dh // 2 - 8, GLASS_DARK)
    a.rect(dx + 14, dy + dh // 2 - 8, dw - 28, dh // 2 - 12, (0.16, 0.20, 0.26))
    # Push plate & magnetic lock housing
    a.rect(dx + dw - 10, dy + dh // 2 - 20, 4, 24, ALU_FRAME)
    a.rect(dx + 12, dy + dh - 16, dw - 24, 6, RED_ACCENT)
    # Digital Intercom & Keypad board on wall
    a.rect(x + 1, dy + dh // 2 - 12, 3, 24, (0.80, 0.80, 0.82))
    for ky in range(dy + dh // 2 - 8, dy + dh // 2 + 10, 4):
        a.rect(x + 1, ky, 2, 2, STEEL_DARK)
    a.noise(x, y, w, h, 0.02)

    # 7. Service / Bin Store Door (R_DOOR_SERVICE)
    x, y, w, h = R_DOOR_SERVICE
    a.rect(x, y, w, h, CONCRETE_GREY)
    sx, sy, sw, sh = x + 4, y, w - 8, h - 8
    a.rect(sx, sy, sw, sh, (0.28, 0.30, 0.32))
    # Metal ventilation louvres
    for ly in range(sy + 10, sy + sh - 10, 6):
        a.rect(sx + 6, ly, sw - 12, 3, STEEL_DARK)
        a.rect(sx + 6, ly + 2, sw - 12, 1, (0.45, 0.47, 0.50))
    a.noise(x, y, w, h, 0.02)

    # 8. Metal Safety Railing (R_RAILING_PANEL)
    x, y, w, h = R_RAILING_PANEL
    a.rect(x, y, w, h, (0.28, 0.28, 0.30))
    # Top handrail
    a.rect(x, y + h - 8, w, 8, RAILING_BLACK)
    # Bottom rail
    a.rect(x, y, w, 6, RAILING_BLACK)
    # Vertical baluster bars
    for rx in range(x + 4, x + w, 8):
        a.rect(rx, y, 2, h, RAILING_BLACK)
        a.rect(rx + 1, y, 1, h, (0.35, 0.35, 0.38))
    a.noise(x, y, w, h, 0.02)

    # 9. Concrete Trim / Coping (R_CONCRETE_DARK)
    x, y, w, h = R_CONCRETE_DARK
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.noise(x, y, w, h, 0.035)

    # 10. Flat Roof Bitumen/Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, ROOF_GRAVEL_COL)
    a.noise(x, y, w, h, 0.05)

    # 11. Lift Core Brick (R_LIFT_CORE)
    x, y, w, h = R_LIFT_CORE
    a.bricks(x, y, w, h, brick=COUNCIL_BRICK, mortar=COUNCIL_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)

    # 12. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 13. Roof Vent Flues & Satellite Dishes (R_VENT_PIPE)
    x, y, w, h = R_VENT_PIPE
    a.rect(x, y, w, h, (0.30, 0.30, 0.32))
    # Galvanized steel vent pipe
    a.rect(x + 12, y, 16, h, (0.65, 0.67, 0.70))
    a.rect(x + 12, y, 4, 16, (0.50, 0.52, 0.55))
    # Satellite dish graphic
    a.disc(x + 44, y + 40, 16, (0.78, 0.80, 0.82))
    a.disc(x + 44, y + 40, 14, (0.60, 0.62, 0.65))
    a.rect(x + 42, y + 20, 4, 20, STEEL_DARK)
    a.noise(x, y, w, h, 0.03)

    return a.to_image("building_london_flats_02_atlas", kit.OUT_DIR)


def side(name):
    checks = {
        "front": lambda f: f.normal.y < -0.5,
        "back": lambda f: f.normal.y > 0.5,
        "left": lambda f: f.normal.x < -0.5,
        "right": lambda f: f.normal.x > 0.5,
        "top": lambda f: f.normal.z > 0.5,
        "bottom": lambda f: f.normal.z < -0.5,
    }
    return checks[name]


def map_box(obj, front, sides, back=None, top=None, bottom=None):
    kit.map_faces_to_region(obj, front, S, only=side("front"))
    kit.map_faces_to_region(obj, sides, S, only=side("left"))
    kit.map_faces_to_region(obj, sides, S, only=side("right"))
    kit.map_faces_to_region(obj, back or sides, S, only=side("back"))
    kit.map_faces_to_region(obj, top or R_CONCRETE_DARK, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CONCRETE_DARK, S, only=side("bottom"))


def make_cylinder(name, r, h, segs=8, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    x, y, z = at
    bot_ring = []
    top_ring = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vx = x + r * math.cos(a)
        vy = y + r * math.sin(a)
        bot_ring.append(bm.verts.new((vx, vy, z)))
        top_ring.append(bm.verts.new((vx, vy, z + h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]))
    bm.faces.new(reversed(bot_ring))
    bm.faces.new(top_ring)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    img = paint_council_atlas()
    mat = material_for(img, "mat_london_flats_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # 4-Storey 1970s Council Estate Block (10.0m x 7.5m, Height: ~11.2m)
    # =========================================================================

    # 1. Pavement
    register_box("Pavement", 10.0, 8.5, 0.10, (0, -0.5, 0),
                 front=R_CONCRETE_DARK, sides=R_CONCRETE_DARK, top=R_PAVEMENT)

    # 2. Main Building Body (10.0m x 7.5m, Z: 0.10 to 9.80, H: 9.70m)
    register_box("MainBlock", 10.0, 7.5, 9.70, (0, 0, 0.10),
                 front=R_BRICK_COUNCIL, sides=R_BRICK_SIDE, back=R_BRICK_SIDE)

    # 3. Ground Floor Entrance & Service Zone (Z: 0.10 to 2.70m)
    # Main Communal Security Door (Center-Left: X = -1.20m)
    register_box("SecurityEntrance", 2.20, 0.25, 2.45, (-1.20, -3.75, 0.10),
                 front=R_DOOR_SECURITY, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    # Bin Store / Louvred Service Door (Right: X = +1.60m)
    register_box("ServiceDoor", 1.80, 0.25, 2.45, (1.60, -3.75, 0.10),
                 front=R_DOOR_SERVICE, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    # Ground Floor Left Window (X = -3.70m)
    register_box("GroundWinL", 1.80, 0.20, 1.60, (-3.70, -3.75, 0.65),
                 front=R_ESTATE_WINDOW, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    # Ground Floor Right Window (X = +3.70m)
    register_box("GroundWinR", 1.80, 0.20, 1.60, (3.70, -3.75, 0.65),
                 front=R_ESTATE_WINDOW, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)

    # 4. Cantilevered Concrete Deck Access Balconies & Railings (Floors 2, 3, 4)
    for floor_idx, fz in enumerate([2.65, 5.05, 7.45]):
        # Concrete floor slab projecting forward (Y = -4.00, protrusion = 0.50m)
        register_box(f"BalconySlab_{floor_idx}", 10.0, 0.60, 0.20, (0.0, -3.95, fz),
                     front=R_CONCRETE_SLAB, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
        # Access Corridor Wall with Flat Doors (recessed behind balcony)
        register_box(f"DeckWall_{floor_idx}", 5.50, 0.15, 1.90, (0.0, -3.75, fz + 0.20),
                     front=R_DECK_CORRIDOR, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
        # Metal Safety Railings along the balcony front
        register_box(f"Railing_{floor_idx}", 10.0, 0.08, 0.90, (0.0, -4.20, fz + 0.20),
                     front=R_RAILING_PANEL, sides=R_RAILING_PANEL, top=R_RAILING_PANEL)
        # Windows on left and right outer bays of upper floors
        register_box(f"UpperWinL_{floor_idx}", 1.80, 0.20, 1.60, (-3.70, -3.75, fz + 0.40),
                     front=R_ESTATE_WINDOW, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
        register_box(f"UpperWinR_{floor_idx}", 1.80, 0.20, 1.60, (3.70, -3.75, fz + 0.40),
                     front=R_ESTATE_WINDOW, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)

    # 5. Flat Roof Parapet & Coping (Z: 9.80 to 10.25m)
    register_box("RoofSlab", 10.0, 7.50, 0.20, (0.0, 0.0, 9.80),
                 front=R_CONCRETE_SLAB, sides=R_CONCRETE_DARK, top=R_ROOF_GRAVEL)
    register_box("ParapetFront", 10.0, 0.30, 0.45, (0.0, -3.60, 10.00),
                 front=R_CONCRETE_DARK, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    register_box("ParapetBack", 10.0, 0.30, 0.45, (0.0, 3.60, 10.00),
                 front=R_CONCRETE_DARK, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    register_box("ParapetLeft", 0.30, 7.50, 0.45, (-4.85, 0.0, 10.00),
                 front=R_CONCRETE_DARK, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)
    register_box("ParapetRight", 0.30, 7.50, 0.45, (4.85, 0.0, 10.00),
                 front=R_CONCRETE_DARK, sides=R_CONCRETE_DARK, top=R_CONCRETE_DARK)

    # 6. Rooftop Lift Motor Room / Plant Housing (Center-Right: X = 1.80m, Y = 0.5m, H = 1.60m)
    register_box("LiftCore", 2.60, 3.00, 1.60, (1.80, 0.5, 10.00),
                 front=R_LIFT_CORE, sides=R_LIFT_CORE, top=R_CONCRETE_DARK)

    # 7. Rooftop Vent Flues & Satellite Dishes
    vent1 = make_cylinder("VentPipe1", r=0.18, h=1.10, segs=8, at=(-2.20, 1.00, 10.00))
    vent1.data.materials.append(mat)
    kit.map_faces_to_region(vent1, R_VENT_PIPE, S)
    parts.append(vent1)

    vent2 = make_cylinder("VentPipe2", r=0.14, h=0.85, segs=8, at=(-2.80, 1.50, 10.00))
    vent2.data.materials.append(mat)
    kit.map_faces_to_region(vent2, R_VENT_PIPE, S)
    parts.append(vent2)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_London_Flats_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_london_flats_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_london_flats_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_london_flats_02] generation complete.")


main()
