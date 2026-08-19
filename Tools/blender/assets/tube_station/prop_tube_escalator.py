"""London Underground Escalator Flight & Tunnel Wall (Tube Environment Prop).

Specs:
- 8.0m length x 2.8m width, Height: 4.5m (30-degree incline).
- Pair of 2 deep tube escalator flights (Up & Down):
  - Grooved aluminium moving step treads with yellow hazard safety border lines.
  - Brushed stainless steel balustrade casings with continuous black rubber handrails.
  - Combplate teeth entry & exit plates at top and bottom landings.
  - Curved deep tube tiled tunnel wall with illuminated framed advertising posters.
  - Lower and upper landing concourse floor slabs.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/prop_tube_escalator.py
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
R_ESCAL_STEPS   = (0,   256, 256, 256)   # Grooved aluminium step treads with yellow safety borders
R_BALUSTRADE    = (256, 256, 256, 256)   # Brushed stainless steel balustrade & black rubber handrail
R_TUNNEL_ADS    = (0,   128, 256, 128)   # Tube tunnel tiled wall with framed West End adverts
R_COMBPLATE     = (256, 128, 128, 128)   # Cast iron yellow combplate teeth & access cover
R_LANDING_FLOOR = (384, 128, 128, 128)   # Station concourse floor tiles
R_STAINLESS_TRIM= (0,   0,   256, 128)   # Stainless steel inner decking & uplighting
R_EMERGENCY_STOP= (256, 0,   128, 128)   # Red emergency stop button pedestal & warning sign
R_POSTER_THEATRE= (384, 0,   128, 128)   # Illuminated framed musical theatre poster

# --- Palette Colors ---
ALUM_TREAD      = (0.50, 0.52, 0.55)
ALUM_DARK       = (0.28, 0.30, 0.32)
SAFETY_YELLOW   = (0.95, 0.85, 0.08)
STEEL_BRUSHED   = (0.75, 0.77, 0.80)
HANDRAIL_BLACK  = (0.10, 0.10, 0.12)
TILE_WHITE      = (0.90, 0.90, 0.92)
COMB_YELLOW     = (0.88, 0.75, 0.10)
AD_RED          = (0.85, 0.15, 0.18)


def paint_escalator_atlas():
    a = Atlas(S, seed=3501)

    # 1. Grooved Step Treads (R_ESCAL_STEPS)
    x, y, w, h = R_ESCAL_STEPS
    a.rect(x, y, w, h, ALUM_DARK)
    # Moving grooved cleat lines
    for sy in range(y, y + h, 10):
        a.rect(x, sy, w, 4, ALUM_TREAD)
        a.rect(x, sy + 4, w, 2, (0.70, 0.72, 0.75))
    # Bright Yellow Warning Border on edges
    a.rect(x, y, 16, h, SAFETY_YELLOW)
    a.rect(x + w - 16, y, 16, h, SAFETY_YELLOW)
    for sy in range(y, y + h, 40):
        a.rect(x, sy, w, 4, SAFETY_YELLOW)
    a.noise(x, y, w, h, 0.02)

    # 2. Brushed Balustrade & Rubber Handrail (R_BALUSTRADE)
    x, y, w, h = R_BALUSTRADE
    a.rect(x, y, w, h, STEEL_BRUSHED)
    # Top continuous black rubber handrail band (top 32px)
    a.rect(x, y + h - 36, w, 32, HANDRAIL_BLACK)
    a.rect(x, y + h - 12, w, 6, (0.25, 0.25, 0.28))  # rubber highlight
    # Inner decking glass / brushed panels
    a.rect(x + 10, y + 10, w - 20, h - 56, (0.65, 0.68, 0.72))
    a.rect(x + 12, y + 12, w - 24, h - 60, STEEL_BRUSHED)
    a.noise(x, y, w, h, 0.02)

    # 3. Tunnel Wall with Adverts (R_TUNNEL_ADS)
    x, y, w, h = R_TUNNEL_ADS
    a.rect(x, y, w, h, TILE_WHITE)
    # White subway tiles
    for ty in range(y, y + h, 14):
        a.rect(x, ty, w, 1, (0.75, 0.75, 0.78))
    for tx in range(x, x + w, 28):
        a.rect(tx, y, 1, h, (0.75, 0.75, 0.78))
    # 2 Framed Advertising Posters
    for px in [x + 16, x + 136]:
        a.rect(px, y + 10, 100, h - 20, (0.2, 0.2, 0.22))
        a.rect(px + 4, y + 14, 92, h - 28, AD_RED)
        a.text(px + 10, y + h - 34, "WEST END", (0.98, 0.98, 0.98), scale=1)
        a.disc(px + 46, y + 36, 16, (0.98, 0.85, 0.15))
    a.noise(x, y, w, h, 0.02)

    # 4. Combplate Teeth (R_COMBPLATE)
    x, y, w, h = R_COMBPLATE
    a.rect(x, y, w, h, COMB_YELLOW)
    for cy in range(y, y + h, 8):
        a.rect(x, cy, w, 3, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.025)

    # 5. Landing Concourse Floor (R_LANDING_FLOOR)
    x, y, w, h = R_LANDING_FLOOR
    a.rect(x, y, w, h, (0.64, 0.65, 0.68))
    for fy in range(y, y + h, 28):
        a.rect(x, fy, w, 2, (0.48, 0.48, 0.50))
    a.noise(x, y, w, h, 0.03)

    # 6. Stainless Steel Trim (R_STAINLESS_TRIM)
    x, y, w, h = R_STAINLESS_TRIM
    a.rect(x, y, w, h, (0.80, 0.82, 0.85))
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, (0.50, 0.52, 0.55))
    a.noise(x, y, w, h, 0.02)

    # 7. Emergency Stop Pedestal (R_EMERGENCY_STOP)
    x, y, w, h = R_EMERGENCY_STOP
    a.rect(x, y, w, h, STEEL_BRUSHED)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, (0.95, 0.12, 0.15))  # Red mushroom emergency button
    a.disc(cx, cy, 14, (0.75, 0.08, 0.10))
    a.noise(x, y, w, h, 0.015)

    # 8. Theatre Poster (R_POSTER_THEATRE)
    x, y, w, h = R_POSTER_THEATRE
    a.rect(x, y, w, h, (0.15, 0.45, 0.75))
    a.text(x + 12, y + h - 28, "MUSEUM", (0.98, 0.98, 0.98), scale=2)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_tube_escalator_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_ESCAL_STEPS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_LANDING_FLOOR, S, only=side("bottom"))


def make_wedge_escalator(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = w / 2.0
    verts = [
        (-hw, 0.0, 0.0), (hw, 0.0, 0.0), (hw, d, 0.0), (-hw, d, 0.0),
        (-hw, d, h), (hw, d, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # inclined slope (steps)
        (1, 2, 5),       # right triangle
        (2, 3, 4, 5),    # back vertical wall
        (3, 0, 4),       # left triangle
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_escalator_atlas()
    mat = material_for(img, "mat_tube_escalator")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London Underground Escalator Flight (8.0m Length x 2.8m Width, Height: 4.5m)
    # - Lower Landing Platform Slab (Z: 0.0 to 0.20m)
    # - Inclined Escalator Wedge Flight (Length: 6.0m, Rise: 3.5m)
    # - Pair of 2 Escalators (Left: Up, Right: Down) with Balustrades & Handrails
    # - Upper Landing Concourse Slab (Z: 3.50m to 3.70m)
    # - Flanking Tiled Tunnel Wall with Framed Adverts
    # =========================================================================

    # 1. Lower Landing Concourse Floor (2.8m x 2.0m, Z = 0.00 to 0.20m at Y = -3.0m)
    register_box("LowerLanding", 2.80, 2.00, 0.20, (0.0, -3.00, 0.0),
                 front=R_LANDING_FLOOR, sides=R_LANDING_FLOOR, top=R_COMBPLATE)

    # 2. Upper Landing Concourse Floor (2.8m x 2.0m, Z = 3.50m to 3.70m at Y = +3.0m)
    register_box("UpperLanding", 2.80, 2.00, 0.20, (0.0, 3.00, 3.50),
                 front=R_LANDING_FLOOR, sides=R_LANDING_FLOOR, top=R_COMBPLATE)

    # 3. Pair of 2 Inclined Escalators (Left at X = -0.75m, Right at X = +0.75m, Width: 1.10m, Incline Y = -2.0 to +2.0m)
    for i, ex in enumerate([-0.75, 0.75]):
        # Inclined steps flight (Length 4.0m, Rise 3.5m)
        esc = make_wedge_escalator(f"Escalator_{i}", 1.05, 4.00, 3.50, at=(ex, -2.00, 0.10))
        esc.data.materials.append(mat)
        kit.map_faces_to_region(esc, R_ESCAL_STEPS, S, only=lambda f: f.normal.z > 0.1)
        kit.map_faces_to_region(esc, R_BALUSTRADE, S, only=lambda f: abs(f.normal.x) > 0.6)
        kit.map_faces_to_region(esc, R_LANDING_FLOOR, S, only=lambda f: f.normal.z < -0.5 or f.normal.y > 0.5)
        parts.append(esc)

        # Central / outer balustrade handrails
        register_box(f"BalustradeL_{i}", 0.10, 4.20, 0.85, (ex - 0.50, 0.0, 1.80),
                     front=R_BALUSTRADE, sides=R_BALUSTRADE, top=R_BALUSTRADE)
        register_box(f"BalustradeR_{i}", 0.10, 4.20, 0.85, (ex + 0.50, 0.0, 1.80),
                     front=R_BALUSTRADE, sides=R_BALUSTRADE, top=R_BALUSTRADE)

    # 4. Tiled Tunnel Wall with Advertising Posters (Left side at X = -1.50m, D: 8.0m, H: 4.5m)
    register_box("TunnelSideWall", 0.25, 8.00, 4.50, (-1.45, 0.0, 0.0),
                 front=R_TUNNEL_ADS, sides=R_TUNNEL_ADS, top=R_LANDING_FLOOR)

    # 5. Emergency Stop Button Pedestals (At bottom landing, X = -0.75m, +0.75m, Y = -2.2m)
    register_box("StopPedestalL", 0.20, 0.20, 0.80, (-0.75, -2.20, 0.20),
                 front=R_EMERGENCY_STOP, sides=R_EMERGENCY_STOP, top=R_EMERGENCY_STOP)
    register_box("StopPedestalR", 0.20, 0.20, 0.80, (0.75, -2.20, 0.20),
                 front=R_EMERGENCY_STOP, sides=R_EMERGENCY_STOP, top=R_EMERGENCY_STOP)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Tube_Escalator")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_tube_escalator_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_tube_escalator.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_tube_escalator.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_tube_escalator_preview.png")
        shutil.copy2(OUT_DIR / "prop_tube_escalator_atlas.png", TOOLS_OUT_DIR / "prop_tube_escalator_atlas.png")
    except Exception as e:
        print(f"[prop_tube_escalator] note: {e}")

    print("[prop_tube_escalator] generation complete.")


main()
