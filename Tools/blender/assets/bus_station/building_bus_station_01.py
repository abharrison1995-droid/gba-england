"""Abandoned London Bus Station - Variant 1: 1970s Brutalist Concrete & Steel Cantilever Terminal.

Specs:
- 10.0m x 8.0m footprint.
- Weathered reinforced concrete ticket office / waiting building with boarded kiosk windows and rusted grilles.
- Cantilevered concrete canopy extending over the bus boarding bay with rusted steel support columns.
- Rusted metal bus timetable display stanchion, peeling London Transport roundel sign, and cracked asphalt bus apron.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_bus_station_01.py
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
R_CONCRETE_WORN  = (0,   256, 256, 256)   # Weathered stained brutalist concrete
R_BOARDED_KIOSK  = (256, 256, 128, 256)   # Boarded ticket office kiosk & roller shutter
R_CANOPY_ROOF    = (0,   128, 256, 128)   # Fluted concrete / rusted metal canopy roof
R_RUST_STEEL     = (256, 128, 128, 128)   # Rusted steel columns & beams
R_BUS_SIGN       = (384, 384, 128, 128)   # Faded London bus timetable & stop sign
R_APRON_ASPHALT  = (384, 256, 128, 128)   # Cracked bus bay apron & yellow hatched bay
R_STONE_TRIM     = (0,   64,  256, 64)    # Kerbs and concrete edges
R_GRAFFITI_WALL  = (256, 64,  128, 64)    # Weathered brick / concrete wall with tags

# --- Colors ---
CONCRETE_GREY    = (0.58, 0.57, 0.54)
CONCRETE_STAIN   = (0.42, 0.40, 0.36)
RUST_DARK        = (0.35, 0.20, 0.14)
RUST_ORANGE      = (0.58, 0.30, 0.15)
STEEL_GREY       = (0.32, 0.33, 0.35)
WOOD_TIMBER      = (0.48, 0.36, 0.24)
SHUTTER_GREY     = (0.45, 0.46, 0.48)
BUS_RED          = (0.72, 0.15, 0.15)
YELLOW_HATCH     = (0.85, 0.72, 0.18)
ASPHALT_BASE     = (0.26, 0.27, 0.29)


def paint_station_01_atlas():
    a = Atlas(S, seed=1201)

    # 1. Weathered Brutalist Concrete (R_CONCRETE_WORN)
    x, y, w, h = R_CONCRETE_WORN
    a.rect(x, y, w, h, CONCRETE_GREY)
    # Concrete formwork panel seam lines
    for py in range(y, y + h, 48):
        a.rect(x, py, w, 2, CONCRETE_STAIN)
    for px in range(x, x + w, 64):
        a.rect(px, y, 2, h, CONCRETE_STAIN)
    # Weathering water drip stains from top
    for sx in range(x + 12, x + w - 12, 28):
        stain_len = a.rng.randint(30, 110)
        a.rect(sx, y + h - stain_len, a.rng.randint(4, 10), stain_len, (0.38, 0.36, 0.32))
    a.noise(x, y, w, h, 0.04)

    # 2. Boarded Kiosk & Derelict Roller Shutter (R_BOARDED_KIOSK)
    x, y, w, h = R_BOARDED_KIOSK
    a.rect(x, y, w, h, SHUTTER_GREY)
    # Corrugated roller shutter lines
    for sy in range(y, y + h // 2, 6):
        a.rect(x, sy, w, 2, (0.30, 0.31, 0.33))
    # Weathered timber boarding on top half
    a.rect(x + 4, y + h // 2 + 6, w - 8, h // 2 - 12, WOOD_TIMBER)
    for ty in range(y + h // 2 + 6, y + h - 6, 12):
        a.rect(x + 4, ty, w - 8, 2, (0.32, 0.24, 0.16))
    # Warning sign stencil
    a.rect(x + 16, y + h // 2 + 20, w - 32, 18, (0.85, 0.75, 0.20))
    a.rect(x + 20, y + h // 2 + 24, w - 40, 10, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.03)

    # 3. Canopy Roof (R_CANOPY_ROOF)
    x, y, w, h = R_CANOPY_ROOF
    a.rect(x, y, w, h, (0.46, 0.45, 0.43))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 3, (0.34, 0.33, 0.31))
    a.noise(x, y, w, h, 0.04)

    # 4. Rusted Steel (R_RUST_STEEL)
    x, y, w, h = R_RUST_STEEL
    a.rect(x, y, w, h, STEEL_GREY)
    for ry in range(y + 10, y + h - 10, 20):
        a.rect(x + 4, ry, w - 8, 8, RUST_DARK)
        a.rect(x + 8, ry + 2, w - 16, 4, RUST_ORANGE)
    a.noise(x, y, w, h, 0.035)

    # 5. Abandoned Bus Timetable & Station Sign (R_BUS_SIGN)
    x, y, w, h = R_BUS_SIGN
    a.rect(x, y, w, h, (0.88, 0.88, 0.86))
    # Red London Transport bar
    a.rect(x + 8, y + h - 28, w - 16, 18, BUS_RED)
    a.disc(x + w // 2, y + h - 19, 12, BUS_RED)
    a.disc(x + w // 2, y + h - 19, 8, (0.88, 0.88, 0.86))
    # Timetable lines (cracked glass effect)
    for ty in range(y + 16, y + h - 36, 12):
        a.rect(x + 12, ty, w - 24, 2, (0.35, 0.35, 0.38))
    a.noise(x, y, w, h, 0.03)

    # 6. Cracked Apron Asphalt (R_APRON_ASPHALT)
    x, y, w, h = R_APRON_ASPHALT
    a.rect(x, y, w, h, ASPHALT_BASE)
    # Faded yellow hatched bus bay markings
    for hy in range(y + 16, y + h - 16, 28):
        a.rect(x + 10, hy, w - 20, 6, YELLOW_HATCH)
    a.noise(x, y, w, h, 0.04)

    # 7. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, CONCRETE_GREY)
    a.noise(x, y, w, h, 0.03)

    # 8. Graffiti Wall (R_GRAFFITI_WALL)
    x, y, w, h = R_GRAFFITI_WALL
    a.rect(x, y, w, h, CONCRETE_GREY)
    # Spray tags
    a.rect(x + 14, y + 18, 48, 14, (0.75, 0.15, 0.55))
    a.rect(x + 68, y + 14, 42, 16, (0.15, 0.65, 0.75))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_01_atlas", OUT_DIR)


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
    img = paint_station_01_atlas()
    mat = material_for(img, "mat_bus_station_01")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Abandoned Bus Station 01: Brutalist Cantilever Terminal (10.0m x 8.0m)
    # - Rear Station Building: 10.0m x 3.5m, Height: 4.2m (Z: 0.10 to 4.30m)
    # - Cantilevered Canopy: 10.0m x 4.5m, Height: 0.35m (Z = 3.60m)
    # - 3 Support Columns along front of bay (X = -3.8m, 0.0m, +3.8m)
    # =========================================================================

    # 1. Pavement & Bus Bay Base (10.0m x 8.0m)
    register_box("StationApron", 10.0, 8.0, 0.10, (0.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_APRON_ASPHALT)

    # 2. Main Rear Concrete Building (10.0m x 3.2m, Z: 0.10 to 4.20, H: 4.10m)
    register_box("RearBuilding", 10.0, 3.20, 4.10, (0.0, 2.20, 0.10),
                 front=R_CONCRETE_WORN, sides=R_CONCRETE_WORN, back=R_GRAFFITI_WALL)

    # 3. Boarded Kiosks / Ticket Office Windows (Front facade of rear building)
    # Left Kiosk (X = -2.80m)
    register_box("KioskLeft", 3.20, 0.15, 2.40, (-2.80, 0.52, 0.40),
                 front=R_BOARDED_KIOSK, sides=R_RUST_STEEL, top=R_RUST_STEEL)
    # Right Kiosk / Shutter (X = +2.80m)
    register_box("KioskRight", 3.20, 0.15, 2.40, (2.80, 0.52, 0.40),
                 front=R_BOARDED_KIOSK, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # 4. Large Cantilever Canopy (Extends over bus boarding bay from Y = 0.5 to -3.8m)
    register_box("CanopySlab", 10.0, 4.80, 0.35, (0.0, -1.60, 3.65),
                 front=R_CONCRETE_WORN, sides=R_CONCRETE_WORN, top=R_CANOPY_ROOF)

    # 5. 3 Rusted Steel Support Pillars (X = -3.8m, 0.0m, +3.8m, at Y = -3.40m)
    for px in [-3.80, 0.0, 3.80]:
        register_box(f"Pillar_{px}", 0.35, 0.35, 3.65, (px, -3.40, 0.10),
                     front=R_RUST_STEEL, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # 6. Timetable Board / Bus Stop Stanchion (X = -1.80m, Y = -2.40m)
    register_box("TimetablePost", 0.12, 0.12, 2.30, (-1.80, -2.40, 0.10),
                 front=R_RUST_STEEL, sides=R_RUST_STEEL, top=R_RUST_STEEL)
    register_box("TimetableBoard", 0.85, 0.10, 1.30, (-1.80, -2.40, 1.20),
                 front=R_BUS_SIGN, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # 7. Parapet Cap on Roof
    register_box("RoofParapet", 10.0, 3.20, 0.30, (0.0, 2.20, 4.20),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_CANOPY_ROOF)

    shell = kit.join(parts, "Building_Bus_Station_01")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_01_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_01.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_bus_station_01.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_bus_station_01_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_01_atlas.png", TOOLS_OUT_DIR / "building_bus_station_01_atlas.png")
    except Exception as e:
        print(f"[building_bus_station_01] note: {e}")

    print("[building_bus_station_01] generation complete.")


main()
