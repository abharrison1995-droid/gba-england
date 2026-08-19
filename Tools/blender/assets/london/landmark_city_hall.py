"""London City Hall (Modernist Helical Glass Civic Landmark).

Specs:
- 9.0m x 9.0m footprint, Height: 10.5m to curved observation roof.
- Modernist London civic architecture:
  - Stepped bulbous / leaning glass sphere geometry.
  - Alternating bands of reflective cyan/blue glass and silver metallic shading louvres.
  - Ground-floor glazed public civic entrance with reception lighting.
  - Public realm plaza plinth with granite steps.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/landmark_city_hall.py
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
R_CITY_GLASS    = (0,   256, 256, 256)   # Reflective cyan/blue curved curtain wall with mullions
R_LOUVRE_BAND   = (256, 256, 256, 256)   # Silver metallic solar shading louvres & floor plates
R_CIVIC_LOBBY   = (0,   128, 256, 128)   # Ground floor civic entrance & reception atrium
R_TOP_DOME      = (256, 128, 128, 128)   # Curved roof skylight & solar panels
R_PLAZA_PAVE    = (384, 128, 128, 128)   # Granite civic plaza paving
R_CITY_SIGN     = (0,   0,   256, 128)   # "LONDON CITY HALL - GREATER LONDON AUTHORITY"
R_STEEL_PANELS  = (256, 0,   128, 128)   # Brushed silver cladding panels
R_CANOPY_GLASS  = (384, 0,   128, 128)   # Glass entrance canopy & downlights

# --- Palette Colors ---
GLASS_CYAN      = (0.24, 0.58, 0.76)
GLASS_HIGHLIGHT = (0.75, 0.92, 0.98)
STEEL_SILVER    = (0.78, 0.80, 0.82)
LOUVRE_DARK     = (0.35, 0.38, 0.40)
SPANDREL_DARK   = (0.16, 0.18, 0.20)
GRANITE_PAVE    = (0.64, 0.66, 0.68)
GOLD_CREST      = (0.90, 0.75, 0.25)


def paint_city_hall_atlas():
    a = Atlas(S, seed=2701)

    # 1. Reflective Curved Glass (R_CITY_GLASS)
    x, y, w, h = R_CITY_GLASS
    a.rect(x, y, w, h, GLASS_CYAN)
    a.shade(x, y, w, h, top=0.18, bottom=-0.12)
    # Curved mullion lines
    for fx in range(x, x + w, 20):
        a.rect(fx, y, 2, h, (0.4, 0.6, 0.8))
        a.rect(fx + 2, y, 1, h, GLASS_HIGHLIGHT)
    for fy in range(y, y + h, 28):
        a.rect(x, fy, w, 2, SPANDREL_DARK)
    a.noise(x, y, w, h, 0.02)

    # 2. Silver Solar Louvres (R_LOUVRE_BAND)
    x, y, w, h = R_LOUVRE_BAND
    a.rect(x, y, w, h, STEEL_SILVER)
    for ly in range(y, y + h, 10):
        a.rect(x, ly, w, 4, LOUVRE_DARK)
        a.rect(x, ly + 4, w, 2, (0.92, 0.94, 0.96))
    a.noise(x, y, w, h, 0.025)

    # 3. Ground Floor Civic Lobby (R_CIVIC_LOBBY)
    x, y, w, h = R_CIVIC_LOBBY
    a.rect(x, y, w, h, SPANDREL_DARK)
    gx, gy, gw, gh = x + 10, y + 8, w - 20, h - 16
    a.rect(gx, gy, gw, gh, (0.85, 0.90, 0.94))
    # Revolving glass doors & atrium illumination
    for rx in [gx + 24, gx + gw // 2 - 16, gx + gw - 56]:
        a.rect(rx, gy + 4, 32, gh - 24, (0.35, 0.40, 0.45))
        a.disc(rx + 16, gy + gh - 16, 12, (0.98, 0.95, 0.80))
    a.noise(x, y, w, h, 0.015)

    # 4. Top Roof Dome (R_TOP_DOME)
    x, y, w, h = R_TOP_DOME
    a.rect(x, y, w, h, STEEL_SILVER)
    a.disc(x + w // 2, y + h // 2, 48, GLASS_CYAN)
    a.disc(x + w // 2, y + h // 2, 36, (0.2, 0.4, 0.6))
    a.disc(x + w // 2, y + h // 2, 14, GLASS_HIGHLIGHT)
    a.noise(x, y, w, h, 0.02)

    # 5. Granite Plaza (R_PLAZA_PAVE)
    x, y, w, h = R_PLAZA_PAVE
    a.rect(x, y, w, h, GRANITE_PAVE)
    for py in range(y, y + h, 24):
        a.rect(x, py, w, 2, (0.48, 0.50, 0.52))
    a.noise(x, y, w, h, 0.03)

    # 6. City Hall Sign (R_CITY_SIGN)
    x, y, w, h = R_CITY_SIGN
    a.rect(x, y, w, h, (0.12, 0.14, 0.16))
    a.rect(x + 4, y + 4, w - 8, h - 8, (0.20, 0.24, 0.28))
    s1 = "LONDON CITY HALL"
    w1 = a.text_width(s1, scale=2)
    a.text(x + (w - w1) // 2, y + h - 20, s1, STEEL_SILVER, scale=2)
    s2 = "GREATER LONDON AUTHORITY"
    w2 = a.text_width(s2, scale=1)
    a.text(x + (w - w2) // 2, y + 26, s2, GOLD_CREST, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 7. Steel Cladding Panels (R_STEEL_PANELS)
    x, y, w, h = R_STEEL_PANELS
    a.rect(x, y, w, h, STEEL_SILVER)
    for py in range(y, y + h, 20):
        a.rect(x, py, w, 2, LOUVRE_DARK)
    a.noise(x, y, w, h, 0.025)

    # 8. Glass Canopy (R_CANOPY_GLASS)
    x, y, w, h = R_CANOPY_GLASS
    a.rect(x, y, w, h, (0.75, 0.85, 0.90))
    for lx in [x + 20, x + 64, x + 108]:
        a.disc(lx, y + h // 2, 8, (0.95, 0.95, 0.85))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("landmark_city_hall_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STEEL_PANELS, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STEEL_PANELS, S, only=side("bottom"))


def make_stepped_cylinder(name, r, h, segs=16, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    # Bottom circle
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    # Top circle
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    # Side quads
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    # Bottom cap & top cap
    faces.append(list(range(segs - 1, -1, -1)))
    faces.append(list(range(segs, segs * 2)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_city_hall_atlas()
    mat = material_for(img, "mat_city_hall")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # London City Hall (9.0m x 9.0m Footprint, Height: 10.5m)
    # - Stepped bulbous / leaning glass & louvre tiers
    # - Ground Floor Civic Lobby & Plaza Plinth
    # - Top Observation Dome Skylight
    # =========================================================================

    # 1. Granite Public Plaza Plinth (9.4m x 9.4m, Z = 0.00 to 0.20m)
    register_box("CityHallPlaza", 9.40, 9.40, 0.20, (0.0, 0.0, 0.0),
                 front=R_PLAZA_PAVE, sides=R_PLAZA_PAVE, top=R_PLAZA_PAVE)

    # 2. Ground Floor Civic Lobby (8.4m x 8.4m, Z: 0.20m to 2.40m, H: 2.20m)
    register_box("CivicLobby", 8.40, 8.40, 2.20, (0.0, -0.20, 0.20),
                 front=R_CIVIC_LOBBY, sides=R_CITY_GLASS, back=R_CITY_GLASS)

    # 3. Projecting Glass Entrance Canopy (Z = 2.30m to 2.50m)
    register_box("LobbyCanopy", 4.20, 1.20, 0.20, (0.0, -4.80, 2.30),
                 front=R_CANOPY_GLASS, sides=R_CANOPY_GLASS, top=R_CANOPY_GLASS, bottom=R_CANOPY_GLASS)

    # 4. Stepped Leaning Helical Tiers (Z: 2.40m to 9.60m)
    # Tier 1 (Radius: 4.4m, H: 1.8m, Z = 2.40m)
    t1 = make_stepped_cylinder("Tier1", 4.40, 1.80, segs=16, at=(0.0, -0.10, 2.40))
    t1.data.materials.append(mat)
    kit.map_faces_to_region(t1, R_CITY_GLASS, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t1, R_LOUVRE_BAND, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t1)

    # Tier 2 (Radius: 4.1m, H: 1.8m, Z = 4.20m, Offset forward by Y = -0.2m)
    t2 = make_stepped_cylinder("Tier2", 4.10, 1.80, segs=16, at=(0.0, -0.30, 4.20))
    t2.data.materials.append(mat)
    kit.map_faces_to_region(t2, R_LOUVRE_BAND, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t2, R_CITY_GLASS, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t2)

    # Tier 3 (Radius: 3.6m, H: 1.8m, Z = 6.00m, Offset forward by Y = -0.4m)
    t3 = make_stepped_cylinder("Tier3", 3.60, 1.80, segs=16, at=(0.0, -0.50, 6.00))
    t3.data.materials.append(mat)
    kit.map_faces_to_region(t3, R_CITY_GLASS, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t3, R_LOUVRE_BAND, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t3)

    # Tier 4 (Radius: 2.9m, H: 1.8m, Z = 7.80m, Offset forward by Y = -0.6m)
    t4 = make_stepped_cylinder("Tier4", 2.90, 1.80, segs=16, at=(0.0, -0.70, 7.80))
    t4.data.materials.append(mat)
    kit.map_faces_to_region(t4, R_LOUVRE_BAND, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(t4, R_CITY_GLASS, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(t4)

    # 5. Top Observation Dome (Radius: 2.1m, H: 1.0m, Z = 9.60m, Offset by Y = -0.8m)
    top_dome = make_stepped_cylinder("TopDome", 2.10, 1.00, segs=16, at=(0.0, -0.80, 9.60))
    top_dome.data.materials.append(mat)
    kit.map_faces_to_region(top_dome, R_TOP_DOME, S, only=lambda f: abs(f.normal.z) < 0.5)
    kit.map_faces_to_region(top_dome, R_TOP_DOME, S, only=lambda f: abs(f.normal.z) >= 0.5)
    parts.append(top_dome)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Landmark_City_Hall")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_city_hall_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_city_hall.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "landmark_city_hall.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "landmark_city_hall_preview.png")
        shutil.copy2(OUT_DIR / "landmark_city_hall_atlas.png", TOOLS_OUT_DIR / "landmark_city_hall_atlas.png")
    except Exception as e:
        print(f"[landmark_city_hall] note: {e}")

    print("[landmark_city_hall] generation complete.")


main()
