"""High-Poly (~3000 Tris) 1997 Fiat Cinquecento in Bright Broom Yellow (Giallo Ginestra).

Specs:
- Real-world scale: Length: 3.23m, Width: 1.50m (1.70m with mirrors), Height: 1.43m (Iconic 90s Italian 3-Door City Hatchback).
- Rich 3D low-poly geometry targeted at ~3,000 Triangles:
  - Compact boxy hatchback body with sloped front bonnet, rear tailgate with spoiler lip & rear wiper.
  - Flush 90s rectangular headlights with orange corner indicators, classic Fiat 5-slanted-bar front badge.
  - Sporting front bumper with round fog lights, black plastic bumpers with yellow inserts, black side rub strips.
  - Detailed interior visible through glass: dashboard binnacle, steering wheel, 2 front bucket seats with headrests, rear bench, rearview mirror.
  - 4x high-detail 3D wheels (24-segment tires, Sporting 4-spoke silver alloy rims with 4 lug nuts, center caps & brake discs).
  - Single front mono-wiper, roof antenna mast, sporty rear exhaust tailpipe, undercarriage chassis, UK 1997 plates ("P97 CINQ").
- Procedural 512x512 texture atlas with separate front and rear defroster glass textures.
- Deploys directly to Assets/3DModels/Vehicles/vehicle_fiat_cinquecento.glb.

Run: python Tools/blender/bpy_runner.py Tools/blender/assets/vehicles/vehicle_fiat_cinquecento_3000tri.py
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
R_BODY_YELLOW     = (0,   256, 256, 256)   # Bright Broom Yellow (Giallo Ginestra) gloss bodywork
R_BUMPER_BLACK    = (256, 256, 128, 256)   # Textured black plastic bumpers & rub strips
R_FRONT_GRILLE    = (0,   128, 256, 128)   # Slotted front intake with Fiat 5-slanted-bar chrome badge
R_HEADLIGHTS      = (256, 128, 128, 128)   # 90s rectangular glass headlights & wrap-around amber turn signals
R_TAILLIGHTS      = (384, 128, 128, 128)   # Vertical rear light cluster (Brake Red / Amber / Reverse White)
R_GLASS_FRONT     = (0,   0,   128, 128)   # Clean tinted windshield & side windows
R_GLASS_REAR      = (128, 0,   128, 128)   # Rear window with orange defroster heating lines
R_WHEEL_TIRE      = (256, 0,   128, 128)   # Compact treaded tire rubber
R_WHEEL_RIM       = (384, 0,   128, 128)   # 90s Fiat Sporting silver alloy rim with 4 lug bolts
R_PLATES_UK       = (384, 256, 128, 128)   # British number plates: White front / Yellow rear ("P97 CINQ")

# --- Palette Colors ---
BROOM_YELLOW      = (1.00, 0.88, 0.04)     # Bright Broom Yellow
BROOM_YELLOW_SHADE= (0.86, 0.74, 0.02)
PLASTIC_BLACK     = (0.13, 0.14, 0.15)
PLASTIC_DARK      = (0.08, 0.09, 0.10)
FIAT_CHROME       = (0.90, 0.92, 0.95)
GLASS_DARK        = (0.12, 0.16, 0.22)
HEADLIGHT_GLASS   = (0.84, 0.88, 0.92)
AMBER_TURN        = (0.96, 0.52, 0.08)
TAIL_RED          = (0.88, 0.08, 0.08)
TIRE_RUBBER       = (0.15, 0.15, 0.16)
RIM_SILVER        = (0.78, 0.80, 0.82)
PLATE_YELLOW      = (0.96, 0.82, 0.12)
PLATE_WHITE       = (0.95, 0.95, 0.95)
GB_BLUE           = (0.05, 0.22, 0.55)


def paint_cinquecento_atlas():
    a = Atlas(S, seed=1997)

    # 1. Bright Broom Yellow Bodywork (R_BODY_YELLOW)
    x, y, w, h = R_BODY_YELLOW
    a.rect(x, y, w, h, BROOM_YELLOW)
    for py in [y + 35, y + 110, y + 190]:
        a.rect(x, py, w, 2, BROOM_YELLOW_SHADE)
    # Black door handle & lock
    a.rect(x + 30, y + 75, 36, 12, PLASTIC_BLACK)
    a.disc(x + 56, y + 81, 3, FIAT_CHROME)
    # Fuel filler cap
    a.disc(x + 180, y + 140, 16, BROOM_YELLOW_SHADE)
    a.disc(x + 180, y + 140, 14, BROOM_YELLOW)
    a.disc(x + 180, y + 140, 3, PLASTIC_BLACK)
    a.shade(x, y, w, h, top=0.02, bottom=-0.03)
    a.noise(x, y, w, h, 0.006)

    # 2. Textured Black Plastic Trim (R_BUMPER_BLACK)
    x, y, w, h = R_BUMPER_BLACK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    for gy in range(y, y + h, 8):
        a.rect(x, gy, w, 2, PLASTIC_DARK)
    a.noise(x, y, w, h, 0.015)

    # 3. Front Grille & Fiat 5-Bar Badge (R_FRONT_GRILLE)
    x, y, w, h = R_FRONT_GRILLE
    a.rect(x, y, w, h, PLASTIC_DARK)
    for gy in range(y + 8, y + h - 8, 12):
        a.rect(x + 8, gy, w - 16, 5, (0.18, 0.19, 0.20))
    # Fiat 5 Slanted Chrome Bars emblem (// / / /)
    cx, cy = x + w // 2, y + h // 2
    for bi in range(5):
        bx = cx - 20 + bi * 10
        for row in range(16):
            a.rect(bx + row // 3, cy - 8 + row, 3, 1, FIAT_CHROME)
    a.noise(x, y, w, h, 0.012)

    # 4. Rectangular 90s Headlights & Fog Lights (R_HEADLIGHTS)
    x, y, w, h = R_HEADLIGHTS
    a.rect(x, y, w, h, (0.10, 0.12, 0.14))
    # Main headlight lens
    a.rect(x + 4, y + 4, w - 36, h - 8, HEADLIGHT_GLASS)
    a.disc(x + 36, y + h // 2, 22, (0.95, 0.98, 1.0))
    a.disc(x + 36, y + h // 2, 10, (0.5, 0.6, 0.7))
    for lx in range(x + 8, x + w - 40, 8):
        a.rect(lx, y + 6, 2, h - 12, (0.72, 0.76, 0.80))
    # Amber indicator corner
    a.rect(x + w - 30, y + 4, 26, h - 8, AMBER_TURN)
    for ix in range(x + w - 28, x + w - 6, 6):
        a.rect(ix, y + 6, 2, h - 12, (0.80, 0.40, 0.05))
    a.noise(x, y, w, h, 0.012)

    # 5. Vertical Rear Light Clusters (R_TAILLIGHTS)
    x, y, w, h = R_TAILLIGHTS
    a.rect(x, y, w, h, (0.10, 0.10, 0.10))
    # Upper Red Brake / Tail
    a.rect(x + 6, y + h // 2 + 6, w - 12, h // 2 - 12, TAIL_RED)
    for ry in range(y + h // 2 + 12, y + h - 10, 10):
        a.rect(x + 10, ry, w - 20, 3, (1.0, 0.25, 0.25))
    # Middle Amber Turn
    a.rect(x + 6, y + h // 4 + 4, w - 12, h // 4 - 2, AMBER_TURN)
    # Lower White Reverse
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
    # Orange horizontal defroster lines
    for dy in range(y + 16, y + h - 16, 14):
        a.rect(x + 8, dy, w - 16, 1, (0.88, 0.48, 0.15))
    a.noise(x, y, w, h, 0.008)

    # 8. Treaded Tire Rubber (R_WHEEL_TIRE)
    x, y, w, h = R_WHEEL_TIRE
    a.rect(x, y, w, h, TIRE_RUBBER)
    for ty in range(y, y + h, 8):
        a.rect(x, ty, w, 2, (0.08, 0.08, 0.09))
    a.noise(x, y, w, h, 0.015)

    # 9. 90s Fiat Sporting Alloy Wheel Rim (R_WHEEL_RIM)
    x, y, w, h = R_WHEEL_RIM
    a.rect(x, y, w, h, (0.25, 0.25, 0.27))
    cx, cy = x + w // 2, y + h // 2
    a.disc(cx, cy, 54, RIM_SILVER)
    a.disc(cx, cy, 44, (0.35, 0.36, 0.38))
    for i in range(4):
        ang = math.pi / 4 + i * (math.pi / 2)
        hx = int(cx + 24 * math.cos(ang))
        hy = int(cy + 24 * math.sin(ang))
        a.disc(hx, hy, 10, PLASTIC_DARK)
    for i in range(4):
        ang = i * (math.pi / 2)
        lx = int(cx + 18 * math.cos(ang))
        ly = int(cy + 18 * math.sin(ang))
        a.disc(lx, ly, 4, FIAT_CHROME)
    # Center Red Fiat badge
    a.disc(cx, cy, 14, PLASTIC_BLACK)
    a.disc(cx, cy, 10, (0.75, 0.10, 0.10))
    a.noise(x, y, w, h, 0.012)

    # 10. UK Number Plates (R_PLATES_UK)
    x, y, w, h = R_PLATES_UK
    a.rect(x, y, w, h, PLASTIC_BLACK)
    # White Front Plate
    f_box = (x + 8, y + h // 2 + 8, w - 16, h // 2 - 16)
    a.rect(*f_box, PLATE_WHITE)
    a.rect(f_box[0] + 2, f_box[1] + 2, 8, f_box[3] - 4, GB_BLUE)
    s_plate = "P97 CINQ"
    tw = a.text_width(s_plate, scale=2)
    a.text(f_box[0] + 16 + (f_box[2] - 20 - tw) // 2, f_box[1] + f_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)

    # Yellow Rear Plate
    r_box = (x + 8, y + 8, w - 16, h // 2 - 16)
    a.rect(*r_box, PLATE_YELLOW)
    a.rect(r_box[0] + 2, r_box[1] + 2, 8, r_box[3] - 4, GB_BLUE)
    a.text(r_box[0] + 16 + (r_box[2] - 20 - tw) // 2, r_box[1] + r_box[3] - 8, s_plate, (0.05, 0.05, 0.05), scale=2)
    a.noise(x, y, w, h, 0.010)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("vehicle_fiat_cinquecento_atlas", OUT_DIR)


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


def map_box(obj, front=R_BODY_YELLOW, sides=R_BODY_YELLOW, back=None, top=None, bottom=None):
    kit.map_faces_to_region(obj, front or R_BODY_YELLOW, S, only=side("front"))
    kit.map_faces_to_region(obj, sides or R_BODY_YELLOW, S, only=side("left"))
    kit.map_faces_to_region(obj, sides or R_BODY_YELLOW, S, only=side("right"))
    kit.map_faces_to_region(obj, back or sides or R_BODY_YELLOW, S, only=side("back"))
    kit.map_faces_to_region(obj, top or R_BODY_YELLOW, S, only=side("top"))
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


def make_wheel_assembly(name, radius=0.28, width=0.18, segs=24, at=(0, 0, 0), is_left=True):
    """Generates a high-detail 3D Cinquecento wheel (~420 tris) with Sporting alloy rim & disc."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    
    r_rim = radius * 0.64
    w_half = width * 0.5
    w_rim_inset = 0.03 if is_left else -0.03

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

    # 4 3D Lug Bolts on Rim
    r_studs = r_rim * 0.50
    for li in range(4):
        ang = li * (math.pi / 2)
        sx = r_studs * math.cos(ang)
        sy = r_studs * math.sin(ang)
        sz = out_z - w_rim_inset * 1.1
        s_verts = []
        for vi in range(6):
            va = 2 * math.pi * vi / 6
            sv = bm.verts.new((sx + 0.015 * math.cos(va), sy + 0.015 * math.sin(va), sz + (0.012 if is_left else -0.012)))
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
    """Creates a seamless sloped 3D cowl box (bonnet, windshield, or rear hatch) with outward normals."""
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


def make_bucket_seat(name, at=(0, 0, 0)):
    """90s Italian compact hatchback bucket seat with headrest."""
    parts = []
    c = kit.make_box(f"{name}_cushion", 0.38, 0.40, 0.10, (at[0], at[1], at[2] + 0.22))
    parts.append(c)
    b = kit.make_box(f"{name}_back", 0.36, 0.08, 0.46, (at[0], at[1] + 0.15, at[2] + 0.32))
    parts.append(b)
    h = kit.make_box(f"{name}_head", 0.18, 0.06, 0.14, (at[0], at[1] + 0.15, at[2] + 0.80))
    parts.append(h)
    s1 = make_cylinder(f"{name}_stalk1", 0.008, 0.06, segs=6, at=(at[0] - 0.05, at[1] + 0.15, at[2] + 0.74))
    s2 = make_cylinder(f"{name}_stalk2", 0.008, 0.06, segs=6, at=(at[0] + 0.05, at[1] + 0.15, at[2] + 0.74))
    parts.extend([s1, s2])
    p = kit.make_box(f"{name}_base", 0.28, 0.28, 0.22, (at[0], at[1], at[2]))
    parts.append(p)
    return parts


def main():
    kit.reset_scene()
    img = paint_cinquecento_atlas()
    mat = material_for(img, "mat_cinquecento")

    parts = []

    def register_box(name, w, d, h, at, **regions):
        o = kit.make_box(name, w, d, h, at)
        o.data.materials.append(mat)
        map_box(o, **regions)
        parts.append(o)
        return o

    # =========================================================================
    # 1997 Fiat Cinquecento Architecture:
    # Length (Y): 3.23m (Front bumper: -1.60m, Rear bumper: +1.63m)
    # Width (X):  1.49m (-0.745m to +0.745m)
    # Height (Z): 1.43m (Ground: 0.0m to Roof: 1.43m)
    # Wheelbase: 2.20m (Front: Y = -1.05m, Rear: Y = +1.15m)
    # =========================================================================

    # 1. Main Cabin Lower Tub (Y: -0.80m to +1.20m, Length: 2.00m, Width: 1.48m, Z: 0.30m to 0.85m)
    register_box("CabinLowerBody", 1.48, 2.00, 0.55, (0.0, 0.20, 0.30),
                 front=R_BODY_YELLOW, sides=R_BODY_YELLOW, back=R_BODY_YELLOW, top=R_BODY_YELLOW)

    # Side Rub Protective Strips along flanks
    register_box("SideRubStrip_L", 0.02, 2.70, 0.06, (-0.75, 0.0, 0.50),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("SideRubStrip_R", 0.02, 2.70, 0.06, (0.75, 0.0, 0.50),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 2. Main Cabin Roof & Pillars (Y: -0.40m to +1.10m, Length: 1.50m, Width: 1.36m, Z: 1.35m to 1.43m)
    register_box("CabinRoof", 1.36, 1.50, 0.08, (0.0, 0.35, 1.35),
                 front=R_BODY_YELLOW, sides=R_BODY_YELLOW, back=R_BODY_YELLOW, top=R_BODY_YELLOW)

    # Front Roof Antenna Mast
    antenna = make_cylinder("RoofAntenna", 0.005, 0.35, segs=6, at=(0.0, -0.30, 1.43))
    antenna.rotation_euler = (math.radians(25), 0, 0)
    antenna.data.materials.append(mat)
    kit.map_faces_to_region(antenna, R_BUMPER_BLACK, S)
    parts.append(antenna)

    # Side Windows (Driver & Passenger front door windows)
    register_box("SideWindow_L", 0.03, 0.75, 0.50, (-0.73, -0.05, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)
    register_box("SideWindow_R", 0.03, 0.75, 0.50, (0.73, -0.05, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)

    # Rear Quarter Pop-Out Windows
    register_box("RearQuarterWin_L", 0.03, 0.65, 0.48, (-0.73, 0.70, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)
    register_box("RearQuarterWin_R", 0.03, 0.65, 0.48, (0.73, 0.70, 0.85),
                 front=R_GLASS_FRONT, sides=R_GLASS_FRONT, top=R_GLASS_FRONT)

    # B-Pillar Black Trim Separators
    register_box("BPillar_L", 0.035, 0.08, 0.52, (-0.735, 0.35, 0.85),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("BPillar_R", 0.035, 0.08, 0.52, (0.735, 0.35, 0.85),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Door Handles
    register_box("DoorHandle_L", 0.03, 0.12, 0.03, (-0.755, 0.15, 0.78),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("DoorHandle_R", 0.03, 0.12, 0.03, (0.755, 0.15, 0.78),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3. Aerodynamic Sloped Front Windshield & Bonnet
    # Sloped Windshield (Y: -0.95m to -0.40m, Z: 0.85m to 1.35m)
    windshield = make_sloped_cowl("WindshieldSloped", w_rear=1.38, w_front=1.42,
                                  y_rear=-0.40, y_front=-0.95,
                                  z_rear_btm=0.30, z_rear_top=1.35,
                                  z_front_btm=0.30, z_front_top=0.85)
    windshield.data.materials.append(mat)
    kit.map_faces_to_region(windshield, R_GLASS_FRONT, S, only=lambda f: f.normal.y < -0.2 and f.normal.z > 0.1)
    kit.map_faces_to_region(windshield, R_BODY_YELLOW, S, only=lambda f: not (f.normal.y < -0.2 and f.normal.z > 0.1))
    parts.append(windshield)

    # Iconic Cinquecento Single Front Mono-Wiper
    wiper = register_box("FrontMonoWiper", 0.02, 0.45, 0.02, (0.0, -0.70, 1.08),
                         front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    wiper.rotation_euler = (math.radians(-32), 0, math.radians(25))

    # Sloped Bonnet / Hood (Y: -1.55m to -0.95m, Z: 0.65m to 0.85m)
    bonnet = make_sloped_cowl("BonnetSloped", w_rear=1.44, w_front=1.40,
                              y_rear=-0.95, y_front=-1.55,
                              z_rear_btm=0.30, z_rear_top=0.85,
                              z_front_btm=0.30, z_front_top=0.65)
    bonnet.data.materials.append(mat)
    kit.map_faces_to_region(bonnet, R_BODY_YELLOW, S)
    parts.append(bonnet)

    # 4. Sloped Rear Hatchback Tailgate (Y: +1.10m to +1.55m, Z: 0.80m to 1.35m)
    rear_hatch = make_sloped_cowl("RearHatchbackSloped", w_rear=1.38, w_front=1.34,
                                   y_rear=1.55, y_front=1.10,
                                   z_rear_btm=0.30, z_rear_top=0.80,
                                   z_front_btm=0.30, z_front_top=1.35)
    rear_hatch.data.materials.append(mat)
    kit.map_faces_to_region(rear_hatch, R_GLASS_REAR, S, only=lambda f: f.normal.y > 0.2 and f.normal.z > 0.1)
    kit.map_faces_to_region(rear_hatch, R_BODY_YELLOW, S, only=lambda f: not (f.normal.y > 0.2 and f.normal.z > 0.1))
    parts.append(rear_hatch)

    # Rear Tailgate Spoiler / Lip
    register_box("RearSpoilerLip", 1.32, 0.10, 0.04, (0.0, 1.15, 1.36),
                 front=R_BODY_YELLOW, sides=R_BODY_YELLOW, back=R_BODY_YELLOW, top=R_BODY_YELLOW)

    # Rear Wiper
    r_wiper = register_box("RearWiper", 0.015, 0.28, 0.015, (0.15, 1.38, 1.05),
                           front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    r_wiper.rotation_euler = (math.radians(35), 0, math.radians(-30))

    # 5. Front Fascia, Headlights, Grille & Front Bumper (Y: -1.58m)
    # Front Bumper with Cinquecento Sporting Styling
    register_box("FrontBumperMain", 1.48, 0.18, 0.26, (0.0, -1.56, 0.20),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK, bottom=R_BUMPER_BLACK)

    # Front Bumper Lower Yellow Insert Strip (Sporting trim)
    register_box("FrontBumperYellowTrim", 1.44, 0.02, 0.04, (0.0, -1.65, 0.24),
                 front=R_BODY_YELLOW, sides=R_BODY_YELLOW, top=R_BODY_YELLOW)

    # 2x Sporting Round Fog Lights in Bumper
    for fi, fx in enumerate([-0.45, 0.45]):
        fog = make_cylinder(f"SportingFog_{fi}", 0.045, 0.02, segs=12, at=(fx, -1.66, 0.28))
        fog.rotation_euler = (math.radians(90), 0, 0)
        fog.data.materials.append(mat)
        kit.map_faces_to_region(fog, R_HEADLIGHTS, S)
        parts.append(fog)

    # Front Radiator Slotted Grille
    register_box("FrontGrille", 0.70, 0.03, 0.18, (0.0, -1.56, 0.46),
                 front=R_FRONT_GRILLE, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Rectangular 90s Headlights (Left & Right)
    for hi, (hx, is_l) in enumerate([(-0.52, True), (0.52, False)]):
        register_box(f"Headlight_{hi}", 0.32, 0.03, 0.18, (hx, -1.56, 0.46),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_YELLOW)

    # Front UK Number Plate ("P97 CINQ" White)
    register_box("FrontNumberPlate", 0.42, 0.02, 0.10, (0.0, -1.66, 0.36),
                 front=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 6. Wing Mirrors & Side Repeaters
    for mi, (mx, is_l) in enumerate([(-0.78, True), (0.78, False)]):
        stalk = make_cylinder(f"MirrorStalk_{mi}", 0.015, 0.08, segs=8, at=(mx * 0.94, -0.50, 0.90))
        stalk.rotation_euler = (0, math.radians(90 if is_l else -90), 0)
        stalk.data.materials.append(mat)
        kit.map_faces_to_region(stalk, R_BUMPER_BLACK, S)
        parts.append(stalk)

        register_box(f"MirrorHousing_{mi}", 0.06, 0.12, 0.16, (mx, -0.50, 0.90),
                     front=R_GLASS_FRONT, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Orange Side Indicator Repeaters on front wings
    for si, sx in enumerate([-0.75, 0.75]):
        register_box(f"SideRepeater_{si}", 0.015, 0.05, 0.03, (sx, -1.20, 0.65),
                     front=R_HEADLIGHTS, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 7. Detailed Interior: Dashboard, Steering Wheel, Bucket Seats & Rear Bench
    driver_seats = make_bucket_seat("DriverSeat", at=(0.32, -0.10, 0.30))
    for s in driver_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    pass_seats = make_bucket_seat("PassengerSeat", at=(-0.32, -0.10, 0.30))
    for s in pass_seats:
        s.data.materials.append(mat)
        map_box(s, front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
        parts.append(s)

    # Rear Bench Seat (Cushion & Backrest)
    register_box("RearBenchCushion", 1.20, 0.40, 0.12, (0.0, 0.70, 0.45),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("RearBenchBack", 1.18, 0.08, 0.42, (0.0, 0.90, 0.57),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Dashboard Binnacle
    register_box("DashboardMain", 1.30, 0.35, 0.22, (0.0, -0.65, 0.68),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 3-Spoke Sporting Steering Wheel
    steer_ring = make_cylinder("SteeringWheelRing", 0.14, 0.025, segs=12, at=(0.32, -0.50, 0.82))
    steer_ring.rotation_euler = (math.radians(-45), 0, 0)
    steer_ring.data.materials.append(mat)
    kit.map_faces_to_region(steer_ring, R_BUMPER_BLACK, S)
    parts.append(steer_ring)

    # Interior Rearview Mirror
    register_box("RearviewMirror", 0.10, 0.02, 0.04, (0.0, -0.42, 1.30),
                 front=R_GLASS_FRONT, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 8. Rear End, Vertical Taillights, Bumper & Exhaust Tailpipe (Y: +1.58m)
    # Rear Bumper
    register_box("RearBumperMain", 1.48, 0.18, 0.26, (0.0, 1.58, 0.20),
                 back=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK, bottom=R_BUMPER_BLACK)

    # Rear Yellow Insert Strip on Bumper
    register_box("RearBumperYellowTrim", 1.44, 0.02, 0.04, (0.0, 1.67, 0.24),
                 back=R_BODY_YELLOW, sides=R_BODY_YELLOW, top=R_BODY_YELLOW)

    # Vertical Taillight Clusters (Left & Right)
    for ti, (tx, is_l) in enumerate([(-0.62, True), (0.62, False)]):
        register_box(f"Taillight_{ti}", 0.18, 0.03, 0.42, (tx, 1.57, 0.55),
                     back=R_TAILLIGHTS, sides=R_BUMPER_BLACK, top=R_BODY_YELLOW)

    # Rear UK Number Plate ("P97 CINQ" Yellow)
    register_box("RearNumberPlate", 0.42, 0.02, 0.10, (0.0, 1.67, 0.55),
                 back=R_PLATES_UK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # Sporty Angled Chrome Exhaust Tailpipe
    tailpipe = make_cylinder("SportingExhaust", 0.03, 0.28, segs=10, at=(-0.45, 1.52, 0.16))
    tailpipe.rotation_euler = (math.radians(90), 0, 0)
    tailpipe.data.materials.append(mat)
    kit.map_faces_to_region(tailpipe, R_BUMPER_BLACK, S)
    parts.append(tailpipe)

    # 9. Undercarriage Chassis Rails & Mudflaps
    register_box("ChassisRail_L", 0.10, 2.80, 0.12, (-0.45, 0.05, 0.25),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)
    register_box("ChassisRail_R", 0.10, 2.80, 0.12, (0.45, 0.05, 0.25),
                 front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, top=R_BUMPER_BLACK)

    # 4 Mudflaps behind wheels
    for mfi, (mfx, is_l) in enumerate([(-0.70, True), (0.70, False)]):
        register_box(f"FrontMudflap_{mfi}", 0.16, 0.02, 0.16, (mfx, -0.75, 0.16),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)
        register_box(f"RearMudflap_{mfi}", 0.16, 0.02, 0.18, (mfx, 1.45, 0.14),
                     front=R_BUMPER_BLACK, sides=R_BUMPER_BLACK, back=R_BUMPER_BLACK)

    # 10. 4x High-Detail 3D Wheels (~420 Tris each = ~1,680 Tris)
    wheel_coords = [
        ("Wheel_FL", -0.66, -1.05, True),
        ("Wheel_FR",  0.66, -1.05, False),
        ("Wheel_RL", -0.66,  1.15, True),
        ("Wheel_RR",  0.66,  1.15, False),
    ]

    for w_name, wx, wy, is_left in wheel_coords:
        wh = make_wheel_assembly(w_name, radius=0.28, width=0.18, segs=24, at=(wx, wy, 0.28), is_left=is_left)
        wh.rotation_euler = (0, math.radians(90), 0)
        wh.data.materials.append(mat)
        
        kit.map_faces_to_region(wh, R_WHEEL_TIRE, S, only=lambda f: f.normal.z > 0.3 or f.normal.z < -0.3 or abs(f.normal.y) > 0.3)
        kit.map_faces_to_region(wh, R_WHEEL_RIM, S, only=lambda f: (f.normal.x > 0.4 if is_left else f.normal.x < -0.4))
        parts.append(wh)

        # 3D Brake Caliper & Disc behind wheel
        disc = make_cylinder(f"BrakeDisc_{w_name}", 0.16, 0.03, segs=10, at=(wx * 0.82, wy, 0.28))
        disc.rotation_euler = (0, math.radians(90), 0)
        disc.data.materials.append(mat)
        kit.map_faces_to_region(disc, R_WHEEL_RIM, S)
        parts.append(disc)

    # =========================================================================
    # Finalize, Preview & Export
    # =========================================================================
    shell = kit.join(parts, "Vehicle_Fiat_Cinquecento")
    kit.finalize(shell)
    kit.report_stats(shell)

    preview_path = OUT_DIR / "vehicle_fiat_cinquecento_preview.png"
    kit.iso_preview(preview_path, [shell], resolution=1024)

    glb_path = OUT_DIR / "vehicle_fiat_cinquecento.glb"
    kit.export_glb(glb_path, [shell])

    # Deploy directly to Assets/3DModels/Vehicles
    try:
        ASSETS_VEHICLES_DIR.mkdir(parents=True, exist_ok=True)
        dest_glb = ASSETS_VEHICLES_DIR / "vehicle_fiat_cinquecento.glb"
        shutil.copy2(glb_path, dest_glb)
        print(f"[vehicle_fiat_cinquecento] deployed to {dest_glb}")
    except Exception as e:
        print(f"[vehicle_fiat_cinquecento] note: {e}")

    print("[vehicle_fiat_cinquecento] generation complete.")


if __name__ == "__main__":
    main()
