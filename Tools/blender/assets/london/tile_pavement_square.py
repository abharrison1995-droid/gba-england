"""Modular Square Pavement / Pedestrian Plaza Tile (10.0m x 10.0m).

Specs:
- 10.0m x 10.0m flat pavement tile for pedestrian squares, plazas, and wide walkways.
- High-detail British concrete flagstone surface with mortar expansion joints, inspection hatches, and perimeter kerb edge.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/tile_pavement_square.py
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

# --- Atlas Regions ---
R_PAVEMENT_MAIN  = (0,   256, 256, 256)   # Large flagstone pattern
R_PAVEMENT_SMALL = (256, 256, 128, 256)   # Small herringbone stone pavers
R_KERB_STONE     = (0,   128, 256, 128)   # Granite kerb line
R_MANHOLE_COVER  = (256, 128, 128, 128)   # Cast iron inspection hatch
R_STONE_TRIM     = (0,   64,  256, 64)    # Kerb bevel & trim
R_CONCRETE_BASE  = (256, 64,  128, 64)    # Base concrete

# --- Palette Colors ---
PAVE_FLAG_BASE  = (0.70, 0.69, 0.65)
PAVE_FLAG_JOINT = (0.46, 0.45, 0.43)
KERB_BASE       = (0.74, 0.73, 0.70)
KERB_JOINT      = (0.50, 0.49, 0.46)
IRON_DARK       = (0.14, 0.14, 0.15)


def paint_pavement_atlas():
    a = Atlas(S, seed=901)

    # 1. Main Flagstones (R_PAVEMENT_MAIN)
    x, y, w, h = R_PAVEMENT_MAIN
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

    # 2. Small Pavers (R_PAVEMENT_SMALL)
    x, y, w, h = R_PAVEMENT_SMALL
    a.rect(x, y, w, h, (0.64, 0.62, 0.58))
    for fy in range(y, y + h, 12):
        for fx in range(x, x + w, 16):
            a.rect(fx, fy, 15, 11, (0.66, 0.64, 0.60))
            a.rect(fx, fy, 16, 1, PAVE_FLAG_JOINT)
            a.rect(fx, fy, 1, 12, PAVE_FLAG_JOINT)
    a.noise(x, y, w, h, 0.03)

    # 3. Kerb Stones (R_KERB_STONE)
    x, y, w, h = R_KERB_STONE
    a.rect(x, y, w, h, KERB_BASE)
    for ky in range(y, y + h, 32):
        a.rect(x, ky, w, 2, KERB_JOINT)
    a.noise(x, y, w, h, 0.03)

    # 4. Square Inspection Hatch (R_MANHOLE_COVER)
    x, y, w, h = R_MANHOLE_COVER
    a.rect(x, y, w, h, PAVE_FLAG_BASE)
    hx, hy, hw, hh = x + 16, y + 16, w - 32, h - 32
    a.rect(hx, hy, hw, hh, IRON_DARK)
    a.rect(hx + 3, hy + 3, hw - 6, hh - 6, (0.28, 0.28, 0.30))
    for ly in range(hy + 8, hy + hh - 8, 8):
        a.rect(hx + 8, ly, hw - 16, 2, IRON_DARK)
    a.noise(x, y, w, h, 0.02)

    # 5. Stone Trim
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, KERB_BASE)
    a.noise(x, y, w, h, 0.03)

    # 6. Concrete Base
    x, y, w, h = R_CONCRETE_BASE
    a.rect(x, y, w, h, (0.60, 0.59, 0.56))
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("tile_pavement_square_atlas", OUT_DIR)


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
    img = paint_pavement_atlas()
    mat = material_for(img, "mat_tile_pavement")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # 1. Main 10.0m x 10.0m Pavement Slab (Z = 0.00 to 0.14m)
    register_box("PavementSquare", 10.0, 10.0, 0.14, (0.0, 0.0, 0.0),
                 front=R_KERB_STONE, sides=R_KERB_STONE, top=R_PAVEMENT_MAIN)

    # 2. Dual Inspection Covers
    register_box("Hatch1", 0.70, 0.70, 0.142, (-2.5, -2.5, 0.0),
                 front=R_MANHOLE_COVER, sides=R_STONE_TRIM, top=R_MANHOLE_COVER)
    register_box("Hatch2", 0.70, 0.70, 0.142, (2.5, 2.5, 0.0),
                 front=R_MANHOLE_COVER, sides=R_STONE_TRIM, top=R_MANHOLE_COVER)

    shell = kit.join(parts, "Tile_Pavement_Square")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "tile_pavement_square_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "tile_pavement_square.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "tile_pavement_square.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "tile_pavement_square_preview.png")
        shutil.copy2(OUT_DIR / "tile_pavement_square_atlas.png", TOOLS_OUT_DIR / "tile_pavement_square_atlas.png")
    except Exception as e:
        print(f"[tile_pavement_square] note: {e}")

    print("[tile_pavement_square] generation complete.")


main()
