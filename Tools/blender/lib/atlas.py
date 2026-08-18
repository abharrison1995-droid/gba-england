"""Tiny pixel-art texture atlas painter (runs INSIDE Blender; numpy ships with it).

Detail lives here, not in geometry: bricks, signage text, stickers, grime are
painted into one small atlas and faces are UV-mapped onto named regions.
Coordinates are bottom-left origin in pixels, matching Blender's image layout,
so a painted rect and its UV region are the same numbers.
"""

import random
from pathlib import Path

import numpy as np

import bpy

# 5x7 pixel font, rows listed top to bottom. Extend as signage needs it.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "£": ["00110", "01001", "01000", "11110", "01000", "01000", "11111"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


class Atlas:
    def __init__(self, size=256, seed=1):
        self.size = size
        self.px = np.zeros((size, size, 4), dtype=np.float32)
        self.px[..., 3] = 1.0
        self.rng = random.Random(seed)

    # -- painting ---------------------------------------------------------

    def rect(self, x, y, w, h, color):
        r, g, b = color
        self.px[y:y + h, x:x + w, 0] = r
        self.px[y:y + h, x:x + w, 1] = g
        self.px[y:y + h, x:x + w, 2] = b

    def noise(self, x, y, w, h, amount=0.03):
        """Per-pixel value jitter over a region — breaks up flat fills."""
        jitter = np.random.default_rng(self.rng.randrange(1 << 30)).uniform(
            -amount, amount, size=(h, w, 1)).astype(np.float32)
        self.px[y:y + h, x:x + w, :3] = np.clip(
            self.px[y:y + h, x:x + w, :3] + jitter, 0.0, 1.0)

    def shade(self, x, y, w, h, top=0.0, bottom=-0.12):
        """Vertical brightness ramp (bottom-up), e.g. street grime."""
        ramp = np.linspace(bottom, top, h, dtype=np.float32).reshape(h, 1, 1)
        self.px[y:y + h, x:x + w, :3] = np.clip(
            self.px[y:y + h, x:x + w, :3] + ramp, 0.0, 1.0)

    def bricks(self, x, y, w, h, brick=(0.47, 0.30, 0.23),
               mortar=(0.62, 0.58, 0.53), bw=16, bh=8, jitter=0.05):
        self.rect(x, y, w, h, mortar)
        row = 0
        for by in range(y, y + h, bh):
            offset = (bw // 2) if row % 2 else 0
            for bx in range(x - offset, x + w, bw):
                j = self.rng.uniform(-jitter, jitter)
                col = tuple(max(0.0, min(1.0, c + j)) for c in brick)
                x0, x1 = max(x, bx), min(x + w, bx + bw - 1)
                y1 = min(y + h, by + bh - 1)
                if x1 > x0:
                    self.rect(x0, by, x1 - x0, y1 - by, col)
            row += 1

    def text(self, x, y, string, color, scale=1):
        """Draw string with its top-left at (x, y_top). Returns width in px."""
        cx = x
        for ch in string:
            glyph = FONT.get(ch.upper())
            if glyph is None:
                cx += 6 * scale
                continue
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + col_i * scale,
                                  y - (row_i + 1) * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_width(self, string, scale=1):
        return len(string) * 6 * scale

    def disc(self, cx, cy, r, color):
        yy, xx = np.ogrid[:self.size, :self.size]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        for i, c in enumerate(color):
            self.px[..., i][mask] = c

    # -- output -----------------------------------------------------------

    def to_image(self, name, out_dir):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        img = bpy.data.images.new(name, width=self.size, height=self.size,
                                  alpha=False)
        img.pixels[:] = self.px.ravel()
        img.filepath_raw = str(out_dir / f"{name}.png")
        img.file_format = "PNG"
        img.save()
        return img


def material_for(img, name):
    """Flat-lit friendly material showing the atlas with nearest filtering."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.95
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"],
                            bsdf.inputs["Base Color"])
    return mat
