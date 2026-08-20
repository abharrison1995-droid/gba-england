"""Mosley Lab: Prop - Fume Hood / Lab Safety Cabinet (~3000 Tris).

A floor-standing laboratory fume extraction hood:
- Heavy steel frame with lift-up sash window (clear acrylic panel).
- Interior white-coated work surface with ceramic liner.
- Twin-coil heating element inside.
- Baffle/duct at rear connecting to extraction pipe.
- Emergency wash bottle, glass thermometer, safety gloves hanging on side peg.
- Exterior warning labels and extraction airflow indicator arrow.
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

R_STEEL_GREY  = (0,   256, 256, 256)
R_SASH_CLEAR  = (256, 256, 256, 256)
R_WHITE_LINER = (0,   128, 128, 128)
R_HAZARD_WARN = (128, 128, 128, 128)
R_ELEMENT_RED = (256, 128, 128, 128)
R_SAFETY_EQUIP= (384, 128, 128, 128)

def paint_atlas():
    a = Atlas(S, seed=7777)
    x,y,w,h = R_STEEL_GREY
    a.rect(x,y,w,h,(0.55,0.56,0.58)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,24): a.rect(x,ry,w,2,(0.42,0.43,0.45))
    x,y,w,h = R_SASH_CLEAR
    a.rect(x,y,w,h,(0.35,0.55,0.65)); a.noise(x,y,w,h,0.01)
    for rx in range(x,x+w,28): a.rect(rx,y,2,h,(0.20,0.38,0.48))
    x,y,w,h = R_WHITE_LINER
    a.rect(x,y,w,h,(0.90,0.90,0.90)); a.noise(x,y,w,h,0.01)
    x,y,w,h = R_HAZARD_WARN
    a.rect(x,y,w,h,(0.88,0.72,0.10))
    for i in range(-w,w+h,16):
        for t in range(5):
            px,py=x+i+t,y+t
            if x<=px<x+w and y<=py<y+h: a.rect(px,py,1,1,(0.12,0.12,0.12))
    x,y,w,h = R_ELEMENT_RED
    a.rect(x,y,w,h,(0.75,0.18,0.08)); a.noise(x,y,w,h,0.02)
    x,y,w,h = R_SAFETY_EQUIP
    a.rect(x,y,w,h,(0.20,0.55,0.30)); a.noise(x,y,w,h,0.015)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_fume_hood", OUT_DIR)

def cyl(name, r, h, segs=16, at=(0,0,0)):
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
    mat = material_for(img,"mat_fume_hood")
    parts=[]
    def box(name,w,d,h,at,region=R_STEEL_GREY):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o
    def cylinder(name,r,h,segs=16,at=(0,0,0),region=R_STEEL_GREY):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Outer cabinet frame
    box("HoodBase",        1.30, 0.72, 0.90, (0, 0, 0.00), R_STEEL_GREY)   # cabinet lower body
    box("HoodWorktop",     1.30, 0.72, 0.06, (0, 0, 0.90), R_WHITE_LINER)  # work surface
    box("HoodInteriorBack",1.20, 0.04, 1.00, (0, 0.34, 0.96), R_WHITE_LINER)
    box("HoodInteriorFloor",1.20,0.68, 0.04, (0, 0.02, 0.96), R_WHITE_LINER)
    box("HoodLeftWall",    0.04, 0.68, 1.00, (-0.62,0.02, 0.96), R_STEEL_GREY)
    box("HoodRightWall",   0.04, 0.68, 1.00, ( 0.62,0.02, 0.96), R_STEEL_GREY)
    box("HoodTop",         1.30, 0.72, 0.08, (0, 0, 1.96), R_STEEL_GREY)

    # Sash window (half open)
    box("SashFrame",       1.22, 0.05, 0.65, (0, -0.34, 0.96), R_STEEL_GREY)
    box("SashGlass",       1.16, 0.03, 0.62, (0, -0.32, 0.97), R_SASH_CLEAR)

    # Extraction duct at rear top
    box("ExtrBaffle",      1.10, 0.08, 0.14, (0, 0.32, 1.82), R_STEEL_GREY)
    cylinder("ExtrDuct",   0.18, 0.55, 16,   (0, 0.30, 2.04), R_STEEL_GREY)

    # Heating elements inside (twin coil)
    for side in [-0.28, 0.28]:
        box(f"HeaterCoil1_{side:.0f}", 0.40, 0.06, 0.05, (side, 0.0, 1.06), R_ELEMENT_RED)
        box(f"HeaterCoil2_{side:.0f}", 0.06, 0.34, 0.05, (side, 0.0, 1.11), R_ELEMENT_RED)

    # Warning label & airflow arrow on front
    box("HazardLabel",     0.38, 0.04, 0.18, (-0.3, -0.36, 0.30), R_HAZARD_WARN)
    box("AirflowArrow",    0.22, 0.04, 0.12, ( 0.30,-0.36, 0.32), R_HAZARD_WARN)

    # Side safety equipment (emergency wash bottle + gloves)
    cylinder("WashBottle", 0.045, 0.18, 16, (0.72,-0.10, 0.92), R_SAFETY_EQUIP)
    box("GlovesHang",      0.20, 0.03, 0.24, (0.72, 0.10, 0.95), R_SAFETY_EQUIP)
    cylinder("Thermometer", 0.012, 0.28, 12, (-0.68, 0.0, 1.00), R_SASH_CLEAR)

    # Cabinet leg levellers
    for lx,ly in [(-0.60,-0.32),(-0.60,0.32),(0.60,-0.32),(0.60,0.32)]:
        cylinder(f"LegLev_{lx:.0f}_{ly:.0f}", 0.04, 0.06, 12, (lx,ly,0.0), R_STEEL_GREY)

    shell = kit.join(parts, "Prop_Fume_Hood")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_fume_hood_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_fume_hood.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_fume_hood.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_fume_hood_preview.png")
        shutil.copy2(OUT_DIR / "atlas_fume_hood.png", TEXTURES_DIR / "atlas_fume_hood.png")
        print("[FumeHood] deployed.")
    except Exception as e: print(f"[FumeHood] notice: {e}")

if __name__ == "__main__": main()
