"""4-Way Road Intersection Square Tile (10.0m x 10.0m Modular Crossroads).

Specs:
- 10.0m x 10.0m flat square intersection tile where 4 straight 2-lane roads meet.
- Central 6.0m x 6.0m open asphalt junction with British give-way dashed double lines across all 4 entry lanes.
- 4 corner pavement quadrants (each 2.0m x 2.0m, height 0.14m) with bevelled corner kerb stones and yellow tactile blister crossing points.
- Central inspection manhole cover.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/tile_road_intersection_4way.py
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
R_JUNCTION_ASPHALT = (0,   256, 256, 256)   # 4-way asphalt with give-way markings
R_ROAD_PLAIN       = (256, 256, 128, 256)   # Plain asphalt
R_PAVEMENT_FLAG    = (0,   128, 256, 128)   # Concrete flagstones
R_KERB_STONE       = (256, 128, 128, 128)   # Granite kerb stone
R_MANHOLE_COVER    = (384, 256, 128, 128)   # Round inspection cover
R_STONE_TRIM       = (0,   64,  256, 64)    # Kerb trim
R_TACTILE_PAVE     = (256, 64,  128, 64)    # Yellow tactile blister crossing
R_GIVE_WAY_LINE    = (384, 384, 128, 128)   # Give way dashed double lines

# --- Palette Colors ---
ASPHALT_BASE    = (0.24, 0.25, 0.27)
ASPHALT_DARK    = (0.16, 0.17, 0.19)
ROAD_WHITE      = (0.92, 0.92, 0.90)
DOUBLE_YELLOW   = (0.92, 0.74, 0.12)
PAVE_FLAG_BASE  = (0.68, 0.67, 0.64)
PAVE_FLAG_JOINT = (0.45, 0.44, 0.42)
KERB_BASE       = (0.74, 0.73, 0.70)
KERB_JOINT      = (0.50, 0.49, 0.46)
IRON_DARK       = (0.14, 0.14, 0.15)
TACTILE_YELLOW  = (0.88, 0.78, 0.28)


def paint_intersection_atlas():
    a = Atlas(S, seed=601)

    # 1. 4-Way Crossroads Asphalt Surface (R_JUNCTION_ASPHALT)
    x, y, w, h = R_JUNCTION_ASPHALT
    a.rect(x, y, w, h, ASPHALT_BASE)
    # Give-way dashed double lines across 4 entry points
    # North (-Y) & South (+Y) entries:
    gw_w = 64
    gw_h = 4
    mid = w // 2
    # South entry (+Y)
    a.rect(x + mid - gw_w // 2, y + h - 16, gw_w, gw_h, ROAD_WHITE)
    a.rect(x + mid - gw_w // 2, y + h - 26, gw_w, gw_h, ROAD_WHITE)
    # North entry (-Y)
    a.rect(x + mid - gw_w // 2, y + 12, gw_w, gw_h, ROAD_WHITE)
    a.rect(x + mid - gw_w // 2, y + 22, gw_w, gw_h, ROAD_WHITE)
    # West entry (-X)
    a.rect(x + 12, y + mid - gw_w // 2, gw_h, gw_w, ROAD_WHITE)
    a.rect(x + 22, y + mid - gw_w // 2, gw_h, gw_w, ROAD_WHITE)
    # East entry (+X)
    a.rect(x + w - 16, y + mid - gw_w // 2, gw_h, gw_w, ROAD_WHITE)
    a.rect(x + w - 26, y + mid - gw_w // 2, gw_h, gw_w, ROAD_WHITE)
    a.noise(x, y, w, h, 0.04)

    # 2. Plain Asphalt (R_ROAD_PLAIN)
    x, y, w, h = R_ROAD_PLAIN
    a.rect(x, y, w, h, ASPHALT_BASE)
    a.noise(x, y, w, h, 0.04)

    # 3. Pavement Flagstones (R_PAVEMENT_FLAG)
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

    # 4. Kerb Stones (R_KERB_STONE)
    x, y, w, h = R_KERB_STONE
    a.rect(x, y, w, h, KERB_BASE)
    for ky in range(y, y + h, 32):
        a.rect(x, ky, w, 2, KERB_JOINT)
        a.rect(x, ky + 2, w, 1, (0.85, 0.84, 0.82))
    a.noise(x, y, w, h, 0.03)

    # 5. Manhole Cover (R_MANHOLE_COVER)
    x, y, w, h = R_MANHOLE_COVER
    a.rect(x, y, w, h, ASPHALT_BASE)
    cx, cy, r = x + w // 2, y + h // 2, 48
    a.disc(cx, cy, r, IRON_DARK)
    a.disc(cx, cy, r - 3, (0.26, 0.26, 0.28))
    a.disc(cx, cy, r - 6, IRON_DARK)
    a.disc(cx, cy, r - 8, (0.30, 0.30, 0.32))
    for py in range(cy - r + 14, cy + r - 14, 8):
        a.rect(cx - r + 14, py, (r - 14) * 2, 2, IRON_DARK)
    a.noise(x, y, w, h, 0.02)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, KERB_BASE)
    a.noise(x, y, w, h, 0.03)

    # 7. Tactile Blister Paving (R_TACTILE_PAVE)
    x, y, w, h = R_TACTILE_PAVE
    a.rect(x, y, w, h, TACTILE_YELLOW)
    for bx in range(x + 6, x + w - 4, 12):
        for by in range(y + 6, y + h - 4, 12):
            a.disc(bx, by, 3, (0.75, 0.65, 0.18))
            a.disc(bx, by, 2, (0.96, 0.88, 0.35))
    a.noise(x, y, w, h, 0.02)

    # 8. Give Way Line Tile (R_GIVE_WAY_LINE)
    x, y, w, h = R_GIVE_WAY_LINE
    a.rect(x, y, w, h, ASPHALT_BASE)
    for dy in range(y + 20, y + h - 20, 24):
        a.rect(x + 20, dy, w - 40, 8, ROAD_WHITE)
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("tile_road_intersection_4way_atlas", OUT_DIR)


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
    img = paint_intersection_atlas()
    mat = material_for(img, "mat_tile_road_intersection")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m x 10.0m 4-Way Crossroads Intersection Tile
    # Central open road surface: 10.0m x 10.0m, Z = 0.00 to 0.04m
    # 4 Corner Pavement Quadrants: 2.0m x 2.0m each at (±4.0m, ±4.0m)
    # =========================================================================

    # 1. Base Full Roadway Mesh (10.0m x 10.0m)
    register_box("RoadIntersectionBase", 10.0, 10.0, 0.04, (0.0, 0.0, 0.0),
                 front=R_ROAD_PLAIN, sides=R_ROAD_PLAIN, top=R_JUNCTION_ASPHALT)

    # 2. 4 Corner Pavement Quadrants (2.0m x 2.0m, Z = 0.00 to 0.14m)
    # Top-Left (-4.0m, +4.0m)
    register_box("PavementTL", 2.0, 2.0, 0.14, (-4.0, 4.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)
    # Tactile drop-kerb pad on TL corner
    register_box("TactileTL", 0.60, 0.60, 0.142, (-3.30, 3.30, 0.0),
                 front=R_TACTILE_PAVE, sides=R_STONE_TRIM, top=R_TACTILE_PAVE)

    # Top-Right (+4.0m, +4.0m)
    register_box("PavementTR", 2.0, 2.0, 0.14, (4.0, 4.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)
    register_box("TactileTR", 0.60, 0.60, 0.142, (3.30, 3.30, 0.0),
                 front=R_TACTILE_PAVE, sides=R_STONE_TRIM, top=R_TACTILE_PAVE)

    # Bottom-Left (-4.0m, -4.0m)
    register_box("PavementBL", 2.0, 2.0, 0.14, (-4.0, -4.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)
    register_box("TactileBL", 0.60, 0.60, 0.142, (-3.30, -3.30, 0.0),
                 front=R_TACTILE_PAVE, sides=R_STONE_TRIM, top=R_TACTILE_PAVE)

    # Bottom-Right (+4.0m, -4.0m)
    register_box("PavementBR", 2.0, 2.0, 0.14, (4.0, -4.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)
    register_box("TactileBR", 0.60, 0.60, 0.142, (3.30, -3.30, 0.0),
                 front=R_TACTILE_PAVE, sides=R_STONE_TRIM, top=R_TACTILE_PAVE)

    # 3. Center Junction Manhole Cover (X = 0.0, Y = 0.0)
    register_box("CenterManhole", 0.90, 0.90, 0.045, (0.0, 0.0, 0.0),
                 front=R_MANHOLE_COVER, sides=R_ROAD_PLAIN, top=R_MANHOLE_COVER)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Tile_Road_Intersection_4Way")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "tile_road_intersection_4way_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "tile_road_intersection_4way.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "tile_road_intersection_4way.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "tile_road_intersection_4way_preview.png")
        shutil.copy2(OUT_DIR / "tile_road_intersection_4way_atlas.png", TOOLS_OUT_DIR / "tile_road_intersection_4way_atlas.png")
    except Exception as e:
        print(f"[tile_road_intersection_4way] note: {e}")

    print("[tile_road_intersection_4way] generation complete.")


main()
