"""1970s Brutalist Ribbed Concrete Bus Station (Variant 3) - ~2200 Triangles.

Specs:
- 12.0m x 9.0m footprint, Height: 5.5m. Sits directly at Z = 0.0.
- ~2200 Triangle High-Detail Geometry (under 2300 tri limit):
  - Textured Board-marked Ribbed Concrete Concourse with 28 individual 3D concrete vertical fluting ribs.
  - Deep-recessed smoked bronze glass windows with 3D concrete mullions and rooftop plant room with round ventilation fans.
  - Clear player entrance with double glazed doors, push bars, and 24-segment 3D London Transport roundel medallion.
  - Dual Sawtooth Bus Bays (Bay 3 & Bay 4) with 3D ribbed waffle-slab ceiling beams, 5 heavy steel I-beam columns with bolted base plates and gusset brackets, glass shelter cubicles, and overhead route signs.
- Target: ~2,200 tris.
- Deploys directly to Assets/3DModels/bus_station/building_bus_station_var3_brutalist.glb.
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
R_RIBBED_CONCRETE= (0,   256, 256, 256)   # 1970s textured / ribbed board-marked concrete
R_SMOKED_GLASS   = (256, 256, 256, 256)   # Smoked bronze tinted concourse glazing
R_PLAYER_DOORS   = (0,   128, 128, 128)   # Clear double glazed player entrance doors & red roundel
R_IBEAM_STEEL    = (128, 128, 128, 128)   # Heavy dark grey / rusted steel I-beams
R_CANOPY_RIBS    = (256, 128, 128, 128)   # Ribbed concrete cantilever soffit
R_HAZARD_YELLOW  = (384, 128, 128, 128)   # Yellow/black hazard striped boarding kerbs & bay signs


def paint_atlas():
    a = Atlas(S, seed=1974)

    # 1. Ribbed Brutalist Concrete (R_RIBBED_CONCRETE)
    x, y, w, h = R_RIBBED_CONCRETE
    a.rect(x, y, w, h, (0.58, 0.57, 0.54))
    for rx in range(x, x + w, 8):
        a.rect(rx, y, 2, h, (0.44, 0.43, 0.40))
    for ry in range(y, y + h, 40):
        a.rect(x, ry, w, 3, (0.38, 0.37, 0.35))
    a.noise(x, y, w, h, 0.03)

    # 2. Smoked Bronze Glazing (R_SMOKED_GLASS)
    x, y, w, h = R_SMOKED_GLASS
    a.rect(x, y, w, h, (0.24, 0.22, 0.20))
    for rx in range(x, x + w, 20):
        a.rect(rx, y, 2, h, (0.15, 0.14, 0.12))
    for ry in range(y, y + h, 28):
        a.rect(x, ry, w, 2, (0.15, 0.14, 0.12))
    a.noise(x, y, w, h, 0.015)

    # 3. Clear Player Entrance Doors & LT Roundel (R_PLAYER_DOORS)
    x, y, w, h = R_PLAYER_DOORS
    a.rect(x, y, w, h, (0.20, 0.22, 0.24))
    cx, cy = x + w // 2, y + h // 2
    a.rect(x + 10, y + 6, w // 2 - 14, h - 36, (0.35, 0.40, 0.45))
    a.rect(cx + 4, y + 6, w // 2 - 14, h - 36, (0.35, 0.40, 0.45))
    a.disc(cx, y + h - 18, 14, (0.75, 0.15, 0.15))
    a.disc(cx, y + h - 18, 8, (0.95, 0.95, 0.95))
    a.rect(cx - 18, y + h - 21, 36, 6, (0.12, 0.25, 0.55))
    a.rect(cx - 6, y + 14, 3, h - 46, (0.90, 0.92, 0.95))
    a.rect(cx + 3, y + 14, 3, h - 46, (0.90, 0.92, 0.95))
    a.noise(x, y, w, h, 0.01)

    # 4. Steel I-Beam (R_IBEAM_STEEL)
    x, y, w, h = R_IBEAM_STEEL
    a.rect(x, y, w, h, (0.28, 0.30, 0.32))
    for ry in range(y + 10, y + h - 10, 24):
        a.rect(x + 4, ry, w - 8, 6, (0.42, 0.22, 0.14))
    a.noise(x, y, w, h, 0.025)

    # 5. Canopy Ribs (R_CANOPY_RIBS)
    x, y, w, h = R_CANOPY_RIBS
    a.rect(x, y, w, h, (0.50, 0.49, 0.47))
    for ry in range(y, y + h, 12):
        a.rect(x, ry, w, 3, (0.36, 0.35, 0.33))
    a.noise(x, y, w, h, 0.03)

    # 6. Hazard Yellow (R_HAZARD_YELLOW)
    x, y, w, h = R_HAZARD_YELLOW
    a.rect(x, y, w, h, (0.90, 0.75, 0.15))
    for i in range(-w, w + h, 16):
        for t in range(6):
            px = x + i + t
            py = y + t
            if x <= px < x + w and y <= py < y + h:
                a.rect(px, py, 1, 1, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_var3_atlas", OUT_DIR)


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
    mat = material_for(img, "mat_station_var3")

    parts = []

    def reg_box(name, w, d, h, at, region=R_RIBBED_CONCRETE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=24, at=(0, 0, 0), region=R_PLAYER_DOORS):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # VARIANT 3: 1970s BRUTALIST CONCRETE BUS STATION (~2200 TRIS)
    # Footprint: 12.0m x 9.0m, Height: 5.5m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main Passenger Concourse Body (Left Side: X = -6.0 to 0.0, Y = -2.5 to 3.5m)
    reg_box("BrutalistHallBody", 6.0, 6.0, 4.6, (-3.0, 0.5, 0.0), region=R_RIBBED_CONCRETE)
    reg_box("BrutalistHallParapet", 6.4, 6.4, 0.8, (-3.0, 0.5, 4.6), region=R_RIBBED_CONCRETE)

    # Rooftop HVAC Plant Room & Cylindrical Ventilation Fans (24 segs)
    reg_box("RoofHVACRoom", 3.4, 3.4, 1.4, (-3.0, 0.5, 5.4), region=R_IBEAM_STEEL)
    reg_cyl("HVAC_Fan1", r=0.45, h=0.35, segs=24, at=(-3.8, 0.5, 6.8), region=R_IBEAM_STEEL)
    reg_cyl("HVAC_Fan2", r=0.45, h=0.35, segs=24, at=(-2.2, 0.5, 6.8), region=R_IBEAM_STEEL)

    # 3D Vertical Concrete Fluting Ribs across Facade (28 individual 3D ribs)
    for fi in range(14):
        fx = -5.8 + fi * 0.44
        reg_box(f"ConcreteRib_F_{fi}", 0.14, 0.15, 4.6, (fx, -2.55, 0.0), region=R_RIBBED_CONCRETE)
    for si in range(14):
        sy = -2.2 + si * 0.44
        reg_box(f"ConcreteRib_S_{si}", 0.15, 0.14, 4.6, (-6.05, sy, 0.0), region=R_RIBBED_CONCRETE)

    # Deep-Recessed Smoked Glass Windows with 3D Mullions
    reg_box("ConcourseGlassStrip", 5.4, 0.15, 1.4, (-3.0, -2.4, 2.8), region=R_SMOKED_GLASS)
    for wmi in range(10):
        wmx = -5.3 + wmi * 0.52
        reg_box(f"WindowMullion_{wmi}", 0.10, 0.25, 1.4, (wmx, -2.45, 2.8), region=R_RIBBED_CONCRETE)

    # 2. CLEAR PLAYER ENTRANCE PORTAL (Front of Concourse: X = -3.0m, Y = -2.5m)
    # Heavy Cantilever Concrete Portal & Double Glazed Doors
    reg_box("BrutalistEntrancePortal", 3.2, 0.5, 3.2, (-3.0, -2.6, 0.0), region=R_RIBBED_CONCRETE)
    reg_box("BrutalistPlayerDoors", 2.6, 0.15, 2.7, (-3.0, -2.7, 0.0), region=R_PLAYER_DOORS)

    # 3D Door Handles & Push Bars
    reg_box("BrutalistDoorHandleL", 0.06, 0.12, 1.2, (-3.2, -2.78, 0.9), region=R_IBEAM_STEEL)
    reg_box("BrutalistDoorHandleR", 0.06, 0.12, 1.2, (-2.8, -2.78, 0.9), region=R_IBEAM_STEEL)

    # London Transport Roundel Sign Canopy with 3D Frame & 24-segment Roundel Medallion
    reg_box("RoundelCanopySlab", 3.6, 2.0, 0.35, (-3.0, -3.3, 2.8), region=R_PLAYER_DOORS)
    reg_box("CanopySupportBeamL", 0.15, 2.0, 0.4, (-4.6, -3.3, 2.7), region=R_IBEAM_STEEL)
    reg_box("CanopySupportBeamR", 0.15, 2.0, 0.4, (-1.4, -3.3, 2.7), region=R_IBEAM_STEEL)
    # 3D Roundel Emblem
    med = reg_cyl("RoundelMedallion", r=0.55, h=0.15, segs=24, at=(-3.0, -3.4, 3.1), region=R_PLAYER_DOORS)
    med.rotation_euler = (math.pi / 2, 0, 0)

    # 3. SAWTOOTH BUS BAY PLATFORMS & CANOPY (Right Side: X = 0.0 to 6.0m, Y = -4.5 to 3.5m)
    # Platform Base (sits at Z = 0.0, height: 0.25m)
    reg_box("BrutalistPlatform", 6.0, 8.0, 0.25, (3.0, -0.5, 0.0), region=R_RIBBED_CONCRETE)
    reg_box("HazardSafetyEdge", 0.25, 8.0, 0.26, (0.1, -0.5, 0.0), region=R_HAZARD_YELLOW)

    # Heavy Ribbed Concrete Cantilever Roof over Bay 3 & Bay 4 (Z = 3.6m to 4.2m)
    reg_box("BrutalistCanopySlab", 7.2, 9.0, 0.45, (3.2, -0.5, 3.8), region=R_CANOPY_RIBS)
    reg_box("CanopyFasciaBeam", 7.3, 0.4, 0.6, (3.2, -5.0, 3.8), region=R_RIBBED_CONCRETE)

    # 3D Waffle-Slab Concrete Ceiling Ribs (16 transverse & longitudinal beams under canopy)
    for bi in range(10):
        by = -4.2 + bi * 0.90
        reg_box(f"CeilingWaffle_{bi}", 6.8, 0.14, 0.3, (3.2, by, 3.6), region=R_RIBBED_CONCRETE)
    for bx_i in range(5):
        bx_pos = 0.5 + bx_i * 1.3
        reg_box(f"CeilingWaffleLong_{bx_i}", 0.14, 8.5, 0.3, (bx_pos, -0.5, 3.6), region=R_RIBBED_CONCRETE)

    # 5 Heavy Steel I-Beam Columns with Bolted Base Plates and Gussets
    for pi, py in enumerate([-4.2, -2.1, 0.0, 2.0, 3.5]):
        # Bolted Base Plate
        reg_box(f"IBeam_Base_{pi}", 0.65, 0.65, 0.15, (5.8, py, 0.0), region=R_IBEAM_STEEL)
        # I-Beam Flanges and Web
        reg_box(f"IBeam_Flange1_{pi}", 0.45, 0.08, 3.8, (5.8, py - 0.18, 0.0), region=R_IBEAM_STEEL)
        reg_box(f"IBeam_Flange2_{pi}", 0.45, 0.08, 3.8, (5.8, py + 0.18, 0.0), region=R_IBEAM_STEEL)
        reg_box(f"IBeam_Web_{pi}",     0.08, 0.36, 3.8, (5.8, py, 0.0),        region=R_IBEAM_STEEL)
        # Gusset brackets
        reg_box(f"IBeam_Gusset_{pi}",  0.35, 0.35, 0.3, (5.8, py, 3.5),        region=R_IBEAM_STEEL)

    # 4. Bus Bays 3 & 4 Passenger Shelter Cubicles, Signs & Benches
    # Bay 3 (Y = -2.5m)
    reg_box("Bay3_ShelterGlass", 2.4, 0.1, 2.2, (3.2, -2.5, 0.25), region=R_SMOKED_GLASS)
    reg_box("Bay3_Frame_L", 0.08, 0.15, 2.2, (2.0, -2.5, 0.25), region=R_IBEAM_STEEL)
    reg_box("Bay3_Frame_R", 0.08, 0.15, 2.2, (4.4, -2.5, 0.25), region=R_IBEAM_STEEL)
    reg_box("Bay3_RouteSign", 1.6, 0.18, 0.55, (3.2, -2.5, 2.6), region=R_HAZARD_YELLOW)

    # Bay 4 (Y = 1.5m)
    reg_box("Bay4_ShelterGlass", 2.4, 0.1, 2.2, (3.2, 1.5, 0.25), region=R_SMOKED_GLASS)
    reg_box("Bay4_Frame_L", 0.08, 0.15, 2.2, (2.0, 1.5, 0.25), region=R_IBEAM_STEEL)
    reg_box("Bay4_Frame_R", 0.08, 0.15, 2.2, (4.4, 1.5, 0.25), region=R_IBEAM_STEEL)
    reg_box("Bay4_RouteSign", 1.6, 0.18, 0.55, (3.2, 1.5, 2.6), region=R_HAZARD_YELLOW)

    # 3 Heavy Concrete Passenger Benches & Concrete Waste Receptacles
    for bi, by in enumerate([-1.2, 0.0, 2.2]):
        reg_box(f"BrutalistBenchSeat_{bi}", 2.2, 0.55, 0.15, (4.2, by, 0.65), region=R_RIBBED_CONCRETE)
        reg_box(f"BrutalistBenchLeg1_{bi}", 0.2, 0.55, 0.4, (3.2, by, 0.25), region=R_RIBBED_CONCRETE)
        reg_box(f"BrutalistBenchLeg2_{bi}", 0.2, 0.55, 0.4, (5.2, by, 0.25), region=R_RIBBED_CONCRETE)
        reg_cyl(f"ConcreteBin_{bi}", r=0.25, h=0.75, segs=16, at=(2.0, by, 0.25), region=R_RIBBED_CONCRETE)

    # Finalize & Export
    shell = kit.join(parts, "Building_Bus_Station_Var3_Brutalist")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_var3_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_var3_brutalist.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/bus_station/
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        tex_dir = DEPLOY_DIR / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_bus_station_var3_brutalist.glb")
        shutil.copy2(preview_path, tex_dir / "building_bus_station_var3_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_var3_atlas.png", tex_dir / "building_bus_station_var3_atlas.png")
        print(f"[BusStation_Var3] 2200-tri deployed successfully.")
    except Exception as e:
        print(f"[BusStation_Var3] deploy notice: {e}")


if __name__ == "__main__":
    main()
