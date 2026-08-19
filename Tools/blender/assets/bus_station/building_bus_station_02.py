"""Abandoned London Bus Station - Variant 2: 1930s Art Deco Municipal Bus Garage & Depot.

Specs:
- 10.0m x 8.5m footprint.
- Left side: 2-storey curved red-brick streamline ticket office and staff mess with round porthole windows, rusted Crittall glazing, and stepped Art Deco parapet.
- Right side: Open-span steel and corrugated iron bus parking shed with rusted truss posts and grease-stained depot floor.
- Boarded ticket window, weathered "LONDON GENERAL OMNIBUS" signage remnants, and overgrown weeds.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_bus_station_02.py
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

# --- Atlas Regions ---
R_BRICK_DECO     = (0,   256, 256, 256)   # 1930s red brick with white horizontal bands
R_SHED_ROOF      = (256, 256, 128, 256)   # Weathered rusted corrugated roof
R_CRITTALL_WIN   = (0,   128, 256, 128)   # Broken Crittall multi-pane glazing
R_BOARDED_DOOR   = (256, 128, 128, 128)   # Boarded ticket window & timber door
R_RUST_STEEL     = (384, 384, 128, 128)   # Rusted truss iron & beams
R_DEPOT_FLOOR    = (384, 256, 128, 128)   # Oil-stained concrete depot apron
R_STONE_BAND     = (0,   64,  256, 64)    # White streamline stone trim
R_DEPOT_SIGN     = (256, 64,  128, 64)    # Faded 1930s Municipal Bus Depot signage

# --- Colors ---
BRICK_RED        = (0.55, 0.22, 0.17)
BRICK_MORTAR     = (0.72, 0.69, 0.65)
STONE_WHITE      = (0.80, 0.78, 0.73)
RUST_DARK        = (0.34, 0.19, 0.13)
RUST_ORANGE      = (0.55, 0.28, 0.14)
STEEL_DARK       = (0.28, 0.29, 0.31)
GLASS_DARK       = (0.18, 0.22, 0.24)
WOOD_TIMBER      = (0.46, 0.34, 0.22)
DEPOT_CREAM      = (0.76, 0.72, 0.62)


def paint_station_02_atlas():
    a = Atlas(S, seed=1301)

    # 1. 1930s Deco Brick (R_BRICK_DECO)
    x, y, w, h = R_BRICK_DECO
    a.bricks(x, y, w, h, brick=BRICK_RED, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.08)
    # White horizontal streamline bands
    for sy in [y + 60, y + 120, y + 180]:
        a.rect(x, sy, w, 8, STONE_WHITE)
        a.rect(x, sy + 8, w, 2, (0.50, 0.48, 0.45))
    a.noise(x, y, w, h, 0.035)

    # 2. Rusted Corrugated Shed Roof (R_SHED_ROOF)
    x, y, w, h = R_SHED_ROOF
    a.rect(x, y, w, h, (0.38, 0.37, 0.36))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.24, 0.23, 0.22))
        a.rect(x, ry + 2, w, 2, RUST_DARK)
        if ry % 24 == 0:
            a.rect(x, ry, w, 4, RUST_ORANGE)
    a.noise(x, y, w, h, 0.04)

    # 3. Broken Crittall Windows (R_CRITTALL_WIN)
    x, y, w, h = R_CRITTALL_WIN
    a.rect(x, y, w, h, STONE_WHITE)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_DARK)
    # Crittall grid bars
    for gx in range(x + 16, x + w - 8, 24):
        a.rect(gx, y + 4, 2, h - 8, STEEL_DARK)
    for gy in range(y + 16, y + h - 8, 20):
        a.rect(x + 4, gy, w - 8, 2, STEEL_DARK)
    # Boarded / broken glass patch
    a.rect(x + 20, y + 20, 50, 40, WOOD_TIMBER)
    a.noise(x, y, w, h, 0.03)

    # 4. Boarded Door / Ticket Window (R_BOARDED_DOOR)
    x, y, w, h = R_BOARDED_DOOR
    a.rect(x, y, w, h, WOOD_TIMBER)
    for ty in range(y + 8, y + h, 14):
        a.rect(x, ty, w, 2, (0.28, 0.20, 0.12))
    a.rect(x + 12, y + 20, w - 24, 30, (0.30, 0.28, 0.26))  # Iron security plate
    a.noise(x, y, w, h, 0.03)

    # 5. Rusted Steel (R_RUST_STEEL)
    x, y, w, h = R_RUST_STEEL
    a.rect(x, y, w, h, STEEL_DARK)
    for ry in range(y + 12, y + h - 12, 24):
        a.rect(x + 4, ry, w - 8, 8, RUST_DARK)
        a.rect(x + 6, ry + 2, w - 12, 4, RUST_ORANGE)
    a.noise(x, y, w, h, 0.03)

    # 6. Oil-Stained Concrete Apron (R_DEPOT_FLOOR)
    x, y, w, h = R_DEPOT_FLOOR
    a.rect(x, y, w, h, (0.50, 0.49, 0.47))
    # Oil spill puddles
    a.disc(x + 40, y + 50, 24, (0.20, 0.20, 0.21))
    a.disc(x + 85, y + 80, 18, (0.22, 0.22, 0.23))
    a.noise(x, y, w, h, 0.04)

    # 7. Stone Band (R_STONE_BAND)
    x, y, w, h = R_STONE_BAND
    a.rect(x, y, w, h, STONE_WHITE)
    a.noise(x, y, w, h, 0.03)

    # 8. Depot Sign (R_DEPOT_SIGN)
    x, y, w, h = R_DEPOT_SIGN
    a.rect(x, y, w, h, DEPOT_CREAM)
    a.rect(x + 4, y + 6, w - 8, h - 12, (0.20, 0.28, 0.35))
    # Weathered sign text line
    a.rect(x + 12, y + h // 2 - 4, w - 24, 8, (0.88, 0.85, 0.70))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_02_atlas", OUT_DIR)


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
    img = paint_station_02_atlas()
    mat = material_for(img, "mat_bus_station_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Abandoned Bus Station 02: 1930s Art Deco Depot (10.0m x 8.5m)
    # - Left: 2-storey curved Brick Office Building (4.5m x 8.0m, Height: 5.4m)
    # - Right: Open Bus Garage Shed (5.5m x 8.0m, Canopy height: 4.6m)
    # =========================================================================

    # 1. Base Apron
    register_box("DepotApron", 10.0, 8.5, 0.10, (0.0, 0.0, 0.0),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_DEPOT_FLOOR)

    # 2. Left Ticket & Staff Building (X = -2.75m, 4.5m x 7.5m, Z: 0.10 to 5.20m)
    register_box("DecoBuilding", 4.50, 7.50, 5.10, (-2.75, 0.20, 0.10),
                 front=R_BRICK_DECO, sides=R_BRICK_DECO, back=R_BRICK_DECO)

    # 3. Streamline Parapet & Coping on Deco Building
    register_box("DecoParapet", 4.70, 7.70, 0.30, (-2.75, 0.20, 5.20),
                 front=R_STONE_BAND, sides=R_STONE_BAND, top=R_SHED_ROOF)

    # 4. Boarded Ticket Window & Entrance (Front face: Y = -3.55m)
    register_box("TicketWindow", 1.80, 0.15, 2.20, (-3.20, -3.55, 0.30),
                 front=R_BOARDED_DOOR, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 5. Upper Crittall Windows on Office Building (Floors 1 & 2)
    register_box("WinUpper1", 1.40, 0.15, 1.30, (-3.20, -3.55, 3.20),
                 front=R_CRITTALL_WIN, sides=R_STONE_BAND, top=R_STONE_BAND)
    register_box("WinUpper2", 1.40, 0.15, 1.30, (-1.30, -3.55, 3.20),
                 front=R_CRITTALL_WIN, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 6. Station Signage Plaque over Office (Z = 4.60m)
    register_box("StationSign", 3.20, 0.12, 0.45, (-2.75, -3.55, 4.60),
                 front=R_DEPOT_SIGN, sides=R_STONE_BAND, top=R_STONE_BAND)

    # 7. Right Open-Span Bus Shed Roof (5.5m x 7.5m, Z = 4.20m to 4.70m)
    register_box("ShedRoof", 5.50, 7.50, 0.30, (2.25, 0.20, 4.30),
                 front=R_SHED_ROOF, sides=R_RUST_STEEL, top=R_SHED_ROOF)

    # 8. Rusted Steel Shed Posts (Right outer edge: X = +4.80m at Y = -3.2m, 0.2m, +3.6m)
    for py in [-3.20, 0.20, 3.60]:
        register_box(f"ShedPost_{py}", 0.30, 0.30, 4.30, (4.80, py, 0.10),
                     front=R_RUST_STEEL, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # 9. Derelict Fuel Pump / Inspection Cabinet inside shed (X = 2.50m, Y = 1.0m)
    register_box("FuelPump", 0.60, 0.60, 1.40, (2.50, 1.00, 0.10),
                 front=R_RUST_STEEL, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    shell = kit.join(parts, "Building_Bus_Station_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_02.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_bus_station_02.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_bus_station_02_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_02_atlas.png", TOOLS_OUT_DIR / "building_bus_station_02_atlas.png")
    except Exception as e:
        print(f"[building_bus_station_02] note: {e}")

    print("[building_bus_station_02] generation complete.")


main()
