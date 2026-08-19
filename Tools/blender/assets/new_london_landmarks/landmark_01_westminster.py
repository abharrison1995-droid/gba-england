"""Palace of Westminster & Big Ben (Elizabeth Tower) - Building Only.

Specs:
- Clean building structure without pavement, embankment slabs, or surrounding paths.
- Sits directly at Z = 0.0.
- Elizabeth Tower (Big Ben), Victoria Tower, River facade, central lantern, and Westminster Hall.
- Target Triangles: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_palace_of_westminster.glb.
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
OUT_DIR = kit.OUT_DIR / "new_london_landmarks"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "New LonLandmark"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions
R_STONE_WALL     = (0,   256, 256, 256)   # Ancaster / Portland limestone ashlar masonry
R_GOTHIC_ROOF    = (256, 256, 256, 256)   # Slate grey gothic roof & lead dormers
R_CLOCK_FACE     = (0,   128, 128, 128)   # Big Ben 4-sided illuminated clock dial & gold hands
R_GOTHIC_WINDOWS = (128, 128, 128, 128)   # Gothic lancet & arcade windows
R_GOLD_TRIM      = (256, 128, 128, 128)   # Gilded crests, pinnacles & clock dials
R_FOUNDATION     = (384, 128, 128, 128)   # Base foundation plinth


def paint_atlas():
    a = Atlas(S, seed=1859)

    # 1. Limestone Gothic Wall (R_STONE_WALL)
    x, y, w, h = R_STONE_WALL
    a.rect(x, y, w, h, (0.82, 0.78, 0.70))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.72, 0.68, 0.60))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.74, 0.70, 0.62))
    a.noise(x, y, w, h, 0.015)

    # 2. Slate Grey Gothic Roof (R_GOTHIC_ROOF)
    x, y, w, h = R_GOTHIC_ROOF
    a.rect(x, y, w, h, (0.28, 0.32, 0.36))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.20, 0.23, 0.26))
    a.noise(x, y, w, h, 0.012)

    # 3. Big Ben Clock Face (R_CLOCK_FACE)
    x, y, w, h = R_CLOCK_FACE
    a.rect(x, y, w, h, (0.15, 0.15, 0.15))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 56, (0.85, 0.75, 0.25))
    a.disc(cx, cy, 50, (0.95, 0.94, 0.88))
    for i in range(12):
        ang = i * (math.pi / 6)
        nx = int(cx + 42 * math.sin(ang))
        ny = int(cy + 42 * math.cos(ang))
        a.disc(nx, ny, 3, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy, 4, 34, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy - 2, 24, 4, (0.1, 0.1, 0.1))
    a.disc(cx, cy, 6, (0.85, 0.75, 0.25))

    # 4. Gothic Arcade Windows (R_GOTHIC_WINDOWS)
    x, y, w, h = R_GOTHIC_WINDOWS
    a.rect(x, y, w, h, (0.75, 0.72, 0.65))
    for wy in range(y + 8, y + h - 20, 36):
        for wx in range(x + 8, x + w - 20, 24):
            a.rect(wx, wy, 16, 26, (0.12, 0.16, 0.22))
            a.rect(wx + 7, wy, 2, 26, (0.70, 0.68, 0.60))
    a.noise(x, y, w, h, 0.01)

    # 5. Gilded Gold Trim (R_GOLD_TRIM)
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, (0.88, 0.76, 0.22))
    a.noise(x, y, w, h, 0.02)

    # 6. Base Foundation Plinth (R_FOUNDATION)
    x, y, w, h = R_FOUNDATION
    a.rect(x, y, w, h, (0.45, 0.45, 0.48))
    for ry in range(y, y + h, 20):
        a.rect(x, ry, w, 2, (0.35, 0.35, 0.38))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_palace_of_westminster", OUT_DIR)


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


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_westminster")

    parts = []

    def reg_box(name, w, d, h, at, region=R_STONE_WALL):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_GOTHIC_ROOF):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # PALACE OF WESTMINSTER GEOMETRY (BUILDING ONLY - NO PAVEMENT)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Main River Facade Central Block
    reg_box("CentralBlock", 12.0, 6.0, 6.5, (0, -2.0, 0.0), region=R_GOTHIC_WINDOWS)

    # Main Gable Roof
    roof = kit.make_box("CentralRoof", 12.2, 5.8, 2.5, (0, -2.0, 6.5))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_GOTHIC_ROOF, S)
    parts.append(roof)

    # Gothic Roof Dormer Gables
    for i in range(7):
        gx = -5.0 + i * 1.66
        reg_pyr(f"Dormer_{i}", 1.2, 1.2, 1.6, (gx, -4.9, 6.5), region=R_GOTHIC_ROOF)

    # 2. Elizabeth Tower (Big Ben) - Sits at Z = 0.0
    reg_box("ClockTowerShaft", 3.8, 3.8, 9.5, (-7.0, -3.0, 0.0), region=R_STONE_WALL)
    reg_box("ClockDialBlock", 4.0, 4.0, 3.2, (-7.0, -3.0, 9.5), region=R_CLOCK_FACE)
    reg_box("BelfrySection", 3.6, 3.6, 2.5, (-7.0, -3.0, 12.7), region=R_GOLD_TRIM)
    reg_pyr("BigBenMainSpire", 3.5, 3.5, 6.5, (-7.0, -3.0, 15.2), region=R_GOTHIC_ROOF)
    reg_pyr("BigBenLanternSpire", 1.2, 1.2, 3.0, (-7.0, -3.0, 21.7), region=R_GOLD_TRIM)

    # 4 Corner Turrets on Clock Tower
    for ci, (cx, cy) in enumerate([(-1.9, -1.9), (1.9, -1.9), (1.9, 1.9), (-1.9, 1.9)]):
        reg_box(f"ClockTurretShaft_{ci}", 0.65, 0.65, 3.5, (-7.0 + cx, -3.0 + cy, 12.5), region=R_STONE_WALL)
        reg_pyr(f"ClockTurretSpire_{ci}", 0.75, 0.75, 2.0, (-7.0 + cx, -3.0 + cy, 16.0), region=R_GOLD_TRIM)

    # 3. Victoria Tower - Sits at Z = 0.0
    reg_box("VicTowerShaft", 4.6, 4.6, 12.5, (7.0, -3.0, 0.0), region=R_STONE_WALL)
    reg_box("VicTowerCrown", 4.8, 4.8, 2.2, (7.0, -3.0, 12.5), region=R_GOTHIC_WINDOWS)
    for ci, (cx, cy) in enumerate([(-2.3, -2.3), (2.3, -2.3), (2.3, 2.3), (-2.3, 2.3)]):
        reg_box(f"VicTurret_{ci}", 0.85, 0.85, 3.2, (7.0 + cx, -3.0 + cy, 12.5), region=R_STONE_WALL)
        reg_pyr(f"VicSpire_{ci}", 0.95, 0.95, 2.4, (7.0 + cx, -3.0 + cy, 15.7), region=R_GOTHIC_ROOF)

    # 4. Central Octagonal Lantern & Spire
    reg_box("CentralOctagon", 3.0, 3.0, 3.8, (0, 0, 6.5), region=R_STONE_WALL)
    reg_pyr("CentralSpire", 2.8, 2.8, 5.5, (0, 0, 10.3), region=R_GOTHIC_ROOF)

    # 5. Westminster Hall Body & Roof
    reg_box("WestminsterHall", 7.2, 6.2, 5.5, (0, 3.0, 0.0), region=R_STONE_WALL)
    reg_pyr("WestminsterHallRoof", 7.4, 6.4, 3.8, (0, 3.0, 5.5), region=R_GOTHIC_ROOF)

    # 6. Facade Buttresses & Pinnacles
    for bi in range(10):
        bx = -5.5 + bi * 1.22
        reg_box(f"FacadeButtress_{bi}", 0.35, 0.5, 7.0, (bx, -5.1, 0.0), region=R_STONE_WALL)
        reg_pyr(f"PinnacleSpire_{bi}", 0.45, 0.45, 1.4, (bx, -5.1, 7.0), region=R_GOLD_TRIM)

    # 7. North & South Wings
    reg_box("NorthWing", 3.2, 6.0, 5.2, (-4.5, 3.0, 0.0), region=R_GOTHIC_WINDOWS)
    reg_pyr("NorthWingRoof", 3.4, 6.2, 2.2, (-4.5, 3.0, 5.2), region=R_GOTHIC_ROOF)

    reg_box("SouthWing", 3.2, 6.0, 5.2, (4.5, 3.0, 0.0), region=R_GOTHIC_WINDOWS)
    reg_pyr("SouthWingRoof", 3.4, 6.2, 2.2, (4.5, 3.0, 5.2), region=R_GOTHIC_ROOF)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Palace_Of_Westminster")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_palace_of_westminster_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_palace_of_westminster.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_palace_of_westminster.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_palace_of_westminster_preview.png")
        shutil.copy2(OUT_DIR / "atlas_palace_of_westminster.png", TEXTURES_DIR / "atlas_palace_of_westminster.png")
        print(f"[Westminster] clean building deployed.")
    except Exception as e:
        print(f"[Westminster] deploy notice: {e}")


if __name__ == "__main__":
    main()
