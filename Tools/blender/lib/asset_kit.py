"""Shared bpy helpers for the local low-poly asset pipeline (runs INSIDE Blender).

Import from asset scripts executed via bpy_runner.py:

    import asset_kit as kit

Conventions (chosen to match the game):
  * 1 Blender unit = 1 metre = 1 Unity unit. Z is up here; the glTF exporter
    converts to Y-up on export, which is what Unity and the existing .glb
    imports in Assets/3DModels expect.
  * Flat-shaded, palette-textured low poly: one material, one tiny N x 1
    palette PNG, every face's UVs collapsed onto one palette texel.
  * Origins sit at bottom-centre so a placed prefab rests on the floor.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT_DIR = Path(__file__).resolve().parent.parent / "out"


def script_args():
    """Args passed after `--` on the bpy_runner command line."""
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


def reset_scene():
    """Start from a truly empty scene, independent of startup file contents."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_palette_material(name, colors, out_dir=OUT_DIR):
    """One material driven by an N x 1 nearest-filtered palette texture.

    colors: list of (r, g, b) floats 0-1. Returns (material, palette_size).
    The PNG is written to out_dir so the glTF exporter can always embed it.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = len(colors)
    img = bpy.data.images.new(f"{name}_palette", width=n, height=1, alpha=False)
    px = []
    for (r, g, b) in colors:
        px += [r, g, b, 1.0]
    img.pixels[:] = px
    img.filepath_raw = str(out_dir / f"{name}_palette.png")
    img.file_format = "PNG"
    img.save()

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"  # hard palette cells, no bleeding
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat, n


def paint_faces(obj, face_color_index, palette_size, default_index=0):
    """Snap every face's UVs onto one palette texel.

    face_color_index: dict {face_index: palette_index} or a callable
    taking (face) and returning a palette index.
    """
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data
    for face in mesh.polygons:
        if callable(face_color_index):
            idx = face_color_index(face)
        else:
            idx = face_color_index.get(face.index, default_index)
        u = (idx + 0.5) / palette_size
        for loop_i in face.loop_indices:
            uv[loop_i].uv = (u, 0.5)


def apply_modifiers(obj):
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def set_origin_bottom_center(obj, snap_to_ground=True):
    """Origin to the centre of the bounding box footprint, at its lowest Z."""
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    cx = sum(c.x for c in corners) / 8.0
    cy = sum(c.y for c in corners) / 8.0
    min_z = min(c.z for c in corners)
    bpy.context.scene.cursor.location = (cx, cy, min_z)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    if snap_to_ground:
        obj.location = (0.0, 0.0, 0.0)


def shade_flat(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False


def finalize(obj):
    """Standard cleanup before export: modifiers applied, flat shaded,
    transforms applied, origin at bottom-centre on the world origin."""
    apply_modifiers(obj)
    shade_flat(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    set_origin_bottom_center(obj)


def iso_preview(path, objects=None, margin=1.25, resolution=512):
    """Render a quick isometric preview PNG with the Workbench engine.

    Camera matches the game's presentation: 30 degree pitch, 45 degree yaw,
    orthographic. Workbench renders headless with no GPU/EEVEE caveats and
    shows the palette texture flat-lit, which is exactly the in-game look.
    """
    scene = bpy.context.scene
    if objects is None:
        objects = [o for o in scene.objects if o.type == "MESH"]

    # Fit: bounding box over all target objects.
    corners = []
    for o in objects:
        corners += [o.matrix_world @ Vector(c) for c in o.bound_box]
    center = sum(corners, Vector()) / len(corners)
    radius = max((c - center).length for c in corners)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = radius * 2.0 * margin
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    pitch, yaw = math.radians(30), math.radians(45)
    direction = Vector((
        math.cos(pitch) * math.sin(yaw),
        -math.cos(pitch) * math.cos(yaw),
        math.sin(pitch),
    ))
    cam.location = center + direction * (radius * 4.0)
    cam.rotation_euler = (math.radians(90) - pitch, 0.0, yaw)
    scene.camera = cam

    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "FLAT"
    shading.color_type = "TEXTURE"
    scene.render.film_transparent = True
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"[asset_kit] preview -> {path}")


def export_glb(path, objects=None):
    """Export to .glb (Y-up, materials + embedded palette texture)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    if objects is None:
        objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    print(f"[asset_kit] export -> {path}")


def report_stats(obj):
    mesh = obj.data
    tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
    dims = obj.dimensions
    print(f"[asset_kit] {obj.name}: {len(mesh.vertices)} verts, "
          f"{len(mesh.polygons)} faces, {tris} tris, "
          f"{dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} m")
