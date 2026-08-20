"""Tiananmen Gate (天安门城楼) - East York Landmark (~3500 Tris).

Specs:
- Clean imperial fortress gate structure without surrounding square/plaza ground slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - Massive sloping crimson red fortress bastion base with 5 arched carriage passageway portals.
  - White marble balustrade surrounding the upper podium terrace.
  - Imperial wooden gatehouse pavilion with 12 vermilion lacquer columns and lattice doors.
  - Double-eaved imperial yellow glazed ceramic tile hip-and-gable roof (Xieshan roof) with sweeping eaves.
  - Central portrait frame plaque, carved timber dougong brackets, and gilded ridge beasts (chiwen).
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_tiananmen_gate.glb.
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
R_CRIMSON_WALL   = (0,   256, 256, 256)   # Deep crimson red plaster on the sloping fortress base
R_YELLOW_EAVE    = (256, 256, 256, 256)   # Imperial yellow glazed ceramic tile roof & ridge beasts
R_WHITE_MARBLE   = (0,   128, 128, 128)   # White marble terrace balustrades & bridge pillars
R_ARCHED_PORTAL  = (128, 128, 128, 128)   # 5 Arched carriage passageways & central national plaque
R_DOUGONG_TIMBER = (256, 128, 128, 128)   # Dougang brackets with gold/blue/green Qingdai paint
R_GOLD_TRIM      = (384, 128, 128, 128)   # Gilded ridge dragons, lanterns & golden column bases


def paint_atlas():
    a = Atlas(S, seed=1417)

    # 1. Crimson Fortress Wall (R_CRIMSON_WALL)
    x, y, w, h = R_CRIMSON_WALL
    a.rect(x, y, w, h, (0.68, 0.14, 0.12))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.52, 0.10, 0.08))
    a.noise(x, y, w, h, 0.015)

    # 2. Yellow Glazed Roof Tiles (R_YELLOW_EAVE)
    x, y, w, h = R_YELLOW_EAVE
    a.rect(x, y, w, h, (0.96, 0.78, 0.12))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.82, 0.64, 0.08))
        for rx in range(x + (ry % 20), x + w, 20):
            a.rect(rx, ry, 2, 10, (0.88, 0.70, 0.10))
    a.noise(x, y, w, h, 0.012)

    # 3. White Marble (R_WHITE_MARBLE)
    x, y, w, h = R_WHITE_MARBLE
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.78, 0.80, 0.82))
    a.noise(x, y, w, h, 0.015)

    # 4. Arched Portals & Plaque (R_ARCHED_PORTAL)
    x, y, w, h = R_ARCHED_PORTAL
    a.rect(x, y, w, h, (0.65, 0.12, 0.10))
    cx, cy = x + w // 2, y + h // 2
    # National Emblazoned Central Plaque
    a.rect(cx - 24, cy - 14, 48, 28, (0.88, 0.15, 0.15))
    a.rect(cx - 22, cy - 12, 44, 24, (0.95, 0.82, 0.22))
    # Arched portal tunnel shadow
    a.rect(x + 10, y + 4, 30, 40, (0.12, 0.08, 0.08))
    a.disc(x + 25, y + 44, 15, (0.12, 0.08, 0.08))
    a.noise(x, y, w, h, 0.01)

    # 5. Dougang Brackets (R_DOUGONG_TIMBER)
    x, y, w, h = R_DOUGONG_TIMBER
    a.rect(x, y, w, h, (0.16, 0.48, 0.42))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.90, 0.78, 0.20))
    a.noise(x, y, w, h, 0.015)

    # 6. Gilded Gold Trim (R_GOLD_TRIM)
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, (0.94, 0.80, 0.22))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_tiananmen_gate", OUT_DIR)


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
    """Creates sweeping Chinese curved roof with upturned eaves."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hbw, hbd = (bw / 2) + flare, (bd / 2) + flare
    htw, htd = tw / 2, td / 2

    v0 = bm.verts.new((-hbw, -hbd, 0.35))
    v1 = bm.verts.new(( hbw, -hbd, 0.35))
    v2 = bm.verts.new(( hbw,  hbd, 0.35))
    v3 = bm.verts.new((-hbw,  hbd, 0.35))

    v01 = bm.verts.new((0, -hbd * 0.92, 0.0))
    v12 = bm.verts.new((hbw * 0.92, 0, 0.0))
    v23 = bm.verts.new((0,  hbd * 0.92, 0.0))
    v30 = bm.verts.new((-hbw * 0.92, 0, 0.0))

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
    mat = material_for(img, "mat_tiananmen_gate")

    parts = []

    def reg_box(name, w, d, h, at, region=R_CRIMSON_WALL):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_CRIMSON_WALL):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # TIANANMEN GATE (BUILDING ONLY - ~3500 TRIS)
    # Width: 24.0m, Depth: 10.0m, Height: 15.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Sloping Crimson Fortress Base Bastion (Z = 0.0 to 5.5m)
    reg_box("FortressBaseBastion", 24.0, 9.5, 5.5, (0, 0, 0.0), region=R_CRIMSON_WALL)

    # 5 Arched Carriage Portals along Front Facade (sits at Z = 0.0)
    portal_specs = [
        # (Index, X, Width, Height)
        (0, -6.4, 1.6, 3.2),
        (1, -3.2, 1.8, 3.5),
        (2,  0.0, 2.4, 4.0),  # Central Imperial Archway
        (3,  3.2, 1.8, 3.5),
        (4,  6.4, 1.6, 3.2),
    ]

    for pi, px, pw, ph in portal_specs:
        arch = kit.make_box(f"ArchedPortal_{pi}", pw, 1.2, ph, (px, -4.8, 0.0))
        arch.data.materials.append(mat)
        kit.map_faces_to_region(arch, R_ARCHED_PORTAL, S)
        parts.append(arch)

    # Central National Plaque Frame above Central Arch
    reg_box("NationalPlaque", 2.2, 0.2, 2.6, (0, -4.85, 3.8), region=R_ARCHED_PORTAL)

    # 2. White Marble Podium Balustrade on Fortress Roof (Z = 5.5m)
    reg_box("PodiumBalustradeBase", 24.4, 9.8, 0.4, (0, 0, 5.5), region=R_WHITE_MARBLE)
    for bi in range(24):
        bx = -11.5 + bi * 1.0
        reg_box(f"MarbleBalusterFront_{bi}", 0.12, 0.12, 0.6, (bx, -4.8, 5.9), region=R_WHITE_MARBLE)
        reg_box(f"MarbleBalusterBack_{bi}", 0.12, 0.12, 0.6, (bx,  4.8, 5.9), region=R_WHITE_MARBLE)

    # 3. Imperial Wooden Gatehouse Pavilion (Z = 5.9m to 9.2m)
    reg_box("GatehousePavilionCore", 17.5, 6.5, 3.3, (0, 0, 5.9), region=R_CRIMSON_WALL)

    # 12 Vermilion Red Lacquer Columns (Front: 6 columns, Back: 6 columns)
    for ci in range(6):
        cx = -7.5 + ci * 3.0
        reg_cyl(f"GateCol_F_{ci}", r=0.24, h=3.3, segs=16, at=(cx, -3.4, 5.9), region=R_CRIMSON_WALL)
        reg_cyl(f"GateCol_B_{ci}", r=0.24, h=3.3, segs=16, at=(cx,  3.4, 5.9), region=R_CRIMSON_WALL)

    # 4. Lower Eave & Dougang Bracket Cluster Tier (Z = 9.2m to 10.8m)
    reg_box("LowerDougangBeam", 19.0, 8.0, 0.5, (0, 0, 9.2), region=R_DOUGONG_TIMBER)
    lower_roof = make_swept_roof("LowerSweptRoof", bw=20.5, bd=9.5, tw=16.5, td=5.5, height=1.4, flare=1.0, at=(0, 0, 9.7))
    lower_roof.data.materials.append(mat)
    kit.map_faces_to_region(lower_roof, R_YELLOW_EAVE, S)
    parts.append(lower_roof)

    # 5. Upper Pavilion Drum & Upper Dougang Tier (Z = 11.1m to 12.2m)
    reg_box("UpperPavilionDrum", 15.0, 5.2, 1.1, (0, 0, 11.1), region=R_CRIMSON_WALL)
    reg_box("UpperDougangBeam", 16.0, 6.2, 0.5, (0, 0, 12.2), region=R_DOUGONG_TIMBER)

    # 6. Upper Imperial Double-Eaved Xieshan Hip-and-Gable Roof (Z = 12.7m to 15.8m)
    upper_roof = make_swept_roof("UpperXieshanRoof", bw=18.5, bd=8.2, tw=10.0, td=1.5, height=3.0, flare=1.2, at=(0, 0, 12.7))
    upper_roof.data.materials.append(mat)
    kit.map_faces_to_region(upper_roof, R_YELLOW_EAVE, S)
    parts.append(upper_roof)

    # Main Ridge Beam & Chiwen Beasts
    reg_box("MainRidgeBeam", 10.2, 0.4, 0.5, (0, 0, 15.6), region=R_GOLD_TRIM)
    reg_box("Chiwen_E", 0.5, 0.6, 0.9, ( 5.1, 0, 15.7), region=R_GOLD_TRIM)
    reg_box("Chiwen_W", 0.5, 0.6, 0.9, (-5.1, 0, 15.7), region=R_GOLD_TRIM)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Tiananmen_Gate")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_tiananmen_gate_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_tiananmen_gate.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_tiananmen_gate.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_tiananmen_gate_preview.png")
        shutil.copy2(OUT_DIR / "atlas_tiananmen_gate.png", TEXTURES_DIR / "atlas_tiananmen_gate.png")
        print(f"[TiananmenGate] deployed successfully.")
    except Exception as e:
        print(f"[TiananmenGate] deploy notice: {e}")


if __name__ == "__main__":
    main()
