"""Modular Low Brick Garden Wall (10.0m Length, Height: 0.90m).

Specs:
- 10.0m long modular London red-brick garden wall with periodic brick piers (pillars) and dressed cream stone coping stones.
- 3 Brick Piers: Left end (X = -5.0m), Centre (X = 0.0m), Right end (X = +5.0m) with pyramidal stone pier caps.
- Wall thickness: 0.28m; Pier thickness: 0.44m; Wall height: 0.82m (coping top: 0.92m, pier caps: 1.05m).
- Snaps seamlessly to 5.0m and 10.0m street grids.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_wall_garden_low.py
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
R_WALL_BRICK    = (0,   256, 256, 256)   # London red brick wall courses
R_PIER_BRICK    = (256, 256, 128, 256)   # Brick pier courses
R_STONE_COPING  = (0,   128, 256, 128)   # Dressed stone wall coping
R_PIER_CAP      = (256, 128, 128, 128)   # Pyramidal stone pier cap
R_STONE_TRIM    = (0,   64,  256, 64)    # Stone plinth & trim
R_PLINTH_DARK   = (256, 64,  128, 64)    # Damp-proof plinth brick

# --- Palette Colors ---
WALL_BRICK_BASE = (0.54, 0.24, 0.18)
WALL_MORTAR     = (0.70, 0.67, 0.62)
STONE_CREAM     = (0.82, 0.79, 0.72)
STONE_DARK      = (0.58, 0.55, 0.48)
PLINTH_BASE     = (0.40, 0.20, 0.16)


def paint_garden_wall_atlas():
    a = Atlas(S, seed=1001)

    # 1. Wall Brick (R_WALL_BRICK)
    x, y, w, h = R_WALL_BRICK
    a.bricks(x, y, w, h, brick=WALL_BRICK_BASE, mortar=WALL_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    a.shade(x, y, w, h, top=-0.04, bottom=-0.08)

    # 2. Pier Brick (R_PIER_BRICK)
    x, y, w, h = R_PIER_BRICK
    a.bricks(x, y, w, h, brick=WALL_BRICK_BASE, mortar=WALL_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)

    # 3. Stone Coping (R_STONE_COPING)
    x, y, w, h = R_STONE_COPING
    a.rect(x, y, w, h, STONE_CREAM)
    for cy in range(y, y + h, 32):
        a.rect(x, cy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.025)

    # 4. Pier Cap (R_PIER_CAP)
    x, y, w, h = R_PIER_CAP
    a.rect(x, y, w, h, STONE_CREAM)
    a.rect(x + 10, y + 10, w - 20, h - 20, (0.88, 0.85, 0.78))
    a.noise(x, y, w, h, 0.025)

    # 5. Stone Trim
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    a.noise(x, y, w, h, 0.03)

    # 6. Plinth Dark Brick
    x, y, w, h = R_PLINTH_DARK
    a.bricks(x, y, w, h, brick=PLINTH_BASE, mortar=(0.55, 0.52, 0.48), bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_wall_garden_low_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_COPING, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_COPING, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_garden_wall_atlas()
    mat = material_for(img, "mat_prop_wall_garden")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modular 10.0m Low Garden Wall
    # Wall spans X: -5.0m to +5.0m (Width: 10.0m, Thickness: 0.28m, H: 0.82m)
    # Coping: Width: 10.0m, Thickness: 0.36m, H: 0.10m at Z = 0.82m
    # 3 Piers: Left (-4.8m), Center (0.0m), Right (+4.8m)
    # =========================================================================

    # 1. Main Brick Wall Body (10.0m length)
    register_box("WallBody", 10.0, 0.28, 0.82, (0.0, 0.0, 0.0),
                 front=R_WALL_BRICK, sides=R_WALL_BRICK, top=R_STONE_COPING)

    # 2. Continuous Stone Coping Saddleback (0.36m width overhang, Z = 0.82m)
    register_box("WallCoping", 10.0, 0.36, 0.10, (0.0, 0.0, 0.82),
                 front=R_STONE_COPING, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 3. 3 Brick Piers (Left X = -4.80m, Center X = 0.0m, Right X = +4.80m)
    for px in [-4.80, 0.0, 4.80]:
        # Brick Pier Pillar (0.44m x 0.44m x 0.94m)
        register_box(f"Pier_{px}", 0.44, 0.44, 0.94, (px, 0.0, 0.0),
                     front=R_PIER_BRICK, sides=R_PIER_BRICK, top=R_PIER_CAP)
        # Stone Pier Cap (0.52m x 0.52m x 0.12m at Z = 0.94m)
        register_box(f"PierCap_{px}", 0.52, 0.52, 0.12, (px, 0.0, 0.94),
                     front=R_PIER_CAP, sides=R_STONE_COPING, top=R_PIER_CAP)

    shell = kit.join(parts, "Prop_Wall_Garden_Low")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_wall_garden_low_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_wall_garden_low.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_wall_garden_low.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_wall_garden_low_preview.png")
        shutil.copy2(OUT_DIR / "prop_wall_garden_low_atlas.png", TOOLS_OUT_DIR / "prop_wall_garden_low_atlas.png")
    except Exception as e:
        print(f"[prop_wall_garden_low] note: {e}")

    print("[prop_wall_garden_low] generation complete.")


main()
