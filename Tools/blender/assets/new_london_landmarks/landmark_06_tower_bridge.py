"""Tower Bridge (Victorian Gothic Suspension Towers) - Structure Only.

Specs:
- Clean bridge structure without extended surrounding river terrain slabs.
- Twin Portland stone clad towers with 4 corner turrets and gothic roof spires.
- High-level double pedestrian walkways with steel truss arches.
- Central bascule bridge deck and side suspension chain approach spans.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_tower_bridge.glb.
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
OUT_DIR = kit.OUT_DIR / "new_london_landmarks"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "New LonLandmark"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions
R_STONE_TOWER     = (0,   256, 256, 256)   # Portland stone & Cornish granite Gothic ashlar
R_BRIDGE_BLUE     = (256, 256, 256, 256)   # Tower Bridge painted blue ironwork & suspension chains
R_GOTHIC_ROOF     = (0,   128, 128, 128)   # Lead & copper turret caps & central pediments
R_WALKWAY_GLASS   = (128, 128, 128, 128)   # High-level walkway glass windows & decorative lattice
R_ROADWAY_TARMAC  = (256, 128, 128, 128)   # Bascule bridge road deck & white road markings


def paint_atlas():
    a = Atlas(S, seed=1894)

    # 1. Portland Stone Tower (R_STONE_TOWER)
    x, y, w, h = R_STONE_TOWER
    a.rect(x, y, w, h, (0.82, 0.80, 0.76))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.70, 0.68, 0.64))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.74, 0.72, 0.68))
    a.noise(x, y, w, h, 0.015)

    # 2. Tower Bridge Blue Ironwork (R_BRIDGE_BLUE)
    x, y, w, h = R_BRIDGE_BLUE
    a.rect(x, y, w, h, (0.12, 0.42, 0.68))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 2, h, (0.08, 0.28, 0.48))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.08, 0.28, 0.48))
    for gx in range(x + 20, x + w, 40):
        a.disc(gx, y + h // 2, 6, (0.85, 0.75, 0.25))
    a.noise(x, y, w, h, 0.012)

    # 3. Gothic Roof (R_GOTHIC_ROOF)
    x, y, w, h = R_GOTHIC_ROOF
    a.rect(x, y, w, h, (0.28, 0.32, 0.36))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.22, 0.26))
    a.noise(x, y, w, h, 0.012)

    # 4. Walkway Windows (R_WALKWAY_GLASS)
    x, y, w, h = R_WALKWAY_GLASS
    a.rect(x, y, w, h, (0.12, 0.16, 0.22))
    for wx in range(x + 8, x + w, 18):
        a.rect(wx, y + 10, 10, h - 20, (0.45, 0.65, 0.80))
    a.noise(x, y, w, h, 0.01)

    # 5. Roadway Tarmac (R_ROADWAY_TARMAC)
    x, y, w, h = R_ROADWAY_TARMAC
    a.rect(x, y, w, h, (0.22, 0.22, 0.24))
    for ry in range(y, y + h, 20):
        a.rect(x + w // 2 - 2, ry, 4, 10, (0.95, 0.95, 0.95))
    a.rect(x + 4, y, 16, h, (0.48, 0.22, 0.20))
    a.rect(x + w - 20, y, 16, h, (0.48, 0.22, 0.20))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_tower_bridge", OUT_DIR)


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
    mat = material_for(img, "mat_tower_bridge")

    parts = []

    def reg_box(name, w, d, h, at, region=R_STONE_TOWER):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_GOTHIC_ROOF):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # TOWER BRIDGE GEOMETRY (STRUCTURE ONLY)
    # Length: 24m, Width: 8m, Height: 16m
    # =========================================================================

    # 1. Roadway Bridge Deck (sits at Z = 1.0m)
    reg_box("BasculeDeck_North", 5.2, 3.8, 0.4, (0, -2.0, 1.0), region=R_ROADWAY_TARMAC)
    reg_box("BasculeDeck_South", 5.2, 3.8, 0.4, (0,  2.0, 1.0), region=R_ROADWAY_TARMAC)

    reg_box("ApproachSpan_North", 5.2, 5.5, 0.4, (0, -9.25, 1.0), region=R_ROADWAY_TARMAC)
    reg_box("ApproachSpan_South", 5.2, 5.5, 0.4, (0,  9.25, 1.0), region=R_ROADWAY_TARMAC)

    # 2. Suspension Chain Beams & Hangers
    for side_x in [-2.4, 2.4]:
        reg_box(f"SuspensionBeam_N_{side_x}", 0.25, 6.0, 0.35, (side_x, -9.0, 4.5), region=R_BRIDGE_BLUE)
        reg_box(f"SuspensionBeam_S_{side_x}", 0.25, 6.0, 0.35, (side_x,  9.0, 4.5), region=R_BRIDGE_BLUE)
        for hi in range(5):
            hy = -11.0 + hi * 1.0
            reg_box(f"Hanger_N_{side_x}_{hi}", 0.08, 0.08, 2.5 + hi * 0.5, (side_x, hy, 1.2), region=R_BRIDGE_BLUE)
            reg_box(f"Hanger_S_{side_x}_{hi}", 0.08, 0.08, 2.5 + (4 - hi) * 0.5, (side_x, -hy, 1.2), region=R_BRIDGE_BLUE)

    # 3. Twin Victorian Gothic Towers (North at Y: -5.5m, South at Y: +5.5m - Sits at Z = 0.0)
    for ti, ty in enumerate([-5.5, 5.5]):
        t_prefix = f"Tower_{ti}"
        reg_box(f"{t_prefix}_Leg_L", 1.4, 4.2, 7.5, (-2.4, ty, 0.0), region=R_STONE_TOWER)
        reg_box(f"{t_prefix}_Leg_R", 1.4, 4.2, 7.5, ( 2.4, ty, 0.0), region=R_STONE_TOWER)
        reg_box(f"{t_prefix}_ArchLintel", 4.0, 4.2, 1.2, (0, ty, 6.3), region=R_STONE_TOWER)

        reg_box(f"{t_prefix}_UpperBody", 5.6, 4.0, 5.5, (0, ty, 7.5), region=R_STONE_TOWER)

        for ci, (cx, c_dy) in enumerate([(-2.5, -1.8), (2.5, -1.8), (-2.5, 1.8), (2.5, 1.8)]):
            reg_box(f"{t_prefix}_Turret_{ci}", 0.9, 0.9, 6.5, (cx, ty + c_dy, 7.5), region=R_STONE_TOWER)
            reg_pyr(f"{t_prefix}_TurretSpire_{ci}", 1.0, 1.0, 2.2, (cx, ty + c_dy, 14.0), region=R_GOTHIC_ROOF)

        reg_pyr(f"{t_prefix}_MainRoof", 4.8, 3.2, 3.5, (0, ty, 13.0), region=R_GOTHIC_ROOF)

    # 4. High-Level Double Walkways
    reg_box("HighWalkway_Upper", 2.2, 10.0, 1.2, (0, 0, 12.8), region=R_WALKWAY_GLASS)
    reg_box("HighWalkway_Lower", 2.2, 10.0, 1.0, (0, 0, 11.2), region=R_WALKWAY_GLASS)

    reg_box("WalkwayArchTruss_L", 0.25, 9.8, 0.4, (-1.2, 0, 10.8), region=R_BRIDGE_BLUE)
    reg_box("WalkwayArchTruss_R", 0.25, 9.8, 0.4, ( 1.2, 0, 10.8), region=R_BRIDGE_BLUE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Tower_Bridge")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_tower_bridge_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_tower_bridge.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_tower_bridge.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_tower_bridge_preview.png")
        shutil.copy2(OUT_DIR / "atlas_tower_bridge.png", TEXTURES_DIR / "atlas_tower_bridge.png")
        print(f"[TowerBridge] clean building deployed.")
    except Exception as e:
        print(f"[TowerBridge] deploy notice: {e}")


if __name__ == "__main__":
    main()
