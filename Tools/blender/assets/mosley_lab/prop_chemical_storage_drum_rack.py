"""Mosley Lab: Prop - Chemical Storage & Drum Rack (~3000 Tris).

Industrial bulk solvent and PG/VG chemical precursor storage:
- Heavy yellow steel pallet racking frame with spill containment bund sump tray.
- 4x 55-gallon steel chemical drums (2 blue, 2 hazard yellow) with bungs and hazard diamond placards.
- 3x 25-litre semi-translucent high-density polyethylene (HDPE) carboys of vegetable glycerin (VG) and propylene glycol (PG).
- Rotary manual hand siphon drum pump with dispensing nozzle.
- Grounding anti-static copper clamp cables.
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

R_RACK_YELLOW   = (0,   256, 256, 256)   # Safety yellow heavy pallet rack frame
R_DRUM_BLUE     = (256, 256, 256, 256)   # 55-gallon industrial blue steel drum
R_DRUM_YELLOW   = (0,   128, 128, 128)   # Flammable hazard yellow drum with Hazmat diamond
R_CARBOY_WHITE  = (128, 128, 128, 128)   # Translucent HDPE carboy container with blue cap
R_SUMP_GRATE    = (256, 128, 128, 128)   # Galvanized steel spill containment mesh grate
R_BRASS_PUMP    = (384, 128, 128, 128)   # Cast iron / brass rotary hand pump & grounding clamp


def paint_atlas():
    a = Atlas(S, seed=5150)
    # 1. Safety Yellow (R_RACK_YELLOW)
    x,y,w,h = R_RACK_YELLOW
    a.rect(x,y,w,h,(0.90,0.76,0.12)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,28): a.rect(x,ry,w,2,(0.70,0.58,0.08))

    # 2. Blue Drum (R_DRUM_BLUE)
    x,y,w,h = R_DRUM_BLUE
    a.rect(x,y,w,h,(0.12,0.32,0.65)); a.noise(x,y,w,h,0.02)
    # Drum chimes / rolling ribs
    for ry in range(y+40,y+h-40,60): a.rect(x,ry,w,8,(0.08,0.22,0.48))

    # 3. Yellow Hazard Drum (R_DRUM_YELLOW)
    x,y,w,h = R_DRUM_YELLOW
    a.rect(x,y,w,h,(0.88,0.72,0.15))
    # Red hazard diamond placard
    cx, cy = x + w//2, y + h//2
    a.disc(cx, cy, 24, (0.85,0.15,0.12))
    a.disc(cx, cy, 18, (0.95,0.95,0.95))
    a.noise(x,y,w,h,0.015)

    # 4. HDPE Carboy (R_CARBOY_WHITE)
    x,y,w,h = R_CARBOY_WHITE
    a.rect(x,y,w,h,(0.88,0.90,0.92)); a.noise(x,y,w,h,0.01)
    a.rect(x+8, y+8, w-16, 20, (0.15,0.45,0.75)) # Blue liquid level / label

    # 5. Sump Grate (R_SUMP_GRATE)
    x,y,w,h = R_SUMP_GRATE
    a.rect(x,y,w,h,(0.40,0.42,0.45))
    for rx in range(x,x+w,12): a.rect(rx,y,3,h,(0.25,0.27,0.30))
    for ry in range(y,y+h,12): a.rect(x,ry,w,3,(0.25,0.27,0.30))

    # 6. Brass Pump (R_BRASS_PUMP)
    x,y,w,h = R_BRASS_PUMP
    a.rect(x,y,w,h,(0.78,0.58,0.18)); a.noise(x,y,w,h,0.02)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_chemical_drum_rack", OUT_DIR)


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
    mat = material_for(img,"mat_chemical_drum_rack")
    parts=[]

    def box(name,w,d,h,at,region=R_RACK_YELLOW):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_DRUM_BLUE):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Spill Containment Bund Base Sump (Z = 0.0 to 0.22m)
    box("SpillBundTray", 2.6, 1.2, 0.22, (0, 0, 0.0), R_RACK_YELLOW)
    box("SpillMeshGrate",2.5, 1.1, 0.04, (0, 0, 0.22), R_SUMP_GRATE)

    # 4 Heavy Steel Pallet Rack Upright Columns
    for cx, cy in [(-1.25, -0.55), (1.25, -0.55), (-1.25, 0.55), (1.25, 0.55)]:
        box(f"RackUpright_{cx:.0f}_{cy:.0f}", 0.10, 0.10, 2.2, (cx, cy, 0.0), R_RACK_YELLOW)

    # Cross beams at top & mid
    box("RackBeamTopF", 2.6, 0.08, 0.12, (0, -0.55, 2.10), R_RACK_YELLOW)
    box("RackBeamTopB", 2.6, 0.08, 0.12, (0,  0.55, 2.10), R_RACK_YELLOW)
    box("RackBeamMidF", 2.6, 0.08, 0.10, (0, -0.55, 1.20), R_RACK_YELLOW)
    box("RackBeamMidB", 2.6, 0.08, 0.10, (0,  0.55, 1.20), R_RACK_YELLOW)

    # 1. LOWER TIER: 4x 55-GALLON STEEL DRUMS (Z = 0.26m)
    drum_positions = [
        (-0.75, -0.22, R_DRUM_BLUE, "BlueDrum1"),
        (-0.25, -0.22, R_DRUM_YELLOW, "YellowDrum1"),
        ( 0.25, -0.22, R_DRUM_BLUE, "BlueDrum2"),
        ( 0.75, -0.22, R_DRUM_YELLOW, "YellowDrum2"),
    ]
    for dx, dy, dcol, dname in drum_positions:
        cylinder(f"{dname}_Body",  0.26, 0.90, 24, (dx, dy, 0.26), dcol)
        # Drum top chime lip
        cylinder(f"{dname}_Lip",   0.28, 0.04, 24, (dx, dy, 1.16), dcol)
        # 2" threaded bung
        cylinder(f"{dname}_Bung",  0.03, 0.03, 12, (dx + 0.12, dy, 1.20), R_BRASS_PUMP)

    # Manual rotary hand siphon pump mounted on first drum
    cylinder("SiphonStandpipe", 0.02, 0.65, 12, (-0.75 + 0.12, -0.22, 1.20), R_BRASS_PUMP)
    cylinder("PumpCrankHousing", 0.06, 0.08, 16, (-0.75 + 0.12, -0.22, 1.85), R_BRASS_PUMP)
    box("PumpHandCrank",        0.18, 0.03, 0.03, (-0.75 + 0.20, -0.22, 1.85), R_BRASS_PUMP)

    # 2. UPPER TIER: 3x 25-LITRE HDPE CARBOYS OF PG/VG SOLVENTS (Z = 1.30m)
    box("UpperShelfGrate", 2.5, 1.1, 0.04, (0, 0, 1.26), R_SUMP_GRATE)
    for ci, cx in enumerate([-0.70, 0.0, 0.70]):
        box(f"CarboyBody_{ci}", 0.38, 0.38, 0.55, (cx, 0.0, 1.30), R_CARBOY_WHITE)
        cylinder(f"CarboyCap_{ci}", 0.06, 0.05, 16, (cx, 0.10, 1.85), R_DRUM_BLUE)
        box(f"CarboyHandle_{ci}", 0.05, 0.20, 0.08, (cx, 0.0, 1.85), R_CARBOY_WHITE)

    # Grounding anti-static cables
    box("GroundingWire", 2.4, 0.02, 0.02, (0, -0.50, 0.40), R_BRASS_PUMP)

    shell = kit.join(parts, "Prop_Chemical_Drum_Rack")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_chemical_drum_rack_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_chemical_drum_rack.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_chemical_drum_rack.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_chemical_drum_rack_preview.png")
        shutil.copy2(OUT_DIR / "atlas_chemical_drum_rack.png", TEXTURES_DIR / "atlas_chemical_drum_rack.png")
        print("[ChemicalDrumRack] deployed.")
    except Exception as e: print(f"[ChemicalDrumRack] notice: {e}")


if __name__ == "__main__": main()
