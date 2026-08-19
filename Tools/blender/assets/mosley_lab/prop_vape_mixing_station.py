"""Mosley Lab: Prop - Clandestine Vape Mixing Station (~3000 Tris).

A bespoke countertop workbench for blending e-liquid formulas:
- Stainless steel lab bench with pegboard back panel and under-shelf storage.
- 3 large borosilicate glass mixing beakers with coloured liquid levels & stirrer rods.
- Hot plate magnetic stirrer unit with digital LED display.
- Dropper bottles rack (8 bottles) of flavour concentrates.
- Precision digital scale with weigh boat.
- Overhead extraction hood funnel connected to ducting.
Target: ~3,000 tris. Deploys to Assets/3DModels/Mosley Cellar lab/
"""

import math, shutil
from pathlib import Path
import bpy, bmesh
import asset_kit as kit
from atlas import Atlas, material_for

S = 512
OUT_DIR   = kit.OUT_DIR / "mosley_lab"
DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "Assets" / "3DModels" / "Mosley Cellar lab"
TEXTURES_DIR = DEPLOY_DIR / "textures"

R_STEEL      = (0,   256, 256, 256)
R_GLASS      = (256, 256, 256, 256)
R_LCD_PANEL  = (0,   128, 128, 128)
R_PLASTIC    = (128, 128, 128, 128)
R_LIQUID_RED = (256, 128, 128, 128)
R_RUBBER     = (384, 128, 128, 128)

def paint_atlas():
    a = Atlas(S, seed=2024)
    x,y,w,h = R_STEEL
    a.rect(x,y,w,h,(0.75,0.76,0.78)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,32): a.rect(x,ry,w,1,(0.55,0.56,0.58))
    x,y,w,h = R_GLASS
    a.rect(x,y,w,h,(0.25,0.45,0.55)); a.noise(x,y,w,h,0.015)
    x,y,w,h = R_LCD_PANEL
    a.rect(x,y,w,h,(0.08,0.12,0.10))
    a.rect(x+6,y+6,w-12,h//2-4,(0.05,0.72,0.35))
    a.noise(x,y,w,h,0.01)
    x,y,w,h = R_PLASTIC
    a.rect(x,y,w,h,(0.22,0.22,0.24)); a.noise(x,y,w,h,0.02)
    x,y,w,h = R_LIQUID_RED
    a.rect(x,y,w,h,(0.72,0.12,0.08)); a.noise(x,y,w,h,0.015)
    for rx in range(x,x+w,14): a.rect(rx,y,2,h,(0.55,0.08,0.05))
    x,y,w,h = R_RUBBER
    a.rect(x,y,w,h,(0.14,0.14,0.14)); a.noise(x,y,w,h,0.02)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_vape_mixing_station", OUT_DIR)

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

def main():
    kit.reset_scene()
    img = paint_atlas()
    mat = material_for(img,"mat_vape_mixing")
    parts=[]
    def box(name,w,d,h,at,region=R_STEEL):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o
    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_GLASS):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Bench body
    box("BenchTop",      2.8, 0.8, 0.08, (0, 0, 0.85), R_STEEL)
    box("BenchFrame",    2.8, 0.8, 0.85, (0, 0, 0.0),  R_STEEL)
    box("BenchShelf",    2.6, 0.7, 0.05, (0, 0, 0.45), R_STEEL)
    box("PegboardBack",  2.8, 0.06, 1.0, (0, 0.42, 0.9), R_PLASTIC)

    # Extraction hood
    box("ExtractionHood",  2.4, 0.7, 0.35, (0, 0, 1.9),  R_STEEL)
    box("ExtractionDuct",  0.3, 0.3, 0.8,  (0.8, 0.38, 2.25), R_PLASTIC)
    cylinder("DuctTop", 0.18, 0.25, 16, (0.8, 0.38, 3.05), R_PLASTIC)

    # 3 Beakers on bench surface
    for i,col in enumerate([R_LIQUID_RED, R_GLASS, R_GLASS]):
        bx = -0.9 + i*0.9
        cylinder(f"Beaker_{i}",     0.16, 0.40, 20, (bx, -0.1, 0.93), R_GLASS)
        cylinder(f"BeakerLiquid_{i}",0.14, 0.24, 20, (bx, -0.1, 0.93), col)
        box(f"StirRod_{i}",  0.02, 0.02, 0.52, (bx, -0.1, 0.93), R_GLASS)

    # Hot plate magnetic stirrer
    box("HotPlateBody",  0.30, 0.28, 0.08, (1.05, -0.1, 0.93), R_PLASTIC)
    box("HotPlateTop",   0.28, 0.26, 0.02, (1.05, -0.1, 1.01), R_RUBBER)
    box("HotPlateLCD",   0.14, 0.05, 0.06, (1.05, -0.24, 0.97), R_LCD_PANEL)

    # Dropper bottle rack (8 bottles)
    box("DroppRack",     0.9, 0.12, 0.12, (-1.0, 0.35, 0.93), R_PLASTIC)
    for i in range(8):
        bx = -1.32 + i*0.10
        cylinder(f"DropperBottle_{i}", 0.03, 0.14, 12, (bx, 0.35, 0.93), R_GLASS)
        cylinder(f"DropperTip_{i}",    0.01, 0.05, 8,  (bx, 0.35, 1.07), R_RUBBER)

    # Precision scale
    box("ScalePlatform", 0.20, 0.18, 0.04, (-1.08, -0.15, 0.93), R_PLASTIC)
    box("ScaleDisplay",  0.12, 0.04, 0.06, (-1.08, -0.26, 0.97), R_LCD_PANEL)
    box("WeighBoat",     0.12, 0.10, 0.01, (-1.08, -0.15, 0.97), R_GLASS)

    # Under-shelf storage boxes
    for i in range(3):
        bx = -0.9 + i*0.9
        box(f"StorageBox_{i}", 0.35, 0.3, 0.28, (bx, 0.0, 0.10), R_PLASTIC)

    shell = kit.join(parts, "Prop_Vape_Mixing_Station")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_vape_mixing_station_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_vape_mixing_station.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR  / "prop_vape_mixing_station.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_vape_mixing_station_preview.png")
        shutil.copy2(OUT_DIR / "atlas_vape_mixing_station.png", TEXTURES_DIR / "atlas_vape_mixing_station.png")
        print("[VapeMixingStation] deployed.")
    except Exception as e: print(f"[VapeMixingStation] notice: {e}")

if __name__ == "__main__": main()
