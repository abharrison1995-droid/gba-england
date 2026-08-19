"""Mosley Lab: Prop - Vape Quality Control & Smoke Testing Rig (~3000 Tris).

A testing station for measuring vape coil resistance, battery output, and vapor density:
- Heavy test bench with aluminium extrusion frame and overhead tool rack.
- Cylindrical acrylic puff-emulator smoke chamber with active vapor flow simulation.
- Digital dual-channel oscilloscope with sine waveform display.
- Benchtop digital multimeter with test lead probes (red/black cables).
- Resistance ohm meter reader block with test vape pod inserted.
- Tray of tested disposable vapes, replacement mesh coils, and lithium battery cells.
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

R_ALU_FRAME    = (0,   256, 256, 256)   # Silver anodized aluminium profile & workbench
R_SCOPE_SCREEN = (256, 256, 256, 256)   # Oscilloscope LCD screen with green waveform
R_SMOKE_CHAMBER= (0,   128, 128, 128)   # Clear acrylic vacuum chamber & dense vapour cloud
R_VAPE_DEVICES = (128, 128, 128, 128)   # Colourful anodized vape pod bodies & LED indicators
R_TEST_LEADS   = (256, 128, 128, 128)   # Red & black silicone probe wires & gold alligator clips
R_BATTERY_CELL = (384, 128, 128, 128)   # 18650 lithium battery cells & wrap labels


def paint_atlas():
    a = Atlas(S, seed=9041)
    # 1. Aluminium Frame (R_ALU_FRAME)
    x,y,w,h = R_ALU_FRAME
    a.rect(x,y,w,h,(0.70,0.72,0.75)); a.noise(x,y,w,h,0.015)
    for rx in range(x,x+w,20): a.rect(rx,y,2,h,(0.55,0.57,0.60))

    # 2. Oscilloscope Screen (R_SCOPE_SCREEN)
    x,y,w,h = R_SCOPE_SCREEN
    a.rect(x,y,w,h,(0.04,0.06,0.08))
    # Grid lines
    for gy in range(y+10,y+h-10,20): a.rect(x+10,gy,w-20,1,(0.08,0.25,0.18))
    for gx in range(x+10,x+w-10,20): a.rect(gx,y+10,1,h-20,(0.08,0.25,0.18))
    # Sine wave waveform (bright neon green)
    for wx in range(x+12, x+w-12):
        rel_x = (wx - x) / 20.0
        wy = int(y + h//2 + math.sin(rel_x) * 45)
        if y < wy < y+h: a.rect(wx,wy,2,3,(0.10,0.95,0.30))

    # 3. Smoke Chamber & Vapor (R_SMOKE_CHAMBER)
    x,y,w,h = R_SMOKE_CHAMBER
    a.rect(x,y,w,h,(0.85,0.90,0.95)); a.noise(x,y,w,h,0.05)
    for ry in range(y+10,y+h-10,16): a.rect(x+10,ry,w-20,8,(0.95,0.98,1.00))

    # 4. Vape Devices (R_VAPE_DEVICES)
    x,y,w,h = R_VAPE_DEVICES
    a.rect(x,y,w,h,(0.85,0.18,0.22)) # Red pod
    a.rect(x+w//3,y,w//3,h,(0.15,0.65,0.85)) # Cyan pod
    a.rect(x+2*w//3,y,w//3,h,(0.55,0.15,0.80)) # Purple pod
    a.noise(x,y,w,h,0.01)

    # 5. Test Leads (R_TEST_LEADS)
    x,y,w,h = R_TEST_LEADS
    a.rect(x,y,w//2,h,(0.82,0.12,0.12)) # Red lead
    a.rect(x+w//2,y,w//2,h,(0.12,0.12,0.14)) # Black lead

    # 6. Battery Cells (R_BATTERY_CELL)
    x,y,w,h = R_BATTERY_CELL
    a.rect(x,y,w,h,(0.18,0.65,0.35)) # Green battery wrap
    a.rect(x+8,y+h-24,w-16,14,(0.85,0.85,0.85))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_vape_testing_rig", OUT_DIR)


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
    mat = material_for(img,"mat_vape_testing")
    parts=[]

    def box(name,w,d,h,at,region=R_ALU_FRAME):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_SMOKE_CHAMBER):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Main Workbench & Overhead Gantry
    box("BenchWorktop",   2.6, 0.8, 0.08, (0, 0, 0.85), R_ALU_FRAME)
    box("BenchLegL",      0.08,0.76,0.85, (-1.22, 0, 0.0), R_ALU_FRAME)
    box("BenchLegR",      0.08,0.76,0.85, ( 1.22, 0, 0.0), R_ALU_FRAME)
    box("OverheadGantryL",0.06,0.06,1.10, (-1.22, 0.35, 0.93), R_ALU_FRAME)
    box("OverheadGantryR",0.06,0.06,1.10, ( 1.22, 0.35, 0.93), R_ALU_FRAME)
    box("OverheadTopBeam",2.50,0.06,0.06, (0, 0.35, 2.00), R_ALU_FRAME)

    # 1. SMOKE / PUFF EMULATOR CHAMBER (Center: X = 0.0m)
    box("ChamberBasePlinth",0.45, 0.45, 0.08, (0.0, 0.0, 0.93), R_ALU_FRAME)
    cylinder("AcrylicCylinder", 0.18, 0.55, 24, (0.0, 0.0, 1.01), R_SMOKE_CHAMBER)
    cylinder("VaporCloudCore",  0.14, 0.45, 20, (0.0, 0.0, 1.05), R_SMOKE_CHAMBER)
    box("ChamberTopLid",    0.42, 0.42, 0.06, (0.0, 0.0, 1.56), R_ALU_FRAME)
    # Test vape pod clamped inside chamber
    box("PuffVapePod",      0.06, 0.04, 0.22, (0.0, 0.0, 1.15), R_VAPE_DEVICES)

    # 2. DUAL-CHANNEL OSCILLOSCOPE (Left: X = -0.75m)
    box("OscilloscopeBody", 0.55, 0.40, 0.35, (-0.75, 0.05, 0.93), R_ALU_FRAME)
    box("ScopeScreenBezel", 0.38, 0.02, 0.26, (-0.75, -0.16, 0.97), R_SCOPE_SCREEN)
    # Knobs & BNC connectors
    for ki in range(4):
        kx = -0.92 + ki * 0.11
        cylinder(f"ScopeKnob_{ki}", 0.02, 0.03, 12, (kx, -0.17, 1.22), R_ALU_FRAME)

    # 3. BENCHTOP DIGITAL MULTIMETER & OHM METER (Right: X = 0.75m)
    box("MultimeterBody",  0.42, 0.35, 0.18, (0.75, 0.05, 0.93), R_TEST_LEADS)
    box("MeterLCDScreen",   0.28, 0.02, 0.10, (0.75, -0.13, 0.98), R_SCOPE_SCREEN)

    # Test lead wires draped on bench
    box("RedLeadWire",     0.02, 0.35, 0.02, (0.60, -0.22, 0.93), R_TEST_LEADS)
    box("BlackLeadWire",   0.02, 0.35, 0.02, (0.90, -0.22, 0.93), R_TEST_LEADS)

    # 4. TRAY OF TESTED VAPE PODS & 18650 BATTERIES
    box("PartsTray",       0.55, 0.30, 0.04, (0.0, -0.25, 0.93), R_ALU_FRAME)
    for vi in range(5):
        vx = -0.20 + vi * 0.10
        box(f"TestedPod_{vi}", 0.04, 0.12, 0.03, (vx, -0.25, 0.97), R_VAPE_DEVICES)

    # Row of lithium batteries on riser shelf
    for bi in range(6):
        bx = -0.80 + bi * 0.12
        cylinder(f"BattCell_{bi}", 0.02, 0.10, 14, (bx, 0.32, 0.93), R_BATTERY_CELL)

    shell = kit.join(parts, "Prop_Vape_Testing_Rig")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_vape_testing_rig_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_vape_testing_rig.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_vape_testing_rig.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_vape_testing_rig_preview.png")
        shutil.copy2(OUT_DIR / "atlas_vape_testing_rig.png", TEXTURES_DIR / "atlas_vape_testing_rig.png")
        print("[VapeTestingRig] deployed.")
    except Exception as e: print(f"[VapeTestingRig] notice: {e}")


if __name__ == "__main__": main()
