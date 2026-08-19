"""Canton Tower (广州塔 / 小蛮腰) - East York Landmark (~3500 Tris).

Specs:
- Clean hyperbolic twisted lattice tower structure without surrounding plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - Hyperboloid twisted lattice structure with a signature narrow "slim waist" at mid-height.
  - 16 inclined diagonal outer steel columns forming an open twisting diagrid framework.
  - Central cylindrical elliptical elevator and observation core.
  - Slanted rooftop open-air observation deck with high-altitude Bubble Tram track.
  - Broadcast antenna mast spire reaching 36m.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_canton_tower.glb.
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
R_LATTICE_STEEL  = (0,   256, 256, 256)   # Silver/white structural steel diagrid lattice
R_CORE_GLASS     = (256, 256, 256, 256)   # Semi-translucent azure glass elevator core
R_ILLUMINATION   = (0,   128, 128, 128)   # Rainbow LED RGB lighting gradient bands
R_ROOF_DECK      = (128, 128, 128, 128)   # Slanted rooftop observation deck & bubble tram
R_ANTENNA_MAST   = (256, 128, 128, 128)   # Broadcast antenna mast & navigation beacon


def paint_atlas():
    a = Atlas(S, seed=2010)

    # 1. Lattice Steel (R_LATTICE_STEEL)
    x, y, w, h = R_LATTICE_STEEL
    a.rect(x, y, w, h, (0.92, 0.94, 0.96))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 3, h, (0.72, 0.75, 0.80))
    a.noise(x, y, w, h, 0.015)

    # 2. Core Glass (R_CORE_GLASS)
    x, y, w, h = R_CORE_GLASS
    a.rect(x, y, w, h, (0.22, 0.45, 0.65))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.14, 0.30, 0.48))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.35, 0.62, 0.82))
    a.noise(x, y, w, h, 0.01)

    # 3. Rainbow LED Illumination (R_ILLUMINATION)
    x, y, w, h = R_ILLUMINATION
    a.rect(x, y, w, h, (0.85, 0.35, 0.65))
    for ry in range(y, y + h, 16):
        col = (
            0.5 + 0.4 * math.sin(ry * 0.05),
            0.5 + 0.4 * math.sin(ry * 0.05 + 2.0),
            0.5 + 0.4 * math.sin(ry * 0.05 + 4.0),
        )
        a.rect(x, ry, w, 8, col)
    a.noise(x, y, w, h, 0.015)

    # 4. Roof Deck & Bubble Tram (R_ROOF_DECK)
    x, y, w, h = R_ROOF_DECK
    a.rect(x, y, w, h, (0.45, 0.48, 0.52))
    for rx in range(x + 10, x + w, 24):
        a.disc(rx, y + h // 2, 8, (0.90, 0.75, 0.20))
    a.noise(x, y, w, h, 0.015)

    # 5. Antenna Mast (R_ANTENNA_MAST)
    x, y, w, h = R_ANTENNA_MAST
    a.rect(x, y, w, h, (0.88, 0.90, 0.92))
    for ry in range(y, y + h, 20):
        a.rect(x, ry, w, 8, (0.85, 0.15, 0.15))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_canton_tower", OUT_DIR)


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


def make_hyperboloid_lattice(name, base_r=5.2, waist_r=2.2, top_r=3.8, height=28.0, waist_frac=0.62, twist_deg=45.0, segs=18, at=(0, 0, 0)):
    """Generates the open twisted hyperboloid diagrid lattice of the Canton Tower."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = 14
    v_rows = []

    for ri in range(rings):
        frac = ri / (rings - 1)
        z = height * frac

        # Hyperbolic profile calculation
        if frac <= waist_frac:
            t = frac / waist_frac
            r_curr = base_r + (waist_r - base_r) * math.sin(t * math.pi / 2)
        else:
            t = (frac - waist_frac) / (1.0 - waist_frac)
            r_curr = waist_r + (top_r - waist_r) * math.sin(t * math.pi / 2)

        twist = math.radians(twist_deg * frac)
        row = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs + twist
            v = bm.verts.new((r_curr * math.cos(ang), r_curr * math.sin(ang), z))
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
    mat = material_for(img, "mat_canton_tower")

    parts = []

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_CORE_GLASS):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # CANTON TOWER (BUILDING ONLY - ~3500 TRIS)
    # Total Height: 36.0m, Base Width: 11.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Ground Entrance Base Ring (sits at Z = 0.0)
    reg_cyl("PlazaBaseRing", r=5.4, h=1.8, segs=24, at=(0, 0, 0.0), region=R_ROOF_DECK)

    # 2. Central Glass Observation & Elevator Core (Z = 1.8m to 28.0m)
    # Lower Core
    reg_cyl("CoreShaft_Lower", r=2.6, h=15.0, segs=20, at=(0, 0, 1.8), region=R_CORE_GLASS)
    # Waist Core
    reg_cyl("CoreShaft_Waist", r=1.6, h=6.0, segs=18, at=(0, 0, 16.8), region=R_ILLUMINATION)
    # Upper Observation Core
    reg_cyl("CoreShaft_Upper", r=2.4, h=5.2, segs=20, at=(0, 0, 22.8), region=R_CORE_GLASS)

    # 3. Outer Hyperbolic Twisted Diagrid Steel Lattice (Z = 0.0 to 28.0m)
    lattice = make_hyperboloid_lattice("OuterDiagridLattice", base_r=5.2, waist_r=2.0, top_r=3.6, height=28.0, waist_frac=0.62, twist_deg=45.0, segs=20, at=(0, 0, 0.0))
    lattice.data.materials.append(mat)
    kit.map_faces_to_region(lattice, R_LATTICE_STEEL, S)
    parts.append(lattice)

    # 4. Slanted Rooftop Observation Deck & Bubble Tram (Z = 28.0m to 29.5m)
    roof_deck = reg_cyl("RooftopObservationDeck", r=3.8, h=1.5, segs=24, at=(0, 0, 28.0), region=R_ROOF_DECK)
    roof_deck.rotation_euler = (0.08, -0.06, 0)

    # 8 Bubble Tram Sightseeing Pods on Roof Ellipse
    for bi in range(8):
        ang = 2 * math.pi * bi / 8
        bx = 3.4 * math.cos(ang)
        by = 3.4 * math.sin(ang)
        pod = kit.make_box(f"BubbleTramPod_{bi}", 0.6, 0.6, 0.5, (bx, by, 29.6))
        pod.data.materials.append(mat)
        kit.map_faces_to_region(pod, R_ILLUMINATION, S)
        parts.append(pod)

    # 5. Broadcast Antenna Mast Spire (Z = 29.5m to 36.0m)
    reg_cyl("AntennaBase", r=0.5, h=2.5, segs=14, at=(0, 0, 29.5), region=R_ANTENNA_MAST)
    reg_cyl("AntennaMid",  r=0.25, h=2.2, segs=10, at=(0, 0, 32.0), region=R_ANTENNA_MAST)
    reg_cyl("AntennaTip",  r=0.10, h=1.8, segs=8,  at=(0, 0, 34.2), region=R_ANTENNA_MAST)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Canton_Tower")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_canton_tower_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_canton_tower.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_canton_tower.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_canton_tower_preview.png")
        shutil.copy2(OUT_DIR / "atlas_canton_tower.png", TEXTURES_DIR / "atlas_canton_tower.png")
        print(f"[CantonTower] deployed successfully.")
    except Exception as e:
        print(f"[CantonTower] deploy notice: {e}")


if __name__ == "__main__":
    main()
