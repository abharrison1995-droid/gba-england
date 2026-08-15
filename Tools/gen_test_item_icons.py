"""Draw a 16x16 pixel-art test shield icon, upscale x4 to 64x64.

Test-only dev art for the equipment system — deliberately simple.
"""
from PIL import Image

SCALE = 4
SIZE = 16

SILVER = (217, 217, 217, 255)
WHITE = (255, 255, 255, 255)
GOLD = (255, 215, 0, 255)
GRIP = (107, 68, 35, 255)
RED = (176, 48, 48, 255)
DARKRED = (120, 24, 24, 255)


def shield():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def body_cell(c, r):
        if r <= 1:
            return 2 <= c <= 13
        if r <= 9:
            return 2 <= c <= 13
        if r <= 11:
            return 3 <= c <= 12
        if r <= 13:
            return 4 <= c <= 11
        if r == 14:
            return 5 <= c <= 10
        return 7 <= c <= 8

    # Pass 1: gold border = any transparent cell adjacent to the body.
    for r in range(SIZE):
        for c in range(SIZE):
            if body_cell(c, r):
                continue
            near = any(
                0 <= c + dc < SIZE and 0 <= r + dr < SIZE and body_cell(c + dc, r + dr)
                for dc in (-1, 0, 1)
                for dr in (-1, 0, 1)
            )
            if near:
                px[c, r] = GOLD
    # Pass 2: body — red with a darker lower half for depth.
    for r in range(SIZE):
        for c in range(SIZE):
            if body_cell(c, r):
                px[c, r] = DARKRED if r >= 8 else RED
    return img


for name, painter in [("spr_ui_item_testshield", shield)]:
    img = painter().resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST)
    path = rf"Assets\Art\Generated\ui\{name}.png"
    img.save(path)
    print("wrote", path)
