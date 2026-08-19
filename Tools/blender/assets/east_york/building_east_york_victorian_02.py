"""East York Victorian Villa (Variant 2 — Asymmetric Turret Pagoda Villa).

Architectural Specs:
- 7.0m wide x 8.0m deep x 9.8m high asymmetric Victorian townhouse
- Left Side: Prominent 3-storey octagonal corner turret capped with flared swept pagoda roof & gold finial
- Right Side: Recessed ground floor entrance with vermilion portico & lantern, 1st & 2nd floor Chinese lattice sash windows
- Weathered York red brick facade, buff stone quoins, and carved Chinese meander frieze
- Multi-tier swept flying eaves with dark glazed emerald ceramic roof tiles and dragon finials.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_victorian_02.py
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

# --- Atlas Regions ---
R_BRICK_MAIN        = (0,   256, 256, 256)   # Weathered York red brick
R_YORK_STONE        = (256, 256, 128, 256)   # Buff stone masonry & plinth
R_EMERALD_ROOF      = (0,   128, 256, 128)   # Glazed dark emerald ceramic roof tiles
R_CHARCOAL_ROOF     = (256, 128, 128, 128)   # Charcoal ceramic ridge roll
R_TURRET_PANEL      = (384, 384, 128, 128)   # Octagonal turret window panel
R_LATTICE_WIN       = (384, 256, 128, 128)   # Main facade lattice window
R_DOOR_VERMILION    = (384, 128, 64,  128)   # Vermilion door with brass knocker
R_LANTERN_RED       = (448, 128, 64,  128)   # Hanging red silk lantern
R_TIMBER_RED        = (0,   64,  256, 64)    # Vermilion wood beams & dougong brackets
R_GOLD_TRIM         = (256, 64,  128, 64)    # Gold leaf trims & finials
R_STONE_TRIM        = (384, 64,  64,  64)    # Sills, lintels & steps
R_PAVEMENT          = (0,   0,   256, 64)    # Flagstone pavement
R_CORNICE_CHINESE   = (256, 0,   256, 64)    # Chinese dougong cornice

# --- Colors ---
RED_BRICK_BASE      = (0.52, 0.22, 0.16)
RED_BRICK_MORTAR    = (0.68, 0.65, 0.58)
STONE_BASE          = (0.76, 0.72, 0.62)
STONE_DARK          = (0.56, 0.52, 0.46)
EMERALD_ROOF_BASE   = (0.12, 0.36, 0.24)
EMERALD_DARK        = (0.07, 0.22, 0.14)
EMERALD_HILITE      = (0.20, 0.52, 0.36)
CHARCOAL_ROOF       = (0.18, 0.19, 0.22)
VERMILION_RED       = (0.72, 0.14, 0.10)
VERMILION_DARK      = (0.45, 0.08, 0.06)
IMPERIAL_GOLD       = (0.88, 0.72, 0.20)
GOLD_DARK           = (0.62, 0.48, 0.12)
STONE_CREAM         = (0.82, 0.78, 0.70)
GLASS_DARK          = (0.08, 0.11, 0.14)
GLASS_HIGHLIGHT     = (0.18, 0.24, 0.30)
LANTERN_RED         = (0.85, 0.12, 0.08)
LANTERN_GLOW        = (0.98, 0.32, 0.15)


def paint_east_york_victorian_02_atlas():
    a = Atlas(S, seed=555)

    # 1. Red Brick Facade
    x, y, w, h = R_BRICK_MAIN
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_BRICK_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)

    # 2. York Stone Plinth
    x, y, w, h = R_YORK_STONE
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y, y + h, 24):
        a.rect(x, my, w, 2, STONE_DARK)
    band_y = y + h - 28
    a.rect(x, band_y, w, 24, STONE_DARK)
    a.rect(x, band_y + 2, w, 20, STONE_BASE)
    for kx in range(x, x + w, 20):
        a.rect(kx + 2, band_y + 4, 16, 2, VERMILION_RED)
        a.rect(kx + 16, band_y + 4, 2, 12, VERMILION_RED)
        a.rect(kx + 6, band_y + 14, 12, 2, VERMILION_RED)
        a.rect(kx + 6, band_y + 8, 2, 8, VERMILION_RED)
    a.noise(x, y, w, h, 0.03)

    # 3. Emerald Roof Tiles
    x, y, w, h = R_EMERALD_ROOF
    a.rect(x, y, w, h, EMERALD_ROOF_BASE)
    tile_h, tile_w = 14, 16
    for ty in range(y, y + h, tile_h):
        a.rect(x, ty, w, 3, EMERALD_DARK)
        a.rect(x, min(y + h - 1, ty + 3), w, 2, EMERALD_HILITE)
        for tx in range(x, x + w, tile_w):
            a.rect(tx, ty, 3, tile_h, EMERALD_DARK)
            a.rect(tx + 3, ty + 3, tile_w - 5, tile_h - 5, EMERALD_ROOF_BASE)
    a.noise(x, y, w, h, 0.025)

    # 4. Charcoal Ridge
    x, y, w, h = R_CHARCOAL_ROOF
    a.rect(x, y, w, h, CHARCOAL_ROOF)
    for ty in range(y, y + h, 12):
        a.rect(x, ty, w, 2, (0.10, 0.10, 0.12))
    a.noise(x, y, w, h, 0.03)

    # 5. Turret Window Panel
    x, y, w, h = R_TURRET_PANEL
    a.rect(x, y, w, h, STONE_BASE)
    a.rect(x + 4, y + h - 14, w - 8, 12, STONE_CREAM)
    a.rect(x + 4, y + 2, w - 8, 10, STONE_CREAM)
    wx, wy, ww, wh = x + 8, y + 14, w - 16, h - 30
    a.rect(wx, wy, ww, wh, VERMILION_RED)
    gx, gy, gw, gh = wx + 4, wy + 4, ww - 8, wh - 8
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for ly in range(gy + 6, gy + gh - 2, 12):
        a.rect(gx, ly, gw, 2, VERMILION_RED)
    for lx in range(gx + 6, gx + gw - 2, 12):
        a.rect(lx, gy, 2, gh, VERMILION_RED)
    a.rect(gx + 3, gy + gh // 2 + 4, (gw // 2) - 6, (gh // 2) - 8, GLASS_HIGHLIGHT)

    # 6. Main Facade Lattice Window
    x, y, w, h = R_LATTICE_WIN
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.rect(x + 6, y + h - 16, w - 12, 14, STONE_CREAM)
    a.rect(x + 6, y + 2, w - 12, 10, STONE_CREAM)
    wx, wy, ww, wh = x + 10, y + 14, w - 20, h - 32
    a.rect(wx, wy, ww, wh, VERMILION_RED)
    gx, gy, gw, gh = wx + 4, wy + 4, ww - 8, wh - 8
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    for ly in range(gy + 8, gy + gh - 4, 14):
        a.rect(gx, ly, gw, 2, VERMILION_RED)
        a.rect(gx, ly + 1, gw, 1, IMPERIAL_GOLD)
    for lx in range(gx + 8, gx + gw - 4, 14):
        a.rect(lx, gy, 2, gh, VERMILION_RED)
        a.rect(lx + 1, gy, 1, gh, IMPERIAL_GOLD)
    a.rect(gx + 4, gy + gh // 2 + 4, (gw // 2) - 8, (gh // 2) - 10, GLASS_HIGHLIGHT)

    # 7. Vermilion Door
    x, y, w, h = R_DOOR_VERMILION
    a.rect(x, y, w, h, STONE_CREAM)
    dx, dy, dw, dh = x + 4, y, w - 8, h - 4
    a.rect(dx, dy, dw, dh, VERMILION_DARK)
    a.rect(dx + 3, dy + 2, dw - 6, dh - 4, VERMILION_RED)
    for cy in range(dy + 12, dy + dh - 20, 14):
        a.rect(dx + 5, cy, 4, 6, IMPERIAL_GOLD)
        a.rect(dx + dw - 9, cy, 4, 6, IMPERIAL_GOLD)
    knocker_y = dy + dh // 2 - 2
    a.rect(dx + dw // 2 - 5, knocker_y, 10, 10, IMPERIAL_GOLD)

    # 8. Lantern
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

    # 9. Vermilion Timber
    x, y, w, h = R_TIMBER_RED
    a.rect(x, y, w, h, VERMILION_RED)
    for ty in range(y, y + h, 16):
        a.rect(x, ty, w, 2, VERMILION_DARK)

    # 10. Gold Trim
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    for gy in range(y, y + h, 12):
        a.rect(x, gy, w, 2, GOLD_DARK)

    # 11. Stone Trim
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 14):
        a.rect(x, sy, w, 2, STONE_DARK)

    # 12. Pavement
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.50, 0.48, 0.44))
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.38, 0.36, 0.33))

    # 13. Cornice
    x, y, w, h = R_CORNICE_CHINESE
    a.rect(x, y, w, h, VERMILION_RED)
    a.rect(x, y + h - 8, w, 8, IMPERIAL_GOLD)
    a.rect(x, y, w, 6, IMPERIAL_GOLD)
    for cx in range(x, x + w, 16):
        a.rect(cx + 2, y + 8, 12, h - 16, VERMILION_DARK)
        a.rect(cx + 4, y + 10, 8, h - 20, IMPERIAL_GOLD)

    return a.to_image("building_east_york_victorian_02_atlas", OUT_DIR)


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

    img = paint_east_york_victorian_02_atlas()
    mat = material_for(img, "EastYorkVictorian02_Mat")

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
    register_box("FrontPavement", 7.0, 1.20, 0.10, (0.0, -4.10, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Main Building Body (Right Block: 4.6m x 7.0m, Z: 0.10 to 6.20)
    register_box("GroundFloorRight", 4.60, 7.0, 3.10, (1.20, 0.0, 0.10),
                 front=R_YORK_STONE, sides=R_BRICK_MAIN, back=R_BRICK_MAIN, top=R_STONE_TRIM)
    register_box("FirstFloorRight", 4.60, 7.0, 3.00, (1.20, 0.0, 3.20),
                 front=R_BRICK_MAIN, sides=R_BRICK_MAIN, back=R_BRICK_MAIN)

    # 3. Left Octagonal Corner Turret (3-Storey Pagoda Tower, X = -2.20m, Y = -2.20m)
    # Turret base & body
    turret_body = make_cylinder("TurretBody", r=1.55, h=7.20, segs=8, at=(-2.20, -2.20, 0.10))
    turret_body.data.materials.append(mat)
    kit.map_faces_to_region(turret_body, R_TURRET_PANEL, S)
    parts.append(turret_body)

    # Turret mid-level string cornice
    register_box("TurretCornice1", 3.30, 3.30, 0.20, (-2.20, -2.20, 3.20),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_EMERALD_ROOF)
    register_box("TurretCornice2", 3.30, 3.30, 0.25, (-2.20, -2.20, 7.30),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    # Turret Swept Pagoda Roof Cap
    turret_roof = make_swept_roof("TurretPagodaRoof", 3.80, 3.80, eaves_h=0.0, ridge_h=1.80, flare=0.55, at=(-2.20, -2.20, 7.55))
    turret_roof.data.materials.append(mat)
    kit.map_faces_to_region(turret_roof, R_EMERALD_ROOF, S)
    parts.append(turret_roof)

    # Turret Gold Flame Finial
    turret_finial = make_cylinder("TurretFinial", r=0.18, h=0.65, segs=8, at=(-2.20, -2.20, 9.35))
    turret_finial.data.materials.append(mat)
    kit.map_faces_to_region(turret_finial, R_GOLD_TRIM, S)
    parts.append(turret_finial)

    # 4. Right Entrance (X = +2.00m)
    register_box("DoorStep1", 1.35, 0.65, 0.15, (2.00, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep2", 1.25, 0.35, 0.15, (2.00, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("FrontDoor", 1.10, 0.20, 2.30, (2.00, -3.52, 0.40),
                 front=R_DOOR_VERMILION, sides=R_TIMBER_RED, top=R_TIMBER_RED)

    # Vermilion Portico Columns
    register_box("Portico_L", 0.14, 0.24, 2.45, (1.35, -3.54, 0.40),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    register_box("Portico_R", 0.14, 0.24, 2.45, (2.65, -3.54, 0.40),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    register_box("Portico_Lintel", 1.55, 0.32, 0.22, (2.00, -3.56, 2.85),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    # Hanging Red Silk Lantern
    register_box("LanternBracket", 0.06, 0.35, 0.06, (1.25, -3.65, 2.70),
                 front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    lantern = make_cylinder("Lantern", r=0.16, h=0.45, segs=8, at=(1.25, -3.80, 2.10))
    lantern.data.materials.append(mat)
    kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
    parts.append(lantern)

    # 5. Right Upper Windows (1st floor: X = +0.20m and X = +2.20m)
    for i, wx in enumerate([0.20, 2.20]):
        register_box(f"UpperWin_{i+1}", 1.25, 0.18, 1.70, (wx, -3.52, 3.90),
                     front=R_LATTICE_WIN, sides=R_TIMBER_RED, top=R_TIMBER_RED)
        register_box(f"UpperCanopy_{i+1}", 1.45, 0.30, 0.15, (wx, -3.58, 5.60),
                     front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_EMERALD_ROOF)

    # 6. Eaves Cornice & Dougong Brackets on Right Main Roof
    register_box("EavesCornice", 5.00, 7.30, 0.28, (1.20, -0.08, 6.20),
                 front=R_CORNICE_CHINESE, sides=R_TIMBER_RED, top=R_GOLD_TRIM)
    for bx in np.linspace(-0.8, 3.2, 5):
        register_box(f"Dougong_{bx:.1f}", 0.20, 0.30, 0.22, (bx, -3.62, 5.98),
                     front=R_TIMBER_RED, sides=R_TIMBER_RED, top=R_GOLD_TRIM)

    # 7. Swept Flying-Eaves Emerald Roof on Main Block
    roof = make_swept_roof("SweptEmeraldRoof", 5.40, 7.70, eaves_h=0.0, ridge_h=1.85, flare=0.55, at=(1.20, 0.0, 6.48))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_EMERALD_ROOF, S, only=lambda f: abs(f.normal.y) > 0.3 and f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_BRICK_MAIN, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_TIMBER_RED, S, only=lambda f: f.normal.z < -0.3)
    parts.append(roof)

    register_box("RoofRidge", 5.40, 0.30, 0.18, (1.20, 0, 8.33),
                 front=R_CHARCOAL_ROOF, sides=R_CHARCOAL_ROOF, top=R_GOLD_TRIM)
    for fx in [-1.50, 3.90]:
        register_box(f"DragonFinial_{fx:.1f}", 0.24, 0.34, 0.38, (fx, 0, 8.43),
                     front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # 8. Chimney Stack on Far Right
    register_box("ChimneyBase", 0.75, 1.40, 1.65, (3.20, 0.4, 7.30),
                 front=R_BRICK_MAIN, sides=R_BRICK_MAIN, top=R_STONE_TRIM)
    register_box("ChimneyCap", 0.90, 1.55, 0.16, (3.20, 0.4, 8.95),
                 front=R_CORNICE_CHINESE, sides=R_EMERALD_ROOF, top=R_GOLD_TRIM)
    for i, pot_y in enumerate([0.0, 0.80]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.13, h=0.45, segs=8, at=(3.20, pot_y, 9.11))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_GOLD_TRIM, S)
        parts.append(pot)

    # =========================================================================
    # Finalize & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_Victorian_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_victorian_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_victorian_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_east_york_victorian_02] generation complete.")


main()
