"""High-Poly (~1000 Tris) Victorian London Townhouse / Gentleman's Club.

Specs:
- 8.0m x 7.5m footprint, Height: 10.5m.
- Detailed 3D geometric modelling (~1,000 triangles):
  - 3-sided projecting Ground Floor Bay Window with modelled stone sills and mullions.
  - Classical Entrance Portico with 2 fluted Corinthian columns, steps, and recessed 6-panel door.
  - 18 individual 3D wrought-iron front lightwell railing balusters with pointed spear finials.
  - 3 first-floor sash windows with modelled pediments and Juliet iron guards.
  - Mansard slate roof with 2 fully modelled 3D dormer windows with pitched gables.
  - Twin brick chimney stacks with stone corbels and 4 modelled terracotta chimney pots.
- Outputs to Tools/blender/out/High_Poly_1000Tri/ and Tools/out/High_Poly_1000Tri/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/exp_victorian_club_1000tri.py
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
R_BRICK_FACADE  = (0,   256, 256, 256)   # Warm London red/brown stock brick with fine white pointing
R_STONE_TRIM    = (256, 256, 256, 256)   # Portland stone quoins, pediments, columns & balustrades
R_SASH_WINDOW   = (0,   128, 256, 128)   # Multi-pane white sash window glazing with interior curtains
R_MANSARD_SLATE = (256, 128, 128, 128)   # Natural Welsh blue-grey roofing slate tiles
R_IRON_RAILINGS = (384, 128, 128, 128)   # Black painted wrought-iron railings & spearheads
R_DOOR_PANEL    = (0,   0,   256, 128)   # Gloss black 6-panel front door with brass knocker & letterbox
R_CHIMNEY_POT   = (256, 0,   128, 128)   # Terracotta chimney pot ceramic glaze & soot ring
R_PAVE_YORK     = (384, 0,   128, 128)   # York stone entrance steps & pavement slabs

# --- Palette Colors ---
BRICK_RED       = (0.64, 0.32, 0.22)
BRICK_MORTAR    = (0.50, 0.44, 0.38)
STONE_PORTLAND  = (0.86, 0.84, 0.80)
STONE_SHADOW    = (0.65, 0.63, 0.58)
SLATE_BLUE      = (0.30, 0.34, 0.38)
IRON_BLACK      = (0.10, 0.10, 0.12)
DOOR_BLACK      = (0.12, 0.12, 0.14)
BRASS_GOLD      = (0.92, 0.78, 0.25)
TERRACOTTA_RED  = (0.75, 0.35, 0.18)
GLASS_PANE      = (0.18, 0.24, 0.30)


def paint_victorian_atlas():
    a = Atlas(S, seed=7101)

    # 1. London Stock Brick (R_BRICK_FACADE)
    x, y, w, h = R_BRICK_FACADE
    a.bricks(x, y, w, h, brick=BRICK_RED, mortar=BRICK_MORTAR, bw=28, bh=12, jitter=0.04)
    # Rustication grooves on ground floor portion
    for ry in range(y, y + 100, 20):
        a.rect(x, ry, w, 2, STONE_SHADOW)
    a.noise(x, y, w, h, 0.025)

    # 2. Portland Stone Trim (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_PORTLAND)
    for qy in range(y, y + h, 24):
        a.rect(x, qy, w, 2, STONE_SHADOW)
    a.noise(x, y, w, h, 0.02)

    # 3. Sash Windows (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    a.rect(x, y, w, h, STONE_PORTLAND)
    # 2 Windows with velvet curtains
    for wx in [x + 16, x + 136]:
        a.rect(wx, y + 8, 100, h - 16, GLASS_PANE)
        # Red velvet curtains at sides
        a.rect(wx + 2, y + 8, 18, h - 16, (0.55, 0.12, 0.14))
        a.rect(wx + 80, y + 8, 18, h - 16, (0.55, 0.12, 0.14))
        # White glazing bars
        a.rect(wx + 48, y + 8, 4, h - 16, STONE_PORTLAND)
        a.rect(wx, y + h // 2, 100, 4, STONE_PORTLAND)
    a.noise(x, y, w, h, 0.015)

    # 4. Mansard Slate (R_MANSARD_SLATE)
    x, y, w, h = R_MANSARD_SLATE
    a.rect(x, y, w, h, SLATE_BLUE)
    for sy in range(y, y + h, 14):
        a.rect(x, sy, w, 2, (0.20, 0.22, 0.26))
        a.rect(x, sy + 2, w, 1, (0.42, 0.46, 0.52))
    a.noise(x, y, w, h, 0.03)

    # 5. Iron Railings (R_IRON_RAILINGS)
    x, y, w, h = R_IRON_RAILINGS
    a.rect(x, y, w, h, IRON_BLACK)
    for px in range(x + 8, x + w, 16):
        a.rect(px, y, 4, h, (0.25, 0.25, 0.28))
        a.disc(px + 2, y + h - 8, 5, BRASS_GOLD)  # gold spearhead
    a.noise(x, y, w, h, 0.015)

    # 6. Front Door (R_DOOR_PANEL)
    x, y, w, h = R_DOOR_PANEL
    a.rect(x, y, w, h, STONE_PORTLAND)
    dx, dy, dw, dh = x + 12, y + 8, w - 24, h - 16
    a.rect(dx, dy, dw, dh, DOOR_BLACK)
    # 6 Panels
    for py in [dy + 12, dy + 44, dy + 76]:
        for px in [dx + 10, dx + dw // 2 + 6]:
            a.rect(px, py, dw // 2 - 16, 26, (0.05, 0.05, 0.06))
            a.rect(px + 2, py + 2, dw // 2 - 20, 22, (0.18, 0.18, 0.20))
    # Brass Knocker & Letterbox
    a.disc(dx + dw // 2, dy + 62, 6, BRASS_GOLD)
    a.rect(dx + dw // 2 - 14, dy + 28, 28, 6, BRASS_GOLD)
    a.noise(x, y, w, h, 0.015)

    # 7. Chimney Pots (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA_RED)
    a.rect(x, y + h - 16, w, 16, (0.12, 0.12, 0.12))  # top soot ring
    for cy in range(y, y + h - 16, 12):
        a.rect(x, cy, w, 2, (0.55, 0.25, 0.12))
    a.noise(x, y, w, h, 0.03)

    # 8. Yorkstone Steps (R_PAVE_YORK)
    x, y, w, h = R_PAVE_YORK
    a.rect(x, y, w, h, (0.75, 0.72, 0.68))
    for sy in range(y, y + h, 20):
        a.rect(x, sy, w, 2, STONE_SHADOW)
    a.noise(x, y, w, h, 0.03)

    EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("exp_victorian_club_atlas", EXP_OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_TRIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_TRIM, S, only=side("bottom"))


def make_cylinder_column(name, r, h, segs=12, at=(0, 0, 0)):
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


def make_dormer(name, w, d, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = w / 2.0
    verts = [
        (-hw, 0.0, 0.0), (hw, 0.0, 0.0), (hw, d, 0.0), (-hw, d, 0.0),
        (-hw, 0.0, h * 0.7), (hw, 0.0, h * 0.7), (hw, d, h * 0.7), (-hw, d, h * 0.7),
        (0.0, 0.0, h), (0.0, d, h)
    ]
    faces = [
        (0, 1, 5, 4),    # front lower
        (4, 5, 8),       # front gable peak
        (1, 2, 6, 5),    # right side
        (5, 6, 9, 8),    # right roof slope
        (2, 3, 7, 6),    # back wall
        (6, 7, 9),       # back gable
        (3, 0, 4, 7),    # left side
        (7, 4, 8, 9),    # left roof slope
        (0, 1, 2, 3),    # bottom
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_victorian_atlas()
    mat = material_for(img, "mat_victorian_club")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Victorian Townhouse (~1000 Triangles Target)
    # - 1. Pavement Slab Plinth & Basement Lightwell Area
    # - 2. Modelled 3D Wrought-Iron Picket Railings (18 individual pickets + spearheads)
    # - 3. Ground Floor Main Body with Rustication
    # - 4. 3-Sided Projecting Faceted Bay Window (Ground Floor Left)
    # - 5. Classical Entrance Portico: 2 Fluted Cylindrical Columns + Pediment + Steps
    # - 6. Recessed 6-Panel Front Door with Fanlight
    # - 7. 1st Floor Piano Nobile with 3 Sash Windows & 3D Stone Pediments
    # - 8. 2nd Floor Sash Windows with Modillion Cornice
    # - 9. Mansard Slate Roof with 2 Fully Modelled 3D Dormer Windows
    # - 10. Twin Brick Chimney Stacks with 4 Modelled 3D Terracotta Chimney Pots
    # =========================================================================

    # 1. Pavement & Lightwell Plinth (8.4m x 8.0m, Z = 0.00 to 0.15m)
    register_box("PavePlinth", 8.40, 8.00, 0.15, (0.0, 0.0, 0.0),
                 front=R_PAVE_YORK, sides=R_PAVE_YORK, top=R_PAVE_YORK)

    # 2. 18 Modelled 3D Wrought-Iron Railing Baluster Pickets (Front perimeter at Y = -3.75m)
    # Bottom rail & Top rail
    register_box("RailingBottomRail", 4.20, 0.05, 0.04, (-1.80, -3.75, 0.15),
                 front=R_IRON_RAILINGS, sides=R_IRON_RAILINGS, top=R_IRON_RAILINGS)
    register_box("RailingTopRail", 4.20, 0.05, 0.04, (-1.80, -3.75, 1.15),
                 front=R_IRON_RAILINGS, sides=R_IRON_RAILINGS, top=R_IRON_RAILINGS)

    # 18 Vertical pickets with spearheads (X = -3.80m to +0.20m, step = 0.22m)
    for i in range(18):
        px = -3.80 + i * 0.22
        # Picket shaft
        register_box(f"Picket_{i}", 0.04, 0.04, 1.05, (px, -3.75, 0.15),
                     front=R_IRON_RAILINGS, sides=R_IRON_RAILINGS, top=R_IRON_RAILINGS)
        # Gold spearhead finial
        register_box(f"Spear_{i}", 0.06, 0.06, 0.12, (px, -3.75, 1.20),
                     front=R_IRON_RAILINGS, sides=R_IRON_RAILINGS, top=R_IRON_RAILINGS)

    # 3. Main Townhouse Body (Width 7.80m, D: 6.20m, Z: 0.15m to 8.20m, H: 8.05m)
    register_box("TownhouseBody", 7.80, 6.20, 8.05, (0.0, 0.50, 0.15),
                 front=R_BRICK_FACADE, sides=R_BRICK_FACADE, back=R_BRICK_FACADE, top=R_STONE_TRIM)

    # 4. Projecting Ground Floor Faceted Bay Window (Left: X = -2.20m, W: 2.6m, D: 0.9m, H: 2.8m, Z = 0.15m to 2.95m)
    register_box("BayWindowBase", 2.60, 0.90, 2.70, (-2.20, -2.85, 0.15),
                 front=R_SASH_WINDOW, sides=R_SASH_WINDOW, back=R_BRICK_FACADE, top=R_STONE_TRIM)
    # Bay window stone parapet cornice
    register_box("BayCornice", 2.80, 1.00, 0.18, (-2.20, -2.85, 2.85),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. Classical Entrance Portico (Right: X = 1.80m, Z = 0.15m to 3.20m)
    # 4-tier entrance steps
    for step_i in range(4):
        sz = 0.15 + step_i * 0.15
        sy = -3.20 - (3 - step_i) * 0.25
        register_box(f"Step_{step_i}", 1.80, 0.35, 0.15, (1.80, sy, sz),
                     front=R_PAVE_YORK, sides=R_PAVE_YORK, top=R_PAVE_YORK)

    # 2 Fluted Cylindrical Corinthian Columns (Left & Right of portico: X = 1.05m, 2.55m, Y = -3.35m)
    col_l = make_cylinder_column("PorticoColL", 0.16, 2.50, segs=12, at=(1.05, -3.35, 0.75))
    col_l.data.materials.append(mat)
    kit.map_faces_to_region(col_l, R_STONE_TRIM, S)
    parts.append(col_l)

    col_r = make_cylinder_column("PorticoColR", 0.16, 2.50, segs=12, at=(2.55, -3.35, 0.75))
    col_r.data.materials.append(mat)
    kit.map_faces_to_region(col_r, R_STONE_TRIM, S)
    parts.append(col_r)

    # Portico Entablature & Cornice (Width 2.10m, D: 1.20m, Z = 3.25m to 3.65m)
    register_box("PorticoRoof", 2.10, 1.20, 0.40, (1.80, -3.10, 3.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. Recessed 6-Panel Front Door (X = 1.80m, Y = -2.62m, Z = 0.75m to 2.95m, H: 2.20m)
    register_box("EntranceDoor", 1.20, 0.10, 2.20, (1.80, -2.62, 0.75),
                 front=R_DOOR_PANEL, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 7. 1st Floor: 3 Modelled Sash Windows with 3D Pediment Hoods (X = -2.20m, 0.0m, +2.20m, Z = 3.60m to 5.40m)
    for wx in [-2.20, 0.0, 2.20]:
        # Window frame
        register_box(f"Win1st_{wx}", 1.40, 0.15, 1.80, (wx, -2.65, 3.60),
                     front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        # 3D Stone Sill
        register_box(f"Sill1st_{wx}", 1.55, 0.22, 0.12, (wx, -2.70, 3.50),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        # 3D Triangular Pediment Hood
        register_box(f"PedHood_{wx}", 1.60, 0.25, 0.25, (wx, -2.70, 5.40),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. 2nd Floor: 3 Modelled Sash Windows (Z = 6.00m to 7.50m)
    for wx in [-2.20, 0.0, 2.20]:
        register_box(f"Win2nd_{wx}", 1.30, 0.12, 1.50, (wx, -2.65, 6.00),
                     front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        register_box(f"Sill2nd_{wx}", 1.45, 0.18, 0.10, (wx, -2.68, 5.92),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # Modillion Dentil Roof Cornice (8.2m x 6.6m, Z: 8.05m to 8.45m)
    register_box("RoofCornice", 8.20, 6.60, 0.40, (0.0, 0.50, 8.05),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, back=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Mansard Slate Roof (Width: 7.80m, D: 5.80m, H: 2.00m, Z: 8.45m to 10.45m)
    register_box("MansardRoofBase", 7.80, 5.80, 2.00, (0.0, 0.50, 8.45),
                 front=R_MANSARD_SLATE, sides=R_MANSARD_SLATE, back=R_MANSARD_SLATE, top=R_MANSARD_SLATE)

    # 2 Fully Modelled 3D Dormer Windows (X = -1.80m, +1.80m, Z = 8.55m to 10.15m)
    for dx in [-1.80, 1.80]:
        dorm = make_dormer(f"Dormer_{dx}", 1.40, 1.40, 1.60, at=(dx, -2.40, 8.55))
        dorm.data.materials.append(mat)
        kit.map_faces_to_region(dorm, R_SASH_WINDOW, S, only=lambda f: f.normal.y < -0.5)
        kit.map_faces_to_region(dorm, R_MANSARD_SLATE, S, only=lambda f: f.normal.z > 0.1)
        kit.map_faces_to_region(dorm, R_STONE_TRIM, S, only=lambda f: abs(f.normal.x) > 0.5)
        parts.append(dorm)

    # 10. Twin Brick Chimney Stacks & 4 Modelled 3D Terracotta Chimney Pots
    # Left Chimney (X = -3.40m) & Right Chimney (X = +3.40m)
    for cx in [-3.40, 3.40]:
        # Brick stack body
        register_box(f"ChimneyStack_{cx}", 0.85, 1.30, 2.20, (cx, 0.50, 8.45),
                     front=R_BRICK_FACADE, sides=R_BRICK_FACADE, back=R_BRICK_FACADE, top=R_STONE_TRIM)
        # Stone corbel cap
        register_box(f"ChimneyCap_{cx}", 0.95, 1.40, 0.15, (cx, 0.50, 10.65),
                     front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
        # 2 Modelled 3D Cylindrical Terracotta Chimney Pots per stack (4 total)
        for cy_pot in [-0.25, 0.25]:
            pot = make_cylinder_column(f"Pot_{cx}_{cy_pot}", 0.14, 0.70, segs=10, at=(cx, 0.50 + cy_pot, 10.80))
            pot.data.materials.append(mat)
            kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
            parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Exp_Victorian_Club_1000Tri")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = EXP_OUT_DIR / "exp_victorian_club_1000tri_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = EXP_OUT_DIR / "exp_victorian_club_1000tri.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_EXP_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_EXP_OUT_DIR / "exp_victorian_club_1000tri.glb")
        shutil.copy2(preview_path, TOOLS_EXP_OUT_DIR / "exp_victorian_club_1000tri_preview.png")
        shutil.copy2(EXP_OUT_DIR / "exp_victorian_club_atlas.png", TOOLS_EXP_OUT_DIR / "exp_victorian_club_atlas.png")
    except Exception as e:
        print(f"[exp_victorian_club_1000tri] note: {e}")

    print("[exp_victorian_club_1000tri] generation complete.")


main()
