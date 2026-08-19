"""London Underground Platform Props & Furniture (Tube Environment Prop).

Specs:
- 4.5m x 2.2m footprint, Height: 2.8m.
- Classic London Underground deep-level tube platform furniture kit:
  - Curved glazed ceramic platform tunnel wall with station roundel ("PICCADILLY").
  - "MIND THE GAP" yellow/black platform floor edge tile stencils.
  - Platform waiting bench with teak timber slats & cast-iron TfL roundel arms.
  - Suspended electronic orange LED Next Train Dot-Matrix Indicator: "1: COCKFOSTERS - 1 MIN".
  - Large illuminated TfL Tube Map poster showcase board.
  - Station stainless steel hoop litter bin with clear bag.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_tube_platform_props.py
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
R_PLATFORM_TILES= (0,   256, 256, 256)   # Glazed cream/green Edwardian tiles with Roundel & "MIND THE GAP"
R_DOT_MATRIX    = (256, 256, 256, 256)   # Electronic LED Next Train display ("1: COCKFOSTERS 1 MIN")
R_TUBE_MAP      = (0,   128, 256, 128)   # Full colour TfL Underground Line Map poster board
R_BENCH_TIMBER  = (256, 128, 128, 128)   # Varnished teak timber bench slats & blue cast-iron frame
R_STEEL_BIN     = (384, 128, 128, 128)   # Stainless steel circular hoop waste bin with clear bag
R_PLATFORM_EDGE = (0,   0,   256, 128)   # Platform concrete edge slab & yellow tactile hazard studs
R_ENAMEL_SIGN   = (256, 0,   128, 128)   # "WAY OUT / NORTHBOUND PLATFORM" enamel directional sign
R_POSTER_ADS    = (384, 0,   128, 128)   # London West End & museum advertising posters

# --- Palette Colors ---
TILE_CREAM      = (0.92, 0.90, 0.82)
TILE_GREEN      = (0.12, 0.38, 0.25)
TFL_RED         = (0.88, 0.12, 0.14)
TFL_BLUE        = (0.05, 0.18, 0.58)
TFL_WHITE       = (0.96, 0.96, 0.98)
LED_ORANGE      = (0.98, 0.60, 0.05)
TEAK_WOOD       = (0.42, 0.24, 0.14)
PLATFORM_GREY   = (0.58, 0.60, 0.62)
YELLOW_SAFETY   = (0.95, 0.85, 0.10)
STEEL_BRIGHT    = (0.80, 0.82, 0.85)


def paint_platform_atlas():
    a = Atlas(S, seed=3401)

    # 1. Glazed Platform Wall & Roundel (R_PLATFORM_TILES)
    x, y, w, h = R_PLATFORM_TILES
    a.rect(x, y, w, h, TILE_CREAM)
    # Green Victorian heritage tile border
    a.rect(x, y, w, 32, TILE_GREEN)
    a.rect(x, y + h - 32, w, 32, TILE_GREEN)
    # Glazed tile grid (24x12px)
    for ty in range(y, y + h, 14):
        a.rect(x, ty, w, 1, (0.75, 0.72, 0.65))
    for tx in range(x, x + w, 28):
        a.rect(tx, y, 1, h, (0.75, 0.72, 0.65))
    # Iconic Platform Roundel: "PICCADILLY"
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 60, TFL_RED)
    a.disc(cx, cy, 40, TILE_CREAM)
    # Blue bar
    bx, by, bw, bh = cx - 80, cy - 16, 160, 32
    a.rect(bx, by, bw, bh, TFL_BLUE)
    s1 = "PICCADILLY"
    tw1 = a.text_width(s1, scale=2)
    a.text(bx + (bw - tw1) // 2, by + 9, s1, TFL_WHITE, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 2. Electronic Dot-Matrix Next Train Display (R_DOT_MATRIX)
    x, y, w, h = R_DOT_MATRIX
    a.rect(x, y, w, h, (0.04, 0.04, 0.05))  # Dark chassis
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.08, 0.08, 0.09))
    # Line 1: "1: COCKFOSTERS   1 MIN"
    s_t1 = "1 COCKFOSTERS 1 MIN"
    a.text(x + 16, y + h - 40, s_t1, LED_ORANGE, scale=2)
    # Line 2: "2: HEATHROW    4 MIN"
    s_t2 = "2 HEATHROW T5 4 MIN"
    a.text(x + 16, y + 24, s_t2, LED_ORANGE, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 3. Tube Map Poster (R_TUBE_MAP)
    x, y, w, h = R_TUBE_MAP
    a.rect(x, y, w, h, (0.2, 0.22, 0.24))  # Silver showcase frame
    mx, my, mw, mh = x + 8, y + 6, w - 16, h - 12
    a.rect(mx, my, mw, mh, TFL_WHITE)
    # Underground network lines
    a.rect(mx + 10, my + mh // 2, mw - 20, 4, TFL_RED)         # Central Line
    a.rect(mx + 30, my + 10, 4, mh - 20, (0.05, 0.40, 0.75))  # Piccadilly Line
    a.rect(mx + 60, my + 15, 4, mh - 30, (0.10, 0.65, 0.25))  # District Line
    a.rect(mx + 90, my + 20, 4, mh - 40, (0.95, 0.80, 0.10))  # Circle Line
    a.rect(mx + 120, my + 10, 4, mh - 20, (0.15, 0.15, 0.15)) # Northern Line
    a.disc(mx + 30, my + mh // 2, 6, (0.1, 0.1, 0.1))         # Interchange station
    s_map = "UNDERGROUND MAP"
    a.text(mx + 10, my + mh - 16, s_map, TFL_BLUE, scale=1)
    a.noise(x, y, w, h, 0.015)

    # 4. Teak Timber Bench (R_BENCH_TIMBER)
    x, y, w, h = R_BENCH_TIMBER
    a.rect(x, y, w, h, TEAK_WOOD)
    for by in range(y, y + h, 14):
        a.rect(x, by, w, 2, (0.26, 0.14, 0.08))
        a.rect(x, by + 2, w, 1, (0.58, 0.36, 0.22))
    # Cast iron TfL blue end frames
    a.rect(x, y, 16, h, TFL_BLUE)
    a.rect(x + w - 16, y, 16, h, TFL_BLUE)
    a.noise(x, y, w, h, 0.025)

    # 5. Stainless Steel Rubbish Bin (R_STEEL_BIN)
    x, y, w, h = R_STEEL_BIN
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    a.rect(x + 10, y + 10, w - 20, h - 20, STEEL_BRIGHT)
    # Clear transparent plastic bag insert
    a.rect(x + 20, y + 20, w - 40, h - 40, (0.85, 0.90, 0.95))
    a.disc(x + w // 2, y + h // 2, 14, (0.5, 0.5, 0.5))
    a.noise(x, y, w, h, 0.02)

    # 6. Platform Floor Edge & "MIND THE GAP" (R_PLATFORM_EDGE)
    x, y, w, h = R_PLATFORM_EDGE
    a.rect(x, y, w, h, PLATFORM_GREY)
    # Yellow hazard safety line
    a.rect(x, y + h - 28, w, 14, YELLOW_SAFETY)
    # Bold Black Text: "MIND THE GAP"
    s_gap = "MIND THE GAP"
    gw = a.text_width(s_gap, scale=2)
    a.text(x + (w - gw) // 2, y + h - 26, s_gap, (0.05, 0.05, 0.05), scale=2)
    a.noise(x, y, w, h, 0.03)

    # 7. Way Out Directional Sign (R_ENAMEL_SIGN)
    x, y, w, h = R_ENAMEL_SIGN
    a.rect(x, y, w, h, (0.95, 0.95, 0.95))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.98, 0.85, 0.10))  # Yellow Way Out
    s_way = "WAY OUT ->"
    ww = a.text_width(s_way, scale=1)
    a.text(x + (w - ww) // 2, y + h // 2 - 4, s_way, (0.05, 0.05, 0.05), scale=1)
    a.noise(x, y, w, h, 0.015)

    # 8. Poster Ads (R_POSTER_ADS)
    x, y, w, h = R_POSTER_ADS
    a.rect(x, y, w, h, (0.85, 0.20, 0.35))
    a.text(x + 12, y + h - 24, "MUSICAL", TFL_WHITE, scale=2)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_tube_platform_props_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_PLATFORM_EDGE, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_PLATFORM_EDGE, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_platform_atlas()
    mat = material_for(img, "mat_platform_props")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London Underground Platform Props Kit (4.5m x 2.2m Footprint, Height: 2.8m)
    # - Platform Floor Slab with Yellow "MIND THE GAP" Safety Edge (Z: 0.0 to 0.15m)
    # - Glazed Ceramic Tiled Tunnel Wall with Roundel & Enamel Signs (Z: 0.15m to 2.8m)
    # - Teak Slatted Platform Waiting Bench (Width 2.2m)
    # - Suspended Electronic Orange LED Dot-Matrix Display (Width 1.8m)
    # - TfL Underground Map Showcase Board (Width 1.4m)
    # - Stainless Steel Hoop Platform Waste Bin
    # =========================================================================

    # 1. Platform Concrete Floor Slab (4.6m x 2.4m, Z = 0.00 to 0.15m)
    register_box("PlatformFloor", 4.60, 2.40, 0.15, (0.0, 0.0, 0.0),
                 front=R_PLATFORM_EDGE, sides=R_PLATFORM_EDGE, top=R_PLATFORM_EDGE)

    # 2. Glazed Ceramic Tiled Tunnel Wall (4.6m x 0.40m, Z: 0.15m to 2.80m, H: 2.65m at Y = 0.90m)
    register_box("TunnelWall", 4.60, 0.40, 2.65, (0.0, 0.90, 0.15),
                 front=R_PLATFORM_TILES, sides=R_PLATFORM_TILES, back=R_PLATFORM_TILES, top=R_PLATFORM_EDGE)

    # 3. TfL Map Showcase Poster Board (Mounted on wall: Width 1.30m, H: 1.10m at X = 1.30m, Z = 1.20m)
    register_box("TubeMapBoard", 1.30, 0.08, 1.10, (1.30, 0.66, 1.20),
                 front=R_TUBE_MAP, sides=R_PLATFORM_EDGE, top=R_PLATFORM_EDGE)

    # 4. Teak Wood Platform Waiting Bench (Width 2.20m, D: 0.65m, H: 0.85m, at X = -0.80m, Y = 0.25m)
    # Bench seat
    register_box("BenchSeat", 2.20, 0.50, 0.10, (-0.80, 0.35, 0.55),
                 front=R_BENCH_TIMBER, sides=R_BENCH_TIMBER, top=R_BENCH_TIMBER)
    # Bench backrest
    register_box("BenchBack", 2.20, 0.10, 0.45, (-0.80, 0.55, 0.65),
                 front=R_BENCH_TIMBER, sides=R_BENCH_TIMBER, top=R_BENCH_TIMBER)
    # Bench legs
    register_box("BenchLegL", 0.12, 0.50, 0.40, (-1.80, 0.35, 0.15),
                 front=R_BENCH_TIMBER, sides=R_BENCH_TIMBER, top=R_BENCH_TIMBER)
    register_box("BenchLegR", 0.12, 0.50, 0.40, (0.20, 0.35, 0.15),
                 front=R_BENCH_TIMBER, sides=R_BENCH_TIMBER, top=R_BENCH_TIMBER)

    # 5. Suspended Electronic LED Next Train Display (Width 1.80m, D: 0.30m, H: 0.55m at Z = 2.05m, Y = -0.30m)
    register_box("DotMatrixDisplay", 1.80, 0.30, 0.55, (-0.50, -0.30, 2.05),
                 front=R_DOT_MATRIX, sides=R_DOT_MATRIX, back=R_DOT_MATRIX, top=R_PLATFORM_EDGE)
    # Suspension poles from ceiling
    register_box("HangerPoleL", 0.06, 0.06, 0.40, (-1.20, -0.30, 2.60),
                 front=R_PLATFORM_EDGE, sides=R_PLATFORM_EDGE, top=R_PLATFORM_EDGE)
    register_box("HangerPoleR", 0.06, 0.06, 0.40, (0.20, -0.30, 2.60),
                 front=R_PLATFORM_EDGE, sides=R_PLATFORM_EDGE, top=R_PLATFORM_EDGE)

    # 6. Stainless Steel Hoop Platform Waste Bin (X = 1.80m, Y = 0.20m, Z = 0.15m to 0.95m)
    register_box("PlatformBin", 0.45, 0.45, 0.80, (1.80, 0.20, 0.15),
                 front=R_STEEL_BIN, sides=R_STEEL_BIN, top=R_STEEL_BIN)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Tube_Platform_Props")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_tube_platform_props_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_tube_platform_props.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_tube_platform_props.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_tube_platform_props_preview.png")
        shutil.copy2(OUT_DIR / "prop_tube_platform_props_atlas.png", TOOLS_OUT_DIR / "prop_tube_platform_props_atlas.png")
    except Exception as e:
        print(f"[prop_tube_platform_props] note: {e}")

    print("[prop_tube_platform_props] generation complete.")


main()
