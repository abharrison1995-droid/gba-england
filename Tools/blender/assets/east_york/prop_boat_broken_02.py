"""Broken Wooden Fishing Boat — Variant 02: Capsized / Overturned Mossy Hull.

Specs:
- 3.8m long x 1.5m wide x 0.68m high overturned wooden fishing skiff
- Lies completely capsized (keel facing up) in the river mud alongside the Mad Fisherman's shack
- Structural Damage & Weathering:
  - Split fractured keel backbone with large gaping rotted hole revealing hollow interior
  - Heavily encrusted with green river algae, barnacles, and rust-stained planking seams
  - Discarded rusty mooring chain wrapped around the upturned bow stem
  - Rotted timber ribs showing through bottom breach.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/prop_boat_broken_02.py
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
R_OVERTURNED_HULL   = (0,   256, 256, 256)   # Overturned clinker planks with water stains & rot
R_MOSS_BARNACLES    = (256, 256, 128, 256)   # Thick green algae crust & barnacle clusters
R_SPLIT_TIMBER      = (384, 384, 128, 128)   # Splintered oak ribs and broken plank edges
R_RUSTY_CHAIN       = (384, 256, 128, 128)   # Rusted iron mooring chain & ring
R_HOLLOW_DARK       = (0,   128, 128, 128)   # Pitch-black shadow inside hollow breach
R_DRIFT_PINS        = (128, 128, 128, 128)   # Rusted copper/iron rivets and drift bolts
R_MUD_SILT          = (256, 128, 128, 128)   # Riverbank mud and silt stains
R_SEAWEED           = (0,   0,   256, 128)   # Trailing brown/green riverweed

# --- Palette Colors ---
WOOD_HULL_BASE      = (0.38, 0.34, 0.28)
WOOD_HULL_DARK      = (0.22, 0.18, 0.14)
WOOD_MOSS_GREEN     = (0.26, 0.36, 0.20)
SPLINTER_LIGHT      = (0.58, 0.52, 0.40)
RUST_CHAIN          = (0.42, 0.20, 0.12)
RUST_DARK           = (0.24, 0.12, 0.08)
MUD_COLOR           = (0.20, 0.18, 0.15)


def paint_boat_02_atlas():
    a = Atlas(S, seed=8102)

    # 1. Overturned Hull Planks (R_OVERTURNED_HULL)
    x, y, w, h = R_OVERTURNED_HULL
    a.rect(x, y, w, h, WOOD_HULL_BASE)
    for py in range(y, y + h, 16):
        a.rect(x, py, w, 2, WOOD_HULL_DARK)
    # Heavy algae / moss along the bottom edge (which was in water)
    a.rect(x, y + h - 80, w, 80, WOOD_MOSS_GREEN)
    for mx in range(x, x + w, 18):
        a.rect(mx, y + h - 100 + (mx % 24), 14, 30, WOOD_MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 2. Moss & Barnacles (R_MOSS_BARNACLES)
    x, y, w, h = R_MOSS_BARNACLES
    a.rect(x, y, w, h, WOOD_MOSS_GREEN)
    for bx in range(x + 4, x + w - 8, 14):
        by = y + 8 + (bx * 9) % (h - 20)
        a.rect(bx, by, 10, 10, (0.72, 0.74, 0.70))
        a.rect(bx + 2, by + 2, 6, 6, (0.25, 0.25, 0.25))

    # 3. Split Timber (R_SPLIT_TIMBER)
    x, y, w, h = R_SPLIT_TIMBER
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    for ry in range(y, y + h, 18):
        a.rect(x + 6, ry, w - 12, 6, SPLINTER_LIGHT)
    a.noise(x, y, w, h, 0.03)

    # 4. Rusty Chain (R_RUSTY_CHAIN)
    x, y, w, h = R_RUSTY_CHAIN
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    for cy in range(y + 8, y + h - 8, 16):
        a.rect(x + 8, cy, w - 16, 10, RUST_CHAIN)
        a.rect(x + 12, cy + 2, w - 24, 6, RUST_DARK)

    # 5. Hollow Dark (R_HOLLOW_DARK)
    x, y, w, h = R_HOLLOW_DARK
    a.rect(x, y, w, h, (0.05, 0.05, 0.05))

    # 6. Drift Pins (R_DRIFT_PINS)
    x, y, w, h = R_DRIFT_PINS
    a.rect(x, y, w, h, WOOD_HULL_BASE)
    for px in range(x + 10, x + w - 10, 20):
        for py in range(y + 10, y + h - 10, 20):
            a.rect(px, py, 4, 4, RUST_CHAIN)

    # 7. Mud Silt (R_MUD_SILT)
    x, y, w, h = R_MUD_SILT
    a.rect(x, y, w, h, MUD_COLOR)
    a.noise(x, y, w, h, 0.04)

    # 8. Seaweed (R_SEAWEED)
    x, y, w, h = R_SEAWEED
    a.rect(x, y, w, h, (0.18, 0.28, 0.16))
    a.noise(x, y, w, h, 0.05)

    return a.to_image("prop_boat_broken_02_atlas", OUT_DIR)


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


def make_capsized_hull(name, length=3.8, width=1.5, height=0.65):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    stations = [
        # (y_pos, half_width, keel_z, gunwale_z)
        (length * 0.50,  0.06,  height, 0.05),  # Bow stem
        (length * 0.25,  width * 0.42, height * 0.95, 0.02),  # Fwd mid
        (0.00,           width * 0.50, height * 0.90, 0.00),  # Midships
        (-length * 0.25, width * 0.44, height * 0.92, 0.02),  # Aft mid
        (-length * 0.50, width * 0.32, height * 0.85, 0.05),  # Stern transom
    ]

    verts_keel = []
    verts_port_chine = []
    verts_star_chine = []
    verts_port_gunwale = []
    verts_star_gunwale = []

    for y, hw, kz, gz in stations:
        vk = bm.verts.new((0.0, y, kz))
        v_pc = bm.verts.new((-hw * 0.75, y, kz * 0.65))
        v_sc = bm.verts.new((hw * 0.75, y, kz * 0.65))
        v_pg = bm.verts.new((-hw, y, gz))
        v_sg = bm.verts.new((hw, y, gz))

        verts_keel.append(vk)
        verts_port_chine.append(v_pc)
        verts_star_chine.append(v_sc)
        verts_port_gunwale.append(v_pg)
        verts_star_gunwale.append(v_sg)

    for i in range(len(stations) - 1):
        # Port upper hull
        bm.faces.new([verts_keel[i], verts_port_chine[i], verts_port_chine[i+1], verts_keel[i+1]])
        # Port lower topside
        bm.faces.new([verts_port_chine[i], verts_port_gunwale[i], verts_port_gunwale[i+1], verts_port_chine[i+1]])

        # Starboard upper hull
        bm.faces.new([verts_keel[i], verts_keel[i+1], verts_star_chine[i+1], verts_star_chine[i]])
        # Starboard lower topside
        bm.faces.new([verts_star_chine[i], verts_star_chine[i+1], verts_star_gunwale[i+1], verts_star_gunwale[i]])

    # Transom back face
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

    img = paint_boat_02_atlas()
    mat = material_for(img, "BoatBroken02_Mat")

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

    # 1. Overturned Hull Body
    hull = make_capsized_hull("CapsizedHull", length=3.8, width=1.5, height=0.68)
    hull.data.materials.append(mat)
    kit.map_faces_to_region(hull, R_OVERTURNED_HULL, S)
    parts.append(hull)

    # 2. Uplifted Keel Backbone
    register_box("UpturnedKeel", 0.12, 3.65, 0.08, (0.0, 0.0, 0.65),
                 front=R_MOSS_BARNACLES, sides=R_MOSS_BARNACLES, top=R_MOSS_BARNACLES)

    # 3. Gaping Rotted Breach / Hole in Bottom Hull (Port side midships)
    register_box("HullRottedHole", 0.45, 0.95, 0.12, (-0.42, 0.10, 0.38),
                 front=R_HOLLOW_DARK, sides=R_SPLIT_TIMBER, top=R_HOLLOW_DARK)

    # Exposed splintered ribs inside the hole
    for ry in [-0.20, 0.15, 0.45]:
        register_box(f"SplitRib_{ry:.2f}", 0.05, 0.05, 0.28, (-0.42, ry, 0.25),
                     front=R_SPLIT_TIMBER, sides=R_SPLIT_TIMBER, top=R_SPLIT_TIMBER)

    # 4. Heavy Rusted Mooring Chain draped over Bow Stem
    chain = make_cylinder("RustyChainLoop", r=0.18, h=0.12, segs=8, at=(0.0, 1.75, 0.45))
    chain.rotation_euler = (1.2, 0.0, 0.0)
    chain.data.materials.append(mat)
    kit.map_faces_to_region(chain, R_RUSTY_CHAIN, S)
    parts.append(chain)

    register_box("ChainTail", 0.08, 0.65, 0.06, (0.15, 1.45, 0.20),
                 front=R_RUSTY_CHAIN, sides=R_RUSTY_CHAIN, top=R_RUSTY_CHAIN)

    # 5. Mud Bank Base Footprint
    register_box("MudBank", 1.80, 4.10, 0.04, (0.0, 0.0, 0.0),
                 front=R_MUD_SILT, sides=R_MUD_SILT, top=R_MUD_SILT)

    # =========================================================================
    # Finalize & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Boat_Broken_02")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_boat_broken_02_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_boat_broken_02.glb"
    kit.export_glb(glb_path, [shell])
    print("[prop_boat_broken_02] generation complete in east_york/ folder.")


main()
