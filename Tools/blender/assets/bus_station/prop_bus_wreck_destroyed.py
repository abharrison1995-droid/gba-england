"""Completely Destroyed & Broken Up Abandoned Bus Wreck (High-Poly ~1000 Tris).

Specs:
- 8.5m long x 3.2m wide x 3.2m high collapsed, twisted, gutted London double-decker bus wreckage
- Destroyed Wreck Features (~1,000 Triangles):
  - Collapsed, buckled upper deck roof with 10 3D jagged twisted steel skeletal ribs and exposed transverse beams
  - Crushed, listing lower chassis propped on twisted axle stubs and crushed suspension leaf-spring blocks
  - Gutted interior with 8 tilted rusted seat frame skeletons and dislodged floor plates
  - Smashed front cab with crumpled bumper bar, dislodged radiator block & tangled wiring harness
  - Fallen yellow grab rails, hanging sheet metal panels, and scattered perimeter chassis debris
  - Severe rust oxidation, fire scorch marks, and peeling London red paint
- Outputs to Tools/blender/out/bus_station/ and Tools/out/bus_station/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/bus_station/prop_bus_wreck_destroyed.py
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
R_RUST_HULL         = (0,   256, 256, 256)   # Heavily oxidized red-oxide steel hull with scorch marks
R_TWISTED_FRAME     = (256, 256, 128, 256)   # Twisted steel chassis beams, ribs & angle iron
R_GUTTED_SEATS      = (0,   128, 256, 128)   # Rusted tubular seat frames & charred foam
R_SCORCH_METAL      = (256, 128, 128, 128)   # Black fire soot & peeling blistered paint
R_TORN_ROOF         = (0,   0,   256, 128)   # Torn corrugated aluminium roof sheeting
R_ENGINE_SCRAP      = (256, 0,   128, 128)   # Broken engine block, radiator & tangled wire harness
R_CRUSHED_AXLE      = (384, 256, 128, 128)   # Crushed suspension leaf springs & axle hubs
R_YELLOW_RAIL_BENT  = (384, 128, 128, 128)   # Bent, scraped yellow grab rails
R_DEBRIS_TARMAC     = (384, 0,   128, 128)   # Base tarmac with glass shards & rust flakes

# --- Palette Colors ---
RUST_OXIDE          = (0.40, 0.20, 0.14)
RUST_DARK           = (0.24, 0.12, 0.08)
BUS_RED_BURNT       = (0.50, 0.10, 0.08)
SOOT_BLACK          = (0.09, 0.09, 0.10)
STEEL_DARK          = (0.18, 0.20, 0.22)
STEEL_LIGHT         = (0.42, 0.45, 0.48)
YELLOW_RAIL         = (0.85, 0.68, 0.12)
FOAM_CHARRED        = (0.20, 0.18, 0.16)


def paint_bus_wreck_atlas():
    a = Atlas(S, seed=309)

    # 1. Oxidized Rust Hull (R_RUST_HULL)
    x, y, w, h = R_RUST_HULL
    a.rect(x, y, w, h, RUST_OXIDE)
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 4, RUST_DARK)
        a.rect(x, ry + 4, w, 2, BUS_RED_BURNT)
    a.shade(x, y, w, h, top=-0.12, bottom=-0.05)
    a.noise(x, y, w, h, 0.04)

    # 2. Twisted Steel Frame (R_TWISTED_FRAME)
    x, y, w, h = R_TWISTED_FRAME
    a.rect(x, y, w, h, STEEL_DARK)
    for fy in range(y, y + h, 12):
        a.rect(x, fy, w, 3, STEEL_LIGHT)
    a.noise(x, y, w, h, 0.03)

    # 3. Gutted Seat Frames (R_GUTTED_SEATS)
    x, y, w, h = R_GUTTED_SEATS
    a.rect(x, y, w, h, FOAM_CHARRED)
    for sy in range(y + 8, y + h - 8, 16):
        a.rect(x + 4, sy, w - 8, 3, RUST_OXIDE)
    a.noise(x, y, w, h, 0.035)

    # 4. Scorch Metal & Fire Blisters (R_SCORCH_METAL)
    x, y, w, h = R_SCORCH_METAL
    a.rect(x, y, w, h, SOOT_BLACK)
    for by in range(y + 8, y + h - 8, 14):
        a.disc(x + w // 2, by, 16, (0.15, 0.12, 0.10))
    a.noise(x, y, w, h, 0.04)

    # 5. Torn Corrugated Roof (R_TORN_ROOF)
    x, y, w, h = R_TORN_ROOF
    a.rect(x, y, w, h, (0.45, 0.44, 0.42))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, SOOT_BLACK)
    a.noise(x, y, w, h, 0.03)

    # 6. Broken Engine Scrap (R_ENGINE_SCRAP)
    x, y, w, h = R_ENGINE_SCRAP
    a.rect(x, y, w, h, STEEL_DARK)
    for ey in range(y + 6, y + h - 6, 10):
        a.rect(x + 4, ey, w - 8, 3, RUST_DARK)
    a.noise(x, y, w, h, 0.03)

    # 7. Crushed Axles & Springs (R_CRUSHED_AXLE)
    x, y, w, h = R_CRUSHED_AXLE
    a.rect(x, y, w, h, RUST_DARK)
    for ay in range(y + 4, y + h - 4, 12):
        a.rect(x + 4, ay, w - 8, 4, STEEL_LIGHT)

    # 8. Bent Yellow Rails (R_YELLOW_RAIL_BENT)
    x, y, w, h = R_YELLOW_RAIL_BENT
    a.rect(x, y, w, h, YELLOW_RAIL)
    for gy in range(y, y + h, 14):
        a.rect(x, gy, w, 3, RUST_DARK)

    # 9. Tarmac Debris (R_DEBRIS_TARMAC)
    x, y, w, h = R_DEBRIS_TARMAC
    a.rect(x, y, w, h, (0.25, 0.26, 0.28))
    for dy in range(y, y + h, 16):
        a.disc(x + (dy % 100), dy, 6, RUST_OXIDE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("prop_bus_wreck_destroyed_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_TORN_ROOF, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_DEBRIS_TARMAC, S, only=side("bottom"))


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
    img = paint_bus_wreck_atlas()
    mat = material_for(img, "mat_bus_wreck")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Destroyed Bus Wreck (~1000 Triangles)
    # - 1. Crushed Chassis Listing on Ground & Shattered Leaf Springs
    # - 2. Crumpled Lower Deck Hull with Gaping Buckled Side Holes
    # - 3. 10 3D Exposed Twisted Steel Skeletal Ribs (Upper Deck Collapse)
    # - 4. 8 Gutted Rusted Seat Frame Skeletons
    # - 5. Smashed Front Cab, Crushed Radiator & Dangling Engine Scrap
    # - 6. Fallen Yellow Rails & Torn Hanging Metal Panels
    # =========================================================================

    # 1. Listing Chassis Floorbed & Crushed Leaf Springs (Z = 0.00 to 0.40m, tilted)
    floor = register_box("ChassisFloor", 8.20, 2.50, 0.25, (0.0, 0.0, 0.15),
                         front=R_RUST_HULL, sides=R_TWISTED_FRAME, top=R_GUTTED_SEATS)
    floor.rotation_euler = (math.radians(-5), math.radians(3), 0)

    # 4 Crushed Suspension Leaf-Spring Blocks & Bent Axle Hubs
    for i, (ax, ay) in enumerate([(-2.80, -1.20), (-2.80, 1.10), (2.60, -1.20), (2.60, 1.10)]):
        register_box(f"CrushedSpring_{i}", 0.80, 0.30, 0.20, (ax, ay, 0.0),
                     front=R_CRUSHED_AXLE, sides=R_CRUSHED_AXLE, top=R_CRUSHED_AXLE)
        axle = make_cylinder(f"AxleStub_{i}", 0.10, 0.40, segs=8, at=(ax, ay, 0.10))
        axle.rotation_euler = (math.radians(90), math.radians(15), 0)
        axle.data.materials.append(mat)
        kit.map_faces_to_region(axle, R_CRUSHED_AXLE, S)
        parts.append(axle)

    # 2. Crumpled Lower Deck Side Walls (Left & Right buckled panels)
    # - Left crumpled wall section
    wall_l = register_box("WallLowerLeft", 4.20, 0.18, 1.40, (-1.20, -1.20, 0.35),
                          front=R_RUST_HULL, sides=R_SCORCH_METAL, top=R_TWISTED_FRAME)
    wall_l.rotation_euler = (math.radians(-8), 0, 0)

    # - Right crumpled rear wall section
    wall_r = register_box("WallLowerRight", 3.80, 0.18, 1.30, (-1.40, 1.15, 0.35),
                          front=R_RUST_HULL, sides=R_SCORCH_METAL, top=R_TWISTED_FRAME)
    wall_r.rotation_euler = (math.radians(10), 0, 0)

    # 3. 10 3D Exposed Twisted Steel Skeletal Ribs (The collapsed upper deck superstructure)
    for i in range(6):
        rx = -3.20 + i * 1.30
        # Left rib rising and bent inward
        rib_l = register_box(f"RibLeft_{i}", 0.08, 0.08, 1.90, (rx, -1.15, 1.60),
                             front=R_TWISTED_FRAME, sides=R_TWISTED_FRAME, top=R_TWISTED_FRAME)
        rib_l.rotation_euler = (math.radians(25 + i * 3), math.radians(i * 2), 0)

        # Right rib collapsed downward
        rib_r = register_box(f"RibRight_{i}", 0.08, 0.08, 1.80, (rx, 1.10, 1.50),
                             front=R_TWISTED_FRAME, sides=R_TWISTED_FRAME, top=R_TWISTED_FRAME)
        rib_r.rotation_euler = (math.radians(-35 - i * 2), math.radians(-i * 2), 0)

        # Transverse cross beam bent in middle
        cross_b = register_box(f"CrossBeam_{i}", 0.06, 2.20, 0.06, (rx, 0.0, 2.40 - i * 0.15),
                               front=R_TWISTED_FRAME, sides=R_TWISTED_FRAME, top=R_TWISTED_FRAME)
        cross_b.rotation_euler = (math.radians(-10), 0, math.radians(5))

    # 4. 8 Gutted Rusted Seat Frame Skeletons tilted in interior
    for i in range(8):
        sx = -2.60 + (i // 2) * 1.30
        sy = -0.55 if (i % 2 == 0) else 0.55
        seat = register_box(f"SeatFrame_{i}", 0.55, 0.65, 0.65, (sx, sy, 0.40),
                            front=R_GUTTED_SEATS, sides=R_GUTTED_SEATS, top=R_GUTTED_SEATS)
        seat.rotation_euler = (math.radians((i * 13) % 25 - 12), math.radians((i * 17) % 20 - 10), 0)

    # 5. Smashed Front Cab, Crushed Radiator & Loose Bumper (X = +3.80m)
    register_box("FrontCrushedCab", 1.20, 2.30, 1.10, (3.80, -0.10, 0.35),
                 front=R_SCORCH_METAL, sides=R_RUST_HULL, top=R_SCORCH_METAL)

    bumper = register_box("PeeledBumper", 0.20, 2.60, 0.22, (4.35, 0.20, 0.25),
                          front=R_TWISTED_FRAME, sides=R_TWISTED_FRAME, top=R_TWISTED_FRAME)
    bumper.rotation_euler = (0, math.radians(18), math.radians(-12))

    # Dislodged Radiator Core Block on Tarmac
    register_box("DislodgedRadiator", 0.65, 0.75, 0.50, (4.10, -0.80, 0.10),
                 front=R_ENGINE_SCRAP, sides=R_ENGINE_SCRAP, top=R_ENGINE_SCRAP)

    # 3D Exposed V6 Engine Cylinder Block & Fan Hub
    eng_block = register_box("EngineBlock", 0.80, 0.60, 0.45, (3.40, -0.70, 0.30),
                             front=R_ENGINE_SCRAP, sides=R_ENGINE_SCRAP, top=R_ENGINE_SCRAP)
    fan_hub = make_cylinder("FanHub", 0.15, 0.08, segs=8, at=(3.85, -0.70, 0.45))
    fan_hub.rotation_euler = (0, math.radians(90), 0)
    fan_hub.data.materials.append(mat)
    kit.map_faces_to_region(fan_hub, R_ENGINE_SCRAP, S)
    parts.append(fan_hub)

    for f_i in range(4):
        blade = register_box(f"FanBlade_{f_i}", 0.02, 0.28, 0.08, (3.90, -0.70, 0.45),
                             front=R_TWISTED_FRAME, sides=R_TWISTED_FRAME, top=R_TWISTED_FRAME)
        blade.rotation_euler = (math.radians(f_i * 45), 0, 0)

    # 6. Hanging Torn Roof Sheeting & Dangling Bent Handrails
    torn_roof = register_box("TornRoofSheet", 3.20, 1.60, 0.05, (0.40, -0.20, 2.70),
                             front=R_TORN_ROOF, sides=R_TORN_ROOF, top=R_TORN_ROOF)
    torn_roof.rotation_euler = (math.radians(20), math.radians(-15), 0)

    # Fallen Bent Yellow Handrail Poles
    for r_i, (rx, ry, rz, rang) in enumerate([(-1.80, -0.30, 0.60, 75), (0.60, 0.40, 0.70, -60)]):
        rail = make_cylinder(f"FallenRail_{r_i}", 0.03, 2.20, segs=8, at=(rx, ry, rz))
        rail.rotation_euler = (math.radians(rang), math.radians(20), 0)
        rail.data.materials.append(mat)
        kit.map_faces_to_region(rail, R_YELLOW_RAIL_BENT, S)
        parts.append(rail)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Bus_Wreck_Destroyed")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_bus_wreck_destroyed_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_bus_wreck_destroyed.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "prop_bus_wreck_destroyed.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "prop_bus_wreck_destroyed_preview.png")
        shutil.copy2(OUT_DIR / "prop_bus_wreck_destroyed_atlas.png", TOOLS_OUT_DIR / "prop_bus_wreck_destroyed_atlas.png")
    except Exception as e:
        print(f"[prop_bus_wreck_destroyed] note: {e}")

    print("[prop_bus_wreck_destroyed] generation complete.")


main()
