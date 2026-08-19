"""East York Modular Chinese Commercial / Shophouse Terrace (Variant 2 — 10.0m Double Unit).

Architectural Specs:
- 10.0m wide double-unit Chinese shophouse / commercial terrace row for East York high street
- Unit A (Left, X: -5.0 to 0.0): "Golden Dragon Herbalist & Tea" (金龍堂) with black/gold lacquered signboard,
  traditional wooden display storefront, red-and-gold canopy, carved column entrance
- Unit B (Right, X: 0.0 to +5.0): "East York Dim Sum & Takeaway" (東約克點心) with illuminated takeaway window,
  red moon-arch entrance portico, menu board, takeaway hatch
- First Floor: Traditional Chinese overhanging timber balcony with vermilion balustrade & lattice fretwork
- Upper Windows: Intricate Chinese hexagonal/Wan-pattern lattice screens with gold-trimmed lintels
- Roof: Multi-tier swept pagoda eaves with glazed emerald green ceramic tiles and gold dragon roof finials
- Multi-tier dougong bracket sets supporting both the first-floor balcony overhang and top eaves
- Seamlessly tiles alongside 10.0m and 5.0m East York residential terraces.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_terrace_02.py
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
R_YORK_STONE       = (0,   256, 256, 256)   # York stone masonry & plinth
R_RED_BRICK        = (256, 256, 128, 256)   # Upper floor red brick facade
R_EMERALD_ROOF     = (0,   128, 256, 128)   # Glazed emerald green ceramic roof tiles
R_CHARCOAL_ROOF    = (256, 128, 128, 128)   # Charcoal ceramic ridge tiles
R_SHOPFRONT_TEA    = (384, 384, 128, 128)   # Unit A Herbalist & Tea shopfront
R_SHOPFRONT_TAKEAWAY = (384, 256, 128, 128) # Unit B Dim Sum / Takeaway shopfront
R_SIGN_TEA         = (0,   96,  256, 32)    # Gold on black "金龍堂 GOLDEN DRAGON TEA"
R_SIGN_TAKEAWAY    = (256, 96,  256, 32)    # Red on gold "東約克點心 EAST YORK DIM SUM"
R_BALCONY_FRETWORK = (0,   64,  256, 32)    # Vermilion & gold carved wooden balcony railing
R_CANOPY_STRIPE    = (256, 64,  128, 32)    # Red & gold striped shopfront awning
R_LATTICE_UPPER    = (384, 128, 64,  128)   # Upper floor Chinese lattice window
R_LANTERN_RED      = (448, 128, 64,  128)   # Hanging red silk lantern
R_TIMBER_VERMILION = (0,   32,  256, 32)    # Vermilion lacquered pillars & beams
R_GOLD_TRIM        = (256, 32,  128, 32)    # Gold leaf accents & finials
R_STONE_TRIM       = (384, 32,  64,  32)    # Stone steps & curbs
R_PAVEMENT         = (0,   0,   256, 32)    # York flagstone pavement
R_CORNICE_CHINESE  = (256, 0,   256, 32)    # Ornate dougong cornice

# --- Palette Colors ---
YORK_STONE_BASE   = (0.76, 0.72, 0.62)
YORK_STONE_MORTAR = (0.64, 0.60, 0.52)
RED_BRICK_BASE    = (0.50, 0.20, 0.15)
RED_BRICK_MORTAR  = (0.68, 0.65, 0.58)
EMERALD_BASE      = (0.12, 0.38, 0.24)
EMERALD_DARK      = (0.07, 0.22, 0.14)
EMERALD_HILITE    = (0.20, 0.54, 0.36)
CHARCOAL_ROOF     = (0.16, 0.17, 0.20)
CHARCOAL_DARK     = (0.10, 0.11, 0.13)
VERMILION_RED     = (0.74, 0.12, 0.08)
VERMILION_DARK    = (0.44, 0.07, 0.05)
VERMILION_LIGHT   = (0.86, 0.20, 0.14)
IMPERIAL_GOLD     = (0.90, 0.74, 0.18)
GOLD_DARK         = (0.64, 0.50, 0.10)
BLACK_LACQUER     = (0.10, 0.10, 0.12)
STONE_CREAM       = (0.82, 0.78, 0.70)
STONE_DARK        = (0.56, 0.52, 0.46)
GLASS_DARK        = (0.07, 0.10, 0.13)
GLASS_HIGHLIGHT   = (0.16, 0.24, 0.32)
LANTERN_RED       = (0.88, 0.10, 0.06)
LANTERN_GLOW      = (0.98, 0.36, 0.16)
TEAL_ACCENT       = (0.15, 0.45, 0.48)


def paint_east_york_terrace_02_atlas():
    a = Atlas(S, seed=999)

    x, y, w, h = R_YORK_STONE
    a.rect(x, y, w, h, YORK_STONE_BASE)
    for my in range(y, y + h, 24):
        a.rect(x, my, w, 2, YORK_STONE_MORTAR)
        offset = 32 if ((my - y) // 24) % 2 else 0
        for mx in range(x - offset, x + w, 64):
            a.rect(max(x, mx), my, 2, 24, YORK_STONE_MORTAR)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)

    x, y, w, h = R_RED_BRICK
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_BRICK_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.04, bottom=0.0)

    x, y, w, h = R_EMERALD_ROOF
    a.rect(x, y, w, h, EMERALD_BASE)
    tile_h, tile_w = 14, 16
    for ty in range(y, y + h, tile_h):
        a.rect(x, ty, w, 3, EMERALD_DARK)
        a.rect(x, min(y + h - 1, ty + 3), w, 2, EMERALD_HILITE)
        for tx in range(x, x + w, tile_w):
            a.rect(tx, ty, 3, tile_h, EMERALD_DARK)
            a.rect(tx + 3, ty + 3, tile_w - 5, tile_h - 5, EMERALD_BASE)
            a.rect(tx + 5, ty + 5, tile_w - 9, tile_h - 7, EMERALD_HILITE)
    a.noise(x, y, w, h, 0.025)

    x, y, w, h = R_CHARCOAL_ROOF
    a.rect(x, y, w, h, CHARCOAL_ROOF)
    for ty in range(y, y + h, 12):
        a.rect(x, ty, w, 2, CHARCOAL_DARK)
        a.rect(x, ty + 2, w, 2, (0.28, 0.30, 0.34))
    a.noise(x, y, w, h, 0.03)

    x, y, w, h = R_SHOPFRONT_TEA
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, VERMILION_RED)
    gx, gy, gw, gh = x + 8, y + 10, w - 54, h - 20
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for sy in range(gy + 10, gy + gh - 4, 18):
        a.rect(gx, sy, gw, 3, VERMILION_DARK)
        for cx in range(gx + 6, gx + gw - 8, 14):
            a.rect(cx, sy + 3, 8, 12, IMPERIAL_GOLD)
            a.rect(cx + 2, sy + 15, 4, 3, TEAL_ACCENT)
    dx, dy, dw, dh = x + w - 42, y + 8, 34, h - 16
    a.rect(dx, dy, dw, dh, VERMILION_DARK)
    a.rect(dx + 2, dy + 2, dw - 4, dh - 4, VERMILION_RED)
    a.rect(dx + 6, dy + dh // 2, dw - 12, dh // 2 - 8, GLASS_DARK)
    for ly in range(dy + dh // 2 + 4, dy + dh - 10, 10):
        a.rect(dx + 6, ly, dw - 12, 2, IMPERIAL_GOLD)
    a.rect(dx + dw // 2 - 2, dy + dh // 4, 4, 8, IMPERIAL_GOLD)

    x, y, w, h = R_SHOPFRONT_TAKEAWAY
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, VERMILION_RED)
    hx, hy, hw, hh = x + 8, y + 12, w - 54, h - 24
    a.rect(hx, hy, hw, hh, (0.20, 0.20, 0.22))
    a.rect(hx + 4, hy + hh - 28, hw - 8, 24, (0.92, 0.88, 0.70))
    for my in range(hy + hh - 24, hy + hh - 6, 6):
        a.rect(hx + 8, my, hw - 16, 2, VERMILION_RED)
    a.rect(hx, hy + 24, hw, 4, (0.75, 0.78, 0.82))
    dx, dy, dw, dh = x + w - 42, y + 8, 34, h - 16
    a.rect(dx, dy, dw, dh, VERMILION_DARK)
    a.rect(dx + 2, dy + 2, dw - 4, dh - 4, VERMILION_RED)
    a.rect(dx + 6, dy + 6, dw - 12, dh - 12, GLASS_DARK)
    for ly in range(dy + 10, dy + dh - 8, 12):
        a.rect(dx + 6, ly, dw - 12, 2, VERMILION_RED)
    a.rect(dx + dw // 2 - 2, dy + dh // 2, 4, 8, IMPERIAL_GOLD)

    x, y, w, h = R_SIGN_TEA
    a.rect(x, y, w, h, BLACK_LACQUER)
    a.rect(x + 2, y + 2, w - 4, h - 4, (0.05, 0.05, 0.06))
    a.rect(x + 4, y + 4, w - 8, 2, IMPERIAL_GOLD)
    a.rect(x + 4, y + h - 6, w - 8, 2, IMPERIAL_GOLD)
    a.rect(x + 4, y + 4, 2, h - 8, IMPERIAL_GOLD)
    a.rect(x + w - 6, y + 4, 2, h - 8, IMPERIAL_GOLD)
    for cx in range(x + 20, x + w - 40, 28):
        a.rect(cx, y + 8, 18, 16, IMPERIAL_GOLD)
        a.rect(cx + 4, y + 12, 10, 8, BLACK_LACQUER)
        a.rect(cx + 7, y + 10, 4, 12, IMPERIAL_GOLD)

    x, y, w, h = R_SIGN_TAKEAWAY
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 2, y + 2, w - 4, h - 4, VERMILION_RED)
    a.rect(x + 4, y + 4, w - 8, 2, IMPERIAL_GOLD)
    a.rect(x + 4, y + h - 6, w - 8, 2, IMPERIAL_GOLD)
    for cx in range(x + 20, x + w - 40, 28):
        a.rect(cx, y + 8, 18, 16, IMPERIAL_GOLD)
        a.rect(cx + 3, y + 11, 12, 10, VERMILION_RED)
        a.rect(cx + 6, y + 9, 6, 14, IMPERIAL_GOLD)

    x, y, w, h = R_BALCONY_FRETWORK
    a.rect(x, y, w, h, VERMILION_RED)
    a.rect(x, y + h - 4, w, 4, IMPERIAL_GOLD)
    a.rect(x, y, w, 4, VERMILION_DARK)
    for bx in range(x, x + w, 16):
        a.rect(bx + 2, y + 6, 12, h - 12, VERMILION_DARK)
        a.rect(bx + 4, y + 8, 8, h - 16, VERMILION_RED)
        a.rect(bx + 7, y + 6, 2, h - 12, IMPERIAL_GOLD)
        a.rect(bx + 2, y + h // 2 - 1, 12, 2, IMPERIAL_GOLD)

    x, y, w, h = R_CANOPY_STRIPE
    a.rect(x, y, w, h, VERMILION_RED)
    for sx in range(x, x + w, 16):
        a.rect(sx, y, 8, h, IMPERIAL_GOLD)
    a.shade(x, y, w, h, top=0.0, bottom=-0.15)

    x, y, w, h = R_LATTICE_UPPER
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.rect(x + 6, y + h - 14, w - 12, 12, STONE_CREAM)
    a.rect(x + 6, y + 2, w - 12, 8, STONE_CREAM)
    wx, wy, ww, wh = x + 10, y + 12, w - 20, h - 26
    a.rect(wx, wy, ww, wh, VERMILION_RED)
    gx, gy, gw, gh = wx + 4, wy + 4, ww - 8, wh - 8
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for ly in range(gy + 6, gy + gh - 2, 12):
        a.rect(gx, ly, gw, 2, VERMILION_RED)
    for lx in range(gx + 6, gx + gw - 2, 12):
        a.rect(lx, gy, 2, gh, VERMILION_RED)
    a.rect(gx + 3, gy + gh // 2 + 4, (gw // 2) - 6, (gh // 2) - 8, GLASS_HIGHLIGHT)

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

    x, y, w, h = R_TIMBER_VERMILION
    a.rect(x, y, w, h, VERMILION_RED)
    for ty in range(y, y + h, 8):
        a.rect(x, ty, w, 2, VERMILION_DARK)
    a.noise(x, y, w, h, 0.02)

    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    for gy in range(y, y + h, 8):
        a.rect(x, gy, w, 2, GOLD_DARK)

    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 8):
        a.rect(x, sy, w, 2, STONE_DARK)

    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.50, 0.48, 0.44))
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    x, y, w, h = R_CORNICE_CHINESE
    a.rect(x, y, w, h, VERMILION_RED)
    a.rect(x, y + h - 6, w, 6, IMPERIAL_GOLD)
    a.rect(x, y, w, 4, IMPERIAL_GOLD)
    for cx in range(x, x + w, 16):
        a.rect(cx + 2, y + 6, 12, h - 12, VERMILION_DARK)
        a.rect(cx + 4, y + 8, 8, h - 16, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_east_york_terrace_02_atlas", OUT_DIR)


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


def make_swept_roof(name, w, d, eaves_h, ridge_h, flare=0.55, at=(0, 0, 0)):
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

    img = paint_east_york_terrace_02_atlas()
    mat = material_for(img, "EastYorkTerrace02_Mat")

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

    # 1. Base Pavement
    register_box("FrontPavement", 10.0, 1.50, 0.10, (0.0, -4.25, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Main Ground Floor Structure
    register_box("GroundFloorCore", 10.0, 7.0, 3.20, (0.0, 0.0, 0.10),
                 front=R_YORK_STONE, sides=R_YORK_STONE, back=R_YORK_STONE, top=R_STONE_TRIM)

    # 3. Unit A Shophouse (Left) — "Golden Dragon Tea & Herbalist"
    register_box("ShopfrontTea", 4.60, 0.22, 2.65, (-2.5, -3.52, 0.10),
                 front=R_SHOPFRONT_TEA, sides=R_TIMBER_VERMILION, top=R_TIMBER_VERMILION)
    register_box("SignboardTea", 4.70, 0.18, 0.55, (-2.5, -3.64, 2.75),
                 front=R_SIGN_TEA, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)
    register_box("AwningTea", 4.60, 0.85, 0.15, (-2.5, -3.95, 2.60),
                 front=R_CANOPY_STRIPE, sides=R_CANOPY_STRIPE, top=R_CANOPY_STRIPE)
    for lx in [-4.85, -0.15]:
        register_box(f"ColumnA_{lx:.1f}", 0.18, 0.24, 3.20, (lx, -3.55, 0.10),
                     front=R_TIMBER_VERMILION, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)
    for i, lx in enumerate([-4.60, -0.40]):
        lantern = make_cylinder(f"LanternTea_{i}", r=0.18, h=0.48, segs=8, at=(lx, -4.10, 1.85))
        lantern.data.materials.append(mat)
        kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
        parts.append(lantern)

    # 4. Unit B Shophouse (Right) — "East York Dim Sum & Takeaway"
    register_box("ShopfrontTakeaway", 4.60, 0.22, 2.65, (2.5, -3.52, 0.10),
                 front=R_SHOPFRONT_TAKEAWAY, sides=R_TIMBER_VERMILION, top=R_TIMBER_VERMILION)
    register_box("SignboardTakeaway", 4.70, 0.18, 0.55, (2.5, -3.64, 2.75),
                 front=R_SIGN_TAKEAWAY, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)
    for rx in [0.15, 4.85]:
        register_box(f"ColumnB_{rx:.1f}", 0.18, 0.24, 3.20, (rx, -3.55, 0.10),
                     front=R_TIMBER_VERMILION, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)
    for i, rx in enumerate([0.40, 4.60]):
        lantern = make_cylinder(f"LanternTakeaway_{i}", r=0.18, h=0.48, segs=8, at=(rx, -4.10, 1.85))
        lantern.data.materials.append(mat)
        kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
        parts.append(lantern)

    # 5. First Floor Overhanging Balcony
    register_box("BalconyFloor", 10.2, 1.15, 0.20, (0.0, -4.00, 3.30),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_VERMILION, top=R_PAVEMENT)
    register_box("BalconyFrontRail", 10.2, 0.08, 0.85, (0.0, -4.54, 3.50),
                 front=R_BALCONY_FRETWORK, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)
    register_box("BalconySideRailL", 0.08, 1.10, 0.85, (-5.06, -4.00, 3.50),
                 front=R_TIMBER_VERMILION, sides=R_BALCONY_FRETWORK, top=R_GOLD_TRIM)
    register_box("BalconySideRailR", 0.08, 1.10, 0.85, (5.06, -4.00, 3.50),
                 front=R_TIMBER_VERMILION, sides=R_BALCONY_FRETWORK, top=R_GOLD_TRIM)

    for bx in np.linspace(-4.5, 4.5, 9):
        register_box(f"BalconyBracket_{bx:.1f}", 0.18, 0.65, 0.30, (bx, -3.80, 3.00),
                     front=R_TIMBER_VERMILION, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)

    # 6. First Floor Red Brick Core
    register_box("FirstFloorCore", 10.0, 7.0, 2.70, (0.0, 0.0, 3.50),
                 front=R_RED_BRICK, sides=R_RED_BRICK, back=R_RED_BRICK)

    # 7. First Floor Chinese Lattice Windows (4 bays)
    for i, wx in enumerate([-3.75, -1.25, 1.25, 3.75]):
        register_box(f"UpperWin_{i+1}", 1.40, 0.18, 1.75, (wx, -3.52, 3.85),
                     front=R_LATTICE_UPPER, sides=R_TIMBER_VERMILION, top=R_TIMBER_VERMILION)
        register_box(f"UpperCanopy_{i+1}", 1.55, 0.32, 0.16, (wx, -3.60, 5.60),
                     front=R_CORNICE_CHINESE, sides=R_TIMBER_VERMILION, top=R_EMERALD_ROOF)

    # 8. Top Eaves Cornice & Dougong Brackets
    register_box("TopEavesCornice", 10.4, 7.30, 0.28, (0.0, -0.08, 6.20),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)
    for bx in np.linspace(-4.6, 4.6, 11):
        register_box(f"TopDougong_{bx:.1f}", 0.20, 0.32, 0.24, (bx, -3.65, 5.96),
                     front=R_TIMBER_VERMILION, sides=R_TIMBER_VERMILION, top=R_GOLD_TRIM)

    # 9. Main Swept Pagoda Roof
    roof = make_swept_roof("SweptEmeraldRoof", 10.8, 7.8, eaves_h=0.0, ridge_h=1.95, flare=0.65, at=(0, 0, 6.48))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_EMERALD_ROOF, S, only=lambda f: abs(f.normal.y) > 0.3 and f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_RED_BRICK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_TIMBER_VERMILION, S, only=lambda f: f.normal.z < -0.3)
    parts.append(roof)

    register_box("RoofRidge", 10.8, 0.32, 0.20, (0, 0, 8.42),
                 front=R_CHARCOAL_ROOF, sides=R_CHARCOAL_ROOF, top=R_GOLD_TRIM)
    for fx in [-5.40, 5.40]:
        register_box(f"DragonFinial_{fx}", 0.26, 0.36, 0.42, (fx, 0, 8.52),
                     front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # 10. Party Wall Chimneys with Pagoda Caps
    for cx in [-4.70, 4.70]:
        register_box(f"Chimney_{cx:.1f}", 0.75, 1.20, 1.60, (cx, 0.4, 7.20),
                     front=R_RED_BRICK, sides=R_RED_BRICK, top=R_STONE_TRIM)
        register_box(f"ChimneyCap_{cx:.1f}", 0.90, 1.35, 0.16, (cx, 0.4, 8.80),
                     front=R_CORNICE_CHINESE, sides=R_EMERALD_ROOF, top=R_GOLD_TRIM)
        pot = make_cylinder(f"ChimneyPot_{cx:.1f}", r=0.14, h=0.45, segs=8, at=(cx, 0.4, 8.96))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_GOLD_TRIM, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_Terrace_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_terrace_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_terrace_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_east_york_terrace_02] generation complete in east_york/ folder.")


main()
