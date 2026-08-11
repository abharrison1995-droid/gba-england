"""Preview mockup of the rebuilt Win95-desktop title screen.

Replicates, at the 1920x1080 canvas reference resolution, the layout that
TitleScreenWin95Builder now generates: teal desktop, taskbar with Start + clock,
St George poster, wordmark, and the Main Menu window layered over the flag.
Pure PIL; no Unity involved.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
TEAL = (0, 128, 128)
FACE = (192, 192, 192)
WHITE = (255, 255, 255)
SHADOW = (128, 128, 128)
NAVY = (0, 0, 128)
BLACK = (0, 0, 0)
FLAG_RED = (206, 17, 36)  # #CE1124

img = Image.new("RGB", (W, H), TEAL)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def raised(x0, y0, x1, y1, w=2):
    d.rectangle([x0, y0, x1, y1], fill=FACE)
    d.rectangle([x0, y0, x1, y0 + w - 1], fill=WHITE)          # top
    d.rectangle([x0, y0, x0 + w - 1, y1], fill=WHITE)          # left
    d.rectangle([x0, y1 - w + 1, x1, y1], fill=SHADOW)         # bottom
    d.rectangle([x1 - w + 1, y0, x1, y1], fill=SHADOW)         # right


def sunken(x0, y0, x1, y1, w=2):
    d.rectangle([x0, y0, x1, y1], fill=FACE)
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
raised(6, H - 44 + 6, 6 + 110, H - 6)                          # Start button
center_text(6 + 55, H - 22, "Start", font(22))
sunken(W - 6 - 110, H - 44 + 6, W - 6, H - 6)                  # clock tray
center_text(W - 6 - 55, H - 22, "12:00", font(20, bold=False))

# ---- St George poster: 800x480 centred at (960, 570) -----------------------
fx0, fy0, fx1, fy1 = 560, 330, 1360, 810
d.rectangle([fx0, fy0, fx1, fy1], fill=WHITE)
d.rectangle([912, fy0, 1088, fy1], fill=FLAG_RED)              # vertical arm (0.44-0.56)
d.rectangle([fx0, 522, fx1, 618], fill=FLAG_RED)               # horizontal arm (0.4-0.6)
# raised bevel frame over the flag edges
d.rectangle([fx0, fy0, fx1, fy0 + 1], fill=WHITE)
d.rectangle([fx0, fy0, fx0 + 1, fy1], fill=WHITE)
d.rectangle([fx0, fy1 - 1, fx1, fy1], fill=SHADOW)
d.rectangle([fx1 - 1, fy0, fx1, fy1], fill=SHADOW)

# ---- Wordmark: 620x240 slot, top of column at y=90 --------------------------
logo = Image.open(r"Assets\Textures\UI\Title\Title_Logo.png").convert("RGBA")
scale = min(620 / logo.width, 240 / logo.height)
logo = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.LANCZOS)
img.paste(logo, (960 - logo.width // 2, 90 + (240 - logo.height) // 2), logo)

# ---- Main Menu window: 470x330, y 370..700 ---------------------------------
wx0, wy0, wx1, wy1 = 725, 370, 1195, 700
raised(wx0, wy0, wx1, wy1)
# title bar (inset 3, height 34)
d.rectangle([wx0 + 3, wy0 + 3, wx1 - 3, wy0 + 3 + 34], fill=NAVY)
d.text((wx0 + 13, wy0 + 8), "Main Menu", font=font(20), fill=WHITE)
for i, glyph in enumerate(["X", "[]", "_"]):
    bx1 = wx1 - 9 - i * 40
    raised(bx1 - 34, wy0 + 7, bx1, wy0 + 7 + 26)
    center_text(bx1 - 17, wy0 + 20, glyph, font(14))
# buttons (3 shown: no save -> Continue hidden; runtime adds Settings)
body_cx = (wx0 + wx1) // 2
labels = ["New Game", "Settings", "Quit"]
total = len(labels) * 64 + (len(labels) - 1) * 14
y = (wy0 + 37 + wy1 - 16) // 2 - total // 2
for label in labels:
    raised(body_cx - 200, y, body_cx + 200, y + 64)
    center_text(body_cx, y + 32, label, font(26))
    y += 64 + 14

img.save("title_screen_win95_preview.png")
print("saved title_screen_win95_preview.png", img.size)
