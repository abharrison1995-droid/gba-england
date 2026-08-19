"""The Shard - Building Only.

Specs:
- Clean skyscraper structure without surrounding plaza slab or pavement.
- Sits directly at Z = 0.0.
- 8-faceted crystalline glass pyramid with fragmented open spire pinnacle blades,
  multi-tier setback glass facade sections, and canted concourse canopies.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_the_shard.glb.
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
R_SHARD_GLASS_A   = (0,   256, 256, 256)   # Reflective azure/cyan glass curtain wall
R_SHARD_GLASS_B   = (256, 256, 256, 256)   # Dark indigo reflective glass shard facets
R_STEEL_MULLIONS  = (0,   128, 128, 128)   # White/silver structural steel framing & spire trusses
R_PODIUM_LOUVERS  = (128, 128, 128, 128)   # Ground concourse vents, louvers & canopy glass
R_NIGHT_GLOW      = (256, 128, 128, 128)   # Illuminated upper observation floors & spire beacon


def paint_atlas():
    a = Atlas(S, seed=2012)

    # 1. Reflective Azure Glass (R_SHARD_GLASS_A)
    x, y, w, h = R_SHARD_GLASS_A
    a.rect(x, y, w, h, (0.35, 0.58, 0.72))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.24, 0.42, 0.55))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.45, 0.70, 0.85))
    a.shade(x, y, w, h, top=0.15, bottom=-0.15)
    a.noise(x, y, w, h, 0.01)

    # 2. Dark Indigo Glass Shard (R_SHARD_GLASS_B)
    x, y, w, h = R_SHARD_GLASS_B
    a.rect(x, y, w, h, (0.20, 0.32, 0.48))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 2, (0.12, 0.20, 0.32))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.30, 0.45, 0.65))
    a.shade(x, y, w, h, top=0.10, bottom=-0.10)
    a.noise(x, y, w, h, 0.01)

    # 3. Steel Mullions & Trusses (R_STEEL_MULLIONS)
    x, y, w, h = R_STEEL_MULLIONS
    a.rect(x, y, w, h, (0.85, 0.88, 0.92))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 3, h, (0.65, 0.68, 0.72))
    a.noise(x, y, w, h, 0.015)

    # 4. Podium Louvers (R_PODIUM_LOUVERS)
    x, y, w, h = R_PODIUM_LOUVERS
    a.rect(x, y, w, h, (0.30, 0.32, 0.35))
    for ry in range(y, y + h, 6):
        a.rect(x, ry, w, 2, (0.15, 0.16, 0.18))
    a.noise(x, y, w, h, 0.015)

    # 5. Observation Night Glow (R_NIGHT_GLOW)
    x, y, w, h = R_NIGHT_GLOW
    a.rect(x, y, w, h, (0.90, 0.95, 1.0))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_the_shard", OUT_DIR)


def make_tapering_shard_tier(name, r_btm, r_top, z_btm, z_top, segs=8, at=(0, 0, 0)):
    """Parametric 8-faceted tapering glass tower tier."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    btm_verts = []
    top_verts = []

    for i in range(segs):
        ang = 2 * math.pi * i / segs
        rad_b = r_btm * (1.0 + 0.08 * math.sin(ang * 4))
        rad_t = r_top * (1.0 + 0.08 * math.sin(ang * 4))
        vb = bm.verts.new((rad_b * math.cos(ang), rad_b * math.sin(ang), z_btm))
        vt = bm.verts.new((rad_t * math.cos(ang), rad_t * math.sin(ang), z_top))
        btm_verts.append(vb)
        top_verts.append(vt)

    for i in range(segs):
        ni = (i + 1) % segs
        bm.faces.new((btm_verts[i], btm_verts[ni], top_verts[ni], top_verts[i]))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_the_shard")

    parts = []

    def reg_box(name, w, d, h, at, region=R_PODIUM_LOUVERS):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # THE SHARD (BUILDING ONLY - NO PLAZA SLAB)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Ground Concourse Podium & Canopies (sits at Z = 0.0)
    reg_box("PodiumConcourseA", 12.0, 12.0, 2.5, (0, 0, 0.0), region=R_PODIUM_LOUVERS)
    reg_box("PodiumCanopyEast", 4.0, 10.0, 0.3, (7.0, 0, 2.2), region=R_SHARD_GLASS_A)
    reg_box("PodiumCanopyWest", 4.0, 10.0, 0.3, (-7.0, 0, 2.2), region=R_SHARD_GLASS_A)

    # 2. Main 8-Faceted Tapering Glass Shaft (Z: 2.5m to 24.0m)
    tiers = [
        ("Tier1_Base",    5.8, 4.8, 2.5,  7.5, R_SHARD_GLASS_A),
        ("Tier2_MidLow",  4.8, 3.8, 7.5, 12.5, R_SHARD_GLASS_B),
        ("Tier3_MidHigh", 3.8, 2.8, 12.5, 17.5, R_SHARD_GLASS_A),
        ("Tier4_Upper",   2.8, 1.8, 17.5, 22.5, R_SHARD_GLASS_B),
        ("Tier5_Viewing", 1.8, 1.1, 22.5, 26.5, R_NIGHT_GLOW),
    ]

    for t_name, rb, rt, zb, zt, reg in tiers:
        t_obj = make_tapering_shard_tier(t_name, rb, rt, zb, zt, segs=8)
        t_obj.data.materials.append(mat)
        kit.map_faces_to_region(t_obj, reg, S)
        parts.append(t_obj)

    # 3. Open Pinnacle Spire Shards (Z: 26.5m to 33.0m)
    shard_blades = [
        ("SpireBlade_N",  0.9, 0.15, 26.5, 32.5, (0, 0.75, 0)),
        ("SpireBlade_S",  0.8, 0.15, 26.5, 31.5, (0, -0.70, 0)),
        ("SpireBlade_E",  0.15, 0.85, 26.5, 33.0, (0.75, 0, 0)),
        ("SpireBlade_W",  0.15, 0.75, 26.5, 30.8, (-0.70, 0, 0)),
        ("SpireBlade_NE", 0.6, 0.15, 26.5, 32.0, (0.5, 0.5, 0)),
        ("SpireBlade_SW", 0.6, 0.15, 26.5, 30.5, (-0.5, -0.5, 0)),
    ]

    for b_name, bw, bd, zb, zt, (ox, oy, _) in shard_blades:
        blade = kit.make_box(b_name, bw, bd, zt - zb, (ox, oy, zb))
        blade.data.materials.append(mat)
        kit.map_faces_to_region(blade, R_SHARD_GLASS_A, S)
        parts.append(blade)

    # Internal Steel Truss Spire Skeleton
    reg_box("SpireInternalTruss1", 0.25, 0.25, 6.0, (0, 0, 26.5), region=R_STEEL_MULLIONS)
    reg_box("SpireCrossTruss1", 1.2, 0.15, 0.15, (0, 0, 28.5), region=R_STEEL_MULLIONS)
    reg_box("SpireCrossTruss2", 0.15, 1.2, 0.15, (0, 0, 30.5), region=R_STEEL_MULLIONS)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_The_Shard")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_the_shard_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_the_shard.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_the_shard.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_the_shard_preview.png")
        shutil.copy2(OUT_DIR / "atlas_the_shard.png", TEXTURES_DIR / "atlas_the_shard.png")
        print(f"[TheShard] clean building deployed.")
    except Exception as e:
        print(f"[TheShard] deploy notice: {e}")


if __name__ == "__main__":
    main()
