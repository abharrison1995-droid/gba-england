"""Ancient Stone Well / Arcane Glowing Pool (Mosley Cellar Lab Dungeon Prop).

Specs:
- 3.2m x 3.2m footprint, Height: 3.4m.
- Dungeon arcane subterranean ritual well:
  - Circular/hexagonal carved stone masonry well wall with glowing cyan/purple arcane runes.
  - Wrought-iron overhead suspension gantry with pulley wheel, chain & wooden bucket.
  - Ethereal glowing mystical water pool surface with swirling magic light.
  - Damp flagstone dungeon floor plinth with moss & bloodstone ritual sigils.
  - Weathered timber beam roof canopy with slate tiles.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/dungeon_stone_well.py
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
OUT_DIR = kit.OUT_DIR
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"

# --- Atlas Region Definitions (x, y, w, h) ---
R_WELL_STONE    = (0,   256, 256, 256)   # Weathered mossy stone well ashlar with glowing cyan runes
R_MAGIC_WATER   = (256, 256, 256, 256)   # Ethereal glowing cyan/purple mystical swirling water pool
R_ROOF_SLATES   = (0,   128, 256, 128)   # Weathered damp dungeon timber & slate well canopy
R_IRON_GANTRY   = (256, 128, 128, 128)   # Forged iron pulley wheel, suspension chains & bucket
R_FLAGSTONE_DUN = (384, 128, 128, 128)   # Dungeon damp flagstone floor with occult sigils
R_OAK_TIMBER    = (0,   0,   256, 128)   # Heavy dark oak gantry support posts
R_RUNIC_GLOW    = (256, 0,   128, 128)   # Concentrated glowing neon cyan magic runes
R_MOSS_GRAVEL   = (384, 0,   128, 128)   # Dark mossy cellar gravel

# --- Palette Colors ---
STONE_GREY      = (0.52, 0.50, 0.46)
STONE_MORTAR    = (0.35, 0.34, 0.32)
RUNIC_CYAN      = (0.15, 0.95, 0.95)
MAGIC_PURPLE    = (0.55, 0.20, 0.85)
WATER_CYAN_GLOW = (0.25, 0.85, 0.95)
OAK_DARK        = (0.24, 0.16, 0.10)
IRON_BLACK      = (0.12, 0.12, 0.14)
ROOF_SLATE      = (0.30, 0.32, 0.35)
MOSS_GREEN      = (0.24, 0.35, 0.18)


def paint_well_atlas():
    a = Atlas(S, seed=6101)

    # 1. Stone Well with Glowing Arcane Runes (R_WELL_STONE)
    x, y, w, h = R_WELL_STONE
    a.bricks(x, y, w, h, brick=STONE_GREY, mortar=STONE_MORTAR, bw=32, bh=14, jitter=0.06)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.15)
    # Carved Glowing Runes along central stone band
    for rx, ry in [(x + 30, y + 120), (x + 90, y + 130), (x + 150, y + 120), (x + 210, y + 130)]:
        a.disc(rx, ry, 12, (0.05, 0.40, 0.45))
        a.disc(rx, ry, 6, RUNIC_CYAN)
        a.rect(rx - 2, ry - 14, 4, 28, RUNIC_CYAN)
        a.rect(rx - 10, ry - 2, 20, 4, RUNIC_CYAN)
    # Moss around base
    for mx in range(x, x + w, 24):
        a.disc(mx, y + 12, 12, MOSS_GREEN)
    a.noise(x, y, w, h, 0.03)

    # 2. Mystical Glowing Water Pool (R_MAGIC_WATER)
    x, y, w, h = R_MAGIC_WATER
    a.rect(x, y, w, h, MAGIC_PURPLE)
    cx, cy = x + w // 2, y + h // 2
    # Concentric swirling vortex rings
    a.disc(cx, cy, 110, (0.30, 0.15, 0.60))
    a.disc(cx, cy, 85, (0.15, 0.60, 0.85))
    a.disc(cx, cy, 60, WATER_CYAN_GLOW)
    a.disc(cx, cy, 35, (0.85, 0.98, 1.00))  # Brilliant white-cyan center core
    # Arcane particle sparks
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        sx = int(cx + 70 * math.cos(rad))
        sy = int(cy + 70 * math.sin(rad))
        a.disc(sx, sy, 6, RUNIC_CYAN)
    a.noise(x, y, w, h, 0.02)

    # 3. Weathered Slate Roof (R_ROOF_SLATES)
    x, y, w, h = R_ROOF_SLATES
    a.rect(x, y, w, h, ROOF_SLATE)
    for sy in range(y, y + h, 14):
        a.rect(x, sy, w, 2, (0.2, 0.22, 0.24))
    a.noise(x, y, w, h, 0.035)

    # 4. Iron Pulley & Chains (R_IRON_GANTRY)
    x, y, w, h = R_IRON_GANTRY
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    # Pulley wheel
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 38, IRON_BLACK)
    a.disc(cx, cy, 22, (0.4, 0.4, 0.4))
    a.disc(cx, cy, 8, IRON_BLACK)
    # Suspension chain links
    a.rect(cx - 3, y, 6, h, (0.6, 0.6, 0.6))
    a.noise(x, y, w, h, 0.02)

    # 5. Dungeon Flagstone Floor (R_FLAGSTONE_DUN)
    x, y, w, h = R_FLAGSTONE_DUN
    a.rect(x, y, w, h, (0.40, 0.38, 0.35))
    for fy in range(y, y + h, 28):
        a.rect(x, fy, w, 2, (0.25, 0.24, 0.22))
    for fx in range(x, x + w, 28):
        a.rect(fx, y, 2, h, (0.25, 0.24, 0.22))
    # Occult circle sigil
    a.disc(x + w // 2, y + h // 2, 40, (0.55, 0.15, 0.15))
    a.disc(x + w // 2, y + h // 2, 34, (0.40, 0.38, 0.35))
    a.noise(x, y, w, h, 0.035)

    # 6. Dark Oak Timber (R_OAK_TIMBER)
    x, y, w, h = R_OAK_TIMBER
    a.rect(x, y, w, h, OAK_DARK)
    for oy in range(y, y + h, 16):
        a.rect(x, oy, w, 2, (0.15, 0.10, 0.06))
    a.noise(x, y, w, h, 0.03)

    # 7. Runic Glow (R_RUNIC_GLOW)
    x, y, w, h = R_RUNIC_GLOW
    a.rect(x, y, w, h, (0.05, 0.15, 0.20))
    a.disc(x + w // 2, y + h // 2, 34, RUNIC_CYAN)
    a.disc(x + w // 2, y + h // 2, 16, (0.95, 1.0, 1.0))
    a.noise(x, y, w, h, 0.015)

    # 8. Moss Gravel (R_MOSS_GRAVEL)
    x, y, w, h = R_MOSS_GRAVEL
    a.rect(x, y, w, h, (0.30, 0.32, 0.26))
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("dungeon_stone_well_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_FLAGSTONE_DUN, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_FLAGSTONE_DUN, S, only=side("bottom"))


def make_hex_cylinder(name, r, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    # Bottom 6 verts
    for i in range(6):
        ang = 2 * math.pi * i / 6.0
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    # Top 6 verts
    for i in range(6):
        ang = 2 * math.pi * i / 6.0
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    # 6 side quads
    for i in range(6):
        ni = (i + 1) % 6
        faces.append((i, ni, 6 + ni, 6 + i))
    # bottom & top caps
    faces.append([5, 4, 3, 2, 1, 0])
    faces.append([6, 7, 8, 9, 10, 11])

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def make_pitched_canopy(name, w, d, h, at=(0, 0, 0)):
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
        (1, 2, 5),       # right gable
        (2, 3, 4, 5),    # back slope
        (3, 0, 4),       # left gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_well_atlas()
    mat = material_for(img, "mat_stone_well")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Ancient Stone Well / Arcane Glowing Pool (3.2m x 3.2m Footprint, Height: 3.4m)
    # - Damp Cellar Flagstone Floor Plinth (Z: 0.0 to 0.12m)
    # - Hexagonal Carved Stone Well Wall (Radius 1.30m, H: 1.10m, Z = 0.12m to 1.22m)
    # - Glowing Arcane Magic Water Pool Interior (Z = 0.90m)
    # - Dark Oak Gantry Posts & Pulley Wheel
    # - Timber Slated Pitched Canopy Roof (Z: 2.50m to 3.40m)
    # =========================================================================

    # 1. Dungeon Flagstone Floor Base (3.4m x 3.4m, Z = 0.00 to 0.12m)
    register_box("WellPlinth", 3.40, 3.40, 0.12, (0.0, 0.0, 0.0),
                 front=R_FLAGSTONE_DUN, sides=R_FLAGSTONE_DUN, top=R_FLAGSTONE_DUN)

    # 2. Hexagonal Carved Stone Well Wall (Radius: 1.30m, H: 1.10m, Z = 0.12m to 1.22m)
    well_wall = make_hex_cylinder("WellWall", 1.30, 1.10, at=(0.0, 0.0, 0.12))
    well_wall.data.materials.append(mat)
    kit.map_faces_to_region(well_wall, R_WELL_STONE, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(well_wall, R_MAGIC_WATER, S, only=lambda f: f.normal.z > 0.5)
    kit.map_faces_to_region(well_wall, R_FLAGSTONE_DUN, S, only=lambda f: f.normal.z < -0.5)
    parts.append(well_wall)

    # 3. Glowing Mystical Water Surface (Inside well at Z = 0.85m to 0.95m)
    water_pool = make_hex_cylinder("MagicWaterPool", 1.05, 0.10, at=(0.0, 0.0, 0.85))
    water_pool.data.materials.append(mat)
    kit.map_faces_to_region(water_pool, R_MAGIC_WATER, S, only=lambda f: f.normal.z > 0.5)
    kit.map_faces_to_region(water_pool, R_RUNIC_GLOW, S, only=lambda f: f.normal.z <= 0.5)
    parts.append(water_pool)

    # 4. Dark Oak Timber Support Posts (Left at X = -1.25m, Right at X = +1.25m, Z = 0.12m to 2.60m)
    register_box("PostLeft", 0.18, 0.18, 2.48, (-1.25, 0.0, 0.12),
                 front=R_OAK_TIMBER, sides=R_OAK_TIMBER, top=R_OAK_TIMBER)
    register_box("PostRight", 0.18, 0.18, 2.48, (1.25, 0.0, 0.12),
                 front=R_OAK_TIMBER, sides=R_OAK_TIMBER, top=R_OAK_TIMBER)

    # Crossbeam Beam (Width: 2.80m, Z = 2.45m to 2.65m)
    register_box("Crossbeam", 2.80, 0.20, 0.20, (0.0, 0.0, 2.45),
                 front=R_OAK_TIMBER, sides=R_OAK_TIMBER, top=R_OAK_TIMBER)

    # 5. Iron Pulley Wheel, Chain & Bucket (Suspended in center: Z = 1.30m to 2.45m)
    register_box("PulleyWheel", 0.12, 0.35, 0.35, (0.0, 0.0, 2.15),
                 front=R_IRON_GANTRY, sides=R_IRON_GANTRY, top=R_IRON_GANTRY)
    register_box("OakBucket", 0.40, 0.40, 0.45, (0.0, 0.0, 1.40),
                 front=R_OAK_TIMBER, sides=R_OAK_TIMBER, top=R_MAGIC_WATER)

    # 6. Pitched Timber Slate Canopy Roof (Width 3.0m, Depth 2.2m, H: 0.85m at Z = 2.65m to 3.50m)
    canopy = make_pitched_canopy("WellCanopy", 3.00, 2.20, 0.85, at=(0.0, 0.0, 2.65))
    canopy.data.materials.append(mat)
    kit.map_faces_to_region(canopy, R_ROOF_SLATES, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(canopy, R_OAK_TIMBER, S, only=lambda f: f.normal.z <= 0.1 or abs(f.normal.x) > 0.6)
    parts.append(canopy)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Dungeon_Stone_Well")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "dungeon_stone_well_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "dungeon_stone_well.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "dungeon_stone_well.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "dungeon_stone_well_preview.png")
        shutil.copy2(OUT_DIR / "dungeon_stone_well_atlas.png", TOOLS_OUT_DIR / "dungeon_stone_well_atlas.png")
    except Exception as e:
        print(f"[dungeon_stone_well] note: {e}")

    print("[dungeon_stone_well] generation complete.")


main()
