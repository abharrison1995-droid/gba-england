"""East York F.U. Sports & Kung Fu Martial Arts Emporium (High-Poly ~1000 Tris).

Architectural Specs:
- East York Chinatown branch of F.U. Sports: "F.U. SPORTS / 功夫體育" (Martial Arts, Tracksuits & Kicks)
- Dimensions: 10.0m x 7.0m footprint, 6.2m height
- Fascia Sign: Bold High-Contrast Yellow & Vermilion Red: "F.U. SPORTS 功夫體育 - MARTIAL ARTS - FOOTWEAR - APPAREL"
- Storefront Displays: Wide glass windows showcasing yellow martial arts tracksuits, dragon gis, trainers & sale banners
- Entrance: Flanking vermilion columns with gold capitals, commercial double glass doors, hanging red silk lanterns
- Roof: Clean Asian swept hip-and-gable roof with glazed imperial green ceramic tiles, gold ridge ornaments & dragon corner finials (no banner bleed)
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_fu_sports.py
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

# --- Atlas Region Definitions (x, y, w, h) ---
R_FASCIA_SIGN   = (0,   384, 512, 128)   # Full-width "F.U. SPORTS 功夫體育" sign
R_SHOP_DISPLAY  = (0,   128, 256, 256)   # Glazed window with martial arts tracksuits & kicks
R_SHOP_DOORS    = (256, 128, 128, 256)   # Vermilion & glass commercial double entrance doors
R_ROOF_GREEN    = (384, 128, 128, 256)   # Glazed imperial green ceramic roof tiles & bamboo roll ribs
R_BRICK_WALL    = (0,   0,   256, 128)   # Red brick side and rear walls
R_STONE_TRIM    = (256, 0,   128, 128)   # Portland stone parapet coping, sills & threshold
R_GOLD_TRIM     = (384, 0,   64,  128)   # Gold dragon finials & vermilion columns
R_LANTERN_RED   = (448, 0,   64,  128)   # Hanging red silk lanterns

# --- Palette Colors ---
SPORT_YELLOW    = (0.98, 0.85, 0.05)
SPORT_RED       = (0.86, 0.08, 0.08)
VERMILION_DARK  = (0.45, 0.06, 0.04)
IMPERIAL_GOLD   = (0.92, 0.76, 0.18)
BRICK_RED       = (0.50, 0.22, 0.16)
BRICK_MORTAR    = (0.68, 0.65, 0.58)
GREEN_ROOF      = (0.16, 0.42, 0.28)
GREEN_DARK      = (0.08, 0.24, 0.15)
GREEN_LIGHT     = (0.25, 0.60, 0.40)
GLASS_SHOP      = (0.14, 0.18, 0.22)
STONE_CREAM     = (0.78, 0.75, 0.68)
LANTERN_RED     = (0.88, 0.10, 0.06)


def paint_east_york_fu_sports_atlas():
    a = Atlas(S, seed=7891)

    # 1. Iconic "F.U. SPORTS 功夫體育" Fascia Sign (R_FASCIA_SIGN)
    x, y, w, h = R_FASCIA_SIGN
    a.rect(x, y, w, h, SPORT_YELLOW)
    # Vermilion outer frame & gold inner borders
    a.rect(x, y, w, 8, SPORT_RED)
    a.rect(x, y + h - 8, w, 8, SPORT_RED)
    a.rect(x, y, 8, h, SPORT_RED)
    a.rect(x + w - 8, y, 8, h, SPORT_RED)
    a.rect(x + 10, y + 10, w - 20, 3, IMPERIAL_GOLD)
    a.rect(x + 10, y + h - 13, w - 20, 3, IMPERIAL_GOLD)

    # English "F.U. SPORTS"
    sign_str = "F.U. SPORTS"
    tw = a.text_width(sign_str, scale=6)
    tx = x + 24
    ty = y + h - 18
    a.text(tx + 4, ty - 4, sign_str, (0.45, 0.04, 0.04), scale=6)
    a.text(tx, ty, sign_str, SPORT_RED, scale=6)

    # Chinese "功夫體育" character blocks on right
    for idx, cx in enumerate(range(x + tw + 48, x + w - 32, 28)):
        a.rect(cx, y + h - 68, 24, 48, SPORT_RED)
        a.rect(cx + 3, y + h - 65, 18, 42, SPORT_YELLOW)
        a.rect(cx + 6, y + h - 55, 12, 22, SPORT_RED)
        a.rect(cx + 9, y + h - 50, 6, 12, IMPERIAL_GOLD)

    # Subtitle: "MARTIAL ARTS - FOOTWEAR - APPAREL"
    a.rect(x + 16, y + 14, w - 32, 24, (0.10, 0.10, 0.12))
    sub_str = "MARTIAL ARTS - FOOTWEAR - APPAREL"
    sw = a.text_width(sub_str, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 30, sub_str, SPORT_YELLOW, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 2. Glazed Display Window (R_SHOP_DISPLAY)
    x, y, w, h = R_SHOP_DISPLAY
    a.rect(x, y, w, h, GLASS_SHOP)
    a.rect(x, y, w, 8, SPORT_RED)
    a.rect(x, y + h - 8, w, 8, SPORT_RED)
    a.rect(x, y, 8, h, SPORT_RED)
    a.rect(x + w - 8, y, 8, h, SPORT_RED)
    # Mannequins in yellow tracksuits & kicks
    for mx in [x + 40, x + 140]:
        a.rect(mx, y + 24, 36, 68, SPORT_YELLOW)
        a.rect(mx + 6, y + 92, 24, 24, (0.85, 0.70, 0.55))
        a.rect(mx + 2, y + 40, 32, 4, (0.1, 0.1, 0.1))  # Black belt
    a.text(x + 20, y + h - 28, "KUNG FU SALE", SPORT_RED, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 3. Commercial Doors (R_SHOP_DOORS)
    x, y, w, h = R_SHOP_DOORS
    a.rect(x, y, w, h, VERMILION_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_SHOP)
    a.rect(x + w // 2 - 2, y + 6, 4, h - 12, SPORT_RED)
    a.rect(x + w // 2 - 8, y + h // 2 - 16, 4, 32, IMPERIAL_GOLD)
    a.rect(x + w // 2 + 4, y + h // 2 - 16, 4, 32, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.015)

    # 4. Glazed Imperial Green Roof Tiles (R_ROOF_GREEN)
    x, y, w, h = R_ROOF_GREEN
    a.rect(x, y, w, h, GREEN_ROOF)
    # Bamboo tube tile vertical ridges
    for tx in range(x, x + w, 12):
        a.rect(tx, y, 3, h, GREEN_DARK)
        a.rect(tx + 3, y, 4, h, GREEN_LIGHT)
    # Horizontal drip tile overlaps
    for ty in range(y, y + h, 20):
        a.rect(x, ty, w, 3, GREEN_DARK)
        a.rect(x, ty + 3, w, 2, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.025)

    # 5. Red Brick Wall (R_BRICK_WALL)
    x, y, w, h = R_BRICK_WALL
    a.bricks(x, y, w, h, brick=BRICK_RED, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.04)
    a.noise(x, y, w, h, 0.03)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for sy in range(y, y + h, 24):
        a.rect(x, sy, w, 2, (0.55, 0.52, 0.46))
    a.noise(x, y, w, h, 0.02)

    # 7. Gold Dragon Trim & Pillars (R_GOLD_TRIM)
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, SPORT_RED)
    a.rect(x, y + h - 24, w, 24, IMPERIAL_GOLD)
    a.rect(x, y, w, 16, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 8. Hanging Red Lanterns (R_LANTERN_RED)
    x, y, w, h = R_LANTERN_RED
    a.rect(x, y, w, h, LANTERN_RED)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, (0.98, 0.35, 0.15))
    a.rect(x, y + h - 10, w, 10, IMPERIAL_GOLD)
    a.rect(x, y, w, 10, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_east_york_fu_sports_atlas", OUT_DIR)


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


def make_clean_pitched_roof(name, w, d, h, overhang=0.40, at=(0, 0, 0)):
    """Creates a clean pitched hip/gable roof with overhang."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang
    ridge_hw = (w / 2.0) * 0.70

    verts = [
        # 4 Eaves Base Vertices (Z = 0)
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
        # 2 Ridge Top Vertices (Z = h)
        (-ridge_hw, 0.0, h), (ridge_hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # Bottom face
        (0, 1, 5, 4),    # Front slope
        (1, 2, 5),       # Right hip slope
        (2, 3, 4, 5),    # Back slope
        (3, 0, 4),       # Left hip slope
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_east_york_fu_sports_atlas()
    mat = material_for(img, "mat_east_york_fu_sports")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly F.U. Sports East York (~900 Triangles)
    # =========================================================================

    # 1. Pavement Slab Plinth (10.6m x 8.4m, Z = 0.00 to 0.15m)
    register_box("FrontPavement", 10.60, 8.40, 0.15, (0.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Store Brick Shell (Width 9.80m, Depth 6.60m, Z: 0.15m to 4.85m, H: 4.70m)
    register_box("StoreCore", 9.80, 6.60, 4.70, (0.0, 0.40, 0.15),
                 front=R_BRICK_WALL, sides=R_BRICK_WALL, back=R_BRICK_WALL, top=R_STONE_TRIM)

    # 3. Storefront:
    # - Left Large Display Window (X = -2.60m)
    register_box("ShopDisplayWin", 4.40, 0.20, 2.70, (-2.60, -2.95, 0.15),
                 front=R_SHOP_DISPLAY, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # - Right Commercial Entrance Doors (X = +2.40m)
    register_box("ShopDoors", 2.40, 0.20, 2.70, (2.40, -2.95, 0.15),
                 front=R_SHOP_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # - 3 Flanking Vermilion Columns with Gold Capitals
    for px in [-4.85, -0.40, 4.85]:
        col = make_cylinder(f"Col_{px:.1f}", 0.16, 2.85, segs=12, at=(px, -3.00, 0.15))
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_GOLD_TRIM, S)
        parts.append(col)

    # - Hanging Red Silk Lanterns
    for i, lx in enumerate([1.00, 3.80]):
        lantern = make_cylinder(f"Lantern_{i}", 0.20, 0.50, segs=10, at=(lx, -3.20, 2.35))
        lantern.data.materials.append(mat)
        kit.map_faces_to_region(lantern, R_LANTERN_RED, S)
        parts.append(lantern)

    # 4. Giant "F.U. SPORTS 功夫體育" Fascia Signboard (Width 9.80m, H: 1.45m, Z = 2.90m to 4.35m)
    register_box("FasciaSign", 9.80, 0.25, 1.45, (0.0, -3.05, 2.90),
                 front=R_FASCIA_SIGN, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # 5. Parapet Cornice Band (10.20m x 7.00m, Z = 4.85m to 5.20m)
    register_box("ParapetCornice", 10.20, 7.00, 0.35, (0.0, 0.40, 4.85),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, back=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Clean Glazed Imperial Green Ceramic Roof (Width 10.40m, Depth 7.20m, H: 1.50m, Z = 5.20m to 6.70m)
    roof = make_clean_pitched_roof("GreenPitchedRoof", 10.40, 7.20, 1.50, overhang=0.35, at=(0.0, 0.40, 5.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_GREEN, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.1)
    parts.append(roof)

    # Gold Dragon Finials on Roof Ridge Ends (Left X = -3.70m, Right X = +3.70m at Z = 6.70m)
    for fx in [-3.70, 3.70]:
        register_box(f"DragonFinial_{fx}", 0.35, 0.35, 0.45, (fx, 0.40, 6.70),
                     front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # Central Roof Crest (Z = 6.70m to 7.05m)
    register_box("RoofRidgeCrest", 4.80, 0.25, 0.20, (0.0, 0.40, 6.70),
                 front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_FU_Sports")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_fu_sports_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_fu_sports.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_east_york_fu_sports.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_east_york_fu_sports_preview.png")
        shutil.copy2(OUT_DIR / "building_east_york_fu_sports_atlas.png", TOOLS_OUT_DIR / "building_east_york_fu_sports_atlas.png")
    except Exception as e:
        print(f"[building_east_york_fu_sports] note: {e}")

    print("[building_east_york_fu_sports] generation complete.")


main()
