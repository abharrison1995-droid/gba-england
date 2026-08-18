"""Quidland exterior shell — band 6. Pound shop that sells weapons.

Recreates the look of the old Tripo model (two-storey London brick, blue
fascia, sticker-plastered shopfront) as clean parametric boxes + a painted
pixel atlas. Exterior only, opaque windows, clear proud door at ground level
(the USE-prompt threshold), per the band 6 contract in docs/art/ART_QUEUE.md.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_quidland.py
"""

import bpy

import asset_kit as kit
from atlas import Atlas, material_for

S = 256  # atlas size

# --- atlas regions (x, y, w, h) — bottom-left origin, matches painting ------
R_FASCIA = (0, 224, 256, 32)
R_FASCIA_SIDE = (0, 192, 64, 32)
R_SHOPFRONT = (0, 128, 128, 64)
R_DOOR = (128, 128, 32, 64)
R_WINDOW = (160, 128, 32, 40)
R_CONCRETE = (192, 128, 32, 32)
R_ROOF = (224, 128, 32, 32)
R_PAVEMENT = (192, 160, 64, 48)
R_BRICK = (0, 0, 128, 128)
R_BRICK_GRIMY = (128, 0, 64, 64)

BLUE = (0.04, 0.22, 0.65)
YELLOW = (1.0, 0.82, 0.05)
WHITE = (0.95, 0.95, 0.95)
RED = (0.80, 0.10, 0.08)
NAVY = (0.10, 0.14, 0.30)
GLASS = (0.07, 0.10, 0.12)
CONCRETE = (0.66, 0.64, 0.60)
ROOF = (0.22, 0.22, 0.24)
PAVE = (0.52, 0.51, 0.49)


def paint_atlas():
    a = Atlas(S, seed=7)

    # Fascia: blue band, white trim lines, QUID in yellow / LAND in white.
    x, y, w, h = R_FASCIA
    a.rect(x, y, w, h, BLUE)
    a.rect(x, y + h - 2, w, 2, WHITE)
    a.rect(x, y, w, 2, WHITE)
    tw = a.text_width("QUIDLAND", scale=4)
    tx = x + (w - tw) // 2
    ty = y + h - 2  # top of glyphs, garish and full-bleed like the real thing
    used = a.text(tx, ty, "QUID", YELLOW, scale=4)
    a.text(tx + used, ty, "LAND", WHITE, scale=4)
    a.noise(x, y, w, h, 0.015)

    # Fascia side: plain blue with trim.
    x, y, w, h = R_FASCIA_SIDE
    a.rect(x, y, w, h, BLUE)
    a.rect(x, y + h - 2, w, 2, WHITE)
    a.rect(x, y, w, 2, WHITE)
    a.noise(x, y, w, h, 0.015)

    # Shopfront: stallriser, glass, mullions, posters, price stickers.
    x, y, w, h = R_SHOPFRONT
    a.rect(x, y, w, h, GLASS)
    a.rect(x, y, w, 9, NAVY)                        # stallriser
    for mx in range(x, x + w + 1, 32):              # mullions
        a.rect(max(x, min(mx, x + w - 2)), y, 2, h, (0.72, 0.72, 0.70))
    for px, py, pw, ph in [(x + 6, y + 22, 20, 26), (x + 40, y + 18, 18, 22),
                           (x + 70, y + 24, 20, 24), (x + 100, y + 16, 18, 26)]:
        a.rect(px, py, pw, ph, YELLOW)              # window posters
        a.rect(px + 2, py + 2, pw - 4, ph - 4, WHITE)
        a.rect(px + 4, py + ph - 10, pw - 8, 6, RED)
    for cx, cy in [(x + 30, y + 50), (x + 62, y + 46), (x + 96, y + 52)]:
        a.disc(cx, cy, 7, RED)                      # everything-a-quid stickers
        a.text(cx - 5, cy + 4, "£1", YELLOW, scale=1)
    a.noise(x, y, w, h, 0.02)

    # Door: white frame, navy leaf, glass panel, handle.
    x, y, w, h = R_DOOR
    a.rect(x, y, w, h, WHITE)
    a.rect(x + 3, y, w - 6, h - 3, NAVY)
    a.rect(x + 6, y + h // 2, w - 12, h // 2 - 8, (0.13, 0.18, 0.22))
    a.rect(x + w - 7, y + 24, 2, 6, YELLOW)
    a.noise(x, y, w, h, 0.02)

    # Upper window: frame, dark glass, sash bar, sky glint top-left.
    x, y, w, h = R_WINDOW
    a.rect(x, y, w, h, WHITE)
    a.rect(x + 3, y + 3, w - 6, h - 6, (0.16, 0.20, 0.28))
    a.rect(x + 3, y + h // 2 - 1, w - 6, 2, WHITE)
    a.rect(x + 4, y + h // 2 + 2, (w - 8) // 2, h // 2 - 6, (0.24, 0.30, 0.40))
    a.noise(x, y, w, h, 0.02)

    # Flat fills.
    for region, col, n in [(R_CONCRETE, CONCRETE, 0.03), (R_ROOF, ROOF, 0.03),
                           (R_PAVEMENT, PAVE, 0.025)]:
        x, y, w, h = region
        a.rect(x, y, w, h, col)
        a.noise(x, y, w, h, n)
    x, y, w, h = R_PAVEMENT                          # paving joints
    for jx in range(x, x + w, 16):
        a.rect(jx, y, 1, h, (0.44, 0.43, 0.41))
    for jy in range(y, y + h, 16):
        a.rect(x, jy, w, 1, (0.44, 0.43, 0.41))

    # Brick: clean upper + grimy ground-floor variant.
    x, y, w, h = R_BRICK
    a.bricks(x, y, w, h)
    a.noise(x, y, w, h, 0.02)
    x, y, w, h = R_BRICK_GRIMY
    a.bricks(x, y, w, h, brick=(0.38, 0.24, 0.19),
             mortar=(0.55, 0.50, 0.45), jitter=0.06)
    a.shade(x, y, w, h, top=0.0, bottom=-0.10)
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_quidland", kit.OUT_DIR)


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


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_quidland")

    boxes = []

    def box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        boxes.append(o)
        return o

    # Front faces -Y. Building footprint 8 x 6 m, ~7 m to parapet.
    box("Pavement", 9.4, 7.6, 0.08, (0, -0.5, 0),
        front=R_CONCRETE, sides=R_CONCRETE, top=R_PAVEMENT)
    box("GroundFloor", 8, 6, 2.6, (0, 0, 0.08),
        front=R_SHOPFRONT, sides=R_BRICK_GRIMY)
    box("Door", 1.6, 0.25, 2.3, (2.2, -3.0, 0.08),
        front=R_DOOR, sides=R_CONCRETE, top=R_CONCRETE)
    box("Fascia", 8.36, 6.3, 0.9, (0, -0.15, 2.68),
        front=R_FASCIA, sides=R_FASCIA_SIDE, back=R_CONCRETE,
        top=R_CONCRETE)
    box("UpperFloor", 8, 6, 3.0, (0, 0, 3.58),
        front=R_BRICK, sides=R_BRICK)
    box("WindowL", 1.3, 0.16, 1.6, (-1.8, -3.0, 4.35),
        front=R_WINDOW, sides=R_CONCRETE, top=R_CONCRETE)
    box("WindowR", 1.3, 0.16, 1.6, (1.8, -3.0, 4.35),
        front=R_WINDOW, sides=R_CONCRETE, top=R_CONCRETE)
    box("Parapet", 8.3, 6.3, 0.35, (0, 0, 6.58),
        front=R_CONCRETE, sides=R_CONCRETE)
    box("Chimney", 0.9, 0.7, 1.3, (2.6, 1.8, 6.6),
        front=R_BRICK, sides=R_BRICK, top=R_CONCRETE)

    shell = kit.join(boxes, "Building_Quidland")
    kit.finalize(shell)
    kit.report_stats(shell)
    kit.iso_preview(kit.OUT_DIR / "building_quidland_preview.png", [shell],
                    resolution=1024)
    kit.export_glb(kit.OUT_DIR / "building_quidland.glb", [shell])
    print("[building_quidland] done")


main()
