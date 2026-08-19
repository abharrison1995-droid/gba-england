"""1930s Art Deco / Inter-War London Residential Block (Flats Variant 3).

Architectural Specs:
- 3-4 storey 1930s London Streamline Moderne / Art Deco brick apartment block
- Facade: Smooth warm red/orange brick with horizontal white stone banding lines
- Central vertical stairwell tower with tall continuous Crittall steel stair glazing
- Ground floor curved Streamline entrance canopy over double Crittall steel & glass communal doors
- Flanking multi-pane Crittall steel casement windows with green stone sills and wrap-around corner detail
- Stepped geometric Art Deco roof parapet with central brick tower feature
- Dimensions: 10.0m width x 7.5m depth x 10.8m total height. Modular 10m grid.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_london_flats_03.py
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

# --- Atlas Region Definitions (x, y, w, h) ---
R_BRICK_DECO     = (0,   256, 256, 256)   # Warm 1930s orange/red brick
R_ROOF_GRAVEL    = (0,   128, 256, 128)   # Flat roof gravel/asphalt
R_STONE_BAND     = (0,   64,  256, 64)    # White horizontal stone bands & sills
R_PAVEMENT       = (0,   0,   256, 64)    # Pavement flags
R_BRICK_SIDE     = (256, 256, 128, 256)   # Side brick
R_STAIR_TOWER    = (256, 128, 128, 128)   # Central stair tower brick + canopy
R_PARAPET_DECO   = (256, 64,  128, 64)    # Stepped parapet trim
R_CANOPY_ROOF    = (256, 0,   128, 64)    # Entrance canopy lead/zinc
R_CRITTALL_WIN   = (384, 384, 128, 128)   # Crittall steel casement window
R_STAIR_GLAZING  = (384, 256, 128, 128)   # Tall vertical stairwell glazing
R_DOOR_CRITTALL  = (448, 128, 64,  128)   # Double Crittall steel/glass entrance
R_WINDOW_CORNER  = (384, 128, 64,  128)   # Corner wraparound window
R_DECO_CREST     = (448, 0,   64,  128)   # Art deco brass nameplate & motifs

# --- Palette Colors ---
DECO_BRICK_BASE  = (0.62, 0.30, 0.18)
DECO_MORTAR      = (0.76, 0.74, 0.70)
SIDE_BRICK_BASE  = (0.45, 0.24, 0.16)
STONE_WHITE      = (0.90, 0.89, 0.86)
STONE_DARK       = (0.60, 0.58, 0.54)
GREEN_SILL       = (0.18, 0.35, 0.24)
STEEL_FRAME      = (0.18, 0.20, 0.22)
GLASS_DARK       = (0.08, 0.11, 0.15)
GLASS_HIGHLIGHT  = (0.22, 0.28, 0.36)
DOOR_GREEN       = (0.08, 0.28, 0.16)
BRASS_GOLD       = (0.86, 0.73, 0.24)
CANOPY_LEAD      = (0.34, 0.35, 0.38)
ROOF_GRAVEL_COL  = (0.38, 0.37, 0.36)
PAVE_GREY        = (0.48, 0.47, 0.45)


def paint_artdeco_atlas():
    a = Atlas(S, seed=404)

    # 1. 1930s Warm Brick Facade with Horizontal Stone Bands (R_BRICK_DECO)
    x, y, w, h = R_BRICK_DECO
    a.bricks(x, y, w, h, brick=DECO_BRICK_BASE, mortar=DECO_MORTAR, bw=24, bh=10, jitter=0.07)
    # Streamline horizontal white stone bands
    for by in [y + 40, y + 100, y + 160, y + 220]:
        a.rect(x, by, w, 5, STONE_WHITE)
        a.rect(x, by, w, 1, STONE_DARK)
        a.rect(x, by + 4, w, 1, (0.95, 0.94, 0.92))
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=-0.04, bottom=0.0)

    # 2. Side Brick (R_BRICK_SIDE)
    x, y, w, h = R_BRICK_SIDE
    a.bricks(x, y, w, h, brick=SIDE_BRICK_BASE, mortar=(0.60, 0.58, 0.54), bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.02)

    # 3. Flat Roof Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, ROOF_GRAVEL_COL)
    a.noise(x, y, w, h, 0.05)

    # 4. White Stone Bands (R_STONE_BAND)
    x, y, w, h = R_STONE_BAND
    a.rect(x, y, w, h, STONE_WHITE)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.025)

    # 5. Crittall Steel Casement Window (R_CRITTALL_WIN)
    x, y, w, h = R_CRITTALL_WIN
    a.rect(x, y, w, h, DECO_BRICK_BASE)
    a.noise(x, y, w, h, 0.03)
    # Green glazed tile / stone sill
    a.rect(x + 6, y + 4, w - 12, 10, GREEN_SILL)
    a.rect(x + 6, y + 4, w - 12, 2, (0.10, 0.20, 0.14))
    # Outer white stone surround
    wx, wy, ww, wh = x + 10, y + 14, w - 20, h - 28
    a.rect(wx, wy, ww, wh, STONE_WHITE)
    # Black steel Crittall frame & glass
    gx, gy, gw, gh = wx + 3, wy + 3, ww - 6, wh - 6
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    # 2 vertical steel mullions
    mw = gw // 3
    a.rect(gx + mw - 1, gy, 2, gh, STEEL_FRAME)
    a.rect(gx + 2 * mw - 1, gy, 2, gh, STEEL_FRAME)
    # 3 horizontal glazing bars (classic 1930s horizontal rhythm)
    for hy in range(gy + 14, gy + gh - 10, 16):
        a.rect(gx, hy, gw, 2, STEEL_FRAME)
    # Glass highlights
    a.rect(gx + 4, gy + gh - 24, mw - 8, 12, GLASS_HIGHLIGHT)
    a.rect(gx + 2 * mw + 4, gy + gh - 24, mw - 8, 12, GLASS_HIGHLIGHT)

    # 6. Tall Vertical Stairwell Glazing (R_STAIR_GLAZING)
    x, y, w, h = R_STAIR_GLAZING
    a.rect(x, y, w, h, DECO_BRICK_BASE)
    # White stone surround
    swx, swy, sww, swh = x + 16, y + 8, w - 32, h - 16
    a.rect(swx, swy, sww, swh, STONE_WHITE)
    sgx, sgy, sgw, sgh = swx + 4, swy + 4, sww - 8, swh - 8
    a.rect(sgx, sgy, sgw, sgh, GLASS_DARK)
    # Center vertical steel mullion
    a.rect(sgx + sgw // 2 - 1, sgy, 3, sgh, STEEL_FRAME)
    # Repeating horizontal bars
    for shy in range(sgy + 10, sgy + sgh - 6, 12):
        a.rect(sgx, shy, sgw, 2, STEEL_FRAME)
        a.rect(sgx + 4, shy + 2, (sgw // 2) - 6, 6, GLASS_HIGHLIGHT)
    a.noise(x, y, w, h, 0.02)

    # 7. Crittall Communal Entrance Doors (R_DOOR_CRITTALL)
    x, y, w, h = R_DOOR_CRITTALL
    a.rect(x, y, w, h, STONE_WHITE)  # Stone entrance frame
    dx, dy, dw, dh = x + 4, y, w - 8, h - 6
    a.rect(dx, dy, dw, dh, DOOR_GREEN)
    # Double door split
    mid_dx = dx + dw // 2
    a.rect(mid_dx - 1, dy + 2, 2, dh - 4, (0.04, 0.14, 0.08))
    # Crittall glass panels in both doors
    gw_d = (dw - 12) // 2
    gh_d = dh - 24
    gy_d = dy + 18
    a.rect(dx + 4, gy_d, gw_d, gh_d, GLASS_DARK)
    a.rect(mid_dx + 2, gy_d, gw_d, gh_d, GLASS_DARK)
    # Horizontal steel bars across door glass
    for hy in range(gy_d + 12, gy_d + gh_d - 6, 16):
        a.rect(dx + 4, hy, gw_d, 2, STEEL_FRAME)
        a.rect(mid_dx + 2, hy, gw_d, 2, STEEL_FRAME)
    # Brass Streamline horizontal push bars & kickplates
    a.rect(dx + 4, dy + 4, dw - 8, 10, BRASS_GOLD)
    a.rect(dx + 4, dy + dh // 2 - 4, dw - 8, 6, BRASS_GOLD)
    # Brass "MANSIONS" sign plaque at top
    a.rect(dx + 4, dy + dh - 14, dw - 8, 8, BRASS_GOLD)
    a.text(dx + 6, dy + dh - 7, "MANSIONS", (0.20, 0.15, 0.05), scale=1)
    a.noise(x, y, w, h, 0.02)

    # 8. Stair Tower Brick (R_STAIR_TOWER)
    x, y, w, h = R_STAIR_TOWER
    a.bricks(x, y, w, h, brick=DECO_BRICK_BASE, mortar=DECO_MORTAR, bw=24, bh=10, jitter=0.07)
    a.noise(x, y, w, h, 0.03)

    # 9. Stepped Parapet Trim (R_PARAPET_DECO)
    x, y, w, h = R_PARAPET_DECO
    a.rect(x, y, w, h, STONE_WHITE)
    for py in range(y, y + h, 14):
        a.rect(x, py, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.025)

    # 10. Canopy Lead (R_CANOPY_ROOF)
    x, y, w, h = R_CANOPY_ROOF
    a.rect(x, y, w, h, CANOPY_LEAD)
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.22, 0.23, 0.25))
        a.rect(lx + 3, y, 1, h, (0.45, 0.46, 0.49))
    a.noise(x, y, w, h, 0.025)

    # 11. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.36, 0.35, 0.33))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 12. Corner Wraparound Window (R_WINDOW_CORNER)
    x, y, w, h = R_WINDOW_CORNER
    a.rect(x, y, w, h, STONE_WHITE)
    a.rect(x + 3, y + 3, w - 6, h - 6, GLASS_DARK)
    for hy in range(y + 14, y + h - 10, 16):
        a.rect(x + 3, hy, w - 6, 2, STEEL_FRAME)
    a.noise(x, y, w, h, 0.02)

    # 13. Deco Brass Crest / Intercom (R_DECO_CREST)
    x, y, w, h = R_DECO_CREST
    a.rect(x, y, w, h, (0.75, 0.75, 0.78))
    a.rect(x + 8, y + 10, w - 16, h - 20, BRASS_GOLD)
    for iy in range(y + 20, y + h - 20, 8):
        a.rect(x + 14, iy, w - 28, 4, (0.20, 0.15, 0.05))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_london_flats_03_atlas", kit.OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_BAND, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_BAND, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_artdeco_atlas()
    mat = material_for(img, "mat_london_flats_03")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # 3.5-Storey 1930s Art Deco Residential Block (10.0m x 7.5m, Height: ~10.8m)
    # =========================================================================

    # 1. Pavement
    register_box("Pavement", 10.0, 8.5, 0.10, (0, -0.5, 0),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_PAVEMENT)

    # 2. Main Building Body (10.0m x 7.5m, Z: 0.10 to 9.20, H: 9.10m)
    register_box("MainBlock", 10.0, 7.5, 9.10, (0, 0, 0.10),
                 front=R_BRICK_DECO, sides=R_BRICK_SIDE, back=R_BRICK_SIDE)

    # 3. Central Projecting Stairwell Tower (Width: 2.6m, Projects forward by 0.45m, H: 10.6m)
    register_box("StairTower", 2.60, 7.95, 10.60, (0.0, -0.22, 0.10),
                 front=R_STAIR_TOWER, sides=R_BRICK_SIDE, back=R_BRICK_SIDE)

    # 4. Streamline Curved Entrance Canopy (Z = 2.65m, projecting over entrance)
    register_box("EntranceCanopy", 3.20, 0.85, 0.22, (0.0, -4.50, 2.65),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_CANOPY_ROOF)

    # 5. Entrance Steps & Double Crittall Communal Doors (Ground Level: X = 0.0m)
    register_box("EntranceSteps", 3.00, 0.80, 0.15, (0.0, -4.50, 0.10),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_STONE_BAND)
    register_box("CommunalDoor", 1.80, 0.20, 2.35, (0.0, -4.22, 0.25),
                 front=R_DOOR_CRITTALL, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 6. Continuous Vertical Stairwell Glazing on Central Tower (Floors 2 & 3: Z: 3.10 to 8.80)
    register_box("StairGlazing", 1.60, 0.15, 5.70, (0.0, -4.20, 3.10),
                 front=R_STAIR_GLAZING, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 7. Flanking Crittall Windows (Left X = -3.20m, Right X = +3.20m on all 3 main storeys)
    for floor_idx, fz in enumerate([0.75, 3.65, 6.55]):
        # Left Window
        register_box(f"WinL_{floor_idx}", 1.60, 0.18, 1.70, (-3.20, -3.75, fz),
                     front=R_CRITTALL_WIN, sides=R_STONE_BAND, top=R_STONE_BAND)
        # Right Window
        register_box(f"WinR_{floor_idx}", 1.60, 0.18, 1.70, (3.20, -3.75, fz),
                     front=R_CRITTALL_WIN, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 8. Stepped Art Deco Roof Parapet (Z: 9.20 to 10.00m)
    register_box("ParapetBase", 10.0, 7.50, 0.35, (0.0, 0.0, 9.20),
                 front=R_PARAPET_DECO, sides=R_STONE_BAND, top=R_ROOF_GRAVEL)
    register_box("ParapetStepL", 3.20, 0.25, 0.35, (-3.20, -3.65, 9.55),
                 front=R_PARAPET_DECO, sides=R_STONE_BAND, top=R_STONE_BAND)
    register_box("ParapetStepR", 3.20, 0.25, 0.35, (3.20, -3.65, 9.55),
                 front=R_PARAPET_DECO, sides=R_STONE_BAND, top=R_STONE_BAND)

    # Central Stepped Tower Crown (Z = 10.70m)
    register_box("TowerCrown", 2.80, 2.80, 0.30, (0.0, -0.22, 10.70),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_STONE_BAND)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_London_Flats_03")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = kit.OUT_DIR / "building_london_flats_03_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = kit.OUT_DIR / "building_london_flats_03.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_london_flats_03] generation complete.")


main()
