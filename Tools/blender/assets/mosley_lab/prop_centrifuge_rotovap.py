"""Mosley Lab: Prop - Rotary Evaporator & Centrifuge Station (~3000 Tris).

A chemical purification and distillation setup:
- Heavy lab workbench with chemical-resistant resin top.
- Rotary Evaporator (Rotovap): angled motorized drive, rotating distillation flask, glass spiral condenser coil, vacuum controller, water heating bath.
- Benchtop high-speed centrifuge unit with opened rotor lid showing 12 tube buckets.
- Microcentrifuge tube racks with coloured Eppendorf tubes.
- Digital vacuum pump with pressure dial beneath the table.
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

R_BENCH_RESIN = (0,   256, 256, 256)   # Black chemical-resistant epoxy resin bench
R_GLASS_COIL  = (256, 256, 256, 256)   # Clear borosilicate spiral condenser coil
R_PUMP_MOTOR  = (0,   128, 128, 128)   # Heavy industrial blue/grey pump body & vacuum gauge
R_ROTO_FLUID  = (128, 128, 128, 128)   # Golden amber distilled concentrate liquid
R_TUBES_RACK  = (256, 128, 128, 128)   # Polypropylene tube rack & fluorescent tube caps
R_STAINLESS   = (384, 128, 128, 128)   # Brushed stainless steel water bath & rotor fittings


def paint_atlas():
    a = Atlas(S, seed=8812)
    # 1. Resin Bench (R_BENCH_RESIN)
    x,y,w,h = R_BENCH_RESIN
    a.rect(x,y,w,h,(0.15,0.16,0.18)); a.noise(x,y,w,h,0.015)
    for ry in range(y,y+h,24): a.rect(x,ry,w,2,(0.25,0.26,0.28))

    # 2. Glass Condenser (R_GLASS_COIL)
    x,y,w,h = R_GLASS_COIL
    a.rect(x,y,w,h,(0.30,0.52,0.64)); a.noise(x,y,w,h,0.01)
    for rx in range(x,x+w,16): a.rect(rx,y,2,h,(0.18,0.36,0.48))

    # 3. Pump Motor (R_PUMP_MOTOR)
    x,y,w,h = R_PUMP_MOTOR
    a.rect(x,y,w,h,(0.18,0.32,0.52))
    a.disc(x+w//2, y+h//2, 36, (0.85,0.85,0.85))
    a.disc(x+w//2, y+h//2, 30, (0.05,0.05,0.05))
    a.rect(x+w//2-2, y+h//2, 4, 20, (0.85,0.15,0.15))
    a.noise(x,y,w,h,0.015)

    # 4. Amber Fluid (R_ROTO_FLUID)
    x,y,w,h = R_ROTO_FLUID
    a.rect(x,y,w,h,(0.85,0.52,0.10)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,12): a.rect(x,ry,w,2,(0.65,0.38,0.06))

    # 5. Tube Rack (R_TUBES_RACK)
    x,y,w,h = R_TUBES_RACK
    a.rect(x,y,w,h,(0.12,0.55,0.72))
    for rx in range(x+8,x+w-8,14):
        for ry in range(y+8,y+h-8,14):
            a.disc(rx,ry,5,(0.92,0.18,0.45))
    a.noise(x,y,w,h,0.01)

    # 6. Stainless Steel (R_STAINLESS)
    x,y,w,h = R_STAINLESS
    a.rect(x,y,w,h,(0.78,0.80,0.82)); a.noise(x,y,w,h,0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_centrifuge_rotovap", OUT_DIR)


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


def sphere(name, r, segs=16, at=(0,0,0)):
    mesh = bpy.data.meshes.new(name+"_m"); obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs//2, radius=r)
    bm.to_mesh(mesh); bm.free(); obj.location=at; return obj


def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img,"mat_centrifuge_rotovap")
    parts=[]

    def box(name,w,d,h,at,region=R_BENCH_RESIN):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_GLASS_COIL):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def ball(name,r,segs=16,at=(0,0,0),region=R_GLASS_COIL):
        o=sphere(name,r,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Main Resin Bench
    box("BenchWorktop",   2.6, 0.8, 0.08, (0, 0, 0.85), R_BENCH_RESIN)
    box("BenchBaseFrame", 2.6, 0.8, 0.85, (0, 0, 0.0),  R_BENCH_RESIN)
    box("BenchRearRiser", 2.6, 0.08, 0.45,(0, 0.36, 0.93), R_BENCH_RESIN)

    # 1. ROTARY EVAPORATOR (Left side: X = -0.65m)
    # Stand & motorized drive head
    box("RotovapBase",     0.55, 0.45, 0.08, (-0.65, 0.0, 0.93), R_PUMP_MOTOR)
    cylinder("RotovapPillar", 0.05, 0.85, 16, (-0.80, 0.12, 1.01), R_STAINLESS)
    box("RotovapMotorHead",0.22, 0.28, 0.24, (-0.65, 0.05, 1.55), R_PUMP_MOTOR)

    # Water heating bath (under flask)
    cylinder("WaterBathOuter", 0.18, 0.18, 20, (-0.45, -0.10, 1.01), R_STAINLESS)
    cylinder("WaterBathInner", 0.16, 0.14, 20, (-0.45, -0.10, 1.05), R_STAINLESS)

    # Evaporation rotating flask (in bath)
    ball("EvapFlask",      0.12, 16, (-0.45, -0.10, 1.18), R_GLASS_COIL)
    cylinder("EvapLiquid", 0.10, 0.08, 16, (-0.45, -0.10, 1.12), R_ROTO_FLUID)

    # Glass condenser diagonal tower
    cylinder("CondenserBody", 0.08, 0.65, 20, (-0.75, 0.0, 1.65), R_GLASS_COIL)
    # Internal glass coil spiral simulation (stacked rings)
    for ci in range(6):
        cylinder(f"CoilRing_{ci}", 0.05, 0.03, 16, (-0.75, 0.0, 1.72 + ci*0.09), R_GLASS_COIL)

    # Receiving flask at bottom of condenser
    ball("ReceivingFlask", 0.11, 16, (-0.75, 0.0, 1.50), R_GLASS_COIL)
    cylinder("RecFluid",   0.09, 0.06, 16, (-0.75, 0.0, 1.45), R_ROTO_FLUID)

    # 2. BENCHTOP CENTRIFUGE (Right side: X = 0.65m)
    box("CentrifugeBody",  0.55, 0.55, 0.32, (0.65, -0.05, 0.93), R_STAINLESS)
    cylinder("CentrifugeChamber", 0.22, 0.18, 24, (0.65, -0.05, 1.25), R_BENCH_RESIN)
    # Rotor with 12 sample tube buckets
    cylinder("RotorHub",   0.08, 0.10, 16, (0.65, -0.05, 1.26), R_STAINLESS)
    for ti in range(8):
        ang = 2 * math.pi * ti / 8
        tx = 0.65 + 0.15 * math.cos(ang)
        ty = -0.05 + 0.15 * math.sin(ang)
        cylinder(f"CentrifugeTube_{ti}", 0.02, 0.10, 12, (tx, ty, 1.28), R_TUBES_RACK)

    # Hinged lid open at 45 degrees
    box("CentrifugeLid",   0.52, 0.52, 0.04, (0.65, 0.22, 1.45), R_STAINLESS)

    # 3. ACCESSORIES: Tube racks & Vacuum pump
    box("EppendorfRack1",  0.30, 0.16, 0.08, (0.05, -0.15, 0.93), R_TUBES_RACK)
    for ri in range(6):
        rx = -0.05 + (ri % 3) * 0.09
        ry = -0.18 + (ri // 3) * 0.08
        cylinder(f"EppTube_{ri}", 0.015, 0.06, 8, (rx, ry, 1.01), R_TUBES_RACK)

    # Vacuum pump on floor beneath table
    box("VacuumPump",      0.45, 0.30, 0.35, (-0.65, 0.0, 0.05), R_PUMP_MOTOR)
    cylinder("PumpGauge",  0.06, 0.04, 16, (-0.65, -0.16, 0.28), R_PUMP_MOTOR)
    cylinder("VacuumHose", 0.025, 0.85, 12, (-0.65, 0.10, 0.40), R_BENCH_RESIN)

    shell = kit.join(parts, "Prop_Centrifuge_Rotovap")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_centrifuge_rotovap_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_centrifuge_rotovap.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_centrifuge_rotovap.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_centrifuge_rotovap_preview.png")
        shutil.copy2(OUT_DIR / "atlas_centrifuge_rotovap.png", TEXTURES_DIR / "atlas_centrifuge_rotovap.png")
        print("[CentrifugeRotovap] deployed.")
    except Exception as e: print(f"[CentrifugeRotovap] notice: {e}")


if __name__ == "__main__": main()
