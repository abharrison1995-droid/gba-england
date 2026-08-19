"""Council 240L Wheelie Bins 3-Pack (Street Rubbish Prop).

Specs:
- 2.4m x 1.2m footprint, Height: 1.15m.
- Set of 3 standard British Council 240L domestic wheelie bins:
  - Bin 1 (Black): General household waste with white house number "42" stencil.
  - Bin 2 (Green): Organic garden & food waste with recycling logo.
  - Bin 3 (Blue): Paper, card & glass dry recycling with council crest.
  - Hinged moulded polyethylene drop lids, rear push handles, black rubber wheels.
  - Pavement slab base with discarded drinks can & newspaper litter.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_wheelie_bins.py
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
R_BIN_BLACK     = (0,   256, 256, 256)   # Black general waste bin with house "42" stencil & grime
R_BIN_GREEN     = (256, 256, 256, 256)   # Green organic recycling bin with Mobius loop logo
R_BIN_BLUE      = (0,   128, 256, 128)   # Blue paper/cardboard bin with Council Crest
R_BIN_LIDS      = (256, 128, 128, 128)   # Moulded plastic lid top with grip handles
R_RUBBER_WHEEL  = (384, 128, 128, 128)   # Solid black rubber tyres with central steel hubcap
R_PAVE_LITTER   = (0,   0,   256, 128)   # Pavement concrete with discarded soda can & newspaper
R_COUNCIL_CREST = (256, 0,   128, 128)   # Hot-stamped white council emblem & barcode
R_PLASTIC_TRIM  = (384, 0,   128, 128)   # Polyethylene rim & hinge brackets

# --- Palette Colors ---
PLASTIC_BLACK   = (0.15, 0.16, 0.18)
PLASTIC_GREEN   = (0.14, 0.42, 0.18)
PLASTIC_BLUE    = (0.10, 0.32, 0.65)
LID_BLACK       = (0.12, 0.13, 0.14)
WHEEL_RUBBER    = (0.08, 0.08, 0.09)
WHITE_STENCIL   = (0.92, 0.92, 0.94)
PAVE_GREY       = (0.64, 0.65, 0.66)
CAN_COLA        = (0.85, 0.12, 0.12)


def paint_wheelie_atlas():
    a = Atlas(S, seed=4201)

    # 1. Black Bin with "42" Stencil (R_BIN_BLACK)
    x, y, w, h = R_BIN_BLACK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    a.shade(x, y, w, h, top=0.08, bottom=-0.08)
    # Stencilled White House Number "42"
    s1 = "42"
    tw1 = a.text_width(s1, scale=5)
    a.text(x + (w - tw1) // 2, y + h // 2 + 10, s1, WHITE_STENCIL, scale=5)
    # Council Stencil: "GENERAL WASTE ONLY"
    s2 = "GENERAL WASTE ONLY"
    tw2 = a.text_width(s2, scale=1)
    a.text(x + (w - tw2) // 2, y + 40, s2, (0.6, 0.6, 0.6), scale=1)
    a.noise(x, y, w, h, 0.03)

    # 2. Green Bin with Recycling Logo (R_BIN_GREEN)
    x, y, w, h = R_BIN_GREEN
    a.rect(x, y, w, h, PLASTIC_GREEN)
    a.shade(x, y, w, h, top=0.10, bottom=-0.06)
    # Recycling Mobius loop triangle symbol in white
    cx, cy = x + w // 2, y + h // 2 + 20
    a.disc(cx, cy, 36, WHITE_STENCIL)
    a.disc(cx, cy, 26, PLASTIC_GREEN)
    a.disc(cx, cy, 10, WHITE_STENCIL)
    # Text: "GARDEN & FOOD WASTE"
    s_grn = "GARDEN & FOOD"
    gw = a.text_width(s_grn, scale=1)
    a.text(x + (w - gw) // 2, y + 40, s_grn, WHITE_STENCIL, scale=1)
    a.noise(x, y, w, h, 0.025)

    # 3. Blue Bin with Council Crest (R_BIN_BLUE)
    x, y, w, h = R_BIN_BLUE
    a.rect(x, y, w, h, PLASTIC_BLUE)
    a.shade(x, y, w, h, top=0.10, bottom=-0.06)
    # Council crest
    cx, cy = x + w // 2, y + h // 2 + 10
    a.disc(cx, cy, 24, WHITE_STENCIL)
    a.disc(cx, cy, 16, PLASTIC_BLUE)
    s_blu = "PAPER & CARD"
    bw = a.text_width(s_blu, scale=1)
    a.text(x + (w - bw) // 2, y + 20, s_blu, WHITE_STENCIL, scale=1)
    a.noise(x, y, w, h, 0.025)

    # 4. Moulded Bin Lids (R_BIN_LIDS)
    x, y, w, h = R_BIN_LIDS
    a.rect(x, y, w, h, LID_BLACK)
    a.rect(x + 10, y + 10, w - 20, h - 20, (0.18, 0.20, 0.22))
    # Handle recess
    a.rect(x + w // 2 - 24, y + 16, 48, 12, (0.08, 0.08, 0.09))
    a.noise(x, y, w, h, 0.02)

    # 5. Rubber Wheel with Hubcap (R_RUBBER_WHEEL)
    x, y, w, h = R_RUBBER_WHEEL
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 46, WHEEL_RUBBER)
    a.disc(cx, cy, 28, (0.40, 0.42, 0.45))  # Steel wheel rim
    a.disc(cx, cy, 14, WHEEL_RUBBER)
    a.disc(cx, cy, 6, (0.7, 0.7, 0.7))      # Central axle pin
    a.noise(x, y, w, h, 0.02)

    # 6. Pavement with Litter (R_PAVE_LITTER)
    x, y, w, h = R_PAVE_LITTER
    a.rect(x, y, w, h, PAVE_GREY)
    # Crushed red cola can
    a.rect(x + 30, y + 24, 20, 10, CAN_COLA)
    a.disc(x + 32, y + 29, 3, (0.8, 0.8, 0.8))
    # Discarded crumpled newsprint
    a.rect(x + 120, y + 36, 32, 22, (0.88, 0.88, 0.84))
    a.rect(x + 124, y + 42, 24, 2, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.03)

    # 7. Council Crest (R_COUNCIL_CREST)
    x, y, w, h = R_COUNCIL_CREST
    a.rect(x, y, w, h, (0.12, 0.14, 0.16))
    a.disc(x + w // 2, y + h // 2, 30, WHITE_STENCIL)
    a.disc(x + w // 2, y + h // 2, 20, (0.12, 0.14, 0.16))
    a.noise(x, y, w, h, 0.02)

    # 8. Plastic Trim (R_PLASTIC_TRIM)
    x, y, w, h = R_PLASTIC_TRIM
    a.rect(x, y, w, h, (0.18, 0.20, 0.22))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_wheelie_bins_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_BIN_LIDS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_RUBBER_WHEEL, S, only=side("bottom"))


def make_wheelie_bin(name, x_pos, y_pos, z_rot_deg, color_front, mat):
    parts = []
    # 1. Tapered Bin Body (Width: 0.58m, D: 0.70m, H: 0.95m, Z = 0.12m to 1.07m)
    body = kit.make_box(f"{name}_Body", 0.58, 0.70, 0.95, (x_pos, y_pos, 0.12))
    body.data.materials.append(mat)
    map_box(body, front=color_front, sides=color_front, back=color_front, top=R_BIN_LIDS)
    parts.append(body)

    # 2. Moulded Lid (Width: 0.62m, D: 0.74m, H: 0.08m, Z = 1.07m to 1.15m)
    lid = kit.make_box(f"{name}_Lid", 0.62, 0.74, 0.08, (x_pos, y_pos, 1.07))
    lid.data.materials.append(mat)
    map_box(lid, front=R_BIN_LIDS, sides=R_BIN_LIDS, top=R_BIN_LIDS)
    parts.append(lid)

    # 3. Rear Push Handle (Width: 0.50m, D: 0.08m, Z = 1.02m to 1.08m)
    handle = kit.make_box(f"{name}_Handle", 0.50, 0.08, 0.06, (x_pos, y_pos + 0.38, 1.02))
    handle.data.materials.append(mat)
    map_box(handle, front=R_BIN_LIDS, sides=R_BIN_LIDS, top=R_BIN_LIDS)
    parts.append(handle)

    # 4. Rear Rubber Wheels (Left & Right wheels, Diam 0.20m, Z = 0.02m to 0.22m)
    wheel_l = kit.make_box(f"{name}_WheelL", 0.06, 0.20, 0.20, (x_pos - 0.30, y_pos + 0.25, 0.02))
    wheel_l.data.materials.append(mat)
    map_box(wheel_l, front=R_RUBBER_WHEEL, sides=R_RUBBER_WHEEL, top=R_RUBBER_WHEEL)
    parts.append(wheel_l)

    wheel_r = kit.make_box(f"{name}_WheelR", 0.06, 0.20, 0.20, (x_pos + 0.30, y_pos + 0.25, 0.02))
    wheel_r.data.materials.append(mat)
    map_box(wheel_r, front=R_RUBBER_WHEEL, sides=R_RUBBER_WHEEL, top=R_RUBBER_WHEEL)
    parts.append(wheel_r)

    return parts


def main():
    kit.reset_scene()
    img = paint_wheelie_atlas()
    mat = material_for(img, "mat_wheelie_bins")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Council 240L Wheelie Bins Set (2.4m x 1.2m Footprint, Height: 1.15m)
    # - Pavement Slab Base with Litter (Z: 0.0 to 0.08m)
    # - Bin 1 (Left: X = -0.75m): Black General Waste (House "42")
    # - Bin 2 (Center: X = 0.0m): Green Organic Garden Waste
    # - Bin 3 (Right: X = +0.75m): Blue Paper/Cardboard Recycling
    # =========================================================================

    # 1. Pavement Concrete Base (2.6m x 1.4m, Z = 0.00 to 0.08m)
    register_box("PavementBase", 2.60, 1.40, 0.08, (0.0, 0.0, 0.0),
                 front=R_PAVE_LITTER, sides=R_PAVE_LITTER, top=R_PAVE_LITTER)

    # 2. Bin 1: Black General Waste Bin (X = -0.75m)
    parts.extend(make_wheelie_bin("BinBlack", -0.75, 0.0, 0, R_BIN_BLACK, mat))

    # 3. Bin 2: Green Recycling Bin (X = 0.0m, slightly offset forward Y = -0.05m)
    parts.extend(make_wheelie_bin("BinGreen", 0.0, -0.05, 0, R_BIN_GREEN, mat))

    # 4. Bin 3: Blue Paper Recycling Bin (X = 0.75m, angled slightly Y = 0.05m)
    parts.extend(make_wheelie_bin("BinBlue", 0.75, 0.05, 0, R_BIN_BLUE, mat))

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Wheelie_Bins")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_wheelie_bins_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_wheelie_bins.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_wheelie_bins.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_wheelie_bins_preview.png")
        shutil.copy2(OUT_DIR / "prop_wheelie_bins_atlas.png", TOOLS_OUT_DIR / "prop_wheelie_bins_atlas.png")
    except Exception as e:
        print(f"[prop_wheelie_bins] note: {e}")

    print("[prop_wheelie_bins] generation complete.")


main()
