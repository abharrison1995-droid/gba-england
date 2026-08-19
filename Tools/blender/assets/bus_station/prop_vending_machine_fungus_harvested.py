"""Vending Machine with Harvested Fungus (Depleted / Harvested State).

Specs:
- 1.2m wide x 0.9m deep x 2.2m high British snack/drinks vending machine after harvesting the masses of bright green fungus
- Post-Harvest State Features (~850 Triangles):
  - Identical vending machine cabinet & cracked glass frame
  - 16 mature bright green mushroom caps cleanly cut / harvested away
  - Remaining 3D cut stalk stumps with pale lime/fleshy cross-sections
  - Residual green mycelium shelf bases, root tendrils, and harvested scars on the front face
- Outputs to Tools/blender/out/bus_station/ and Tools/out/bus_station/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/bus_station/prop_vending_machine_fungus_harvested.py
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
OUT_DIR = kit.OUT_DIR / "bus_station"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "bus_station"

# --- Atlas Region Definitions (x, y, w, h) ---
R_VEND_BLUE         = (0,   256, 256, 256)   # Blue enamel vending housing with residual green slime & rust
R_FUNGUS_CAP_GREEN  = (256, 256, 128, 256)   # Residual tiny unpicked bright green spore pins
R_FUNGUS_STALK      = (0,   128, 256, 128)   # Pale lime fibrous mushroom stalks & cut fleshy cross-sections
R_FRONT_HARVESTED   = (256, 128, 128, 128)   # Front display with cut green mycelium roots & harvested scars
R_HEADER_SIGN       = (0,   0,   256, 128)   # Lit acrylic sign: "SNACK ATTACK" (cracked & mossy)
R_COIN_KEYPAD       = (256, 0,   128, 128)   # Keypad & coin slot
R_DISPENSE_FLAP     = (384, 256, 128, 128)   # Retrieval hatch with residual cut green stumps
R_METAL_TRIM        = (384, 128, 128, 128)   # Dark galvanized steel base plinth
R_SPORE_MASS        = (384, 0,   128, 128)   # Residual spore scabs

# --- Palette Colors ---
VEND_BLUE_BASE      = (0.14, 0.28, 0.52)
RUST_DARK           = (0.30, 0.16, 0.10)
GREEN_NEON_BASE     = (0.22, 0.95, 0.15)
GREEN_NEON_GLOW     = (0.55, 1.00, 0.20)
GREEN_ELECTRIC_HI   = (0.85, 1.00, 0.35)
GREEN_DARK_SHADOW   = (0.08, 0.55, 0.10)
STALK_LIME_PALE     = (0.75, 0.92, 0.65)
STALK_FIBER         = (0.45, 0.75, 0.35)
STALK_CUT_FLESH     = (0.90, 0.98, 0.88)
HEADER_CYAN         = (0.20, 0.80, 0.88)
STEEL_DARK          = (0.18, 0.20, 0.22)


def paint_harvested_vending_atlas():
    a = Atlas(S, seed=405)

    # 1. Blue Vending Housing with Residual Slime (R_VEND_BLUE)
    x, y, w, h = R_VEND_BLUE
    a.rect(x, y, w, h, VEND_BLUE_BASE)
    a.shade(x, y, w, h, top=-0.04, bottom=-0.16)
    for sx in range(x, x + w, 16):
        a.disc(sx, y + h - 14, 12, GREEN_DARK_SHADOW)
    a.noise(x, y, w, h, 0.03)

    # 2. Residual Tiny Spore Pins (R_FUNGUS_CAP_GREEN)
    x, y, w, h = R_FUNGUS_CAP_GREEN
    a.rect(x, y, w, h, GREEN_DARK_SHADOW)
    for cy in range(y + 16, y + h - 16, 28):
        for cx in range(x + 16, x + w - 16, 28):
            a.disc(cx, cy, 8, GREEN_NEON_BASE)
            a.disc(cx, cy, 4, GREEN_NEON_GLOW)
    a.noise(x, y, w, h, 0.02)

    # 3. Cut Fibrous Stalks with White Flesh (R_FUNGUS_STALK)
    x, y, w, h = R_FUNGUS_STALK
    a.rect(x, y, w, h, STALK_LIME_PALE)
    for sy in range(y, y + h, 10):
        a.rect(x, sy, w, 2, STALK_FIBER)
    # Cut cross-section disc
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 32, STALK_CUT_FLESH)
    a.disc(cx, cy, 16, (0.75, 0.88, 0.72))
    a.noise(x, y, w, h, 0.02)

    # 4. Front Display Harvested (R_FRONT_HARVESTED)
    x, y, w, h = R_FRONT_HARVESTED
    a.rect(x, y, w, h, GREEN_DARK_SHADOW)
    for gy in range(y + 12, y + h - 12, 24):
        for gx in range(x + 12, x + w - 12, 24):
            a.disc(gx, gy, 10, STALK_CUT_FLESH)
            a.disc(gx, gy, 4, GREEN_NEON_BASE)
    a.noise(x, y, w, h, 0.02)

    # 5. Header Sign (R_HEADER_SIGN)
    x, y, w, h = R_HEADER_SIGN
    a.rect(x, y, w, h, (0.08, 0.12, 0.18))
    a.rect(x + 4, y + 4, w - 8, h - 8, HEADER_CYAN)
    s_title = "SNACK ATTACK"
    tw = a.text_width(s_title, scale=3)
    a.text(x + (w - tw) // 2, y + h - 22, s_title, (0.05, 0.10, 0.18), scale=3)
    a.noise(x, y, w, h, 0.015)

    # 6. Coin Keypad (R_COIN_KEYPAD)
    x, y, w, h = R_COIN_KEYPAD
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 12, y + h - 36, w - 24, 20, (0.05, 0.05, 0.05))
    a.text(x + 20, y + h - 24, "8.88", GREEN_ELECTRIC_HI, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 7. Dispense Flap (R_DISPENSE_FLAP)
    x, y, w, h = R_DISPENSE_FLAP
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.12, 0.14, 0.16))
    a.text(x + 24, y + h // 2, "PUSH", (0.8, 0.8, 0.8), scale=2)

    # 8. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    # 9. Spore Mass (R_SPORE_MASS)
    x, y, w, h = R_SPORE_MASS
    a.rect(x, y, w, h, GREEN_DARK_SHADOW)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_vending_machine_fungus_harvested_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_FUNGUS_STALK, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_METAL_TRIM, S, only=side("bottom"))


def make_cylinder(name, r, h, segs=10, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    faces.append(list(range(segs - 1, -1, -1)))
    faces.append(list(range(segs, segs * 2)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_harvested_vending_atlas()
    mat = material_for(img, "mat_harvested_vending")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Harvested Vending Machine (Depleted Green Fungus Stalks & Stumps)
    # =========================================================================

    # 1. Base Machine Chassis
    register_box("BasePlinth", 1.25, 0.90, 0.12, (0.0, 0.0, 0.0),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    register_box("MachineBody", 1.20, 0.85, 1.98, (0.0, 0.0, 0.12),
                 front=R_VEND_BLUE, sides=R_VEND_BLUE, back=R_VEND_BLUE, top=R_METAL_TRIM)

    # 2. Header Sign
    register_box("HeaderSign", 1.15, 0.12, 0.32, (0.0, -0.38, 1.75),
                 front=R_HEADER_SIGN, sides=R_VEND_BLUE, top=R_FUNGUS_STALK)

    # 3. Front Display Window
    register_box("DisplayWindow", 0.72, 0.10, 1.08, (-0.22, -0.39, 0.60),
                 front=R_FRONT_HARVESTED, sides=R_FRONT_HARVESTED, top=R_FUNGUS_STALK)

    # 4. Control Panel: Keypad & Coin Slot
    register_box("ControlPanel", 0.36, 0.10, 1.08, (0.38, -0.39, 0.60),
                 front=R_COIN_KEYPAD, sides=R_VEND_BLUE, top=R_FUNGUS_STALK)

    # Bottom Dispense Flap
    register_box("RetrievalFlap", 0.85, 0.18, 0.35, (0.0, -0.40, 0.18),
                 front=R_DISPENSE_FLAP, sides=R_FUNGUS_STALK, top=R_FUNGUS_STALK)

    # =========================================================================
    # 5. 16 Cut Stalk Stumps (Clean cut short stalks with flat white cross-sections)
    # =========================================================================
    cut_stumps = [
        (-0.15, -0.46, 1.30, 0.06, 0.12, -30, 15),
        (-0.38, -0.44, 1.48, 0.05, 0.10, -25, -20),
        (0.02, -0.45, 1.00, 0.05, 0.11, -35, 30),
        (-0.28, -0.44, 0.82, 0.04, 0.09, -20, -10),
        (-0.05, -0.44, 1.55, 0.04, 0.08, -15, 10),

        (-0.30, -0.50, 0.30, 0.05, 0.10, -45, -15),
        (0.00, -0.52, 0.28, 0.06, 0.12, -40, 0),
        (0.25, -0.50, 0.32, 0.05, 0.09, -35, 25),
        (0.40, -0.48, 0.45, 0.04, 0.08, -25, 35),

        (0.48, -0.42, 1.15, 0.04, 0.08, -20, 45),
        (0.35, -0.43, 1.40, 0.04, 0.07, -25, 15),
        (0.55, -0.25, 0.85, 0.04, 0.09, -10, 80),

        (-0.25, -0.15, 2.10, 0.06, 0.10, 12, -20),
        (0.10, -0.10, 2.10, 0.07, 0.12, 15, 10),
        (0.35, -0.12, 2.10, 0.05, 0.09, 18, 30),
        (-0.42, -0.25, 1.85, 0.04, 0.08, -15, -45),
    ]

    for i, (sx, sy, sz, sr, sh, pitch, yaw) in enumerate(cut_stumps):
        stump = make_cylinder(f"CutStump_{i}", sr, sh, segs=8, at=(sx, sy, sz))
        stump.rotation_euler = (math.radians(pitch), math.radians(yaw), 0)
        stump.data.materials.append(mat)
        kit.map_faces_to_region(stump, R_FUNGUS_STALK, S)
        parts.append(stump)

    # 6. Residual Cut Green Shelf Base Brackets
    residual_masses = [
        (-0.25, -0.44, 1.15, 0.28, 0.12, 0.06),
        (0.20, -0.44, 0.90, 0.22, 0.10, 0.05),
        (-0.10, -0.48, 0.40, 0.30, 0.14, 0.08),
        (0.35, -0.46, 0.35, 0.20, 0.12, 0.06),
        (0.58, -0.20, 1.25, 0.08, 0.18, 0.05),
        (-0.05, -0.42, 1.70, 0.25, 0.10, 0.05),
    ]
    for i, (nx, ny, nz, nw, nd, nh) in enumerate(residual_masses):
        node = register_box(f"HarvestedShelfNode_{i}", nw, nd, nh, (nx, ny, nz),
                            front=R_FUNGUS_STALK, sides=R_FUNGUS_STALK, top=R_FUNGUS_STALK)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Vending_Machine_Fungus_Harvested")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_vending_machine_fungus_harvested_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_vending_machine_fungus_harvested.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_vending_machine_fungus_harvested.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_vending_machine_fungus_harvested_preview.png")
        shutil.copy2(OUT_DIR / "prop_vending_machine_fungus_harvested_atlas.png", TOOLS_OUT_DIR / "prop_vending_machine_fungus_harvested_atlas.png")
    except Exception as e:
        print(f"[prop_vending_machine_fungus_harvested] note: {e}")

    print("[prop_vending_machine_fungus_harvested] generation complete.")


main()
