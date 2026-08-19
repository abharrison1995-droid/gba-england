"""London Underground Oyster Card Fare Gate Turnstiles (Tube Environment Prop).

Specs:
- 3.6m x 2.0m footprint, Height: 1.25m.
- Bank of 3 modern London Underground ticket barrier turnstiles:
  - Brushed stainless steel barrier pedestals with dark charcoal glass tops.
  - Iconic circular yellow Oyster / contactless reader touch pads.
  - Illuminated LED status displays: Green Arrow (Open) & Red Cross (Closed).
  - Pneumatic orange / clear glass gate paddle barrier wings.
  - Concourse ceramic tiled floor base with yellow tactile safety line.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_tube_turnstile.py
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
R_OYSTER_PAD    = (0,   256, 256, 256)   # Yellow Oyster reader disc, green LED arrow & LCD
R_STEEL_BARRIER = (256, 256, 256, 256)   # Brushed stainless steel pedestal side panels
R_GATE_PADDLE   = (0,   128, 256, 128)   # Bright orange / glass safety barrier paddle wings
R_CONCOURSE_TILE= (256, 128, 128, 128)   # Underground station concourse floor tiles & yellow line
R_GLASS_TOP     = (384, 128, 128, 128)   # Smoked black glass pedestal top surface
R_RED_CROSS_LED = (0,   0,   256, 128)   # Red 'X' no entry LED display
R_TICKET_SLOT   = (256, 0,   128, 128)   # Magnetic paper ticket feeder slot & LED
R_STAINLESS_TRIM= (384, 0,   128, 128)   # Polished stainless steel corner trims

# --- Palette Colors ---
STEEL_BRUSHED   = (0.75, 0.77, 0.80)
STEEL_DARK      = (0.45, 0.47, 0.50)
OYSTER_YELLOW   = (0.98, 0.84, 0.12)
LED_GREEN       = (0.15, 0.95, 0.25)
LED_RED         = (0.95, 0.12, 0.15)
PADDLE_ORANGE   = (0.98, 0.45, 0.08)
GLASS_SMOKED    = (0.12, 0.14, 0.16)
FLOOR_TERRAZZO  = (0.65, 0.65, 0.68)


def paint_turnstile_atlas():
    a = Atlas(S, seed=3301)

    # 1. Yellow Oyster Reader & Green Arrow (R_OYSTER_PAD)
    x, y, w, h = R_OYSTER_PAD
    a.rect(x, y, w, h, STEEL_BRUSHED)
    # Smoked glass top insert
    a.rect(x + 12, y + 12, w - 24, h - 24, GLASS_SMOKED)
    # Circular Yellow Oyster Reader Pad
    cx, cy = x + w // 2, y + h // 2 + 30
    a.disc(cx, cy, 48, OYSTER_YELLOW)
    a.disc(cx, cy, 42, (0.92, 0.76, 0.08))
    # Reader target crosshair rings
    a.disc(cx, cy, 24, OYSTER_YELLOW)
    a.disc(cx, cy, 8, (0.2, 0.2, 0.2))
    # Green LED Arrow Display (Below Oyster pad)
    ax, ay = x + w // 2, y + 50
    a.rect(ax - 28, ay - 18, 56, 36, (0.05, 0.05, 0.05))
    # Green arrow shape
    a.disc(ax, ay, 12, LED_GREEN)
    a.rect(ax - 4, ay - 14, 8, 20, LED_GREEN)
    a.noise(x, y, w, h, 0.015)

    # 2. Brushed Stainless Steel Barrier Sides (R_STEEL_BARRIER)
    x, y, w, h = R_STEEL_BARRIER
    a.rect(x, y, w, h, STEEL_BRUSHED)
    # Horizontal brushed grain texture
    for sy in range(y, y + h, 8):
        a.rect(x, sy, w, 2, STEEL_DARK)
        a.rect(x, sy + 2, w, 1, (0.88, 0.90, 0.92))
    # Maintenance keyhole & recessed access door
    a.rect(x + 20, y + 30, w - 40, h - 60, (0.70, 0.72, 0.75))
    a.rect(x + 22, y + 32, w - 44, h - 64, STEEL_BRUSHED)
    a.disc(x + w // 2, y + h - 40, 6, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 3. Orange Gate Paddle Wings (R_GATE_PADDLE)
    x, y, w, h = R_GATE_PADDLE
    a.rect(x, y, w, h, PADDLE_ORANGE)
    # Translucent glass / rubber safety edge
    a.rect(x + 6, y + 6, w - 12, h - 12, (0.98, 0.55, 0.15))
    a.rect(x + w - 16, y, 16, h, (0.15, 0.15, 0.15))  # black rubber bumper
    a.noise(x, y, w, h, 0.015)

    # 4. Station Concourse Floor (R_CONCOURSE_TILE)
    x, y, w, h = R_CONCOURSE_TILE
    a.rect(x, y, w, h, FLOOR_TERRAZZO)
    for fy in range(y, y + h, 32):
        a.rect(x, fy, w, 2, (0.50, 0.50, 0.52))
    for fx in range(x, x + w, 32):
        a.rect(fx, y, 2, h, (0.50, 0.50, 0.52))
    # Yellow hazard safety strip
    a.rect(x, y + 16, w, 8, (0.95, 0.85, 0.10))
    a.noise(x, y, w, h, 0.03)

    # 5. Smoked Glass Top (R_GLASS_TOP)
    x, y, w, h = R_GLASS_TOP
    a.rect(x, y, w, h, GLASS_SMOKED)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 6. Red Cross LED Display (R_RED_CROSS_LED)
    x, y, w, h = R_RED_CROSS_LED
    a.rect(x, y, w, h, (0.05, 0.05, 0.05))
    # Red X cross
    for step in range(-24, 25, 4):
        a.disc(x + w // 2 + step, y + h // 2 + step, 5, LED_RED)
        a.disc(x + w // 2 + step, y + h // 2 - step, 5, LED_RED)
    a.noise(x, y, w, h, 0.015)

    # 7. Ticket Feeder Slot (R_TICKET_SLOT)
    x, y, w, h = R_TICKET_SLOT
    a.rect(x, y, w, h, STEEL_BRUSHED)
    a.rect(x + 10, y + h // 2 - 4, w - 20, 8, (0.1, 0.1, 0.1))
    a.disc(x + w // 2, y + h // 2 + 16, 6, LED_GREEN)
    a.noise(x, y, w, h, 0.015)

    # 8. Stainless Trim (R_STAINLESS_TRIM)
    x, y, w, h = R_STAINLESS_TRIM
    a.rect(x, y, w, h, (0.85, 0.87, 0.90))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_tube_turnstile_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_GLASS_TOP, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CONCOURSE_TILE, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_turnstile_atlas()
    mat = material_for(img, "mat_tube_turnstile")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London Underground Oyster Card Fare Gate Turnstiles (3.6m x 2.0m Footprint)
    # - 4 Stainless Steel Pedestals forming 3 Gate Aisles (Width 0.35m, Length 1.80m, Height 1.05m)
    # - Angled Top Reader Pods with Yellow Oyster Target & Green LED Display
    # - 3 Pairs of Orange Retractable Paddle Barrier Wings
    # - Station Concourse Floor Base (3.8m x 2.2m)
    # =========================================================================

    # 1. Station Concourse Floor Base (3.8m x 2.2m, Z = 0.00 to 0.10m)
    register_box("TurnstileFloor", 3.80, 2.20, 0.10, (0.0, 0.0, 0.0),
                 front=R_CONCOURSE_TILE, sides=R_CONCOURSE_TILE, top=R_CONCOURSE_TILE)

    # 2. 4 Stainless Steel Pedestals (X = -1.35m, -0.45m, +0.45m, +1.35m)
    # Aisle width = 0.55m
    ped_xs = [-1.35, -0.45, 0.45, 1.35]
    for i, px in enumerate(ped_xs):
        # Main pedestal cabinet (Width: 0.32m, D: 1.80m, H: 0.95m, Z = 0.10m to 1.05m)
        register_box(f"PedestalBody_{i}", 0.32, 1.80, 0.95, (px, 0.0, 0.10),
                     front=R_STEEL_BARRIER, sides=R_STEEL_BARRIER, back=R_STEEL_BARRIER, top=R_GLASS_TOP)

        # Front Angled Oyster Card Reader Head (Width: 0.30m, D: 0.45m, H: 0.15m, Z = 1.05m to 1.20m)
        register_box(f"OysterHead_{i}", 0.30, 0.45, 0.15, (px, -0.65, 1.05),
                     front=R_OYSTER_PAD, sides=R_STAINLESS_TRIM, top=R_OYSTER_PAD)

    # 3. 3 Sets of Retractable Orange Paddle Barrier Wings (In aisles at X = -0.90m, 0.0m, +0.90m)
    aisle_xs = [-0.90, 0.0, 0.90]
    for i, ax in enumerate(aisle_xs):
        # Left paddle wing
        register_box(f"PaddleLeft_{i}", 0.24, 0.06, 0.70, (ax - 0.12, 0.0, 0.35),
                     front=R_GATE_PADDLE, sides=R_GATE_PADDLE, top=R_GATE_PADDLE)
        # Right paddle wing
        register_box(f"PaddleRight_{i}", 0.24, 0.06, 0.70, (ax + 0.12, 0.0, 0.35),
                     front=R_GATE_PADDLE, sides=R_GATE_PADDLE, top=R_GATE_PADDLE)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Tube_Turnstiles")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_tube_turnstile_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_tube_turnstile.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_tube_turnstile.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_tube_turnstile_preview.png")
        shutil.copy2(OUT_DIR / "prop_tube_turnstile_atlas.png", TOOLS_OUT_DIR / "prop_tube_turnstile_atlas.png")
    except Exception as e:
        print(f"[prop_tube_turnstile] note: {e}")

    print("[prop_tube_turnstile] generation complete.")


main()
