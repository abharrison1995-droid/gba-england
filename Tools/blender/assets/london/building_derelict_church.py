"""Derelict Gothic Parish Church (10.0m x 14.0m Modular Footprint).

Specs:
- 10.0m x 14.0m footprint, Height: 13.8m to belfry tower pinnacles.
- Weathered English ragstone & ashlar masonry walls with moss/lichen staining and stepped buttresses.
- Tower & Belfry on West corner with stone louvred belfry openings, crenellated battlements, and stone corner pinnacles.
- Steeply pitched weathered Welsh slate nave roof with iron ridge cresting and stone gable crosses.
- Pointed Gothic arch windows with stone tracery (some broken/boarded with timber), arched oak double entrance doors with iron strapwork.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_derelict_church.py
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
R_STONE_WALL    = (0,   256, 256, 256)   # Weathered ragstone ashlar with moss & lichen
R_SLATE_ROOF    = (0,   128, 256, 128)   # Welsh slate church roof with moss patches
R_GOTHIC_WIN    = (256, 256, 128, 256)   # Pointed Gothic arch window with stone tracery
R_BELFRY_LOUVRE = (256, 128, 128, 128)   # Stone belfry louvres & slit windows
R_STONE_TRIM    = (0,   64,  256, 64)    # Dressed stone quoins, coping, buttress caps
R_OAK_DOOR      = (256, 64,  128, 64)    # Arched heavy oak doors with iron strap hinges
R_MOSS_PLINTH   = (384, 384, 128, 128)   # Dark damp mossy plinth stone
R_ROSE_WINDOW   = (384, 256, 128, 128)   # Circular stone rose tracery window

# --- Colors ---
STONE_BASE      = (0.58, 0.56, 0.52)
STONE_MORTAR    = (0.44, 0.42, 0.38)
STONE_DAMP      = (0.36, 0.34, 0.30)
SLATE_GREY      = (0.30, 0.32, 0.36)
MOSS_GREEN      = (0.28, 0.38, 0.22)
OAK_DARK        = (0.32, 0.22, 0.14)
IRON_BLACK      = (0.12, 0.12, 0.13)
GLASS_LEADED    = (0.18, 0.24, 0.26)
STONE_CREAM     = (0.76, 0.73, 0.67)


def paint_church_atlas():
    a = Atlas(S, seed=1501)

    # 1. Weathered Stone Wall (R_STONE_WALL)
    x, y, w, h = R_STONE_WALL
    a.bricks(x, y, w, h, brick=STONE_BASE, mortar=STONE_MORTAR, bw=32, bh=14, jitter=0.07)
    # Moss & water runoff stains
    for mx in range(x + 10, x + w - 10, 36):
        m_len = a.rng.randint(20, 90)
        a.rect(mx, y, a.rng.randint(6, 16), m_len, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 2. Slate Roof with Moss (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, SLATE_GREY)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.20, 0.22, 0.25))
    # Moss patches
    a.disc(x + 50, y + 40, 20, MOSS_GREEN)
    a.disc(x + 180, y + 70, 24, MOSS_GREEN)
    a.noise(x, y, w, h, 0.035)

    # 3. Gothic Arch Window with Tracery (R_GOTHIC_WIN)
    x, y, w, h = R_GOTHIC_WIN
    a.rect(x, y, w, h, STONE_BASE)
    # Arched stone moulding surround
    wx, wy, ww, wh = x + 12, y + 12, w - 24, h - 24
    a.rect(wx, wy, ww, wh, GLASS_LEADED)
    # Stone central mullion & arch tracery
    a.rect(wx + ww // 2 - 2, wy, 4, wh - 30, STONE_CREAM)
    # Pointed arch top
    for ay in range(wy + wh - 40, wy + wh):
        frac = (ay - (wy + wh - 40)) / 40.0
        inset = int(frac * (ww // 2))
        a.rect(wx, ay, inset, 1, STONE_BASE)
        a.rect(wx + ww - inset, ay, inset, 1, STONE_BASE)
    # Leaded diamond glazing pattern
    for ly in range(wy + 8, wy + wh - 40, 16):
        a.rect(wx + 4, ly, ww - 8, 2, (0.10, 0.12, 0.14))
    # Weathered timber board patch over bottom
    a.rect(wx + 6, wy + 6, ww - 12, 40, (0.42, 0.30, 0.18))
    a.noise(x, y, w, h, 0.03)

    # 4. Belfry Louvres & Slits (R_BELFRY_LOUVRE)
    x, y, w, h = R_BELFRY_LOUVRE
    a.rect(x, y, w, h, STONE_BASE)
    lx, ly, lw, lh = x + 16, y + 16, w - 32, h - 32
    a.rect(lx, ly, lw, lh, STONE_DAMP)
    for sy in range(ly + 8, ly + lh - 8, 12):
        a.rect(lx + 4, sy, lw - 8, 4, (0.18, 0.17, 0.16))
        a.rect(lx + 4, sy + 3, lw - 8, 2, STONE_CREAM)
    a.noise(x, y, w, h, 0.03)

    # 5. Dressed Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for qy in range(y, y + h, 24):
        a.rect(x, qy, w, 2, STONE_MORTAR)
    a.noise(x, y, w, h, 0.03)

    # 6. Oak Entrance Doors with Iron Strapwork (R_OAK_DOOR)
    x, y, w, h = R_OAK_DOOR
    a.rect(x, y, w, h, OAK_DARK)
    # Timber plank vertical lines
    for px in range(x + 10, x + w - 10, 16):
        a.rect(px, y, 2, h, (0.18, 0.12, 0.08))
    # Ornate Gothic iron hinge straps
    for hy in [y + 16, y + h // 2, y + h - 20]:
        a.rect(x + 8, hy, w - 16, 5, IRON_BLACK)
        a.disc(x + 16, hy + 2, 4, IRON_BLACK)
        a.disc(x + w - 16, hy + 2, 4, IRON_BLACK)
    a.noise(x, y, w, h, 0.03)

    # 7. Moss Plinth (R_MOSS_PLINTH)
    x, y, w, h = R_MOSS_PLINTH
    a.rect(x, y, w, h, STONE_DAMP)
    a.rect(x, y + 10, w, h - 20, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 8. Rose Window (R_ROSE_WINDOW)
    x, y, w, h = R_ROSE_WINDOW
    a.rect(x, y, w, h, STONE_BASE)
    rcx, rcy, rr = x + w // 2, y + h // 2, 48
    a.disc(rcx, rcy, rr, STONE_CREAM)
    a.disc(rcx, rcy, rr - 6, GLASS_LEADED)
    a.disc(rcx, rcy, 12, STONE_CREAM)
    for angle_deg in range(0, 360, 45):
        rad = math.radians(angle_deg)
        ex = int(rcx + (rr - 8) * math.cos(rad))
        ey = int(rcy + (rr - 8) * math.sin(rad))
        a.rect(min(rcx, ex), min(rcy, ey), max(3, abs(ex - rcx)), max(3, abs(ey - rcy)), STONE_CREAM)
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_derelict_church_atlas", OUT_DIR)


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


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    hw, hd = w / 2.0, d / 2.0
    z = at[2]
    b0 = (-hw + at[0], -hd + at[1], z)
    b1 = (hw + at[0],  -hd + at[1], z)
    b2 = (hw + at[0],   hd + at[1], z)
    b3 = (-hw + at[0],  hd + at[1], z)
    r0 = (at[0], -hd + at[1], z + h)
    r1 = (at[0],  hd + at[1], z + h)

    v_b0 = bm.verts.new(b0)
    v_b1 = bm.verts.new(b1)
    v_b2 = bm.verts.new(b2)
    v_b3 = bm.verts.new(b3)
    v_r0 = bm.verts.new(r0)
    v_r1 = bm.verts.new(r1)

    bm.faces.new([v_b0, v_b1, v_b2, v_b3])  # bottom
    bm.faces.new([v_b0, v_r0, v_r1, v_b3])  # left slope
    bm.faces.new([v_b1, v_b2, v_r1, v_r0])  # right slope
    bm.faces.new([v_b0, v_b1, v_r0])        # front gable
    bm.faces.new([v_b3, v_r1, v_b2])        # back gable

    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    img = paint_church_atlas()
    mat = material_for(img, "mat_derelict_church")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Derelict Gothic Church (10.0m x 14.0m Footprint)
    # - Nave: 6.8m width x 13.0m depth, Walls H: 6.2m, Pitched Roof H: 4.2m (Total H: 10.4m)
    # - Bell Tower (Front-Left, X = -3.2m, Y = -4.5m): 3.6m x 3.6m, H: 13.5m
    # - Buttresses, Pointed Tracery Windows, Porch & Gothic Double Doors
    # =========================================================================

    # 1. Ground Plinth (10.0m x 14.0m)
    register_box("ChurchPlinth", 10.0, 14.0, 0.20, (0.0, 0.0, 0.0),
                 front=R_MOSS_PLINTH, sides=R_MOSS_PLINTH, top=R_STONE_TRIM)

    # 2. Main Nave Hall Body (6.8m x 12.5m, Z: 0.20 to 6.20m, H: 6.0m)
    register_box("NaveBody", 6.80, 12.50, 6.00, (1.20, 0.25, 0.20),
                 front=R_STONE_WALL, sides=R_STONE_WALL, back=R_STONE_WALL)

    # 3. Steeply Pitched Nave Slate Roof (Ridge running North-South along Y, H: 4.0m, Z: 6.20m)
    roof = make_pitched_roof("NaveRoof", 7.20, 12.70, 4.00, at=(1.20, 0.25, 6.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: f.normal.z > 0.1 and abs(f.normal.y) < 0.5)
    kit.map_faces_to_region(roof, R_STONE_WALL, S, only=lambda f: abs(f.normal.y) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    # 4. Bell Tower & Belfry (Front-Left: X = -3.20m, Y = -4.20m, 3.6m x 3.6m, Z: 0.20 to 12.50m)
    register_box("BellTowerLower", 3.60, 3.60, 8.00, (-3.20, -4.20, 0.20),
                 front=R_STONE_WALL, sides=R_STONE_WALL, back=R_STONE_WALL)
    register_box("BellTowerBelfry", 3.40, 3.40, 4.30, (-3.20, -4.20, 8.20),
                 front=R_BELFRY_LOUVRE, sides=R_BELFRY_LOUVRE, back=R_BELFRY_LOUVRE)

    # Tower Parapet & 4 Corner Stone Pinnacles (Z = 12.50m to 13.80m)
    register_box("TowerParapet", 3.70, 3.70, 0.50, (-3.20, -4.20, 12.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    for px, py in [(-4.70, -5.70), (-1.70, -5.70), (-4.70, -2.70), (-1.70, -2.70)]:
        register_box(f"Pinnacle_{px}_{py}", 0.45, 0.45, 0.85, (px, py, 12.80),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Stepped Stone Buttresses along Nave Side (Right wall X = 4.60m at Y = -4.0, -1.0, +2.0, +5.0)
    for by in [-4.0, -1.0, 2.0, 5.0]:
        register_box(f"Buttress_{by}", 0.50, 0.80, 5.20, (4.85, by, 0.20),
                     front=R_STONE_TRIM, sides=R_STONE_WALL, top=R_STONE_TRIM)

    # 6. Gothic Arched Tracery Windows along Right Nave Wall
    for wy in [-2.5, 0.5, 3.5]:
        register_box(f"GothicWin_{wy}", 0.18, 1.40, 3.20, (4.65, wy, 1.80),
                     front=R_STONE_TRIM, sides=R_GOTHIC_WIN, top=R_STONE_TRIM)

    # 7. Front Gothic Entrance Porch & Rose Window (Front gable at Y = -6.0m)
    register_box("FrontPorch", 2.60, 1.80, 3.40, (1.80, -6.40, 0.20),
                 front=R_STONE_WALL, sides=R_STONE_WALL, top=R_STONE_TRIM)
    porch_roof = make_pitched_roof("PorchRoof", 2.80, 2.00, 1.20, at=(1.80, -6.40, 3.60))
    porch_roof.data.materials.append(mat)
    kit.map_faces_to_region(porch_roof, R_SLATE_ROOF, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(porch_roof, R_STONE_WALL, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z < 0.1)
    kit.map_faces_to_region(porch_roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(porch_roof)

    # Arched Oak Double Doors on Porch Front (Y = -7.32m)
    register_box("ChurchDoors", 1.80, 0.15, 2.60, (1.80, -7.32, 0.25),
                 front=R_OAK_DOOR, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # Circular Rose Window on Front Nave Gable (Z = 6.40m)
    register_box("RoseWindow", 1.60, 0.15, 1.60, (1.80, -6.05, 6.40),
                 front=R_ROSE_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    shell = kit.join(parts, "Building_Derelict_Church")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_derelict_church_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_derelict_church.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_derelict_church.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_derelict_church_preview.png")
        shutil.copy2(OUT_DIR / "building_derelict_church_atlas.png", TOOLS_OUT_DIR / "building_derelict_church_atlas.png")
    except Exception as e:
        print(f"[building_derelict_church] note: {e}")

    print("[building_derelict_church] generation complete.")


main()
