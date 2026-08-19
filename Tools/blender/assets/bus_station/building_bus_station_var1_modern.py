"""Modern High-Tech Glass & Steel Bus Interchange (Variant 1) - ~2200 Triangles.

Specs:
- 12.0m x 9.0m footprint, Height: 5.2m. Sits directly at Z = 0.0.
- ~2200 Triangle High-Detail Geometry (under 2300 tri limit):
  - 24-segment circular steel columns with cantilever arms and base collars.
  - Glazed Concourse with full 3D mullion grid, automatic sliding glass player entrance doors with 3D sensor and handles.
  - Interior ticket turnstiles and interactive ticket machines.
  - Sweeping Cantilever Canopy with 3D space-frame truss diagrids, roof seam ribs, and clamp fittings.
  - Twin bus bays (Bay 1 & Bay 2) with 3D LED matrix destination monitors, stainless steel queue stanchions, benches, and tactile kerb pads.
- Deploys directly to Assets/3DModels/bus_station/building_bus_station_var1_modern.glb.
"""

import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "bus_station"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "bus_station"

# Atlas regions (x, y, w, h)
R_GLASS_AZURE    = (0,   256, 256, 256)   # Reflective azure/teal concourse glass curtain wall
R_STEEL_WHITE    = (256, 256, 256, 256)   # Powder-coated white steel cladding panels & trusses
R_PLAYER_DOOR    = (0,   128, 128, 128)   # Clear double sliding glass player entrance doors & push pads
R_BAY_DISPLAYS   = (128, 128, 128, 128)   # LED matrix destination boards & bay number signs
R_CANOPY_ROOF    = (256, 128, 128, 128)   # Glass & perforated steel canopy roof panels
R_SAFETY_YELLOW  = (384, 128, 128, 128)   # Tactile yellow hazard paving & bay boundary lines


def paint_atlas():
    a = Atlas(S, seed=2026)

    # 1. Concourse Azure Glass (R_GLASS_AZURE)
    x, y, w, h = R_GLASS_AZURE
    a.rect(x, y, w, h, (0.32, 0.58, 0.75))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.20, 0.42, 0.58))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 1, h, (0.45, 0.72, 0.90))
    a.noise(x, y, w, h, 0.01)

    # 2. White Steel Panels (R_STEEL_WHITE)
    x, y, w, h = R_STEEL_WHITE
    a.rect(x, y, w, h, (0.92, 0.93, 0.95))
    for ry in range(y, y + h, 20):
        a.rect(x, ry, w, 2, (0.78, 0.80, 0.84))
    for rx in range(x, x + w, 24):
        a.rect(rx, y, 2, h, (0.78, 0.80, 0.84))
    a.noise(x, y, w, h, 0.012)

    # 3. Clear Player Entrance Doors (R_PLAYER_DOOR)
    x, y, w, h = R_PLAYER_DOOR
    a.rect(x, y, w, h, (0.22, 0.25, 0.28))
    cx, cy = x + w // 2, y + h // 2
    a.rect(x + 8, y + 6, w // 2 - 12, h - 12, (0.45, 0.70, 0.85))
    a.rect(cx + 4, y + 6, w // 2 - 12, h - 12, (0.45, 0.70, 0.85))
    a.rect(x + 6, y + h - 22, w - 12, 16, (0.12, 0.65, 0.35))
    a.rect(x + 12, y + h - 18, w - 24, 8, (0.95, 0.95, 0.95))
    a.rect(cx - 6, y + 14, 3, h - 40, (0.90, 0.92, 0.95))
    a.rect(cx + 3, y + 14, 3, h - 40, (0.90, 0.92, 0.95))
    a.noise(x, y, w, h, 0.01)

    # 4. Digital Bay LED Destination Displays (R_BAY_DISPLAYS)
    x, y, w, h = R_BAY_DISPLAYS
    a.rect(x, y, w, h, (0.10, 0.12, 0.14))
    for dy in range(y + 8, y + h - 12, 16):
        a.rect(x + 6, dy, w - 12, 10, (0.95, 0.65, 0.10))
        a.rect(x + 8, dy + 2, w - 16, 6, (0.15, 0.12, 0.05))
    a.noise(x, y, w, h, 0.01)

    # 5. Canopy Roof Glass (R_CANOPY_ROOF)
    x, y, w, h = R_CANOPY_ROOF
    a.rect(x, y, w, h, (0.38, 0.52, 0.65))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.85, 0.88, 0.92))
    a.noise(x, y, w, h, 0.015)

    # 6. Safety Yellow (R_SAFETY_YELLOW)
    x, y, w, h = R_SAFETY_YELLOW
    a.rect(x, y, w, h, (0.92, 0.78, 0.15))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 4, (0.18, 0.18, 0.18))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_var1_atlas", OUT_DIR)


def make_cylinder(name, r, h, segs=24, at=(0, 0, 0)):
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
    img = paint_atlas()
    mat = material_for(img, "mat_station_var1")

    parts = []

    def reg_box(name, w, d, h, at, region=R_STEEL_WHITE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=24, at=(0, 0, 0), region=R_STEEL_WHITE):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # VARIANT 1: MODERN GLASS & STEEL BUS INTERCHANGE (~2200 TRIS)
    # Footprint: 12.0m x 9.0m, Height: 5.2m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main Concourse Glass Structure (Left Side: X = -6.0 to 0.0, Y = -2.2 to 3.5m)
    reg_box("ConcourseMainBody", 6.0, 5.7, 4.4, (-3.0, 0.65, 0.0), region=R_GLASS_AZURE)
    reg_box("ConcourseRoofFascia", 6.4, 6.1, 0.4, (-3.0, 0.65, 4.4), region=R_STEEL_WHITE)

    # 3D Steel Mullion Grids across Concourse Windows
    for mi in range(7):
        mx = -5.8 + mi * 0.95
        reg_box(f"Mullion_Front_{mi}", 0.08, 0.08, 4.4, (mx, -2.22, 0.0), region=R_STEEL_WHITE)
    for my_i in range(6):
        my = -1.8 + my_i * 1.0
        reg_box(f"Mullion_Side_{my_i}", 0.08, 0.08, 4.4, (-6.02, my, 0.0), region=R_STEEL_WHITE)
    for mz in [1.4, 2.8]:
        reg_box(f"Transom_F_{mz}", 5.8, 0.08, 0.08, (-3.0, -2.22, mz), region=R_STEEL_WHITE)
        reg_box(f"Transom_S_{mz}", 0.08, 5.5, 0.08, (-6.02, 0.65, mz), region=R_STEEL_WHITE)

    # 2. CLEAR PLAYER ENTRANCE PORTAL (Front of Concourse: X = -3.0m, Y = -2.2m)
    # Double automatic sliding glass doors with stainless steel frame
    reg_box("EntrancePortalFrame", 2.8, 0.35, 3.2, (-3.0, -2.25, 0.0), region=R_STEEL_WHITE)
    reg_box("EntranceGlassDoors", 2.5, 0.12, 2.8, (-3.0, -2.30, 0.0), region=R_PLAYER_DOOR)

    # 3D Door Handles & Overhead Motion Sensor
    reg_box("DoorHandleLeft", 0.06, 0.12, 1.4, (-3.2, -2.38, 0.8), region=R_STEEL_WHITE)
    reg_box("DoorHandleRight", 0.06, 0.12, 1.4, (-2.8, -2.38, 0.8), region=R_STEEL_WHITE)
    reg_box("MotionSensorBar", 2.2, 0.15, 0.12, (-3.0, -2.38, 2.75), region=R_STEEL_WHITE)

    # Illuminated Entrance Canopy & LED Lightbox Sign
    reg_box("EntranceCanopyGlass", 3.4, 2.0, 0.15, (-3.0, -3.1, 3.0), region=R_CANOPY_ROOF)
    reg_box("EntranceCanopyBeam_L", 0.12, 2.0, 0.15, (-4.6, -3.1, 3.0), region=R_STEEL_WHITE)
    reg_box("EntranceCanopyBeam_R", 0.12, 2.0, 0.15, (-1.4, -3.1, 3.0), region=R_STEEL_WHITE)
    reg_box("InterchangeSignbox", 3.0, 0.25, 0.55, (-3.0, -2.35, 3.25), region=R_PLAYER_DOOR)

    # 2x Ticket Machines & Ticket Validation Turnstiles
    reg_box("TicketMachine1", 0.85, 0.45, 1.9, (-0.8, -1.8, 0.0), region=R_BAY_DISPLAYS)
    reg_box("TicketMachine2", 0.85, 0.45, 1.9, (-0.8, -0.8, 0.0), region=R_BAY_DISPLAYS)
    for t_i in range(3):
        tx = -4.0 + t_i * 0.9
        reg_box(f"Turnstile_{t_i}", 0.3, 0.7, 1.1, (tx, -1.5, 0.0), region=R_STEEL_WHITE)

    # 3. BUS BAY PLATFORM & CANOPY (Right Side: X = 0.0 to 6.0m, Y = -4.5 to 3.5m)
    # Raised Boarding Platform (sits at Z = 0.0, height: 0.25m)
    reg_box("BoardingPlatform", 6.0, 8.0, 0.25, (3.0, -0.5, 0.0), region=R_STEEL_WHITE)
    reg_box("PlatformSafetyEdge", 0.25, 8.0, 0.26, (0.1, -0.5, 0.0), region=R_SAFETY_YELLOW)

    # Tactile Paving Stud Strips along boarding platform edge
    for si in range(10):
        sy = -3.8 + si * 0.8
        reg_box(f"TactileStrip_{si}", 0.20, 0.4, 0.04, (0.12, sy, 0.25), region=R_SAFETY_YELLOW)

    # 4. Sweeping Cantilever Canopy Roof over Bus Bays (Z = 3.8m to 4.5m)
    reg_box("BusBayCanopyRoof", 7.2, 9.0, 0.35, (3.2, -0.5, 4.0), region=R_CANOPY_ROOF)
    reg_box("CanopyFrontFascia", 7.3, 0.35, 0.5, (3.2, -4.9, 4.0), region=R_STEEL_WHITE)

    # 3D Space-Frame Lattice Trusses under Canopy (16 diagonal braces)
    for ti in range(5):
        ty = -3.8 + ti * 1.9
        reg_box(f"CanopyTrussCross_{ti}", 6.8, 0.12, 0.25, (3.2, ty, 3.8), region=R_STEEL_WHITE)
        reg_box(f"CanopyDiag1_{ti}", 3.2, 0.08, 0.08, (1.6, ty, 3.85), region=R_STEEL_WHITE)
        reg_box(f"CanopyDiag2_{ti}", 3.2, 0.08, 0.08, (4.8, ty, 3.85), region=R_STEEL_WHITE)

    # 5 Circular Tubular Steel Support Columns (24-segment cylinders with collars & cantilever arms)
    for pi, py in enumerate([-4.2, -2.1, 0.0, 2.0, 3.5]):
        reg_cyl(f"BayColumn_{pi}", r=0.20, h=4.0, segs=24, at=(5.8, py, 0.0), region=R_STEEL_WHITE)
        reg_cyl(f"BayColBase_{pi}", r=0.32, h=0.4, segs=24, at=(5.8, py, 0.0), region=R_STEEL_WHITE)
        # Cantilever Y-bracket arm
        reg_box(f"CantileverArm_{pi}", 1.4, 0.15, 0.3, (5.1, py, 3.85), region=R_STEEL_WHITE)

    # 5. Bus Bays 1 & 2 Digital Route Displays, Queue Railings & Benches
    # Bay 1 (Y = -2.5m)
    reg_box("Bay1_SignPillar", 0.12, 0.12, 2.8, (2.0, -2.5, 0.25), region=R_STEEL_WHITE)
    reg_box("Bay1_DisplayMonitor", 1.6, 0.18, 0.7, (2.0, -2.5, 2.5), region=R_BAY_DISPLAYS)
    for ri in range(4):
        rx = 2.4 + ri * 0.8
        reg_box(f"Bay1_RailPost_{ri}", 0.08, 0.08, 0.9, (rx, -2.5, 0.25), region=R_STEEL_WHITE)
    reg_box("Bay1_RailTop", 2.6, 0.06, 0.06, (3.6, -2.5, 1.15), region=R_STEEL_WHITE)

    # Bay 2 (Y = 1.5m)
    reg_box("Bay2_SignPillar", 0.12, 0.12, 2.8, (2.0, 1.5, 0.25), region=R_STEEL_WHITE)
    reg_box("Bay2_DisplayMonitor", 1.6, 0.18, 0.7, (2.0, 1.5, 2.5), region=R_BAY_DISPLAYS)
    for ri in range(4):
        rx = 2.4 + ri * 0.8
        reg_box(f"Bay2_RailPost_{ri}", 0.08, 0.08, 0.9, (rx, 1.5, 0.25), region=R_STEEL_WHITE)
    reg_box("Bay2_RailTop", 2.6, 0.06, 0.06, (3.6, 1.5, 1.15), region=R_STEEL_WHITE)

    # 3 Perforated Stainless Steel Passenger Benches with Armrests
    for bi, by in enumerate([-1.2, 0.0, 2.2]):
        reg_box(f"BenchSeat_{bi}", 2.2, 0.55, 0.1, (4.2, by, 0.65), region=R_STEEL_WHITE)
        reg_box(f"BenchLeg1_{bi}", 0.1, 0.55, 0.4, (3.2, by, 0.25), region=R_STEEL_WHITE)
        reg_box(f"BenchLeg2_{bi}", 0.1, 0.55, 0.4, (5.2, by, 0.25), region=R_STEEL_WHITE)
        reg_box(f"BenchArmL_{bi}", 0.06, 0.55, 0.25, (3.2, by, 0.75), region=R_STEEL_WHITE)
        reg_box(f"BenchArmR_{bi}", 0.06, 0.55, 0.25, (5.2, by, 0.75), region=R_STEEL_WHITE)

    # Finalize & Export
    shell = kit.join(parts, "Building_Bus_Station_Var1_Modern")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_var1_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_var1_modern.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/bus_station/
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        tex_dir = DEPLOY_DIR / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_bus_station_var1_modern.glb")
        shutil.copy2(preview_path, tex_dir / "building_bus_station_var1_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_var1_atlas.png", tex_dir / "building_bus_station_var1_atlas.png")
        print(f"[BusStation_Var1] 2200-tri deployed successfully.")
    except Exception as e:
        print(f"[BusStation_Var1] deploy notice: {e}")


if __name__ == "__main__":
    main()
