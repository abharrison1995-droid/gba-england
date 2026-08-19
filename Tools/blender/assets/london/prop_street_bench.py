"""Victorian Cast-Iron & Teak London Street Bench (Street Furniture Prop).

Specs:
- 2.2m x 1.0m footprint, Height: 0.95m.
- Classic British municipal park & street bench:
  - Ornate cast-iron dark green stanchions with Victorian scrollwork & lion paw feet.
  - Varnished natural teak hardwood timber slats on seat and curved backrest.
  - Central cast-iron intermediate support bracket.
  - Polished brass memorial tribute plaque: "IN LOVING MEMORY".
  - Dressed stone pavement plinth with fallen autumn leaves & moss.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_street_bench.py
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
R_TEAK_SLATS    = (0,   256, 256, 256)   # Varnished teak wood slats with rich grain & wood screws
R_CAST_IRON     = (256, 256, 256, 256)   # Dark heritage green Victorian cast-iron scrollwork
R_BRASS_PLAQUE  = (0,   128, 256, 128)   # Polished brass engraved memorial dedication plaque
R_PAVE_LEAVES   = (256, 128, 128, 128)   # York stone paving slabs with fallen autumn leaves
R_MOSS_TRIM     = (384, 128, 128, 128)   # Weathered stone & green moss edge
R_IRON_BOLTS    = (0,   0,   256, 128)   # Forged iron bolts & ground anchor brackets
R_WOOD_ENDGRAIN = (256, 0,   128, 128)   # Teak slat endgrain & cross-cut timber
R_FALLEN_LEAF   = (384, 0,   128, 128)   # Golden orange & red autumn oak leaves

# --- Palette Colors ---
TEAK_WOOD       = (0.52, 0.32, 0.18)
TEAK_DARK       = (0.32, 0.18, 0.10)
TEAK_GRAIN      = (0.65, 0.42, 0.24)
IRON_GREEN      = (0.10, 0.22, 0.15)
IRON_DARK       = (0.06, 0.12, 0.08)
BRASS_GOLD      = (0.92, 0.78, 0.25)
BRASS_DARK      = (0.50, 0.40, 0.12)
STONE_YORK      = (0.72, 0.70, 0.65)
LEAF_ORANGE     = (0.88, 0.45, 0.10)


def paint_bench_atlas():
    a = Atlas(S, seed=4401)

    # 1. Varnished Teak Wood Slats (R_TEAK_SLATS)
    x, y, w, h = R_TEAK_SLATS
    a.rect(x, y, w, h, TEAK_WOOD)
    # Wood grain and slat separations
    for sy in range(y, y + h, 24):
        a.rect(x, sy, w, 3, TEAK_DARK)
        a.rect(x, sy + 3, w, 1, TEAK_GRAIN)
        # Brass screw heads at ends
        a.disc(x + 14, sy + 12, 4, BRASS_GOLD)
        a.disc(x + w - 14, sy + 12, 4, BRASS_GOLD)
        a.disc(x + w // 2, sy + 12, 4, BRASS_GOLD)
    a.noise(x, y, w, h, 0.025)

    # 2. Victorian Cast-Iron Scrollwork (R_CAST_IRON)
    x, y, w, h = R_CAST_IRON
    a.rect(x, y, w, h, IRON_GREEN)
    # Scrollwork curves and lion head crest
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 55, IRON_DARK)
    a.disc(cx, cy, 40, IRON_GREEN)
    a.disc(cx, cy, 20, (0.15, 0.32, 0.20))
    # Acanthus leaf brackets
    for step in range(-40, 41, 10):
        a.disc(cx + step, cy + 30, 8, IRON_DARK)
    a.noise(x, y, w, h, 0.03)

    # 3. Polished Brass Plaque (R_BRASS_PLAQUE)
    x, y, w, h = R_BRASS_PLAQUE
    a.rect(x, y, w, h, BRASS_GOLD)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.98, 0.88, 0.35))
    # Screws in 4 corners
    for sx in [x + 8, x + w - 8]:
        for sy in [y + 8, y + h - 8]:
            a.disc(sx, sy, 3, BRASS_DARK)
    # Inscribed Text: "IN LOVING MEMORY"
    s1 = "IN LOVING MEMORY"
    tw1 = a.text_width(s1, scale=2)
    a.text(x + (w - tw1) // 2, y + h // 2 - 6, s1, BRASS_DARK, scale=2)
    a.noise(x, y, w, h, 0.015)

    # 4. Yorkstone Paving with Leaves (R_PAVE_LEAVES)
    x, y, w, h = R_PAVE_LEAVES
    a.rect(x, y, w, h, STONE_YORK)
    # Scattered autumn oak leaves
    for lx, ly in [(x + 24, y + 30), (x + 80, y + 80), (x + 100, y + 20)]:
        a.disc(lx, ly, 10, LEAF_ORANGE)
        a.disc(lx + 4, ly + 2, 6, (0.85, 0.25, 0.10))
    a.noise(x, y, w, h, 0.03)

    # 5. Moss Trim (R_MOSS_TRIM)
    x, y, w, h = R_MOSS_TRIM
    a.rect(x, y, w, h, (0.55, 0.52, 0.46))
    for mx in range(x, x + w, 16):
        a.disc(mx, y + 8, 10, (0.22, 0.38, 0.16))
    a.noise(x, y, w, h, 0.03)

    # 6. Iron Bolts (R_IRON_BOLTS)
    x, y, w, h = R_IRON_BOLTS
    a.rect(x, y, w, h, IRON_DARK)
    for bx in range(x + 16, x + w, 32):
        a.disc(bx, y + h // 2, 8, (0.4, 0.4, 0.4))
    a.noise(x, y, w, h, 0.02)

    # 7. Teak Endgrain (R_WOOD_ENDGRAIN)
    x, y, w, h = R_WOOD_ENDGRAIN
    a.rect(x, y, w, h, TEAK_DARK)
    a.noise(x, y, w, h, 0.04)

    # 8. Fallen Leaf (R_FALLEN_LEAF)
    x, y, w, h = R_FALLEN_LEAF
    a.rect(x, y, w, h, LEAF_ORANGE)
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_street_bench_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_TEAK_SLATS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CAST_IRON, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_bench_atlas()
    mat = material_for(img, "mat_street_bench")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Victorian Cast-Iron London Street Bench (2.2m x 1.0m Footprint, Height: 0.95m)
    # - Yorkstone Paving Slab Plinth (Z: 0.0 to 0.08m)
    # - 3 Cast-Iron Stanchions with Armrests (Left, Center, Right: Z = 0.08m to 0.70m)
    # - Varnished Teak Wood Seat Slats (Width 2.0m, D: 0.50m, Z = 0.48m to 0.56m)
    # - Ergonomic Curved Teak Backrest (Width 2.0m, H: 0.45m, Z = 0.56m to 0.95m)
    # - Brass Memorial Plaque mounted in backrest center
    # =========================================================================

    # 1. Yorkstone Pavement Plinth (2.4m x 1.2m, Z = 0.00 to 0.08m)
    register_box("BenchPlinth", 2.40, 1.20, 0.08, (0.0, 0.0, 0.0),
                 front=R_PAVE_LEAVES, sides=R_PAVE_LEAVES, top=R_PAVE_LEAVES)

    # 2. 3 Cast-Iron Stanchions with Armrests & Lion Feet (X = -0.95m, 0.0m, +0.95m)
    for i, sx in enumerate([-0.95, 0.0, 0.95]):
        # Stanchion lower leg & foot
        register_box(f"StanchionLeg_{i}", 0.08, 0.65, 0.45, (sx, 0.0, 0.08),
                     front=R_CAST_IRON, sides=R_CAST_IRON, top=R_CAST_IRON)
        # Armrest curve (Z = 0.48m to 0.68m)
        register_box(f"Armrest_{i}", 0.08, 0.55, 0.20, (sx, -0.05, 0.48),
                     front=R_CAST_IRON, sides=R_CAST_IRON, top=R_CAST_IRON)
        # Back upright support
        register_box(f"BackUpright_{i}", 0.08, 0.12, 0.42, (sx, 0.22, 0.53),
                     front=R_CAST_IRON, sides=R_CAST_IRON, top=R_CAST_IRON)

    # 3. Teak Wood Slatted Seat (Width 2.00m, D: 0.52m, H: 0.08m, Z = 0.45m to 0.53m)
    register_box("SeatSlats", 2.00, 0.52, 0.08, (0.0, -0.02, 0.45),
                 front=R_TEAK_SLATS, sides=R_WOOD_ENDGRAIN, back=R_TEAK_SLATS, top=R_TEAK_SLATS)

    # 4. Teak Wood Slatted Backrest (Width 2.00m, D: 0.10m, H: 0.40m, Z = 0.55m to 0.95m at Y = 0.22m)
    register_box("BackrestSlats", 2.00, 0.10, 0.40, (0.0, 0.22, 0.55),
                 front=R_TEAK_SLATS, sides=R_WOOD_ENDGRAIN, back=R_TEAK_SLATS, top=R_TEAK_SLATS)

    # 5. Polished Brass Memorial Plaque (Mounted in center of backrest)
    register_box("MemorialPlaque", 0.55, 0.03, 0.18, (0.0, 0.16, 0.68),
                 front=R_BRASS_PLAQUE, sides=R_BRASS_PLAQUE, top=R_BRASS_PLAQUE)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Street_Bench")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_street_bench_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_street_bench.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_street_bench.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_street_bench_preview.png")
        shutil.copy2(OUT_DIR / "prop_street_bench_atlas.png", TOOLS_OUT_DIR / "prop_street_bench_atlas.png")
    except Exception as e:
        print(f"[prop_street_bench] note: {e}")

    print("[prop_street_bench] generation complete.")


main()
