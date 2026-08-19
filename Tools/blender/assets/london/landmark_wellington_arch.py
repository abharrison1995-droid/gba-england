"""Wellington Arch (Classical Portland Stone Triumphal Arch Landmark).

Specs:
- 10.0m x 5.8m footprint, Height: 9.8m to top bronze quadriga pedestal.
- Neoclassical London triumphal monument:
  - Dressed Portland limestone ashlar masonry with classical rustication.
  - Grand central arched barrel-vault carriage portal.
  - Flanking Corinthian stone columns with carved acanthus capitals and fluted shafts.
  - Classical frieze, modillion cornice, and stepped attic storey.
  - Bronze / gold laurel victory wreaths, royal crests, and top bronze quadriga statue plinth.
  - Ornate wrought-iron and gilded central entrance gates.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_wellington_arch.py
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
OUT_DIR = kit.OUT_DIR
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"

# --- Atlas Region Definitions (x, y, w, h) ---
R_PORTLAND_STONE= (0,   256, 256, 256)   # Dressed Portland stone ashlar with classical rustication
R_ARCH_VAULT    = (256, 256, 256, 256)   # Central coffered barrel-vault portal with rosettes
R_COLUMN_FLUTE  = (0,   128, 256, 128)   # Fluted Corinthian columns with acanthus leaf capitals
R_ATTIC_FRIEZE  = (256, 128, 128, 128)   # Classical frieze with carved relief & gold Latin inscriptions
R_BRONZE_STATUE = (384, 128, 128, 128)   # Dark patinated bronze quadriga / angel of peace
R_STONE_CORNICE = (0,   0,   256, 128)   # Modillion dentil cornice & plinth steps
R_IRON_GATES    = (256, 0,   128, 128)   # Gilded wrought-iron park entrance gates
R_GOLD_WREATH   = (384, 0,   128, 128)   # Gilded bronze laurel victory wreaths & royal crest

# --- Palette Colors ---
STONE_PORTLAND  = (0.84, 0.82, 0.78)
STONE_SHADOW    = (0.64, 0.62, 0.58)
STONE_MORTAR    = (0.55, 0.52, 0.48)
GOLD_BRONZE     = (0.90, 0.78, 0.28)
BRONZE_DARK     = (0.24, 0.22, 0.20)
BRONZE_VERDIG   = (0.32, 0.46, 0.42)
IRON_BLACK      = (0.12, 0.12, 0.14)


def paint_wellington_atlas():
    a = Atlas(S, seed=2601)

    # 1. Portland Stone Ashlar (R_PORTLAND_STONE)
    x, y, w, h = R_PORTLAND_STONE
    a.bricks(x, y, w, h, brick=STONE_PORTLAND, mortar=STONE_MORTAR, bw=36, bh=14, jitter=0.04)
    # Classical rustication horizontal grooves
    for ry in range(y, y + h, 28):
        a.rect(x, ry, w, 3, STONE_SHADOW)
    a.noise(x, y, w, h, 0.025)

    # 2. Coffered Barrel-Vault Portal (R_ARCH_VAULT)
    x, y, w, h = R_ARCH_VAULT
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Coffered stone ceiling panels with rosettes
    for cy in range(y + 12, y + h - 12, 36):
        for cx in range(x + 12, x + w - 12, 36):
            a.rect(cx, cy, 30, 30, STONE_SHADOW)
            a.rect(cx + 4, cy + 4, 22, 22, STONE_PORTLAND)
            a.disc(cx + 15, cy + 15, 6, GOLD_BRONZE)
    a.noise(x, y, w, h, 0.025)

    # 3. Fluted Corinthian Columns (R_COLUMN_FLUTE)
    x, y, w, h = R_COLUMN_FLUTE
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Acanthus leaf capital at top
    a.rect(x, y + h - 24, w, 24, STONE_SHADOW)
    for kx in range(x + 4, x + w, 16):
        a.disc(kx, y + h - 12, 8, GOLD_BRONZE)
    # Vertical flutes
    for fx in range(x, x + w, 14):
        a.rect(fx, y, 4, h - 26, STONE_SHADOW)
        a.rect(fx + 4, y, 2, h - 26, (0.92, 0.90, 0.86))
    a.noise(x, y, w, h, 0.02)

    # 4. Attic Frieze with Inscription (R_ATTIC_FRIEZE)
    x, y, w, h = R_ATTIC_FRIEZE
    a.rect(x, y, w, h, STONE_PORTLAND)
    a.rect(x + 4, y + 4, w - 8, h - 8, STONE_SHADOW)
    # Gold Relief Inscription: "WELLINGTON"
    s1 = "WELLINGTON"
    w1 = a.text_width(s1, scale=1)
    a.text(x + (w - w1) // 2, y + h // 2 + 10, s1, GOLD_BRONZE, scale=1)
    s2 = "MDCCCXXVIII"
    w2 = a.text_width(s2, scale=1)
    a.text(x + (w - w2) // 2, y + 16, s2, GOLD_BRONZE, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 5. Bronze Quadriga Statue (R_BRONZE_STATUE)
    x, y, w, h = R_BRONZE_STATUE
    a.rect(x, y, w, h, BRONZE_DARK)
    a.shade(x, y, w, h, top=0.10, bottom=-0.10)
    # Winged victory & 4 horse silhouettes
    a.disc(x + w // 2, y + h // 2 + 10, 32, BRONZE_VERDIG)
    a.disc(x + w // 2, y + h // 2 + 10, 20, BRONZE_DARK)
    a.disc(x + w // 2, y + h // 2 + 24, 12, GOLD_BRONZE)  # Angel head
    a.noise(x, y, w, h, 0.03)

    # 6. Stone Modillion Cornice (R_STONE_CORNICE)
    x, y, w, h = R_STONE_CORNICE
    a.rect(x, y, w, h, STONE_PORTLAND)
    # Dentils / modillion brackets
    for dx in range(x, x + w, 16):
        a.rect(dx, y + 20, 8, 16, STONE_SHADOW)
    a.noise(x, y, w, h, 0.025)

    # 7. Gilded Wrought Iron Gates (R_IRON_GATES)
    x, y, w, h = R_IRON_GATES
    a.rect(x, y, w, h, (0.10, 0.10, 0.12))
    # Vertical iron railings & spearheads
    for rx in range(x + 6, x + w - 6, 12):
        a.rect(rx, y, 3, h, IRON_BLACK)
        a.disc(rx + 1, y + h - 10, 5, GOLD_BRONZE)  # gold spear tip
    # Gold rosettes
    for ry in [y + 24, y + h // 2, y + h - 30]:
        a.rect(x, ry, w, 4, IRON_BLACK)
        for gx in range(x + 12, x + w, 24):
            a.disc(gx, ry + 2, 4, GOLD_BRONZE)
    a.noise(x, y, w, h, 0.02)

    # 8. Gold Laurel Wreath (R_GOLD_WREATH)
    x, y, w, h = R_GOLD_WREATH
    a.rect(x, y, w, h, STONE_PORTLAND)
    a.disc(x + w // 2, y + h // 2, 34, GOLD_BRONZE)
    a.disc(x + w // 2, y + h // 2, 22, STONE_PORTLAND)
    a.disc(x + w // 2, y + h // 2, 10, GOLD_BRONZE)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_wellington_arch_atlas", OUT_DIR)


def side(name):
    checks = {
        "front": lambda f: f.normal.y < -0.5,
        "back": lambda f: f.normal.y > 0.5,
        "left": lambda f: f.normal.x < -0.5,
        "right": lambda f: f.normal.x > 0.5,
        "top": lambda f: f.normal.z > 0.5,
        "bottom": lambda f: f.normal.z < -0.5,
    }
    return checks[name]


def map_box(obj, front, sides, back=None, top=None, bottom=None):
    kit.map_faces_to_region(obj, front, S, only=side("front"))
    kit.map_faces_to_region(obj, sides, S, only=side("left"))
    kit.map_faces_to_region(obj, sides, S, only=side("right"))
    kit.map_faces_to_region(obj, back or sides, S, only=side("back"))
    kit.map_faces_to_region(obj, top or R_STONE_CORNICE, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_CORNICE, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_wellington_atlas()
    mat = material_for(img, "mat_wellington_arch")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Wellington Arch (10.0m x 5.8m Footprint, Height: 9.8m)
    # - Plinth Base & Steps (Z: 0.0 to 0.3m)
    # - Left & Right Pylons with Central Open Arched Barrel-Vault (Z: 0.3 to 6.2m)
    # - 4 Corinthian Classical Stone Columns Flanking Entrance
    # - Entablature, Frieze & Modillion Cornice (Z: 6.2m to 7.4m)
    # - Stepped Attic Storey with Gold Latin Inscription (Z: 7.4m to 8.8m)
    # - Top Bronze Quadriga Statue Pedestal (Z: 8.8m to 9.8m)
    # =========================================================================

    # 1. Portland Stone Plinth Base (10.4m x 6.2m, Z = 0.00 to 0.30m)
    register_box("ArchPlinth", 10.40, 6.20, 0.30, (0.0, 0.0, 0.0),
                 front=R_STONE_CORNICE, sides=R_STONE_CORNICE, top=R_STONE_CORNICE)

    # 2. Left Stone Pylon (Width: 3.2m, D: 5.6m, Z: 0.30m to 6.20m, H: 5.90m)
    register_box("LeftPylon", 3.20, 5.60, 5.90, (-3.40, 0.0, 0.30),
                 front=R_PORTLAND_STONE, sides=R_PORTLAND_STONE, back=R_PORTLAND_STONE)

    # 3. Right Stone Pylon (Width: 3.2m, D: 5.6m, Z: 0.30m to 6.20m, H: 5.90m)
    register_box("RightPylon", 3.20, 5.60, 5.90, (3.40, 0.0, 0.30),
                 front=R_PORTLAND_STONE, sides=R_PORTLAND_STONE, back=R_PORTLAND_STONE)

    # 4. Central Arched Barrel-Vault Arch Spandrel (Width: 3.6m, Z: 4.80m to 6.20m, H: 1.40m)
    register_box("ArchSpandrel", 3.60, 5.60, 1.40, (0.0, 0.0, 4.80),
                 front=R_GOLD_WREATH, sides=R_ARCH_VAULT, back=R_GOLD_WREATH, bottom=R_ARCH_VAULT)

    # 5. Gilded Wrought Iron Central Gates (In portal: Z = 0.30m to 4.20m)
    register_box("PortalGates", 3.40, 0.15, 3.90, (0.0, 0.0, 0.30),
                 front=R_IRON_GATES, sides=R_STONE_CORNICE, top=R_STONE_CORNICE)

    # 6. Flanking Corinthian Columns (Front & Back, 4 columns total)
    for col_x in [-2.40, 2.40]:
        # Front column
        register_box(f"ColFront_{col_x}", 0.70, 0.70, 5.80, (col_x, -2.95, 0.35),
                     front=R_COLUMN_FLUTE, sides=R_COLUMN_FLUTE, top=R_STONE_CORNICE)
        # Back column
        register_box(f"ColBack_{col_x}", 0.70, 0.70, 5.80, (col_x, 2.95, 0.35),
                     front=R_COLUMN_FLUTE, sides=R_COLUMN_FLUTE, top=R_STONE_CORNICE)

    # 7. Classical Entablature & Modillion Cornice (10.4m x 6.2m, Z: 6.20m to 7.40m, H: 1.20m)
    register_box("Entablature", 10.40, 6.20, 1.20, (0.0, 0.0, 6.20),
                 front=R_STONE_CORNICE, sides=R_STONE_CORNICE, back=R_STONE_CORNICE, top=R_STONE_CORNICE)

    # 8. Stepped Attic Storey with Gold Inscription (8.6m x 4.8m, Z: 7.40m to 8.80m, H: 1.40m)
    register_box("AtticStorey", 8.60, 4.80, 1.40, (0.0, 0.0, 7.40),
                 front=R_ATTIC_FRIEZE, sides=R_PORTLAND_STONE, back=R_ATTIC_FRIEZE, top=R_STONE_CORNICE)

    # 9. Top Bronze Quadriga Monument Pedestal & Statue (5.2m x 3.2m, Z: 8.80m to 9.80m)
    register_box("StatuePedestal", 5.20, 3.20, 0.40, (0.0, 0.0, 8.80),
                 front=R_STONE_CORNICE, sides=R_STONE_CORNICE, top=R_STONE_CORNICE)
    register_box("QuadrigaStatue", 4.40, 2.40, 0.60, (0.0, 0.0, 9.20),
                 front=R_BRONZE_STATUE, sides=R_BRONZE_STATUE, top=R_BRONZE_STATUE)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_Wellington_Arch")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_wellington_arch_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_wellington_arch.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_wellington_arch.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_wellington_arch_preview.png")
        shutil.copy2(OUT_DIR / "landmark_wellington_arch_atlas.png", TOOLS_OUT_DIR / "landmark_wellington_arch_atlas.png")
    except Exception as e:
        print(f"[landmark_wellington_arch] note: {e}")

    print("[landmark_wellington_arch] generation complete.")


main()
