"""West York Martial Arts Dojo - Variant 3: Courtyard Temple Dojo (~880 Tris).

Specs:
- Footprint: 10.0m wide x 9.0m deep, Height: 7.0m. Sits directly at Z = 0.0.
- Features:
  - Elevated 2-tier stone terrace with open martial arts sparring courtyard.
  - Central Pagoda training pavilion with double swept glazed blue/gold eaves and bell finial.
  - Ceremonial circular Moon Gate entrance portal with red lacquer frame.
  - Wooden dummy (Mook Yan Jong) training posts and brass gong stanchion.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/building_dojo_03_courtyard_temple_dojo.glb.
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
R_COBALT_ROOF    = (0,   256, 256, 256)   # Sacred cobalt blue glazed ceramic roof tiles
R_TEMPLE_WOOD    = (256, 256, 256, 256)   # Dark polished cedar timber posts & moon gate
R_STONE_TERRACE  = (0,   128, 128, 128)   # Grey granite terrace paving & courtyard flags
R_MOON_GATE      = (128, 128, 128, 128)   # Vermilion red ceremonial circular moon gate & gold plaque
R_BRASS_GONG     = (256, 128, 128, 128)   # Gilded temple bells, brass gong & dragon finials
R_WOOD_DUMMY     = (384, 128, 128, 128)   # Wing Chun wooden dummy (Mook Yan Jong) timber


def paint_atlas():
    a = Atlas(S, seed=1720)

    # 1. Cobalt Tile (R_COBALT_ROOF)
    x, y, w, h = R_COBALT_ROOF
    a.rect(x, y, w, h, (0.16, 0.32, 0.68))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.08, 0.18, 0.45))
    a.noise(x, y, w, h, 0.015)

    # 2. Cedar Timber (R_TEMPLE_WOOD)
    x, y, w, h = R_TEMPLE_WOOD
    a.rect(x, y, w, h, (0.35, 0.18, 0.10))
    for ry in range(y, y + h, 28):
        a.rect(x, ry, w, 2, (0.22, 0.10, 0.06))
    a.noise(x, y, w, h, 0.02)

    # 3. Stone Terrace (R_STONE_TERRACE)
    x, y, w, h = R_STONE_TERRACE
    a.rect(x, y, w, h, (0.75, 0.74, 0.72))
    for ry in range(y, y + h, 20):
        a.rect(x, ry, w, 2, (0.58, 0.57, 0.55))
        for rx in range(x + (ry % 30), x + w, 30):
            a.rect(rx, ry, 2, 20, (0.58, 0.57, 0.55))
    a.noise(x, y, w, h, 0.02)

    # 4. Moon Gate (R_MOON_GATE)
    x, y, w, h = R_MOON_GATE
    a.rect(x, y, w, h, (0.78, 0.16, 0.14))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 44, (0.10, 0.12, 0.14))
    a.disc(cx, cy, 38, (0.78, 0.16, 0.14))
    a.noise(x, y, w, h, 0.01)

    # 5. Brass Gong & Bells (R_BRASS_GONG)
    x, y, w, h = R_BRASS_GONG
    a.rect(x, y, w, h, (0.90, 0.76, 0.20))
    a.disc(x + w // 2, y + h // 2, 40, (0.72, 0.56, 0.12))
    a.disc(x + w // 2, y + h // 2, 34, (0.92, 0.80, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 6. Wooden Dummy (R_WOOD_DUMMY)
    x, y, w, h = R_WOOD_DUMMY
    a.rect(x, y, w, h, (0.52, 0.32, 0.18))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.35, 0.20, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_dojo_03", OUT_DIR)


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


def make_swept_roof(name, base_w, base_d, height, flare=0.6, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hw, hd = base_w / 2, base_d / 2
    f = flare

    v0 = bm.verts.new((-hw - f, -hd - f, 0))
    v1 = bm.verts.new(( hw + f, -hd - f, 0))
    v2 = bm.verts.new(( hw + f,  hd + f, 0))
    v3 = bm.verts.new((-hw - f,  hd + f, 0))

    rw, rd = hw * 0.4, hd * 0.4
    v4 = bm.verts.new((-rw, -rd, height))
    v5 = bm.verts.new(( rw, -rd, height))
    v6 = bm.verts.new(( rw,  rd, height))
    v7 = bm.verts.new((-rw,  rd, height))

    bm.faces.new((v0, v1, v5, v4))
    bm.faces.new((v1, v2, v6, v5))
    bm.faces.new((v2, v3, v7, v6))
    bm.faces.new((v3, v0, v4, v7))
    bm.faces.new((v4, v5, v6, v7))
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_dojo_03")

    parts = []

    def reg_box(name, w, d, h, at, region=R_TEMPLE_WOOD):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_swept(name, bw, bd, h, flare=0.6, at=(0, 0, 0), region=R_COBALT_ROOF):
        o = make_swept_roof(name, bw, bd, h, flare, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_BRASS_GONG):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK MARTIAL ARTS DOJO 03: COURTYARD TEMPLE DOJO (~880 TRIS)
    # Footprint: 10.0m x 9.0m, Height: 7.0m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Stepped Stone Courtyard Platform (Z = 0.0 to 0.6m)
    reg_box("CourtyardTerraceBase", 9.8, 8.8, 0.35, (0, 0, 0.0), region=R_STONE_TERRACE)
    reg_box("UpperTerracePavilion", 6.8, 5.8, 0.25, (0, 1.0, 0.35), region=R_STONE_TERRACE)

    # 2. Central Pagoda Training Pavilion (X = 0, Y = 1.0m, Z = 0.6m to 7.0m)
    # 4 Heavy Cedar Corner Columns
    for ci, (cx, cy) in enumerate([(-2.6, -1.2), (2.6, -1.2), (-2.6, 3.2), (2.6, 3.2)]):
        reg_cyl(f"PavilionCol_{ci}", r=0.20, h=3.0, segs=16, at=(cx, cy, 0.6), region=R_TEMPLE_WOOD)

    # Pavilion Enclosed Screen Back & Sides
    reg_box("PavilionBackWall", 5.2, 0.2, 3.0, (0, 3.2, 0.6), region=R_TEMPLE_WOOD)
    reg_box("PavilionSideL",    0.2, 4.4, 3.0, (-2.6, 1.0, 0.6), region=R_TEMPLE_WOOD)
    reg_box("PavilionSideR",    0.2, 4.4, 3.0, ( 2.6, 1.0, 0.6), region=R_TEMPLE_WOOD)

    # Double Swept Eaved Pagoda Roof
    # Lower Eave
    reg_swept("PagodaLowerEave", 7.2, 6.2, 1.2, flare=0.8, at=(0, 1.0, 3.6), region=R_COBALT_ROOF)
    # Upper Eave & Apex Spire
    reg_box("PagodaMidClerestory", 4.0, 3.4, 0.8, (0, 1.0, 4.8), region=R_TEMPLE_WOOD)
    reg_swept("PagodaUpperEave", 5.2, 4.4, 1.4, flare=0.7, at=(0, 1.0, 5.4), region=R_COBALT_ROOF)
    reg_cyl("PagodaApexSpire", r=0.18, h=0.8, segs=16, at=(0, 1.0, 6.8), region=R_BRASS_GONG)

    # 3. Ceremonial Moon Gate Entrance Arch (Front Courtyard Portal at Y = -3.2m)
    reg_box("MoonGatePillarL", 0.6, 0.6, 3.2, (-2.0, -3.2, 0.0), region=R_MOON_GATE)
    reg_box("MoonGatePillarR", 0.6, 0.6, 3.2, ( 2.0, -3.2, 0.0), region=R_MOON_GATE)
    reg_box("MoonGateArchTop", 4.6, 0.6, 0.6, (0.0,  -3.2, 3.0), region=R_MOON_GATE)
    reg_swept("MoonGateRoof",  5.2, 1.4, 0.8, flare=0.5, at=(0.0, -3.2, 3.6), region=R_COBALT_ROOF)

    # 4. Courtyard Training Amenities (Wooden Dummy & Brass Gong)
    # Wing Chun Wooden Dummy (Mook Yan Jong) at Left Courtyard
    reg_cyl("WoodenDummyPost", r=0.15, h=1.6, segs=16, at=(-3.0, -1.8, 0.0), region=R_WOOD_DUMMY)
    reg_box("WoodenDummyArms", 0.8, 0.1, 0.1, (-3.0, -1.8, 1.1), region=R_WOOD_DUMMY)
    reg_box("WoodenDummyLeg",  0.1, 0.5, 0.1, (-3.0, -1.6, 0.5), region=R_WOOD_DUMMY)

    # Large Ceremonial Brass Gong at Right Courtyard
    reg_box("GongFrameL", 0.12, 0.12, 2.2, (2.4, -1.8, 0.0), region=R_TEMPLE_WOOD)
    reg_box("GongFrameR", 0.12, 0.12, 2.2, (3.6, -1.8, 0.0), region=R_TEMPLE_WOOD)
    reg_box("GongFrameTop", 1.4, 0.12, 0.12, (3.0, -1.8, 2.1), region=R_TEMPLE_WOOD)
    gong = reg_cyl("BrassGongDisc", r=0.45, h=0.08, segs=16, at=(3.0, -1.8, 1.2), region=R_BRASS_GONG)
    gong.rotation_euler = (math.pi / 2, 0, 0)

    # Finalize & Export
    shell = kit.join(parts, "Building_Dojo_03_Courtyard_Temple")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_dojo_03_courtyard_temple_dojo_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_dojo_03_courtyard_temple_dojo.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_dojo_03_courtyard_temple_dojo.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "building_dojo_03_courtyard_temple_dojo_preview.png")
        shutil.copy2(OUT_DIR / "atlas_dojo_03.png", TEXTURES_DIR / "atlas_dojo_03.png")
        print(f"[Dojo_03] deployed successfully.")
    except Exception as e:
        print(f"[Dojo_03] deploy notice: {e}")


if __name__ == "__main__":
    main()
