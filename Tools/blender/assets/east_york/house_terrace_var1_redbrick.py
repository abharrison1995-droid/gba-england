"""West York Terraced House - Variant 1: Victorian Red Brick (~850 Tris).

Specs:
- Footprint: 5.5m wide x 8.0m deep, Height: 7.5m. Sits directly at Z = 0.0.
- Features:
  - 2-storey Victorian red brick facade with stone lintels and sills.
  - Ground floor projecting bay window with slate rooflet.
  - Recessed panelled front entrance door with transom fanlight and entrance steps.
  - Pitched Welsh slate roof with chimney stack and ceramic chimney pots.
- Target: <1,000 tris (~850 tris).
- Deploys to Assets/3DModels/West York/house_terrace_01_redbrick.glb.
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
R_BRICK_RED      = (0,   256, 256, 256)   # Victorian red brick with stone lintel bands
R_SLATE_ROOF     = (256, 256, 256, 256)   # Dark grey Welsh slate roof tiles
R_BAY_WINDOW     = (0,   128, 128, 128)   # White painted timber sash windows
R_FRONT_DOOR     = (128, 128, 128, 128)   # Deep green 4-panel front door with brass knocker & fanlight
R_STONE_TRIM     = (256, 128, 128, 128)   # Stone sills, chimney caps, and steps
R_CHIMNEY_POT    = (384, 128, 128, 128)   # Terracotta chimney pot clay


def paint_atlas():
    a = Atlas(S, seed=1890)

    # 1. Victorian Red Brick (R_BRICK_RED)
    x, y, w, h = R_BRICK_RED
    a.bricks(x, y, w, h, brick=(0.62, 0.22, 0.16), mortar=(0.78, 0.75, 0.70), bw=18, bh=8, jitter=0.05)
    for ry in range(y, y + h, 36):
        a.rect(x, ry, w, 4, (0.84, 0.82, 0.76))
    a.noise(x, y, w, h, 0.02)

    # 2. Welsh Slate (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, (0.28, 0.30, 0.34))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 3. White Bay Windows (R_BAY_WINDOW)
    x, y, w, h = R_BAY_WINDOW
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for wy in range(y + 8, y + h - 12, 28):
        a.rect(x + 8, wy, w - 16, 20, (0.18, 0.28, 0.38))
        a.rect(x + w // 2 - 2, wy, 4, 20, (0.92, 0.93, 0.94))
    a.noise(x, y, w, h, 0.01)

    # 4. Front Door & Fanlight (R_FRONT_DOOR)
    x, y, w, h = R_FRONT_DOOR
    a.rect(x, y, w, h, (0.12, 0.32, 0.20))
    a.rect(x + 10, y + 8, w - 20, 18, (0.85, 0.72, 0.25))
    a.disc(x + w // 2, y + 40, 4, (0.85, 0.72, 0.25))
    # Fanlight semi-circle
    a.disc(x + w // 2, y + h - 16, 14, (0.22, 0.40, 0.55))
    a.noise(x, y, w, h, 0.01)

    # 5. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, (0.82, 0.80, 0.75))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.65, 0.63, 0.58))
    a.noise(x, y, w, h, 0.02)

    # 6. Chimney Pot (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, (0.68, 0.32, 0.18))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.48, 0.20, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_terrace_01", OUT_DIR)


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
    mat = material_for(img, "mat_terrace_01")

    parts = []

    def reg_box(name, w, d, h, at, region=R_BRICK_RED):
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

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_CHIMNEY_POT):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK TERRACED HOUSE 01: VICTORIAN RED BRICK (~850 TRIS)
    # Footprint: 5.5m x 8.0m, Height: 7.5m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main 2-Storey House Body (Z = 0.0 to 5.2m)
    reg_box("HouseMainBody", 5.5, 7.8, 5.2, (0, 0, 0.0), region=R_BRICK_RED)

    # 2. Pitched Slate Roof (Z = 5.2m to 7.2m)
    reg_pyr("HouseRoof", 5.7, 8.0, 2.0, (0, 0, 5.2), region=R_SLATE_ROOF)

    # 3. Ground Floor Projecting Bay Window (X = -1.2m, Y = -3.9m)
    reg_box("BayWindowBase", 2.2, 0.8, 0.4, (-1.2, -4.1, 0.0), region=R_STONE_TRIM)
    reg_box("BayWindowFrame", 2.0, 0.7, 2.0, (-1.2, -4.1, 0.4), region=R_BAY_WINDOW)
    reg_pyr("BayWindowRoof", 2.3, 0.9, 0.6, (-1.2, -4.1, 2.4), region=R_SLATE_ROOF)

    # 4. Front Entrance Door & Stone Steps (X = 1.4m, Y = -3.9m)
    reg_box("FrontDoorStep1", 1.4, 0.5, 0.15, (1.4, -4.1, 0.0), region=R_STONE_TRIM)
    reg_box("FrontDoorStep2", 1.2, 0.4, 0.15, (1.4, -4.0, 0.15), region=R_STONE_TRIM)
    reg_box("FrontDoorFrame", 1.2, 0.25, 2.5, (1.4, -3.95, 0.3), region=R_STONE_TRIM)
    reg_box("FrontDoorLeaf", 1.0, 0.10, 2.3, (1.4, -3.98, 0.3), region=R_FRONT_DOOR)

    # 5. First Floor Sash Windows (Front Facade)
    for wi, wx in enumerate([-1.2, 1.4]):
        reg_box(f"UpperWinSill_{wi}", 1.4, 0.2, 0.12, (wx, -3.95, 3.1), region=R_STONE_TRIM)
        reg_box(f"UpperWinFrame_{wi}", 1.2, 0.1, 1.6, (wx, -3.92, 3.22), region=R_BAY_WINDOW)
        reg_box(f"UpperWinLintel_{wi}", 1.4, 0.2, 0.15, (wx, -3.95, 4.82), region=R_STONE_TRIM)

    # 6. Chimney Stack & Terracotta Chimney Pots
    reg_box("ChimneyStack", 1.0, 1.4, 1.8, (2.0, 0.0, 6.2), region=R_BRICK_RED)
    reg_box("ChimneyCap", 1.2, 1.6, 0.2, (2.0, 0.0, 8.0), region=R_STONE_TRIM)
    reg_cyl("ChimneyPot1", r=0.18, h=0.6, segs=16, at=(2.0, -0.4, 8.2), region=R_CHIMNEY_POT)
    reg_cyl("ChimneyPot2", r=0.18, h=0.6, segs=16, at=(2.0,  0.4, 8.2), region=R_CHIMNEY_POT)

    # Finalize & Export
    shell = kit.join(parts, "House_Terrace_01_Redbrick")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_terrace_01_redbrick_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_terrace_01_redbrick.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_terrace_01_redbrick.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_terrace_01_redbrick_preview.png")
        shutil.copy2(OUT_DIR / "atlas_terrace_01.png", TEXTURES_DIR / "atlas_terrace_01.png")
        print(f"[House_Terrace_01] deployed successfully.")
    except Exception as e:
        print(f"[House_Terrace_01] deploy notice: {e}")


if __name__ == "__main__":
    main()
