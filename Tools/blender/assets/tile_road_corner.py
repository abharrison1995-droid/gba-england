"""90-Degree Corner Road Turn Tile (10.0m x 10.0m Modular Bend).

Specs:
- 10.0m x 10.0m flat corner road tile connecting South road entrance (-Y) to East road exit (+X).
- Outer corner pavement quadrant (Top-Left 4.0m x 4.0m) and inner corner pavement quadrant (Bottom-Right 2.0m x 2.0m).
- Curved 2-lane asphalt carriageway with curved center white hazard dashes and double yellow lines.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/tile_road_corner.py
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

# --- Atlas Region Definitions ---
R_CORNER_ASPHALT = (0,   256, 256, 256)   # Curved road markings
R_ROAD_PLAIN     = (256, 256, 128, 256)   # Plain asphalt
R_PAVEMENT_FLAG  = (0,   128, 256, 128)   # Concrete flagstones
R_KERB_STONE     = (256, 128, 128, 128)   # Granite kerb stone
R_MANHOLE_COVER  = (384, 256, 128, 128)   # Round inspection cover
R_STONE_TRIM     = (0,   64,  256, 64)    # Kerb trim
R_TACTILE_PAVE   = (256, 64,  128, 64)    # Yellow tactile blister crossing

# --- Palette Colors ---
ASPHALT_BASE    = (0.24, 0.25, 0.27)
ROAD_WHITE      = (0.92, 0.92, 0.90)
DOUBLE_YELLOW   = (0.92, 0.74, 0.12)
PAVE_FLAG_BASE  = (0.68, 0.67, 0.64)
PAVE_FLAG_JOINT = (0.45, 0.44, 0.42)
KERB_BASE       = (0.74, 0.73, 0.70)
KERB_JOINT      = (0.50, 0.49, 0.46)
IRON_DARK       = (0.14, 0.14, 0.15)
TACTILE_YELLOW  = (0.88, 0.78, 0.28)


def paint_corner_atlas():
    a = Atlas(S, seed=801)

    # 1. Corner Asphalt (R_CORNER_ASPHALT)
    x, y, w, h = R_CORNER_ASPHALT
    a.rect(x, y, w, h, ASPHALT_BASE)
    # Continuous smooth curved double yellow lines
    cx, cy = x + w, y  # Center of curvature at bottom-right
    for deg in np.linspace(92, 178, 180):
        rad = math.radians(deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        # Outer yellow line (r = 224)
        px1, py1 = int(cx + 224 * cos_r), int(cy + 224 * sin_r)
        a.disc(px1, py1, 3, DOUBLE_YELLOW)
        # Inner yellow line (r = 214)
        px2, py2 = int(cx + 214 * cos_r), int(cy + 214 * sin_r)
        a.disc(px2, py2, 3, DOUBLE_YELLOW)

    # Curved Center Dashes (3 prominent dashed segments)
    for (start_deg, end_deg) in [(100, 118), (128, 146), (156, 174)]:
        for deg in np.linspace(start_deg, end_deg, 30):
            rad = math.radians(deg)
            px = int(cx + 135 * math.cos(rad))
            py = int(cy + 135 * math.sin(rad))
            a.disc(px, py, 4, ROAD_WHITE)
    a.noise(x, y, w, h, 0.035)

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
    a.noise(x, y, w, h, 0.03)

    # 5. Manhole Cover (R_MANHOLE_COVER)
    x, y, w, h = R_MANHOLE_COVER
    a.rect(x, y, w, h, ASPHALT_BASE)
    cx, cy, r = x + w // 2, y + h // 2, 48
    a.disc(cx, cy, r, IRON_DARK)
    a.disc(cx, cy, r - 4, (0.28, 0.28, 0.30))
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
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("tile_road_corner_atlas", OUT_DIR)


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
    img = paint_corner_atlas()
    mat = material_for(img, "mat_tile_road_corner")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m x 10.0m 90-Degree Corner Road Turn Tile
    # Road base: 10.0m x 10.0m
    # Outer pavement: Top-Left quadrant (4.0m x 4.0m)
    # Inner pavement: Bottom-Right corner (2.0m x 2.0m)
    # =========================================================================

    # 1. Base Road Surface
    register_box("RoadCornerBase", 10.0, 10.0, 0.04, (0.0, 0.0, 0.0),
                 front=R_ROAD_PLAIN, sides=R_ROAD_PLAIN, top=R_CORNER_ASPHALT)

    # 2. Outer Pavement (North-West: X = -3.0m, Y = +3.0m, 4.0m x 4.0m)
    register_box("PavementOuter", 4.0, 4.0, 0.14, (-3.0, 3.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)

    # 3. Inner Corner Pavement (South-East: X = +4.0m, Y = -4.0m, 2.0m x 2.0m)
    register_box("PavementInner", 2.0, 2.0, 0.14, (4.0, -4.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_FLAG)
    register_box("TactileInner", 0.60, 0.60, 0.142, (3.30, -3.30, 0.0),
                 front=R_TACTILE_PAVE, sides=R_STONE_TRIM, top=R_TACTILE_PAVE)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Tile_Road_Corner")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "tile_road_corner_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "tile_road_corner.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "tile_road_corner.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "tile_road_corner_preview.png")
        shutil.copy2(OUT_DIR / "tile_road_corner_atlas.png", TOOLS_OUT_DIR / "tile_road_corner_atlas.png")
    except Exception as e:
        print(f"[tile_road_corner] note: {e}")

    print("[tile_road_corner] generation complete.")


main()
