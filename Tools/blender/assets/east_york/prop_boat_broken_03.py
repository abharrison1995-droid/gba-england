"""Broken Wooden Fishing Boat — Variant 03: Split Half-Wrecked Skiff with Eel Trap & Nets.

Specs:
- 3.4m long x 1.4m wide x 0.85m high half-wrecked fishing skiff
- The rear stern transom has been violently smashed away, leaving splintered hull planking
- The upright forward half features an intact bow stem with iron mooring ring
- Contents & Props Inside Wreckage:
  - Wicker/wire woven eel pot (fish trap) wedged in the bilge
  - Tangled green hemp fishing net trailing overboard onto the mud
  - Stagnant water puddle with fish bones and discarded tin can.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/east_york/prop_boat_broken_03.py
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
R_HULL_PLANKS       = (0,   256, 256, 256)   # Weathered wood planks with broken jagged edges
R_EEL_TRAP          = (256, 256, 128, 256)   # Woven wicker & wire eel trap pot
R_NETS_HEMP         = (384, 384, 128, 128)   # Tangled green hemp fishing net
R_SPLINTERED_WOOD   = (384, 256, 128, 128)   # Jagged broken oak timber ribs and plank ends
R_BILGE_PUDDLE      = (0,   128, 128, 128)   # Stagnant bilge water with algae scum
R_MOORING_RING      = (128, 128, 128, 128)   # Rusted iron mooring eye & ring
R_MOSS_WEATHERING   = (256, 128, 128, 128)   # Green moss and river slime
R_MUD_SILT          = (0,   0,   256, 128)   # Mud bank base

# --- Palette Colors ---
WOOD_HULL_BASE      = (0.44, 0.38, 0.30)
WOOD_HULL_DARK      = (0.26, 0.22, 0.16)
WOOD_SPLINTER_LIGHT = (0.64, 0.58, 0.44)
WICKER_BROWN        = (0.52, 0.42, 0.26)
WICKER_DARK         = (0.30, 0.24, 0.14)
NET_GREEN           = (0.18, 0.38, 0.26)
RUST_IRON           = (0.48, 0.24, 0.14)
BILGE_DARK          = (0.10, 0.16, 0.14)
MOSS_GREEN          = (0.28, 0.36, 0.22)


def paint_boat_03_atlas():
    a = Atlas(S, seed=8103)

    # 1. Hull Planks (R_HULL_PLANKS)
    x, y, w, h = R_HULL_PLANKS
    a.rect(x, y, w, h, WOOD_HULL_BASE)
    for py in range(y, y + h, 18):
        a.rect(x, py, w, 2, WOOD_HULL_DARK)
    a.rect(x, y, w, 50, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 2. Woven Eel Trap Pot (R_EEL_TRAP)
    x, y, w, h = R_EEL_TRAP
    a.rect(x, y, w, h, WICKER_BROWN)
    # Wicker cross-hatching
    for wy in range(y, y + h, 10):
        a.rect(x, wy, w, 2, WICKER_DARK)
    for wx in range(x, x + w, 10):
        a.rect(wx, y, 2, h, WICKER_DARK)
    a.noise(x, y, w, h, 0.03)

    # 3. Nets (R_NETS_HEMP)
    x, y, w, h = R_NETS_HEMP
    a.rect(x, y, w, h, (0.22, 0.20, 0.16))
    for ny in range(y, y + h, 8):
        a.rect(x, ny, w, 2, NET_GREEN)
    for nx in range(x, x + w, 8):
        a.rect(nx, y, 2, h, NET_GREEN)

    # 4. Splintered Jagged Wood (R_SPLINTERED_WOOD)
    x, y, w, h = R_SPLINTERED_WOOD
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    for ry in range(y, y + h, 16):
        a.rect(x + 4, ry, w - 8, 8, WOOD_SPLINTER_LIGHT)
    a.noise(x, y, w, h, 0.035)

    # 5. Bilge Puddle (R_BILGE_PUDDLE)
    x, y, w, h = R_BILGE_PUDDLE
    a.rect(x, y, w, h, BILGE_DARK)
    a.noise(x, y, w, h, 0.02)

    # 6. Mooring Ring (R_MOORING_RING)
    x, y, w, h = R_MOORING_RING
    a.rect(x, y, w, h, WOOD_HULL_DARK)
    a.rect(x + w // 2 - 16, y + h // 2 - 16, 32, 32, RUST_IRON)
    a.rect(x + w // 2 - 8, y + h // 2 - 8, 16, 16, (0.12, 0.12, 0.12))

    # 7. Moss Weathering (R_MOSS_WEATHERING)
    x, y, w, h = R_MOSS_WEATHERING
    a.rect(x, y, w, h, MOSS_GREEN)
    a.noise(x, y, w, h, 0.04)

    # 8. Mud Silt (R_MUD_SILT)
    x, y, w, h = R_MUD_SILT
    a.rect(x, y, w, h, (0.22, 0.20, 0.16))

    return a.to_image("prop_boat_broken_03_atlas", OUT_DIR)


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


def make_split_hull(name, length=3.4, width=1.4, depth=0.55):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Stations from bow to mid-point where hull ends abruptly in broken jagged split
    stations = [
        # (y_pos, half_width, bottom_z, gunwale_z)
        (length * 0.50,  0.05,  0.15, 0.70),  # Bow stem
        (length * 0.30,  width * 0.40, 0.06, 0.58),  # Forward quarter
        (0.00,           width * 0.48, 0.02, 0.52),  # Midships
        (-length * 0.20, width * 0.50, 0.00, 0.48),  # Broken split fracture line
    ]

    verts_keel = []
    verts_port_gunwale = []
    verts_star_gunwale = []
    verts_port_chine = []
    verts_star_chine = []

    for y, hw, bz, gz in stations:
        vk = bm.verts.new((0.0, y, bz))
        v_pg = bm.verts.new((-hw, y, gz))
        v_sg = bm.verts.new((hw, y, gz))
        v_pc = bm.verts.new((-hw * 0.7, y, bz + 0.12))
        v_sc = bm.verts.new((hw * 0.7, y, bz + 0.12))

        verts_keel.append(vk)
        verts_port_gunwale.append(v_pg)
        verts_star_gunwale.append(v_sg)
        verts_port_chine.append(v_pc)
        verts_star_chine.append(v_sc)

    for i in range(len(stations) - 1):
        bm.faces.new([verts_keel[i], verts_keel[i+1], verts_port_chine[i+1], verts_port_chine[i]])
        bm.faces.new([verts_port_chine[i], verts_port_chine[i+1], verts_port_gunwale[i+1], verts_port_gunwale[i]])
        bm.faces.new([verts_keel[i], verts_star_chine[i], verts_star_chine[i+1], verts_keel[i+1]])
        bm.faces.new([verts_star_chine[i], verts_star_gunwale[i], verts_star_gunwale[i+1], verts_star_chine[i+1]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    img = paint_boat_03_atlas()
    mat = material_for(img, "BoatBroken03_Mat")

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

    # 1. Split Half Hull
    hull = make_split_hull("SplitHull", length=3.4, width=1.4, depth=0.55)
    hull.data.materials.append(mat)
    kit.map_faces_to_region(hull, R_HULL_PLANKS, S)
    parts.append(hull)

    # 2. Keel
    register_box("KeelStrip", 0.10, 2.40, 0.08, (0.0, 0.50, 0.02),
                 front=R_MOSS_WEATHERING, sides=R_MOSS_WEATHERING, top=R_MOSS_WEATHERING)

    # 3. Jagged Splintered Planks at the Break Line (Y = -0.68m)
    for bx in [-0.55, -0.30, -0.05, 0.20, 0.45]:
        bh = 0.25 + abs(bx) * 0.2
        register_box(f"BreakSplinter_{bx:.2f}", 0.08, 0.28, bh, (bx, -0.75, 0.10),
                     front=R_SPLINTERED_WOOD, sides=R_SPLINTERED_WOOD, top=R_SPLINTERED_WOOD)

    # 4. Bilge Puddle in Broken Interior
    register_box("BilgePuddle", 0.70, 1.40, 0.04, (0.0, 0.20, 0.08),
                 front=R_BILGE_PUDDLE, sides=R_BILGE_PUDDLE, top=R_BILGE_PUDDLE)

    # 5. Wicker Eel Trap Pot inside Hull
    eel_pot = make_cylinder("EelTrapPot", r=0.20, h=0.65, segs=8, at=(0.15, 0.35, 0.14))
    eel_pot.rotation_euler = (0.3, 1.3, 0.4)
    eel_pot.data.materials.append(mat)
    kit.map_faces_to_region(eel_pot, R_EEL_TRAP, S)
    parts.append(eel_pot)

    # 6. Green Hemp Fishing Net trailing over the Port Gunwale
    register_box("DrapedNetPort", 0.28, 0.85, 0.35, (-0.68, 0.20, 0.30),
                 front=R_NETS_HEMP, sides=R_NETS_HEMP, top=R_NETS_HEMP)
    register_box("DrapedNetOverboard", 0.35, 0.60, 0.12, (-0.85, 0.20, 0.06),
                 front=R_NETS_HEMP, sides=R_NETS_HEMP, top=R_NETS_HEMP)

    # 7. Bow Stem Mooring Ring
    ring = make_cylinder("MooringRing", r=0.08, h=0.04, segs=8, at=(0.0, 1.70, 0.72))
    ring.rotation_euler = (1.57, 0.0, 0.0)
    ring.data.materials.append(mat)
    kit.map_faces_to_region(ring, R_MOORING_RING, S)
    parts.append(ring)

    # =========================================================================
    # Finalize & Export
    # =========================================================================
    shell = kit.join(parts, "Prop_Boat_Broken_03")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "prop_boat_broken_03_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "prop_boat_broken_03.glb"
    kit.export_glb(glb_path, [shell])
    print("[prop_boat_broken_03] generation complete in east_york/ folder.")


main()
