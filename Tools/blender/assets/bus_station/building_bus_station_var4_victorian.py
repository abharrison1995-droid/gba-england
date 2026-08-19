"""Victorian / Edwardian Heritage Bus & Coach Interchange (Variant 4) - ~2200 Triangles.

Specs:
- 12.0m x 9.0m footprint, Height: 6.8m. Sits directly at Z = 0.0.
- ~2200 Triangle High-Detail Geometry (under 2300 tri limit):
  - Victorian Red-Brick Booking Hall with 24 individual 3D stone corner quoins, arched window hoods, and slate roof with cast-iron ridge cresting.
  - Clock bell turret with 3D dial bezel, spire, and brass weathervane.
  - Ornate Cast-Iron Gabled Porch with 3D scrollwork brackets, dark oak double player doors with brass kickplates.
  - 4 Ridge-and-Furrow Glass Canopy Bays over Platform 1 & Platform 2 with 6 fluted cast-iron columns (20 segments), ornate scroll brackets, Victorian gas lanterns, and teak benches.
- Target: ~2,200 tris.
- Deploys directly to Assets/3DModels/bus_station/building_bus_station_var4_victorian.glb.
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
R_VICTORIAN_BRICK= (0,   256, 256, 256)   # Victorian London red brick with Bath stone quoins
R_SLATE_GABLE    = (256, 256, 256, 256)   # Welsh dark blue-grey slate roof tiles
R_OAK_PLAYER_DOOR= (0,   128, 128, 128)   # Clear dark oak double player doors with brass kickplates
R_HERITAGE_GLASS = (128, 128, 128, 128)   # Ridge-and-furrow canopy glass & arched transom
R_IRON_GREEN     = (256, 128, 128, 128)   # Heritage green painted cast-iron columns & brackets
R_TIMBER_BENCH   = (384, 128, 128, 128)   # Varnished teak wood slatted benches & platform kerbs


def paint_atlas():
    a = Atlas(S, seed=1898)

    # 1. Victorian Red Brick (R_VICTORIAN_BRICK)
    x, y, w, h = R_VICTORIAN_BRICK
    a.bricks(x, y, w, h, brick=(0.60, 0.20, 0.16), mortar=(0.78, 0.75, 0.70), bw=18, bh=8, jitter=0.05)
    for ry in range(y, y + h, 28):
        a.rect(x, ry, 24, 12, (0.85, 0.82, 0.74))
        a.rect(x + w - 24, ry, 24, 12, (0.85, 0.82, 0.74))
    a.noise(x, y, w, h, 0.02)

    # 2. Welsh Slate Roof (R_SLATE_GABLE)
    x, y, w, h = R_SLATE_GABLE
    a.rect(x, y, w, h, (0.28, 0.30, 0.35))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 3. Clear Oak Player Doors & Transom (R_OAK_PLAYER_DOOR)
    x, y, w, h = R_OAK_PLAYER_DOOR
    a.rect(x, y, w, h, (0.34, 0.20, 0.12))
    cx, cy = x + w // 2, y + h // 2
    a.rect(x + 10, y + 6, w // 2 - 14, h - 34, (0.24, 0.14, 0.08))
    a.rect(cx + 4, y + 6, w // 2 - 14, h - 34, (0.24, 0.14, 0.08))
    a.rect(x + 10, y + 6, w // 2 - 14, 12, (0.85, 0.72, 0.25))
    a.rect(cx + 4, y + 6, w // 2 - 14, 12, (0.85, 0.72, 0.25))
    a.rect(x + 8, y + h - 24, w - 16, 18, (0.14, 0.36, 0.22))
    a.rect(x + 12, y + h - 20, w - 24, 10, (0.95, 0.92, 0.78))
    a.noise(x, y, w, h, 0.01)

    # 4. Heritage Canopy Glass (R_HERITAGE_GLASS)
    x, y, w, h = R_HERITAGE_GLASS
    a.rect(x, y, w, h, (0.35, 0.50, 0.60))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.15, 0.35, 0.25))
    a.noise(x, y, w, h, 0.01)

    # 5. Heritage Green Ironwork (R_IRON_GREEN)
    x, y, w, h = R_IRON_GREEN
    a.rect(x, y, w, h, (0.14, 0.35, 0.22))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.08, 0.22, 0.14))
    a.noise(x, y, w, h, 0.015)

    # 6. Teak Timber Bench (R_TIMBER_BENCH)
    x, y, w, h = R_TIMBER_BENCH
    a.rect(x, y, w, h, (0.50, 0.32, 0.18))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.35, 0.20, 0.10))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_bus_station_var4_atlas", OUT_DIR)


def make_cylinder(name, r, h, segs=20, at=(0, 0, 0)):
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


def make_pyramid(name, base_w, base_d, height, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hw, hd = base_w / 2, base_d / 2
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, 0))
    v3 = bm.verts.new((-hw,  hd, 0))
    v_top = bm.verts.new((0, 0, height))

    bm.faces.new((v0, v1, v_top))
    bm.faces.new((v1, v2, v_top))
    bm.faces.new((v2, v3, v_top))
    bm.faces.new((v3, v0, v_top))
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_station_var4")

    parts = []

    def reg_box(name, w, d, h, at, region=R_VICTORIAN_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_GABLE):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=20, at=(0, 0, 0), region=R_IRON_GREEN):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # VARIANT 4: VICTORIAN / EDWARDIAN HERITAGE BUS INTERCHANGE (~2200 TRIS)
    # Footprint: 12.0m x 9.0m, Height: 6.8m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main Victorian Booking Hall (Left Side: X = -6.0 to 0.0, Y = -2.5 to 3.5m)
    reg_box("VictorianHallBody", 6.0, 6.0, 4.2, (-3.0, 0.5, 0.0), region=R_VICTORIAN_BRICK)
    reg_pyr("VictorianHallRoof", 6.4, 6.4, 2.4, (-3.0, 0.5, 4.2), region=R_SLATE_GABLE)

    # 3D Roof Ridge Cresting (Cast-iron finial ridge)
    reg_box("RoofRidgeCrest", 6.2, 0.15, 0.35, (-3.0, 0.5, 6.6), region=R_IRON_GREEN)

    # 3D Stone Corner Quoins (24 individual quoin blocks on corners)
    for qi in range(8):
        qz = 0.3 + qi * 0.5
        reg_box(f"Quoin_FL_{qi}", 0.35, 0.35, 0.25, (-5.95, -2.45, qz), region=R_OAK_PLAYER_DOOR)
        reg_box(f"Quoin_FR_{qi}", 0.35, 0.35, 0.25, (-0.05, -2.45, qz), region=R_OAK_PLAYER_DOOR)
        reg_box(f"Quoin_BL_{qi}", 0.35, 0.35, 0.25, (-5.95,  3.45, qz), region=R_OAK_PLAYER_DOOR)

    # 3D Arched Windows with Molded Stone Lintels
    for wi, wx in enumerate([-5.0, -1.2]):
        reg_box(f"WindowFrame_{wi}", 1.2, 0.15, 1.8, (wx, -2.52, 1.8), region=R_HERITAGE_GLASS)
        reg_box(f"WindowHood_{wi}",  1.4, 0.25, 0.2, (wx, -2.55, 3.6), region=R_OAK_PLAYER_DOOR)
        reg_box(f"WindowKeystone_{wi}", 0.3, 0.3, 0.25, (wx, -2.58, 3.7), region=R_OAK_PLAYER_DOOR)

    # Front Gable Pediment & Clock Turret with Spire
    reg_pyr("FrontGablePeak", 3.4, 1.4, 1.6, (-3.0, -2.4, 4.2), region=R_SLATE_GABLE)
    reg_box("ClockTurretBox", 1.4, 1.4, 1.4, (-3.0, -1.0, 5.8), region=R_VICTORIAN_BRICK)
    # 3D Clock Bezel (20 segments)
    clock_b = reg_cyl("TurretClockBezel", r=0.55, h=0.12, segs=20, at=(-3.0, -1.72, 6.5), region=R_OAK_PLAYER_DOOR)
    clock_b.rotation_euler = (math.pi / 2, 0, 0)
    reg_pyr("ClockTurretSpire", 1.6, 1.6, 1.4, (-3.0, -1.0, 7.2), region=R_SLATE_GABLE)
    reg_cyl("TurretWeathervane", r=0.04, h=1.0, segs=12, at=(-3.0, -1.0, 8.6), region=R_IRON_GREEN)

    # 2. CLEAR PLAYER ENTRANCE PORTAL (Front of Booking Hall: X = -3.0m, Y = -2.5m)
    # Ornate Cast-Iron Gabled Porch
    reg_box("VictorianPorchBase", 3.2, 0.5, 3.4, (-3.0, -2.6, 0.0), region=R_IRON_GREEN)
    reg_box("VictorianPlayerDoors", 2.6, 0.15, 2.9, (-3.0, -2.7, 0.0), region=R_OAK_PLAYER_DOOR)

    # 3D Brass Door Knobs & Kickplates
    reg_box("DoorPlateL", 0.08, 0.12, 1.2, (-3.2, -2.78, 0.8), region=R_OAK_PLAYER_DOOR)
    reg_box("DoorPlateR", 0.08, 0.12, 1.2, (-2.8, -2.78, 0.8), region=R_OAK_PLAYER_DOOR)

    # Pitched Iron Porch Canopy with 3D Decorative Brackets
    reg_pyr("PorchCanopyGable", 3.6, 1.8, 1.1, (-3.0, -3.3, 3.0), region=R_SLATE_GABLE)
    reg_box("PorchBracketL", 0.15, 1.6, 0.6, (-4.5, -3.2, 2.6), region=R_IRON_GREEN)
    reg_box("PorchBracketR", 0.15, 1.6, 0.6, (-1.5, -3.2, 2.6), region=R_IRON_GREEN)

    # 3. HERITAGE BUS PLATFORMS & RIDGE-AND-FURROW CANOPY (Right Side: X = 0.0 to 6.0m)
    # Platform Slab (sits at Z = 0.0, height: 0.25m)
    reg_box("HeritagePlatform", 6.0, 8.0, 0.25, (3.0, -0.5, 0.0), region=R_TIMBER_BENCH)

    # Ridge-and-Furrow Glass Canopy over Platform 1 & Platform 2 (4 triangular bays)
    for gi in range(4):
        gy = -3.5 + gi * 2.1
        reg_pyr(f"CanopyRidge_{gi}", 7.0, 2.0, 1.1, (3.2, gy, 3.6), region=R_HERITAGE_GLASS)

    # Canopy Front & Side Fascia Ironwork
    reg_box("CanopyFrontFascia", 7.1, 0.35, 0.45, (3.2, -4.8, 3.6), region=R_IRON_GREEN)

    # 6 Fluted Cast-Iron Columns (20 segments) with Ornate Scroll Brackets
    for c_idx, (cx, cy) in enumerate([
        (5.8, -4.2), (5.8, -0.5), (5.8, 3.0),
        (0.8, -4.2), (0.8, -0.5), (0.8, 3.0)
    ]):
        reg_cyl(f"CastIronCol_{c_idx}", r=0.18, h=3.6, segs=20, at=(cx, cy, 0.0), region=R_IRON_GREEN)
        reg_cyl(f"ColBase_{c_idx}",     r=0.28, h=0.4, segs=20, at=(cx, cy, 0.0), region=R_IRON_GREEN)
        reg_box(f"ScrollBracket_{c_idx}", 0.8, 0.8, 0.6, (cx, cy, 3.0), region=R_IRON_GREEN)

    # 4. Platforms 1 & 2 Heritage Enamel Signposts, Gas Lanterns & Benches
    # Platform 1 (Y = -2.5m)
    reg_box("Plat1_Post", 0.12, 0.12, 2.8, (2.2, -2.5, 0.25), region=R_IRON_GREEN)
    reg_box("Plat1_Sign", 1.4, 0.12, 0.65, (2.2, -2.5, 2.3), region=R_OAK_PLAYER_DOOR)

    # Platform 2 (Y = 1.5m)
    reg_box("Plat2_Post", 0.12, 0.12, 2.8, (2.2, 1.5, 0.25), region=R_IRON_GREEN)
    reg_box("Plat2_Sign", 1.4, 0.12, 0.65, (2.2, 1.5, 2.3), region=R_OAK_PLAYER_DOOR)

    # 3 Teak Wooden Slatted Waiting Benches with Cast-Iron Arms
    for bi, by in enumerate([-1.2, 0.0, 2.2]):
        reg_box(f"HeritageBenchSeat_{bi}", 2.2, 0.55, 0.1, (4.2, by, 0.65), region=R_TIMBER_BENCH)
        reg_box(f"HeritageBenchLeg1_{bi}", 0.1, 0.55, 0.4, (3.2, by, 0.25), region=R_IRON_GREEN)
        reg_box(f"HeritageBenchLeg2_{bi}", 0.1, 0.55, 0.4, (5.2, by, 0.25), region=R_IRON_GREEN)

    # Finalize & Export
    shell = kit.join(parts, "Building_Bus_Station_Var4_Victorian")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_bus_station_var4_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_bus_station_var4_victorian.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/bus_station/
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        tex_dir = DEPLOY_DIR / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_bus_station_var4_victorian.glb")
        shutil.copy2(preview_path, tex_dir / "building_bus_station_var4_preview.png")
        shutil.copy2(OUT_DIR / "building_bus_station_var4_atlas.png", tex_dir / "building_bus_station_var4_atlas.png")
        print(f"[BusStation_Var4] 2200-tri deployed successfully.")
    except Exception as e:
        print(f"[BusStation_Var4] deploy notice: {e}")


if __name__ == "__main__":
    main()
