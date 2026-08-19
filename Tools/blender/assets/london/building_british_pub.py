"""Traditional British Corner Pub (10.0m x 8.0m, "The Red Lion").

Specs:
- 10.0m x 8.0m footprint, Height: 8.5m to chimney pots.
- Classic London Victorian corner tavern:
  - Ground floor: Dark glazed green/black ceramic tile facade with gold signwriting: "THE RED LION - TRADITIONAL ALES & FOOD".
  - Polished mahogany pub entrance doors with etched brass plates and frosted glass.
  - Large curved bay pub windows with leaded stained-glass heraldic lions.
  - 1st & 2nd floors: Traditional half-timbered dark oak beams on warm cream stucco (or warm London stock brick with timber accents).
  - Projecting double-sided hanging iron pub sign board with painted Red Lion crest.
  - Slate pitched roof with twin brick chimneys and terracotta chimney pots.
  - Front outdoor beer garden bench and floral hanging baskets.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_british_pub.py
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
R_PUB_FASCIA   = (0,   384, 512, 128)   # "THE RED LION" gold on dark green glazed fascia
R_PUB_TILES    = (0,   128, 256, 256)   # Dark Victorian glazed green ceramic tiles & windows
R_PUB_DOORS    = (256, 128, 128, 256)   # Mahogany paneled pub doors with brass kicks & etched glass
R_TIMBER_WALL  = (0,   0,   256, 128)   # Half-timbered dark oak beams on cream stucco
R_ROOF_SLATE   = (256, 0,   128, 128)   # Dark Welsh slate tiles
R_STONE_TRIM   = (384, 256, 128, 128)   # Polished stone sills, coping & pavement
R_HANGING_SIGN = (384, 128, 128, 128)   # Double-sided hanging iron pub sign with Red Lion crest
R_CHIMNEY_BRICK= (384, 0,   128, 128)   # Red brick chimney with terracotta pots

# --- Palette Colors ---
GREEN_GLAZE    = (0.10, 0.24, 0.16)
GREEN_DARK     = (0.05, 0.14, 0.09)
GOLD_TEXT      = (0.94, 0.80, 0.22)
MAHOGANY_WOOD  = (0.28, 0.14, 0.08)
BRASS_TRIM     = (0.86, 0.72, 0.24)
CREAM_STUCCO   = (0.84, 0.80, 0.72)
OAK_TIMBER     = (0.18, 0.12, 0.08)
SLATE_GREY     = (0.26, 0.28, 0.32)
RED_LION_COL   = (0.82, 0.16, 0.12)
STONE_CREAM    = (0.75, 0.72, 0.65)
GLASS_LEADED   = (0.22, 0.30, 0.32)


def paint_pub_atlas():
    a = Atlas(S, seed=1901)

    # 1. Iconic "THE RED LION" Fascia Sign (R_PUB_FASCIA)
    x, y, w, h = R_PUB_FASCIA
    a.rect(x, y, w, h, GREEN_GLAZE)
    # Gold & Dark Wood Trim Frame
    a.rect(x, y, w, 8, MAHOGANY_WOOD)
    a.rect(x, y + h - 8, w, 8, MAHOGANY_WOOD)
    a.rect(x + 4, y + 4, w - 8, 3, BRASS_TRIM)
    a.rect(x + 4, y + h - 7, w - 8, 3, BRASS_TRIM)

    # Gold Red Lion crest on left & right
    for cx in [x + 28, x + w - 28]:
        a.disc(cx, y + h // 2, 16, BRASS_TRIM)
        a.disc(cx, y + h // 2, 13, RED_LION_COL)
        a.disc(cx, y + h // 2, 6, GOLD_TEXT)

    # Main Gold Lettering: "THE RED LION" (scale=6)
    s1 = "THE RED LION"
    tw = a.text_width(s1, scale=6)
    tx = x + (w - tw) // 2
    ty = y + h - 18
    # Deep shadow + gold text
    a.text(tx + 3, ty - 3, s1, (0.02, 0.08, 0.04), scale=6)
    a.text(tx, ty, s1, GOLD_TEXT, scale=6)

    # Subtitle: "FINE ALES * WINES * TRADITIONAL FOOD"
    s2 = "FINE ALES - WINES - TRADITIONAL FOOD"
    sw = a.text_width(s2, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx + 1, y + 23, s2, (0.02, 0.08, 0.04), scale=2)
    a.text(sx, y + 24, s2, BRASS_TRIM, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 2. Dark Glazed Green Ceramic Tiles & Leaded Windows (R_PUB_TILES)
    x, y, w, h = R_PUB_TILES
    a.rect(x, y, w, h, GREEN_GLAZE)
    # Glazed tile grid lines
    for ty in range(y, y + h, 16):
        a.rect(x, ty, w, 2, GREEN_DARK)
    for tx in range(x, x + w, 32):
        a.rect(tx, y, 2, h, GREEN_DARK)

    # Large bay window glazed pane
    wx, wy, ww, wh = x + 16, y + 24, w - 32, h - 48
    a.rect(wx, wy, ww, wh, MAHOGANY_WOOD)
    a.rect(wx + 6, wy + 6, ww - 12, wh - 12, GLASS_LEADED)
    # Leaded diamond grid
    for dy in range(wy + 10, wy + wh - 10, 16):
        a.rect(wx + 6, dy, ww - 12, 2, (0.15, 0.15, 0.18))
    # Red Lion stained glass emblem in center
    a.disc(wx + ww // 2, wy + wh // 2, 20, BRASS_TRIM)
    a.disc(wx + ww // 2, wy + wh // 2, 16, RED_LION_COL)
    a.disc(wx + ww // 2, wy + wh // 2, 8, GOLD_TEXT)
    a.noise(x, y, w, h, 0.025)

    # 3. Mahogany Pub Doors (R_PUB_DOORS)
    x, y, w, h = R_PUB_DOORS
    a.rect(x, y, w, h, MAHOGANY_WOOD)
    # Door leaves
    dx, dy, dw, dh = x + 6, y + 6, w - 12, h - 12
    a.rect(dx, dy, dw, dh, (0.20, 0.10, 0.05))
    a.rect(dx + dw // 2 - 1, dy, 2, dh, (0.10, 0.05, 0.02))  # split
    # Upper etched glass panels
    a.rect(dx + 6, dy + 110, dw // 2 - 10, 100, (0.70, 0.72, 0.70))
    a.rect(dx + dw // 2 + 4, dy + 110, dw // 2 - 10, 100, (0.70, 0.72, 0.70))
    # Brass kickplates & push plates
    a.rect(dx + 4, dy + 6, dw - 8, 30, BRASS_TRIM)
    a.rect(dx + 8, dy + 90, 14, 24, BRASS_TRIM)
    a.rect(dx + dw // 2 + 8, dy + 90, 14, 24, BRASS_TRIM)
    a.noise(x, y, w, h, 0.02)

    # 4. Half-Timbered Stucco & Oak Beams (R_TIMBER_WALL)
    x, y, w, h = R_TIMBER_WALL
    a.rect(x, y, w, h, CREAM_STUCCO)
    # Horizontal oak beam bands
    a.rect(x, y, w, 12, OAK_TIMBER)
    a.rect(x, y + h - 12, w, 12, OAK_TIMBER)
    a.rect(x, y + h // 2 - 6, w, 12, OAK_TIMBER)
    # Vertical and diagonal oak timber struts
    for vx in range(x, x + w, 64):
        a.rect(vx, y, 12, h, OAK_TIMBER)
    # Small leaded sash windows
    for sx in [x + 20, x + 84, x + 148, x + 212]:
        a.rect(sx, y + 16, 36, 44, OAK_TIMBER)
        a.rect(sx + 4, y + 20, 28, 36, GLASS_LEADED)
        a.rect(sx + 16, y + 20, 4, 36, OAK_TIMBER)
        a.rect(sx + 4, y + 36, 28, 4, OAK_TIMBER)
    a.noise(x, y, w, h, 0.035)

    # 5. Roof Welsh Slate (R_ROOF_SLATE)
    x, y, w, h = R_ROOF_SLATE
    a.rect(x, y, w, h, SLATE_GREY)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.18, 0.20, 0.22))
    a.noise(x, y, w, h, 0.04)

    # 6. Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    for qy in range(y, y + h, 24):
        a.rect(x, qy, w, 2, (0.55, 0.52, 0.46))
    a.noise(x, y, w, h, 0.03)

    # 7. Hanging Iron Pub Sign Board (R_HANGING_SIGN)
    x, y, w, h = R_HANGING_SIGN
    a.rect(x, y, w, h, (0.12, 0.12, 0.14))  # Wrought iron frame
    a.rect(x + 10, y + 10, w - 20, h - 20, CREAM_STUCCO)
    a.rect(x + 14, y + 14, w - 28, h - 28, GREEN_GLAZE)
    # Red Lion silhouette
    a.disc(x + w // 2, y + h // 2 + 8, 28, RED_LION_COL)
    a.disc(x + w // 2, y + h // 2 + 8, 16, GOLD_TEXT)
    # Text "RED LION"
    s_sign = "RED LION"
    st_w = a.text_width(s_sign, scale=1)
    a.text(x + (w - st_w) // 2, y + 24, s_sign, GOLD_TEXT, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 8. Chimney Brick (R_CHIMNEY_BRICK)
    x, y, w, h = R_CHIMNEY_BRICK
    a.bricks(x, y, w, h, brick=(0.58, 0.24, 0.18), mortar=(0.65, 0.60, 0.55), bw=20, bh=10)
    a.rect(x, y + h - 20, w, 20, (0.75, 0.38, 0.22))  # Terracotta pot rim
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_british_pub_atlas", OUT_DIR)


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


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (-hw, 0.0, h), (hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front slope
        (2, 3, 4, 5),    # back slope
        (0, 4, 3),       # left gable
        (1, 2, 5),       # right gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_pub_atlas()
    mat = material_for(img, "mat_british_pub")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Traditional British Pub ("The Red Lion")
    # - 10.0m x 8.0m footprint, Height: 8.5m
    # - Ground Floor: Glazed green tile pub facade, bay windows, mahogany doors
    # - Fascia Sign: "THE RED LION" with gold lettering
    # - 1st & 2nd Floors: Half-timbered oak & stucco with leaded sash windows
    # - Pitched Slate Roof + Twin Chimneys with Terracotta Pots
    # - Projecting Hanging Wrought-Iron Pub Sign & Beer Garden Bench
    # =========================================================================

    # 1. Pavement & Beer Garden Apron (10.0m x 8.5m, Z = 0.00 to 0.12m)
    register_box("PubPlinth", 10.0, 8.50, 0.12, (0.0, -0.25, 0.0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 2. Ground Floor Glazed Pub Base (10.0m x 7.5m, Z: 0.12 to 4.55m, H: 4.43m)
    register_box("PubGroundFloor", 10.0, 7.50, 4.43, (0.0, 0.25, 0.12),
                 front=R_PUB_TILES, sides=R_TIMBER_WALL, back=R_TIMBER_WALL)

    # 3. Prominent "THE RED LION" Gold Glazed Fascia Sign (Z = 3.35m to 4.55m, H: 1.20m)
    register_box("PubFasciaSign", 9.80, 0.35, 1.20, (0.0, -3.65, 3.35),
                 front=R_PUB_FASCIA, sides=R_PUB_FASCIA, top=R_STONE_TRIM)

    # 4. Central Mahogany Entrance Doors (Z = 0.12 to 3.30m, H: 3.18m)
    register_box("PubDoors", 2.40, 0.18, 3.18, (0.0, -3.58, 0.12),
                 front=R_PUB_DOORS, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Flanking Curved / Box Bay Pub Windows (Left X = -3.20m, Right X = +3.20m)
    register_box("BayWindowLeft", 3.20, 0.28, 2.90, (-3.20, -3.60, 0.25),
                 front=R_PUB_TILES, sides=R_PUB_TILES, top=R_STONE_TRIM)
    register_box("BayWindowRight", 3.20, 0.28, 2.90, (3.20, -3.60, 0.25),
                 front=R_PUB_TILES, sides=R_PUB_TILES, top=R_STONE_TRIM)

    # 6. 1st & 2nd Storey Half-Timbered Living Quarters (10.0m x 7.5m, Z: 4.55m to 7.80m, H: 3.25m)
    register_box("PubUpperFloors", 10.0, 7.50, 3.25, (0.0, 0.25, 4.55),
                 front=R_TIMBER_WALL, sides=R_TIMBER_WALL, back=R_TIMBER_WALL)

    # 7. Pitched Slate Roof (Ridge along X, W: 10.40m, D: 7.90m, H: 2.20m at Z = 7.80m)
    roof = make_pitched_roof("PubRoof", 10.40, 7.90, 2.20, at=(0.0, 0.25, 7.80))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_SLATE, S, only=lambda f: f.normal.z > 0.1)
    kit.map_faces_to_region(roof, R_TIMBER_WALL, S, only=lambda f: abs(f.normal.x) > 0.6)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    # 8. Twin Brick Chimneys (Left X = -4.20m, Right X = +4.20m, Z = 7.80m to 10.40m)
    for cx in [-4.20, 4.20]:
        register_box(f"Chimney_{cx}", 0.90, 1.20, 2.40, (cx, 0.25, 7.80),
                     front=R_CHIMNEY_BRICK, sides=R_CHIMNEY_BRICK, top=R_STONE_TRIM)

    # 9. Projecting Wrought Iron Hanging Pub Sign (Corner: X = -4.90m, Y = -3.20m, Z = 4.20m)
    register_box("SignBracket", 0.08, 0.08, 2.00, (-4.90, -3.20, 3.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("HangingPubSign", 0.10, 1.10, 1.10, (-4.90, -3.20, 4.40),
                 front=R_STONE_TRIM, sides=R_HANGING_SIGN, top=R_STONE_TRIM)

    # 10. Outdoor Beer Garden Wooden Picnic Table & Benches (X = 3.20m, Y = -4.10m)
    register_box("BeerTable", 1.80, 0.80, 0.75, (3.20, -4.10, 0.12),
                 front=R_TIMBER_WALL, sides=R_TIMBER_WALL, top=R_TIMBER_WALL)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_British_Pub")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_british_pub_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_british_pub.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_british_pub.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_british_pub_preview.png")
        shutil.copy2(OUT_DIR / "building_british_pub_atlas.png", TOOLS_OUT_DIR / "building_british_pub_atlas.png")
    except Exception as e:
        print(f"[building_british_pub] note: {e}")

    print("[building_british_pub] generation complete.")


main()
