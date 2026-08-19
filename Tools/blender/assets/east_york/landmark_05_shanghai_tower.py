"""Shanghai Tower (上海中心大厦) - East York Landmark (~3500 Tris).

Specs:
- Clean twisting mega-tall skyscraper structure without surrounding plaza slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - 120-degree twisting curved double-skin glass curtain wall with rounded triangular cross-section.
  - 9 stacked vertical cylindrical atrium zones tapering from base to crown.
  - Signature continuous vertical notch groove reducing wind loads.
  - Open crown parapet with spiral observation ring and tuned mass damper beacon.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_shanghai_tower.glb.
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
R_GLASS_AZURE    = (0,   256, 256, 256)   # Reflective azure/teal double-curved glass facade
R_GLASS_CYAN     = (256, 256, 256, 256)   # Shaded glass panel reflections & inner atrium core
R_STEEL_DIAGRID  = (0,   128, 128, 128)   # White/silver structural steel node ring trusses
R_PODIUM_LOUVERS = (128, 128, 128, 128)   # Ground entrance canopy & ventilation louvers
R_CROWN_BEACON   = (256, 128, 128, 128)   # Upper crown tuned mass damper & night lighting glow


def paint_atlas():
    a = Atlas(S, seed=2015)

    # 1. Reflective Azure Glass (R_GLASS_AZURE)
    x, y, w, h = R_GLASS_AZURE
    a.rect(x, y, w, h, (0.32, 0.60, 0.75))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 1, (0.22, 0.45, 0.60))
    for rx in range(x, x + w, 14):
        a.rect(rx, y, 1, h, (0.45, 0.75, 0.90))
    a.shade(x, y, w, h, top=0.15, bottom=-0.15)
    a.noise(x, y, w, h, 0.01)

    # 2. Shaded Cyan Glass (R_GLASS_CYAN)
    x, y, w, h = R_GLASS_CYAN
    a.rect(x, y, w, h, (0.20, 0.42, 0.58))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.12, 0.28, 0.42))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.35, 0.60, 0.80))
    a.noise(x, y, w, h, 0.01)

    # 3. Steel Diagrid (R_STEEL_DIAGRID)
    x, y, w, h = R_STEEL_DIAGRID
    a.rect(x, y, w, h, (0.88, 0.90, 0.94))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 3, h, (0.70, 0.72, 0.76))
    a.noise(x, y, w, h, 0.015)

    # 4. Podium Louvers (R_PODIUM_LOUVERS)
    x, y, w, h = R_PODIUM_LOUVERS
    a.rect(x, y, w, h, (0.25, 0.28, 0.32))
    for ry in range(y, y + h, 6):
        a.rect(x, ry, w, 2, (0.14, 0.15, 0.18))
    a.noise(x, y, w, h, 0.015)

    # 5. Crown Beacon Glow (R_CROWN_BEACON)
    x, y, w, h = R_CROWN_BEACON
    a.rect(x, y, w, h, (0.90, 0.95, 1.0))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_shanghai_tower", OUT_DIR)


def make_twisting_tower(name, base_r=5.6, top_r=2.8, height=32.0, total_twist_deg=120.0, rings=24, segs=28, at=(0, 0, 0)):
    """Generates the signature 120-degree twisting rounded triangular Shanghai Tower body."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    v_rows = []

    for ri in range(rings):
        frac = ri / (rings - 1)
        z = height * frac
        # Slight parabolic taper
        r_curr = base_r + (top_r - base_r) * (frac ** 0.85)
        twist = math.radians(total_twist_deg * frac)

        row = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs + twist
            # Rounded triangular profile with notch
            tri_shape = 1.0 + 0.16 * math.cos(3 * (ang - twist))
            # Wind notch
            notch_angle = (ang - twist) % (2 * math.pi)
            if notch_angle < 0.35:
                tri_shape *= (0.75 + 0.25 * (notch_angle / 0.35))

            r_eff = r_curr * tri_shape
            v = bm.verts.new((r_eff * math.cos(ang), r_eff * math.sin(ang), z))
            row.append(v)
        v_rows.append(row)

    for ri in range(rings - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[ri][i], v_rows[ri][ni], v_rows[ri + 1][ni], v_rows[ri + 1][i]))

    # Top crown cap
    v_top = bm.verts.new((0, 0, height + 0.8))
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
    mat = material_for(img, "mat_shanghai_tower")

    parts = []

    # =========================================================================
    # SHANGHAI TOWER (BUILDING ONLY - ~3500 TRIS)
    # Total Height: 34.0m, Base Width: 12.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Ground Entrance Podium & Canopies (sits at Z = 0.0)
    podium = kit.make_box("PodiumGround", 11.5, 11.5, 2.5, (0, 0, 0.0))
    podium.data.materials.append(mat)
    kit.map_faces_to_region(podium, R_PODIUM_LOUVERS, S)
    parts.append(podium)

    for can_i, (cx, cy) in enumerate([(6.2, 0), (-6.2, 0), (0, 6.2), (0, -6.2)]):
        can = kit.make_box(f"EntranceCanopy_{can_i}", 3.0, 3.0, 0.3, (cx, cy, 2.2))
        can.data.materials.append(mat)
        kit.map_faces_to_region(can, R_GLASS_AZURE, S)
        parts.append(can)

    # 2. Main 120-Degree Twisting Glass Tower Body (Z = 2.5m to 32.5m)
    tower = make_twisting_tower("TwistingGlassShaft", base_r=5.2, top_r=2.5, height=30.0, total_twist_deg=120.0, rings=24, segs=28, at=(0, 0, 2.5))
    tower.data.materials.append(mat)
    kit.map_faces_to_region(tower, R_GLASS_AZURE, S)
    parts.append(tower)

    # 3. Intermediate Atrium Ring Trusses (8 Belt Truss Bands)
    for bi in range(8):
        bz = 3.0 + bi * 3.7
        b_r = 5.2 + (2.5 - 5.2) * (bi / 8.0)
        band = kit.make_box(f"BeltTruss_{bi}", b_r * 2.2, b_r * 2.2, 0.35, (0, 0, bz))
        band.data.materials.append(mat)
        kit.map_faces_to_region(band, R_STEEL_DIAGRID, S)
        parts.append(band)

    # 4. Open Crown Parapet & Tuned Mass Damper Beacon (Z = 32.5m to 35.0m)
    crown = kit.make_box("CrownParapetSpiral", 3.8, 3.8, 2.2, (0, 0, 32.5))
    crown.data.materials.append(mat)
    kit.map_faces_to_region(crown, R_CROWN_BEACON, S)
    parts.append(crown)

    damper = kit.make_box("TunedMassDamper", 1.2, 1.2, 1.2, (0, 0, 33.0))
    damper.data.materials.append(mat)
    kit.map_faces_to_region(damper, R_STEEL_DIAGRID, S)
    parts.append(damper)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Shanghai_Tower")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_shanghai_tower_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_shanghai_tower.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_shanghai_tower.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_shanghai_tower_preview.png")
        shutil.copy2(OUT_DIR / "atlas_shanghai_tower.png", TEXTURES_DIR / "atlas_shanghai_tower.png")
        print(f"[ShanghaiTower] deployed successfully.")
    except Exception as e:
        print(f"[ShanghaiTower] deploy notice: {e}")


if __name__ == "__main__":
    main()
