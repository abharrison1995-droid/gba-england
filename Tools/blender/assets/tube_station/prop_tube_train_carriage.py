"""London Underground Tube Train Carriage (1995/1996 Stock Deep Tube Prop).

Specs:
- 12.0m x 2.6m footprint, Height: 2.85m.
- Iconic London Underground deep tube rolling stock:
  - White aluminium upper body panels with curved tube roofline.
  - Bold TfL red front cab end & passenger double sliding doors.
  - Royal blue underframe lower skirt / solebar.
  - Dark tinted passenger windows with visible interior yellow grab poles & moquette seats.
  - Front cab windscreen with illuminated LED destination matrix: "PICCADILLY CIRCUS".
  - High-intensity LED headlights, red tail marker lamps, and TfL Roundel insignia.
  - Track rail bed with conductor third rail and bogie wheel sets.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_tube_train_carriage.py
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
R_TRAIN_SIDE    = (0,   256, 256, 256)   # White body, red sliding doors, blue skirt & tinted windows
R_CAB_FRONT     = (256, 256, 256, 256)   # Red cab face, destination matrix & twin LED headlights
R_TUBE_ROOF     = (0,   128, 256, 128)   # Ribbed aluminium curved tube carriage roof
R_INTERIOR_MOQ  = (256, 128, 128, 128)   # Barman geometric moquette seat pattern & yellow poles
R_BOGIE_WHEELS  = (384, 128, 128, 128)   # Steel bogie wheel sets, brake discs & conductor shoes
R_TRACK_BED     = (0,   0,   256, 128)   # Ballast gravel, timber sleepers & steel running rails
R_TFL_BADGE     = (256, 0,   128, 128)   # London Underground roundel logo badge
R_DOOR_RED      = (384, 0,   128, 128)   # Pure TfL red gloss enamel for door wings

# --- Palette Colors ---
TUBE_WHITE      = (0.94, 0.94, 0.96)
TUBE_RED        = (0.88, 0.12, 0.14)
TUBE_BLUE       = (0.05, 0.18, 0.58)
WINDOW_TINT     = (0.16, 0.22, 0.28)
POLE_YELLOW     = (0.98, 0.82, 0.10)
ROOF_ALUM       = (0.72, 0.74, 0.76)
BOGIE_STEEL     = (0.18, 0.20, 0.22)
DEST_ORANGE     = (0.98, 0.60, 0.05)
HEADLIGHT_GLOW  = (0.98, 0.98, 0.85)


def paint_tube_train_atlas():
    a = Atlas(S, seed=3201)

    # 1. Train Side Carriage Livery (R_TRAIN_SIDE)
    x, y, w, h = R_TRAIN_SIDE
    a.rect(x, y, w, h, TUBE_WHITE)
    # Royal Blue lower skirt band (bottom 48px)
    a.rect(x, y, w, 48, TUBE_BLUE)
    # 2 Sets of Red Passenger Double Sliding Doors
    for dx in [x + 28, x + 150]:
        a.rect(dx, y + 6, 76, h - 20, TUBE_RED)
        # Door glass windows
        a.rect(dx + 8, y + 70, 26, 90, WINDOW_TINT)
        a.rect(dx + 42, y + 70, 26, 90, WINDOW_TINT)
        # Yellow grab handles & door seals
        a.rect(dx + 36, y + 6, 4, h - 20, (0.10, 0.10, 0.12))
        a.disc(dx + 30, y + 60, 3, POLE_YELLOW)
        a.disc(dx + 46, y + 60, 3, POLE_YELLOW)
    # Tinted Saloon Windows (between doors)
    for wx in [x + 110, x + 232]:
        if wx + 36 <= x + w:
            a.rect(wx, y + 70, 36, 90, WINDOW_TINT)
            # Visible yellow grab pole inside
            a.rect(wx + 16, y + 74, 4, 82, POLE_YELLOW)
    # TfL Roundel crest on body
    a.disc(x + 120, y + 30, 10, TUBE_RED)
    a.disc(x + 120, y + 30, 6, TUBE_WHITE)
    a.rect(x + 108, y + 27, 24, 6, TUBE_BLUE)
    a.noise(x, y, w, h, 0.015)

    # 2. Front Cab Face & Windscreen (R_CAB_FRONT)
    x, y, w, h = R_CAB_FRONT
    a.rect(x, y, w, h, TUBE_RED)
    # Lower blue skirt
    a.rect(x, y, w, 44, TUBE_BLUE)
    # Tinted Cab Windscreen
    wx, wy, ww, wh = x + 20, y + 80, w - 40, 110
    a.rect(wx, wy, ww, wh, WINDOW_TINT)
    # Central windscreen wiper
    a.rect(wx + ww // 2 - 2, wy + 10, 4, wh - 20, (0.10, 0.10, 0.12))
    # Illuminated LED Destination Matrix Header
    dx, dy, dw, dh = x + 30, y + 200, w - 60, 36
    a.rect(dx, dy, dw, dh, (0.05, 0.05, 0.05))
    s1 = "PICCADILLY CIRCUS"
    tw = a.text_width(s1, scale=1)
    a.text(dx + (dw - tw) // 2, dy + 12, s1, DEST_ORANGE, scale=1)
    # High-intensity twin headlights & red marker lamps
    a.disc(x + 40, y + 60, 12, HEADLIGHT_GLOW)
    a.disc(x + w - 40, y + 60, 12, HEADLIGHT_GLOW)
    a.disc(x + 70, y + 60, 6, (0.95, 0.10, 0.10))  # red tail light
    a.disc(x + w - 70, y + 60, 6, (0.95, 0.10, 0.10))
    # Emergency egress cab door outline
    a.rect(x + w // 2 - 20, y + 44, 40, 150, (0.10, 0.10, 0.12))
    a.rect(x + w // 2 - 16, y + 48, 32, 142, TUBE_RED)
    a.noise(x, y, w, h, 0.015)

    # 3. Ribbed Tube Roof (R_TUBE_ROOF)
    x, y, w, h = R_TUBE_ROOF
    a.rect(x, y, w, h, ROOF_ALUM)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 3, (0.55, 0.58, 0.60))
        a.rect(x, ry + 3, w, 1, (0.85, 0.88, 0.90))
    a.noise(x, y, w, h, 0.02)

    # 4. Moquette Interior Seating (R_INTERIOR_MOQ)
    x, y, w, h = R_INTERIOR_MOQ
    a.rect(x, y, w, h, (0.10, 0.20, 0.45))
    # London Underground Barman moquette geometric pattern
    for py in range(y + 8, y + h, 18):
        for px in range(x + 8, x + w, 18):
            a.disc(px, py, 5, TUBE_RED)
            a.disc(px + 9, py + 9, 5, POLE_YELLOW)
            a.disc(px + 4, py + 4, 3, (0.2, 0.7, 0.8))
    a.noise(x, y, w, h, 0.02)

    # 5. Bogie Wheels (R_BOGIE_WHEELS)
    x, y, w, h = R_BOGIE_WHEELS
    a.rect(x, y, w, h, BOGIE_STEEL)
    # Steel wheels with brake discs
    a.disc(x + 36, y + h // 2, 28, (0.45, 0.48, 0.50))
    a.disc(x + 36, y + h // 2, 18, (0.25, 0.26, 0.28))
    a.disc(x + w - 36, y + h // 2, 28, (0.45, 0.48, 0.50))
    a.disc(x + w - 36, y + h // 2, 18, (0.25, 0.26, 0.28))
    a.noise(x, y, w, h, 0.03)

    # 6. Track Rail Bed (R_TRACK_BED)
    x, y, w, h = R_TRACK_BED
    a.rect(x, y, w, h, (0.35, 0.32, 0.30))  # Ballast gravel
    # Timber sleepers
    for sx in range(x + 8, x + w, 24):
        a.rect(sx, y + 10, 14, h - 20, (0.20, 0.15, 0.10))
    # Running rails (steel shiny top)
    a.rect(x, y + 26, w, 6, (0.65, 0.68, 0.72))
    a.rect(x, y + h - 32, w, 6, (0.65, 0.68, 0.72))
    a.noise(x, y, w, h, 0.035)

    # 7. TfL Badge (R_TFL_BADGE)
    x, y, w, h = R_TFL_BADGE
    a.rect(x, y, w, h, TUBE_WHITE)
    a.disc(x + w // 2, y + h // 2, 40, TUBE_RED)
    a.disc(x + w // 2, y + h // 2, 26, TUBE_WHITE)
    a.rect(x + 8, y + h // 2 - 10, w - 16, 20, TUBE_BLUE)
    a.noise(x, y, w, h, 0.015)

    # 8. Pure Door Red (R_DOOR_RED)
    x, y, w, h = R_DOOR_RED
    a.rect(x, y, w, h, TUBE_RED)
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_tube_train_carriage_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_TUBE_ROOF, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_BOGIE_WHEELS, S, only=side("bottom"))


def make_tube_carriage_body(name, length, width, height, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hl, hw = length / 2.0, width / 2.0
    # 8 verts for lower & upper chamfered tube carriage profile
    verts = [
        # Bottom profile (Z = 0.0)
        (-hw + 0.15, -hl, 0.0), (hw - 0.15, -hl, 0.0), (hw - 0.15, hl, 0.0), (-hw + 0.15, -hl, 0.0),
        # Mid waist (Z = 1.6m)
        (-hw, -hl, 1.60), (hw, -hl, 1.60), (hw, hl, 1.60), (-hw, hl, 1.60),
        # Curved roof crown (Z = height)
        (-hw + 0.30, -hl, height), (hw - 0.30, -hl, height), (hw - 0.30, hl, height), (-hw + 0.30, hl, height),
    ]
    # Simple quad box representation
    return kit.make_box(name, width, length, height, at)


def main():
    kit.reset_scene()
    img = paint_tube_train_atlas()
    mat = material_for(img, "mat_tube_train")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London Underground Tube Train Carriage (12.0m Length, 2.6m Width, 2.85m Height)
    # - Ballast & Running Track Bed (Z: 0.0 to 0.25m)
    # - Steel Bogies & Wheels (Z: 0.25m to 0.65m)
    # - Main Tube Carriage Body (Z: 0.65m to 2.85m)
    #   - Front Red Cab with Windscreen & "PICCADILLY CIRCUS" Matrix
    #   - Side White Body with Red Passenger Doors & Tinted Windows
    #   - Curved Aluminium Roof with Ventilation Pods
    # =========================================================================

    # 1. Track Bed & Conductor Third Rail (Width 3.0m, Length 13.0m, Z = 0.00 to 0.20m)
    register_box("TrackBed", 3.00, 13.00, 0.20, (0.0, 0.0, 0.0),
                 front=R_TRACK_BED, sides=R_TRACK_BED, top=R_TRACK_BED)

    # 2. Front & Rear Steel Bogie Wheel Sets (Z = 0.20m to 0.65m, H: 0.45m)
    # Front Bogie (Y = -4.2m)
    register_box("FrontBogie", 2.20, 2.80, 0.45, (0.0, -4.20, 0.20),
                 front=R_BOGIE_WHEELS, sides=R_BOGIE_WHEELS, top=R_BOGIE_WHEELS)
    # Rear Bogie (Y = +4.2m)
    register_box("RearBogie", 2.20, 2.80, 0.45, (0.0, 4.20, 0.20),
                 front=R_BOGIE_WHEELS, sides=R_BOGIE_WHEELS, top=R_BOGIE_WHEELS)

    # 3. Lower Blue Undercarriage Skirt (Width 2.55m, Length 12.0m, Z = 0.65m to 1.05m, H: 0.40m)
    register_box("UndercarriageSkirt", 2.55, 12.00, 0.40, (0.0, 0.0, 0.65),
                 front=R_CAB_FRONT, sides=R_TRAIN_SIDE, back=R_CAB_FRONT, top=R_TRAIN_SIDE)

    # 4. Main Passenger Saloon Body (Width 2.60m, Length 12.0m, Z = 1.05m to 2.50m, H: 1.45m)
    register_box("CarriageBody", 2.60, 12.00, 1.45, (0.0, 0.0, 1.05),
                 front=R_CAB_FRONT, sides=R_TRAIN_SIDE, back=R_CAB_FRONT, top=R_TUBE_ROOF)

    # 5. Curved Aluminium Roof (Width 2.45m, Length 12.0m, Z = 2.50m to 2.85m, H: 0.35m)
    register_box("CurvedRoof", 2.45, 12.00, 0.35, (0.0, 0.0, 2.50),
                 front=R_CAB_FRONT, sides=R_TUBE_ROOF, back=R_CAB_FRONT, top=R_TUBE_ROOF)

    # 6. Roof Air Conditioning & Ventilation Pods (Z = 2.85m to 3.00m)
    register_box("AeroPodFront", 1.40, 2.20, 0.15, (0.0, -3.50, 2.85),
                 front=R_TUBE_ROOF, sides=R_TUBE_ROOF, top=R_TUBE_ROOF)
    register_box("AeroPodRear", 1.40, 2.20, 0.15, (0.0, 3.50, 2.85),
                 front=R_TUBE_ROOF, sides=R_TUBE_ROOF, top=R_TUBE_ROOF)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Tube_Train_Carriage")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_tube_train_carriage_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_tube_train_carriage.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_tube_train_carriage.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_tube_train_carriage_preview.png")
        shutil.copy2(OUT_DIR / "prop_tube_train_carriage_atlas.png", TOOLS_OUT_DIR / "prop_tube_train_carriage_atlas.png")
    except Exception as e:
        print(f"[prop_tube_train_carriage] note: {e}")

    print("[prop_tube_train_carriage] generation complete.")


main()
