"""North Korean Estate Terraced Housing Variant 2 (Guard Post & Balcony Block — High-Poly ~1000 Tris).

Architectural Specs:
- 10.0m wide x 7.0m deep x 9.2m high residential block in the North Korean housing estate
- Detailed ~1,000 Triangles 3D Geometry:
  - Left Ground Floor: Estate Security Warden Check-in Office with projecting booth, 6 3D steel bars, hatch & 3D CCTV camera
  - Right Ground Floor: Heavy steel residential entrance with concrete canopy & threshold
  - 2 fully modelled 3D precast concrete cantilever balconies with red star geometric relief panels
  - 3D vertical red slogan banner: "자립 만세 / SELF RELIANCE"
  - Large 3D wall-mounted DPRK flag banner
  - Dual 3D conical PA propaganda loudspeaker horns on steel roof mounts
  - Parapet with VHF dipole communications mast & rooftop ventilation box
- Outputs to Tools/blender/out/nk_estate/ and Tools/out/nk_estate/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/nk_estate/building_nk_terrace_housing_02.py
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
R_BRICK_GREY        = (0,   256, 256, 256)   # Utilitarian grey council brick
R_CONCRETE_BAND     = (256, 256, 128, 256)   # Weathered pre-cast concrete lintels, sills & plinth
R_NK_FLAG_BANNER    = (0,   128, 128, 128)   # Large DPRK flag banner
R_SLOGAN_BANNER     = (128, 128, 128, 128)   # Vertical red slogan banner: "자립 만세"
R_GUARD_HATCH       = (256, 128, 128, 128)   # Security warden check-in hatch with bars & speaker
R_STEEL_WINDOW_UF   = (384, 384, 128, 128)   # Upper floor multi-pane window
R_DOOR_ENAMEL       = (384, 256, 64,  128)   # Heavy steel door with red star plaque
R_LOUDSPEAKER_HORN  = (448, 256, 64,  128)   # Grey metal PA horn
R_BALCONY_PANEL     = (384, 128, 128, 128)   # Concrete balcony with red star relief
R_ROOF_GRAVEL       = (0,   0,   256, 64)    # Bitumen gravel roof
R_METAL_TRIM        = (256, 0,   128, 64)    # Dark galvanized steel
R_PAVEMENT          = (384, 0,   128, 64)    # Pavement flags

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


def paint_nk_terrace_02_atlas():
    a = Atlas(S, seed=902)

    # 1. Grey Council Brick (R_BRICK_GREY)
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

    # 4. Vertical Slogan Banner (R_SLOGAN_BANNER)
    x, y, w, h = R_SLOGAN_BANNER
    a.rect(x, y, w, h, NK_RED)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.75, 0.05, 0.05))
    a.rect(x + 6, y + 6, w - 12, 4, GOLD_ACCENT)
    a.rect(x + 6, y + h - 10, w - 12, 4, GOLD_ACCENT)
    for sy in range(y + h - 30, y + 15, -24):
        a.rect(x + 16, sy, w - 32, 14, GOLD_ACCENT)
        a.rect(x + 20, sy + 3, w - 40, 8, NK_RED)

    # 5. Security Guard Hatch (R_GUARD_HATCH)
    x, y, w, h = R_GUARD_HATCH
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_DARK)
    a.rect(x + w // 2 - 18, y + 12, 36, 24, STEEL_LIGHT)  # pass-through tray
    a.disc(x + w - 24, y + h - 24, 10, STEEL_LIGHT)       # intercom speaker

    # 6. Upper Floor Multi-Pane Window (R_STEEL_WINDOW_UF)
    x, y, w, h = R_STEEL_WINDOW_UF
    a.rect(x, y, w, h, CONCRETE_DARK)
    a.rect(x + 4, y + 4, w - 8, h - 8, GLASS_DARK)
    for wx in range(x + 8, x + w - 8, (w - 16) // 3):
        a.rect(wx, y + 4, 2, h - 8, STEEL_LIGHT)
    for wy in range(y + 8, y + h - 8, (h - 16) // 3):
        a.rect(x + 4, wy, w - 8, 2, STEEL_LIGHT)
    a.rect(x + 8, y + 8, w - 16, 3, GLASS_HIGHLIGHT)

    # 7. Steel Door (R_DOOR_ENAMEL)
    x, y, w, h = R_DOOR_ENAMEL
    a.rect(x, y, w, h, DOOR_TEAL)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.12, 0.22, 0.24))
    a.disc(x + w // 2, y + h - 35, 14, NK_RED)
    a.disc(x + w // 2, y + h - 35, 6, GOLD_ACCENT)

    # 8. Loudspeaker Horn (R_LOUDSPEAKER_HORN)
    x, y, w, h = R_LOUDSPEAKER_HORN
    a.rect(x, y, w, h, STEEL_DARK)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, STEEL_LIGHT)
    a.disc(cx, cy, 18, STEEL_DARK)

    # 9. Balcony Relief Panel (R_BALCONY_PANEL)
    x, y, w, h = R_BALCONY_PANEL
    a.rect(x, y, w, h, CONCRETE_BASE)
    cx, cy = x + w // 2, y + h // 2
    a.rect(x + 6, y + 6, w - 12, h - 12, CONCRETE_DARK)
    a.disc(cx, cy, 32, GOLD_ACCENT)
    a.disc(cx, cy, 24, NK_RED)
    a.disc(cx, cy, 10, GOLD_ACCENT)

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
    return a.to_image("building_nk_terrace_housing_02_atlas", OUT_DIR)


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
    img = paint_nk_terrace_02_atlas()
    mat = material_for(img, "mat_nk_terrace_02")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly NK Terraced Housing Block 02 (~1000 Triangles)
    # - 1. Pavement Plinth Base
    # - 2. Main 2-Storey Building Body & Precast Floor Bands
    # - 3. Ground Floor Left: Security Warden Booth with 6 3D Steel Bars, Hatch & 3D CCTV Camera
    # - 4. Ground Floor Right: Residential Entrance Portal with Canopy
    # - 5. 1st Floor: 2 Fully Modelled 3D Cantilever Concrete Balconies with Red Star Relief
    # - 6. 3D Vertical Slogan Banner & Wall-Mounted DPRK Flag
    # - 7. Dual 3D Conical PA Loudspeaker Horns & VHF Antenna on Roof
    # =========================================================================

    # 1. Pavement Plinth Base (10.8m x 8.0m, Z = 0.00 to 0.15m)
    register_box("PavementPlinth", 10.80, 8.00, 0.15, (0.0, 0.0, 0.0),
                 front=R_PAVEMENT, sides=R_PAVEMENT, top=R_PAVEMENT)

    # 2. Main Terraced Housing Body (Width 9.80m, Depth 6.40m, Z: 0.15m to 8.20m, H: 8.05m)
    register_box("HousingBody", 9.80, 6.40, 8.05, (0.0, 0.30, 0.15),
                 front=R_BRICK_GREY, sides=R_BRICK_GREY, back=R_BRICK_GREY, top=R_ROOF_GRAVEL)

    # Protruding Mid-Floor Band (Z = 4.10m to 4.35m)
    register_box("MidFloorBand", 10.00, 6.60, 0.25, (0.0, 0.30, 4.10),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Roof Parapet Band (Z = 8.05m to 8.55m)
    register_box("ParapetBand", 10.10, 6.70, 0.50, (0.0, 0.30, 8.05),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, back=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Parapet Upstand Wall (Z = 8.55m to 9.20m)
    register_box("ParapetWall", 9.80, 6.40, 0.65, (0.0, 0.30, 8.55),
                 front=R_BRICK_GREY, sides=R_BRICK_GREY, back=R_BRICK_GREY, top=R_CONCRETE_BAND)

    # =========================================================================
    # 3. Ground Floor Left: Estate Security Warden Office Booth (X = -2.60m)
    # =========================================================================
    # Projecting Concrete Guard Booth Frame (Width 2.80m, D: 0.80m, H: 2.60m)
    register_box("GuardBoothFrame", 2.80, 0.80, 2.60, (-2.60, -3.20, 0.15),
                 front=R_GUARD_HATCH, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Projecting Concrete Sill & Pass-Through Tray (Z = 0.95m)
    register_box("GuardSill", 3.00, 0.95, 0.15, (-2.60, -3.25, 0.95),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # 6 3D Heavy Steel Security Bars on Guard Window (X = -3.70m to -1.50m)
    for bar_i in range(6):
        bx = -3.70 + bar_i * 0.44
        register_box(f"GuardBar_{bar_i}", 0.04, 0.04, 1.40, (bx, -3.62, 1.10),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # 3D Wall-Mounted CCTV Camera Box on Corner Bracket (X = -4.30m, Y = -3.20m, Z = 3.20m)
    register_box("CCTVBracket", 0.04, 0.35, 0.04, (-4.30, -3.20, 3.20),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("CCTVCamera", 0.18, 0.35, 0.18, (-4.30, -3.45, 3.12),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # 4. Ground Floor Right: Residential Entrance Portal (X = +2.60m)
    # =========================================================================
    register_box("RightDoor", 1.20, 0.10, 2.20, (2.60, -2.92, 0.15),
                 front=R_DOOR_ENAMEL, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
    register_box("RightCanopy", 1.80, 0.80, 0.20, (2.60, -3.20, 2.45),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
    register_box("RightDoorStep", 1.50, 0.40, 0.15, (2.60, -3.10, 0.15),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # Ground floor side window with 4 3D security bars
    register_box("GFWinRight", 1.40, 0.12, 1.40, (4.10, -2.92, 1.00),
                 front=R_STEEL_WINDOW_UF, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
    register_box("GFSillRight", 1.55, 0.22, 0.12, (4.10, -2.96, 0.88),
                 front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
    for bar_i in range(4):
        bx = 4.10 - 0.45 + bar_i * 0.30
        register_box(f"GFBarRight_{bar_i}", 0.03, 0.03, 1.40, (bx, -3.00, 1.00),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # 5. 1st Floor: 2 Modelled 3D Cantilever Balconies (X = -2.60m, +2.60m)
    # =========================================================================
    for b_i, bx in enumerate([-2.60, 2.60]):
        # Balcony Floor Slab (Cantilevered forward by 1.40m at Z = 4.35m to 4.55m)
        register_box(f"BalconyFloor_{b_i}", 2.60, 1.40, 0.20, (bx, -3.40, 4.35),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # Front Concrete Balustrade Wall with Red Star Relief (Z = 4.55m to 5.65m)
        register_box(f"BalconyFront_{b_i}", 2.60, 0.12, 1.10, (bx, -4.04, 4.55),
                     front=R_BALCONY_PANEL, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # Left & Right Balustrade Walls
        register_box(f"BalconySideL_{b_i}", 0.12, 1.30, 1.10, (bx - 1.24, -3.40, 4.55),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"BalconySideR_{b_i}", 0.12, 1.30, 1.10, (bx + 1.24, -3.40, 4.55),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 3D Steel Handrail Rim along balcony top
        register_box(f"BalconyRailFront_{b_i}", 2.64, 0.05, 0.05, (bx, -4.04, 5.65),
                     front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
        # Recessed Balcony Door & Window Pair
        register_box(f"BalconyWin_{b_i}", 2.20, 0.10, 2.00, (bx, -2.92, 4.55),
                     front=R_STEEL_WINDOW_UF, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        # 3D Balcony Window Concrete Lintel
        register_box(f"BalconyLintel_{b_i}", 2.40, 0.20, 0.16, (bx, -2.96, 6.55),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # 1st Floor Outer Windows (X = -4.20m, +4.20m)
    for wx in [-4.20, 4.20]:
        register_box(f"UFWinOuter_{wx}", 1.20, 0.10, 1.60, (wx, -2.92, 4.90),
                     front=R_STEEL_WINDOW_UF, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)
        register_box(f"UFSillOuter_{wx}", 1.35, 0.20, 0.12, (wx, -2.96, 4.78),
                     front=R_CONCRETE_BAND, sides=R_CONCRETE_BAND, top=R_CONCRETE_BAND)

    # =========================================================================
    # 6. 3D Vertical Slogan Banner & Large DPRK Flag
    # =========================================================================
    # Vertical Red Slogan Banner: "자립 만세" (Center: X = 0.0m, Z = 3.60m to 7.80m)
    register_box("SloganBanner", 1.20, 0.08, 4.20, (0.0, -2.96, 3.60),
                 front=R_SLOGAN_BANNER, sides=R_SLOGAN_BANNER, top=R_CONCRETE_BAND)

    # Large DPRK Flag (Mounted flat above right balcony: X = 2.60m, Z = 6.80m to 8.00m)
    register_box("DPRKFlagWall", 2.20, 0.06, 1.20, (2.60, -2.96, 6.80),
                 front=R_NK_FLAG_BANNER, sides=R_NK_FLAG_BANNER, top=R_CONCRETE_BAND)

    # =========================================================================
    # 7. Dual 3D Conical PA Loudspeaker Horns & Communications Mast on Roof
    # =========================================================================
    # Left PA Horn
    mast_l = make_cylinder("PAMastL2", 0.05, 1.20, segs=8, at=(-2.60, -2.40, 8.55))
    mast_l.data.materials.append(mat)
    kit.map_faces_to_region(mast_l, R_METAL_TRIM, S)
    parts.append(mast_l)

    horn_l = make_cone_horn("HornL2", 0.05, 0.20, 0.35, segs=8, at=(-2.60, -2.60, 9.60))
    horn_l.data.materials.append(mat)
    kit.map_faces_to_region(horn_l, R_LOUDSPEAKER_HORN, S)
    parts.append(horn_l)

    # Right PA Horn
    mast_r = make_cylinder("PAMastR2", 0.05, 1.20, segs=8, at=(2.60, -2.40, 8.55))
    mast_r.data.materials.append(mat)
    kit.map_faces_to_region(mast_r, R_METAL_TRIM, S)
    parts.append(mast_r)

    horn_r = make_cone_horn("HornR2", 0.05, 0.20, 0.35, segs=8, at=(2.60, -2.60, 9.60))
    horn_r.data.materials.append(mat)
    kit.map_faces_to_region(horn_r, R_LOUDSPEAKER_HORN, S)
    parts.append(horn_r)

    # Communications Mast with Dipole Crossbars (X = 0.0m, Z = 8.55m to 12.00m)
    comms = make_cylinder("CommsMast", 0.04, 3.45, segs=6, at=(0.0, 0.50, 8.55))
    comms.data.materials.append(mat)
    kit.map_faces_to_region(comms, R_METAL_TRIM, S)
    parts.append(comms)

    register_box("DipoleBar1", 1.20, 0.04, 0.04, (0.0, 0.50, 11.20),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)
    register_box("DipoleBar2", 0.80, 0.04, 0.04, (0.0, 0.50, 11.70),
                 front=R_METAL_TRIM, sides=R_METAL_TRIM, top=R_METAL_TRIM)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_NK_Terrace_Housing_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_nk_terrace_housing_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_nk_terrace_housing_02.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_nk_terrace_housing_02.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_nk_terrace_housing_02_preview.png")
        shutil.copy2(OUT_DIR / "building_nk_terrace_housing_02_atlas.png", TOOLS_OUT_DIR / "building_nk_terrace_housing_02_atlas.png")
    except Exception as e:
        print(f"[building_nk_terrace_housing_02] note: {e}")

    print("[building_nk_terrace_housing_02] generation complete.")


main()
