"""East York Chinese Guardian Lion — Male with Xiuqiu Orb (Foo Dog / 雄石獅 — High-Poly ~1000 Tris).

Sculptural Specs:
- 1.4m x 1.8m footprint, 2.6m total height
- Plinth: Multi-tier carved York marble pedestal with lotus petal relief frieze and base moldings
- Lion Anatomy & Geometry (~1,000 Triangles):
  - Sitting on muscular hindquarters with arched back and curved tufted tail
  - Powerful barrel chest adorned with vermilion ceremonial ribbon collar and sculpted golden bell
  - Fierce roaring head with open jaws, prominent fangs, tongue, flared nostrils, and bulging eyes
  - Cascading 3D spiral mane curl clusters covering crown, nape, and shoulders
  - Right front paw planted firmly atop an intricately carved 3D Xiuqiu (embroidered silk ball)
  - Left front paw rooted to the pedestal with sculpted claws
- Texture Atlas: Dressed carved limestone, antique gold accents, vermilion ribbon, and jade inlays.
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/statue_east_york_pho_dog_male.py
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
R_MARBLE_BASE       = (0,   256, 256, 256)   # Carved York stone pedestal & lotus frieze
R_LION_STONE        = (256, 256, 128, 256)   # Dressed limestone body & muscular anatomy
R_LION_FACE         = (384, 384, 128, 128)   # Fierce face, open roaring mouth, fangs & eyes
R_XIUQIU_BALL       = (384, 256, 128, 128)   # Embroidered silk ball with gold ribbons & jade
R_COLLAR_BELL       = (0,   128, 256, 128)   # Vermilion ribbon collar & gold bronze bell
R_MANE_CURLS        = (256, 128, 128, 128)   # Stylized spiral mane curls
R_GOLD_ORNAMENT     = (384, 128, 128, 128)   # Imperial gold leaf accents

# --- Palette Colors ---
STONE_BASE          = (0.76, 0.72, 0.62)
STONE_DARK          = (0.50, 0.46, 0.38)
STONE_CREAM         = (0.86, 0.83, 0.75)
VERMILION_RED       = (0.78, 0.12, 0.08)
IMPERIAL_GOLD       = (0.92, 0.76, 0.18)
GOLD_DARK           = (0.64, 0.50, 0.10)
MOUTH_DARK          = (0.22, 0.06, 0.06)
JADE_GREEN          = (0.18, 0.55, 0.35)


def paint_pho_dog_male_atlas():
    a = Atlas(S, seed=1011)

    # 1. Carved Marble Pedestal (R_MARBLE_BASE)
    x, y, w, h = R_MARBLE_BASE
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y, y + h, 28):
        a.rect(x, my, w, 2, STONE_DARK)
    # Lotus frieze relief
    band_y = y + h - 40
    a.rect(x, band_y, w, 36, STONE_DARK)
    a.rect(x, band_y + 3, w, 30, STONE_BASE)
    for cx in range(x + 4, x + w - 24, 28):
        a.rect(cx, band_y + 6, 20, 20, STONE_CREAM)
        a.rect(cx + 4, band_y + 10, 12, 12, STONE_DARK)
        a.rect(cx + 6, band_y + 12, 8, 8, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.03)

    # 2. Lion Limestone Body (R_LION_STONE)
    x, y, w, h = R_LION_STONE
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y + 8, y + h, 24):
        a.rect(x, my, w, 3, STONE_DARK)
    a.noise(x, y, w, h, 0.035)

    # 3. Lion Face & Roaring Mouth (R_LION_FACE)
    x, y, w, h = R_LION_FACE
    a.rect(x, y, w, h, STONE_BASE)
    # Roaring mouth cavity
    a.rect(x + 20, y + 20, w - 40, 44, MOUTH_DARK)
    a.rect(x + 28, y + 50, 14, 12, STONE_CREAM)   # Left upper fang
    a.rect(x + w - 42, y + 50, 14, 12, STONE_CREAM)  # Right upper fang
    a.rect(x + 36, y + 22, 12, 10, STONE_CREAM)   # Lower teeth
    a.rect(x + w - 48, y + 22, 12, 10, STONE_CREAM)
    a.disc(x + w // 2, y + 32, 14, (0.75, 0.15, 0.12))  # Tongue
    # Flared nostrils & bulging eyes
    a.disc(x + 36, y + h - 36, 12, IMPERIAL_GOLD)
    a.disc(x + 36, y + h - 36, 6, (0.1, 0.1, 0.1))
    a.disc(x + w - 36, y + h - 36, 12, IMPERIAL_GOLD)
    a.disc(x + w - 36, y + h - 36, 6, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.02)

    # 4. Embroidered Xiuqiu Ball (R_XIUQIU_BALL)
    x, y, w, h = R_XIUQIU_BALL
    a.rect(x, y, w, h, VERMILION_RED)
    for ly in range(y + 8, y + h - 8, 18):
        a.rect(x + 4, ly, w - 8, 3, IMPERIAL_GOLD)
    for lx in range(x + 8, x + w - 8, 18):
        a.rect(lx, y + 4, 3, h - 8, IMPERIAL_GOLD)
    for cy in range(y + 16, y + h - 16, 32):
        for cx in range(x + 16, x + w - 16, 32):
            a.disc(cx + 7, cy + 7, 10, IMPERIAL_GOLD)
            a.disc(cx + 7, cy + 7, 6, JADE_GREEN)
    a.noise(x, y, w, h, 0.02)

    # 5. Ribbon Collar & Bell (R_COLLAR_BELL)
    x, y, w, h = R_COLLAR_BELL
    a.rect(x, y, w, h, VERMILION_RED)
    a.rect(x + 6, y + 6, w - 12, h - 12, (0.65, 0.08, 0.06))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 32, IMPERIAL_GOLD)
    a.disc(cx, cy, 22, GOLD_DARK)
    a.disc(cx, cy, 10, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    # 6. Mane Curls (R_MANE_CURLS)
    x, y, w, h = R_MANE_CURLS
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y, y + h, 24):
        for mx in range(x, x + w, 24):
            a.disc(mx + 12, my + 12, 10, STONE_DARK)
            a.disc(mx + 12, my + 12, 7, STONE_CREAM)
            a.disc(mx + 12, my + 12, 3, STONE_BASE)
    a.noise(x, y, w, h, 0.025)

    # 7. Gold Ornament (R_GOLD_ORNAMENT)
    x, y, w, h = R_GOLD_ORNAMENT
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("statue_east_york_pho_dog_male_atlas", OUT_DIR)


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
    # Bottom cap
    for seg in range(segs):
        nseg = (seg + 1) % segs
        faces.append((0, 1 + nseg, 1 + seg))
    # Middle quads
    for ring in range(rings - 2):
        r1 = 1 + ring * segs
        r2 = 1 + (ring + 1) * segs
        for seg in range(segs):
            nseg = (seg + 1) % segs
            faces.append((r1 + seg, r1 + nseg, r2 + nseg, r2 + seg))
    # Top cap
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
    img = paint_pho_dog_male_atlas()
    mat = material_for(img, "mat_pho_dog_male")

    parts = []

    def register_box(name, w, d, h, at, region=R_LION_STONE, front_region=None):
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
    # High-Poly Male Foo Dog (~1,000 Triangles)
    # =========================================================================

    # 1. Tiered Carved York Marble Pedestal (Z = 0.00 to 0.85m)
    # - Tier 1: Plinth Foot (1.40m x 1.80m x 0.20m)
    register_box("PedestalFoot", 1.40, 1.80, 0.20, (0.0, 0.0, 0.0), region=R_MARBLE_BASE)

    # - Tier 2: Lotus Petal Frieze Body (1.20m x 1.60m x 0.45m)
    register_box("PedestalLotus", 1.20, 1.60, 0.45, (0.0, 0.0, 0.20), region=R_MARBLE_BASE)

    # - Tier 3: Stepped Cap Table (1.30m x 1.70m x 0.20m)
    register_box("PedestalCap", 1.30, 1.70, 0.20, (0.0, 0.0, 0.65), region=R_MARBLE_BASE)

    # 2. Lion Muscular Haunches & Sitting Hindquarters (Z = 0.85m to 1.55m)
    # Left Haunch & Thigh
    register_box("HindHaunchL", 0.35, 0.70, 0.60, (-0.42, 0.35, 0.85), region=R_LION_STONE)
    register_box("HindPawL", 0.28, 0.40, 0.18, (-0.45, 0.50, 0.85), region=R_LION_STONE)

    # Right Haunch & Thigh
    register_box("HindHaunchR", 0.35, 0.70, 0.60, (0.42, 0.35, 0.85), region=R_LION_STONE)
    register_box("HindPawR", 0.28, 0.40, 0.18, (0.45, 0.50, 0.85), region=R_LION_STONE)

    # 3. Upright Torso & Arched Barrel Chest (Z = 1.15m to 2.05m)
    register_box("TorsoLower", 0.75, 0.85, 0.55, (0.0, 0.10, 1.15), region=R_LION_STONE)
    register_box("ChestUpper", 0.82, 0.75, 0.50, (0.0, -0.05, 1.60), region=R_LION_STONE)

    # 4. Front Legs & Paws
    # Left Foreleg (Rooted firmly on stone pedestal)
    leg_l = make_cylinder("ForelegL", 0.14, 0.85, segs=12, at=(-0.35, -0.40, 0.85))
    leg_l.data.materials.append(mat)
    kit.map_faces_to_region(leg_l, R_LION_STONE, S)
    parts.append(leg_l)

    register_box("PawL", 0.32, 0.38, 0.18, (-0.35, -0.48, 0.85), region=R_LION_STONE)

    # Right Foreleg (Raised and resting proudly on Xiuqiu ball)
    leg_r = make_cylinder("ForelegR", 0.14, 0.65, segs=12, at=(0.35, -0.30, 1.35))
    leg_r.data.materials.append(mat)
    kit.map_faces_to_region(leg_r, R_LION_STONE, S)
    parts.append(leg_r)

    register_box("PawR", 0.30, 0.34, 0.18, (0.35, -0.40, 1.38), region=R_LION_STONE)

    # 5. Intricate 3D Xiuqiu (Embroidered Silk Ball: Diam 0.56m, Z = 0.85m to 1.41m)
    ball = make_sphere("XiuqiuBall", 0.28, segs=16, rings=10, at=(0.35, -0.40, 1.13))
    ball.data.materials.append(mat)
    kit.map_faces_to_region(ball, R_XIUQIU_BALL, S)
    parts.append(ball)

    # 6. Vermilion Ribbon Collar with Sculpted Gold Bell (Z = 1.85m to 1.95m)
    collar = make_cylinder("CollarRibbon", 0.44, 0.12, segs=16, at=(0.0, -0.05, 1.85))
    collar.data.materials.append(mat)
    kit.map_faces_to_region(collar, R_COLLAR_BELL, S)
    parts.append(collar)

    bell = make_sphere("GoldBell", 0.12, segs=10, rings=8, at=(0.0, -0.50, 1.88))
    bell.data.materials.append(mat)
    kit.map_faces_to_region(bell, R_GOLD_ORNAMENT, S)
    parts.append(bell)

    # 7. Lion Sculpted Head & Roaring Jaws (Z = 2.05m to 2.70m)
    # Head block with face on front
    register_box("LionHead", 0.72, 0.68, 0.60, (0.0, -0.18, 2.05), region=R_LION_STONE, front_region=R_LION_FACE)

    # Projecting Snout & Muzzle
    register_box("SnoutMuzzle", 0.46, 0.30, 0.32, (0.0, -0.52, 2.10), region=R_LION_STONE, front_region=R_LION_FACE)

    # Left & Right Mane Curl Horns / Ears
    register_box("EarL", 0.18, 0.18, 0.22, (-0.38, -0.10, 2.58), region=R_MANE_CURLS)
    register_box("EarR", 0.18, 0.18, 0.22, (0.38, -0.10, 2.58), region=R_MANE_CURLS)

    # 8 3D Mane Spiral Curl Clusters around Neck, Head & Back (12-segment cylinders)
    mane_locs = [
        (-0.35, 0.15, 2.20), (0.35, 0.15, 2.20), (0.0, 0.22, 2.25),
        (-0.30, 0.25, 1.80), (0.30, 0.25, 1.80), (0.0, 0.30, 1.85),
        (-0.25, 0.32, 1.45), (0.25, 0.32, 1.45)
    ]
    for i, (mx, my, mz) in enumerate(mane_locs):
        curl = make_cylinder(f"ManeCurl_{i}", 0.12, 0.20, segs=8, at=(mx, my, mz))
        curl.data.materials.append(mat)
        kit.map_faces_to_region(curl, R_MANE_CURLS, S)
        parts.append(curl)

    # 8. Sculpted Tail Resting over Back (Z = 1.00m to 1.75m)
    tail = make_cylinder("LionTail", 0.08, 0.75, segs=8, at=(0.0, 0.50, 1.00))
    tail.data.materials.append(mat)
    kit.map_faces_to_region(tail, R_LION_STONE, S)
    parts.append(tail)

    tail_tuft = make_sphere("TailTuft", 0.15, segs=10, rings=8, at=(0.0, 0.42, 1.75))
    tail_tuft.data.materials.append(mat)
    kit.map_faces_to_region(tail_tuft, R_MANE_CURLS, S)
    parts.append(tail_tuft)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Statue_East_York_Pho_Dog_Male")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "statue_east_york_pho_dog_male_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "statue_east_york_pho_dog_male.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "statue_east_york_pho_dog_male.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "statue_east_york_pho_dog_male_preview.png")
        shutil.copy2(OUT_DIR / "statue_east_york_pho_dog_male_atlas.png", TOOLS_OUT_DIR / "statue_east_york_pho_dog_male_atlas.png")
    except Exception as e:
        print(f"[statue_east_york_pho_dog_male] note: {e}")

    print("[statue_east_york_pho_dog_male] generation complete.")


main()
