"""Working-class terraced house — repeatable scenery filler, not band 6.

A generic 2-up-2-down London terrace: brick shell, gable roof, door offset to
one side with a single ground-floor window opposite, two first-floor windows.
Meant to stand in for the downloaded photo-baked terrace models currently
placed repeatedly in Home_London_Prefab (`Assets/3DModels/major london
buildings/terraced+house+3d+model.glb` and the "row of" variant) — same
low-poly painted-atlas approach as building_quidland.py, not a photo bake.

Repeatability is handled by painting the SAME geometry with different atlas
colours per call — three variants exported in one run, so placing several
side by side does not read as one house copy-pasted down the street.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/building_terrace_house.py
"""

import bmesh
import bpy

import asset_kit as kit
from atlas import Atlas, material_for

S = 256  # atlas size

# --- atlas regions (x, y, w, h) — bottom-left origin, matches painting ------
# Bottom half: brick/ground materials, exact 256x128 tiling.
R_BRICK       = (0,   0,  128, 128)  # main/upper-floor/side brick
R_BRICK_GRIME = (128, 0,   64,  64)  # ground-floor brick, grimier + shaded
R_STEP        = (192, 0,   64,  64)  # pavement / step / misc concrete reveal
R_ROOF        = (128, 64,  64,  64)  # roof slate
R_CHIMNEY     = (192, 64,  64,  64)  # chimney stack / cap
# Top half: full 256x128, also exact tiling.
R_EAVES       = (0,   232, 256, 24)  # timber fascia board, full width
R_DOOR        = (0,   128, 40, 104)  # door incl. frame
R_WINDOW      = (40,  128, 48,  80)  # sash window (reused for GF + both FF)
R_DISH        = (40,  208, 48,  24)  # small wall decal slot (dish or blank)
R_BRICK_PARTY = (88,  128, 168, 104)  # party-wall / gable brick

# --- house geometry, shared by every variant --------------------------------
W = 5.2          # width (X, street frontage)
D = 8.0           # depth (Y, front to back)
GF_H = 2.6        # ground floor height
FF_H = 2.5        # first floor height
EAVES_H = GF_H + FF_H       # 5.1 — wallplate / eaves line
RIDGE_RISE = 2.1
RIDGE_H = EAVES_H + RIDGE_RISE   # 7.2
EAVES_OVERHANG = 0.25

DOOR_W, DOOR_H, DOOR_X = 0.95, 2.05, -1.35
WIN_W, WIN_H = 1.05, 1.4
WIN_GF_X, WIN_GF_Z = 1.35, 0.75
WIN_FF_X_L, WIN_FF_X_R, WIN_FF_Z = -1.1, 1.1, GF_H + 0.55


def make_gable_roof(name, w, d, eaves_h, ridge_h, at=(0.0, 0.0, 0.0)):
    """Simple pitched roof: ridge runs along X, centred on Y. `at` is the
    house footprint centre at the eaves baseline (matches kit.make_box's
    bottom-centre convention). Closed manifold: 6 verts, 5 faces."""
    hw, hd = w / 2, d / 2
    cx, cy, cz = at
    verts_co = [
        (cx - hw, cy - hd, cz + eaves_h),  # 0 front-left eave
        (cx + hw, cy - hd, cz + eaves_h),  # 1 front-right eave
        (cx + hw, cy + hd, cz + eaves_h),  # 2 back-right eave
        (cx - hw, cy + hd, cz + eaves_h),  # 3 back-left eave
        (cx - hw, cy, cz + ridge_h),       # 4 ridge left
        (cx + hw, cy, cz + ridge_h),       # 5 ridge right
    ]
    faces_idx = [
        (0, 1, 5, 4),   # front slope
        (2, 3, 4, 5),   # back slope
        (3, 0, 4),      # left gable end
        (1, 2, 5),      # right gable end
        (0, 3, 2, 1),   # underside, closes the mesh
    ]
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bverts = [bm.verts.new(co) for co in verts_co]
    for idx in faces_idx:
        bm.faces.new([bverts[i] for i in idx])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def roof_side(direction):
    checks = {
        "front": lambda f: f.normal.y < -0.3,
        "back": lambda f: f.normal.y > 0.3,
        "left": lambda f: f.normal.x < -0.3,
        "right": lambda f: f.normal.x > 0.3,
        "bottom": lambda f: f.normal.z < -0.3,
    }
    return checks[direction]


def wall_side(name):
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
    kit.map_faces_to_region(obj, front, S, only=wall_side("front"))
    kit.map_faces_to_region(obj, sides, S, only=wall_side("left"))
    kit.map_faces_to_region(obj, sides, S, only=wall_side("right"))
    kit.map_faces_to_region(obj, back or sides, S, only=wall_side("back"))
    kit.map_faces_to_region(obj, top or R_STEP, S, only=wall_side("top"))
    kit.map_faces_to_region(obj, bottom or R_STEP, S, only=wall_side("bottom"))


def paint_atlas(name, colors, boarded, has_dish):
    a = Atlas(S, seed=colors["seed"])

    # Main brick — upper floor + party walls, clean-ish.
    x, y, w, h = R_BRICK
    a.bricks(x, y, w, h, brick=colors["brick_main"], mortar=colors["mortar"],
              jitter=colors["brick_jitter"])
    a.noise(x, y, w, h, 0.015)

    # Ground-floor brick, grimier, darker toward the pavement.
    x, y, w, h = R_BRICK_GRIME
    a.bricks(x, y, w, h, brick=colors["brick_grime"], mortar=colors["mortar"],
              jitter=colors["brick_jitter"] + 0.02)
    a.shade(x, y, w, h, top=0.0, bottom=-0.12)
    a.noise(x, y, w, h, 0.02)

    # Party/gable wall brick, matches ground-floor grubbiness.
    x, y, w, h = R_BRICK_PARTY
    a.bricks(x, y, w, h, brick=colors["brick_party"], mortar=colors["mortar"],
              jitter=colors["brick_jitter"] + 0.015)
    a.noise(x, y, w, h, 0.02)

    # Roof slate: flat colour, coarse coursing lines, noise.
    x, y, w, h = R_ROOF
    a.rect(x, y, w, h, colors["roof"])
    for ry in range(y, y + h, 6):
        a.rect(x, ry, w, 1, tuple(max(0.0, c - 0.04) for c in colors["roof"]))
    a.noise(x, y, w, h, 0.02)

    # Timber fascia board along the eaves.
    x, y, w, h = R_EAVES
    a.rect(x, y, w, h, colors["eaves"])
    a.rect(x, y, w, 2, tuple(max(0.0, c - 0.08) for c in colors["eaves"]))
    a.noise(x, y, w, h, 0.02)

    # Chimney stack / cap.
    x, y, w, h = R_CHIMNEY
    a.rect(x, y, w, h, colors["chimney"])
    a.noise(x, y, w, h, 0.03)

    # Step / concrete reveal, used for pavement + box sides/tops.
    x, y, w, h = R_STEP
    a.rect(x, y, w, h, colors["step"])
    a.noise(x, y, w, h, 0.025)

    # Door.
    x, y, w, h = R_DOOR
    if boarded:
        a.rect(x, y, w, h, colors["board"])
        for by in range(y + 6, y + h - 4, 12):
            a.rect(x + 2, by, w - 4, 2,
                    tuple(max(0.0, c - 0.06) for c in colors["board"]))
        # rough diagonal cross-brace, staircase-stepped pixels
        brace = tuple(max(0.0, c - 0.10) for c in colors["board"])
        for i in range(h):
            xx = x + int(i * (w - 2) / h)
            a.rect(xx, y + i, 2, 1, brace)
            a.rect(x + w - 2 - xx + x, y + i, 2, 1, brace)
        a.disc(x + w // 2, y + h - 14, 2, (0.15, 0.15, 0.16))  # padlock
    else:
        a.rect(x, y, w, h, colors["door_frame"])
        a.rect(x + 3, y, w - 6, h - 4, colors["door"])
        a.rect(x + 3, y + h - 20, w - 6, 14, colors["door_glass"])  # fanlight
        for gy in range(y + 10, y + h - 24, 22):
            a.rect(x + 6, gy, w - 12, 2,
                    tuple(max(0.0, c - 0.05) for c in colors["door"]))
        a.disc(x + w - 8, y + h // 2 - 8, 2, (0.75, 0.65, 0.20))  # handle
    a.noise(x, y, w, h, 0.015)

    # Window — reused for ground floor and both first-floor windows.
    x, y, w, h = R_WINDOW
    if boarded:
        a.rect(x, y, w, h, colors["board"])
        for by in range(y + 6, y + h - 4, 10):
            a.rect(x + 2, by, w - 4, 2,
                    tuple(max(0.0, c - 0.06) for c in colors["board"]))
    else:
        a.rect(x, y, w, h, colors["window_frame"])
        a.rect(x + 3, y + 3, w - 6, h - 6, colors["door_glass"])
        a.rect(x + 3, y + h // 2 - 1, w - 6, 2, colors["window_frame"])
        a.rect(x + w // 2 - 1, y + 3, 2, h - 6, colors["window_frame"])
        a.rect(x + 4, y + h - 12, (w - 8) // 2, 8, colors["curtain"])
    a.noise(x, y, w, h, 0.015)

    # Wall decal slot — extra party brick, with an optional dish sticker.
    x, y, w, h = R_DISH
    a.bricks(x, y, w, h, brick=colors["brick_party"], mortar=colors["mortar"],
              jitter=colors["brick_jitter"])
    if has_dish:
        cx, cy = x + w // 2, y + h // 2
        a.disc(cx, cy, 8, colors["dish"])
        a.rect(cx - 1, y, 2, h // 2, (0.15, 0.15, 0.16))  # LNB arm

    return a.to_image(name, kit.OUT_DIR)


def build_house(variant, colors, boarded=False, has_dish=False):
    kit.reset_scene()
    img = paint_atlas(f"building_terrace_{variant}", colors, boarded, has_dish)
    mat = material_for(img, f"mat_terrace_{variant}")

    boxes = []

    def box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        boxes.append(o)
        return o

    box("Pavement", W + 1.4, 1.6, 0.08, (0, -D / 2 - 0.7, 0),
        front=R_STEP, sides=R_STEP, top=R_STEP)
    box("GroundFloor", W, D, GF_H, (0, 0, 0),
        front=R_BRICK_GRIME, sides=R_BRICK_PARTY, back=R_BRICK_PARTY)
    box("Door", DOOR_W, 0.2, DOOR_H, (DOOR_X, -D / 2 - 0.05, 0),
        front=R_DOOR, sides=R_STEP, top=R_STEP)
    box("Window_GF", WIN_W, 0.12, WIN_H, (WIN_GF_X, -D / 2 - 0.02, WIN_GF_Z),
        front=R_WINDOW, sides=R_STEP, top=R_STEP)
    box("UpperFloor", W, D, FF_H, (0, 0, GF_H),
        front=R_BRICK, sides=R_BRICK_PARTY, back=R_BRICK_PARTY)
    box("Window_FF_L", WIN_W, 0.12, WIN_H,
        (WIN_FF_X_L, -D / 2 - 0.02, WIN_FF_Z),
        front=R_WINDOW, sides=R_STEP, top=R_STEP)
    box("Window_FF_R", WIN_W, 0.12, WIN_H,
        (WIN_FF_X_R, -D / 2 - 0.02, WIN_FF_Z),
        front=R_WINDOW, sides=R_STEP, top=R_STEP)
    box("Eaves", W + 2 * EAVES_OVERHANG, D + 2 * EAVES_OVERHANG, 0.12,
        (0, 0, EAVES_H), front=R_EAVES, sides=R_EAVES, back=R_EAVES,
        top=R_STEP)
    box("Chimney", 0.5, 0.35, 0.9, (W / 2 - 0.5, -0.3, RIDGE_H - 0.3),
        front=R_CHIMNEY, sides=R_CHIMNEY, top=R_CHIMNEY)
    if has_dish:
        box("Dish", 0.35, 0.05, 0.35,
            (W / 2 - 0.35, -D / 2 - 0.02, GF_H + FF_H - 0.7),
            front=R_DISH, sides=R_STEP, top=R_STEP)

    roof = make_gable_roof("Roof", W + 2 * EAVES_OVERHANG,
                            D + 2 * EAVES_OVERHANG, 0.0, RIDGE_RISE,
                            at=(0, 0, EAVES_H))
    roof.data.materials.append(mat)
    kit.map_faces_to_region(roof, R_ROOF, S, only=roof_side("front"))
    kit.map_faces_to_region(roof, R_ROOF, S, only=roof_side("back"))
    kit.map_faces_to_region(roof, R_BRICK_PARTY, S, only=roof_side("left"))
    kit.map_faces_to_region(roof, R_BRICK_PARTY, S, only=roof_side("right"))
    kit.map_faces_to_region(roof, R_STEP, S, only=roof_side("bottom"))
    boxes.append(roof)

    shell = kit.join(boxes, f"Building_Terrace_{variant}")
    kit.finalize(shell)
    kit.report_stats(shell)
    kit.iso_preview(kit.OUT_DIR / f"building_terrace_{variant}_preview.png",
                    [shell], resolution=1024)
    kit.export_glb(kit.OUT_DIR / f"building_terrace_{variant}.glb", [shell])
    print(f"[building_terrace_house] {variant} done")


VARIANTS = {
    "redbrick": dict(
        colors=dict(
            seed=11,
            brick_main=(0.55, 0.24, 0.18), brick_grime=(0.42, 0.20, 0.16),
            brick_party=(0.48, 0.21, 0.16), mortar=(0.72, 0.68, 0.62),
            brick_jitter=0.05,
            door=(0.08, 0.10, 0.09), door_frame=(0.92, 0.92, 0.88),
            door_glass=(0.12, 0.15, 0.18),
            window_frame=(0.92, 0.92, 0.88), curtain=(0.85, 0.80, 0.68),
            roof=(0.20, 0.20, 0.22), eaves=(0.90, 0.90, 0.85),
            step=(0.55, 0.53, 0.50), chimney=(0.42, 0.24, 0.19),
            dish=(0.75, 0.75, 0.75), board=(0.45, 0.36, 0.24),
        ),
        boarded=False, has_dish=True,
    ),
    "yellowbrick_grubby": dict(
        colors=dict(
            seed=23,
            brick_main=(0.68, 0.58, 0.40), brick_grime=(0.48, 0.42, 0.32),
            brick_party=(0.55, 0.47, 0.34), mortar=(0.66, 0.62, 0.52),
            brick_jitter=0.06,
            door=(0.15, 0.28, 0.16), door_frame=(0.80, 0.78, 0.70),
            door_glass=(0.10, 0.13, 0.14),
            window_frame=(0.80, 0.78, 0.70), curtain=(0.70, 0.66, 0.55),
            roof=(0.25, 0.23, 0.20), eaves=(0.55, 0.50, 0.40),
            step=(0.45, 0.43, 0.40), chimney=(0.40, 0.34, 0.26),
            dish=(0.70, 0.70, 0.70), board=(0.42, 0.34, 0.23),
        ),
        boarded=False, has_dish=False,
    ),
    "boarded": dict(
        colors=dict(
            seed=37,
            brick_main=(0.50, 0.26, 0.20), brick_grime=(0.34, 0.18, 0.15),
            brick_party=(0.40, 0.20, 0.16), mortar=(0.58, 0.54, 0.48),
            brick_jitter=0.07,
            door=(0.35, 0.36, 0.38), door_frame=(0.30, 0.31, 0.33),
            door_glass=(0.10, 0.13, 0.14),
            window_frame=(0.30, 0.31, 0.33), curtain=(0.60, 0.58, 0.50),
            roof=(0.18, 0.18, 0.19), eaves=(0.55, 0.52, 0.45),
            step=(0.40, 0.38, 0.36), chimney=(0.32, 0.22, 0.18),
            dish=(0.65, 0.65, 0.65), board=(0.45, 0.36, 0.24),
        ),
        boarded=True, has_dish=False,
    ),
}


def main():
    for name, spec in VARIANTS.items():
        build_house(name, spec["colors"], boarded=spec["boarded"],
                    has_dish=spec["has_dish"])


main()
