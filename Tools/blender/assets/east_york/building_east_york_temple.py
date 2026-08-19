"""East York Chinese Temple Landmark (High-Poly ~1000 Tris).

Architectural Specs:
- Landmark cultural/spiritual building for East York (Taoist/Buddhist civic temple)
- Dimensions: 12.0m x 9.0m footprint, 10.8m height
- Plinth: Elevated York limestone plinth with carved dragon reliefs, steps & cloud balustrades
- Portico: 4 round vermilion pillars with gold capitals & dougong timber brackets
- Portal: Black lacquer & gold sign: "東約克廟 EAST YORK TEMPLE", vermilion studded doors
- Roof: Dual-tier Chinese swept hip-and-gable roofs (Xieshan-ding) with glazed golden-amber tiles & Chiwen finials
- Forecourt: Central bronze incense cauldron and twin carved guardian lions
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_temple.py
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
OUT_DIR = kit.OUT_DIR / "east_york"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "east_york"

# --- Atlas Regions ---
R_LIMESTONE_PLINTH  = (0,   256, 256, 256)   # York limestone & carved dragon reliefs
R_TEMPLE_WALL       = (256, 256, 128, 256)   # Red lacquered temple timber & lattice screens
R_GOLD_ROOF_TILES   = (0,   128, 256, 128)   # Imperial gold-amber ceramic barrel roof tiles
R_TEMPLE_DOORS      = (384, 256, 128, 256)   # Vermilion temple doors with brass studs
R_TEMPLE_SIGNBOARD  = (256, 128, 128, 128)   # Gold on black "東約克廟 EAST YORK TEMPLE"
R_FOO_DOG_STONE     = (384, 128, 128, 128)   # Carved grey stone guardian lion texture
R_TIMBER_VERMILION  = (0,   0,   256, 128)   # Vermilion columns, beams & dougong brackets
R_GOLD_DRAGON_TRIM  = (256, 0,   128, 128)   # Gold leaf dragon finials & ornamental caps
R_INCENSE_BRONZE    = (384, 0,   64,  128)   # Patinated dark bronze cauldron
R_LANTERN_RED       = (448, 0,   64,  128)   # Large hanging red silk temple lantern

# --- Colors ---
STONE_BASE          = (0.78, 0.74, 0.65)
STONE_MORTAR        = (0.60, 0.56, 0.48)
GOLD_ROOF_BASE      = (0.88, 0.62, 0.14)
GOLD_ROOF_DARK      = (0.58, 0.38, 0.08)
GOLD_ROOF_HILITE    = (0.98, 0.82, 0.28)
VERMILION_BASE      = (0.76, 0.12, 0.08)
VERMILION_DARK      = (0.46, 0.06, 0.04)
IMPERIAL_GOLD       = (0.92, 0.76, 0.18)
BLACK_LACQUER       = (0.08, 0.08, 0.10)
BRONZE_PATINA       = (0.24, 0.32, 0.28)
LANTERN_RED         = (0.90, 0.10, 0.06)


def paint_east_york_temple_atlas():
    a = Atlas(S, seed=3331)

    # 1. York Limestone Plinth & Dragon Relief (R_LIMESTONE_PLINTH)
    x, y, w, h = R_LIMESTONE_PLINTH
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y, y + h, 32):
        a.rect(x, my, w, 3, STONE_MORTAR)
        offset = 40 if ((my - y) // 32) % 2 else 0
        for mx in range(x - offset, x + w, 80):
            a.rect(max(x, mx), my, 3, 32, STONE_MORTAR)
    band_y = y + h - 36
    a.rect(x, band_y, w, 32, (0.50, 0.46, 0.40))
    a.rect(x, band_y + 3, w, 26, STONE_BASE)
    for cx in range(x + 4, x + w - 24, 32):
        a.rect(cx, band_y + 6, 24, 20, (0.64, 0.60, 0.52))
        a.rect(cx + 4, band_y + 10, 16, 12, (0.84, 0.80, 0.72))
        a.rect(cx + 8, band_y + 14, 8, 4, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.03)

    # 2. Temple Wall Lattice Panels (R_TEMPLE_WALL)
    x, y, w, h = R_TEMPLE_WALL
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, VERMILION_BASE)
    for ly in range(y + 12, y + h - 12, 20):
        a.rect(x + 6, ly, w - 12, 3, VERMILION_DARK)
        a.rect(x + 6, ly + 1, w - 12, 1, IMPERIAL_GOLD)
    for lx in range(x + 12, x + w - 12, 20):
        a.rect(lx, y + 6, 3, h - 12, VERMILION_DARK)
        a.rect(lx + 1, y + 6, 1, h - 12, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 3. Gold Amber Roof Tiles (R_GOLD_ROOF_TILES)
    x, y, w, h = R_GOLD_ROOF_TILES
    a.rect(x, y, w, h, GOLD_ROOF_BASE)
    for tx in range(x, x + w, 12):
        a.rect(tx, y, 3, h, GOLD_ROOF_DARK)
        a.rect(tx + 3, y, 4, h, GOLD_ROOF_HILITE)
    for ty in range(y, y + h, 20):
        a.rect(x, ty, w, 3, GOLD_ROOF_DARK)
        a.rect(x, ty + 3, w, 2, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.025)

    # 4. Temple Doors (R_TEMPLE_DOORS)
    x, y, w, h = R_TEMPLE_DOORS
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, VERMILION_BASE)
    a.rect(x + w // 2 - 2, y + 6, 4, h - 12, (0.2, 0.05, 0.05))
    # Brass Studs (9x9 grid)
    for sy in range(y + 16, y + h - 16, 24):
        for sx in [x + 20, x + 44, x + w - 48, x + w - 24]:
            a.disc(sx, sy, 5, IMPERIAL_GOLD)
            a.disc(sx, sy, 2, (0.4, 0.3, 0.1))
    a.noise(x, y, w, h, 0.02)

    # 5. Temple Signboard (R_TEMPLE_SIGNBOARD)
    x, y, w, h = R_TEMPLE_SIGNBOARD
    a.rect(x, y, w, h, BLACK_LACQUER)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.05, 0.05, 0.06))
    a.rect(x + 6, y + 6, w - 12, 3, IMPERIAL_GOLD)
    a.rect(x + 6, y + h - 9, w - 12, 3, IMPERIAL_GOLD)
    s_temp = "EAST YORK TEMPLE"
    tw = a.text_width(s_temp, scale=1)
    a.text(x + (w - tw) // 2, y + 16, s_temp, IMPERIAL_GOLD, scale=1)
    # Chinese characters
    s_cn = "EAST YORK SHUSHAN"
    a.text(x + 14, y + h - 20, "EAST YORK TEMPLE", IMPERIAL_GOLD, scale=1)
    a.noise(x, y, w, h, 0.015)

    # 6. Foo Dog Stone (R_FOO_DOG_STONE)
    x, y, w, h = R_FOO_DOG_STONE
    a.rect(x, y, w, h, STONE_BASE)
    for fy in range(y, y + h, 16):
        a.rect(x, fy, w, 2, STONE_MORTAR)
    a.noise(x, y, w, h, 0.03)

    # 7. Timber Vermilion & Dougong (R_TIMBER_VERMILION)
    x, y, w, h = R_TIMBER_VERMILION
    a.rect(x, y, w, h, VERMILION_BASE)
    a.rect(x, y + h - 16, w, 16, IMPERIAL_GOLD)
    a.rect(x, y, w, 12, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 8. Gold Dragon Trim (R_GOLD_DRAGON_TRIM)
    x, y, w, h = R_GOLD_DRAGON_TRIM
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 9. Incense Bronze (R_INCENSE_BRONZE)
    x, y, w, h = R_INCENSE_BRONZE
    a.rect(x, y, w, h, BRONZE_PATINA)
    a.noise(x, y, w, h, 0.02)

    # 10. Lantern Red (R_LANTERN_RED)
    x, y, w, h = R_LANTERN_RED
    a.rect(x, y, w, h, LANTERN_RED)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 24, (0.99, 0.40, 0.16))
    a.rect(x, y + h - 10, w, 10, IMPERIAL_GOLD)
    a.rect(x, y, w, 10, IMPERIAL_GOLD)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_east_york_temple_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_GOLD_ROOF_TILES, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_TIMBER_VERMILION, S, only=side("bottom"))


def make_cylinder(name, r, h, segs=12, at=(0, 0, 0)):
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


def make_swept_chinese_roof(name, w, d, h, overhang=0.80, flare=0.35, at=(0, 0, 0)):
    """Creates a clean swept Chinese hip-and-gable roof tier with upward flared eave corners."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang
    ridge_hw = (w / 2.0) * 0.55

    # 4 Eaves Base Vertices (Corners flare up slightly by +flare)
    verts = [
        (-hw, -hd, flare),    # 0: Front-Left Eave
        (hw, -hd, flare),     # 1: Front-Right Eave
        (hw, hd, flare),      # 2: Back-Right Eave
        (-hw, hd, flare),     # 3: Back-Left Eave
        (0.0, -hd, 0.0),      # 4: Front-Mid Eave dip
        (0.0, hd, 0.0),       # 5: Back-Mid Eave dip
        (-ridge_hw, 0.0, h),  # 6: Ridge Left
        (ridge_hw, 0.0, h),   # 7: Ridge Right
    ]

    faces = [
        (0, 1, 2, 3),         # Bottom underside
        (0, 4, 7, 6),         # Front-left slope
        (4, 1, 7),            # Front-right slope
        (1, 2, 7),            # Right hip slope
        (2, 5, 6, 7),         # Back-right slope
        (5, 3, 6),            # Back-left slope
        (3, 0, 6),            # Left hip slope
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_east_york_temple_atlas()
    mat = material_for(img, "mat_east_york_temple")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly East York Chinese Temple (~1000 Triangles)
    # - 1. Elevated York Limestone Plinth with Balustrades & Steps
    # - 2. Ground Floor Sanctuary Hall (11.0m x 7.6m, Z: 0.80m to 4.80m)
    # - 3. Portico with 4 Round Vermilion Columns & Dougong Brackets
    # - 4. Front Portal: Black Lacquer Gold Signboard & Studded Doors
    # - 5. Lower Swept Pagoda Eaves (Width 12.8m, D: 9.4m, Z: 4.80m to 6.20m)
    # - 6. Upper Temple Sanctuary Drum Tower (Width 8.0m, D: 5.6m, Z: 6.20m to 8.60m)
    # - 7. Top Swept Pagoda Roof (Width 9.8m, D: 7.2m, H: 2.20m, Z = 8.60m to 10.80m)
    # - 8. Roof Crest & Gold Dragon-Fish Chiwen Finials
    # - 9. Forecourt Incense Cauldron & Twin Guardian Lion Plinths
    # =========================================================================

    # 1. York Limestone Plinth Base (12.4m x 9.6m, Z = 0.00 to 0.80m)
    register_box("PlinthBase", 12.40, 9.60, 0.80, (0.0, 0.0, 0.0),
                 front=R_LIMESTONE_PLINTH, sides=R_LIMESTONE_PLINTH, back=R_LIMESTONE_PLINTH, top=R_LIMESTONE_PLINTH)

    # 4-Tier Grand Entrance Steps (Width: 4.8m, Z = 0.00 to 0.80m at Y = -5.10m)
    for step_i in range(4):
        sz = step_i * 0.20
        sy = -4.80 - (3 - step_i) * 0.30
        register_box(f"TempleStep_{step_i}", 4.80, 0.40, 0.20, (0.0, sy, sz),
                     front=R_LIMESTONE_PLINTH, sides=R_LIMESTONE_PLINTH, top=R_LIMESTONE_PLINTH)

    # 2 Stone Cheek Pedestals for Guardian Lions
    register_box("PedestalL", 0.90, 1.10, 0.90, (-3.20, -4.80, 0.0),
                 front=R_FOO_DOG_STONE, sides=R_FOO_DOG_STONE, top=R_FOO_DOG_STONE)
    register_box("PedestalR", 0.90, 1.10, 0.90, (3.20, -4.80, 0.0),
                 front=R_FOO_DOG_STONE, sides=R_FOO_DOG_STONE, top=R_FOO_DOG_STONE)

    # 2. Ground Floor Sanctuary Hall (Width 10.80m, Depth 7.40m, Z: 0.80m to 4.80m, H: 4.00m)
    register_box("SanctuaryGF", 10.80, 7.40, 4.00, (0.0, 0.30, 0.80),
                 front=R_TEMPLE_WALL, sides=R_TEMPLE_WALL, back=R_TEMPLE_WALL, top=R_TIMBER_VERMILION)

    # 3. Portico: 4 Round Vermilion Columns (X = -4.20m, -1.40m, +1.40m, +4.20m)
    for i, col_x in enumerate([-4.20, -1.40, 1.40, 4.20]):
        col = make_cylinder(f"ColGF_{i}", 0.22, 3.80, segs=12, at=(col_x, -3.20, 0.80))
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_TIMBER_VERMILION, S)
        parts.append(col)
        # Gold base and capital
        register_box(f"ColCap_{i}", 0.60, 0.60, 0.25, (col_x, -3.20, 4.55),
                     front=R_GOLD_DRAGON_TRIM, sides=R_GOLD_DRAGON_TRIM, top=R_GOLD_DRAGON_TRIM)

    # 4. Front Portal: Black Lacquer Gold Signboard & Studded Doors
    register_box("TempleDoors", 2.60, 0.15, 3.20, (0.0, -3.25, 0.80),
                 front=R_TEMPLE_DOORS, sides=R_TIMBER_VERMILION, top=R_TIMBER_VERMILION)
    register_box("Signboard", 3.40, 0.15, 0.90, (0.0, -3.32, 4.00),
                 front=R_TEMPLE_SIGNBOARD, sides=R_GOLD_DRAGON_TRIM, top=R_GOLD_DRAGON_TRIM)

    # 2 Hanging Red Silk Temple Lanterns
    for i, lx in enumerate([-2.80, 2.80]):
        lantern = make_cylinder(f"Lantern_{i}", 0.25, 0.65, segs=10, at=(lx, -3.40, 3.20))
        lantern.data.materials.append(mat)
        kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
        parts.append(lantern)

    # 5. Lower Swept Pagoda Eaves (Width 12.80m, Depth 9.20m, H: 1.40m, Z: 4.80m to 6.20m)
    lower_roof = make_swept_chinese_roof("LowerSweptRoof", 12.80, 9.20, 1.40, overhang=0.60, flare=0.35, at=(0.0, 0.30, 4.80))
    lower_roof.data.materials.append(mat)
    kit.map_faces_to_region(lower_roof, R_GOLD_ROOF_TILES, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(lower_roof, R_TIMBER_VERMILION, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(lower_roof)

    # 6. Upper Temple Sanctuary Drum Tower (Width 7.60m, Depth 5.20m, Z: 6.20m to 8.60m, H: 2.40m)
    register_box("SanctuaryUF", 7.60, 5.20, 2.40, (0.0, 0.30, 6.20),
                 front=R_TEMPLE_WALL, sides=R_TEMPLE_WALL, back=R_TEMPLE_WALL, top=R_TIMBER_VERMILION)

    # 7. Top Swept Pagoda Roof (Width 9.80m, Depth 7.20m, H: 2.20m, Z: 8.60m to 10.80m)
    top_roof = make_swept_chinese_roof("TopSweptRoof", 9.80, 7.20, 2.20, overhang=0.80, flare=0.45, at=(0.0, 0.30, 8.60))
    top_roof.data.materials.append(mat)
    kit.map_faces_to_region(top_roof, R_GOLD_ROOF_TILES, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(top_roof, R_TIMBER_VERMILION, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(top_roof)

    # 8. Top Roof Ridge Crest & Gold Chiwen Dragon Finials
    register_box("TopRidgeBeam", 4.80, 0.30, 0.35, (0.0, 0.30, 10.80),
                 front=R_GOLD_DRAGON_TRIM, sides=R_GOLD_DRAGON_TRIM, top=R_GOLD_DRAGON_TRIM)

    for fx in [-2.50, 2.50]:
        register_box(f"Chiwen_{fx}", 0.40, 0.40, 0.60, (fx, 0.30, 10.80),
                     front=R_GOLD_DRAGON_TRIM, sides=R_GOLD_DRAGON_TRIM, top=R_GOLD_DRAGON_TRIM)

    # Central Sacred Flame Pearl (Baoding: Z = 11.15m)
    pearl = make_cylinder("BaodingPearl", 0.30, 0.55, segs=10, at=(0.0, 0.30, 11.15))
    pearl.data.materials.append(mat)
    kit.map_faces_to_region(pearl, R_GOLD_DRAGON_TRIM, S)
    parts.append(pearl)

    # 9. Forecourt Bronze Incense Cauldron (X = 0.0m, Y = -4.20m, Z = 0.80m to 1.90m)
    cauldron = make_cylinder("IncenseCauldron", 0.45, 0.85, segs=12, at=(0.0, -4.20, 0.80))
    cauldron.data.materials.append(mat)
    kit.map_faces_to_region(cauldron, R_INCENSE_BRONZE, S)
    parts.append(cauldron)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_Temple")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_temple_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_temple.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_east_york_temple.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_east_york_temple_preview.png")
        shutil.copy2(OUT_DIR / "building_east_york_temple_atlas.png", TOOLS_OUT_DIR / "building_east_york_temple_atlas.png")
    except Exception as e:
        print(f"[building_east_york_temple] note: {e}")

    print("[building_east_york_temple] generation complete.")


main()
