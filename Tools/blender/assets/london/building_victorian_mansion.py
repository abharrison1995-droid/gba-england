"""Grand Victorian London Manor / Mansion (12.0m x 9.0m Modular Footprint).

Specs:
- 12.0m x 9.0m footprint, Height: 11.8m to chimney tops.
- 3 Storeys + Mansard Attic: Classic London red brick with dressed stone corner quoins, stringer cornices, and window architraves.
- Left side: 3-storey faceted canted bay window tower with lead cap.
- Center/Right: Grand classical stone entrance portico with twin pillars, stone balustrade, and panelled oak double doors with fanlight.
- Mansard slate roof with 3 ornate pedimented dormer windows and 2 grand chimney stacks with 6 terracotta pots.
- Outputs to Tools/blender/out/Background Assets/ and Tools/out/Background Assets/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_victorian_mansion.py
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
R_BRICK_MANOR   = (0,   256, 256, 256)   # Deep red brick with stone quoins & string courses
R_SLATE_MANSARD = (0,   128, 256, 128)   # Welsh slate mansard tiles
R_STONE_PORTICO = (256, 256, 128, 256)   # Grand classical stone portico & balustrade
R_SASH_GRAND    = (256, 128, 128, 128)   # Grand 2-over-2 sash window with pediment
R_STONE_TRIM    = (0,   64,  256, 64)    # Dressed stone cornice & quoins
R_DOOR_MANOR    = (256, 64,  128, 64)    # Panelled dark oak double doors + fanlight
R_DORMER_WIN    = (384, 384, 128, 128)   # Mansard dormer window with stone pediment
R_CHIMNEY_POT   = (384, 256, 128, 128)   # Terracotta chimney pot & lead roof cap

# --- Colors ---
BRICK_RED       = (0.58, 0.22, 0.16)
BRICK_MORTAR    = (0.72, 0.70, 0.66)
STONE_CREAM     = (0.84, 0.81, 0.74)
STONE_SHADE     = (0.60, 0.57, 0.50)
SLATE_GREY      = (0.28, 0.30, 0.34)
OAK_DARK        = (0.28, 0.18, 0.12)
GLASS_DARK      = (0.18, 0.22, 0.26)
WHITE_SASH      = (0.94, 0.94, 0.92)
POT_TERRACOTTA  = (0.68, 0.32, 0.16)


def paint_mansion_atlas():
    a = Atlas(S, seed=1601)

    # 1. Manor Brick with Quoins (R_BRICK_MANOR)
    x, y, w, h = R_BRICK_MANOR
    a.bricks(x, y, w, h, brick=BRICK_RED, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.07)
    # Alternating stone corner quoins on left edge
    for qy in range(y, y + h, 20):
        qw = 28 if (qy // 20) % 2 == 0 else 18
        a.rect(x, qy, qw, 18, STONE_CREAM)
        a.rect(x, qy, qw, 2, STONE_SHADE)
    # Horizontal stone string course
    for sy in [y + 80, y + 160]:
        a.rect(x, sy, w, 8, STONE_CREAM)
        a.rect(x, sy + 8, w, 2, STONE_SHADE)
    a.noise(x, y, w, h, 0.035)

    # 2. Slate Mansard Roof (R_SLATE_MANSARD)
    x, y, w, h = R_SLATE_MANSARD
    a.rect(x, y, w, h, SLATE_GREY)
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.18, 0.20, 0.23))
    a.noise(x, y, w, h, 0.035)

    # 3. Classical Stone Portico & Balustrade (R_STONE_PORTICO)
    x, y, w, h = R_STONE_PORTICO
    a.rect(x, y, w, h, STONE_CREAM)
    # Balusters pattern
    for bx in range(x + 12, x + w - 12, 16):
        a.rect(bx, y + 10, 8, h - 30, STONE_SHADE)
        a.rect(bx + 2, y + 14, 4, h - 38, STONE_CREAM)
    # Pediment top cornice
    a.rect(x, y + h - 16, w, 16, (0.88, 0.85, 0.78))
    a.noise(x, y, w, h, 0.025)

    # 4. Grand Sash Window with Triangular Pediment (R_SASH_GRAND)
    x, y, w, h = R_SASH_GRAND
    a.rect(x, y, w, h, STONE_CREAM)
    # Window opening
    wx, wy, ww, wh = x + 16, y + 14, w - 32, h - 36
    a.rect(wx, wy, ww, wh, GLASS_DARK)
    # White 2-over-2 sash frame
    a.rect(wx + 2, wy + 2, ww - 4, wh - 4, GLASS_DARK)
    a.rect(wx + ww // 2 - 2, wy, 4, wh, WHITE_SASH)
    a.rect(wx, wy + wh // 2 - 2, ww, 4, WHITE_SASH)
    # Triangular pediment on top
    a.rect(x + 8, y + h - 18, w - 16, 12, STONE_CREAM)
    a.noise(x, y, w, h, 0.025)

    # 5. Stone Trim & Cornice (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for dy in range(y + 12, y + h - 12, 16):
        a.rect(x, dy, w, 4, STONE_SHADE)
    a.noise(x, y, w, h, 0.03)

    # 6. Grand Oak Double Doors + Fanlight (R_DOOR_MANOR)
    x, y, w, h = R_DOOR_MANOR
    a.rect(x, y, w, h, STONE_CREAM)
    # Semicircular fanlight on top
    a.rect(x + 12, y + h - 32, w - 24, 24, GLASS_DARK)
    for fx in range(x + 20, x + w - 20, 14):
        a.rect(fx, y + h - 32, 2, 24, WHITE_SASH)
    # Oak doors
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 44
    a.rect(dx, dy, dw, dh, OAK_DARK)
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.16, 0.10, 0.06))
    # Brass door knockers & knobs
    a.disc(dx + 12, dy + dh // 2, 4, (0.85, 0.72, 0.22))
    a.disc(dx + dw - 12, dy + dh // 2, 4, (0.85, 0.72, 0.22))
    a.noise(x, y, w, h, 0.025)

    # 7. Mansard Dormer Window (R_DORMER_WIN)
    x, y, w, h = R_DORMER_WIN
    a.rect(x, y, w, h, STONE_CREAM)
    a.rect(x + 14, y + 12, w - 28, h - 32, GLASS_DARK)
    a.rect(x + w // 2 - 2, y + 12, 4, h - 32, WHITE_SASH)
    a.rect(x + 14, y + (h - 32) // 2 + 12, w - 28, 4, WHITE_SASH)
    a.noise(x, y, w, h, 0.025)

    # 8. Chimney Pot & Lead Cap (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, (0.42, 0.44, 0.46))
    a.rect(x + 16, y + 16, w - 32, h - 32, POT_TERRACOTTA)
    a.rect(x + 12, y + h - 28, w - 24, 10, (0.78, 0.38, 0.20))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_victorian_mansion_atlas", OUT_DIR)


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


def make_canted_bay(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    hw, d_proj = w / 2.0, d
    chamfer = hw * 0.40
    z_bot, z_top = at[2], at[2] + h
    x_c, y_c = at[0], at[1]

    b0 = (-hw + x_c, y_c, z_bot)
    b1 = (-hw + chamfer + x_c, y_c - d_proj, z_bot)
    b2 = (hw - chamfer + x_c,  y_c - d_proj, z_bot)
    b3 = (hw + x_c, y_c, z_bot)

    t0 = (-hw + x_c, y_c, z_top)
    t1 = (-hw + chamfer + x_c, y_c - d_proj, z_top)
    t2 = (hw - chamfer + x_c,  y_c - d_proj, z_top)
    t3 = (hw + x_c, y_c, z_top)

    vb0, vb1, vb2, vb3 = bm.verts.new(b0), bm.verts.new(b1), bm.verts.new(b2), bm.verts.new(b3)
    vt0, vt1, vt2, vt3 = bm.verts.new(t0), bm.verts.new(t1), bm.verts.new(t2), bm.verts.new(t3)

    bm.faces.new([vb0, vb1, vb2, vb3])
    bm.faces.new([vt3, vt2, vt1, vt0])
    bm.faces.new([vb0, vt0, vt1, vb1])
    bm.faces.new([vb1, vt1, vt2, vb2])
    bm.faces.new([vb2, vt2, vt3, vb3])

    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    img = paint_mansion_atlas()
    mat = material_for(img, "mat_victorian_mansion")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Grand Victorian London Mansion (12.0m x 9.0m Footprint)
    # - Main Body: 12.0m x 8.0m, 3 Storeys (Z: 0.15 to 8.20m, H: 8.05m)
    # - Mansard Attic Roof: 12.2m x 8.2m, H: 2.2m (Z: 8.20 to 10.40m)
    # - Left: 3-Storey Canted Bay Window Tower (Width 3.8m, Projects forward 0.9m)
    # - Center/Right: Grand Classical Stone Entrance Portico with Balustraded Terrace
    # - 3 Mansard Dormer Windows & 2 Chimney Stacks with 6 Terracotta Pots
    # =========================================================================

    # 1. Pavement & Terrace Plinth (12.0m x 9.0m, Z = 0.00 to 0.15m)
    register_box("MansionPlinth", 12.0, 9.0, 0.15, (0.0, -0.50, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Building Body (12.0m x 7.5m, Z: 0.15 to 8.20m, H: 8.05m)
    register_box("MainManorBody", 12.0, 7.50, 8.05, (0.0, 0.25, 0.15),
                 front=R_BRICK_MANOR, sides=R_BRICK_MANOR, back=R_BRICK_MANOR)

    # 3. Left 3-Storey Projecting Bay Tower (X = -3.60m, Width: 3.8m, Projects forward by 1.1m)
    register_box("BayTowerBody", 3.80, 1.10, 8.05, (-3.60, -3.80, 0.15),
                 front=R_BRICK_MANOR, sides=R_BRICK_MANOR, back=R_BRICK_MANOR)

    # 3 Individual Sash Windows on Bay Tower (Floors 1, 2, 3)
    for floor_idx, fz in enumerate([0.80, 3.40, 5.80]):
        register_box(f"BayWin_{floor_idx}", 2.20, 0.15, 1.80, (-3.60, -4.38, fz),
                     front=R_SASH_GRAND, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # Lead roof cap on bay tower
    register_box("BayCap", 4.00, 1.30, 0.25, (-3.60, -3.80, 8.20),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_SLATE_MANSARD)

    # 4. Classical Stone Entrance Portico (X = +1.80m, Y = -3.50 to -4.60m, Z: 0.15 to 3.80m)
    register_box("PorticoSteps", 3.40, 1.20, 0.25, (1.80, -4.10, 0.15),
                 front=R_STONE_PORTICO, sides=R_STONE_PORTICO, top=R_STONE_TRIM)
    # Twin stone portico columns (X = +0.50m and +3.10m at Y = -4.50m)
    register_box("PorticoColL", 0.40, 0.40, 3.20, (0.60, -4.50, 0.40),
                 front=R_STONE_PORTICO, sides=R_STONE_PORTICO, top=R_STONE_TRIM)
    register_box("PorticoColR", 0.40, 0.40, 3.20, (3.00, -4.50, 0.40),
                 front=R_STONE_PORTICO, sides=R_STONE_PORTICO, top=R_STONE_TRIM)
    # Portico entablature / pediment roof & stone balustrade (Z = 3.60m)
    register_box("PorticoBalustrade", 3.60, 1.40, 0.70, (1.80, -4.10, 3.60),
                 front=R_STONE_PORTICO, sides=R_STONE_PORTICO, top=R_STONE_TRIM)

    # Panelled Oak Entrance Double Doors + Fanlight (Y = -3.52m, Z = 0.40 to 3.20m)
    register_box("MansionDoor", 2.20, 0.15, 2.80, (1.80, -3.52, 0.40),
                 front=R_DOOR_MANOR, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Right Wing Sash Windows (Ground floor right X = 4.80m, and Floors 2 & 3: X = 0.8m, 2.8m, 4.8m)
    register_box("Win_Ground_R", 1.40, 0.15, 1.80, (4.80, -3.52, 0.80),
                 front=R_SASH_GRAND, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    for floor_idx, fz in enumerate([3.40, 5.80]):
        for wx in [0.80, 2.80, 4.80]:
            register_box(f"Win_{floor_idx}_{wx}", 1.40, 0.15, 1.80, (wx, -3.52, fz),
                         front=R_SASH_GRAND, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Modillion Eaves Cornice (Z = 8.20m)
    register_box("EavesCornice", 12.40, 7.90, 0.35, (0.0, 0.25, 8.20),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 7. Mansard Roof (12.2m x 7.7m, Z: 8.55 to 10.55m, H: 2.0m)
    register_box("MansardRoof", 12.20, 7.70, 2.00, (0.0, 0.25, 8.55),
                 front=R_SLATE_MANSARD, sides=R_SLATE_MANSARD, top=R_SLATE_MANSARD)

    # 8. 3 Pedimented Mansard Dormer Windows (Z = 8.90m at X = -3.20, 0.80, 4.20)
    for dx in [-3.20, 0.80, 4.20]:
        register_box(f"Dormer_{dx}", 1.40, 0.40, 1.50, (dx, -3.70, 8.90),
                     front=R_DORMER_WIN, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. 2 Grand Chimney Stacks with 6 Terracotta Pots (Left X = -5.0m, Right X = +5.0m)
    for cx in [-5.00, 5.00]:
        register_box(f"ChimneyStack_{cx}", 1.20, 1.80, 2.80, (cx, 0.25, 8.55),
                     front=R_BRICK_MANOR, sides=R_BRICK_MANOR, top=R_STONE_TRIM)
        for py in [-0.40, 0.0, 0.40]:
            register_box(f"Pot_{cx}_{py}", 0.30, 0.30, 0.65, (cx, 0.25 + py, 11.35),
                         front=R_CHIMNEY_POT, sides=R_CHIMNEY_POT, top=R_CHIMNEY_POT)

    shell = kit.join(parts, "Building_Victorian_Mansion")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_victorian_mansion_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_victorian_mansion.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_victorian_mansion.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_victorian_mansion_preview.png")
        shutil.copy2(OUT_DIR / "building_victorian_mansion_atlas.png", TOOLS_OUT_DIR / "building_victorian_mansion_atlas.png")
    except Exception as e:
        print(f"[building_victorian_mansion] note: {e}")

    print("[building_victorian_mansion] generation complete.")


main()
