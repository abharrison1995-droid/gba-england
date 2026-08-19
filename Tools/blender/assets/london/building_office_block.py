"""Modern London Commercial Office Building (10.0m x 8.0m 3-Storey Corporate Block).

Specs:
- 10.0m x 8.0m footprint, Height: 10.5m to rooftop HVAC screen.
- Modern London City / Canary Wharf commercial architecture:
  - Tinted blue/cyan reflective glass curtain wall with dark charcoal aluminium spandrel panels.
  - Ground floor glazed commercial reception lobby with brushed stainless steel entrance canopy.
  - Corporate brass nameplate: "ST. PAUL'S HOUSE - 120 CANNON STREET".
  - Rooftop HVAC mechanical plant room with louvred acoustic screens and satellite dish.
  - Stainless steel security pavement bollards.
- Outputs to Tools/blender/out/ and Tools/out/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_office_block.py
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
R_GLASS_CURTAIN = (0,   256, 256, 256)   # Reflective blue/cyan glass curtain wall with mullions
R_LOBBY_ENTRANCE= (256, 256, 128, 256)   # Glazed reception entrance with revolving door & lobby light
R_CORPORATE_SIGN= (0,   128, 256, 128)   # "ST. PAUL'S HOUSE - 120 CANNON STREET" brass sign
R_STEEL_SPANDREL= (256, 128, 128, 128)   # Charcoal metallic spandrel panels & concrete side walls
R_HVAC_LOUVRES  = (0,   0,   256, 128)   # Rooftop acoustic louvre screen & mechanical plant
R_STONE_PAVEMENT= (256, 0,   128, 128)   # Modern granite paving slabs & stainless steel bollards
R_SATELLITE_DISH= (384, 256, 128, 128)   # Rooftop commercial telecoms dish
R_ROOF_GRAVEL   = (384, 128, 128, 128)   # Flat gravel roof with drainage sumps
R_ALUM_CANOPY   = (384, 0,   128, 128)   # Brushed aluminium entrance canopy & soffit lights

# --- Palette Colors ---
GLASS_BLUE      = (0.16, 0.42, 0.62)
GLASS_CYAN      = (0.28, 0.65, 0.82)
GLASS_LOBBY     = (0.85, 0.88, 0.90)
SPANDREL_DARK   = (0.18, 0.20, 0.22)
MULLION_GREY    = (0.32, 0.35, 0.38)
BRASS_CORP      = (0.88, 0.74, 0.26)
GRANITE_PAVE    = (0.65, 0.68, 0.70)
STEEL_BRUSHED   = (0.75, 0.78, 0.80)


def paint_office_atlas():
    a = Atlas(S, seed=2301)

    # 1. Glass Curtain Wall Facade (R_GLASS_CURTAIN)
    x, y, w, h = R_GLASS_CURTAIN
    a.rect(x, y, w, h, GLASS_BLUE)
    # Sky reflection gradient
    a.shade(x, y, w, h, top=0.15, bottom=-0.10)
    # Charcoal spandrel floor bands
    a.rect(x, y + 70, w, 16, SPANDREL_DARK)
    a.rect(x, y + 150, w, 16, SPANDREL_DARK)
    a.rect(x, y + 230, w, 16, SPANDREL_DARK)
    # Vertical aluminium mullions
    for mx in range(x, x + w, 32):
        a.rect(mx, y, 4, h, MULLION_GREY)
        a.rect(mx + 4, y, 1, h, (0.5, 0.7, 0.9))  # glass highlight
    a.noise(x, y, w, h, 0.02)

    # 2. Glazed Reception Entrance (R_LOBBY_ENTRANCE)
    x, y, w, h = R_LOBBY_ENTRANCE
    a.rect(x, y, w, h, SPANDREL_DARK)
    dx, dy, dw, dh = x + 8, y + 8, w - 16, h - 16
    a.rect(dx, dy, dw, dh, GLASS_LOBBY)
    # Warm interior reception light
    a.disc(dx + dw // 2, dy + dh - 40, 36, (0.98, 0.92, 0.75))
    # Revolving door cylinder outline & stainless frame
    a.rect(dx + 12, dy + 6, dw - 24, dh - 30, (0.35, 0.40, 0.45))
    a.rect(dx + dw // 2 - 2, dy + 6, 4, dh - 30, STEEL_BRUSHED)
    a.rect(dx + 6, dy + 6, dw - 12, 16, STEEL_BRUSHED)
    a.noise(x, y, w, h, 0.015)

    # 3. Corporate Sign: "ST. PAUL'S HOUSE" (R_CORPORATE_SIGN)
    x, y, w, h = R_CORPORATE_SIGN
    a.rect(x, y, w, h, (0.12, 0.14, 0.16))
    # Brushed brass plaque
    px, py, pw, ph = x + 12, y + 16, w - 24, h - 32
    a.rect(px, py, pw, ph, BRASS_CORP)
    a.rect(px + 4, py + 4, pw - 8, ph - 8, (0.20, 0.16, 0.08))
    # Gold Lettering
    s1 = "ST. PAUL'S HOUSE"
    w1 = a.text_width(s1, scale=2)
    a.text(px + (pw - w1) // 2, py + ph - 14, s1, BRASS_CORP, scale=2)
    s2 = "120 CANNON STREET - EC4"
    w2 = a.text_width(s2, scale=1)
    a.text(px + (pw - w2) // 2, py + 22, s2, BRASS_CORP, scale=1)
    a.noise(x, y, w, h, 0.02)

    # 4. Metallic Charcoal Spandrel & Concrete (R_STEEL_SPANDREL)
    x, y, w, h = R_STEEL_SPANDREL
    a.rect(x, y, w, h, SPANDREL_DARK)
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.10, 0.12, 0.14))
    a.noise(x, y, w, h, 0.03)

    # 5. Rooftop HVAC Louvres (R_HVAC_LOUVRES)
    x, y, w, h = R_HVAC_LOUVRES
    a.rect(x, y, w, h, (0.35, 0.38, 0.40))
    for ly in range(y + 6, y + h, 8):
        a.rect(x + 4, ly, w - 8, 4, (0.18, 0.20, 0.22))
    a.noise(x, y, w, h, 0.025)

    # 6. Granite Paving (R_STONE_PAVEMENT)
    x, y, w, h = R_STONE_PAVEMENT
    a.rect(x, y, w, h, GRANITE_PAVE)
    for py in range(y, y + h, 32):
        a.rect(x, py, w, 2, (0.45, 0.48, 0.50))
    for px in range(x, x + w, 32):
        a.rect(px, y, 2, h, (0.45, 0.48, 0.50))
    a.noise(x, y, w, h, 0.03)

    # 7. Satellite Telecoms Dish (R_SATELLITE_DISH)
    x, y, w, h = R_SATELLITE_DISH
    a.rect(x, y, w, h, (0.35, 0.38, 0.40))
    a.disc(x + w // 2, y + h // 2, 36, (0.80, 0.82, 0.85))
    a.disc(x + w // 2, y + h // 2, 30, (0.65, 0.68, 0.70))
    a.rect(x + w // 2 - 2, y + h // 2 - 24, 4, 24, (0.2, 0.2, 0.2))
    a.noise(x, y, w, h, 0.02)

    # 8. Flat Roof Gravel (R_ROOF_GRAVEL)
    x, y, w, h = R_ROOF_GRAVEL
    a.rect(x, y, w, h, (0.40, 0.42, 0.44))
    a.noise(x, y, w, h, 0.04)

    # 9. Aluminium Entrance Canopy (R_ALUM_CANOPY)
    x, y, w, h = R_ALUM_CANOPY
    a.rect(x, y, w, h, STEEL_BRUSHED)
    # Recessed spotlight downlights
    for lx in [x + 24, x + 64, x + 104]:
        a.disc(lx, y + h // 2, 10, (0.95, 0.95, 0.85))
        a.disc(lx, y + h // 2, 6, (1.0, 1.0, 0.95))
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("building_office_block_atlas", OUT_DIR)


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
    kit.map_faces_to_region(obj, top or R_STEEL_SPANDREL, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_STEEL_SPANDREL, S, only=side("bottom"))


def main():
    kit.reset_scene()
    img = paint_office_atlas()
    mat = material_for(img, "mat_office_block")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # Modern London Commercial Office Building (10.0m x 8.0m Footprint)
    # - 3 Storeys Glass Curtain Wall (Height: 8.8m, Z = 0.15m to 8.95m)
    # - Ground Floor Glazed Reception Lobby & Projecting Stainless Steel Canopy
    # - Brass Corporate Sign: "ST. PAUL'S HOUSE"
    # - Rooftop HVAC Plant Room with Louvred Acoustic Screens & Telecoms Dish
    # =========================================================================

    # 1. Granite Pavement Plinth (10.0m x 8.5m, Z = 0.00 to 0.15m)
    register_box("PlazaPlinth", 10.0, 8.50, 0.15, (0.0, -0.25, 0.0),
                 front=R_STONE_PAVEMENT, sides=R_STONE_PAVEMENT, top=R_STONE_PAVEMENT)

    # 2. Main Glass Office Block (10.0m x 7.5m, Z: 0.15 to 8.80m, H: 8.65m)
    register_box("OfficeTower", 10.0, 7.50, 8.65, (0.0, 0.25, 0.15),
                 front=R_GLASS_CURTAIN, sides=R_STEEL_SPANDREL, back=R_STEEL_SPANDREL)

    # 3. Ground Floor Glazed Reception Entrance (Center: X = 0.0m, Z = 0.15 to 3.20m, H: 3.05m)
    register_box("LobbyDoors", 3.20, 0.20, 3.05, (0.0, -3.58, 0.15),
                 front=R_LOBBY_ENTRANCE, sides=R_STEEL_SPANDREL, top=R_ALUM_CANOPY)

    # 4. Projecting Brushed Aluminium Entrance Canopy (Z = 3.20m to 3.50m, Projects forward by 1.2m)
    register_box("EntranceCanopy", 4.40, 1.40, 0.30, (0.0, -4.15, 3.20),
                 front=R_ALUM_CANOPY, sides=R_ALUM_CANOPY, top=R_ALUM_CANOPY, bottom=R_ALUM_CANOPY)

    # 5. Brass Corporate Directory Plaque (X = -2.80m, Y = -3.55m, Z = 1.40m to 2.60m)
    register_box("CorpPlacard", 1.80, 0.15, 1.20, (-2.80, -3.55, 1.40),
                 front=R_CORPORATE_SIGN, sides=R_STEEL_SPANDREL, top=R_STEEL_SPANDREL)

    # 6. Rooftop Parapet Coping (Z = 8.80m to 9.20m, H: 0.40m)
    register_box("RoofParapet", 10.20, 7.70, 0.40, (0.0, 0.25, 8.80),
                 front=R_STEEL_SPANDREL, sides=R_STEEL_SPANDREL, top=R_ROOF_GRAVEL)

    # 7. Rooftop HVAC Mechanical Plant Enclosure (6.0m x 4.5m, Z = 9.20m to 10.60m, H: 1.40m)
    register_box("HVACEnclosure", 6.00, 4.50, 1.40, (0.0, 0.25, 9.20),
                 front=R_HVAC_LOUVRES, sides=R_HVAC_LOUVRES, top=R_ROOF_GRAVEL)

    # 8. Rooftop Satellite Telecoms Dish (X = 3.40m, Y = 0.50m, Z = 9.20m to 10.50m)
    register_box("TelecomsDish", 1.10, 0.40, 1.30, (3.40, 0.50, 9.20),
                 front=R_SATELLITE_DISH, sides=R_SATELLITE_DISH, top=R_STEEL_SPANDREL)

    # 9. Stainless Steel Pavement Security Bollards (Front row at Y = -4.30m)
    for bx in [-2.40, -0.80, 0.80, 2.40]:
        register_box(f"Bollard_{bx}", 0.20, 0.20, 0.80, (bx, -4.30, 0.15),
                     front=R_ALUM_CANOPY, sides=R_ALUM_CANOPY, top=R_ALUM_CANOPY)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Building_Office_Block")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "building_office_block_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "building_office_block.glb"
    kit.export_glb(glb_path, [shell])

    try:
        TOOLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, TOOLS_OUT_DIR / "building_office_block.glb")
        shutil.copy2(preview_path, TOOLS_OUT_DIR / "building_office_block_preview.png")
        shutil.copy2(OUT_DIR / "building_office_block_atlas.png", TOOLS_OUT_DIR / "building_office_block_atlas.png")
    except Exception as e:
        print(f"[building_office_block] note: {e}")

    print("[building_office_block] generation complete.")


main()
