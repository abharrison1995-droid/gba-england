"""London Underground Station Surface Entrance Canopy (Tube Environment Prop).

Specs:
- 6.0m x 4.5m footprint, Height: 4.2m.
- Classic London Underground street level entrance:
  - Edwardian oxblood red ceramic faience tile facade & Portland stone coping.
  - Iconic TfL Illuminated Roundel: Blue bar with white "UNDERGROUND" over bold red circle.
  - Station entrance header sign: "UNDERGROUND - CHARING CROSS STATION".
  - Subterranean descending flight of stone stairs into dark tunnel.
  - Wrought-iron safety railings & bronze central handrail.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_tube_entrance.py
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
R_TUBE_ROUNDEL  = (0,   256, 256, 256)   # Iconic TfL Underground Roundel & Header Signs
R_OXBLOOD_TILES = (256, 256, 256, 256)   # Edwardian glazed oxblood red ceramic faience tiles
R_STAIRS_TUNNEL = (0,   128, 256, 128)   # Descending stone steps into subterranean station
R_STONE_COPING  = (256, 128, 128, 128)   # Portland stone coping, plinths & cornice
R_IRON_RAILING  = (384, 128, 128, 128)   # Black wrought-iron perimeter railings & bronze rail
R_POSTER_FRAME  = (0,   0,   256, 128)   # Station notice boards, TfL line map & West End posters
R_BRONZE_LAMP   = (256, 0,   128, 128)   # Heritage bronze spherical globe wall lanterns
R_CONCRETE_PAVE = (384, 0,   128, 128)   # Pavement slab plinth

# --- Palette Colors ---
TFL_RED         = (0.88, 0.12, 0.14)
TFL_BLUE        = (0.05, 0.18, 0.58)
TFL_WHITE       = (0.96, 0.96, 0.98)
OXBLOOD_RED     = (0.42, 0.12, 0.10)
OXBLOOD_DARK    = (0.26, 0.08, 0.06)
STONE_PORTLAND  = (0.82, 0.80, 0.76)
IRON_BLACK      = (0.12, 0.12, 0.14)
BRONZE_ACCENT   = (0.80, 0.65, 0.25)
STAIR_GREY      = (0.45, 0.46, 0.48)


def paint_tube_entrance_atlas():
    a = Atlas(S, seed=3101)

    # 1. Iconic TfL Underground Roundel & Header Signs (R_TUBE_ROUNDEL)
    x, y, w, h = R_TUBE_ROUNDEL
    a.rect(x, y, w, h, (0.10, 0.10, 0.12))  # Dark enamel casing

    # Main Giant Roundel (Center: cx, cy)
    cx, cy = x + w // 2, y + h // 2 + 20
    # Red outer circle ring (radius 75)
    a.disc(cx, cy, 75, TFL_RED)
    a.disc(cx, cy, 50, (0.10, 0.10, 0.12))
    # Blue central rectangular bar (width 190, height 40)
    bx, by, bw, bh = cx - 95, cy - 20, 190, 40
    a.rect(bx, by, bw, bh, TFL_BLUE)
    # White Johnston-style font "UNDERGROUND"
    s1 = "UNDERGROUND"
    tw1 = a.text_width(s1, scale=2)
    a.text(bx + (bw - tw1) // 2, by + 12, s1, TFL_WHITE, scale=2)

    # Header Bar: "CHARING CROSS STATION"
    a.rect(x + 10, y + 16, w - 20, 36, TFL_BLUE)
    s2 = "CHARING CROSS"
    tw2 = a.text_width(s2, scale=2)
    a.text(x + (w - tw2) // 2, y + 26, s2, TFL_WHITE, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 2. Edwardian Glazed Oxblood Tiles (R_OXBLOOD_TILES)
    x, y, w, h = R_OXBLOOD_TILES
    a.rect(x, y, w, h, OXBLOOD_RED)
    # Glazed tile grid (32x16px) with deep gloss highlights
    for ty in range(y, y + h, 16):
        a.rect(x, ty, w, 2, OXBLOOD_DARK)
        a.rect(x, ty + 2, w, 1, (0.55, 0.20, 0.18))
    for tx in range(x, x + w, 32):
        a.rect(tx, y, 2, h, OXBLOOD_DARK)
    # Large semi-circular station arch moulding
    a.disc(x + w // 2, y + h // 2, 70, OXBLOOD_DARK)
    a.disc(x + w // 2, y + h // 2, 58, OXBLOOD_RED)
    a.noise(x, y, w, h, 0.02)

    # 3. Descending Stairs into Tunnel (R_STAIRS_TUNNEL)
    x, y, w, h = R_STAIRS_TUNNEL
    a.rect(x, y, w, h, (0.05, 0.05, 0.06))  # Dark subterranean tunnel void
    # Stepped stair treads descending
    for sy in range(y + 8, y + h - 8, 14):
        a.rect(x + 16, sy, w - 32, 6, STAIR_GREY)
        a.rect(x + 16, sy + 6, w - 32, 2, (0.85, 0.85, 0.85))  # White safety step nosing
        # Yellow hazard tactile line
        a.rect(x + 16, sy + 8, w - 32, 2, (0.95, 0.85, 0.15))
    a.noise(x, y, w, h, 0.02)

    # 4. Portland Stone Coping (R_STONE_COPING)
    x, y, w, h = R_STONE_COPING
    a.rect(x, y, w, h, STONE_PORTLAND)
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.60, 0.58, 0.54))
    a.noise(x, y, w, h, 0.03)

    # 5. Black Wrought-Iron Railings & Bronze Rail (R_IRON_RAILING)
    x, y, w, h = R_IRON_RAILING
    a.rect(x, y, w, h, (0.15, 0.15, 0.16))
    # Top Bronze polished handrail
    a.rect(x, y + h - 14, w, 10, BRONZE_ACCENT)
    a.rect(x, y + h - 4, w, 4, (0.95, 0.85, 0.45))
    # Vertical black baluster spindles
    for rx in range(x + 8, x + w, 14):
        a.rect(rx, y, 3, h - 14, IRON_BLACK)
    a.noise(x, y, w, h, 0.02)

    # 6. Poster Frame & Map (R_POSTER_FRAME)
    x, y, w, h = R_POSTER_FRAME
    a.rect(x, y, w, h, (0.20, 0.22, 0.24))
    # TfL Underground Map poster (colourful lines on white)
    px, py, pw, ph = x + 10, y + 8, 100, h - 16
    a.rect(px, py, pw, ph, TFL_WHITE)
    a.rect(px + 10, py + ph // 2, pw - 20, 3, TFL_RED)        # Central line
    a.rect(px + 20, py + 10, 3, ph - 20, (0.1, 0.4, 0.7))    # Piccadilly
    a.rect(px + 40, py + 15, 3, ph - 30, (0.2, 0.6, 0.3))    # District
    a.rect(px + 60, py + 20, 3, ph - 35, (0.5, 0.3, 0.1))    # Bakerloo
    # West End Theatre poster
    wx, wy, ww, wh = x + 120, y + 8, w - 130, h - 16
    a.rect(wx, wy, ww, wh, (0.85, 0.75, 0.20))
    a.text(wx + 10, wy + wh - 18, "WEST END", (0.1, 0.1, 0.1), scale=1)
    a.noise(x, y, w, h, 0.02)

    # 7. Bronze Globe Lantern (R_BRONZE_LAMP)
    x, y, w, h = R_BRONZE_LAMP
    a.rect(x, y, w, h, STONE_PORTLAND)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 32, (0.98, 0.96, 0.85))  # Glowing opal sphere
    a.disc(cx, cy, 20, (1.0, 1.0, 0.95))
    a.rect(cx - 4, cy - 40, 8, 16, BRONZE_ACCENT)  # Bronze bracket
    a.noise(x, y, w, h, 0.015)

    # 8. Pavement Plinth (R_CONCRETE_PAVE)
    x, y, w, h = R_CONCRETE_PAVE
    a.rect(x, y, w, h, (0.68, 0.68, 0.70))
    for dy in range(y, y + h, 24):
        a.rect(x, dy, w, 2, (0.50, 0.50, 0.52))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_tube_entrance_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_COPING, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_COPING, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_tube_entrance_atlas()
    mat = material_for(img, "mat_tube_entrance")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London Underground Station Surface Entrance (6.0m x 4.5m Footprint, Height: 4.2m)
    # - Pavement Plinth & Staircase Well (Z: 0.0 to 0.15m)
    # - Descending Steps into Subterranean concourse
    # - Oxblood Ceramic Tile Canopy Portal & Side Walls (Z: 0.15m to 3.2m)
    # - Giant Iconic Illuminated TfL Roundel Signboard (Z: 3.2m to 4.2m)
    # - Wrought-Iron Safety Railings & Bronze Central Handrail
    # - Twin Heritage Bronze Globe Lanterns
    # =========================================================================

    # 1. Pavement Concrete Base Surround (6.4m x 4.8m, Z = 0.00 to 0.15m)
    register_box("PavementPlinth", 6.40, 4.80, 0.15, (0.0, 0.0, 0.0),
                 front=R_CONCRETE_PAVE, sides=R_CONCRETE_PAVE, top=R_CONCRETE_PAVE)

    # 2. Descending Subterranean Staircase Void (Width 3.8m, D: 3.2m, in center)
    register_box("StairVoid", 3.80, 3.20, 0.05, (0.0, 0.20, 0.15),
                 front=R_STAIRS_TUNNEL, sides=R_STAIRS_TUNNEL, top=R_STAIRS_TUNNEL)

    # 3. Left Oxblood Tiled Flank Wall (Width 1.0m, D: 4.0m, Z: 0.15m to 2.80m, H: 2.65m)
    register_box("LeftWall", 1.00, 4.00, 2.65, (-2.40, 0.20, 0.15),
                 front=R_OXBLOOD_TILES, sides=R_OXBLOOD_TILES, back=R_OXBLOOD_TILES, top=R_STONE_COPING)

    # 4. Right Oxblood Tiled Flank Wall (Width 1.0m, D: 4.0m, Z: 0.15m to 2.80m, H: 2.65m)
    register_box("RightWall", 1.00, 4.00, 2.65, (2.40, 0.20, 0.15),
                 front=R_OXBLOOD_TILES, sides=R_OXBLOOD_TILES, back=R_OXBLOOD_TILES, top=R_STONE_COPING)

    # 5. Back Tiled Enclosure Wall with Poster Frames (Width 5.8m, D: 0.6m, Z: 0.15m to 2.80m)
    register_box("BackWall", 5.80, 0.60, 2.65, (0.0, 1.90, 0.15),
                 front=R_POSTER_FRAME, sides=R_OXBLOOD_TILES, back=R_OXBLOOD_TILES, top=R_STONE_COPING)

    # 6. Overhead Station Portal Fascia Beam (Width: 5.8m, D: 0.8m, Z: 2.60m to 3.20m, H: 0.60m)
    register_box("FasciaBeam", 5.80, 0.80, 0.60, (0.0, -1.60, 2.60),
                 front=R_STONE_COPING, sides=R_STONE_COPING, back=R_STONE_COPING, top=R_STONE_COPING)

    # 7. Giant Illuminated TfL Roundel Signboard (Width 4.4m, D: 0.25m, H: 1.30m, Z = 3.10m to 4.40m)
    register_box("TflRoundelSign", 4.40, 0.25, 1.30, (0.0, -1.65, 3.10),
                 front=R_TUBE_ROUNDEL, sides=R_STONE_COPING, back=R_TUBE_ROUNDEL, top=R_STONE_COPING)

    # 8. Front Stair Entrance Wrought-Iron Gate Railings (Left & Right of opening)
    register_box("LeftRailing", 0.80, 0.15, 1.10, (-1.50, -1.80, 0.15),
                 front=R_IRON_RAILING, sides=R_STONE_COPING, top=R_IRON_RAILING)
    register_box("RightRailing", 0.80, 0.15, 1.10, (1.50, -1.80, 0.15),
                 front=R_IRON_RAILING, sides=R_STONE_COPING, top=R_IRON_RAILING)

    # 9. Central Bronze Handrail Divider (In center of stair flight)
    register_box("CenterHandrail", 0.12, 2.80, 0.95, (0.0, 0.20, 0.15),
                 front=R_IRON_RAILING, sides=R_IRON_RAILING, top=R_IRON_RAILING)

    # 10. Twin Heritage Bronze Globe Lanterns (Flanking entrance at X = -2.40m, +2.40m, Z = 2.40m)
    register_box("LanternLeft", 0.40, 0.40, 0.60, (-2.40, -1.65, 2.20),
                 front=R_BRONZE_LAMP, sides=R_BRONZE_LAMP, top=R_BRONZE_LAMP)
    register_box("LanternRight", 0.40, 0.40, 0.60, (2.40, -1.65, 2.20),
                 front=R_BRONZE_LAMP, sides=R_BRONZE_LAMP, top=R_BRONZE_LAMP)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Tube_Entrance")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_tube_entrance_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_tube_entrance.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_tube_entrance.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_tube_entrance_preview.png")
        shutil.copy2(OUT_DIR / "prop_tube_entrance_atlas.png", TOOLS_OUT_DIR / "prop_tube_entrance_atlas.png")
    except Exception as e:
        print(f"[prop_tube_entrance] note: {e}")

    print("[prop_tube_entrance] generation complete.")


main()
