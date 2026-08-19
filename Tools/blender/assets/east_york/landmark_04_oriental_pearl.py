"""Oriental Pearl Tower (东方明珠广播电视塔) - East York Landmark (~3500 Tris).

Specs:
- Clean sci-fi TV tower structure without surrounding plaza slabs or pavement.
- Sits directly at Z = 0.0 with 3 massive inclined support tripod legs.
- Architectural Features:
  - 3 large cylindrical inclined support legs meeting at ground level.
  - Lower Sphere (Lower Pearl, 50m observation level).
  - Central 3-column elevator core with 5 intermediate spherical modules.
  - Upper Sphere (Upper Pearl, revolving restaurant & glass sightseeing deck).
  - Space Capsule observation pod and top broadcast antenna mast spire reaching 35m.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_oriental_pearl_tower.glb.
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
R_PEARL_MAGENTA  = (0,   256, 256, 256)   # Signature metallic ruby/magenta pearl glass spherical shell
R_CONCRETE_WHITE = (256, 256, 256, 256)   # Architectural white reinforced concrete columns & legs
R_OBSERVATION    = (0,   128, 128, 128)   # Panoramic 360-degree glass viewing strips & glow
R_ANTENNA_STEEL  = (128, 128, 128, 128)   # Red & white striped broadcast transmission antenna mast
R_TRIPOD_TRUSS   = (256, 128, 128, 128)   # Diagonal tripod base braces & space frame lattice


def paint_atlas():
    a = Atlas(S, seed=1994)

    # 1. Ruby/Magenta Metallic Pearl Sphere (R_PEARL_MAGENTA)
    x, y, w, h = R_PEARL_MAGENTA
    a.rect(x, y, w, h, (0.78, 0.22, 0.42))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.60, 0.14, 0.32))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.90, 0.35, 0.55))
    a.shade(x, y, w, h, top=0.15, bottom=-0.15)
    a.noise(x, y, w, h, 0.015)

    # 2. White Concrete Legs (R_CONCRETE_WHITE)
    x, y, w, h = R_CONCRETE_WHITE
    a.rect(x, y, w, h, (0.92, 0.92, 0.94))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.78, 0.80, 0.84))
    a.noise(x, y, w, h, 0.012)

    # 3. Observation Glass (R_OBSERVATION)
    x, y, w, h = R_OBSERVATION
    a.rect(x, y, w, h, (0.18, 0.28, 0.42))
    for rx in range(x, x + w, 12):
        a.rect(rx, y + 10, 8, h - 20, (0.45, 0.70, 0.90))
    a.noise(x, y, w, h, 0.01)

    # 4. Antenna Steel (R_ANTENNA_STEEL)
    x, y, w, h = R_ANTENNA_STEEL
    a.rect(x, y, w, h, (0.95, 0.95, 0.95))
    for ry in range(y, y + h, 24):
        a.rect(x, ry, w, 12, (0.85, 0.20, 0.20))
    a.noise(x, y, w, h, 0.015)

    # 5. Tripod Braces (R_TRIPOD_TRUSS)
    x, y, w, h = R_TRIPOD_TRUSS
    a.rect(x, y, w, h, (0.80, 0.82, 0.86))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 3, h, (0.65, 0.68, 0.72))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_oriental_pearl", OUT_DIR)


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


def make_sphere(name, r, rings=12, segs=20, at=(0, 0, 0)):
    """Parametric sphere module for Pearl towers."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    v_rows = []
    for ri in range(rings):
        phi = math.pi * ri / (rings - 1)
        z = -r * math.cos(phi)
        r_curr = r * math.sin(phi)
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


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_oriental_pearl")

    parts = []

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_CONCRETE_WHITE):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_sphere(name, r, rings=12, segs=20, at=(0, 0, 0), region=R_PEARL_MAGENTA):
        o = make_sphere(name, r, rings, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # ORIENTAL PEARL TV TOWER (~3500 TRIS)
    # Total Height: 35.0m, Base Width: 12.0m
    # Sits directly on Z = 0.0 with 3 tripod legs
    # =========================================================================

    # 1. Three Massive Inclined Support Tripod Legs (sits at Z = 0.0)
    for li in range(3):
        ang = 2 * math.pi * li / 3
        # Ground foot at r = 5.2m
        lx = 5.2 * math.cos(ang)
        ly = 5.2 * math.sin(ang)
        foot = kit.make_box(f"TripodFoot_{li}", 1.8, 1.8, 1.2, (lx, ly, 0.0))
        foot.data.materials.append(mat)
        kit.map_faces_to_region(foot, R_CONCRETE_WHITE, S)
        parts.append(foot)

        # Inclined leg column (Z = 0.5 to 8.5m)
        leg = reg_cyl(f"TripodLeg_{li}", r=0.55, h=8.0, segs=14, at=(lx * 0.55, ly * 0.55, 0.5), region=R_CONCRETE_WHITE)
        # Incline rotation
        leg.rotation_euler = (-0.18 * math.sin(ang), 0.18 * math.cos(ang), 0)

    # Central Tripod Base Hub (Z = 0.0 to 8.5m)
    reg_cyl("TripodBaseHub", r=2.2, h=8.5, segs=20, at=(0, 0, 0.0), region=R_CONCRETE_WHITE)

    # 2. Lower Sphere (Lower Pearl, Diameter 6.0m at Z = 11.5m)
    lower_pearl = reg_sphere("LowerPearlSphere", r=3.0, rings=16, segs=24, at=(0, 0, 11.5), region=R_PEARL_MAGENTA)
    # Observation Ring around equator
    reg_cyl("LowerPearlObservationRing", r=3.1, h=0.8, segs=24, at=(0, 0, 11.1), region=R_OBSERVATION)

    # 3. Three Vertical Column Shafts (Z = 14.5m to 21.5m)
    for ci in range(3):
        ang = 2 * math.pi * ci / 3 + math.pi / 6
        cx = 1.4 * math.cos(ang)
        cy = 1.4 * math.sin(ang)
        reg_cyl(f"ShaftCol_{ci}", r=0.38, h=7.0, segs=12, at=(cx, cy, 14.5), region=R_CONCRETE_WHITE)

    # 5 Small Intermediate Spheres along central shaft
    for si in range(5):
        sz = 15.5 + si * 1.2
        reg_sphere(f"SmallSphere_{si}", r=0.75, rings=8, segs=14, at=(0, 0, sz), region=R_PEARL_MAGENTA)

    # 4. Upper Sphere (Upper Pearl, Diameter 4.6m at Z = 23.5m)
    reg_sphere("UpperPearlSphere", r=2.3, rings=14, segs=22, at=(0, 0, 23.5), region=R_PEARL_MAGENTA)
    reg_cyl("UpperPearlObservationRing", r=2.4, h=0.7, segs=24, at=(0, 0, 23.15), region=R_OBSERVATION)

    # 5. Space Capsule Sightseeing Pod (Z = 27.2m)
    reg_sphere("SpaceCapsuleSphere", r=1.1, rings=10, segs=16, at=(0, 0, 27.2), region=R_PEARL_MAGENTA)

    # 6. Broadcast Transmission Antenna Mast Spire (Z = 28.3m to 35.0m)
    reg_cyl("AntennaMastBase", r=0.45, h=2.0, segs=12, at=(0, 0, 28.3), region=R_ANTENNA_STEEL)
    reg_cyl("AntennaMastMid",  r=0.25, h=2.5, segs=10, at=(0, 0, 30.3), region=R_ANTENNA_STEEL)
    reg_cyl("AntennaMastTip",  r=0.10, h=2.2, segs=8,  at=(0, 0, 32.8), region=R_ANTENNA_STEEL)

    # Antenna Cross Trusses
    box1 = kit.make_box("AntennaCross1", 1.8, 0.1, 0.1, (0, 0, 31.5))
    box1.data.materials.append(mat)
    kit.map_faces_to_region(box1, R_ANTENNA_STEEL, S)
    parts.append(box1)

    box2 = kit.make_box("AntennaCross2", 0.1, 1.8, 0.1, (0, 0, 31.5))
    box2.data.materials.append(mat)
    kit.map_faces_to_region(box2, R_ANTENNA_STEEL, S)
    parts.append(box2)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Oriental_Pearl")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_oriental_pearl_tower_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_oriental_pearl_tower.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_oriental_pearl_tower.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_oriental_pearl_tower_preview.png")
        shutil.copy2(OUT_DIR / "atlas_oriental_pearl.png", TEXTURES_DIR / "atlas_oriental_pearl.png")
        print(f"[OrientalPearl] deployed successfully.")
    except Exception as e:
        print(f"[OrientalPearl] deploy notice: {e}")


if __name__ == "__main__":
    main()
