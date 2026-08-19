"""Battersea Power Station - Building Only.

Specs:
- Clean building structure without wharf plinth, river slabs, or surrounding pavement.
- Sits directly at Z = 0.0.
- 4 iconic fluted white wash-tower chimneys on corner podiums, stepped brick boiler hall,
  cathedral turbine hall windows, and fluted vertical brick pilasters.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_battersea_power_station.glb.
"""

import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "new_london_landmarks"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "New LonLandmark"
TEXTURES_DIR = DEPLOY_DIR / "textures"

# Atlas regions
R_BATTERSEA_BRICK = (0,   256, 256, 256)   # London stock weathered red/brown brickwork
R_CHIMNEY_WHITE   = (256, 256, 256, 256)   # Fluted white concrete chimneys
R_ART_DECO_GLASS  = (0,   128, 128, 128)   # Tall vertical multi-pane industrial cathedral glass
R_CONCRETE_TRIM   = (128, 128, 128, 128)   # Stepped Art Deco cornices & parapet copings


def paint_atlas():
    a = Atlas(S, seed=1933)

    # 1. Battersea Brickwork (R_BATTERSEA_BRICK)
    x, y, w, h = R_BATTERSEA_BRICK
    a.rect(x, y, w, h, (0.64, 0.32, 0.22))
    for ry in range(y, y + h, 10):
        a.rect(x, ry, w, 2, (0.50, 0.24, 0.16))
        for rx in range(x + (ry % 20), x + w, 20):
            a.rect(rx, ry, 2, 10, (0.54, 0.26, 0.18))
    for fx in range(x + 20, x + w, 40):
        a.rect(fx, y, 4, h, (0.42, 0.20, 0.14))
    a.noise(x, y, w, h, 0.02)

    # 2. Fluted White Chimney (R_CHIMNEY_WHITE)
    x, y, w, h = R_CHIMNEY_WHITE
    a.rect(x, y, w, h, (0.90, 0.90, 0.88))
    for fx in range(x, x + w, 16):
        a.rect(fx, y, 3, h, (0.75, 0.75, 0.73))
    a.shade(x, y + h - 60, w, 60, top=-0.25, bottom=0.0)
    a.noise(x, y, w, h, 0.015)

    # 3. Art Deco Glass (R_ART_DECO_GLASS)
    x, y, w, h = R_ART_DECO_GLASS
    a.rect(x, y, w, h, (0.12, 0.16, 0.20))
    for wy in range(y + 6, y + h, 16):
        a.rect(x, wy, w, 2, (0.28, 0.32, 0.36))
    for wx in range(x + 10, x + w, 20):
        a.rect(wx, y, 2, h, (0.35, 0.40, 0.45))
    a.noise(x, y, w, h, 0.01)

    # 4. Concrete Trim (R_CONCRETE_TRIM)
    x, y, w, h = R_CONCRETE_TRIM
    a.rect(x, y, w, h, (0.80, 0.78, 0.74))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.65, 0.63, 0.60))
    a.noise(x, y, w, h, 0.015)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_battersea_power_station", OUT_DIR)


def make_fluted_chimney(name, base_r=1.2, top_r=0.8, height=12.0, segs=20, at=(0, 0, 0)):
    """Fluted tapering white wash-tower chimney."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = 6
    v_rows = []
    for ri in range(rings):
        frac = ri / (rings - 1)
        z = height * frac
        r_curr = base_r + (top_r - base_r) * frac
        if frac > 0.90:
            r_curr += 0.08
        row = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            flute = 0.04 * math.sin(ang * segs / 2)
            r_eff = r_curr + flute
            v = bm.verts.new((r_eff * math.cos(ang), r_eff * math.sin(ang), z))
            row.append(v)
        v_rows.append(row)

    for ri in range(rings - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((v_rows[ri][i], v_rows[ri][ni], v_rows[ri + 1][ni], v_rows[ri + 1][i]))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_battersea")

    parts = []

    def reg_box(name, w, d, h, at, region=R_BATTERSEA_BRICK):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # BATTERSEA POWER STATION (BUILDING ONLY - NO WHARF/RIVERBED)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Main Central Boiler House (sits at Z = 0.0)
    reg_box("MainBoilerHall", 12.0, 14.0, 8.0, (0, 0, 0.0), region=R_BATTERSEA_BRICK)
    reg_box("BoilerHallAttic", 11.4, 13.4, 1.2, (0, 0, 8.0), region=R_CONCRETE_TRIM)

    # Fluted Vertical Brick Pilasters on Boiler Hall Front & Back
    for side_y in [-7.1, 7.1]:
        for pi in range(8):
            px = -4.2 + pi * 1.2
            reg_box(f"BoilerPilaster_{side_y}_{pi}", 0.4, 0.3, 8.5, (px, side_y, 0.0), region=R_BATTERSEA_BRICK)

    # 2. Turbine Hall Flanks with Cathedral Windows
    for side_x in [-6.1, 6.1]:
        reg_box(f"TurbineHallBody_{side_x}", 2.2, 14.0, 6.5, (side_x, 0, 0.0), region=R_BATTERSEA_BRICK)
        for wi in range(5):
            wy = -4.5 + wi * 2.25
            reg_box(f"CathedralWin_{side_x}_{wi}", 0.3, 1.4, 4.8, (side_x + (1.0 if side_x > 0 else -1.0), wy, 1.0), region=R_ART_DECO_GLASS)

    # 3. Four Stepped Art Deco Wash-Tower Corner Podiums (sits at Z = 0.0)
    corner_coords = [
        ("WashPodium_NW", -5.5, -6.5),
        ("WashPodium_NE",  5.5, -6.5),
        ("WashPodium_SW", -5.5,  6.5),
        ("WashPodium_SE",  5.5,  6.5),
    ]

    for p_name, px, py in corner_coords:
        reg_box(f"{p_name}_Lower", 3.2, 3.2, 9.0, (px, py, 0.0), region=R_BATTERSEA_BRICK)
        reg_box(f"{p_name}_Collar1", 3.0, 3.0, 0.6, (px, py, 9.0), region=R_CONCRETE_TRIM)
        reg_box(f"{p_name}_Collar2", 2.6, 2.6, 0.6, (px, py, 9.6), region=R_CONCRETE_TRIM)
        reg_box(f"{p_name}_Octagon", 2.2, 2.2, 0.8, (px, py, 10.2), region=R_CONCRETE_TRIM)

        # Fluted White Wash-Tower Chimney
        chimney = make_fluted_chimney(f"Chimney_{p_name}", base_r=1.05, top_r=0.72, height=11.0, segs=20, at=(px, py, 11.0))
        chimney.data.materials.append(mat)
        kit.map_faces_to_region(chimney, R_CHIMNEY_WHITE, S)
        parts.append(chimney)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Battersea_Power_Station")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_battersea_power_station_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_battersea_power_station.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_battersea_power_station.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_battersea_power_station_preview.png")
        shutil.copy2(OUT_DIR / "atlas_battersea_power_station.png", TEXTURES_DIR / "atlas_battersea_power_station.png")
        print(f"[Battersea] clean building deployed.")
    except Exception as e:
        print(f"[Battersea] deploy notice: {e}")


if __name__ == "__main__":
    main()
