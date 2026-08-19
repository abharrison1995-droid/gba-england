"""East York Yuan Warehouse / 元倉 (High-Poly ~1000 Tris).

Architectural Specs:
- East York's notorious discount bargain warehouse & pound shop: "YUAN WAREHOUSE / 元倉"
- Sells cheap contraband, discount weapons, fireworks, knick-knacks, and vapes
- Dimensions: 10.0m x 7.0m footprint, 6.2m height
- Fascia Sign: Bold Red & Yellow: "YUAN WAREHOUSE 元倉 - EVERYTHING 1 YUAN / £1 - WEAPONS & FIREWORKS"
- Storefront: Sticker-plastered glass displays, commercial double sliding doors, bargain dump crates out front
- Roof: Clean Asian pitched hip-and-gable roof with glazed jade ceramic tiles, gold ridge ornaments & dragon finials (no banner bleed)
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_east_york_yuan_warehouse.py
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
R_FASCIA_SIGN   = (0,   384, 512, 128)   # Full-width "YUAN WAREHOUSE 元倉" sign
R_SHOP_DISPLAY  = (0,   128, 256, 256)   # Glazed window plastered in sale stickers & weapon crates
R_SHOP_DOORS    = (256, 128, 128, 256)   # Commercial sliding doors & clearance stickers
R_ROOF_JADE     = (384, 128, 128, 256)   # Glazed jade ceramic roof tiles & ridges
R_BRICK_WALL    = (0,   0,   256, 128)   # Weathered red brick walls
R_STONE_TRIM    = (256, 0,   128, 128)   # Concrete coping, sills & threshold
R_CRATE_BOX     = (384, 0,   64,  128)   # Discount wooden crates & dump bins
R_GOLD_TRIM     = (448, 0,   64,  128)   # Gold dragon finials & trims

# --- Palette Colors ---
DISCOUNT_RED    = (0.84, 0.08, 0.08)
DISCOUNT_YELLOW = (0.98, 0.88, 0.05)
IMPERIAL_GOLD   = (0.90, 0.74, 0.18)
BRICK_RED       = (0.48, 0.20, 0.15)
BRICK_MORTAR    = (0.66, 0.63, 0.56)
JADE_ROOF       = (0.15, 0.35, 0.26)
JADE_DARK       = (0.08, 0.20, 0.14)
JADE_LIGHT      = (0.25, 0.52, 0.38)
GLASS_SHOP      = (0.12, 0.16, 0.20)
CONCRETE_GREY   = (0.65, 0.63, 0.58)
CRATE_BROWN     = (0.58, 0.44, 0.28)


def paint_east_york_yuan_warehouse_atlas():
    a = Atlas(S, seed=8888)

    # 1. Iconic "YUAN WAREHOUSE 元倉" Fascia Sign (R_FASCIA_SIGN)
    x, y, w, h = R_FASCIA_SIGN
    a.rect(x, y, w, h, DISCOUNT_RED)
    a.rect(x, y, w, 8, DISCOUNT_YELLOW)
    a.rect(x, y + h - 8, w, 8, DISCOUNT_YELLOW)
    a.rect(x, y, 8, h, DISCOUNT_YELLOW)
    a.rect(x + w - 8, y, 8, h, DISCOUNT_YELLOW)

    sign_str = "YUAN WAREHOUSE"
    tw = a.text_width(sign_str, scale=5)
    tx = x + 20
    ty = y + h - 18
    a.text(tx + 3, ty - 3, sign_str, (0.40, 0.04, 0.04), scale=5)
    a.text(tx, ty, sign_str, DISCOUNT_YELLOW, scale=5)

    # Large Chinese "元倉" block on right
    for idx, cx in enumerate(range(x + tw + 36, x + w - 28, 36)):
        a.rect(cx, y + h - 68, 30, 48, DISCOUNT_YELLOW)
        a.rect(cx + 4, y + h - 64, 22, 40, DISCOUNT_RED)
        a.rect(cx + 8, y + h - 56, 14, 24, DISCOUNT_YELLOW)

    # Subtitle: "EVERYTHING 1 YUAN / £1 - WEAPONS & FIREWORKS"
    a.rect(x + 16, y + 14, w - 32, 24, (0.10, 0.10, 0.12))
    sub_str = "EVERYTHING 1 YUAN / £1 - WEAPONS - FIREWORKS"
    sw = a.text_width(sub_str, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 30, sub_str, DISCOUNT_YELLOW, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 2. Glazed Display Window (R_SHOP_DISPLAY)
    x, y, w, h = R_SHOP_DISPLAY
    a.rect(x, y, w, h, GLASS_SHOP)
    a.rect(x, y, w, 8, DISCOUNT_RED)
    a.rect(x, y + h - 8, w, 8, DISCOUNT_RED)
    a.rect(x, y, 8, h, DISCOUNT_RED)
    a.rect(x + w - 8, y, 8, h, DISCOUNT_RED)
    # Clearance Stickers ("1元", "HOT SALE")
    for sx, sy, sw, sh in [(x + 20, y + 140, 50, 40), (x + 80, y + 80, 44, 34), (x + 140, y + 150, 60, 45)]:
        a.rect(sx, sy, sw, sh, DISCOUNT_YELLOW)
        a.rect(sx + 3, sy + 3, sw - 6, sh - 6, DISCOUNT_RED)
    a.noise(x, y, w, h, 0.02)

    # 3. Commercial Doors (R_SHOP_DOORS)
    x, y, w, h = R_SHOP_DOORS
    a.rect(x, y, w, h, (0.20, 0.05, 0.05))
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_SHOP)
    a.rect(x + w // 2 - 2, y + 6, 4, h - 12, DISCOUNT_RED)
    a.rect(x + 16, y + 40, w - 32, 28, DISCOUNT_YELLOW)
    a.rect(x + 18, y + 42, w - 36, 24, DISCOUNT_RED)
    a.noise(x, y, w, h, 0.015)

    # 4. Glazed Jade Roof Tiles (R_ROOF_JADE)
    x, y, w, h = R_ROOF_JADE
    a.rect(x, y, w, h, JADE_ROOF)
    for tx in range(x, x + w, 12):
        a.rect(tx, y, 3, h, JADE_DARK)
        a.rect(tx + 3, y, 4, h, JADE_LIGHT)
    for ty in range(y, y + h, 20):
        a.rect(x, ty, w, 3, JADE_DARK)
        a.rect(x, ty + 3, w, 2, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.025)

    # 5. Red Brick Wall (R_BRICK_WALL)
    x, y, w, h = R_BRICK_WALL
    a.bricks(x, y, w, h, brick=BRICK_RED, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.04)
    a.noise(x, y, w, h, 0.03)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, CONCRETE_GREY)
    for sy in range(y, y + h, 24):
        a.rect(x, sy, w, 2, (0.45, 0.43, 0.40))
    a.noise(x, y, w, h, 0.02)

    # 7. Discount Crates (R_CRATE_BOX)
    x, y, w, h = R_CRATE_BOX
    a.rect(x, y, w, h, CRATE_BROWN)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.40, 0.30, 0.18))
    a.rect(x + 8, y + h // 2 - 10, w - 16, 20, DISCOUNT_RED)
    a.text(x + 10, y + h // 2 - 4, "1 YUAN", DISCOUNT_YELLOW, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 8. Gold Trim (R_GOLD_TRIM)
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_east_york_yuan_warehouse_atlas", OUT_DIR)


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
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang
    ridge_hw = (w / 2.0) * 0.70

    verts = [
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
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
    img = paint_east_york_yuan_warehouse_atlas()
    mat = material_for(img, "mat_east_york_yuan_warehouse")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Yuan Warehouse (~900 Triangles)
    # =========================================================================

    # 1. Pavement Slab Plinth (10.6m x 8.4m, Z = 0.00 to 0.15m)
    register_box("FrontPavement", 10.60, 8.40, 0.15, (0.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Warehouse Brick Shell (Width 9.80m, Depth 6.60m, Z: 0.15m to 4.85m, H: 4.70m)
    register_box("WarehouseCore", 9.80, 6.60, 4.70, (0.0, 0.40, 0.15),
                 front=R_BRICK_WALL, sides=R_BRICK_WALL, back=R_BRICK_WALL, top=R_STONE_TRIM)

    # 3. Storefront:
    # - Left Large Display Window (X = -2.60m)
    register_box("ShopDisplayWin", 4.40, 0.20, 2.70, (-2.60, -2.95, 0.15),
                 front=R_SHOP_DISPLAY, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # - Right Commercial Sliding Doors (X = +2.40m)
    register_box("ShopDoors", 2.40, 0.20, 2.70, (2.40, -2.95, 0.15),
                 front=R_SHOP_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # - Flanking Vermilion Columns with Gold Capitals
    for px in [-4.85, -0.40, 4.85]:
        col = make_cylinder(f"Col_{px:.1f}", 0.16, 2.85, segs=12, at=(px, -3.00, 0.15))
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_GOLD_TRIM, S)
        parts.append(col)

    # - Piled Discount Bargain Crates out front
    for i, (cx, cy, cz, cw, cd, ch) in enumerate([
        (-4.20, -3.50, 0.15, 0.80, 0.60, 0.50),
        (-3.90, -3.40, 0.65, 0.60, 0.50, 0.40),
        (-1.20, -3.50, 0.15, 0.70, 0.55, 0.45),
    ]):
        register_box(f"Crate_{i}", cw, cd, ch, (cx, cy, cz),
                     front=R_CRATE_BOX, sides=R_CRATE_BOX, top=R_CRATE_BOX)

    # 4. Giant "YUAN WAREHOUSE 元倉" Fascia Signboard (Width 9.80m, H: 1.45m, Z = 2.90m to 4.35m)
    register_box("FasciaSign", 9.80, 0.25, 1.45, (0.0, -3.05, 2.90),
                 front=R_FASCIA_SIGN, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # 5. Parapet Cornice Band (10.20m x 7.00m, Z = 4.85m to 5.20m)
    register_box("ParapetCornice", 10.20, 7.00, 0.35, (0.0, 0.40, 4.85),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, back=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Clean Glazed Jade Ceramic Roof (Width 10.40m, Depth 7.20m, H: 1.50m, Z = 5.20m to 6.70m)
    roof = make_clean_pitched_roof("JadePitchedRoof", 10.40, 7.20, 1.50, overhang=0.35, at=(0.0, 0.40, 5.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_JADE, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.1)
    parts.append(roof)

    # Gold Dragon Finials on Ridge Ends
    for fx in [-3.70, 3.70]:
        register_box(f"DragonFinial_{fx}", 0.35, 0.35, 0.45, (fx, 0.40, 6.70),
                     front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # Central Roof Crest
    register_box("RoofRidgeCrest", 4.80, 0.25, 0.20, (0.0, 0.40, 6.70),
                 front=R_GOLD_TRIM, sides=R_GOLD_TRIM, top=R_GOLD_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_East_York_Yuan_Warehouse")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_east_york_yuan_warehouse_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_east_york_yuan_warehouse.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_east_york_yuan_warehouse.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_east_york_yuan_warehouse_preview.png")
        shutil.copy2(OUT_DIR / "building_east_york_yuan_warehouse_atlas.png", TOOLS_OUT_DIR / "building_east_york_yuan_warehouse_atlas.png")
    except Exception as e:
        print(f"[building_east_york_yuan_warehouse] note: {e}")

    print("[building_east_york_yuan_warehouse] generation complete.")


main()
