"""St Paul's Cathedral - Building Only.

Specs:
- Clean cathedral structure without podium slab or external pavement.
- Sits directly at Z = 0.0.
- Grand 32-column peristyle dome with lantern & golden cross, twin baroque West bell towers,
  classical Corinthian portico, pediment, nave, and transepts.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_st_pauls_cathedral.glb.
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
R_PORTLAND_STONE = (0,   256, 256, 256)   # Weathered Portland limestone ashlar
R_LEAD_DOME      = (256, 256, 256, 256)   # Lead & copper dome cladding with rib seams
R_BAROQUE_FACADE = (0,   128, 128, 128)   # Portico arches, Corinthian capitals & pediment carving
R_BELL_CLOCK     = (128, 128, 128, 128)   # West bell tower clock dials & louvered belfries
R_GOLD_CROSS     = (256, 128, 128, 128)   # Gilded ball and cross atop lantern


def paint_atlas():
    a = Atlas(S, seed=1710)

    # 1. Portland Stone (R_PORTLAND_STONE)
    x, y, w, h = R_PORTLAND_STONE
    a.rect(x, y, w, h, (0.84, 0.82, 0.78))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.74, 0.72, 0.68))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.76, 0.74, 0.70))
    a.noise(x, y, w, h, 0.015)

    # 2. Lead Dome (R_LEAD_DOME)
    x, y, w, h = R_LEAD_DOME
    a.rect(x, y, w, h, (0.38, 0.42, 0.44))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 2, h, (0.28, 0.32, 0.34))
    a.noise(x, y, w, h, 0.012)

    # 3. Baroque Facade & Pediment (R_BAROQUE_FACADE)
    x, y, w, h = R_BAROQUE_FACADE
    a.rect(x, y, w, h, (0.80, 0.78, 0.74))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 32, (0.68, 0.66, 0.62))
    a.noise(x, y, w, h, 0.018)

    # 4. Bell Tower Clocks (R_BELL_CLOCK)
    x, y, w, h = R_BELL_CLOCK
    a.rect(x, y, w, h, (0.78, 0.76, 0.72))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 40, (0.15, 0.15, 0.15))
    a.disc(cx, cy, 36, (0.95, 0.95, 0.90))
    a.disc(cx, cy, 4, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy, 4, 22, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.01)

    # 5. Golden Cross (R_GOLD_CROSS)
    x, y, w, h = R_GOLD_CROSS
    a.rect(x, y, w, h, (0.92, 0.80, 0.25))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_st_pauls", OUT_DIR)


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


def make_dome_hemisphere(name, r, h, rings=8, segs=24, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    v_rows = []
    for ri in range(rings):
        phi = (math.pi / 2) * (ri / (rings - 1))
        z = h * math.sin(phi)
        r_curr = r * math.cos(phi)
        row = []
        for i in range(segs):
            theta = 2 * math.pi * i / segs
            v = bm.verts.new((r_curr * math.cos(theta), r_curr * math.sin(theta), z))
            row.append(v)
        v_rows.append(row)

    for ri in range(rings - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[ri][i], v_rows[ri][ni], v_rows[ri + 1][ni], v_rows[ri + 1][i]))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


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
    mat = material_for(img, "mat_st_pauls")

    parts = []

    def reg_box(name, w, d, h, at, region=R_PORTLAND_STONE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_PORTLAND_STONE):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # ST PAUL'S CATHEDRAL (BUILDING ONLY - NO PODIUM/PAVEMENT)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Main Latin Cross Body (Nave, Transepts & Choir)
    reg_box("NaveBody", 8.0, 18.0, 7.0, (0, 1.0, 0.0), region=R_PORTLAND_STONE)
    reg_box("NaveRoof", 7.6, 18.2, 2.5, (0, 1.0, 7.0), region=R_LEAD_DOME)

    # Transepts (North-South Cross Arms)
    reg_box("TranseptBody", 16.0, 6.0, 7.0, (0, 2.0, 0.0), region=R_PORTLAND_STONE)
    reg_box("TranseptRoof", 16.2, 5.6, 2.5, (0, 2.0, 7.0), region=R_LEAD_DOME)

    # 2. Grand Central Dome
    reg_box("DomeBaseCrossing", 8.4, 8.4, 2.0, (0, 2.0, 7.0), region=R_PORTLAND_STONE)

    # Peristyle Colonnade Drum (32 Columns around drum)
    drum = reg_cyl("DomePeristyleDrum", r=3.8, h=3.4, segs=24, at=(0, 2.0, 9.0), region=R_PORTLAND_STONE)
    for ci in range(16):
        ang = 2 * math.pi * ci / 16
        col_x = 4.2 * math.cos(ang)
        col_y = 2.0 + 4.2 * math.sin(ang)
        reg_cyl(f"PeristyleCol_{ci}", r=0.18, h=3.4, segs=8, at=(col_x, col_y, 9.0), region=R_PORTLAND_STONE)

    # Attic Drum
    reg_cyl("DomeAtticDrum", r=3.6, h=1.4, segs=24, at=(0, 2.0, 12.4), region=R_PORTLAND_STONE)

    # Main Lead Outer Dome
    dome = make_dome_hemisphere("MainLeadDome", r=3.5, h=4.4, rings=8, segs=24, at=(0, 2.0, 13.8))
    dome.data.materials.append(mat)
    kit.map_faces_to_region(dome, R_LEAD_DOME, S)
    parts.append(dome)

    # Lantern Belfry & Golden Cross
    reg_cyl("DomeLanternBase", r=1.0, h=2.5, segs=16, at=(0, 2.0, 18.2), region=R_PORTLAND_STONE)
    reg_cyl("DomeLanternSpire", r=0.4, h=2.2, segs=12, at=(0, 2.0, 20.7), region=R_LEAD_DOME)

    reg_cyl("GoldenBall", r=0.4, h=0.6, segs=10, at=(0, 2.0, 22.9), region=R_GOLD_CROSS)
    reg_box("GoldenCrossV", 0.15, 0.15, 1.4, (0, 2.0, 23.5), region=R_GOLD_CROSS)
    reg_box("GoldenCrossH", 0.8, 0.15, 0.15, (0, 2.0, 24.2), region=R_GOLD_CROSS)

    # 3. West Front Portico & Twin Bell Towers
    # Lower Portico Columns (sits at Z = 0.0)
    for col_i, cx in enumerate([-3.0, -1.8, -0.6, 0.6, 1.8, 3.0]):
        reg_cyl(f"PorticoLowerCol_{col_i}", r=0.24, h=4.2, segs=10, at=(cx, -8.2, 0.0), region=R_PORTLAND_STONE)
    reg_box("PorticoLowerEntablature", 7.2, 1.2, 0.6, (0, -8.2, 4.2), region=R_PORTLAND_STONE)

    # Upper Portico & Triangular Pediment
    for col_i, cx in enumerate([-2.4, -0.8, 0.8, 2.4]):
        reg_cyl(f"PorticoUpperCol_{col_i}", r=0.22, h=3.2, segs=10, at=(cx, -8.2, 4.8), region=R_PORTLAND_STONE)

    pediment = make_pyramid("WestPediment", base_w=6.4, base_d=0.8, height=1.8, at=(0, -8.2, 8.0))
    pediment.data.materials.append(mat)
    kit.map_faces_to_region(pediment, R_BAROQUE_FACADE, S)
    parts.append(pediment)

    # Twin Baroque Bell Towers (sits at Z = 0.0)
    for ti, (tx, is_l) in enumerate([(-4.8, True), (4.8, False)]):
        reg_box(f"WestTowerLower_{ti}", 3.2, 3.2, 7.0, (tx, -7.5, 0.0), region=R_PORTLAND_STONE)
        reg_box(f"WestTowerClock_{ti}", 3.0, 3.0, 3.5, (tx, -7.5, 7.0), region=R_BELL_CLOCK)
        reg_cyl(f"WestTowerLantern_{ti}", r=1.1, h=2.5, segs=14, at=(tx, -7.5, 10.5), region=R_PORTLAND_STONE)
        reg_cyl(f"WestTowerPineapple_{ti}", r=0.5, h=1.8, segs=10, at=(tx, -7.5, 13.0), region=R_GOLD_CROSS)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_St_Pauls_Cathedral")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_st_pauls_cathedral_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_st_pauls_cathedral.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_st_pauls_cathedral.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_st_pauls_cathedral_preview.png")
        shutil.copy2(OUT_DIR / "atlas_st_pauls.png", TEXTURES_DIR / "atlas_st_pauls.png")
        print(f"[StPauls] clean building deployed.")
    except Exception as e:
        print(f"[StPauls] deploy notice: {e}")


if __name__ == "__main__":
    main()
