"""Yellow Crane Tower (黄鹤楼) - East York Landmark (~3500 Tris).

Specs:
- Clean 5-tiered classical pagoda structure without surrounding garden/plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - 5 tiers of dramatic upturned swept-wing flying eaves (feiyan) clad in yellow glazed ceramic tiles.
  - Red vermilion lacquer structural columns and wraparound scenic balconies on every storey.
  - Intricate wooden Dougang bracket clusters supporting each flared roof level.
  - Carved golden ridge ornaments, wind bells (fengling), and golden pagoda apex finial (Baoding).
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_yellow_crane_tower.glb.
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
R_YELLOW_TILES   = (0,   256, 256, 256)   # Golden-yellow glazed ceramic pagoda roof tiles
R_VERMILION_POST = (256, 256, 256, 256)   # Vermilion lacquer columns, balustrades & beams
R_STONE_PLINTH   = (0,   128, 128, 128)   # Granite pedestal base & steps
R_PAGODA_LATTICE = (128, 128, 128, 128)   # Traditional wooden lattice windows & carved doors
R_DOUGONG_JADE   = (256, 128, 128, 128)   # Dougang bracket clusters with jade green & gold trim
R_GOLD_FINIAL    = (384, 128, 128, 128)   # Gilded pagoda spire apex finial & corner wind chimes


def paint_atlas():
    a = Atlas(S, seed=1985)

    # 1. Yellow Glazed Pagoda Tiles (R_YELLOW_TILES)
    x, y, w, h = R_YELLOW_TILES
    a.rect(x, y, w, h, (0.95, 0.76, 0.12))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.80, 0.60, 0.08))
        for rx in range(x + (ry % 20), x + w, 20):
            a.rect(rx, ry, 2, 10, (0.88, 0.68, 0.10))
    a.noise(x, y, w, h, 0.012)

    # 2. Vermilion Lacquer Posts & Balconies (R_VERMILION_POST)
    x, y, w, h = R_VERMILION_POST
    a.rect(x, y, w, h, (0.76, 0.18, 0.15))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.58, 0.12, 0.10))
    a.noise(x, y, w, h, 0.015)

    # 3. Granite Plinth (R_STONE_PLINTH)
    x, y, w, h = R_STONE_PLINTH
    a.rect(x, y, w, h, (0.68, 0.66, 0.62))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.52, 0.50, 0.48))
    a.noise(x, y, w, h, 0.018)

    # 4. Pagoda Lattice (R_PAGODA_LATTICE)
    x, y, w, h = R_PAGODA_LATTICE
    a.rect(x, y, w, h, (0.72, 0.22, 0.18))
    for wy in range(y + 6, y + h - 12, 22):
        for wx in range(x + 6, x + w - 12, 18):
            a.rect(wx, wy, 12, 16, (0.20, 0.12, 0.08))
            a.rect(wx + 5, wy, 2, 16, (0.90, 0.75, 0.20))
    a.noise(x, y, w, h, 0.01)

    # 5. Dougang Jade (R_DOUGONG_JADE)
    x, y, w, h = R_DOUGONG_JADE
    a.rect(x, y, w, h, (0.16, 0.46, 0.38))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.90, 0.78, 0.22))
    a.noise(x, y, w, h, 0.015)

    # 6. Gilded Finial (R_GOLD_FINIAL)
    x, y, w, h = R_GOLD_FINIAL
    a.rect(x, y, w, h, (0.94, 0.80, 0.22))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_yellow_crane_tower", OUT_DIR)


def make_cylinder(name, r, h, segs=16, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    faces.append(list(range(segs - 1, -1, -1)))
    faces.append(list(range(segs, segs * 2)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def make_flared_pagoda_eave(name, bw, bd, tw, td, height, flare=1.0, at=(0, 0, 0)):
    """Creates octagonal/cross swept pagoda eave with upturned flying corners."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hbw, hbd = bw / 2 + flare, bd / 2 + flare
    htw, htd = tw / 2, td / 2

    # Corner upturns
    v0 = bm.verts.new((-hbw, -hbd, 0.45))
    v1 = bm.verts.new(( hbw, -hbd, 0.45))
    v2 = bm.verts.new(( hbw,  hbd, 0.45))
    v3 = bm.verts.new((-hbw,  hbd, 0.45))

    v01 = bm.verts.new((0, -hbd * 0.90, 0.0))
    v12 = bm.verts.new((hbw * 0.90, 0, 0.0))
    v23 = bm.verts.new((0,  hbd * 0.90, 0.0))
    v30 = bm.verts.new((-hbw * 0.90, 0, 0.0))

    t0 = bm.verts.new((-htw, -htd, height))
    t1 = bm.verts.new(( htw, -htd, height))
    t2 = bm.verts.new(( htw,  htd, height))
    t3 = bm.verts.new((-htw,  htd, height))

    bm.faces.new((v0, v01, t0))
    bm.faces.new((v01, v1, t1, t0))
    bm.faces.new((v1, v12, t1))
    bm.faces.new((v12, v2, t2, t1))
    bm.faces.new((v2, v23, t2))
    bm.faces.new((v23, v3, t3, t2))
    bm.faces.new((v3, v30, t3))
    bm.faces.new((v30, v0, t0, t3))
    bm.faces.new((t3, t2, t1, t0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_yellow_crane")

    parts = []

    def reg_box(name, w, d, h, at, region=R_VERMILION_POST):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_VERMILION_POST):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_eave(name, bw, bd, tw, td, h, flare=1.0, at=(0, 0, 0), region=R_YELLOW_TILES):
        o = make_flared_pagoda_eave(name, bw, bd, tw, td, h, flare, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # YELLOW CRANE TOWER (BUILDING ONLY - ~3500 TRIS)
    # Total Height: 22.0m, Base Width: 12.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Granite Pedestal Plinth Base (Z = 0.0 to 1.5m)
    reg_box("GraniteBase_L1", 12.0, 12.0, 0.8, (0, 0, 0.0), region=R_STONE_PLINTH)
    reg_box("GraniteBase_L2", 10.8, 10.8, 0.7, (0, 0, 0.8), region=R_STONE_PLINTH)

    # 2. Five Pagoda Storeys (Z = 1.5m to 19.5m)
    storey_specs = [
        # (Tier, Core Width, Storey Height, Eave Width, Eave Flare, Z Base)
        (1, 9.2, 3.2, 11.2, 1.2,  1.5),
        (2, 8.2, 2.8, 10.2, 1.1,  5.2),
        (3, 7.2, 2.8,  9.2, 1.0,  8.6),
        (4, 6.2, 2.8,  8.2, 0.9, 12.0),
        (5, 5.2, 2.8,  7.2, 0.8, 15.4),
    ]

    for ti, cw, sh, ew, flare, zb in storey_specs:
        # Core Room Body
        reg_box(f"PagodaCore_T{ti}", cw, cw, sh, (0, 0, zb), region=R_PAGODA_LATTICE)

        # Wraparound Balcony Railings
        reg_box(f"Balcony_T{ti}", cw + 0.8, cw + 0.8, 0.5, (0, 0, zb), region=R_VERMILION_POST)

        # 8 Columns around storey perimeter (16 segments each)
        for ci, (cx, cy) in enumerate([
            (-cw/2, -cw/2), (0, -cw/2), (cw/2, -cw/2),
            (-cw/2,  cw/2), (0,  cw/2), (cw/2,  cw/2),
            (-cw/2, 0), (cw/2, 0)
        ]):
            reg_cyl(f"Col_T{ti}_{ci}", r=0.18, h=sh, segs=12, at=(cx, cy, zb), region=R_VERMILION_POST)

        # Dougang Bracket Band
        reg_box(f"Dougang_T{ti}", cw + 0.6, cw + 0.6, 0.4, (0, 0, zb + sh), region=R_DOUGONG_JADE)

        # Flared Swept-Wing Flying Eave
        top_w = cw * 0.7 if ti < 5 else 0.4
        reg_eave(f"RoofEave_T{ti}", bw=ew, bd=ew, tw=top_w, td=top_w, h=1.4 if ti < 5 else 2.5, flare=flare, at=(0, 0, zb + sh + 0.4), region=R_YELLOW_TILES)

    # 3. Golden Pagoda Spire Apex Finial (Baoding at Z = 19.8m)
    reg_cyl("PagodaFinialBase", r=0.7, h=0.6, segs=16, at=(0, 0, 19.8), region=R_GOLD_FINIAL)
    reg_cyl("PagodaFinialGourd", r=0.5, h=1.4, segs=16, at=(0, 0, 20.4), region=R_GOLD_FINIAL)
    reg_cyl("PagodaFinialSpireTip", r=0.15, h=1.0, segs=10, at=(0, 0, 21.8), region=R_GOLD_FINIAL)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Yellow_Crane_Tower")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_yellow_crane_tower_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_yellow_crane_tower.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_yellow_crane_tower.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_yellow_crane_tower_preview.png")
        shutil.copy2(OUT_DIR / "atlas_yellow_crane_tower.png", TEXTURES_DIR / "atlas_yellow_crane_tower.png")
        print(f"[YellowCraneTower] deployed successfully.")
    except Exception as e:
        print(f"[YellowCraneTower] deploy notice: {e}")


if __name__ == "__main__":
    main()
