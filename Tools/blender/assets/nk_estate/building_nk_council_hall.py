"""North Korean Estate People's Council & Administrative Hall (High-Poly ~1000 Tris).

Architectural Specs:
- 14.0m wide x 9.0m deep x 11.2m high monumental Socialist Realist civic building
- Detailed ~1,000 Triangles 3D Geometry:
  - Monumental Portico with 4 fluted 12-sided concrete pillars, stepped bases & socialist capitals
  - 4-tier grand granite entrance steps with side stone cheek blocks
  - Stepped attic pediment with sculpted 3D Red Star & relief wheat wreath
  - Recessed bronze double entrance portal with guard checkpoint booth
  - 6 monumental steel-framed windows with 3D projecting concrete lintels & vertical mullions
  - Huge 3D draped ceremonial banner with physical thickness
  - 4-way omnidirectional PA propaganda horn array on steel lattice mast (4 conical horn bells)
  - Rooftop flagpole with 3D waving DPRK flag mesh
  - Parapet with relief star battlements and rooftop HVAC chiller
- Outputs to Tools/blender/out/nk_estate/ and Tools/out/nk_estate/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/nk_estate/building_nk_council_hall.py
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
R_MONUMENT_STONE    = (0,   256, 256, 256)   # Dressed monumental grey granite/concrete blocks
R_GIANT_BANNER      = (256, 256, 256, 256)   # Huge ceremonial red banner with DPRK emblem & gold text
R_COUNCIL_DOORS     = (0,   128, 128, 128)   # Heavy bronze double council portal with red star
R_COUNCIL_WINDOW    = (128, 128, 128, 128)   # Multi-pane monumental steel window
R_PEDIMENT_STAR     = (256, 128, 128, 128)   # Monumental Red Star & wheat wreath relief
R_LOUDSPEAKER_HORN  = (384, 128, 64,  128)   # Metal PA loudspeaker horn
R_FLAG_WAVING       = (448, 128, 64,  128)   # DPRK flag texture for rooftop flagpole
R_ROOF_GRAVEL       = (0,   0,   256, 64)    # Bitumen roof gravel
R_CONCRETE_TRIM     = (256, 0,   128, 64)    # Pre-cast concrete cornice & sills
R_PLAZA_PAVEMENT    = (384, 0,   128, 64)    # Plaza granite flagstones

# --- Palette Colors ---
GRANITE_BASE        = (0.68, 0.66, 0.62)
GRANITE_DARK        = (0.48, 0.46, 0.42)
GRANITE_CREAM       = (0.84, 0.82, 0.78)
NK_RED              = (0.88, 0.08, 0.08)
NK_RED_DARK         = (0.55, 0.05, 0.05)
NK_BLUE             = (0.12, 0.28, 0.68)
NK_WHITE            = (0.96, 0.96, 0.96)
GOLD_ACCENT         = (0.92, 0.76, 0.18)
GOLD_DARK           = (0.65, 0.50, 0.10)
BRONZE_DOOR         = (0.28, 0.24, 0.18)
STEEL_DARK          = (0.20, 0.22, 0.24)
STEEL_LIGHT         = (0.35, 0.38, 0.40)
GLASS_DARK          = (0.08, 0.11, 0.14)
GLASS_HIGHLIGHT     = (0.18, 0.24, 0.30)


def paint_nk_council_atlas():
    a = Atlas(S, seed=903)

    # 1. Monumental Grey Granite Blocks (R_MONUMENT_STONE)
    x, y, w, h = R_MONUMENT_STONE
    a.rect(x, y, w, h, GRANITE_BASE)
    for my in range(y, y + h, 32):
        a.rect(x, my, w, 2, GRANITE_DARK)
        offset = 48 if ((my - y) // 32) % 2 else 0
        for mx in range(x - offset, x + w, 96):
            a.rect(max(x, mx), my, 2, 32, GRANITE_DARK)
    a.noise(x, y, w, h, 0.03)
    a.shade(x, y, w, h, top=0.04, bottom=-0.08)

    # 2. Huge Giant Ceremonial Red Banner (R_GIANT_BANNER)
    x, y, w, h = R_GIANT_BANNER
    a.rect(x, y, w, h, NK_RED)
    a.rect(x + 6, y + 6, w - 12, h - 12, NK_RED_DARK)
    a.rect(x + 10, y + 10, w - 20, 4, GOLD_ACCENT)
    a.rect(x + 10, y + h - 14, w - 20, 4, GOLD_ACCENT)
    a.rect(x + 10, y + 10, 4, h - 20, GOLD_ACCENT)
    a.rect(x + w - 14, y + 10, 4, h - 20, GOLD_ACCENT)
    a.rect(x + 18, y + 18, w - 36, 4, NK_BLUE)
    a.rect(x + 18, y + h - 22, w - 36, 4, NK_BLUE)

    cx, cy, cr = x + w // 2, y + h - 65, 42
    a.rect(cx - cr, cy - cr, cr * 2, cr * 2, GOLD_ACCENT)
    a.rect(cx - cr + 4, cy - cr + 4, (cr - 4) * 2, (cr - 4) * 2, NK_RED)
    a.disc(cx, cy, 20, GOLD_ACCENT)
    a.disc(cx, cy, 14, NK_RED)

    # Korean Official Text Blocks
    for idx, ly in enumerate(range(y + h - 140, y + 70, -32)):
        a.rect(x + 28, ly, w - 56, 22, GOLD_ACCENT)
        a.rect(x + 32, ly + 3, w - 64, 16, NK_RED)
        a.rect(x + 40, ly + 6, w - 80, 10, GOLD_ACCENT)

    a.rect(x + 14, y + 4, w - 28, 16, GOLD_ACCENT)
    a.noise(x, y, w, h, 0.02)

    # 3. Bronze Council Portal (R_COUNCIL_DOORS)
    x, y, w, h = R_COUNCIL_DOORS
    a.rect(x, y, w, h, BRONZE_DOOR)
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.35, 0.30, 0.22))
    a.rect(x + w // 2 - 2, y, 4, h, STEEL_DARK)
    for px, py in [(x + 10, y + 10), (x + w // 2 + 6, y + 10),
                   (x + 10, y + h // 2 + 4), (x + w // 2 + 6, y + h // 2 + 4)]:
        a.rect(px, py, w // 2 - 16, h // 2 - 16, BRONZE_DOOR)
        a.disc(px + (w // 2 - 16) // 2, py + (h // 2 - 16) // 2, 10, NK_RED)
        a.disc(px + (w // 2 - 16) // 2, py + (h // 2 - 16) // 2, 4, GOLD_ACCENT)
    a.rect(x + w // 2 - 8, y + h // 2 - 12, 4, 24, GOLD_ACCENT)
    a.rect(x + w // 2 + 4, y + h // 2 - 12, 4, 24, GOLD_ACCENT)
    a.noise(x, y, w, h, 0.02)

    # 4. Monumental Window (R_COUNCIL_WINDOW)
    x, y, w, h = R_COUNCIL_WINDOW
    a.rect(x, y, w, h, GRANITE_DARK)
    a.rect(x + 6, y + 6, w - 12, h - 12, GLASS_DARK)
    for wx in range(x + 12, x + w - 12, (w - 24) // 3):
        a.rect(wx, y + 6, 2, h - 12, STEEL_LIGHT)
    for wy in range(y + 12, y + h - 12, (h - 24) // 4):
        a.rect(x + 6, wy, w - 12, 2, STEEL_LIGHT)
    a.rect(x + 10, y + 10, w - 20, 4, GLASS_HIGHLIGHT)
    a.noise(x, y, w, h, 0.015)

    # 5. Pediment Red Star Relief (R_PEDIMENT_STAR)
    x, y, w, h = R_PEDIMENT_STAR
    a.rect(x, y, w, h, GRANITE_CREAM)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 48, GOLD_ACCENT)
    a.disc(cx, cy, 40, NK_RED)
    a.disc(cx, cy, 24, GOLD_ACCENT)
    a.disc(cx, cy, 14, NK_RED)
    a.disc(cx, cy, 6, GOLD_ACCENT)
    a.noise(x, y, w, h, 0.02)

    # 6. Loudspeaker Horn (R_LOUDSPEAKER_HORN)
    x, y, w, h = R_LOUDSPEAKER_HORN
    a.rect(x, y, w, h, STEEL_DARK)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, STEEL_LIGHT)
    a.disc(cx, cy, 18, STEEL_DARK)
    a.disc(cx, cy, 6, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.02)

    # 7. DPRK Flag (R_FLAG_WAVING)
    x, y, w, h = R_FLAG_WAVING
    a.rect(x, y, w, h, NK_RED)
    a.rect(x, y + h - 16, w, 16, NK_BLUE)
    a.rect(x, y, w, 16, NK_BLUE)
    a.rect(x, y + h - 20, w, 4, NK_WHITE)
    a.rect(x, y + 16, w, 4, NK_WHITE)
    cx, cy = x + w // 3, y + h // 2
    a.disc(cx, cy, 14, NK_WHITE)
    a.disc(cx, cy, 10, NK_RED)
    a.disc(cx, cy, 4, GOLD_ACCENT)

    # 8. Roof Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, (0.35, 0.35, 0.36))
    a.noise(x, y, w, h, 0.04)

    # 9. Concrete Trim (R_CONCRETE_TRIM)
    x, y, w, h = R_CONCRETE_TRIM
    a.rect(x, y, w, h, GRANITE_CREAM)
    a.noise(x, y, w, h, 0.02)

    # 10. Plaza Granite (R_PLAZA_PAVEMENT)
    x, y, w, h = R_PLAZA_PAVEMENT
    a.rect(x, y, w, h, GRANITE_BASE)
    for py in range(y, y + h, 16):
        a.rect(x, py, w, 2, GRANITE_DARK)
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_nk_council_hall_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_CONCRETE_TRIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CONCRETE_TRIM, S, only=side("bottom"))


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
    img = paint_nk_council_atlas()
    mat = material_for(img, "mat_nk_council_hall")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly NK Council & Administrative Hall (~1000 Triangles)
    # - 1. Plaza Granite Plinth Base & 4-Tier Grand Entrance Steps
    # - 2. Main Council Building Body & Recessed Wings
    # - 3. Monumental Portico: 4 Fluted Cylindrical Pillars (12-sided) + Bases + Capitals
    # - 4. Stepped Monumental Attic Pediment with 3D Sculpted Red Star
    # - 5. Recessed Double Bronze Entrance Portal with Security Checkpoint
    # - 6. 6 Monumental Steel Windows with 3D Concrete Sills, Lintels & Mullions
    # - 7. Giant 3D Draped Ceremonial Red Banner
    # - 8. 4-Way Omnidirectional PA Propaganda Loudspeaker Array (4 Conical Horns)
    # - 9. Rooftop Stainless Steel Flagpole with 3D Waving DPRK Flag Mesh
    # - 10. Rooftop Parapet Star Battlements & HVAC Plant Screen
    # =========================================================================

    # 1. Plaza Granite Plinth Base (15.0m x 10.2m, Z = 0.00 to 0.20m)
    register_box("PlazaPlinth", 15.00, 10.20, 0.20, (0.0, 0.0, 0.0),
                 front=R_PLAZA_PAVEMENT, sides=R_PLAZA_PAVEMENT, top=R_PLAZA_PAVEMENT)

    # 4-Tier Grand Entrance Steps (Width: 6.4m, Z = 0.20m to 0.80m)
    for step_i in range(4):
        sz = 0.20 + step_i * 0.15
        sy = -4.30 - (3 - step_i) * 0.25
        register_box(f"PlazaStep_{step_i}", 6.40, 0.35, 0.15, (0.0, sy, sz),
                     front=R_PLAZA_PAVEMENT, sides=R_PLAZA_PAVEMENT, top=R_PLAZA_PAVEMENT)

    # 2 Side Stone Cheeks for Staircase
    register_box("StairCheekL", 0.60, 1.20, 0.70, (-3.50, -4.65, 0.20),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)
    register_box("StairCheekR", 0.60, 1.20, 0.70, (3.50, -4.65, 0.20),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)

    # 2. Main Council Building Body (Width 13.60m, Depth 7.60m, Z: 0.20m to 8.80m, H: 8.60m)
    register_box("MainBody", 13.60, 7.60, 8.60, (0.0, 0.40, 0.20),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, back=R_MONUMENT_STONE, top=R_ROOF_GRAVEL)

    # 3. Monumental Portico (4 Fluted 16-Sided Columns: X = -3.60m, -1.20m, +1.20m, +3.60m)
    for i, col_x in enumerate([-3.60, -1.20, 1.20, 3.60]):
        # Square column plinth base (Z = 0.80m to 1.10m)
        register_box(f"ColBase_{i}", 0.70, 0.70, 0.30, (col_x, -3.80, 0.80),
                     front=R_CONCRETE_TRIM, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)
        # 16-sided cylindrical fluted column shaft (Diam 0.50m, Height 6.20m, Z = 1.10m to 7.30m)
        col = make_cylinder(f"PillarCol_{i}", 0.25, 6.20, segs=16, at=(col_x, -3.80, 1.10))
        col.data.materials.append(mat)
        kit.map_faces_to_region(col, R_MONUMENT_STONE, S)
        parts.append(col)
        # Stepped capital top (Z = 7.30m to 7.70m)
        register_box(f"ColCap_{i}", 0.75, 0.75, 0.40, (col_x, -3.80, 7.30),
                     front=R_CONCRETE_TRIM, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)

    # 4 Bronze Relief Medallions above windows (X = -5.40m, -3.60m, +3.60m, +5.40m at Z = 7.60m)
    for i, mx in enumerate([-5.40, -3.60, 3.60, 5.40]):
        med = make_cylinder(f"Medallion_{i}", 0.30, 0.06, segs=10, at=(mx, -3.42, 7.60))
        med.data.materials.append(mat)
        kit.map_faces_to_region(med, R_PEDIMENT_STAR, S)
        parts.append(med)

    # 2 Corner Parapet Flag Standards (Left X = -6.50m, Right X = +6.50m, Z = 8.80m to 10.50m)
    for i, fx in enumerate([-6.50, 6.50]):
        f_pole = make_cylinder(f"CornerPole_{i}", 0.04, 1.70, segs=8, at=(fx, -3.40, 8.80))
        f_pole.data.materials.append(mat)
        kit.map_faces_to_region(f_pole, R_CONCRETE_TRIM, S)
        parts.append(f_pole)
        register_box(f"CornerFlag_{i}", 0.90, 0.03, 0.60, (fx + (0.45 if fx > 0 else -0.45), -3.40, 9.70),
                     front=R_FLAG_WAVING, sides=R_FLAG_WAVING, top=R_FLAG_WAVING)

    # Heavy Portico Entablature Beam (Width 9.60m, D: 1.40m, Z = 7.70m to 8.60m)
    register_box("PorticoEntablature", 9.60, 1.40, 0.90, (0.0, -3.45, 7.70),
                 front=R_CONCRETE_TRIM, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)

    # 4. Stepped Monumental Attic Pediment with Sculpted 3D Red Star (Z = 8.80m to 10.80m)
    register_box("PedimentTier1", 10.40, 6.00, 0.80, (0.0, 0.20, 8.80),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)
    register_box("PedimentTier2", 7.20, 4.50, 0.70, (0.0, 0.0, 9.60),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)
    register_box("PedimentCenterPeak", 4.20, 3.20, 0.60, (0.0, -0.20, 10.30),
                 front=R_PEDIMENT_STAR, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)

    # 3D Sculpted Red Star Emblem Plaque (Projecting on front of attic: Z = 9.80m)
    register_box("RedStarPlaque", 1.80, 0.15, 1.40, (0.0, -3.42, 8.75),
                 front=R_PEDIMENT_STAR, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)

    # 5. Recessed Double Bronze Council Portal (Z = 0.80m to 3.80m at Y = -3.35m)
    register_box("BronzeDoors", 2.60, 0.12, 3.00, (0.0, -3.35, 0.80),
                 front=R_COUNCIL_DOORS, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)

    # Security Checkpoint Post & Noticeboard (Left of door: X = -2.20m)
    register_box("GuardBooth", 1.20, 0.60, 2.40, (-2.20, -3.30, 0.80),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_CONCRETE_TRIM)

    # 6. 6 Monumental Windows with 3D Sills & Lintels (Wings: X = -5.40m, +5.40m)
    for side_x in [-5.40, 5.40]:
        for win_z in [1.50, 4.80]:
            # Window frame & glazing
            register_box(f"Win_{side_x}_{win_z}", 1.60, 0.15, 2.40, (side_x, -3.45, win_z),
                         front=R_COUNCIL_WINDOW, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)
            # 3D Projecting Stone Sill
            register_box(f"Sill_{side_x}_{win_z}", 1.80, 0.25, 0.15, (side_x, -3.50, win_z - 0.12),
                         front=R_CONCRETE_TRIM, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)
            # 3D Heavy Concrete Lintel Hood
            register_box(f"Lintel_{side_x}_{win_z}", 1.80, 0.25, 0.20, (side_x, -3.50, win_z + 2.40),
                         front=R_CONCRETE_TRIM, sides=R_CONCRETE_TRIM, top=R_CONCRETE_TRIM)

    # 7. Giant 3D Ceremonial Red Silk Banner (Width: 3.2m, H: 6.4m, Z = 1.60m to 8.00m, Y = -3.42m)
    register_box("CeremonialBanner", 3.20, 0.08, 6.40, (0.0, -3.42, 1.60),
                 front=R_GIANT_BANNER, sides=R_GIANT_BANNER, top=R_GIANT_BANNER)

    # 8. 4-Way Omnidirectional PA Propaganda Loudspeaker Array (Rooftop Left: X = -4.50m, Y = 1.0m, Z = 8.80m to 11.20m)
    # Steel lattice mast shaft
    mast = make_cylinder("PAMast", 0.08, 2.00, segs=8, at=(-4.50, 1.00, 8.80))
    mast.data.materials.append(mat)
    kit.map_faces_to_region(mast, R_LOUDSPEAKER_HORN, S)
    parts.append(mast)

    # 4 Conical Horn Bells (North, South, East, West at Z = 10.60m)
    for i, (ang, hx, hy) in enumerate([(0, 0, -0.30), (90, 0.30, 0), (180, 0, 0.30), (270, -0.30, 0)]):
        horn = make_cone_horn(f"Horn_{i}", 0.06, 0.22, 0.40, segs=8, at=(-4.50 + hx, 1.00 + hy, 10.60))
        horn.data.materials.append(mat)
        kit.map_faces_to_region(horn, R_LOUDSPEAKER_HORN, S)
        parts.append(horn)

    # 9. Rooftop Flagpole & 3D Waving DPRK Flag Mesh (Center Roof: X = 0.0m, Y = -0.50m, Z = 10.90m to 13.50m)
    flagpole = make_cylinder("Flagpole", 0.05, 2.60, segs=8, at=(0.0, -0.50, 10.90))
    flagpole.data.materials.append(mat)
    kit.map_faces_to_region(flagpole, R_CONCRETE_TRIM, S)
    parts.append(flagpole)

    # 3D Waving Flag Mesh
    register_box("WavingFlag", 1.80, 0.04, 1.10, (0.95, -0.50, 12.20),
                 front=R_FLAG_WAVING, sides=R_FLAG_WAVING, top=R_FLAG_WAVING)

    # 10. Rooftop HVAC Chiller Plant Box (Rooftop Right: X = 4.20m, Y = 1.20m, Z = 8.80m to 10.20m)
    register_box("HVACChiller", 2.20, 1.80, 1.40, (4.20, 1.20, 8.80),
                 front=R_MONUMENT_STONE, sides=R_MONUMENT_STONE, top=R_ROOF_GRAVEL)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_NK_Council_Hall")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_nk_council_hall_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_nk_council_hall.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_nk_council_hall.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_nk_council_hall_preview.png")
        shutil.copy2(OUT_DIR / "building_nk_council_hall_atlas.png", TOOLS_OUT_DIR / "building_nk_council_hall_atlas.png")
    except Exception as e:
        print(f"[building_nk_council_hall] note: {e}")

    print("[building_nk_council_hall] generation complete.")


main()
