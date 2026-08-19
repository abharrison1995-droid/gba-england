"""Mosley Lab: Prop - Pressurized Gas Cylinder Manifold (~3000 Tris).

Industrial pressurized inert gas delivery bank (Nitrogen / Argon / CO2):
- Heavy wall-mounting steel bracket frame with steel safety retention chains.
- 4x high-pressure gas cylinders (2 grey nitrogen, 1 teal argon, 1 maroon CO2).
- Brass dual-stage pressure regulators with primary & delivery dial gauges.
- High-pressure braided stainless steel pigtail hoses connecting cylinders to a central brass manifold header bar.
- Master shutoff ball valve and gas line output pipe.
Target: ~3,000 tris. Deploys to Assets/3DModels/Mosley Cellar lab/
"""

import math, shutil
from pathlib import Path
import bpy, bmesh
import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR    = kit.OUT_DIR / "mosley_lab"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "Mosley Cellar lab"
TEXTURES_DIR = DEPLOY_DIR / "textures"

R_CYL_GREY    = (0,   256, 256, 256)   # Nitrogen grey cylinder body & black neck
R_CYL_TEAL    = (256, 256, 256, 256)   # Argon teal/green cylinder body
R_CYL_MAROON  = (0,   128, 128, 128)   # Carbon dioxide maroon cylinder body
R_BRASS_REG   = (128, 128, 128, 128)   # Brass dual-stage regulator valves & copper fittings
R_DIAL_GAUGES = (256, 128, 128, 128)   # White dial faces with psi graduations & red needles
R_STEEL_CHAIN = (384, 128, 128, 128)   # Heavy zinc galvanized retention chains & bracket


def paint_atlas():
    a = Atlas(S, seed=7474)
    # 1. Grey Nitrogen (R_CYL_GREY)
    x,y,w,h = R_CYL_GREY
    a.rect(x,y,w,h,(0.55,0.56,0.58)); a.noise(x,y,w,h,0.02)
    a.rect(x,y+h-40,w,40,(0.12,0.12,0.14)) # Black shoulder band

    # 2. Teal Argon (R_CYL_TEAL)
    x,y,w,h = R_CYL_TEAL
    a.rect(x,y,w,h,(0.12,0.52,0.48)); a.noise(x,y,w,h,0.02)
    a.rect(x,y+h-40,w,40,(0.18,0.72,0.65))

    # 3. Maroon CO2 (R_CYL_MAROON)
    x,y,w,h = R_CYL_MAROON
    a.rect(x,y,w,h,(0.55,0.15,0.18)); a.noise(x,y,w,h,0.015)
    a.rect(x,y+h-24,w,24,(0.80,0.80,0.80))

    # 4. Brass Regulator (R_BRASS_REG)
    x,y,w,h = R_BRASS_REG
    a.rect(x,y,w,h,(0.82,0.65,0.22)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,14): a.rect(x,ry,w,2,(0.62,0.48,0.14))

    # 5. Dial Gauges (R_DIAL_GAUGES)
    x,y,w,h = R_DIAL_GAUGES
    a.rect(x,y,w,h,(0.90,0.92,0.94))
    a.disc(x+w//2, y+h//2, 34, (0.12,0.14,0.16)) # Chrome bezel
    a.disc(x+w//2, y+h//2, 28, (0.95,0.95,0.95)) # White face
    a.rect(x+w//2-1, y+h//2, 2, 20, (0.85,0.12,0.12)) # Red needle

    # 6. Steel Chain (R_STEEL_CHAIN)
    x,y,w,h = R_STEEL_CHAIN
    a.rect(x,y,w,h,(0.45,0.47,0.50))
    for rx in range(x,x+w,12): a.rect(rx,y,4,h,(0.30,0.32,0.35))
    a.noise(x,y,w,h,0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_gas_manifold", OUT_DIR)


def cyl(name, r, h, segs=20, at=(0,0,0)):
    mesh = bpy.data.meshes.new(name+"_m"); obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    verts=[]; faces=[]
    for i in range(segs):
        ang=2*math.pi*i/segs; verts.append((r*math.cos(ang),r*math.sin(ang),0))
    for i in range(segs):
        ang=2*math.pi*i/segs; verts.append((r*math.cos(ang),r*math.sin(ang),h))
    for i in range(segs):
        ni=(i+1)%segs; faces.append((i,ni,segs+ni,segs+i))
    faces.append(list(range(segs-1,-1,-1))); faces.append(list(range(segs,segs*2)))
    mesh.from_pydata(verts,[],faces); mesh.update(); obj.location=at; return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img,"mat_gas_manifold")
    parts=[]

    def box(name,w,d,h,at,region=R_STEEL_CHAIN):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_CYL_GREY):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Steel Wall Mounting Bracket & Base Rest Stand (Z = 0.0 to 1.8m)
    box("FloorStandPlate", 2.2, 0.45, 0.05, (0, 0, 0.0), R_STEEL_CHAIN)
    box("WallBracketRail", 2.2, 0.06, 0.10, (0, 0.18, 1.10), R_STEEL_CHAIN)
    box("RetentionChain",  2.1, 0.04, 0.06, (0, -0.15, 1.10), R_STEEL_CHAIN)

    # 4 HIGH-PRESSURE GAS CYLINDERS (Spacing: 0.50m apart)
    cyl_configs = [
        (-0.75, R_CYL_GREY,   "Nitrogen1"),
        (-0.25, R_CYL_GREY,   "Nitrogen2"),
        ( 0.25, R_CYL_TEAL,   "Argon1"),
        ( 0.75, R_CYL_MAROON, "CO2_1"),
    ]

    for cx, ccol, cname in cyl_configs:
        # Cylinder main body (r = 0.14m, height = 1.40m)
        cylinder(f"{cname}_Body", 0.14, 1.25, 24, (cx, 0.0, 0.05), ccol)
        # Rounded shoulder & neck
        cylinder(f"{cname}_Neck", 0.08, 0.15, 20, (cx, 0.0, 1.30), ccol)
        cylinder(f"{cname}_Stem", 0.03, 0.10, 14, (cx, 0.0, 1.45), R_BRASS_REG)

        # Brass dual-stage regulator assembly
        box(f"{cname}_RegBody",    0.08, 0.08, 0.08, (cx, 0.0, 1.55), R_BRASS_REG)
        # 2 Dial pressure gauges (Inlet & Delivery)
        cylinder(f"{cname}_Gauge1", 0.04, 0.03, 16, (cx - 0.06, -0.06, 1.62), R_DIAL_GAUGES)
        cylinder(f"{cname}_Gauge2", 0.04, 0.03, 16, (cx + 0.06, -0.06, 1.62), R_DIAL_GAUGES)
        # T-bar adjustment handle
        box(f"{cname}_THandle",     0.10, 0.02, 0.02, (cx, -0.07, 1.55), R_BRASS_REG)

    # Central Header Manifold Bar (X = -0.85m to +0.85m at Z = 1.85m)
    box("HeaderManifoldBar", 2.0, 0.05, 0.05, (0, 0.0, 1.85), R_BRASS_REG)
    # Master shutoff valve wheel
    cylinder("MasterValveWheel", 0.08, 0.03, 16, (1.05, 0.0, 1.85), R_CYL_MAROON)

    # 4 Braided Stainless Steel Pigtail Connecting Lines
    for cx, _, cname in cyl_configs:
        box(f"{cname}_Pigtail", 0.02, 0.02, 0.22, (cx, 0.0, 1.63), R_STEEL_CHAIN)

    # Main gas line discharge pipe running upward
    cylinder("DischargePipe", 0.03, 0.55, 14, (0.0, 0.0, 1.90), R_BRASS_REG)

    shell = kit.join(parts, "Prop_Gas_Cylinder_Manifold")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_gas_cylinder_manifold_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_gas_cylinder_manifold.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_gas_cylinder_manifold.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_gas_cylinder_manifold_preview.png")
        shutil.copy2(OUT_DIR / "atlas_gas_manifold.png", TEXTURES_DIR / "atlas_gas_manifold.png")
        print("[GasManifold] deployed.")
    except Exception as e: print(f"[GasManifold] notice: {e}")


if __name__ == "__main__": main()
