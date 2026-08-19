"""Commercial Industrial Skip / Roll-on Dumpster (Street Rubbish Prop).

Specs:
- 3.2m x 1.8m footprint, Height: 1.4m.
- Classic British yellow commercial builder's skip:
  - Trapezoidal sloping ends with reinforced steel channel rim.
  - Weathered builder's yellow enamel with grimy rust patina, scratches, and oil drips.
  - Stencilled warning: "MAX LOAD - NO FIRES - 0800 SKIP HIRE".
  - Yellow/black reflective safety chevron hazard marker plates.
  - Overflowing construction debris: broken London yellow stock bricks, plasterboard, timber offcuts.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_street_dumpster.py
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
R_SKIP_YELLOW   = (0,   256, 256, 256)   # Weathered yellow enamel skip side with stencil & rust
R_SKIP_DEBRIS   = (256, 256, 256, 256)   # Overflowing rubble, broken bricks, mortar & timber
R_CHEVRON_PLATE = (0,   128, 256, 128)   # Reflective red/yellow hazard chevron corner markers
R_RUST_METAL    = (256, 128, 128, 128)   # Heavy pitted dark rust & oil stains
R_STEEL_RIM     = (384, 128, 128, 128)   # Reinforced dark steel lip rim & lifting lugs
R_GROUND_ASPHALT= (0,   0,   256, 128)   # Road asphalt ground with tyre scuffs & grit
R_TIMBER_OFFCUT = (256, 0,   128, 128)   # Splintered pine timber 2x4s
R_PLASTER_DUST  = (384, 0,   128, 128)   # White gypsum plasterboard & cement dust

# --- Palette Colors ---
SKIP_YELLOW     = (0.92, 0.72, 0.12)
SKIP_DARK_YELL  = (0.65, 0.48, 0.08)
RUST_BROWN      = (0.42, 0.22, 0.12)
RUST_DARK       = (0.24, 0.12, 0.08)
STEEL_BLACK     = (0.16, 0.16, 0.18)
CHEVRON_RED     = (0.85, 0.12, 0.14)
CHEVRON_YELL    = (0.95, 0.85, 0.10)
BRICK_RED       = (0.72, 0.32, 0.22)
ASPHALT_GREY    = (0.32, 0.32, 0.34)


def paint_dumpster_atlas():
    a = Atlas(S, seed=4101)

    # 1. Weathered Yellow Skip Side (R_SKIP_YELLOW)
    x, y, w, h = R_SKIP_YELLOW
    a.rect(x, y, w, h, SKIP_YELLOW)
    # Rust streaks dripping from top rim
    a.shade(x, y, w, h, top=-0.10, bottom=0.15)
    for rx in range(x + 16, x + w - 16, 28):
        a.rect(rx, y, 6, 40, RUST_BROWN)
        a.rect(rx + 2, y, 2, 80, RUST_DARK)
    # Stencilled Text: "0800 SKIP HIRE"
    s1 = "0800 SKIP HIRE"
    tw1 = a.text_width(s1, scale=2)
    a.text(x + (w - tw1) // 2, y + h // 2 + 10, s1, STEEL_BLACK, scale=2)
    # Subtitle: "MAX LOAD - NO FIRES"
    s2 = "MAX LOAD - NO FIRES"
    tw2 = a.text_width(s2, scale=1)
    a.text(x + (w - tw2) // 2, y + h // 2 - 18, s2, STEEL_BLACK, scale=1)
    # Welded steel ribs
    a.rect(x, y + 20, w, 4, STEEL_BLACK)
    a.rect(x, y + h - 24, w, 4, STEEL_BLACK)
    a.noise(x, y, w, h, 0.035)

    # 2. Construction Rubble & Bricks (R_SKIP_DEBRIS)
    x, y, w, h = R_SKIP_DEBRIS
    a.rect(x, y, w, h, (0.55, 0.52, 0.48))  # Mortar & dust
    # Broken bricks & concrete chunks
    for by in range(y + 12, y + h - 12, 28):
        for bx in range(x + 12, x + w - 12, 36):
            a.rect(bx, by, 28, 16, BRICK_RED)
            a.rect(bx + 4, by + 4, 12, 8, (0.85, 0.75, 0.30))  # yellow stock brick
    # Timber offcuts crossing through
    a.rect(x + 30, y + 20, 180, 12, (0.65, 0.48, 0.28))
    a.rect(x + 60, y + 140, 140, 14, (0.55, 0.40, 0.22))
    a.noise(x, y, w, h, 0.045)

    # 3. Hazard Chevrons (R_CHEVRON_PLATE)
    x, y, w, h = R_CHEVRON_PLATE
    a.rect(x, y, w, h, CHEVRON_RED)
    # Diagonal yellow reflective stripes
    for cx in range(x - 40, x + w + 40, 32):
        for step in range(0, h, 4):
            a.rect(cx + step, y + step, 16, 4, CHEVRON_YELL)
    a.noise(x, y, w, h, 0.02)

    # 4. Pitted Rust Metal (R_RUST_METAL)
    x, y, w, h = R_RUST_METAL
    a.rect(x, y, w, h, RUST_BROWN)
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 4, RUST_DARK)
    a.noise(x, y, w, h, 0.05)

    # 5. Steel Lip Rim (R_STEEL_RIM)
    x, y, w, h = R_STEEL_RIM
    a.rect(x, y, w, h, STEEL_BLACK)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.35, 0.35, 0.38))
    a.noise(x, y, w, h, 0.025)

    # 6. Asphalt Ground (R_GROUND_ASPHALT)
    x, y, w, h = R_GROUND_ASPHALT
    a.rect(x, y, w, h, ASPHALT_GREY)
    a.noise(x, y, w, h, 0.04)

    # 7. Timber 2x4s (R_TIMBER_OFFCUT)
    x, y, w, h = R_TIMBER_OFFCUT
    a.rect(x, y, w, h, (0.68, 0.50, 0.32))
    a.noise(x, y, w, h, 0.03)

    # 8. Plasterboard Dust (R_PLASTER_DUST)
    x, y, w, h = R_PLASTER_DUST
    a.rect(x, y, w, h, (0.88, 0.88, 0.86))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_street_dumpster_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STEEL_RIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_RUST_METAL, S, only=side("bottom"))


def make_trapezoid_skip(name, bw, tw, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hbw, htw, hd = bw / 2.0, tw / 2.0, d / 2.0
    verts = [
        # Bottom 4 verts
        (-hbw, -hd, 0.0), (hbw, -hd, 0.0), (hbw, hd, 0.0), (-hbw, hd, 0.0),
        # Top 4 verts (wider in X)
        (-htw, -hd, h), (htw, -hd, h), (htw, hd, h), (-htw, hd, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front
        (1, 2, 6, 5),    # right slope
        (2, 3, 7, 6),    # back
        (3, 0, 4, 7),    # left slope
        (4, 5, 6, 7),    # top
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_dumpster_atlas()
    mat = material_for(img, "mat_street_dumpster")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Commercial Industrial Builder's Skip (3.2m x 1.8m Footprint, Height: 1.4m)
    # - Road Asphalt Base Slab (Z: 0.0 to 0.10m)
    # - Trapezoidal Yellow Skip Tub with Sloping Ends (Z: 0.10m to 1.25m)
    # - Welded Top Steel Channel Rim (Z: 1.25m to 1.35m)
    # - Overflowing Demolition Rubble, Bricks & Timber (Z: 1.20m to 1.55m)
    # - Reflective Hazard Chevrons & Side Crane Lifting Lugs
    # =========================================================================

    # 1. Road Asphalt Base (3.6m x 2.2m, Z = 0.00 to 0.10m)
    register_box("AsphaltBase", 3.60, 2.20, 0.10, (0.0, 0.0, 0.0),
                 front=R_GROUND_ASPHALT, sides=R_GROUND_ASPHALT, top=R_GROUND_ASPHALT)

    # 2. Main Trapezoidal Skip Tub (Bottom Width: 2.2m, Top Width: 3.2m, D: 1.60m, H: 1.15m, Z = 0.10m to 1.25m)
    skip = make_trapezoid_skip("SkipTub", 2.20, 3.20, 1.60, 1.15, at=(0.0, 0.0, 0.10))
    skip.data.materials.append(mat)
    kit.map_faces_to_region(skip, R_SKIP_YELLOW, S, only=lambda f: abs(f.normal.y) > 0.5)
    kit.map_faces_to_region(skip, R_CHEVRON_PLATE, S, only=lambda f: abs(f.normal.x) > 0.5)
    kit.map_faces_to_region(skip, R_SKIP_DEBRIS, S, only=lambda f: f.normal.z > 0.5)
    kit.map_faces_to_region(skip, R_RUST_METAL, S, only=lambda f: f.normal.z < -0.5)
    parts.append(skip)

    # 3. Top Reinforced Steel Channel Rim (3.30m x 1.70m, Z = 1.25m to 1.35m, H: 0.10m)
    register_box("SkipRim", 3.30, 1.70, 0.10, (0.0, 0.0, 1.25),
                 front=R_STEEL_RIM, sides=R_STEEL_RIM, back=R_STEEL_RIM, top=R_SKIP_DEBRIS)

    # 4. Overflowing Construction Debris Heap (Width: 2.80m, D: 1.30m, H: 0.35m, Z = 1.30m to 1.65m)
    register_box("RubbleMound", 2.80, 1.30, 0.35, (0.0, 0.0, 1.30),
                 front=R_SKIP_DEBRIS, sides=R_SKIP_DEBRIS, top=R_SKIP_DEBRIS)

    # 5. Projecting Timber 2x4 Planks (Overflowing over edge)
    register_box("TimberPlank1", 1.80, 0.15, 0.08, (0.40, -0.45, 1.55),
                 front=R_TIMBER_OFFCUT, sides=R_TIMBER_OFFCUT, top=R_TIMBER_OFFCUT)
    register_box("TimberPlank2", 1.40, 0.15, 0.08, (-0.60, 0.35, 1.60),
                 front=R_TIMBER_OFFCUT, sides=R_TIMBER_OFFCUT, top=R_TIMBER_OFFCUT)

    # 6. Crane Lifting Lugs (4 welded forged steel pin lugs on sides)
    for lx in [-0.80, 0.80]:
        register_box(f"LugFront_{lx}", 0.12, 0.12, 0.15, (lx, -0.85, 0.70),
                     front=R_STEEL_RIM, sides=R_STEEL_RIM, top=R_STEEL_RIM)
        register_box(f"LugBack_{lx}", 0.12, 0.12, 0.15, (lx, 0.85, 0.70),
                     front=R_STEEL_RIM, sides=R_STEEL_RIM, top=R_STEEL_RIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Street_Dumpster")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_street_dumpster_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_street_dumpster.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_street_dumpster.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_street_dumpster_preview.png")
        shutil.copy2(OUT_DIR / "prop_street_dumpster_atlas.png", TOOLS_OUT_DIR / "prop_street_dumpster_atlas.png")
    except Exception as e:
        print(f"[prop_street_dumpster] note: {e}")

    print("[prop_street_dumpster] generation complete.")


main()
