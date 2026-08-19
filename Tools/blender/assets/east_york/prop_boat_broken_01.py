"""Broken Wooden Fishing Boat — Variant 01: Beached Hull with Fractured Ribs & Broken Oar.

Specs:
- 3.6m long x 1.45m wide x 0.80m high clinker-built wooden river rowing boat / skiff
- Settled at a slight list in the river mud/water next to the Mad Fisherman's shack
- Structural Damage:
  - Gaping fractured hole in the starboard gunwale with exposed, splintered oak ribs
  - Split floorboards with stagnant bilge water reflection
  - Broken wooden oar snapped in two, resting diagonally across the middle thwart
  - Mossy green water-line weathering, peeled paint, and tangled hemp line on stern.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/prop_boat_broken_01.py
"""

import math
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "east_york"

# --- Atlas Region Definitions (x, y, w, h) ---
R_HULL_PLANKS       = (0,   256, 256, 256)   # Weathered clinker wood planks with mossy waterline
R_INTERIOR_RIBS     = (256, 256, 128, 256)   # Broken oak ribs, frames, and thwart seats
R_BILGE_WATER       = (384, 384, 128, 128)   # Murky stagnant bilge water in hull bottom
R_BROKEN_OAR        = (384, 256, 128, 128)   # Weathered ash wood oar (splintered blade and shaft)
R_MOSS_BARNACLES    = (0,   128, 128, 128)   # Dense green moss, algae, and barnacle crusts
R_ROPE_NETTING      = (128, 128, 128, 128)   # Tangled green hemp rope and net remnants
R_RUST_METAL        = (256, 128, 128, 128)   # Rusted iron rowlocks, keel bands, and nails
R_MUD_BASE          = (0,   0,   256, 128)   # Muddy shoreline silt footprint

# --- Palette Colors ---
WOOD_HULL_BASE      = (0.42, 0.38, 0.30)
WOOD_HULL_DARK      = (0.28, 0.24, 0.18)
WOOD_MOSS_GREEN     = (0.30, 0.38, 0.22)
WOOD_SPLINTER_LIGHT = (0.62, 0.56, 0.44)
BILGE_DARK          = (0.12, 0.18, 0.15)
OAR_WOOD            = (0.58, 0.50, 0.38)
NET_GREEN           = (0.20, 0.40, 0.28)
RUST_IRON           = (0.45, 0.22, 0.14)
MUD_SILT            = (0.22, 0.20, 0.16)


def paint_boat_01_atlas():
    a = Atlas(S, seed=8101)

    # 1. Hull Planks with Waterline Weathering (R_HULL_PLANKS)
    x, y, w, h = R_HULL_PLANKS
    a.rect(x, y, w, h, WOOD_HULL_BASE)
    for py in range(y, y + h, 18):
        a.rect(x, py, w, 2, WOOD_HULL_DARK)
    # Mossy green water-line bottom
    a.rect(x, y, w, 64, WOOD_MOSS_GREEN)
    for mx in range(x, x + w, 16):
        a.rect(mx, y + 50 + (mx % 20), 12, 24, WOOD_MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)
    a.shade(x, y, w, h, top=-0.06, bottom=0.08)

    # 2. Interior Ribs & Thwarts (R_INTERIOR_RIBS)
    x, y, w, h = R_INTERIOR_RIBS
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    for ry in range(y, y + h, 20):
        a.rect(x + 4, ry, w - 8, 8, WOOD_SPLINTER_LIGHT)
        a.rect(x + 4, ry + 8, w - 8, 2, (0.15, 0.12, 0.10))
    a.noise(x, y, w, h, 0.035)

    # 3. Bilge Water (R_BILGE_WATER)
    x, y, w, h = R_BILGE_WATER
    a.rect(x, y, w, h, BILGE_DARK)
    a.rect(x + 8, y + 8, w - 16, h - 16, (0.08, 0.14, 0.12))
    a.noise(x, y, w, h, 0.02)

    # 4. Broken Oar (R_BROKEN_OAR)
    x, y, w, h = R_BROKEN_OAR
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    a.rect(x + 8, y + 20, w - 16, 24, OAR_WOOD)
    # Splintered jagged end
    a.rect(x + w - 24, y + 20, 16, 24, WOOD_SPLINTER_LIGHT)
    a.noise(x, y, w, h, 0.03)

    # 5. Moss & Barnacles (R_MOSS_BARNACLES)
    x, y, w, h = R_MOSS_BARNACLES
    a.rect(x, y, w, h, WOOD_MOSS_GREEN)
    for bx in range(x + 4, x + w - 8, 12):
        by = y + 8 + (bx * 7) % (h - 20)
        a.rect(bx, by, 8, 8, (0.70, 0.72, 0.68))
        a.rect(bx + 2, by + 2, 4, 4, (0.20, 0.20, 0.20))

    # 6. Rope & Netting (R_ROPE_NETTING)
    x, y, w, h = R_ROPE_NETTING
    a.rect(x, y, w, h, (0.25, 0.22, 0.18))
    for ny in range(y, y + h, 10):
        a.rect(x, ny, w, 2, NET_GREEN)
    for nx in range(x, x + w, 10):
        a.rect(nx, y, 2, h, NET_GREEN)

    # 7. Rust Metal (R_RUST_METAL)
    x, y, w, h = R_RUST_METAL
    a.rect(x, y, w, h, RUST_IRON)
    a.noise(x, y, w, h, 0.05)

    # 8. Mud Base
    x, y, w, h = R_MUD_BASE
    a.rect(x, y, w, h, MUD_SILT)
    a.noise(x, y, w, h, 0.04)

    return a.to_image("prop_boat_broken_01_atlas", OUT_DIR)


def make_cylinder(name, r=0.15, h=0.6, segs=8, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    x, y, z = at
    bot_ring = []
    top_ring = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vx = x + r * math.cos(a)
        vy = y + r * math.sin(a)
        bot_ring.append(bm.verts.new((vx, vy, z)))
        top_ring.append(bm.verts.new((vx, vy, z + h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]))
    bm.faces.new(reversed(bot_ring))
    bm.faces.new(top_ring)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_boat_hull(name, length=3.6, width=1.4, depth=0.6, broken_side="starboard"):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    stations = [
        # (y_pos, half_width, bottom_z, gunwale_z)
        (length * 0.50,  0.05,  0.15, 0.65),  # Bow stem
        (length * 0.25,  width * 0.42, 0.05, 0.55),  # Forward mid
        (0.00,           width * 0.50, 0.00, 0.50),  # Midships
        (-length * 0.25, width * 0.44, 0.05, 0.52),  # Aft mid
        (-length * 0.50, width * 0.32, 0.10, 0.58),  # Stern transom
    ]

    verts_port_gunwale = []
    verts_star_gunwale = []
    verts_port_chine   = []
    verts_star_chine   = []
    verts_keel         = []

    for y, hw, bz, gz in stations:
        vk = bm.verts.new((0.0, y, bz))
        v_pg = bm.verts.new((-hw, y, gz))
        v_pc = bm.verts.new((-hw * 0.7, y, bz + 0.12))

        # If broken on starboard, dip or omit part of the gunwale
        if broken_side == "starboard" and 0.0 <= y <= length * 0.3:
            v_sg = bm.verts.new((hw * 0.5, y, bz + 0.18))
            v_sc = bm.verts.new((hw * 0.3, y, bz + 0.08))
        else:
            v_sg = bm.verts.new((hw, y, gz))
            v_sc = bm.verts.new((hw * 0.7, y, bz + 0.12))

        verts_keel.append(vk)
        verts_port_gunwale.append(v_pg)
        verts_port_chine.append(v_pc)
        verts_star_gunwale.append(v_sg)
        verts_star_chine.append(v_sc)

    # Build hull plank faces
    for i in range(len(stations) - 1):
        # Port bottom
        bm.faces.new([verts_keel[i], verts_keel[i+1], verts_port_chine[i+1], verts_port_chine[i]])
        # Port topsides
        bm.faces.new([verts_port_chine[i], verts_port_chine[i+1], verts_port_gunwale[i+1], verts_port_gunwale[i]])

        # Starboard bottom
        bm.faces.new([verts_keel[i], verts_star_chine[i], verts_star_chine[i+1], verts_keel[i+1]])
        # Starboard topsides
        bm.faces.new([verts_star_chine[i], verts_star_gunwale[i], verts_star_gunwale[i+1], verts_star_chine[i+1]])

    # Transom (stern back)
    last = len(stations) - 1
    bm.faces.new([verts_keel[last], verts_port_chine[last], verts_port_gunwale[last],
                  verts_star_gunwale[last], verts_star_chine[last]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    img = paint_boat_01_atlas()
    mat = material_for(img, "BoatBroken01_Mat")

    parts = []

    def register_box(name, w, d, h, at, front=None, sides=None, top=None, back=None):
        obj = kit.make_box(name, w, d, h, at=at)
        obj.data.materials.append(mat)
        if front is not None:
            kit.map_faces_to_region(obj, front, S, only=lambda f: f.normal.y < -0.5)
        if sides is not None:
            kit.map_faces_to_region(obj, sides, S, only=lambda f: abs(f.normal.x) > 0.5)
        if top is not None:
            kit.map_faces_to_region(obj, top, S, only=lambda f: abs(f.normal.z) > 0.5)
        if back is not None:
            kit.map_faces_to_region(obj, back, S, only=lambda f: f.normal.y > 0.5)
        parts.append(obj)
        return obj

    # 1. Main Clinker Hull (with broken starboard breach)
    hull = make_boat_hull("BoatHull_Broken", length=3.6, width=1.45, depth=0.6, broken_side="starboard")
    hull.data.materials.append(mat)
    kit.map_faces_to_region(hull, R_HULL_PLANKS, S)
    parts.append(hull)

    # 2. Keel Backbone Strip
    register_box("KeelPlank", 0.10, 3.50, 0.08, (0.0, 0.0, 0.0),
                 front=R_RUST_METAL, sides=R_MOSS_BARNACLES, top=R_MOSS_BARNACLES)

    # 3. Bilge Stagnant Murky Water in Hull Bottom
    register_box("BilgeWater", 0.70, 2.20, 0.04, (-0.05, -0.20, 0.10),
                 front=R_BILGE_WATER, sides=R_BILGE_WATER, top=R_BILGE_WATER)

    # 4. Broken Wooden Ribs (exposed in breach area)
    for ry in [0.20, 0.55, 0.85]:
        register_box(f"ExposedRib_{ry:.2f}", 0.06, 0.06, 0.35, (0.48, ry, 0.22),
                     front=R_INTERIOR_RIBS, sides=R_INTERIOR_RIBS, top=R_INTERIOR_RIBS)

    # 5. Thwart Benches (Aft seat & Center seat)
    register_box("AftThwart", 0.85, 0.28, 0.06, (0.0, -1.10, 0.44),
                 front=R_INTERIOR_RIBS, sides=R_INTERIOR_RIBS, top=R_INTERIOR_RIBS)
    register_box("MidThwart", 0.65, 0.26, 0.06, (-0.25, -0.10, 0.42),
                 front=R_INTERIOR_RIBS, sides=R_INTERIOR_RIBS, top=R_INTERIOR_RIBS)

    # 6. Broken Snapped Oar resting across hull
    oar_shaft = make_cylinder("OarShaft", r=0.03, h=1.50, segs=8, at=(-0.20, 0.30, 0.40))
    oar_shaft.rotation_euler = (0.2, 0.5, 0.6)
    oar_shaft.data.materials.append(mat)
    kit.map_faces_to_region(oar_shaft, R_BROKEN_OAR, S)
    parts.append(oar_shaft)

    # 7. Tangled Rope on Bow Post
    register_box("BowRopeCluster", 0.22, 0.22, 0.16, (0.0, 1.70, 0.60),
                 front=R_ROPE_NETTING, sides=R_ROPE_NETTING, top=R_ROPE_NETTING)

    # =========================================================================
    # Finalize & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Boat_Broken_01")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_boat_broken_01_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_boat_broken_01.glb"
    kit.export_glb(glb_path, [shell])
    print("[prop_boat_broken_01] generation complete in east_york/ folder.")


main()
