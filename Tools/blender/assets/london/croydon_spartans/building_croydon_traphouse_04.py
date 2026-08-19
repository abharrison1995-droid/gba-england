"""Croydon Spartan Traphouse Variation 04 — Fortified Security Den (High-Poly ~1000 Tris).

Architectural Specs:
- 8.0m wide x 7.2m deep x 7.8m high heavily fortified Croydon drug den & stash house
- High-Poly ~1,000 Triangles 3D Geometry:
  - All windows fitted with heavy corrugated steel security blast shutters
  - Outer front porch enclosed in a 3D welded steel security cage airlock with padlocked iron gate
  - High-intensity halogen security floodlight pod & 3D CCTV camera
  - High perimeter garden wall topped with 3D broken glass bottle deterrent shards
  - Fly-tipped wheelie bin & discarded cinder blocks out front
  - Stencils: "SPARTAN BLOOD", "24HR CCTV", "DANGER"
- Outputs to Tools/blender/out/london/ and Tools/out/london/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/london/building_croydon_traphouse_04.py
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
R_DARK_BRICK        = (0,   256, 256, 256)   # Dark soot-stained Victorian brick with warning stencils
R_STEEL_SHUTTER     = (256, 256, 128, 256)   # Corrugated steel security blast shutters
R_STEEL_CAGE        = (0,   128, 256, 128)   # Heavy welded steel security cage & mesh
R_AIRLOCK_DOOR      = (256, 128, 128, 128)   # Armoured security door with triple deadbolts
R_ROOF_SLATE        = (0,   0,   256, 128)   # Grimy slate roof
R_WHEELIE_BIN       = (256, 0,   128, 128)   # Black council wheelie bin & rubbish
R_STONE_WALL        = (384, 256, 128, 128)   # High perimeter wall with broken glass tops
R_FLOODLIGHT_POD    = (384, 128, 128, 128)   # Halogen security floodlight & CCTV
R_METAL_TRIM        = (384, 0,   128, 128)   # Steel bars, conduits & hinges

# --- Palette Colors ---
BRICK_DARK_BASE     = (0.38, 0.32, 0.28)
BRICK_MORTAR        = (0.48, 0.44, 0.38)
STEEL_CHARCOAL      = (0.22, 0.24, 0.26)
STEEL_RUST          = (0.38, 0.22, 0.15)
STEEL_LIGHT         = (0.50, 0.52, 0.56)
GRAFFITI_YELLOW     = (0.95, 0.85, 0.10)
GRAFFITI_RED        = (0.85, 0.12, 0.10)
SLATE_DARK          = (0.20, 0.22, 0.24)
BIN_BLACK           = (0.12, 0.12, 0.14)
GLASS_GREEN_SHARD   = (0.20, 0.55, 0.35)


def paint_traphouse_04_atlas():
    a = Atlas(S, seed=2104)

    # 1. Dark Victorian Brick Wall (R_DARK_BRICK) - Clean of graffiti
    x, y, w, h = R_DARK_BRICK
    a.bricks(x, y, w, h, brick=BRICK_DARK_BASE, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.08)
    a.shade(x, y, w, h, top=-0.06, bottom=-0.18)
    a.noise(x, y, w, h, 0.035)

    # 2. Corrugated Steel Security Blast Shutter (R_STEEL_SHUTTER)
    x, y, w, h = R_STEEL_SHUTTER
    a.rect(x, y, w, h, STEEL_CHARCOAL)
    for sy in range(y + 6, y + h - 6, 10):
        a.rect(x + 4, sy, w - 8, 3, (0.12, 0.14, 0.16))
        a.rect(x + 4, sy + 3, w - 8, 2, STEEL_LIGHT)
    # Corner padlock plates
    for px in [x + 12, x + w - 24]:
        a.rect(px, y + 12, 12, 20, (0.7, 0.6, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 3. Security Airlock Cage (R_STEEL_CAGE)
    x, y, w, h = R_STEEL_CAGE
    a.rect(x, y, w, h, (0.18, 0.19, 0.20))
    for gy in range(y + 8, y + h - 8, 14):
        a.rect(x + 4, gy, w - 8, 2, STEEL_LIGHT)
    for gx in range(x + 8, x + w - 8, 14):
        a.rect(gx, y + 4, 2, h - 8, STEEL_LIGHT)
    a.noise(x, y, w, h, 0.02)

    # 4. Airlock Security Door (R_AIRLOCK_DOOR)
    x, y, w, h = R_AIRLOCK_DOOR
    a.rect(x, y, w, h, (0.15, 0.16, 0.18))
    a.rect(x + 6, y + 6, w - 12, h - 12, (0.10, 0.11, 0.12))
    # Triple deadbolt housings
    for dy in [y + 30, y + h // 2, y + h - 30]:
        a.rect(x + w - 22, dy, 14, 18, (0.8, 0.7, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 5. Roof Slate (R_ROOF_SLATE)
    x, y, w, h = R_ROOF_SLATE
    a.rect(x, y, w, h, SLATE_DARK)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.12, 0.14, 0.16))
    a.noise(x, y, w, h, 0.04)

    # 6. Wheelie Bin (R_WHEELIE_BIN)
    x, y, w, h = R_WHEELIE_BIN
    a.rect(x, y, w, h, BIN_BLACK)
    a.text(x + 16, y + h // 2, "42", (0.9, 0.9, 0.9), scale=3)
    a.noise(x, y, w, h, 0.02)

    # 7. High Perimeter Wall & Broken Glass (R_STONE_WALL)
    x, y, w, h = R_STONE_WALL
    a.bricks(x, y, w, h, brick=BRICK_DARK_BASE, mortar=BRICK_MORTAR, bw=20, bh=10, jitter=0.06)
    # Glass shards embedded in concrete top
    a.rect(x, y + h - 12, w, 12, (0.60, 0.58, 0.54))
    for gx in range(x + 4, x + w - 4, 8):
        a.rect(gx, y + h - 8, 3, 6, GLASS_GREEN_SHARD)
    a.noise(x, y, w, h, 0.03)

    # 8. Halogen Floodlight (R_FLOODLIGHT_POD)
    x, y, w, h = R_FLOODLIGHT_POD
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.98, 0.95, 0.70))  # Lit halogen
    a.noise(x, y, w, h, 0.015)

    # 9. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_CHARCOAL)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_croydon_traphouse_04_atlas", OUT_DIR)


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
    img = paint_traphouse_04_atlas()
    mat = material_for(img, "mat_traphouse_04")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Croydon Traphouse 04 — Fortified Security Den (~950 Triangles)
    # =========================================================================

    # 1. Base Pavement (8.60m x 7.80m x 0.15m)
    register_box("PavementPlinth", 8.60, 7.80, 0.15, (0.0, 0.0, 0.0),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 2. Main 2-Storey Brick House Body (Width 7.40m, Depth 6.20m, Z: 0.15m to 6.20m, H: 6.05m)
    register_box("HouseCore", 7.40, 6.20, 6.05, (0.0, 0.40, 0.15),
                 front=R_DARK_BRICK, sides=R_DARK_BRICK, back=R_DARK_BRICK, top=R_STONE_WALL)

    # 3. Ground Floor Blast Shutters (Left X = -2.20m, Right X = +2.20m)
    for i, wx in enumerate([-2.20, 2.20]):
        register_box(f"GFShutter_{i}", 1.60, 0.15, 1.50, (wx, -2.75, 0.90),
                     front=R_STEEL_SHUTTER, sides=R_METAL_TRIM, top=R_METAL_TRIM)
        register_box(f"GFSill_{i}", 1.80, 0.25, 0.15, (wx, -2.80, 0.75),
                     front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 4. Front Entrance: 3D Welded Security Airlock Cage (Center: X = 0.0m)
    # - Concrete Porch Threshold
    register_box("PorchThreshold", 2.20, 1.20, 0.15, (0.0, -3.30, 0.15),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)
    # - Inner Armoured Door
    register_box("InnerDoor", 1.20, 0.10, 2.20, (0.0, -2.75, 0.15),
                 front=R_AIRLOCK_DOOR, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    # - Outer Steel Cage Front Gate & Side Mesh Panels
    register_box("CageFront", 2.20, 0.06, 2.40, (0.0, -3.87, 0.15),
                 front=R_STEEL_CAGE, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("CageSideL", 0.06, 1.10, 2.40, (-1.07, -3.32, 0.15),
                 front=R_STEEL_CAGE, sides=R_STEEL_CAGE, top=R_METAL_TRIM)
    register_box("CageSideR", 0.06, 1.10, 2.40, (1.07, -3.32, 0.15),
                 front=R_STEEL_CAGE, sides=R_STEEL_CAGE, top=R_METAL_TRIM)
    register_box("CageRoof", 2.20, 1.20, 0.06, (0.0, -3.30, 2.55),
                 front=R_STEEL_CAGE, sides=R_STEEL_CAGE, top=R_STEEL_CAGE)

    # Halogen Security Floodlight Pod mounted above cage
    register_box("Floodlight", 0.35, 0.25, 0.25, (0.0, -2.90, 2.85),
                 front=R_FLOODLIGHT_POD, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 5. 1st Floor Steel Blast Shutters (X = -2.20m, +2.20m, Z = 3.60m to 5.20m)
    for i, wx in enumerate([-2.20, 2.20]):
        register_box(f"UFShutter_{i}", 1.40, 0.15, 1.60, (wx, -2.75, 3.60),
                     front=R_STEEL_SHUTTER, sides=R_METAL_TRIM, top=R_METAL_TRIM)
        register_box(f"UFSill_{i}", 1.55, 0.20, 0.12, (wx, -2.80, 3.48),
                     front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # 6. High Perimeter Brick Boundary Wall with 3D Glass Shards
    register_box("HighWallL", 2.60, 0.25, 1.40, (-2.70, -3.80, 0.15),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)
    register_box("HighWallR", 2.60, 0.25, 1.40, (2.70, -3.80, 0.15),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # Glass Shard Prisms atop wall
    for i in range(12):
        gx = -3.80 + i * 0.22
        register_box(f"GlassShard_{i}", 0.04, 0.04, 0.08, (gx, -3.80, 1.55),
                     front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_WALL)

    # Black Council Wheelie Bin
    register_box("WheelieBin", 0.65, 0.65, 1.10, (3.20, -3.20, 0.15),
                 front=R_WHEELIE_BIN, sides=R_WHEELIE_BIN, top=R_WHEELIE_BIN)

    # 7. Pitched Slate Roof (Width 7.80m, Depth 6.60m, H: 1.80m, Z = 6.20m to 8.00m)
    roof = make_pitched_roof("SlateRoof", 7.80, 6.60, 1.80, overhang=0.35, at=(0.0, 0.40, 6.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_SLATE, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(roof, R_DARK_BRICK, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(roof)

    # Brick Chimneys (Left X = -2.80m, Right X = +2.80m)
    for i, cx in enumerate([-2.80, 2.80]):
        register_box(f"Chimney_{i}", 0.80, 0.80, 1.10, (cx, 0.40, 7.30),
                     front=R_DARK_BRICK, sides=R_DARK_BRICK, top=R_STONE_WALL)
        for pot_i in [-0.18, 0.18]:
            pot = make_cylinder(f"Pot_{i}_{pot_i}", 0.10, 0.35, segs=8, at=(cx + pot_i, 0.40, 8.40))
            pot.data.materials.append(mat)
            kit.map_faces_to_region(pot, R_STONE_WALL, S)
            parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Croydon_Traphouse_04")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_croydon_traphouse_04_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_croydon_traphouse_04.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_croydon_traphouse_04.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_croydon_traphouse_04_preview.png")
        shutil.copy2(OUT_DIR / "building_croydon_traphouse_04_atlas.png", TOOLS_OUT_DIR / "building_croydon_traphouse_04_atlas.png")
    except Exception as e:
        print(f"[building_croydon_traphouse_04] note: {e}")

    print("[building_croydon_traphouse_04] generation complete.")


main()
