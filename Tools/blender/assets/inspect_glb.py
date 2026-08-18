"""Inspect an existing .glb: import, report per-object stats, render iso preview.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/inspect_glb.py -- <path.glb> [preview_name]
"""

import bpy

import asset_kit as kit


def main():
    args = kit.script_args()
    glb_path = args[0]
    name = args[1] if len(args) > 1 else "inspect"
    kit.reset_scene()
    bpy.ops.import_scene.gltf(filepath=glb_path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print(f"[inspect] {glb_path}: {len(meshes)} mesh objects")
    for o in meshes:
        kit.report_stats(o)
        for slot in o.material_slots:
            if slot.material:
                print(f"           material: {slot.material.name}")
    # Whole-model preview with materials as authored.
    kit.iso_preview(kit.OUT_DIR / f"{name}_preview.png", meshes)


main()
