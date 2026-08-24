"""Shared helper toolkit for Mass Generation of low-poly 3D building and interior assets (<1500 Tris).

Runs INSIDE Blender via bpy_runner.py.
"""

import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Matrix

import asset_kit as kit

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"


def setup_palette_material(name, colors):
    """Creates a palette texture and material for an asset."""
    mat, n = kit.make_palette_material(name, colors, out_dir=OUT_DIR)
    return mat, n


def make_cuboid(bm, w, d, h, center=(0, 0, 0), color_idx=0):
    """Creates an axis-aligned box with given color index stored on face UVs."""
    cx, cy, cz = center
    verts = [
        bm.verts.new((cx - w/2, cy - d/2, cz - h/2)),
        bm.verts.new((cx + w/2, cy - d/2, cz - h/2)),
        bm.verts.new((cx + w/2, cy + d/2, cz - h/2)),
        bm.verts.new((cx - w/2, cy + d/2, cz - h/2)),
        bm.verts.new((cx - w/2, cy - d/2, cz + h/2)),
        bm.verts.new((cx + w/2, cy - d/2, cz + h/2)),
        bm.verts.new((cx + w/2, cy + d/2, cz + h/2)),
        bm.verts.new((cx - w/2, cy + d/2, cz + h/2)),
    ]
    face_indices = [
        (0, 1, 2, 3), # Bottom
        (4, 7, 6, 5), # Top
        (0, 4, 5, 1), # Front (-Y)
        (2, 6, 7, 3), # Back (+Y)
        (0, 3, 7, 4), # Left (-X)
        (1, 5, 6, 2), # Right (+X)
    ]
    faces = []
    for fi in face_indices:
        f = bm.faces.new([verts[i] for i in fi])
        f.smooth = False
        f.material_index = 0
        faces.append((f, color_idx))
    return faces


def make_cylinder(bm, r, h, segs=8, center=(0, 0, 0), color_idx=0):
    """Creates a vertical cylinder."""
    cx, cy, cz = center
    bottom_verts = []
    top_verts = []
    for i in range(segs):
        ang = (2 * math.pi * i) / segs
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        bottom_verts.append(bm.verts.new((x, y, cz - h/2)))
        top_verts.append(bm.verts.new((x, y, cz + h/2)))
    
    faces = []
    # Side quads
    for i in range(segs):
        ni = (i + 1) % segs
        f = bm.faces.new([bottom_verts[i], bottom_verts[ni], top_verts[ni], top_verts[i]])
        f.smooth = False
        faces.append((f, color_idx))
    
    # Bottom & top fan/caps
    fb = bm.faces.new(list(reversed(bottom_verts)))
    ft = bm.faces.new(top_verts)
    fb.smooth = False
    ft.smooth = False
    faces.append((fb, color_idx))
    faces.append((ft, color_idx))
    return faces


def make_pitched_roof(bm, w, d, h, overhang=0.2, center=(0, 0, 0), color_idx=0):
    """Creates a standard gabled pitched roof."""
    cx, cy, cz = center
    hw = (w / 2) + overhang
    hd = (d / 2) + overhang
    
    # Base corners
    v_fl = bm.verts.new((cx - hw, cy - hd, cz))
    v_fr = bm.verts.new((cx + hw, cy - hd, cz))
    v_br = bm.verts.new((cx + hw, cy + hd, cz))
    v_bl = bm.verts.new((cx - hw, cy + hd, cz))
    
    # Ridge verts (along X axis)
    v_rl = bm.verts.new((cx - hw, cy, cz + h))
    v_rr = bm.verts.new((cx + hw, cy, cz + h))
    
    faces = []
    # Front slope (-Y)
    f1 = bm.faces.new([v_fl, v_fr, v_rr, v_rl])
    # Back slope (+Y)
    f2 = bm.faces.new([v_rr, v_br, v_bl, v_rl])
    # Left gable (-X)
    f3 = bm.faces.new([v_fl, v_rl, v_bl])
    # Right gable (+X)
    f4 = bm.faces.new([v_fr, v_br, v_rr])
    # Underside
    f5 = bm.faces.new([v_bl, v_br, v_fr, v_fl])
    
    for f in (f1, f2, f3, f4, f5):
        f.smooth = False
        faces.append((f, color_idx))
    return faces


def make_hipped_roof(bm, w, d, h, overhang=0.2, center=(0, 0, 0), color_idx=0):
    """Creates a hipped roof with 4 sloping sides."""
    cx, cy, cz = center
    hw = (w / 2) + overhang
    hd = (d / 2) + overhang
    ridge_w = max(0.5, hw - hd) if hw > hd else 0.5
    
    v_fl = bm.verts.new((cx - hw, cy - hd, cz))
    v_fr = bm.verts.new((cx + hw, cy - hd, cz))
    v_br = bm.verts.new((cx + hw, cy + hd, cz))
    v_bl = bm.verts.new((cx - hw, cy + hd, cz))
    
    v_rl = bm.verts.new((cx - ridge_w, cy, cz + h))
    v_rr = bm.verts.new((cx + ridge_w, cy, cz + h))
    
    faces = []
    f_front = bm.faces.new([v_fl, v_fr, v_rr, v_rl])
    f_back = bm.faces.new([v_br, v_bl, v_rl, v_rr])
    f_left = bm.faces.new([v_fl, v_rl, v_bl])
    f_right = bm.faces.new([v_fr, v_br, v_rr])
    f_bottom = bm.faces.new([v_bl, v_br, v_fr, v_fl])
    for f in (f_front, f_back, f_left, f_right, f_bottom):
        f.smooth = False
        faces.append((f, color_idx))
    return faces


def make_pagoda_roof(bm, w, d, h, overhang=0.4, flare=0.3, center=(0, 0, 0), color_idx=0):
    """Creates an East Asian / fusion flared pagoda roof layer."""
    cx, cy, cz = center
    hw = (w / 2) + overhang
    hd = (d / 2) + overhang
    ridge_w = max(0.6, hw * 0.4)
    ridge_d = max(0.6, hd * 0.4)
    
    # Flared eave corners (slightly upturned at corners)
    v_fl = bm.verts.new((cx - hw, cy - hd, cz + flare))
    v_fr = bm.verts.new((cx + hw, cy - hd, cz + flare))
    v_br = bm.verts.new((cx + hw, cy + hd, cz + flare))
    v_bl = bm.verts.new((cx - hw, cy + hd, cz + flare))
    
    # Mid edge dips
    v_fm = bm.verts.new((cx, cy - hd, cz))
    v_bm = bm.verts.new((cx, cy + hd, cz))
    v_lm = bm.verts.new((cx - hw, cy, cz))
    v_rm = bm.verts.new((cx + hw, cy, cz))
    
    # Top ridge / peak
    v_rfl = bm.verts.new((cx - ridge_w, cy - ridge_d, cz + h))
    v_rfr = bm.verts.new((cx + ridge_w, cy - ridge_d, cz + h))
    v_rbr = bm.verts.new((cx + ridge_w, cy + ridge_d, cz + h))
    v_rbl = bm.verts.new((cx - ridge_w, cy + ridge_d, cz + h))
    
    faces = []
    # Slopes
    f1 = bm.faces.new([v_fl, v_fm, v_rfl])
    f2 = bm.faces.new([v_fm, v_fr, v_rfr, v_rfl])
    f3 = bm.faces.new([v_fr, v_rm, v_rfr])
    f4 = bm.faces.new([v_rm, v_br, v_rbr, v_rfr])
    f5 = bm.faces.new([v_br, v_bm, v_rbr])
    f6 = bm.faces.new([v_bm, v_bl, v_rbl, v_rbr])
    f7 = bm.faces.new([v_bl, v_lm, v_rbl])
    f8 = bm.faces.new([v_lm, v_fl, v_rfl, v_rbl])
    f_top = bm.faces.new([v_rfl, v_rfr, v_rbr, v_rbl])
    
    for f in (f1, f2, f3, f4, f5, f6, f7, f8, f_top):
        f.smooth = False
        faces.append((f, color_idx))
    return faces


def apply_bmesh_and_export(name, bm, face_color_pairs, palette_colors, dest_subdir="london/modular_sets", tri_limit=1600):
    """Builds mesh, maps UVs, finalizes, checks tri count, renders preview and exports GLB."""
    kit.reset_scene()
    
    # Index faces in bmesh before converting to mesh
    bm.faces.index_update()
    face_map = {f.index: color_idx for f, color_idx in face_color_pairs}
    
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    # Material
    mat, palette_size = setup_palette_material(name, palette_colors)
    obj.data.materials.append(mat)
    
    # Map UVs via kit.paint_faces
    kit.paint_faces(obj, face_map, palette_size)
            
    kit.finalize(obj)
    
    # Count triangles
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"[{name}] Verts: {len(obj.data.vertices)}, Polys: {len(obj.data.polygons)}, Triangles: {tri_count} / Limit: {tri_limit}")
    assert tri_count <= tri_limit, f"ERROR: {name} exceeded {tri_limit} tri limit with {tri_count} tris!"
    
    # Export previews and GLB to Tools/blender/out and project Assets/3DModels/
    out_glb = OUT_DIR / f"{name}.glb"
    out_png = OUT_DIR / f"{name}_preview.png"
    kit.iso_preview(out_png, [obj])
    kit.export_glb(out_glb, [obj])
    
    # Deploy to Assets/3DModels
    target_dir = ROOT_DIR / "Assets" / "3DModels" / dest_subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    
    final_glb = target_dir / f"{name}.glb"
    final_png = target_dir / f"{name}_preview.png"
    shutil.copyfile(out_glb, final_glb)
    shutil.copyfile(out_png, final_png)
    print(f"[{name}] Deployed to: {final_glb}")
    return tri_count
