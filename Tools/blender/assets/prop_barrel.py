"""Proof-of-concept asset: a stylized low-poly wooden barrel.

Run:  python Tools/blender/bpy_runner.py Tools/blender/assets/prop_barrel.py

Outputs (Tools/blender/out/):
  prop_barrel.glb        — Y-up, bottom-centre origin, palette material
  prop_barrel_preview.png — isometric Workbench render, 30/45 like the game camera
"""

import bmesh
import bpy

import asset_kit as kit

SIDES = 10
# Barrel silhouette: (height_m, radius_m) rings, bottom to top. ~0.9 m tall,
# which reads right next to the 1.55 m NPC height.
RINGS = [
    (0.00, 0.30),
    (0.10, 0.335),  # lower metal band bottom edge
    (0.17, 0.35),   # lower metal band top edge
    (0.45, 0.385),  # belly
    (0.73, 0.35),   # upper metal band bottom edge
    (0.80, 0.335),  # upper metal band top edge
    (0.90, 0.30),
]
BANDS = [(0.10, 0.17), (0.73, 0.80)]  # z ranges that get the metal colour

WOOD, METAL, WOOD_LIGHT = 0, 1, 2
PALETTE = [
    (0.42, 0.26, 0.13),  # stave wood
    (0.16, 0.16, 0.18),  # iron band
    (0.55, 0.37, 0.19),  # lid wood
]


def build_barrel():
    mesh = bpy.data.meshes.new("Barrel")
    bm = bmesh.new()
    loops = []
    for z, r in RINGS:
        ring = []
        for i in range(SIDES):
            import math
            a = 2 * math.pi * i / SIDES
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        loops.append(ring)
    for lower, upper in zip(loops, loops[1:]):
        for i in range(SIDES):
            j = (i + 1) % SIDES
            bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    bm.faces.new(reversed(loops[0]))   # bottom cap, facing down
    bm.faces.new(loops[-1])            # top cap, facing up
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Prop_Barrel", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def colour_for(face):
    z = face.center.z
    if any(lo - 0.01 <= z <= hi + 0.01 for lo, hi in BANDS):
        return METAL
    if abs(face.normal.z) > 0.9 and z > 0.5:
        return WOOD_LIGHT
    return WOOD


def main():
    kit.reset_scene()
    barrel = build_barrel()
    mat, n = kit.make_palette_material("prop_barrel", PALETTE)
    barrel.data.materials.append(mat)
    kit.paint_faces(barrel, colour_for, n)
    kit.finalize(barrel)
    kit.report_stats(barrel)
    kit.iso_preview(kit.OUT_DIR / "prop_barrel_preview.png", [barrel])
    kit.export_glb(kit.OUT_DIR / "prop_barrel.glb", [barrel])
    print("[prop_barrel] done")


main()
