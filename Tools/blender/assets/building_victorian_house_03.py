"""Victorian London Terraced House (Variant 3 — Weathered Dark Brick & Portico Entrance).

Architectural Specs:
- Weathered dark brown/charcoal London brick facade with decorative corner stone quoins
- Ground floor classical stone portico entrance canopy with triangular pediment
- Gloss British Racing Green 4-panel front door with brass knocker and arched fanlight
- 3 tall upper sash windows with moulded stone architraves & pediments
- 2 ground floor sash windows to the left of the entrance
- Welsh blue-slate pitched roof with left party-wall chimney stack and 3 terracotta pots
- Designed to tile seamlessly on a 5.0m grid (width: 5.0m, depth: 7.0m, origin at bottom-centre).

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_victorian_house_03.py
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

# --- Atlas Regions (x, y, w, h) ---
R_BRICK_DARK    = (0,   256, 256, 256)   # Weathered dark brown London brick facade
R_BRICK_SIDE    = (256, 256, 128, 256)   # Side party wall brick
R_SLATE_ROOF    = (0,   128, 256, 128)   # Welsh blue-slate roof tiles
R_STUCCO_PLINTH = (256, 128, 128, 128)   # Lower plinth stucco
R_SASH_WINDOW   = (384, 384, 128, 128)   # Victorian 2-over-2 sash with pediment lintel
R_QUOINS        = (384, 256, 128, 128)   # Corner stone quoins block texture
R_DOOR_GREEN    = (448, 128, 64,  128)   # British Racing Green Victorian door + fanlight
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, coping, portico stone
R_PORTICO_ROOF  = (256, 64,  128, 64)    # Portico pediment lead/slate flashing
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Terracotta clay pot with soot
R_PAVEMENT      = (0,   0,   256, 64)    # Pavement flags
R_CORNICE       = (256, 0,   256, 64)    # Modillion eaves cornice

# --- Color Palette ---
DARK_BRICK_BASE  = (0.36, 0.28, 0.24)
DARK_MORTAR      = (0.68, 0.65, 0.60)
SIDE_BRICK_BASE  = (0.30, 0.24, 0.20)
PLINTH_BASE      = (0.50, 0.48, 0.45)
SLATE_BASE       = (0.22, 0.25, 0.30)
SLATE_DARK       = (0.15, 0.17, 0.20)
SLATE_HIGHLIGHT  = (0.32, 0.36, 0.42)
STONE_CREAM      = (0.82, 0.79, 0.72)
STONE_DARK       = (0.58, 0.55, 0.48)
TIMBER_WHITE     = (0.94, 0.94, 0.92)
TIMBER_FRAME     = (0.84, 0.84, 0.82)
GLASS_DARK       = (0.08, 0.11, 0.15)
GLASS_HIGHLIGHT  = (0.18, 0.24, 0.32)
DOOR_GREEN       = (0.05, 0.28, 0.12)
DOOR_DARK        = (0.02, 0.14, 0.06)
BRASS_GOLD       = (0.86, 0.73, 0.24)
TERRACOTTA       = (0.72, 0.36, 0.20)
SOOT_BLACK       = (0.14, 0.14, 0.14)
LEAD_GREY        = (0.34, 0.35, 0.38)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_victorian_03_atlas():
    a = Atlas(S, seed=103)

    # 1. Dark Brown London Brick Facade (R_BRICK_DARK)
    x, y, w, h = R_BRICK_DARK
    a.bricks(x, y, w, h, brick=DARK_BRICK_BASE, mortar=DARK_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.05, bottom=0.0)

    # 2. Side Brick (R_BRICK_SIDE)
    x, y, w, h = R_BRICK_SIDE
    a.bricks(x, y, w, h, brick=SIDE_BRICK_BASE, mortar=(0.55, 0.52, 0.48), bw=24, bh=10, jitter=0.08)
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

    # 4. Lower Stucco Plinth (R_STUCCO_PLINTH)
    x, y, w, h = R_STUCCO_PLINTH
    a.rect(x, y, w, h, PLINTH_BASE)
    for gy in range(y, y + h, 20):
        a.rect(x, gy, w, 2, (0.38, 0.36, 0.34))
    a.shade(x, y, w, h, top=0.0, bottom=-0.14)
    a.noise(x, y, w, h, 0.03)

    # 5. Sash Window with Triangular Pediment (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, DARK_BRICK_BASE)
    a.noise(x, y, w, h, 0.03)
    # Triangular pediment / lintel
    a.rect(x + 8, y + h - 22, w - 16, 20, STONE_CREAM)
    a.rect(x + 8, y + h - 22, w - 16, 2, STONE_DARK)
    # Sill
    a.rect(x + 6, y + 4, w - 12, 12, STONE_CREAM)
    a.rect(x + 6, y + 4, w - 12, 2, STONE_DARK)
    # Window Frame & Glass
    wx, wy, ww, wh = x + 14, y + 16, w - 28, h - 38
    a.rect(wx, wy, ww, wh, TIMBER_FRAME)
    gx, gy, gw, gh = wx + 5, wy + 5, ww - 10, wh - 10
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    mid_y = gy + gh // 2
    a.rect(gx, mid_y - 3, gw, 6, TIMBER_WHITE)
    mid_x = gx + gw // 2
    a.rect(mid_x - 2, gy, 4, gh, TIMBER_WHITE)
    a.rect(gx + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)
    a.rect(mid_x + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)

    # 6. Stone Quoins (R_QUOINS)
    x, y, w, h = R_QUOINS
    a.rect(x, y, w, h, STONE_CREAM)
    for qy in range(y, y + h, 32):
        a.rect(x, qy, w, 2, STONE_DARK)
        a.rect(x, qy + 2, w, 1, (0.92, 0.89, 0.82))
        a.rect(x, qy + 16, w // 2, 16, (0.78, 0.75, 0.68))
    a.noise(x, y, w, h, 0.03)

    # 7. British Racing Green Front Door (R_DOOR_GREEN)
    x, y, w, h = R_DOOR_GREEN
    a.rect(x, y, w, h, STONE_CREAM)
    dx, dy, dw, dh = x + 4, y, w - 8, h - 6
    a.rect(dx, dy, dw, dh, TIMBER_WHITE)
    fl_y = dy + dh - 26
    a.rect(dx + 4, fl_y, dw - 8, 22, GLASS_DARK)
    a.rect(dx + dw // 2 - 1, fl_y, 2, 22, TIMBER_WHITE)
    a.rect(dx + 6, fl_y + 4, (dw - 12) // 2, 14, GLASS_HIGHLIGHT)
    door_top = fl_y - 4
    door_h = door_top - dy
    a.rect(dx + 3, dy + 2, dw - 6, door_h - 2, DOOR_GREEN)
    pw = (dw - 18) // 2
    ph_top = (door_h - 28) // 2
    ph_bot = (door_h - 28) // 2
    # Panels
    p_uy = dy + door_h - ph_top - 8
    a.rect(dx + 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + 7, p_uy + 1, pw - 2, ph_top - 2, DOOR_GREEN)
    a.rect(dx + dw - pw - 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_uy + 1, pw - 2, ph_top - 2, DOOR_GREEN)
    p_ly = dy + 8
    a.rect(dx + 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + 7, p_ly + 1, pw - 2, ph_bot - 2, DOOR_GREEN)
    a.rect(dx + dw - pw - 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_ly + 1, pw - 2, ph_bot - 2, DOOR_GREEN)
    # Brass fixtures
    a.rect(dx + dw // 2 - 2, p_uy + ph_top // 2 - 2, 4, 8, BRASS_GOLD)
    a.rect(dx + dw // 2 - 2, dy + door_h // 2 - 2, 4, 4, BRASS_GOLD)
    a.rect(dx + dw // 2 - 8, dy + door_h // 2 - 12, 16, 4, BRASS_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 8. Stone Trims (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 9. Portico Roof Flashing (R_PORTICO_ROOF)
    x, y, w, h = R_PORTICO_ROOF
    a.rect(x, y, w, h, LEAD_GREY)
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.24, 0.25, 0.27))
        a.rect(lx + 3, y, 1, h, (0.46, 0.47, 0.50))
    a.noise(x, y, w, h, 0.025)

    # 10. Chimney Pot (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    a.rect(x, y + h - 12, w, 12, (0.78, 0.42, 0.24))
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 11. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 12. Cornice (R_CORNICE)
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    for dx in range(x, x + w, 14):
        a.rect(dx, y + 8, 7, 16, STONE_DARK)
        a.rect(dx + 1, y + 10, 5, 12, (0.90, 0.87, 0.80))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.94, 0.92, 0.86))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_victorian_house_03_atlas", kit.OUT_DIR)


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
    img = paint_victorian_03_atlas()
    mat = material_for(img, "mat_victorian_house_03")

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

    # 2. Lower Plinth (Z: 0.10 to 0.60)
    register_box("Plinth", 5.0, 7.0, 0.50, (0, 0, 0.10),
                 front=R_STUCCO_PLINTH, sides=R_BRICK_SIDE, back=R_BRICK_SIDE)

    # 3. Main Dark Brick Facade (Z: 0.60 to 5.90, H: 5.30m)
    register_box("MainFacade", 5.0, 7.0, 5.30, (0, 0, 0.60),
                 front=R_BRICK_DARK, sides=R_BRICK_SIDE, back=R_BRICK_SIDE)

    # 4. Corner Stone Quoins (Left and Right edges of facade)
    register_box("QuoinsL", 0.40, 0.12, 5.30, (-2.30, -3.51, 0.60),
                 front=R_QUOINS, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("QuoinsR", 0.40, 0.12, 5.30, (2.30, -3.51, 0.60),
                 front=R_QUOINS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Front Entrance: Green Door + Classical Portico Canopy (Right side: X = +1.15m)
    # Entrance Steps
    register_box("DoorStep1", 1.40, 0.70, 0.15, (1.15, -3.85, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep2", 1.30, 0.40, 0.15, (1.15, -3.55, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # Door Slab
    register_box("FrontDoor", 1.05, 0.20, 2.25, (1.15, -3.52, 0.40),
                 front=R_DOOR_GREEN, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # Portico Pillared Canopy (Porch canopy projecting over door)
    register_box("PorticoPillars", 1.36, 0.55, 0.15, (1.15, -3.75, 2.65),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("PorticoPediment", 1.44, 0.60, 0.35, (1.15, -3.75, 2.80),
                 front=R_PORTICO_ROOF, sides=R_STONE_TRIM, top=R_PORTICO_ROOF)

    # 6. Ground Floor Windows (2 Windows on Left: X = -1.45m and X = -0.25m)
    register_box("GroundWindowL", 1.05, 0.16, 1.70, (-1.45, -3.50, 0.85),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("GroundWindowM", 1.05, 0.16, 1.70, (-0.25, -3.50, 0.85),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 7. First Floor 3 Sash Windows (X = -1.45m, -0.25m, +1.15m)
    register_box("UpperWindowL", 1.05, 0.16, 1.65, (-1.45, -3.50, 3.65),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWindowM", 1.05, 0.16, 1.65, (-0.25, -3.50, 3.65),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("UpperWindowR", 1.05, 0.16, 1.65, (1.15, -3.50, 3.65),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Eaves Cornice Band
    register_box("EavesCornice", 5.0, 7.16, 0.25, (0, -0.06, 5.90),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Pitched Slate Roof
    roof = make_pitched_roof("PitchedRoof", 5.0, 7.10, 1.60, at=(0, 0, 6.15))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z > 0.2)
    kit.map_faces_to_region(roof, R_BRICK_SIDE, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    register_box("RoofRidge", 5.0, 0.22, 0.12, (0, 0, 7.72),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Left Party-Wall Chimney Stack (X = -2.05m, Y = 0.5m) with 3 Pots
    register_box("ChimneyBase", 0.75, 1.50, 1.80, (-2.05, 0.5, 6.70),
                 front=R_BRICK_SIDE, sides=R_BRICK_SIDE, top=R_STONE_TRIM)
    register_box("ChimneyCap", 0.85, 1.60, 0.14, (-2.05, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    for i, pot_y in enumerate([0.05, 0.50, 0.95]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.13, h=0.55, segs=8, at=(-2.05, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Victorian_House_03")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_victorian_house_03_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_victorian_house_03.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_victorian_house_03] generation complete.")


main()
