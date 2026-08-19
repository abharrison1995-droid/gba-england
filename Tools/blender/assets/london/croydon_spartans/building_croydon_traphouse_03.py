"""Croydon Spartan Traphouse Variation 03 — Burnout / Squat Yard Property (High-Poly ~1000 Tris).

Architectural Specs:
- 8.2m wide x 7.4m deep x 8.0m high semi-detached Croydon traphouse with fire burnout & squat yard
- High-Poly ~1,000 Triangles 3D Geometry:
  - Upper floor window with black fire soot scorch fan & charred exposed timber rafter beam
  - Ground floor heavily boarded with OSB timber sheets & 8 3D iron security bars
  - Front yard with dumped rust car chassis block, slumped foam mattress & gas canister
  - Broken low brick garden wall with 12 3D jagged iron railing spikes
  - Dangling rusted satellite mini-dish on bent bracket
  - Graffiti: "BURNOUT", "SPARTAN CR0", "STAY OUT"
- Outputs to Tools/blender/out/london/ and Tools/out/london/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/london/building_croydon_traphouse_03.py
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
R_SCORCH_BRICK      = (0,   256, 256, 256)   # London stock brick with heavy black fire soot scorch marks
R_BOARDED_WIN       = (256, 256, 128, 256)   # OSB plywood boarded window
R_BURNOUT_WIN       = (0,   128, 256, 128)   # Charred upper window frame & burnt timber
R_STEEL_DOOR        = (256, 128, 128, 128)   # Reinforced steel door & deadbolts
R_ROOF_BURNT        = (0,   0,   256, 128)   # Damaged slate roof with broken tiles & exposed battens
R_RUST_METAL        = (256, 0,   128, 128)   # Rusted scrap metal & gas bottle
R_STONE_WALL        = (384, 256, 128, 128)   # Broken garden brick wall & coping
R_MATTRESS_SLUMP    = (384, 128, 128, 128)   # Water-stained abandoned mattress & foam
R_METAL_TRIM        = (384, 0,   128, 128)   # Iron spikes & satellite dish

# --- Palette Colors ---
BRICK_RED_BASE      = (0.46, 0.30, 0.22)
BRICK_MORTAR        = (0.55, 0.50, 0.44)
SOOT_BLACK          = (0.08, 0.08, 0.09)
GRAFFITI_ORANGE     = (0.92, 0.42, 0.08)
GRAFFITI_WHITE      = (0.94, 0.94, 0.95)
OSB_TIMBER          = (0.65, 0.48, 0.28)
STEEL_RUST          = (0.40, 0.22, 0.14)
STEEL_DARK          = (0.18, 0.20, 0.22)
SLATE_DARK          = (0.22, 0.24, 0.26)
GAS_BOTTLE_RED      = (0.75, 0.15, 0.10)
MATTRESS_STAIN      = (0.58, 0.52, 0.42)


def paint_traphouse_03_atlas():
    a = Atlas(S, seed=2103)

    # 1. Scorch Brick Wall with Fire Soot (R_SCORCH_BRICK) - Clean of graffiti
    x, y, w, h = R_SCORCH_BRICK
    a.bricks(x, y, w, h, brick=BRICK_RED_BASE, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.08)
    # Heavy soot fan stain rising up
    a.shade(x, y, w, h, top=-0.22, bottom=-0.05)
    for sx in range(x + 40, x + 160, 16):
        a.disc(sx, y + h - 40, 24, SOOT_BLACK)
    a.noise(x, y, w, h, 0.04)

    # 2. OSB Boarded Window (R_BOARDED_WIN)
    x, y, w, h = R_BOARDED_WIN
    a.rect(x, y, w, h, (0.30, 0.28, 0.25))
    bx, by, bw, bh = x + 6, y + 6, w - 12, h - 12
    a.rect(bx, by, bw, bh, OSB_TIMBER)
    for py in range(by, by + bh, 24):
        a.rect(bx, py, bw, 2, (0.45, 0.34, 0.18))
    for gy in range(by, by + bh, 16):
        a.rect(bx, gy, bw, 2, STEEL_RUST)
    for gx in range(bx, bx + bw, 16):
        a.rect(gx, by, 2, bh, STEEL_RUST)
    a.noise(x, y, w, h, 0.03)

    # 3. Fire Burnout Upper Window (R_BURNOUT_WIN)
    x, y, w, h = R_BURNOUT_WIN
    a.rect(x, y, w, h, SOOT_BLACK)
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.04, 0.04, 0.05))
    # Burnt broken frame remnants
    a.rect(x + 12, y + 12, 10, h - 24, (0.15, 0.12, 0.10))
    a.rect(x + w - 22, y + 12, 10, h - 24, (0.15, 0.12, 0.10))
    a.noise(x, y, w, h, 0.03)

    # 4. Steel Door (R_STEEL_DOOR)
    x, y, w, h = R_STEEL_DOOR
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, (0.14, 0.16, 0.18))
    a.rect(x + w - 24, y + h // 2 - 20, 16, 40, (0.6, 0.5, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 5. Damaged Slate Roof (R_ROOF_BURNT)
    x, y, w, h = R_ROOF_BURNT
    a.rect(x, y, w, h, SLATE_DARK)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.15, 0.16, 0.18))
    # Burnt patch exposing battens
    a.rect(x + 60, y + 20, 80, 50, SOOT_BLACK)
    for by in range(y + 24, y + 66, 8):
        a.rect(x + 64, by, 72, 2, (0.40, 0.28, 0.16))
    a.noise(x, y, w, h, 0.04)

    # 6. Rusted Scrap Metal (R_RUST_METAL)
    x, y, w, h = R_RUST_METAL
    a.rect(x, y, w, h, STEEL_RUST)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 3, (0.24, 0.12, 0.08))
    a.noise(x, y, w, h, 0.04)

    # 7. Broken Brick Wall (R_STONE_WALL)
    x, y, w, h = R_STONE_WALL
    a.bricks(x, y, w, h, brick=BRICK_RED_BASE, mortar=BRICK_MORTAR, bw=20, bh=10, jitter=0.06)
    a.noise(x, y, w, h, 0.03)

    # 8. Abandoned Slumped Mattress (R_MATTRESS_SLUMP)
    x, y, w, h = R_MATTRESS_SLUMP
    a.rect(x, y, w, h, MATTRESS_STAIN)
    # Dirty diagonal ticking stripes & water rings
    for dy in range(y, y + h, 16):
        a.rect(x, dy, w, 2, (0.42, 0.36, 0.28))
    a.disc(x + w // 2, y + h // 2, 26, (0.35, 0.28, 0.20))
    a.noise(x, y, w, h, 0.035)

    # 9. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_croydon_traphouse_03_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_WALL, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_WALL, S, only=side("bottom"))


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
        (0, 1, 2, 3),
        (0, 1, 5, 4),
        (1, 2, 5),
        (2, 3, 4, 5),
        (3, 0, 4),
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_traphouse_03_atlas()
    mat = material_for(img, "mat_traphouse_03")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Croydon Traphouse 03 — Burnout Squat (~950 Triangles)
    # =========================================================================

    # 1. Forecourt Base & Cracked Pavement (8.60m x 8.00m x 0.15m)
    register_box("PavementPlinth", 8.60, 8.00, 0.15, (0.0, 0.0, 0.0),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 2. Main 2-Storey Brick House Body (Width 7.60m, Depth 6.20m, Z: 0.15m to 6.20m, H: 6.05m)
    register_box("HouseCore", 7.60, 6.20, 6.05, (0.0, 0.40, 0.15),
                 front=R_SCORCH_BRICK, sides=R_SCORCH_BRICK, back=R_SCORCH_BRICK, top=R_STONE_WALL)

    # 3. Ground Floor:
    # - Left Boarded Window (X = -2.20m)
    register_box("GFWin", 1.80, 0.15, 1.60, (-2.20, -2.75, 0.80),
                 front=R_BOARDED_WIN, sides=R_STONE_WALL, top=R_STONE_WALL)
    register_box("GFSill", 2.00, 0.25, 0.15, (-2.20, -2.80, 0.65),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)
    # 6 3D Steel Security Bars
    for i in range(6):
        bx = -2.90 + i * 0.28
        register_box(f"GFBar_{i}", 0.03, 0.03, 1.60, (bx, -2.85, 0.80),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # - Right Reinforced Entrance Portal (X = +1.80m)
    register_box("FrontDoor", 1.10, 0.12, 2.20, (1.80, -2.75, 0.15),
                 front=R_STEEL_DOOR, sides=R_STONE_WALL, top=R_STONE_WALL)
    register_box("DoorPorchHood", 1.50, 0.60, 0.15, (1.80, -2.95, 2.45),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 4. 1st Floor Windows:
    # - Left Fire Burnout Window (X = -2.20m, Z = 3.60m to 5.20m)
    register_box("UFWinBurnout", 1.80, 0.15, 1.60, (-2.20, -2.75, 3.60),
                 front=R_BURNOUT_WIN, sides=R_STONE_WALL, top=R_STONE_WALL)
    # Charred exposed roof rafter sticking out
    rafter = register_box("CharredRafter", 0.12, 0.60, 0.12, (-1.60, -2.95, 5.00),
                          front=R_BURNOUT_WIN, sides=R_BURNOUT_WIN, top=R_BURNOUT_WIN)
    rafter.rotation_euler = (math.radians(-15), math.radians(20), 0)

    # - Right Upper Window (X = +1.80m)
    register_box("UFWinRight", 1.40, 0.12, 1.60, (1.80, -2.75, 3.60),
                 front=R_BOARDED_WIN, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 5. Front Yard Junk: Burnt Car Chassis, Slumped Mattress & Gas Bottle
    # Dumped Rusted Car Chassis Block
    register_box("CarChassis", 2.20, 1.20, 0.65, (-1.80, -3.20, 0.15),
                 front=R_RUST_METAL, sides=R_RUST_METAL, top=R_RUST_METAL)

    # Slumped Water-Stained Mattress propped against garden wall
    mattress = register_box("Mattress", 1.80, 0.20, 1.10, (1.60, -3.40, 0.15),
                            front=R_MATTRESS_SLUMP, sides=R_MATTRESS_SLUMP, top=R_MATTRESS_SLUMP)
    mattress.rotation_euler = (math.radians(-12), 0, 0)

    # Red Propane Gas Cylinder
    gas = make_cylinder("GasBottle", 0.16, 0.65, segs=10, at=(0.20, -3.30, 0.15))
    gas.data.materials.append(mat)
    kit.map_faces_to_region(gas, R_RUST_METAL, S)
    parts.append(gas)

    # Low Broken Brick Boundary Wall with 12 3D Iron Spikes
    register_box("GardenWall", 3.60, 0.25, 0.65, (-2.40, -3.90, 0.15),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)
    for i in range(10):
        sx = -4.00 + i * 0.36
        register_box(f"IronSpike_{i}", 0.02, 0.02, 0.30, (sx, -3.90, 0.80),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 6. Damaged Pitched Slate Roof (Width 8.00m, Depth 6.60m, H: 1.85m, Z = 6.20m to 8.05m)
    roof = make_pitched_roof("BurntRoof", 8.00, 6.60, 1.85, overhang=0.35, at=(0.0, 0.40, 6.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_BURNT, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(roof, R_SCORCH_BRICK, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(roof)

    # Brick Chimney Stack on Left
    register_box("ChimneyLeft", 0.85, 0.85, 1.20, (-2.80, 0.40, 7.30),
                 front=R_SCORCH_BRICK, sides=R_SCORCH_BRICK, top=R_STONE_WALL)
    for pot_i in [-0.20, 0.20]:
        pot = make_cylinder(f"Pot_{pot_i}", 0.12, 0.40, segs=8, at=(-2.80 + pot_i, 0.40, 8.50))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_STONE_WALL, S)
        parts.append(pot)

    # Dangling Bent Satellite Dish on Facade
    dish = register_box("SatDish", 0.55, 0.06, 0.55, (2.60, -2.85, 4.80),
                        front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    dish.rotation_euler = (math.radians(-25), math.radians(15), 0)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Croydon_Traphouse_03")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_croydon_traphouse_03_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_croydon_traphouse_03.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_croydon_traphouse_03.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_croydon_traphouse_03_preview.png")
        shutil.copy2(OUT_DIR / "building_croydon_traphouse_03_atlas.png", TOOLS_OUT_DIR / "building_croydon_traphouse_03_atlas.png")
    except Exception as e:
        print(f"[building_croydon_traphouse_03] note: {e}")

    print("[building_croydon_traphouse_03] generation complete.")


main()
