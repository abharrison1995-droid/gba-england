"""Mosley Lab: Prop - Server Rack & Lab Computer Terminal (~3000 Tris).

A wall-mounted or floor-standing rack for lab data logging & process control:
- Black 42U server rack cabinet with vented mesh front door.
- 6 rack-mount units (1U each): servers, patch panels, UPS battery backup.
- Lab workstation desk beside it: curved monitor, keyboard tray, mouse.
- Cable management arms behind rack units.
- Status LED indicator strips on rack front (green, amber, red).
- Power distribution unit with visible cable runs.
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

R_RACK_BLACK = (0,   256, 256, 256)
R_MESH_VENT  = (256, 256, 256, 256)
R_LED_GREEN  = (0,   128, 128, 128)
R_MONITOR    = (128, 128, 128, 128)
R_DESK_GREY  = (256, 128, 128, 128)
R_CABLE_DARK = (384, 128, 128, 128)

def paint_atlas():
    a = Atlas(S, seed=3001)
    x,y,w,h = R_RACK_BLACK
    a.rect(x,y,w,h,(0.10,0.10,0.11)); a.noise(x,y,w,h,0.015)
    for ry in range(y,y+h,12): a.rect(x,ry,w,1,(0.18,0.18,0.20))
    x,y,w,h = R_MESH_VENT
    a.rect(x,y,w,h,(0.16,0.16,0.18))
    for ry in range(y,y+h,5):
        for rx in range(x,x+w,6): a.rect(rx,ry,3,3,(0.06,0.06,0.07))
    x,y,w,h = R_LED_GREEN
    a.rect(x,y,w,h,(0.08,0.08,0.08))
    for rx in range(x+4,x+w-4,10):
        a.disc(rx,y+h//3,3,(0.10,0.90,0.20))
        a.disc(rx,y+2*h//3,3,(0.90,0.60,0.08))
    x,y,w,h = R_MONITOR
    a.rect(x,y,w,h,(0.05,0.06,0.08))
    a.rect(x+4,y+4,w-8,h-16,(0.08,0.22,0.38))
    a.rect(x+8,y+8,w//2-8,20,(0.15,0.60,0.85))
    x,y,w,h = R_DESK_GREY
    a.rect(x,y,w,h,(0.62,0.63,0.65)); a.noise(x,y,w,h,0.02)
    x,y,w,h = R_CABLE_DARK
    a.rect(x,y,w,h,(0.14,0.14,0.15)); a.noise(x,y,w,h,0.025)
    for rx in range(x,x+w,10): a.rect(rx,y,2,h,(0.20,0.20,0.22))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_server_rack", OUT_DIR)

def cyl(name, r, h, segs=12, at=(0,0,0)):
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
    mat = material_for(img,"mat_server_rack")
    parts=[]
    def box(name,w,d,h,at,region=R_RACK_BLACK):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Server rack cabinet
    box("RackBody",      0.60, 0.80, 1.80, (-0.80,  0.0, 0.0), R_RACK_BLACK)
    box("RackDoorFront", 0.58, 0.04, 1.76, (-0.80, -0.42, 0.02), R_MESH_VENT)
    box("RackTop",       0.62, 0.82, 0.04, (-0.80,  0.0, 1.80), R_RACK_BLACK)

    # 6 rack-mount units (1U = 4.4cm high)
    rack_labels = [R_LED_GREEN, R_RACK_BLACK, R_LED_GREEN, R_MESH_VENT, R_LED_GREEN, R_RACK_BLACK]
    for i,col in enumerate(rack_labels):
        rz = 0.12 + i * 0.24
        box(f"RackUnit_{i}",   0.54, 0.70, 0.18, (-0.80, 0.0, rz), col)
        box(f"RackUnitLEDs_{i}",0.50,0.02, 0.06, (-0.80,-0.40,rz+0.06), R_LED_GREEN)

    # Cable management arms
    for i in range(3):
        rz = 0.20 + i*0.48
        box(f"CableArm_{i}",   0.55, 0.20, 0.03, (-0.80, 0.36, rz), R_CABLE_DARK)

    # PDU / power strip on side
    box("PDUStrip",      0.06, 0.70, 0.80, (-1.12, 0.0, 0.50), R_RACK_BLACK)
    for i in range(6):
        box(f"PDUSocket_{i}", 0.06, 0.05, 0.05, (-1.15, -0.25+i*0.10, 0.52+i*0.04), R_LED_GREEN)

    # Lab desk beside rack
    box("DeskTop",       1.20, 0.65, 0.05, (0.55, 0.0, 0.76), R_DESK_GREY)
    box("DeskLeftLeg",   0.06, 0.06, 0.76, (0.0,  -0.28, 0.0), R_DESK_GREY)
    box("DeskRightLeg",  0.06, 0.06, 0.76, (1.10, -0.28, 0.0), R_DESK_GREY)
    box("DeskBackLeg1",  0.06, 0.06, 0.76, (0.0,   0.28, 0.0), R_DESK_GREY)
    box("DeskBackLeg2",  0.06, 0.06, 0.76, (1.10,  0.28, 0.0), R_DESK_GREY)

    # Monitor on desk
    box("MonitorScreen", 0.55, 0.04, 0.34, (0.55, -0.26, 0.81), R_MONITOR)
    box("MonitorBase",   0.20, 0.18, 0.03, (0.55, -0.18, 0.81), R_RACK_BLACK)
    box("MonitorStand",  0.04, 0.04, 0.14, (0.55, -0.22, 0.81), R_RACK_BLACK)

    # Keyboard + mouse
    box("Keyboard",      0.34, 0.12, 0.02, (0.55, -0.14, 0.81), R_DESK_GREY)
    box("Mouse",         0.07, 0.11, 0.02, (0.20, -0.14, 0.81), R_RACK_BLACK)

    shell = kit.join(parts, "Prop_Server_Rack")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_server_rack_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_server_rack.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_server_rack.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_server_rack_preview.png")
        shutil.copy2(OUT_DIR / "atlas_server_rack.png", TEXTURES_DIR / "atlas_server_rack.png")
        print("[ServerRack] deployed.")
    except Exception as e: print(f"[ServerRack] notice: {e}")

if __name__ == "__main__": main()
