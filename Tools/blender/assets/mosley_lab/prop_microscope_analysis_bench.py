"""Mosley Lab: Prop - Compound Analysis & Microscope Table (~3000 Tris).

A high-magnification purity and contaminant analysis workstation:
- Heavy solid oak & laminate inspection table with drawer pedestal.
- Binocular compound optical laboratory microscope: dual eyepieces, rotating nosepiece with 4 objective lenses, mechanical X-Y stage with slide clip, condenser iris, focus coarse/fine adjustment wheels.
- Glass Petri dishes with crystallized chemical compound residue.
- Slide storage box with prepared glass specimen slides.
- Flexible gooseneck LED task lamp with illuminated reflector head.
- Reagent dropper bottles & solvent wash flask.
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

R_MICROSCOPE_BODY = (0,   256, 256, 256)   # White enamel lab instrument coating
R_DESK_WOOD       = (256, 256, 256, 256)   # Polished dark lab oak timber & drawers
R_PETRI_GLASS     = (0,   128, 128, 128)   # Clear glass petri dishes & crystalline residue
R_BRASS_OPTICS    = (128, 128, 128, 128)   # Gold/brass objective lens barrels & stage clips
R_LAMP_SHADE      = (256, 128, 128, 128)   # Matte black task lamp & gooseneck
R_SPECIMEN_SLIDES = (384, 128, 128, 128)   # Frosted glass microscope slides with stained specimens


def paint_atlas():
    a = Atlas(S, seed=6162)
    # 1. Microscope White Enamel (R_MICROSCOPE_BODY)
    x,y,w,h = R_MICROSCOPE_BODY
    a.rect(x,y,w,h,(0.92,0.93,0.95)); a.noise(x,y,w,h,0.01)
    for ry in range(y,y+h,32): a.rect(x,ry,w,2,(0.75,0.76,0.78))

    # 2. Desk Oak (R_DESK_WOOD)
    x,y,w,h = R_DESK_WOOD
    a.rect(x,y,w,h,(0.45,0.28,0.16)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,16): a.rect(x,ry,w,2,(0.32,0.18,0.10))

    # 3. Petri Glass (R_PETRI_GLASS)
    x,y,w,h = R_PETRI_GLASS
    a.rect(x,y,w,h,(0.40,0.60,0.70))
    a.disc(x+w//2, y+h//2, 36, (0.75,0.25,0.65)) # Purple crystalline residue
    a.noise(x,y,w,h,0.015)

    # 4. Brass Optics (R_BRASS_OPTICS)
    x,y,w,h = R_BRASS_OPTICS
    a.rect(x,y,w,h,(0.88,0.72,0.20)); a.noise(x,y,w,h,0.02)
    for ry in range(y,y+h,12): a.rect(x,ry,w,2,(0.65,0.50,0.10))

    # 5. Lamp Black (R_LAMP_SHADE)
    x,y,w,h = R_LAMP_SHADE
    a.rect(x,y,w,h,(0.15,0.16,0.18)); a.noise(x,y,w,h,0.02)
    a.disc(x+w//2, y+h//2, 28, (0.95,0.92,0.65)) # Lamp bulb light

    # 6. Specimen Slides (R_SPECIMEN_SLIDES)
    x,y,w,h = R_SPECIMEN_SLIDES
    a.rect(x,y,w,h,(0.75,0.85,0.90))
    for ry in range(y+8,y+h-8,14):
        a.rect(x+8,ry,w-16,8,(0.85,0.20,0.40)) # Stained cell samples

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return a.to_image("atlas_microscope_bench", OUT_DIR)


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
    mat = material_for(img,"mat_microscope_bench")
    parts=[]

    def box(name,w,d,h,at,region=R_DESK_WOOD):
        o=kit.make_box(name,w,d,h,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    def cylinder(name,r,h,segs=20,at=(0,0,0),region=R_MICROSCOPE_BODY):
        o=cyl(name,r,h,segs,at); o.data.materials.append(mat)
        kit.map_faces_to_region(o,region,S); parts.append(o); return o

    # Solid Oak Lab Table & Drawer Pedestal (Z = 0.0 to 0.85m)
    box("TableTop",        2.2, 0.8, 0.08, (0, 0, 0.85), R_DESK_WOOD)
    box("TableLegLeft",    0.08,0.76,0.85, (-1.02, 0, 0.0), R_DESK_WOOD)
    box("TableLegRight",   0.08,0.76,0.85, ( 1.02, 0, 0.0), R_DESK_WOOD)
    # Right-side 3-drawer pedestal unit
    box("DrawerPedestal",  0.55, 0.70, 0.75, (0.70, 0.0, 0.10), R_DESK_WOOD)
    for di in range(3):
        box(f"DrawerHandle_{di}", 0.15, 0.04, 0.04, (0.70, -0.37, 0.25 + di*0.22), R_BRASS_OPTICS)

    # 1. COMPOUND BINOCULAR MICROSCOPE (Center: X = -0.25m, Y = -0.05m)
    # Heavy horseshoe base & curved limb arm
    box("ScopeBase",       0.32, 0.38, 0.08, (-0.25, -0.05, 0.93), R_MICROSCOPE_BODY)
    cylinder("ScopeLimbPillar", 0.06, 0.45, 16, (-0.25, 0.10, 1.01), R_MICROSCOPE_BODY)
    box("ScopeArmCurve",   0.14, 0.22, 0.30, (-0.25, 0.06, 1.35), R_MICROSCOPE_BODY)

    # Mechanical stage with slide clip
    box("MechanicalStage", 0.30, 0.28, 0.04, (-0.25, -0.05, 1.25), R_LAMP_SHADE)
    box("SlideClipL",      0.08, 0.02, 0.02, (-0.32, -0.05, 1.29), R_BRASS_OPTICS)
    box("SlideClipR",      0.08, 0.02, 0.02, (-0.18, -0.05, 1.29), R_BRASS_OPTICS)

    # Revolving nosepiece turret & 4 objective lenses
    cylinder("NosepieceTurret", 0.07, 0.05, 16, (-0.25, -0.05, 1.45), R_BRASS_OPTICS)
    for oi in range(4):
        ang = math.pi/2 * oi
        ox = -0.25 + 0.04 * math.cos(ang)
        oy = -0.05 + 0.04 * math.sin(ang)
        cylinder(f"ObjectiveLens_{oi}", 0.018, 0.08, 12, (ox, oy, 1.37), R_BRASS_OPTICS)

    # Binocular head with dual angled eyepieces
    box("BinocularHead",   0.18, 0.14, 0.12, (-0.25, -0.02, 1.62), R_MICROSCOPE_BODY)
    cylinder("EyepieceL",  0.022, 0.16, 14, (-0.30, -0.10, 1.70), R_LAMP_SHADE)
    cylinder("EyepieceR",  0.022, 0.16, 14, (-0.20, -0.10, 1.70), R_LAMP_SHADE)

    # Coarse & Fine Focus Adjustment Knobs
    cylinder("CoarseKnobL", 0.04, 0.04, 16, (-0.36, 0.08, 1.22), R_BRASS_OPTICS)
    cylinder("CoarseKnobR", 0.04, 0.04, 16, (-0.14, 0.08, 1.22), R_BRASS_OPTICS)

    # 2. PETRI DISHES & SPECIMEN SLIDE BOX
    # 2 Glass Petri dishes
    cylinder("PetriDish1", 0.10, 0.025, 20, (0.25, -0.15, 0.93), R_PETRI_GLASS)
    cylinder("PetriDish2", 0.10, 0.025, 20, (0.42, -0.12, 0.93), R_PETRI_GLASS)

    # Wooden slide preparation box
    box("SlideBox",        0.26, 0.18, 0.08, (0.35, 0.18, 0.93), R_DESK_WOOD)
    box("SlideInside",     0.22, 0.02, 0.06, (0.35, 0.18, 0.97), R_SPECIMEN_SLIDES)

    # 3. GOOSENECK LED TASK LAMP (Left: X = -0.80m)
    cylinder("LampBase",   0.09, 0.04, 16, (-0.80, 0.18, 0.93), R_LAMP_SHADE)
    box("Gooseneck1",      0.02, 0.02, 0.40, (-0.80, 0.18, 0.97), R_LAMP_SHADE)
    box("Gooseneck2",      0.25, 0.02, 0.02, (-0.68, 0.18, 1.35), R_LAMP_SHADE)
    cylinder("LampHead",   0.07, 0.12, 16, (-0.55, 0.18, 1.30), R_LAMP_SHADE)

    shell = kit.join(parts, "Prop_Microscope_Bench")
    kit.finalize(shell); kit.report_stats(shell)

    preview = OUT_DIR / "prop_microscope_analysis_bench_preview.png"
    kit.iso_preview(preview, [shell], resolution=1024)
    glb = OUT_DIR / "prop_microscope_analysis_bench.glb"
    kit.export_glb(glb, [shell])

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True); TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(glb,     DEPLOY_DIR   / "prop_microscope_analysis_bench.glb")
        shutil.copy2(preview, TEXTURES_DIR / "prop_microscope_analysis_bench_preview.png")
        shutil.copy2(OUT_DIR / "atlas_microscope_bench.png", TEXTURES_DIR / "atlas_microscope_bench.png")
        print("[MicroscopeBench] deployed.")
    except Exception as e: print(f"[MicroscopeBench] notice: {e}")


if __name__ == "__main__": main()
