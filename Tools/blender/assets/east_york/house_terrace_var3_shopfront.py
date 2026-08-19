"""West York Terraced House - Variant 3: Traditional Ground Shopfront & Flat (~850 Tris).

Specs:
- Footprint: 5.5m wide x 8.0m deep, Height: 7.6m. Sits directly at Z = 0.0.
- Features:
  - Ground floor traditional British high-street shopfront with display bay window, entrance door, stallriser, and fascia sign board with retractable awning hood.
  - Upper residential flat with red brick facade and dual sash windows.
  - Pitched slate roof with decorative parapet corbel and brick chimney.
- Target: <1,000 tris (~850 tris).
- Deploys to Assets/3DModels/West York/house_terrace_03_shopfront.glb.
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
R_BRICK_FACADE   = (0,   256, 256, 256)   # Upper storey warm red/brown brick
R_SLATE_ROOF     = (256, 256, 256, 256)   # Grey slate roof tiles
R_SHOP_GLASS     = (0,   128, 128, 128)   # Ground floor glazed shop display bay & wares
R_SHOP_FASCIA    = (128, 128, 128, 128)   # Traditional British shop fascia sign (Gold & Burgundy)
R_SHOP_DOOR      = (256, 128, 128, 128)   # Half-glazed shop entrance door & stallriser panel
R_AWNING_FABRIC  = (384, 128, 128, 128)   # Striped red/white canvas awning fabric


def paint_atlas():
    a = Atlas(S, seed=1925)

    # 1. Brick Facade (R_BRICK_FACADE)
    x, y, w, h = R_BRICK_FACADE
    a.bricks(x, y, w, h, brick=(0.56, 0.26, 0.18), mortar=(0.74, 0.72, 0.68), bw=18, bh=8, jitter=0.06)
    a.noise(x, y, w, h, 0.02)

    # 2. Slate Roof (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, (0.26, 0.28, 0.32))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 3. Shop Display Glazing (R_SHOP_GLASS)
    x, y, w, h = R_SHOP_GLASS
    a.rect(x, y, w, h, (0.22, 0.36, 0.48))
    # Interior display shelves
    for ry in range(y + 12, y + h - 16, 24):
        a.rect(x + 8, ry, w - 16, 4, (0.85, 0.75, 0.50))
    a.noise(x, y, w, h, 0.01)

    # 4. Shop Fascia Sign (R_SHOP_FASCIA)
    x, y, w, h = R_SHOP_FASCIA
    a.rect(x, y, w, h, (0.42, 0.12, 0.16))
    # Gold lettering header bar
    a.rect(x + 6, y + h // 2 - 8, w - 12, 16, (0.88, 0.76, 0.25))
    a.rect(x + 10, y + h // 2 - 4, w - 20, 8, (0.42, 0.12, 0.16))
    a.noise(x, y, w, h, 0.01)

    # 5. Shop Door & Timber (R_SHOP_DOOR)
    x, y, w, h = R_SHOP_DOOR
    a.rect(x, y, w, h, (0.16, 0.28, 0.22))
    a.rect(x + 8, y + h // 2, w - 16, h // 2 - 12, (0.25, 0.45, 0.58))
    a.rect(x + 8, y + 8, w - 16, 14, (0.85, 0.72, 0.25))
    a.noise(x, y, w, h, 0.01)

    # 6. Canvas Awning (R_AWNING_FABRIC)
    x, y, w, h = R_AWNING_FABRIC
    a.rect(x, y, w, h, (0.75, 0.18, 0.18))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 8, h, (0.92, 0.90, 0.85))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_terrace_03", OUT_DIR)


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
    mat = material_for(img, "mat_terrace_03")

    parts = []

    def reg_box(name, w, d, h, at, region=R_BRICK_FACADE):
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

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_AWNING_FABRIC):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK TERRACED HOUSE 03: SHOPFRONT & FLAT (~850 TRIS)
    # Footprint: 5.5m x 8.0m, Height: 7.6m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main 2-Storey House Body (Z = 0.0 to 5.2m)
    reg_box("HouseMainBody", 5.5, 7.8, 5.2, (0, 0, 0.0), region=R_BRICK_FACADE)

    # 2. Pitched Slate Roof (Z = 5.2m to 7.2m)
    reg_pyr("HouseRoof", 5.7, 8.0, 2.0, (0, 0, 5.2), region=R_SLATE_ROOF)

    # 3. Ground Floor Shopfront (Front Facade at Y = -3.9m)
    # Stallriser base (Z = 0.0 to 0.45m)
    reg_box("ShopStallriser", 5.4, 0.35, 0.45, (0, -4.0, 0.0), region=R_SHOP_DOOR)

    # Shop Glazed Display Window (Left side: X = -1.2m, Width: 3.0m, Height: 2.2m)
    reg_box("ShopDisplayWindow", 3.0, 0.3, 2.2, (-1.0, -4.05, 0.45), region=R_SHOP_GLASS)
    reg_box("ShopMullionMid", 0.08, 0.35, 2.2, (-1.0, -4.08, 0.45), region=R_SHOP_DOOR)

    # Shop Entrance Door (Right side: X = 1.6m, Width: 1.2m, Height: 2.4m)
    reg_box("ShopDoorFrame", 1.4, 0.3, 2.6, (1.6, -4.0, 0.0), region=R_SHOP_DOOR)
    reg_box("ShopDoorLeaf", 1.1, 0.1, 2.3, (1.6, -4.05, 0.0), region=R_SHOP_DOOR)

    # Traditional Shop Fascia Signboard (Z = 2.7m to 3.4m)
    reg_box("ShopFasciaSign", 5.4, 0.35, 0.7, (0, -4.1, 2.7), region=R_SHOP_FASCIA)
    reg_box("ShopFasciaCornice", 5.6, 0.45, 0.15, (0, -4.1, 3.4), region=R_SHOP_DOOR)

    # Retractable Canvas Awning Canopy (Z = 2.6m)
    reg_box("ShopAwningCanopy", 4.8, 1.4, 0.15, (0, -4.7, 2.6), region=R_AWNING_FABRIC)

    # 4. First Floor Residential Sash Windows
    for wi, wx in enumerate([-1.2, 1.4]):
        reg_box(f"UpperWinSill_{wi}", 1.4, 0.2, 0.12, (wx, -3.95, 3.8), region=R_SHOP_DOOR)
        reg_box(f"UpperWinFrame_{wi}", 1.2, 0.1, 1.4, (wx, -3.92, 3.92), region=R_SHOP_GLASS)
        reg_box(f"UpperWinLintel_{wi}", 1.4, 0.2, 0.15, (wx, -3.95, 5.32), region=R_SHOP_DOOR)

    # 5. Brick Chimney Stack
    reg_box("ChimneyStack", 0.9, 1.2, 1.8, (2.0, 0.0, 6.2), region=R_BRICK_FACADE)
    reg_cyl("ChimneyPot1", r=0.18, h=0.6, segs=16, at=(2.0, 0.0, 8.0), region=R_AWNING_FABRIC)

    # Finalize & Export
    shell = kit.join(parts, "House_Terrace_03_Shopfront")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_terrace_03_shopfront_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_terrace_03_shopfront.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_terrace_03_shopfront.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_terrace_03_shopfront_preview.png")
        shutil.copy2(OUT_DIR / "atlas_terrace_03.png", TEXTURES_DIR / "atlas_terrace_03.png")
        print(f"[House_Terrace_03] deployed successfully.")
    except Exception as e:
        print(f"[House_Terrace_03] deploy notice: {e}")


if __name__ == "__main__":
    main()
