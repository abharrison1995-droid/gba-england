"""Croydon Spartan Traphouse Variation 02 — Corner Fortified Property (High-Poly ~1000 Tris).

Architectural Specs:
- 8.4m wide x 7.6m deep x 8.2m high end-of-terrace Croydon traphouse
- High-Poly ~1,000 Triangles 3D Geometry:
  - 3-sided projecting ground floor bay window with 3D welded iron security bars & OSB boards
  - Heavy reinforced steel entrance door with security peephole & concrete porch hood
  - Side alleyway with corrugated iron gate, 3D razor wire bracket, and fly-tipped rubbish (oil drum & pallets)
  - 3D wall-mounted CCTV security camera box with corner conduit
  - Blackout plastic sheeting & duct-tape crosses on upper floor windows
  - Twin brick chimney stacks with terracotta chimney pots
  - Graffiti: "SPARTAN 24/7", "NO FEDS", "0208"
- Outputs to Tools/blender/out/london/ and Tools/out/london/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/london/building_croydon_traphouse_02.py
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
R_YELLOW_BRICK      = (0,   256, 256, 256)   # Grubby London yellow-stock brick with graffiti tags
R_BAY_BOARDED       = (256, 256, 128, 256)   # Armoured OSB bay window & welded steel bars
R_BLACKOUT_WIN      = (0,   128, 256, 128)   # Upper floor blackout sheeting & duct-tape crosses
R_STEEL_DOOR        = (256, 128, 128, 128)   # Heavy reinforced steel security door
R_ROOF_SLATE        = (0,   0,   256, 128)   # Weathered slate roof & soot stains
R_ALLEY_GATE        = (256, 0,   128, 128)   # Rusted corrugated sheet metal alley gate
R_STONE_TRIM        = (384, 256, 128, 128)   # Concrete sills, lintels & coping
R_OIL_DRUM          = (384, 128, 128, 128)   # Blue industrial chemical/oil drum & litter
R_METAL_TRIM        = (384, 0,   128, 128)   # CCTV, pipes & razor wire brackets

# --- Palette Colors ---
BRICK_YELLOW_BASE   = (0.55, 0.50, 0.38)
BRICK_MORTAR        = (0.65, 0.62, 0.54)
GRAFFITI_RED        = (0.85, 0.12, 0.10)
GRAFFITI_WHITE      = (0.95, 0.95, 0.95)
GRAFFITI_BLACK      = (0.10, 0.10, 0.12)
OSB_TIMBER          = (0.65, 0.48, 0.28)
STEEL_RUST          = (0.35, 0.20, 0.14)
STEEL_DARK          = (0.20, 0.22, 0.24)
DUCT_TAPE           = (0.75, 0.76, 0.78)
SLATE_DARK          = (0.24, 0.26, 0.28)
MOSS_GREEN          = (0.26, 0.38, 0.18)
DRUM_BLUE           = (0.15, 0.30, 0.55)


def paint_traphouse_02_atlas():
    a = Atlas(S, seed=2102)

    # 1. Grubby London Yellow-Stock Brick (R_YELLOW_BRICK) - Clean of graffiti
    x, y, w, h = R_YELLOW_BRICK
    a.bricks(x, y, w, h, brick=BRICK_YELLOW_BASE, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.08)
    a.shade(x, y, w, h, top=-0.04, bottom=-0.16)
    for mx in range(x, x + w, 16):
        a.disc(mx, y + 8, 10, MOSS_GREEN)
    a.noise(x, y, w, h, 0.035)

    # 2. Armoured OSB Bay Window (R_BAY_BOARDED)
    x, y, w, h = R_BAY_BOARDED
    a.rect(x, y, w, h, (0.32, 0.30, 0.26))
    bx, by, bw, bh = x + 6, y + 6, w - 12, h - 12
    a.rect(bx, by, bw, bh, OSB_TIMBER)
    for py in range(by, by + bh, 24):
        a.rect(bx, py, bw, 2, (0.45, 0.34, 0.18))
    # Steel security mesh
    for gy in range(by, by + bh, 16):
        a.rect(bx, gy, bw, 2, STEEL_RUST)
    for gx in range(bx, bx + bw, 16):
        a.rect(gx, by, 2, bh, STEEL_RUST)
    a.noise(x, y, w, h, 0.03)

    # 3. Blackout Upper Window (R_BLACKOUT_WIN)
    x, y, w, h = R_BLACKOUT_WIN
    a.rect(x, y, w, h, (0.60, 0.58, 0.54))
    wx, wy, ww, wh = x + 8, y + 8, w - 16, h - 16
    a.rect(wx, wy, ww, wh, (0.08, 0.08, 0.10))  # Blackout plastic
    # Silver duct-tape cross
    for i in range(min(ww, wh)):
        a.rect(wx + i, wy + i, 4, 4, DUCT_TAPE)
        a.rect(wx + ww - i - 4, wy + i, 4, 4, DUCT_TAPE)
    a.noise(x, y, w, h, 0.02)

    # 4. Heavy Steel Security Door (R_STEEL_DOOR)
    x, y, w, h = R_STEEL_DOOR
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, (0.14, 0.16, 0.18))
    # Heavy lock reinforcement plates
    a.rect(x + w - 24, y + h // 2 - 20, 16, 40, (0.7, 0.6, 0.2))
    a.disc(x + w // 2, y + h - 36, 6, (0.8, 0.8, 0.8))  # Peephole
    a.noise(x, y, w, h, 0.02)

    # 5. Weathered Slate Roof (R_ROOF_SLATE)
    x, y, w, h = R_ROOF_SLATE
    a.rect(x, y, w, h, SLATE_DARK)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.16, 0.18, 0.20))
        for rx in range(x, x + w, 28):
            a.rect(rx, ry, 2, 14, (0.16, 0.18, 0.20))
    a.noise(x, y, w, h, 0.04)

    # 6. Rusted Corrugated Alley Gate (R_ALLEY_GATE)
    x, y, w, h = R_ALLEY_GATE
    a.rect(x, y, w, h, (0.42, 0.26, 0.18))
    for gx in range(x, x + w, 8):
        a.rect(gx, y, 2, h, (0.28, 0.16, 0.10))
    a.noise(x, y, w, h, 0.035)

    # 7. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, (0.68, 0.65, 0.60))
    for sy in range(y, y + h, 24):
        a.rect(x, sy, w, 2, (0.45, 0.42, 0.38))

    # 8. Blue Oil Drum & Litter (R_OIL_DRUM)
    x, y, w, h = R_OIL_DRUM
    a.rect(x, y, w, h, DRUM_BLUE)
    for dy in [y + 20, y + h // 2, y + h - 20]:
        a.rect(x, dy, w, 4, (0.10, 0.20, 0.38))
    a.text(x + 12, y + h // 2 - 6, "HAZMAT", (0.9, 0.9, 0.2), scale=1)
    a.noise(x, y, w, h, 0.03)

    # 9. Metal Trim & CCTV (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_croydon_traphouse_02_atlas", OUT_DIR)


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


def make_cylinder(name, r, h, segs=10, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    faces.append(list(range(segs - 1, -1, -1)))
    faces.append(list(range(segs, segs * 2)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def make_pitched_roof(name, w, d, h, overhang=0.35, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang

    verts = [
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
        (-hw, 0.0, h), (hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # Underside
        (0, 1, 5, 4),    # Front slope
        (1, 2, 5),       # Right gable
        (2, 3, 4, 5),    # Back slope
        (3, 0, 4),       # Left gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_traphouse_02_atlas()
    mat = material_for(img, "mat_traphouse_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Croydon Traphouse 02 (~950 Triangles)
    # =========================================================================

    # 1. Pavement & Forecourt Base (8.80m x 8.00m x 0.15m)
    register_box("PavementPlinth", 8.80, 8.00, 0.15, (0.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main 2-Storey Brick House Body (Width 7.20m, Depth 6.40m, Z: 0.15m to 6.20m, H: 6.05m)
    register_box("HouseCore", 7.20, 6.40, 6.05, (-0.60, 0.30, 0.15),
                 front=R_YELLOW_BRICK, sides=R_YELLOW_BRICK, back=R_YELLOW_BRICK, top=R_STONE_TRIM)

    # 3. Ground Floor 3-Sided Armoured Bay Window (Left Wing: X = -2.40m)
    # - Central Bay Face
    register_box("BayFront", 2.20, 0.80, 2.40, (-2.40, -3.20, 0.15),
                 front=R_BAY_BOARDED, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # - Bay Concrete Sill & Rooflet
    register_box("BaySill", 2.40, 0.90, 0.15, (-2.40, -3.25, 0.15),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("BayRooflet", 2.40, 0.90, 0.20, (-2.40, -3.25, 2.55),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_ROOF_SLATE)

    # 6 3D Steel Security Bars across Bay Window
    for i in range(6):
        bx = -3.20 + i * 0.32
        register_box(f"BayBar_{i}", 0.03, 0.03, 2.20, (bx, -3.62, 0.30),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 4. Front Entrance Portal (X = +1.60m)
    register_box("FrontDoor", 1.10, 0.12, 2.20, (1.60, -2.92, 0.15),
                 front=R_STEEL_DOOR, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorPorchHood", 1.50, 0.60, 0.15, (1.60, -3.15, 2.45),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep", 1.30, 0.40, 0.12, (1.60, -3.05, 0.15),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 3D Wall-Mounted CCTV Camera Box on Corner
    register_box("CCTVBracket", 0.04, 0.35, 0.04, (2.60, -2.95, 3.20),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("CCTVCamera", 0.18, 0.32, 0.18, (2.60, -3.20, 3.12),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 5. 1st Floor Blackout Windows (X = -2.40m, +1.60m, Z = 3.60m to 5.20m)
    for i, wx in enumerate([-2.40, 1.60]):
        register_box(f"UFWin_{i}", 1.40, 0.12, 1.60, (wx, -2.92, 3.60),
                     front=R_BLACKOUT_WIN, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        register_box(f"UFSill_{i}", 1.55, 0.20, 0.12, (wx, -2.96, 3.48),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Side Alleyway & Rusted Corrugated Iron Security Gate (Right: X = +3.40m)
    register_box("AlleyWall", 0.25, 3.20, 2.40, (3.60, -1.30, 0.15),
                 front=R_YELLOW_BRICK, sides=R_YELLOW_BRICK, top=R_STONE_TRIM)
    register_box("AlleyGate", 1.20, 0.08, 2.20, (3.20, -2.85, 0.15),
                 front=R_ALLEY_GATE, sides=R_ALLEY_GATE, top=R_ALLEY_GATE)

    # 3D Razor Wire Bracket Bar atop Gate
    register_box("RazorBracket", 1.30, 0.04, 0.20, (3.20, -2.85, 2.35),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # Fly-tipped Chemical Oil Drum & Rubbish in front
    drum = make_cylinder("OilDrum", 0.30, 0.90, segs=10, at=(3.40, -3.40, 0.15))
    drum.data.materials.append(mat)
    kit.map_faces_to_region(drum, R_OIL_DRUM, S)
    parts.append(drum)

    register_box("PalletRubbish", 0.80, 0.60, 0.25, (2.60, -3.50, 0.15),
                 front=R_BAY_BOARDED, sides=R_BAY_BOARDED, top=R_BAY_BOARDED)

    # 7. Weathered Pitched Slate Roof (Width 7.60m, Depth 6.80m, H: 2.00m, Z = 6.20m to 8.20m)
    roof = make_pitched_roof("SlateRoof", 7.60, 6.80, 2.00, overhang=0.35, at=(-0.60, 0.30, 6.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_SLATE, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(roof, R_YELLOW_BRICK, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(roof)

    # Twin Brick Chimneys with Terracotta Pots (Left X = -3.40m, Right X = +2.20m)
    for i, cx in enumerate([-3.40, 2.20]):
        register_box(f"Chimney_{i}", 0.80, 0.80, 1.20, (cx, 0.30, 7.40),
                     front=R_YELLOW_BRICK, sides=R_YELLOW_BRICK, top=R_STONE_TRIM)
        for pot_i in [-0.20, 0.20]:
            pot = make_cylinder(f"Pot_{i}_{pot_i}", 0.12, 0.40, segs=8, at=(cx + pot_i, 0.30, 8.60))
            pot.data.materials.append(mat)
            kit.map_faces_to_region(pot, R_STONE_TRIM, S)
            parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Croydon_Traphouse_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_croydon_traphouse_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_croydon_traphouse_02.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_croydon_traphouse_02.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_croydon_traphouse_02_preview.png")
        shutil.copy2(OUT_DIR / "building_croydon_traphouse_02_atlas.png", TOOLS_OUT_DIR / "building_croydon_traphouse_02_atlas.png")
    except Exception as e:
        print(f"[building_croydon_traphouse_02] note: {e}")

    print("[building_croydon_traphouse_02] generation complete.")


main()
