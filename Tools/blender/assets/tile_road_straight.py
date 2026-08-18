"""Repeatable Straight Road Tile with Pavements & Kerbs (10.0m x 10.0m Modular Square).

Specs:
- 10.0m x 10.0m flat road tile, designed for seamless tiling on a 10m grid.
- Central 2-lane 6.0m carriageway (X: -3.0m to +3.0m) with British dashed white center line, double yellow lines, and storm drain gullies.
- Flanking 2.0m wide concrete flagstone pavements (Left X: -5.0 to -3.0, Right X: +3.0 to +5.0) with raised granite kerbstones (0.12m height).
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/tile_road_straight.py
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
OUT_DIR = Path(__file__).resolve().parent.parent / "out" / "Background Assets"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "Background Assets"

# --- Atlas Region Definitions (x, y, w, h) ---
R_ROAD_ASPHALT  = (0,   256, 256, 256)   # 2-lane tarmac with white dashes & double yellow
R_ROAD_PLAIN    = (256, 256, 128, 256)   # Plain asphalt with aggregate grain
R_PAVEMENT_FLAG = (0,   128, 256, 128)   # British concrete flagstones
R_KERB_STONE    = (256, 128, 128, 128)   # Granite kerb stone strip
R_DRAIN_GULLY   = (384, 384, 128, 128)   # Cast iron storm drain gully
R_MANHOLE_COVER = (384, 256, 128, 128)   # Round cast iron manhole cover
R_STONE_TRIM    = (0,   64,  256, 64)    # Kerb bevel & step trim
R_TACTILE_PAVE  = (256, 64,  128, 64)    # Yellow blister tactile crossing pavers

# --- Palette Colors ---
ASPHALT_BASE    = (0.24, 0.25, 0.27)
ASPHALT_DARK    = (0.16, 0.17, 0.19)
ASPHALT_GRAIN   = (0.32, 0.33, 0.35)
ROAD_WHITE      = (0.92, 0.92, 0.90)
DOUBLE_YELLOW   = (0.92, 0.74, 0.12)
PAVE_FLAG_BASE  = (0.68, 0.67, 0.64)
PAVE_FLAG_JOINT = (0.45, 0.44, 0.42)
KERB_BASE       = (0.74, 0.73, 0.70)
KERB_JOINT      = (0.50, 0.49, 0.46)
IRON_DARK       = (0.14, 0.14, 0.15)
IRON_LIGHT      = (0.32, 0.32, 0.34)
TACTILE_YELLOW  = (0.88, 0.78, 0.28)


def paint_road_atlas():
    a = Atlas(S, seed=501)

    # 1. Road Asphalt with Markings (R_ROAD_ASPHALT)
    x, y, w, h = R_ROAD_ASPHALT
    a.rect(x, y, w, h, ASPHALT_BASE)
    # Tyre track wear lines
    for ty in [y + 60, y + 180]:
        a.rect(x, ty, w, 24, ASPHALT_DARK)
    # Centre Broken White Hazard Dashes (UK standard dashed line)
    # Stretches along Y, centered at X = x + w // 2
    dash_w = 8
    mid_x = x + (w - dash_w) // 2
    for dy in range(y, y + h, 64):
        a.rect(mid_x, dy + 8, dash_w, 48, ROAD_WHITE)
    # Double Yellow Lines along outer left and right gutter edges
    yellow_w = 5
    gap = 4
    # Left edge double yellow
    a.rect(x + 12, y, yellow_w, h, DOUBLE_YELLOW)
    a.rect(x + 12 + yellow_w + gap, y, yellow_w, h, DOUBLE_YELLOW)
    # Right edge double yellow
    a.rect(x + w - 12 - yellow_w, y, yellow_w, h, DOUBLE_YELLOW)
    a.rect(x + w - 12 - 2 * yellow_w - gap, y, yellow_w, h, DOUBLE_YELLOW)
    # Surface aggregate noise
    a.noise(x, y, w, h, 0.04)

    # 2. Plain Asphalt (R_ROAD_PLAIN)
    x, y, w, h = R_ROAD_PLAIN
    a.rect(x, y, w, h, ASPHALT_BASE)
    a.noise(x, y, w, h, 0.045)

    # 3. British Pavement Flagstones (R_PAVEMENT_FLAG)
    x, y, w, h = R_PAVEMENT_FLAG
    a.rect(x, y, w, h, PAVE_FLAG_BASE)
    flag_w, flag_h = 32, 24
    row = 0
    for fy in range(y, y + h, flag_h):
        stagger = (flag_w // 2) if (row % 2 == 1) else 0
        a.rect(x, fy, w, 2, PAVE_FLAG_JOINT)
        for fx in range(x - stagger, x + w, flag_w):
            x0 = max(x, fx)
            x1 = min(x + w, fx + flag_w)
            if x1 > x0:
                a.rect(x0, fy, 2, flag_h, PAVE_FLAG_JOINT)
                j = a.rng.uniform(-0.03, 0.03)
                col = tuple(max(0.0, min(1.0, c + j)) for c in PAVE_FLAG_BASE)
                a.rect(x0 + 2, fy + 2, max(1, x1 - x0 - 3), max(1, flag_h - 3), col)
        row += 1
    a.noise(x, y, w, h, 0.025)

    # 4. Granite Kerb Stone (R_KERB_STONE)
    x, y, w, h = R_KERB_STONE
    a.rect(x, y, w, h, KERB_BASE)
    for ky in range(y, y + h, 32):
        a.rect(x, ky, w, 2, KERB_JOINT)
        a.rect(x, ky + 2, w, 1, (0.85, 0.84, 0.82))
    a.noise(x, y, w, h, 0.03)

    # 5. Cast Iron Drain Gully (R_DRAIN_GULLY)
    x, y, w, h = R_DRAIN_GULLY
    a.rect(x, y, w, h, ASPHALT_BASE)
    gx, gy, gw, gh = x + 16, y + 16, w - 32, h - 32
    a.rect(gx, gy, gw, gh, IRON_DARK)
    a.rect(gx + 2, gy + 2, gw - 4, gh - 4, (0.22, 0.22, 0.24))
    # Grate slots
    for sy in range(gy + 6, gy + gh - 6, 8):
        a.rect(gx + 6, sy, gw - 12, 4, IRON_DARK)
        a.rect(gx + 6, sy + 3, gw - 12, 1, IRON_LIGHT)
    a.noise(x, y, w, h, 0.02)

    # 6. Manhole Cover (R_MANHOLE_COVER)
    x, y, w, h = R_MANHOLE_COVER
    a.rect(x, y, w, h, ASPHALT_BASE)
    cx, cy, r = x + w // 2, y + h // 2, 48
    a.disc(cx, cy, r, IRON_DARK)
    a.disc(cx, cy, r - 3, (0.26, 0.26, 0.28))
    a.disc(cx, cy, r - 6, IRON_DARK)
    a.disc(cx, cy, r - 8, (0.30, 0.30, 0.32))
    # Cross-hatch waffle pattern
    for py in range(cy - r + 14, cy + r - 14, 8):
        a.rect(cx - r + 14, py, (r - 14) * 2, 2, IRON_DARK)
    a.noise(x, y, w, h, 0.02)

    # 7. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, KERB_BASE)
    a.noise(x, y, w, h, 0.03)

    # 8. Tactile Blister Paving (R_TACTILE_PAVE)
    x, y, w, h = R_TACTILE_PAVE
    a.rect(x, y, w, h, TACTILE_YELLOW)
    for bx in range(x + 6, x + w - 4, 12):
        for by in range(y + 6, y + h - 4, 12):
            a.disc(bx, by, 3, (0.75, 0.65, 0.18))
            a.disc(bx, by, 2, (0.96, 0.88, 0.35))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("tile_road_straight_atlas", OUT_DIR)


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
    img = paint_road_atlas()
    mat = material_for(img, "mat_tile_road")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m x 10.0m Straight Road Tile
    # Carriageway: 6.0m width (X: -3.0 to +3.0), height Z = 0.00 to 0.04m
    # Left Pavement: 2.0m width (X: -5.0 to -3.0), height Z = 0.00 to 0.14m (Kerb +0.10m)
    # Right Pavement: 2.0m width (X: +3.0 to +5.0), height Z = 0.00 to 0.14m (Kerb +0.10m)
    # =========================================================================

    # 1. Central Carriageway Road Surface (6.0m x 10.0m, Z = 0.00 to 0.04m)
    register_box("RoadSurface", 6.0, 10.0, 0.04, (0.0, 0.0, 0.0),
                 front=R_ROAD_PLAIN, sides=R_ROAD_PLAIN, top=R_ROAD_ASPHALT)

    # 2. Left Pavement & Kerb (X: -4.0m center, width 2.0m x 10.0m, Z = 0.00 to 0.14m)
    register_box("LeftPavement", 2.0, 10.0, 0.14, (-4.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)

    # 3. Right Pavement & Kerb (X: +4.0m center, width 2.0m x 10.0m, Z = 0.00 to 0.14m)
    register_box("RightPavement", 2.0, 10.0, 0.14, (4.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)

    # 4. Inset Storm Drain Gully (Left gutter: X = -2.80m, Y = -2.0m)
    register_box("DrainGullyL", 0.35, 0.50, 0.045, (-2.80, -2.0, 0.0),
                 front=R_DRAIN_GULLY, sides=R_ROAD_PLAIN, top=R_DRAIN_GULLY)

    # 5. Inset Manhole Cover (Right lane: X = 1.50m, Y = 2.0m)
    register_box("ManholeR", 0.80, 0.80, 0.045, (1.50, 2.0, 0.0),
                 front=R_MANHOLE_COVER, sides=R_ROAD_PLAIN, top=R_MANHOLE_COVER)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Tile_Road_Straight")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "tile_road_straight_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "tile_road_straight.glb"
    kit.export_glb(glb_path, [shell])

    # Mirror to Tools/out/Background Assets/ if requested
    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "tile_road_straight.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "tile_road_straight_preview.png")
        shutil.copy2(OUT_DIR / "tile_road_straight_atlas.png", TOOLS_OUT_DIR / "tile_road_straight_atlas.png")
    except Exception as e:
        print(f"[tile_road_straight] note: {e}")

    print("[tile_road_straight] generation complete.")


main()
