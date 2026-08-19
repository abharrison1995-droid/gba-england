"""Big Ben / Elizabeth Tower (Gothic Revival Clock Tower Landmark).

Specs:
- 6.0m x 6.0m footprint, Height: 22.0m to gilded spire finial.
- Gothic Revival Victorian architecture:
  - Base & Shaft: Portland / Caen limestone panelled stonework with Gothic blind tracery.
  - Clock Stage: 4 illuminated clock dials with gold Roman numerals and hands.
  - Belfry: Louvred stone belfry containing Big Ben bell.
  - Spire & Roof: Stepped cast iron / copper pyramid spire with 4 corner pinnacles and gilded finials.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_big_ben.py
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
R_CLOCK_DIAL    = (0,   256, 256, 256)   # Illuminated clock dial with gold Roman numerals & hands
R_GOTHIC_STONE  = (256, 256, 256, 256)   # Limestone ashlar shaft with Gothic blind tracery
R_BELFRY_LOUVRE = (0,   128, 256, 128)   # Louvred belfry windows with gold trefoils
R_SPARKLE_GOLD  = (256, 128, 128, 128)   # Gilded crests, finials & decorative ironwork
R_SPIDER_SPIRE  = (384, 128, 128, 128)   # Dark cast iron / oxidised slate spire panels
R_STONE_TRIM    = (0,   0,   256, 128)   # Dressed stone parapet coping, cornices & base
R_GOTHIC_DOOR   = (256, 0,   128, 128)   # Arched oak base entrance with iron scrollwork
R_FLAG_ROYAL    = (384, 0,   128, 128)   # Royal coat of arms shield plaque

# --- Palette Colors ---
STONE_CAEN      = (0.78, 0.74, 0.65)
STONE_MORTAR    = (0.60, 0.56, 0.48)
GOLD_GILT       = (0.95, 0.82, 0.25)
CLOCK_OPAL      = (0.96, 0.94, 0.88)
CLOCK_BLACK     = (0.12, 0.12, 0.14)
CLOCK_BLUE      = (0.10, 0.22, 0.45)
SPIRE_IRON      = (0.24, 0.26, 0.30)
OAK_DARK        = (0.22, 0.15, 0.10)


def paint_big_ben_atlas():
    a = Atlas(S, seed=2401)

    # 1. Iconic Clock Dial (R_CLOCK_DIAL)
    x, y, w, h = R_CLOCK_DIAL
    a.rect(x, y, w, h, STONE_CAEN)
    # Gilded square clock surround with royal blue inner frame
    a.rect(x + 8, y + 8, w - 16, h - 16, CLOCK_BLUE)
    a.rect(x + 12, y + 12, w - 24, h - 24, GOLD_GILT)
    a.rect(x + 16, y + 16, w - 32, h - 32, CLOCK_BLUE)
    # Opal glass circular dial
    cx, cy, r = x + w // 2, y + h // 2, 96
    a.disc(cx, cy, r, GOLD_GILT)
    a.disc(cx, cy, r - 4, CLOCK_BLACK)
    a.disc(cx, cy, r - 8, CLOCK_OPAL)
    # Outer Roman numeral ring
    a.disc(cx, cy, r - 26, (0.92, 0.90, 0.84))
    a.disc(cx, cy, r - 30, CLOCK_OPAL)
    # 12 Roman numeral tick marks around perimeter
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        tx = int(cx + (r - 18) * math.sin(rad))
        ty = int(cy + (r - 18) * math.cos(rad))
        a.disc(tx, ty, 5, CLOCK_BLACK)
    # Clock hands pointing at 10:10 (Gothic fleur-de-lis hands in gold & black)
    # Hour hand (pointing to 10)
    for step in range(10, 55, 4):
        hx = int(cx - step * 0.86)
        hy = int(cy + step * 0.50)
        a.disc(hx, hy, 4, CLOCK_BLACK)
        a.disc(hx, hy, 2, GOLD_GILT)
    # Minute hand (pointing to 2)
    for step in range(10, 75, 4):
        mx = int(cx + step * 0.86)
        my = int(cy + step * 0.50)
        a.disc(mx, my, 3, CLOCK_BLACK)
        a.disc(mx, my, 1, GOLD_GILT)
    # Center boss
    a.disc(cx, cy, 10, GOLD_GILT)
    a.disc(cx, cy, 4, CLOCK_BLUE)
    a.noise(x, y, w, h, 0.02)

    # 2. Limestone Shaft with Gothic Blind Tracery (R_GOTHIC_STONE)
    x, y, w, h = R_GOTHIC_STONE
    a.bricks(x, y, w, h, brick=STONE_CAEN, mortar=STONE_MORTAR, bw=32, bh=14, jitter=0.06)
    # Vertical Gothic tracery mullions
    for mx in range(x + 16, x + w - 16, 44):
        a.rect(mx, y, 6, h, (0.65, 0.60, 0.52))
        a.rect(mx + 6, y, 2, h, (0.85, 0.80, 0.72))
    # Pointed arch window insets
    for ay in [y + 30, y + 140]:
        for ax in [x + 28, x + 116, x + 204]:
            a.rect(ax, ay, 28, 56, (0.45, 0.42, 0.38))
            a.rect(ax + 4, ay + 4, 20, 48, (0.25, 0.26, 0.28))
    a.noise(x, y, w, h, 0.03)

    # 3. Louvred Belfry Windows (R_BELFRY_LOUVRE)
    x, y, w, h = R_BELFRY_LOUVRE
    a.rect(x, y, w, h, STONE_CAEN)
    # 2 Grand Belfry arched louvres
    for bx in [x + 20, x + 140]:
        a.rect(bx, y + 8, 96, h - 16, (0.15, 0.15, 0.18))
        a.rect(bx + 4, y + 12, 88, h - 24, (0.22, 0.24, 0.26))
        # Stone belfry louvre slats
        for ly in range(y + 16, y + h - 20, 10):
            a.rect(bx + 6, ly, 84, 4, STONE_CAEN)
            a.rect(bx + 6, ly + 4, 84, 2, (0.55, 0.50, 0.42))
        # Gilded tracery crown
        a.rect(bx + 20, y + h - 28, 56, 6, GOLD_GILT)
    a.noise(x, y, w, h, 0.025)

    # 4. Gilded Crests & Finials (R_SPARKLE_GOLD)
    x, y, w, h = R_SPARKLE_GOLD
    a.rect(x, y, w, h, (0.12, 0.18, 0.35))  # Royal blue field
    a.rect(x + 4, y + 4, w - 8, h - 8, GOLD_GILT)
    a.disc(x + w // 2, y + h // 2, 34, GOLD_GILT)
    a.disc(x + w // 2, y + h // 2, 22, (0.85, 0.15, 0.12))  # Royal red crest
    a.disc(x + w // 2, y + h // 2, 10, GOLD_GILT)
    a.noise(x, y, w, h, 0.02)

    # 5. Cast Iron Spire Tiles (R_SPIDER_SPIRE)
    x, y, w, h = R_SPIDER_SPIRE
    a.rect(x, y, w, h, SPIRE_IRON)
    for sy in range(y, y + h, 12):
        a.rect(x, sy, w, 2, (0.15, 0.16, 0.18))
        a.rect(x, sy + 2, w, 1, (0.35, 0.38, 0.42))
    # Gilded spire crest ribbing
    for sx in range(x, x + w, 24):
        a.rect(sx, y, 2, h, GOLD_GILT)
    a.noise(x, y, w, h, 0.035)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CAEN)
    for qy in range(y, y + h, 20):
        a.rect(x, qy, w, 2, (0.55, 0.50, 0.42))
    a.noise(x, y, w, h, 0.03)

    # 7. Gothic Entrance Door (R_GOTHIC_DOOR)
    x, y, w, h = R_GOTHIC_DOOR
    a.rect(x, y, w, h, STONE_CAEN)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, OAK_DARK)
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.08, 0.06, 0.04))
    for hy in [dy + 16, dy + dh - 24]:
        a.rect(dx + 6, hy, dw - 12, 4, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.025)

    # 8. Royal Flag / Crest Shield (R_FLAG_ROYAL)
    x, y, w, h = R_FLAG_ROYAL
    a.rect(x, y, w, h, (0.80, 0.15, 0.12))
    # St George cross & harp
    a.rect(x + w // 2 - 4, y, 8, h, (0.95, 0.95, 0.95))
    a.rect(x, y + h // 2 - 4, w, 8, (0.95, 0.95, 0.95))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_big_ben_atlas", OUT_DIR)


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


def make_pyramid_spire(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (0.0, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 4),       # front slope
        (1, 2, 4),       # right slope
        (2, 3, 4),       # back slope
        (3, 0, 4),       # left slope
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_big_ben_atlas()
    mat = material_for(img, "mat_big_ben")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Big Ben / Elizabeth Tower (6.0m x 6.0m Footprint, Height: 22.0m)
    # - Plinth Base & Entrance Stage (Z: 0.0 to 2.5m)
    # - Main Gothic Tracery Shaft (Z: 2.5m to 12.0m, H: 9.5m)
    # - Clock Face Stage: 4 Big Ben Clock Dials (Z: 12.0m to 15.5m)
    # - Belfry Stage: Louvred Windows with Bells (Z: 15.5m to 18.0m)
    # - 4 Corner Pinnacles & Stepped Iron/Copper Spire with Gilded Finial (Z: 18.0 to 22.0m)
    # =========================================================================

    # 1. Base Plinth & Ground Floor (6.2m x 6.2m, Z = 0.00 to 2.50m)
    register_box("TowerPlinth", 6.20, 6.20, 0.30, (0.0, 0.0, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("TowerBase", 5.80, 5.80, 2.20, (0.0, 0.0, 0.30),
                 front=R_GOTHIC_STONE, sides=R_GOTHIC_STONE, back=R_GOTHIC_STONE)
    register_box("TowerDoor", 1.80, 0.15, 2.00, (0.0, -2.85, 0.30),
                 front=R_GOTHIC_DOOR, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Main Gothic Shaft (5.2m x 5.2m, Z: 2.50m to 12.00m, H: 9.50m)
    register_box("MainShaft", 5.20, 5.20, 9.50, (0.0, 0.0, 2.50),
                 front=R_GOTHIC_STONE, sides=R_GOTHIC_STONE, back=R_GOTHIC_STONE)

    # 3. Lower Clock Balcony Cornice (Z = 12.00m to 12.40m)
    register_box("ClockCorniceLower", 5.60, 5.60, 0.40, (0.0, 0.0, 12.00),
                 front=R_SPARKLE_GOLD, sides=R_SPARKLE_GOLD, top=R_STONE_TRIM)

    # 4. Clock Stage: 4 Illuminated Big Ben Clock Dials (5.4m x 5.4m, Z: 12.40m to 15.60m, H: 3.20m)
    register_box("ClockStage", 5.40, 5.40, 3.20, (0.0, 0.0, 12.40),
                 front=R_CLOCK_DIAL, sides=R_CLOCK_DIAL, back=R_CLOCK_DIAL)

    # 5. Upper Clock Cornice & Gilded Parapet (Z = 15.60m to 16.00m)
    register_box("ClockCorniceUpper", 5.60, 5.60, 0.40, (0.0, 0.0, 15.60),
                 front=R_SPARKLE_GOLD, sides=R_SPARKLE_GOLD, top=R_STONE_TRIM)

    # 6. Louvred Belfry Stage (4.8m x 4.8m, Z: 16.00m to 18.20m, H: 2.20m)
    register_box("BelfryStage", 4.80, 4.80, 2.20, (0.0, 0.0, 16.00),
                 front=R_BELFRY_LOUVRE, sides=R_BELFRY_LOUVRE, back=R_BELFRY_LOUVRE)

    # 7. 4 Corner Pinnacles (Z = 18.20m to 20.00m)
    for px, py in [(-2.20, -2.20), (2.20, -2.20), (2.20, 2.20), (-2.20, 2.20)]:
        register_box(f"Pinnacle_{px}_{py}", 0.60, 0.60, 1.80, (px, py, 18.20),
                     front=R_SPARKLE_GOLD, sides=R_SPARKLE_GOLD, top=R_SPARKLE_GOLD)

    # 8. Pyramidal Cast Iron & Copper Spire (W: 4.6m, D: 4.6m, H: 3.80m, Z = 18.20m to 22.00m)
    spire = make_pyramid_spire("BigBenSpire", 4.60, 4.60, 3.80, at=(0.0, 0.0, 18.20))
    spire.data.materials.append(mat)
    kit.map_faces_to_region(spire, R_SPIDER_SPIRE, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(spire, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(spire)

    # 9. Gilded Finial Spire Point (Z = 22.00m to 22.80m)
    register_box("GiltFinial", 0.20, 0.20, 0.80, (0.0, 0.0, 22.00),
                 front=R_SPARKLE_GOLD, sides=R_SPARKLE_GOLD, top=R_SPARKLE_GOLD)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_Big_Ben")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_big_ben_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_big_ben.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_big_ben.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_big_ben_preview.png")
        shutil.copy2(OUT_DIR / "landmark_big_ben_atlas.png", TOOLS_OUT_DIR / "landmark_big_ben_atlas.png")
    except Exception as e:
        print(f"[landmark_big_ben] note: {e}")

    print("[landmark_big_ben] generation complete.")


main()
