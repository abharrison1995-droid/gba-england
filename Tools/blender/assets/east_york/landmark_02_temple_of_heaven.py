"""Temple of Heaven (Hall of Prayer for Good Harvests / 祈年殿) - East York Landmark (~3500 Tris).

Specs:
- Clean circular temple building structure without surrounding ground/plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - Triple-tiered circular white marble terrace base with individual balustrades and carved stair flights.
  - Triple-gabled circular conical roof clad in deep cobalt blue glazed tiles.
  - Gilded golden spherical apex finial (Baoding).
  - Ring of 12 circular vermilion red lacquer Dragon Well pillars supporting the lower and upper eaves.
  - Elaborate multi-tiered circular Dougang wooden bracket rings painted with jade/gold Qingdai motifs.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_temple_of_heaven.glb.
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
R_COBALT_ROOF    = (0,   256, 256, 256)   # Sacred cobalt blue glazed ceramic circular tiles
R_VERMILION_RED  = (256, 256, 256, 256)   # Vermilion lacquer columns & circular pavilion core
R_WHITE_MARBLE   = (0,   128, 128, 128)   # Triple circular Hanbaiyu white marble terraces
R_GOLD_FINIAL    = (128, 128, 128, 128)   # Gilded gold sphere apex finial (Baoding)
R_QINGDAI_PAINT  = (256, 128, 128, 128)   # Dragon & phoenix jade green & gold painted beams
R_TEMPLE_LATTICE = (384, 128, 128, 128)   # Gold & red geometric circular door lattice screens


def paint_atlas():
    a = Atlas(S, seed=1420)

    # 1. Cobalt Blue Glazed Roof (R_COBALT_ROOF)
    x, y, w, h = R_COBALT_ROOF
    a.rect(x, y, w, h, (0.12, 0.32, 0.62))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.08, 0.22, 0.45))
        for rx in range(x + (ry % 18), x + w, 18):
            a.rect(rx, ry, 2, 10, (0.16, 0.40, 0.72))
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
    a.noise(x, y, w, h, 0.015)

    # 4. Gilded Golden Finial (R_GOLD_FINIAL)
    x, y, w, h = R_GOLD_FINIAL
    a.rect(x, y, w, h, (0.95, 0.82, 0.22))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 50, (0.98, 0.90, 0.35))
    a.noise(x, y, w, h, 0.015)

    # 5. Qingdai Dragon Beam Paint (R_QINGDAI_PAINT)
    x, y, w, h = R_QINGDAI_PAINT
    a.rect(x, y, w, h, (0.14, 0.45, 0.38))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 4, h, (0.12, 0.28, 0.50))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.92, 0.80, 0.25))
    a.noise(x, y, w, h, 0.012)

    # 6. Temple Door Lattice (R_TEMPLE_LATTICE)
    x, y, w, h = R_TEMPLE_LATTICE
    a.rect(x, y, w, h, (0.75, 0.20, 0.16))
    for wy in range(y + 8, y + h - 16, 24):
        for wx in range(x + 8, x + w - 16, 18):
            a.rect(wx, wy, 12, 18, (0.22, 0.14, 0.10))
            a.rect(wx + 5, wy, 2, 18, (0.90, 0.75, 0.20))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_temple_of_heaven", OUT_DIR)


def make_cylinder(name, r, h, segs=24, at=(0, 0, 0)):
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


def make_circular_cone_roof(name, base_r, top_r, height, segs=28, flare=0.5, at=(0, 0, 0)):
    """Parametric circular conical roof tier with swept flared rim."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = 4
    v_rows = []

    for ri in range(rings):
        frac = ri / (rings - 1)
        z = height * frac
        # Flared parabolic curve
        r_curr = (base_r + flare * (1.0 - frac)**1.8) * (1.0 - frac) + top_r * frac
        row = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            v = bm.verts.new((r_curr * math.cos(ang), r_curr * math.sin(ang), z))
            row.append(v)
        v_rows.append(row)

    for ri in range(rings - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[ri][i], v_rows[ri][ni], v_rows[ri + 1][ni], v_rows[ri + 1][i]))

    if top_r <= 0.2:
        v_top = bm.verts.new((0, 0, height + 0.3))
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[-1][i], v_rows[-1][ni], v_top))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_temple_of_heaven")

    parts = []

    def reg_cyl(name, r, h, segs=24, at=(0, 0, 0), region=R_WHITE_MARBLE):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_roof(name, base_r, top_r, height, segs=28, flare=0.6, at=(0, 0, 0), region=R_COBALT_ROOF):
        o = make_circular_cone_roof(name, base_r, top_r, height, segs, flare, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # TEMPLE OF HEAVEN: HALL OF PRAYER FOR GOOD HARVESTS (~3500 TRIS)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Triple-Tier Circular White Marble Altar Terraces (Z = 0.0 to 2.4m)
    # Tier 1 (Lowest, r = 10.0m)
    reg_cyl("MarbleTerrace_Round_1", r=10.0, h=0.8, segs=32, at=(0, 0, 0.0), region=R_WHITE_MARBLE)
    # Tier 2 (Middle, r = 8.5m)
    reg_cyl("MarbleTerrace_Round_2", r=8.5, h=0.8, segs=32, at=(0, 0, 0.8), region=R_WHITE_MARBLE)
    # Tier 3 (Upper, r = 7.0m)
    reg_cyl("MarbleTerrace_Round_3", r=7.0, h=0.8, segs=32, at=(0, 0, 1.6), region=R_WHITE_MARBLE)

    # 32 Marble Balustrade Spindles on Top Terrace
    for bi in range(24):
        ang = 2 * math.pi * bi / 24
        bx = 6.8 * math.cos(ang)
        by = 6.8 * math.sin(ang)
        reg_cyl(f"MarbleBaluster_{bi}", r=0.08, h=0.65, segs=8, at=(bx, by, 2.4), region=R_WHITE_MARBLE)

    # 4 Cardinal Stair Flights
    for si, (sx, sy, rot) in enumerate([(0, -7.5, 0), (0, 7.5, 0), (-7.5, 0, 1), (7.5, 0, 1)]):
        step_w = 2.4 if rot == 0 else 1.2
        step_d = 1.2 if rot == 0 else 2.4
        box = kit.make_box(f"MarbleStep_{si}", step_w, step_d, 2.4, (sx, sy, 0.0))
        box.data.materials.append(mat)
        kit.map_faces_to_region(box, R_WHITE_MARBLE, S)
        parts.append(box)

    # 2. Main Circular Wooden Temple Body (Z = 2.4m to 6.0m)
    reg_cyl("TempleCoreBody", r=5.2, h=3.6, segs=24, at=(0, 0, 2.4), region=R_TEMPLE_LATTICE)

    # 12 Outer Red Vermilion Dragon Well Columns (16 segments each)
    for ci in range(12):
        ang = 2 * math.pi * ci / 12
        cx = 5.0 * math.cos(ang)
        cy = 5.0 * math.sin(ang)
        reg_cyl(f"DragonCol_{ci}", r=0.22, h=3.6, segs=16, at=(cx, cy, 2.4), region=R_VERMILION_RED)

    # 3. Lower Tier Circular Eave & Dougang Bracket Ring (Z = 6.0m to 8.2m)
    reg_cyl("LowerDougangRing", r=5.6, h=0.6, segs=28, at=(0, 0, 6.0), region=R_QINGDAI_PAINT)
    reg_roof("Roof_Tier1", base_r=7.2, top_r=4.6, height=1.6, segs=32, flare=0.8, at=(0, 0, 6.6), region=R_COBALT_ROOF)

    # 4. Middle Tier Drum & Eave (Z = 8.2m to 11.2m)
    reg_cyl("MiddleDrumBody", r=4.4, h=1.4, segs=24, at=(0, 0, 8.2), region=R_TEMPLE_LATTICE)
    reg_cyl("MiddleDougangRing", r=4.6, h=0.5, segs=28, at=(0, 0, 9.6), region=R_QINGDAI_PAINT)
    reg_roof("Roof_Tier2", base_r=5.8, top_r=3.2, height=1.5, segs=32, flare=0.7, at=(0, 0, 10.1), region=R_COBALT_ROOF)

    # 5. Upper Conical Pagoda Dome Tier (Z = 11.6m to 15.5m)
    reg_cyl("UpperDrumBody", r=3.0, h=1.2, segs=24, at=(0, 0, 11.6), region=R_TEMPLE_LATTICE)
    reg_cyl("UpperDougangRing", r=3.2, h=0.5, segs=24, at=(0, 0, 12.8), region=R_QINGDAI_PAINT)
    reg_roof("Roof_Tier3_Apex", base_r=4.5, top_r=0.2, height=3.2, segs=32, flare=0.6, at=(0, 0, 13.3), region=R_COBALT_ROOF)

    # 6. Gilded Golden Sphere Apex Finial (Baoding at Z = 16.5m)
    reg_cyl("GoldFinialBase", r=0.6, h=0.5, segs=16, at=(0, 0, 16.5), region=R_GOLD_FINIAL)
    reg_cyl("GoldFinialSphere", r=0.85, h=1.2, segs=20, at=(0, 0, 17.0), region=R_GOLD_FINIAL)
    reg_cyl("GoldFinialSpireTip", r=0.2, h=0.8, segs=12, at=(0, 0, 18.2), region=R_GOLD_FINIAL)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Temple_Of_Heaven")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_temple_of_heaven_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_temple_of_heaven.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_temple_of_heaven.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_temple_of_heaven_preview.png")
        shutil.copy2(OUT_DIR / "atlas_temple_of_heaven.png", TEXTURES_DIR / "atlas_temple_of_heaven.png")
        print(f"[TempleOfHeaven] deployed successfully.")
    except Exception as e:
        print(f"[TempleOfHeaven] deploy notice: {e}")


if __name__ == "__main__":
    main()
