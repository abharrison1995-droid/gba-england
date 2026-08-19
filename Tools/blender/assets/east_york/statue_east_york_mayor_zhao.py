"""Civic Monument Statue of Mayor Zhao (市長 趙 — Benefactor of East York).

Specs:
- 1.50m x 1.50m footprint, Height: 3.50m total (Plinth: 1.40m, Statue: 2.10m)
- Plinth: Multi-tier carved York limestone monument pedestal with lotus relief and bronze plaque:
  "MAYOR ZHAO 市長趙 — BENEFACTOR OF EAST YORK"
- Statue: Cast bronze figure of Mayor Zhao standing proud and dignified:
  - Formal Victorian mayoral morning coat combined with Chinese silk embroidered dragon waistcoat
  - Heavy gold Mayoral Chain of Office draped across shoulders
  - Right arm outstretched holding the Ceremonial Golden Key to East York
  - Left hand resting on hip / mayoral cane
  - Distinguished facial features with groomed hair and moustache
- Designed as the central civic landmark for East York Town Square / Council Hall plaza.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/statue_east_york_mayor_zhao.py
"""

import math
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "east_york"

# --- Atlas Regions ---
R_MONUMENT_PLINTH   = (0,   256, 256, 256)   # Dressed York limestone & stepped moldings
R_BRONZE_PLAQUE     = (256, 256, 256, 128)   # "MAYOR ZHAO 市長趙 — BENEFACTOR OF EAST YORK"
R_MAYOR_SUIT        = (0,   128, 256, 128)   # Bronze / dark tweed tailcoat & dragon waistcoat
R_MAYOR_HEAD        = (256, 128, 128, 128)   # Mayor Zhao face, hair & moustache
R_GOLD_CHAIN_KEY    = (384, 128, 128, 128)   # Mayoral gold chain of office & golden key
R_PAVEMENT          = (0,   0,   256, 128)   # Monument plaza flagstones
R_BRONZE_BASE       = (256, 0,   256, 128)   # Patinated bronze statue base & shoes

# --- Colors ---
STONE_BASE          = (0.78, 0.74, 0.65)
STONE_DARK          = (0.54, 0.50, 0.44)
STONE_CREAM         = (0.86, 0.83, 0.75)
BRONZE_DARK         = (0.18, 0.20, 0.18)
BRONZE_PATINA       = (0.26, 0.35, 0.30)
IMPERIAL_GOLD       = (0.92, 0.76, 0.18)
GOLD_HILITE         = (0.99, 0.88, 0.35)
GOLD_DARK           = (0.65, 0.50, 0.10)
PLAQUE_BRONZE       = (0.28, 0.22, 0.14)
VERMILION_ACCENT    = (0.65, 0.12, 0.08)


def paint_mayor_zhao_atlas():
    a = Atlas(S, seed=606)

    # 1. York Limestone Monument Plinth
    x, y, w, h = R_MONUMENT_PLINTH
    a.rect(x, y, w, h, STONE_BASE)
    for my in range(y, y + h, 24):
        a.rect(x, my, w, 2, STONE_DARK)
        offset = 32 if ((my - y) // 24) % 2 else 0
        for mx in range(x - offset, x + w, 64):
            a.rect(max(x, mx), my, 2, 24, STONE_DARK)
    # Lotus petal & cloud molding band
    band_y = y + h - 36
    a.rect(x, band_y, w, 32, STONE_DARK)
    a.rect(x, band_y + 3, w, 26, STONE_BASE)
    for cx in range(x + 4, x + w - 24, 28):
        a.rect(cx, band_y + 6, 20, 18, STONE_CREAM)
        a.rect(cx + 4, band_y + 10, 12, 10, STONE_DARK)
        a.rect(cx + 6, band_y + 12, 8, 6, IMPERIAL_GOLD)
    a.noise(x, y, w, h, 0.03)

    # 2. Bronze Commemorative Plaque (R_BRONZE_PLAQUE)
    x, y, w, h = R_BRONZE_PLAQUE
    a.rect(x, y, w, h, PLAQUE_BRONZE)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.18, 0.14, 0.10))
    a.rect(x + 6, y + 6, w - 12, 2, IMPERIAL_GOLD)
    a.rect(x + 6, y + h - 8, w - 12, 2, IMPERIAL_GOLD)
    a.rect(x + 6, y + 6, 2, h - 12, IMPERIAL_GOLD)
    a.rect(x + w - 8, y + 6, 2, h - 12, IMPERIAL_GOLD)

    # Main Title: "MAYOR ZHAO"
    title_str = "MAYOR ZHAO"
    tw = a.text_width(title_str, scale=4)
    tx = x + (w - tw) // 2
    a.text(tx + 2, y + h - 22, title_str, GOLD_DARK, scale=4)
    a.text(tx, y + h - 20, title_str, IMPERIAL_GOLD, scale=4)

    # Chinese "市長 趙" (Mayor Zhao)
    for idx, cx in enumerate([x + 32, x + w - 60]):
        a.rect(cx, y + h - 56, 24, 24, IMPERIAL_GOLD)
        a.rect(cx + 3, y + h - 53, 18, 18, (0.18, 0.14, 0.10))
        a.rect(cx + 6, y + h - 50, 12, 12, IMPERIAL_GOLD)

    # Subtitle: "BENEFACTOR OF EAST YORK"
    sub_str = "BENEFACTOR OF EAST YORK"
    sw = a.text_width(sub_str, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 24, sub_str, IMPERIAL_GOLD, scale=2)

    # 3. Mayor Zhao Formal Suit & Embroidered Vest (R_MAYOR_SUIT)
    x, y, w, h = R_MAYOR_SUIT
    a.rect(x, y, w, h, BRONZE_DARK)
    # Dragon waistcoat center panel
    wx, wy, ww, wh = x + 32, y + 10, w - 64, h - 20
    a.rect(wx, wy, ww, wh, VERMILION_ACCENT)
    for dy in range(wy + 8, wy + wh - 8, 16):
        a.rect(wx + 8, dy, ww - 16, 2, IMPERIAL_GOLD)
    # Suit buttons
    for by in range(wy + 12, wy + wh - 12, 18):
        a.rect(wx + ww // 2 - 3, by, 6, 6, IMPERIAL_GOLD)

    # 4. Mayor Zhao Head & Features (R_MAYOR_HEAD)
    x, y, w, h = R_MAYOR_HEAD
    a.rect(x, y, w, h, BRONZE_DARK)
    a.rect(x + 16, y + 16, w - 32, h - 32, BRONZE_PATINA)
    # Moustache & hair
    a.rect(x + 28, y + 28, w - 56, 12, BRONZE_DARK)
    a.rect(x + 20, y + h - 32, w - 40, 20, BRONZE_DARK)

    # 5. Mayoral Chain of Office & Golden Key (R_GOLD_CHAIN_KEY)
    x, y, w, h = R_GOLD_CHAIN_KEY
    a.rect(x, y, w, h, GOLD_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, IMPERIAL_GOLD)
    # Medallion & Key
    a.rect(x + w // 2 - 12, y + 16, 24, 24, GOLD_HILITE)
    a.rect(x + 16, y + h - 36, w - 32, 14, GOLD_HILITE)
    a.noise(x, y, w, h, 0.02)

    # 6. Plaza Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.50, 0.48, 0.44))
    for my in range(y, y + h, 20):
        a.rect(x, my, w, 2, (0.38, 0.36, 0.33))
        offset = 24 if ((my - y) // 20) % 2 else 0
        for mx in range(x - offset, x + w, 48):
            a.rect(max(x, mx), my, 2, 20, (0.38, 0.36, 0.33))

    # 7. Bronze Base (R_BRONZE_BASE)
    x, y, w, h = R_BRONZE_BASE
    a.rect(x, y, w, h, BRONZE_DARK)
    for by in range(y, y + h, 16):
        a.rect(x, by, w, 2, BRONZE_PATINA)

    return a.to_image("statue_east_york_mayor_zhao_atlas", OUT_DIR)


def make_cylinder(name, r=0.15, h=0.6, segs=8, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    x, y, z = at
    bot_ring = []
    top_ring = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vx = x + r * math.cos(a)
        vy = y + r * math.sin(a)
        bot_ring.append(bm.verts.new((vx, vy, z)))
        top_ring.append(bm.verts.new((vx, vy, z + h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]))
    bm.faces.new(reversed(bot_ring))
    bm.faces.new(top_ring)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    img = paint_mayor_zhao_atlas()
    mat = material_for(img, "MayorZhao_Mat")

    parts = []

    def register_box(name, w, d, h, at, front=None, sides=None, top=None, back=None):
        obj = kit.make_box(name, w, d, h, at=at)
        obj.data.materials.append(mat)
        if front is not None:
            kit.map_faces_to_region(obj, front, S, only=lambda f: f.normal.y < -0.5)
        if sides is not None:
            kit.map_faces_to_region(obj, sides, S, only=lambda f: abs(f.normal.x) > 0.5)
        if top is not None:
            kit.map_faces_to_region(obj, top, S, only=lambda f: abs(f.normal.z) > 0.5)
        if back is not None:
            kit.map_faces_to_region(obj, back, S, only=lambda f: f.normal.y > 0.5)
        parts.append(obj)
        return obj

    # =========================================================================
    # 1. Monument Stone Plinth (1.50m x 1.50m footprint, Height: 1.40m)
    # =========================================================================
    # Plaza stepping slab
    register_box("PlazaStep", 1.50, 1.50, 0.12, (0.0, 0.0, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # Base Tier 1
    register_box("PlinthTier1", 1.30, 1.30, 0.25, (0.0, 0.0, 0.12),
                 front=R_MONUMENT_PLINTH, sides=R_MONUMENT_PLINTH, top=R_MONUMENT_PLINTH)

    # Plinth Shaft (Core)
    register_box("PlinthShaft", 1.10, 1.10, 0.85, (0.0, 0.0, 0.37),
                 front=R_MONUMENT_PLINTH, sides=R_MONUMENT_PLINTH, back=R_MONUMENT_PLINTH)

    # Commemorative Bronze Plaque on Front
    register_box("BronzePlaque", 0.90, 0.06, 0.55, (0.0, -0.56, 0.55),
                 front=R_BRONZE_PLAQUE, sides=R_GOLD_CHAIN_KEY, top=R_GOLD_CHAIN_KEY)

    # Plinth Cornice & Top Cap
    register_box("PlinthCornice", 1.25, 1.25, 0.18, (0.0, 0.0, 1.22),
                 front=R_MONUMENT_PLINTH, sides=R_MONUMENT_PLINTH, top=R_MONUMENT_PLINTH)

    # Bronze Statue Sub-Base
    register_box("StatueSubBase", 0.90, 0.90, 0.08, (0.0, 0.0, 1.40),
                 front=R_BRONZE_BASE, sides=R_BRONZE_BASE, top=R_BRONZE_BASE)

    # =========================================================================
    # 2. Standing Bronze Figure of Mayor Zhao (Height: 2.05m, Z: 1.48 to 3.50m)
    # =========================================================================
    # Boots / Shoes
    for sx in [-0.14, 0.14]:
        register_box(f"MayorShoe_{sx:.2f}", 0.16, 0.30, 0.12, (sx, -0.04, 1.48),
                     front=R_BRONZE_BASE, sides=R_BRONZE_BASE, top=R_BRONZE_BASE)

    # Legs (Trousered in formal bronze/tweed)
    for lx in [-0.14, 0.14]:
        leg = make_cylinder(f"MayorLeg_{lx:.2f}", r=0.10, h=0.75, segs=8, at=(lx, 0.0, 1.60))
        leg.data.materials.append(mat)
        kit.map_faces_to_region(leg, R_MAYOR_SUIT, S)
        parts.append(leg)

    # Mayoral Long Tailcoat & Waistcoat Torso
    register_box("MayorTailcoatLower", 0.56, 0.40, 0.45, (0.0, 0.02, 2.10),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, back=R_MAYOR_SUIT, top=R_MAYOR_SUIT)
    register_box("MayorTorsoVest", 0.52, 0.36, 0.50, (0.0, 0.0, 2.45),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, back=R_MAYOR_SUIT, top=R_MAYOR_SUIT)

    # Gold Chain of Office across chest
    register_box("GoldChainOfOffice", 0.48, 0.38, 0.22, (0.0, -0.02, 2.65),
                 front=R_GOLD_CHAIN_KEY, sides=R_GOLD_CHAIN_KEY, top=R_GOLD_CHAIN_KEY)

    # Left Arm (Resting gracefully on hip / ceremonial mayoral cane)
    register_box("MayorLeftArmUpper", 0.14, 0.16, 0.35, (-0.32, 0.0, 2.55),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, top=R_MAYOR_SUIT)
    register_box("MayorLeftArmLower", 0.12, 0.14, 0.30, (-0.28, -0.10, 2.30),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, top=R_MAYOR_SUIT)
    register_box("MayorLeftHand", 0.12, 0.14, 0.10, (-0.26, -0.15, 2.25),
                 front=R_MAYOR_HEAD, sides=R_MAYOR_HEAD, top=R_MAYOR_HEAD)

    # Right Arm Outstretched (Holding the Ceremonial Golden Key to East York)
    register_box("MayorRightArmUpper", 0.14, 0.16, 0.35, (0.32, 0.0, 2.55),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, top=R_MAYOR_SUIT)
    register_box("MayorRightArmFore", 0.12, 0.40, 0.12, (0.32, -0.22, 2.55),
                 front=R_MAYOR_SUIT, sides=R_MAYOR_SUIT, top=R_MAYOR_SUIT)
    register_box("MayorRightHand", 0.10, 0.12, 0.10, (0.32, -0.44, 2.55),
                 front=R_MAYOR_HEAD, sides=R_MAYOR_HEAD, top=R_MAYOR_HEAD)

    # Ceremonial Golden Key to East York in Hand
    register_box("GoldenKeyShaft", 0.06, 0.30, 0.06, (0.32, -0.52, 2.55),
                 front=R_GOLD_CHAIN_KEY, sides=R_GOLD_CHAIN_KEY, top=R_GOLD_CHAIN_KEY)
    register_box("GoldenKeyBow", 0.16, 0.06, 0.14, (0.32, -0.38, 2.55),
                 front=R_GOLD_CHAIN_KEY, sides=R_GOLD_CHAIN_KEY, top=R_GOLD_CHAIN_KEY)
    register_box("GoldenKeyBit", 0.10, 0.06, 0.12, (0.32, -0.64, 2.52),
                 front=R_GOLD_CHAIN_KEY, sides=R_GOLD_CHAIN_KEY, top=R_GOLD_CHAIN_KEY)

    # Neck & Mandarin Collar
    register_box("MayorNeck", 0.18, 0.18, 0.12, (0.0, 0.0, 2.95),
                 front=R_MAYOR_HEAD, sides=R_MAYOR_HEAD, top=R_MAYOR_HEAD)

    # Head, Hair & Distinguished Moustache
    register_box("MayorHead", 0.26, 0.28, 0.32, (0.0, -0.02, 3.05),
                 front=R_MAYOR_HEAD, sides=R_MAYOR_HEAD, back=R_MAYOR_HEAD, top=R_MAYOR_HEAD)
    # Formal Top Hair
    register_box("MayorHair", 0.28, 0.30, 0.12, (0.0, 0.0, 3.32),
                 front=R_MAYOR_HEAD, sides=R_MAYOR_HEAD, top=R_MAYOR_HEAD)

    # =========================================================================
    # Finalize & Export
    # =========================================================================
    shell = kit.join(parts, "Statue_East_York_Mayor_Zhao")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "statue_east_york_mayor_zhao_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "statue_east_york_mayor_zhao.glb"
    kit.export_glb(glb_path, [shell])
    print("[statue_east_york_mayor_zhao] generation complete.")


main()
