"""East York Mad Fisherman's Stilted Tidal Hut (High-Poly ~1000 Tris).

Architectural Specs:
- Ramshackle stilted wooden tidal shack over muddy water in East York docklands
- Footprint: 8.5m x 6.5m timber boardwalk deck on heavy pilings, 5.2m total height
- Signboard: Bold, crisp hand-painted wooden fascia sign: "MAD FISHERMAN" (Yellow) / "FRESH BAIT & LIVE EELS" (White)
- Cladding: Weathered driftwood clapperboard planks with green sea moss, rope coils, hanging dried fish & lifebuoys
- Roof: Rusty corrugated sheet metal & mossy cedar shakes with a crooked smoking stovepipe chimney
- Deck: Stilted timber boardwalk with mooring bollards, rope netting, fish traps & bait barrels
- Outputs to Tools/blender/out/east_york/ and Tools/out/east_york/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/building_mad_fisherman_hut.py
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
OUT_DIR = kit.OUT_DIR / "east_york"
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out" / "east_york"

# --- Atlas Region Definitions (x, y, w, h) ---
R_SIGNBOARD         = (0,   384, 512, 128)   # Clear hand-painted "MAD FISHERMAN / FRESH BAIT & LIVE EELS"
R_WOOD_PLANKS       = (0,   128, 256, 256)   # Weathered driftwood clapperboards & sea moss
R_CORRUGATED_ROOF   = (256, 128, 256, 256)   # Rusty corrugated sheet metal & mossy cedar shingles
R_DECK_PLANKS       = (0,   0,   256, 128)   # Stilted boardwalk deck timber
R_NETS_DRIED_FISH   = (256, 0,   128, 128)   # Hanging green fishnets, silver dried fish, red lifebuoy
R_PILING_TIMBER     = (384, 0,   64,  128)   # Wet creosote dock piles & rope coils
R_LANTERN_BAIT      = (448, 0,   64,  128)   # Amber paraffin lantern & rusty bait tins

# --- Palette Colors ---
WOOD_DRIFT_BASE     = (0.52, 0.46, 0.38)
WOOD_DRIFT_DARK     = (0.32, 0.28, 0.22)
WOOD_DRIFT_MOSS     = (0.28, 0.42, 0.25)
ROOF_RUST_BASE      = (0.58, 0.26, 0.16)
ROOF_RUST_DARK      = (0.35, 0.18, 0.12)
ROOF_TIN_GREY       = (0.45, 0.46, 0.48)
DECK_BASE           = (0.48, 0.42, 0.34)
DECK_DARK           = (0.30, 0.26, 0.20)
NET_GREEN           = (0.22, 0.42, 0.32)
FISH_SILVER         = (0.65, 0.68, 0.70)
BUOY_RED            = (0.78, 0.18, 0.12)
SIGN_YELLOW         = (0.96, 0.84, 0.18)
SIGN_WHITE          = (0.95, 0.94, 0.90)


def paint_fisherman_hut_atlas():
    a = Atlas(S, seed=7772)

    # 1. Clear Hand-Painted Signboard (R_SIGNBOARD)
    x, y, w, h = R_SIGNBOARD
    a.rect(x, y, w, h, (0.22, 0.16, 0.10))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.38, 0.30, 0.20))
    # Weathered wood grain on sign
    for sy in range(y + 8, y + h - 8, 12):
        a.rect(x + 6, sy, w - 12, 2, (0.28, 0.22, 0.14))

    # Bold Main Title: "MAD FISHERMAN"
    sign_str = "MAD FISHERMAN"
    tw = a.text_width(sign_str, scale=5)
    tx = x + (w - tw) // 2
    ty = y + h - 18
    a.text(tx + 3, ty - 3, sign_str, (0.10, 0.06, 0.04), scale=5)
    a.text(tx, ty, sign_str, SIGN_YELLOW, scale=5)

    # Subtitle: "FRESH BAIT & LIVE EELS"
    a.rect(x + 24, y + 14, w - 48, 26, (0.15, 0.10, 0.06))
    sub_str = "FRESH BAIT & LIVE EELS"
    sw = a.text_width(sub_str, scale=2)
    sx = x + (w - sw) // 2
    a.text(sx, y + 32, sub_str, SIGN_WHITE, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 2. Weathered Driftwood Planks (R_WOOD_PLANKS)
    x, y, w, h = R_WOOD_PLANKS
    a.rect(x, y, w, h, WOOD_DRIFT_BASE)
    for py in range(y, y + h, 16):
        a.rect(x, py, w, 2, WOOD_DRIFT_DARK)
        for px in range(x + 8, x + w - 16, 32):
            if ((px + py) // 16) % 3 == 0:
                a.rect(px, py + 2, 20, 6, WOOD_DRIFT_MOSS)
    a.noise(x, y, w, h, 0.035)

    # 3. Corrugated Rusty Roof (R_CORRUGATED_ROOF)
    x, y, w, h = R_CORRUGATED_ROOF
    a.rect(x, y, w, h, ROOF_TIN_GREY)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 3, ROOF_RUST_DARK)
        a.rect(x, ry + 3, w, 4, ROOF_RUST_BASE)
        for rx in range(x, x + w, 10):
            a.rect(rx, ry, 2, 14, ROOF_RUST_DARK)
    for my in range(y + 12, y + h - 12, 40):
        for mx in range(x + 8, x + w - 24, 32):
            a.rect(mx, my, 22, 10, WOOD_DRIFT_MOSS)
    a.noise(x, y, w, h, 0.035)

    # 4. Deck Planks (R_DECK_PLANKS)
    x, y, w, h = R_DECK_PLANKS
    a.rect(x, y, w, h, DECK_BASE)
    for px in range(x, x + w, 24):
        a.rect(px, y, 2, h, DECK_DARK)
        a.rect(px + 4, y + 8, 2, 2, (0.15, 0.15, 0.15))
        a.rect(px + 4, y + h - 10, 2, 2, (0.15, 0.15, 0.15))
    a.noise(x, y, w, h, 0.035)

    # 5. Nets & Dried Fish (R_NETS_DRIED_FISH)
    x, y, w, h = R_NETS_DRIED_FISH
    a.rect(x, y, w, h, WOOD_DRIFT_DARK)
    for ny in range(y, y + h, 12):
        a.rect(x, ny, w, 2, NET_GREEN)
    for nx in range(x, x + w, 12):
        a.rect(nx, y, 2, h, NET_GREEN)
    for fx in range(x + 12, x + w - 16, 28):
        a.rect(fx, y + 24, 14, 38, FISH_SILVER)
        a.rect(fx + 2, y + 26, 10, 30, (0.45, 0.48, 0.50))
    # Lifebuoy
    bx, by = x + w - 40, y + h - 40
    a.disc(bx, by, 18, BUOY_RED)
    a.disc(bx, by, 10, (0.95, 0.95, 0.95))
    a.disc(bx, by, 6, WOOD_DRIFT_DARK)
    a.noise(x, y, w, h, 0.02)

    # 6. Timber Pilings (R_PILING_TIMBER)
    x, y, w, h = R_PILING_TIMBER
    a.rect(x, y, w, h, (0.24, 0.20, 0.16))
    for py in range(y, y + h, 14):
        a.rect(x, py, w, 2, (0.14, 0.10, 0.08))
    a.noise(x, y, w, h, 0.03)

    # 7. Lantern & Bait Tins (R_LANTERN_BAIT)
    x, y, w, h = R_LANTERN_BAIT
    a.rect(x, y, w, h, (0.75, 0.42, 0.18))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.98, 0.70, 0.20))
    a.text(x + 8, y + h // 2, "BAIT", (0.15, 0.10, 0.05), scale=1)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_mad_fisherman_hut_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_WOOD_PLANKS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_WOOD_PLANKS, S, only=side("bottom"))


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


def make_pitched_shack_roof(name, w, d, h, overhang=0.45, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hw = (w / 2.0) + overhang
    hd = (d / 2.0) + overhang

    verts = [
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
        (-hw, 0.0, h), (hw, 0.0, h)
    ]
    faces = [
        (0, 1, 2, 3),    # Underside
        (0, 1, 5, 4),    # Front slope
        (1, 2, 5),       # Right gable
        (2, 3, 4, 5),    # Back slope
        (3, 0, 4),       # Left gable
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_fisherman_hut_atlas()
    mat = material_for(img, "mat_mad_fisherman_hut")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly Mad Fisherman's Stilted Hut (~950 Triangles)
    # =========================================================================

    # 1. 8 Heavy Wooden Dock Pilings (Z = 0.00 to 1.40m)
    piling_coords = [
        (-3.80, -2.80), (0.0, -2.80), (3.80, -2.80),
        (-3.80, 0.0), (3.80, 0.0),
        (-3.80, 2.80), (0.0, 2.80), (3.80, 2.80)
    ]
    for i, (px, py) in enumerate(piling_coords):
        pile = make_cylinder(f"Piling_{i}", 0.16, 1.40, segs=10, at=(px, py, 0.0))
        pile.data.materials.append(mat)
        kit.map_faces_to_region(pile, R_PILING_TIMBER, S)
        parts.append(pile)

    # 2. Main Stilted Boardwalk Deck (8.60m x 6.60m x 0.22m at Z = 1.40m)
    register_box("BoardwalkDeck", 8.60, 6.60, 0.22, (0.0, 0.0, 1.40),
                 front=R_DECK_PLANKS, sides=R_DECK_PLANKS, back=R_DECK_PLANKS, top=R_DECK_PLANKS)

    # 3. Main Shack Wooden Body (Width 5.60m, Depth 4.40m, Z: 1.62m to 4.40m, H: 2.78m)
    register_box("ShackBody", 5.60, 4.40, 2.78, (0.40, 0.60, 1.62),
                 front=R_WOOD_PLANKS, sides=R_WOOD_PLANKS, back=R_WOOD_PLANKS, top=R_WOOD_PLANKS)

    # Door & Window Frames on Shack Front
    register_box("ShackDoor", 1.20, 0.10, 2.20, (-0.80, -1.62, 1.62),
                 front=R_WOOD_PLANKS, sides=R_WOOD_PLANKS, top=R_WOOD_PLANKS)
    register_box("ShackWindow", 1.40, 0.10, 1.10, (1.60, -1.62, 2.20),
                 front=R_NETS_DRIED_FISH, sides=R_WOOD_PLANKS, top=R_WOOD_PLANKS)

    # 4. Front Porch Posts & Clear Bold Hand-Painted "MAD FISHERMAN" Signboard
    # Twin timber porch posts supporting sign & eave
    for i, px in enumerate([-1.80, 1.80]):
        post = make_cylinder(f"SignPost_{i}", 0.10, 2.20, segs=8, at=(px, -2.10, 1.62))
        post.data.materials.append(mat)
        kit.map_faces_to_region(post, R_PILING_TIMBER, S)
        parts.append(post)

    # Front fascia signboard mounted prominently across posts (Width 4.40m, H: 0.95m, Z = 2.85m to 3.80m)
    register_box("FasciaSignBoard", 4.40, 0.15, 0.95, (0.0, -2.15, 2.85),
                 front=R_SIGNBOARD, sides=R_PILING_TIMBER, top=R_PILING_TIMBER, back=R_PILING_TIMBER)

    # 5. Shack Pitched Roof with Rusty Corrugated Sheet Metal (Width 6.60m, Depth 5.40m, H: 1.65m, Z = 4.40m)
    roof = make_pitched_shack_roof("CorrugatedRoof", 6.60, 5.40, 1.65, overhang=0.40, at=(0.40, 0.60, 4.40))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_CORRUGATED_ROOF, S, only=lambda f: f.normal.z > 0.05)
    kit.map_faces_to_region(roof, R_WOOD_PLANKS, S, only=lambda f: f.normal.z <= 0.05)
    parts.append(roof)

    # Crooked Stovepipe Chimney (Z = 5.20m to 6.30m)
    chimney = make_cylinder("ChimneyPipe", 0.12, 1.10, segs=8, at=(1.60, 1.20, 5.20))
    chimney.data.materials.append(mat)
    kit.map_faces_to_region(chimney, R_PILING_TIMBER, S)
    parts.append(chimney)

    # 6. Deck Props: Wooden Crates, Bait Barrels, Net Racks & Paraffin Lantern
    # Bait Barrels
    for i, (bx, by) in enumerate([(-2.40, -2.0), (-2.0, -2.2)]):
        barrel = make_cylinder(f"Barrel_{i}", 0.28, 0.70, segs=10, at=(bx, by, 1.62))
        barrel.data.materials.append(mat)
        kit.map_faces_to_region(barrel, R_LANTERN_BAIT, S)
        parts.append(barrel)

    # Fish Crates
    register_box("FishCrate1", 0.80, 0.60, 0.45, (2.60, -2.00, 1.62),
                 front=R_LANTERN_BAIT, sides=R_LANTERN_BAIT, top=R_NETS_DRIED_FISH)
    register_box("FishCrate2", 0.70, 0.50, 0.40, (2.80, -1.30, 1.62),
                 front=R_LANTERN_BAIT, sides=R_LANTERN_BAIT, top=R_NETS_DRIED_FISH)

    # Mooring Bollards along Deck Edge
    for i, (bx, by) in enumerate([(-3.90, -3.0), (3.90, -3.0), (-3.90, 2.9), (3.90, 2.9)]):
        bollard = make_cylinder(f"Bollard_{i}", 0.12, 0.45, segs=8, at=(bx, by, 1.62))
        bollard.data.materials.append(mat)
        kit.map_faces_to_region(bollard, R_PILING_TIMBER, S)
        parts.append(bollard)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Mad_Fisherman_Hut")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_mad_fisherman_hut_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_mad_fisherman_hut.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_mad_fisherman_hut.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_mad_fisherman_hut_preview.png")
        shutil.copy2(OUT_DIR / "building_mad_fisherman_hut_atlas.png", TOOLS_OUT_DIR / "building_mad_fisherman_hut_atlas.png")
    except Exception as e:
        print(f"[building_mad_fisherman_hut] note: {e}")

    print("[building_mad_fisherman_hut] generation complete.")


main()
