"""Victorian London Terraced House (Variant 2 — London Stock Yellow Brick).

Architectural Specs:
- Iconic London Stock Yellow/Buff brick facade with warm stone mortar
- Ground floor right-hand canted 3-sided bay window
- Ground floor left-hand navy blue 4-panel front door with arched fanlight and stone steps
- Upper-floor sash windows with decorative stone architraves & keystones
- Graphite slate pitched roof with central brick chimney stack and 2 terracotta pots
- Designed to tile seamlessly on a 5.0m grid (width: 5.0m, depth: 7.0m, origin at bottom-centre).

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_victorian_house_02.py
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

# --- Atlas Region Definitions (x, y, w, h) in pixels ---
R_BRICK_STOCK   = (0,   256, 256, 256)   # London stock yellow/ochre brick facade
R_BRICK_DARK    = (256, 256, 128, 256)   # Weathered side party wall & chimney brick
R_SLATE_ROOF    = (0,   128, 256, 128)   # Graphite slate roof tiles
R_STUCCO        = (256, 128, 128, 128)   # Ground floor warm stone stucco
R_SASH_WINDOW   = (384, 384, 128, 128)   # Upper floor 2-over-2 sash window with keystone
R_BAY_FRONT     = (384, 256, 128, 128)   # Bay window front sash
R_BAY_SIDE      = (384, 128, 64,  128)   # Bay window angled side sash
R_DOOR_NAVY     = (448, 128, 64,  128)   # Navy 4-panel Victorian door + fanlight
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, coping, steps
R_BAY_ROOF      = (256, 64,  128, 64)    # Lead flashing for bay canopy
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Terracotta clay pot with soot
R_PAVEMENT      = (0,   0,   256, 64)    # Pavement flags
R_CORNICE       = (256, 0,   256, 64)    # Classical modillion cornice moulding

# --- Color Palette ---
STOCK_BRICK_BASE = (0.74, 0.63, 0.44)
STOCK_MORTAR     = (0.78, 0.76, 0.70)
DARK_BRICK_BASE  = (0.42, 0.35, 0.28)
STUCCO_BASE      = (0.75, 0.72, 0.65)
STUCCO_GROOVE    = (0.55, 0.52, 0.46)
SLATE_BASE       = (0.24, 0.26, 0.30)
SLATE_DARK       = (0.16, 0.18, 0.20)
SLATE_HIGHLIGHT  = (0.34, 0.38, 0.44)
STONE_CREAM      = (0.80, 0.77, 0.70)
STONE_DARK       = (0.58, 0.55, 0.49)
TIMBER_WHITE     = (0.94, 0.94, 0.92)
TIMBER_FRAME     = (0.84, 0.84, 0.82)
GLASS_DARK       = (0.09, 0.12, 0.16)
GLASS_HIGHLIGHT  = (0.20, 0.26, 0.34)
DOOR_NAVY        = (0.08, 0.14, 0.28)
DOOR_DARK        = (0.04, 0.07, 0.16)
BRASS_GOLD       = (0.86, 0.73, 0.24)
TERRACOTTA       = (0.70, 0.34, 0.18)
SOOT_BLACK       = (0.14, 0.14, 0.14)
LEAD_GREY        = (0.32, 0.33, 0.36)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_victorian_02_atlas():
    a = Atlas(S, seed=88)

    # 1. London Stock Yellow Brick (R_BRICK_STOCK)
    x, y, w, h = R_BRICK_STOCK
    a.bricks(x, y, w, h, brick=STOCK_BRICK_BASE, mortar=STOCK_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.04, bottom=0.0)

    # 2. Darker Weathered Party Wall Brick (R_BRICK_DARK)
    x, y, w, h = R_BRICK_DARK
    a.bricks(x, y, w, h, brick=DARK_BRICK_BASE, mortar=(0.60, 0.58, 0.53), bw=24, bh=10, jitter=0.08)
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
        a.rect(x, gy + 2, w, 1, (0.86, 0.83, 0.76))
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.03)

    # 5. Upper Sash Window with Keystone Arch (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, STOCK_BRICK_BASE)
    a.noise(x, y, w, h, 0.03)
    # Stone arch lintel + prominent central keystone
    a.rect(x + 10, y + h - 20, w - 20, 18, STONE_CREAM)
    a.rect(x + w // 2 - 6, y + h - 24, 12, 24, (0.88, 0.85, 0.78))  # Keystone
    a.rect(x + 10, y + h - 20, w - 20, 2, STONE_DARK)
    # Sill
    a.rect(x + 8, y + 4, w - 16, 12, STONE_CREAM)
    a.rect(x + 8, y + 4, w - 16, 2, STONE_DARK)
    # Window frame
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
    a.noise(x, y, w, h, 0.02)

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

    # 8. Victorian Navy Door + Fanlight (R_DOOR_NAVY)
    x, y, w, h = R_DOOR_NAVY
    a.rect(x, y, w, h, STONE_CREAM)
    dx, dy, dw, dh = x + 4, y, w - 8, h - 6
    a.rect(dx, dy, dw, dh, TIMBER_WHITE)
    fl_y = dy + dh - 26
    a.rect(dx + 4, fl_y, dw - 8, 22, GLASS_DARK)
    a.rect(dx + dw // 2 - 1, fl_y, 2, 22, TIMBER_WHITE)
    a.rect(dx + 6, fl_y + 4, (dw - 12) // 2, 14, GLASS_HIGHLIGHT)
    door_top = fl_y - 4
    door_h = door_top - dy
    a.rect(dx + 3, dy + 2, dw - 6, door_h - 2, DOOR_NAVY)
    pw = (dw - 18) // 2
    ph_top = (door_h - 28) // 2
    ph_bot = (door_h - 28) // 2
    # Panels
    p_uy = dy + door_h - ph_top - 8
    a.rect(dx + 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + 7, p_uy + 1, pw - 2, ph_top - 2, DOOR_NAVY)
    a.rect(dx + dw - pw - 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_uy + 1, pw - 2, ph_top - 2, DOOR_NAVY)
    p_ly = dy + 8
    a.rect(dx + 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + 7, p_ly + 1, pw - 2, ph_bot - 2, DOOR_NAVY)
    a.rect(dx + dw - pw - 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_ly + 1, pw - 2, ph_bot - 2, DOOR_NAVY)
    # Brass fixtures
    a.rect(dx + dw // 2 - 2, p_uy + ph_top // 2 - 2, 4, 8, BRASS_GOLD)
    a.rect(dx + dw // 2 - 2, dy + door_h // 2 - 2, 4, 4, BRASS_GOLD)
    a.rect(dx + dw // 2 - 8, dy + door_h // 2 - 12, 16, 4, BRASS_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 9. Stone Trims (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 10. Bay Roof (R_BAY_ROOF)
    x, y, w, h = R_BAY_ROOF
    a.rect(x, y, w, h, LEAD_GREY)
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.22, 0.23, 0.25))
        a.rect(lx + 3, y, 1, h, (0.45, 0.46, 0.49))
    a.noise(x, y, w, h, 0.025)

    # 11. Chimney Pot (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    a.rect(x, y + h - 12, w, 12, (0.76, 0.40, 0.22))
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 12. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 13. Cornice (R_CORNICE)
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    for dx in range(x, x + w, 16):
        a.rect(dx, y + 8, 8, 16, STONE_DARK)
        a.rect(dx + 1, y + 10, 6, 12, (0.88, 0.85, 0.78))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.92, 0.90, 0.84))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_victorian_house_02_atlas", kit.OUT_DIR)


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
    img = paint_victorian_02_atlas()
    mat = material_for(img, "mat_victorian_house_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 5.0m Grid Alignment (X: -2.5 to +2.5, Y: -3.5 to +3.5)
    # =========================================================================

    # 1. Pavement
    register_box("Pavement", 5.0, 8.0, 0.10, (0, -0.5, 0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_PAVEMENT)

    # 2. Ground Floor Stucco (Z: 0.10 to 3.00, H: 2.90m)
    register_box("GroundFloor", 5.0, 7.0, 2.90, (0, 0, 0.10),
                 front=R_STUCCO, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 3. Ground Floor Canted Bay Window (Right side: X = +1.15m)
    bay = make_canted_bay("BayWindow", 2.2, 0.65, 2.40, bevel=0.45, at=(1.15, -3.5, 0.35))
    bay.data.materials.append(mat)
    kit.map_faces_to_region(bay, R_BAY_FRONT, S, only=lambda f: f.normal.y < -0.8)
    kit.map_faces_to_region(bay, R_BAY_SIDE,  S, only=lambda f: abs(f.normal.x) > 0.4 and f.normal.y < -0.2)
    kit.map_faces_to_region(bay, R_BAY_ROOF,  S, only=lambda f: f.normal.z > 0.7)
    kit.map_faces_to_region(bay, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.7 or f.normal.y > 0.5)
    parts.append(bay)

    bay_roof = make_canted_bay("BayRoof", 2.36, 0.75, 0.32, bevel=0.50, at=(1.15, -3.5, 2.75))
    bay_roof.data.materials.append(mat)
    kit.map_faces_to_region(bay_roof, R_BAY_ROOF, S, only=lambda f: f.normal.z > 0.3 or f.normal.y < -0.2)
    kit.map_faces_to_region(bay_roof, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.3 and f.normal.y >= -0.2)
    parts.append(bay_roof)

    # 4. Front Entrance: Navy Door (Left side: X = -1.35m)
    register_box("DoorStep1", 1.30, 0.65, 0.15, (-1.35, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep2", 1.20, 0.35, 0.15, (-1.35, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("FrontDoor", 1.05, 0.20, 2.25, (-1.35, -3.52, 0.40),
                 front=R_DOOR_NAVY, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. String Course
    register_box("MidCornice", 5.0, 7.12, 0.18, (0, -0.04, 3.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. First Floor London Stock Yellow Brick (Z: 3.18 to 5.90, H: 2.72m)
    register_box("FirstFloor", 5.0, 7.0, 2.72, (0, 0, 3.18),
                 front=R_BRICK_STOCK, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 7. Upper Floor Sash Windows
    register_box("UpperWindowL", 1.10, 0.18, 1.65, (-1.35, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWindowR", 1.20, 0.18, 1.65, (1.15, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Eaves Cornice
    register_box("EavesCornice", 5.0, 7.16, 0.25, (0, -0.06, 5.90),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Pitched Slate Roof
    roof = make_pitched_roof("PitchedRoof", 5.0, 7.10, 1.60, at=(0, 0, 6.15))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z > 0.2)
    kit.map_faces_to_region(roof, R_BRICK_DARK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    register_box("RoofRidge", 5.0, 0.22, 0.12, (0, 0, 7.72),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Central Chimney Stack (X = 0, Y = 0.5)
    register_box("ChimneyBase", 0.75, 1.20, 1.80, (0.0, 0.5, 6.70),
                 front=R_BRICK_DARK, sides=R_BRICK_DARK, top=R_STONE_TRIM)
    register_box("ChimneyCap", 0.85, 1.30, 0.14, (0.0, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 11. Terracotta Clay Chimney Pots
    for i, pot_y in enumerate([0.20, 0.80]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.14, h=0.55, segs=8, at=(0.0, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Victorian_House_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_victorian_house_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_victorian_house_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_victorian_house_02] generation complete.")


main()
