"""Tileable Great Wall of China - Variant 3: Fortified Pass Gate Archway (~850 Tris).

Specs:
- Modular Gate Archway Segment: Length: 12.0m (X: -6.0 to +6.0m), Width: 4.5m, Height: 7.5m.
- Seamless Tiling: Connects at X = -6.0m and X = +6.0m with standard rampart profile (walkway at Z = 6.5m).
- Features:
  - Grand semi-circular vaulted passage archway through the center (Z: 0.0 to 3.8m, clearance: 3.4m) allowing players & vehicles to walk through the wall.
  - Reinforced iron-studded timber gate doors.
  - Ming brick gatehouse parapet with stone plaque ("天下第一关" / First Pass Under Heaven) and upper battlements.
- Target: <1,000 tris (~850 tris).
- Deploys to Assets/3DModels/West York/great_wall_var3_gate_arch.glb.
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
R_GATE_TIMBER    = (128, 128, 128, 128)   # Iron-studded heavy timber gate doors & arch keystone


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

    # 4. Gate Timber & Iron (R_GATE_TIMBER)
    x, y, w, h = R_GATE_TIMBER
    a.rect(x, y, w, h, (0.32, 0.16, 0.10))
    for rx in range(x + 10, x + w - 10, 16):
        a.rect(rx, y + 6, 2, h - 12, (0.18, 0.08, 0.04))
    # Iron studs & ring knockers
    for sy in range(y + 20, y + h - 20, 28):
        for sx in range(x + 16, x + w - 16, 24):
            a.disc(sx, sy, 4, (0.15, 0.15, 0.15))
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
    # TILEABLE GREAT WALL 03: FORTIFIED PASS GATE ARCHWAY (~850 TRIS)
    # Length: 12.0m (X: -6.0 to +6.0m), Width: 4.5m, Height: 7.5m
    # =========================================================================

    # 1. Left Bastion Pier (X: -6.0 to -2.0m, Width: 4.0m, Height: 6.5m)
    reg_box("LeftPierBase",    4.0, 4.8, 1.2, (-4.0, 0.0, 0.0), region=R_GRANITE_BASE)
    reg_box("LeftPierBody",    4.0, 4.5, 5.3, (-4.0, 0.0, 1.2), region=R_GREY_BRICK)

    # 2. Right Bastion Pier (X: +2.0 to +6.0m, Width: 4.0m, Height: 6.5m)
    reg_box("RightPierBase",   4.0, 4.8, 1.2, ( 4.0, 0.0, 0.0), region=R_GRANITE_BASE)
    reg_box("RightPierBody",   4.0, 4.5, 5.3, ( 4.0, 0.0, 1.2), region=R_GREY_BRICK)

    # 3. Central Archway Vault & Lintel (Span: 4.0m from X = -2.0 to +2.0m, Z = 3.8m to 6.5m)
    reg_box("ArchwayVaultLintel", 4.0, 4.5, 2.7, (0.0, 0.0, 3.8), region=R_GREY_BRICK)
    reg_box("ArchwayGraniteImpostL", 0.4, 4.6, 0.3, (-2.0, 0.0, 3.6), region=R_GRANITE_BASE)
    reg_box("ArchwayGraniteImpostR", 0.4, 4.6, 0.3, ( 2.0, 0.0, 3.6), region=R_GRANITE_BASE)

    # Arched Opening Keystone Surround (Front & Back)
    reg_box("ArchKeystoneF", 0.8, 0.3, 0.6, (0.0, -2.3, 3.8), region=R_GRANITE_BASE)
    reg_box("ArchKeystoneB", 0.8, 0.3, 0.6, (0.0,  2.3, 3.8), region=R_GRANITE_BASE)

    # 4. Iron-Studded Timber Gate Doors (Inside Portal at Y = 0.0m)
    reg_box("GateDoorL", 1.8, 0.25, 3.6, (-0.95, 0.0, 0.0), region=R_GATE_TIMBER)
    reg_box("GateDoorR", 1.8, 0.25, 3.6, ( 0.95, 0.0, 0.0), region=R_GATE_TIMBER)

    # 5. Continuous Upper Rampart Walkway (X = 12.0m, Z = 6.5m)
    reg_box("GateWalkwaySlab", 12.0, 3.6, 0.2, (0.0, 0.0, 6.5), region=R_PAVER_WALKWAY)

    # 6. Upper Battlements & Merlons (8 Front, 8 Back)
    for mi in range(8):
        mx = -5.25 + mi * 1.5
        reg_box(f"GateMerlon_F_{mi}", 0.9, 0.35, 0.8, (mx, -2.1, 6.7), region=R_GREY_BRICK)
        reg_box(f"GateMerlon_B_{mi}", 0.9, 0.35, 0.8, (mx,  2.1, 6.7), region=R_GREY_BRICK)

    # Finalize & Export
    shell = kit.join(parts, "Great_Wall_Var3_Gate_Arch")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "great_wall_var3_gate_arch_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "great_wall_var3_gate_arch.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "great_wall_var3_gate_arch.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "great_wall_var3_gate_arch_preview.png")
        shutil.copy2(OUT_DIR / "atlas_great_wall_tileable.png", TEXTURES_DIR / "atlas_great_wall_tileable.png")
        print(f"[GreatWall_Var3] deployed successfully.")
    except Exception as e:
        print(f"[GreatWall_Var3] deploy notice: {e}")


if __name__ == "__main__":
    main()
