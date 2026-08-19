"""Mosley Lab: Prop - Vape Filling & Bottling Machine (~3000 Tris).

An industrial semi-automated e-liquid filling line:
- Rectangular stainless steel machine body with control panel.
- 4 large cylindrical supply tanks (clear acrylic with coloured liquid fill levels).
- Filling nozzle carousel with 4 precision nozzles on an aluminium arm.
- Conveyor tray for empty bottles / filled vape cartridges.
- Digital touch-screen control interface with volume and batch readouts.
- Pneumatic air lines and quick-connect fittings.
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

R_STEEL      = (0,   256, 256, 256)
R_ACRYLIC    = (256, 256, 256, 256)
R_TOUCH_UI   = (0,   128, 128, 128)
R_LIQUID_BLUE= (128, 128, 128, 128)
R_AIR_LINE   = (256, 128, 128, 128)
R_CONVEYOR   = (384, 128, 128, 128)

def paint_atlas():
    a = Atlas(S, seed=4242)
    x,y,w,h = R_STEEL
    a.rect(x,y,w,h,(0.72,0.74,0.76)); a.noise(x,y,w,h,0.018)
    for rx in range(x,x+w,24): a.rect(rx,y,1,h,(0.58,0.60,0.62))
    x,y,w,h = R_ACRYLIC
    a.rect(x,y,w,h,(0.20,0.50,0.70)); a.noise(x,y,w,h,0.01)
    x,y,w,h = R_TOUCH_UI
    a.rect(x,y,w,h,(0.06,0.08,0.12))
    a.rect(x+4,y+4,w-8,h//3,(0.05,0.65,0.90))
    a.rect(x+4,y+h//3+6,40,18,(0.08,0.78,0.25))
    a.rect(x+50,y+h//3+6,40,18,(0.80,0.22,0.12))
    a.noise(x,y,w,h,0.01)
    x,y,w,h = R_LIQUID_BLUE
    a.rect(x,y,w,h,(0.08,0.28,0.75)); a.noise(x,y,w,h,0.015)
    x,y,w,h = R_AIR_LINE
    a.rect(x,y,w,h,(0.80,0.35,0.08)); a.noise(x,y,w,h,0.02)
    x,y,w,h = R_CONVEYOR
    a.rect(x,y,w,h,(0.35,0.36,0.38))
    for rx in range(x,x+w,12): a.rect(rx,y,4,h,(0.25,0.26,0.28))
    a.noise(x,y,w,h,0.015)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_filling_machine", OUT_DIR)

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
    mat = material_for(img,"mat_filling_machine")
    parts=[]
    def box(name,w,d,h,at,region=R_STEEL):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o
    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_ACRYLIC):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Machine body
    box("MachineBody",    1.8, 0.7, 1.2,  (0, 0, 0.0),  R_STEEL)
    box("MachineLid",     1.8, 0.7, 0.06, (0, 0, 1.2),  R_STEEL)
    box("MachineFoot1",   0.08,0.08,0.12, (-0.82,-0.3,0), R_STEEL)
    box("MachineFoot2",   0.08,0.08,0.12, ( 0.82,-0.3,0), R_STEEL)
    box("MachineFoot3",   0.08,0.08,0.12, (-0.82, 0.3,0), R_STEEL)
    box("MachineFoot4",   0.08,0.08,0.12, ( 0.82, 0.3,0), R_STEEL)

    # Touch-screen control panel (front face)
    box("ControlPanel",   0.50, 0.05, 0.36, (-0.5, -0.36, 0.72), R_TOUCH_UI)

    # 4 supply tanks on top of machine
    tank_cols = [R_LIQUID_BLUE, R_ACRYLIC, R_LIQUID_BLUE, R_ACRYLIC]
    for i,col in enumerate(tank_cols):
        tx = -0.66 + i*0.44
        cylinder(f"SupplyTank_{i}",    0.14, 0.55, 20, (tx, 0.0, 1.26), R_ACRYLIC)
        cylinder(f"SupplyLiquid_{i}",  0.12, 0.35, 20, (tx, 0.0, 1.26), col)
        box(f"TankCap_{i}",            0.30, 0.30, 0.04, (tx, 0.0, 1.81), R_STEEL)

    # Filling nozzle carousel arm
    box("NozzleArm",      1.60, 0.06, 0.05, (0, 0.0, 1.22), R_STEEL)
    for i in range(4):
        nx = -0.60 + i*0.40
        cylinder(f"FillingNozzle_{i}", 0.025, 0.18, 12, (nx, 0.0, 1.04), R_STEEL)
        cylinder(f"NozzleTip_{i}",     0.018, 0.04, 10, (nx, 0.0, 0.86), R_AIR_LINE)

    # Conveyor tray (front)
    box("ConveyorTray",   1.70, 0.30, 0.04, (0, -0.52, 0.88), R_CONVEYOR)
    box("ConveyorSideL",  0.04, 0.30, 0.06, (-0.87,-0.52, 0.88), R_STEEL)
    box("ConveyorSideR",  0.04, 0.30, 0.06, ( 0.87,-0.52, 0.88), R_STEEL)

    # Vape cartridges / bottles on conveyor
    for i in range(6):
        cx = -0.62 + i*0.24
        cylinder(f"VapeCartridge_{i}", 0.04, 0.12, 16, (cx, -0.52, 0.92), R_ACRYLIC)

    # Pneumatic air lines
    box("AirLineMain",    0.02, 0.55, 0.02, (0.78, 0.0, 0.80), R_AIR_LINE)
    for i in range(4):
        nx = -0.60 + i*0.40
        box(f"AirLineBranch_{i}", 0.02, 0.02, 0.24, (nx, 0.0, 0.82), R_AIR_LINE)

    shell = kit.join(parts, "Prop_Filling_Machine")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_filling_machine_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_filling_machine.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_filling_machine.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_filling_machine_preview.png")
        shutil.copy2(OUT_DIR / "atlas_filling_machine.png", TEXTURES_DIR / "atlas_filling_machine.png")
        print("[FillingMachine] deployed.")
    except Exception as e: print(f"[FillingMachine] notice: {e}")

if __name__ == "__main__": main()
