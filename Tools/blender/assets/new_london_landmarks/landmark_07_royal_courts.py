"""Royal Courts of Justice (The Strand) - Building Only.

Specs:
- Clean building structure without pavement or surrounding ground slabs.
- Sits directly at Z = 0.0.
- Victorian High Gothic Great Hall, recessed carriage arch portal, stained glass rose window,
  eastern Clock Spire Tower, and flanking courtroom wings.
- Target: ~3,500 tris.
- Deploys to Assets/3DModels/New LonLandmark/landmark_royal_courts_of_justice.glb.
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
R_GREY_STONE      = (0,   256, 256, 256)   # Weathered grey Portland & Bath stone ashlar
R_SLATE_ROOF      = (256, 256, 256, 256)   # Steep dark slate roofs & lead valleys
R_GREAT_PORTAL    = (0,   128, 128, 128)   # Grand gothic archway & stained-glass rose window
R_COURT_WINDOWS   = (128, 128, 128, 128)   # Gothic lancet & arcade windows
R_CLOCK_TOWER     = (256, 128, 128, 128)   # East clock tower dial & belfry louvers


def paint_atlas():
    a = Atlas(S, seed=1882)

    # 1. Grey Gothic Stone (R_GREY_STONE)
    x, y, w, h = R_GREY_STONE
    a.rect(x, y, w, h, (0.78, 0.76, 0.72))
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, (0.68, 0.66, 0.62))
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.72, 0.70, 0.66))
    a.noise(x, y, w, h, 0.015)

    # 2. Slate Roof (R_SLATE_ROOF)
    x, y, w, h = R_SLATE_ROOF
    a.rect(x, y, w, h, (0.26, 0.28, 0.32))
    for ry in range(y, y + h, 8):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.012)

    # 3. Great Portal & Rose Window (R_GREAT_PORTAL)
    x, y, w, h = R_GREAT_PORTAL
    a.rect(x, y, w, h, (0.72, 0.70, 0.66))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy + 16, 32, (0.15, 0.18, 0.24))
    a.disc(cx, cy + 16, 26, (0.35, 0.45, 0.65))
    for i in range(8):
        ang = i * (math.pi / 4)
        rx = int(cx + 18 * math.cos(ang))
        ry = int(cy + 16 + 18 * math.sin(ang))
        a.disc(rx, ry, 5, (0.75, 0.25, 0.25))
    a.rect(x + 20, y + 4, w - 40, 40, (0.12, 0.12, 0.14))
    a.noise(x, y, w, h, 0.015)

    # 4. Court Windows (R_COURT_WINDOWS)
    x, y, w, h = R_COURT_WINDOWS
    a.rect(x, y, w, h, (0.75, 0.73, 0.70))
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 22):
            a.rect(wx, wy, 14, 20, (0.12, 0.16, 0.22))
            a.rect(wx + 6, wy, 2, 20, (0.65, 0.63, 0.60))
    a.noise(x, y, w, h, 0.01)

    # 5. Clock Tower Dial (R_CLOCK_TOWER)
    x, y, w, h = R_CLOCK_TOWER
    a.rect(x, y, w, h, (0.72, 0.70, 0.66))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 38, (0.85, 0.75, 0.25))
    a.disc(cx, cy, 32, (0.95, 0.94, 0.88))
    a.disc(cx, cy, 4, (0.1, 0.1, 0.1))
    a.rect(cx - 2, cy, 4, 20, (0.1, 0.1, 0.1))
    a.noise(x, y, w, h, 0.01)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_royal_courts", OUT_DIR)


def make_pyramid(name, base_w, base_d, height, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hw, hd = base_w / 2, base_d / 2
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, 0))
    v3 = bm.verts.new((-hw,  hd, 0))
    v_top = bm.verts.new((0, 0, height))

    bm.faces.new((v0, v1, v_top))
    bm.faces.new((v1, v2, v_top))
    bm.faces.new((v2, v3, v_top))
    bm.faces.new((v3, v0, v_top))
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img, "mat_royal_courts")

    parts = []

    def reg_box(name, w, d, h, at, region=R_GREY_STONE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_ROOF):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # ROYAL COURTS OF JUSTICE (BUILDING ONLY - NO PAVEMENT)
    # Sits directly on Z = 0.0
    # =========================================================================

    # 1. Central Great Hall Body & Grand Portal (sits at Z = 0.0)
    reg_box("GreatHallMain", 8.0, 8.0, 7.5, (0, 0, 0.0), region=R_COURT_WINDOWS)
    reg_box("GreatHallPortal", 4.5, 1.2, 5.0, (0, -4.2, 0.0), region=R_GREAT_PORTAL)
    reg_pyr("GreatHallRoof", 8.2, 8.2, 4.2, (0, 0, 7.5), region=R_SLATE_ROOF)

    # 4 Gabled Dormers on Great Hall Roof
    for di, dx in enumerate([-2.8, -1.0, 1.0, 2.8]):
        reg_pyr(f"HallDormer_{di}", 1.4, 1.4, 1.8, (dx, -3.8, 7.5), region=R_SLATE_ROOF)

    # 2. East Clock Spire Tower (X: +6.5m, Y: -2.5m, sits at Z = 0.0)
    reg_box("EastClockTowerShaft", 3.2, 3.2, 10.5, (6.5, -2.5, 0.0), region=R_GREY_STONE)
    reg_box("EastClockDialBlock", 3.4, 3.4, 2.8, (6.5, -2.5, 10.5), region=R_CLOCK_TOWER)
    reg_pyr("EastClockMainSpire", 3.2, 3.2, 5.8, (6.5, -2.5, 13.3), region=R_SLATE_ROOF)
    reg_pyr("EastClockLantern", 1.0, 1.0, 2.2, (6.5, -2.5, 19.1), region=R_CLOCK_TOWER)

    # 3. West Flank Courtroom Wing (sits at Z = 0.0)
    reg_box("WestWingBody", 5.5, 9.0, 6.5, (-6.5, 0, 0.0), region=R_COURT_WINDOWS)
    reg_pyr("WestWingRoof", 5.7, 9.2, 3.4, (-6.5, 0, 6.5), region=R_SLATE_ROOF)

    # Corner Turrets on West Wing
    reg_box("WestTurretShaft_1", 1.2, 1.2, 8.5, (-9.0, -4.2, 0.0), region=R_GREY_STONE)
    reg_pyr("WestTurretSpire_1", 1.3, 1.3, 2.6, (-9.0, -4.2, 8.5), region=R_SLATE_ROOF)
    reg_box("WestTurretShaft_2", 1.2, 1.2, 8.5, (-9.0,  4.2, 0.0), region=R_GREY_STONE)
    reg_pyr("WestTurretSpire_2", 1.3, 1.3, 2.6, (-9.0,  4.2, 8.5), region=R_SLATE_ROOF)

    # 4. Facade Buttresses & Gothic Pinnacles
    for bi in range(6):
        bx = -7.0 + bi * 2.8
        reg_box(f"CourtsButtress_{bi}", 0.4, 0.6, 7.2, (bx, -4.3, 0.0), region=R_GREY_STONE)
        reg_pyr(f"CourtsPinnacle_{bi}", 0.5, 0.5, 1.4, (bx, -4.3, 7.2), region=R_GREY_STONE)

    # 5. Rear Chambers Wing
    reg_box("RearChambersBody", 14.0, 4.0, 5.5, (0, 5.5, 0.0), region=R_COURT_WINDOWS)
    reg_pyr("RearChambersRoof", 14.2, 4.2, 2.4, (0, 5.5, 5.5), region=R_SLATE_ROOF)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Royal_Courts_Of_Justice")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_royal_courts_of_justice_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_royal_courts_of_justice.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy to Assets/3DModels/New LonLandmark
    try:
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_royal_courts_of_justice.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_royal_courts_of_justice_preview.png")
        shutil.copy2(OUT_DIR / "atlas_royal_courts.png", TEXTURES_DIR / "atlas_royal_courts.png")
        print(f"[RoyalCourts] clean building deployed.")
    except Exception as e:
        print(f"[RoyalCourts] deploy notice: {e}")


if __name__ == "__main__":
    main()
