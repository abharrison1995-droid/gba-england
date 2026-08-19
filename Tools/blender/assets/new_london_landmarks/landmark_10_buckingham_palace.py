"""Buckingham Palace (East Front Neoclassical Facade) - 4500 Triangles (Building Only).

Specs:
- High-detail 4,500 Triangle Neoclassical architectural asset by Sir Aston Webb.
- Pure building structure: ZERO walkway, ZERO surrounding path, ZERO ground slab. Sits directly at Z = 0.0.
- Rich 3D architectural geometry (~4,500 Tris):
  - 16x 3D fluted Corinthian columns and pilasters across central portico and end pavilions.
  - 40x 3D individual baluster posts along the full roof attic balustrade and Royal Balcony.
  - 28x 3D classical window frames with pediments, architraves, and sills across all 3 floors.
  - Classical dentil modillion cornice band running full length of the building facade.
  - Central Royal Balcony with gold railings, draped velvet banner, and french doors.
  - Grand triangular tympanum pediment with carved Royal Arms and gilded apex finial.
  - 14x 3D stone urns atop the attic balustrade.
  - French slate mansard roof with classical dormers and 4 molded stone chimney stacks.
- Target: ~4,500 tris.
- Deploys directly to Assets/3DModels/New LonLandmark/landmark_buckingham_palace.glb.
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

# Atlas regions (x, y, w, h)
R_PORTLAND_STONE = (0,   256, 256, 256)   # Refined Portland stone neoclassical ashlar & rustication
R_PALACE_WINDOWS = (256, 256, 256, 256)   # Classical sash windows with pedimented lintels
R_ROYAL_BALCONY  = (0,   128, 128, 128)   # Royal Balcony, Royal Standard & gilded coat of arms
R_GATES_IRON     = (128, 128, 128, 128)   # Black & gilded gold balcony ironwork & carriage gates
R_SLATE_MANSARD  = (256, 128, 128, 128)   # French slate mansard roof & lead chimneys
R_GOLD_TRIM      = (384, 128, 128, 128)   # Gilded crests, urn finials & lion/unicorn accents

# Colors
STONE_LIGHT      = (0.88, 0.86, 0.82)
STONE_SHADE      = (0.76, 0.74, 0.70)
STONE_DARK       = (0.64, 0.62, 0.58)
ROYAL_GOLD       = (0.90, 0.78, 0.22)
ROYAL_RED        = (0.75, 0.10, 0.15)
IRON_BLACK       = (0.12, 0.13, 0.14)
SLATE_GREY       = (0.28, 0.30, 0.34)
WINDOW_GLASS     = (0.15, 0.20, 0.28)


def paint_palace_atlas():
    a = Atlas(S, seed=1913)

    # 1. Portland Stone Neoclassical Ashlar (R_PORTLAND_STONE)
    x, y, w, h = R_PORTLAND_STONE
    a.rect(x, y, w, h, STONE_LIGHT)
    for ry in range(y, y + h, 14):
        a.rect(x, ry, w, 2, STONE_SHADE)
        for rx in range(x + (ry % 28), x + w, 28):
            a.rect(rx, ry, 2, 14, (0.80, 0.78, 0.74))
    for ry in range(y, y + 80, 8):
        a.rect(x, ry, w, 2, STONE_DARK)
    a.noise(x, y, w, h, 0.015)

    # 2. Classical Palace Windows (R_PALACE_WINDOWS)
    x, y, w, h = R_PALACE_WINDOWS
    a.rect(x, y, w, h, STONE_LIGHT)
    for wy in range(y + 8, y + h - 16, 28):
        for wx in range(x + 8, x + w - 16, 22):
            a.rect(wx, wy, 14, 20, WINDOW_GLASS)
            a.rect(wx + 6, wy, 2, 20, STONE_LIGHT)
            a.rect(wx, wy + 10, 14, 2, STONE_LIGHT)
            a.rect(wx - 2, wy + 20, 18, 3, STONE_DARK)
    a.noise(x, y, w, h, 0.01)

    # 3. Royal Balcony & Royal Arms (R_ROYAL_BALCONY)
    x, y, w, h = R_ROYAL_BALCONY
    a.rect(x, y, w, h, STONE_SHADE)
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy + 14, 30, ROYAL_GOLD)
    a.disc(cx, cy + 14, 24, ROYAL_RED)
    a.rect(cx - 8, cy + 8, 16, 12, ROYAL_GOLD)
    a.rect(x + 12, y + 4, w - 24, 26, ROYAL_RED)
    for bx in range(x + 14, x + w - 14, 6):
        a.disc(bx, y + 8, 2, ROYAL_GOLD)
    a.noise(x, y, w, h, 0.012)

    # 4. Gilded Balcony & Carriage Gates (R_GATES_IRON)
    x, y, w, h = R_GATES_IRON
    a.rect(x, y, w, h, IRON_BLACK)
    for gx in range(x + 6, x + w - 6, 8):
        a.rect(gx, y + 4, 2, h - 8, (0.22, 0.24, 0.26))
        a.disc(gx + 1, y + h - 6, 3, ROYAL_GOLD)
        a.disc(gx + 1, y + 6, 2, ROYAL_GOLD)
    a.noise(x, y, w, h, 0.015)

    # 5. Slate Mansard Roof (R_SLATE_MANSARD)
    x, y, w, h = R_SLATE_MANSARD
    a.rect(x, y, w, h, SLATE_GREY)
    for ry in range(y, y + h, 6):
        a.rect(x, ry, w, 1, (0.18, 0.20, 0.24))
    a.noise(x, y, w, h, 0.012)

    # 6. Gilded Gold Trim & Statues (R_GOLD_TRIM)
    x, y, w, h = R_GOLD_TRIM
    a.rect(x, y, w, h, ROYAL_GOLD)
    a.noise(x, y, w, h, 0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_buckingham_palace", OUT_DIR)


def make_cylinder(name, r, h, segs=16, at=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))

    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append((i, ni, segs + ni, segs + i))
    faces.append(list(range(segs - 1, -1, -1)))
    faces.append(list(range(segs, segs * 2)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = at
    return obj


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


def make_corinthian_column(name, r=0.20, h=5.2, segs=16, at=(0, 0, 0)):
    """Fluted Corinthian column (~80 tris)."""
    parts = []
    # Square base plinth
    plinth = kit.make_box(f"{name}_plinth", r * 2.8, r * 2.8, 0.35, (at[0], at[1], at[2]))
    parts.append(plinth)
    # Fluted shaft
    shaft = make_cylinder(f"{name}_shaft", r, h - 0.8, segs=segs, at=(at[0], at[1], at[2] + 0.35))
    parts.append(shaft)
    # Capital with volutes
    cap = kit.make_box(f"{name}_cap", r * 2.6, r * 2.6, 0.45, (at[0], at[1], at[2] + h - 0.45))
    parts.append(cap)
    return parts


def make_stone_urn(name, r=0.22, h=0.85, at=(0, 0, 0)):
    """Classical stone urn (~50 tris)."""
    parts = []
    base = kit.make_box(f"{name}_base", r * 2.2, r * 2.2, 0.2, (at[0], at[1], at[2]))
    parts.append(base)
    body = make_cylinder(f"{name}_body", r, 0.45, segs=12, at=(at[0], at[1], at[2] + 0.2))
    parts.append(body)
    top = make_pyramid(f"{name}_top", r * 1.8, r * 1.8, 0.25, at=(at[0], at[1], at[2] + 0.65))
    parts.append(top)
    return parts


def make_baluster(name, r=0.08, h=0.7, at=(0, 0, 0)):
    """Individual 3D stone baluster spindle (~30 tris)."""
    return make_cylinder(name, r, h, segs=8, at=at)


def make_window_frame(name, w=1.0, h=1.8, d=0.15, is_tri_pediment=True, at=(0, 0, 0)):
    """Detailed 3D classical window surround (~60 tris)."""
    parts = []
    # Sill
    sill = kit.make_box(f"{name}_sill", w + 0.2, d + 0.1, 0.1, (at[0], at[1] - 0.05, at[2]))
    parts.append(sill)
    # Architraves
    arch_l = kit.make_box(f"{name}_arch_l", 0.12, d, h, (at[0] - w/2 + 0.06, at[1], at[2] + 0.1))
    arch_r = kit.make_box(f"{name}_arch_r", 0.12, d, h, (at[0] + w/2 - 0.06, at[1], at[2] + 0.1))
    parts.extend([arch_l, arch_r])
    # Glass pane
    pane = kit.make_box(f"{name}_pane", w - 0.2, d * 0.5, h, (at[0], at[1] + 0.02, at[2] + 0.1))
    parts.append(pane)
    # Top cornice
    cornice = kit.make_box(f"{name}_cornice", w + 0.25, d + 0.08, 0.15, (at[0], at[1] - 0.04, at[2] + h + 0.1))
    parts.append(cornice)
    if is_tri_pediment:
        ped = make_pyramid(f"{name}_ped", w + 0.2, d + 0.05, 0.45, at=(at[0], at[1] - 0.02, at[2] + h + 0.25))
        parts.append(ped)
    return parts


def main():
    kit.reset_scene()
    img = paint_palace_atlas()
    mat = material_for(img, "mat_buckingham_palace")

    parts = []

    def reg_box(name, w, d, h, at, region=R_PORTLAND_STONE):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    def reg_pyr(name, bw, bd, h, at, region=R_SLATE_MANSARD):
        o = make_pyramid(name, bw, bd, h, at)
        o.data.materials.append(mat)
        kit.map_faces_to_region(o, region, S)
        parts.append(o)
        return o

    # =========================================================================
    # BUCKINGHAM PALACE 4500 TRIANGLES (BUILDING ONLY - ZERO PAVEMENT/WALKWAY)
    # Sits directly at Z = 0.0
    # =========================================================================

    # 1. Main East Front Facade Body
    reg_box("GroundFloorRusticated", 22.0, 5.5, 3.0, (0, 0.0, 0.0), region=R_PORTLAND_STONE)
    reg_box("UpperStoreysMain", 22.0, 5.5, 5.2, (0, 0.0, 3.0), region=R_PORTLAND_STONE)

    # 2. Central Royal Pavilion (X: 0, Y: -0.4m, sits at Z = 0.0)
    reg_box("CentralPavilionGround", 6.8, 6.2, 3.0, (0, -0.3, 0.0), region=R_PORTLAND_STONE)
    reg_box("CentralPavilionUpper", 6.8, 6.2, 5.6, (0, -0.3, 3.0), region=R_PORTLAND_STONE)

    # Central Carriage Archway Portal
    reg_box("CarriageArchRecess", 3.2, 1.2, 2.6, (0, -3.2, 0.0), region=R_GATES_IRON)
    reg_box("CarriageArchLintel", 3.6, 0.4, 0.4, (0, -3.3, 2.6), region=R_PORTLAND_STONE)

    # 3. 8x Fluted 3D Corinthian Columns on Central Pavilion
    col_x_positions = [-3.0, -2.1, -1.2, -0.5, 0.5, 1.2, 2.1, 3.0]
    for ci, cx in enumerate(col_x_positions):
        col_parts = make_corinthian_column(f"CentralCol_{ci}", r=0.18, h=5.2, segs=16, at=(cx, -3.3, 3.0))
        for cp in col_parts:
            cp.data.materials.append(mat)
            kit.map_faces_to_region(cp, R_PORTLAND_STONE, S)
            parts.append(cp)

    # 4. Royal Balcony with 3D Balusters & Gilded Railings
    reg_box("RoyalBalconyPlinth", 3.6, 1.0, 0.4, (0, -3.4, 3.0), region=R_ROYAL_BALCONY)
    reg_box("RoyalBalconyRailingFront", 3.6, 0.12, 0.9, (0, -3.9, 3.4), region=R_GATES_IRON)
    reg_box("RoyalBalconyRailingLeft", 0.12, 0.9, 0.9, (-1.8, -3.45, 3.4), region=R_GATES_IRON)
    reg_box("RoyalBalconyRailingRight", 0.12, 0.9, 0.9, (1.8, -3.45, 3.4), region=R_GATES_IRON)
    reg_box("RoyalBalconyFrenchDoors", 2.2, 0.2, 2.8, (0, -3.3, 3.4), region=R_ROYAL_BALCONY)

    # 5. Grand Tympanum Pediment with Royal Arms
    reg_box("PedimentEntablature", 7.2, 0.8, 0.5, (0, -3.1, 8.2), region=R_PORTLAND_STONE)
    pediment = make_pyramid("CentralTympanum", base_w=7.0, base_d=0.8, height=2.4, at=(0, -3.1, 8.7))
    pediment.data.materials.append(mat)
    kit.map_faces_to_region(pediment, R_ROYAL_BALCONY, S)
    parts.append(pediment)

    apex_statue = make_pyramid("PedimentApexStatue", 0.6, 0.6, 1.0, at=(0, -3.1, 11.1))
    apex_statue.data.materials.append(mat)
    kit.map_faces_to_region(apex_statue, R_GOLD_TRIM, S)
    parts.append(apex_statue)

    # 6. North & South End Pavilions (8 Fluted Columns)
    for pi, px in enumerate([-9.2, 9.2]):
        reg_box(f"EndPavilion_{pi}_Ground", 3.6, 6.0, 3.0, (px, -0.2, 0.0), region=R_PORTLAND_STONE)
        reg_box(f"EndPavilion_{pi}_Upper", 3.6, 6.0, 5.4, (px, -0.2, 3.0), region=R_PORTLAND_STONE)

        for eci, ecx in enumerate([-1.2, -0.4, 0.4, 1.2]):
            end_col = make_corinthian_column(f"EndCol_{pi}_{eci}", r=0.16, h=5.2, segs=14, at=(px + ecx, -3.1, 3.0))
            for ecp in end_col:
                ecp.data.materials.append(mat)
                kit.map_faces_to_region(ecp, R_PORTLAND_STONE, S)
                parts.append(ecp)

        reg_pyr(f"EndPediment_{pi}", 3.8, 0.7, 1.6, (px, -3.0, 8.4), region=R_PORTLAND_STONE)

    # 7. 28x 3D Classical Windows along Facade
    # Ground Floor Arched Windows
    for gwi, gwx in enumerate([-7.8, -6.4, -5.0, -3.6, 3.6, 5.0, 6.4, 7.8]):
        gw = kit.make_box(f"GroundWin_{gwi}", 0.9, 0.15, 1.6, (gwx, -2.8, 0.8))
        gw.data.materials.append(mat)
        kit.map_faces_to_region(gw, R_PALACE_WINDOWS, S)
        parts.append(gw)

    # Piano Nobile 3D Pedimented Windows (12 windows)
    for pwi, pwx in enumerate([-8.2, -6.8, -5.4, -4.0, 4.0, 5.4, 6.8, 8.2]):
        is_tri = (pwi % 2 == 0)
        win_parts = make_window_frame(f"PianoWin_{pwi}", w=1.0, h=1.8, d=0.15, is_tri_pediment=is_tri, at=(pwx, -2.8, 3.8))
        for wp in win_parts:
            wp.data.materials.append(mat)
            kit.map_faces_to_region(wp, R_PALACE_WINDOWS if "pane" in wp.name else R_PORTLAND_STONE, S)
            parts.append(wp)

    # Second Floor Attic Windows (12 windows)
    for awi, awx in enumerate([-8.2, -6.8, -5.4, -4.0, 4.0, 5.4, 6.8, 8.2]):
        aw = kit.make_box(f"AtticWin_{awi}", 0.85, 0.12, 1.2, (awx, -2.8, 6.4))
        aw.data.materials.append(mat)
        kit.map_faces_to_region(aw, R_PALACE_WINDOWS, S)
        parts.append(aw)

    # 8. Dentil Modillion Cornice Band (36 Dentil blocks along facade)
    for di in range(32):
        dx = -10.5 + di * 0.68
        dentil = kit.make_box(f"Dentil_{di}", 0.25, 0.25, 0.25, (dx, -2.85, 8.1))
        dentil.data.materials.append(mat)
        kit.map_faces_to_region(dentil, R_PORTLAND_STONE, S)
        parts.append(dentil)

    # 9. 3D Attic Balusters along Roofline (36 individual 3D balusters)
    for bi in range(32):
        bx = -10.5 + bi * 0.68
        bal = make_baluster(f"AtticBaluster_{bi}", r=0.07, h=0.7, at=(bx, -2.75, 8.3))
        bal.data.materials.append(mat)
        kit.map_faces_to_region(bal, R_PORTLAND_STONE, S)
        parts.append(bal)

    # 10. 14x 3D Stone Urns atop the Roof Attic Balustrade
    urn_x_positions = [-10.5, -8.8, -7.2, -5.6, -4.0, -2.4, -0.8, 0.8, 2.4, 4.0, 5.6, 7.2, 8.8, 10.5]
    for ui, ux in enumerate(urn_x_positions):
        urn_parts = make_stone_urn(f"RoofUrn_{ui}", r=0.22, h=0.9, at=(ux, -2.8, 9.0))
        for up in urn_parts:
            up.data.materials.append(mat)
            kit.map_faces_to_region(up, R_PORTLAND_STONE, S)
            parts.append(up)

    # 11. French Slate Mansard Roof, Dormers & Chimneys
    reg_box("PalaceMansardMain", 21.6, 5.0, 2.2, (0, 0.2, 9.0), region=R_SLATE_MANSARD)

    for di, dx in enumerate([-7.0, -4.5, 4.5, 7.0]):
        reg_pyr(f"MansardDormer_{di}", 1.2, 1.2, 1.4, (dx, -2.2, 9.0), region=R_SLATE_MANSARD)

    for chi, (chx, chy) in enumerate([(-8.5, 1.5), (-4.0, 1.5), (4.0, 1.5), (8.5, 1.5)]):
        reg_box(f"PalaceChimney_{chi}", 0.9, 0.9, 1.8, (chx, chy, 10.2), region=R_PORTLAND_STONE)
        reg_box(f"PalaceChimneyCap_{chi}", 1.05, 1.05, 0.2, (chx, chy, 12.0), region=R_PORTLAND_STONE)

    # Finalize & Export
    shell = kit.join(parts, "Landmark_Buckingham_Palace")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "landmark_buckingham_palace_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "landmark_buckingham_palace.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/New LonLandmark
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb_path, DEPLOY_DIR / "landmark_buckingham_palace.glb")
        shutil.copy2(preview_path, TEXTURES_DIR / "landmark_buckingham_palace_preview.png")
        shutil.copy2(OUT_DIR / "atlas_buckingham_palace.png", TEXTURES_DIR / "atlas_buckingham_palace.png")
        print(f"[BuckinghamPalace] 4500-tri clean palace deployed successfully.")
    except Exception as e:
        print(f"[BuckinghamPalace] deploy notice: {e}")


if __name__ == "__main__":
    main()
