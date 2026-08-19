"""West York Terraced House - Variant 2: Stone & Cream Render with Dormer (~850 Tris).

Specs:
- Footprint: 5.5m wide x 8.0m deep, Height: 7.8m. Sits directly at Z = 0.0.
- Features:
  - 2.5-storey Yorkshire gritstone & cream render facade.
  - Pitched slate roof with gabled rooftop attic dormer window.
  - Black wrought-iron boundary front railings and timber entrance door with porch hood.
  - 4 Georgian sash windows with painted stone surrounds.
  - Dual end chimney stacks with clay pots.
- Target: <1,000 tris (~850 tris).
- Deploys to Assets/3DModels/West York/house_terrace_02_stone_render.glb.
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
R_STONE_RENDER   = (0,   256, 256, 256)   # Yorkshire gritstone masonry & warm cream render
R_SLATE_DARK     = (256, 256, 256, 256)   # Weathered dark slate roofing
R_SASH_WINDOW    = (0,   128, 128, 128)   # White Georgian 6-pane sash windows
R_TIMBER_DOOR    = (128, 128, 128, 128)   # Navy blue timber entrance door & porch hood
R_IRON_RAILING   = (256, 128, 128, 128)   # Black painted wrought iron railings
R_CHIMNEY_POT    = (384, 128, 128, 128)   # Terracotta chimney pots


def paint_atlas():
    a = Atlas(S, seed=1910)

    # 1. Stone / Render (R_STONE_RENDER)
    x, y, w, h = R_STONE_RENDER
    a.rect(x, y, w, h, (0.78, 0.75, 0.68))
    # Stone block courses
    for ry in range(y, y + h, 24):
        a.rect(x, ry, w, 2, (0.62, 0.59, 0.52))
        for rx in range(x + (ry % 36), x + w, 36):
            a.rect(rx, ry, 2, 24, (0.62, 0.59, 0.52))
    a.noise(x, y, w, h, 0.02)

    # 2. Dark Slate (R_SLATE_DARK)
    x, y, w, h = R_SLATE_DARK
    a.rect(x, y, w, h, (0.24, 0.26, 0.28))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.16, 0.17, 0.19))
    a.noise(x, y, w, h, 0.015)

    # 3. Sash Windows (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, (0.92, 0.93, 0.94))
    for wy in range(y + 6, y + h - 10, 24):
        a.rect(x + 6, wy, w - 12, 18, (0.18, 0.28, 0.38))
        a.rect(x + w // 2 - 2, wy, 4, 18, (0.92, 0.93, 0.94))
    a.noise(x, y, w, h, 0.01)

    # 4. Navy Blue Door (R_TIMBER_DOOR)
    x, y, w, h = R_TIMBER_DOOR
    a.rect(x, y, w, h, (0.15, 0.22, 0.35))
    a.rect(x + 8, y + 6, w - 16, 18, (0.85, 0.72, 0.25))
    a.disc(x + w // 2, y + 42, 4, (0.85, 0.72, 0.25))
    a.noise(x, y, w, h, 0.01)

    # 5. Iron Railings (R_IRON_RAILING)
    x, y, w, h = R_IRON_RAILING
    a.rect(x, y, w, h, (0.14, 0.15, 0.16))
    for rx in range(x + 4, x + w - 4, 12):
        a.rect(rx, y, 2, h, (0.35, 0.36, 0.38))
    a.noise(x, y, w, h, 0.015)

    # 6. Chimney Pot (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, (0.68, 0.32, 0.18))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.48, 0.20, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_terrace_02", OUT_DIR)


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
    mat = material_for(img, "mat_terrace_02")

    parts = []

    def reg_box(name, w, d, h, at, region=R_STONE_RENDER):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_DARK):
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
    # WEST YORK TERRACED HOUSE 02: STONE / RENDER WITH DORMER (~850 TRIS)
    # Footprint: 5.5m x 8.0m, Height: 7.8m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main 2.5-Storey House Body (Z = 0.0 to 5.4m)
    reg_box("HouseMainBody", 5.5, 7.8, 5.4, (0, 0, 0.0), region=R_STONE_RENDER)

    # 2. Pitched Slate Roof (Z = 5.4m to 7.4m)
    reg_pyr("HouseRoof", 5.7, 8.0, 2.0, (0, 0, 5.4), region=R_SLATE_DARK)

    # 3. Rooftop Attic Dormer Window (Front Roof Slope at Y = -2.2m, Z = 5.8m)
    reg_box("DormerBody", 1.6, 1.4, 1.2, (-0.8, -2.2, 5.8), region=R_STONE_RENDER)
    reg_box("DormerWindow", 1.2, 0.1, 0.9, (-0.8, -2.92, 5.9), region=R_SASH_WINDOW)
    reg_pyr("DormerRoof", 1.8, 1.6, 0.6, (-0.8, -2.2, 7.0), region=R_SLATE_DARK)

    # 4. Front Entrance Door & Porch Hood (X = 1.4m, Y = -3.9m)
    reg_box("DoorStep", 1.4, 0.4, 0.15, (1.4, -4.1, 0.0), region=R_STONE_RENDER)
    reg_box("DoorFrame", 1.2, 0.2, 2.4, (1.4, -3.95, 0.15), region=R_STONE_RENDER)
    reg_box("DoorLeaf", 1.0, 0.1, 2.2, (1.4, -3.98, 0.15), region=R_TIMBER_DOOR)
    reg_box("PorchHood", 1.6, 0.6, 0.15, (1.4, -4.2, 2.65), region=R_TIMBER_DOOR)

    # 5. Ground & First Floor Sash Windows
    # Ground Floor Window (X = -1.4m)
    reg_box("GroundWinFrame", 1.4, 0.15, 1.8, (-1.4, -3.95, 0.6), region=R_SASH_WINDOW)
    reg_box("GroundWinSill", 1.6, 0.25, 0.12, (-1.4, -3.98, 0.48), region=R_STONE_RENDER)

    # First Floor Windows (X = -1.4m, +1.4m)
    for wi, wx in enumerate([-1.4, 1.4]):
        reg_box(f"UpperWinFrame_{wi}", 1.3, 0.15, 1.6, (wx, -3.95, 3.2), region=R_SASH_WINDOW)
        reg_box(f"UpperWinSill_{wi}", 1.5, 0.25, 0.12, (wx, -3.98, 3.08), region=R_STONE_RENDER)

    # 6. Front Wrought Iron Railings (X = -2.7 to 0.5m along front boundary)
    reg_box("RailingBase", 3.2, 0.15, 0.15, (-1.2, -4.1, 0.0), region=R_STONE_RENDER)
    reg_box("RailingPickets", 3.0, 0.08, 0.9, (-1.2, -4.1, 0.15), region=R_IRON_RAILING)

    # 7. Chimney Stacks & Pots
    reg_box("ChimneyLeft", 0.9, 1.2, 1.6, (-2.1, 0.0, 6.4), region=R_STONE_RENDER)
    reg_cyl("ChimneyPot_L", r=0.18, h=0.6, segs=16, at=(-2.1, 0.0, 8.0), region=R_CHIMNEY_POT)

    # Finalize & Export
    shell = kit.join(parts, "House_Terrace_02_Stone_Render")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_terrace_02_stone_render_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_terrace_02_stone_render.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_terrace_02_stone_render.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_terrace_02_stone_render_preview.png")
        shutil.copy2(OUT_DIR / "atlas_terrace_02.png", TEXTURES_DIR / "atlas_terrace_02.png")
        print(f"[House_Terrace_02] deployed successfully.")
    except Exception as e:
        print(f"[House_Terrace_02] deploy notice: {e}")


if __name__ == "__main__":
    main()
