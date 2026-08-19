"""East York Imperial Gilded Bronze Guardian Lion (Foo Dog / 金銅神獸獅 — High-Poly ~1000 Tris).

Sculptural Specs:
- 1.4m x 1.8m footprint, 2.8m total height
- Plinth: Multi-tier vermilion lacquer and gold filigree pedestal with polished black marble cap
- Lion Figure (~1,000 Triangles):
  - Cast in dark patinated bronze with shimmering Imperial Gold leaf accents on mane curls, fangs, and Xiuqiu ball
  - Sitting on muscular hindquarters with arched back and curved tufted tail
  - Barrel chest adorned with gold collar and bronze bell
  - Fierce roaring head with open jaws, gold fangs, and 3D spiral mane curl clusters
  - Right front paw planted firmly atop a pierced gold filigree Xiuqiu ball
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/statue_east_york_pho_dog_gilded.py
"""

import math
import shutil
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "east_york"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "east_york"

# --- Atlas Region Definitions (x, y, w, h) ---
R_LACQUER_PLINTH    = (0,   256, 256, 256)   # Vermilion lacquer plinth & gold dragon filigree
R_BRONZE_BODY       = (256, 256, 128, 256)   # Dark patinated bronze lion body
R_GOLD_MANE_HEAD    = (384, 384, 128, 128)   # Gilded lion face, fangs & eyes
R_GOLD_XIUQIU       = (384, 256, 128, 128)   # Imperial gold filigree sphere
R_COLLAR_GOLD       = (0,   128, 256, 128)   # Heavy gold collar & bronze bell
R_GOLD_CURLS        = (256, 128, 128, 128)   # Gilded mane spiral curls
R_MARBLE_BLACK      = (384, 128, 128, 128)   # Polished black marble cap

# --- Palette Colors ---
VERMILION_DARK      = (0.45, 0.06, 0.04)
VERMILION_BASE      = (0.76, 0.12, 0.08)
BRONZE_DARK         = (0.16, 0.18, 0.16)
BRONZE_PATINA       = (0.24, 0.32, 0.28)
IMPERIAL_GOLD       = (0.92, 0.76, 0.18)
GOLD_HILITE         = (0.99, 0.88, 0.35)
GOLD_DARK           = (0.65, 0.50, 0.10)
BLACK_MARBLE        = (0.10, 0.10, 0.12)
MOUTH_DARK          = (0.25, 0.06, 0.06)


def paint_pho_dog_gilded_atlas():
    a = Atlas(S, seed=3031)

    # 1. Vermilion & Gold Dragon Plinth (R_LACQUER_PLINTH)
    x, y, w, h = R_LACQUER_PLINTH
    a.rect(x, y, w, h, VERMILION_BASE)
    a.rect(x + 4, y + 4, w - 8, h - 8, VERMILION_DARK)
    band_y = y + h - 40
    a.rect(x, band_y, w, 36, IMPERIAL_GOLD)
    a.rect(x + 2, band_y + 3, w - 4, 30, VERMILION_DARK)
    for cx in range(x + 4, x + w - 24, 28):
        a.rect(cx, band_y + 6, 20, 20, IMPERIAL_GOLD)
        a.rect(cx + 4, band_y + 10, 12, 12, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 2. Dark Bronze Body (R_BRONZE_BODY)
    x, y, w, h = R_BRONZE_BODY
    a.rect(x, y, w, h, BRONZE_DARK)
    for my in range(y + 8, y + h, 24):
        a.rect(x, my, w, 3, BRONZE_PATINA)
    a.noise(x, y, w, h, 0.025)

    # 3. Gilded Lion Face (R_GOLD_MANE_HEAD)
    x, y, w, h = R_GOLD_MANE_HEAD
    a.rect(x, y, w, h, BRONZE_DARK)
    a.rect(x + 20, y + 20, w - 40, 44, MOUTH_DARK)
    a.rect(x + 28, y + 50, 14, 12, GOLD_HILITE)
    a.rect(x + w - 42, y + 50, 14, 12, GOLD_HILITE)
    a.rect(x + 36, y + 22, 12, 10, GOLD_HILITE)
    a.rect(x + w - 48, y + 22, 12, 10, GOLD_HILITE)
    a.disc(x + 36, y + h - 36, 12, GOLD_HILITE)
    a.disc(x + 36, y + h - 36, 6, (0.1, 0.1, 0.1))
    a.disc(x + w - 36, y + h - 36, 12, GOLD_HILITE)
    a.disc(x + w - 36, y + h - 36, 6, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.02)

    # 4. Gold Xiuqiu Ball (R_GOLD_XIUQIU)
    x, y, w, h = R_GOLD_XIUQIU
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    for ly in range(y + 8, y + h - 8, 16):
        a.rect(x + 4, ly, w - 8, 4, GOLD_DARK)
    for lx in range(x + 8, x + w - 8, 16):
        a.rect(lx, y + 4, 4, h - 8, GOLD_DARK)
    for cy in range(y + 16, y + h - 16, 28):
        for cx in range(x + 16, x + w - 16, 28):
            a.disc(cx + 6, cy + 6, 8, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 5. Collar & Bell (R_COLLAR_GOLD)
    x, y, w, h = R_COLLAR_GOLD
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 32, GOLD_HILITE)
    a.disc(cx, cy, 22, GOLD_DARK)
    a.noise(x, y, w, h, 0.02)

    # 6. Gilded Mane Curls (R_GOLD_CURLS)
    x, y, w, h = R_GOLD_CURLS
    a.rect(x, y, w, h, BRONZE_DARK)
    for my in range(y, y + h, 24):
        for mx in range(x, x + w, 24):
            a.disc(mx + 12, my + 12, 10, IMPERIAL_GOLD)
            a.disc(mx + 12, my + 12, 6, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 7. Black Marble (R_MARBLE_BLACK)
    x, y, w, h = R_MARBLE_BLACK
    a.rect(x, y, w, h, BLACK_MARBLE)
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("statue_east_york_pho_dog_gilded_atlas", OUT_DIR)


def make_cylinder(name, r, h, segs=12, at=(0, 0, 0)):
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


def make_sphere(name, r, segs=12, rings=8, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = [(0, 0, -r)]
    for ring in range(1, rings):
        phi = -math.pi / 2.0 + math.pi * ring / rings
        z = r * math.sin(phi)
        r_ring = r * math.cos(phi)
        for seg in range(segs):
            theta = 2.0 * math.pi * seg / segs
            verts.append((r_ring * math.cos(theta), r_ring * math.sin(theta), z))
    verts.append((0, 0, r))

    faces = []
    for seg in range(segs):
        nseg = (seg + 1) % segs
        faces.append((0, 1 + nseg, 1 + seg))
    for ring in range(rings - 2):
        r1 = 1 + ring * segs
        r2 = 1 + (ring + 1) * segs
        for seg in range(segs):
            nseg = (seg + 1) % segs
            faces.append((r1 + seg, r1 + nseg, r2 + nseg, r2 + seg))
    top_idx = len(verts) - 1
    r_top = 1 + (rings - 2) * segs
    for seg in range(segs):
        nseg = (seg + 1) % segs
        faces.append((top_idx, r_top + seg, r_top + nseg))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_pho_dog_gilded_atlas()
    mat = material_for(img, "mat_pho_dog_gilded")

    parts = []

    def register_box(name, w, d, h, at, region=R_BRONZE_BODY, front_region=None):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        if front_region:
            kit.map_faces_to_region(o, front_region, S, only=lambda f: f.normal.y < -0.5)
            kit.map_faces_to_region(o, region, S, only=lambda f: f.normal.y >= -0.5)
        else:
            kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Gilded Foo Dog (~1,000 Triangles)
    # =========================================================================

    # 1. Tiered Carved Lacquer Pedestal (Z = 0.00 to 0.85m)
    register_box("PedestalFoot", 1.40, 1.80, 0.20, (0.0, 0.0, 0.0), region=R_LACQUER_PLINTH)
    register_box("PedestalLotus", 1.20, 1.60, 0.45, (0.0, 0.0, 0.20), region=R_LACQUER_PLINTH)
    register_box("PedestalCap", 1.30, 1.70, 0.20, (0.0, 0.0, 0.65), region=R_MARBLE_BLACK)

    # 2. Lion Muscular Haunches (Z = 0.85m to 1.55m)
    register_box("HindHaunchL", 0.35, 0.70, 0.60, (-0.42, 0.35, 0.85), region=R_BRONZE_BODY)
    register_box("HindPawL", 0.28, 0.40, 0.18, (-0.45, 0.50, 0.85), region=R_BRONZE_BODY)

    register_box("HindHaunchR", 0.35, 0.70, 0.60, (0.42, 0.35, 0.85), region=R_BRONZE_BODY)
    register_box("HindPawR", 0.28, 0.40, 0.18, (0.45, 0.50, 0.85), region=R_BRONZE_BODY)

    # 3. Upright Torso & Arched Barrel Chest (Z = 1.15m to 2.05m)
    register_box("TorsoLower", 0.75, 0.85, 0.55, (0.0, 0.10, 1.15), region=R_BRONZE_BODY)
    register_box("ChestUpper", 0.82, 0.75, 0.50, (0.0, -0.05, 1.60), region=R_BRONZE_BODY)

    # 4. Front Legs & Paws
    leg_l = make_cylinder("ForelegL", 0.14, 0.85, segs=12, at=(-0.35, -0.40, 0.85))
    leg_l.data.materials.append(mat)
    kit.map_faces_to_region(leg_l, R_BRONZE_BODY, S)
    parts.append(leg_l)

    register_box("PawL", 0.32, 0.38, 0.18, (-0.35, -0.48, 0.85), region=R_BRONZE_BODY)

    leg_r = make_cylinder("ForelegR", 0.14, 0.65, segs=12, at=(0.35, -0.30, 1.35))
    leg_r.data.materials.append(mat)
    kit.map_faces_to_region(leg_r, R_BRONZE_BODY, S)
    parts.append(leg_r)

    register_box("PawR", 0.30, 0.34, 0.18, (0.35, -0.40, 1.38), region=R_BRONZE_BODY)

    # 5. Gilded Xiuqiu Orb
    ball = make_sphere("XiuqiuBall", 0.28, segs=16, rings=10, at=(0.35, -0.40, 1.13))
    ball.data.materials.append(mat)
    kit.map_faces_to_region(ball, R_GOLD_XIUQIU, S)
    parts.append(ball)

    # 6. Gold Collar & Bell
    collar = make_cylinder("CollarRibbon", 0.44, 0.12, segs=16, at=(0.0, -0.05, 1.85))
    collar.data.materials.append(mat)
    kit.map_faces_to_region(collar, R_COLLAR_GOLD, S)
    parts.append(collar)

    bell = make_sphere("GoldBell", 0.12, segs=10, rings=8, at=(0.0, -0.50, 1.88))
    bell.data.materials.append(mat)
    kit.map_faces_to_region(bell, R_COLLAR_GOLD, S)
    parts.append(bell)

    # 7. Gilded Lion Head & Roaring Jaws
    register_box("LionHead", 0.72, 0.68, 0.60, (0.0, -0.18, 2.05), region=R_BRONZE_BODY, front_region=R_GOLD_MANE_HEAD)
    register_box("SnoutMuzzle", 0.46, 0.30, 0.32, (0.0, -0.52, 2.10), region=R_BRONZE_BODY, front_region=R_GOLD_MANE_HEAD)

    register_box("EarL", 0.18, 0.18, 0.22, (-0.38, -0.10, 2.58), region=R_GOLD_CURLS)
    register_box("EarR", 0.18, 0.18, 0.22, (0.38, -0.10, 2.58), region=R_GOLD_CURLS)

    # 8 3D Mane Spiral Curl Clusters
    mane_locs = [
        (-0.35, 0.15, 2.20), (0.35, 0.15, 2.20), (0.0, 0.22, 2.25),
        (-0.30, 0.25, 1.80), (0.30, 0.25, 1.80), (0.0, 0.30, 1.85),
        (-0.25, 0.32, 1.45), (0.25, 0.32, 1.45)
    ]
    for i, (mx, my, mz) in enumerate(mane_locs):
        curl = make_cylinder(f"ManeCurl_{i}", 0.12, 0.20, segs=8, at=(mx, my, mz))
        curl.data.materials.append(mat)
        kit.map_faces_to_region(curl, R_GOLD_CURLS, S)
        parts.append(curl)

    # 8. Sculpted Tail
    tail = make_cylinder("LionTail", 0.08, 0.75, segs=8, at=(0.0, 0.50, 1.00))
    tail.data.materials.append(mat)
    kit.map_faces_to_region(tail, R_BRONZE_BODY, S)
    parts.append(tail)

    tail_tuft = make_sphere("TailTuft", 0.15, segs=10, rings=8, at=(0.0, 0.42, 1.75))
    tail_tuft.data.materials.append(mat)
    kit.map_faces_to_region(tail_tuft, R_GOLD_CURLS, S)
    parts.append(tail_tuft)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Statue_East_York_Pho_Dog_Gilded")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "statue_east_york_pho_dog_gilded_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "statue_east_york_pho_dog_gilded.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "statue_east_york_pho_dog_gilded.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "statue_east_york_pho_dog_gilded_preview.png")
        shutil.copy2(OUT_DIR / "statue_east_york_pho_dog_gilded_atlas.png", TOOLS_OUT_DIR / "statue_east_york_pho_dog_gilded_atlas.png")
    except Exception as e:
        print(f"[statue_east_york_pho_dog_gilded] note: {e}")

    print("[statue_east_york_pho_dog_gilded] generation complete.")


main()
