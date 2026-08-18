"""Modular Terraced Housing Pair (Variant 1 — 2-Unit Red/Stock Brick Asymmetric Terrace).

Architectural Specs:
- 10.0m wide double-unit London terraced block (2x 5.0m houses connected along party wall)
- Unit A (Left, X: -5.0 to 0.0): London Red Brick, left canted bay window, right black gloss door
- Unit B (Right, X: 0.0 to +5.0): London Stock Yellow Brick, left royal blue door, right canted bay window
- Continuous ground-floor rusticated stucco plinth
- Shared central party-wall chimney stack with 4 terracotta clay chimney pots
- Continuous weathered Welsh slate roof
- Designed for seamless tiling on a 10.0m grid or directly alongside 5.0m single houses.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_terraced_row_01.py
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
R_BRICK_RED     = (0,   256, 256, 256)   # Unit A red brick
R_BRICK_STOCK   = (256, 256, 128, 256)   # Unit B London stock yellow brick
R_SLATE_ROOF    = (0,   128, 256, 128)   # Welsh slate roof
R_STUCCO        = (256, 128, 128, 128)   # Ground floor stucco
R_SASH_WINDOW   = (384, 384, 128, 128)   # Upper sash window
R_BAY_FRONT     = (384, 256, 128, 128)   # Bay window front panel
R_BAY_SIDE      = (384, 128, 64,  128)   # Bay window side panel
R_DOOR_BLACK    = (448, 128, 64,  128)   # Unit A Black gloss door
R_DOOR_BLUE     = (448, 0,   64,  128)   # Unit B Royal blue door
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, steps
R_BAY_ROOF      = (256, 64,  128, 64)    # Lead canopy
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Terracotta chimney pot
R_PAVEMENT      = (0,   0,   256, 64)    # Pavement flags
R_CORNICE       = (256, 0,   128, 64)    # Eaves cornice band

# --- Palette Colors ---
RED_BRICK_BASE   = (0.54, 0.24, 0.18)
RED_MORTAR       = (0.70, 0.67, 0.62)
STOCK_BRICK_BASE = (0.74, 0.63, 0.44)
STOCK_MORTAR     = (0.78, 0.76, 0.70)
DARK_BRICK_BASE  = (0.40, 0.32, 0.26)
STUCCO_BASE      = (0.76, 0.73, 0.66)
STUCCO_GROOVE    = (0.56, 0.53, 0.47)
SLATE_BASE       = (0.26, 0.28, 0.33)
SLATE_DARK       = (0.18, 0.20, 0.23)
SLATE_HIGHLIGHT  = (0.34, 0.38, 0.44)
STONE_CREAM      = (0.80, 0.77, 0.70)
STONE_DARK       = (0.58, 0.55, 0.49)
TIMBER_WHITE     = (0.94, 0.94, 0.92)
TIMBER_FRAME     = (0.84, 0.84, 0.82)
GLASS_DARK       = (0.09, 0.12, 0.16)
GLASS_HIGHLIGHT  = (0.20, 0.26, 0.34)
DOOR_BLACK       = (0.12, 0.12, 0.13)
DOOR_BLUE        = (0.10, 0.24, 0.55)
BRASS_GOLD       = (0.86, 0.73, 0.24)
TERRACOTTA       = (0.70, 0.34, 0.18)
SOOT_BLACK       = (0.14, 0.14, 0.14)
LEAD_GREY        = (0.32, 0.33, 0.36)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_terraced_01_atlas():
    a = Atlas(S, seed=120)

    # 1. Red Brick (R_BRICK_RED)
    x, y, w, h = R_BRICK_RED
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.05, bottom=0.0)

    # 2. London Stock Yellow Brick (R_BRICK_STOCK)
    x, y, w, h = R_BRICK_STOCK
    a.bricks(x, y, w, h, brick=STOCK_BRICK_BASE, mortar=STOCK_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.04, bottom=0.0)

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
        a.rect(x, gy + 2, w, 1, (0.86, 0.83, 0.76))
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.03)

    # 5. Upper Sash Window (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.noise(x, y, w, h, 0.03)
    a.rect(x + 10, y + h - 18, w - 20, 16, STONE_CREAM)
    a.rect(x + 10, y + h - 18, w - 20, 2, STONE_DARK)
    a.rect(x + 8, y + 4, w - 16, 12, STONE_CREAM)
    a.rect(x + 8, y + 4, w - 16, 2, STONE_DARK)
    wx, wy, ww, wh = x + 16, y + 16, w - 32, h - 36
    a.rect(wx, wy, ww, wh, TIMBER_FRAME)
    gx, gy, gw, gh = wx + 5, wy + 5, ww - 10, wh - 10
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    mid_y = gy + gh // 2
    a.rect(gx, mid_y - 3, gw, 6, TIMBER_WHITE)
    mid_x = gx + gw // 2
    a.rect(mid_x - 2, gy, 4, gh, TIMBER_WHITE)
    a.rect(gx + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)
    a.rect(mid_x + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)

    # 6. Bay Window Front Panel (R_BAY_FRONT)
    x, y, w, h = R_BAY_FRONT
    a.rect(x, y, w, h, STUCCO_BASE)
    a.rect(x, y + h - 14, w, 14, STONE_CREAM)
    a.rect(x, y + h - 14, w, 2, STONE_DARK)
    a.rect(x, y, w, 16, STONE_CREAM)
    bx, by, bw, bh = x + 12, y + 16, w - 24, h - 32
    a.rect(bx, by, bw, bh, TIMBER_WHITE)
    igx, igy, igw, igh = bx + 5, by + 5, bw - 10, bh - 10
    a.rect(igx, igy, igw, igh, GLASS_DARK)
    a.rect(igx, igy + igh // 2 - 2, igw, 5, TIMBER_WHITE)
    a.rect(igx + igw // 2 - 2, igy, 4, igh, TIMBER_WHITE)
    a.rect(igx + 4, igy + igh // 2 + 6, (igw // 2) - 8, (igh // 2) - 12, GLASS_HIGHLIGHT)

    # 7. Bay Window Side Panel (R_BAY_SIDE)
    x, y, w, h = R_BAY_SIDE
    a.rect(x, y, w, h, STUCCO_BASE)
    a.rect(x, y + h - 14, w, 14, STONE_CREAM)
    a.rect(x, y, w, 16, STONE_CREAM)
    sx, sy, sw, sh = x + 8, y + 16, w - 16, h - 32
    a.rect(sx, sy, sw, sh, TIMBER_WHITE)
    sgx, sgy, sgw, sgh = sx + 4, sy + 4, sw - 8, sh - 8
    a.rect(sgx, sgy, sgw, sgh, GLASS_DARK)
    a.rect(sgx, sgy + sgh // 2 - 2, sgw, 4, TIMBER_WHITE)
    a.rect(sgx + 2, sgy + sgh // 2 + 4, sgw - 4, sgh // 2 - 8, GLASS_HIGHLIGHT)

    # 8. Black Door (R_DOOR_BLACK)
    for (rx, ry, rw, rh), col, d_dark in [(R_DOOR_BLACK, DOOR_BLACK, (0.05, 0.05, 0.05)),
                                          (R_DOOR_BLUE,  DOOR_BLUE,  (0.04, 0.10, 0.28))]:
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

    # 9. Stone Trims
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 10. Bay Roof
    x, y, w, h = R_BAY_ROOF
    a.rect(x, y, w, h, LEAD_GREY)
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.22, 0.23, 0.25))
        a.rect(lx + 3, y, 1, h, (0.45, 0.46, 0.49))
    a.noise(x, y, w, h, 0.025)

    # 11. Chimney Pot
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    a.rect(x, y + h - 12, w, 12, (0.76, 0.40, 0.22))
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 12. Pavement
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 13. Cornice
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    for dx in range(x, x + w, 16):
        a.rect(dx, y + 8, 8, 16, STONE_DARK)
        a.rect(dx + 1, y + 10, 6, 12, (0.88, 0.85, 0.78))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.92, 0.90, 0.84))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_terraced_row_01_atlas", kit.OUT_DIR)


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


def make_canted_bay(name, w, d, h, bevel=0.45, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    hw = w / 2.0
    x, y, z = at
    b0 = bm.verts.new((x - hw,         y,     z))
    b1 = bm.verts.new((x - hw + bevel, y - d, z))
    b2 = bm.verts.new((x + hw - bevel, y - d, z))
    b3 = bm.verts.new((x + hw,         y,     z))
    t0 = bm.verts.new((x - hw,         y,     z + h))
    t1 = bm.verts.new((x - hw + bevel, y - d, z + h))
    t2 = bm.verts.new((x + hw - bevel, y - d, z + h))
    t3 = bm.verts.new((x + hw,         y,     z + h))
    bm.faces.new((b0, b1, t1, t0))
    bm.faces.new((b1, b2, t2, t1))
    bm.faces.new((b2, b3, t3, t2))
    bm.faces.new((t0, t1, t2, t3))
    bm.faces.new((b0, b3, b2, b1))
    bm.faces.new((b3, b0, t0, t3))
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
    img = paint_terraced_01_atlas()
    mat = material_for(img, "mat_terraced_row_01")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m Double-Unit Terraced Block (X: -5.0 to +5.0, Y: -3.5 to +3.5)
    # =========================================================================

    # 1. Continuous Pavement (10.0m x 8.0m)
    register_box("Pavement", 10.0, 8.0, 0.10, (0, -0.5, 0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_PAVEMENT)

    # 2. Continuous Ground Floor Stucco (10.0m x 7.0m, Z: 0.10 to 3.00)
    register_box("GroundFloor", 10.0, 7.0, 2.90, (0, 0, 0.10),
                 front=R_STUCCO, sides=R_BRICK_RED, back=R_BRICK_RED)

    # 3. Unit A (Left, center X = -2.5m):
    # - Canted Bay Window on Left (X = -3.65m)
    bay_a = make_canted_bay("BayA", 2.2, 0.65, 2.40, bevel=0.45, at=(-3.65, -3.5, 0.35))
    bay_a.data.materials.append(mat)
    kit.map_faces_to_region(bay_a, R_BAY_FRONT, S, only=lambda f: f.normal.y < -0.8)
    kit.map_faces_to_region(bay_a, R_BAY_SIDE,  S, only=lambda f: abs(f.normal.x) > 0.4 and f.normal.y < -0.2)
    kit.map_faces_to_region(bay_a, R_BAY_ROOF,  S, only=lambda f: f.normal.z > 0.7)
    kit.map_faces_to_region(bay_a, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.7 or f.normal.y > 0.5)
    parts.append(bay_a)

    bay_roof_a = make_canted_bay("BayRoofA", 2.36, 0.75, 0.32, bevel=0.50, at=(-3.65, -3.5, 2.75))
    bay_roof_a.data.materials.append(mat)
    kit.map_faces_to_region(bay_roof_a, R_BAY_ROOF, S, only=lambda f: f.normal.z > 0.3 or f.normal.y < -0.2)
    kit.map_faces_to_region(bay_roof_a, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.3 and f.normal.y >= -0.2)
    parts.append(bay_roof_a)

    # - Black Front Door on Right (X = -1.35m)
    register_box("DoorStepA1", 1.30, 0.65, 0.15, (-1.35, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStepA2", 1.20, 0.35, 0.15, (-1.35, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("FrontDoorA", 1.05, 0.20, 2.25, (-1.35, -3.52, 0.40),
                 front=R_DOOR_BLACK, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 4. Unit B (Right, center X = +2.5m):
    # - Royal Blue Front Door on Left (X = +1.35m)
    register_box("DoorStepB1", 1.30, 0.65, 0.15, (1.35, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStepB2", 1.20, 0.35, 0.15, (1.35, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("FrontDoorB", 1.05, 0.20, 2.25, (1.35, -3.52, 0.40),
                 front=R_DOOR_BLUE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # - Canted Bay Window on Right (X = +3.65m)
    bay_b = make_canted_bay("BayB", 2.2, 0.65, 2.40, bevel=0.45, at=(3.65, -3.5, 0.35))
    bay_b.data.materials.append(mat)
    kit.map_faces_to_region(bay_b, R_BAY_FRONT, S, only=lambda f: f.normal.y < -0.8)
    kit.map_faces_to_region(bay_b, R_BAY_SIDE,  S, only=lambda f: abs(f.normal.x) > 0.4 and f.normal.y < -0.2)
    kit.map_faces_to_region(bay_b, R_BAY_ROOF,  S, only=lambda f: f.normal.z > 0.7)
    kit.map_faces_to_region(bay_b, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.7 or f.normal.y > 0.5)
    parts.append(bay_b)

    bay_roof_b = make_canted_bay("BayRoofB", 2.36, 0.75, 0.32, bevel=0.50, at=(3.65, -3.5, 2.75))
    bay_roof_b.data.materials.append(mat)
    kit.map_faces_to_region(bay_roof_b, R_BAY_ROOF, S, only=lambda f: f.normal.z > 0.3 or f.normal.y < -0.2)
    kit.map_faces_to_region(bay_roof_b, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.3 and f.normal.y >= -0.2)
    parts.append(bay_roof_b)

    # 5. Continuous Mid-Level String Course
    register_box("MidCornice", 10.0, 7.12, 0.18, (0, -0.04, 3.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. First Floor:
    # - Unit A Red Brick Upper Facade (X: -5.0 to 0.0)
    register_box("FirstFloorA", 5.0, 7.0, 2.72, (-2.5, 0, 3.18),
                 front=R_BRICK_RED, sides=R_BRICK_RED, back=R_BRICK_RED)
    # - Unit B London Stock Yellow Brick Upper Facade (X: 0.0 to +5.0)
    register_box("FirstFloorB", 5.0, 7.0, 2.72, (2.5, 0, 3.18),
                 front=R_BRICK_STOCK, sides=R_BRICK_STOCK, back=R_BRICK_STOCK)

    # 7. First Floor Sash Windows (4 windows across the row)
    register_box("UpperWinA1", 1.20, 0.18, 1.65, (-3.65, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWinA2", 1.10, 0.18, 1.65, (-1.35, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWinB1", 1.10, 0.18, 1.65, (1.35, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWinB2", 1.20, 0.18, 1.65, (3.65, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Continuous Eaves Cornice
    register_box("EavesCornice", 10.0, 7.16, 0.25, (0, -0.06, 5.90),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Continuous Pitched Slate Roof (10.0m x 7.1m)
    roof = make_pitched_roof("PitchedRoof", 10.0, 7.10, 1.60, at=(0, 0, 6.15))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z > 0.2)
    kit.map_faces_to_region(roof, R_BRICK_STOCK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    register_box("RoofRidge", 10.0, 0.22, 0.12, (0, 0, 7.72),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Shared Central Party-Wall Chimney Stack (X = 0.0m, Y = 0.5m) with 4 Pots
    register_box("ChimneyBase", 0.75, 1.80, 1.80, (0.0, 0.5, 6.70),
                 front=R_BRICK_RED, sides=R_BRICK_RED, top=R_STONE_TRIM)
    register_box("ChimneyCap", 0.85, 1.90, 0.14, (0.0, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    for i, pot_y in enumerate([-0.25, 0.25, 0.75, 1.25]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.13, h=0.55, segs=8, at=(0.0, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Terraced_Row_01")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_terraced_row_01_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_terraced_row_01.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_terraced_row_01] generation complete.")


main()
