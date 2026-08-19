"""Abandoned London Bus Station - Variant 3: Suburban Steel Truss Passenger Interchange & Shelter.

Specs:
- 10.0m x 8.0m footprint.
- Dual-island curved arched passenger canopy with rusted yellow/red steel tubular trusses and polycarbonate roof panels.
- Vandalized glass & steel waiting cubicle with shattered glass textures and graffiti tags.
- Derelict ticket machine kiosk, rusted route map stanchion, and weeds growing through cracked tarmac.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_bus_station_03.py
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
R_CANOPY_CORRUG  = (0,   256, 256, 256)   # Arched corrugated roof panels
R_SHATTERED_GLS  = (256, 256, 128, 256)   # Shattered tempered glass waiting panels
R_TRUSS_STEEL    = (0,   128, 256, 128)   # Yellow/red rusted tubular steel truss
R_KIOSK_METAL    = (256, 128, 128, 128)   # Vandalized ticket vending machine & kiosk
R_BUS_MAP_SIGN   = (384, 384, 128, 128)   # Rusted route map billboard
R_APRON_CRACKED  = (384, 256, 128, 128)   # Cracked asphalt apron with weeds
R_STONE_KERB     = (0,   64,  256, 64)    # Kerbstones & platform edge
R_GRAFFITI_TAG   = (256, 64,  128, 64)    # Graffiti tags on enamel panels

# --- Colors ---
STEEL_YELLOW     = (0.80, 0.65, 0.16)
STEEL_RED        = (0.68, 0.20, 0.18)
RUST_DARK        = (0.34, 0.19, 0.13)
RUST_ORANGE      = (0.58, 0.30, 0.15)
GLASS_SHATTER    = (0.24, 0.30, 0.34)
ASPHALT_CRACK    = (0.28, 0.29, 0.31)
WEED_GREEN       = (0.28, 0.38, 0.22)
KERB_BASE        = (0.70, 0.69, 0.66)


def paint_station_03_atlas():
    a = Atlas(S, seed=1401)

    # 1. Arched Corrugated Canopy (R_CANOPY_CORRUG)
    x, y, w, h = R_CANOPY_CORRUG
    a.rect(x, y, w, h, (0.42, 0.44, 0.46))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.26, 0.28, 0.30))
        if ry % 16 == 0:
            a.rect(x, ry, w, 2, RUST_DARK)
    a.noise(x, y, w, h, 0.035)

    # 2. Shattered Glass Shelter Panels (R_SHATTERED_GLS)
    x, y, w, h = R_SHATTERED_GLS
    a.rect(x, y, w, h, GLASS_SHATTER)
    # Spider-web glass cracks & fractured lines
    cx, cy = x + w // 2, y + h // 2
    for angle_deg in range(0, 360, 30):
        rad = math.radians(angle_deg)
        for r_step in range(10, 55, 12):
            px = int(cx + r_step * math.cos(rad))
            py = int(cy + r_step * math.sin(rad))
            a.disc(px, py, 2, (0.85, 0.90, 0.95))
    a.rect(x + 4, y + 4, 30, h - 8, (0.15, 0.18, 0.20))  # Missing glass hole
    a.noise(x, y, w, h, 0.03)

    # 3. Rusted Steel Truss (R_TRUSS_STEEL)
    x, y, w, h = R_TRUSS_STEEL
    a.rect(x, y, w, h, STEEL_YELLOW)
    for ry in range(y + 8, y + h - 8, 16):
        a.rect(x + 4, ry, w - 8, 4, RUST_DARK)
        a.rect(x + 8, ry + 1, w - 16, 2, RUST_ORANGE)
    a.noise(x, y, w, h, 0.03)

    # 4. Ticket Machine / Kiosk (R_KIOSK_METAL)
    x, y, w, h = R_KIOSK_METAL
    a.rect(x, y, w, h, (0.35, 0.38, 0.40))
    # Smashed screen & coin slot
    a.rect(x + 12, y + h - 50, w - 24, 32, (0.12, 0.14, 0.16))
    a.rect(x + 16, y + h - 46, w - 32, 24, (0.20, 0.24, 0.28))
    a.rect(x + 16, y + 20, w - 32, 10, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.03)

    # 5. Route Map Billboard (R_BUS_MAP_SIGN)
    x, y, w, h = R_BUS_MAP_SIGN
    a.rect(x, y, w, h, (0.85, 0.85, 0.82))
    a.rect(x + 6, y + h - 24, w - 12, 16, STEEL_RED)
    # Faded map lines
    for my in range(y + 16, y + h - 32, 14):
        a.rect(x + 10, my, w - 20, 3, (0.35, 0.50, 0.65))
    a.noise(x, y, w, h, 0.03)

    # 6. Cracked Apron with Weeds (R_APRON_CRACKED)
    x, y, w, h = R_APRON_CRACKED
    a.rect(x, y, w, h, ASPHALT_CRACK)
    # Weed patches
    a.disc(x + 30, y + 30, 16, WEED_GREEN)
    a.disc(x + 80, y + 90, 20, WEED_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 7. Stone Kerb (R_STONE_KERB)
    x, y, w, h = R_STONE_KERB
    a.rect(x, y, w, h, KERB_BASE)
    for ky in range(y, y + h, 32):
        a.rect(x, ky, w, 2, (0.48, 0.47, 0.44))
    a.noise(x, y, w, h, 0.03)

    # 8. Graffiti Tag (R_GRAFFITI_TAG)
    x, y, w, h = R_GRAFFITI_TAG
    a.rect(x, y, w, h, (0.50, 0.52, 0.55))
    a.rect(x + 12, y + 14, 50, 18, (0.80, 0.10, 0.10))
    a.rect(x + 66, y + 18, 48, 14, (0.10, 0.70, 0.30))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_03_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_KERB, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_KERB, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_station_03_atlas()
    mat = material_for(img, "mat_bus_station_03")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Abandoned Bus Station 03: Modernist Steel Truss Passenger Interchange
    # Footprint: 10.0m x 8.0m
    # Raised Passenger Platform Island: 10.0m x 4.0m, Z = 0.18m
    # Arched Twin Canopies on Tubular Trusses: Height 3.8m
    # Shattered Passenger Waiting Shelter & Ticket Machine
    # =========================================================================

    # 1. Base Concourse & Bus Bay Apron
    register_box("InterchangeApron", 10.0, 8.0, 0.08, (0.0, 0.0, 0.0),
                 front=R_STONE_KERB, sides=R_STONE_KERB, top=R_APRON_CRACKED)

    # 2. Raised Platform Island (X: -5.0 to +5.0, Y: 0.0 to 4.0, Z: 0.08 to 0.22m)
    register_box("PlatformIsland", 10.0, 3.80, 0.16, (0.0, 1.90, 0.08),
                 front=R_STONE_KERB, sides=R_STONE_KERB, top=R_STONE_KERB)

    # 3. Main Interchange Canopy Roof (10.0m x 5.0m, Z = 3.40m to 3.75m)
    register_box("InterchangeCanopy", 10.0, 5.00, 0.25, (0.0, 0.80, 3.45),
                 front=R_CANOPY_CORRUG, sides=R_TRUSS_STEEL, top=R_CANOPY_CORRUG)

    # 4. 4 Yellow Tubular Steel Support Trusses (X = -4.0, -1.3, +1.3, +4.0 at Y = 1.80m)
    for px in [-4.0, -1.3, 1.3, 4.0]:
        register_box(f"TrussPost_{px}", 0.30, 0.30, 3.45, (px, 1.80, 0.22),
                     front=R_TRUSS_STEEL, sides=R_TRUSS_STEEL, top=R_TRUSS_STEEL)

    # 5. Shattered Glass Passenger Waiting Shelter (X = -1.5m to +1.5m, Y = 2.0m, H: 2.3m)
    register_box("GlassShelterBack", 3.20, 0.12, 2.30, (0.0, 2.80, 0.22),
                 front=R_SHATTERED_GLS, sides=R_TRUSS_STEEL, back=R_GRAFFITI_TAG)
    register_box("GlassShelterSideL", 0.12, 1.40, 2.30, (-1.60, 2.10, 0.22),
                 front=R_SHATTERED_GLS, sides=R_TRUSS_STEEL, top=R_TRUSS_STEEL)
    register_box("GlassShelterSideR", 0.12, 1.40, 2.30, (1.60, 2.10, 0.22),
                 front=R_SHATTERED_GLS, sides=R_TRUSS_STEEL, top=R_TRUSS_STEEL)

    # 6. Derelict Ticket Machine Kiosk (X = 3.20m, Y = 2.20m)
    register_box("TicketKiosk", 0.90, 0.70, 1.85, (3.20, 2.20, 0.22),
                 front=R_KIOSK_METAL, sides=R_GRAFFITI_TAG, top=R_TRUSS_STEEL)

    # 7. Route Map Billboard Stand (X = -3.20m, Y = 2.20m)
    register_box("MapBillboard", 1.20, 0.15, 1.60, (-3.20, 2.20, 0.80),
                 front=R_BUS_MAP_SIGN, sides=R_TRUSS_STEEL, top=R_TRUSS_STEEL)

    shell = kit.join(parts, "Building_Bus_Station_03")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_03_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_03.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_bus_station_03.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_bus_station_03_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_03_atlas.png", TOOLS_OUT_DIR / "building_bus_station_03_atlas.png")
    except Exception as e:
        print(f"[building_bus_station_03] note: {e}")

    print("[building_bus_station_03] generation complete.")


main()
