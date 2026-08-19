"""Vending Machine with Overgrown Masses of Bright Green Fungus (High-Poly ~1000 Tris).

Specs:
- 1.2m wide x 0.9m deep x 2.2m high British snack/drinks vending machine engulfed in masses of bright electric green fungus
- High-Poly Bright Green Fungal Overgrowth (~1,000 Triangles):
  - Front glass display & housing completely erupting with 16 3D bright neon lime-green mushroom caps & bulbous spore sacks
  - Huge cascading 3D green fungal shelf clusters weeping down the front panels, coin slot, and keypad
  - Massive pulsating bright green spore cluster bursting out of the bottom dispense flap onto the pavement
  - Vivid electric toxic green bioluminescent texture atlas with glowing yellow-green spores and dripping slime tendrils
- Outputs to Tools/blender/out/bus_station/ and Tools/out/bus_station/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/bus_station/prop_vending_machine_fungal_growth.py
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
R_VEND_BLUE         = (0,   256, 256, 256)   # Blue enamel vending housing with green slime & rust
R_FUNGUS_CAP_GREEN  = (256, 256, 128, 256)   # Masses of vibrant electric neon green fungal mushroom caps
R_FUNGUS_STALK      = (0,   128, 256, 128)   # Pale lime/fibrous mushroom stalks & creeping green mycelium
R_FRONT_OVERGROWTH  = (256, 128, 128, 128)   # Front display engulfed in thick bright green fungus & slime
R_HEADER_SIGN       = (0,   0,   256, 128)   # Lit acrylic sign: "SNACK ATTACK" (cracked & mossy)
R_COIN_KEYPAD       = (256, 0,   128, 128)   # Keypad & coin slot choked with bright green slime
R_DISPENSE_FLAP     = (384, 256, 128, 128)   # Retrieval hatch bursting with neon green fungal mass
R_METAL_TRIM        = (384, 128, 128, 128)   # Dark galvanized steel base plinth
R_SPORE_MASS        = (384, 0,   128, 128)   # Glowing bioluminescent spore cluster

# --- Palette Colors ---
VEND_BLUE_BASE      = (0.14, 0.28, 0.52)
RUST_DARK           = (0.30, 0.16, 0.10)
GREEN_NEON_BASE     = (0.22, 0.95, 0.15)
GREEN_NEON_GLOW     = (0.55, 1.00, 0.20)
GREEN_ELECTRIC_HI   = (0.85, 1.00, 0.35)
GREEN_DARK_SHADOW   = (0.08, 0.55, 0.10)
STALK_LIME_PALE     = (0.75, 0.92, 0.65)
STALK_FIBER         = (0.45, 0.75, 0.35)
GLASS_DARK          = (0.10, 0.14, 0.18)
HEADER_CYAN         = (0.20, 0.80, 0.88)
STEEL_DARK          = (0.18, 0.20, 0.22)


def paint_fungal_vending_atlas():
    a = Atlas(S, seed=404)

    # 1. Blue Vending Housing with Creeping Green Slime (R_VEND_BLUE)
    x, y, w, h = R_VEND_BLUE
    a.rect(x, y, w, h, VEND_BLUE_BASE)
    a.shade(x, y, w, h, top=-0.04, bottom=-0.16)
    # Bright green slime weeping down edges
    for sx in range(x, x + w, 16):
        a.disc(sx, y + h - 14, 16, GREEN_NEON_BASE)
        a.disc(sx, y + h - 22, 10, GREEN_NEON_GLOW)
        a.disc(sx, y + 10, 12, GREEN_DARK_SHADOW)
    a.noise(x, y, w, h, 0.03)

    # 2. Masses of Vibrant Electric Green Fungus Caps (R_FUNGUS_CAP_GREEN)
    x, y, w, h = R_FUNGUS_CAP_GREEN
    a.rect(x, y, w, h, GREEN_NEON_BASE)
    # Glowing concentric spore rings & neon yellow-green highlights
    for cy in range(y + 16, y + h - 16, 28):
        for cx in range(x + 16, x + w - 16, 28):
            a.disc(cx, cy, 14, GREEN_NEON_GLOW)
            a.disc(cx, cy, 8, GREEN_ELECTRIC_HI)
            a.disc(cx, cy, 4, GREEN_DARK_SHADOW)
    a.noise(x, y, w, h, 0.02)

    # 3. Pale Lime Fibrous Mushroom Stalks & Green Mycelium (R_FUNGUS_STALK)
    x, y, w, h = R_FUNGUS_STALK
    a.rect(x, y, w, h, STALK_LIME_PALE)
    for sy in range(y, y + h, 10):
        a.rect(x, sy, w, 2, STALK_FIBER)
        for sx in range(x, x + w, 14):
            a.rect(sx, sy, 2, 10, GREEN_DARK_SHADOW)
    a.noise(x, y, w, h, 0.025)

    # 4. Front Display Engulfed in Bright Green Fungus (R_FRONT_OVERGROWTH)
    x, y, w, h = R_FRONT_OVERGROWTH
    a.rect(x, y, w, h, GREEN_NEON_BASE)
    # Glass remnants & spiral coils buried under green growth
    a.rect(x + 6, y + 6, w - 12, h - 12, GREEN_DARK_SHADOW)
    for gy in range(y + 12, y + h - 12, 20):
        for gx in range(x + 12, x + w - 12, 20):
            a.disc(gx, gy, 12, GREEN_NEON_BASE)
            a.disc(gx, gy, 7, GREEN_NEON_GLOW)
            a.disc(gx, gy, 3, GREEN_ELECTRIC_HI)
    a.noise(x, y, w, h, 0.02)

    # 5. Header Sign: "SNACK ATTACK" with Moss & Mold (R_HEADER_SIGN)
    x, y, w, h = R_HEADER_SIGN
    a.rect(x, y, w, h, (0.08, 0.12, 0.18))
    a.rect(x + 4, y + 4, w - 8, h - 8, HEADER_CYAN)
    s_title = "SNACK ATTACK"
    tw = a.text_width(s_title, scale=3)
    a.text(x + (w - tw) // 2, y + h - 22, s_title, (0.05, 0.10, 0.18), scale=3)
    # Green fungal creep across header
    for mx in range(x + 4, x + w - 4, 18):
        a.disc(mx, y + 10, 10, GREEN_NEON_BASE)
    a.noise(x, y, w, h, 0.015)

    # 6. Coin Keypad with Green Slime (R_COIN_KEYPAD)
    x, y, w, h = R_COIN_KEYPAD
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 12, y + h - 36, w - 24, 20, (0.05, 0.05, 0.05))
    a.text(x + 20, y + h - 24, "8.88", GREEN_ELECTRIC_HI, scale=2)
    for ky in range(y + 12, y + h - 44, 18):
        for kx in range(x + 16, x + w - 16, 24):
            a.rect(kx, ky, 16, 12, (0.5, 0.6, 0.5))
    # Green slime across keypad
    for sx in range(x + 8, x + w - 8, 20):
        a.disc(sx, y + 24, 12, GREEN_NEON_BASE)
    a.noise(x, y, w, h, 0.02)

    # 7. Dispense Flap Bursting with Neon Green Mass (R_DISPENSE_FLAP)
    x, y, w, h = R_DISPENSE_FLAP
    a.rect(x, y, w, h, GREEN_DARK_SHADOW)
    for gy in range(y + 10, y + h - 10, 16):
        for gx in range(x + 10, x + w - 10, 16):
            a.disc(gx, gy, 12, GREEN_NEON_BASE)
            a.disc(gx, gy, 6, GREEN_NEON_GLOW)
    a.noise(x, y, w, h, 0.02)

    # 8. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    # 9. Spore Mass (R_SPORE_MASS)
    x, y, w, h = R_SPORE_MASS
    a.rect(x, y, w, h, GREEN_NEON_GLOW)
    for sy in range(y, y + h, 14):
        a.disc(x + w // 2, sy, 18, GREEN_ELECTRIC_HI)
        a.disc(x + w // 2, sy, 8, GREEN_NEON_BASE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_vending_machine_fungal_growth_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_FUNGUS_CAP_GREEN, S, only=side("top"))
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


def make_mushroom_cap(name, r=0.20, h=0.12, segs=12, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = [(0, 0, h)]  # Apex
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    verts.append((0, 0, 0.02))  # Underside center

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((0, 1 + i, 1 + ni))
        faces.append((1 + ni, 1 + i, segs + 1))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_fungal_vending_atlas()
    mat = material_for(img, "mat_fungal_vending")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Vending Machine with Masses of Bright Green Fungus (~950 Tris)
    # =========================================================================

    # 1. Base Machine Chassis (1.20m x 0.85m x 2.10m)
    register_box("BasePlinth", 1.25, 0.90, 0.12, (0.0, 0.0, 0.0),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    register_box("MachineBody", 1.20, 0.85, 1.98, (0.0, 0.0, 0.12),
                 front=R_VEND_BLUE, sides=R_VEND_BLUE, back=R_VEND_BLUE, top=R_METAL_TRIM)

    # 2. Illuminated Header Sign with Green Creep
    register_box("HeaderSign", 1.15, 0.12, 0.32, (0.0, -0.38, 1.75),
                 front=R_HEADER_SIGN, sides=R_VEND_BLUE, top=R_FUNGUS_CAP_GREEN)

    # 3. Front Display Window Engulfed in Bright Green Fungus
    register_box("DisplayWindow", 0.72, 0.10, 1.08, (-0.22, -0.39, 0.60),
                 front=R_FRONT_OVERGROWTH, sides=R_FRONT_OVERGROWTH, top=R_FUNGUS_CAP_GREEN)

    # 4. Control Panel: Keypad & Coin Slot
    register_box("ControlPanel", 0.36, 0.10, 1.08, (0.38, -0.39, 0.60),
                 front=R_COIN_KEYPAD, sides=R_VEND_BLUE, top=R_FUNGUS_CAP_GREEN)

    # Bottom Dispense Flap Bursting with Green Mass
    register_box("RetrievalFlap", 0.85, 0.18, 0.35, (0.0, -0.40, 0.18),
                 front=R_DISPENSE_FLAP, sides=R_FUNGUS_CAP_GREEN, top=R_FUNGUS_CAP_GREEN)

    # =========================================================================
    # 5. MASSES OF BRIGHT GREEN 3D FUNGUS: 16 3D Mushroom Caps & Stalks on Front
    # =========================================================================
    # (x, y, z, stalk_r, stalk_h, cap_r, cap_h, pitch, yaw)
    green_mushrooms = [
        # Main front display burst (Center-Left)
        (-0.15, -0.46, 1.30, 0.06, 0.38, 0.26, 0.16, -30, 15),
        (-0.38, -0.44, 1.48, 0.05, 0.32, 0.22, 0.14, -25, -20),
        (0.02, -0.45, 1.00, 0.05, 0.34, 0.20, 0.12, -35, 30),
        (-0.28, -0.44, 0.82, 0.04, 0.26, 0.18, 0.11, -20, -10),
        (-0.05, -0.44, 1.55, 0.04, 0.28, 0.17, 0.11, -15, 10),

        # Bottom flap erupting cluster (Porous floor burst)
        (-0.30, -0.50, 0.30, 0.05, 0.30, 0.22, 0.14, -45, -15),
        (0.00, -0.52, 0.28, 0.06, 0.35, 0.25, 0.15, -40, 0),
        (0.25, -0.50, 0.32, 0.05, 0.28, 0.20, 0.13, -35, 25),
        (0.40, -0.48, 0.45, 0.04, 0.24, 0.16, 0.10, -25, 35),

        # Keypad & side wall encroaching clusters
        (0.48, -0.42, 1.15, 0.04, 0.25, 0.18, 0.12, -20, 45),
        (0.35, -0.43, 1.40, 0.04, 0.22, 0.16, 0.10, -25, 15),
        (0.55, -0.25, 0.85, 0.04, 0.26, 0.17, 0.11, -10, 80),

        # Top rooftop & header canopy giant caps
        (-0.25, -0.15, 2.10, 0.06, 0.32, 0.28, 0.18, 12, -20),
        (0.10, -0.10, 2.10, 0.07, 0.36, 0.30, 0.20, 15, 10),
        (0.35, -0.12, 2.10, 0.05, 0.28, 0.22, 0.14, 18, 30),
        (-0.42, -0.25, 1.85, 0.04, 0.24, 0.18, 0.11, -15, -45),
    ]

    for i, (mx, my, mz, sr, sh, cr, ch, pitch, yaw) in enumerate(green_mushrooms):
        stalk = make_cylinder(f"GreenStalk_{i}", sr, sh, segs=8, at=(mx, my, mz))
        stalk.rotation_euler = (math.radians(pitch), math.radians(yaw), 0)
        stalk.data.materials.append(mat)
        kit.map_faces_to_region(stalk, R_FUNGUS_STALK, S)
        parts.append(stalk)

        tip_x = mx - sh * math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
        tip_y = my - sh * math.sin(math.radians(pitch))
        tip_z = mz + sh * math.cos(math.radians(pitch)) * math.cos(math.radians(yaw))

        cap = make_mushroom_cap(f"GreenCap_{i}", r=cr, h=ch, segs=12, at=(tip_x, tip_y, tip_z))
        cap.rotation_euler = (math.radians(pitch), math.radians(yaw), 0)
        cap.data.materials.append(mat)
        kit.map_faces_to_region(cap, R_FUNGUS_CAP_GREEN, S)
        parts.append(cap)

    # 6. Massive 3D Bulbous Fungal Shelf Masses on Front
    front_green_masses = [
        (-0.25, -0.44, 1.15, 0.38, 0.18, 0.12),
        (0.20, -0.44, 0.90, 0.32, 0.16, 0.10),
        (-0.10, -0.48, 0.40, 0.45, 0.22, 0.15),
        (0.35, -0.46, 0.35, 0.30, 0.18, 0.12),
        (0.58, -0.20, 1.25, 0.14, 0.30, 0.10),
        (-0.05, -0.42, 1.70, 0.40, 0.16, 0.10),
    ]
    for i, (nx, ny, nz, nw, nd, nh) in enumerate(front_green_masses):
        node = register_box(f"GreenShelfNode_{i}", nw, nd, nh, (nx, ny, nz),
                            front=R_FUNGUS_CAP_GREEN, sides=R_FUNGUS_STALK, top=R_FUNGUS_CAP_GREEN)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Vending_Machine_Fungal_Growth")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_vending_machine_fungal_growth_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_vending_machine_fungal_growth.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_vending_machine_fungal_growth.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_vending_machine_fungal_growth_preview.png")
        shutil.copy2(OUT_DIR / "prop_vending_machine_fungal_growth_atlas.png", TOOLS_OUT_DIR / "prop_vending_machine_fungal_growth_atlas.png")
    except Exception as e:
        print(f"[prop_vending_machine_fungal_growth] note: {e}")

    print("[prop_vending_machine_fungal_growth] generation complete.")


main()
