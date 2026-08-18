"""Proxy-rig sprite-sheet renderer for the 2D cast pipeline (runs INSIDE Blender).

The 2D analogue of asset_kit: a subject is a script, the animation is a pose
function, and every frame is a deterministic orthographic render. Re-running a
subject regenerates its frames in place — change a frame count or smooth a pose
curve and the whole sheet is rebuilt identically everywhere else.

    import sprite_kit as sk
    sk.render_subject("proxy", world_height=1.55)

Pipeline shape:
  1. build_proxy_rig  — a segmented humanoid: one box (or textured card) per
     body part, each with its origin at its joint, parented into a hierarchy.
     Rotating a part about its origin IS the animation; no armature, no
     skinning, nothing that behaves differently headless.
  2. POSES            — parametric pose functions, action name -> f(i, n) ->
     {part: (rx, ry, rz) degrees}. Continuous in i/n, so any frame count
     samples the same motion: regenerate walk at 8 frames instead of 6 and it
     is the same walk, smoother.
  3. render_action    — fixed ortho camera, transparent film, one PNG per
     frame plus a manifest.json, under out/sprites/<subject>/<action>/.
     Tools/pack_sprites.py (plain CPython + Pillow) packs those into the
     sheet + sidecar that ART_PIPELINE.md specifies.

Camera: the game contract (ART_PIPELINE.md §1) wants THREE-QUARTER view facing
camera-right, 30 degrees from above — NOT a flat side view. The importer
measures body width against the idle sheet and has rejected side-on art before
(47 px against an idle's 122). Default azimuth/pitch match the contract; both
are parameters if a genuine side view is ever wanted for something else.

Conventions: 1 unit = 1 metre, Z up, character faces +X (renders as
camera-right). Feet at z=0. worldHeight here must equal the height the actor
renders at (WorldActorVisual.Height), same rule as hand-delivered art.
"""

import json
import math
import shutil
from pathlib import Path

import bpy
from mathutils import Vector

import asset_kit as kit

OUT_DIR = Path(__file__).resolve().parent.parent / "out"
SPRITES_DIR = OUT_DIR / "sprites"

# Actions whose body legitimately leaves the ground / changes shape. Exempt
# from ground-snapping here and from the baseline+height checks in
# Tools/pack_sprites.py, mirroring ArtImportTool. Keep the two lists in step.
SHAPE_CHANGING = {"death", "roll", "knockback", "cycle"}

# How densely fit_camera_to_poses samples each pose function. Independent of
# any action's real frame count on purpose — see the comment there.
FIT_SAMPLES = 24

# ---------------------------------------------------------------------------
# Rig
# ---------------------------------------------------------------------------

# Default palette, overridable per subject: grubby modern Britain.
DEFAULT_COLORS = {
    "skin":   (0.72, 0.57, 0.45),
    "top":    (0.35, 0.36, 0.38),   # hoodie grey
    "bottom": (0.14, 0.16, 0.20),   # dark trackies
    "shoes":  (0.09, 0.09, 0.10),
}

# Part table, all lengths as fractions of total height H. Facing +X, so:
# x = forward/back, y = left(+)/right(-), z = up. Each part:
#   (name, parent, pivot(x,y,z), box(sx, sy, z0, z1, cx), color_key)
# box: sx/sy are x/y sizes, z0..z1 the vertical span, cx an optional forward
# offset of the box centre (feet stick out forward). Pivot is the joint the
# part rotates about.
PARTS = [
    ("pelvis",  None,      (0, 0,      0.52), (0.11,  0.17,  0.47, 0.56, 0),     "bottom"),
    ("torso",   "pelvis",  (0, 0,      0.55), (0.13,  0.19,  0.56, 0.84, 0),     "top"),
    ("head",    "torso",   (0, 0,      0.85), (0.115, 0.115, 0.86, 1.00, 0.01),  "skin"),
    ("arm_u.L", "torso",   (0,  0.125, 0.81), (0.05,  0.05,  0.64, 0.81, 0),     "top"),
    ("arm_l.L", "arm_u.L", (0,  0.125, 0.64), (0.045, 0.045, 0.47, 0.64, 0),     "skin"),
    ("arm_u.R", "torso",   (0, -0.125, 0.81), (0.05,  0.05,  0.64, 0.81, 0),     "top"),
    ("arm_l.R", "arm_u.R", (0, -0.125, 0.64), (0.045, 0.045, 0.47, 0.64, 0),     "skin"),
    ("thigh.L", "pelvis",  (0,  0.055, 0.49), (0.07,  0.075, 0.27, 0.49, 0),     "bottom"),
    ("shin.L",  "thigh.L", (0,  0.055, 0.27), (0.06,  0.065, 0.045, 0.27, 0),    "bottom"),
    ("foot.L",  "shin.L",  (0,  0.055, 0.05), (0.11,  0.06,  0.0,  0.045, 0.025), "shoes"),
    ("thigh.R", "pelvis",  (0, -0.055, 0.49), (0.07,  0.075, 0.27, 0.49, 0),     "bottom"),
    ("shin.R",  "thigh.R", (0, -0.055, 0.27), (0.06,  0.065, 0.045, 0.27, 0),    "bottom"),
    ("foot.R",  "shin.R",  (0, -0.055, 0.05), (0.11,  0.06,  0.0,  0.045, 0.025), "shoes"),
]

LEG_LENGTH = 0.44  # hip pivot z minus foot sole, as a fraction of H


def build_proxy_rig(height, colors=None, part_images=None):
    """Build the segmented humanoid. Returns {part_name: object}.

    colors: {color_key: (r, g, b)} overriding DEFAULT_COLORS.
    part_images: {part_name: png_path} — replaces that part's box with a
    camera-facing textured card (the photo-staging seam, see make_part_card).
    Parts with an image need engine="CYCLES" in render_subject for the alpha
    to render.
    """
    palette = dict(DEFAULT_COLORS)
    if colors:
        palette.update(colors)
    keys = sorted(palette)
    mat, n = kit.make_palette_material("sprite_rig", [palette[k] for k in keys])

    rig = {}
    for name, parent, pivot, box, ckey in PARTS:
        sx, sy, z0, z1, cx = box
        if part_images and name in part_images:
            obj = make_part_card(name, part_images[name],
                                 height=(z1 - z0) * height,
                                 at=(cx * height, pivot[1] * height, z0 * height))
        else:
            obj = kit.make_box(name, sx * height, sy * height,
                               (z1 - z0) * height,
                               at=(cx * height, pivot[1] * height, z0 * height))
            obj.data.materials.append(mat)
            kit.paint_faces(obj, lambda f, i=keys.index(ckey): i, n)
        # Origin at the joint so rotation_euler rotates about it.
        bpy.context.scene.cursor.location = Vector(pivot) * height
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        rig[name] = obj

    for name, parent, *_ in PARTS:
        if parent:
            child = rig[name]
            child.parent = rig[parent]
            child.matrix_parent_inverse = rig[parent].matrix_world.inverted()
    return rig


def make_part_card(name, image_path, height, at, azimuth_deg=-45.0):
    """The photo-staging seam: a body part as a flat textured card.

    Cut a photorealistic source image into per-part PNGs (with alpha) once per
    subject; each card is sized to the part's height, keeps the image's aspect,
    and faces the camera azimuth so it never renders edge-on. The rig then
    animates the photo exactly like the boxes — classic paper-doll cutout.
    """
    img = bpy.data.images.load(str(Path(image_path).resolve()))
    aspect = img.size[0] / img.size[1]
    w = height * aspect

    import bmesh
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    # Card in the plane whose normal is the camera's horizontal direction.
    a = math.radians(azimuth_deg)
    right = Vector((-math.sin(a), math.cos(a), 0.0))  # screen-right in world
    verts = []
    for u, v in ((-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0)):
        p = Vector(at) + right * (u * w) + Vector((0, 0, v * height))
        verts.append(bm.verts.new(p))
    bm.faces.new(verts)
    uvl = bm.loops.layers.uv.new("UVMap")
    for loop, uv in zip(bm.faces[:][0].loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uvl].uv = uv
    bm.to_mesh(mesh)
    bm.free()

    mat = bpy.data.materials.new(f"{name}_card")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat.blend_method = "CLIP"
    mesh.materials.append(mat)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Poses — parametric, so any frame count samples the same motion
# ---------------------------------------------------------------------------

def _smoothstep(u):
    return u * u * (3.0 - 2.0 * u)


def _interp_keys(keys, t):
    """Key-pose interpolation: keys = [(t, {part: (rx,ry,rz)}), ...] sorted."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1:
            u = _smoothstep((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            names = set(p0) | set(p1)
            out = {}
            for nm in names:
                a = p0.get(nm, (0, 0, 0))
                b = p1.get(nm, (0, 0, 0))
                out[nm] = tuple(a[k] + (b[k] - a[k]) * u for k in range(3))
            return out
    return dict(keys[-1][1])


def pose_idle(i, n):
    ph = 2 * math.pi * i / n
    b = math.sin(ph)  # breathe
    return {
        "torso":   (0, -2 + 1.5 * b, 0),
        "head":    (0, 1.5 - 1.5 * b, 0),
        "arm_u.L": (-3, 2 * b, 0),
        "arm_u.R": (3, 2 * b, 0),
        "arm_l.L": (0, -8, 0),
        "arm_l.R": (0, -8, 0),
    }


def pose_walk(i, n):
    # Positive ry swings a limb backward (-X); the stride is a sine, knees lag
    # half a phase, arms counter-swing. Nothing here compensates for the hips
    # dropping as the legs spread — apply_pose ground-snaps the whole rig
    # numerically, which is exact where a compass-gait formula was not.
    ph = 2 * math.pi * i / n + math.pi / 2  # frame 0 = full stride
    s = math.sin(ph)
    swing = 26.0
    knee_l = max(0.0, -38.0 * math.sin(ph - 0.5))
    knee_r = max(0.0, -38.0 * math.sin(ph - 0.5 + math.pi))
    return {
        "thigh.L": (0, swing * s, 0),
        "thigh.R": (0, -swing * s, 0),
        "shin.L":  (0, knee_l, 0),
        "shin.R":  (0, knee_r, 0),
        "foot.L":  (0, -0.4 * knee_l, 0),
        "foot.R":  (0, -0.4 * knee_r, 0),
        "arm_u.L": (-3, -18 * s, 0),
        "arm_u.R": (3, 18 * s, 0),
        "arm_l.L": (0, -14, 0),
        "arm_l.R": (0, -14, 0),
        "torso":   (0, -4, 0),
        "head":    (0, 2, 0),
    }


def pose_attack(i, n):
    t = i / (n - 1) if n > 1 else 0.0
    rest = {"arm_l.L": (0, -10, 0), "arm_l.R": (0, -10, 0)}
    windup = {
        "arm_u.R": (10, 75, 0), "arm_l.R": (0, -80, 0),
        "arm_u.L": (-5, -15, 0), "arm_l.L": (0, -20, 0),
        "torso": (0, 7, 8), "head": (0, -5, -6),
        "thigh.L": (0, -8, 0), "thigh.R": (0, 8, 0),
    }
    strike = {
        "arm_u.R": (5, -80, 0), "arm_l.R": (0, -10, 0),
        "arm_u.L": (-5, 12, 0), "arm_l.L": (0, -25, 0),
        "torso": (0, -12, -10), "head": (0, 4, 4),
        "thigh.L": (0, -14, 0), "thigh.R": (0, 12, 0),
        "shin.R": (0, 14, 0),
    }
    return _interp_keys(
        [(0.0, rest), (0.35, windup), (0.55, strike), (1.0, rest)], t)


def pose_hurt(i, n):
    t = i / (n - 1) if n > 1 else 0.0
    rest = {"arm_l.L": (0, -10, 0), "arm_l.R": (0, -10, 0)}
    recoil = {
        "torso": (0, 15, 0), "head": (0, 12, 0),
        "arm_u.L": (-8, -35, 0), "arm_u.R": (8, -35, 0),
        "arm_l.L": (0, -40, 0), "arm_l.R": (0, -40, 0),
        "thigh.L": (0, 6, 0), "thigh.R": (0, -6, 0),
    }
    return _interp_keys([(0.0, rest), (0.45, recoil), (1.0, rest)], t)


POSES = {
    "idle": pose_idle,
    "walk": pose_walk,
    "attack": pose_attack,
    "hurt": pose_hurt,
}

# Contract defaults straight from ART_PIPELINE.md §8. Override per subject to
# regenerate an action smoother (e.g. walk at 8 frames) — the pose functions
# are parametric, so the motion is identical, just sampled finer. The importer
# warns on a non-standard count; it does not refuse.
DEFAULT_ACTIONS = {
    "idle":   {"frames": 4, "fps": 6,  "loop": True},
    "walk":   {"frames": 6, "fps": 8,  "loop": True},
    "attack": {"frames": 6, "fps": 12, "loop": False},
    "hurt":   {"frames": 3, "fps": 12, "loop": False},
}


# ---------------------------------------------------------------------------
# Camera + render
# ---------------------------------------------------------------------------

def setup_camera(height, azimuth=-45.0, pitch=30.0):
    """Fixed orthographic camera, identical for every frame of every action.

    Defaults give the contract view: three-quarter, 30 degrees from above,
    character facing camera-right. The framing (ortho_scale) is not set here —
    fit_camera_to_poses measures it from the real posed geometry.
    """
    scene = bpy.context.scene
    target = Vector((0.0, 0.0, height * 0.5))
    a, p = math.radians(azimuth), math.radians(pitch)
    direction = Vector((math.cos(p) * math.cos(a),
                        math.cos(p) * math.sin(a),
                        math.sin(p)))
    cam_data = bpy.data.cameras.new("SpriteCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = height * 2.0  # provisional; fitted below
    cam = bpy.data.objects.new("SpriteCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = target + direction * max(height * 4.0, 3.0)
    cam.rotation_euler = (cam.location - target).to_track_quat("Z", "Y").to_euler()
    scene.camera = cam
    return cam


def _rig_world_verts(rig):
    """Every rig vertex in world space, after constraints/parenting resolve."""
    deps = bpy.context.evaluated_depsgraph_get()
    for obj in rig.values():
        ev = obj.evaluated_get(deps)
        mw = ev.matrix_world
        for v in ev.data.vertices:
            yield mw @ v.co


def fit_camera_to_poses(rig, cam, actions, height, fill=0.88,
                        h_margin=0.96):
    """Set ortho_scale ONCE from the widest/tallest pose the subject reaches.

    This is what makes every sheet of a subject agree with every other one:
    the camera is fitted across all actions together, so idle, walk and attack
    are drawn at the same scale by construction rather than by hope. Fitting
    per action would let a wide attack pose shrink that sheet's figure and trip
    the importer's body-width check.

    fill: figure height as a fraction of frame height (accepted idle = 0.89).
    """
    # setup_camera assigned rotation_euler; matrix_world does not reflect it
    # until the depsgraph runs. Without this the fit silently measures WORLD
    # axes instead of camera axes and every figure overflows its cell.
    inv, _ = _cam_space(cam)
    top = 0.0
    left, right = float("inf"), float("-inf")
    # Sample EVERY known pose at a fixed rate, not the actions actually being
    # rendered at their actual frame counts. Otherwise the fitted scale is a
    # function of the frame counts — re-rendering walk at 10 frames instead of
    # 6 moved it 0.2% — and of which actions a subject happens to declare. A
    # fixed sampling makes ortho_scale depend only on the rig and the camera,
    # so every sheet of every subject at a given height is drawn at one scale.
    for action, pose_fn in sorted(POSES.items()):
        for i in range(FIT_SAMPLES):
            apply_pose(rig, pose_fn(i, FIT_SAMPLES), height, cam=cam,
                       ground_snap=action not in SHAPE_CHANGING)
            pts = [inv @ p for p in _rig_world_verts(rig)]
            # apply_pose pinned the lowest point to camera-space y = 0, so the
            # vertical extent is just the highest point.
            top = max(top, max(p.y for p in pts))
            left = min(left, min(p.x for p in pts))
            right = max(right, max(p.x for p in pts))
    cam.data.ortho_scale = max(top / fill, (right - left) / h_margin)

    # Centre horizontally by moving the camera: sliding it along its own right
    # axis cannot change any point's camera-space y, so the baseline is safe.
    mw = cam.matrix_world.to_3x3()
    cam.location += (mw @ Vector((1.0, 0.0, 0.0))).normalized() * ((left + right) / 2.0)
    bpy.context.view_layer.update()

    # Centre vertically by moving the FIGURE, not the camera. The snap in
    # apply_pose re-pins the feet to baseline_v on every frame, so a camera
    # move here would simply be undone at render time — that regression put
    # the feet on the frame's centreline and halved the fill.
    baseline_v = -top / 2.0
    print(f"[sprite_kit] fitted ortho_scale {cam.data.ortho_scale:.3f} "
          f"(tallest pose {top:.3f} m, widest {right - left:.3f} m)")
    return baseline_v


def setup_render(resolution=512, engine="BLENDER_WORKBENCH"):
    scene = bpy.context.scene
    scene.render.engine = engine
    if engine == "BLENDER_WORKBENCH":
        shading = scene.display.shading
        shading.light = "FLAT"
        shading.color_type = "TEXTURE"
    elif engine == "CYCLES":
        scene.cycles.samples = 32
        scene.cycles.use_denoising = False
    scene.render.film_transparent = True
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def _cam_space(cam):
    """(world->camera matrix, world-Z component of the camera's up axis)."""
    bpy.context.view_layer.update()
    up = (cam.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    return cam.matrix_world.inverted(), up.z


def apply_pose(rig, pose, height, cam=None, ground_snap=True, baseline_v=0.0):
    """Pose the rig, then pin its lowest *screen* point to one fixed line.

    Snapping in world Z is not enough. At a 30 degree pitch the pixel-lowest
    point is whichever ground contact is furthest toward the camera, so in a
    walk it alternates feet and the bounding box bottom moves — 23 px of drift
    on the first run, against an importer that demands 0. Snapping in camera
    space pins the pixels instead, which is what is actually measured.

    Shape-changing actions (roll, knockback, death) pass ground_snap=False:
    leaving the ground is the pose, and they are exempt from the check.
    """
    for obj in rig.values():
        obj.rotation_euler = (0.0, 0.0, 0.0)
    rig["pelvis"].location = (0.0, 0.0, 0.0)
    for name, value in pose.items():
        # Underscore keys are rig-level scalars (e.g. _pelvis_lift), not
        # per-part euler triples — filter before unpacking.
        if name.startswith("_"):
            continue
        rx, ry, rz = value
        rig[name].rotation_euler = (math.radians(rx),
                                    math.radians(ry),
                                    math.radians(rz))
    bpy.context.view_layer.update()
    if ground_snap:
        if cam is None:
            rig["pelvis"].location.z -= min(p.z for p in _rig_world_verts(rig))
        else:
            inv, up_z = _cam_space(cam)
            lowest_v = min((inv @ p).y for p in _rig_world_verts(rig))
            rig["pelvis"].location.z -= (lowest_v - baseline_v) / up_z
        bpy.context.view_layer.update()


def render_action(rig, subject, action, frames, fps, loop, world_height,
                  cam=None, baseline_v=0.0, category="characters",
                  out_root=SPRITES_DIR):
    """Render one action's frames + manifest. Wipes and rewrites its folder,
    so regeneration can never leave stale frames behind."""
    pose_fn = POSES[action]
    out_dir = Path(out_root) / subject / action
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    scene = bpy.context.scene
    for i in range(frames):
        apply_pose(rig, pose_fn(i, frames), world_height, cam=cam,
                   ground_snap=action not in SHAPE_CHANGING,
                   baseline_v=baseline_v)
        scene.render.filepath = str(out_dir / f"frame_{i:02d}.png")
        bpy.ops.render.render(write_still=True)
    manifest = {
        "subject": subject, "action": action, "category": category,
        "frames": frames, "fps": fps, "loop": loop,
        "worldHeight": world_height,
        "resolution": scene.render.resolution_x,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[sprite_kit] {subject}/{action}: {frames} frames -> {out_dir}")


def render_subject(subject, world_height, colors=None, part_images=None,
                   actions=None, resolution=512, fill=0.88,
                   azimuth=-45.0, pitch=30.0, engine=None,
                   category="characters"):
    """One call per subject script: build, aim, render every action."""
    kit.reset_scene()
    rig = build_proxy_rig(world_height, colors=colors, part_images=part_images)
    actions = actions or DEFAULT_ACTIONS
    cam = setup_camera(world_height, azimuth=azimuth, pitch=pitch)
    baseline_v = fit_camera_to_poses(rig, cam, actions, world_height, fill=fill)
    if engine is None:
        # Workbench ignores material alpha, so textured cards need Cycles.
        engine = "CYCLES" if part_images else "BLENDER_WORKBENCH"
    setup_render(resolution=resolution, engine=engine)
    for action, spec in actions.items():
        render_action(rig, subject, action, spec["frames"], spec["fps"],
                      spec["loop"], world_height, cam=cam,
                      baseline_v=baseline_v, category=category)
    print(f"[sprite_kit] subject '{subject}' done "
          f"({len(actions)} actions, engine {engine})")
