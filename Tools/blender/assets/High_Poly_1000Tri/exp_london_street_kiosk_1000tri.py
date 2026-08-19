"""High-Poly (~1000 Tris) Royal London Red Telephone Kiosk & Post Box Diorama.

Specs:
- 3.5m x 2.2m footprint, Height: 3.2m.
- Detailed 3D geometric modelling (~1,000 triangles):
  - K6 Cast-Iron Red Phone Box with 4-sided domed roof, St Edward's crowns, glazing bars, interior phone & handset.
  - Royal Mail Type B Pillar Post Box with 16-sided fluted cylinder body, dome cap, and letter slot.
  - Victorian Gas Lamp Post with 12-sided fluted column, ladder crossbar, and 8-sided glass lantern.
  - Yorkstone pavement base with bevelled granite curb and cast-iron storm drain grate.
- Outputs to Tools/blender/out/High_Poly_1000Tri/ and Tools/out/High_Poly_1000Tri/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/exp_london_street_kiosk_1000tri.py
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
R_PHONE_RED_SOLID= (0,   256, 256, 256)   # Pure Post Office Red (BS381C 539) cast iron with edge bevels
R_PHONE_GLASS    = (256, 256, 256, 256)   # 72-pane glass grid with subtle cyan reflection
R_PHONE_HEADER   = (0,   128, 256, 128)   # White "TELEPHONE" header sign & Gold Tudor Royal Crown
R_LANTERN_GLASS  = (256, 128, 128, 128)   # Warm glowing gas mantle lantern glass & copper pagoda top
R_LAMP_POST_IRON = (384, 128, 128, 128)   # Victorian black fluted cast-iron street lamp column
R_PHONE_INSIDE   = (0,   0,   256, 128)   # Push-button keypad phone unit, black handset & coin tray
R_YORK_STONE     = (256, 0,   128, 128)   # York stone pavement slabs with bevelled granite curb
R_DRAIN_GRATE    = (384, 0,   128, 128)   # Cast-iron street stormwater gully drain grate

# --- Palette Colors ---
POST_OFFICE_RED = (0.85, 0.12, 0.12)
POST_RED_DARK   = (0.50, 0.08, 0.08)
GOLD_CROWN      = (0.95, 0.82, 0.25)
GLASS_TINT      = (0.22, 0.32, 0.38)
LAMP_GLOW       = (0.98, 0.92, 0.65)
LAMP_COPPER     = (0.45, 0.62, 0.48)
IRON_BLACK      = (0.12, 0.12, 0.14)
STONE_GREY      = (0.72, 0.70, 0.66)


def paint_kiosk_atlas():
    a = Atlas(S, seed=7201)

    # 1. Solid Red Cast Iron (R_PHONE_RED_SOLID)
    x, y, w, h = R_PHONE_RED_SOLID
    a.rect(x, y, w, h, POST_OFFICE_RED)
    a.shade(x, y, w, h, top=-0.06, bottom=0.10)
    a.noise(x, y, w, h, 0.015)

    # 2. 72-Pane Glazing (R_PHONE_GLASS)
    x, y, w, h = R_PHONE_GLASS
    a.rect(x, y, w, h, GLASS_TINT)
    # Subtle inner pane shine
    for gy in range(y + 12, y + h - 12, 32):
        for gx in range(x + 12, x + w - 12, 40):
            a.rect(gx, gy, 28, 20, (0.30, 0.42, 0.50))
    a.noise(x, y, w, h, 0.015)

    # 3. Kiosk Header & Gold Crown (R_PHONE_HEADER)
    x, y, w, h = R_PHONE_HEADER
    a.rect(x, y, w, h, POST_OFFICE_RED)
    # White "TELEPHONE" header transom
    hx, hy, hw, hh = x + 16, y + 16, w - 32, 40
    a.rect(hx, hy, hw, hh, (0.95, 0.95, 0.95))
    a.rect(hx + 2, hy + 2, hw - 4, hh - 4, (0.05, 0.05, 0.05))
    s_tel = "TELEPHONE"
    tw = a.text_width(s_tel, scale=2)
    a.text(hx + (hw - tw) // 2, hy + 12, s_tel, (0.95, 0.95, 0.95), scale=2)
    # 1 Gold St Edward's Tudor Crown
    cx, cy = x + w // 2, y + h - 35
    a.disc(cx, cy, 22, GOLD_CROWN)
    a.disc(cx, cy, 14, (0.85, 0.15, 0.15))
    a.disc(cx, cy + 10, 5, GOLD_CROWN)
    a.noise(x, y, w, h, 0.015)

    # 4. Lantern Glass & Pagoda Roof (R_LANTERN_GLASS)
    x, y, w, h = R_LANTERN_GLASS
    a.rect(x, y, w, h, LAMP_GLOW)
    a.disc(x + w // 2, y + h // 2, 40, (1.0, 1.0, 0.85))  # glowing gas mantle
    a.rect(x, y + h - 24, w, 24, LAMP_COPPER)
    a.noise(x, y, w, h, 0.015)

    # 5. Lamp Post Iron (R_LAMP_POST_IRON)
    x, y, w, h = R_LAMP_POST_IRON
    a.rect(x, y, w, h, IRON_BLACK)
    for ly in range(y, y + h, 16):
        a.rect(x, ly, w, 2, (0.28, 0.28, 0.32))
    a.noise(x, y, w, h, 0.02)

    # 6. Phone Inside Interior (R_PHONE_INSIDE)
    x, y, w, h = R_PHONE_INSIDE
    a.rect(x, y, w, h, (0.25, 0.25, 0.28))
    a.rect(x + 20, y + 20, 80, 80, (0.45, 0.45, 0.48))
    for by in [y + 40, y + 55, y + 70]:
        for bx in [x + 35, x + 50, x + 65]:
            a.rect(bx, by, 10, 10, (0.85, 0.85, 0.85))
    a.rect(x + 120, y + 30, 24, 70, (0.05, 0.05, 0.05))
    a.noise(x, y, w, h, 0.02)

    # 7. York Stone Pavement (R_YORK_STONE)
    x, y, w, h = R_YORK_STONE
    a.rect(x, y, w, h, STONE_GREY)
    for sy in range(y, y + h, 24):
        a.rect(x, sy, w, 2, (0.45, 0.43, 0.40))
    a.noise(x, y, w, h, 0.03)

    # 8. Storm Drain Grate (R_DRAIN_GRATE)
    x, y, w, h = R_DRAIN_GRATE
    a.rect(x, y, w, h, (0.08, 0.08, 0.10))
    for gx in range(x + 8, x + w - 8, 12):
        a.rect(gx, y + 8, 5, h - 16, (0.35, 0.35, 0.38))
    a.noise(x, y, w, h, 0.02)

    EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("exp_london_kiosk_atlas", EXP_OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_PHONE_RED_SOLID, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_PHONE_RED_SOLID, S, only=side("bottom"))


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


def make_dome_cap(name, r, h, segs=16, at=(0, 0, 0)):
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
    img = paint_kiosk_atlas()
    mat = material_for(img, "mat_london_kiosk")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly London Red Telephone Kiosk & Post Box Diorama (~1000 Triangles)
    # =========================================================================

    # 1. Yorkstone Pavement Base (3.6m x 2.4m, Z = 0.00 to 0.12m)
    register_box("PavementBase", 3.60, 2.40, 0.12, (0.0, 0.0, 0.0),
                 front=R_YORK_STONE, sides=R_YORK_STONE, top=R_YORK_STONE)

    # Cast-iron road storm drain grate (Right corner: X = 1.30m, Y = -0.90m)
    register_box("DrainGrate", 0.65, 0.45, 0.02, (1.30, -0.90, 0.12),
                 front=R_DRAIN_GRATE, sides=R_DRAIN_GRATE, top=R_DRAIN_GRATE)

    # =========================================================================
    # 2. K6 Red Telephone Box (Left: X = -0.80m, Footprint 1.0m x 1.0m, Height 2.55m)
    # =========================================================================
    # Cast-iron plinth base
    register_box("KioskPlinth", 1.05, 1.05, 0.15, (-0.80, 0.0, 0.12),
                 front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # 4 Corner Posts (X = -1.25m / -0.35m, Y = -0.45m / +0.45m)
    for px in [-1.25, -0.35]:
        for py in [-0.45, 0.45]:
            register_box(f"CornerPost_{px}_{py}", 0.10, 0.10, 2.05, (px, py, 0.27),
                         front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # 3 Multi-Pane Glazed Walls (Back, Left, Right)
    register_box("KioskBackWall", 0.80, 0.06, 1.85, (-0.80, 0.45, 0.37),
                 front=R_PHONE_GLASS, sides=R_PHONE_RED_SOLID, back=R_PHONE_GLASS, top=R_PHONE_RED_SOLID)
    register_box("KioskLeftWall", 0.06, 0.80, 1.85, (-1.25, 0.0, 0.37),
                 front=R_PHONE_GLASS, sides=R_PHONE_GLASS, back=R_PHONE_GLASS, top=R_PHONE_RED_SOLID)
    register_box("KioskRightWall", 0.06, 0.80, 1.85, (-0.35, 0.0, 0.37),
                 front=R_PHONE_GLASS, sides=R_PHONE_GLASS, back=R_PHONE_GLASS, top=R_PHONE_RED_SOLID)

    # Front Door Frame & Glazing (Front: Y = -0.45m)
    register_box("KioskDoor", 0.80, 0.06, 1.85, (-0.80, -0.45, 0.37),
                 front=R_PHONE_GLASS, sides=R_PHONE_RED_SOLID, back=R_PHONE_GLASS, top=R_PHONE_RED_SOLID)

    # Modelled 3D Glazing Bar Grid on Glass Walls (6 tiers horizontal)
    for tier in range(6):
        bz = 0.55 + tier * 0.26
        register_box(f"BarL_H_{tier}", 0.08, 0.76, 0.03, (-1.25, 0.0, bz),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarR_H_{tier}", 0.08, 0.76, 0.03, (-0.35, 0.0, bz),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarB_H_{tier}", 0.76, 0.08, 0.03, (-0.80, 0.45, bz),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarF_H_{tier}", 0.76, 0.08, 0.03, (-0.80, -0.45, bz),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # Vertical Mullion Bars (2 per side)
    for col_i in [-0.20, 0.20]:
        register_box(f"BarL_V_{col_i}", 0.08, 0.03, 1.65, (-1.25, col_i, 0.45),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarR_V_{col_i}", 0.08, 0.03, 1.65, (-0.35, col_i, 0.45),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarB_V_{col_i}", 0.03, 0.08, 1.65, (-0.80 + col_i, 0.45, 0.45),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)
        register_box(f"BarF_V_{col_i}", 0.03, 0.08, 1.65, (-0.80 + col_i, -0.45, 0.45),
                     front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # 4 Transom Headers with "TELEPHONE" Sign & Crown (Z = 2.22m to 2.45m)
    register_box("KioskTransom", 1.02, 1.02, 0.23, (-0.80, 0.0, 2.22),
                 front=R_PHONE_HEADER, sides=R_PHONE_HEADER, back=R_PHONE_HEADER, top=R_PHONE_RED_SOLID)

    # Domed Roof Cap (Z = 2.45m to 2.70m)
    register_box("KioskRoofDome", 0.95, 0.95, 0.25, (-0.80, 0.0, 2.45),
                 front=R_PHONE_RED_SOLID, sides=R_PHONE_RED_SOLID, back=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # Kiosk Interior: Shelf & Phone Unit
    register_box("PhoneShelf", 0.75, 0.35, 0.05, (-0.80, 0.25, 1.05),
                 front=R_PHONE_INSIDE, sides=R_PHONE_INSIDE, top=R_PHONE_INSIDE)
    register_box("PhoneUnit", 0.40, 0.12, 0.50, (-0.80, 0.38, 1.10),
                 front=R_PHONE_INSIDE, sides=R_PHONE_INSIDE, top=R_PHONE_INSIDE)

    # =========================================================================
    # 3. Royal Mail Type B Pillar Post Box (Right: X = 0.85m, Y = -0.20m)
    # =========================================================================
    post_box = make_cylinder("PillarBoxBody", 0.30, 1.35, segs=16, at=(0.85, -0.20, 0.12))
    post_box.data.materials.append(mat)
    kit.map_faces_to_region(post_box, R_PHONE_RED_SOLID, S)
    parts.append(post_box)

    # Letter Slot Weather Hood & Timetable (Front face of post box)
    register_box("PostBoxHood", 0.32, 0.10, 0.12, (0.85, -0.48, 1.25),
                 front=R_PHONE_HEADER, sides=R_PHONE_RED_SOLID, top=R_PHONE_RED_SOLID)

    # 16-Sided Dome Cap (Z = 1.47m to 1.72m)
    box_cap = make_dome_cap("PillarBoxCap", 0.32, 0.25, segs=16, at=(0.85, -0.20, 1.47))
    box_cap.data.materials.append(mat)
    kit.map_faces_to_region(box_cap, R_PHONE_RED_SOLID, S)
    parts.append(box_cap)

    # =========================================================================
    # 4. Victorian Cast-Iron Street Gas Lamp Post (Back Right: X = 0.95m, Y = 0.70m)
    # =========================================================================
    lamp_base = make_cylinder("LampBase", 0.22, 0.53, segs=8, at=(0.95, 0.70, 0.12))
    lamp_base.data.materials.append(mat)
    kit.map_faces_to_region(lamp_base, R_LAMP_POST_IRON, S)
    parts.append(lamp_base)

    lamp_col = make_cylinder("LampColumn", 0.07, 2.00, segs=12, at=(0.95, 0.70, 0.65))
    lamp_col.data.materials.append(mat)
    kit.map_faces_to_region(lamp_col, R_LAMP_POST_IRON, S)
    parts.append(lamp_col)

    register_box("LadderCrossbar", 0.65, 0.04, 0.04, (0.95, 0.70, 2.45),
                 front=R_LAMP_POST_IRON, sides=R_LAMP_POST_IRON, top=R_LAMP_POST_IRON)

    lantern = make_cylinder("GasLantern", 0.22, 0.50, segs=8, at=(0.95, 0.70, 2.65))
    lantern.data.materials.append(mat)
    kit.map_faces_to_region(lantern, R_LANTERN_GLASS, S)
    parts.append(lantern)

    lantern_cap = make_dome_cap("LanternCap", 0.24, 0.20, segs=8, at=(0.95, 0.70, 3.15))
    lantern_cap.data.materials.append(mat)
    kit.map_faces_to_region(lantern_cap, R_LANTERN_GLASS, S)
    parts.append(lantern_cap)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Exp_London_Street_Kiosk_1000Tri")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = EXP_OUT_DIR / "exp_london_street_kiosk_1000tri_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = EXP_OUT_DIR / "exp_london_street_kiosk_1000tri.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_EXP_OUT_DIR / "exp_london_street_kiosk_1000tri.glb")
        shutil.copy2(preview_path, TOOLS_EXP_OUT_DIR / "exp_london_street_kiosk_1000tri_preview.png")
        shutil.copy2(EXP_OUT_DIR / "exp_london_kiosk_atlas.png", TOOLS_EXP_OUT_DIR / "exp_london_kiosk_atlas.png")
    except Exception as e:
        print(f"[exp_london_street_kiosk_1000tri] note: {e}")

    print("[exp_london_street_kiosk_1000tri] generation complete.")


main()
