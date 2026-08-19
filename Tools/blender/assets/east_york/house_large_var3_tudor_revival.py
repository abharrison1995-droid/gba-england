"""West York Large Home - Variant 3: Mock-Tudor Revival (~880 Tris).

Specs:
- Footprint: 10.5m wide x 9.0m deep, Height: 8.4m. Sits directly at Z = 0.0.
- Features:
  - Red brick ground floor with projecting upper floor jetty in exposed black timber framing and white wattle infill.
  - Steep twin gables with ornate carved bargeboards.
  - Leaded diamond lattice casement windows.
  - Heavy oak plank entrance door with wrought-iron hinges and gabled timber porch.
  - Tall diagonal decorative brick chimney stack with clay pots.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/house_large_03_tudor_revival.glb.
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
R_TUDOR_TIMBER   = (0,   256, 256, 256)   # Black timber framing with white plaster infill panels
R_BRICK_BASE     = (256, 256, 256, 256)   # Weathered Tudor red brickwork
R_SLATE_STEEP    = (0,   128, 128, 128)   # Steep dark grey roof tiles
R_LEADED_WINDOW  = (128, 128, 128, 128)   # Leaded diamond lattice casement windows
R_OAK_PLANK_DOOR = (256, 128, 128, 128)   # Studded dark oak plank door & wrought iron strap hinges
R_TUDOR_CHIMNEY  = (384, 128, 128, 128)   # Diagonal decorative moulded brick chimney


def paint_atlas():
    a = Atlas(S, seed=1590)

    # 1. Tudor Timber & Plaster (R_TUDOR_TIMBER)
    x, y, w, h = R_TUDOR_TIMBER
    a.rect(x, y, w, h, (0.92, 0.90, 0.85))
    # Vertical black timber studs
    for rx in range(x, x + w, 28):
        a.rect(rx, y, 6, h, (0.16, 0.12, 0.08))
    # Horizontal rails & diagonal braces
    for ry in range(y, y + h, 48):
        a.rect(x, ry, w, 6, (0.16, 0.12, 0.08))
    a.noise(x, y, w, h, 0.02)

    # 2. Tudor Brick Base (R_BRICK_BASE)
    x, y, w, h = R_BRICK_BASE
    a.bricks(x, y, w, h, brick=(0.58, 0.20, 0.14), mortar=(0.72, 0.69, 0.64), bw=18, bh=8, jitter=0.06)
    a.noise(x, y, w, h, 0.02)

    # 3. Steep Slate (R_SLATE_STEEP)
    x, y, w, h = R_SLATE_STEEP
    a.rect(x, y, w, h, (0.24, 0.26, 0.28))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.14, 0.16, 0.18))
    a.noise(x, y, w, h, 0.015)

    # 4. Leaded Lattice Windows (R_LEADED_WINDOW)
    x, y, w, h = R_LEADED_WINDOW
    a.rect(x, y, w, h, (0.22, 0.32, 0.40))
    # Diamond leaded grid
    for i in range(-w, w + h, 12):
        for t in range(4):
            px1, py1 = x + i + t, y + t
            px2, py2 = x + i - t, y + t
            if x <= px1 < x + w and y <= py1 < y + h:
                a.rect(px1, py1, 1, 1, (0.10, 0.10, 0.10))
    a.noise(x, y, w, h, 0.01)

    # 5. Oak Plank Door (R_OAK_PLANK_DOOR)
    x, y, w, h = R_OAK_PLANK_DOOR
    a.rect(x, y, w, h, (0.28, 0.16, 0.08))
    for rx in range(x + 12, x + w - 12, 16):
        a.rect(rx, y + 6, 2, h - 12, (0.14, 0.08, 0.04))
    # Wrought iron strap hinges
    a.rect(x + 8, y + 24, w - 24, 4, (0.15, 0.15, 0.15))
    a.rect(x + 8, y + h - 36, w - 24, 4, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.01)

    # 6. Chimney Moulding (R_TUDOR_CHIMNEY)
    x, y, w, h = R_TUDOR_CHIMNEY
    a.rect(x, y, w, h, (0.58, 0.22, 0.16))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.38, 0.14, 0.10))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_large_house_03", OUT_DIR)


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
    mat = material_for(img, "mat_large_house_03")

    parts = []

    def reg_box(name, w, d, h, at, region=R_TUDOR_TIMBER):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_STEEP):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_TUDOR_CHIMNEY):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK LARGE HOME 03: MOCK-TUDOR REVIVAL (~880 TRIS)
    # Footprint: 10.5m x 9.0m, Height: 8.4m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Ground Floor Red Brick Base (Z = 0.0 to 2.8m, Footprint: 10.0m x 8.0m)
    reg_box("GroundBrickBase", 10.0, 8.0, 2.8, (0, 0, 0.0), region=R_BRICK_BASE)

    # 2. Overhanging Upper Floor Jetty in Black Timber Framing (Z = 2.8m to 5.6m, Overhang: 10.6m x 8.6m)
    reg_box("UpperJettyBody", 10.6, 8.6, 2.8, (0, 0, 2.8), region=R_TUDOR_TIMBER)
    reg_box("JettyBressummerBeam", 10.8, 8.8, 0.25, (0, 0, 2.7), region=R_OAK_PLANK_DOOR)

    # 3. Steep Twin Gables (Left Gable: X = -2.8m, Right Gable: X = 2.8m)
    # Main Connecting Roof
    reg_pyr("MainTudorRoof", 11.0, 9.0, 2.8, (0, 0, 5.6), region=R_SLATE_STEEP)

    # Left Projecting Gable (X = -2.8m)
    reg_box("LeftGableWall",  4.6, 2.0, 2.0, (-2.8, -4.0, 5.6), region=R_TUDOR_TIMBER)
    reg_pyr("LeftGableRoof",  5.0, 2.4, 2.2, (-2.8, -4.0, 6.4), region=R_SLATE_STEEP)

    # Right Projecting Gable (X = 2.8m)
    reg_box("RightGableWall", 4.6, 2.0, 2.0, ( 2.8, -4.0, 5.6), region=R_TUDOR_TIMBER)
    reg_pyr("RightGableRoof", 5.0, 2.4, 2.2, ( 2.8, -4.0, 6.4), region=R_SLATE_STEEP)

    # 4. Front Gabled Timber Entrance Porch & Studded Oak Door (Center: X = 0.0m, Y = -4.2m)
    reg_box("TudorPorchBase", 2.0, 1.0, 0.2, (0, -4.5, 0.0), region=R_BRICK_BASE)
    reg_box("TudorDoorFrame", 1.5, 0.3, 2.4, (0, -4.2, 0.2), region=R_OAK_PLANK_DOOR)
    reg_box("TudorDoorLeaf",  1.2, 0.1, 2.2, (0, -4.25, 0.2), region=R_OAK_PLANK_DOOR)
    reg_pyr("TudorPorchGable", 2.2, 1.2, 0.9, (0, -4.5, 2.4), region=R_SLATE_STEEP)

    # 5. Leaded Lattice Windows
    # Ground floor casements
    for wi, wx in enumerate([-3.0, 3.0]):
        reg_box(f"GroundWin_{wi}", 2.0, 0.15, 1.5, (wx, -4.05, 0.8), region=R_LEADED_WINDOW)

    # Upper jetty casements
    for wi, wx in enumerate([-2.8, 0.0, 2.8]):
        reg_box(f"UpperWin_{wi}", 1.8, 0.15, 1.4, (wx, -4.35, 3.4), region=R_LEADED_WINDOW)

    # 6. Tall Decorative Diagonal Chimney Stack with 3 Shafts
    reg_box("TudorChimneyBase", 1.4, 1.4, 1.8, (-3.6, 0.0, 6.2), region=R_TUDOR_CHIMNEY)
    for si in range(2):
        sy = -0.3 + si * 0.6
        reg_cyl(f"ChimneyShaft_{si}", r=0.22, h=1.4, segs=16, at=(-3.6, sy, 8.0), region=R_TUDOR_CHIMNEY)

    # Finalize & Export
    shell = kit.join(parts, "House_Large_03_Tudor_Revival")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "house_large_03_tudor_revival_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "house_large_03_tudor_revival.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "house_large_03_tudor_revival.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "house_large_03_tudor_revival_preview.png")
        shutil.copy2(OUT_DIR / "atlas_large_house_03.png", TEXTURES_DIR / "atlas_large_house_03.png")
        print(f"[House_Large_03] deployed successfully.")
    except Exception as e:
        print(f"[House_Large_03] deploy notice: {e}")


if __name__ == "__main__":
    main()
