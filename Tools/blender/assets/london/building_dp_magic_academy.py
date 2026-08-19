"""DP Magic Academy Guild Building (10.0m x 8.5m Arcane Guildhall).

Specs:
- 10.0m x 8.5m footprint, Height: 11.8m to astrological observatory cupola spire.
- Dark mystical Gothic / Victorian esoteric guildhall: charcoal-indigo stone and dark brick facade with gold celestial runes.
- Grand gold engraved header sign: "D.P. MAGIC ACADEMY - GUILD OF ARCANUM".
- Grand arched mystical entrance with dark oak & brass sigil doors and twin blue-glowing arcane brazier wall lanterns.
- Tall leaded stained-glass Gothic windows with celestial constellations and arcane glyphs.
- Projecting 2nd-floor library oriel window with gold runic border.
- Rooftop copper astrological observatory cupola dome with telescope slit and lightning spire.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_dp_magic_academy.py
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
R_ACADEMY_STONE = (0,   256, 256, 256)   # Dark indigo-charcoal stone masonry with gold runes
R_COPPER_DOME   = (256, 256, 128, 256)   # Verdigris green oxidized copper observatory dome
R_STAINED_GLASS = (0,   128, 256, 128)   # Arcane celestial stained glass windows
R_MAGIC_DOORS   = (256, 128, 128, 128)   # Heavy dark oak doors with glowing brass arcane sigils
R_ACADEMY_SIGN  = (0,   0,   256, 128)   # Gold engraved "D.P. MAGIC ACADEMY" guild banner
R_STONE_TRIM    = (256, 0,   128, 128)   # Dressed silver-grey stone quoins, battlements & coping
R_ORIEL_WINDOW  = (384, 384, 128, 128)   # 2nd-floor oriel library window with gold inlays
R_BLUE_BRAZIER  = (384, 256, 128, 128)   # Glowing cyan/blue arcane wall lantern sconce
R_OBSERVATORY   = (384, 128, 128, 128)   # Astronomical slit shutters & brass astrolabe detail
R_ROOF_LEAD     = (384, 0,   128, 128)   # Weathered dark lead roof deck

# --- Palette Colors ---
STONE_INDIGO    = (0.28, 0.28, 0.32)
STONE_MORTAR    = (0.20, 0.20, 0.24)
GOLD_RUNE       = (0.92, 0.78, 0.25)
COPPER_VERDIG   = (0.34, 0.58, 0.52)
COPPER_DARK     = (0.22, 0.40, 0.36)
GLASS_PURPLE    = (0.32, 0.20, 0.42)
GLASS_CYAN      = (0.20, 0.55, 0.75)
OAK_EBONY       = (0.18, 0.16, 0.15)
BRASS_GOLD      = (0.86, 0.72, 0.22)
STONE_SILVER    = (0.65, 0.65, 0.68)
BLUE_FIRE       = (0.30, 0.80, 0.98)


def paint_dp_academy_atlas():
    a = Atlas(S, seed=1801)

    # 1. Dark Indigo-Charcoal Masonry with Gold Celestial Runes (R_ACADEMY_STONE)
    x, y, w, h = R_ACADEMY_STONE
    a.bricks(x, y, w, h, brick=STONE_INDIGO, mortar=STONE_MORTAR, bw=32, bh=14, jitter=0.06)
    # Engraved Gold Celestial Sigils and Star Glyphs
    for gx, gy in [(x + 40, y + 60), (x + 180, y + 80), (x + 120, y + 190), (x + 210, y + 170)]:
        a.disc(gx, gy, 8, GOLD_RUNE)
        a.disc(gx, gy, 6, STONE_INDIGO)
        a.disc(gx, gy, 2, GOLD_RUNE)
        # Star rays
        a.rect(gx - 10, gy, 20, 2, GOLD_RUNE)
        a.rect(gx, gy - 10, 2, 20, GOLD_RUNE)
    a.noise(x, y, w, h, 0.035)

    # 2. Verdigris Oxidized Copper Dome (R_COPPER_DOME)
    x, y, w, h = R_COPPER_DOME
    a.rect(x, y, w, h, COPPER_VERDIG)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, COPPER_DARK)
        a.rect(x, ry + 2, w, 1, (0.42, 0.68, 0.60))
    # Vertical rib seams
    for rx in range(x, x + w, 24):
        a.rect(rx, y, 2, h, COPPER_DARK)
    a.noise(x, y, w, h, 0.03)

    # 3. Arcane Stained Glass Windows (R_STAINED_GLASS)
    x, y, w, h = R_STAINED_GLASS
    a.rect(x, y, w, h, STONE_SILVER)
    # Window glazed interior
    wx, wy, ww, wh = x + 12, y + 10, w - 24, h - 20
    a.rect(wx, wy, ww, wh, GLASS_PURPLE)
    # Central glowing alchemical circle
    cx, cy = wx + ww // 2, wy + wh // 2
    a.disc(cx, cy, 32, GLASS_CYAN)
    a.disc(cx, cy, 26, GLASS_PURPLE)
    a.disc(cx, cy, 14, GOLD_RUNE)
    a.disc(cx, cy, 8, BLUE_FIRE)
    # Gothic leaded tracery
    for ly in range(wy + 8, wy + wh, 18):
        a.rect(wx, ly, ww, 2, (0.12, 0.12, 0.14))
    a.noise(x, y, w, h, 0.025)

    # 4. Mystical Dark Oak & Brass Sigil Doors (R_MAGIC_DOORS)
    x, y, w, h = R_MAGIC_DOORS
    a.rect(x, y, w, h, STONE_SILVER)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, OAK_EBONY)
    # Door central split
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.08, 0.08, 0.08))
    # Grand Brass Star of Daniel Sigil on doors
    dcx, dcy = dx + dw // 2, dy + dh // 2
    a.disc(dcx, dcy, 28, BRASS_GOLD)
    a.disc(dcx, dcy, 24, OAK_EBONY)
    a.disc(dcx, dcy, 10, BRASS_GOLD)
    a.disc(dcx, dcy, 6, BLUE_FIRE)
    # Iron/brass hinges
    for hy in [dy + 14, dy + dh - 20]:
        a.rect(dx + 4, hy, dw - 8, 4, BRASS_GOLD)
    a.noise(x, y, w, h, 0.025)

    # 5. Gold "D.P. MAGIC ACADEMY" Banner (R_ACADEMY_SIGN)
    x, y, w, h = R_ACADEMY_SIGN
    a.rect(x, y, w, h, (0.14, 0.14, 0.18))
    # Gold border
    a.rect(x + 4, y + 4, w - 8, 4, GOLD_RUNE)
    a.rect(x + 4, y + h - 8, w - 8, 4, GOLD_RUNE)
    a.rect(x + 4, y + 4, 4, h - 8, GOLD_RUNE)
    a.rect(x + w - 8, y + 4, 4, h - 8, GOLD_RUNE)
    # Guild Star Emblem on left and right
    a.disc(x + 20, y + h // 2, 10, GOLD_RUNE)
    a.disc(x + 20, y + h // 2, 5, (0.14, 0.14, 0.18))
    a.disc(x + w - 20, y + h // 2, 10, GOLD_RUNE)
    a.disc(x + w - 20, y + h // 2, 5, (0.14, 0.14, 0.18))
    # Crisp Gold text
    s1 = "D.P. MAGIC"
    w1 = a.text_width(s1, scale=3)
    a.text(x + (w - w1) // 2, y + h - 18, s1, GOLD_RUNE, scale=3)
    s2 = "ACADEMY"
    w2 = a.text_width(s2, scale=3)
    a.text(x + (w - w2) // 2, y + h - 52, s2, GOLD_RUNE, scale=3)
    s3 = "GUILD OF ARCANUM"
    w3 = a.text_width(s3, scale=1)
    a.text(x + (w - w3) // 2, y + 16, s3, (0.80, 0.70, 0.30), scale=1)
    a.noise(x, y, w, h, 0.02)

    # 6. Silver Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_SILVER)
    for qy in range(y, y + h, 20):
        a.rect(x, qy, w, 2, (0.45, 0.45, 0.48))
    a.noise(x, y, w, h, 0.03)

    # 7. Oriel Library Window (R_ORIEL_WINDOW)
    x, y, w, h = R_ORIEL_WINDOW
    a.rect(x, y, w, h, STONE_SILVER)
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_PURPLE)
    # Gold runic border
    a.rect(x + 8, y + 8, w - 16, 4, GOLD_RUNE)
    a.rect(x + 8, y + h - 12, w - 16, 4, GOLD_RUNE)
    # Diamond leaded panes
    for gy in range(y + 14, y + h - 14, 16):
        a.rect(x + 8, gy, w - 16, 2, (0.10, 0.10, 0.12))
    a.noise(x, y, w, h, 0.02)

    # 8. Blue Fire Brazier (R_BLUE_BRAZIER)
    x, y, w, h = R_BLUE_BRAZIER
    a.rect(x, y, w, h, (0.15, 0.15, 0.18))
    # Brass bracket
    a.rect(x + 12, y + 10, w - 24, 16, BRASS_GOLD)
    # Blue flame core
    a.disc(x + w // 2, y + h // 2 + 10, 24, GLASS_CYAN)
    a.disc(x + w // 2, y + h // 2 + 10, 16, BLUE_FIRE)
    a.disc(x + w // 2, y + h // 2 + 10, 8, (0.90, 0.98, 1.0))
    a.noise(x, y, w, h, 0.02)

    # 9. Astronomical Observatory Details (R_OBSERVATORY)
    x, y, w, h = R_OBSERVATORY
    a.rect(x, y, w, h, COPPER_VERDIG)
    a.rect(x + w // 2 - 8, y, 16, h, (0.12, 0.12, 0.14))  # Telescope slit
    a.rect(x + 10, y + 10, 24, 24, BRASS_GOLD)  # Astrolabe plaque
    a.noise(x, y, w, h, 0.02)

    # 10. Lead Roof (R_ROOF_LEAD)
    x, y, w, h = R_ROOF_LEAD
    a.rect(x, y, w, h, (0.30, 0.32, 0.35))
    a.noise(x, y, w, h, 0.04)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_dp_magic_academy_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_TRIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_TRIM, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_dp_academy_atlas()
    mat = material_for(img, "mat_dp_magic_academy")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # D.P. Magic Academy Guild Building (10.0m x 8.5m Footprint)
    # - Main Guildhall Body: 10.0m x 7.5m, 3 Storeys (Z: 0.15 to 8.80m, H: 8.65m)
    # - Central Projecting Entrance Tower & Oriel: Width 3.4m, H: 9.60m
    # - Rooftop Astrological Observatory Cupola & Dome: Z = 8.80 to 11.50m
    # - Arcane Stained Glass Windows, Blue Brazier Sconces & "D.P. MAGIC ACADEMY" Banner
    # =========================================================================

    # 1. Pavement & Entrance Plinth (10.0m x 8.5m, Z = 0.00 to 0.15m)
    register_box("AcademyPlinth", 10.0, 8.50, 0.15, (0.0, -0.25, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Building Body (10.0m x 7.0m, Z: 0.15 to 8.60m, H: 8.45m)
    register_box("GuildhallBody", 10.0, 7.00, 8.45, (0.0, 0.25, 0.15),
                 front=R_ACADEMY_STONE, sides=R_ACADEMY_STONE, back=R_ACADEMY_STONE)

    # 3. Central Projecting Tower (Width: 3.60m, Projects forward by 0.6m, H: 9.60m)
    register_box("CentralTower", 3.60, 7.60, 9.45, (0.0, -0.05, 0.15),
                 front=R_ACADEMY_STONE, sides=R_ACADEMY_STONE, back=R_ACADEMY_STONE)

    # 4. Grand Gold "D.P. MAGIC ACADEMY" Header Sign on Central Tower (Z = 3.70m to 4.70m)
    register_box("AcademySignBoard", 3.60, 0.20, 1.00, (0.0, -3.95, 3.70),
                 front=R_ACADEMY_SIGN, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Grand Arched Mystical Entrance (Y = -3.88m, Z = 0.15 to 3.45m)
    register_box("GrandArchSurround", 2.80, 0.30, 3.35, (0.0, -3.88, 0.15),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("MysticDoors", 2.20, 0.15, 2.90, (0.0, -3.98, 0.25),
                 front=R_MAGIC_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # Twin Blue Fire Brazier Wall Sconces (Flanking entrance at X = -1.80m, +1.80m)
    register_box("BrazierLeft", 0.35, 0.35, 0.65, (-1.80, -3.85, 2.10),
                 front=R_BLUE_BRAZIER, sides=R_BLUE_BRAZIER, top=R_BLUE_BRAZIER)
    register_box("BrazierRight", 0.35, 0.35, 0.65, (1.80, -3.85, 2.10),
                 front=R_BLUE_BRAZIER, sides=R_BLUE_BRAZIER, top=R_BLUE_BRAZIER)

    # 6. 2nd-Storey Projecting Oriel Library Window (Z = 5.20m to 7.60m)
    register_box("OrielWindow", 2.40, 0.50, 2.40, (0.0, -3.95, 5.20),
                 front=R_ORIEL_WINDOW, sides=R_ORIEL_WINDOW, top=R_COPPER_DOME, bottom=R_STONE_TRIM)

    # 7. Flanking Gothic Stained Glass Windows (Left X = -3.20m, Right X = +3.20m)
    for wx in [-3.20, 3.20]:
        # Ground floor arcane window
        register_box(f"WinG_{wx}", 1.40, 0.15, 2.20, (wx, -3.32, 0.80),
                     front=R_STAINED_GLASS, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        # 1st floor arcane window
        register_box(f"Win1_{wx}", 1.40, 0.15, 2.20, (wx, -3.32, 5.20),
                     front=R_STAINED_GLASS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Stepped Stone Parapet & Crenellations (Z = 8.60m to 9.30m)
    register_box("ParapetBase", 10.20, 7.20, 0.40, (0.0, 0.25, 8.60),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_ROOF_LEAD)
    # Tower central crenellated battlements (Z = 9.60m to 10.10m)
    register_box("TowerCrenels", 3.60, 0.40, 0.50, (0.0, -3.75, 9.60),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Rooftop Astrological Observatory Cupola & Copper Dome (Z = 9.00m to 11.50m)
    # Hexagonal / square cupola base (2.8m x 2.8m x 1.4m)
    register_box("ObservatoryBase", 2.80, 2.80, 1.40, (0.0, 0.25, 9.00),
                 front=R_OBSERVATORY, sides=R_OBSERVATORY, top=R_COPPER_DOME)
    # Verdigris Copper Observatory Dome (2.4m x 2.4m x 1.1m)
    register_box("ObservatoryDome", 2.40, 2.40, 1.10, (0.0, 0.25, 10.40),
                 front=R_COPPER_DOME, sides=R_COPPER_DOME, top=R_COPPER_DOME)
    # Spire / Lightning Rod (Height: 0.8m at Z = 11.50m)
    register_box("AstrolabeSpire", 0.12, 0.12, 0.85, (0.0, 0.25, 11.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Dual Corner Chimneys with Lead Caps (Left X = -4.4m, Right X = +4.4m)
    for cx in [-4.40, 4.40]:
        register_box(f"Chimney_{cx}", 0.90, 1.20, 1.80, (cx, 0.25, 8.80),
                     front=R_ACADEMY_STONE, sides=R_ACADEMY_STONE, top=R_STONE_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_DP_Magic_Academy")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_dp_magic_academy_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_dp_magic_academy.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_dp_magic_academy.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_dp_magic_academy_preview.png")
        shutil.copy2(OUT_DIR / "building_dp_magic_academy_atlas.png", TOOLS_OUT_DIR / "building_dp_magic_academy_atlas.png")
    except Exception as e:
        print(f"[building_dp_magic_academy] note: {e}")

    print("[building_dp_magic_academy] generation complete.")


main()
