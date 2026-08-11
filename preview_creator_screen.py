"""Preview mockup of the rebuilt Win95-desktop character creator.

Replicates, at the 1920x1080 canvas reference resolution, the layout that
CharacterCreatorWin95Builder now generates: teal desktop, shared taskbar, and the
"Pick your Brit" window floating over the desktop. Pure PIL; no Unity involved.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
TEAL = (0, 128, 128)
FACE = (192, 192, 192)
WHITE = (255, 255, 255)
SHADOW = (128, 128, 128)
NAVY = (0, 0, 128)
BLACK = (0, 0, 0)
PAPER_DOLL_BLUE = (100, 149, 237)  # #6495ED

img = Image.new("RGB", (W, H), TEAL)
d = ImageDraw.Draw(img)


def font(size, bold=True, italic=False):
    name = "arialbd.ttf" if bold else ("ariali.ttf" if italic else "arial.ttf")
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def raised(x0, y0, x1, y1, w=2, fill=FACE):
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.rectangle([x0, y0, x1, y0 + w - 1], fill=WHITE)
    d.rectangle([x0, y0, x0 + w - 1, y1], fill=WHITE)
    d.rectangle([x0, y1 - w + 1, x1, y1], fill=SHADOW)
    d.rectangle([x1 - w + 1, y0, x1, y1], fill=SHADOW)


def sunken(x0, y0, x1, y1, w=2, fill=FACE):
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.rectangle([x0, y0, x1, y0 + w - 1], fill=SHADOW)
    d.rectangle([x0, y0, x0 + w - 1, y1], fill=SHADOW)
    d.rectangle([x0, y1 - w + 1, x1, y1], fill=WHITE)
    d.rectangle([x1 - w + 1, y0, x1, y1], fill=WHITE)


def center_text(cx, cy, text, f, fill=BLACK):
    box = d.textbbox((0, 0), text, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text((cx - tw / 2 - box[0], cy - th / 2 - box[1]), text, font=f, fill=fill)


# ---- Taskbar (bottom 44 px) -------------------------------------------------
raised(0, H - 44, W - 1, H - 1)
raised(6, H - 44 + 6, 6 + 110, H - 6)
center_text(6 + 55, H - 22, "Start", font(22))
sunken(W - 6 - 110, H - 44 + 6, W - 6, H - 6)
center_text(W - 6 - 55, H - 22, "12:00", font(20, bold=False))

# ---- Creator window: anchors (0.04,0.06)-(0.96,0.95) ------------------------
WX0, WY0, WX1, WY1 = 77, 54, 1843, 1015  # top-left coords
WW, WH = WX1 - WX0, WY1 - WY0
raised(WX0, WY0, WX1, WY1)
d.rectangle([WX0 + 3, WY0 + 3, WX1 - 3, WY0 + 3 + 36], fill=NAVY)
d.text((WX0 + 13, WY0 + 10), "Pick your Brit", font=font(22), fill=WHITE)
for i, glyph in enumerate(["X", "[]", "_"]):
    bx1 = WX1 - 9 - i * 40
    raised(bx1 - 34, WY0 + 8, bx1, WY0 + 8 + 28)
    center_text(bx1 - 17, WY0 + 22, glyph, font(14))


def box(amin, amax):
    """Window-relative anchors -> top-left-coord rect."""
    x0 = WX0 + amin[0] * WW
    x1 = WX0 + amax[0] * WW
    y0 = WY0 + (1 - amax[1]) * WH
    y1 = WY0 + (1 - amin[1]) * WH
    return x0, y0, x1, y1


# Name input — sunken white field
x0, y0, x1, y1 = box((0.28, 0.835), (0.72, 0.90))
sunken(x0, y0, x1, y1, fill=WHITE)
d.text((x0 + 14, y0 + (y1 - y0) / 2 - 13), "Player name here!",
       font=font(24, bold=False, italic=True), fill=(0, 0, 0))

# Class tabs — five raised buttons
x0, y0, x1, y1 = box((0.03, 0.745), (0.97, 0.82))
tab_w = (x1 - x0 - 4 * 8) / 5
for i, name in enumerate(["Young Driller", "Stabmeister", "Mr Hood", "Dynamo", "Bunda Basher"]):
    tx0 = x0 + i * (tab_w + 8)
    raised(tx0, y0, tx0 + tab_w, y1)
    center_text(tx0 + tab_w / 2, (y0 + y1) / 2, name, font(20))

# Details panel
x0, y0, x1, y1 = box((0.03, 0.22), (0.38, 0.725))
raised(x0, y0, x1, y1)
dw, dh = x1 - x0, y1 - y0
nb = (x0 + 0.05 * dw, y0 + 0.025 * dh, x0 + 0.95 * dw, y0 + 0.115 * dh)
d.rectangle(nb, fill=BLACK)
center_text((nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2, "Young Driller", font(26), fill=WHITE)
d.text((x0 + 0.07 * dw, y0 + 0.14 * dh), "Class tagline and readouts", font=font(20, bold=False), fill=BLACK)
d.text((x0 + 0.07 * dw, y0 + 0.40 * dh), "Specialises in: ...", font=font(20), fill=BLACK)
d.text((x0 + 0.07 * dw, y0 + 0.52 * dh), "STR / END / AGI\nINT / AWA / PER\nHP / Resource", font=font(19, bold=False), fill=BLACK)

# Intro panel
x0, y0, x1, y1 = box((0.40, 0.22), (0.63, 0.725))
raised(x0, y0, x1, y1)
intro = "It's time for GBH: England.\nAre you ready? Magic? Police?\nFascists? It's all here!\n\nDive in! Pick one of five\nclasses and discover the\nreal England!"
d.text((x0 + 18, y0 + 18), intro, font=font(20, bold=False), fill=BLACK)

# Preview panel — cornflower paper-doll block
x0, y0, x1, y1 = box((0.65, 0.22), (0.97, 0.725))
raised(x0, y0, x1, y1)
pw, ph = x1 - x0, y1 - y0
bx0, by0 = x0 + 0.18 * pw, y0 + 0.05 * ph
bx1, by1 = x0 + 0.82 * pw, y0 + 0.95 * ph
d.rectangle([bx0, by0, bx1, by1], fill=PAPER_DOLL_BLUE)
center_text((x0 + x1) / 2, (y0 + y1) / 2, "Visual pending", font(24, bold=False, italic=True), fill=BLACK)

# Confirm / Back buttons
for amin, amax, label in [
    ((0.28, 0.105), (0.72, 0.195), "Enter Manor Cellars"),
    ((0.28, 0.02), (0.72, 0.095), "Back"),
]:
    x0, y0, x1, y1 = box(amin, amax)
    raised(x0, y0, x1, y1)
    center_text((x0 + x1) / 2, (y0 + y1) / 2, label, font(24))

img.save("creator_screen_win95_preview.png")
print("saved creator_screen_win95_preview.png", img.size)
