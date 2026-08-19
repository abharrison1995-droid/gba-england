"""The Gherkin (30 St Mary Axe) - Building Only.

Specs:
- Clean skyscraper structure without surrounding plaza slab or pavement.
- Sits directly at Z = 0.0.
- Parametric aerodynamic curved body with diagrid nodes, spiraling dark and light glass bands,
  glass dome apex lens cap, and ground-level diamond-faceted colonnade.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_the_gherkin.glb.
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
R_LIGHT_GLASS     = (0,   256, 256, 256)   # Reflective light cyan diagrid glass panels
R_DARK_GLASS      = (256, 256, 256, 256)   # Dark obsidian spiraling ventilation glass bands
R_DIAGRID_WHITE   = (0,   128, 128, 128)   # White structural steel diagrid node lines
R_DOME_LENS       = (128, 128, 128, 128)   # Top glass dome apex lens cap
R_COLONNADE       = (256, 128, 128, 128)   # Ground plaza retail colonnade & diamond entrance


def paint_atlas():
    a = Atlas(S, seed=2004)

    # 1. Light Diagrid Glass (R_LIGHT_GLASS)
    x, y, w, h = R_LIGHT_GLASS
    a.rect(x, y, w, h, (0.42, 0.65, 0.78))
    for gy in range(y, y + h, 16):
        a.rect(x, gy, w, 1, (0.30, 0.50, 0.65))
    for gx in range(x, x + w, 16):
        a.rect(gx, y, 1, h, (0.55, 0.78, 0.90))
    a.shade(x, y, w, h, top=0.12, bottom=-0.12)
    a.noise(x, y, w, h, 0.01)

    # 2. Dark Obsidian Spiraling Glass (R_DARK_GLASS)
    x, y, w, h = R_DARK_GLASS
    a.rect(x, y, w, h, (0.14, 0.18, 0.24))
    for gy in range(y, y + h, 16):
        a.rect(x, gy, w, 1, (0.08, 0.10, 0.14))
    for gx in range(x, x + w, 16):
        a.rect(gx, y, 1, h, (0.22, 0.28, 0.36))
    a.noise(x, y, w, h, 0.01)

    # 3. White Diagrid Nodes (R_DIAGRID_WHITE)
    x, y, w, h = R_DIAGRID_WHITE
    a.rect(x, y, w, h, (0.90, 0.92, 0.95))
    a.noise(x, y, w, h, 0.015)

    # 4. Dome Lens (R_DOME_LENS)
    x, y, w, h = R_DOME_LENS
    a.rect(x, y, w, h, (0.25, 0.35, 0.45))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, (0.85, 0.90, 0.95))
    a.disc(cx, cy, 32, (0.45, 0.60, 0.75))
    a.disc(cx, cy, 16, (0.15, 0.22, 0.30))
    a.noise(x, y, w, h, 0.01)

    # 5. Colonnade Entrances (R_COLONNADE)
    x, y, w, h = R_COLONNADE
    a.rect(x, y, w, h, (0.20, 0.22, 0.25))
    for rx in range(x + 10, x + w - 10, 24):
        a.rect(rx, y + 6, 16, h - 12, (0.75, 0.85, 0.95))
        a.rect(rx + 6, y + 6, 4, h - 12, (0.15, 0.16, 0.18))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_the_gherkin", OUT_DIR)


def make_gherkin_tower(name, base_r=3.8, max_r=5.5, top_r=0.6, height=26.0, rings=16, segs=24, at=(0, 0, 0)):
    """Generates the signature curved aerodynamic Gherkin body with spiral diagrid facets."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    v_rows = []

    for ri in range(rings):
        frac = ri / (rings - 1)
        z = height * frac
        if frac < 0.32:
            t = frac / 0.32
            r_curr = base_r + (max_r - base_r) * math.sin(t * math.pi / 2)
        else:
            t = (frac - 0.32) / 0.68
            r_curr = max_r * math.cos(t * math.pi * 0.46) + top_r * (1.0 - math.cos(t * math.pi * 0.46))

        row = []
        for i in range(segs):
            twist = ri * (math.pi / 12)
            ang = 2 * math.pi * i / segs + twist
            v = bm.verts.new((r_curr * math.cos(ang), r_curr * math.sin(ang), z))
            row.append(v)
        v_rows.append(row)

    for ri in range(rings - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[ri][i], v_rows[ri][ni], v_rows[ri + 1][ni], v_rows[ri + 1][i]))

    v_apex = bm.verts.new((0, 0, height + 0.6))
    for i in range(segs):
        ni = (i + 1) % segs
        bm.faces.new((v_rows[-1][i], v_rows[-1][ni], v_apex))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_the_gherkin")

    parts = []

    # =========================================================================
    # THE GHERKIN (BUILDING ONLY - NO PLAZA SLAB)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Ground Level Retail Colonnade & Diamond Entrances (sits at Z = 0.0)
    col_ring = kit.make_box("PlazaColonnadeRing", 8.2, 8.2, 2.2, (0, 0, 0.0))
    col_ring.data.materials.append(mat)
    kit.map_faces_to_region(col_ring, R_COLONNADE, S)
    parts.append(col_ring)

    # 12 V-Columns around ground perimeter (sits at Z = 0.0)
    for ci in range(12):
        ang = 2 * math.pi * ci / 12
        cx = 4.0 * math.cos(ang)
        cy = 4.0 * math.sin(ang)
        col = kit.make_box(f"VColumn_{ci}", 0.35, 0.35, 2.2, (cx, cy, 0.0))
        col.rotation_euler = (0, 0, ang)
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_DIAGRID_WHITE, S)
        parts.append(col)

    # 2. Main Aerodynamic Curved Gherkin Tower (Z: 2.2m to 27.2m)
    tower = make_gherkin_tower("GherkinTowerMain", base_r=3.8, max_r=5.6, top_r=0.8, height=25.0, rings=16, segs=24, at=(0, 0, 2.2))
    tower.data.materials.append(mat)
    kit.map_faces_to_region(tower, R_LIGHT_GLASS, S)
    parts.append(tower)

    # 3. Glass Apex Lens Cap (Z: 27.2m)
    lens = kit.make_box("ApexLensCap", 1.4, 1.4, 0.4, (0, 0, 27.4))
    lens.data.materials.append(mat)
    kit.map_faces_to_region(lens, R_DOME_LENS, S)
    parts.append(lens)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_The_Gherkin")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_the_gherkin_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_the_gherkin.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_the_gherkin.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_the_gherkin_preview.png")
        shutil.copy2(OUT_DIR / "atlas_the_gherkin.png", TEXTURES_DIR / "atlas_the_gherkin.png")
        print(f"[TheGherkin] clean building deployed.")
    except Exception as e:
        print(f"[TheGherkin] deploy notice: {e}")


if __name__ == "__main__":
    main()
