"""Industrial Pipes & Valves Wall Kit (Mosley Cellar Lab Dungeon Prop).

Specs:
- 4.0m x 1.2m footprint, Height: 2.8m.
- Modular Victorian industrial laboratory pipework:
  - Cast-iron, copper, and insulated steam/chemical pipeline conduits.
  - Bold red circular cast-iron wheel control valves.
  - Brass analog circular pressure gauges with needle dials and glass reflections.
  - Heavy bolted flanged pipe couplings, pipe hanging clamps, and steam bleeders.
  - Damp London cellar brick wall backdrop with concrete floor plinth.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/dungeon_industrial_pipes.py
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
R_PIPE_METAL    = (0,   256, 256, 256)   # Cast iron & galvanized steel pipes with specular highlights
R_VALVE_RED     = (256, 256, 256, 256)   # Bright red circular cast-iron wheel valves
R_PRESSURE_GAUGE= (0,   128, 256, 128)   # Brass circular pressure gauges with PSI dial & needle
R_COPPER_PIPE   = (256, 128, 128, 128)   # Polished & tarnished copper tubing
R_CELLAR_BRICK  = (384, 128, 128, 128)   # Damp Victorian cellar brick with lime mortar
R_CONCRETE_BASE = (0,   0,   256, 128)   # Grimy cellar concrete floor slab
R_FLANGE_BOLTS  = (256, 0,   128, 128)   # Bolted iron pipe flanges & wall mounting brackets
R_HAZARD_LABEL  = (384, 0,   128, 128)   # Yellow/black chemical hazard warning labels: "STEAM HIGH PRESSURE"

# --- Palette Colors ---
PIPE_STEEL      = (0.45, 0.48, 0.52)
PIPE_DARK       = (0.24, 0.26, 0.28)
VALVE_RED       = (0.88, 0.14, 0.14)
VALVE_DARK      = (0.48, 0.08, 0.08)
BRASS_GAUGE     = (0.90, 0.78, 0.25)
GAUGE_FACE      = (0.95, 0.95, 0.92)
COPPER_TONE     = (0.80, 0.45, 0.25)
BRICK_CELLAR    = (0.52, 0.34, 0.26)
FLOOR_GREY      = (0.40, 0.40, 0.42)


def paint_pipes_atlas():
    a = Atlas(S, seed=6201)

    # 1. Pipe Metal (R_PIPE_METAL)
    x, y, w, h = R_PIPE_METAL
    a.rect(x, y, w, h, PIPE_STEEL)
    # Cylindrical specular highlight band
    for sy in range(y, y + h, 20):
        a.rect(x, sy, w, 4, PIPE_DARK)
        a.rect(x, sy + 8, w, 6, (0.75, 0.78, 0.82))  # bright reflection
    a.noise(x, y, w, h, 0.02)

    # 2. Red Wheel Valves (R_VALVE_RED)
    x, y, w, h = R_VALVE_RED
    a.rect(x, y, w, h, (0.15, 0.15, 0.15))
    cx, cy = x + w // 2, y + h // 2
    # Circular outer rim of valve wheel
    a.disc(cx, cy, 95, VALVE_RED)
    a.disc(cx, cy, 75, (0.15, 0.15, 0.15))
    # 4 Wheel spokes
    a.rect(cx - 8, cy - 85, 16, 170, VALVE_RED)
    a.rect(cx - 85, cy - 8, 170, 16, VALVE_RED)
    # Center brass hub
    a.disc(cx, cy, 26, BRASS_GAUGE)
    a.disc(cx, cy, 14, VALVE_DARK)
    a.noise(x, y, w, h, 0.02)

    # 3. Brass Pressure Gauges (R_PRESSURE_GAUGE)
    x, y, w, h = R_PRESSURE_GAUGE
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    # 2 Gauges side-by-side
    for gx in [x + 64, x + 192]:
        cy = y + h // 2
        a.disc(gx, cy, 54, BRASS_GAUGE)
        a.disc(gx, cy, 46, (0.1, 0.1, 0.1))
        a.disc(gx, cy, 42, GAUGE_FACE)
        # Dial tick marks & red danger zone
        a.disc(gx, cy, 18, (0.85, 0.15, 0.15))
        a.disc(gx, cy, 12, GAUGE_FACE)
        # Black indicator needle (pointing to 80 PSI)
        for step in range(5, 34, 3):
            a.disc(int(gx + step * 0.7), int(cy + step * 0.7), 2, (0.1, 0.1, 0.1))
        a.disc(gx, cy, 6, BRASS_GAUGE)
    a.noise(x, y, w, h, 0.015)

    # 4. Copper Tubing (R_COPPER_PIPE)
    x, y, w, h = R_COPPER_PIPE
    a.rect(x, y, w, h, COPPER_TONE)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, (0.50, 0.25, 0.12))
        a.rect(x, sy + 6, w, 4, (0.95, 0.70, 0.45))
    a.noise(x, y, w, h, 0.02)

    # 5. Cellar Brick Wall (R_CELLAR_BRICK)
    x, y, w, h = R_CELLAR_BRICK
    a.bricks(x, y, w, h, brick=BRICK_CELLAR, mortar=(0.35, 0.32, 0.30), bw=28, bh=12, jitter=0.06)
    a.noise(x, y, w, h, 0.035)

    # 6. Concrete Floor (R_CONCRETE_BASE)
    x, y, w, h = R_CONCRETE_BASE
    a.rect(x, y, w, h, FLOOR_GREY)
    for fy in range(y, y + h, 24):
        a.rect(x, fy, w, 2, (0.30, 0.30, 0.32))
    a.noise(x, y, w, h, 0.03)

    # 7. Flange Bolts & Brackets (R_FLANGE_BOLTS)
    x, y, w, h = R_FLANGE_BOLTS
    a.rect(x, y, w, h, PIPE_DARK)
    for bx in range(x + 16, x + w, 24):
        for by in range(y + 16, y + h, 24):
            a.disc(bx, by, 6, (0.75, 0.78, 0.80))
            a.disc(bx, by, 3, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 8. Hazard Label (R_HAZARD_LABEL)
    x, y, w, h = R_HAZARD_LABEL
    a.rect(x, y, w, h, (0.95, 0.85, 0.10))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.1, 0.1, 0.1))
    a.text(x + 10, y + h // 2 - 6, "HIGH PRESSURE", (0.95, 0.85, 0.10), scale=1)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("dungeon_industrial_pipes_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_PIPE_METAL, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_PIPE_METAL, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_pipes_atlas()
    mat = material_for(img, "mat_industrial_pipes")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Industrial Pipes & Valves Wall Kit (4.0m x 1.2m Footprint, Height: 2.8m)
    # - Cellar Concrete Floor Base (Z: 0.0 to 0.10m)
    # - Cellar Brick Backdrop Wall (Width 4.0m, D: 0.30m, H: 2.7m at Y = 0.40m)
    # - Main Heavy Horizontal Steam Pipeline (Diam 0.35m, Length 4.0m at Z = 1.80m)
    # - Lower Secondary Return Pipe (Diam 0.25m, Length 4.0m at Z = 0.65m)
    # - 2 Vertical Interconnecting Pipes with Flanges
    # - 2 Red Wheel Control Valves (X = -0.90m, +0.90m)
    # - 2 Brass Pressure Dial Gauges (X = -0.40m, +0.40m)
    # =========================================================================

    # 1. Cellar Concrete Floor (4.2m x 1.4m, Z = 0.00 to 0.10m)
    register_box("CellarFloor", 4.20, 1.40, 0.10, (0.0, 0.0, 0.0),
                 front=R_CONCRETE_BASE, sides=R_CONCRETE_BASE, top=R_CONCRETE_BASE)

    # 2. Back Cellar Brick Wall (4.00m x 0.30m, Z: 0.10m to 2.80m, H: 2.70m at Y = 0.45m)
    register_box("BackBrickWall", 4.00, 0.30, 2.70, (0.0, 0.45, 0.10),
                 front=R_CELLAR_BRICK, sides=R_CELLAR_BRICK, back=R_CELLAR_BRICK, top=R_CONCRETE_BASE)

    # 3. Main Upper Steam Pipe (Width: 4.0m, D: 0.32m, H: 0.32m at Z = 1.85m, Y = 0.15m)
    register_box("MainUpperPipe", 4.00, 0.32, 0.32, (0.0, 0.15, 1.85),
                 front=R_PIPE_METAL, sides=R_FLANGE_BOLTS, back=R_PIPE_METAL, top=R_PIPE_METAL)

    # 4. Lower Return Pipe (Width: 4.0m, D: 0.24m, H: 0.24m at Z = 0.65m, Y = 0.15m)
    register_box("LowerReturnPipe", 4.00, 0.24, 0.24, (0.0, 0.15, 0.65),
                 front=R_COPPER_PIPE, sides=R_FLANGE_BOLTS, back=R_COPPER_PIPE, top=R_COPPER_PIPE)

    # 5. 2 Vertical Connecting Pipes (X = -1.40m, +1.40m, Z = 0.65m to 1.85m)
    for px in [-1.40, 1.40]:
        register_box(f"VertPipe_{px}", 0.22, 0.22, 1.20, (px, 0.15, 0.65),
                     front=R_PIPE_METAL, sides=R_FLANGE_BOLTS, top=R_FLANGE_BOLTS)

    # 6. 2 Red Wheel Control Valves (Mounted on front of upper pipe: X = -0.90m, +0.90m)
    for vx in [-0.90, 0.90]:
        register_box(f"ValveWheel_{vx}", 0.45, 0.12, 0.45, (vx, -0.08, 1.78),
                     front=R_VALVE_RED, sides=R_FLANGE_BOLTS, back=R_VALVE_RED, top=R_VALVE_RED)

    # 7. 2 Brass Analog Pressure Gauges (Mounted above upper pipe: X = -0.35m, +0.35m)
    for gx in [-0.35, 0.35]:
        register_box(f"Gauge_{gx}", 0.30, 0.10, 0.30, (gx, -0.04, 2.22),
                     front=R_PRESSURE_GAUGE, sides=R_FLANGE_BOLTS, top=R_FLANGE_BOLTS)

    # 8. Chemical Hazard Warning Plaque (Mounted in wall center: Z = 1.25m)
    register_box("HazardPlaque", 0.60, 0.04, 0.22, (0.0, 0.28, 1.25),
                 front=R_HAZARD_LABEL, sides=R_HAZARD_LABEL, top=R_HAZARD_LABEL)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Dungeon_Industrial_Pipes")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "dungeon_industrial_pipes_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "dungeon_industrial_pipes.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "dungeon_industrial_pipes.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "dungeon_industrial_pipes_preview.png")
        shutil.copy2(OUT_DIR / "dungeon_industrial_pipes_atlas.png", TOOLS_OUT_DIR / "dungeon_industrial_pipes_atlas.png")
    except Exception as e:
        print(f"[dungeon_industrial_pipes] note: {e}")

    print("[dungeon_industrial_pipes] generation complete.")


main()
