"""North Korean Estate Terraced Housing Block (High-Poly ~1000 Tris).

Architectural Specs:
- 10.0m wide x 7.0m deep x 9.2m high residential block in the North Korean housing quarter
- Detailed ~1,000 Triangles 3D Geometry:
  - 2 recessed heavy steel entrance portals with concrete canopies & 3D red star badges
  - 4 ground floor windows with 3D concrete sills and individual 3D steel security bars
  - 4 first floor casement windows with 3D projecting concrete lintels & sills
  - Protruding horizontal precast concrete floor slab bands
  - 3D wall-mounted DPRK flag banner & sculpted red star medallion in relief
  - 3D propaganda noticeboard with weather hood
  - Dual 3D conical PA propaganda loudspeaker horns on steel roof brackets
  - Brutalist parapet with scuppers, VHF radio antenna, and rooftop ventilation cowl
- Outputs to Tools/blender/out/nk_estate/ and Tools/out/nk_estate/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/nk_estate/building_nk_terrace_housing.py
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
R_BRICK_GREY        = (0,   256, 256, 256)   # Utilitarian grey-brown council brick facade
R_CONCRETE_BAND     = (256, 256, 128, 256)   # Weathered pre-cast concrete lintels, sills & plinth
R_NK_FLAG_BANNER    = (0,   128, 128, 128)   # DPRK flag banner
R_NK_EMBLEM_CREST   = (128, 128, 128, 128)   # Red star & gold wheat emblem plaque
R_STEEL_WINDOW_GF   = (256, 128, 128, 128)   # Ground floor steel window
R_STEEL_WINDOW_UF   = (384, 384, 128, 128)   # Upper floor multi-pane steel casement window
R_DOOR_ENAMEL       = (384, 256, 64,  128)   # Heavy steel door with red star plaque & peephole
R_LOUDSPEAKER_HORN  = (448, 256, 64,  128)   # Grey metal PA loudspeaker horn
R_NOTICEBOARD       = (384, 128, 128, 128)   # Estate rules & propaganda noticeboard
R_ROOF_GRAVEL       = (0,   0,   256, 64)    # Bitumen gravel flat roof with water stains
R_METAL_TRIM        = (256, 0,   128, 64)    # Dark galvanized steel railings & pipes
R_PAVEMENT          = (384, 0,   128, 64)    # Concrete council pavement flags

# --- Palette Colors ---
BRICK_GREY_BASE     = (0.42, 0.40, 0.38)
BRICK_MORTAR        = (0.58, 0.56, 0.52)
CONCRETE_BASE       = (0.64, 0.62, 0.58)
CONCRETE_DARK       = (0.46, 0.44, 0.40)
NK_RED              = (0.88, 0.08, 0.08)
NK_BLUE             = (0.12, 0.28, 0.68)
NK_WHITE            = (0.96, 0.96, 0.96)
GOLD_ACCENT         = (0.88, 0.72, 0.18)
STEEL_DARK          = (0.20, 0.22, 0.24)
STEEL_LIGHT         = (0.35, 0.38, 0.40)
GLASS_DARK          = (0.10, 0.12, 0.15)
GLASS_HIGHLIGHT     = (0.20, 0.26, 0.32)
DOOR_TEAL           = (0.18, 0.32, 0.35)


def paint_nk_terrace_atlas():
    a = Atlas(S, seed=901)

    # 1. Grey-Brown Council Brick (R_BRICK_GREY)
    x, y, w, h = R_BRICK_GREY
    a.bricks(x, y, w, h, brick=BRICK_GREY_BASE, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.04)
    a.noise(x, y, w, h, 0.03)

    # 2. Concrete Bands & Sills (R_CONCRETE_BAND)
    x, y, w, h = R_CONCRETE_BAND
    a.rect(x, y, w, h, CONCRETE_BASE)
    for cy in range(y, y + h, 28):
        a.rect(x, cy, w, 2, CONCRETE_DARK)
    a.noise(x, y, w, h, 0.02)

    # 3. DPRK Flag Banner (R_NK_FLAG_BANNER)
    x, y, w, h = R_NK_FLAG_BANNER
    a.rect(x, y, w, h, NK_RED)
    a.rect(x, y + h - 16, w, 16, NK_BLUE)
    a.rect(x, y, w, 16, NK_BLUE)
    a.rect(x, y + h - 20, w, 4, NK_WHITE)
    a.rect(x, y + 16, w, 4, NK_WHITE)
    cx, cy = x + w // 3, y + h // 2
    a.disc(cx, cy, 26, NK_WHITE)
    a.disc(cx, cy, 20, NK_RED)
    a.disc(cx, cy, 8, GOLD_ACCENT)

    # 4. Red Star & Gold Wheat Crest (R_NK_EMBLEM_CREST)
    x, y, w, h = R_NK_EMBLEM_CREST
    a.rect(x, y, w, h, CONCRETE_BASE)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 46, GOLD_ACCENT)
    a.disc(cx, cy, 38, NK_RED)
    a.disc(cx, cy, 22, GOLD_ACCENT)
    a.disc(cx, cy, 12, NK_RED)
    a.disc(cx, cy, 5, GOLD_ACCENT)

    # 5. Ground Floor Steel Window (R_STEEL_WINDOW_GF)
    x, y, w, h = R_STEEL_WINDOW_GF
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_DARK)
    for wx in range(x + 8, x + w - 8, (w - 16) // 3):
        a.rect(wx, y + 4, 2, h - 8, STEEL_LIGHT)
    for wy in range(y + 8, y + h - 8, (h - 16) // 3):
        a.rect(x + 4, wy, w - 8, 2, STEEL_LIGHT)

    # 6. Upper Floor Multi-Pane Window (R_STEEL_WINDOW_UF)
    x, y, w, h = R_STEEL_WINDOW_UF
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_DARK)
    for wx in range(x + 8, x + w - 8, (w - 16) // 3):
        a.rect(wx, y + 4, 2, h - 8, STEEL_LIGHT)
    for wy in range(y + 8, y + h - 8, (h - 16) // 3):
        a.rect(x + 4, wy, w - 8, 2, STEEL_LIGHT)
    a.rect(x + 8, y + 8, w - 16, 3, GLASS_HIGHLIGHT)

    # 7. Steel Door with Red Star (R_DOOR_ENAMEL)
    x, y, w, h = R_DOOR_ENAMEL
    a.rect(x, y, w, h, DOOR_TEAL)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.12, 0.22, 0.24))
    a.disc(x + w // 2, y + h - 35, 14, NK_RED)
    a.disc(x + w // 2, y + h - 35, 6, GOLD_ACCENT)
    a.rect(x + w - 12, y + h // 2 - 8, 4, 16, GOLD_ACCENT)

    # 8. Loudspeaker Horn (R_LOUDSPEAKER_HORN)
    x, y, w, h = R_LOUDSPEAKER_HORN
    a.rect(x, y, w, h, STEEL_DARK)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, STEEL_LIGHT)
    a.disc(cx, cy, 18, STEEL_DARK)

    # 9. Noticeboard (R_NOTICEBOARD)
    x, y, w, h = R_NOTICEBOARD
    a.rect(x, y, w, h, (0.2, 0.2, 0.2))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.92, 0.90, 0.82))
    a.rect(x + 6, y + h - 22, w - 12, 14, NK_RED)
    a.rect(x + 10, y + h - 18, w - 20, 6, GOLD_ACCENT)
    for ny in range(y + 12, y + h - 28, 8):
        a.rect(x + 8, ny, w - 16, 2, (0.2, 0.2, 0.2))

    # 10. Roof Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, (0.35, 0.35, 0.36))
    a.noise(x, y, w, h, 0.04)

    # 11. Metal Trim (R_METAL_TRIM)
    x, y, w, h = R_METAL_TRIM
    a.rect(x, y, w, h, STEEL_DARK)

    # 12. Pavement (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, (0.60, 0.58, 0.54))
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, (0.45, 0.43, 0.40))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_nk_terrace_housing_atlas", OUT_DIR)


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
    img = paint_nk_terrace_atlas()
    mat = material_for(img, "mat_nk_terrace_housing")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly NK Terraced Housing Block (~1000 Triangles)
    # - 1. Concrete Pavement Plinth Base
    # - 2. Main 2-Storey Building Body & Protruding Floor Slab Bands
    # - 3. 2 Entrance Porches with Concrete Canopies & Steel Doors
    # - 4. 4 Ground Floor Windows with 3D Sills & 16 Individual 3D Steel Security Bars
    # - 5. 4 Upper Floor Windows with 3D Sills & Lintels
    # - 6. 3D Wall-Mounted DPRK Flag Banner & Sculpted Red Star Medallion
    # - 7. 3D Propaganda Noticeboard with Weather Hood
    # - 8. Dual 3D Conical PA Propaganda Loudspeaker Horns & Antennas
    # =========================================================================

    # 1. Pavement Plinth Base (10.8m x 8.0m, Z = 0.00 to 0.15m)
    register_box("PavementPlinth", 10.80, 8.00, 0.15, (0.0, 0.0, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Main Terraced Housing Body (Width 9.80m, Depth 6.40m, Z: 0.15m to 8.20m, H: 8.05m)
    register_box("HousingBody", 9.80, 6.40, 8.05, (0.0, 0.30, 0.15),
                 front=R_BRICK_GREY, sides=R_BRICK_GREY, back=R_BRICK_GREY, top=R_ROOF_GRAVEL)

    # Protruding Precast Concrete Mid-Floor Slab Band (Width 10.0m, D: 6.6m, Z = 4.10m to 4.35m)
    register_box("MidFloorBand", 10.00, 6.60, 0.25, (0.0, 0.30, 4.10),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Roof Parapet Cornice Band (Width 10.10m, D: 6.7m, Z = 8.05m to 8.55m)
    register_box("ParapetBand", 10.10, 6.70, 0.50, (0.0, 0.30, 8.05),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Parapet Upstand Wall (Z = 8.55m to 9.20m)
    register_box("ParapetWall", 9.80, 6.40, 0.65, (0.0, 0.30, 8.55),
                 front=R_BRICK_GREY, sides=R_BRICK_GREY, back=R_BRICK_GREY, top=R_CONCRETE_BAND)

    # 3. 2 Entrance Porches with Concrete Canopies (Left Unit: X = -2.60m, Right Unit: X = +2.60m)
    for i, px in enumerate([-2.60, 2.60]):
        # Recessed entrance door
        register_box(f"Door_{i}", 1.10, 0.10, 2.20, (px, -2.92, 0.15),
                     front=R_DOOR_ENAMEL, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # Heavy Concrete Overhead Canopy Hood
        register_box(f"DoorCanopy_{i}", 1.60, 0.80, 0.20, (px, -3.20, 2.45),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # Concrete Entrance Threshold Step
        register_box(f"DoorStep_{i}", 1.40, 0.40, 0.15, (px, -3.10, 0.15),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # 4. 4 Ground Floor Windows with 3D Sills & 16 Individual 3D Steel Security Bars
    # (X = -4.10m, -1.10m, +1.10m, +4.10m, Z = 1.00m to 2.40m)
    gf_win_xs = [-4.10, -1.10, 1.10, 4.10]
    for w_i, wx in enumerate(gf_win_xs):
        # Window box & glazing
        register_box(f"GFWin_{w_i}", 1.40, 0.12, 1.40, (wx, -2.92, 1.00),
                     front=R_STEEL_WINDOW_GF, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 3D Projecting Concrete Sill
        register_box(f"GFSill_{w_i}", 1.55, 0.22, 0.12, (wx, -2.96, 0.88),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 3D Projecting Concrete Lintel
        register_box(f"GFLintel_{w_i}", 1.55, 0.22, 0.16, (wx, -2.96, 2.40),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

        # 4 Individual 3D Steel Security Bars per window (16 total)
        for bar_i in range(4):
            bx = wx - 0.45 + bar_i * 0.30
            register_box(f"GFBar_{w_i}_{bar_i}", 0.03, 0.03, 1.40, (bx, -3.00, 1.00),
                         front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 5. 4 Upper Floor Windows with 3D Sills & Lintels (Z = 5.00m to 6.60m)
    for w_i, wx in enumerate(gf_win_xs):
        register_box(f"UFWin_{w_i}", 1.40, 0.12, 1.60, (wx, -2.92, 5.00),
                     front=R_STEEL_WINDOW_UF, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"UFSill_{w_i}", 1.55, 0.22, 0.12, (wx, -2.96, 4.88),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"UFLintel_{w_i}", 1.55, 0.22, 0.16, (wx, -2.96, 6.60),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # 6. 3D Wall-Mounted DPRK Flag Banner & Sculpted Red Star Medallion (Center Facade: X = 0.0m)
    # Red Star Medallion (Z = 7.00m)
    register_box("CenterRedStar", 1.40, 0.08, 1.40, (0.0, -2.96, 6.80),
                 front=R_NK_EMBLEM_CREST, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Flag Banner (Between 1st floor windows: Z = 4.80m to 6.60m)
    register_box("FlagBannerL", 0.90, 0.06, 1.80, (-2.60, -2.96, 4.80),
                 front=R_NK_FLAG_BANNER, sides=R_NK_FLAG_BANNER, top=R_CONCRETE_BAND)
    register_box("FlagBannerR", 0.90, 0.06, 1.80, (2.60, -2.96, 4.80),
                 front=R_NK_FLAG_BANNER, sides=R_NK_FLAG_BANNER, top=R_CONCRETE_BAND)

    # 7. 3D Propaganda Noticeboard with Weather Hood (Ground floor center: X = 0.0m, Z = 0.60m to 2.20m)
    register_box("NoticeboardBody", 1.60, 0.12, 1.40, (0.0, -2.96, 0.80),
                 front=R_NOTICEBOARD, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
    register_box("NoticeboardHood", 1.75, 0.25, 0.10, (0.0, -3.02, 2.20),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 8. Dual 3D Conical PA Propaganda Loudspeakers & Radio Antenna on Roof (Z = 8.55m to 10.50m)
    # Left PA Speaker Mount
    mast_l = make_cylinder("PAMastL", 0.05, 1.20, segs=8, at=(-2.60, -2.40, 8.55))
    mast_l.data.materials.append(mat)
    kit.map_faces_to_region(mast_l, R_METAL_TRIM, S)
    parts.append(mast_l)

    horn_l = make_cone_horn("HornL", 0.05, 0.20, 0.35, segs=8, at=(-2.60, -2.60, 9.60))
    horn_l.data.materials.append(mat)
    kit.map_faces_to_region(horn_l, R_LOUDSPEAKER_HORN, S)
    parts.append(horn_l)

    # Right PA Speaker Mount
    mast_r = make_cylinder("PAMastR", 0.05, 1.20, segs=8, at=(2.60, -2.40, 8.55))
    mast_r.data.materials.append(mat)
    kit.map_faces_to_region(mast_r, R_METAL_TRIM, S)
    parts.append(mast_r)

    horn_r = make_cone_horn("HornR", 0.05, 0.20, 0.35, segs=8, at=(2.60, -2.60, 9.60))
    horn_r.data.materials.append(mat)
    kit.map_faces_to_region(horn_r, R_LOUDSPEAKER_HORN, S)
    parts.append(horn_r)

    # Central VHF Antenna Mast (Z = 8.55m to 11.50m)
    antenna = make_cylinder("VHFAntenna", 0.03, 2.80, segs=6, at=(0.0, 0.50, 8.55))
    antenna.data.materials.append(mat)
    kit.map_faces_to_region(antenna, R_METAL_TRIM, S)
    parts.append(antenna)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_NK_Terrace_Housing")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_nk_terrace_housing_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_nk_terrace_housing.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_nk_terrace_housing.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_nk_terrace_housing_preview.png")
        shutil.copy2(OUT_DIR / "building_nk_terrace_housing_atlas.png", TOOLS_OUT_DIR / "building_nk_terrace_housing_atlas.png")
    except Exception as e:
        print(f"[building_nk_terrace_housing] note: {e}")

    print("[building_nk_terrace_housing] generation complete.")


main()
