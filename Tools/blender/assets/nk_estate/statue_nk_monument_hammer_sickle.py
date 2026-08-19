"""North Korean Monument to the Workers' Party — Hammer, Sickle & Calligraphy Brush (High-Poly ~1000 Tris).

Sculptural Specs:
- Imposing 4.2m high Socialist Realist monument celebrating the Workers' Party of Korea
- Footprint: 2.4m x 2.4m granite plinth, 4.2m total height
- Plinth: 3-tier stepped polished red granite pedestal with carved Korean relief inscriptions: "영광스러운 로동당 만세 / GLORY TO THE WORKERS' PARTY"
- Monumental Sculpted Emblem (~1,000 Triangles):
  - Massive crossed 3D Hammer (heavy steel striking head, faceted handle)
  - Massive crossed 3D Sickle (curved arced steel blade with sharpened edge)
  - Central 3D Calligraphy Writing Brush (intellectuals/working class unity) with gold ferrule
  - Radiant 3D Red Star medallion at the intersection
  - Flanking draped 3D socialist red stone banner reliefs with gold fringe
- Outputs to Tools/blender/out/nk_estate/ and Tools/out/nk_estate/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/nk_estate/statue_nk_monument_hammer_sickle.py
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
OUT_DIR = kit.OUT_DIR / "nk_estate"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "nk_estate"

# --- Atlas Region Definitions (x, y, w, h) ---
R_RED_GRANITE       = (0,   256, 256, 256)   # Polished red porphyry granite pedestal
R_GOLD_BRONZE       = (256, 256, 128, 256)   # Shimmering monumental gold bronze tools
R_RED_BANNER        = (384, 384, 128, 128)   # Draped socialist red banner & gold fringe
R_RED_STAR_CREST    = (384, 256, 128, 128)   # Radiant 3D red star crest with gold rays
R_PEDESTAL_INSCRIPT = (0,   128, 256, 128)   # Gold carved Korean inscription: "영광스러운 로동당"
R_STEEL_BLADE       = (256, 128, 128, 128)   # Polished sickle steel blade
R_PAVEMENT          = (384, 128, 128, 128)   # Base paving flags
R_METAL_TRIM        = (0,   0,   256, 128)   # Dark bronze mounting brackets

# --- Palette Colors ---
GRANITE_RED_BASE    = (0.54, 0.20, 0.16)
GRANITE_RED_DARK    = (0.36, 0.12, 0.10)
GRANITE_RED_LIGHT   = (0.70, 0.30, 0.24)
NK_RED              = (0.88, 0.08, 0.08)
IMPERIAL_GOLD       = (0.92, 0.76, 0.18)
GOLD_DARK           = (0.64, 0.50, 0.10)
GOLD_HILITE         = (0.99, 0.88, 0.35)
STEEL_LIGHT         = (0.80, 0.82, 0.85)
STEEL_DARK          = (0.30, 0.32, 0.35)
BRONZE_DARK         = (0.22, 0.18, 0.14)


def paint_hammer_sickle_atlas():
    a = Atlas(S, seed=707)

    # 1. Polished Red Granite Pedestal (R_RED_GRANITE)
    x, y, w, h = R_RED_GRANITE
    a.rect(x, y, w, h, GRANITE_RED_BASE)
    for gy in range(y, y + h, 24):
        a.rect(x, gy, w, 2, GRANITE_RED_DARK)
        for gx in range(x, x + w, 24):
            if ((gx + gy) // 24) % 2 == 0:
                a.rect(gx, gy, 12, 12, GRANITE_RED_LIGHT)
    a.noise(x, y, w, h, 0.03)

    # 2. Monumental Gold Bronze (R_GOLD_BRONZE)
    x, y, w, h = R_GOLD_BRONZE
    a.rect(x, y, w, h, IMPERIAL_GOLD)
    for by in range(y + 8, y + h, 20):
        a.rect(x, by, w, 3, GOLD_DARK)
        a.rect(x, by + 3, w, 2, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 3. Draped Socialist Red Banner (R_RED_BANNER)
    x, y, w, h = R_RED_BANNER
    a.rect(x, y, w, h, NK_RED)
    a.rect(x, y + h - 14, w, 14, IMPERIAL_GOLD)
    a.rect(x, y, w, 14, IMPERIAL_GOLD)
    for fy in range(y + 14, y + h - 14, 18):
        a.rect(x + 4, fy, w - 8, 4, (0.65, 0.05, 0.05))
    a.noise(x, y, w, h, 0.02)

    # 4. Radiant Red Star Crest (R_RED_STAR_CREST)
    x, y, w, h = R_RED_STAR_CREST
    a.rect(x, y, w, h, GRANITE_RED_DARK)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, IMPERIAL_GOLD)
    a.disc(cx, cy, 40, NK_RED)
    a.disc(cx, cy, 20, IMPERIAL_GOLD)
    a.disc(cx, cy, 8, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 5. Carved Pedestal Inscription (R_PEDESTAL_INSCRIPT)
    x, y, w, h = R_PEDESTAL_INSCRIPT
    a.rect(x, y, w, h, GRANITE_RED_BASE)
    a.rect(x + 4, y + 4, w - 8, h - 8, GRANITE_RED_DARK)
    a.rect(x + 8, y + 8, w - 16, 2, IMPERIAL_GOLD)
    a.rect(x + 8, y + h - 10, w - 16, 2, IMPERIAL_GOLD)

    # Inscription text
    s_top = "WORKERS' PARTY"
    tw = a.text_width(s_top, scale=2)
    a.text(x + (w - tw) // 2, y + h - 22, s_top, IMPERIAL_GOLD, scale=2)

    s_bot = "GLORY TO THE HEROIC WORKERS"
    bw = a.text_width(s_bot, scale=1)
    a.text(x + (w - bw) // 2, y + 26, s_bot, GOLD_HILITE, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 6. Polished Steel Blade (R_STEEL_BLADE)
    x, y, w, h = R_STEEL_BLADE
    a.rect(x, y, w, h, STEEL_LIGHT)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STEEL_DARK)
    a.noise(x, y, w, h, 0.02)

    # 7. Pavement Flags (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.62, 0.60, 0.56))
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.45, 0.43, 0.40))

    # 8. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, BRONZE_DARK)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("statue_nk_monument_hammer_sickle_atlas", OUT_DIR)


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


def make_curved_sickle_blade(name, r_inner=0.60, r_outer=0.85, thickness=0.08, arc_deg=190, segs=16, at=(0, 0, 0)):
    """Generates a swept curved 3D sickle blade."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    ht = thickness / 2.0

    for i in range(segs + 1):
        ang = math.radians(arc_deg * (i / segs))
        # Inner curve
        ix = r_inner * math.cos(ang)
        iy = r_inner * math.sin(ang)
        # Outer curve
        ox = r_outer * math.cos(ang)
        oy = r_outer * math.sin(ang)

        verts.append((ix, iy, -ht))
        verts.append((ix, iy, ht))
        verts.append((ox, oy, -ht))
        verts.append((ox, oy, ht))

    faces = []
    for i in range(segs):
        v = i * 4
        nv = (i + 1) * 4
        # Inner wall
        faces.append((v + 0, nv + 0, nv + 1, v + 1))
        # Outer wall
        faces.append((v + 2, v + 3, nv + 3, nv + 2))
        # Bottom face
        faces.append((v + 0, v + 2, nv + 2, nv + 0))
        # Top face
        faces.append((v + 1, nv + 1, nv + 3, v + 3))

    # Base cap
    faces.append((0, 1, 3, 2))
    # Tip cap
    last = segs * 4
    faces.append((last + 0, last + 2, last + 3, last + 1))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_hammer_sickle_atlas()
    mat = material_for(img, "mat_nk_hammer_sickle")

    parts = []

    def register_box(name, w, d, h, at, region=R_RED_GRANITE, front_region=None):
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
    # High-Poly Workers' Party Monument (~1,000 Triangles)
    # - 1. 3-Tier Stepped Red Granite Pedestal with Inscriptions
    # - 2. Massive 3D Crossed Golden Hammer (Head, Bevels, Handle)
    # - 3. Massive 3D Crossed Golden Sickle (Swept 16-Segment Curved Blade & Handle)
    # - 4. Central 3D Calligraphy Writing Brush
    # - 5. Radiant Red Star & Gold Wreath Medallion
    # - 6. Flanking 3D Draped Socialist Red Banners
    # =========================================================================

    # 1. Red Granite Pedestal (Z = 0.00 to 1.60m)
    # - Tier 1: Ground Plinth (2.40m x 2.40m x 0.25m)
    register_box("PedestalTier1", 2.40, 2.40, 0.25, (0.0, 0.0, 0.0), region=R_RED_GRANITE)

    # - Tier 2: Mid Step (2.00m x 2.00m x 0.35m)
    register_box("PedestalTier2", 2.00, 2.00, 0.35, (0.0, 0.0, 0.25), region=R_RED_GRANITE)

    # - Tier 3: Inscribed Pillar (1.50m x 1.50m x 1.00m, Z = 0.60m to 1.60m)
    register_box("PedestalPillar", 1.50, 1.50, 1.00, (0.0, 0.0, 0.60),
                 region=R_RED_GRANITE, front_region=R_PEDESTAL_INSCRIPT)

    # - Pedestal Cap Table (1.65m x 1.65m x 0.15m at Z = 1.60m)
    register_box("PedestalCap", 1.65, 1.65, 0.15, (0.0, 0.0, 1.60), region=R_RED_GRANITE)

    # =========================================================================
    # 2. Monumental 3D Hammer (Crossed at +35 deg from Left to Right, Z = 1.75m to 3.80m)
    # =========================================================================
    # Hammer Handle (12-segment cylinder, Length 2.40m, Diam 0.14m)
    hammer_handle = make_cylinder("HammerHandle", 0.07, 2.40, segs=12, at=(0.0, 0.0, 0.0))
    hammer_handle.rotation_euler = (0, math.radians(-35), 0)
    hammer_handle.location = (-0.65, -0.15, 1.85)
    hammer_handle.data.materials.append(mat)
    kit.map_faces_to_region(hammer_handle, R_GOLD_BRONZE, S)
    parts.append(hammer_handle)

    # Hammer Head (Heavy rectangular block with striking bevels: 0.50m x 0.28m x 0.30m)
    hammer_head = kit.make_box("HammerHead", 0.52, 0.28, 0.30, at=(0.70, -0.15, 3.75))
    hammer_head.rotation_euler = (0, math.radians(-35), 0)
    hammer_head.data.materials.append(mat)
    kit.map_faces_to_region(hammer_head, R_GOLD_BRONZE, S)
    parts.append(hammer_head)

    # Striking Face Caps
    for hx in [-0.28, 0.28]:
        hcap = kit.make_box(f"HammerFaceCap_{hx}", 0.06, 0.26, 0.28, at=(0.70 + hx * math.cos(math.radians(-35)), -0.15, 3.75 + hx * math.sin(math.radians(-35))))
        hcap.rotation_euler = (0, math.radians(-35), 0)
        hcap.data.materials.append(mat)
        kit.map_faces_to_region(hcap, R_STEEL_BLADE, S)
        parts.append(hcap)

    # =========================================================================
    # 3. Monumental 3D Sickle (Crossed at -35 deg from Right to Left, Z = 1.75m to 4.10m)
    # =========================================================================
    # Sickle Handle (Length 1.20m, Diam 0.12m)
    sickle_handle = make_cylinder("SickleHandle", 0.06, 1.20, segs=12, at=(0.0, 0.0, 0.0))
    sickle_handle.rotation_euler = (0, math.radians(35), 0)
    sickle_handle.location = (0.60, 0.05, 1.85)
    sickle_handle.data.materials.append(mat)
    kit.map_faces_to_region(sickle_handle, R_GOLD_BRONZE, S)
    parts.append(sickle_handle)

    # Swept 16-Segment Curved 3D Sickle Blade (Arc = 190 deg)
    sickle_blade = make_curved_sickle_blade("SickleBlade", r_inner=0.65, r_outer=0.92, thickness=0.08, arc_deg=190, segs=16, at=(0.0, 0.0, 0.0))
    sickle_blade.rotation_euler = (math.radians(90), 0, math.radians(45))
    sickle_blade.location = (-0.10, 0.05, 3.10)
    sickle_blade.data.materials.append(mat)
    kit.map_faces_to_region(sickle_blade, R_STEEL_BLADE, S)
    parts.append(sickle_blade)

    # =========================================================================
    # 4. Central Calligraphy Writing Brush (Vertical: Z = 1.75m to 4.20m)
    # =========================================================================
    # Brush Shaft (Length 2.20m, Diam 0.10m)
    brush_shaft = make_cylinder("BrushShaft", 0.05, 2.20, segs=12, at=(0.0, 0.15, 1.75))
    brush_shaft.data.materials.append(mat)
    kit.map_faces_to_region(brush_shaft, R_GOLD_BRONZE, S)
    parts.append(brush_shaft)

    # Gold Ferrule & Tip (Z = 3.95m to 4.30m)
    brush_ferrule = make_cylinder("BrushFerrule", 0.07, 0.20, segs=10, at=(0.0, 0.15, 3.95))
    brush_ferrule.data.materials.append(mat)
    kit.map_faces_to_region(brush_ferrule, R_GOLD_BRONZE, S)
    parts.append(brush_ferrule)

    brush_tip = make_cylinder("BrushTip", 0.04, 0.25, segs=8, at=(0.0, 0.15, 4.15))
    brush_tip.data.materials.append(mat)
    kit.map_faces_to_region(brush_tip, R_METAL_TRIM, S)
    parts.append(brush_tip)

    # =========================================================================
    # 5. Central Radiant Red Star Medallion (Intersection: Z = 2.80m)
    # =========================================================================
    star_box = kit.make_box("StarMedallion", 0.65, 0.10, 0.65, at=(0.0, -0.22, 2.80))
    star_box.data.materials.append(mat)
    kit.map_faces_to_region(star_box, R_RED_STAR_CREST, S)
    parts.append(star_box)

    # =========================================================================
    # 6. Flanking 3D Draped Socialist Red Banners
    # =========================================================================
    for i, bx in enumerate([-0.95, 0.95]):
        banner = kit.make_box(f"SideBanner_{i}", 0.35, 0.60, 1.60, at=(bx, 0.0, 1.75))
        banner.data.materials.append(mat)
        kit.map_faces_to_region(banner, R_RED_BANNER, S)
        parts.append(banner)

    # 4 Corner Ceremonial Victory Torch Braziers on Plinth Corners (X = +-1.0m, Y = +-1.0m)
    for i, (bx, by) in enumerate([(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)]):
        # Brazier Stand Post
        b_post = make_cylinder(f"BrazierPost_{i}", 0.08, 0.55, segs=10, at=(bx, by, 0.25))
        b_post.data.materials.append(mat)
        kit.map_faces_to_region(b_post, R_GOLD_BRONZE, S)
        parts.append(b_post)

        # Brazier Bowl & Eternal Flame Crest
        b_bowl = make_cylinder(f"BrazierBowl_{i}", 0.16, 0.15, segs=12, at=(bx, by, 0.80))
        b_bowl.data.materials.append(mat)
        kit.map_faces_to_region(b_bowl, R_GOLD_BRONZE, S)
        parts.append(b_bowl)

        b_flame = kit.make_box(f"BrazierFlame_{i}", 0.12, 0.12, 0.22, (bx, by, 0.95))
        b_flame.data.materials.append(mat)
        kit.map_faces_to_region(b_flame, R_RED_STAR_CREST, S)
        parts.append(b_flame)

    # Bronze Relief Star Medallions on Pedestal Side Faces (Left & Right at Z = 1.10m)
    for i, sx in enumerate([-0.76, 0.76]):
        s_med = make_cylinder(f"SideMedallion_{i}", 0.22, 0.04, segs=10, at=(sx, 0.0, 1.10))
        s_med.rotation_euler = (0, math.radians(90), 0)
        s_med.data.materials.append(mat)
        kit.map_faces_to_region(s_med, R_RED_STAR_CREST, S)
        parts.append(s_med)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Statue_NK_Monument_Hammer_Sickle")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "statue_nk_monument_hammer_sickle_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "statue_nk_monument_hammer_sickle.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "statue_nk_monument_hammer_sickle.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "statue_nk_monument_hammer_sickle_preview.png")
        shutil.copy2(OUT_DIR / "statue_nk_monument_hammer_sickle_atlas.png", TOOLS_OUT_DIR / "statue_nk_monument_hammer_sickle_atlas.png")
    except Exception as e:
        print(f"[statue_nk_monument_hammer_sickle] note: {e}")

    print("[statue_nk_monument_hammer_sickle] generation complete.")


main()
