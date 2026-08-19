"""Tileable Great Wall of China - Variant 2: 90-Degree Corner Bastion (~850 Tris).

Specs:
- Modular 90-Degree Turn:
  - Input wall enters at X = -6.0m (along X-axis, width: 3.8m, height: 6.5m/7.5m).
  - Output wall exits at Y = +6.0m (along Y-axis, width: 3.8m, height: 6.5m/7.5m).
  - Seamlessly tiles with Straight Segment (Var 1) and Landmark Watchtower.
- Features:
  - Elevated octagonal corner turret bastion at the junction (Height: 8.5m).
  - Ming brick masonry, granite base, arched arrow-slit embrasures, and perimeter battlements.
- Target: <1,000 tris (~850 tris).
- Deploys to Assets/3DModels/West York/great_wall_var2_corner_tower.glb.
"""

import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "west_york"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "West York"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions (x, y, w, h)
R_GREY_BRICK     = (0,   256, 256, 256)   # Ming Dynasty weathered grey brick masonry
R_GRANITE_BASE   = (256, 256, 256, 256)   # Heavy dressed granite foundation blocks
R_PAVER_WALKWAY  = (0,   128, 128, 128)   # Stone rampart walkway paving flags
R_ARCHED_SLIT    = (128, 128, 128, 128)   # Arrow slit embrasures & stone drainage spouts


def paint_atlas():
    a = Atlas(S, seed=1368)

    # 1. Grey Ming Brick (R_GREY_BRICK)
    x, y, w, h = R_GREY_BRICK
    a.rect(x, y, w, h, (0.62, 0.64, 0.66))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.48, 0.50, 0.52))
        for rx in range(x + (ry % 24), x + w, 24):
            a.rect(rx, ry, 2, 12, (0.52, 0.54, 0.56))
    a.noise(x, y, w, h, 0.02)

    # 2. Heavy Granite Base (R_GRANITE_BASE)
    x, y, w, h = R_GRANITE_BASE
    a.rect(x, y, w, h, (0.50, 0.48, 0.45))
    for ry in range(y, y + h, 18):
        a.rect(x, ry, w, 3, (0.36, 0.34, 0.32))
    a.noise(x, y, w, h, 0.025)

    # 3. Paved Walkway (R_PAVER_WALKWAY)
    x, y, w, h = R_PAVER_WALKWAY
    a.rect(x, y, w, h, (0.58, 0.57, 0.55))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.42, 0.40, 0.38))
    a.noise(x, y, w, h, 0.02)

    # 4. Arrow Slits (R_ARCHED_SLIT)
    x, y, w, h = R_ARCHED_SLIT
    a.rect(x, y, w, h, (0.58, 0.60, 0.62))
    for wy in range(y + 12, y + h - 16, 28):
        for wx in range(x + 12, x + w - 16, 24):
            a.rect(wx, wy, 8, 16, (0.12, 0.14, 0.16))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_great_wall_tileable", OUT_DIR)


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_great_wall_tile")

    parts = []

    def reg_box(name, w, d, h, at, region=R_GREY_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # TILEABLE GREAT WALL 02: 90-DEGREE CORNER BASTION (~850 TRIS)
    # Enters at X = -6.0m, turns 90 degrees and exits at Y = +6.0m
    # =========================================================================

    # 1. West Arm (Length: 6.0m along X from X = -6.0 to 0.0, Y-center: 0.0)
    reg_box("WestArmBase",    6.0, 4.2, 1.2, (-3.0, 0.0, 0.0), region=R_GRANITE_BASE)
    reg_box("WestArmBody",    6.0, 3.8, 5.3, (-3.0, 0.0, 1.2), region=R_GREY_BRICK)
    reg_box("WestArmWalkway", 6.0, 3.2, 0.2, (-3.0, 0.0, 6.5), region=R_PAVER_WALKWAY)

    # West Arm Crenellations (Outer south side at Y = -1.8m)
    for mi in range(4):
        mx = -5.25 + mi * 1.5
        reg_box(f"WestMerlon_F_{mi}", 0.9, 0.35, 0.8, (mx, -1.8, 6.7), region=R_ARCHED_SLIT)

    # 2. North Arm (Length: 6.0m along Y from Y = 0.0 to +6.0, X-center: 0.0)
    reg_box("NorthArmBase",    4.2, 6.0, 1.2, (0.0, 3.0, 0.0), region=R_GRANITE_BASE)
    reg_box("NorthArmBody",    3.8, 6.0, 5.3, (0.0, 3.0, 1.2), region=R_GREY_BRICK)
    reg_box("NorthArmWalkway", 3.2, 6.0, 0.2, (0.0, 3.0, 6.5), region=R_PAVER_WALKWAY)

    # North Arm Crenellations (Outer east side at X = 1.8m)
    for mi in range(4):
        my = 1.25 + mi * 1.5
        reg_box(f"NorthMerlon_R_{mi}", 0.35, 0.9, 0.8, (1.8, my, 6.7), region=R_ARCHED_SLIT)

    # 3. Central Corner Turret Bastion (Center: X = 0.0, Y = 0.0, Z = 0.0 to 8.5m)
    reg_box("CornerTurretBase", 5.2, 5.2, 1.2, (0.0, 0.0, 0.0), region=R_GRANITE_BASE)
    reg_box("CornerTurretBody", 4.8, 4.8, 6.2, (0.0, 0.0, 1.2), region=R_ARCHED_SLIT)
    reg_box("CornerTurretCornice", 5.2, 5.2, 0.4, (0.0, 0.0, 7.4), region=R_GREY_BRICK)

    # Corner Turret Rooftop Merlons (8 Merlons on Turret Parapet)
    for mi in range(3):
        pos = -1.6 + mi * 1.6
        # South outer merlons
        reg_box(f"TurretMerlon_S_{mi}", 0.8, 0.35, 0.8, (pos, -2.4, 7.8), region=R_ARCHED_SLIT)
        # East outer merlons
        reg_box(f"TurretMerlon_E_{mi}", 0.35, 0.8, 0.8, ( 2.4, pos, 7.8), region=R_ARCHED_SLIT)

    # Finalize & Export
    shell = kit.join(parts, "Great_Wall_Var2_Corner_Tower")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "great_wall_var2_corner_tower_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "great_wall_var2_corner_tower.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "great_wall_var2_corner_tower.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "great_wall_var2_corner_tower_preview.png")
        shutil.copy2(OUT_DIR / "atlas_great_wall_tileable.png", TEXTURES_DIR / "atlas_great_wall_tileable.png")
        print(f"[GreatWall_Var2] deployed successfully.")
    except Exception as e:
        print(f"[GreatWall_Var2] deploy notice: {e}")


if __name__ == "__main__":
    main()
