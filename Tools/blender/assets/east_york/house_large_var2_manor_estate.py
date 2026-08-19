"""West York Large Home - Variant 2: Grand Country Manor Estate (~880 Tris).

Specs:
- Footprint: 12.0m wide x 9.0m deep, Height: 8.2m. Sits directly at Z = 0.0.
- Features:
  - Symmetrical 2-storey Georgian country manor with Bath stone ashlar blocks and corner quoins.
  - Central neoclassical pediment portico with 4 Tuscan stone columns and grand double entrance doors.
  - Symmetrical flanking wings with 8 Georgian 12-pane sash windows and stone architraves.
  - Hipped slate roof with twin substantial stone chimney stacks and ceramic pots.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/house_large_02_manor_estate.glb.
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
R_MANOR_STONE    = (0,   256, 256, 256)   # Bath stone ashlar blocks & rusticated base
R_MANOR_SLATE    = (256, 256, 256, 256)   # Welsh dark grey slate roofing
R_GEORGIAN_WIN   = (0,   128, 128, 128)   # White Georgian 12-pane sash windows with stone hoods
R_MANOR_DOORS    = (128, 128, 128, 128)   # Double panelled oak manor entrance doors & brass handles
R_PORTICO_COL    = (256, 128, 128, 128)   # Tuscan stone columns & pediment entablature
R_CHIMNEY_POTS   = (384, 128, 128, 128)   # Terracotta chimney pots


def paint_atlas():
    a = Atlas(S, seed=1780)

    # 1. Bath Stone (R_MANOR_STONE)
    x, y, w, h = R_MANOR_STONE
    a.rect(x, y, w, h, (0.84, 0.81, 0.74))
    for ry in range(y, y + h, 24):
        a.rect(x, ry, w, 2, (0.68, 0.65, 0.58))
        for rx in range(x + (ry % 36), x + w, 36):
            a.rect(rx, ry, 2, 24, (0.68, 0.65, 0.58))
    # Corner quoins
    for ry in range(y, y + h, 28):
        a.rect(x, ry, 24, 12, (0.76, 0.73, 0.66))
        a.rect(x + w - 24, ry, 24, 12, (0.76, 0.73, 0.66))
    a.noise(x, y, w, h, 0.02)

    # 2. Manor Slate (R_MANOR_SLATE)
    x, y, w, h = R_MANOR_SLATE
    a.rect(x, y, w, h, (0.26, 0.28, 0.32))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.16, 0.18, 0.22))
    a.noise(x, y, w, h, 0.015)

    # 3. Georgian Windows (R_GEORGIAN_WIN)
    x, y, w, h = R_GEORGIAN_WIN
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for wy in range(y + 6, y + h - 10, 24):
        a.rect(x + 6, wy, w - 12, 18, (0.18, 0.28, 0.38))
        for mx in range(x + 16, x + w - 16, 20):
            a.rect(mx, wy, 2, 18, (0.92, 0.93, 0.94))
    a.noise(x, y, w, h, 0.01)

    # 4. Manor Double Doors (R_MANOR_DOORS)
    x, y, w, h = R_MANOR_DOORS
    a.rect(x, y, w, h, (0.32, 0.18, 0.10))
    a.rect(x + 8, y + 8, w // 2 - 12, h - 24, (0.22, 0.12, 0.06))
    a.rect(x + w // 2 + 4, y + 8, w // 2 - 12, h - 24, (0.22, 0.12, 0.06))
    # Brass handles
    a.disc(x + w // 2 - 4, y + 44, 3, (0.85, 0.72, 0.25))
    a.disc(x + w // 2 + 4, y + 44, 3, (0.85, 0.72, 0.25))
    a.noise(x, y, w, h, 0.01)

    # 5. Portico Columns (R_PORTICO_COL)
    x, y, w, h = R_PORTICO_COL
    a.rect(x, y, w, h, (0.86, 0.84, 0.78))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.72, 0.70, 0.64))
    a.noise(x, y, w, h, 0.015)

    # 6. Chimney Pots (R_CHIMNEY_POTS)
    x, y, w, h = R_CHIMNEY_POTS
    a.rect(x, y, w, h, (0.68, 0.32, 0.18))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.48, 0.20, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_large_house_02", OUT_DIR)


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
    mat = material_for(img, "mat_large_house_02")

    parts = []

    def reg_box(name, w, d, h, at, region=R_MANOR_STONE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_MANOR_SLATE):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_PORTICO_COL):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK LARGE HOME 02: GRAND COUNTRY MANOR ESTATE (~880 TRIS)
    # Footprint: 12.0m x 9.0m, Height: 8.2m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Central 2-Storey Manor Corps de Logis (Width: 7.0m, Depth: 8.0m, Height: 5.6m)
    reg_box("ManorCenterBody", 7.0, 8.0, 5.6, (0, 0, 0.0), region=R_MANOR_STONE)
    reg_pyr("ManorCenterRoof", 7.4, 8.4, 2.6, (0, 0, 5.6), region=R_MANOR_SLATE)

    # 2. Symmetrical Flanking Wings (Left & Right: Width: 2.5m each, Height: 4.8m)
    reg_box("ManorWingLeft",  2.5, 7.2, 4.8, (-4.75, 0.0, 0.0), region=R_MANOR_STONE)
    reg_pyr("ManorRoofLeft",  2.8, 7.6, 1.8, (-4.75, 0.0, 4.8), region=R_MANOR_SLATE)

    reg_box("ManorWingRight", 2.5, 7.2, 4.8, ( 4.75, 0.0, 0.0), region=R_MANOR_STONE)
    reg_pyr("ManorRoofRight", 2.8, 7.6, 1.8, ( 4.75, 0.0, 4.8), region=R_MANOR_SLATE)

    # 3. Neoclassical Entrance Portico & Pediment (Center: X = 0.0, Y = -4.0m)
    reg_box("PorticoPlatform", 3.6, 1.2, 0.25, (0, -4.5, 0.0), region=R_PORTICO_COL)
    # 4 Tuscan Columns (16 segments each)
    for ci, cx in enumerate([-1.4, -0.5, 0.5, 1.4]):
        reg_cyl(f"PorticoCol_{ci}", r=0.14, h=3.0, segs=16, at=(cx, -4.8, 0.25), region=R_PORTICO_COL)
        reg_box(f"ColCap_{ci}", 0.35, 0.35, 0.15, (cx, -4.8, 3.25), region=R_PORTICO_COL)

    # Portico Entablature & Triangular Pediment
    reg_box("PorticoEntablature", 3.8, 1.2, 0.35, (0, -4.6, 3.4), region=R_PORTICO_COL)
    reg_pyr("PorticoPediment",    3.8, 1.2, 1.0,  (0, -4.6, 3.75), region=R_MANOR_STONE)

    # Double Grand Manor Doors (X = 0, Y = -4.0m)
    reg_box("ManorDoorFrame", 2.0, 0.25, 2.7, (0, -4.05, 0.25), region=R_PORTICO_COL)
    reg_box("ManorDoorLeaf",  1.6, 0.10, 2.5, (0, -4.10, 0.25), region=R_MANOR_DOORS)

    # 4. Georgian Sash Windows (8 Symmetrical Windows across Facade)
    # Center First Floor Windows (X = -1.6m, +1.6m)
    for wi, wx in enumerate([-1.6, 1.6]):
        reg_box(f"CenterUpperWin_{wi}", 1.4, 0.15, 1.8, (wx, -4.05, 3.4), region=R_GEORGIAN_WIN)

    # Wing Windows (Ground & Upper)
    for side_i, sx in enumerate([-4.75, 4.75]):
        reg_box(f"WingWinGround_{side_i}", 1.4, 0.15, 1.8, (sx, -3.65, 0.8), region=R_GEORGIAN_WIN)
        reg_box(f"WingWinUpper_{side_i}",  1.4, 0.15, 1.6, (sx, -3.65, 3.0), region=R_GEORGIAN_WIN)

    # 5. Twin Stone Chimney Stacks & Pots
    for chi, cx in enumerate([-2.4, 2.4]):
        reg_box(f"ManorChimney_{chi}", 1.0, 1.4, 2.0, (cx, 0.0, 6.2), region=R_MANOR_STONE)
        reg_cyl(f"ManorPot1_{chi}", r=0.18, h=0.6, segs=16, at=(cx, -0.4, 8.2), region=R_CHIMNEY_POTS)
        reg_cyl(f"ManorPot2_{chi}", r=0.18, h=0.6, segs=16, at=(cx,  0.4, 8.2), region=R_CHIMNEY_POTS)

    # Finalize & Export
    shell = kit.join(parts, "House_Large_02_Manor_Estate")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_large_02_manor_estate_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_large_02_manor_estate.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_large_02_manor_estate.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_large_02_manor_estate_preview.png")
        shutil.copy2(OUT_DIR / "atlas_large_house_02.png", TEXTURES_DIR / "atlas_large_house_02.png")
        print(f"[House_Large_02] deployed successfully.")
    except Exception as e:
        print(f"[House_Large_02] deploy notice: {e}")


if __name__ == "__main__":
    main()
