"""High-Poly (~1000 Tris) Arcane Alchemist Bio-Vat & Control Console.

Specs:
- 3.6m x 3.0m footprint, Height: 3.5m.
- Detailed 3D geometric modelling (~1,000 triangles):
  - 16-sided glass containment cylinder with glowing cyan/purple broth and floating specimen core.
  - Heavy brass plinth base, 3 reinforcing structural ring hoops, and domed pressure containment lid.
  - Victorian iron operator console with 4 glowing Nixie vacuum display tubes, toggle switches, and chart roll.
  - Multi-tiered 3D chemical piping network with red wheel valves and 3 brass pressure gauges.
  - Octagonal riveted heavy iron deck platform with diamond tread drainage.
- Outputs to Tools/blender/out/High_Poly_1000Tri/ and Tools/out/High_Poly_1000Tri/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/exp_alchemist_biovat_1000tri.py
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
EXP_OUT_DIR = kit.OUT_DIR / "High_Poly_1000Tri"
TOOLS_EXP_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "High_Poly_1000Tri"

# --- Atlas Region Definitions (x, y, w, h) ---
R_BRASS_BRONZE  = (0,   256, 256, 256)   # Heavy riveted antique brass & bronze containment plates
R_BIO_GLASS     = (256, 256, 256, 256)   # Cylindrical glass vat containing glowing cyan/purple broth
R_CONSOLE_STEEL = (0,   128, 256, 128)   # Hammered industrial green/grey steel console casing
R_NIXIE_TUBES   = (256, 128, 128, 128)   # Glowing orange vacuum Nixie tubes & digital readouts
R_COPPER_TUBES  = (384, 128, 128, 128)   # Polished copper pipe coils & flanged couplings
R_PRESSURE_DIAL = (0,   0,   256, 128)   # Brass circular pressure gauges with PSI dial needles
R_IRON_DECK     = (256, 0,   128, 128)   # Octagonal heavy iron diamond treadplate deck floor
R_VALVE_RED_HEX = (384, 0,   128, 128)   # Red circular wheel gate valves & warning indicators

# --- Palette Colors ---
BRASS_ANTIQUE   = (0.82, 0.68, 0.28)
BRASS_DARK      = (0.42, 0.34, 0.14)
GLOW_CYAN       = (0.20, 0.95, 0.95)
BROTH_PURPLE    = (0.50, 0.15, 0.75)
SPECIMEN_CORE   = (0.85, 0.98, 1.00)
CONSOLE_GREEN   = (0.22, 0.32, 0.26)
NIXIE_ORANGE    = (1.00, 0.55, 0.10)
COPPER_SHINE    = (0.85, 0.48, 0.28)
DECK_IRON       = (0.25, 0.25, 0.28)
VALVE_RED       = (0.88, 0.12, 0.12)


def paint_biovat_atlas():
    a = Atlas(S, seed=7301)

    # 1. Antique Riveted Brass (R_BRASS_BRONZE)
    x, y, w, h = R_BRASS_BRONZE
    a.rect(x, y, w, h, BRASS_ANTIQUE)
    # Rivet lines along seams
    for by in [y + 16, y + h - 16]:
        for bx in range(x + 12, x + w, 24):
            a.disc(bx, by, 5, (0.2, 0.15, 0.05))
            a.disc(bx, by, 3, (0.95, 0.85, 0.45))
    a.shade(x, y, w, h, top=-0.08, bottom=0.12)
    a.noise(x, y, w, h, 0.02)

    # 2. Glowing Arcane Broth Glass (R_BIO_GLASS)
    x, y, w, h = R_BIO_GLASS
    a.rect(x, y, w, h, BROTH_PURPLE)
    cx, cy = x + w // 2, y + h // 2
    # Swirling glowing core
    a.disc(cx, cy, 100, (0.35, 0.18, 0.65))
    a.disc(cx, cy, 75, (0.15, 0.70, 0.85))
    a.disc(cx, cy, 50, GLOW_CYAN)
    a.disc(cx, cy, 26, SPECIMEN_CORE)  # Suspended Homunculus Specimen Core
    # Bubbles rising
    for bx, by in [(cx - 40, cy - 30), (cx + 35, cy + 40), (cx - 20, cy + 60), (cx + 50, cy - 50)]:
        a.disc(bx, by, 8, GLOW_CYAN)
        a.disc(bx, by, 4, SPECIMEN_CORE)
    a.noise(x, y, w, h, 0.015)

    # 3. Industrial Control Console (R_CONSOLE_STEEL)
    x, y, w, h = R_CONSOLE_STEEL
    a.rect(x, y, w, h, CONSOLE_GREEN)
    # Slanted control panel face with toggle switches
    a.rect(x + 12, y + 12, w - 24, h - 24, (0.15, 0.20, 0.18))
    for tx in range(x + 24, x + w - 24, 36):
        a.disc(tx, y + 36, 6, (0.7, 0.7, 0.7))
        a.rect(tx - 2, y + 36, 4, 16, (0.9, 0.9, 0.9))  # toggle lever
    # Paper chart recorder roll
    a.rect(x + w - 70, y + 16, 50, h - 32, (0.95, 0.92, 0.85))
    for py in range(y + 24, y + h - 24, 6):
        a.rect(x + w - 66, py, 42, 1, (0.75, 0.2, 0.2))  # red chart trace
    a.noise(x, y, w, h, 0.02)

    # 4. Nixie Vacuum Display Tubes (R_NIXIE_TUBES)
    x, y, w, h = R_NIXIE_TUBES
    a.rect(x, y, w, h, (0.08, 0.08, 0.10))
    # 4 Glowing Nixie Tubes side by side
    for nx in [x + 16, x + 44, x + 72, x + 100]:
        a.rect(nx, y + 16, 22, h - 32, (0.2, 0.2, 0.25))
        a.disc(nx + 11, y + h - 22, 10, (0.3, 0.3, 0.35))
        # Orange glowing digits inside
        a.rect(nx + 6, y + 24, 10, h - 48, NIXIE_ORANGE)
        a.rect(nx + 8, y + 26, 6, h - 52, (1.0, 0.9, 0.5))
    a.noise(x, y, w, h, 0.015)

    # 5. Polished Copper Tubing (R_COPPER_TUBES)
    x, y, w, h = R_COPPER_TUBES
    a.rect(x, y, w, h, COPPER_SHINE)
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 3, (0.55, 0.25, 0.12))
        a.rect(x, sy + 6, w, 4, (0.98, 0.75, 0.55))
    a.noise(x, y, w, h, 0.02)

    # 6. Brass Pressure Gauges (R_PRESSURE_DIAL)
    x, y, w, h = R_PRESSURE_DIAL
    a.rect(x, y, w, h, (0.15, 0.15, 0.15))
    for gx in [x + 64, x + 192]:
        cy = y + h // 2
        a.disc(gx, cy, 54, BRASS_ANTIQUE)
        a.disc(gx, cy, 44, (0.95, 0.95, 0.92))
        a.disc(gx, cy, 18, (0.85, 0.15, 0.15))
        a.disc(gx, cy, 12, (0.95, 0.95, 0.92))
        # Needle
        for step in range(4, 32, 3):
            a.disc(int(gx + step * 0.7), int(cy + step * 0.7), 2, (0.1, 0.1, 0.1))
        a.disc(gx, cy, 5, BRASS_DARK)
    a.noise(x, y, w, h, 0.015)

    # 7. Iron Treadplate Deck (R_IRON_DECK)
    x, y, w, h = R_IRON_DECK
    a.rect(x, y, w, h, DECK_IRON)
    for dy in range(y, y + h, 14):
        for dx in range(x, x + w, 14):
            a.rect(dx, dy, 6, 2, (0.42, 0.42, 0.46))
            a.rect(dx + 7, dy + 7, 6, 2, (0.42, 0.42, 0.46))
    a.noise(x, y, w, h, 0.03)

    # 8. Red Wheel Valves (R_VALVE_RED_HEX)
    x, y, w, h = R_VALVE_RED_HEX
    a.rect(x, y, w, h, (0.15, 0.15, 0.15))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, VALVE_RED)
    a.disc(cx, cy, 36, (0.15, 0.15, 0.15))
    a.rect(cx - 4, cy - 44, 8, 88, VALVE_RED)
    a.rect(cx - 44, cy - 4, 88, 8, VALVE_RED)
    a.disc(cx, cy, 14, BRASS_ANTIQUE)
    a.noise(x, y, w, h, 0.02)

    EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("exp_alchemist_biovat_atlas", EXP_OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_BRASS_BRONZE, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_BRASS_BRONZE, S, only=side("bottom"))


def make_cylinder(name, r, h, segs=16, at=(0, 0, 0)):
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


def make_dome(name, r, h, segs=16, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * 0.75 * math.cos(ang), r * 0.75 * math.sin(ang), h * 0.65))
    verts.append((0.0, 0.0, h))

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    apex_idx = segs * 2
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((segs + i, segs + ni, apex_idx))
    faces.append(list(range(segs - 1, -1, -1)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_biovat_atlas()
    mat = material_for(img, "mat_alchemist_biovat")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Arcane Alchemist Bio-Vat & Control Console (~1000 Triangles)
    # - 1. Octagonal Riveted Iron Deck Platform (Radius 1.9m, Z: 0.0 to 0.15m)
    # - 2. Alchemical Bio-Vat (Center-Left: X = -0.50m, Y = 0.0m):
    #      - 8-Sided Brass Plinth Base (Z = 0.15m to 0.55m)
    #      - 16-Sided Glass Vat Cylinder (Radius 0.85m, H: 2.20m, Z = 0.55m to 2.75m)
    #      - 3 3D Brass Reinforcing Hoop Bands & 4 Vertical Tie Rods
    #      - 8-Sided Domed Pressure Lid + Vacuum Globe (Z = 2.75m to 3.45m)
    # - 3. Victorian Operator Control Console (Right: X = 1.10m, Y = -0.40m):
    #      - Stepped Console Body & Slanted Operator Desk
    #      - 4 Glowing 3D Nixie Vacuum Tubes
    #      - Paper Chart Recorder Roll
    # - 4. Interconnecting Chemical Pipeline Loops, Red Gate Valves & 3 Pressure Gauges
    # =========================================================================

    # 1. Octagonal Riveted Iron Platform Base (Radius: 1.90m, Z = 0.00 to 0.15m)
    plat = make_cylinder("IronDeckPlat", 1.90, 0.15, segs=8, at=(0.0, 0.0, 0.0))
    plat.data.materials.append(mat)
    kit.map_faces_to_region(plat, R_IRON_DECK, S)
    parts.append(plat)

    # =========================================================================
    # 2. Central Alchemical Bio-Vat (X = -0.50m, Y = 0.0m)
    # =========================================================================
    # 8-Sided Brass Plinth Base (Radius 0.95m, H: 0.40m, Z = 0.15m to 0.55m)
    vat_base = make_cylinder("VatPlinthBase", 0.95, 0.40, segs=8, at=(-0.50, 0.0, 0.15))
    vat_base.data.materials.append(mat)
    kit.map_faces_to_region(vat_base, R_BRASS_BRONZE, S)
    parts.append(vat_base)

    # 16-Sided Glass Containment Cylinder (Radius 0.85m, H: 2.20m, Z = 0.55m to 2.75m)
    vat_glass = make_cylinder("VatGlassCylinder", 0.85, 2.20, segs=16, at=(-0.50, 0.0, 0.55))
    vat_glass.data.materials.append(mat)
    kit.map_faces_to_region(vat_glass, R_BIO_GLASS, S)
    parts.append(vat_glass)

    # 3 Curved 3D Brass Structural Reinforcing Rings (Z = 1.05m, 1.65m, 2.25m)
    for ring_z in [1.05, 1.65, 2.25]:
        ring = make_cylinder(f"VatHoop_{ring_z}", 0.88, 0.08, segs=16, at=(-0.50, 0.0, ring_z))
        ring.data.materials.append(mat)
        kit.map_faces_to_region(ring, R_BRASS_BRONZE, S)
        parts.append(ring)

    # 4 Vertical Steel Tie Rods around vat perimeter
    for ang in [45, 135, 225, 315]:
        rad = math.radians(ang)
        tx = -0.50 + 0.89 * math.cos(rad)
        ty = 0.89 * math.sin(rad)
        rod = make_cylinder(f"TieRod_{ang}", 0.03, 2.20, segs=6, at=(tx, ty, 0.55))
        rod.data.materials.append(mat)
        kit.map_faces_to_region(rod, R_BRASS_BRONZE, S)
        parts.append(rod)

    # 8-Sided Domed Pressure Containment Lid (Radius 0.95m, H: 0.50m, Z = 2.75m to 3.25m)
    vat_lid = make_dome("VatPressureLid", 0.95, 0.50, segs=8, at=(-0.50, 0.0, 2.75))
    vat_lid.data.materials.append(mat)
    kit.map_faces_to_region(vat_lid, R_BRASS_BRONZE, S)
    parts.append(vat_lid)

    # Top Glowing Vacuum Globe (Z = 3.25m to 3.50m)
    globe = make_dome("VatVacuumGlobe", 0.25, 0.25, segs=8, at=(-0.50, 0.0, 3.25))
    globe.data.materials.append(mat)
    kit.map_faces_to_region(globe, R_BIO_GLASS, S)
    parts.append(globe)

    # =========================================================================
    # 3. Victorian Operator Control Console (Right: X = 1.15m, Y = -0.35m)
    # =========================================================================
    # Console Base Cabinet (Width 1.20m, D: 0.70m, H: 0.85m, Z = 0.15m to 1.00m)
    register_box("ConsoleCabinet", 1.20, 0.70, 0.85, (1.15, -0.35, 0.15),
                 front=R_CONSOLE_STEEL, sides=R_CONSOLE_STEEL, back=R_CONSOLE_STEEL, top=R_CONSOLE_STEEL)

    # Slanted Operator Desk Surface (Z = 1.00m to 1.30m)
    register_box("ConsoleDesk", 1.20, 0.65, 0.30, (1.15, -0.35, 1.00),
                 front=R_CONSOLE_STEEL, sides=R_CONSOLE_STEEL, back=R_CONSOLE_STEEL, top=R_CONSOLE_STEEL)

    # 4 Glowing 3D Nixie Vacuum Display Tubes (Mounted on top of console: X = 0.80m to 1.50m)
    for i, nx in enumerate([0.80, 1.00, 1.20, 1.40]):
        nixie = make_cylinder(f"NixieTube_{i}", 0.06, 0.28, segs=8, at=(nx, -0.20, 1.30))
        nixie.data.materials.append(mat)
        kit.map_faces_to_region(nixie, R_NIXIE_TUBES, S)
        parts.append(nixie)

    # =========================================================================
    # 4. Pipeline Network, 2 Red Handwheel Valves & 3 Analog Pressure Gauges
    # =========================================================================
    # Main Horizontal Feed Pipe (From vat to console: X = -0.50m to 1.15m, Z = 1.85m, Y = 0.85m)
    register_box("FeedPipeHoriz", 1.65, 0.16, 0.16, (0.32, 0.85, 1.85),
                 front=R_COPPER_TUBES, sides=R_COPPER_TUBES, top=R_COPPER_TUBES)

    # Vertical Drop Pipe into Base (X = 1.15m, Y = 0.85m, Z = 0.15m to 1.85m)
    vert_pipe = make_cylinder("VertPipeDrop", 0.08, 1.70, segs=8, at=(1.15, 0.85, 0.15))
    vert_pipe.data.materials.append(mat)
    kit.map_faces_to_region(vert_pipe, R_COPPER_TUBES, S)
    parts.append(vert_pipe)

    # 2 Red Circular Wheel Gate Valves (X = 0.20m at Z = 1.85m, and X = 1.15m at Z = 1.10m)
    v1 = make_cylinder("GateValve1", 0.18, 0.06, segs=8, at=(0.20, 0.70, 1.85))
    v1.data.materials.append(mat)
    kit.map_faces_to_region(v1, R_VALVE_RED_HEX, S)
    parts.append(v1)

    v2 = make_cylinder("GateValve2", 0.16, 0.06, segs=8, at=(1.15, 0.70, 1.10))
    v2.data.materials.append(mat)
    kit.map_faces_to_region(v2, R_VALVE_RED_HEX, S)
    parts.append(v2)

    # 8 Bolted Heavy Steel Foundation Gussets around the base plinth (Z = 0.0m to 0.45m)
    for i in range(8):
        ang = 2 * math.pi * i / 8.0
        gx = -0.50 + 1.10 * math.cos(ang)
        gy = 1.10 * math.sin(ang)
        register_box(f"BaseGusset_{i}", 0.12, 0.12, 0.35, (gx, gy, 0.15),
                     front=R_BRASS_BRONZE, sides=R_BRASS_BRONZE, top=R_BRASS_BRONZE)

    # 3D Copper Spiral Condenser Heat Exchanger Coil on Side Pipe (Z = 0.50m to 1.70m)
    for coil_i in range(5):
        cz = 0.55 + coil_i * 0.24
        coil = make_cylinder(f"CondenserCoil_{coil_i}", 0.18, 0.08, segs=12, at=(1.15, 0.85, cz))
        coil.data.materials.append(mat)
        kit.map_faces_to_region(coil, R_COPPER_TUBES, S)
        parts.append(coil)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Exp_Alchemist_Biovat_1000Tri")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = EXP_OUT_DIR / "exp_alchemist_biovat_1000tri_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = EXP_OUT_DIR / "exp_alchemist_biovat_1000tri.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_EXP_OUT_DIR / "exp_alchemist_biovat_1000tri.glb")
        shutil.copy2(preview_path, TOOLS_EXP_OUT_DIR / "exp_alchemist_biovat_1000tri_preview.png")
        shutil.copy2(EXP_OUT_DIR / "exp_alchemist_biovat_atlas.png", TOOLS_EXP_OUT_DIR / "exp_alchemist_biovat_atlas.png")
    except Exception as e:
        print(f"[exp_alchemist_biovat_1000tri] note: {e}")

    print("[exp_alchemist_biovat_1000tri] generation complete.")


main()
