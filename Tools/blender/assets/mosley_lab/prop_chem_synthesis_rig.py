"""Mosley Lab: Prop - Chemical Synthesis Rig (~3000 Tris).

A fume-hood chemistry setup for synthesizing vape compounds:
- Borosilicate round-bottom flask on iron stand with clay triangle & wire gauze.
- Liebig condenser with rubber hose connections (coiled glass tube).
- Separating funnel on ring stand with stopcock.
- Bunsen burner / lab hot plate beneath the main flask.
- Erlenmeyer flasks with coloured chemical reagents (amber, green, clear).
- Chemical reagent bottle rack with labelled bottles.
- Stir plates, clamps, and iron ring stands.
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

R_GLASS_CLEAR= (0,   256, 256, 256)
R_IRON_STAND = (256, 256, 256, 256)
R_AMBER_LIQ  = (0,   128, 128, 128)
R_GREEN_LIQ  = (128, 128, 128, 128)
R_RUBBER_TUBE= (256, 128, 128, 128)
R_LABEL_WHITE= (384, 128, 128, 128)

def paint_atlas():
    a = Atlas(S, seed=1337)
    x,y,w,h = R_GLASS_CLEAR
    a.rect(x,y,w,h,(0.30,0.50,0.60)); a.noise(x,y,w,h,0.015)
    x,y,w,h = R_IRON_STAND
    a.rect(x,y,w,h,(0.28,0.29,0.30)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,18): a.rect(x,ry,w,2,(0.18,0.19,0.20))
    x,y,w,h = R_AMBER_LIQ
    a.rect(x,y,w,h,(0.80,0.45,0.08)); a.noise(x,y,w,h,0.015)
    x,y,w,h = R_GREEN_LIQ
    a.rect(x,y,w,h,(0.10,0.62,0.25)); a.noise(x,y,w,h,0.015)
    x,y,w,h = R_RUBBER_TUBE
    a.rect(x,y,w,h,(0.16,0.16,0.16)); a.noise(x,y,w,h,0.02)
    x,y,w,h = R_LABEL_WHITE
    a.rect(x,y,w,h,(0.92,0.91,0.88))
    a.rect(x+6,y+8,w-12,10,(0.14,0.14,0.16)); a.noise(x,y,w,h,0.01)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_chem_synthesis_rig", OUT_DIR)

def cyl(name, r, h, segs=20, at=(0,0,0)):
    mesh = bpy.data.meshes.new(name+"_m"); obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    verts=[]; faces=[]
    for i in range(segs):
        a=2*math.pi*i/segs; verts.append((r*math.cos(a),r*math.sin(a),0))
    for i in range(segs):
        a=2*math.pi*i/segs; verts.append((r*math.cos(a),r*math.sin(a),h))
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
    mat = material_for(img,"mat_chem_rig")
    parts=[]
    def box(name,w,d,h,at,region=R_IRON_STAND):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o
    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_GLASS_CLEAR):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o
    def ball(name,r,segs=16,at=(0,0,0),region=R_GLASS_CLEAR):
        o=sphere(name,r,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Bench base
    box("LabBench",     2.4, 0.7, 0.06, (0,0,0.80), R_IRON_STAND)
    box("BenchFrame",   2.4, 0.7, 0.80, (0,0,0.00), R_IRON_STAND)

    # Main iron ring stand (left)
    box("RingStandRodL", 0.04, 0.04, 1.10, (-0.7, 0.0, 0.86), R_IRON_STAND)
    box("RingStandBaseL",0.28, 0.20, 0.03, (-0.7, 0.0, 0.86), R_IRON_STAND)
    box("IronRingL",     0.22, 0.03, 0.03, (-0.7, 0.0, 1.38), R_IRON_STAND)

    # Round-bottom flask on ring stand
    ball("RBFlask",      0.14, 16, (-0.7, 0.0, 1.52), R_GLASS_CLEAR)
    cylinder("RBNeck",   0.04, 0.18, 16, (-0.7, 0.0, 1.66), R_GLASS_CLEAR)
    cylinder("RBLiquid", 0.12, 0.10, 16, (-0.7, 0.0, 1.42), R_AMBER_LIQ)

    # Bunsen burner beneath flask
    cylinder("BunsenBase",  0.07, 0.04, 16, (-0.7, 0.0, 0.86), R_IRON_STAND)
    cylinder("BunsenBarrel",0.03, 0.22, 12, (-0.7, 0.0, 0.90), R_IRON_STAND)
    cylinder("BunsenFlame", 0.02, 0.08, 12, (-0.7, 0.0, 1.12), R_AMBER_LIQ)

    # Liebig condenser (center, angled)
    box("CondenserOuter",  0.06, 0.06, 0.55, (0.0, 0.0, 1.05), R_GLASS_CLEAR)
    box("CondenserInner",  0.03, 0.03, 0.55, (0.0, 0.0, 1.05), R_GLASS_CLEAR)
    # Rubber hose connections
    box("HoseTop",    0.02, 0.16, 0.02, (0.0, 0.08, 1.56), R_RUBBER_TUBE)
    box("HoseBottom", 0.02, 0.16, 0.02, (0.0, 0.08, 1.05), R_RUBBER_TUBE)

    # Separating funnel + stand (right)
    box("SepFunnelStandRod",  0.03, 0.03, 1.10, (0.70, 0.0, 0.86), R_IRON_STAND)
    box("SepFunnelStandBase", 0.26, 0.20, 0.03, (0.70, 0.0, 0.86), R_IRON_STAND)
    ball("SepFunnelBulb",     0.12, 14, (0.70, 0.0, 1.50), R_GLASS_CLEAR)
    cylinder("SepFunnelStem", 0.025, 0.22, 12, (0.70, 0.0, 1.28), R_GLASS_CLEAR)
    cylinder("SepFunnelLiquid",0.10, 0.08, 12, (0.70, 0.0, 1.42), R_GREEN_LIQ)
    box("SepFunnelStopcock",   0.06, 0.06, 0.05, (0.70, 0.0, 1.28), R_IRON_STAND)

    # Erlenmeyer flasks (3 small ones on bench)
    for i,col in enumerate([R_AMBER_LIQ, R_GREEN_LIQ, R_GLASS_CLEAR]):
        bx = -0.5 + i*0.52
        cylinder(f"ErlFlask_{i}",     0.10, 0.22, 16, (bx, 0.26, 0.86), R_GLASS_CLEAR)
        cylinder(f"ErlLiquid_{i}",    0.08, 0.12, 16, (bx, 0.26, 0.86), col)
        cylinder(f"ErlNeck_{i}",      0.03, 0.10, 12, (bx, 0.26, 1.08), R_GLASS_CLEAR)

    # Reagent bottle rack (rear of bench)
    box("ReagentRack", 1.2, 0.12, 0.24, (0.0, 0.33, 0.86), R_IRON_STAND)
    for i in range(6):
        bx = -0.5 + i*0.20
        cylinder(f"ReagentBottle_{i}", 0.045, 0.20, 14, (bx, 0.33, 0.86), R_GLASS_CLEAR)
        box(f"ReagentLabel_{i}",       0.07, 0.01, 0.06, (bx, 0.29, 0.96), R_LABEL_WHITE)

    shell = kit.join(parts, "Prop_Chem_Synthesis_Rig")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_chem_synthesis_rig_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_chem_synthesis_rig.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR  / "prop_chem_synthesis_rig.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_chem_synthesis_rig_preview.png")
        shutil.copy2(OUT_DIR / "atlas_chem_synthesis_rig.png", TEXTURES_DIR / "atlas_chem_synthesis_rig.png")
        print("[ChemSynthesisRig] deployed.")
    except Exception as e: print(f"[ChemSynthesisRig] notice: {e}")

if __name__ == "__main__": main()
