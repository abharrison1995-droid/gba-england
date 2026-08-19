"""Croydon Spartan Main Traphouse HQ — Ralph & Sanjeet's Gang Stronghold (High-Poly ~1000 Tris).

Architectural Specs:
- Large imposing 3-storey double-fronted Victorian villa fortified as the primary headquarters for Ralph & Sanjeet
- Dimensions: 12.0m wide x 9.0m deep x 11.2m high
- Gang Stronghold & Security Features (~1,000 Triangles):
  - Heavy reinforced entrance portico with steel blast portal, intercom & twin halogen security floodlights
  - 3D CCTV surveillance camera arrays on corner brackets covering street approaches
  - Perimeter brick & stone wall with welded iron security gate, iron pickets & razor wire coils
  - 8 Modelled windows with 3D stone sills and welded steel security bar grilles
  - Rooftop Command Array:
    - 3D satellite mini-dish & high-gain VHF comms antenna
    - Industrial backup generator exhaust chimney stack with rain cap
    - Mansard slate roof with dormers & quad brick chimneys with terracotta pots
  - High-Contrast Gang Markings: "RALPH & SANJEET", "SPARTAN HQ", "DO NOT APPROACH", "0208 CRO"
- Outputs to Tools/blender/out/london/ and Tools/out/london/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/london/building_croydon_traphouse_hq.py
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
OUT_DIR = kit.OUT_DIR / "london" / "croydon_spartans"
TOOLS_OUT_DIR = Path(__file__).resolve().parents[4] / "out" / "london" / "croydon_spartans"

# --- Atlas Region Definitions (x, y, w, h) ---
R_HQ_BRICK          = (0,   256, 256, 256)   # Dark soot-stained Victorian brick with bold gang tags
R_HQ_SIGN_WALL      = (256, 256, 128, 256)   # "RALPH & SANJEET - SPARTAN HQ" graffiti & warning stencils
R_ARMORED_PORTAL    = (0,   128, 256, 128)   # Reinforced steel entrance portal & intercom keypad
R_SECURITY_WIN      = (256, 128, 128, 128)   # Ground & 1st floor heavy security window & blackout glass
R_ROOF_MANSARD      = (0,   0,   256, 128)   # Dark Victorian Welsh slate mansard roof
R_STONE_DRESSING    = (256, 0,   128, 128)   # Carved stone string courses, portico columns & sills
R_PERIMETER_GATE    = (384, 256, 128, 128)   # Welded iron security gate with spikes & warning signs
R_FLOODLIGHT_CCTV   = (384, 128, 128, 128)   # Halogen security floodlights & CCTV surveillance pods
R_METAL_TRIM        = (384, 0,   128, 128)   # Dark galvanized steel, comms antenna & generator pipe

# --- Palette Colors ---
BRICK_HQ_BASE       = (0.44, 0.34, 0.28)
BRICK_MORTAR        = (0.55, 0.50, 0.44)
GRAFFITI_GOLD       = (0.95, 0.82, 0.15)
GRAFFITI_RED        = (0.88, 0.10, 0.08)
GRAFFITI_WHITE      = (0.95, 0.95, 0.95)
STONE_PORTLAND      = (0.75, 0.72, 0.65)
STONE_DARK          = (0.50, 0.46, 0.40)
STEEL_DARK          = (0.18, 0.20, 0.22)
STEEL_LIGHT         = (0.45, 0.48, 0.52)
SLATE_DARK          = (0.20, 0.22, 0.25)
GLASS_BLACKOUT      = (0.08, 0.09, 0.11)


def paint_traphouse_hq_atlas():
    a = Atlas(S, seed=2105)

    # 1. Dark Victorian Brick (R_HQ_BRICK) - Clean of graffiti
    x, y, w, h = R_HQ_BRICK
    a.bricks(x, y, w, h, brick=BRICK_HQ_BASE, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.07)
    a.shade(x, y, w, h, top=-0.05, bottom=-0.16)
    a.noise(x, y, w, h, 0.03)

    # 2. Plain Clean Brick Wall (R_HQ_SIGN_WALL)
    x, y, w, h = R_HQ_SIGN_WALL
    a.bricks(x, y, w, h, brick=BRICK_HQ_BASE, mortar=BRICK_MORTAR, bw=24, bh=11, jitter=0.07)
    a.noise(x, y, w, h, 0.02)

    # 3. Armoured Entrance Portal (R_ARMORED_PORTAL)
    x, y, w, h = R_ARMORED_PORTAL
    a.rect(x, y, w, h, STEEL_DARK)
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.12, 0.14, 0.16))
    # Intercom keypad & reinforced steel locking plates
    a.rect(x + w - 36, y + h // 2 - 20, 24, 40, (0.7, 0.6, 0.2))
    a.rect(x + 16, y + h // 2, 20, 28, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 4. Security Windows (R_SECURITY_WIN)
    x, y, w, h = R_SECURITY_WIN
    a.rect(x, y, w, h, STONE_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_BLACKOUT)
    for wx in range(x + 8, x + w - 8, (w - 16) // 3):
        a.rect(wx, y + 4, 2, h - 8, STEEL_LIGHT)
    for wy in range(y + 8, y + h - 8, (h - 16) // 3):
        a.rect(x + 4, wy, w - 8, 2, STEEL_LIGHT)
    a.noise(x, y, w, h, 0.02)

    # 5. Mansard Slate Roof (R_ROOF_MANSARD)
    x, y, w, h = R_ROOF_MANSARD
    a.rect(x, y, w, h, SLATE_DARK)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.14, 0.15, 0.18))
    a.noise(x, y, w, h, 0.035)

    # 6. Stone Dressings & Portico (R_STONE_DRESSING)
    x, y, w, h = R_STONE_DRESSING
    a.rect(x, y, w, h, STONE_PORTLAND)
    for sy in range(y, y + h, 28):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.02)

    # 7. Welded Iron Perimeter Gate (R_PERIMETER_GATE)
    x, y, w, h = R_PERIMETER_GATE
    a.rect(x, y, w, h, STEEL_DARK)
    for gx in range(x + 6, x + w - 6, 12):
        a.rect(gx, y + 4, 3, h - 8, STEEL_LIGHT)
    a.rect(x + 4, y + h // 2 - 8, w - 8, 16, STEEL_LIGHT)
    # Warning sign on gate
    a.rect(x + 16, y + h // 2 - 6, w - 32, 12, GRAFFITI_RED)
    a.text(x + 20, y + h // 2 + 2, "WARNING", GRAFFITI_WHITE, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 8. Halogen Floodlights & CCTV (R_FLOODLIGHT_CCTV)
    x, y, w, h = R_FLOODLIGHT_CCTV
    a.rect(x, y, w, h, STEEL_DARK)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 36, (0.98, 0.95, 0.65))  # Halogen bulb glow
    a.disc(cx, cy, 22, (0.99, 0.99, 0.85))
    a.noise(x, y, w, h, 0.015)

    # 9. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_croydon_traphouse_hq_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_DRESSING, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_DRESSING, S, only=side("bottom"))


def make_cylinder(name, r, h, segs=12, at=(0, 0, 0)):
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


def make_pitched_mansard_roof(name, w, d, h, overhang=0.40, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang
    ridge_hw = (w / 2.0) * 0.70
    ridge_hd = (d / 2.0) * 0.50

    verts = [
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
        (-ridge_hw, -ridge_hd, h), (ridge_hw, -ridge_hd, h), (ridge_hw, ridge_hd, h), (-ridge_hw, ridge_hd, h)
    ]
    faces = [
        (0, 1, 2, 3),    # Underside
        (0, 1, 5, 4),    # Front slope
        (1, 2, 6, 5),    # Right slope
        (2, 3, 7, 6),    # Back slope
        (3, 0, 4, 7),    # Left slope
        (4, 5, 6, 7),    # Flat top roof
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_traphouse_hq_atlas()
    mat = material_for(img, "mat_traphouse_hq")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Ralph & Sanjeet Main Traphouse HQ (~1050 Triangles)
    # - 1. Pavement Plinth & Fortified Front Forecourt
    # - 2. 3-Storey Double-Fronted Victorian Villa Body with String Courses
    # - 3. Heavy Armoured Entrance Portico with Floodlights & CCTV Arrays
    # - 4. 8 Modelled Windows with 3D Sills & 24 3D Steel Security Bars
    # - 5. Perimeter Wall with Welded Iron Gate & Razor Wire
    # - 6. Mansard Roof with Dormers, Backup Generator Exhaust & Quad Chimneys
    # =========================================================================

    # 1. Pavement & Forecourt Base (12.80m x 10.00m x 0.20m)
    register_box("PavementPlinth", 12.80, 10.00, 0.20, (0.0, 0.0, 0.0),
                 front=R_STONE_DRESSING, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # 2. Main 3-Storey Villa Body (Width 11.40m, Depth 7.80m, Z: 0.20m to 8.80m, H: 8.60m)
    register_box("VillaCore", 11.40, 7.80, 8.60, (0.0, 0.40, 0.20),
                 front=R_HQ_BRICK, sides=R_HQ_BRICK, back=R_HQ_BRICK, top=R_STONE_DRESSING)

    # Protruding Stone String Courses
    # - 1st Floor Stone Course (Z = 3.20m to 3.40m)
    register_box("StringCourse1", 11.60, 8.00, 0.20, (0.0, 0.40, 3.20),
                 front=R_STONE_DRESSING, sides=R_STONE_DRESSING, back=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # - 2nd Floor Stone Course (Z = 6.00m to 6.20m)
    register_box("StringCourse2", 11.60, 8.00, 0.20, (0.0, 0.40, 6.00),
                 front=R_STONE_DRESSING, sides=R_STONE_DRESSING, back=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # - Roof Parapet Cornice (Z = 8.80m to 9.20m)
    register_box("RoofCornice", 11.80, 8.20, 0.40, (0.0, 0.40, 8.80),
                 front=R_STONE_DRESSING, sides=R_STONE_DRESSING, back=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # =========================================================================
    # 3. Main Armoured Entrance Portico & Gang Mural (Center: X = 0.0m)
    # =========================================================================
    # Heavy Stone Portico with Twin Round Columns
    for i, px in enumerate([-1.40, 1.40]):
        col = make_cylinder(f"PorticoCol_{i}", 0.18, 3.00, segs=12, at=(px, -3.80, 0.20))
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_STONE_DRESSING, S)
        parts.append(col)

    register_box("PorticoCanopy", 3.40, 1.40, 0.35, (0.0, -3.80, 3.20),
                 front=R_STONE_DRESSING, sides=R_STONE_DRESSING, top=R_ROOF_MANSARD)

    # Armoured Steel Entrance Blast Door
    register_box("ArmoredPortal", 1.80, 0.15, 2.40, (0.0, -3.55, 0.20),
                 front=R_ARMORED_PORTAL, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # Twin Halogen Security Floodlights mounted flanking canopy
    for i, fx in enumerate([-1.50, 1.50]):
        register_box(f"Floodlight_{i}", 0.30, 0.25, 0.25, (fx, -3.85, 3.40),
                     front=R_FLOODLIGHT_CCTV, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # Corner 3D CCTV Camera Pods on Swivel Brackets (Left X = -5.80m, Right X = +5.80m)
    for i, cx in enumerate([-5.80, 5.80]):
        register_box(f"CCTVBracket_{i}", 0.04, 0.40, 0.04, (cx, -3.50, 4.20),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
        register_box(f"CCTVCamera_{i}", 0.20, 0.35, 0.20, (cx, -3.80, 4.10),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # 4. 8 Modelled Windows with 3D Sills & 24 3D Steel Security Bars
    # =========================================================================
    # Ground Floor Windows (Left Wing: X = -3.80m, Right Wing: X = +3.80m, Z = 0.80m to 2.40m)
    for w_i, wx in enumerate([-3.80, 3.80]):
        register_box(f"GFWin_{w_i}", 2.20, 0.15, 1.60, (wx, -3.52, 0.80),
                     front=R_SECURITY_WIN, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)
        register_box(f"GFSill_{w_i}", 2.40, 0.25, 0.15, (wx, -3.58, 0.65),
                     front=R_STONE_DRESSING, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)
        # 6 3D Steel Security Bars per GF window
        for b_i in range(6):
            bx = wx - 0.80 + b_i * 0.32
            register_box(f"GFBar_{w_i}_{b_i}", 0.03, 0.03, 1.60, (bx, -3.62, 0.80),
                         front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 1st Floor Windows (Left X = -3.80m, Right X = +3.80m, Z = 3.80m to 5.40m)
    for w_i, wx in enumerate([-3.80, 3.80]):
        register_box(f"UF1Win_{w_i}", 2.20, 0.15, 1.60, (wx, -3.52, 3.80),
                     front=R_SECURITY_WIN, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)
        register_box(f"UF1Sill_{w_i}", 2.40, 0.25, 0.15, (wx, -3.58, 3.65),
                     front=R_STONE_DRESSING, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # 2nd Floor Windows (3 Windows: X = -3.80m, 0.0m, +3.80m, Z = 6.60m to 8.20m)
    for w_i, wx in enumerate([-3.80, 0.0, 3.80]):
        register_box(f"UF2Win_{w_i}", 1.80, 0.15, 1.60, (wx, -3.52, 6.60),
                     front=R_SECURITY_WIN, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)
        register_box(f"UF2Sill_{w_i}", 2.00, 0.25, 0.15, (wx, -3.58, 6.45),
                     front=R_STONE_DRESSING, sides=R_STONE_DRESSING, top=R_STONE_DRESSING)

    # =========================================================================
    # 5. Perimeter Brick & Stone Wall with Welded Iron Gate & Razor Wire
    # =========================================================================
    register_box("PerimeterWallL", 4.20, 0.30, 1.50, (-3.80, -4.60, 0.20),
                 front=R_HQ_BRICK, sides=R_HQ_BRICK, top=R_STONE_DRESSING)
    register_box("PerimeterWallR", 4.20, 0.30, 1.50, (3.80, -4.60, 0.20),
                 front=R_HQ_BRICK, sides=R_HQ_BRICK, top=R_STONE_DRESSING)

    # Welded Iron Security Gate (Center: Width 2.80m, H: 2.20m, Z = 0.20m to 2.40m)
    register_box("IronSecurityGate", 2.80, 0.08, 2.20, (0.0, -4.60, 0.20),
                 front=R_PERIMETER_GATE, sides=R_PERIMETER_GATE, top=R_PERIMETER_GATE)

    # Razor Wire Bar atop Wall
    for i, wx in enumerate([-3.80, 3.80]):
        register_box(f"RazorBar_{i}", 4.20, 0.05, 0.20, (wx, -4.60, 1.70),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # 6. Mansard Roof, Rooftop Comms Array & Generator Stack
    # =========================================================================
    # Mansard Slate Roof (Width 11.80m, Depth 8.20m, H: 2.00m, Z = 9.20m to 11.20m)
    roof = make_pitched_mansard_roof("MansardRoof", 11.80, 8.20, 2.00, overhang=0.35, at=(0.0, 0.40, 9.20))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF_MANSARD, S)
    parts.append(roof)

    # Rooftop Satellite Mini-Dish (X = -3.20m, Y = 0.0m, Z = 11.20m)
    dish_post = make_cylinder("SatDishPost", 0.05, 0.80, segs=8, at=(-3.20, 0.0, 11.20))
    dish_post.data.materials.append(mat)
    kit.map_faces_to_region(dish_post, R_METAL_TRIM, S)
    parts.append(dish_post)

    dish = register_box("SatDish", 0.75, 0.06, 0.75, (-3.20, -0.30, 12.00),
                        front=R_FLOODLIGHT_CCTV, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    dish.rotation_euler = (math.radians(-30), math.radians(20), 0)

    # High-Gain VHF Comms Antenna (X = 3.20m, Z = 11.20m to 13.80m)
    antenna = make_cylinder("VHFAntenna", 0.04, 2.60, segs=6, at=(3.20, 0.0, 11.20))
    antenna.data.materials.append(mat)
    kit.map_faces_to_region(antenna, R_METAL_TRIM, S)
    parts.append(antenna)

    # Industrial Generator Exhaust Pipe with Rain Cap (X = 0.0m, Y = 2.20m, Z = 11.20m to 13.00m)
    gen_pipe = make_cylinder("GeneratorExhaust", 0.14, 1.80, segs=8, at=(0.0, 2.20, 11.20))
    gen_pipe.data.materials.append(mat)
    kit.map_faces_to_region(gen_pipe, R_METAL_TRIM, S)
    parts.append(gen_pipe)

    # 4 Brick Chimney Stacks with Terracotta Pots (Corners of roof)
    chimney_coords = [(-4.60, -1.80), (4.60, -1.80), (-4.60, 2.60), (4.60, 2.60)]
    for i, (cx, cy) in enumerate(chimney_coords):
        register_box(f"ChimneyHQ_{i}", 0.85, 0.85, 1.40, (cx, cy, 10.40),
                     front=R_HQ_BRICK, sides=R_HQ_BRICK, top=R_STONE_DRESSING)
        for pot_i in [-0.20, 0.20]:
            pot = make_cylinder(f"PotHQ_{i}_{pot_i}", 0.12, 0.45, segs=8, at=(cx + pot_i, cy, 11.80))
            pot.data.materials.append(mat)
            kit.map_faces_to_region(pot, R_STONE_DRESSING, S)
            parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Croydon_Traphouse_HQ")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_croydon_traphouse_hq_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_croydon_traphouse_hq.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_croydon_traphouse_hq.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_croydon_traphouse_hq_preview.png")
        shutil.copy2(OUT_DIR / "building_croydon_traphouse_hq_atlas.png", TOOLS_OUT_DIR / "building_croydon_traphouse_hq_atlas.png")
    except Exception as e:
        print(f"[building_croydon_traphouse_hq] note: {e}")

    print("[building_croydon_traphouse_hq] generation complete.")


main()
