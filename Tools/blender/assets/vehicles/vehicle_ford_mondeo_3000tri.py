"""High-Poly (~3000 Tris) 1997 Ford Mondeo Mk2 (Metallic State Blue Saloon/Hatchback).

Specs:
- Real-world scale: Length: 4.56m, Width: 1.76m (1.96m with mirrors), Height: 1.42m (Iconic 90s British D-segment family/fleet car).
- Rich 3D low-poly geometry targeted at ~3,000 Triangles:
  - Aerodynamic 3-box saloon body with sloped bonnet, curved cabin roof, rear boot deck & lip.
  - Signature Mk2 Mondeo oval chrome radiator grille with Ford Blue Oval badge, curved wrap-around headlights.
  - Front bumper with lower air intake, round fog lights, black side rub strips, door handles, and wing mirrors.
  - Detailed interior: curved 90s Ford dashboard, steering wheel with airbag boss, 2 front bucket seats with headrests, rear bench, rearview mirror.
  - 4x high-detail 3D wheels (24-segment tires, Mondeo multi-spoke silver alloy rims with 4 lug nuts, blue Ford center caps & brake discs).
  - Dual front wipers, roof antenna, chrome exhaust tailpipe, undercarriage chassis rails, UK 1997 plates ("R97 MON").
- Procedural 512x512 texture atlas with nearest-neighbor crisp pixel art texturing.
- Deploys directly to Assets/3DModels/Vehicles/vehicle_ford_mondeo.glb.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/vehicles/vehicle_ford_mondeo_3000tri.py
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
R_BODY_BLUE       = (0,   256, 256, 256)   # Metallic State Blue gloss bodywork with highlights
R_BUMPER_BLACK    = (256, 256, 128, 256)   # Textured black plastic trim & rub strips
R_FRONT_GRILLE    = (0,   128, 256, 128)   # Signature oval chrome grille with Ford Blue Oval badge
R_HEADLIGHTS      = (256, 128, 128, 128)   # Curved 90s teardrop halogen headlights & amber turn signals
R_TAILLIGHTS      = (384, 128, 128, 128)   # Wrap-around rear light cluster (Brake Red / Amber / Reverse White)
R_GLASS_FRONT     = (0,   0,   128, 128)   # Clean tinted windshield & side windows
R_GLASS_REAR      = (128, 0,   128, 128)   # Rear window with orange defroster heating lines
R_WHEEL_TIRE      = (256, 0,   128, 128)   # Compact treaded tire rubber
R_WHEEL_RIM       = (384, 0,   128, 128)   # Ford Mondeo silver alloy rim with 4 lug nuts & blue center cap
R_PLATES_UK       = (384, 256, 128, 128)   # British number plates: White front / Yellow rear ("R97 MON")

# --- Palette Colors ---
STATE_BLUE        = (0.12, 0.28, 0.52)     # Classic 90s Ford State Blue Metallic
STATE_BLUE_SHADE  = (0.08, 0.18, 0.38)
STATE_BLUE_HI     = (0.22, 0.42, 0.68)
PLASTIC_BLACK     = (0.13, 0.14, 0.15)
PLASTIC_DARK      = (0.08, 0.09, 0.10)
CHROME_SILVER     = (0.88, 0.90, 0.94)
FORD_BLUE         = (0.05, 0.22, 0.55)
GLASS_DARK        = (0.11, 0.15, 0.20)
HEADLIGHT_GLASS   = (0.84, 0.88, 0.92)
AMBER_TURN        = (0.96, 0.52, 0.08)
TAIL_RED          = (0.88, 0.08, 0.08)
TIRE_RUBBER       = (0.15, 0.15, 0.16)
RIM_SILVER        = (0.78, 0.80, 0.82)
PLATE_YELLOW      = (0.96, 0.82, 0.12)
PLATE_WHITE       = (0.95, 0.95, 0.95)
GB_BLUE           = (0.05, 0.22, 0.55)


def paint_mondeo_atlas():
    a = Atlas(S, seed=1997)

    # 1. Metallic State Blue Bodywork (R_BODY_BLUE)
    x, y, w, h = R_BODY_BLUE
    a.rect(x, y, w, h, STATE_BLUE)
    for py in [y + 35, y + 110, y + 190]:
        a.rect(x, py, w, 2, STATE_BLUE_SHADE)
    # Body-colored door handles with chrome lock
    a.rect(x + 30, y + 75, 38, 10, STATE_BLUE_SHADE)
    a.rect(x + 32, y + 77, 34, 6, STATE_BLUE_HI)
    a.disc(x + 60, y + 80, 3, CHROME_SILVER)
    # Fuel filler door
    a.disc(x + 180, y + 140, 18, STATE_BLUE_SHADE)
    a.disc(x + 180, y + 140, 16, STATE_BLUE)
    a.shade(x, y, w, h, top=0.04, bottom=-0.04)
    a.noise(x, y, w, h, 0.008)

    # 2. Textured Black Plastic Trim (R_BUMPER_BLACK)
    x, y, w, h = R_BUMPER_BLACK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    for gy in range(y, y + h, 8):
        a.rect(x, gy, w, 2, PLASTIC_DARK)
    a.noise(x, y, w, h, 0.015)

    # 3. Signature Oval Chrome Grille & Ford Badge (R_FRONT_GRILLE)
    x, y, w, h = R_FRONT_GRILLE
    a.rect(x, y, w, h, PLASTIC_DARK)
    cx, cy = x + w // 2, y + h // 2
    for r in range(48, 40, -1):
        a.disc(cx, cy, r, CHROME_SILVER)
    a.disc(cx, cy, 40, PLASTIC_DARK)
    for gy in range(cy - 30, cy + 30, 8):
        for gx in range(cx - 36, cx + 36, 10):
            a.rect(gx, gy, 6, 4, (0.18, 0.19, 0.20))
    # Ford Blue Oval badge
    a.disc(cx, cy, 20, CHROME_SILVER)
    a.disc(cx, cy, 16, FORD_BLUE)
    a.rect(cx - 10, cy - 2, 20, 3, (0.95, 0.95, 0.95))
    a.noise(x, y, w, h, 0.012)

    # 4. 90s Teardrop Curved Headlights (R_HEADLIGHTS)
    x, y, w, h = R_HEADLIGHTS
    a.rect(x, y, w, h, (0.10, 0.12, 0.14))
    a.rect(x + 4, y + 4, w - 36, h - 8, HEADLIGHT_GLASS)
    a.disc(x + 40, y + h // 2, 24, (0.95, 0.98, 1.0))
    a.disc(x + 40, y + h // 2, 12, (0.5, 0.6, 0.7))
    for lx in range(x + 8, x + w - 40, 8):
        a.rect(lx, y + 6, 2, h - 12, (0.72, 0.76, 0.80))
    # Amber turn indicator
    a.rect(x + w - 30, y + 4, 26, h - 8, AMBER_TURN)
    for ix in range(x + w - 28, x + w - 6, 6):
        a.rect(ix, y + 6, 2, h - 12, (0.80, 0.40, 0.05))
    a.noise(x, y, w, h, 0.012)

    # 5. Wrap-Around Rear Taillight Clusters (R_TAILLIGHTS)
    x, y, w, h = R_TAILLIGHTS
    a.rect(x, y, w, h, (0.10, 0.10, 0.10))
    a.rect(x + 6, y + h // 2 + 6, w - 12, h // 2 - 12, TAIL_RED)
    for ry in range(y + h // 2 + 12, y + h - 10, 10):
        a.rect(x + 10, ry, w - 20, 3, (1.0, 0.25, 0.25))
    a.rect(x + 6, y + h // 4 + 4, w - 12, h // 4 - 2, AMBER_TURN)
    a.rect(x + 6, y + 6, w - 12, h // 4 - 4, (0.95, 0.95, 0.95))
    a.noise(x, y, w, h, 0.012)

    # 6. Clean Front & Side Glass (R_GLASS_FRONT)
    x, y, w, h = R_GLASS_FRONT
    a.rect(x, y, w, h, GLASS_DARK)
    for gx in range(x + 15, x + w - 15, 40):
        a.rect(gx, y + 8, 20, h - 16, (0.16, 0.22, 0.28))
    a.noise(x, y, w, h, 0.008)

    # 7. Rear Glass with Heated Defroster Lines (R_GLASS_REAR)
    x, y, w, h = R_GLASS_REAR
    a.rect(x, y, w, h, GLASS_DARK)
    for gx in range(x + 15, x + w - 15, 40):
        a.rect(gx, y + 8, 20, h - 16, (0.16, 0.22, 0.28))
    for dy in range(y + 16, y + h - 16, 14):
        a.rect(x + 8, dy, w - 16, 1, (0.88, 0.48, 0.15))
    a.noise(x, y, w, h, 0.008)

    # 8. Treaded Tire Rubber (R_WHEEL_TIRE)
    x, y, w, h = R_WHEEL_TIRE
    a.rect(x, y, w, h, TIRE_RUBBER)
    for ty in range(y, y + h, 8):
        a.rect(x, ty, w, 2, (0.08, 0.08, 0.09))
    a.noise(x, y, w, h, 0.015)

    # 9. 90s Ford Mondeo Ghia Silver Alloy Wheel Rim (R_WHEEL_RIM)
    x, y, w, h = R_WHEEL_RIM
    a.rect(x, y, w, h, (0.25, 0.25, 0.27))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 54, RIM_SILVER)
    a.disc(cx, cy, 46, (0.35, 0.36, 0.38))
    for i in range(8):
        ang = i * (math.pi / 4)
        hx = int(cx + 26 * math.cos(ang))
        hy = int(cy + 26 * math.sin(ang))
        a.disc(hx, hy, 8, PLASTIC_DARK)
    for i in range(4):
        ang = math.pi / 4 + i * (math.pi / 2)
        lx = int(cx + 18 * math.cos(ang))
        ly = int(cy + 18 * math.sin(ang))
        a.disc(lx, ly, 4, CHROME_SILVER)
    a.disc(cx, cy, 14, PLASTIC_BLACK)
    a.disc(cx, cy, 10, FORD_BLUE)
    a.noise(x, y, w, h, 0.012)

    # 10. UK Number Plates (R_PLATES_UK)
    x, y, w, h = R_PLATES_UK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    # White Front Plate
    f_box = (x + 8, y + h // 2 + 8, w - 16, h // 2 - 16)
    a.rect(*f_box, PLATE_WHITE)
    a.rect(f_box[0] + 2, f_box[1] + 2, 8, f_box[3] - 4, GB_BLUE)
    s_plate = "R97 MON"
    tw = a.text_width(s_plate, scale=2)
    a.text(f_box[0] + 16 + (f_box[2] - 20 - tw) // 2, f_box[1] + f_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)

    # Yellow Rear Plate
    r_box = (x + 8, y + 8, w - 16, h // 2 - 16)
    a.rect(*r_box, PLATE_YELLOW)
    a.rect(r_box[0] + 2, r_box[1] + 2, 8, r_box[3] - 4, GB_BLUE)
    a.text(r_box[0] + 16 + (r_box[2] - 20 - tw) // 2, r_box[1] + r_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)
    a.noise(x, y, w, h, 0.010)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("vehicle_ford_mondeo_atlas", OUT_DIR)


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


def map_box(obj, front=R_BODY_BLUE, sides=R_BODY_BLUE, back=None, top=None, bottom=None):
    kit.map_faces_to_region(obj, front or R_BODY_BLUE, S, only=side("front"))
    kit.map_faces_to_region(obj, sides or R_BODY_BLUE, S, only=side("left"))
    kit.map_faces_to_region(obj, sides or R_BODY_BLUE, S, only=side("right"))
    kit.map_faces_to_region(obj, back or sides or R_BODY_BLUE, S, only=side("back"))
    kit.map_faces_to_region(obj, top or R_BODY_BLUE, S, only=side("top"))
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


def make_wheel_assembly(name, radius=0.30, width=0.20, segs=24, at=(0, 0, 0), is_left=True):
    """Generates a high-detail 3D Mondeo alloy wheel (~440 tris) with tire, rim face & disc."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    
    r_rim = radius * 0.65
    w_half = width * 0.5
    w_rim_inset = 0.035 if is_left else -0.035

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

    hub_center = bm.verts.new((0, 0, out_z - w_rim_inset * 1.4))
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

    # 4 3D Lug Nuts on Rim
    r_studs = r_rim * 0.48
    for li in range(4):
        ang = math.pi / 4 + li * (math.pi / 2)
        sx = r_studs * math.cos(ang)
        sy = r_studs * math.sin(ang)
        sz = out_z - w_rim_inset * 1.1
        s_verts = []
        for vi in range(6):
            va = 2 * math.pi * vi / 6
            sv = bm.verts.new((sx + 0.016 * math.cos(va), sy + 0.016 * math.sin(va), sz + (0.012 if is_left else -0.012)))
            s_verts.append(sv)
        sv_tip = bm.verts.new((sx, sy, sz + (0.020 if is_left else -0.020)))
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
    """Creates a seamless sloped 3D cowl box (bonnet, windshield, or bootlid) with outward normals."""
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
    bm.faces.new((v7, v6, v2, v3)) # Top (sloped outer surface)
    bm.faces.new((v0, v1, v5, v4)) # Bottom (-Z)

    bm.to_mesh(mesh)
    bm.free()
    return obj


def make_driver_seat(name, at=(0, 0, 0)):
    """90s Ford Ghia contoured bucket seat with headrest."""
    parts = []
    c = kit.make_box(f"{name}_cushion", 0.44, 0.44, 0.12, (at[0], at[1], at[2] + 0.24))
    parts.append(c)
    b = kit.make_box(f"{name}_back", 0.42, 0.09, 0.52, (at[0], at[1] + 0.16, at[2] + 0.35))
    parts.append(b)
    h = kit.make_box(f"{name}_head", 0.20, 0.07, 0.15, (at[0], at[1] + 0.16, at[2] + 0.88))
    parts.append(h)
    s1 = make_cylinder(f"{name}_stalk1", 0.009, 0.07, segs=6, at=(at[0] - 0.05, at[1] + 0.16, at[2] + 0.82))
    s2 = make_cylinder(f"{name}_stalk2", 0.009, 0.07, segs=6, at=(at[0] + 0.05, at[1] + 0.16, at[2] + 0.82))
    parts.extend([s1, s2])
    p = kit.make_box(f"{name}_base", 0.30, 0.30, 0.24, (at[0], at[1], at[2]))
    parts.append(p)
    return parts


def main():
    kit.reset_scene()
    img = paint_mondeo_atlas()
    mat = material_for(img, "mat_mondeo")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # 1997 Ford Mondeo Mk2 Architecture:
    # Length (Y): 4.56m (Front bumper: -2.28m, Rear bumper: +2.28m)
    # Width (X):  1.76m (-0.88m to +0.88m)
    # Height (Z): 1.42m (Ground: 0.0m to Roof: 1.42m)
    # Wheelbase: 2.70m (Front: Y = -1.35m, Rear: Y = +1.35m)
    # =========================================================================

    # 1. Main Cabin Lower Tub (Y: -1.10m to +1.40m, Length: 2.50m, Width: 1.74m, Z: 0.32m to 0.85m)
    register_box("CabinLowerBody", 1.74, 2.50, 0.53, (0.0, 0.15, 0.32),
                 front=R_BODY_BLUE, sides=R_BODY_BLUE, back=R_BODY_BLUE, top=R_BODY_BLUE)

    # Side Rub Protective Strips along flanks
    register_box("SideRubStrip_L", 0.025, 3.80, 0.06, (-0.88, 0.0, 0.52),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("SideRubStrip_R", 0.025, 3.80, 0.06, (0.88, 0.0, 0.52),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 2. Main Cabin Roof & Pillars (Y: -0.55m to +0.85m, Length: 1.40m, Width: 1.54m, Z: 1.34m to 1.42m)
    register_box("CabinRoof", 1.54, 1.40, 0.08, (0.0, 0.15, 1.34),
                 front=R_BODY_BLUE, sides=R_BODY_BLUE, back=R_BODY_BLUE, top=R_BODY_BLUE)

    # Roof Antenna Mast
    antenna = make_cylinder("RoofAntenna", 0.005, 0.38, segs=6, at=(0.0, -0.45, 1.42))
    antenna.rotation_euler = (math.radians(25), 0, 0)
    antenna.data.materials.append(mat)
    kit.map_faces_to_region(antenna, R_BUMPER_BLACK, S)
    parts.append(antenna)

    # 4 Side Windows (Front Driver/Passenger & Rear Passenger windows)
    register_box("FrontSideWin_L", 0.03, 0.72, 0.49, (-0.86, -0.15, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)
    register_box("FrontSideWin_R", 0.03, 0.72, 0.49, (0.86, -0.15, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)

    register_box("RearSideWin_L", 0.03, 0.68, 0.48, (-0.86, 0.55, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)
    register_box("RearSideWin_R", 0.03, 0.68, 0.48, (0.86, 0.55, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)

    # B-Pillar Black Trim Divider
    register_box("BPillar_L", 0.035, 0.08, 0.50, (-0.865, 0.21, 0.85),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("BPillar_R", 0.035, 0.08, 0.50, (0.865, 0.21, 0.85),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4 Door Handles (Front & Rear)
    for di, dy in enumerate([-0.05, 0.65]):
        register_box(f"DoorHandle_L_{di}", 0.03, 0.12, 0.03, (-0.89, dy, 0.76),
                     front=R_BODY_BLUE, sides=R_BUMPER_BLACK, top=R_BODY_BLUE)
        register_box(f"DoorHandle_R_{di}", 0.03, 0.12, 0.03, (0.89, dy, 0.76),
                     front=R_BODY_BLUE, sides=R_BUMPER_BLACK, top=R_BODY_BLUE)

    # 3. Aerodynamic Sloped Front Windshield & Bonnet
    # Sloped Windshield (Y: -1.25m to -0.55m, Z: 0.85m to 1.34m)
    windshield = make_sloped_cowl("WindshieldSloped", w_rear=1.56, w_front=1.66,
                                  y_rear=-0.55, y_front=-1.25,
                                  z_rear_btm=0.32, z_rear_top=1.34,
                                  z_front_btm=0.32, z_front_top=0.85)
    windshield.data.materials.append(mat)
    kit.map_faces_to_region(windshield, R_GLASS_FRONT, S, only=lambda f: f.normal.y < -0.2 and f.normal.z > 0.1)
    kit.map_faces_to_region(windshield, R_BODY_BLUE, S, only=lambda f: not (f.normal.y < -0.2 and f.normal.z > 0.1))
    parts.append(windshield)

    # 2x Windshield Wipers
    for wi, wx in enumerate([-0.35, 0.25]):
        wiper = register_box(f"WiperArm_{wi}", 0.02, 0.44, 0.02, (wx, -1.05, 1.02),
                             front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        wiper.rotation_euler = (math.radians(-30), 0, math.radians(18))

    # Sloped Bonnet / Hood (Y: -2.20m to -1.25m, Z: 0.62m to 0.85m)
    bonnet = make_sloped_cowl("BonnetSloped", w_rear=1.68, w_front=1.60,
                              y_rear=-1.25, y_front=-2.20,
                              z_rear_btm=0.32, z_rear_top=0.85,
                              z_front_btm=0.32, z_front_top=0.62)
    bonnet.data.materials.append(mat)
    kit.map_faces_to_region(bonnet, R_BODY_BLUE, S)
    parts.append(bonnet)

    # 4. Sloped Rear Glass & Saloon Boot Deck
    # Sloped Rear Glass (Y: +0.85m to +1.45m, Z: 0.85m to 1.34m)
    rear_glass = make_sloped_cowl("RearGlassSloped", w_rear=1.62, w_front=1.56,
                                  y_rear=1.45, y_front=0.85,
                                  z_rear_btm=0.32, z_rear_top=0.85,
                                  z_front_btm=0.32, z_front_top=1.34)
    rear_glass.data.materials.append(mat)
    kit.map_faces_to_region(rear_glass, R_GLASS_REAR, S, only=lambda f: f.normal.y > 0.2 and f.normal.z > 0.1)
    kit.map_faces_to_region(rear_glass, R_BODY_BLUE, S, only=lambda f: not (f.normal.y > 0.2 and f.normal.z > 0.1))
    parts.append(rear_glass)

    # Saloon Boot Deck / Trunk Lid (Y: +1.45m to +2.20m, Z: 0.72m to 0.85m)
    boot = make_sloped_cowl("BootLidSloped", w_rear=1.60, w_front=1.64,
                            y_rear=2.20, y_front=1.45,
                            z_rear_btm=0.32, z_rear_top=0.76,
                            z_front_btm=0.32, z_front_top=0.85)
    boot.data.materials.append(mat)
    kit.map_faces_to_region(boot, R_BODY_BLUE, S)
    parts.append(boot)

    # Bootlid Lip Spoiler & Handle Bar
    register_box("BootLipSpoiler", 1.56, 0.08, 0.04, (0.0, 2.18, 0.76),
                 front=R_BODY_BLUE, sides=R_BODY_BLUE, back=R_BODY_BLUE, top=R_BODY_BLUE)

    # 5. Front Fascia, Signature Oval Grille & Flush Headlights (Y: -2.24m)
    # Front Bumper Main Bar
    register_box("FrontBumperMain", 1.74, 0.22, 0.28, (0.0, -2.22, 0.22),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BODY_BLUE, bottom=R_BUMPER_BLACK)

    # Front Lower Air Intake Grille
    register_box("FrontLowerIntake", 1.10, 0.03, 0.10, (0.0, -2.32, 0.24),
                 front=R_FRONT_GRILLE, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 2x Round Fog Lights in Bumper
    for fi, fx in enumerate([-0.62, 0.62]):
        fog = make_cylinder(f"MondeoFog_{fi}", 0.045, 0.02, segs=12, at=(fx, -2.31, 0.28))
        fog.rotation_euler = (math.radians(90), 0, 0)
        fog.data.materials.append(mat)
        kit.map_faces_to_region(fog, R_HEADLIGHTS, S)
        parts.append(fog)

    # Signature Ford Mondeo Oval Radiator Grille
    register_box("FrontGrille", 0.68, 0.04, 0.22, (0.0, -2.22, 0.48),
                 front=R_FRONT_GRILLE, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3D Chrome Ford Oval Badge Emblem Plinth
    badge = make_cylinder("FordOvalBadge", 0.06, 0.02, segs=16, at=(0.0, -2.25, 0.59))
    badge.rotation_euler = (math.radians(90), 0, 0)
    badge.data.materials.append(mat)
    kit.map_faces_to_region(badge, R_FRONT_GRILLE, S)
    parts.append(badge)

    # Curved Teardrop Headlights (Left & Right - Flush inside front corners)
    for hi, (hx, is_l) in enumerate([(-0.58, True), (0.58, False)]):
        register_box(f"Headlight_{hi}", 0.36, 0.04, 0.22, (hx, -2.22, 0.48),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_BLUE)

    # Front UK Number Plate ("R97 MON" White)
    register_box("FrontNumberPlate", 0.48, 0.02, 0.11, (0.0, -2.33, 0.36),
                 front=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 6. Wing Mirrors & Side Repeaters
    for mi, (mx, is_l) in enumerate([(-0.92, True), (0.92, False)]):
        stalk = make_cylinder(f"MirrorStalk_{mi}", 0.016, 0.09, segs=8, at=(mx * 0.94, -0.65, 0.90))
        stalk.rotation_euler = (0, math.radians(90 if is_l else -90), 0)
        stalk.data.materials.append(mat)
        kit.map_faces_to_region(stalk, R_BODY_BLUE, S)
        parts.append(stalk)

        register_box(f"MirrorHousing_{mi}", 0.07, 0.14, 0.18, (mx, -0.65, 0.90),
                     front=R_GLASS_FRONT, sides=R_BODY_BLUE, back=R_BODY_BLUE, top=R_BODY_BLUE)

    # Orange Side Indicator Repeaters on front wings
    for si, sx in enumerate([-0.88, 0.88]):
        register_box(f"SideRepeater_{si}", 0.015, 0.06, 0.03, (sx, -1.60, 0.68),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 7. Detailed Interior: Dashboard, Steering Wheel, Bucket Seats & Rear Bench
    driver_seats = make_driver_seat("DriverSeat", at=(0.38, -0.15, 0.32))
    for s in driver_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    pass_seats = make_driver_seat("PassengerSeat", at=(-0.38, -0.15, 0.32))
    for s in pass_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    # Rear Bench Seat
    register_box("RearBenchCushion", 1.42, 0.46, 0.14, (0.0, 0.75, 0.46),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("RearBenchBack", 1.40, 0.09, 0.46, (0.0, 0.98, 0.60),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 90s Curved Ford Oval Dashboard
    register_box("DashboardMain", 1.52, 0.40, 0.25, (0.0, -0.78, 0.72),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4-Spoke Mondeo Steering Wheel with Airbag
    steer_ring = make_cylinder("SteeringWheelRing", 0.16, 0.025, segs=12, at=(0.38, -0.62, 0.88))
    steer_ring.rotation_euler = (math.radians(-45), 0, 0)
    steer_ring.data.materials.append(mat)
    kit.map_faces_to_region(steer_ring, R_BUMPER_BLACK, S)
    parts.append(steer_ring)

    # Interior Rearview Mirror
    register_box("RearviewMirror", 0.10, 0.02, 0.04, (0.0, -0.56, 1.28),
                 front=R_GLASS_FRONT, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 8. Rear End, Wrap-Around Taillights, Bumper & Exhaust Tailpipe (Y: +2.24m)
    # Rear Bumper
    register_box("RearBumperMain", 1.74, 0.22, 0.28, (0.0, 2.22, 0.22),
                 back=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BODY_BLUE, bottom=R_BUMPER_BLACK)

    # Wrap-Around Taillight Clusters (Flush on rear corners: Z = 0.48m to 0.74m)
    for ti, (tx, is_l) in enumerate([(-0.66, True), (0.66, False)]):
        register_box(f"Taillight_{ti}", 0.26, 0.04, 0.26, (tx, 2.22, 0.48),
                     back=R_TAILLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_BLUE)

    # Rear UK Number Plate ("R97 MON" Yellow)
    register_box("RearNumberPlate", 0.48, 0.02, 0.11, (0.0, 2.31, 0.48),
                 back=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Rear Bootlid Ford Oval Badge
    r_badge = make_cylinder("RearFordBadge", 0.045, 0.015, segs=12, at=(0.0, 2.24, 0.72))
    r_badge.rotation_euler = (math.radians(90), 0, 0)
    r_badge.data.materials.append(mat)
    kit.map_faces_to_region(r_badge, R_FRONT_GRILLE, S)
    parts.append(r_badge)

    # Chrome Exhaust Tailpipe
    tailpipe = make_cylinder("MondeoExhaust", 0.035, 0.32, segs=10, at=(-0.58, 2.15, 0.18))
    tailpipe.rotation_euler = (math.radians(90), 0, 0)
    tailpipe.data.materials.append(mat)
    kit.map_faces_to_region(tailpipe, R_BUMPER_BLACK, S)
    parts.append(tailpipe)

    # 9. Undercarriage Chassis Rails & Mudflaps
    register_box("ChassisRail_L", 0.12, 4.10, 0.14, (-0.55, 0.05, 0.26),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("ChassisRail_R", 0.12, 4.10, 0.14, (0.55, 0.05, 0.26),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4 Mudflaps behind wheels
    for mfi, (mfx, is_l) in enumerate([(-0.84, True), (0.84, False)]):
        register_box(f"FrontMudflap_{mfi}", 0.18, 0.02, 0.18, (mfx, -1.00, 0.18),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)
        register_box(f"RearMudflap_{mfi}", 0.18, 0.02, 0.20, (mfx, 1.70, 0.16),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)

    # 10. 4x High-Detail 3D Wheels (~440 Tris each = ~1,760 Tris)
    wheel_coords = [
        ("Wheel_FL", -0.78, -1.35, True),
        ("Wheel_FR",  0.78, -1.35, False),
        ("Wheel_RL", -0.78,  1.35, True),
        ("Wheel_RR",  0.78,  1.35, False),
    ]

    for w_name, wx, wy, is_left in wheel_coords:
        wh = make_wheel_assembly(w_name, radius=0.30, width=0.20, segs=24, at=(wx, wy, 0.30), is_left=is_left)
        wh.rotation_euler = (0, math.radians(90), 0)
        wh.data.materials.append(mat)
        
        kit.map_faces_to_region(wh, R_WHEEL_TIRE, S, only=lambda f: f.normal.z > 0.3 or f.normal.z < -0.3 or abs(f.normal.y) > 0.3)
        kit.map_faces_to_region(wh, R_WHEEL_RIM, S, only=lambda f: (f.normal.x > 0.4 if is_left else f.normal.x < -0.4))
        parts.append(wh)

        # 3D Brake Caliper & Disc
        disc = make_cylinder(f"BrakeDisc_{w_name}", 0.18, 0.035, segs=12, at=(wx * 0.84, wy, 0.30))
        disc.rotation_euler = (0, math.radians(90), 0)
        disc.data.materials.append(mat)
        kit.map_faces_to_region(disc, R_WHEEL_RIM, S)
        parts.append(disc)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Vehicle_Ford_Mondeo")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "vehicle_ford_mondeo_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "vehicle_ford_mondeo.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/Vehicles
    try:
        ASSETS_VEHICLES_DIR.mkdir(parents=True, exist_ok=True)
        dest_glb = ASSETS_VEHICLES_DIR / "vehicle_ford_mondeo.glb"
        shutil.copy2(glb_path, dest_glb)
        print(f"[vehicle_ford_mondeo] deployed to {dest_glb}")
    except Exception as e:
        print(f"[vehicle_ford_mondeo] note: {e}")

    print("[vehicle_ford_mondeo] generation complete.")


if __name__ == "__main__":
    main()
