"""Natural History Museum (Waterhouse Building) - Building Only.

Specs:
- Clean building structure without forecourt lawn or gravel slabs.
- Sits directly at Z = 0.0.
- Romanesque Revival Waterhouse facade, twin entrance towers with pyramidal spires,
  triple-recessed rounded portal, and striped terracotta bands.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_natural_history_museum.glb.
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
R_TERRACOTTA_BUFF = (0,   256, 256, 256)   # Waterhouse buff & cream terracotta ceramic ashlar
R_TERRACOTTA_BLUE = (256, 256, 256, 256)   # Blue-grey decorative terracotta striped bands
R_ROMANESQUE_ARCH = (0,   128, 128, 128)   # Triple round-arched portal & animal relief friezes
R_SLATE_SPIRE     = (128, 128, 128, 128)   # Slate tile spires & dormer gables
R_MUSEUM_WINDOWS  = (256, 128, 128, 128)   # Romanesque arched twin windows


def paint_atlas():
    a = Atlas(S, seed=1881)

    # 1. Buff Terracotta (R_TERRACOTTA_BUFF)
    x, y, w, h = R_TERRACOTTA_BUFF
    a.rect(x, y, w, h, (0.86, 0.76, 0.62))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.76, 0.66, 0.52))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.80, 0.70, 0.56))
    a.noise(x, y, w, h, 0.015)

    # 2. Blue-Grey Striped Terracotta (R_TERRACOTTA_BLUE)
    x, y, w, h = R_TERRACOTTA_BLUE
    a.rect(x, y, w, h, (0.42, 0.48, 0.54))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 3, (0.30, 0.36, 0.42))
    a.noise(x, y, w, h, 0.015)

    # 3. Romanesque Portal (R_ROMANESQUE_ARCH)
    x, y, w, h = R_ROMANESQUE_ARCH
    a.rect(x, y, w, h, (0.82, 0.72, 0.58))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy + 10, 48, (0.68, 0.58, 0.46))
    a.disc(cx, cy + 10, 40, (0.86, 0.76, 0.62))
    a.disc(cx, cy + 10, 32, (0.50, 0.40, 0.32))
    a.disc(cx, cy + 10, 24, (0.12, 0.12, 0.14))
    a.noise(x, y, w, h, 0.015)

    # 4. Slate Spires (R_SLATE_SPIRE)
    x, y, w, h = R_SLATE_SPIRE
    a.rect(x, y, w, h, (0.28, 0.32, 0.38))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.22, 0.28))
    a.noise(x, y, w, h, 0.012)

    # 5. Museum Windows (R_MUSEUM_WINDOWS)
    x, y, w, h = R_MUSEUM_WINDOWS
    a.rect(x, y, w, h, (0.82, 0.74, 0.60))
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 22):
            a.rect(wx, wy, 14, 18, (0.12, 0.16, 0.22))
            a.disc(wx + 7, wy + 16, 7, (0.12, 0.16, 0.22))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_natural_history_museum", OUT_DIR)


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
    mat = material_for(img, "mat_natural_history")

    parts = []

    def reg_box(name, w, d, h, at, region=R_TERRACOTTA_BUFF):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_SPIRE):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # NATURAL HISTORY MUSEUM (BUILDING ONLY - NO FORECOURT/LAWN)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Central Waterhouse Portal & Hall (sits at Z = 0.0)
    reg_box("CentralHallBody", 8.0, 8.0, 8.5, (0, 0, 0.0), region=R_TERRACOTTA_BUFF)
    reg_box("GrandArchPortal", 5.0, 1.4, 5.8, (0, -4.3, 0.0), region=R_ROMANESQUE_ARCH)
    reg_pyr("CentralHallRoof", 8.2, 8.2, 4.2, (0, 0, 8.5), region=R_SLATE_SPIRE)

    # Striped Bands on Central Hall
    for bi in range(4):
        reg_box(f"CentralBand_{bi}", 8.1, 8.1, 0.4, (0, 0, 1.8 + bi * 1.8), region=R_TERRACOTTA_BLUE)

    # 2. Twin Waterhouse Entrance Towers (sits at Z = 0.0)
    for ti, (tx, is_l) in enumerate([(-4.8, True), (4.8, False)]):
        t_prefix = f"NHM_Tower_{ti}"
        reg_box(f"{t_prefix}_Shaft", 3.2, 3.2, 11.5, (tx, -3.5, 0.0), region=R_MUSEUM_WINDOWS)
        for bi in range(5):
            reg_box(f"{t_prefix}_Band_{bi}", 3.3, 3.3, 0.35, (tx, -3.5, 1.8 + bi * 2.0), region=R_TERRACOTTA_BLUE)
        reg_box(f"{t_prefix}_Belfry", 3.4, 3.4, 2.2, (tx, -3.5, 11.5), region=R_TERRACOTTA_BUFF)
        reg_pyr(f"{t_prefix}_Spire", 3.4, 3.4, 5.2, (tx, -3.5, 13.7), region=R_SLATE_SPIRE)

        for ci, (cx, cy) in enumerate([(-1.6, -1.6), (1.6, -1.6), (-1.6, 1.6), (1.6, 1.6)]):
            reg_box(f"{t_prefix}_CornerTurret_{ci}", 0.7, 0.7, 3.2, (tx + cx, -3.5 + cy, 11.5), region=R_TERRACOTTA_BUFF)
            reg_pyr(f"{t_prefix}_TurretSpire_{ci}", 0.8, 0.8, 1.8, (tx + cx, -3.5 + cy, 14.7), region=R_SLATE_SPIRE)

    # 3. Flanking East & West Wings (sits at Z = 0.0)
    for wi, (wx, is_l) in enumerate([(-9.0, True), (9.0, False)]):
        w_prefix = f"NHM_Wing_{wi}"
        reg_box(f"{w_prefix}_Body", 6.5, 8.0, 7.0, (wx, 0, 0.0), region=R_MUSEUM_WINDOWS)
        reg_pyr(f"{w_prefix}_Roof", 6.7, 8.2, 3.2, (wx, 0, 7.0), region=R_SLATE_SPIRE)
        for bi in range(3):
            reg_box(f"{w_prefix}_Band_{bi}", 6.6, 8.1, 0.35, (wx, 0, 1.8 + bi * 1.8), region=R_TERRACOTTA_BLUE)
        for di in range(3):
            dy = -2.5 + di * 2.5
            reg_pyr(f"{w_prefix}_Dormer_{di}", 1.4, 1.4, 1.6, (wx, dy, 7.0), region=R_SLATE_SPIRE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Natural_History_Museum")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_natural_history_museum_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_natural_history_museum.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_natural_history_museum.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_natural_history_museum_preview.png")
        shutil.copy2(OUT_DIR / "atlas_natural_history_museum.png", TEXTURES_DIR / "atlas_natural_history_museum.png")
        print(f"[NaturalHistoryMuseum] clean building deployed.")
    except Exception as e:
        print(f"[NaturalHistoryMuseum] deploy notice: {e}")


if __name__ == "__main__":
    main()
