"""Classic Victorian 2-Storey London Terraced House — Background 3D Asset.

Authentic Victorian London architecture:
- Red/stock brick facade with subtle weathering and mortar detailing
- Ground-floor rusticated stucco plinth & canted 3-sided bay window
- Recessed gloss front door with stone steps, brass hardware & fanlight
- Upper-floor Victorian 2-over-2 sash windows with stone sills & lintels
- Pitched slate roof with decorative dentil cornice, brick chimney stack & terracotta pots
- Modelled at real scale (1 unit = 1 metre), origin at bottom-centre, facing -Y.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_victorian_house.py
"""

import math
import random
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512  # High-detail 512x512 procedural atlas

# --- Atlas Region Definitions (x, y, w, h) in pixels, bottom-left origin ---
R_BRICK_MAIN    = (0,   256, 256, 256)   # Upper red/stock brick facade
R_BRICK_DARK    = (256, 256, 128, 256)   # Side party wall & chimney brick
R_SLATE_ROOF    = (0,   128, 256, 128)   # Weathered slate roof tiles
R_STUCCO        = (256, 128, 128, 128)   # Ground floor rusticated stucco
R_SASH_WINDOW   = (384, 384, 128, 128)   # Upper floor 2-over-2 sash window
R_BAY_FRONT     = (384, 256, 128, 128)   # Bay window front sash
R_BAY_SIDE      = (384, 128, 64,  128)   # Bay window angled side sash
R_DOOR          = (448, 128, 64,  128)   # Victorian panelled front door + fanlight
R_STONE_TRIM    = (0,   64,  256, 64)    # Sills, lintels, coping, steps
R_BAY_ROOF      = (256, 64,  128, 64)    # Lead/zinc flashing for bay canopy
R_CHIMNEY_POT   = (384, 64,  64,  64)    # Terracotta clay pot with soot
R_PAVEMENT      = (0,   0,   256, 64)    # Flagstone pavement / threshold base
R_CORNICE       = (256, 0,   256, 64)    # Decorative dentil moulding / eaves band

# --- Palette Colors (sRGB 0.0 - 1.0) ---
BRICK_RED_BASE  = (0.54, 0.24, 0.18)
BRICK_MORTAR    = (0.70, 0.67, 0.62)
BRICK_DARK_BASE = (0.40, 0.20, 0.16)
STUCCO_BASE     = (0.78, 0.75, 0.68)
STUCCO_GROOVE   = (0.58, 0.54, 0.48)
SLATE_BASE      = (0.28, 0.31, 0.35)
SLATE_DARK      = (0.20, 0.22, 0.25)
SLATE_HIGHLIGHT = (0.36, 0.40, 0.45)
STONE_CREAM     = (0.75, 0.72, 0.65)
STONE_DARK      = (0.55, 0.52, 0.46)
TIMBER_WHITE    = (0.92, 0.92, 0.90)
TIMBER_FRAME    = (0.82, 0.82, 0.80)
GLASS_DARK      = (0.10, 0.14, 0.18)
GLASS_HIGHLIGHT = (0.22, 0.28, 0.36)
DOOR_RED        = (0.48, 0.08, 0.08)
DOOR_DARK       = (0.30, 0.05, 0.05)
BRASS_GOLD      = (0.85, 0.72, 0.25)
TERRACOTTA      = (0.68, 0.32, 0.18)
SOOT_BLACK      = (0.15, 0.14, 0.14)
LEAD_GREY       = (0.35, 0.36, 0.38)
PAVE_GREY       = (0.50, 0.49, 0.47)


def paint_victorian_atlas():
    """Generates the high-detail procedural texture atlas."""
    a = Atlas(S, seed=42)

    # 1. Main Red/Stock Brick Facade (R_BRICK_MAIN)
    x, y, w, h = R_BRICK_MAIN
    a.bricks(x, y, w, h, brick=BRICK_RED_BASE, mortar=BRICK_MORTAR, bw=24, bh=10, jitter=0.08)
    a.noise(x, y, w, h, 0.035)
    # Subtle soot gradient near top / eaves
    a.shade(x, y, w, h, top=-0.05, bottom=0.0)

    # 2. Darker Party Wall & Chimney Brick (R_BRICK_DARK)
    x, y, w, h = R_BRICK_DARK
    a.bricks(x, y, w, h, brick=BRICK_DARK_BASE, mortar=(0.58, 0.55, 0.50), bw=24, bh=10, jitter=0.09)
    a.noise(x, y, w, h, 0.04)
    a.shade(x, y, w, h, top=-0.08, bottom=-0.02)

    # 3. Weathered Welsh Slate Roof (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, SLATE_BASE)
    tile_h = 12
    tile_w = 20
    row = 0
    for ty in range(y, y + h, tile_h):
        stagger = (tile_w // 2) if (row % 2 == 1) else 0
        # Horizontal slate overlap shadow & top highlight
        a.rect(x, ty, w, 2, SLATE_DARK)
        a.rect(x, min(y + h - 1, ty + 2), w, 1, SLATE_HIGHLIGHT)
        for tx in range(x - stagger, x + w, tile_w):
            x0 = max(x, tx)
            x1 = min(x + w, tx + tile_w)
            if x1 > x0:
                # Vertical tile split joint
                a.rect(x0, ty, 1, tile_h, SLATE_DARK)
                # Subtle tonal nuance per slate
                j = a.rng.uniform(-0.04, 0.04)
                tint = tuple(max(0.0, min(1.0, c + j)) for c in SLATE_BASE)
                a.rect(x0 + 1, ty + 3, max(1, x1 - x0 - 2), max(1, tile_h - 4), tint)
        row += 1
    a.noise(x, y, w, h, 0.03)

    # 4. Ground Floor Rusticated Stucco Plinth (R_STUCCO)
    x, y, w, h = R_STUCCO
    a.rect(x, y, w, h, STUCCO_BASE)
    # Horizontal stone joint channels (rustication)
    for gy in range(y, y + h, 16):
        a.rect(x, gy, w, 2, STUCCO_GROOVE)
        a.rect(x, gy + 2, w, 1, (0.88, 0.85, 0.78))
    # Street grime at bottom
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.03)

    # 5. Upper Floor Victorian 2-over-2 Sash Window (R_SASH_WINDOW)
    x, y, w, h = R_SASH_WINDOW
    # Brick surround / reveal
    a.rect(x, y, w, h, BRICK_RED_BASE)
    a.noise(x, y, w, h, 0.03)
    # Stone arch lintel at top
    a.rect(x + 12, y + h - 18, w - 24, 16, STONE_CREAM)
    a.rect(x + 12, y + h - 18, w - 24, 2, STONE_DARK)
    # Heavy stone sill at bottom
    a.rect(x + 8, y + 4, w - 16, 12, STONE_CREAM)
    a.rect(x + 8, y + 4, w - 16, 2, STONE_DARK)
    a.rect(x + 8, y + 14, w - 16, 2, (0.88, 0.86, 0.80))
    # Window opening & outer wooden box frame
    wx, wy, ww, wh = x + 16, y + 16, w - 32, h - 36
    a.rect(wx, wy, ww, wh, TIMBER_FRAME)
    # Dark glass cavity
    gx, gy, gw, gh = wx + 6, wy + 6, ww - 12, wh - 12
    a.rect(gx, gy, gw, gh, GLASS_DARK)
    # Upper/lower sash split bar
    mid_y = gy + gh // 2
    a.rect(gx, mid_y - 3, gw, 6, TIMBER_WHITE)
    # Vertical glazing bars (creating 2 panes top, 2 panes bottom)
    mid_x = gx + gw // 2
    a.rect(mid_x - 2, gy, 4, gh, TIMBER_WHITE)
    # Glass reflection highlights (diagonal glint on upper panes)
    a.rect(gx + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)
    a.rect(mid_x + 4, mid_y + 8, (gw // 2) - 8, (gh // 2) - 14, GLASS_HIGHLIGHT)
    # Subtle interior lace / curtain drape silhouette
    a.rect(gx + 2, mid_y + 4, 6, gh // 2 - 6, (0.45, 0.45, 0.42))
    a.rect(gx + gw - 8, mid_y + 4, 6, gh // 2 - 6, (0.45, 0.45, 0.42))

    # 6. Bay Window Front Panel (R_BAY_FRONT)
    x, y, w, h = R_BAY_FRONT
    a.rect(x, y, w, h, STUCCO_BASE)
    # Top & bottom decorative stone mouldings
    a.rect(x, y + h - 14, w, 14, STONE_CREAM)
    a.rect(x, y + h - 14, w, 2, STONE_DARK)
    a.rect(x, y, w, 16, STONE_CREAM)
    # Sash window inside bay
    bx, by, bw, bh = x + 12, y + 16, w - 24, h - 32
    a.rect(bx, by, bw, bh, TIMBER_WHITE)
    # Glass & glazing bars
    igx, igy, igw, igh = bx + 5, by + 5, bw - 10, bh - 10
    a.rect(igx, igy, igw, igh, GLASS_DARK)
    a.rect(igx, igy + igh // 2 - 2, igw, 5, TIMBER_WHITE)
    a.rect(igx + igw // 2 - 2, igy, 4, igh, TIMBER_WHITE)
    a.rect(igx + 4, igy + igh // 2 + 6, (igw // 2) - 8, (igh // 2) - 12, GLASS_HIGHLIGHT)
    a.noise(x, y, w, h, 0.02)

    # 7. Bay Window Angled Side Panel (R_BAY_SIDE)
    x, y, w, h = R_BAY_SIDE
    a.rect(x, y, w, h, STUCCO_BASE)
    a.rect(x, y + h - 14, w, 14, STONE_CREAM)
    a.rect(x, y, w, 16, STONE_CREAM)
    # Narrow side sash
    sx, sy, sw, sh = x + 8, y + 16, w - 16, h - 32
    a.rect(sx, sy, sw, sh, TIMBER_WHITE)
    sgx, sgy, sgw, sgh = sx + 4, sy + 4, sw - 8, sh - 8
    a.rect(sgx, sgy, sgw, sgh, GLASS_DARK)
    a.rect(sgx, sgy + sgh // 2 - 2, sgw, 4, TIMBER_WHITE)
    a.rect(sgx + 2, sgy + sgh // 2 + 4, sgw - 4, sgh // 2 - 8, GLASS_HIGHLIGHT)

    # 8. Victorian Front Door + Fanlight (R_DOOR)
    x, y, w, h = R_DOOR
    a.rect(x, y, w, h, STONE_CREAM)  # Stone entrance surround
    # White door frame
    dx, dy, dw, dh = x + 4, y, w - 8, h - 6
    a.rect(dx, dy, dw, dh, TIMBER_WHITE)
    # Arched / semi-circular fanlight at top
    fl_y = dy + dh - 26
    a.rect(dx + 4, fl_y, dw - 8, 22, GLASS_DARK)
    a.rect(dx + dw // 2 - 1, fl_y, 2, 22, TIMBER_WHITE)
    a.rect(dx + 6, fl_y + 4, (dw - 12) // 2, 14, GLASS_HIGHLIGHT)
    # Transom bar separator
    a.rect(dx + 2, fl_y - 4, dw - 4, 4, TIMBER_FRAME)
    # Main door leaf (Gloss Victorian Crimson)
    door_top = fl_y - 4
    door_h = door_top - dy
    a.rect(dx + 3, dy + 2, dw - 6, door_h - 2, DOOR_RED)
    # 4 Raised Door Panels
    pw = (dw - 18) // 2
    ph_top = (door_h - 28) // 2
    ph_bot = (door_h - 28) // 2
    # Upper left & right panels
    p_uy = dy + door_h - ph_top - 8
    a.rect(dx + 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + 7, p_uy + 1, pw - 2, ph_top - 2, DOOR_RED)
    a.rect(dx + dw - pw - 6, p_uy, pw, ph_top, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_uy + 1, pw - 2, ph_top - 2, DOOR_RED)
    # Lower left & right panels
    p_ly = dy + 8
    a.rect(dx + 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + 7, p_ly + 1, pw - 2, ph_bot - 2, DOOR_RED)
    a.rect(dx + dw - pw - 6, p_ly, pw, ph_bot, DOOR_DARK)
    a.rect(dx + dw - pw - 5, p_ly + 1, pw - 2, ph_bot - 2, DOOR_RED)
    # Polished Brass Hardware: central knocker, knob, letterbox
    a.rect(dx + dw // 2 - 2, p_uy + ph_top // 2 - 2, 4, 8, BRASS_GOLD)       # Knocker
    a.rect(dx + dw // 2 - 2, dy + door_h // 2 - 2, 4, 4, BRASS_GOLD)         # Centre knob
    a.rect(dx + dw // 2 - 8, dy + door_h // 2 - 12, 16, 4, BRASS_GOLD)       # Letterbox
    a.noise(x, y, w, h, 0.02)

    # 9. Stone Trims, Sills & Coping (R_STONE_TRIM)
    x, y, w, h = R_STONE_TRIM
    a.rect(x, y, w, h, STONE_CREAM)
    # Weathering streaks and bevel shadows
    for sy in range(y, y + h, 16):
        a.rect(x, sy, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.03)

    # 10. Bay Window Canopy Roof / Lead Flashing (R_BAY_ROOF)
    x, y, w, h = R_BAY_ROOF
    a.rect(x, y, w, h, LEAD_GREY)
    # Rolled lead seams
    for lx in range(x, x + w, 24):
        a.rect(lx, y, 3, h, (0.24, 0.25, 0.27))
        a.rect(lx + 3, y, 1, h, (0.48, 0.49, 0.52))
    a.noise(x, y, w, h, 0.025)

    # 11. Terracotta Chimney Pot (R_CHIMNEY_POT)
    x, y, w, h = R_CHIMNEY_POT
    a.rect(x, y, w, h, TERRACOTTA)
    # Flared clay crown at top
    a.rect(x, y + h - 12, w, 12, (0.75, 0.38, 0.22))
    # Soot accumulation near rim
    a.rect(x, y + h - 6, w, 6, SOOT_BLACK)
    a.shade(x, y, w, h, top=-0.15, bottom=0.05)
    a.noise(x, y, w, h, 0.03)

    # 12. Pavement & Threshold Base (R_PAVEMENT)
    x, y, w, h = R_PAVEMENT
    a.rect(x, y, w, h, PAVE_GREY)
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.38, 0.37, 0.35))
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.38, 0.37, 0.35))
    a.noise(x, y, w, h, 0.03)

    # 13. Decorative Cornice / Dentil Band (R_CORNICE)
    x, y, w, h = R_CORNICE
    a.rect(x, y, w, h, STONE_CREAM)
    # Dentil teeth (Victorian classical moulding blocks)
    for dx in range(x, x + w, 12):
        a.rect(dx, y + 10, 6, 14, STONE_DARK)
        a.rect(dx + 1, y + 12, 4, 10, (0.85, 0.82, 0.75))
    a.rect(x, y + 26, w, 4, STONE_DARK)
    a.rect(x, y + 30, w, 4, (0.90, 0.88, 0.82))
    a.noise(x, y, w, h, 0.02)

    return a.to_image("building_victorian_house_atlas", kit.OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STONE_TRIM, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STONE_TRIM, S, only=side("bottom"))


def make_pitched_roof(name, w, d, h, at=(0, 0, 0)):
    """Gable pitched roof with ridge along X (slopes facing front -Y and back +Y)."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    hw, hd = w / 2.0, d / 2.0
    x, y, z = at

    # Vertices: 4 base, 2 ridge
    b0 = bm.verts.new((x - hw, y - hd, z))
    b1 = bm.verts.new((x + hw, y - hd, z))
    b2 = bm.verts.new((x + hw, y + hd, z))
    b3 = bm.verts.new((x - hw, y + hd, z))
    r0 = bm.verts.new((x - hw, y, z + h))
    r1 = bm.verts.new((x + hw, y, z + h))

    # Faces
    bm.faces.new((b0, b1, r1, r0))  # Front slope (-Y)
    bm.faces.new((b2, b3, r0, r1))  # Back slope (+Y)
    bm.faces.new((b3, b0, r0))      # Left gable (-X)
    bm.faces.new((b1, b2, r1))      # Right gable (+X)
    bm.faces.new((b0, b3, b2, b1))  # Bottom (-Z)

    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_canted_bay(name, w, d, h, bevel=0.45, at=(0, 0, 0)):
    """Canted 3-sided bay window extrusion facing -Y."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    hw = w / 2.0
    x, y, z = at

    # 4 bottom vertices (against wall at y, projecting to y - d)
    b0 = bm.verts.new((x - hw,         y,     z))
    b1 = bm.verts.new((x - hw + bevel, y - d, z))
    b2 = bm.verts.new((x + hw - bevel, y - d, z))
    b3 = bm.verts.new((x + hw,         y,     z))

    # 4 top vertices
    t0 = bm.verts.new((x - hw,         y,     z + h))
    t1 = bm.verts.new((x - hw + bevel, y - d, z + h))
    t2 = bm.verts.new((x + hw - bevel, y - d, z + h))
    t3 = bm.verts.new((x + hw,         y,     z + h))

    # Faces
    bm.faces.new((b0, b1, t1, t0))  # Left angled side
    bm.faces.new((b1, b2, t2, t1))  # Front main face
    bm.faces.new((b2, b3, t3, t2))  # Right angled side
    bm.faces.new((t0, t1, t2, t3))  # Top cap
    bm.faces.new((b0, b3, b2, b1))  # Bottom
    bm.faces.new((b3, b0, t0, t3))  # Back against wall

    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_cylinder(name, r, h, segs=8, at=(0, 0, 0)):
    """Low-poly cylinder with bottom-centre origin."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    x, y, z = at
    bot_ring = []
    top_ring = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vx = x + r * math.cos(a)
        vy = y + r * math.sin(a)
        bot_ring.append(bm.verts.new((vx, vy, z)))
        top_ring.append(bm.verts.new((vx, vy, z + h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]))
    bm.faces.new(reversed(bot_ring))  # bottom cap facing -Z
    bm.faces.new(top_ring)            # top cap facing +Z
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    kit.reset_scene()
    img = paint_victorian_atlas()
    mat = material_for(img, "mat_victorian_house")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Architectural Dimensions & Geometry Layout
    # House footprint: 5.0m width x 7.0m depth.
    # Total height to roof ridge: ~7.6m (chimneys ~8.5m).
    # =========================================================================

    # 1. Pavement / Foundation Plinth
    register_box("Pavement", 6.0, 8.2, 0.10, (0, -0.4, 0),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_PAVEMENT)

    # 2. Ground Floor Stucco Base (Z: 0.10 to 3.00, H: 2.90m)
    register_box("GroundFloor", 5.0, 7.0, 2.90, (0, 0, 0.10),
                 front=R_STUCCO, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 3. Ground Floor Canted Bay Window (Left side: X = -1.15m, Width: 2.2m, Depth: 0.65m, H: 2.40m)
    bay = make_canted_bay("BayWindow", 2.2, 0.65, 2.40, bevel=0.45, at=(-1.15, -3.5, 0.35))
    bay.data.materials.append(mat)
    # Map bay window faces: front -> R_BAY_FRONT, angled sides -> R_BAY_SIDE, top -> R_BAY_ROOF
    kit.map_faces_to_region(bay, R_BAY_FRONT, S, only=lambda f: f.normal.y < -0.8)
    kit.map_faces_to_region(bay, R_BAY_SIDE,  S, only=lambda f: abs(f.normal.x) > 0.4 and f.normal.y < -0.2)
    kit.map_faces_to_region(bay, R_BAY_ROOF,  S, only=lambda f: f.normal.z > 0.7)
    kit.map_faces_to_region(bay, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.7 or f.normal.y > 0.5)
    parts.append(bay)

    # Bay Window Sloped Roof Canopy
    bay_roof = make_canted_bay("BayRoof", 2.36, 0.75, 0.32, bevel=0.50, at=(-1.15, -3.5, 2.75))
    bay_roof.data.materials.append(mat)
    kit.map_faces_to_region(bay_roof, R_BAY_ROOF, S, only=lambda f: f.normal.z > 0.3 or f.normal.y < -0.2)
    kit.map_faces_to_region(bay_roof, R_STONE_TRIM, S, only=lambda f: f.normal.z <= 0.3 and f.normal.y >= -0.2)
    parts.append(bay_roof)

    # 4. Front Entrance: Recessed Victorian Door & Threshold Steps (Right side: X = 1.35m)
    # Entrance Steps
    register_box("DoorStep1", 1.30, 0.65, 0.15, (1.35, -3.80, 0.10),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    register_box("DoorStep2", 1.20, 0.35, 0.15, (1.35, -3.50, 0.25),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # Front Door Slab
    register_box("FrontDoor", 1.05, 0.20, 2.25, (1.35, -3.52, 0.40),
                 front=R_DOOR, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 5. String Course / Mid-Level Moulding Band (Z: 3.00, H: 0.18m)
    register_box("MidCornice", 5.16, 7.12, 0.18, (0, -0.04, 3.00),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 6. First Floor Red Brick Facade (Z: 3.18 to 5.90, H: 2.72m)
    register_box("FirstFloor", 5.0, 7.0, 2.72, (0, 0, 3.18),
                 front=R_BRICK_MAIN, sides=R_BRICK_DARK, back=R_BRICK_DARK)

    # 7. Upper Floor Sash Windows (Relief boxes for sills and window frames)
    # Window Left (above Bay Window)
    register_box("UpperWindowL", 1.20, 0.18, 1.65, (-1.15, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)
    # Window Right (above Front Door)
    register_box("UpperWindowR", 1.10, 0.18, 1.65, (1.35, -3.50, 3.75),
                 front=R_SASH_WINDOW, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 8. Eaves Cornice / Parapet Band (Z: 5.90, H: 0.25m)
    register_box("EavesCornice", 5.22, 7.16, 0.25, (0, -0.06, 5.90),
                 front=R_CORNICE, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 9. Pitched Slate Roof (Pitched gable, H: 1.60m from Z: 6.15m to 7.75m)
    roof = make_pitched_roof("PitchedRoof", 5.18, 7.10, 1.60, at=(0, 0, 6.15))
    roof.data.materials.append(mat)
    # Front and back slopes -> R_SLATE_ROOF; side gables -> R_BRICK_DARK
    kit.map_faces_to_region(roof, R_SLATE_ROOF, S, only=lambda f: abs(f.normal.y) > 0.4 and f.normal.z > 0.2)
    kit.map_faces_to_region(roof, R_BRICK_DARK, S, only=lambda f: abs(f.normal.x) > 0.7)
    kit.map_faces_to_region(roof, R_STONE_TRIM, S, only=lambda f: f.normal.z < -0.5)
    parts.append(roof)

    # Ridge Tile Trim
    register_box("RoofRidge", 5.24, 0.22, 0.12, (0, 0, 7.72),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 10. Brick Chimney Stack on Right Party Wall (+X side: X = 2.05m, Y = 0.5m)
    register_box("ChimneyBase", 0.75, 1.20, 1.80, (2.05, 0.5, 6.70),
                 front=R_BRICK_DARK, sides=R_BRICK_DARK, top=R_STONE_TRIM)
    # Chimney Stone Cap
    register_box("ChimneyCap", 0.85, 1.30, 0.14, (2.05, 0.5, 8.50),
                 front=R_STONE_TRIM, sides=R_STONE_TRIM, top=R_STONE_TRIM)

    # 11. Terracotta Clay Chimney Pots (2 pots atop stack)
    for i, pot_y in enumerate([0.20, 0.80]):
        pot = make_cylinder(f"ChimneyPot_{i+1}", r=0.14, h=0.55, segs=8, at=(2.05, pot_y, 8.64))
        pot.data.materials.append(mat)
        kit.map_faces_to_region(pot, R_CHIMNEY_POT, S)
        parts.append(pot)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Victorian_House")
    kit.finalize(shell)
    kit.report_stats(shell)

    # Isometric Workbench preview matching in-game camera (30° pitch / 45° yaw)
    preview_path = kit.OUT_DIR / "building_victorian_house_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    # GLB export
    glb_path = kit.OUT_DIR / "building_victorian_house.glb"
    kit.export_glb(glb_path, [shell])
    print("[building_victorian_house] generation complete.")


main()
