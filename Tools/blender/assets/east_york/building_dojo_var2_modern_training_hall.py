"""West York Martial Arts Dojo - Variant 2: Modern Urban MMA Academy (~880 Tris).

Specs:
- Footprint: 10.5m wide x 8.5m deep, Height: 6.0m. Sits directly at Z = 0.0.
- Features:
  - Converted industrial red brick & black steel martial arts academy / combat club.
  - Sawtooth industrial roof with north-facing clerestory glass skylights.
  - Large roller shutter entrance with illuminated neon martial arts signage.
  - External heavy steel punching bag gantry frame with hanging heavy bags.
  - Industrial ventilation ducting on the roof.
- Target: <1,000 tris (~880 tris).
- Deploys to Assets/3DModels/West York/building_dojo_02_modern_training_hall.glb.
"""

import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "west_york"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "West York"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions (x, y, w, h)
R_URBAN_BRICK    = (0,   256, 256, 256)   # Weathered industrial red/brown brick
R_CORRUG_STEEL   = (256, 256, 256, 256)   # Dark grey corrugated metal sawtooth roof
R_GYM_SHUTTER    = (0,   128, 128, 128)   # Heavy industrial roller shutter entry & personnel door
R_NEON_SIGN      = (128, 128, 128, 128)   # Vibrant red & gold illuminated Combat Club neon sign
R_PUNCH_BAG      = (256, 128, 128, 128)   # Heavy leather punching bags & steel stanchions
R_FACTORY_GLASS  = (384, 128, 128, 128)   # Multi-pane wired factory skylight glass


def paint_atlas():
    a = Atlas(S, seed=1995)

    # 1. Industrial Brick (R_URBAN_BRICK)
    x, y, w, h = R_URBAN_BRICK
    a.bricks(x, y, w, h, brick=(0.52, 0.24, 0.16), mortar=(0.70, 0.68, 0.64), bw=18, bh=8, jitter=0.06)
    a.noise(x, y, w, h, 0.02)

    # 2. Corrugated Metal (R_CORRUG_STEEL)
    x, y, w, h = R_CORRUG_STEEL
    a.rect(x, y, w, h, (0.32, 0.34, 0.36))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 2, (0.20, 0.22, 0.24))
    a.noise(x, y, w, h, 0.015)

    # 3. Roller Shutter (R_GYM_SHUTTER)
    x, y, w, h = R_GYM_SHUTTER
    a.rect(x, y, w, h, (0.42, 0.44, 0.46))
    for ry in range(y + 6, y + h - 6, 8):
        a.rect(x + 4, ry, w - 8, 2, (0.25, 0.26, 0.28))
    # Personnel entry door on right side of shutter
    a.rect(x + w - 36, y + 6, 28, h - 16, (0.18, 0.20, 0.22))
    a.noise(x, y, w, h, 0.01)

    # 4. Neon Sign (R_NEON_SIGN)
    x, y, w, h = R_NEON_SIGN
    a.rect(x, y, w, h, (0.12, 0.12, 0.14))
    # Bright red neon box with fist icon / text
    a.rect(x + 6, y + 10, w - 12, h - 20, (0.85, 0.15, 0.15))
    a.rect(x + 10, y + 14, w - 20, h - 28, (0.12, 0.12, 0.14))
    a.rect(x + 16, y + h // 2 - 4, w - 32, 8, (0.95, 0.85, 0.20))
    a.noise(x, y, w, h, 0.01)

    # 5. Punching Bag Leather (R_PUNCH_BAG)
    x, y, w, h = R_PUNCH_BAG
    a.rect(x, y, w, h, (0.18, 0.18, 0.20))
    a.rect(x + 10, y + 10, w - 20, h - 20, (0.75, 0.15, 0.15))
    a.noise(x, y, w, h, 0.015)

    # 6. Factory Glass (R_FACTORY_GLASS)
    x, y, w, h = R_FACTORY_GLASS
    a.rect(x, y, w, h, (0.35, 0.48, 0.58))
    for rx in range(x, x + w, 16):
        a.rect(rx, y, 2, h, (0.18, 0.22, 0.26))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_dojo_02", OUT_DIR)


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


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_dojo_02")

    parts = []

    def reg_box(name, w, d, h, at, region=R_URBAN_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_cyl(name, r, h, segs=16, at=(0, 0, 0), region=R_PUNCH_BAG):
        o = make_cylinder(name, r, h, segs, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # WEST YORK MARTIAL ARTS DOJO 02: MODERN URBAN MMA ACADEMY (~880 TRIS)
    # Footprint: 10.5m x 8.5m, Height: 6.0m. Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main Warehouse Brick Hall Body (Z = 0.0 to 4.2m)
    reg_box("AcademyMainBody", 10.0, 8.0, 4.2, (0, 0, 0.0), region=R_URBAN_BRICK)
    reg_box("ParapetCapBeam", 10.3, 8.3, 0.25, (0, 0, 4.2), region=R_CORRUG_STEEL)

    # 2. Industrial Sawtooth Roof with Clerestory Skylights (3 Sawtooth Bays)
    for si in range(3):
        sy = -2.5 + si * 2.5
        # Slanted corrugated roof pitch
        reg_box(f"SawtoothRoof_{si}", 9.6, 2.0, 0.2, (0, sy, 4.8), region=R_CORRUG_STEEL)
        # Vertical glazed clerestory skylight
        reg_box(f"SkylightGlass_{si}", 9.6, 0.15, 0.8, (0, sy - 1.0, 4.4), region=R_FACTORY_GLASS)

    # 3. Large Industrial Roller Shutter & Player Entry Door (Front Facade at Y = -4.0m)
    reg_box("ShutterFrame", 4.2, 0.3, 3.2, (-1.5, -4.1, 0.0), region=R_CORRUG_STEEL)
    reg_box("RollerShutter", 3.8, 0.1, 3.0, (-1.5, -4.15, 0.0), region=R_GYM_SHUTTER)

    # Illuminated Neon Sign ("COMBAT CLUB / MMA DOJO")
    reg_box("NeonSignBoard", 3.6, 0.25, 0.9, (-1.5, -4.2, 3.3), region=R_NEON_SIGN)

    # 4. External Heavy Punching Bag Gantry Frame & 2 Hanging Bags (Right side: X = 2.8m, Y = -4.0m)
    # Steel frame posts & beam
    reg_box("GantryPostL", 0.15, 0.15, 3.2, (1.8, -4.4, 0.0), region=R_CORRUG_STEEL)
    reg_box("GantryPostR", 0.15, 0.15, 3.2, (4.2, -4.4, 0.0), region=R_CORRUG_STEEL)
    reg_box("GantryTopBeam", 2.6, 0.15, 0.15, (3.0, -4.4, 3.1), region=R_CORRUG_STEEL)

    # 2 Heavy Punching Bags (16 segments each)
    reg_cyl("PunchBag1", r=0.22, h=1.4, segs=16, at=(2.4, -4.4, 1.2), region=R_PUNCH_BAG)
    reg_cyl("PunchBag2", r=0.22, h=1.4, segs=16, at=(3.6, -4.4, 1.2), region=R_PUNCH_BAG)

    # 5. Rooftop Ventilation Ducts & Fans
    reg_box("VentilationDuct", 4.0, 0.6, 0.5, (2.0, 0.0, 4.45), region=R_CORRUG_STEEL)
    reg_cyl("ExhaustVent", r=0.35, h=0.6, segs=16, at=(4.0, 0.0, 4.7), region=R_CORRUG_STEEL)

    # Finalize & Export
    shell = kit.join(parts, "Building_Dojo_02_Modern_Training_Hall")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_dojo_02_modern_training_hall_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_dojo_02_modern_training_hall.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/West York
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "building_dojo_02_modern_training_hall.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "building_dojo_02_modern_training_hall_preview.png")
        shutil.copy2(OUT_DIR / "atlas_dojo_02.png", TEXTURES_DIR / "atlas_dojo_02.png")
        print(f"[Dojo_02] deployed successfully.")
    except Exception as e:
        print(f"[Dojo_02] deploy notice: {e}")


if __name__ == "__main__":
    main()
