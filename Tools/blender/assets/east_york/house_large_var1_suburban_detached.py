"""West York Large Home - Variant 1: Suburban Detached Villa (~880 Tris).

Specs:
- Footprint: 10.5m wide x 9.0m deep, Height: 7.8m. Sits directly at Z = 0.0.
- Features:
  - 2-storey asymmetric detached family home with red brick base & cream render first floor.
  - Projecting double-height front gable wing with bay window.
  - Integrated garage wing with panelled up-and-over garage door.
  - Recessed covered front entrance porch with panelled timber door.
  - Pitched slate roof with gables and brick chimney stack with ceramic pots.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/house_large_01_suburban_detached.glb.
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
R_BRICK_RENDER   = (0,   256, 256, 256)   # Red brick ground floor & warm cream roughcast render
R_SLATE_ROOF     = (256, 256, 256, 256)   # Dark grey Welsh slate roof tiles
R_LARGE_WINDOWS  = (0,   128, 128, 128)   # White double-glazed UPVC casement windows
R_GARAGE_DOOR    = (128, 128, 128, 128)   # White ribbed up-and-over garage door
R_OAK_FRONT_DOOR = (256, 128, 128, 128)   # Oak panelled front entrance door & porch timber
R_CHIMNEY_POTS   = (384, 128, 128, 128)   # Terracotta chimney pots & concrete caps


def paint_atlas():
    a = Atlas(S, seed=1955)

    # 1. Brick / Render (R_BRICK_RENDER)
    x, y, w, h = R_BRICK_RENDER
    # Ground floor brick
    a.bricks(x, y, w, h // 2, brick=(0.60, 0.22, 0.16), mortar=(0.76, 0.74, 0.70), bw=20, bh=8, jitter=0.06)
    # First floor cream render
    a.rect(x, y + h // 2, w, h // 2, (0.88, 0.85, 0.78))
    for ry in range(y + h // 2, y + h, 30):
        a.rect(x, ry, w, 2, (0.75, 0.72, 0.65))
    a.noise(x, y, w, h, 0.02)

    # 2. Slate Roof (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, (0.28, 0.30, 0.34))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 3. Large Windows (R_LARGE_WINDOWS)
    x, y, w, h = R_LARGE_WINDOWS
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for wy in range(y + 6, y + h - 10, 24):
        a.rect(x + 6, wy, w - 12, 18, (0.18, 0.28, 0.38))
        a.rect(x + w // 2 - 2, wy, 4, 18, (0.92, 0.93, 0.94))
    a.noise(x, y, w, h, 0.01)

    # 4. Garage Door (R_GARAGE_DOOR)
    x, y, w, h = R_GARAGE_DOOR
    a.rect(x, y, w, h, (0.90, 0.91, 0.92))
    for ry in range(y + 8, y + h - 8, 12):
        a.rect(x + 6, ry, w - 12, 2, (0.45, 0.46, 0.48))
    a.rect(x + w // 2 - 4, y + 20, 8, 4, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.01)

    # 5. Oak Front Door (R_OAK_FRONT_DOOR)
    x, y, w, h = R_OAK_FRONT_DOOR
    a.rect(x, y, w, h, (0.45, 0.28, 0.16))
    a.rect(x + 8, y + 8, w - 16, 16, (0.85, 0.72, 0.25))
    a.disc(x + w // 2, y + 44, 4, (0.85, 0.72, 0.25))
    a.noise(x, y, w, h, 0.01)

    # 6. Chimney Pots (R_CHIMNEY_POTS)
    x, y, w, h = R_CHIMNEY_POTS
    a.rect(x, y, w, h, (0.68, 0.32, 0.18))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.48, 0.20, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_large_house_01", OUT_DIR)


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


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_large_house_01")

    parts = []

    def reg_box(name, w, d, h, at, region=R_BRICK_RENDER):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_ROOF):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_CHIMNEY_POTS):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK LARGE HOME 01: SUBURBAN DETACHED VILLA (~880 TRIS)
    # Footprint: 10.5m x 9.0m, Height: 7.8m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main 2-Storey House Body (Left & Center: X = -5.0 to 1.5m, Width: 6.5m, Depth: 8.5m)
    reg_box("MainHouseBody", 6.5, 8.5, 5.4, (-1.75, 0.0, 0.0), region=R_BRICK_RENDER)
    reg_pyr("MainHouseRoof", 6.9, 8.9, 2.4, (-1.75, 0.0, 5.4), region=R_SLATE_ROOF)

    # 2. Projecting Front Gable Wing with Double-Height Bay Window (X = -3.2m, Y = -4.2m)
    reg_box("FrontGableWing", 3.4, 1.8, 5.4, (-3.2, -4.2, 0.0), region=R_BRICK_RENDER)
    reg_pyr("FrontGableRoof", 3.8, 2.2, 1.8, (-3.2, -4.2, 5.4), region=R_SLATE_ROOF)

    # Ground & First Floor Bay Windows on Front Gable
    reg_box("BayWinGround", 2.2, 0.4, 2.0, (-3.2, -5.2, 0.4), region=R_LARGE_WINDOWS)
    reg_box("BayWinUpper",  2.2, 0.4, 1.8, (-3.2, -5.2, 3.0), region=R_LARGE_WINDOWS)

    # 3. Integrated Garage Wing (Right side: X = 1.5 to 5.2m, Width: 3.7m, Depth: 6.5m, Height: 3.5m)
    reg_box("GarageWingBody", 3.7, 6.5, 3.4, (3.35, -0.5, 0.0), region=R_BRICK_RENDER)
    reg_pyr("GarageWingRoof", 4.1, 6.9, 1.6, (3.35, -0.5, 3.4), region=R_SLATE_ROOF)

    # Ribbed Garage Door (Front of Garage at Y = -3.7m)
    reg_box("GarageDoorFrame", 2.8, 0.25, 2.6, (3.35, -3.8, 0.0), region=R_BRICK_RENDER)
    reg_box("GarageDoorLeaf",  2.5, 0.10, 2.4, (3.35, -3.85, 0.0), region=R_GARAGE_DOOR)

    # 4. Covered Front Entrance Porch & Oak Door (Between Gable and Garage: X = -0.4m, Y = -4.2m)
    reg_box("EntrancePorchBase", 1.8, 0.8, 0.15, (-0.4, -4.4, 0.0), region=R_BRICK_RENDER)
    reg_box("EntranceDoorFrame", 1.4, 0.25, 2.5, (-0.4, -4.25, 0.15), region=R_BRICK_RENDER)
    reg_box("EntranceDoorLeaf",  1.1, 0.10, 2.3, (-0.4, -4.28, 0.15), region=R_OAK_FRONT_DOOR)
    reg_pyr("EntrancePorchRoof", 2.0, 1.2, 0.8, (-0.4, -4.4, 2.8), region=R_SLATE_ROOF)

    # 5. Additional Upper Floor Casement Windows
    reg_box("UpperWinRight", 1.6, 0.15, 1.5, (-0.4, -4.25, 3.2), region=R_LARGE_WINDOWS)

    # 6. Side Chimney Stack & Pots
    reg_box("SideChimneyStack", 1.0, 1.4, 2.2, (-4.8, 0.5, 5.6), region=R_BRICK_RENDER)
    reg_cyl("SideChimneyPot1", r=0.18, h=0.6, segs=16, at=(-4.8, 0.1, 7.8), region=R_CHIMNEY_POTS)
    reg_cyl("SideChimneyPot2", r=0.18, h=0.6, segs=16, at=(-4.8, 0.9, 7.8), region=R_CHIMNEY_POTS)

    # Finalize & Export
    shell = kit.join(parts, "House_Large_01_Suburban_Detached")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_large_01_suburban_detached_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_large_01_suburban_detached.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_large_01_suburban_detached.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_large_01_suburban_detached_preview.png")
        shutil.copy2(OUT_DIR / "atlas_large_house_01.png", TEXTURES_DIR / "atlas_large_house_01.png")
        print(f"[House_Large_01] deployed successfully.")
    except Exception as e:
        print(f"[House_Large_01] deploy notice: {e}")


if __name__ == "__main__":
    main()
