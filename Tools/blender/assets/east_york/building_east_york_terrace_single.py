"""East York Modular Single Chinese Townhouse (5.0m Repeatable Unit).

Architectural Specs:
- 5.0m wide single-unit Chinese-British terraced house
- Designed for flexible street planning, gap filling, and alternating modular streetscapes in East York
- Ground floor: Weathered York stone plinth with carved meander fretwork, offset vermilion entrance door
- Entrance: Vermilion door with brass knocker, lucky red couplet banners, hanging red silk lantern
- Windows: Authentic Chinese lattice sash window on ground floor, 2 upper floor lattice windows with jade canopies
- Roof: Pagoda-style swept flying eaves with glazed jade ceramic tiles and gold dragon roof finial
- Dougong timber bracket sets supporting the eaves
- Flush side party walls for seamless modular snapping on a 5.0m grid.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_terrace_single.py
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
OUT_DIR = kit.OUT_DIR / "east_york"

# --- Atlas Region Definitions (x, y, w, h) ---
R_YORK_STONE       = (0,   256, 256, 256)   # York stone masonry & meander frieze
R_RED_BRICK        = (256, 256, 128, 256)   # Weathered red brick upper facade
R_JADE_ROOF        = (0,   128, 256, 128)   # Glazed dark jade ceramic roof tiles
R_CHARCOAL_ROOF    = (256, 128, 128, 128)   # Charcoal ceramic ridge tiles
R_LATTICE_WIN_LG   = (384, 384, 128, 128)   # Ground floor large lattice window
R_LATTICE_WIN_SM   = (384, 256, 128, 128)   # Upper floor lattice window
R_DOOR_VERMILION   = (384, 128, 64,  128)   # Vermilion door with brass lion knocker
R_LANTERN_RED      = (448, 128, 64,  128)   # Hanging red silk lantern
R_TIMBER_RED       = (0,   64,  256, 64)    # Vermilion wood beams & dougong brackets
R_GOLD_TRIM        = (256, 64,  128, 64)    # Gold leaf trims & finials
R_STONE_TRIM       = (384, 64,  64,  64)    # Sills & steps
R_PAVEMENT         = (0,   0,   256, 64)    # York flagstones
R_CORNICE_CHINESE  = (256, 0,   192, 64)    # Chinese carved cornice

# --- Palette Colors ---
YORK_STONE_BASE   = (0.76, 0.72, 0.62)
YORK_STONE_MORTAR = (0.64, 0.60, 0.52)
RED_BRICK_BASE    = (0.52, 0.22, 0.16)
RED_BRICK_MORTAR  = (0.68, 0.65, 0.58)
JADE_ROOF_BASE    = (0.16, 0.32, 0.26)
JADE_ROOF_DARK    = (0.09, 0.20, 0.16)
JADE_ROOF_HILITE  = (0.24, 0.44, 0.36)
CHARCOAL_ROOF     = (0.18, 0.19, 0.22)
CHARCOAL_DARK     = (0.11, 0.12, 0.14)
VERMILION_RED     = (0.72, 0.14, 0.10)
VERMILION_DARK    = (0.45, 0.08, 0.06)
VERMILION_LIGHT   = (0.85, 0.22, 0.15)
IMPERIAL_GOLD     = (0.88, 0.72, 0.20)
GOLD_DARK         = (0.62, 0.48, 0.12)
STONE_CREAM       = (0.82, 0.78, 0.70)
STONE_DARK        = (0.56, 0.52, 0.46)
GLASS_DARK        = (0.08, 0.11, 0.14)
GLASS_HIGHLIGHT   = (0.18, 0.24, 0.30)
LANTERN_RED       = (0.85, 0.12, 0.08)
LANTERN_GLOW      = (0.98, 0.32, 0.15)


def paint_east_york_terrace_single_atlas():
    a = Atlas(S, seed=777)

    x, y, w, h = R_YORK_STONE
    a.rect(x, y, w, h, YORK_STONE_BASE)
    for my in range(y, y + h, 24):
        a.rect(x, my, w, 2, YORK_STONE_MORTAR)
        offset = 32 if ((my - y) // 24) % 2 else 0
        for mx in range(x - offset, x + w, 64):
            a.rect(max(x, mx), my, 2, 24, YORK_STONE_MORTAR)
    band_y = y + h - 28
    a.rect(x, band_y, w, 24, STONE_DARK)
    a.rect(x, band_y + 2, w, 20, YORK_STONE_BASE)
    for kx in range(x, x + w, 20):
        a.rect(kx + 2, band_y + 4, 16, 2, VERMILION_RED)
        a.rect(kx + 16, band_y + 4, 2, 12, VERMILION_RED)
        a.rect(kx + 6, band_y + 14, 12, 2, VERMILION_RED)
        a.rect(kx + 6, band_y + 8, 2, 8, VERMILION_RED)
        a.rect(kx + 6, band_y + 8, 6, 2, VERMILION_RED)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=0.0, bottom=-0.10)

    x, y, w, h = R_RED_BRICK
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_BRICK_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.04, bottom=0.0)

    x, y, w, h = R_JADE_ROOF
    a.rect(x, y, w, h, JADE_ROOF_BASE)
    tile_h, tile_w = 14, 16
    for ty in range(y, y + h, tile_h):
        a.rect(x, ty, w, 3, JADE_ROOF_DARK)
        a.rect(x, min(y + h - 1, ty + 3), w, 2, JADE_ROOF_HILITE)
        for tx in range(x, x + w, tile_w):
            a.rect(tx, ty, 3, tile_h, JADE_ROOF_DARK)
            a.rect(tx + 3, ty + 3, tile_w - 5, tile_h - 5, JADE_ROOF_BASE)
            a.rect(tx + 5, ty + 5, tile_w - 9, tile_h - 7, JADE_ROOF_HILITE)
    a.noise(x, y, w, h, 0.025)

    x, y, w, h = R_CHARCOAL_ROOF
    a.rect(x, y, w, h, CHARCOAL_ROOF)
    for ty in range(y, y + h, 12):
        a.rect(x, ty, w, 2, CHARCOAL_DARK)
        a.rect(x, ty + 2, w, 2, (0.28, 0.30, 0.34))
    a.noise(x, y, w, h, 0.03)

    x, y, w, h = R_LATTICE_WIN_LG
    a.rect(x, y, w, h, YORK_STONE_BASE)
    a.rect(x + 6, y + h - 16, w - 12, 14, STONE_CREAM)
    a.rect(x + 6, y + 2, w - 12, 10, STONE_CREAM)
    wx, wy, ww, wh = x + 12, y + 14, w - 24, h - 32
    a.rect(wx, wy, ww, wh, VERMILION_RED)
    gx, gy, gw, gh = wx + 5, wy + 5, ww - 10, wh - 10
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for ly in range(gy + 8, gy + gh - 4, 14):
        a.rect(gx, ly, gw, 2, VERMILION_RED)
        a.rect(gx, ly + 1, gw, 1, IMPERIAL_GOLD)
    for lx in range(gx + 8, gx + gw - 4, 14):
        a.rect(lx, gy, 2, gh, VERMILION_RED)
        a.rect(lx + 1, gy, 1, gh, IMPERIAL_GOLD)
    a.rect(gx + 4, gy + gh // 2 + 4, (gw // 2) - 8, (gh // 2) - 10, GLASS_HIGHLIGHT)

    x, y, w, h = R_LATTICE_WIN_SM
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.rect(x + 10, y + h - 16, w - 20, 14, STONE_CREAM)
    a.rect(x + 10, y + 4, w - 20, 10, STONE_CREAM)
    wx, wy, ww, wh = x + 16, y + 16, w - 32, h - 34
    a.rect(wx, wy, ww, wh, VERMILION_RED)
    gx, gy, gw, gh = wx + 4, wy + 4, ww - 8, wh - 8
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for ly in range(gy + 6, gy + gh - 2, 12):
        a.rect(gx, ly, gw, 2, VERMILION_RED)
    for lx in range(gx + 6, gx + gw - 2, 12):
        a.rect(lx, gy, 2, gh, VERMILION_RED)
    a.rect(gx + 3, gy + gh // 2 + 4, (gw // 2) - 6, (gh // 2) - 8, GLASS_HIGHLIGHT)

    x, y, w, h = R_DOOR_VERMILION
    a.rect(x, y, w, h, STONE_CREAM)
    dx, dy, dw, dh = x + 4, y, w - 8, h - 4
    a.rect(dx, dy, dw, dh, VERMILION_DARK)
    a.rect(dx + 3, dy + 2, dw - 6, dh - 4, VERMILION_RED)
    a.rect(dx + 4, dy + 6, 6, dh - 16, VERMILION_DARK)
    a.rect(dx + dw - 10, dy + 6, 6, dh - 16, VERMILION_DARK)
    for cy in range(dy + 12, dy + dh - 20, 14):
        a.rect(dx + 5, cy, 4, 6, IMPERIAL_GOLD)
        a.rect(dx + dw - 9, cy, 4, 6, IMPERIAL_GOLD)
    pw = (dw - 24) // 2
    ph = (dh - 24) // 3
    for py_idx in range(3):
        py = dy + 6 + py_idx * (ph + 4)
        a.rect(dx + 12, py, pw, ph, VERMILION_DARK)
        a.rect(dx + 13, py + 1, pw - 2, ph - 2, VERMILION_RED)
        a.rect(dx + 12 + pw + 2, py, pw, ph, VERMILION_DARK)
        a.rect(dx + 13 + pw + 2, py + 1, pw - 2, ph - 2, VERMILION_RED)
    knocker_y = dy + dh // 2 - 2
    a.rect(dx + dw // 2 - 5, knocker_y, 10, 10, IMPERIAL_GOLD)

    x, y, w, h = R_LANTERN_RED
    a.rect(x, y, w, h, (0.05, 0.05, 0.05))
    a.rect(x + 12, y + h - 14, w - 24, 10, IMPERIAL_GOLD)
    a.rect(x + 12, y + 36, w - 24, 8, IMPERIAL_GOLD)
    body_y, body_h = y + 44, h - 60
    a.rect(x + 6, body_y, w - 12, body_h, LANTERN_RED)
    a.rect(x + 10, body_y + 4, w - 20, body_h - 8, LANTERN_GLOW)
    for rib_x in range(x + 10, x + w - 10, 8):
        a.rect(rib_x, body_y, 2, body_h, (0.35, 0.05, 0.04))
    a.rect(x + w // 2 - 4, y + 6, 8, 30, IMPERIAL_GOLD)

    x, y, w, h = R_TIMBER_RED
    a.rect(x, y, w, h, VERMILION_RED)
    for ty in range(y, y + h, 16):
        a.rect(x, ty, w, 2, VERMILION_DARK)
    a.noise(x, y, w, h, 0.02)

    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    for gy in range(y, y + h, 12):
        a.rect(x, gy, w, 2, GOLD_DARK)

    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 14):
        a.rect(x, sy, w, 2, STONE_DARK)

    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.50, 0.48, 0.44))
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.38, 0.36, 0.33))
    a.noise(x, y, w, h, 0.03)

    x, y, w, h = R_CORNICE_CHINESE
    a.rect(x, y, w, h, VERMILION_RED)
    a.rect(x, y + h - 8, w, 8, IMPERIAL_GOLD)
    a.rect(x, y, w, 6, IMPERIAL_GOLD)
    for cx in range(x, x + w, 16):
        a.rect(cx + 2, y + 8, 12, h - 16, VERMILION_DARK)
        a.rect(cx + 4, y + 10, 8, h - 20, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_east_york_terrace_single_atlas", OUT_DIR)


def make_cylinder(name, r=0.15, h=0.6, segs=8, at=(0, 0, 0)):
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


def make_swept_roof(name, w, d, eaves_h, ridge_h, flare=0.50, at=(0, 0, 0)):
    hw, hd = w / 2.0, d / 2.0
    cx, cy, cz = at
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    x_steps = [-hw, -hw * 0.5, 0.0, hw * 0.5, hw]
    
    front_eaves = []
    for x in x_steps:
        x_factor = (abs(x) / hw) ** 2.0
        z = cz + eaves_h + flare * x_factor
        front_eaves.append(bm.verts.new((cx + x, cy - hd, z)))

    ridge_verts = []
    for x in x_steps:
        x_factor = (abs(x) / hw) ** 2.0
        z = cz + ridge_h + (flare * 0.35) * x_factor
        ridge_verts.append(bm.verts.new((cx + x, cy, z)))

    back_eaves = []
    for x in x_steps:
        x_factor = (abs(x) / hw) ** 2.0
        z = cz + eaves_h + flare * x_factor
        back_eaves.append(bm.verts.new((cx + x, cy + hd, z)))

    for i in range(len(x_steps) - 1):
        bm.faces.new([front_eaves[i], front_eaves[i + 1], ridge_verts[i + 1], ridge_verts[i]])

    for i in range(len(x_steps) - 1):
        bm.faces.new([ridge_verts[i], ridge_verts[i + 1], back_eaves[i + 1], back_eaves[i]])

    v_left_bot = bm.verts.new((cx - hw, cy, cz + eaves_h))
    bm.faces.new([front_eaves[0], ridge_verts[0], v_left_bot])
    bm.faces.new([ridge_verts[0], back_eaves[0], v_left_bot])

    v_right_bot = bm.verts.new((cx + hw, cy, cz + eaves_h))
    bm.faces.new([ridge_verts[-1], front_eaves[-1], v_right_bot])
    bm.faces.new([back_eaves[-1], ridge_verts[-1], v_right_bot])

    bm.faces.new([front_eaves[0], v_left_bot, v_right_bot, front_eaves[-1]])
    bm.faces.new([v_left_bot, back_eaves[0], back_eaves[-1], v_right_bot])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    img = paint_east_york_terrace_single_atlas()
    mat = material_for(img, "EastYorkTerraceSingle_Mat")

    parts = []

    def register_box(name, w, d, h, at, front=None, sides=None, top=None, back=None):
        obj = kit.make_box(name, w, d, h, at=at)
        obj.data.materials.append(mat)
        if front is not None:
            kit.map_faces_to_region(obj, front, S, only=lambda f: f.normal.y < -0.5)
        if sides is not None:
            kit.map_faces_to_region(obj, sides, S, only=lambda f: abs(f.normal.x) > 0.5)
        if top is not None:
            kit.map_faces_to_region(obj, top, S, only=lambda f: abs(f.normal.z) > 0.5)
        if back is not None:
            kit.map_faces_to_region(obj, back, S, only=lambda f: f.normal.y > 0.5)
        parts.append(obj)
        return obj

    # 1. Pavement
    register_box("FrontPavement", 5.0, 1.20, 0.10, (0.0, -4.10, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Ground Floor York Stone Facade
    register_box("GroundFloorStone", 5.0, 7.0, 3.10, (0.0, 0.0, 0.10),
                 front=R_YORK_STONE, sides=R_YORK_STONE, back=R_YORK_STONE, top=R_STONE_TRIM)

    # 3. Entrance on Left (X = -1.40m)
    register_box("DoorStep1", 1.30, 0.65, 0.15, (-1.40, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep2", 1.20, 0.35, 0.15, (-1.40, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("FrontDoor", 1.05, 0.20, 2.25, (-1.40, -3.52, 0.40),
                 front=R_DOOR_VERMILION, sides=R_TIMBER_RED, top=R_TIMBER_RED)

    register_box("Portico_L", 0.14, 0.24, 2.40, (-2.00, -3.54, 0.40),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    register_box("Portico_R", 0.14, 0.24, 2.40, (-0.80, -3.54, 0.40),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    register_box("Portico_Lintel", 1.45, 0.32, 0.22, (-1.40, -3.56, 2.80),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    register_box("LanternBracket", 0.06, 0.35, 0.06, (-2.15, -3.65, 2.65),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    lantern = make_cylinder("Lantern", r=0.16, h=0.45, segs=8, at=(-2.15, -3.80, 2.05))
    lantern.data.materials.append(mat)
    kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
    parts.append(lantern)

    # 4. Ground Floor Chinese Lattice Window on Right (X = +1.15m)
    register_box("GroundWin", 1.60, 0.20, 1.85, (1.15, -3.52, 0.85),
                 front=R_LATTICE_WIN_LG, sides=R_TIMBER_RED, top=R_TIMBER_RED)
    register_box("GroundWin_Canopy", 1.80, 0.35, 0.16, (1.15, -3.60, 2.70),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_JADE_ROOF)

    # 5. Mid-Level String Course
    register_box("MidCornice", 5.0, 7.15, 0.22, (0, -0.05, 3.20),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_JADE_ROOF)

    # 6. First Floor Red Brick Facade
    register_box("FirstFloor", 5.0, 7.0, 2.70, (0.0, 0, 3.42),
                 front=R_RED_BRICK, sides=R_RED_BRICK, back=R_RED_BRICK)

    for px in [-2.45, 2.45]:
        register_box(f"Pilaster_{px}", 0.14, 0.18, 2.70, (px, -3.52, 3.42),
                     front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    # 7. First Floor Windows (2 bays)
    for i, wx in enumerate([-1.40, 1.15]):
        register_box(f"UpperWin_{i+1}", 1.25, 0.18, 1.65, (wx, -3.52, 4.00),
                     front=R_LATTICE_WIN_SM, sides=R_TIMBER_RED, top=R_TIMBER_RED)
        register_box(f"UpperWinCanopy_{i+1}", 1.45, 0.28, 0.14, (wx, -3.58, 5.65),
                     front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_JADE_ROOF)

    # 8. Eaves Cornice & Dougong Brackets
    register_box("EavesCornice", 5.2, 7.25, 0.28, (0, -0.08, 6.12),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    for bx in np.linspace(-2.1, 2.1, 6):
        register_box(f"Dougong_{bx:.1f}", 0.20, 0.30, 0.22, (bx, -3.62, 5.90),
                     front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    # 9. Swept Flying-Eaves Jade Roof
    roof = make_swept_roof("SweptJadeRoof", 5.5, 7.6, eaves_h=0.0, ridge_h=1.80, flare=0.50, at=(0, 0, 6.40))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_JADE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.3 and f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_RED_BRICK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_TIMBER_RED, S, only=lambda f: f.normal.z < -0.3)
    parts.append(roof)

    register_box("RoofRidge", 5.5, 0.30, 0.18, (0, 0, 8.20),
                 front=R_CHARCOAL_ROOF, sides=R_CHARCOAL_ROOF, top=R_GOLD_TRIM)
    for fx in [-2.75, 2.75]:
        register_box(f"RidgeFinial_{fx}", 0.22, 0.32, 0.35, (fx, 0, 8.30),
                     front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # 10. Party Wall Chimney Stack
    register_box("ChimneyBase", 0.75, 1.20, 1.60, (2.10, 0.4, 7.10),
                 front=R_RED_BRICK, sides=R_RED_BRICK, top=R_STONE_TRIM)
    register_box("ChimneyCap", 0.88, 1.35, 0.16, (2.10, 0.4, 8.70),
                 front=R_CORNICE_CHINESE, sides=R_JADE_ROOF, top=R_GOLD_TRIM)
    for i, pot_y in enumerate([0.15, 0.65]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.13, h=0.45, segs=8, at=(2.10, pot_y, 8.86))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_GOLD_TRIM, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_Terrace_Single")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_terrace_single_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_terrace_single.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_east_york_terrace_single] generation complete in east_york/ folder.")


main()
