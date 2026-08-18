"""Rundown four-house council terrace, built as a repeatable street module.

The 20 m-wide shell terminates flush at both X boundaries, so copies can be
placed at 20 m intervals without a visible gap. Exterior only: opaque windows,
clear ground-level doors, one 256 px atlas, and deliberately cheap geometry.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_council_terrace.py
"""

import bmesh
import bpy

import asset_kit as kit
from atlas import Atlas, material_for

S = 256

R_BRICK = (0, 0, 128, 128)
R_BRICK_DAMP = (128, 0, 64, 64)
R_ROOF = (192, 0, 64, 64)
R_WINDOW = (128, 64, 32, 48)
R_WINDOW_DIRTY = (160, 64, 32, 48)
R_BOARD = (192, 64, 32, 48)
R_DOOR_RED = (128, 112, 32, 64)
R_DOOR_BLUE = (160, 112, 32, 64)
R_DOOR_GREEN = (192, 112, 32, 64)
R_DOOR_BOARD = (224, 112, 32, 64)
R_CONCRETE = (0, 128, 64, 64)
R_PAVEMENT = (64, 128, 64, 64)
R_BLACK = (0, 192, 32, 32)
R_GUTTER = (32, 192, 32, 32)
R_BIN_GREEN = (64, 192, 32, 32)
R_BIN_BLACK = (96, 192, 32, 32)
R_MOSS = (128, 192, 32, 32)

BRICK = (0.43, 0.24, 0.17)
MORTAR = (0.54, 0.49, 0.43)
ROOF = (0.24, 0.19, 0.18)
GLASS = (0.13, 0.17, 0.19)
FRAME = (0.78, 0.75, 0.68)
BOARD = (0.42, 0.30, 0.18)
CONCRETE = (0.46, 0.45, 0.42)
PAVE = (0.48, 0.47, 0.44)


def paint_atlas():
    a = Atlas(S, seed=27)

    x, y, w, h = R_BRICK
    a.bricks(x, y, w, h, brick=BRICK, mortar=MORTAR, bw=16, bh=8, jitter=0.07)
    a.shade(x, y, w, h, top=0.02, bottom=-0.08)
    a.noise(x, y, w, h, 0.025)
    # Old repairs and soot streaks are texture detail, not geometry.
    for rx, ry, rw, rh in [(18, 15, 22, 3), (72, 43, 14, 4), (97, 81, 18, 3)]:
        a.rect(x + rx, y + ry, rw, rh, (0.34, 0.31, 0.28))

    x, y, w, h = R_BRICK_DAMP
    a.bricks(x, y, w, h, brick=(0.34, 0.21, 0.16), mortar=(0.44, 0.42, 0.38),
             bw=12, bh=7, jitter=0.06)
    a.shade(x, y, w, h, top=-0.03, bottom=-0.18)
    a.noise(x, y, w, h, 0.03)

    x, y, w, h = R_ROOF
    a.rect(x, y, w, h, ROOF)
    for ty in range(y, y + h, 8):
        a.rect(x, ty, w, 1, (0.13, 0.12, 0.12))
        offset = 4 if ((ty - y) // 8) % 2 else 0
        for tx in range(x - offset, x + w, 8):
            a.rect(max(x, tx), ty, 1, min(8, y + h - ty), (0.15, 0.14, 0.14))
    a.noise(x, y, w, h, 0.035)

    def window(region, dirty=False):
        x, y, w, h = region
        a.rect(x, y, w, h, FRAME)
        a.rect(x + 3, y + 3, w - 6, h - 6, GLASS)
        a.rect(x + w // 2 - 1, y + 3, 2, h - 6, FRAME)
        a.rect(x + 3, y + h // 2 - 1, w - 6, 2, FRAME)
        a.rect(x + 4, y + h // 2 + 2, 8, h // 2 - 7, (0.21, 0.25, 0.26))
        if dirty:
            a.shade(x + 3, y + 3, w - 6, h - 6, top=-0.03, bottom=-0.14)
            for sx in (x + 7, x + 21):
                a.rect(sx, y + 5, 2, h - 12, (0.18, 0.16, 0.14))
        a.noise(x, y, w, h, 0.018)

    window(R_WINDOW)
    window(R_WINDOW_DIRTY, dirty=True)

    x, y, w, h = R_BOARD
    a.rect(x, y, w, h, BOARD)
    for py in range(y + 5, y + h, 9):
        a.rect(x, py, w, 1, (0.24, 0.18, 0.12))
    for nx, ny in [(x + 4, y + 4), (x + w - 5, y + 4),
                   (x + 4, y + h - 5), (x + w - 5, y + h - 5)]:
        a.disc(nx, ny, 1, (0.12, 0.12, 0.11))
    a.noise(x, y, w, h, 0.04)

    def door(region, colour, boarded=False):
        x, y, w, h = region
        a.rect(x, y, w, h, FRAME if not boarded else CONCRETE)
        a.rect(x + 3, y, w - 6, h - 3, colour)
        if boarded:
            for py in range(y + 8, y + h - 4, 12):
                a.rect(x + 3, py, w - 6, 3, (0.27, 0.20, 0.13))
        else:
            a.rect(x + 7, y + h - 22, w - 14, 14, (0.12, 0.15, 0.16))
            a.rect(x + w - 8, y + 25, 2, 5, (0.72, 0.60, 0.28))
            a.rect(x + 7, y + 9, w - 14, 14, tuple(max(0, c - 0.08) for c in colour))
        a.noise(x, y, w, h, 0.025)

    door(R_DOOR_RED, (0.47, 0.10, 0.08))
    door(R_DOOR_BLUE, (0.08, 0.20, 0.35))
    door(R_DOOR_GREEN, (0.09, 0.28, 0.18))
    door(R_DOOR_BOARD, BOARD, boarded=True)

    for region, colour, noise in [
            (R_CONCRETE, CONCRETE, 0.035), (R_PAVEMENT, PAVE, 0.025),
            (R_BLACK, (0.07, 0.07, 0.065), 0.015),
            (R_GUTTER, (0.20, 0.19, 0.18), 0.02),
            (R_BIN_GREEN, (0.10, 0.24, 0.14), 0.025),
            (R_BIN_BLACK, (0.08, 0.085, 0.08), 0.02),
            (R_MOSS, (0.18, 0.24, 0.10), 0.04)]:
        x, y, w, h = region
        a.rect(x, y, w, h, colour)
        a.noise(x, y, w, h, noise)

    x, y, w, h = R_PAVEMENT
    for px in range(x, x + w, 16):
        a.rect(px, y, 1, h, (0.35, 0.34, 0.32))
    for py in range(y, y + h, 16):
        a.rect(x, py, w, 1, (0.35, 0.34, 0.32))
    # A few dark cracks make the repeated pavement less pristine.
    for ox, oy in [(9, 11), (35, 28), (50, 7)]:
        a.rect(x + ox, y + oy, 2, 13, (0.22, 0.22, 0.21))

    return a.to_image("building_council_terrace", kit.OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_ROOF, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_CONCRETE, S, only=side("bottom"))


def make_gable_roof(name, width, depth, eave_z, ridge_z):
    """Continuous pitched roof whose X ends are flush for repeat placement."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    coords = [
        (-width / 2, -depth / 2, eave_z), (width / 2, -depth / 2, eave_z),
        (-width / 2, depth / 2, eave_z), (width / 2, depth / 2, eave_z),
        (-width / 2, 0, ridge_z), (width / 2, 0, ridge_z),
    ]
    verts = [bm.verts.new(co) for co in coords]
    bm.faces.new((verts[0], verts[1], verts[5], verts[4]))
    bm.faces.new((verts[3], verts[2], verts[4], verts[5]))
    bm.faces.new((verts[2], verts[0], verts[4]))
    bm.faces.new((verts[1], verts[3], verts[5]))
    bm.faces.new((verts[0], verts[2], verts[3], verts[1]))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    image = paint_atlas()
    material = material_for(image, "mat_council_terrace")
    pieces = []

    def box(name, w, d, h, at, front=R_BRICK, sides=R_BRICK,
            back=None, top=None, bottom=None):
        obj = kit.make_box(name, w, d, h, at)
        obj.data.materials.append(material)
        map_box(obj, front, sides, back, top, bottom)
        pieces.append(obj)
        return obj

    # Four 5 m houses. The shell and roof terminate exactly at +/-10 m.
    box("Pavement", 21.2, 8.7, 0.08, (0, -0.65, 0),
        front=R_CONCRETE, sides=R_CONCRETE, top=R_PAVEMENT)
    box("TerraceShell", 20.0, 7.0, 5.35, (0, 0, 0.08),
        front=R_BRICK, sides=R_BRICK_DAMP, back=R_BRICK_DAMP, top=R_BRICK)
    box("DampCourse", 20.0, 0.08, 0.48, (0, -3.54, 0.08),
        front=R_BRICK_DAMP, sides=R_BRICK_DAMP, top=R_MOSS)

    roof = make_gable_roof("ContinuousRoof", 20.0, 7.35, 5.43, 7.15)
    roof.data.materials.append(material)
    for poly in roof.data.polygons:
        region = R_ROOF if abs(poly.normal.x) < 0.5 else R_BRICK
        kit.map_faces_to_region(roof, region, S, only=lambda f, i=poly.index: f.index == i)
    pieces.append(roof)

    centres = (-7.5, -2.5, 2.5, 7.5)
    doors = (R_DOOR_RED, R_DOOR_BLUE, R_DOOR_BOARD, R_DOOR_GREEN)
    dirty = (R_WINDOW_DIRTY, R_WINDOW, R_BOARD, R_WINDOW_DIRTY)
    for i, cx in enumerate(centres):
        # Party-line drainpipes make each repeat boundary/house rhythm legible.
        if i > 0:
            box(f"Downpipe_{i}", 0.13, 0.16, 5.25, (cx - 2.5, -3.58, 0.1),
                front=R_GUTTER, sides=R_GUTTER, top=R_BLACK)
        door_x = cx - 1.35 if i % 2 == 0 else cx + 1.35
        window_x = cx + 0.85 if i % 2 == 0 else cx - 0.85
        box(f"Door_{i}", 1.05, 0.16, 2.18, (door_x, -3.57, 0.1),
            front=doors[i], sides=R_CONCRETE, top=R_CONCRETE)
        box(f"GroundWindow_{i}", 1.55, 0.13, 1.45, (window_x, -3.56, 0.62),
            front=dirty[i], sides=R_CONCRETE, top=R_CONCRETE)
        box(f"UpperWindowL_{i}", 1.20, 0.13, 1.35, (cx - 1.12, -3.56, 3.25),
            front=R_WINDOW_DIRTY if i in (1, 3) else R_WINDOW,
            sides=R_CONCRETE, top=R_CONCRETE)
        box(f"UpperWindowR_{i}", 1.20, 0.13, 1.35, (cx + 1.12, -3.56, 3.25),
            front=R_BOARD if i == 2 else R_WINDOW,
            sides=R_CONCRETE, top=R_CONCRETE)
        box(f"DoorStep_{i}", 1.35, 0.55, 0.14, (door_x, -3.78, 0.08),
            front=R_CONCRETE, sides=R_CONCRETE, top=R_CONCRETE)

    # Cheap continuous gutter, plus four chimney stacks shared by party walls.
    box("FrontGutter", 20.0, 0.16, 0.16, (0, -3.72, 5.32),
        front=R_GUTTER, sides=R_GUTTER, top=R_GUTTER)
    for i, x in enumerate((-7.5, -2.5, 2.5, 7.5)):
        box(f"Chimney_{i}", 0.72, 0.85, 1.05, (x, 0.35, 6.48),
            front=R_BRICK_DAMP, sides=R_BRICK_DAMP, top=R_BLACK)

    # A small amount of asymmetric clutter helps hide obvious tiling.
    box("WheelieBinGreen", 0.62, 0.60, 0.96, (-4.15, -4.00, 0.08),
        front=R_BIN_GREEN, sides=R_BIN_GREEN, top=R_BLACK)
    box("WheelieBinBlack", 0.62, 0.60, 0.90, (8.95, -4.00, 0.08),
        front=R_BIN_BLACK, sides=R_BIN_BLACK, top=R_BLACK)

    terrace = kit.join(pieces, "Building_CouncilTerrace_Row4")
    kit.finalize(terrace)
    kit.report_stats(terrace)
    kit.iso_preview(kit.OUT_DIR / "building_council_terrace_preview.png", [terrace],
                    resolution=1024)
    kit.export_glb(kit.OUT_DIR / "building_council_terrace.glb", [terrace])
    print("[building_council_terrace] repeat spacing: 20.00 m on X")
    print("[building_council_terrace] done")


main()
