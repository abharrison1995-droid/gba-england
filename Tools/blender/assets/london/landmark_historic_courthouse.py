"""Historic London Courthouse / Town Hall (Neoclassical Portland Stone Landmark).

Specs:
- 12.0m x 9.0m footprint, Height: 13.0m to copper dome finial.
- Grand Neoclassical London civic courthouse / town hall:
  - Dressed Portland stone ashlar with rusticated ground floor base.
  - Grand hexastyle entrance portico with 6 Corinthian fluted stone columns.
  - Triangular classical pediment carved with Royal Coat of Arms & Latin motto.
  - Grand ceremonial stone steps with bronze handrails.
  - Arched double oak courthouse doors with heavy bronze studs and fanlight.
  - Multi-pane sash windows with triangular & segmental stone pediments.
  - Rooftop central oxidized green copper dome cupola with bronze Lady Justice finial.
  - Classical stone balustrade parapet along roof perimeter.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_historic_courthouse.py
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
R_PORTLAND_WALL = (0,   256, 256, 256)   # Dressed Portland stone with classical windows & pediments
R_PEDIMENT_RELIEF=(256, 256, 256, 256)   # Triangular pediment tympanum with Royal Coat of Arms
R_COLUMN_FLUTE  = (0,   128, 256, 128)   # Fluted Corinthian columns with acanthus capitals
R_COPPER_DOME   = (256, 128, 128, 128)   # Oxidized green copper cupola dome & bronze Justice statue
R_COURT_DOORS   = (384, 128, 128, 128)   # Arched double oak courthouse doors with bronze studs
R_STONE_STEPS   = (0,   0,   256, 128)   # Portland stone ceremonial steps & balustrade
R_COURT_SIGN    = (256, 0,   128, 128)   # Gold engraved "ROYAL COURTS OF JUSTICE" plaque
R_ROOF_LEAD     = (384, 0,   128, 128)   # Lead flat roof deck with balustrades

# --- Palette Colors ---
STONE_PORTLAND  = (0.84, 0.82, 0.78)
STONE_SHADOW    = (0.64, 0.62, 0.58)
STONE_MORTAR    = (0.55, 0.52, 0.48)
GOLD_GILT       = (0.92, 0.78, 0.24)
COPPER_VERDIG   = (0.34, 0.58, 0.52)
COPPER_DARK     = (0.22, 0.40, 0.36)
OAK_DARK        = (0.24, 0.16, 0.10)
BRONZE_TRIM     = (0.38, 0.32, 0.26)
GLASS_PANE      = (0.22, 0.30, 0.36)


def paint_courthouse_atlas():
    a = Atlas(S, seed=2901)

    # 1. Portland Stone with Windows & Pediments (R_PORTLAND_WALL)
    x, y, w, h = R_PORTLAND_WALL
    a.bricks(x, y, w, h, brick=STONE_PORTLAND, mortar=STONE_MORTAR, bw=36, bh=14, jitter=0.04)
    # Rustication grooves on lower half
    for ry in range(y, y + 120, 24):
        a.rect(x, ry, w, 3, STONE_SHADOW)
    # Classical pedimented sash windows (2 storeys)
    for wy in [y + 20, y + 140]:
        for wx in [x + 20, x + 100, x + 180]:
            a.rect(wx, wy, 56, 76, STONE_PORTLAND)
            # Triangular pediment cap on upper windows
            if wy > y + 100:
                a.rect(wx, wy + 76, 56, 12, STONE_SHADOW)
                a.disc(wx + 28, wy + 82, 10, GOLD_GILT)
            a.rect(wx + 6, wy + 6, 44, 64, GLASS_PANE)
            # White sash glazing bars
            a.rect(wx + 26, wy + 6, 4, 64, STONE_PORTLAND)
            a.rect(wx + 6, wy + 36, 44, 4, STONE_PORTLAND)
    a.noise(x, y, w, h, 0.025)

    # 2. Triangular Pediment Relief (R_PEDIMENT_RELIEF)
    x, y, w, h = R_PEDIMENT_RELIEF
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Heavy stone moulding frame
    a.rect(x + 8, y + 8, w - 16, h - 16, STONE_SHADOW)
    a.rect(x + 16, y + 16, w - 32, h - 32, STONE_PORTLAND)
    # Royal Coat of Arms carved in high relief (Lion, Unicorn, Crown)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, GOLD_GILT)
    a.disc(cx, cy, 36, STONE_PORTLAND)
    a.disc(cx, cy, 18, GOLD_GILT)
    # Motto banner at base
    s_motto = "DIEU ET MON DROIT"
    mw = a.text_width(s_motto, scale=1)
    a.rect(cx - mw // 2 - 8, cy - 40, mw + 16, 16, STONE_SHADOW)
    a.text(cx - mw // 2, cy - 28, s_motto, GOLD_GILT, scale=1)
    a.noise(x, y, w, h, 0.025)

    # 3. Fluted Corinthian Columns (R_COLUMN_FLUTE)
    x, y, w, h = R_COLUMN_FLUTE
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Acanthus capital
    a.rect(x, y + h - 24, w, 24, STONE_SHADOW)
    for kx in range(x + 4, x + w, 16):
        a.disc(kx, y + h - 12, 8, GOLD_GILT)
    # Vertical flutes
    for fx in range(x, x + w, 14):
        a.rect(fx, y, 4, h - 26, STONE_SHADOW)
        a.rect(fx + 4, y, 2, h - 26, (0.92, 0.90, 0.86))
    a.noise(x, y, w, h, 0.02)

    # 4. Copper Dome Cupola (R_COPPER_DOME)
    x, y, w, h = R_COPPER_DOME
    a.rect(x, y, w, h, COPPER_VERDIG)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, COPPER_DARK)
        a.rect(x, ry + 2, w, 1, (0.42, 0.68, 0.60))
    for rx in range(x, x + w, 24):
        a.rect(rx, y, 2, h, COPPER_DARK)
    # Bronze Lady Justice silhouette
    a.disc(x + w // 2, y + h - 24, 16, GOLD_GILT)
    a.noise(x, y, w, h, 0.03)

    # 5. Arched Courthouse Doors (R_COURT_DOORS)
    x, y, w, h = R_COURT_DOORS
    a.rect(x, y, w, h, STONE_PORTLAND)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, OAK_DARK)
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.10, 0.06, 0.04))
    # Bronze studs & kickplates
    a.rect(dx + 4, dy + 4, dw - 8, 24, BRONZE_TRIM)
    for sy in range(dy + 36, dy + dh - 16, 24):
        for sx in [dx + 16, dx + dw // 2 - 16, dx + dw // 2 + 16, dx + dw - 16]:
            a.disc(sx, sy, 4, GOLD_GILT)
    a.noise(x, y, w, h, 0.025)

    # 6. Stone Steps & Balustrade (R_STONE_STEPS)
    x, y, w, h = R_STONE_STEPS
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Baluster vase bottle shapes
    for bx in range(x + 12, x + w - 12, 24):
        a.rect(bx, y + 8, 12, h - 16, STONE_SHADOW)
        a.rect(bx + 2, y + 10, 8, h - 20, STONE_PORTLAND)
    a.noise(x, y, w, h, 0.03)

    # 7. Court Sign (R_COURT_SIGN)
    x, y, w, h = R_COURT_SIGN
    a.rect(x, y, w, h, (0.14, 0.16, 0.18))
    a.rect(x + 4, y + 4, w - 8, h - 8, BRONZE_TRIM)
    s1 = "ROYAL COURTS OF JUSTICE"
    w1 = a.text_width(s1, scale=1)
    a.text(x + (w - w1) // 2, y + h // 2 + 6, s1, GOLD_GILT, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 8. Lead Roof (R_ROOF_LEAD)
    x, y, w, h = R_ROOF_LEAD
    a.rect(x, y, w, h, (0.32, 0.34, 0.36))
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_historic_courthouse_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_STEPS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_STEPS, S, only=side("bottom"))


def make_pediment_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (0.0, -hd, h), (0.0, hd, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 4),       # front triangular tympanum
        (1, 2, 5, 4),    # right slope
        (2, 3, 5),       # back triangular tympanum
        (3, 0, 4, 5),    # left slope
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_courthouse_atlas()
    mat = material_for(img, "mat_historic_courthouse")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Historic London Courthouse / Town Hall (12.0m x 9.0m Footprint, Height: 13.0m)
    # - Grand Ceremonial Stone Staircase Plinth (Z: 0.0 to 1.2m)
    # - Main Neoclassical Building Body: 12.0m x 8.0m, 2 Storeys (Z: 1.2m to 8.2m)
    # - Grand Hexastyle Portico: 6 Corinthian Columns + Triangular Pediment (H: 9.8m)
    # - Arched Double Oak Courthouse Doors + Fanlight
    # - Rooftop Central Copper Dome Cupola with Lady Justice Finial (Z: 8.2m to 13.2m)
    # =========================================================================

    # 1. Grand Ceremonial Stone Steps Plinth (12.4m x 9.6m, Z = 0.00 to 1.20m, 4 stepped terraces)
    register_box("StepsTier1", 12.40, 9.60, 0.30, (0.0, -0.40, 0.0),
                 front=R_STONE_STEPS, sides=R_STONE_STEPS, top=R_STONE_STEPS)
    register_box("StepsTier2", 12.00, 9.20, 0.30, (0.0, -0.20, 0.30),
                 front=R_STONE_STEPS, sides=R_STONE_STEPS, top=R_STONE_STEPS)
    register_box("StepsTier3", 11.60, 8.80, 0.30, (0.0, 0.0, 0.60),
                 front=R_STONE_STEPS, sides=R_STONE_STEPS, top=R_STONE_STEPS)
    register_box("StepsTier4", 11.20, 8.40, 0.30, (0.0, 0.20, 0.90),
                 front=R_STONE_STEPS, sides=R_STONE_STEPS, top=R_STONE_STEPS)

    # 2. Main Courthouse Body (12.0m x 7.6m, Z: 1.20m to 8.20m, H: 7.00m)
    register_box("CourtBody", 12.00, 7.60, 7.00, (0.0, 0.40, 1.20),
                 front=R_PORTLAND_WALL, sides=R_PORTLAND_WALL, back=R_PORTLAND_WALL)

    # 3. Arched Central Oak Doors (Z = 1.20m to 4.60m, H: 3.40m)
    register_box("CourtDoors", 2.60, 0.20, 3.40, (0.0, -3.42, 1.20),
                 front=R_COURT_DOORS, sides=R_STONE_STEPS, top=R_STONE_STEPS)

    # 4. Grand Hexastyle Portico: 6 Corinthian Columns (Front row at Y = -4.50m, Z = 1.20m to 6.80m)
    for col_x in [-3.60, -2.15, -0.70, 0.70, 2.15, 3.60]:
        register_box(f"PorticoCol_{col_x}", 0.65, 0.65, 5.60, (col_x, -4.50, 1.20),
                     front=R_COLUMN_FLUTE, sides=R_COLUMN_FLUTE, top=R_STONE_STEPS)

    # 5. Portico Entablature & Frieze (Width: 8.8m, D: 2.4m, Z: 6.80m to 7.80m)
    register_box("PorticoEntablature", 8.80, 2.40, 1.00, (0.0, -3.60, 6.80),
                 front=R_COURT_SIGN, sides=R_STONE_STEPS, top=R_STONE_STEPS)

    # 6. Triangular Classical Pediment with Royal Coat of Arms (W: 8.8m, D: 2.4m, H: 2.2m at Z = 7.80m)
    pediment = make_pediment_roof("PorticoPediment", 8.80, 2.40, 2.20, at=(0.0, -3.60, 7.80))
    pediment.data.materials.append(mat)
    kit.map_faces_to_region(pediment, R_PEDIMENT_RELIEF, S, only=lambda f: f.normal.y < -0.5)
    kit.map_faces_to_region(pediment, R_COPPER_DOME, S, only=lambda f: f.normal.z > 0.1 and f.normal.y > -0.5)
    kit.map_faces_to_region(pediment, R_STONE_STEPS, S, only=lambda f: f.normal.z < -0.5 or abs(f.normal.x) > 0.6)
    parts.append(pediment)

    # 7. Roof Parapet Balustrade (12.2m x 7.8m, Z = 8.20m to 9.00m, H: 0.80m)
    register_box("RoofBalustrade", 12.20, 7.80, 0.80, (0.0, 0.40, 8.20),
                 front=R_STONE_STEPS, sides=R_STONE_STEPS, back=R_STONE_STEPS, top=R_ROOF_LEAD)

    # 8. Rooftop Central Copper Dome Cupola (Z: 8.20m to 13.00m)
    # Drum base (4.0m x 4.0m x 1.8m)
    register_box("DomeDrum", 4.00, 4.00, 1.80, (0.0, 0.40, 8.20),
                 front=R_PORTLAND_WALL, sides=R_PORTLAND_WALL, top=R_COPPER_DOME)
    # Copper Dome (3.4m x 3.4m x 1.8m)
    register_box("CopperDome", 3.40, 3.40, 1.80, (0.0, 0.40, 10.00),
                 front=R_COPPER_DOME, sides=R_COPPER_DOME, top=R_COPPER_DOME)
    # Lady Justice Spire Finial (Z = 11.80m to 13.20m)
    register_box("JusticeFinial", 0.30, 0.30, 1.40, (0.0, 0.40, 11.80),
                 front=R_COPPER_DOME, sides=R_COPPER_DOME, top=R_COPPER_DOME)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_Historic_Courthouse")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_historic_courthouse_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_historic_courthouse.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_historic_courthouse.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_historic_courthouse_preview.png")
        shutil.copy2(OUT_DIR / "landmark_historic_courthouse_atlas.png", TOOLS_OUT_DIR / "landmark_historic_courthouse_atlas.png")
    except Exception as e:
        print(f"[landmark_historic_courthouse] note: {e}")

    print("[landmark_historic_courthouse] generation complete.")


main()
