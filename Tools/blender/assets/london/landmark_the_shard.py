"""The Shard (London Glass Spire Skyscraper Landmark).

Specs:
- 8.0m x 8.0m footprint, Height: 22.0m to fractured glass spire apex.
- Modern London iconic architecture:
  - Tapering 4-sided pyramidal glass curtain wall shards.
  - Reflective sky blue / cyan mirrored glass with white diagrid structural bracing.
  - Fractured glass pinnacle spire at apex with open observation terrace.
  - Ground-floor glazed lobby with granite plaza plinth.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_the_shard.py
"""

import math
import shutil
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR
TOOLS_OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"

# --- Atlas Region Definitions (x, y, w, h) ---
R_SHARD_GLASS   = (0,   256, 256, 256)   # Reflective blue glass curtain with diagrid bracing
R_LOBBY_BASE    = (256, 256, 256, 256)   # Ground floor concourse lobby with revolving doors
R_SPANDREL_TIER = (0,   128, 256, 128)   # Intermediate structural floor plates & louvres
R_FRACTURED_TIP = (256, 128, 128, 128)   # Open glass pinnacle shards with sky highlights
R_PLAZA_PAVE    = (384, 128, 128, 128)   # Modern granite public realm paving
R_STEEL_DIAGRID = (0,   0,   256, 128)   # White structural steel diagrid nodes
R_SHARD_SIGN    = (256, 0,   128, 128)   # "THE SHARD - LONDON BRIDGE" illuminated plaque
R_TERRACE_DECK  = (384, 0,   128, 128)   # Viewing level observation terrace decking

# --- Palette Colors ---
SHARD_BLUE      = (0.20, 0.48, 0.72)
SHARD_CYAN      = (0.35, 0.72, 0.90)
SHARD_HIGHLIGHT = (0.75, 0.90, 0.98)
STEEL_WHITE     = (0.92, 0.94, 0.96)
DARK_SPANDREL   = (0.14, 0.16, 0.18)
GRANITE_GREY    = (0.60, 0.62, 0.65)


def paint_shard_atlas():
    a = Atlas(S, seed=2501)

    # 1. Reflective Glass Curtain with Diagrid Bracing (R_SHARD_GLASS)
    x, y, w, h = R_SHARD_GLASS
    a.rect(x, y, w, h, SHARD_BLUE)
    # Sky vertical gradient reflection
    a.shade(x, y, w, h, top=0.20, bottom=-0.15)
    # Horizontal floor band mullions
    for fy in range(y, y + h, 28):
        a.rect(x, fy, w, 3, DARK_SPANDREL)
        a.rect(x, fy + 3, w, 1, SHARD_HIGHLIGHT)
    # Vertical window mullions
    for fx in range(x, x + w, 24):
        a.rect(fx, y, 2, h, (0.28, 0.32, 0.36))
    # Structural White Diagrid Bracing
    for dy in range(y, y + h, 64):
        for dx in range(x, x + w, 64):
            for step in range(0, 64, 4):
                a.rect(dx + step, dy + step, 3, 3, STEEL_WHITE)
                a.rect(dx + 64 - step, dy + step, 3, 3, STEEL_WHITE)
    a.noise(x, y, w, h, 0.02)

    # 2. Ground Floor Concourse Lobby (R_LOBBY_BASE)
    x, y, w, h = R_LOBBY_BASE
    a.rect(x, y, w, h, DARK_SPANDREL)
    gx, gy, gw, gh = x + 10, y + 10, w - 20, h - 20
    a.rect(gx, gy, gw, gh, (0.80, 0.88, 0.92))
    # Revolving glass doors & atrium lighting
    for rx in [gx + 30, gx + gw // 2 - 20, gx + gw - 70]:
        a.rect(rx, gy + 4, 40, gh - 40, (0.35, 0.40, 0.45))
        a.disc(rx + 20, gy + gh - 20, 16, (0.98, 0.95, 0.80))
    # "THE SHARD" header banner
    s1 = "THE SHARD"
    tw = a.text_width(s1, scale=3)
    a.text(gx + (gw - tw) // 2, gy + gh - 14, s1, STEEL_WHITE, scale=3)
    a.noise(x, y, w, h, 0.015)

    # 3. Intermediate Spandrel Tier (R_SPANDREL_TIER)
    x, y, w, h = R_SPANDREL_TIER
    a.rect(x, y, w, h, DARK_SPANDREL)
    for ly in range(y + 8, y + h - 8, 12):
        a.rect(x + 6, ly, w - 12, 4, (0.30, 0.35, 0.40))
    a.noise(x, y, w, h, 0.025)

    # 4. Fractured Glass Pinnacle (R_FRACTURED_TIP)
    x, y, w, h = R_FRACTURED_TIP
    a.rect(x, y, w, h, SHARD_CYAN)
    a.shade(x, y, w, h, top=0.30, bottom=0.0)
    for fx in range(x, x + w, 16):
        a.rect(fx, y, 2, h, STEEL_WHITE)
    a.noise(x, y, w, h, 0.02)

    # 5. Granite Public Realm Plaza (R_PLAZA_PAVE)
    x, y, w, h = R_PLAZA_PAVE
    a.rect(x, y, w, h, GRANITE_GREY)
    for py in range(y, y + h, 24):
        a.rect(x, py, w, 2, (0.45, 0.48, 0.50))
    for px in range(x, x + w, 24):
        a.rect(px, y, 2, h, (0.45, 0.48, 0.50))
    a.noise(x, y, w, h, 0.03)

    # 6. Steel Diagrid Nodes (R_STEEL_DIAGRID)
    x, y, w, h = R_STEEL_DIAGRID
    a.rect(x, y, w, h, (0.15, 0.18, 0.22))
    for nx in range(x + 16, x + w - 16, 32):
        for ny in range(y + 16, y + h - 16, 32):
            a.disc(nx, ny, 8, STEEL_WHITE)
            a.disc(nx, ny, 4, DARK_SPANDREL)
    a.noise(x, y, w, h, 0.02)

    # 7. Shard Sign Plaque (R_SHARD_SIGN)
    x, y, w, h = R_SHARD_SIGN
    a.rect(x, y, w, h, (0.10, 0.12, 0.14))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.22, 0.26, 0.30))
    s_sign = "THE SHARD"
    sw = a.text_width(s_sign, scale=2)
    a.text(x + (w - sw) // 2, y + h - 24, s_sign, SHARD_CYAN, scale=2)
    a.noise(x, y, w, h, 0.02)

    # 8. Terrace Deck (R_TERRACE_DECK)
    x, y, w, h = R_TERRACE_DECK
    a.rect(x, y, w, h, (0.40, 0.42, 0.45))
    a.noise(x, y, w, h, 0.03)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_the_shard_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_SPANDREL_TIER, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_SPANDREL_TIER, S, only=side("bottom"))


def make_tapered_shard_tier(name, bw, bd, tw, td, h, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    hbw, hbd = bw / 2.0, bd / 2.0
    htw, htd = tw / 2.0, td / 2.0
    verts = [
        (-hbw, -hbd, 0), (hbw, -hbd, 0), (hbw, hbd, 0), (-hbw, hbd, 0),
        (-htw, -htd, h), (htw, -htd, h), (htw, htd, h), (-htw, htd, h)
    ]
    faces = [
        (0, 1, 2, 3),    # bottom
        (0, 1, 5, 4),    # front
        (1, 2, 6, 5),    # right
        (2, 3, 7, 6),    # back
        (3, 0, 4, 7),    # left
        (4, 5, 6, 7),    # top
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_shard_atlas()
    mat = material_for(img, "mat_the_shard")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # The Shard (8.0m x 8.0m Footprint, Height: 22.0m)
    # - Plaza Base & Concourse (Z: 0.0 to 3.0m)
    # - Lower Shard Tier (Z: 3.0 to 9.0m, Tapers from 7.2m to 5.4m)
    # - Middle Shard Tier (Z: 9.0 to 15.0m, Tapers from 5.4m to 3.6m)
    # - Upper Shard Tier (Z: 15.0 to 19.5m, Tapers from 3.6m to 1.8m)
    # - Fractured Glass Pinnacle Spire Shards (Z: 19.5 to 22.5m)
    # =========================================================================

    # 1. Granite Public Plaza Plinth (8.4m x 8.4m, Z = 0.00 to 0.20m)
    register_box("ShardPlaza", 8.40, 8.40, 0.20, (0.0, 0.0, 0.0),
                 front=R_PLAZA_PAVE, sides=R_PLAZA_PAVE, top=R_PLAZA_PAVE)

    # 2. Ground Floor Concourse Lobby (7.6m x 7.6m, Z: 0.20m to 3.20m, H: 3.0m)
    register_box("ShardLobby", 7.60, 7.60, 3.00, (0.0, 0.0, 0.20),
                 front=R_LOBBY_BASE, sides=R_LOBBY_BASE, back=R_LOBBY_BASE)

    # 3. Lower Tier (Tapers from 7.2m to 5.4m, Z: 3.20m to 9.20m, H: 6.0m)
    t1 = make_tapered_shard_tier("Tier1", 7.20, 7.20, 5.40, 5.40, 6.00, at=(0.0, 0.0, 3.20))
    t1.data.materials.append(mat)
    kit.map_faces_to_region(t1, R_SHARD_GLASS, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t1, R_SPANDREL_TIER, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t1)

    # 4. Middle Tier (Tapers from 5.4m to 3.6m, Z: 9.20m to 15.20m, H: 6.0m)
    t2 = make_tapered_shard_tier("Tier2", 5.40, 5.40, 3.60, 3.60, 6.00, at=(0.0, 0.0, 9.20))
    t2.data.materials.append(mat)
    kit.map_faces_to_region(t2, R_SHARD_GLASS, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t2, R_SPANDREL_TIER, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t2)

    # 5. Upper Tier (Tapers from 3.6m to 1.8m, Z: 15.20m to 19.50m, H: 4.30m)
    t3 = make_tapered_shard_tier("Tier3", 3.60, 3.60, 1.80, 1.80, 4.30, at=(0.0, 0.0, 15.20))
    t3.data.materials.append(mat)
    kit.map_faces_to_region(t3, R_SHARD_GLASS, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t3, R_TERRACE_DECK, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t3)

    # 6. Fractured Glass Pinnacle Shard Blades (4 asymmetrical glass blades at apex, Z = 19.50m to 22.50m)
    # Front-Left Shard Blade
    register_box("PinnacleShard1", 0.85, 0.85, 3.00, (-0.45, -0.45, 19.50),
                 front=R_FRACTURED_TIP, sides=R_FRACTURED_TIP, top=R_FRACTURED_TIP)
    # Back-Right Shard Blade (Tallest)
    register_box("PinnacleShard2", 0.85, 0.85, 3.40, (0.45, 0.45, 19.50),
                 front=R_FRACTURED_TIP, sides=R_FRACTURED_TIP, top=R_FRACTURED_TIP)
    # Front-Right Shard Blade
    register_box("PinnacleShard3", 0.80, 0.80, 2.40, (0.45, -0.45, 19.50),
                 front=R_FRACTURED_TIP, sides=R_FRACTURED_TIP, top=R_FRACTURED_TIP)
    # Back-Left Shard Blade
    register_box("PinnacleShard4", 0.80, 0.80, 2.70, (-0.45, 0.45, 19.50),
                 front=R_FRACTURED_TIP, sides=R_FRACTURED_TIP, top=R_FRACTURED_TIP)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_The_Shard")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_the_shard_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_the_shard.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_the_shard.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_the_shard_preview.png")
        shutil.copy2(OUT_DIR / "landmark_the_shard_atlas.png", TOOLS_OUT_DIR / "landmark_the_shard_atlas.png")
    except Exception as e:
        print(f"[landmark_the_shard] note: {e}")

    print("[landmark_the_shard] generation complete.")


main()
