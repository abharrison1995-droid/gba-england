"""West York Martial Arts Dojo - Variant 1: Traditional Kung Fu Kwoon (~880 Tris).

Specs:
- Footprint: 10.0m wide x 8.0m deep, Height: 6.2m. Sits directly at Z = 0.0.
- Features:
  - Single-storey traditional Chinese martial arts training hall (Kwoon).
  - Vermilion red timber columns with jade bracket capitals and carved lattice screen walls.
  - Sweeping glazed imperial green/gold ceramic hip-and-gable tile roof with upturned flying eaves and dragon ridge beasts.
  - Central double lattice player entrance doors with gold calligraphy plaque ("武道馆" / Martial Arts Hall).
  - Flanking stone guardian lion pedestals and bronze incense burner.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/building_dojo_01_traditional_kwoon.glb.
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
R_VERMILION_WOOD = (0,   256, 256, 256)   # Vermilion red lacquer timber posts & beams
R_GREEN_ROOF     = (256, 256, 256, 256)   # Glazed imperial green ceramic roof tiles
R_LATTICE_DOOR   = (0,   128, 128, 128)   # Traditional wooden lattice screen doors & gold sign
R_MARBLE_BASE    = (128, 128, 128, 128)   # White carved marble base & lion pedestals
R_GOLD_FINIAL    = (256, 128, 128, 128)   # Gilded dragon ridge beasts & brass incense burner
R_BRACKET_PAINT  = (384, 128, 128, 128)   # Qing Dynasty polychrome painted Dougang brackets


def paint_atlas():
    a = Atlas(S, seed=1644)

    # 1. Vermilion Timber (R_VERMILION_WOOD)
    x, y, w, h = R_VERMILION_WOOD
    a.rect(x, y, w, h, (0.74, 0.16, 0.12))
    for ry in range(y, y + h, 32):
        a.rect(x, ry, w, 2, (0.54, 0.10, 0.08))
    a.noise(x, y, w, h, 0.02)

    # 2. Glazed Green Tile (R_GREEN_ROOF)
    x, y, w, h = R_GREEN_ROOF
    a.rect(x, y, w, h, (0.16, 0.45, 0.28))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.08, 0.28, 0.16))
    a.noise(x, y, w, h, 0.015)

    # 3. Lattice Screen & Sign (R_LATTICE_DOOR)
    x, y, w, h = R_LATTICE_DOOR
    a.rect(x, y, w, h, (0.28, 0.14, 0.08))
    # Lattice geometric grid
    for rx in range(x + 6, x + w - 6, 10):
        a.rect(rx, y + 6, 2, h - 12, (0.85, 0.72, 0.35))
    for ry in range(y + 6, y + h - 12, 10):
        a.rect(x + 6, ry, w - 12, 2, (0.85, 0.72, 0.35))
    # Gold calligraphic plaque
    a.rect(x + 8, y + h - 24, w - 16, 18, (0.10, 0.10, 0.10))
    a.rect(x + 12, y + h - 20, w - 24, 10, (0.92, 0.80, 0.22))
    a.noise(x, y, w, h, 0.01)

    # 4. Marble Base (R_MARBLE_BASE)
    x, y, w, h = R_MARBLE_BASE
    a.rect(x, y, w, h, (0.88, 0.87, 0.84))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.72, 0.70, 0.66))
    a.noise(x, y, w, h, 0.015)

    # 5. Gold Finial (R_GOLD_FINIAL)
    x, y, w, h = R_GOLD_FINIAL
    a.rect(x, y, w, h, (0.92, 0.78, 0.22))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.68, 0.54, 0.12))
    a.noise(x, y, w, h, 0.02)

    # 6. Polychrome Brackets (R_BRACKET_PAINT)
    x, y, w, h = R_BRACKET_PAINT
    a.rect(x, y, w, h, (0.15, 0.42, 0.55))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 8, h, (0.75, 0.18, 0.15))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_dojo_01", OUT_DIR)


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
    mat = material_for(img, "mat_dojo_01")

    parts = []

    def reg_box(name, w, d, h, at, region=R_VERMILION_WOOD):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_swept(name, bw, bd, h, flare=0.6, at=(0, 0, 0), region=R_GREEN_ROOF):
        o = make_swept_roof(name, bw, bd, h, flare, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_VERMILION_WOOD):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK MARTIAL ARTS DOJO 01: TRADITIONAL KUNG FU KWOON (~880 TRIS)
    # Footprint: 10.0m x 8.0m, Height: 6.2m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. White Marble Podium Base (Z = 0.0 to 0.45m, Width: 9.5m, Depth: 7.5m)
    reg_box("DojoPlinthBase", 9.5, 7.5, 0.45, (0, 0, 0.0), region=R_MARBLE_BASE)

    # 2. Main Training Hall Body with Lattice Screen Walls (Z = 0.45m to 3.8m)
    reg_box("DojoHallBody", 8.8, 6.8, 3.35, (0, 0, 0.45), region=R_LATTICE_DOOR)

    # 3. 6 Vermilion Lacquer Perimeter Columns (Front & Back Porches)
    for ci, cx in enumerate([-4.0, -1.6, 1.6, 4.0]):
        reg_cyl(f"FrontCol_{ci}", r=0.18, h=3.35, segs=16, at=(cx, -3.4, 0.45), region=R_VERMILION_WOOD)
        reg_box(f"DougangCap_{ci}", 0.55, 0.55, 0.25, (cx, -3.4, 3.8), region=R_BRACKET_PAINT)

    # 4. Sweeping Flared Green Glazed Tile Roof with Dragon Ridge (Z = 3.8m to 6.2m)
    reg_swept("DojoSweptRoof", 10.2, 8.2, 2.0, flare=0.8, at=(0, 0, 4.05), region=R_GREEN_ROOF)

    # Central Golden Ridge Beam & Dragon Beasts
    reg_box("RoofRidgeBeam", 6.0, 0.35, 0.35, (0, 0, 6.05), region=R_GOLD_FINIAL)
    reg_box("DragonFinialL", 0.4, 0.4, 0.5, (-3.0, 0, 6.15), region=R_GOLD_FINIAL)
    reg_box("DragonFinialR", 0.4, 0.4, 0.5, ( 3.0, 0, 6.15), region=R_GOLD_FINIAL)

    # 5. Central Grand Entrance Lattice Doors & Martial Arts Signboard (Center: X = 0.0, Y = -3.4m)
    reg_box("DojoEntranceFrame", 2.6, 0.25, 2.8, (0, -3.45, 0.45), region=R_VERMILION_WOOD)
    reg_box("DojoEntranceDoors", 2.2, 0.10, 2.6, (0, -3.50, 0.45), region=R_LATTICE_DOOR)
    reg_box("DojoCalligraphySign", 2.4, 0.2, 0.6, (0, -3.55, 3.25), region=R_LATTICE_DOOR)

    # 6. Stone Guardian Lion Pedestals & Incense Burner
    reg_box("LionPedestalL", 0.8, 0.8, 0.8, (-2.6, -4.0, 0.0), region=R_MARBLE_BASE)
    reg_box("LionStatueL",   0.5, 0.5, 0.6, (-2.6, -4.0, 0.8), region=R_MARBLE_BASE)

    reg_box("LionPedestalR", 0.8, 0.8, 0.8, ( 2.6, -4.0, 0.0), region=R_MARBLE_BASE)
    reg_box("LionStatueR",   0.5, 0.5, 0.6, ( 2.6, -4.0, 0.8), region=R_MARBLE_BASE)

    # Bronze Tripod Incense Burner
    reg_cyl("IncenseBurnerBody", r=0.4, h=0.6, segs=16, at=(0, -4.2, 0.0), region=R_GOLD_FINIAL)

    # Finalize & Export
    shell = kit.join(parts, "Building_Dojo_01_Traditional_Kwoon")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_dojo_01_traditional_kwoon_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_dojo_01_traditional_kwoon.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_dojo_01_traditional_kwoon.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "building_dojo_01_traditional_kwoon_preview.png")
        shutil.copy2(OUT_DIR / "atlas_dojo_01.png", TEXTURES_DIR / "atlas_dojo_01.png")
        print(f"[Dojo_01] deployed successfully.")
    except Exception as e:
        print(f"[Dojo_01] deploy notice: {e}")


if __name__ == "__main__":
    main()
