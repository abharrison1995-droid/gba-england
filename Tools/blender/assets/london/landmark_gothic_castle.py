"""Gothic Castle / Tower of London Keep (Medieval Stone Fortress Landmark).

Specs:
- 10.0m x 8.5m footprint, Height: 12.5m to turret battlements / flagpole.
- Medieval Norman & Gothic fortress architecture:
  - Heavy weathered Kentish ragstone ashlar walls with arrow slits and cross loopholes.
  - 4 prominent corner battlements / machicolated turrets.
  - Central arched gatehouse with heavy iron-reinforced timber portcullis.
  - Central elevated keep tower with royal heraldic banner flagpole.
  - Damp foundation plinth with moss and iron torch wall brackets.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_gothic_castle.py
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
R_CASTLE_STONE  = (0,   256, 256, 256)   # Heavy Kentish ragstone ashlar with arrow loops & moss
R_PORTCULLIS    = (256, 256, 256, 256)   # Heavy iron-spiked portcullis gate & stone arch surround
R_BATTLE_CRENELS= (0,   128, 256, 128)   # Crenellated battlements & machicolation stone brackets
R_ROYAL_BANNER  = (256, 128, 128, 128)   # St George royal heraldic banner flag
R_STONE_PLINTH  = (384, 128, 128, 128)   # Dressed stone foundation plinth with moss & lichen
R_ROOF_LEAD     = (0,   0,   256, 128)   # Weathered lead fortress roof deck
R_IRON_TORCH    = (256, 0,   128, 128)   # Wrought-iron wall torch brazier with orange fire
R_OAK_TIMBER    = (384, 0,   128, 128)   # Heavy studded oak gate timbers

# --- Palette Colors ---
STONE_RAGSTONE  = (0.58, 0.56, 0.52)
STONE_DARK      = (0.38, 0.36, 0.34)
STONE_MORTAR    = (0.45, 0.44, 0.42)
MOSS_GREEN      = (0.26, 0.36, 0.20)
IRON_BLACK      = (0.14, 0.14, 0.16)
OAK_EBONY       = (0.24, 0.16, 0.10)
GOLD_CREST      = (0.92, 0.78, 0.24)
ROYAL_RED       = (0.82, 0.14, 0.12)
FIRE_ORANGE     = (0.98, 0.55, 0.10)


def paint_castle_atlas():
    a = Atlas(S, seed=2801)

    # 1. Ragstone Castle Walls with Arrow Slits (R_CASTLE_STONE)
    x, y, w, h = R_CASTLE_STONE
    a.bricks(x, y, w, h, brick=STONE_RAGSTONE, mortar=STONE_MORTAR, bw=32, bh=14, jitter=0.08)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.20)
    # Narrow Arrow Loop Slits
    for ay in [y + 40, y + 150]:
        for ax in [x + 36, x + 116, x + 196]:
            # Arrow slit (cross shape)
            a.rect(ax + 8, ay, 4, 48, (0.08, 0.08, 0.08))
            a.rect(ax, ay + 20, 20, 4, (0.08, 0.08, 0.08))
            a.rect(ax + 4, ay - 4, 12, 4, STONE_DARK)  # stone sill
    # Moss along bottom
    for mx in range(x, x + w, 20):
        a.disc(mx, y + 10, 14, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 2. Portcullis Gate & Arch (R_PORTCULLIS)
    x, y, w, h = R_PORTCULLIS
    a.rect(x, y, w, h, STONE_RAGSTONE)
    # Arched portal surround
    px, py, pw, ph = x + 16, y + 16, w - 32, h - 32
    a.rect(px, py, pw, ph, (0.10, 0.10, 0.12))
    # Heavy oak door backing
    a.rect(px + 6, py + 6, pw - 12, ph - 12, OAK_EBONY)
    # Iron Portcullis Grid with Spikes at bottom
    for gx in range(px + 12, px + pw - 12, 18):
        a.rect(gx, py + 12, 4, ph - 24, IRON_BLACK)
        # Spiked bottom tip
        a.disc(gx + 2, py + 8, 4, IRON_BLACK)
    for gy in range(py + 24, py + ph - 24, 24):
        a.rect(px + 6, gy, pw - 12, 4, IRON_BLACK)
        # Iron rivets
        for rx in range(px + 12, px + pw - 12, 18):
            a.disc(rx + 2, gy + 2, 3, (0.4, 0.4, 0.4))
    a.noise(x, y, w, h, 0.03)

    # 3. Battlements & Machicolations (R_BATTLE_CRENELS)
    x, y, w, h = R_BATTLE_CRENELS
    a.rect(x, y, w, h, STONE_RAGSTONE)
    # Machicolation corbel brackets
    for mx in range(x + 8, x + w, 24):
        a.rect(mx, y + 10, 12, 20, STONE_DARK)
    # Crenel openings
    for cx in range(x + 16, x + w, 40):
        a.rect(cx, y + h - 36, 18, 36, (0.15, 0.15, 0.16))
    a.noise(x, y, w, h, 0.035)

    # 4. Royal Heraldic Banner (R_ROYAL_BANNER)
    x, y, w, h = R_ROYAL_BANNER
    a.rect(x, y, w, h, ROYAL_RED)
    # St George cross & Royal Lion
    a.rect(x + w // 2 - 6, y, 12, h, (0.95, 0.95, 0.95))
    a.rect(x, y + h // 2 - 6, w, 12, (0.95, 0.95, 0.95))
    a.disc(x + w // 2, y + h // 2, 20, GOLD_CREST)
    a.noise(x, y, w, h, 0.02)

    # 5. Stone Plinth (R_STONE_PLINTH)
    x, y, w, h = R_STONE_PLINTH
    a.rect(x, y, w, h, (0.50, 0.48, 0.44))
    for mx in range(x, x + w, 16):
        a.disc(mx, y + 12, 10, MOSS_GREEN)
    a.noise(x, y, w, h, 0.03)

    # 6. Fortress Lead Roof (R_ROOF_LEAD)
    x, y, w, h = R_ROOF_LEAD
    a.rect(x, y, w, h, (0.28, 0.30, 0.32))
    a.noise(x, y, w, h, 0.04)

    # 7. Iron Torch Brazier (R_IRON_TORCH)
    x, y, w, h = R_IRON_TORCH
    a.rect(x, y, w, h, (0.14, 0.14, 0.16))
    a.rect(x + 14, y + 10, w - 28, 16, IRON_BLACK)
    a.disc(x + w // 2, y + h // 2 + 10, 24, FIRE_ORANGE)
    a.disc(x + w // 2, y + h // 2 + 10, 14, (0.98, 0.90, 0.30))
    a.noise(x, y, w, h, 0.02)

    # 8. Oak Timbers (R_OAK_TIMBER)
    x, y, w, h = R_OAK_TIMBER
    a.rect(x, y, w, h, OAK_EBONY)
    for ox in range(x, x + w, 16):
        a.rect(ox, y, 2, h, (0.12, 0.08, 0.05))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_gothic_castle_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_PLINTH, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_PLINTH, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_castle_atlas()
    mat = material_for(img, "mat_gothic_castle")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Gothic Castle / Tower of London Keep (10.0m x 8.5m Footprint, Height: 12.5m)
    # - Heavy Plinth Base (Z: 0.0 to 0.3m)
    # - Main Fortress Body (Width 9.2m, D: 7.6m, Z: 0.3m to 8.5m)
    # - 4 Machicolated Corner Turrets (Width 2.2m, Z: 0.3m to 10.8m)
    # - Arched Gatehouse with Spiked Portcullis (Z: 0.3m to 4.5m)
    # - Elevated Central Keep Tower (Width 4.6m, Z: 8.5m to 12.0m) + Royal Flagpole
    # =========================================================================

    # 1. Foundation Stone Plinth (10.4m x 9.0m, Z = 0.00 to 0.30m)
    register_box("CastlePlinth", 10.40, 9.00, 0.30, (0.0, 0.0, 0.0),
                 front=R_STONE_PLINTH, sides=R_STONE_PLINTH, top=R_STONE_PLINTH)

    # 2. Main Fortress Wall Body (9.0m x 7.4m, Z: 0.30m to 8.50m, H: 8.20m)
    register_box("FortressBody", 9.00, 7.40, 8.20, (0.0, 0.0, 0.30),
                 front=R_CASTLE_STONE, sides=R_CASTLE_STONE, back=R_CASTLE_STONE)

    # 3. Main Battlements Parapet (Z = 8.50m to 9.30m, H: 0.80m)
    register_box("MainBattlements", 9.40, 7.80, 0.80, (0.0, 0.0, 8.50),
                 front=R_BATTLE_CRENELS, sides=R_BATTLE_CRENELS, top=R_ROOF_LEAD)

    # 4. 4 Corner Fortress Turrets (Z: 0.30m to 10.80m, H: 10.50m)
    for tx, ty in [(-3.80, -3.00), (3.80, -3.00), (3.80, 3.00), (-3.80, 3.00)]:
        # Turret body
        register_box(f"TurretBody_{tx}_{ty}", 2.20, 2.20, 10.00, (tx, ty, 0.30),
                     front=R_CASTLE_STONE, sides=R_CASTLE_STONE, back=R_CASTLE_STONE)
        # Turret machicolated battlement top
        register_box(f"TurretTop_{tx}_{ty}", 2.50, 2.50, 0.80, (tx, ty, 10.30),
                     front=R_BATTLE_CRENELS, sides=R_BATTLE_CRENELS, top=R_ROOF_LEAD)

    # 5. Arched Gatehouse & Heavy Iron Portcullis (Front Center: X = 0.0m, Z = 0.30m to 4.80m)
    register_box("GatehouseSurround", 4.20, 1.00, 4.50, (0.0, -3.80, 0.30),
                 front=R_CASTLE_STONE, sides=R_CASTLE_STONE, top=R_BATTLE_CRENELS)
    register_box("PortcullisGate", 3.20, 0.20, 4.00, (0.0, -4.22, 0.30),
                 front=R_PORTCULLIS, sides=R_STONE_PLINTH, top=R_STONE_PLINTH)

    # Twin Wall Torch Braziers (Flanking gate at X = -2.60m, +2.60m)
    register_box("TorchLeft", 0.40, 0.40, 0.70, (-2.60, -3.85, 2.80),
                 front=R_IRON_TORCH, sides=R_IRON_TORCH, top=R_IRON_TORCH)
    register_box("TorchRight", 0.40, 0.40, 0.70, (2.60, -3.85, 2.80),
                 front=R_IRON_TORCH, sides=R_IRON_TORCH, top=R_IRON_TORCH)

    # 6. Elevated Central Keep Tower (4.6m x 4.6m, Z: 8.50m to 11.80m, H: 3.30m)
    register_box("CentralKeep", 4.60, 4.60, 3.30, (0.0, 0.0, 8.50),
                 front=R_CASTLE_STONE, sides=R_CASTLE_STONE, back=R_CASTLE_STONE)
    register_box("KeepBattlements", 5.00, 5.00, 0.80, (0.0, 0.0, 11.80),
                 front=R_BATTLE_CRENELS, sides=R_BATTLE_CRENELS, top=R_ROOF_LEAD)

    # 7. Royal Flagpole & St George Banner (Z = 12.60m to 14.80m)
    register_box("Flagpole", 0.12, 0.12, 2.20, (0.0, 0.0, 12.60),
                 front=R_STONE_PLINTH, sides=R_STONE_PLINTH, top=R_STONE_PLINTH)
    register_box("RoyalBanner", 0.08, 1.40, 0.90, (0.0, 0.70, 13.80),
                 front=R_ROYAL_BANNER, sides=R_ROYAL_BANNER, top=R_ROYAL_BANNER)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_Gothic_Castle")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_gothic_castle_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_gothic_castle.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_gothic_castle.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_gothic_castle_preview.png")
        shutil.copy2(OUT_DIR / "landmark_gothic_castle_atlas.png", TOOLS_OUT_DIR / "landmark_gothic_castle_atlas.png")
    except Exception as e:
        print(f"[landmark_gothic_castle] note: {e}")

    print("[landmark_gothic_castle] generation complete.")


main()
