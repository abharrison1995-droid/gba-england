"""HVAC Air Ducting Kit (Mosley Cellar Lab Dungeon Prop).

Specs:
- 4.0m x 1.4m footprint, Height: 2.8m.
- Laboratory industrial ventilation ductwork:
  - Galvanized rectangular steel sheet-metal ventilation trunking with cross-break creases.
  - Industrial circular exhaust fan housing & square louvred air intake grilles.
  - Threaded rod ceiling suspension unistrut brackets.
  - 90-degree duct elbow turn, transition reducer, and inspection hatch panel.
  - Cellar brick wall backdrop with concrete floor plinth.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/dungeon_hvac_ducting.py
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
R_GALV_STEEL    = (0,   256, 256, 256)   # Galvanized spangle steel sheet metal with cross-brake creases
R_EXHAUST_FAN   = (256, 256, 256, 256)   # Circular exhaust fan grille with curved rotor blades
R_LOUVRE_GRILLE = (0,   128, 256, 128)   # Heavy industrial stamped steel air intake louvre slats
R_DUCT_SEAMS    = (256, 128, 128, 128)   # Flanged transverse duct connector slip joints (TDC/TDF)
R_CELLAR_WALL   = (384, 128, 128, 128)   # Damp Victorian cellar brick wall
R_FLOOR_CONC    = (0,   0,   256, 128)   # Cellar concrete floor base
R_HATCH_DOOR    = (256, 0,   128, 128)   # Hinged inspection access hatch with lever handles
R_UNISTRUT_ROD  = (384, 0,   128, 128)   # Slotted unistrut channel & threaded drop rods

# --- Palette Colors ---
GALV_SILVER     = (0.75, 0.77, 0.80)
GALV_DARK       = (0.50, 0.52, 0.55)
GALV_HIGHLIGHT  = (0.88, 0.90, 0.94)
FAN_BLACK       = (0.12, 0.12, 0.14)
LOUVRE_DARK     = (0.24, 0.26, 0.28)
BRICK_CELLAR    = (0.52, 0.34, 0.26)
FLOOR_GREY      = (0.42, 0.42, 0.44)


def paint_hvac_atlas():
    a = Atlas(S, seed=6301)

    # 1. Galvanized Sheet Metal with Cross-Break Creases (R_GALV_STEEL)
    x, y, w, h = R_GALV_STEEL
    a.rect(x, y, w, h, GALV_SILVER)
    # Galvanized zinc crystal spangle mottling
    for sy in range(y + 8, y + h - 8, 24):
        for sx in range(x + 8, x + w - 8, 32):
            a.disc(sx, sy, 8, (0.82, 0.84, 0.88))
            a.disc(sx + 10, sy + 6, 6, (0.65, 0.67, 0.70))
    # Diagonal Cross-Brake Stiffener Creases ('X' crease on sheet)
    for step in range(0, w, 4):
        a.disc(x + step, y + step, 2, GALV_DARK)
        a.disc(x + step, y + step + 2, 1, GALV_HIGHLIGHT)
        a.disc(x + step, y + h - step, 2, GALV_DARK)
        a.disc(x + step, y + h - step + 2, 1, GALV_HIGHLIGHT)
    # Rivet / screw seams along edges
    for rx in range(x + 12, x + w, 24):
        a.disc(rx, y + 8, 3, (0.3, 0.3, 0.3))
        a.disc(rx, y + h - 8, 3, (0.3, 0.3, 0.3))
    a.noise(x, y, w, h, 0.02)

    # 2. Circular Exhaust Fan (R_EXHAUST_FAN)
    x, y, w, h = R_EXHAUST_FAN
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    cx, cy = x + w // 2, y + h // 2
    # Heavy outer steel mounting flange
    a.disc(cx, cy, 105, GALV_SILVER)
    a.disc(cx, cy, 90, FAN_BLACK)
    # 6 Curved Fan Rotor Blades
    for deg in range(0, 360, 60):
        rad = math.radians(deg)
        for step in range(15, 80, 5):
            bx = int(cx + step * math.cos(rad + step * 0.015))
            by = int(cy + step * math.sin(rad + step * 0.015))
            a.disc(bx, by, 10, (0.35, 0.38, 0.42))
    # Center motor hub
    a.disc(cx, cy, 26, GALV_SILVER)
    a.disc(cx, cy, 12, FAN_BLACK)
    a.noise(x, y, w, h, 0.02)

    # 3. Industrial Louvre Grilles (R_LOUVRE_GRILLE)
    x, y, w, h = R_LOUVRE_GRILLE
    a.rect(x, y, w, h, GALV_SILVER)
    # Heavy frame
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.1, 0.1, 0.1))
    # Downward-angled horizontal louvre slats
    for ly in range(y + 14, y + h - 14, 12):
        a.rect(x + 12, ly, w - 24, 6, LOUVRE_DARK)
        a.rect(x + 12, ly + 6, w - 24, 2, GALV_HIGHLIGHT)
    a.noise(x, y, w, h, 0.02)

    # 4. Flanged Duct Seams (R_DUCT_SEAMS)
    x, y, w, h = R_DUCT_SEAMS
    a.rect(x, y, w, h, (0.60, 0.62, 0.65))
    a.rect(x + w // 2 - 8, y, 16, h, (0.35, 0.36, 0.38))
    for by in range(y + 8, y + h, 16):
        a.disc(x + w // 2, by, 4, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.025)

    # 5. Cellar Brick Wall (R_CELLAR_WALL)
    x, y, w, h = R_CELLAR_WALL
    a.bricks(x, y, w, h, brick=BRICK_CELLAR, mortar=(0.35, 0.32, 0.30), bw=28, bh=12, jitter=0.06)
    a.noise(x, y, w, h, 0.035)

    # 6. Concrete Floor (R_FLOOR_CONC)
    x, y, w, h = R_FLOOR_CONC
    a.rect(x, y, w, h, FLOOR_GREY)
    a.noise(x, y, w, h, 0.03)

    # 7. Inspection Hatch Door (R_HATCH_DOOR)
    x, y, w, h = R_HATCH_DOOR
    a.rect(x, y, w, h, GALV_SILVER)
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.45, 0.47, 0.50))
    a.rect(x + 10, y + 10, w - 20, h - 20, GALV_SILVER)
    # Cam-lock handles
    a.disc(x + 24, y + h // 2, 8, (0.1, 0.1, 0.1))
    a.disc(x + w - 24, y + h // 2, 8, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.02)

    # 8. Unistrut Channel (R_UNISTRUT_ROD)
    x, y, w, h = R_UNISTRUT_ROD
    a.rect(x, y, w, h, GALV_DARK)
    for sy in range(y, y + h, 12):
        a.rect(x + 8, sy, w - 16, 4, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("dungeon_hvac_ducting_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_GALV_STEEL, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_GALV_STEEL, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_hvac_atlas()
    mat = material_for(img, "mat_hvac_ducting")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # HVAC Air Ducting Kit (4.0m x 1.4m Footprint, Height: 2.8m)
    # - Cellar Floor Base & Back Wall (Z: 0.0 to 2.80m)
    # - Main Overhead Horizontal Supply Duct (Width 4.0m, D: 0.60m, H: 0.50m at Z = 2.10m)
    # - 90-Degree Vertical Return Drop Duct (X = -1.30m, Z = 0.50m to 2.10m)
    # - Industrial Circular Exhaust Fan Housing (X = 1.00m, Z = 2.05m)
    # - Louvred Wall Intake Grille (X = -1.30m, Z = 0.55m)
    # - Ceiling Unistrut Hanger Brackets & Drop Rods
    # =========================================================================

    # 1. Cellar Concrete Floor Base (4.2m x 1.4m, Z = 0.00 to 0.10m)
    register_box("HVACFloor", 4.20, 1.40, 0.10, (0.0, 0.0, 0.0),
                 front=R_FLOOR_CONC, sides=R_FLOOR_CONC, top=R_FLOOR_CONC)

    # 2. Back Cellar Wall (4.00m x 0.30m, Z: 0.10m to 2.80m, H: 2.70m at Y = 0.50m)
    register_box("HVACBackWall", 4.00, 0.30, 2.70, (0.0, 0.50, 0.10),
                 front=R_CELLAR_WALL, sides=R_CELLAR_WALL, back=R_CELLAR_WALL, top=R_FLOOR_CONC)

    # 3. Main Overhead Horizontal Supply Duct Trunk (Width 4.00m, D: 0.60m, H: 0.50m at Z = 2.10m, Y = 0.10m)
    register_box("MainSupplyDuct", 4.00, 0.60, 0.50, (0.0, 0.10, 2.10),
                 front=R_GALV_STEEL, sides=R_DUCT_SEAMS, back=R_GALV_STEEL, top=R_GALV_STEEL)

    # 4. Vertical Drop Duct (X = -1.30m, Width: 0.50m, D: 0.50m, H: 1.50m, Z = 0.60m to 2.10m)
    register_box("VertDropDuct", 0.50, 0.50, 1.50, (-1.30, 0.10, 0.60),
                 front=R_GALV_STEEL, sides=R_GALV_STEEL, back=R_GALV_STEEL, top=R_GALV_STEEL)

    # 5. Inspection Access Hatch (Mounted on horizontal duct center: X = 0.0m)
    register_box("AccessHatch", 0.60, 0.05, 0.38, (0.0, -0.22, 2.16),
                 front=R_HATCH_DOOR, sides=R_DUCT_SEAMS, top=R_DUCT_SEAMS)

    # 6. Industrial Circular Exhaust Fan Housing (X = 1.00m, Mounted projecting on front of duct)
    register_box("ExhaustFanHousing", 0.55, 0.20, 0.55, (1.00, -0.25, 2.08),
                 front=R_EXHAUST_FAN, sides=R_DUCT_SEAMS, top=R_DUCT_SEAMS)

    # 7. Lower Louvred Air Intake Grille Box (X = -1.30m, Z = 0.30m to 0.60m)
    register_box("IntakeGrilleBox", 0.65, 0.35, 0.40, (-1.30, 0.05, 0.20),
                 front=R_LOUVRE_GRILLE, sides=R_GALV_STEEL, top=R_GALV_STEEL)

    # 8. Ceiling Unistrut Hanger Rods (X = -1.80m, +1.80m, Z = 2.60m to 2.80m)
    register_box("HangerRodL", 0.06, 0.65, 0.20, (-1.80, 0.10, 2.60),
                 front=R_UNISTRUT_ROD, sides=R_UNISTRUT_ROD, top=R_UNISTRUT_ROD)
    register_box("HangerRodR", 0.06, 0.65, 0.20, (1.80, 0.10, 2.60),
                 front=R_UNISTRUT_ROD, sides=R_UNISTRUT_ROD, top=R_UNISTRUT_ROD)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Dungeon_HVAC_Ducting")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "dungeon_hvac_ducting_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "dungeon_hvac_ducting.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "dungeon_hvac_ducting.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "dungeon_hvac_ducting_preview.png")
        shutil.copy2(OUT_DIR / "dungeon_hvac_ducting_atlas.png", TOOLS_OUT_DIR / "dungeon_hvac_ducting_atlas.png")
    except Exception as e:
        print(f"[dungeon_hvac_ducting] note: {e}")

    print("[dungeon_hvac_ducting] generation complete.")


main()
