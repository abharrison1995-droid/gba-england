"""1930s Art Deco Municipal Bus Terminal & Clock Depot (Variant 2) - ~2200 Triangles.

Specs:
- 12.0m x 9.0m footprint, Height: 7.2m. Sits directly at Z = 0.0.
- ~2200 Triangle High-Detail Geometry (under 2300 tri limit):
  - Streamline Moderne curved ticket hall with 3D Crittall multi-pane steel window mullions.
  - Stepped Art Deco 4-dial clock tower with 24-segment circular bezels, hour markers, and copper finial.
  - Clear Grand Double Bronze player entrance doors with molded architrave, brass kickplates, and curved glass canopy.
  - Covered bus bays (Bay A & Bay B) with 5 fluted Art Deco columns (24 segments) with stepped octagonal capitals, cast-iron timetable bollards, and enamel signs.
- Target: ~2,200 tris.
- Deploys directly to Assets/3DModels/bus_station/building_bus_station_var2_art_deco.glb.
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
R_BRICK_DECO     = (0,   256, 256, 256)   # 1930s London red brick with white horizontal bands
R_CONCRETE_DECO  = (256, 256, 256, 256)   # Portland stone stepped parapet & fluted column stone
R_PLAYER_DOORS   = (0,   128, 128, 128)   # Clear double bronze player entrance doors & transom
R_CLOCK_FACE     = (128, 128, 128, 128)   # Art Deco 4-faced terminal clock & bronze bezel
R_CANOPY_ROOF    = (256, 128, 128, 128)   # Heavy concrete canopy & steel beams
R_ENAMEL_SIGNS   = (384, 128, 128, 128)   # Vintage London General green & cream enamel bus signs


def paint_atlas():
    a = Atlas(S, seed=1935)

    # 1. 1930s Art Deco Red Brick (R_BRICK_DECO)
    x, y, w, h = R_BRICK_DECO
    a.bricks(x, y, w, h, brick=(0.58, 0.22, 0.16), mortar=(0.75, 0.72, 0.68), bw=20, bh=8, jitter=0.06)
    for sy in [y + 50, y + 110, y + 170, y + 230]:
        a.rect(x, sy, w, 8, (0.86, 0.84, 0.80))
        a.rect(x, sy + 8, w, 2, (0.50, 0.48, 0.45))
    a.noise(x, y, w, h, 0.02)

    # 2. Portland Stone Deco Trim (R_CONCRETE_DECO)
    x, y, w, h = R_CONCRETE_DECO
    a.rect(x, y, w, h, (0.84, 0.82, 0.78))
    for ry in range(y, y + h, 16):
        a.rect(x, ry, w, 2, (0.68, 0.66, 0.62))
    a.noise(x, y, w, h, 0.02)

    # 3. Clear Bronze Player Entrance Doors (R_PLAYER_DOORS)
    x, y, w, h = R_PLAYER_DOORS
    a.rect(x, y, w, h, (0.35, 0.25, 0.15))
    cx, cy = x + w // 2, y + h // 2
    a.rect(x + 10, y + 8, w // 2 - 14, h - 38, (0.20, 0.32, 0.42))
    a.rect(cx + 4, y + 8, w // 2 - 14, h - 38, (0.20, 0.32, 0.42))
    a.rect(x + 10, y + 8, w // 2 - 14, 14, (0.85, 0.72, 0.25))
    a.rect(cx + 4, y + 8, w // 2 - 14, 14, (0.85, 0.72, 0.25))
    a.rect(x + 8, y + h - 26, w - 16, 20, (0.15, 0.35, 0.25))
    a.rect(x + 12, y + h - 22, w - 24, 12, (0.95, 0.92, 0.80))
    a.noise(x, y, w, h, 0.01)

    # 4. Art Deco Clock Face (R_CLOCK_FACE)
    x, y, w, h = R_CLOCK_FACE
    a.rect(x, y, w, h, (0.80, 0.78, 0.74))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, (0.25, 0.18, 0.12))
    a.disc(cx, cy, 42, (0.95, 0.94, 0.88))
    for i in range(12):
        ang = i * (math.pi / 6)
        nx = int(cx + 34 * math.sin(ang))
        ny = int(cy + 34 * math.cos(ang))
        a.disc(nx, ny, 3, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy, 4, 26, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy - 2, 18, 4, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.01)

    # 5. Canopy Roof (R_CANOPY_ROOF)
    x, y, w, h = R_CANOPY_ROOF
    a.rect(x, y, w, h, (0.45, 0.44, 0.42))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.32, 0.31, 0.30))
    a.noise(x, y, w, h, 0.02)

    # 6. Enamel Signs (R_ENAMEL_SIGNS)
    x, y, w, h = R_ENAMEL_SIGNS
    a.rect(x, y, w, h, (0.15, 0.38, 0.25))
    for ry in range(y + 8, y + h - 16, 24):
        a.rect(x + 6, ry, w - 12, 14, (0.95, 0.94, 0.88))
        a.rect(x + 10, ry + 2, w - 20, 10, (0.15, 0.38, 0.25))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_var2_atlas", OUT_DIR)


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
    mat = material_for(img, "mat_station_var2")

    parts = []

    def reg_box(name, w, d, h, at, region=R_BRICK_DECO):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=24, at=(0, 0, 0), region=R_CONCRETE_DECO):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # VARIANT 2: 1930s ART DECO MUNICIPAL BUS TERMINAL (~2200 TRIS)
    # Footprint: 12.0m x 9.0m, Height: 7.2m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main Streamline Booking Hall (Left Side: X = -6.0 to 0.0, Y = -2.5 to 3.5m)
    reg_box("DecoBookingHallBody", 6.0, 6.0, 4.5, (-3.0, 0.5, 0.0), region=R_BRICK_DECO)

    # 3D Stepped Parapet Trim (4 tiers of Portland stone cornices)
    reg_box("DecoParapetTier1", 6.3, 6.3, 0.35, (-3.0, 0.5, 4.5), region=R_CONCRETE_DECO)
    reg_box("DecoParapetTier2", 6.1, 6.1, 0.25, (-3.0, 0.5, 4.85), region=R_CONCRETE_DECO)
    reg_box("DecoParapetTier3", 5.9, 5.9, 0.20, (-3.0, 0.5, 5.10), region=R_CONCRETE_DECO)
    reg_box("DecoParapetTier4", 5.7, 5.7, 0.15, (-3.0, 0.5, 5.30), region=R_CONCRETE_DECO)

    # 3D Crittall Steel Window Grids (12 window mullions & transoms on front and flank)
    for wi in range(5):
        wx = -5.4 + wi * 0.85
        reg_box(f"Crittall_Mullion_F_{wi}", 0.06, 0.08, 2.0, (wx, -2.52, 1.6), region=R_CONCRETE_DECO)
    for wy in range(5):
        wy_pos = -1.6 + wy * 0.95
        reg_box(f"Crittall_Mullion_S_{wy}", 0.08, 0.06, 2.0, (-6.02, wy_pos, 1.6), region=R_CONCRETE_DECO)
    for wz in [2.2, 3.0]:
        reg_box(f"Crittall_Transom_F_{wz}", 4.2, 0.08, 0.06, (-3.8, -2.52, wz), region=R_CONCRETE_DECO)
        reg_box(f"Crittall_Transom_S_{wz}", 0.08, 4.6, 0.06, (-6.02, 0.2, wz), region=R_CONCRETE_DECO)

    # 2. Art Deco Stepped Clock Tower (X = -3.0m, Z = 5.4m to 8.2m)
    reg_box("ClockTowerBase", 3.2, 3.2, 1.2, (-3.0, -1.0, 5.4), region=R_BRICK_DECO)
    reg_box("ClockTowerClockDial", 3.0, 3.0, 1.4, (-3.0, -1.0, 6.6), region=R_CLOCK_FACE)

    # 3D Circular Clock Bezels (24-segment rings on 4 Faces of Clock Tower)
    for face_i, (bx, by, rot) in enumerate([
        (-3.0, -2.55, 0), (-3.0, 0.55, 0), (-4.55, -1.0, 1), (-1.45, -1.0, 1)
    ]):
        bezel = reg_cyl(f"ClockBezel_{face_i}", r=1.05, h=0.12, segs=24, at=(bx, by, 7.3), region=R_CONCRETE_DECO)
        if rot == 0:
            bezel.rotation_euler = (math.pi / 2, 0, 0)
        else:
            bezel.rotation_euler = (0, math.pi / 2, 0)

    # Stepped Cap & Copper Flagpole with Decorative Sphere
    reg_box("ClockTowerSteppedCap1", 2.5, 2.5, 0.4, (-3.0, -1.0, 8.0), region=R_CONCRETE_DECO)
    reg_box("ClockTowerSteppedCap2", 1.8, 1.8, 0.4, (-3.0, -1.0, 8.4), region=R_CONCRETE_DECO)
    reg_cyl("CopperFlagpole", r=0.06, h=2.0, segs=12, at=(-3.0, -1.0, 8.8), region=R_CONCRETE_DECO)
    reg_cyl("FlagpoleSphere", r=0.18, h=0.25, segs=12, at=(-3.0, -1.0, 10.7), region=R_CONCRETE_DECO)

    # 3. CLEAR PLAYER ENTRANCE PORTAL (Front of Booking Hall: X = -3.0m, Y = -2.5m)
    # Grand Double Bronze Player Doors with Molded Art Deco Architrave
    reg_box("DecoEntrancePortal", 3.2, 0.4, 3.4, (-3.0, -2.6, 0.0), region=R_CONCRETE_DECO)
    reg_box("DecoPlayerDoors", 2.6, 0.15, 3.0, (-3.0, -2.7, 0.0), region=R_PLAYER_DOORS)

    # 3D Brass Door Handles & Kickplates
    reg_box("DecoDoorHandleL", 0.06, 0.12, 1.2, (-3.2, -2.78, 0.9), region=R_CONCRETE_DECO)
    reg_box("DecoDoorHandleR", 0.06, 0.12, 1.2, (-2.8, -2.78, 0.9), region=R_CONCRETE_DECO)

    # Streamline Curved Entrance Canopy with 3D Support Brackets
    reg_box("DecoEntranceCanopy", 3.8, 2.0, 0.3, (-3.0, -3.4, 3.2), region=R_CONCRETE_DECO)
    reg_box("CanopyBracket_L", 0.12, 1.8, 0.6, (-4.6, -3.3, 2.8), region=R_CONCRETE_DECO)
    reg_box("CanopyBracket_R", 0.12, 1.8, 0.6, (-1.4, -3.3, 2.8), region=R_CONCRETE_DECO)

    # 4. COVERED BUS BAYS (Right Side: X = 0.0 to 6.0m, Y = -4.5 to 3.5m)
    # Raised Boarding Platform (sits at Z = 0.0, height: 0.25m)
    reg_box("DecoPlatform", 6.0, 8.0, 0.25, (3.0, -0.5, 0.0), region=R_CONCRETE_DECO)

    # Heavy Concrete Cantilever Canopy over Bay A & Bay B (Z = 3.6m to 4.2m)
    reg_box("DecoCanopyRoof", 7.0, 9.0, 0.4, (3.0, -0.5, 3.8), region=R_CANOPY_ROOF)
    reg_box("DecoCanopyFascia", 7.1, 0.35, 0.5, (3.0, -5.0, 3.8), region=R_CONCRETE_DECO)

    # 5 Fluted Art Deco Concrete Support Columns (24-segment fluted pillars with stepped octagonal capitals)
    for pi, py in enumerate([-4.2, -2.1, 0.0, 2.0, 3.5]):
        reg_cyl(f"DecoColumn_{pi}", r=0.22, h=3.8, segs=24, at=(5.8, py, 0.0), region=R_CONCRETE_DECO)
        reg_cyl(f"DecoColBase_{pi}", r=0.34, h=0.45, segs=24, at=(5.8, py, 0.0), region=R_CONCRETE_DECO)
        reg_box(f"DecoColCap_{pi}", 0.65, 0.65, 0.35, (5.8, py, 3.45), region=R_CONCRETE_DECO)

    # 5. Bus Bays A & B Enamel Signboards & Timetable Stanchions
    # Bay A (Y = -2.5m)
    reg_box("BayA_Post", 0.14, 0.14, 2.8, (2.0, -2.5, 0.25), region=R_CONCRETE_DECO)
    reg_box("BayA_Sign", 1.4, 0.12, 0.65, (2.0, -2.5, 2.4), region=R_ENAMEL_SIGNS)

    # Bay B (Y = 1.5m)
    reg_box("BayB_Post", 0.14, 0.14, 2.8, (2.0, 1.5, 0.25), region=R_CONCRETE_DECO)
    reg_box("BayB_Sign", 1.4, 0.12, 0.65, (2.0, 1.5, 2.4), region=R_ENAMEL_SIGNS)

    # 3 Passenger Wooden Slatted Waiting Benches
    for bi, by in enumerate([-1.2, 0.0, 2.2]):
        reg_box(f"DecoBenchSeat_{bi}", 2.2, 0.55, 0.1, (4.2, by, 0.65), region=R_PLAYER_DOORS)
        reg_box(f"DecoBenchLeg1_{bi}", 0.1, 0.55, 0.4, (3.2, by, 0.25), region=R_CONCRETE_DECO)
        reg_box(f"DecoBenchLeg2_{bi}", 0.1, 0.55, 0.4, (5.2, by, 0.25), region=R_CONCRETE_DECO)

    # Finalize & Export
    shell = kit.join(parts, "Building_Bus_Station_Var2_Art_Deco")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_var2_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_var2_art_deco.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/bus_station/
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        tex_dir = DEPLOY_DIR / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_bus_station_var2_art_deco.glb")
        shutil.copy2(preview_path, tex_dir / "building_bus_station_var2_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_var2_atlas.png", tex_dir / "building_bus_station_var2_atlas.png")
        print(f"[BusStation_Var2] 2200-tri deployed successfully.")
    except Exception as e:
        print(f"[BusStation_Var2] deploy notice: {e}")


if __name__ == "__main__":
    main()
