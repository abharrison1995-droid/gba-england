"""Giant Wild Goose Pagoda (大雁塔) - East York Landmark (~3500 Tris).

Specs:
- Clean 7-storey ancient Tang Dynasty square brick pagoda without surrounding garden/plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - 7 stepped square tiers constructed in warm grey-terracotta rammed brick masonry.
  - Multi-layered projecting brick corbel eaves (dougang mimicry) under every storey.
  - Arched Buddhist relic shrine niches on all 4 cardinal faces of every storey.
  - Classic Tang Dynasty pyramidal crown roof with bronze pagoda spire finial.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_giant_wild_goose_pagoda.glb.
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
R_TANG_BRICK     = (0,   256, 256, 256)   # Ancient warm terracotta-grey Tang Dynasty rammed brick
R_BRICK_EAVE     = (256, 256, 256, 256)   # Stepped corbel brick eaves & shaded overhangs
R_BUDDHIST_NICHE = (0,   128, 128, 128)   # Arched stone shrine niches & seated Buddha figures
R_BRONZE_SPIRE   = (128, 128, 128, 128)   # Weathered bronze pagoda apex spire finial
R_STONE_PODIUM   = (256, 128, 128, 128)   # Terraced stone foundation base plinth


def paint_atlas():
    a = Atlas(S, seed=652)

    # 1. Tang Dynasty Brick (R_TANG_BRICK)
    x, y, w, h = R_TANG_BRICK
    a.rect(x, y, w, h, (0.74, 0.62, 0.52))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.58, 0.46, 0.38))
        for rx in range(x + (ry % 20), x + w, 20):
            a.rect(rx, ry, 2, 10, (0.64, 0.52, 0.42))
    a.noise(x, y, w, h, 0.02)

    # 2. Corbel Brick Eaves (R_BRICK_EAVE)
    x, y, w, h = R_BRICK_EAVE
    a.rect(x, y, w, h, (0.52, 0.42, 0.35))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.38, 0.28, 0.22))
    a.noise(x, y, w, h, 0.02)

    # 3. Buddhist Arched Niches (R_BUDDHIST_NICHE)
    x, y, w, h = R_BUDDHIST_NICHE
    a.rect(x, y, w, h, (0.68, 0.58, 0.48))
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 22):
            a.rect(wx, wy, 12, 18, (0.18, 0.14, 0.12))
            a.disc(wx + 6, wy + 16, 6, (0.18, 0.14, 0.12))
            # Gold seated Buddha silhouette
            a.disc(wx + 6, wy + 8, 3, (0.88, 0.74, 0.22))
    a.noise(x, y, w, h, 0.01)

    # 4. Bronze Spire (R_BRONZE_SPIRE)
    x, y, w, h = R_BRONZE_SPIRE
    a.rect(x, y, w, h, (0.35, 0.45, 0.38))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.24, 0.32, 0.26))
    a.noise(x, y, w, h, 0.015)

    # 5. Stone Podium (R_STONE_PODIUM)
    x, y, w, h = R_STONE_PODIUM
    a.rect(x, y, w, h, (0.60, 0.56, 0.50))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.45, 0.42, 0.36))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_giant_wild_goose_pagoda", OUT_DIR)


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
    mat = material_for(img, "mat_wild_goose")

    parts = []

    def reg_box(name, w, d, h, at, region=R_TANG_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_BRICK_EAVE):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # GIANT WILD GOOSE PAGODA (BUILDING ONLY - ~3500 TRIS)
    # Total Height: 24.0m, Base Width: 11.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Terraced Stone Base Podium (Z = 0.0 to 1.5m)
    reg_box("Podium_L1", 11.5, 11.5, 0.8, (0, 0, 0.0), region=R_STONE_PODIUM)
    reg_box("Podium_L2", 10.4, 10.4, 0.7, (0, 0, 0.8), region=R_STONE_PODIUM)

    # 2. Seven Stepped Square Brick Pagoda Storeys (Z = 1.5m to 21.5m)
    tier_specs = [
        # (Tier, Base Width, Height, Eave Width, Z Base)
        (1, 9.2, 3.0, 9.8,  1.5),
        (2, 8.4, 2.8, 8.9,  4.9),
        (3, 7.6, 2.6, 8.0,  8.1),
        (4, 6.8, 2.4, 7.2, 11.1),
        (5, 6.0, 2.2, 6.4, 13.9),
        (6, 5.2, 2.0, 5.5, 16.5),
        (7, 4.4, 1.8, 4.7, 18.9),
    ]

    for ti, bw, th, ew, zb in tier_specs:
        # Brick Tower Body
        reg_box(f"PagodaBody_T{ti}", bw, bw, th, (0, 0, zb), region=R_TANG_BRICK)

        # 4 Arched Relic Niches (N, S, E, W faces)
        nw = bw * 0.28
        for fi, (fx, fy, fw, fd) in enumerate([
            (0, -bw/2 - 0.05, nw, 0.1),
            (0,  bw/2 + 0.05, nw, 0.1),
            (-bw/2 - 0.05, 0, 0.1, nw),
            ( bw/2 + 0.05, 0, 0.1, nw),
        ]):
            niche = kit.make_box(f"Niche_T{ti}_{fi}", fw, fd, th * 0.65, (fx, fy, zb + th * 0.2))
            niche.data.materials.append(mat)
            kit.map_faces_to_region(niche, R_BUDDHIST_NICHE, S)
            parts.append(niche)

        # Stepped Corbel Brick Eaves (3 projecting brick sub-layers per eave)
        reg_box(f"Corbel1_T{ti}", ew * 0.95, ew * 0.95, 0.12, (0, 0, zb + th), region=R_BRICK_EAVE)
        reg_box(f"Corbel2_T{ti}", ew * 1.00, ew * 1.00, 0.14, (0, 0, zb + th + 0.12), region=R_BRICK_EAVE)
        reg_box(f"Corbel3_T{ti}", ew * 1.05, ew * 1.05, 0.14, (0, 0, zb + th + 0.26), region=R_BRICK_EAVE)

    # 3. Tang Pyramidal Crown Roof (Z = 21.1m to 23.2m)
    reg_pyr("CrownPyramidRoof", 4.6, 4.6, 2.1, (0, 0, 21.1), region=R_BRICK_EAVE)

    # 4. Bronze Pagoda Spire Finial (Z = 23.2m to 25.5m)
    spire_base = kit.make_box("BronzeFinialBase", 1.0, 1.0, 0.5, (0, 0, 23.2))
    spire_base.data.materials.append(mat)
    kit.map_faces_to_region(spire_base, R_BRONZE_SPIRE, S)
    parts.append(spire_base)

    spire_tip = reg_pyr("BronzeSpireTip", 0.6, 0.6, 1.8, (0, 0, 23.7), region=R_BRONZE_SPIRE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Giant_Wild_Goose_Pagoda")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_giant_wild_goose_pagoda_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_giant_wild_goose_pagoda.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_giant_wild_goose_pagoda.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_giant_wild_goose_pagoda_preview.png")
        shutil.copy2(OUT_DIR / "atlas_giant_wild_goose_pagoda.png", TEXTURES_DIR / "atlas_giant_wild_goose_pagoda.png")
        print(f"[WildGoosePagoda] deployed successfully.")
    except Exception as e:
        print(f"[WildGoosePagoda] deploy notice: {e}")


if __name__ == "__main__":
    main()
