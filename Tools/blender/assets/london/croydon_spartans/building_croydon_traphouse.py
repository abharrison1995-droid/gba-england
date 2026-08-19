"""Croydon Spartan Traphouse (8.0m x 7.5m Dilapidated Urban Property).

Specs:
- 8.0m x 7.5m footprint, Height: 7.8m.
- Grimy, soot-weathered London brick traphouse:
  - Peeling masonry paint, moisture streaks, and spray-painted urban graffiti ("101", "TRAP", "SPARTAN").
  - Ground floor windows boarded with weathered OSB timber plywood and steel mesh security grilles.
  - Smashed 1st floor sash window patched with cardboard and silver duct-tape.
  - Reinforced heavy security steel front door with multiple deadbolts.
  - Rusted Sky satellite dish on facade, broken brick garden wall, discarded car tyre, and weathered slate roof.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_croydon_traphouse.py
"""

import math
import shutil
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "london" / "croydon_spartans"
TOOLS_OUT_DIR = Path(__file__).resolve().parents[4] / "out" / "london" / "croydon_spartans"

# --- Atlas Region Definitions (x, y, w, h) ---
R_GRIMY_BRICK   = (0,   256, 256, 256)   # Grimy soot-stained brick & weathering stains
R_BOARDED_WIN   = (256, 256, 128, 256)   # OSB plywood boarded window with steel security grille
R_BROKEN_SASH   = (0,   128, 256, 128)   # Broken 1st floor sash with cardboard & duct-tape
R_STEEL_DOOR    = (256, 128, 128, 128)   # Heavy security door with padlocks & metal reinforcement
R_ROOF_WEATHERED= (0,   0,   256, 128)   # Grimy slate roof with missing tiles & moss
R_STONE_COPING  = (256, 0,   128, 128)   # Cracked weathered stone coping & garden wall
R_SATELLITE_DISH= (384, 384, 128, 128)   # Rusted mini satellite dish
R_RUBBISH_YARD  = (384, 256, 128, 128)   # Discarded car tyre & fly-tipped rubbish
R_CHIMNEY_STAIN = (384, 128, 128, 128)   # Stained brick chimney stack
R_TIMBER_FENCE  = (384, 0,   128, 128)   # Broken rotting timber fence panel

# --- Palette Colors ---
BRICK_GRIMY     = (0.42, 0.36, 0.28)
BRICK_MORTAR    = (0.52, 0.48, 0.42)
OSB_TIMBER      = (0.68, 0.52, 0.32)
STEEL_RUST      = (0.35, 0.22, 0.16)
DUCT_TAPE       = (0.75, 0.76, 0.78)
GLASS_CRACKED   = (0.24, 0.28, 0.30)
SLATE_DARK      = (0.22, 0.24, 0.26)
MOSS_GREEN      = (0.28, 0.38, 0.20)
TYRE_BLACK      = (0.12, 0.12, 0.14)


def paint_traphouse_atlas():
    a = Atlas(S, seed=2101)

    # 1. Grimy Brick Wall (R_GRIMY_BRICK) - Clean of graffiti
    x, y, w, h = R_GRIMY_BRICK
    a.bricks(x, y, w, h, brick=BRICK_GRIMY, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.09)
    # Soot & water drainage stains
    a.shade(x, y, w, h, top=-0.05, bottom=-0.18)
    # Moss near ground
    for mx in range(x, x + w, 16):
        a.disc(mx, y + 8, 12, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 2. OSB Boarded Windows with Security Grille (R_BOARDED_WIN)
    x, y, w, h = R_BOARDED_WIN
    a.rect(x, y, w, h, (0.30, 0.28, 0.25))  # Stone frame
    bx, by, bw, bh = x + 8, y + 8, w - 16, h - 16
    a.rect(bx, by, bw, bh, OSB_TIMBER)
    # Plywood horizontal seams & wood grain
    for py in range(by, by + bh, 24):
        a.rect(bx, py, bw, 2, (0.50, 0.38, 0.22))
    # Screw fixings
    for sy in [by + 10, by + bh - 10]:
        for sx in [bx + 8, bx + bw - 8]:
            a.disc(sx, sy, 3, (0.15, 0.15, 0.15))
    # Steel mesh security grille overlay
    for gy in range(by, by + bh, 14):
        a.rect(bx, gy, bw, 2, STEEL_RUST)
    for gx in range(bx, bx + bw, 14):
        a.rect(gx, by, 2, bh, STEEL_RUST)
    a.noise(x, y, w, h, 0.035)

    # 3. Broken 1st Floor Sash with Cardboard Patch (R_BROKEN_SASH)
    x, y, w, h = R_BROKEN_SASH
    a.rect(x, y, w, h, (0.70, 0.68, 0.62))  # Peeling white sash frame
    wx, wy, ww, wh = x + 10, y + 8, w - 20, h - 16
    a.rect(wx, wy, ww, wh, GLASS_CRACKED)
    # Sash meeting rail
    a.rect(wx, wy + wh // 2, ww, 4, (0.50, 0.48, 0.44))
    # Cardboard patched lower pane
    a.rect(wx + 4, wy + 4, ww // 2 - 6, wh // 2 - 8, (0.55, 0.42, 0.28))
    # Silver duct-tape criss-cross
    a.rect(wx + 2, wy + 16, ww // 2, 4, DUCT_TAPE)
    a.rect(wx + 16, wy + 4, 4, wh // 2, DUCT_TAPE)
    # Shatter crack lines on top pane
    a.rect(wx + ww // 2, wy + wh // 2 + 10, ww // 2 - 10, 2, (0.85, 0.90, 0.92))
    a.noise(x, y, w, h, 0.03)

    # 4. Heavy Steel Security Door (R_STEEL_DOOR)
    x, y, w, h = R_STEEL_DOOR
    a.rect(x, y, w, h, (0.35, 0.32, 0.30))  # Frame
    dx, dy, dw, dh = x + 6, y + 6, w - 12, h - 12
    a.rect(dx, dy, dw, dh, (0.24, 0.22, 0.22))  # Steel door sheet
    # Rust patches
    a.disc(dx + 20, dy + 30, 14, STEEL_RUST)
    a.disc(dx + dw - 24, dy + 80, 18, STEEL_RUST)
    # Multiple heavy deadbolts & padlocks
    for ly in [dy + 40, dy + 65, dy + 90]:
        a.rect(dx + dw - 18, ly, 12, 10, (0.80, 0.70, 0.20))
    # Metal kickplate
    a.rect(dx + 4, dy + 4, dw - 8, 24, STEEL_RUST)
    a.noise(x, y, w, h, 0.03)

    # 5. Weathered Slate Roof (R_ROOF_WEATHERED)
    x, y, w, h = R_ROOF_WEATHERED
    a.rect(x, y, w, h, SLATE_DARK)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.14, 0.15, 0.16))
    # Patches of green roof moss
    for _ in range(6):
        rx = x + int(a.rng.uniform(10, w - 30))
        ry = y + int(a.rng.uniform(10, h - 30))
        a.disc(rx, ry, 12, MOSS_GREEN)
    a.noise(x, y, w, h, 0.045)

    # 6. Stone Coping (R_STONE_COPING)
    x, y, w, h = R_STONE_COPING
    a.rect(x, y, w, h, (0.58, 0.55, 0.50))
    for cy in range(y, y + h, 20):
        a.rect(x, cy, w, 2, (0.35, 0.32, 0.28))
    a.noise(x, y, w, h, 0.035)

    # 7. Satellite Dish (R_SATELLITE_DISH)
    x, y, w, h = R_SATELLITE_DISH
    a.rect(x, y, w, h, BRICK_GRIMY)
    a.disc(x + w // 2, y + h // 2, 36, (0.18, 0.18, 0.20))
    a.disc(x + w // 2, y + h // 2, 30, (0.75, 0.75, 0.78))
    a.disc(x + w // 2 - 6, y + h // 2 + 6, 14, STEEL_RUST)  # rust
    # LNB arm
    a.rect(x + w // 2 - 2, y + h // 2 - 28, 4, 28, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.02)

    # 8. Rubbish & Car Tyre (R_RUBBISH_YARD)
    x, y, w, h = R_RUBBISH_YARD
    a.rect(x, y, w, h, (0.35, 0.32, 0.28))
    # Black rubber tyre
    a.disc(x + w // 2, y + h // 2, 34, TYRE_BLACK)
    a.disc(x + w // 2, y + h // 2, 16, (0.35, 0.32, 0.28))
    # Crushed beer cans
    a.rect(x + 14, y + 16, 12, 18, (0.85, 0.15, 0.12))
    a.rect(x + w - 28, y + 18, 14, 16, (0.20, 0.40, 0.85))
    a.noise(x, y, w, h, 0.035)

    # 9. Chimney (R_CHIMNEY_STAIN)
    x, y, w, h = R_CHIMNEY_STAIN
    a.bricks(x, y, w, h, brick=(0.40, 0.32, 0.24), mortar=(0.48, 0.44, 0.38), bw=18, bh=9)
    a.shade(x, y, w, h, top=-0.15, bottom=0.0)
    a.noise(x, y, w, h, 0.035)

    # 10. Timber Fence (R_TIMBER_FENCE)
    x, y, w, h = R_TIMBER_FENCE
    a.rect(x, y, w, h, (0.38, 0.28, 0.18))
    for fx in range(x, x + w, 18):
        a.rect(fx, y, 2, h, (0.22, 0.16, 0.10))
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_croydon_traphouse_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_COPING, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_COPING, S, only=side("bottom"))


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (-hw, 0.0, h), (hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front slope
        (2, 3, 4, 5),    # back slope
        (0, 4, 3),       # left gable
        (1, 2, 5),       # right gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_traphouse_atlas()
    mat = material_for(img, "mat_croydon_traphouse")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Croydon Spartan Traphouse (8.0m x 7.5m Footprint)
    # - 2 Storeys with Weathered Slate Pitched Roof & Stained Chimney
    # - Boarded Ground Floor Windows with Steel Security Grilles
    # - Heavy Reinforced Security Door with Multiple Locks
    # - Smashed 1st Floor Sash Window with Cardboard & Duct-Tape
    # - Facade Satellite Dish, Broken Low Front Garden Wall & Yard Debris
    # =========================================================================

    # 1. Front Yard & Cracked Concrete Base (8.0m x 8.0m, Z = 0.00 to 0.12m)
    register_box("YardBase", 8.0, 8.00, 0.12, (0.0, -0.25, 0.0),
                 front=R_RUBBISH_YARD, sides=R_RUBBISH_YARD, top=R_RUBBISH_YARD)

    # 2. Main Traphouse Body (8.0m x 6.5m, Z: 0.12 to 5.80m, H: 5.68m)
    register_box("HouseBody", 8.0, 6.50, 5.68, (0.0, 0.50, 0.12),
                 front=R_GRIMY_BRICK, sides=R_GRIMY_BRICK, back=R_GRIMY_BRICK)

    # 3. Ground Floor Boarded Window (Left: X = -2.20m, Z = 0.80m to 2.80m)
    register_box("BoardedWinGround", 2.20, 0.18, 2.00, (-2.20, -2.82, 0.80),
                 front=R_BOARDED_WIN, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 4. Heavy Steel Security Front Door (Right: X = 1.80m, Z = 0.12 to 2.80m)
    register_box("TrapDoor", 1.80, 0.18, 2.68, (1.80, -2.82, 0.12),
                 front=R_STEEL_DOOR, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 5. 1st Floor Smashed & Patched Sash Windows (Left X = -2.20m, Right X = 1.80m)
    register_box("BrokenSashLeft", 1.80, 0.15, 1.80, (-2.20, -2.80, 3.40),
                 front=R_BROKEN_SASH, sides=R_STONE_COPING, top=R_STONE_COPING)
    register_box("BrokenSashRight", 1.80, 0.15, 1.80, (1.80, -2.80, 3.40),
                 front=R_BROKEN_SASH, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 6. Satellite Dish Mounted on 1st Floor Facade (X = 0.0m, Z = 3.60m)
    register_box("SatelliteDish", 0.70, 0.25, 0.70, (0.0, -2.85, 3.60),
                 front=R_SATELLITE_DISH, sides=R_SATELLITE_DISH, top=R_STONE_COPING)

    # 7. Weathered Pitched Slate Roof (Ridge along X, W: 8.40m, D: 6.90m, H: 2.00m at Z = 5.80m)
    roof = make_pitched_roof("TrapRoof", 8.40, 6.90, 2.00, at=(0.0, 0.50, 5.80))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_WEATHERED, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_CHIMNEY_STAIN, S, only=lambda f: abs(f.normal.x) > 0.6)
    kit.map_faces_to_region(roof, R_STONE_COPING, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    # 8. Stained Brick Chimney Stack (Left: X = -3.20m, Z = 5.80m to 8.20m)
    register_box("TrapChimney", 0.90, 1.10, 2.40, (-3.20, 0.50, 5.80),
                 front=R_CHIMNEY_STAIN, sides=R_CHIMNEY_STAIN, top=R_STONE_COPING)

    # 9. Low Broken Front Garden Wall (Front at Y = -4.10m, H = 0.70m)
    register_box("BrokenFrontWall", 5.20, 0.25, 0.70, (-1.40, -4.10, 0.12),
                 front=R_GRIMY_BRICK, sides=R_GRIMY_BRICK, top=R_STONE_COPING)

    # 10. Discarded Fly-Tipped Car Tyre in Yard (X = 2.40m, Y = -3.60m)
    register_box("YardTyre", 0.90, 0.90, 0.40, (2.40, -3.60, 0.12),
                 front=R_RUBBISH_YARD, sides=R_RUBBISH_YARD, top=R_RUBBISH_YARD)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Croydon_Traphouse")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_croydon_traphouse_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_croydon_traphouse.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_croydon_traphouse.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_croydon_traphouse_preview.png")
        shutil.copy2(OUT_DIR / "building_croydon_traphouse_atlas.png", TOOLS_OUT_DIR / "building_croydon_traphouse_atlas.png")
    except Exception as e:
        print(f"[building_croydon_traphouse] note: {e}")

    print("[building_croydon_traphouse] generation complete.")


main()
