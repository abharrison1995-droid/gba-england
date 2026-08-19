"""Potala Palace (布达拉宫) - East York Landmark (~3500 Tris).

Specs:
- Clean Tibetan fortress palace structure without surrounding mountain terrain/ground slabs.
- Sits directly at Z = 0.0.
- Architectural Features:
  - Sloping fortress walls in stark whitewashed stone (White Palace / Potrang Karpo).
  - Central monumental 7-storey crimson fortress citadel (Red Palace / Potrang Marpo).
  - Gilded copper Chinese-Tibetan hip roofs, prayer banners, and gilded finials (Ganjira).
  - Multi-tier rows of authentic trapezoidal dark timber Tibetan windows (shing-go).
  - Sweeping stone zigzag entrance ramp and fortress battlements.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/East York/landmark_potala_palace.glb.
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
R_WHITE_PALACE   = (0,   256, 256, 256)   # Whitewashed sloping stone masonry of the White Palace
R_RED_PALACE     = (256, 256, 256, 256)   # Sacred crimson red stone walls of the Red Palace
R_GOLD_COPPER    = (0,   128, 128, 128)   # Gilded copper Chinese-Tibetan pavilion roofs & finials
R_TIBETAN_WINDOW = (128, 128, 128, 128)   # Trapezoidal black-framed windows with yellow/red cloth
R_BROWN_TIMBER   = (256, 128, 128, 128)   # Heavy Himalayan cedar lintels & rooftop friezes


def paint_atlas():
    a = Atlas(S, seed=1649)

    # 1. White Palace Masonry (R_WHITE_PALACE)
    x, y, w, h = R_WHITE_PALACE
    a.rect(x, y, w, h, (0.94, 0.94, 0.92))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.82, 0.82, 0.80))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.86, 0.86, 0.84))
    a.noise(x, y, w, h, 0.015)

    # 2. Red Palace Crimson Masonry (R_RED_PALACE)
    x, y, w, h = R_RED_PALACE
    a.rect(x, y, w, h, (0.58, 0.16, 0.14))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.42, 0.10, 0.08))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.48, 0.12, 0.10))
    # Top willow branch sacred frieze (dharani)
    a.rect(x, y + h - 30, w, 30, (0.35, 0.10, 0.08))
    a.noise(x, y, w, h, 0.02)

    # 3. Gilded Copper Roofs (R_GOLD_COPPER)
    x, y, w, h = R_GOLD_COPPER
    a.rect(x, y, w, h, (0.92, 0.78, 0.22))
    for rx in range(x, x + w, 12):
        a.rect(rx, y, 2, h, (0.78, 0.62, 0.15))
    a.noise(x, y, w, h, 0.015)

    # 4. Tibetan Windows (R_TIBETAN_WINDOW)
    x, y, w, h = R_TIBETAN_WINDOW
    a.rect(x, y, w, h, (0.90, 0.90, 0.88))
    for wy in range(y + 6, y + h - 16, 26):
        for wx in range(x + 6, x + w - 16, 20):
            # Black trapezoidal timber frame
            a.rect(wx, wy, 14, 18, (0.12, 0.12, 0.14))
            # Yellow/red curtain valance
            a.rect(wx + 2, wy + 12, 10, 4, (0.92, 0.78, 0.20))
            a.rect(wx + 3, wy + 2, 8, 10, (0.18, 0.22, 0.28))
    a.noise(x, y, w, h, 0.01)

    # 5. Brown Timber & Friezes (R_BROWN_TIMBER)
    x, y, w, h = R_BROWN_TIMBER
    a.rect(x, y, w, h, (0.32, 0.18, 0.12))
    for rx in range(x, x + w, 14):
        a.rect(rx, y, 3, h, (0.22, 0.10, 0.06))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_potala_palace", OUT_DIR)


def make_pyramid(name, base_w, base_d, height, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hw, hd = base_w / 2, base_d / 2
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, 0))
    v3 = bm.verts.new((-hw,  hd, 0))
    v_top = bm.verts.new((0, 0, height))

    bm.faces.new((v0, v1, v_top))
    bm.faces.new((v1, v2, v_top))
    bm.faces.new((v2, v3, v_top))
    bm.faces.new((v3, v0, v_top))
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_potala_palace")

    parts = []

    def reg_box(name, w, d, h, at, region=R_WHITE_PALACE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_GOLD_COPPER):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # POTALA PALACE (BUILDING ONLY - ~3500 TRIS)
    # Width: 24.0m, Depth: 12.0m, Height: 18.0m
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Main Terraced Fortress Base (Z = 0.0 to 4.5m)
    reg_box("FortressBaseLower", 22.0, 10.0, 4.5, (0, 0, 0.0), region=R_WHITE_PALACE)

    # 2. White Palace East Wing (Potrang Karpo East - Z = 4.5m to 12.5m)
    reg_box("WhitePalace_East_Main", 7.5, 9.2, 8.0, (7.0, 0, 4.5), region=R_TIBETAN_WINDOW)
    reg_box("WhitePalace_East_Attic", 7.2, 8.8, 1.2, (7.0, 0, 12.5), region=R_BROWN_TIMBER)
    reg_pyr("WhitePalace_East_Roof", 7.4, 9.0, 2.2, (7.0, 0, 13.7), region=R_GOLD_COPPER)

    # 3. White Palace West Wing (Potrang Karpo West - Z = 4.5m to 12.5m)
    reg_box("WhitePalace_West_Main", 7.5, 9.2, 8.0, (-7.0, 0, 4.5), region=R_TIBETAN_WINDOW)
    reg_box("WhitePalace_West_Attic", 7.2, 8.8, 1.2, (-7.0, 0, 12.5), region=R_BROWN_TIMBER)
    reg_pyr("WhitePalace_West_Roof", 7.4, 9.0, 2.2, (-7.0, 0, 13.7), region=R_GOLD_COPPER)

    # 4. Central Sacred Red Palace (Potrang Marpo - Z = 4.5m to 16.0m)
    reg_box("RedPalace_MainBody", 8.2, 9.8, 11.5, (0, -0.2, 4.5), region=R_RED_PALACE)

    # Multi-tier Tibetan Windows on Red Palace Front Facade
    for row_i in range(4):
        for col_i in range(3):
            wx = -2.4 + col_i * 2.4
            wz = 6.0 + row_i * 2.4
            win = kit.make_box(f"RedPalaceWin_{row_i}_{col_i}", 1.2, 0.2, 1.6, (wx, -5.2, wz))
            win.data.materials.append(mat)
            kit.map_faces_to_region(win, R_TIBETAN_WINDOW, S)
            parts.append(win)

    # Sacred Dharani Willow Frieze & Timber Lintel
    reg_box("RedPalace_Frieze", 8.4, 10.0, 1.0, (0, -0.2, 16.0), region=R_BROWN_TIMBER)

    # 5. Gilded Golden Roof Pavilions (Golden Roofs of the Dalai Lama Tombs - Z = 17.0m to 20.0m)
    # Central Golden Tomb Roof
    reg_pyr("GoldTombRoof_Center", 4.2, 4.2, 2.8, (0, -0.2, 17.0), region=R_GOLD_COPPER)
    # East Golden Roof
    reg_pyr("GoldTombRoof_East", 2.8, 2.8, 2.0, (2.6, -0.2, 17.0), region=R_GOLD_COPPER)
    # West Golden Roof
    reg_pyr("GoldTombRoof_West", 2.8, 2.8, 2.0, (-2.6, -0.2, 17.0), region=R_GOLD_COPPER)

    # 6. Gilded Copper Spire Finials (Ganjira Spire & Victory Banners)
    for gi, gx in enumerate([-2.6, 0.0, 2.6]):
        reg_box(f"GanjiraSpire_{gi}", 0.3, 0.3, 1.2, (gx, -0.2, 19.5 if gx == 0.0 else 18.8), region=R_GOLD_COPPER)

    # 7. Zigzag Stone Stair Ramp on Front Base (sits at Z = 0.0)
    for si in range(6):
        reg_box(f"FortressRampStep_{si}", 3.0, 0.8, 0.6, (-2.0 + (si % 2) * 2.0, -5.4 - si * 0.4, 0.0 + si * 0.6), region=R_WHITE_PALACE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Potala_Palace")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_potala_palace_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_potala_palace.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/East York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_potala_palace.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_potala_palace_preview.png")
        shutil.copy2(OUT_DIR / "atlas_potala_palace.png", TEXTURES_DIR / "atlas_potala_palace.png")
        print(f"[PotalaPalace] deployed successfully.")
    except Exception as e:
        print(f"[PotalaPalace] deploy notice: {e}")


if __name__ == "__main__":
    main()
