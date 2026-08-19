"""Metropolitan London Police Station (10.0m x 8.0m Civic Municipal Unit).

Specs:
- 10.0m x 8.0m footprint, Height: 7.2m to parapet / antenna.
- Classic British Metropolitan Police Station:
  - Dressed Portland stone plinth and London stock/blue-grey brick civic facade.
  - Prominent blue & white header sign: "METROPOLITAN POLICE - CENTRAL DIVISION".
  - Iconic blue hexagonal illuminated "POLICE" wall lantern lamp.
  - Heavy glazed security entrance doors with electronic intercom / keycard access.
  - Barred custody suite / station windows with steel security grilles.
  - Flat roof with stone parapet coping, HVAC ventilation unit, and police radio antenna mast.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_police_station.py
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
R_POLICE_SIGN   = (0,   384, 512, 128)   # "METROPOLITAN POLICE" blue & white header sign
R_POLICE_BRICK  = (0,   128, 256, 256)   # Blue-grey/London brick with barred security windows
R_POLICE_DOORS  = (256, 128, 128, 256)   # Reinforced security entrance with intercom & blue crest
R_STONE_TRIM    = (384, 256, 128, 128)   # Dressed Portland stone bands, coping & plinth
R_BLUE_LANTERN  = (384, 128, 128, 128)   # Iconic blue glowing "POLICE" lantern lamp
R_ROOF_GRAVEL   = (0,   0,   256, 128)   # Flat bitumen/gravel roof deck with water marks
R_HVAC_UNIT     = (256, 0,   128, 128)   # Rooftop air handling / AC chiller unit
R_CUSTODY_GATE  = (384, 0,   128, 128)   # Steel mesh custody vehicle gate / fence

# --- Palette Colors ---
POLICE_BLUE     = (0.06, 0.22, 0.48)
POLICE_DARK     = (0.02, 0.08, 0.20)
POLICE_WHITE    = (0.96, 0.96, 0.98)
POLICE_CYAN     = (0.25, 0.70, 0.95)
STONE_PORTLAND  = (0.82, 0.80, 0.76)
BRICK_GREY      = (0.42, 0.44, 0.46)
BRICK_MORTAR    = (0.62, 0.60, 0.58)
STEEL_DARK      = (0.22, 0.24, 0.26)
GLASS_TINTED    = (0.16, 0.24, 0.30)
YELLOW_SILL     = (0.92, 0.75, 0.12)


def paint_police_atlas():
    a = Atlas(S, seed=2001)

    # 1. "METROPOLITAN POLICE" Sign (R_POLICE_SIGN)
    x, y, w, h = R_POLICE_SIGN
    a.rect(x, y, w, h, POLICE_BLUE)
    # White border & police checkerboard sill strip
    a.rect(x, y + h - 8, w, 8, POLICE_WHITE)
    a.rect(x, y, w, 8, POLICE_WHITE)
    # Checkerboard sill bar (Sillium band)
    for bx in range(x + 8, x + w - 8, 20):
        a.rect(bx, y + 10, 10, 10, POLICE_WHITE)
        a.rect(bx + 10, y + 10, 10, 10, POLICE_DARK)

    # Metropolitan Police Star Crest on left & right
    for cx in [x + 28, x + w - 28]:
        a.disc(cx, y + h // 2, 16, POLICE_WHITE)
        a.disc(cx, y + h // 2, 12, POLICE_BLUE)
        a.disc(cx, y + h // 2, 5, POLICE_WHITE)

    # Main Bold White Text: "METROPOLITAN POLICE" (scale=4)
    s1 = "METROPOLITAN POLICE"
    tw = a.text_width(s1, scale=4)
    tx = x + (w - tw) // 2
    ty = y + h - 18
    a.text(tx + 2, ty - 2, s1, POLICE_DARK, scale=4)
    a.text(tx, ty, s1, POLICE_WHITE, scale=4)

    # Subtitle: "CENTRAL DIVISION - 24HR ACCESS"
    s2 = "CENTRAL DIVISION - 24HR ACCESS"
    sw = a.text_width(s2, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 26, s2, (0.80, 0.90, 1.0), scale=2)
    a.noise(x, y, w, h, 0.015)

    # 2. Brick Wall with Barred Security Windows (R_POLICE_BRICK)
    x, y, w, h = R_POLICE_BRICK
    a.bricks(x, y, w, h, brick=BRICK_GREY, mortar=BRICK_MORTAR, bw=28, bh=12, jitter=0.06)
    # Stone banding
    a.rect(x, y + 120, w, 12, STONE_PORTLAND)
    # Barred Security Windows (2 rows)
    for wy in [y + 20, y + 140]:
        for wx in [x + 20, x + 100, x + 180]:
            # Stone frame
            a.rect(wx, wy, 56, 76, STONE_PORTLAND)
            a.rect(wx + 4, wy + 4, 48, 68, GLASS_TINTED)
            # Heavy vertical steel security bars
            for bar_x in range(wx + 8, wx + 50, 8):
                a.rect(bar_x, wy + 4, 3, 68, STEEL_DARK)
            # Horizontal cross-tie bar
            a.rect(wx + 4, wy + 38, 48, 3, STEEL_DARK)
    a.noise(x, y, w, h, 0.025)

    # 3. Heavy Security Entrance Doors (R_POLICE_DOORS)
    x, y, w, h = R_POLICE_DOORS
    a.rect(x, y, w, h, STONE_PORTLAND)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, STEEL_DARK)
    # Glass inspection panels
    a.rect(dx + 8, dy + 100, dw // 2 - 12, 110, GLASS_TINTED)
    a.rect(dx + dw // 2 + 4, dy + 100, dw // 2 - 12, 110, GLASS_TINTED)
    # Blue police crest badge
    a.disc(dx + dw // 2, dy + dh - 24, 14, POLICE_BLUE)
    a.disc(dx + dw // 2, dy + dh - 24, 6, POLICE_WHITE)
    # Electronic Keypad & Intercom panel on right jamb
    a.rect(dx + dw - 12, dy + 80, 8, 28, (0.12, 0.12, 0.14))
    a.disc(dx + dw - 8, dy + 98, 2, (0.2, 0.9, 0.2))  # green LED
    # Bottom kickplates
    a.rect(dx + 4, dy + 4, dw - 8, 30, (0.35, 0.38, 0.40))
    a.noise(x, y, w, h, 0.02)

    # 4. Portland Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_PORTLAND)
    for qy in range(y, y + h, 24):
        a.rect(x, qy, w, 2, (0.60, 0.58, 0.54))
    a.noise(x, y, w, h, 0.025)

    # 5. Blue Police Wall Lantern Lamp (R_BLUE_LANTERN)
    x, y, w, h = R_BLUE_LANTERN
    a.rect(x, y, w, h, (0.15, 0.15, 0.18))
    # Wall mounting bracket
    a.rect(x + 16, y + 10, w - 32, 14, STEEL_DARK)
    # Glowing Blue Hexagonal Lantern Core
    a.disc(x + w // 2, y + h // 2 + 6, 32, POLICE_BLUE)
    a.disc(x + w // 2, y + h // 2 + 6, 24, POLICE_CYAN)
    a.disc(x + w // 2, y + h // 2 + 6, 12, POLICE_WHITE)
    # Text "POLICE" on lamp
    s_lamp = "POLICE"
    lw = a.text_width(s_lamp, scale=1)
    a.text(x + (w - lw) // 2, y + 22, s_lamp, POLICE_WHITE, scale=1)
    a.noise(x, y, w, h, 0.015)

    # 6. Roof Bitumen & Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, (0.32, 0.34, 0.36))
    a.noise(x, y, w, h, 0.045)

    # 7. Rooftop HVAC Chiller Unit (R_HVAC_UNIT)
    x, y, w, h = R_HVAC_UNIT
    a.rect(x, y, w, h, (0.45, 0.48, 0.50))
    for ly in range(y + 8, y + h - 8, 10):
        a.rect(x + 6, ly, w - 12, 5, (0.22, 0.24, 0.26))
    a.noise(x, y, w, h, 0.03)

    # 8. Custody Vehicle Gate / Fence (R_CUSTODY_GATE)
    x, y, w, h = R_CUSTODY_GATE
    a.rect(x, y, w, h, STEEL_DARK)
    # Metal mesh grid
    for my in range(y + 6, y + h, 12):
        a.rect(x, my, w, 2, (0.45, 0.48, 0.50))
    for mx in range(x + 6, x + w, 12):
        a.rect(mx, y, 2, h, (0.45, 0.48, 0.50))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_police_station_atlas", OUT_DIR)


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
    img = paint_police_atlas()
    mat = material_for(img, "mat_police_station")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Metropolitan Police Station (10.0m x 8.0m Modular Footprint)
    # - 2-Storey Civic Building with Portland Stone Trim & Parapet
    # - "METROPOLITAN POLICE" Bold Blue Header Sign
    # - Iconic Blue Glowing "POLICE" Wall Lantern Lamp
    # - Heavy Security Entrance Doors + Barred Detention Windows
    # - Rooftop HVAC Chiller Unit & Radio Communications Antenna Spire
    # =========================================================================

    # 1. Stone Plinth & Entrance Steps (10.0m x 8.5m, Z = 0.00 to 0.15m)
    register_box("StationPlinth", 10.0, 8.50, 0.15, (0.0, -0.25, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Station Body (10.0m x 7.5m, Z: 0.15 to 6.20m, H: 6.05m)
    register_box("StationBody", 10.0, 7.50, 6.05, (0.0, 0.25, 0.15),
                 front=R_POLICE_BRICK, sides=R_POLICE_BRICK, back=R_POLICE_BRICK)

    # 3. Parapet Cornice & Flat Roof (Z = 6.20m to 6.70m, H: 0.50m)
    register_box("StationParapet", 10.20, 7.70, 0.50, (0.0, 0.25, 6.20),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_ROOF_GRAVEL)

    # 4. Prominent "METROPOLITAN POLICE" Header Sign (Z = 3.30m to 4.55m, H: 1.25m)
    register_box("PoliceSignBoard", 9.80, 0.30, 1.25, (0.0, -3.65, 3.30),
                 front=R_POLICE_SIGN, sides=R_POLICE_SIGN, top=R_STONE_TRIM)

    # 5. Heavy Security Entrance Doors (Z = 0.15 to 3.25m, H: 3.10m)
    register_box("SecurityDoors", 2.40, 0.18, 3.10, (0.0, -3.58, 0.15),
                 front=R_POLICE_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Iconic Blue "POLICE" Lantern Lamp (Mounted over entrance at Z = 4.60m)
    register_box("PoliceLantern", 0.60, 0.60, 0.85, (0.0, -3.80, 4.60),
                 front=R_BLUE_LANTERN, sides=R_BLUE_LANTERN, top=R_BLUE_LANTERN)

    # 7. Flanking Barred Windows (Left X = -3.20m, Right X = +3.20m)
    for wx in [-3.20, 3.20]:
        register_box(f"CustodyWin_{wx}", 3.00, 0.15, 2.70, (wx, -3.55, 0.35),
                     front=R_POLICE_BRICK, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Rooftop HVAC Chiller Unit (X = -2.20m, Y = 0.50m, Z = 6.70m)
    register_box("HVACChiller", 2.40, 1.80, 1.10, (-2.20, 0.50, 6.70),
                 front=R_HVAC_UNIT, sides=R_HVAC_UNIT, top=R_HVAC_UNIT)

    # 9. Radio Communications Antenna Spire (X = 3.20m, Y = 0.50m, Z = 6.70m to 9.20m)
    register_box("AntennaBase", 0.60, 0.60, 0.40, (3.20, 0.50, 6.70),
                 front=R_HVAC_UNIT, sides=R_HVAC_UNIT, top=R_HVAC_UNIT)
    register_box("AntennaMast", 0.10, 0.10, 2.20, (3.20, 0.50, 7.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Police_Station")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_police_station_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_police_station.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_police_station.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_police_station_preview.png")
        shutil.copy2(OUT_DIR / "building_police_station_atlas.png", TOOLS_OUT_DIR / "building_police_station_atlas.png")
    except Exception as e:
        print(f"[building_police_station] note: {e}")

    print("[building_police_station] generation complete.")


main()
