"""Fly-Tipped Street Mattress & Rubbish Heap (Urban Street Rubbish Prop).

Specs:
- 2.8m x 2.2m footprint, Height: 1.6m.
- Classic London urban fly-tipping alleyway heap:
  - Stained, grimy double mattress slumped against a grimy London brick wall.
  - Torn fabric ticking exposing yellow foam core and rusted steel coil springs.
  - 4 piled glossy black heavy-duty bin bags / rubbish sacks.
  - Flattened soggy cardboard delivery boxes with brown packing tape.
  - Discarded broken wooden chair & pavement base with oil stains.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_street_mattress.py
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
R_MATTRESS_STAIN= (0,   256, 256, 256)   # Stained striped mattress ticking, coffee stains & foam tear
R_BLACK_BIN_BAG = (256, 256, 256, 256)   # Glossy black polyethylene bin bag with reflective creases
R_CARDBOARD_BOX = (0,   128, 256, 128)   # Soggy brown corrugated cardboard box & packing tape
R_BRICK_ALLEY   = (256, 128, 128, 128)   # Grimy soot-stained London brick wall with damp patches
R_EXPOSED_FOAM  = (384, 128, 128, 128)   # Exposed yellow foam stuffing & rusted coil springs
R_PAVE_DAMP     = (0,   0,   256, 128)   # Damp cracked pavement with oil puddles & cig butts
R_WOOD_PALLET   = (256, 0,   128, 128)   # Broken weathered timber pallet planks
R_RUBBISH_DEBRIS= (384, 0,   128, 128)   # Crushed food packaging, polystyrene & cans

# --- Palette Colors ---
MATTRESS_CREAM  = (0.84, 0.80, 0.72)
STAIN_BROWN     = (0.45, 0.35, 0.22)
FOAM_YELLOW     = (0.90, 0.78, 0.28)
BIN_BAG_BLACK   = (0.08, 0.08, 0.10)
BIN_BAG_SHINE   = (0.28, 0.30, 0.35)
CARDBOARD_BROWN = (0.58, 0.44, 0.28)
TAPE_BROWN      = (0.75, 0.55, 0.32)
BRICK_GRIMY     = (0.50, 0.32, 0.25)
PAVE_DAMP_GREY  = (0.42, 0.44, 0.46)


def paint_mattress_atlas():
    a = Atlas(S, seed=4301)

    # 1. Stained Slumped Mattress (R_MATTRESS_STAIN)
    x, y, w, h = R_MATTRESS_STAIN
    a.rect(x, y, w, h, MATTRESS_CREAM)
    # Damask quilted stripes
    for sy in range(y, y + h, 20):
        a.rect(x, sy, w, 3, (0.76, 0.72, 0.65))
    # Big damp water & coffee stains
    for cx, cy, rad in [(x + 80, y + 140, 55), (x + 180, y + 70, 45), (x + 140, y + 190, 35)]:
        a.disc(cx, cy, rad, STAIN_BROWN)
        a.disc(cx, cy, rad - 12, (0.65, 0.52, 0.34))
    # Big corner tear exposing yellow foam
    a.rect(x + w - 70, y + h - 70, 60, 60, FOAM_YELLOW)
    for ry in range(y + h - 60, y + h - 20, 14):
        a.disc(x + w - 40, ry, 8, (0.3, 0.2, 0.1))  # rusted spring coil
    a.noise(x, y, w, h, 0.04)

    # 2. Glossy Black Bin Bags (R_BLACK_BIN_BAG)
    x, y, w, h = R_BLACK_BIN_BAG
    a.rect(x, y, w, h, BIN_BAG_BLACK)
    # Glossy crinkle plastic highlights
    for sy in range(y + 16, y + h - 16, 28):
        for sx in range(x + 16, x + w - 16, 36):
            a.disc(sx, sy, 22, (0.16, 0.18, 0.22))
            a.disc(sx + 4, sy + 4, 8, BIN_BAG_SHINE)
    # White drawstring knot at top
    a.disc(x + w // 2, y + h - 20, 14, (0.90, 0.90, 0.92))
    a.noise(x, y, w, h, 0.02)

    # 3. Cardboard Boxes (R_CARDBOARD_BOX)
    x, y, w, h = R_CARDBOARD_BOX
    a.rect(x, y, w, h, CARDBOARD_BROWN)
    # Corrugated packing tape crosses
    a.rect(x, y + h // 2 - 8, w, 16, TAPE_BROWN)
    a.rect(x + w // 2 - 8, y, 16, h, TAPE_BROWN)
    # Barcode & fragile stencil
    a.rect(x + 20, y + 16, 40, 24, (0.9, 0.9, 0.9))
    a.rect(x + 24, y + 18, 32, 20, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.035)

    # 4. Grimy Brick Alley Wall (R_BRICK_ALLEY)
    x, y, w, h = R_BRICK_ALLEY
    a.bricks(x, y, w, h, brick=BRICK_GRIMY, mortar=(0.35, 0.32, 0.30), bw=28, bh=12, jitter=0.08)
    a.noise(x, y, w, h, 0.04)

    # 5. Exposed Foam & Springs (R_EXPOSED_FOAM)
    x, y, w, h = R_EXPOSED_FOAM
    a.rect(x, y, w, h, FOAM_YELLOW)
    for fy in range(y + 12, y + h - 12, 24):
        a.disc(x + w // 2, fy, 14, (0.35, 0.25, 0.15))
        a.disc(x + w // 2, fy, 8, FOAM_YELLOW)
    a.noise(x, y, w, h, 0.04)

    # 6. Damp Pavement (R_PAVE_DAMP)
    x, y, w, h = R_PAVE_DAMP
    a.rect(x, y, w, h, PAVE_DAMP_GREY)
    a.disc(x + 80, y + 50, 40, (0.28, 0.30, 0.32))  # oil puddle
    # Discarded cigarette butts
    for bx in [x + 40, x + 120, x + 190]:
        a.rect(bx, y + 30, 6, 2, (0.9, 0.9, 0.9))
        a.rect(bx + 6, y + 30, 2, 2, (0.8, 0.5, 0.2))
    a.noise(x, y, w, h, 0.04)

    # 7. Broken Wood Pallet (R_WOOD_PALLET)
    x, y, w, h = R_WOOD_PALLET
    a.rect(x, y, w, h, (0.45, 0.35, 0.22))
    for py in range(y, y + h, 16):
        a.rect(x, py, w, 2, (0.2, 0.15, 0.1))
    a.noise(x, y, w, h, 0.035)

    # 8. Rubbish Debris (R_RUBBISH_DEBRIS)
    x, y, w, h = R_RUBBISH_DEBRIS
    a.rect(x, y, w, h, (0.50, 0.48, 0.45))
    a.rect(x + 16, y + 16, 24, 16, (0.85, 0.15, 0.15))  # red takeaway box
    a.disc(x + 80, y + 40, 10, (0.9, 0.9, 0.9))         # coffee cup lid
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_street_mattress_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_PAVE_DAMP, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_PAVE_DAMP, S, only=side("bottom"))


def make_slumped_mattress(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = w / 2.0
    # Angled mattress box leaning back against wall
    verts = [
        # Bottom front
        (-hw, -0.60, 0.0), (hw, -0.60, 0.0),
        # Bottom back
        (hw, -0.35, 0.0), (-hw, -0.35, 0.0),
        # Top front (leaning back at Y = +0.20m, Z = h)
        (-hw, 0.20, h), (hw, 0.20, h),
        # Top back (leaning back at Y = +0.45m, Z = h)
        (hw, 0.45, h), (-hw, 0.45, h),
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front face (slumped)
        (1, 2, 6, 5),    # right side
        (2, 3, 7, 6),    # back (against wall)
        (3, 0, 4, 7),    # left side
        (4, 5, 6, 7),    # top rim
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_mattress_atlas()
    mat = material_for(img, "mat_street_mattress")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Fly-Tipped Street Mattress & Rubbish Heap (2.8m x 2.2m Footprint, Height: 1.6m)
    # - Damp Alleyway Pavement Slab (Z: 0.0 to 0.08m)
    # - Back Brick Wall (Width 2.8m, D: 0.35m, Height 1.6m at Y = 0.85m)
    # - Slumped Stained Double Mattress leaning against wall (Width 1.6m, H: 1.35m)
    # - 4 Heavy Piled Black Bin Bags (Stuffed plastic sacks)
    # - Soggy Flattened Cardboard Delivery Boxes & Rubbish Debris
    # =========================================================================

    # 1. Pavement Concrete Base (3.0m x 2.4m, Z = 0.00 to 0.08m)
    register_box("AlleyPavement", 3.00, 2.40, 0.08, (0.0, 0.0, 0.0),
                 front=R_PAVE_DAMP, sides=R_PAVE_DAMP, top=R_PAVE_DAMP)

    # 2. Back Alley Brick Wall (2.80m x 0.35m, Z: 0.08m to 1.65m, H: 1.57m at Y = 0.95m)
    register_box("AlleyWall", 2.80, 0.35, 1.57, (0.0, 0.95, 0.08),
                 front=R_BRICK_ALLEY, sides=R_BRICK_ALLEY, back=R_BRICK_ALLEY, top=R_PAVE_DAMP)

    # 3. Slumped Stained Double Mattress (Width: 1.50m, H: 1.35m, Z: 0.08m to 1.43m, leaning at X = -0.40m)
    mattress = make_slumped_mattress("MattressSlumped", 1.50, 0.80, 1.35, at=(-0.40, 0.35, 0.08))
    mattress.data.materials.append(mat)
    kit.map_faces_to_region(mattress, R_MATTRESS_STAIN, S, only=lambda f: f.normal.y < -0.1)
    kit.map_faces_to_region(mattress, R_EXPOSED_FOAM, S, only=lambda f: abs(f.normal.x) > 0.5)
    kit.map_faces_to_region(mattress, R_MATTRESS_STAIN, S, only=lambda f: f.normal.y >= -0.1)
    parts.append(mattress)

    # 4. 4 Black Polyethylene Rubbish Sacks / Bin Bags
    # Bag 1 (Front Right: X = 0.70m, Y = -0.30m)
    register_box("BinBag1", 0.65, 0.65, 0.55, (0.70, -0.30, 0.08),
                 front=R_BLACK_BIN_BAG, sides=R_BLACK_BIN_BAG, top=R_BLACK_BIN_BAG)
    # Bag 2 (Behind Bag 1: X = 0.75m, Y = 0.35m)
    register_box("BinBag2", 0.60, 0.60, 0.60, (0.75, 0.35, 0.08),
                 front=R_BLACK_BIN_BAG, sides=R_BLACK_BIN_BAG, top=R_BLACK_BIN_BAG)
    # Bag 3 (Stacked on top: X = 0.65m, Y = 0.0m, Z = 0.60m)
    register_box("BinBag3", 0.55, 0.55, 0.50, (0.65, 0.0, 0.60),
                 front=R_BLACK_BIN_BAG, sides=R_BLACK_BIN_BAG, top=R_BLACK_BIN_BAG)
    # Bag 4 (Torn bag near mattress: X = -0.90m, Y = -0.40m)
    register_box("BinBag4", 0.55, 0.55, 0.45, (-0.90, -0.40, 0.08),
                 front=R_BLACK_BIN_BAG, sides=R_BLACK_BIN_BAG, top=R_RUBBISH_DEBRIS)

    # 5. Soggy Flattened Cardboard Boxes (In front of mattress: X = 0.0m, Y = -0.65m)
    register_box("CardboardBox1", 0.80, 0.65, 0.14, (0.0, -0.65, 0.08),
                 front=R_CARDBOARD_BOX, sides=R_CARDBOARD_BOX, top=R_CARDBOARD_BOX)
    register_box("CardboardBox2", 0.60, 0.50, 0.22, (-0.20, -0.55, 0.20),
                 front=R_CARDBOARD_BOX, sides=R_CARDBOARD_BOX, top=R_CARDBOARD_BOX)

    # 6. Broken Wooden Pallet & Takeaway Debris
    register_box("BrokenPallet", 0.85, 0.55, 0.08, (0.75, -0.80, 0.08),
                 front=R_WOOD_PALLET, sides=R_WOOD_PALLET, top=R_WOOD_PALLET)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Street_Mattress")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_street_mattress_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_street_mattress.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_street_mattress.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_street_mattress_preview.png")
        shutil.copy2(OUT_DIR / "prop_street_mattress_atlas.png", TOOLS_OUT_DIR / "prop_street_mattress_atlas.png")
    except Exception as e:
        print(f"[prop_street_mattress] note: {e}")

    print("[prop_street_mattress] generation complete.")


main()
