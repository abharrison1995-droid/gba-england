"""Victorian Industrial Brick Warehouse (11.0m x 8.5m Factory Unit).

Specs:
- 11.0m x 8.5m footprint, Height: 8.8m to roof ridge / crane hoist.
- Classic London Victorian industrial warehouse:
  - Weathered industrial dark red brick with arched window lintels and soot stains.
  - Large corrugated steel roller shutter loading bay with yellow/black hazard striping.
  - Projecting gable crane hoist jib beam with pulley wheel and iron hook.
  - 3 storeys of multipane industrial Crittall steel windows with wire-glass & soot patina.
  - Upper 2nd-floor double timber loft loading doors.
  - Corrugated industrial steel roof with industrial vent stacks and skylights.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_industrial_warehouse.py
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
R_BRICK_FACTORY = (0,   256, 256, 256)   # Dark industrial red brick with soot stains
R_ROLLER_DOOR   = (256, 256, 256, 256)   # Corrugated roller shutter loading door with hazard stripes
R_CRITTALL_WIN  = (0,   128, 256, 128)   # Multipane industrial Crittall factory windows
R_LOFT_DOORS    = (256, 128, 128, 128)   # Upper loft timber loading doors & crane beam
R_ROOF_CORRUG   = (0,   0,   256, 128)   # Weathered corrugated steel / slate factory roof
R_STONE_COPING  = (256, 0,   128, 128)   # Dressed stone coping, sills & concrete loading dock
R_FACTORY_SIGN  = (384, 128, 128, 128)   # Painted brick sign: "THAMES WHARF WORKS"
R_VENT_STACK    = (384, 0,   128, 128)   # Industrial galvanised steel exhaust vent pipe

# --- Palette Colors ---
BRICK_INDUSTRIAL= (0.50, 0.28, 0.20)
BRICK_MORTAR    = (0.55, 0.50, 0.45)
STEEL_ROLLER    = (0.35, 0.38, 0.40)
HAZARD_YELLOW   = (0.94, 0.82, 0.10)
HAZARD_BLACK    = (0.12, 0.12, 0.14)
CRITTALL_STEEL  = (0.20, 0.22, 0.24)
GLASS_FACTORY   = (0.24, 0.32, 0.35)
TIMBER_OAK      = (0.34, 0.24, 0.16)
ROOF_STEEL      = (0.30, 0.34, 0.38)
STONE_GREY      = (0.65, 0.62, 0.58)


def paint_warehouse_atlas():
    a = Atlas(S, seed=2201)

    # 1. Industrial Brick Wall (R_BRICK_FACTORY)
    x, y, w, h = R_BRICK_FACTORY
    a.bricks(x, y, w, h, brick=BRICK_INDUSTRIAL, mortar=BRICK_MORTAR, bw=28, bh=12, jitter=0.08)
    a.shade(x, y, w, h, top=-0.12, bottom=-0.02)  # Chimney soot at top
    a.noise(x, y, w, h, 0.04)

    # 2. Roller Shutter Loading Bay (R_ROLLER_DOOR)
    x, y, w, h = R_ROLLER_DOOR
    a.rect(x, y, w, h, STONE_GREY)  # Concrete portal frame
    dx, dy, dw, dh = x + 12, y + 12, w - 24, h - 24
    a.rect(dx, dy, dw, dh, STEEL_ROLLER)
    # Corrugation horizontal slats
    for sy in range(dy, dy + dh, 10):
        a.rect(dx, sy, dw, 3, (0.24, 0.26, 0.28))
    # Yellow & Black Hazard Striped Header Bar
    for hx in range(dx, dx + dw, 24):
        a.rect(hx, dy + dh - 28, 12, 28, HAZARD_YELLOW)
        a.rect(hx + 12, dy + dh - 28, 12, 28, HAZARD_BLACK)
    # "BAY 1 - NO PARKING" stenciled text
    s_bay = "BAY 1 - NO PARKING"
    bw = a.text_width(s_bay, scale=2)
    a.text(dx + (dw - bw) // 2, dy + dh // 2 + 10, s_bay, HAZARD_YELLOW, scale=2)
    a.noise(x, y, w, h, 0.03)

    # 3. Crittall Factory Windows (R_CRITTALL_WIN)
    x, y, w, h = R_CRITTALL_WIN
    a.rect(x, y, w, h, STONE_GREY)
    wx, wy, ww, wh = x + 8, y + 8, w - 16, h - 16
    a.rect(wx, wy, ww, wh, GLASS_FACTORY)
    # Crittall grid pattern (4x3 panes)
    for gy in range(wy, wy + wh, 24):
        a.rect(wx, gy, ww, 2, CRITTALL_STEEL)
    for gx in range(wx, wx + ww, 36):
        a.rect(gx, wy, 2, wh, CRITTALL_STEEL)
    a.noise(x, y, w, h, 0.025)

    # 4. Upper Loft Loading Doors & Crane Beam (R_LOFT_DOORS)
    x, y, w, h = R_LOFT_DOORS
    a.rect(x, y, w, h, STONE_GREY)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, TIMBER_OAK)
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.15, 0.10, 0.05))  # central split
    # Iron Z-bracing & strap hinges
    for hy in [dy + 12, dy + dh - 16]:
        a.rect(dx + 4, hy, dw - 8, 4, CRITTALL_STEEL)
    a.noise(x, y, w, h, 0.03)

    # 5. Corrugated Factory Roof (R_ROOF_CORRUG)
    x, y, w, h = R_ROOF_CORRUG
    a.rect(x, y, w, h, ROOF_STEEL)
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.045)

    # 6. Stone Coping (R_STONE_COPING)
    x, y, w, h = R_STONE_COPING
    a.rect(x, y, w, h, STONE_GREY)
    for cy in range(y, y + h, 20):
        a.rect(x, cy, w, 2, (0.45, 0.42, 0.38))
    a.noise(x, y, w, h, 0.03)

    # 7. Painted Brick Sign: "THAMES WHARF WORKS" (R_FACTORY_SIGN)
    x, y, w, h = R_FACTORY_SIGN
    a.bricks(x, y, w, h, brick=BRICK_INDUSTRIAL, mortar=BRICK_MORTAR, bw=24, bh=10)
    # Faded white painted letter banner
    a.rect(x + 6, y + 16, w - 12, h - 32, (0.22, 0.20, 0.18))
    s1 = "THAMES WHARF"
    w1 = a.text_width(s1, scale=1)
    a.text(x + (w - w1) // 2, y + h - 22, s1, (0.85, 0.85, 0.85), scale=1)
    s2 = "ENGINEERING"
    w2 = a.text_width(s2, scale=1)
    a.text(x + (w - w2) // 2, y + 36, s2, (0.85, 0.85, 0.85), scale=1)
    a.noise(x, y, w, h, 0.03)

    # 8. Vent Stack Pipe (R_VENT_STACK)
    x, y, w, h = R_VENT_STACK
    a.rect(x, y, w, h, (0.45, 0.48, 0.50))
    for vy in range(y, y + h, 16):
        a.rect(x, vy, w, 3, (0.28, 0.30, 0.32))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_industrial_warehouse_atlas", OUT_DIR)


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


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (-hw, 0.0, h), (hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front slope
        (2, 3, 4, 5),    # back slope
        (0, 4, 3),       # left gable
        (1, 2, 5),       # right gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_warehouse_atlas()
    mat = material_for(img, "mat_industrial_warehouse")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Victorian Industrial Brick Warehouse (11.0m x 8.5m Footprint)
    # - 3 Storeys with Pitched Industrial Roof & Crane Hoist Jib Beam
    # - Large Ground Floor Roller Shutter Loading Bay with Hazard Striping
    # - 2nd Floor Timber Loft Loading Doors
    # - Multi-pane Crittall Steel Factory Windows
    # - Rooftop Exhaust Flue Stacks & Painted Thames Wharf Sign
    # =========================================================================

    # 1. Concrete Loading Apron & Plinth (11.0m x 9.0m, Z = 0.00 to 0.15m)
    register_box("DockPlinth", 11.0, 9.00, 0.15, (0.0, -0.25, 0.0),
                 front=R_STONE_COPING, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 2. Main Factory Body (11.0m x 8.0m, Z: 0.15 to 7.00m, H: 6.85m)
    register_box("FactoryBody", 11.0, 8.00, 6.85, (0.0, 0.25, 0.15),
                 front=R_BRICK_FACTORY, sides=R_BRICK_FACTORY, back=R_BRICK_FACTORY)

    # 3. Ground Floor Roller Shutter Loading Bay (Left: X = -2.60m, Z = 0.15 to 3.80m, H: 3.65m)
    register_box("LoadingShutter", 4.40, 0.25, 3.65, (-2.60, -3.85, 0.15),
                 front=R_ROLLER_DOOR, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 4. Flanking Crittall Windows on Ground Floor (Right: X = 2.60m, Z = 1.00m to 3.20m)
    register_box("GroundWinRight", 3.80, 0.15, 2.20, (2.60, -3.80, 1.00),
                 front=R_CRITTALL_WIN, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 5. 1st Floor Crittall Windows (Left X = -2.80m, Right X = 2.80m, Z = 4.20m to 6.20m)
    register_box("Win1Left", 3.80, 0.15, 2.00, (-2.80, -3.80, 4.20),
                 front=R_CRITTALL_WIN, sides=R_STONE_COPING, top=R_STONE_COPING)
    register_box("Win1Right", 3.80, 0.15, 2.00, (2.80, -3.80, 4.20),
                 front=R_CRITTALL_WIN, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 6. Central Painted Wharf Sign on 1st Floor (Z = 4.30m to 5.90m)
    register_box("WharfSign", 1.80, 0.18, 1.60, (0.0, -3.82, 4.30),
                 front=R_FACTORY_SIGN, sides=R_STONE_COPING, top=R_STONE_COPING)

    # 7. Pitched Corrugated Steel Roof (Ridge along X, W: 11.40m, D: 8.40m, H: 2.20m at Z = 7.00m)
    roof = make_pitched_roof("FactoryRoof", 11.40, 8.40, 2.20, at=(0.0, 0.25, 7.00))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_CORRUG, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_BRICK_FACTORY, S, only=lambda f: abs(f.normal.x) > 0.6)
    kit.map_faces_to_region(roof, R_STONE_COPING, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    # 8. Projecting Crane Hoist Jib Beam & Pulley (Mounted at front gable apex: Z = 8.50m)
    register_box("CraneJibBeam", 0.35, 2.00, 0.35, (0.0, -4.60, 8.50),
                 front=R_STONE_COPING, sides=R_VENT_STACK, top=R_VENT_STACK)
    register_box("CraneHook", 0.15, 0.15, 0.80, (0.0, -5.30, 7.70),
                 front=R_VENT_STACK, sides=R_VENT_STACK, top=R_VENT_STACK)

    # 9. Rooftop Exhaust Vent Pipe Stacks (X = 3.60m, Y = 0.50m, Z = 7.00m to 9.60m)
    register_box("VentStack", 0.50, 0.50, 2.60, (3.60, 0.50, 7.00),
                 front=R_VENT_STACK, sides=R_VENT_STACK, top=R_VENT_STACK)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Industrial_Warehouse")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_industrial_warehouse_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_industrial_warehouse.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_industrial_warehouse.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_industrial_warehouse_preview.png")
        shutil.copy2(OUT_DIR / "building_industrial_warehouse_atlas.png", TOOLS_OUT_DIR / "building_industrial_warehouse_atlas.png")
    except Exception as e:
        print(f"[building_industrial_warehouse] note: {e}")

    print("[building_industrial_warehouse] generation complete.")


main()
