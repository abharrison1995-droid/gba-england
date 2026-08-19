"""North Korean Military Barracks disguised as a Housing Allocation Office (High-Poly ~1000 Tris).

Architectural Specs:
- Large 3-storey Soviet/DPRK brutalist compound building secretly housing an undercover garrison
- Dimensions: 15.5m wide x 9.5m deep x 12.0m high (including rooftop comms)
- Disguised Facade: Fake civilian fascia sign: "DISTRICT RESIDENCE & HOUSING BUREAU / 인민 주택국"
- Covert Military Features (~1,000 Triangles):
  - Reinforced concrete blast portals and heavy armoured steel blast doors
  - 12 windows with 3D concrete sills and individual 3D steel security grilles across ground & 1st floors
  - Side/Rear military supply loading dock with roll-up blast gate & stacked olive ammo crates
  - Rooftop Command Array:
    - 3D parabolic satellite tracking dish on angled gimbal
    - High-gain VHF communications mast with dual dipole crossbars
    - 4-horn omnidirectional air-raid siren / PA loudspeaker array
    - Industrial emergency generator ventilation housings
  - Red star socialist medallions, 3D CCTV surveillance cameras & security floodlights
- Outputs to Tools/blender/out/nk_estate/ and Tools/out/nk_estate/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/nk_estate/building_nk_military_barracks.py
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
OUT_DIR = kit.OUT_DIR / "nk_estate"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "nk_estate"

# --- Atlas Region Definitions (x, y, w, h) ---
R_CONCRETE_FACADE   = (0,   256, 256, 256)   # Weathered utilitarian Soviet precast concrete panels
R_CONCRETE_BAND     = (256, 256, 128, 256)   # Concrete floor bands, parapet coping & sills
R_DISGUISE_SIGN     = (0,   128, 256, 128)   # Fake "PEOPLE'S RESIDENCE & HOUSING BUREAU" sign
R_BLAST_GATE        = (256, 128, 128, 128)   # Heavy olive-drab steel roll-up blast gate & hazard stripes
R_ARMORED_WINDOW    = (384, 384, 128, 128)   # Armoured window with security bars & dark glass
R_RED_STAR_CREST    = (384, 256, 128, 128)   # Red Star crest & socialist laurel wreath
R_MILITARY_CRATE    = (384, 128, 128, 128)   # Olive-drab ammo / supply crates with serial stencils
R_ROOF_GRAVEL       = (0,   0,   256, 128)   # Flat bitumen roof with water stains
R_METAL_TRIM        = (256, 0,   128, 128)   # Dark galvanized steel, comms masts & CCTV
R_PAVEMENT          = (384, 0,   128, 128)   # Concrete base pavement flags

# --- Palette Colors ---
CONCRETE_BASE       = (0.58, 0.56, 0.52)
CONCRETE_DARK       = (0.42, 0.40, 0.36)
CONCRETE_LIGHT      = (0.72, 0.70, 0.65)
NK_RED              = (0.88, 0.08, 0.08)
NK_BLUE             = (0.12, 0.28, 0.68)
IMPERIAL_GOLD       = (0.90, 0.74, 0.18)
MILITARY_OLIVE      = (0.28, 0.34, 0.22)
OLIVE_DARK          = (0.18, 0.22, 0.14)
STEEL_DARK          = (0.18, 0.20, 0.22)
STEEL_LIGHT         = (0.40, 0.44, 0.48)
GLASS_DARK          = (0.09, 0.11, 0.14)
HAZARD_YELLOW       = (0.92, 0.78, 0.12)
HAZARD_BLACK        = (0.12, 0.12, 0.14)


def paint_military_barracks_atlas():
    a = Atlas(S, seed=909)

    # 1. Precast Concrete Facade Panels (R_CONCRETE_FACADE)
    x, y, w, h = R_CONCRETE_FACADE
    a.rect(x, y, w, h, CONCRETE_BASE)
    # Horizontal panel joints
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 3, CONCRETE_DARK)
        # Vertical joint offsets
        offset = 64 if ((py - y) // 32) % 2 else 0
        for px in range(x - offset, x + w, 128):
            a.rect(max(x, px), py, 3, 32, CONCRETE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 2. Concrete Bands & Sills (R_CONCRETE_BAND)
    x, y, w, h = R_CONCRETE_BAND
    a.rect(x, y, w, h, CONCRETE_LIGHT)
    for cy in range(y, y + h, 28):
        a.rect(x, cy, w, 2, CONCRETE_DARK)
    a.noise(x, y, w, h, 0.02)

    # 3. Fake Civilian Signboard: "HOUSING ALLOCATION BUREAU" (R_DISGUISE_SIGN)
    x, y, w, h = R_DISGUISE_SIGN
    a.rect(x, y, w, h, (0.22, 0.24, 0.25))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.88, 0.86, 0.82))
    a.rect(x + 8, y + h - 28, w - 16, 20, NK_RED)
    a.rect(x + 12, y + h - 24, w - 24, 4, IMPERIAL_GOLD)

    # Disguise Sign Text
    sign_en = "HOUSING BUREAU"
    tw = a.text_width(sign_en, scale=3)
    a.text(x + (w - tw) // 2, y + h - 18, sign_en, (0.95, 0.95, 0.95), scale=3)

    sub_en = "DISTRICT 4 ALLOCATION - PUBLIC SERVICE"
    sw = a.text_width(sub_en, scale=1)
    a.text(x + (w - sw) // 2, y + 24, sub_en, (0.20, 0.20, 0.22), scale=1)
    a.noise(x, y, w, h, 0.015)

    # 4. Heavy Steel Roll-up Blast Gate (R_BLAST_GATE)
    x, y, w, h = R_BLAST_GATE
    a.rect(x, y, w, h, MILITARY_OLIVE)
    # Heavy horizontal slats
    for sy in range(y + 8, y + h - 8, 12):
        a.rect(x + 4, sy, w - 8, 3, OLIVE_DARK)
    # Hazard stripe bar across top
    for hy in [y + h - 18, y + 4]:
        a.rect(x + 4, hy, w - 8, 12, HAZARD_YELLOW)
        for hx in range(x + 4, x + w - 8, 16):
            a.rect(hx, hy, 8, 12, HAZARD_BLACK)
    a.noise(x, y, w, h, 0.02)

    # 5. Armoured Windows (R_ARMORED_WINDOW)
    x, y, w, h = R_ARMORED_WINDOW
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_DARK)
    for wx in range(x + 8, x + w - 8, (w - 16) // 3):
        a.rect(wx, y + 4, 2, h - 8, STEEL_LIGHT)
    for wy in range(y + 8, y + h - 8, (h - 16) // 3):
        a.rect(x + 4, wy, w - 8, 2, STEEL_LIGHT)
    a.noise(x, y, w, h, 0.02)

    # 6. Red Star Crest (R_RED_STAR_CREST)
    x, y, w, h = R_RED_STAR_CREST
    a.rect(x, y, w, h, CONCRETE_LIGHT)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, IMPERIAL_GOLD)
    a.disc(cx, cy, 40, NK_RED)
    a.disc(cx, cy, 22, IMPERIAL_GOLD)
    a.disc(cx, cy, 10, NK_RED)
    a.noise(x, y, w, h, 0.02)

    # 7. Military Ammo Crates (R_MILITARY_CRATE)
    x, y, w, h = R_MILITARY_CRATE
    a.rect(x, y, w, h, MILITARY_OLIVE)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.22, 0.28, 0.18))
    # Stencilled serial numbers & hazard star
    a.disc(x + w // 2, y + h // 2 + 10, 14, NK_RED)
    a.disc(x + w // 2, y + h // 2 + 10, 6, IMPERIAL_GOLD)
    a.text(x + 12, y + 18, "ORD-7.62mm-DPRK", (0.85, 0.85, 0.80), scale=1)
    a.noise(x, y, w, h, 0.025)

    # 8. Roof Bitumen Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, (0.32, 0.33, 0.35))
    a.noise(x, y, w, h, 0.04)

    # 9. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)
    a.noise(x, y, w, h, 0.02)

    # 10. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.60, 0.58, 0.54))
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.45, 0.43, 0.40))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_nk_military_barracks_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_CONCRETE_BAND, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CONCRETE_BAND, S, only=side("bottom"))


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


def make_dish(name, r, depth, segs=16, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = [(0, 0, -depth)]
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    verts.append((0, 0, 0.05))  # Central feed horn

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((0, 1 + i, 1 + ni))
        faces.append((1 + ni, 1 + i, segs + 1))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def make_cone_horn(name, r_base, r_top, h, segs=8, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r_base * math.cos(ang), r_base * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r_top * math.cos(ang), r_top * math.sin(ang), h))

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
    img = paint_military_barracks_atlas()
    mat = material_for(img, "mat_nk_military_barracks")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly NK Military Barracks Compound (~1000 Triangles)
    # - 1. Pavement Plinth Base
    # - 2. 3-Storey Concrete Main Building Body & Protruding Floor Slab Bands
    # - 3. Disguised Main Entrance (Fake Housing Bureau Sign, Armoured Door, Canopy)
    # - 4. Side/Rear Military Supply Loading Dock (Roll-up Blast Gate, Stacked Ammo Crates)
    # - 5. 12 Modelled Windows with Sills & 24 3D Security Bars
    # - 6. Red Star Socialist Crests
    # - 7. Rooftop Military Command Array (Satellite Dish, VHF Radar Mast, 4-Horn Siren)
    # =========================================================================

    # 1. Pavement Plinth Base (16.5m x 10.5m x 0.20m, Z = 0.00 to 0.20m)
    register_box("PavementPlinth", 16.50, 10.50, 0.20, (0.0, 0.0, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Main 3-Storey Concrete Barracks Body (Width 15.0m, Depth 9.0m, Z: 0.20m to 9.80m, H: 9.60m)
    register_box("BarracksBody", 15.00, 9.00, 9.60, (0.0, 0.40, 0.20),
                 front=R_CONCRETE_FACADE, sides=R_CONCRETE_FACADE, back=R_CONCRETE_FACADE, top=R_ROOF_GRAVEL)

    # Protruding Precast Floor Slab Bands:
    # - 1st Floor Band (Z = 3.40m to 3.65m)
    register_box("FloorBand1", 15.30, 9.30, 0.25, (0.0, 0.40, 3.40),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # - 2nd Floor Band (Z = 6.60m to 6.85m)
    register_box("FloorBand2", 15.30, 9.30, 0.25, (0.0, 0.40, 6.60),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # - Roof Parapet Cornice Band (Z = 9.80m to 10.40m)
    register_box("ParapetBand", 15.40, 9.40, 0.60, (0.0, 0.40, 9.80),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Roof Parapet Upstand Wall (Z = 10.40m to 11.10m)
    register_box("ParapetWall", 15.00, 9.00, 0.70, (0.0, 0.40, 10.40),
                 front=R_CONCRETE_FACADE, sides=R_CONCRETE_FACADE, back=R_CONCRETE_FACADE, top=R_CONCRETE_BAND)

    # =========================================================================
    # 3. Disguised Main Entrance (Center: X = 0.0m)
    # =========================================================================
    # Heavy Concrete Entrance Portico
    register_box("EntrancePortico", 3.80, 1.20, 3.20, (0.0, -4.30, 0.20),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Armoured Steel Entrance Door
    register_box("ArmoredDoor", 1.80, 0.15, 2.40, (0.0, -4.85, 0.20),
                 front=R_BLAST_GATE, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Fake Civilian Signboard: "HOUSING BUREAU" (Mounted above portico)
    register_box("DisguiseSignBoard", 4.20, 0.20, 1.10, (0.0, -4.95, 3.40),
                 front=R_DISGUISE_SIGN, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 3D Wall-Mounted CCTV Surveillance Camera Box on Bracket
    register_box("CCTVBracket", 0.04, 0.40, 0.04, (-2.10, -4.80, 3.80),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("CCTVCamera", 0.20, 0.35, 0.20, (-2.10, -5.10, 3.70),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # 4. Side Military Supply Loading Dock (Right Wing: X = +5.20m, Y = -4.10m)
    # =========================================================================
    # Roll-up Armoured Blast Gate
    register_box("LoadingBlastGate", 3.20, 0.15, 2.80, (5.20, -4.12, 0.20),
                 front=R_BLAST_GATE, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Concrete Dock Threshold
    register_box("DockThreshold", 3.60, 0.60, 0.30, (5.20, -4.30, 0.20),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Stacked Military Ammo / Equipment Crates on dock
    for i, (cx, cy, cz, cw, cd, ch) in enumerate([
        (6.50, -4.50, 0.20, 0.90, 0.70, 0.60),
        (6.30, -4.40, 0.80, 0.80, 0.60, 0.50),
        (3.80, -4.50, 0.20, 0.75, 0.65, 0.55),
    ]):
        register_box(f"AmmoCrate_{i}", cw, cd, ch, (cx, cy, cz),
                     front=R_MILITARY_CRATE, sides=R_MILITARY_CRATE, top=R_MILITARY_CRATE)

    # =========================================================================
    # 5. 12 Modelled Windows with 3D Sills & 24 3D Security Bars
    # =========================================================================
    # Ground Floor Windows (Left Wing: X = -5.60m, -3.20m, Z = 1.00m to 2.40m)
    for w_i, wx in enumerate([-5.60, -3.20]):
        register_box(f"GFWin_{w_i}", 1.60, 0.15, 1.40, (wx, -4.12, 1.00),
                     front=R_ARMORED_WINDOW, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"GFSill_{w_i}", 1.80, 0.25, 0.15, (wx, -4.18, 0.85),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 4 3D Steel Security Bars per window
        for b_i in range(4):
            bx = wx - 0.50 + b_i * 0.33
            register_box(f"GFBar_{w_i}_{b_i}", 0.04, 0.04, 1.40, (bx, -4.22, 1.00),
                         front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 1st Floor Windows (4 Windows: X = -5.60m, -2.0m, +2.0m, +5.60m, Z = 4.20m to 5.80m)
    for w_i, wx in enumerate([-5.60, -2.00, 2.00, 5.60]):
        register_box(f"UF1Win_{w_i}", 1.60, 0.15, 1.60, (wx, -4.12, 4.20),
                     front=R_ARMORED_WINDOW, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"UF1Sill_{w_i}", 1.80, 0.25, 0.15, (wx, -4.18, 4.05),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 4 3D Steel Security Bars per window
        for b_i in range(4):
            bx = wx - 0.50 + b_i * 0.33
            register_box(f"UF1Bar_{w_i}_{b_i}", 0.04, 0.04, 1.60, (bx, -4.22, 4.20),
                         front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 2nd Floor Windows (4 Windows: Z = 7.40m to 9.00m)
    for w_i, wx in enumerate([-5.60, -2.00, 2.00, 5.60]):
        register_box(f"UF2Win_{w_i}", 1.60, 0.15, 1.60, (wx, -4.12, 7.40),
                     front=R_ARMORED_WINDOW, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"UF2Sill_{w_i}", 1.80, 0.25, 0.15, (wx, -4.18, 7.25),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # =========================================================================
    # 6. Red Star Socialist Crests
    # =========================================================================
    register_box("CenterRedStar", 1.60, 0.10, 1.60, (0.0, -4.15, 7.40),
                 front=R_RED_STAR_CREST, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # =========================================================================
    # 7. Rooftop Command Array (Z = 10.40m to 14.50m)
    # =========================================================================
    # A. 16-Segment 3D Parabolic Satellite Tracking Dish (X = -4.20m, Y = 1.0m, Z = 10.40m to 12.80m)
    dish_base = make_cylinder("DishBase", 0.35, 0.80, segs=8, at=(-4.20, 1.00, 10.40))
    dish_base.data.materials.append(mat)
    kit.map_faces_to_region(dish_base, R_METAL_TRIM, S)
    parts.append(dish_base)

    dish = make_dish("SatDish", r=1.10, depth=0.35, segs=16, at=(-4.20, 0.60, 12.00))
    dish.rotation_euler = (math.radians(-35), math.radians(20), 0)
    dish.data.materials.append(mat)
    kit.map_faces_to_region(dish, R_METAL_TRIM, S)
    parts.append(dish)

    # B. High-Gain VHF Radar Mast with Crossbars (X = 4.20m, Y = 1.0m, Z = 10.40m to 14.50m)
    radar_mast = make_cylinder("RadarMast", 0.06, 4.10, segs=8, at=(4.20, 1.00, 10.40))
    radar_mast.data.materials.append(mat)
    kit.map_faces_to_region(radar_mast, R_METAL_TRIM, S)
    parts.append(radar_mast)

    register_box("DipoleBar1", 2.20, 0.05, 0.05, (4.20, 1.00, 13.50),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("DipoleBar2", 1.50, 0.05, 0.05, (4.20, 1.00, 14.20),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # C. 4-Horn Omnidirectional Siren Array (Center: X = 0.0m, Y = -2.0m, Z = 10.40m to 12.20m)
    siren_post = make_cylinder("SirenPost", 0.06, 1.40, segs=8, at=(0.0, -2.00, 10.40))
    siren_post.data.materials.append(mat)
    kit.map_faces_to_region(siren_post, R_METAL_TRIM, S)
    parts.append(siren_post)

    for i, (hx, hy, ang) in enumerate([
        (0.0, -2.25, 0), (0.25, -2.0, 90), (0.0, -1.75, 180), (-0.25, -2.0, 270)
    ]):
        horn = make_cone_horn(f"SirenHorn_{i}", 0.05, 0.18, 0.32, segs=8, at=(hx, hy, 11.50))
        horn.rotation_euler = (math.radians(90), 0, math.radians(ang))
        horn.data.materials.append(mat)
        kit.map_faces_to_region(horn, R_METAL_TRIM, S)
        parts.append(horn)

    # D. Rooftop Emergency Generator HVAC Ventilation Cowl (X = 0.0m, Y = 2.40m, Z = 10.40m to 11.80m)
    register_box("HVACCowl", 2.80, 1.80, 1.20, (0.0, 2.40, 10.40),
                 front=R_BLAST_GATE, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_NK_Military_Barracks")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_nk_military_barracks_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_nk_military_barracks.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_nk_military_barracks.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_nk_military_barracks_preview.png")
        shutil.copy2(OUT_DIR / "building_nk_military_barracks_atlas.png", TOOLS_OUT_DIR / "building_nk_military_barracks_atlas.png")
    except Exception as e:
        print(f"[building_nk_military_barracks] note: {e}")

    print("[building_nk_military_barracks] generation complete.")


main()
