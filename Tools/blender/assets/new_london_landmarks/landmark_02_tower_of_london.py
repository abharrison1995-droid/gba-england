"""Tower of London (The White Tower Keep) - Building Only.

Specs:
- Clean fortress keep structure without surrounding courtyard slabs, plinths, or pavement.
- Sits directly at Z = 0.0.
- Norman Caen stone keep with 4 corner turrets (including rounded NE turret with onion dome),
  crenellated parapets, pilaster buttresses, and forebuilding entrance.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_tower_of_london.glb.
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
R_WHITE_STONE    = (0,   256, 256, 256)   # White Caen stone & Kentish ragstone fortress masonry
R_DARK_STONE     = (256, 256, 256, 256)   # Weathered masonry & stone steps
R_TURRET_LEAD    = (0,   128, 128, 128)   # Lead onion dome turret caps & weather vanes
R_NORMAN_WINDOWS = (128, 128, 128, 128)   # Round-arched Norman slit & double windows
R_TIMBER_DOOR    = (256, 128, 128, 128)   # Heavy oak studded doors & portcullis iron grates


def paint_atlas():
    a = Atlas(S, seed=1078)

    # 1. White Caen Stone (R_WHITE_STONE)
    x, y, w, h = R_WHITE_STONE
    a.rect(x, y, w, h, (0.85, 0.83, 0.78))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.75, 0.73, 0.68))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.78, 0.76, 0.71))
    a.noise(x, y, w, h, 0.02)

    # 2. Weathered Dark Stone (R_DARK_STONE)
    x, y, w, h = R_DARK_STONE
    a.rect(x, y, w, h, (0.50, 0.48, 0.45))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.38, 0.36, 0.34))
    a.noise(x, y, w, h, 0.025)

    # 3. Turret Lead Dome (R_TURRET_LEAD)
    x, y, w, h = R_TURRET_LEAD
    a.rect(x, y, w, h, (0.32, 0.36, 0.40))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 1, (0.24, 0.28, 0.32))
    a.noise(x, y, w, h, 0.015)

    # 4. Norman Windows (R_NORMAN_WINDOWS)
    x, y, w, h = R_NORMAN_WINDOWS
    a.rect(x, y, w, h, (0.80, 0.78, 0.74))
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 20):
            a.rect(wx, wy, 12, 18, (0.12, 0.14, 0.18))
            a.disc(wx + 6, wy + 16, 6, (0.12, 0.14, 0.18))
    a.noise(x, y, w, h, 0.012)

    # 5. Timber Doors & Ironwork (R_TIMBER_DOOR)
    x, y, w, h = R_TIMBER_DOOR
    a.rect(x, y, w, h, (0.35, 0.22, 0.12))
    for rx in range(x, x + w, 12):
        a.rect(rx, y, 2, h, (0.22, 0.14, 0.08))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_tower_of_london", OUT_DIR)


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


def make_turret_dome(name, r, h, segs=16, at=(0, 0, 0)):
    """Lead onion-domed cupola cap."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = 6
    v_rows = []
    for ri in range(rings):
        frac = ri / (rings - 1)
        z = h * frac
        r_curr = r * math.sin(frac * math.pi * 0.85 + 0.15) * 1.15 if frac < 0.7 else r * (1.0 - frac) * 2.0
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

    v_top = bm.verts.new((0, 0, h + 0.3))
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
    mat = material_for(img, "mat_tower_london")

    parts = []

    def reg_box(name, w, d, h, at, region=R_WHITE_STONE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_WHITE_STONE):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # TOWER OF LONDON (WHITE TOWER KEEP ONLY - NO SURROUNDING PLAZA/GROUND)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Main White Tower Norman Keep Body (10m x 10m x 9.5m)
    reg_box("WhiteTowerKeep", 10.0, 10.0, 9.5, (0, 0, 0.0), region=R_NORMAN_WINDOWS)

    # Cross Pilaster Buttresses on Keep Faces
    for side_i, (px, py, pw, pd) in enumerate([
        (0, -5.15, 2.2, 0.3),
        (0,  5.15, 2.2, 0.3),
        (-5.15, 0, 0.3, 2.2),
        ( 5.15, 0, 0.3, 2.2),
    ]):
        reg_box(f"KeepPilaster_{side_i}", pw, pd, 9.8, (px, py, 0.0), region=R_WHITE_STONE)

    # 2. Four Corner Turrets:
    # NW, SW, SE: Square Turrets (Z = 0.0 to 12.5m)
    square_turrets = [
        ("Turret_NW", -5.0, -5.0),
        ("Turret_SW", -5.0,  5.0),
        ("Turret_SE",  5.0,  5.0),
    ]
    for t_name, tx, ty in square_turrets:
        reg_box(f"{t_name}_Shaft", 2.6, 2.6, 12.5, (tx, ty, 0.0), region=R_WHITE_STONE)
        reg_box(f"{t_name}_Crown", 2.8, 2.8, 0.8, (tx, ty, 12.5), region=R_WHITE_STONE)
        dome = make_turret_dome(f"{t_name}_Dome", r=1.35, h=2.6, segs=18, at=(tx, ty, 13.3))
        dome.data.materials.append(mat)
        kit.map_faces_to_region(dome, R_TURRET_LEAD, S)
        parts.append(dome)

    # NE Turret: Famous Rounded Turret (Z = 0.0 to 12.5m)
    reg_cyl("Turret_NE_Shaft", r=1.65, h=12.5, segs=20, at=(5.0, -5.0, 0.0), region=R_WHITE_STONE)
    reg_cyl("Turret_NE_Crown", r=1.80, h=0.8, segs=20, at=(5.0, -5.0, 12.5), region=R_WHITE_STONE)
    ne_dome = make_turret_dome("Turret_NE_Dome", r=1.70, h=2.9, segs=20, at=(5.0, -5.0, 13.3))
    ne_dome.data.materials.append(mat)
    kit.map_faces_to_region(ne_dome, R_TURRET_LEAD, S)
    parts.append(ne_dome)

    # 3. Crenellated Parapet Battlements along Keep Roof
    for bi in range(6):
        bx = -3.8 + bi * 1.5
        reg_box(f"Merlon_F_{bi}", 0.8, 0.35, 0.9, (bx, -5.1, 9.5), region=R_WHITE_STONE)
        reg_box(f"Merlon_B_{bi}", 0.8, 0.35, 0.9, (bx,  5.1, 9.5), region=R_WHITE_STONE)
        reg_box(f"Merlon_L_{bi}", 0.35, 0.8, 0.9, (-5.1, bx, 9.5), region=R_WHITE_STONE)
        reg_box(f"Merlon_R_{bi}", 0.35, 0.8, 0.9, ( 5.1, bx, 9.5), region=R_WHITE_STONE)

    # 4. External Norman Forebuilding Entrance Staircase
    reg_box("EntranceForebuilding", 3.0, 2.5, 4.8, (-2.5, -6.0, 0.0), region=R_WHITE_STONE)
    for step_i in range(5):
        reg_box(f"StoneStep_{step_i}", 2.2, 0.5, 0.3, (-2.5, -7.0 - step_i * 0.45, 0.0 + step_i * 0.3), region=R_DARK_STONE)
    reg_box("EntrancePortcullis", 1.4, 0.2, 2.2, (-2.5, -7.2, 1.5), region=R_TIMBER_DOOR)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Tower_Of_London")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_tower_of_london_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_tower_of_london.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_tower_of_london.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_tower_of_london_preview.png")
        shutil.copy2(OUT_DIR / "atlas_tower_of_london.png", TEXTURES_DIR / "atlas_tower_of_london.png")
        print(f"[TowerOfLondon] clean building deployed.")
    except Exception as e:
        print(f"[TowerOfLondon] deploy notice: {e}")


if __name__ == "__main__":
    main()
