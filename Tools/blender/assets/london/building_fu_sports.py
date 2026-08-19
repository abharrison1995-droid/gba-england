"""F.U. Sports Storefront Building (10.0m x 7.0m Commercial Retail Unit).

Specs:
- 10.0m x 7.0m footprint, Height: 5.4m to parapet top.
- Iconic bright yellow & red illuminated commercial fascia sign: "F.U. SPORTS - FOOTWEAR - APPAREL - EQUIPMENT".
- Wide glass shopfront display windows with sports trainers, tracksuits, and red sale clearance posters.
- Blue-accented commercial glass double entrance doors.
- Weathered London stock brick walls with stone parapet cornice, side hanging sign, and pavement apron.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_fu_sports.py
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
R_FASCIA_SIGN   = (0,   384, 512, 128)   # Full-width "F.U. SPORTS" yellow & red bold storefront sign
R_SHOP_DISPLAY  = (0,   128, 256, 256)   # Glazed window with tracksuits, trainers & sale posters
R_SHOP_DOORS    = (256, 128, 128, 256)   # Blue header commercial glass double doors
R_STONE_TRIM    = (384, 256, 128, 128)   # Dressed stone parapet coping, sills & pavement
R_HANGING_SIGN  = (384, 128, 128, 128)   # Double-sided hanging projecting sign
R_BRICK_WALL    = (0,   0,   256, 128)   # London brown/stock brick side and rear walls
R_ROOF_GRAVEL   = (256, 0,   128, 128)   # Flat bitumen/gravel roof with water stains
R_LOUVRE_VENT   = (384, 0,   128, 128)   # Upper pediment clerestory louvre / AC unit

# --- Palette Colors ---
SPORT_YELLOW    = (0.98, 0.85, 0.05)
SPORT_RED       = (0.86, 0.08, 0.08)
SPORT_BLUE      = (0.10, 0.35, 0.65)
SPORT_WHITE     = (0.95, 0.95, 0.94)
BRICK_BROWN     = (0.46, 0.34, 0.26)
BRICK_MORTAR    = (0.64, 0.61, 0.56)
ALUM_GREY       = (0.28, 0.30, 0.32)
GLASS_SHOP      = (0.16, 0.20, 0.24)
STONE_CREAM     = (0.78, 0.75, 0.68)
ROOF_DARK       = (0.34, 0.35, 0.36)


def paint_fu_sports_atlas():
    a = Atlas(S, seed=1701)

    # 1. Iconic "F.U. SPORTS" Giant Fascia Sign (R_FASCIA_SIGN)
    x, y, w, h = R_FASCIA_SIGN
    a.rect(x, y, w, h, SPORT_YELLOW)
    # Heavy Red outer and inner border frame
    a.rect(x, y, w, 8, SPORT_RED)
    a.rect(x, y + h - 8, w, 8, SPORT_RED)
    a.rect(x, y, 8, h, SPORT_RED)
    a.rect(x + w - 8, y, 8, h, SPORT_RED)

    # Giant "F.U. SPORTS" bold letter blocks (scale=7)
    sign_str = "F.U. SPORTS"
    tw = a.text_width(sign_str, scale=7)
    tx = x + (w - tw) // 2
    ty = y + h - 14
    # Deep shadow + bold red
    a.text(tx + 4, ty - 4, sign_str, (0.45, 0.04, 0.04), scale=7)
    a.text(tx, ty, sign_str, SPORT_RED, scale=7)

    # Subtitle: "FOOTWEAR - APPAREL - EQUIPMENT"
    a.rect(x + 12, y + 10, w - 24, 24, (0.10, 0.10, 0.12))
    sub_str = "FOOTWEAR - APPAREL - EQUIPMENT"
    sw = a.text_width(sub_str, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 27, sub_str, SPORT_YELLOW, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 2. Glazed Shopfront Display (R_SHOP_DISPLAY)
    x, y, w, h = R_SHOP_DISPLAY
    a.rect(x, y, w, h, ALUM_GREY)
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_SHOP)
    # Aluminium window mullions
    a.rect(x + w // 2 - 2, y, 4, h, ALUM_GREY)
    # Sports trainer display shelves
    for sy in range(y + 24, y + 110, 28):
        a.rect(x + 12, sy, w - 24, 3, (0.75, 0.75, 0.78))
        # Trainer silhouettes
        for shx in range(x + 20, x + w - 40, 45):
            a.rect(shx, sy + 3, 22, 12, SPORT_WHITE)
            a.rect(shx + 4, sy + 15, 14, 4, SPORT_RED)
    # Clearance SALE poster (Bright red/yellow)
    a.rect(x + 20, y + h - 85, 80, 65, SPORT_RED)
    a.rect(x + 24, y + h - 81, 72, 57, SPORT_YELLOW)
    a.rect(x + 32, y + h - 55, 56, 16, SPORT_RED)
    a.noise(x, y, w, h, 0.025)

    # 3. Commercial Shop Doors (R_SHOP_DOORS)
    x, y, w, h = R_SHOP_DOORS
    a.rect(x, y, w, h, ALUM_GREY)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_SHOP)
    # Blue branding header stripe
    a.rect(x + 4, y + h - 34, w - 8, 26, SPORT_BLUE)
    a.rect(x + 12, y + h - 24, w - 24, 8, SPORT_WHITE)
    # Door central split & push bars
    a.rect(x + w // 2 - 2, y, 4, h, ALUM_GREY)
    a.rect(x + 10, y + 90, w - 20, 6, (0.85, 0.85, 0.88))
    # Bottom kickplates
    a.rect(x + 4, y + 4, w - 8, 30, (0.38, 0.40, 0.42))
    a.noise(x, y, w, h, 0.025)

    # 4. Brick Wall (R_BRICK_WALL)
    x, y, w, h = R_BRICK_WALL
    a.bricks(x, y, w, h, brick=BRICK_BROWN, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)

    # 5. Roof Bitumen & Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, ROOF_DARK)
    a.noise(x, y, w, h, 0.045)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for qy in range(y, y + h, 24):
        a.rect(x, qy, w, 2, (0.55, 0.52, 0.46))
    a.noise(x, y, w, h, 0.03)

    # 7. Projecting Hanging Sign (R_HANGING_SIGN)
    x, y, w, h = R_HANGING_SIGN
    a.rect(x, y, w, h, (0.22, 0.22, 0.24))
    a.rect(x + 8, y + 8, w - 16, h - 16, SPORT_YELLOW)
    a.rect(x + 14, y + 14, w - 28, h - 28, SPORT_RED)
    a.rect(x + 22, y + h // 2 - 8, w - 44, 16, SPORT_WHITE)
    a.noise(x, y, w, h, 0.02)

    # 8. Clerestory Louvre / Vent (R_LOUVRE_VENT)
    x, y, w, h = R_LOUVRE_VENT
    a.rect(x, y, w, h, STONE_CREAM)
    vx, vy, vw, vh = x + 10, y + 10, w - 20, h - 20
    a.rect(vx, vy, vw, vh, (0.20, 0.22, 0.24))
    for ly in range(vy + 6, vy + vh - 6, 8):
        a.rect(vx + 4, ly, vw - 8, 4, (0.35, 0.38, 0.40))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_fu_sports_atlas", OUT_DIR)


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


def main():
    kit.reset_scene()
    img = paint_fu_sports_atlas()
    mat = material_for(img, "mat_fu_sports")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # F.U. Sports Retail Building (10.0m x 7.0m Modular Footprint)
    # - Main Shop Shell: 10.0m x 6.5m, Height: 4.8m (Z: 0.10 to 4.90m)
    # - Large Yellow/Red Fascia Sign: 9.6m x 0.35m x 1.30m (Z = 3.20m to 4.50m)
    # - Glazed Window Displays (Left & Right) & Central Glass Entrance Doors
    # - Upper Clerestory Pediment Louvre & Side Projecting Sign
    # =========================================================================

    # 1. Front Pavement Base (10.0m x 7.5m, Z = 0.00 to 0.10m)
    register_box("ShopPavement", 10.0, 7.50, 0.10, (0.0, -0.25, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Building Body (10.0m x 6.5m, Z: 0.10 to 4.70m, H: 4.60m)
    register_box("ShopBody", 10.0, 6.50, 4.60, (0.0, 0.25, 0.10),
                 front=R_BRICK_WALL, sides=R_BRICK_WALL, back=R_BRICK_WALL)

    # 3. Parapet Cornice & Flat Gravel Roof (Z = 4.70 to 5.10m)
    register_box("ParapetCornice", 10.20, 6.70, 0.40, (0.0, 0.25, 4.70),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_ROOF_GRAVEL)

    # 4. Upper Decorative Pediment Centerpiece (Z = 5.10 to 5.75m)
    register_box("UpperPediment", 3.60, 0.40, 0.65, (0.0, -3.05, 5.10),
                 front=R_LOUVRE_VENT, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Prominent "F.U. SPORTS" Giant Illuminated Fascia Sign (Z = 3.10m to 4.55m)
    register_box("FasciaSignBoard", 9.80, 0.35, 1.45, (0.0, -3.18, 3.10),
                 front=R_FASCIA_SIGN, sides=R_FASCIA_SIGN, top=R_STONE_TRIM)

    # 6. Central Commercial Glass Entrance Doors (X = 0.0m, Z = 0.10 to 3.10m, H: 3.0m)
    register_box("EntranceDoors", 2.60, 0.18, 3.00, (0.0, -3.08, 0.10),
                 front=R_SHOP_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 7. Flanking Large Display Windows (Left X = -3.15m, Right X = +3.15m)
    register_box("WindowLeft", 3.20, 0.18, 3.00, (-3.15, -3.08, 0.10),
                 front=R_SHOP_DISPLAY, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("WindowRight", 3.20, 0.18, 3.00, (3.15, -3.08, 0.10),
                 front=R_SHOP_DISPLAY, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Side Projecting Hanging Sign (Left corner: X = -4.90m, Y = -2.8m, Z = 3.2m)
    register_box("SignPost", 0.08, 0.08, 2.40, (-4.90, -2.80, 2.20),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("HangingSign", 0.10, 0.90, 0.90, (-4.90, -2.80, 3.40),
                 front=R_STONE_TRIM, sides=R_HANGING_SIGN, top=R_STONE_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_FU_Sports")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_fu_sports_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_fu_sports.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_fu_sports.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_fu_sports_preview.png")
        shutil.copy2(OUT_DIR / "building_fu_sports_atlas.png", TOOLS_OUT_DIR / "building_fu_sports_atlas.png")
    except Exception as e:
        print(f"[building_fu_sports] note: {e}")

    print("[building_fu_sports] generation complete.")


main()
