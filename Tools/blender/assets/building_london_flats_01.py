"""Victorian/Edwardian London Mansion Block (Flats Variant 1).

Architectural Specs:
- 4-storey classic London red-brick mansion block with white stone banding & rusticated stucco ground floor
- Central grand arched stone entrance with double glazed doors, brass push bars, and intercom buzzer board
- Symmetrical layout with 2 full-height 4-storey bay stacks (Left and Right)
- Upper floors with grand 2-over-2 sash windows, stone lintels, and decorative string courses
- Decorative classical roof parapet with stone urns/coping, pitched slate roof, and double brick chimneys
- Dimensions: 10.0m width x 7.5m depth x 12.0m total height. Modular 10m grid.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_london_flats_01.py
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
R_BRICK_RED     = (0,   256, 256, 256)   # Red brick facade with stone banding
R_SLATE_ROOF    = (0,   128, 256, 128)   # Welsh slate roof
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, quoins, steps
R_PAVEMENT      = (0,   0,   256, 64)    # Pavement flags
R_BRICK_DARK    = (256, 256, 128, 256)   # Side party wall & chimney brick
R_STUCCO        = (256, 128, 128, 128)   # Ground floor rusticated stucco
R_CORNICE       = (256, 64,  128, 64)    # Modillion cornice
R_ROOF_CAP      = (256, 0,   128, 64)    # Bay roof lead/slate
R_SASH_UPPER    = (384, 384, 128, 128)   # Upper floor 2-over-2 sash window
R_BAY_WINDOW    = (384, 256, 128, 128)   # Bay window sash panel
R_DOOR_COMMUNAL = (448, 128, 64,  128)   # Grand communal double doors + intercom
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Clay chimney pot
R_BALCONY_TRIM  = (448, 0,   64,  128)   # Cast iron balcony detail

# --- Colors ---
RED_BRICK_BASE   = (0.52, 0.22, 0.16)
RED_MORTAR       = (0.70, 0.67, 0.62)
DARK_BRICK_BASE  = (0.38, 0.20, 0.16)
STUCCO_BASE      = (0.80, 0.77, 0.70)
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
DOOR_OAK         = (0.35, 0.18, 0.10)
DOOR_DARK        = (0.20, 0.10, 0.05)
BRASS_GOLD       = (0.86, 0.73, 0.24)
TERRACOTTA       = (0.70, 0.34, 0.18)
SOOT_BLACK       = (0.14, 0.14, 0.14)
LEAD_GREY        = (0.32, 0.33, 0.36)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_mansion_atlas():
    a = Atlas(S, seed=201)

    # 1. Red Brick Facade with Horizontal Stone Bands (R_BRICK_RED)
    x, y, w, h = R_BRICK_RED
    a.bricks(x, y, w, h, brick=RED_BRICK_BASE, mortar=RED_MORTAR, bw=24, bh=10, jitter=0.08)
    # Horizontal stone courses between brick storeys
    for by in [y + 60, y + 120, y + 180]:
        a.rect(x, by, w, 6, STONE_CREAM)
        a.rect(x, by, w, 1, STONE_DARK)
        a.rect(x, by + 5, w, 1, (0.90, 0.88, 0.82))
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.05, bottom=0.0)

    # 2. Side Brick (R_BRICK_DARK)
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

    # 4. Ground Floor Rusticated Stucco (R_STUCCO)
    x, y, w, h = R_STUCCO
    a.rect(x, y, w, h, STUCCO_BASE)
    for gy in range(y, y + h, 18):
        a.rect(x, gy, w, 2, STUCCO_GROOVE)
        a.rect(x, gy + 2, w, 1, (0.90, 0.88, 0.82))
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.03)

    # 5. Upper Sash Window (R_SASH_UPPER)
    x, y, w, h = R_SASH_UPPER
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

    # 6. Bay Window Panel (R_BAY_WINDOW)
    x, y, w, h = R_BAY_WINDOW
    a.rect(x, y, w, h, RED_BRICK_BASE)
    a.rect(x, y + h - 14, w, 14, STONE_CREAM)
    a.rect(x, y + h - 14, w, 2, STONE_DARK)
    a.rect(x, y, w, 14, STONE_CREAM)
    bx, by, bw, bh = x + 10, y + 14, w - 20, h - 28
    a.rect(bx, by, bw, bh, TIMBER_WHITE)
    bgx, bgy, bgw, bgh = bx + 5, by + 5, bw - 10, bh - 10
    a.rect(bgx, bgy, bgw, bgh, GLASS_DARK)
    a.rect(bgx, bgy + bgh // 2 - 2, bgw, 5, TIMBER_WHITE)
    a.rect(bgx + bgw // 2 - 2, bgy, 4, bgh, TIMBER_WHITE)
    a.rect(bgx + 4, bgy + bgh // 2 + 6, (bgw // 2) - 8, (bgh // 2) - 12, GLASS_HIGHLIGHT)

    # 7. Grand Communal Entrance Doors + Intercom (R_DOOR_COMMUNAL)
    x, y, w, h = R_DOOR_COMMUNAL
    a.rect(x, y, w, h, STONE_CREAM)  # Arched stone surround
    dx, dy, dw, dh = x + 4, y, w - 8, h - 6
    a.rect(dx, dy, dw, dh, TIMBER_WHITE)
    # Semicircular fanlight
    fl_y = dy + dh - 28
    a.rect(dx + 4, fl_y, dw - 8, 24, GLASS_DARK)
    a.rect(dx + dw // 2 - 1, fl_y, 2, 24, TIMBER_WHITE)
    a.rect(dx + 6, fl_y + 4, (dw - 12) // 2, 16, GLASS_HIGHLIGHT)
    door_top = fl_y - 4
    door_h = door_top - dy
    # Oak double doors
    a.rect(dx + 2, dy + 2, dw - 4, door_h - 2, DOOR_OAK)
    # Door split
    mid_dx = dx + dw // 2
    a.rect(mid_dx - 1, dy + 2, 2, door_h - 2, DOOR_DARK)
    # Glass vision panels in upper half of both doors
    gw_d = (dw - 12) // 2
    gh_d = door_h // 2 - 8
    gy_d = dy + door_h // 2 + 4
    a.rect(dx + 4, gy_d, gw_d, gh_d, GLASS_DARK)
    a.rect(mid_dx + 2, gy_d, gw_d, gh_d, GLASS_DARK)
    # Brass push bars & kickplates
    a.rect(dx + 4, dy + 4, dw - 8, 6, BRASS_GOLD)
    a.rect(dx + 6, dy + door_h // 2 - 2, dw - 12, 4, BRASS_GOLD)
    # Intercom panel beside door
    a.rect(x + 1, dy + door_h // 2 - 6, 3, 14, (0.75, 0.75, 0.78))
    for iy in range(dy + door_h // 2 - 4, dy + door_h // 2 + 6, 3):
        a.rect(x + 2, iy, 1, 1, BRASS_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 8. Stone Trims
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 9. Lead/Slate Roof Cap
    x, y, w, h = R_ROOF_CAP
    a.rect(x, y, w, h, LEAD_GREY)
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.22, 0.23, 0.25))
        a.rect(lx + 3, y, 1, h, (0.45, 0.46, 0.49))
    a.noise(x, y, w, h, 0.025)

    # 10. Chimney Pot
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    a.rect(x, y + h - 12, w, 12, (0.76, 0.40, 0.22))
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 11. Pavement
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 12. Cornice
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    for dx in range(x, x + w, 16):
        a.rect(dx, y + 8, 8, 16, STONE_DARK)
        a.rect(dx + 1, y + 10, 6, 12, (0.88, 0.85, 0.78))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.92, 0.90, 0.84))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_london_flats_01_atlas", kit.OUT_DIR)


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
    img = paint_mansion_atlas()
    mat = material_for(img, "mat_london_flats_01")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # 4-Storey Mansion Block (Width: 10.0m, Depth: 7.5m, Total Height: ~12.0m)
    # =========================================================================

    # 1. Pavement
    register_box("Pavement", 10.0, 8.5, 0.10, (0, -0.5, 0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_PAVEMENT)

    # 2. Ground Floor Stucco (Z: 0.10 to 3.00, H: 2.90m)
    register_box("GroundFloor", 10.0, 7.5, 2.90, (0, 0, 0.10),
                 front=R_STUCCO, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 3. Central Grand Communal Entrance (X = 0.0m)
    register_box("EntranceSteps", 2.60, 0.70, 0.20, (0.0, -4.10, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("EntrancePortico", 2.20, 0.35, 2.80, (0.0, -3.75, 0.30),
                 front=R_DOOR_COMMUNAL, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 4. Ground Floor Windows flanking entrance (Left X = -3.20m, Right X = +3.20m)
    register_box("GroundWinL", 1.50, 0.25, 1.80, (-3.20, -3.75, 0.75),
                 front=R_BAY_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("GroundWinR", 1.50, 0.25, 1.80, (3.20, -3.75, 0.75),
                 front=R_BAY_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. String Course
    register_box("MidCornice", 10.0, 7.62, 0.20, (0, -0.04, 3.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Upper Floors Red Brick Main Body (Storeys 2, 3, 4: Z: 3.20 to 10.00, H: 6.80m)
    register_box("UpperFloors", 10.0, 7.5, 6.80, (0, 0, 3.20),
                 front=R_BRICK_RED, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 7. Upper Floor Bay Columns / Windows
    # Level 2 (Z = 3.60m)
    register_box("L2_WinL", 1.40, 0.20, 1.70, (-3.20, -3.75, 3.60), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L2_WinM", 1.20, 0.20, 1.70, (0.0, -3.75, 3.60), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L2_WinR", 1.40, 0.20, 1.70, (3.20, -3.75, 3.60), front=R_SASH_UPPER, sides=R_STONE_TRIM)

    # Level 3 (Z = 5.80m)
    register_box("L3_WinL", 1.40, 0.20, 1.70, (-3.20, -3.75, 5.80), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L3_WinM", 1.20, 0.20, 1.70, (0.0, -3.75, 5.80), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L3_WinR", 1.40, 0.20, 1.70, (3.20, -3.75, 5.80), front=R_SASH_UPPER, sides=R_STONE_TRIM)

    # Level 4 (Z = 8.00m)
    register_box("L4_WinL", 1.40, 0.20, 1.60, (-3.20, -3.75, 8.00), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L4_WinM", 1.20, 0.20, 1.60, (0.0, -3.75, 8.00), front=R_SASH_UPPER, sides=R_STONE_TRIM)
    register_box("L4_WinR", 1.40, 0.20, 1.60, (3.20, -3.75, 8.00), front=R_SASH_UPPER, sides=R_STONE_TRIM)

    # 8. Top Eaves Cornice & Parapet (Z: 10.00 to 10.60m)
    register_box("EavesCornice", 10.0, 7.66, 0.30, (0, -0.06, 10.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("ParapetWall", 10.0, 7.50, 0.35, (0, 0, 10.30),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Pitched Slate Roof (H: 1.40m, Z: 10.30 to 11.70m)
    roof = make_pitched_roof("PitchedRoof", 10.0, 7.50, 1.40, at=(0, 0, 10.30))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: f.normal.z > 0.1 and abs(f.normal.x) < 0.5)
    kit.map_faces_to_region(roof, R_BRICK_DARK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    register_box("RoofRidge", 10.0, 0.25, 0.12, (0, 0, 11.66),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Twin Party-Wall Chimneys (Left X = -4.50m, Right X = +4.50m)
    for cx in [-4.50, 4.50]:
        register_box(f"ChimneyBase_{cx}", 0.75, 1.20, 1.60, (cx, 0.5, 10.80),
                     front=R_BRICK_DARK, sides=R_BRICK_DARK, top=R_STONE_TRIM)
        register_box(f"ChimneyCap_{cx}", 0.85, 1.30, 0.14, (cx, 0.5, 12.40),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        for i, pot_y in enumerate([0.20, 0.80]):
            pot = make_cylinder(f"ChimneyPot_{cx}_{i}", r=0.13, h=0.50, segs=8, at=(cx, pot_y, 12.54))
            pot.data.materials.append(mat)
            kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
            parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_London_Flats_01")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_london_flats_01_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_london_flats_01.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_london_flats_01] generation complete.")


main()
