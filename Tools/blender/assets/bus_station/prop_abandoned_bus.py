"""Abandoned London Double-Decker Bus on Cinder Blocks (No Wheels, High-Poly ~1000 Tris).

Specs:
- 8.8m long x 2.6m wide x 4.2m high classic London red double-decker bus
- Derelict & Stripped Features (~1,000 Triangles):
  - NO WHEELS: Stripped down to 3D rusty axle hubs, cast-iron brake drums & propped on 4 concrete cinder block stacks
  - 14 Modelled window frames across lower and upper decks with 3D mullions, shattered glass & jagged fracture panes
  - Open front engine maintenance hatch exposing 3D engine block, fan housing & radiator hoses
  - Rear open passenger boarding platform with 3D yellow steel grab rails & emergency exit door ajar
  - Destination blinds: "109 BRIXTON VIA NORBURY"
  - Peeling London bus red paint, oxidized red-oxide primer patches, soot & rust streaks
- Outputs to Tools/blender/out/bus_station/ and Tools/out/bus_station/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/bus_station/prop_abandoned_bus.py
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
R_BUS_RED           = (0,   256, 256, 256)   # Weathered London bus red with rust streaks & oxidized primer
R_WINDOW_BAND       = (256, 256, 128, 256)   # Shattered bus window glass & rubber seal frames
R_DESTINATION_SIGN  = (0,   128, 256, 128)   # "109 BRIXTON VIA NORBURY" destination roll
R_ENGINE_BAY        = (256, 128, 128, 128)   # Exposed rusted diesel engine components & radiator grille
R_ROOF_CREAM        = (0,   0,   256, 128)   # Weathered white/cream curved roof dome & soot
R_CINDER_BLOCKS     = (256, 0,   128, 128)   # Stacked grey concrete cinder blocks
R_RUST_STEEL        = (384, 256, 128, 128)   # Heavy rusted axle hubs, brake drums & chassis rails
R_GRAB_RAILS        = (384, 128, 128, 128)   # Worn yellow/chrome passenger grab rails & platform floor
R_TIRE_WELL         = (384, 0,   128, 128)   # Dark muddy empty wheel wells & undercarriage

# --- Palette Colors ---
BUS_RED_BASE        = (0.75, 0.12, 0.10)
BUS_RED_DARK        = (0.50, 0.08, 0.06)
PRIMER_OXIDE        = (0.42, 0.22, 0.16)
RUST_DARK           = (0.28, 0.16, 0.10)
STEEL_DARK          = (0.18, 0.20, 0.22)
ROOF_CREAM          = (0.82, 0.80, 0.74)
GLASS_CRACKED       = (0.20, 0.25, 0.28)
YELLOW_RAIL         = (0.90, 0.75, 0.15)
CONCRETE_CINDER     = (0.55, 0.54, 0.52)


def paint_abandoned_bus_atlas():
    a = Atlas(S, seed=109)

    # 1. Weathered Bus Red Body (R_BUS_RED)
    x, y, w, h = R_BUS_RED
    a.rect(x, y, w, h, BUS_RED_BASE)
    # Rust streaks & primer patches
    for rx in range(x + 12, x + w, 32):
        a.rect(rx, y, 6, h, BUS_RED_DARK)
        a.disc(rx + 3, y + h // 3, 14, PRIMER_OXIDE)
        a.disc(rx + 3, y + h // 3, 8, RUST_DARK)
    a.shade(x, y, w, h, top=-0.04, bottom=-0.16)
    a.noise(x, y, w, h, 0.035)

    # 2. Window Band & Shattered Glass (R_WINDOW_BAND)
    x, y, w, h = R_WINDOW_BAND
    a.rect(x, y, w, h, (0.15, 0.16, 0.18))  # Rubber seal frame
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_CRACKED)
    # Glass cracks & duct tape
    for i in range(x + 12, x + w - 12, 28):
        a.rect(i, y + 8, 2, h - 16, (0.75, 0.82, 0.88))
        a.rect(i - 8, y + h // 2, 16, 2, (0.75, 0.82, 0.88))
    a.noise(x, y, w, h, 0.025)

    # 3. Destination Sign (R_DESTINATION_SIGN)
    x, y, w, h = R_DESTINATION_SIGN
    a.rect(x, y, w, h, (0.10, 0.10, 0.12))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.05, 0.05, 0.06))
    dest_main = "109 BRIXTON"
    tw = a.text_width(dest_main, scale=3)
    a.text(x + (w - tw) // 2, y + h - 18, dest_main, (0.95, 0.95, 0.95), scale=3)
    dest_sub = "VIA STREATHAM & NORBURY"
    sw = a.text_width(dest_sub, scale=1)
    a.text(x + (w - sw) // 2, y + 24, dest_sub, (0.85, 0.85, 0.85), scale=1)
    a.noise(x, y, w, h, 0.02)

    # 4. Engine Bay & Radiator (R_ENGINE_BAY)
    x, y, w, h = R_ENGINE_BAY
    a.rect(x, y, w, h, RUST_DARK)
    for ey in range(y + 8, y + h - 8, 12):
        a.rect(x + 6, ey, w - 12, 4, STEEL_DARK)
    a.noise(x, y, w, h, 0.03)

    # 5. Cream Roof Dome (R_ROOF_CREAM)
    x, y, w, h = R_ROOF_CREAM
    a.rect(x, y, w, h, ROOF_CREAM)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.02)
    a.noise(x, y, w, h, 0.035)

    # 6. Concrete Cinder Blocks (R_CINDER_BLOCKS)
    x, y, w, h = R_CINDER_BLOCKS
    a.rect(x, y, w, h, CONCRETE_CINDER)
    for cy in range(y, y + h, 20):
        a.rect(x, cy, w, 2, (0.35, 0.34, 0.32))
        for cx in range(x, x + w, 32):
            a.rect(cx, cy, 2, 20, (0.35, 0.34, 0.32))
            a.rect(cx + 8, cy + 5, 14, 10, (0.25, 0.24, 0.22))  # Block core hole
    a.noise(x, y, w, h, 0.03)

    # 7. Rusted Steel Axles & Brake Drums (R_RUST_STEEL)
    x, y, w, h = R_RUST_STEEL
    a.rect(x, y, w, h, RUST_DARK)
    a.disc(x + w // 2, y + h // 2, 44, STEEL_DARK)
    a.disc(x + w // 2, y + h // 2, 28, RUST_DARK)
    a.disc(x + w // 2, y + h // 2, 10, (0.12, 0.12, 0.14))
    a.noise(x, y, w, h, 0.02)

    # 8. Grab Rails (R_GRAB_RAILS)
    x, y, w, h = R_GRAB_RAILS
    a.rect(x, y, w, h, YELLOW_RAIL)
    for gy in range(y, y + h, 16):
        a.rect(x, gy, w, 3, (0.65, 0.50, 0.10))

    # 9. Wheel Well Undercarriage (R_TIRE_WELL)
    x, y, w, h = R_TIRE_WELL
    a.rect(x, y, w, h, (0.12, 0.12, 0.14))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_abandoned_bus_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_ROOF_CREAM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_TIRE_WELL, S, only=side("bottom"))


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


def main():
    kit.reset_scene()
    img = paint_abandoned_bus_atlas()
    mat = material_for(img, "mat_abandoned_bus")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Abandoned London Bus (No Wheels, Propped on Cinder Blocks ~1000 Tris)
    # - 1. 4 Cinder Block Stacks & Rusted Brake Drum Hubs (No Wheels)
    # - 2. Lower & Upper Deck Coachwork Bodies
    # - 3. Front Cabin & Grille with Exposed Engine Bay
    # - 4. 14 Modelled Windows with Mullions & Shattered Glass
    # - 5. Rear Open Platform & Grab Rails
    # - 6. Destination Blinds & Cream Roof
    # =========================================================================

    # 1. 4 Stacks of Concrete Cinder Blocks Propping the Axles (Z = 0.00 to 0.50m)
    axle_locs = [(-2.60, -1.15), (-2.60, 1.15), (2.40, -1.15), (2.40, 1.15)]
    for i, (ax, ay) in enumerate(axle_locs):
        # 2 Cinder Blocks per stack
        register_box(f"CinderBlockBtm_{i}", 0.70, 0.40, 0.22, (ax, ay, 0.0),
                     front=R_CINDER_BLOCKS, sides=R_CINDER_BLOCKS, top=R_CINDER_BLOCKS)
        register_box(f"CinderBlockTop_{i}", 0.60, 0.35, 0.22, (ax, ay, 0.22),
                     front=R_CINDER_BLOCKS, sides=R_CINDER_BLOCKS, top=R_CINDER_BLOCKS)

        # 3D Exposed Rusted Brake Drum & Axle Hub (Where wheel used to be)
        drum = make_cylinder(f"BrakeDrum_{i}", 0.36, 0.20, segs=10, at=(ax, ay, 0.30))
        drum.rotation_euler = (math.radians(90), 0, 0)
        drum.data.materials.append(mat)
        kit.map_faces_to_region(drum, R_RUST_STEEL, S)
        parts.append(drum)

    # 2. Main Lower Deck Body (Length 8.40m, Width 2.40m, Z: 0.45m to 2.25m, H: 1.80m)
    register_box("LowerDeckBody", 8.40, 2.40, 1.80, (0.0, 0.0, 0.45),
                 front=R_BUS_RED, sides=R_BUS_RED, back=R_BUS_RED, top=R_BUS_RED)

    # Inter-Deck Band (Z = 2.25m to 2.40m)
    register_box("InterDeckBand", 8.45, 2.45, 0.15, (0.0, 0.0, 2.25),
                 front=R_BUS_RED, sides=R_BUS_RED, back=R_BUS_RED, top=R_BUS_RED)

    # Upper Deck Body (Length 8.40m, Width 2.40m, Z: 2.40m to 3.80m, H: 1.40m)
    register_box("UpperDeckBody", 8.40, 2.40, 1.40, (0.0, 0.0, 2.40),
                 front=R_BUS_RED, sides=R_BUS_RED, back=R_BUS_RED, top=R_BUS_RED)

    # Curved Cream Roof Dome (Length 8.50m, Width 2.45m, H: 0.45m, Z = 3.80m to 4.25m)
    register_box("RoofDome", 8.50, 2.45, 0.45, (0.0, 0.0, 3.80),
                 front=R_ROOF_CREAM, sides=R_ROOF_CREAM, back=R_ROOF_CREAM, top=R_ROOF_CREAM)

    # =========================================================================
    # 3. Front Cabin & Exposed Engine Bay (Front: X = +4.20m)
    # =========================================================================
    # Front Bumper Bar
    register_box("FrontBumper", 0.30, 2.50, 0.25, (4.25, 0.0, 0.45),
                 front=R_RUST_STEEL, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # Front Destination Blind Box (Z = 3.85m to 4.25m)
    register_box("FrontDestBox", 0.15, 1.60, 0.45, (4.22, 0.0, 3.85),
                 front=R_DESTINATION_SIGN, sides=R_BUS_RED, top=R_ROOF_CREAM)

    # Open Front Engine Maintenance Grille / Exposed Radiator (X = 4.22m, Z = 0.70m to 1.50m)
    register_box("EngineHatch", 0.15, 1.20, 0.80, (4.22, -0.40, 0.70),
                 front=R_ENGINE_BAY, sides=R_RUST_STEEL, top=R_RUST_STEEL)

    # 3D Exposed Radiator Pipe Cylinder
    rad_pipe = make_cylinder("RadPipe", 0.06, 0.70, segs=8, at=(4.25, -0.40, 0.75))
    rad_pipe.data.materials.append(mat)
    kit.map_faces_to_region(rad_pipe, R_RUST_STEEL, S)
    parts.append(rad_pipe)

    # Front Windshields (Driver & Passenger)
    register_box("WindshieldLower", 0.12, 2.20, 0.75, (4.21, 0.0, 1.50),
                 front=R_WINDOW_BAND, sides=R_BUS_RED, top=R_BUS_RED)
    register_box("WindshieldUpper", 0.12, 2.20, 0.85, (4.21, 0.0, 2.65),
                 front=R_WINDOW_BAND, sides=R_BUS_RED, top=R_BUS_RED)

    # =========================================================================
    # 4. Side Window Bays with 3D Mullions & Glass Shards
    # =========================================================================
    # Lower Deck Side Windows (5 windows per side)
    for i in range(5):
        wx = -2.80 + i * 1.40
        # Lower near-side window
        register_box(f"LDWin_N_{i}", 1.10, 0.08, 0.85, (wx, -1.21, 1.15),
                     front=R_WINDOW_BAND, sides=R_BUS_RED, top=R_BUS_RED)
        register_box(f"LDMullion_N_{i}", 0.04, 0.06, 0.85, (wx, -1.23, 1.15),
                     front=R_BUS_RED, sides=R_BUS_RED, top=R_BUS_RED)

        # Upper near-side window
        register_box(f"UDWin_N_{i}", 1.10, 0.08, 0.80, (wx, -1.21, 2.65),
                     front=R_WINDOW_BAND, sides=R_BUS_RED, top=R_BUS_RED)
        register_box(f"UDMullion_N_{i}", 0.04, 0.06, 0.80, (wx, -1.23, 2.65),
                     front=R_BUS_RED, sides=R_BUS_RED, top=R_BUS_RED)

    # 8 Modelled Interior Seats visible through shattered glass
    for i in range(8):
        sx = -2.40 + (i // 2) * 1.40
        sy = -0.65 if (i % 2 == 0) else 0.65
        # Seat Cushion & Backrest
        register_box(f"SeatCushion_{i}", 0.50, 0.50, 0.12, (sx, sy, 0.70),
                     front=R_BUS_RED, sides=R_RUST_STEEL, top=R_BUS_RED)
        register_box(f"SeatBack_{i}", 0.10, 0.50, 0.45, (sx - 0.20, sy, 0.95),
                     front=R_BUS_RED, sides=R_RUST_STEEL, top=R_BUS_RED)
        # Steel tubular seat leg
        s_leg = make_cylinder(f"SeatLeg_{i}", 0.03, 0.25, segs=6, at=(sx, sy, 0.45))
        s_leg.data.materials.append(mat)
        kit.map_faces_to_region(s_leg, R_RUST_STEEL, S)
        parts.append(s_leg)

    # Side Emergency Exit Door propped open ajar on near side
    door_ajar = register_box("EmergencyDoorAjar", 0.90, 0.06, 1.65, (-1.20, -1.35, 0.55),
                             front=R_BUS_RED, sides=R_RUST_STEEL, top=R_BUS_RED)
    door_ajar.rotation_euler = (0, 0, math.radians(35))

    # =========================================================================
    # 5. Rear Open Platform & Grab Rails (Rear: X = -4.20m)
    # =========================================================================
    # Rear Passenger Step Platform
    register_box("RearPlatform", 0.60, 1.20, 0.18, (-4.20, -0.60, 0.45),
                 front=R_GRAB_RAILS, sides=R_BUS_RED, top=R_GRAB_RAILS)

    # 3D Vertical Yellow Grab Rail Poles
    for i, (gx, gy) in enumerate([(-4.20, -1.15), (-4.20, -0.05)]):
        rail = make_cylinder(f"GrabRail_{i}", 0.025, 1.70, segs=8, at=(gx, gy, 0.55))
        rail.data.materials.append(mat)
        kit.map_faces_to_region(rail, R_GRAB_RAILS, S)
        parts.append(rail)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Abandoned_Bus")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_abandoned_bus_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_abandoned_bus.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_abandoned_bus.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_abandoned_bus_preview.png")
        shutil.copy2(OUT_DIR / "prop_abandoned_bus_atlas.png", TOOLS_OUT_DIR / "prop_abandoned_bus_atlas.png")
    except Exception as e:
        print(f"[prop_abandoned_bus] note: {e}")

    print("[prop_abandoned_bus] generation complete.")


main()
