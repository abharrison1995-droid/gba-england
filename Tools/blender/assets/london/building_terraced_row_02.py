"""Modular Terraced Housing Pair (Variant 2 — Symmetrical Stucco/Brick Townhouse Terrace).

Architectural Specs:
- 10.0m wide double-unit symmetrical London terrace pair
- Ground floor: Continuous painted rusticated stucco spanning both units
- Centre: Paired classical front doors (Maroon & Emerald Green) with shared wide stone entrance steps and fanlights
- Ground floor flanking large sash windows with stone architraves
- Upper floor: Warm red/brown London brick with 4 grand sash windows and triangular stone pediments
- Classical modillion eaves cornice and continuous slate roof
- Twin outer party-wall chimney stacks (left & right ends), each with 2 terracotta clay pots
- Designed for seamless tiling on a 10.0m grid or alongside 5.0m single houses.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_terraced_row_02.py
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
R_BRICK_RED     = (0,   256, 256, 256)   # Warm red/brown London brick facade
R_BRICK_DARK    = (256, 256, 128, 256)   # Side party wall & chimney brick
R_SLATE_ROOF    = (0,   128, 256, 128)   # Welsh slate roof
R_STUCCO        = (256, 128, 128, 128)   # Ground floor rusticated stucco
R_SASH_WINDOW   = (384, 384, 128, 128)   # Upper sash window with pediment
R_SASH_GROUND   = (384, 256, 128, 128)   # Ground floor sash with stone frame
R_DOOR_MAROON   = (384, 128, 64,  128)   # Left Maroon door
R_DOOR_GREEN    = (448, 128, 64,  128)   # Right Emerald Green door
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, steps
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Terracotta chimney pot
R_PAVEMENT      = (0,   0,   256, 64)    # Pavement flags
R_CORNICE       = (256, 0,   256, 64)    # Modillion cornice

# --- Color Palette ---
RED_BRICK_BASE   = (0.50, 0.22, 0.16)
RED_MORTAR       = (0.70, 0.67, 0.62)
DARK_BRICK_BASE  = (0.38, 0.22, 0.18)
STUCCO_BASE      = (0.78, 0.75, 0.68)
STUCCO_GROOVE    = (0.58, 0.54, 0.48)
SLATE_BASE       = (0.24, 0.27, 0.32)
SLATE_DARK       = (0.16, 0.18, 0.22)
SLATE_HIGHLIGHT  = (0.34, 0.38, 0.44)
STONE_CREAM      = (0.82, 0.79, 0.72)
STONE_DARK       = (0.58, 0.55, 0.48)
TIMBER_WHITE     = (0.94, 0.94, 0.92)
TIMBER_FRAME     = (0.84, 0.84, 0.82)
GLASS_DARK       = (0.09, 0.12, 0.16)
GLASS_HIGHLIGHT  = (0.20, 0.26, 0.34)
DOOR_MAROON      = (0.44, 0.08, 0.12)
DOOR_GREEN       = (0.06, 0.30, 0.14)
BRASS_GOLD       = (0.86, 0.73, 0.24)
TERRACOTTA       = (0.70, 0.34, 0.18)
SOOT_BLACK       = (0.14, 0.14, 0.14)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_terraced_02_atlas():
    a = Atlas(S, seed=150)

    # 1. Upper Red/Brown Brick (R_BRICK_RED)
    x, y, w, h = R_BRICK_RED
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.05, bottom=0.0)

    # 2. Side Party Wall Brick (R_BRICK_DARK)
    x, y, w, h = R_BRICK_DARK
    a.bricks(x, y, w, h, brick=DARK_BRICK_BASE, mortar=(0.58, 0.55, 0.50), bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.02)

    # 3. Slate Roof (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, SLATE_BASE)
    tile_h, tile_w = 12, 20
    row = 0
    for ty in range(y, y + h, tile_h):
        stagger = (tile_w // 2) if (row % 2 == 1) else 0
        a.rect(x, ty, w, 2, SLATE_DARK)
        a.rect(x, min(y + h - 1, ty + 2), w, 1, SLATE_HIGHLIGHT)
        for tx in range(x - stagger, x + w, tile_w):
            x0 = max(x, tx)
            x1 = min(x + w, tx + tile_w)
            if x1 > x0:
                a.rect(x0, ty, 1, tile_h, SLATE_DARK)
                j = a.rng.uniform(-0.035, 0.035)
                tint = tuple(max(0.0, min(1.0, c + j)) for c in SLATE_BASE)
                a.rect(x0 + 1, ty + 3, max(1, x1 - x0 - 2), max(1, tile_h - 4), tint)
        row += 1
    a.noise(x, y, w, h, 0.025)

    # 4. Ground Floor Stucco (R_STUCCO)
    x, y, w, h = R_STUCCO
    a.rect(x, y, w, h, STUCCO_BASE)
    for gy in range(y, y + h, 18):
        a.rect(x, gy, w, 2, STUCCO_GROOVE)
        a.rect(x, gy + 2, w, 1, (0.88, 0.85, 0.78))
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.03)

    # 5. Upper Sash Window with Pediment (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.noise(x, y, w, h, 0.03)
    a.rect(x + 10, y + h - 22, w - 20, 20, STONE_CREAM)
    a.rect(x + 10, y + h - 22, w - 20, 2, STONE_DARK)
    a.rect(x + 8, y + 4, w - 16, 12, STONE_CREAM)
    a.rect(x + 8, y + 4, w - 16, 2, STONE_DARK)
    wx, wy, ww, wh = x + 16, y + 16, w - 32, h - 38
    a.rect(wx, wy, ww, wh, TIMBER_FRAME)
    gx, gy, gw, gh = wx + 5, wy + 5, ww - 10, wh - 10
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    mid_y = gy + gh // 2
    a.rect(gx, mid_y - 3, gw, 6, TIMBER_WHITE)
    mid_x = gx + gw // 2
    a.rect(mid_x - 2, gy, 4, gh, TIMBER_WHITE)
    a.rect(gx + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)
    a.rect(mid_x + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)

    # 6. Ground Floor Sash Window with Stone Frame (R_SASH_GROUND)
    x, y, w, h = R_SASH_GROUND
    a.rect(x, y, w, h, STUCCO_BASE)
    a.noise(x, y, w, h, 0.025)
    a.rect(x + 8, y + h - 18, w - 16, 16, STONE_CREAM)
    a.rect(x + 8, y + h - 18, w - 16, 2, STONE_DARK)
    a.rect(x + 6, y + 4, w - 12, 14, STONE_CREAM)
    a.rect(x + 6, y + 4, w - 12, 2, STONE_DARK)
    gwx, gwy, gww, gwh = x + 14, y + 18, w - 28, h - 36
    a.rect(gwx, gwy, gww, gwh, TIMBER_WHITE)
    ggx, ggy, ggw, ggh = gwx + 5, gwy + 5, gww - 10, gwh - 10
    a.rect(ggx, ggy, ggw, ggh, GLASS_DARK)
    a.rect(ggx, ggy + ggh // 2 - 2, ggw, 5, TIMBER_WHITE)
    a.rect(ggx + ggw // 2 - 2, ggy, 4, ggh, TIMBER_WHITE)
    a.rect(ggx + 4, ggy + ggh // 2 + 6, (ggw // 2) - 8, (ggh // 2) - 12, GLASS_HIGHLIGHT)

    # 7. Maroon & Emerald Green Doors
    for (rx, ry, rw, rh), col, d_dark in [(R_DOOR_MAROON, DOOR_MAROON, (0.24, 0.04, 0.06)),
                                          (R_DOOR_GREEN,  DOOR_GREEN,  (0.02, 0.15, 0.07))]:
        a.rect(rx, ry, rw, rh, STONE_CREAM)
        dx, dy, dw, dh = rx + 4, ry, rw - 8, rh - 6
        a.rect(dx, dy, dw, dh, TIMBER_WHITE)
        fl_y = dy + dh - 26
        a.rect(dx + 4, fl_y, dw - 8, 22, GLASS_DARK)
        a.rect(dx + dw // 2 - 1, fl_y, 2, 22, TIMBER_WHITE)
        a.rect(dx + 6, fl_y + 4, (dw - 12) // 2, 14, GLASS_HIGHLIGHT)
        door_top = fl_y - 4
        door_h = door_top - dy
        a.rect(dx + 3, dy + 2, dw - 6, door_h - 2, col)
        pw = (dw - 18) // 2
        ph_top = (door_h - 28) // 2
        ph_bot = (door_h - 28) // 2
        p_uy = dy + door_h - ph_top - 8
        a.rect(dx + 6, p_uy, pw, ph_top, d_dark)
        a.rect(dx + 7, p_uy + 1, pw - 2, ph_top - 2, col)
        a.rect(dx + dw - pw - 6, p_uy, pw, ph_top, d_dark)
        a.rect(dx + dw - pw - 5, p_uy + 1, pw - 2, ph_top - 2, col)
        p_ly = dy + 8
        a.rect(dx + 6, p_ly, pw, ph_bot, d_dark)
        a.rect(dx + 7, p_ly + 1, pw - 2, ph_bot - 2, col)
        a.rect(dx + dw - pw - 6, p_ly, pw, ph_bot, d_dark)
        a.rect(dx + dw - pw - 5, p_ly + 1, pw - 2, ph_bot - 2, col)
        a.rect(dx + dw // 2 - 2, p_uy + ph_top // 2 - 2, 4, 8, BRASS_GOLD)
        a.rect(dx + dw // 2 - 2, dy + door_h // 2 - 2, 4, 4, BRASS_GOLD)
        a.rect(dx + dw // 2 - 8, dy + door_h // 2 - 12, 16, 4, BRASS_GOLD)
        a.noise(rx, ry, rw, rh, 0.02)

    # 8. Stone Trims
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 9. Chimney Pot
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    a.rect(x, y + h - 12, w, 12, (0.76, 0.40, 0.22))
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 10. Pavement
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 11. Cornice
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    for dx in range(x, x + w, 16):
        a.rect(dx, y + 8, 8, 16, STONE_DARK)
        a.rect(dx + 1, y + 10, 6, 12, (0.88, 0.85, 0.78))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.92, 0.90, 0.84))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_terraced_row_02_atlas", kit.OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_TRIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_TRIM, S, only=side("bottom"))


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    hw, hd = w / 2.0, d / 2.0
    x, y, z = at
    b0 = bm.verts.new((x - hw, y - hd, z))
    b1 = bm.verts.new((x + hw, y - hd, z))
    b2 = bm.verts.new((x + hw, y + hd, z))
    b3 = bm.verts.new((x - hw, y + hd, z))
    r0 = bm.verts.new((x - hw, y, z + h))
    r1 = bm.verts.new((x + hw, y, z + h))
    bm.faces.new((b0, b1, r1, r0))
    bm.faces.new((b2, b3, r0, r1))
    bm.faces.new((b3, b0, r0))
    bm.faces.new((b1, b2, r1))
    bm.faces.new((b0, b3, b2, b1))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


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
    img = paint_terraced_02_atlas()
    mat = material_for(img, "mat_terraced_row_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m Symmetrical Townhouse Pair (X: -5.0 to +5.0, Y: -3.5 to +3.5)
    # =========================================================================

    # 1. Continuous Pavement (10.0m x 8.0m)
    register_box("Pavement", 10.0, 8.0, 0.10, (0, -0.5, 0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_PAVEMENT)

    # 2. Continuous Ground Floor Stucco (10.0m x 7.0m, Z: 0.10 to 3.00)
    register_box("GroundFloor", 10.0, 7.0, 2.90, (0, 0, 0.10),
                 front=R_STUCCO, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 3. Paired Central Entrance: Shared Double Steps & Dual Doors (X = 0.0m)
    register_box("SharedStep1", 3.00, 0.70, 0.15, (0.0, -3.85, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("SharedStep2", 2.80, 0.40, 0.15, (0.0, -3.55, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # Left Door (Maroon, X = -0.75m)
    register_box("DoorL", 1.05, 0.20, 2.25, (-0.75, -3.52, 0.40),
                 front=R_DOOR_MAROON, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # Right Door (Green, X = +0.75m)
    register_box("DoorR", 1.05, 0.20, 2.25, (0.75, -3.52, 0.40),
                 front=R_DOOR_GREEN, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 4. Flanking Ground Floor Windows (Left X = -3.20m, Right X = +3.20m)
    register_box("GroundWinL", 1.40, 0.18, 1.85, (-3.20, -3.50, 0.75),
                 front=R_SASH_GROUND, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("GroundWinR", 1.40, 0.18, 1.85, (3.20, -3.50, 0.75),
                 front=R_SASH_GROUND, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Continuous Mid-Level String Course
    register_box("MidCornice", 10.0, 7.12, 0.18, (0, -0.04, 3.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Upper Floor Red/Brown Brick Facade (10.0m x 7.0m, Z: 3.18 to 5.90)
    register_box("FirstFloor", 10.0, 7.0, 2.72, (0, 0, 3.18),
                 front=R_BRICK_RED, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 7. Upper Floor 4 Sash Windows (X = -3.20m, -1.05m, +1.05m, +3.20m)
    register_box("UpperWin1", 1.15, 0.18, 1.65, (-3.20, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWin2", 1.15, 0.18, 1.65, (-1.05, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWin3", 1.15, 0.18, 1.65, (1.05, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWin4", 1.15, 0.18, 1.65, (3.20, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Continuous Eaves Cornice
    register_box("EavesCornice", 10.0, 7.16, 0.25, (0, -0.06, 5.90),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Continuous Pitched Slate Roof (10.0m x 7.1m)
    roof = make_pitched_roof("PitchedRoof", 10.0, 7.10, 1.60, at=(0, 0, 6.15))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z > 0.2)
    kit.map_faces_to_region(roof, R_BRICK_DARK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    register_box("RoofRidge", 10.0, 0.22, 0.12, (0, 0, 7.72),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Twin Outer Party-Wall Chimney Stacks (Left X = -4.55m, Right X = +4.55m)
    # Left Chimney
    register_box("ChimneyBaseL", 0.75, 1.20, 1.80, (-4.55, 0.5, 6.70),
                 front=R_BRICK_DARK, sides=R_BRICK_DARK, top=R_STONE_TRIM)
    register_box("ChimneyCapL", 0.85, 1.30, 0.14, (-4.55, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    for i, pot_y in enumerate([0.20, 0.80]):
        pot = make_cylinder(f"ChimneyPotL_{i+1}", r=0.13, h=0.55, segs=8, at=(-4.55, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # Right Chimney
    register_box("ChimneyBaseR", 0.75, 1.20, 1.80, (4.55, 0.5, 6.70),
                 front=R_BRICK_DARK, sides=R_BRICK_DARK, top=R_STONE_TRIM)
    register_box("ChimneyCapR", 0.85, 1.30, 0.14, (4.55, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    for i, pot_y in enumerate([0.20, 0.80]):
        pot = make_cylinder(f"ChimneyPotR_{i+1}", r=0.13, h=0.55, segs=8, at=(4.55, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Terraced_Row_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_terraced_row_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_terraced_row_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_terraced_row_02] generation complete.")


main()
