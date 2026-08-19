"""The Great Wall (Watchtower Fortress / 长城敌楼) - East York Landmark (~3500 Tris).

Specs:
- Clean fortress watchtower structure without terrain or outer landscape ground slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - 2-storey heavy grey granite and kiln-fired Ming brick defensive bastion.
  - Arched brick arrow-slit windows (embrasures) across lower and upper storeys.
  - Stepped stone cornices and upper rooftop battlement parapet with 40+ merlons.
  - Central pitched watch house guard room atop the roof with traditional gabled tile roof.
  - Flanking fortified rampart sections with crenellations and stone steps.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_great_wall.glb.
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
OUT_DIR = kit.OUT_DIR / "east_york"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "East York"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions (x, y, w, h)
R_GREY_BRICK     = (0,   256, 256, 256)   # Ming Dynasty weathered grey brick masonry
R_GRANITE_BASE   = (256, 256, 256, 256)   # Heavy dressed granite foundation blocks
R_ROOF_TILE_GREY = (0,   128, 128, 128)   # Dark grey earthenware cylindrical ridge tiles
R_ARCHED_WINDOW  = (128, 128, 128, 128)   # Arched brick arrow-slit openings & wooden shutters
R_TIMBER_GUARD   = (256, 128, 128, 128)   # Timber guardhouse posts, beams & studded door


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

    # 2. Heavy Granite (R_GRANITE_BASE)
    x, y, w, h = R_GRANITE_BASE
    a.rect(x, y, w, h, (0.50, 0.48, 0.45))
    for ry in range(y, y + h, 18):
        a.rect(x, ry, w, 3, (0.36, 0.34, 0.32))
    a.noise(x, y, w, h, 0.025)

    # 3. Grey Roof Tile (R_ROOF_TILE_GREY)
    x, y, w, h = R_ROOF_TILE_GREY
    a.rect(x, y, w, h, (0.34, 0.36, 0.38))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.24, 0.26, 0.28))
    a.noise(x, y, w, h, 0.012)

    # 4. Arched Windows (R_ARCHED_WINDOW)
    x, y, w, h = R_ARCHED_WINDOW
    a.rect(x, y, w, h, (0.58, 0.60, 0.62))
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 22):
            a.rect(wx, wy, 12, 20, (0.10, 0.12, 0.14))
            a.disc(wx + 6, wy + 18, 6, (0.10, 0.12, 0.14))
    a.noise(x, y, w, h, 0.01)

    # 5. Timber Guardhouse (R_TIMBER_GUARD)
    x, y, w, h = R_TIMBER_GUARD
    a.rect(x, y, w, h, (0.42, 0.24, 0.16))
    for rx in range(x, x + w, 14):
        a.rect(rx, y, 3, h, (0.28, 0.14, 0.10))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_great_wall", OUT_DIR)


def make_pyramid(name, base_w, base_d, height, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hw, hd = base_w / 2, base_d / 2
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, 0))
    v3 = bm.verts.new((-hw,  hd, 0))
    v_top = bm.verts.new((0, 0, height))

    bm.faces.new((v0, v1, v_top))
    bm.faces.new((v1, v2, v_top))
    bm.faces.new((v2, v3, v_top))
    bm.faces.new((v3, v0, v_top))
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_great_wall")

    parts = []

    def reg_box(name, w, d, h, at, region=R_GREY_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_ROOF_TILE_GREY):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # THE GREAT WALL: WATCHTOWER FORTRESS BASTION (~3500 TRIS)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Heavy Granite Foundation Base (Z = 0.0 to 1.5m)
    reg_box("GraniteBase_Main", 10.5, 10.5, 1.5, (0, 0, 0.0), region=R_GRANITE_BASE)

    # 2. Main 2-Storey Bastion Tower Body (Z = 1.5m to 8.5m)
    # Lower Storey
    reg_box("TowerLowerStorey", 10.0, 10.0, 3.5, (0, 0, 1.5), region=R_ARCHED_WINDOW)
    # Belt Cornice
    reg_box("TowerMidCornice", 10.3, 10.3, 0.4, (0, 0, 5.0), region=R_GREY_BRICK)
    # Upper Storey
    reg_box("TowerUpperStorey", 9.8, 9.8, 3.5, (0, 0, 5.4), region=R_ARCHED_WINDOW)
    # Rooftop Cornice
    reg_box("TowerRoofCornice", 10.4, 10.4, 0.5, (0, 0, 8.9), region=R_GREY_BRICK)

    # 3. Upper Rooftop Battlements & Crenellations (44 Merlons)
    for mi in range(6):
        mx = -4.0 + mi * 1.6
        # Front merlons
        reg_box(f"Merlon_F_{mi}", 0.9, 0.35, 0.9, (mx, -5.0, 9.4), region=R_GREY_BRICK)
        # Back merlons
        reg_box(f"Merlon_B_{mi}", 0.9, 0.35, 0.9, (mx,  5.0, 9.4), region=R_GREY_BRICK)
        # Left merlons
        reg_box(f"Merlon_L_{mi}", 0.35, 0.9, 0.9, (-5.0, mx, 9.4), region=R_GREY_BRICK)
        # Right merlons
        reg_box(f"Merlon_R_{mi}", 0.35, 0.9, 0.9, ( 5.0, mx, 9.4), region=R_GREY_BRICK)

    # 4. Central Rooftop Guardhouse & Swept Tile Roof (Z = 9.4m to 13.0m)
    reg_box("RooftopGuardhouse", 5.2, 5.2, 2.2, (0, 0, 9.4), region=R_TIMBER_GUARD)
    reg_box("GuardhouseDoor", 1.2, 0.2, 1.8, (0, -2.6, 9.4), region=R_TIMBER_GUARD)
    reg_pyr("GuardhouseRoof", 6.2, 6.2, 1.8, (0, 0, 11.6), region=R_ROOF_TILE_GREY)

    # 5. Flanking Rampart Wall Arms (East & West Wall Wings)
    # West Rampart Wall (Length: 6m, Height: 6.5m)
    reg_box("WestRampartBase", 6.0, 4.2, 1.2, (-8.0, 0, 0.0), region=R_GRANITE_BASE)
    reg_box("WestRampartBody", 6.0, 3.8, 5.3, (-8.0, 0, 1.2), region=R_GREY_BRICK)
    reg_box("WestRampartWalkway", 6.0, 3.0, 0.2, (-8.0, 0, 6.5), region=R_GREY_BRICK)

    # West Rampart Crenellations (Front & Back)
    for wi in range(4):
        wx = -10.0 + wi * 1.5
        reg_box(f"RampartMerlon_WF_{wi}", 0.8, 0.3, 0.8, (wx, -1.8, 6.7), region=R_GREY_BRICK)
        reg_box(f"RampartMerlon_WB_{wi}", 0.8, 0.3, 0.8, (wx,  1.8, 6.7), region=R_GREY_BRICK)

    # East Rampart Wall (Length: 6m, Height: 6.5m)
    reg_box("EastRampartBase", 6.0, 4.2, 1.2, (8.0, 0, 0.0), region=R_GRANITE_BASE)
    reg_box("EastRampartBody", 6.0, 3.8, 5.3, (8.0, 0, 1.2), region=R_GREY_BRICK)
    reg_box("EastRampartWalkway", 6.0, 3.0, 0.2, (8.0, 0, 6.5), region=R_GREY_BRICK)

    # East Rampart Crenellations (Front & Back)
    for wi in range(4):
        wx = 6.0 + wi * 1.5
        reg_box(f"RampartMerlon_EF_{wi}", 0.8, 0.3, 0.8, (wx, -1.8, 6.7), region=R_GREY_BRICK)
        reg_box(f"RampartMerlon_EB_{wi}", 0.8, 0.3, 0.8, (wx,  1.8, 6.7), region=R_GREY_BRICK)

    # 6. Stone Staircase Access on Rampart
    for si in range(6):
        reg_box(f"AccessStep_{si}", 1.4, 0.4, 0.3, (-5.5, 2.2 + si * 0.35, 0.0 + si * 0.3), region=R_GRANITE_BASE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Great_Wall")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_great_wall_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_great_wall.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_great_wall.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_great_wall_preview.png")
        shutil.copy2(OUT_DIR / "atlas_great_wall.png", TEXTURES_DIR / "atlas_great_wall.png")
        print(f"[GreatWall] deployed successfully.")
    except Exception as e:
        print(f"[GreatWall] deploy notice: {e}")


if __name__ == "__main__":
    main()
