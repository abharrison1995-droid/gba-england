"""High-Poly (~3000 Tris) British Ford Transit Van (White Commercial Work Van).

Specs:
- Real-world scale: Length: 5.35m, Width: 2.04m, Height: 2.30m (MWB Medium Roof).
- Rich 3D low-poly geometry targeted at ~3,000 Triangles:
  - Aerodynamic front cab with integrated flush headlight clusters, sloped hood, chrome Ford badge, lower air intake.
  - Detailed commercial interior visible through windshield: 2 bucket seats with headrests, steering wheel & dash.
  - 4x high-detail 3D wheels (24-segment treaded tires, deep 5-hole steel rims with 3D lug nuts, hubs & brake discs).
  - Passenger sliding door rail, side panel recesses, rear 50/50 barn doors, rear ladder, roof ribs, mudflaps.
  - High-mount third brake light, vertical D-pillar taillight towers, British registration plates (BD24 VNN).
- Procedural 512x512 texture atlas with nearest-neighbor crisp pixel art texturing.
- Deploys directly to Assets/3DModels/Vehicles/.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/vehicles/vehicle_transit_van_3000tri.py
"""

import math
import shutil
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR = kit.OUT_DIR / "vehicles"
ASSETS_VEHICLES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "Vehicles"

# --- Atlas Region Definitions (x, y, w, h) ---
R_BODY_WHITE      = (0,   256, 256, 256)   # Commercial White gloss bodywork
R_BUMPER_BLACK    = (256, 256, 128, 256)   # Heavy-duty textured black plastic bumpers & trim
R_FRONT_GRILLE    = (0,   128, 256, 128)   # Black honeycomb radiator grille with Ford Blue Oval badge
R_HEADLIGHTS      = (256, 128, 128, 128)   # Clear polycarbonate headlights with chrome reflectors & amber turn
R_TAILLIGHTS      = (384, 128, 128, 128)   # Vertical red brake light, amber turn, white reverse cluster
R_GLASS_TINT      = (0,   0,   256, 128)   # Deep tinted windshield & cab windows
R_WHEEL_TIRE      = (256, 0,   128, 128)   # Treaded tire rubber
R_WHEEL_RIM       = (384, 0,   128, 128)   # Silver 5-hole steel wheel rim with black 5-lug nuts & center hub
R_PLATES_UK       = (384, 256, 128, 128)   # British number plates: White front / Yellow rear ("BD24 VNN")

# --- Palette Colors ---
VAN_WHITE         = (0.92, 0.93, 0.94)
VAN_WHITE_SHADE   = (0.82, 0.83, 0.85)
PLASTIC_BLACK     = (0.13, 0.14, 0.15)
PLASTIC_DARK      = (0.08, 0.09, 0.10)
FORD_BLUE         = (0.05, 0.22, 0.55)
GLASS_DARK        = (0.11, 0.15, 0.20)
HEADLIGHT_CHROME  = (0.85, 0.88, 0.92)
AMBER_TURN        = (0.95, 0.55, 0.08)
TAIL_RED          = (0.85, 0.08, 0.08)
TIRE_RUBBER       = (0.15, 0.15, 0.16)
RIM_SILVER        = (0.75, 0.76, 0.78)
PLATE_YELLOW      = (0.96, 0.82, 0.12)
PLATE_WHITE       = (0.95, 0.95, 0.95)


def paint_transit_van_atlas():
    a = Atlas(S, seed=3000)

    # 1. White Van Bodywork (R_BODY_WHITE)
    x, y, w, h = R_BODY_WHITE
    a.rect(x, y, w, h, VAN_WHITE)
    for py in [y + 40, y + 120, y + 200]:
        a.rect(x, py, w, 2, VAN_WHITE_SHADE)
    # Door handle recess & lock cylinder
    a.rect(x + 30, y + 80, 40, 14, (0.08, 0.08, 0.09))
    a.disc(x + 60, y + 87, 4, (0.7, 0.7, 0.7))
    a.shade(x, y, w, h, top=0.02, bottom=-0.04)
    a.noise(x, y, w, h, 0.008)

    # 2. Heavy-Duty Textured Plastic Trim (R_BUMPER_BLACK)
    x, y, w, h = R_BUMPER_BLACK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    for gy in range(y, y + h, 8):
        a.rect(x, gy, w, 2, PLASTIC_DARK)
    a.noise(x, y, w, h, 0.015)

    # 3. Front Radiator Grille & Ford Badge (R_FRONT_GRILLE)
    x, y, w, h = R_FRONT_GRILLE
    a.rect(x, y, w, h, PLASTIC_DARK)
    for gy in range(y + 10, y + h - 10, 14):
        a.rect(x + 10, gy, w - 20, 6, (0.18, 0.19, 0.20))
    # Ford Blue Oval Badge in center
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 26, (0.8, 0.8, 0.8))
    a.disc(cx, cy, 22, FORD_BLUE)
    a.rect(cx - 14, cy - 2, 28, 4, (0.9, 0.9, 0.9))
    a.noise(x, y, w, h, 0.012)

    # 4. Modern Headlights (R_HEADLIGHTS)
    x, y, w, h = R_HEADLIGHTS
    a.rect(x, y, w, h, (0.10, 0.12, 0.14))
    a.rect(x + 4, y + 4, w - 8, h - 8, HEADLIGHT_CHROME)
    a.disc(x + 40, y + h // 2, 24, (0.95, 0.98, 1.0))
    a.disc(x + 40, y + h // 2, 14, (0.4, 0.6, 0.8))
    a.rect(x + 8, y + h - 14, w - 16, 6, (1.0, 1.0, 0.95))
    a.rect(x + w - 32, y + 8, 24, h - 16, AMBER_TURN)
    a.noise(x, y, w, h, 0.012)

    # 5. Vertical Rear Taillights (R_TAILLIGHTS)
    x, y, w, h = R_TAILLIGHTS
    a.rect(x, y, w, h, (0.10, 0.10, 0.10))
    a.rect(x + 6, y + h // 2 + 10, w - 12, h // 2 - 16, TAIL_RED)
    for ry in range(y + h // 2 + 16, y + h - 10, 12):
        a.rect(x + 10, ry, w - 20, 4, (1.0, 0.25, 0.25))
    a.rect(x + 6, y + h // 4 + 4, w - 12, h // 4 - 2, AMBER_TURN)
    a.rect(x + 6, y + 6, w - 12, h // 4 - 4, (0.95, 0.95, 0.95))
    a.rect(x + 12, y + 10, w - 24, h // 4 - 12, (0.85, 0.10, 0.10))
    a.noise(x, y, w, h, 0.012)

    # 6. Tinted Glass (R_GLASS_TINT)
    x, y, w, h = R_GLASS_TINT
    a.rect(x, y, w, h, GLASS_DARK)
    for gx in range(x + 20, x + w - 20, 60):
        a.rect(gx, y + 10, 30, h - 20, (0.16, 0.22, 0.28))
    a.noise(x, y, w, h, 0.008)

    # 7. Treaded Tire Rubber (R_WHEEL_TIRE)
    x, y, w, h = R_WHEEL_TIRE
    a.rect(x, y, w, h, TIRE_RUBBER)
    for ty in range(y, y + h, 10):
        a.rect(x, ty, w, 3, (0.08, 0.08, 0.09))
    a.noise(x, y, w, h, 0.015)

    # 8. 5-Hole Steel Wheel Rim (R_WHEEL_RIM)
    x, y, w, h = R_WHEEL_RIM
    a.rect(x, y, w, h, (0.25, 0.25, 0.27))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 54, RIM_SILVER)
    a.disc(cx, cy, 46, (0.35, 0.36, 0.38))
    for i in range(5):
        ang = 2 * math.pi * i / 5
        hx = int(cx + 28 * math.cos(ang))
        hy = int(cy + 28 * math.sin(ang))
        a.disc(hx, hy, 8, PLASTIC_DARK)
        a.disc(hx, hy, 4, (0.7, 0.7, 0.7))
    a.disc(cx, cy, 18, PLASTIC_BLACK)
    a.disc(cx, cy, 8, FORD_BLUE)
    a.noise(x, y, w, h, 0.012)

    # 9. UK Number Plates (R_PLATES_UK)
    x, y, w, h = R_PLATES_UK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    # White Front Plate
    f_box = (x + 8, y + h // 2 + 8, w - 16, h // 2 - 16)
    a.rect(*f_box, PLATE_WHITE)
    a.rect(f_box[0] + 2, f_box[1] + 2, 8, f_box[3] - 4, FORD_BLUE)
    s_plate = "BD24 VNN"
    tw = a.text_width(s_plate, scale=2)
    a.text(f_box[0] + 16 + (f_box[2] - 20 - tw) // 2, f_box[1] + f_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)

    # Yellow Rear Plate
    r_box = (x + 8, y + 8, w - 16, h // 2 - 16)
    a.rect(*r_box, PLATE_YELLOW)
    a.rect(r_box[0] + 2, r_box[1] + 2, 8, r_box[3] - 4, FORD_BLUE)
    a.text(r_box[0] + 16 + (r_box[2] - 20 - tw) // 2, r_box[1] + r_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)
    a.noise(x, y, w, h, 0.010)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("vehicle_transit_van_atlas", OUT_DIR)


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


def map_box(obj, front=R_BODY_WHITE, sides=R_BODY_WHITE, back=None, top=None, bottom=None):
    kit.map_faces_to_region(obj, front or R_BODY_WHITE, S, only=side("front"))
    kit.map_faces_to_region(obj, sides or R_BODY_WHITE, S, only=side("left"))
    kit.map_faces_to_region(obj, sides or R_BODY_WHITE, S, only=side("right"))
    kit.map_faces_to_region(obj, back or sides or R_BODY_WHITE, S, only=side("back"))
    kit.map_faces_to_region(obj, top or R_BODY_WHITE, S, only=side("top"))
    kit.map_faces_to_region(obj, bottom or R_BUMPER_BLACK, S, only=side("bottom"))


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


def make_wheel_assembly(name, radius=0.38, width=0.24, segs=24, at=(0, 0, 0), is_left=True):
    """Generates a high-detail 3D wheel (~380 tris) with tire, deep rim face, and brake disc."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    
    r_rim = radius * 0.62
    w_half = width * 0.5
    w_rim_inset = 0.04 if is_left else -0.04

    # 4 rings of vertices for beveled tire profile
    z_rings = [-w_half, -w_half * 0.75, w_half * 0.75, w_half]
    r_rings = [radius * 0.90, radius, radius, radius * 0.90]

    tire_verts = []
    for ring_i in range(len(z_rings)):
        r_curr = r_rings[ring_i]
        z_curr = z_rings[ring_i]
        ring = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            v = bm.verts.new((r_curr * math.cos(ang), r_curr * math.sin(ang), z_curr))
            ring.append(v)
        tire_verts.append(ring)

    for ring_i in range(len(z_rings) - 1):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((tire_verts[ring_i][i], tire_verts[ring_i][ni],
                          tire_verts[ring_i + 1][ni], tire_verts[ring_i + 1][i]))

    rim_outer_ring = []
    rim_inner_ring = []
    out_z = w_half if is_left else -w_half
    in_z = -w_half if is_left else w_half

    for i in range(segs):
        ang = 2 * math.pi * i / segs
        v_out = bm.verts.new((r_rim * math.cos(ang), r_rim * math.sin(ang), out_z - w_rim_inset))
        rim_outer_ring.append(v_out)
        v_in = bm.verts.new((r_rim * math.cos(ang), r_rim * math.sin(ang), in_z))
        rim_inner_ring.append(v_in)

    out_sidewall_ring = tire_verts[-1] if is_left else tire_verts[0]
    in_sidewall_ring = tire_verts[0] if is_left else tire_verts[-1]

    for i in range(segs):
        ni = (i + 1) % segs
        if is_left:
            bm.faces.new((out_sidewall_ring[i], out_sidewall_ring[ni], rim_outer_ring[ni], rim_outer_ring[i]))
            bm.faces.new((in_sidewall_ring[ni], in_sidewall_ring[i], rim_inner_ring[i], rim_inner_ring[ni]))
        else:
            bm.faces.new((out_sidewall_ring[ni], out_sidewall_ring[i], rim_outer_ring[i], rim_outer_ring[ni]))
            bm.faces.new((in_sidewall_ring[i], in_sidewall_ring[ni], rim_inner_ring[ni], rim_inner_ring[i]))

    hub_center = bm.verts.new((0, 0, out_z - w_rim_inset * 1.5))
    for i in range(segs):
        ni = (i + 1) % segs
        if is_left:
            bm.faces.new((rim_outer_ring[i], rim_outer_ring[ni], hub_center))
        else:
            bm.faces.new((rim_outer_ring[ni], rim_outer_ring[i], hub_center))

    hub_in_center = bm.verts.new((0, 0, in_z))
    for i in range(segs):
        ni = (i + 1) % segs
        if is_left:
            bm.faces.new((rim_inner_ring[ni], rim_inner_ring[i], hub_in_center))
        else:
            bm.faces.new((rim_inner_ring[i], rim_inner_ring[ni], hub_in_center))

    # Add 5 3D Lug Nut Studs on the rim
    r_studs = r_rim * 0.55
    for li in range(5):
        ang = 2 * math.pi * li / 5
        sx = r_studs * math.cos(ang)
        sy = r_studs * math.sin(ang)
        sz = out_z - w_rim_inset * 1.2
        # Hexagonal stud
        s_verts = []
        for vi in range(6):
            va = 2 * math.pi * vi / 6
            sv = bm.verts.new((sx + 0.02 * math.cos(va), sy + 0.02 * math.sin(va), sz + (0.015 if is_left else -0.015)))
            s_verts.append(sv)
        sv_tip = bm.verts.new((sx, sy, sz + (0.025 if is_left else -0.025)))
        for vi in range(6):
            vni = (vi + 1) % 6
            if is_left:
                bm.faces.new((s_verts[vi], s_verts[vni], sv_tip))
            else:
                bm.faces.new((s_verts[vni], s_verts[vi], sv_tip))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = at
    return obj


def make_sloped_cowl(name, w_rear, w_front, y_rear, y_front, z_rear_btm, z_rear_top, z_front_btm, z_front_top):
    """Creates a seamless sloped 3D cowl box (bonnet or windshield) with outward normals."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    v0 = bm.verts.new((-w_rear/2,  y_rear, z_rear_btm))
    v1 = bm.verts.new(( w_rear/2,  y_rear, z_rear_btm))
    v2 = bm.verts.new(( w_rear/2,  y_rear, z_rear_top))
    v3 = bm.verts.new((-w_rear/2,  y_rear, z_rear_top))

    v4 = bm.verts.new((-w_front/2, y_front, z_front_btm))
    v5 = bm.verts.new(( w_front/2, y_front, z_front_btm))
    v6 = bm.verts.new(( w_front/2, y_front, z_front_top))
    v7 = bm.verts.new((-w_front/2, y_front, z_front_top))

    bm.faces.new((v1, v0, v3, v2)) # Back (+Y)
    bm.faces.new((v4, v5, v6, v7)) # Front (-Y)
    bm.faces.new((v0, v4, v7, v3)) # Left (-X)
    bm.faces.new((v5, v1, v2, v6)) # Right (+X)
    bm.faces.new((v7, v6, v2, v3)) # Top (sloped roof/windshield outward)
    bm.faces.new((v0, v1, v5, v4)) # Bottom (-Z)

    bm.to_mesh(mesh)
    bm.free()
    return obj


def make_driver_seat(name, at=(0, 0, 0)):
    """Detailed high-back commercial van bucket seat with headrest."""
    parts = []
    c = kit.make_box(f"{name}_cushion", 0.46, 0.46, 0.12, (at[0], at[1], at[2] + 0.35))
    parts.append(c)
    b = kit.make_box(f"{name}_back", 0.44, 0.10, 0.55, (at[0], at[1] + 0.18, at[2] + 0.47))
    parts.append(b)
    h = kit.make_box(f"{name}_head", 0.22, 0.08, 0.16, (at[0], at[1] + 0.18, at[2] + 1.02))
    parts.append(h)
    s1 = make_cylinder(f"{name}_stalk1", 0.01, 0.08, segs=6, at=(at[0] - 0.06, at[1] + 0.18, at[2] + 0.95))
    s2 = make_cylinder(f"{name}_stalk2", 0.01, 0.08, segs=6, at=(at[0] + 0.06, at[1] + 0.18, at[2] + 0.95))
    parts.extend([s1, s2])
    p = kit.make_box(f"{name}_pedestal", 0.32, 0.32, 0.35, (at[0], at[1], at[2]))
    parts.append(p)
    return parts


def main():
    kit.reset_scene()
    img = paint_transit_van_atlas()
    mat = material_for(img, "mat_transit_van")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # High-Poly (~3000 Tris) British Ford Transit Van Architecture:
    # Length (Y): 5.35m (Front bumper: -2.65m, Rear bumper: +2.70m)
    # Width (X):  2.04m (-1.02m to +1.02m)
    # Height (Z): 2.30m (Ground: 0.0m to Roof: 2.30m)
    # =========================================================================

    # 1. Main Cargo Box Body (Y: -0.70m to +2.65m, Height: 1.80m, Z: 0.45m to 2.25m)
    register_box("MainCargoBody", 2.04, 3.35, 1.80, (0.0, 0.975, 0.45),
                 front=R_BODY_WHITE, sides=R_BODY_WHITE, back=R_BODY_WHITE, top=R_BODY_WHITE)

    # Cargo Roof Cap (Beveled top)
    register_box("CargoRoofCap", 1.96, 3.35, 0.05, (0.0, 0.975, 2.25),
                 front=R_BODY_WHITE, sides=R_BODY_WHITE, back=R_BODY_WHITE, top=R_BODY_WHITE)

    # 5 Longitudinal Roof Reinforcement Ribs
    for ri in range(5):
        rx = -0.70 + ri * 0.35
        register_box(f"RoofRib_{ri}", 0.04, 3.20, 0.03, (rx, 0.975, 2.30),
                     front=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)

    # 2. Side Panel Recesses & Sliding Door Track
    for pi in range(3):
        py = -0.10 + pi * 0.95
        register_box(f"SideRecess_L_{pi}", 0.03, 0.80, 0.90, (-1.03, py, 0.95),
                     front=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)
        register_box(f"SideRecess_R_{pi}", 0.03, 0.80, 0.90, (1.03, py, 0.95),
                     front=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)

    # Sliding Door Outer Rail Guide on Passenger Side (+X)
    register_box("SlidingDoorRail", 0.04, 2.20, 0.04, (1.03, 0.80, 1.25),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("SlidingDoorHandle", 0.04, 0.16, 0.05, (1.04, 0.25, 1.15),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Side Rub Protection Strips
    register_box("SideRubStrip_L", 0.03, 4.80, 0.08, (-1.03, 0.0, 0.65),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("SideRubStrip_R", 0.03, 4.80, 0.08, (1.03, 0.0, 0.65),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3. Front Cab Structure (Y: -1.45m to -0.70m, Z: 0.45m to 2.30m)
    register_box("CabMainStructure", 2.02, 0.75, 1.80, (0.0, -1.075, 0.45),
                 front=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)

    # Cab Roof Cap
    register_box("CabRoofCap", 1.94, 0.75, 0.05, (0.0, -1.075, 2.25),
                 front=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)

    # Side Cab Windows (Driver & Passenger)
    register_box("CabWindow_L", 0.04, 0.65, 0.65, (-1.02, -1.075, 1.40),
                 front=R_GLASS_TINT, sides=R_GLASS_TINT, top=R_GLASS_TINT)
    register_box("CabWindow_R", 0.04, 0.65, 0.65, (1.02, -1.075, 1.40),
                 front=R_GLASS_TINT, sides=R_GLASS_TINT, top=R_GLASS_TINT)

    # Cab Door Handles
    register_box("CabDoorHandle_L", 0.04, 0.15, 0.04, (-1.03, -0.90, 1.15),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("CabDoorHandle_R", 0.04, 0.15, 0.04, (1.03, -0.90, 1.15),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4. Seamless Aerodynamic Sloped Windshield & Bonnet
    # Sloped Windshield (Y: -1.85m to -1.45m, Z: 1.15m to 2.25m)
    windshield = make_sloped_cowl("WindshieldSloped", w_rear=1.98, w_front=1.94,
                                  y_rear=-1.45, y_front=-1.85,
                                  z_rear_btm=0.45, z_rear_top=2.25,
                                  z_front_btm=0.45, z_front_top=1.15)
    windshield.data.materials.append(mat)
    # The sloped outer surface has normal facing partly in -Y and partly +Z
    kit.map_faces_to_region(windshield, R_GLASS_TINT, S, only=lambda f: f.normal.y < -0.2 and f.normal.z > 0.1)
    kit.map_faces_to_region(windshield, R_BODY_WHITE, S, only=lambda f: not (f.normal.y < -0.2 and f.normal.z > 0.1))
    parts.append(windshield)

    # 2x Windshield Wipers
    for wi, wx in enumerate([-0.45, 0.25]):
        wiper = register_box(f"WiperArm_{wi}", 0.025, 0.48, 0.02, (wx, -1.65, 1.55),
                             front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        wiper.rotation_euler = (math.radians(-25), 0, math.radians(15))

    # Sloped Bonnet / Hood (Y: -2.60m to -1.85m, Z: 0.85m to 1.15m)
    bonnet = make_sloped_cowl("BonnetSloped", w_rear=1.98, w_front=1.92,
                              y_rear=-1.85, y_front=-2.60,
                              z_rear_btm=0.45, z_rear_top=1.15,
                              z_front_btm=0.45, z_front_top=0.85)
    bonnet.data.materials.append(mat)
    kit.map_faces_to_region(bonnet, R_BODY_WHITE, S)
    parts.append(bonnet)

    # 5. Commercial Wing Mirrors (Mounted to A-Pillars at Y: -1.50m)
    for mi, (mx, is_l) in enumerate([(-1.08, True), (1.08, False)]):
        stalk = make_cylinder(f"MirrorStalk_{mi}", 0.02, 0.12, segs=8, at=(mx * 0.94, -1.50, 1.40))
        stalk.rotation_euler = (0, math.radians(90 if is_l else -90), 0)
        stalk.data.materials.append(mat)
        kit.map_faces_to_region(stalk, R_BUMPER_BLACK, S)
        parts.append(stalk)

        register_box(f"MirrorHousing_{mi}", 0.08, 0.16, 0.28, (mx, -1.50, 1.40),
                     front=R_GLASS_TINT, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Side Wing Indicator Repeaters (Amber)
    for si, sx in enumerate([-1.03, 1.03]):
        register_box(f"SideRepeater_{si}", 0.02, 0.08, 0.04, (sx, -2.15, 0.95),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 6. Detailed Interior: Seats, Steering Wheel & Dashboard
    driver_seats = make_driver_seat("DriverSeat", at=(0.48, -1.15, 0.45))
    for s in driver_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    pass_seats = make_driver_seat("PassengerSeat", at=(-0.42, -1.15, 0.45))
    for s in pass_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    # Dashboard
    register_box("DashboardMain", 1.80, 0.45, 0.28, (0.0, -1.55, 0.95),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Steering Wheel
    steer_ring = make_cylinder("SteeringWheelRing", 0.18, 0.03, segs=12, at=(0.48, -1.40, 1.15))
    steer_ring.rotation_euler = (math.radians(-50), 0, 0)
    steer_ring.data.materials.append(mat)
    kit.map_faces_to_region(steer_ring, R_BUMPER_BLACK, S)
    parts.append(steer_ring)

    # 7. Front Fascia, Integrated Flush Headlights, Grille & Bumper (Y: -2.62m)
    # Front Radiator Grille (Center)
    register_box("FrontGrille", 1.10, 0.04, 0.32, (0.0, -2.62, 0.55),
                 front=R_FRONT_GRILLE, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3D Chrome Ford Emblem Plinth
    emblem = make_cylinder("FordEmblemBadge", 0.07, 0.02, segs=16, at=(0.0, -2.64, 0.72))
    emblem.rotation_euler = (math.radians(90), 0, 0)
    emblem.data.materials.append(mat)
    kit.map_faces_to_region(emblem, R_FRONT_GRILLE, S)
    parts.append(emblem)

    # Left & Right Headlight Assemblies (Flush next to grille)
    for hi, (hx, is_l) in enumerate([(-0.76, True), (0.76, False)]):
        register_box(f"Headlight_{hi}", 0.38, 0.04, 0.28, (hx, -2.62, 0.57),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_WHITE)

    # Front Bumper Main Bar (Full width across front)
    register_box("FrontBumperMain", 2.04, 0.22, 0.30, (0.0, -2.62, 0.25),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK, bottom=R_BUMPER_BLACK)

    # Lower Air Intake Grille
    register_box("FrontLowerIntake", 1.10, 0.04, 0.10, (0.0, -2.73, 0.22),
                 front=R_FRONT_GRILLE, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 2x Fog Light Pods in Bumper
    register_box("FogLight_L", 0.16, 0.03, 0.10, (-0.68, -2.73, 0.32),
                 front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("FogLight_R", 0.16, 0.03, 0.10, (0.68, -2.73, 0.32),
                 front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Front UK Number Plate ("BD24 VNN" White)
    register_box("FrontNumberPlate", 0.52, 0.03, 0.12, (0.0, -2.74, 0.34),
                 front=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 8. Rear End, Barn Doors & Rear Roof Ladder (Y: +2.65m)
    # Rear Split Barn Doors
    register_box("RearDoor_L", 0.98, 0.04, 1.45, (-0.50, 2.66, 0.60),
                 back=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)
    register_box("RearDoor_R", 0.98, 0.04, 1.45, (0.50, 2.66, 0.60),
                 back=R_BODY_WHITE, sides=R_BODY_WHITE, top=R_BODY_WHITE)

    # Rear Door Grab Handle & Lock
    register_box("RearDoorHandle", 0.05, 0.05, 0.18, (0.08, 2.69, 1.25),
                 back=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4x Door Hinges
    for hi, (hx, hy, hz) in enumerate([(-0.99, 2.66, 1.85), (-0.99, 2.66, 0.85),
                                       ( 0.99, 2.66, 1.85), ( 0.99, 2.66, 0.85)]):
        register_box(f"RearHinge_{hi}", 0.06, 0.04, 0.08, (hx, hy, hz),
                     back=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3D Rear Roof Access Ladder on Passenger Barn Door (+X)
    for li, lz in enumerate([0.70, 0.95, 1.20, 1.45, 1.70, 1.95]):
        rung = make_cylinder(f"LadderRung_{li}", 0.015, 0.32, segs=8, at=(0.55, 2.72, lz))
        rung.rotation_euler = (0, math.radians(90), 0)
        rung.data.materials.append(mat)
        kit.map_faces_to_region(rung, R_BUMPER_BLACK, S)
        parts.append(rung)

    for ri, rx in enumerate([0.38, 0.72]):
        l_rail = make_cylinder(f"LadderRail_{ri}", 0.018, 1.50, segs=8, at=(rx, 2.72, 0.65))
        l_rail.data.materials.append(mat)
        kit.map_faces_to_region(l_rail, R_BUMPER_BLACK, S)
        parts.append(l_rail)

    # High-Mount Third Brake Light
    register_box("HighBrakeLight", 0.32, 0.04, 0.06, (0.0, 2.67, 2.12),
                 back=R_TAILLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_WHITE)

    # Vertical Rear Tail Light Clusters (Mounted on D-pillars)
    register_box("Taillight_L", 0.16, 0.05, 0.72, (-0.95, 2.66, 1.05),
                 back=R_TAILLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("Taillight_R", 0.16, 0.05, 0.72, (0.95, 2.66, 1.05),
                 back=R_TAILLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Rear Step Bumper
    register_box("RearStepBumper", 2.04, 0.24, 0.22, (0.0, 2.74, 0.38),
                 back=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK, bottom=R_BUMPER_BLACK)

    # Rear UK Number Plate ("BD24 VNN" Yellow)
    register_box("RearNumberPlate", 0.52, 0.03, 0.12, (-0.35, 2.70, 0.95),
                 back=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 9. Undercarriage, Chassis Rails & Mudflaps
    register_box("ChassisRail_L", 0.14, 4.80, 0.18, (-0.60, 0.10, 0.38),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("ChassisRail_R", 0.14, 4.80, 0.18, (0.60, 0.10, 0.38),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Exhaust Muffler & Chrome Tailpipe
    register_box("ExhaustMuffler", 0.24, 0.65, 0.16, (-0.45, 1.40, 0.32),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    tailpipe = make_cylinder("ExhaustTailpipe", 0.035, 0.35, segs=10, at=(-0.55, 2.05, 0.28))
    tailpipe.rotation_euler = (math.radians(90), 0, 0)
    tailpipe.data.materials.append(mat)
    kit.map_faces_to_region(tailpipe, R_BUMPER_BLACK, S)
    parts.append(tailpipe)

    # 4 Sleek Mudflaps behind wheels
    for mfi, (mfx, is_l) in enumerate([(-0.98, True), (0.98, False)]):
        register_box(f"FrontMudflap_{mfi}", 0.20, 0.02, 0.22, (mfx, -1.30, 0.20),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)
        register_box(f"RearMudflap_{mfi}", 0.20, 0.02, 0.24, (mfx, 2.05, 0.18),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)

    # 10. 4x High-Detail 3D Wheels (~440 Tris each = ~1,760 Tris)
    wheel_coords = [
        ("Wheel_FL", -0.92, -1.75, True),
        ("Wheel_FR",  0.92, -1.75, False),
        ("Wheel_RL", -0.92,  1.60, True),
        ("Wheel_RR",  0.92,  1.60, False),
    ]

    for w_name, wx, wy, is_left in wheel_coords:
        wh = make_wheel_assembly(w_name, radius=0.38, width=0.22, segs=24, at=(wx, wy, 0.38), is_left=is_left)
        wh.rotation_euler = (0, math.radians(90), 0)
        wh.data.materials.append(mat)
        
        kit.map_faces_to_region(wh, R_WHEEL_TIRE, S, only=lambda f: f.normal.z > 0.3 or f.normal.z < -0.3 or abs(f.normal.y) > 0.3)
        kit.map_faces_to_region(wh, R_WHEEL_RIM, S, only=lambda f: (f.normal.x > 0.4 if is_left else f.normal.x < -0.4))
        parts.append(wh)

        # 3D Brake Caliper & Disc
        disc = make_cylinder(f"BrakeDisc_{w_name}", 0.22, 0.04, segs=12, at=(wx * 0.82, wy, 0.38))
        disc.rotation_euler = (0, math.radians(90), 0)
        disc.data.materials.append(mat)
        kit.map_faces_to_region(disc, R_WHEEL_RIM, S)
        parts.append(disc)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Vehicle_Transit_Van")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "vehicle_transit_van_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "vehicle_transit_van.glb"
    kit.export_glb(glb_path, [shell])

    # Copy output to Assets/3DModels/Vehicles
    try:
        ASSETS_VEHICLES_DIR.mkdir(parents=True, exist_ok=True)
        dest_glb = ASSETS_VEHICLES_DIR / "vehicle_transit_van.glb"
        shutil.copy2(glb_path, dest_glb)
        print(f"[vehicle_transit_van] deployed to {dest_glb}")
    except Exception as e:
        print(f"[vehicle_transit_van] note: {e}")

    print("[vehicle_transit_van] generation complete.")


if __name__ == "__main__":
    main()
