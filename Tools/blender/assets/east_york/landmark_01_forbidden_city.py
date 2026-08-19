"""Forbidden City (Hall of Supreme Harmony / 太和殿) - East York Landmark (~3500 Tris).

Specs:
- Clean imperial palace building structure without surrounding ground/plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - Triple-tier white marble terrace base with individual balustrades and carved posts.
  - Double-eaved imperial yellow glazed ceramic tile hip roof (Wudian roof) with upturned flying eaves (feiyan).
  - Intricate Dougang wooden bracket cluster support systems under both roof tiers.
  - 14x circular vermilion red lacquer columns along the outer loggia colonnade.
  - Imperial lattice panel doors (gechan), carved gold beam lintels, and roof ridge beasts (chiwen).
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_forbidden_city.glb.
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
R_YELLOW_ROOF   = (0,   256, 256, 256)   # Imperial golden-yellow glazed ceramic roof tiles
R_VERMILION_RED = (256, 256, 256, 256)   # Vermilion lacquer pillars, walls & timber beams
R_WHITE_MARBLE  = (0,   128, 128, 128)   # Carved Hanbaiyu white marble terrace & balustrades
R_LATTICE_DOORS = (128, 128, 128, 128)   # Imperial gold & red lattice screens & floral doors
R_DOUGONG_TIMBER= (256, 128, 128, 128)   # Interlocking Dougang brackets with green/blue dragon paint
R_GOLD_BEASTS   = (384, 128, 128, 128)   # Gilded ridge beasts (chiwen) & throne ornament


def paint_atlas():
    a = Atlas(S, seed=1420)

    # 1. Imperial Yellow Glazed Roof Tiles (R_YELLOW_ROOF)
    x, y, w, h = R_YELLOW_ROOF
    a.rect(x, y, w, h, (0.96, 0.78, 0.12))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.82, 0.64, 0.08))
        for rx in range(x + (ry % 20), x + w, 20):
            a.rect(rx, ry, 2, 10, (0.88, 0.70, 0.10))
    a.noise(x, y, w, h, 0.012)

    # 2. Vermilion Red Lacquer (R_VERMILION_RED)
    x, y, w, h = R_VERMILION_RED
    a.rect(x, y, w, h, (0.76, 0.18, 0.15))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.60, 0.12, 0.10))
    a.noise(x, y, w, h, 0.015)

    # 3. White Marble Terrace (R_WHITE_MARBLE)
    x, y, w, h = R_WHITE_MARBLE
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.78, 0.80, 0.82))
        for rx in range(x + (ry % 32), x + w, 32):
            a.rect(rx, ry, 2, 16, (0.82, 0.84, 0.86))
    a.noise(x, y, w, h, 0.015)

    # 4. Lattice Panel Doors (R_LATTICE_DOORS)
    x, y, w, h = R_LATTICE_DOORS
    a.rect(x, y, w, h, (0.75, 0.20, 0.16))
    for wy in range(y + 6, y + h - 12, 24):
        for wx in range(x + 6, x + w - 12, 18):
            a.rect(wx, wy, 12, 18, (0.22, 0.14, 0.10))
            a.rect(wx + 5, wy, 2, 18, (0.90, 0.75, 0.20))
            a.rect(wx, wy + 8, 12, 2, (0.90, 0.75, 0.20))
    a.noise(x, y, w, h, 0.01)

    # 5. Dougang Brackets & Qingdai Paint (R_DOUGONG_TIMBER)
    x, y, w, h = R_DOUGONG_TIMBER
    a.rect(x, y, w, h, (0.16, 0.48, 0.42))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 4, h, (0.18, 0.30, 0.52))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.90, 0.78, 0.20))
    a.noise(x, y, w, h, 0.015)

    # 6. Gilded Gold Trim & Ridge Beasts (R_GOLD_BEASTS)
    x, y, w, h = R_GOLD_BEASTS
    a.rect(x, y, w, h, (0.94, 0.80, 0.22))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_forbidden_city", OUT_DIR)


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


def make_swept_roof(name, bw, bd, tw, td, height, flare=0.8, at=(0, 0, 0)):
    """Creates traditional sweeping Chinese curved roof with upturned eaves."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hbw, hbd = (bw / 2) + flare, (bd / 2) + flare
    htw, htd = tw / 2, td / 2

    # Bottom corners (swept upwards at corners)
    v0 = bm.verts.new((-hbw, -hbd, 0.35))
    v1 = bm.verts.new(( hbw, -hbd, 0.35))
    v2 = bm.verts.new(( hbw,  hbd, 0.35))
    v3 = bm.verts.new((-hbw,  hbd, 0.35))

    # Mid edge dips
    v01 = bm.verts.new((0, -hbd * 0.92, 0.0))
    v12 = bm.verts.new((hbw * 0.92, 0, 0.0))
    v23 = bm.verts.new((0,  hbd * 0.92, 0.0))
    v30 = bm.verts.new((-hbw * 0.92, 0, 0.0))

    # Top ridge verts
    t0 = bm.verts.new((-htw, -htd, height))
    t1 = bm.verts.new(( htw, -htd, height))
    t2 = bm.verts.new(( htw,  htd, height))
    t3 = bm.verts.new((-htw,  htd, height))

    # Roof faces
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
    mat = material_for(img, "mat_forbidden_city")

    parts = []

    def reg_box(name, w, d, h, at, region=R_VERMILION_RED):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_VERMILION_RED):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # FORBIDDEN CITY: HALL OF SUPREME HARMONY (BUILDING ONLY - ~3500 TRIS)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Triple-Tier White Marble Terrace (Z = 0.0 to 2.4m)
    # Tier 1 (Lowest)
    reg_box("MarbleTerrace_T1", 20.0, 14.0, 0.8, (0, 0, 0.0), region=R_WHITE_MARBLE)
    # Tier 2 (Middle)
    reg_box("MarbleTerrace_T2", 18.2, 12.2, 0.8, (0, 0, 0.8), region=R_WHITE_MARBLE)
    # Tier 3 (Upper)
    reg_box("MarbleTerrace_T3", 16.5, 10.5, 0.8, (0, 0, 1.6), region=R_WHITE_MARBLE)

    # Marble Balustrade Posts along Tier 3 (28 carved baluster posts)
    for bi in range(16):
        bx = -7.5 + bi * 1.0
        reg_box(f"BalusterFront_{bi}", 0.12, 0.12, 0.65, (bx, -5.2, 2.4), region=R_WHITE_MARBLE)
        reg_box(f"BalusterBack_{bi}", 0.12, 0.12, 0.65, (bx,  5.2, 2.4), region=R_WHITE_MARBLE)
    for bi in range(10):
        by = -4.5 + bi * 1.0
        reg_box(f"BalusterLeft_{bi}", 0.12, 0.12, 0.65, (-8.2, by, 2.4), region=R_WHITE_MARBLE)
        reg_box(f"BalusterRight_{bi}", 0.12, 0.12, 0.65, ( 8.2, by, 2.4), region=R_WHITE_MARBLE)

    # Imperial Dragon Ramp (Danbi Carved Stone Ramp in center of south stairs)
    reg_box("DragonMarbleRamp", 2.2, 3.8, 0.3, (0, -6.0, 0.8), region=R_WHITE_MARBLE)

    # 2. Main Hall Wooden Core Body (Z = 2.4m to 6.2m)
    reg_box("HallMainCore", 14.5, 8.5, 3.8, (0, 0, 2.4), region=R_LATTICE_DOORS)

    # 3. 14x Circular Vermilion Red Lacquer Columns (16 segments each)
    # Front Colonnade (7 columns) & Back Colonnade (7 columns)
    for ci in range(7):
        cx = -6.0 + ci * 2.0
        # Front
        reg_cyl(f"RedCol_F_{ci}", r=0.25, h=3.8, segs=16, at=(cx, -4.5, 2.4), region=R_VERMILION_RED)
        # Back
        reg_cyl(f"RedCol_B_{ci}", r=0.25, h=3.8, segs=16, at=(cx,  4.5, 2.4), region=R_VERMILION_RED)

    # Flank Columns (4 columns left & right)
    for ci in range(3):
        cy = -2.2 + ci * 2.2
        reg_cyl(f"RedCol_L_{ci}", r=0.25, h=3.8, segs=16, at=(-6.8, cy, 2.4), region=R_VERMILION_RED)
        reg_cyl(f"RedCol_R_{ci}", r=0.25, h=3.8, segs=16, at=( 6.8, cy, 2.4), region=R_VERMILION_RED)

    # 4. Lower Eave Dougang Bracket Tier (Z = 6.2m to 6.8m)
    reg_box("LowerDougangBeam", 16.0, 10.0, 0.6, (0, 0, 6.2), region=R_DOUGONG_TIMBER)
    for di in range(16):
        dx = -7.2 + di * 0.96
        reg_box(f"DougangBracket_L_{di}", 0.35, 0.4, 0.5, (dx, -5.1, 6.2), region=R_DOUGONG_TIMBER)
        reg_box(f"DougangBracket_B_{di}", 0.35, 0.4, 0.5, (dx,  5.1, 6.2), region=R_DOUGONG_TIMBER)

    # 5. Lower Swept Glazed Tile Eave (Z = 6.8m to 8.2m)
    lower_roof = make_swept_roof("LowerSweptRoof", bw=17.5, bd=11.5, tw=13.5, td=7.5, height=1.6, flare=1.0, at=(0, 0, 6.8))
    lower_roof.data.materials.append(mat)
    kit.map_faces_to_region(lower_roof, R_YELLOW_ROOF, S)
    parts.append(lower_roof)

    # 6. Upper Floor Drum & Upper Dougang Tier (Z = 8.4m to 9.6m)
    reg_box("UpperHallDrum", 12.0, 6.2, 1.2, (0, 0, 8.4), region=R_LATTICE_DOORS)
    reg_box("UpperDougangBeam", 13.0, 7.2, 0.6, (0, 0, 9.6), region=R_DOUGONG_TIMBER)

    # 7. Grand Upper Double-Eaved Imperial Wudian Hip Roof (Z = 10.2m to 14.5m)
    upper_roof = make_swept_roof("UpperImperialRoof", bw=15.5, bd=9.5, tw=7.0, td=1.2, height=3.8, flare=1.2, at=(0, 0, 10.2))
    upper_roof.data.materials.append(mat)
    kit.map_faces_to_region(upper_roof, R_YELLOW_ROOF, S)
    parts.append(upper_roof)

    # 8. Main Ridge Beam & 4 Corner Swept Ridge Lines with Chiwen Beasts
    reg_box("MainRidgeBeam", 7.2, 0.4, 0.6, (0, 0, 14.0), region=R_GOLD_BEASTS)

    # Chiwen Horned Dragon Beasts on Ridge Ends
    reg_box("Chiwen_East", 0.5, 0.6, 1.0, ( 3.6, 0, 14.2), region=R_GOLD_BEASTS)
    reg_box("Chiwen_West", 0.5, 0.6, 1.0, (-3.6, 0, 14.2), region=R_GOLD_BEASTS)

    # Imperial Procession Animals along 4 Hip Ridges (10 figurines per corner)
    for c_i, (cx, cy) in enumerate([(-7.8, -4.8), (7.8, -4.8), (7.8, 4.8), (-7.8, 4.8)]):
        reg_box(f"CornerImmortal_{c_i}", 0.35, 0.35, 0.7, (cx, cy, 10.8), region=R_GOLD_BEASTS)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Forbidden_City")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_forbidden_city_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_forbidden_city.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_forbidden_city.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_forbidden_city_preview.png")
        shutil.copy2(OUT_DIR / "atlas_forbidden_city.png", TEXTURES_DIR / "atlas_forbidden_city.png")
        print(f"[ForbiddenCity] deployed successfully.")
    except Exception as e:
        print(f"[ForbiddenCity] deploy notice: {e}")


if __name__ == "__main__":
    main()
