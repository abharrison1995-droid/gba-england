"""Procedural Data Center Bandit Camp Assets (Mad Max Cyberpunk Style).

Nomadic rogue tech camps setting up illegal wild data centres / mining rigs.
- Modular tileable ramshackle shelters
- Shipping container server shacks
- Elevated rig lookout tower
- Generator / power hub
- Outdoor server clusters, satellite uplink dish, radiator cooling units

Executes inside Blender via bpy_runner.py.
"""

import sys
from pathlib import Path
import bmesh
from mathutils import Vector

# Add parent path for mass_kit
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent.parent / "lib"))

import mass_kit as mkit

# ==============================================================================
# PALETTE
# ==============================================================================
PAL_DATACAMP = [
    (0.42, 0.44, 0.46),  # 0: Weathered Scrap Metal / Corrugated Steel
    (0.55, 0.28, 0.16),  # 1: Rusted Iron / Scrap Sheets
    (0.18, 0.18, 0.20),  # 2: Matte Black Server Racks & Rubber Cables
    (0.85, 0.65, 0.15),  # 3: Industrial Hazard Yellow / Warning Stripes
    (0.18, 0.38, 0.55),  # 4: Blue Tarp / Heavy Canvas Weatherproofing
    (0.58, 0.42, 0.28),  # 5: Plywood / Scaffolding Timber Planks
    (0.15, 0.85, 0.75),  # 6: Cyber Neon Cyan (Server Blinking Lights / Screens)
    (0.85, 0.40, 0.18),  # 7: Copper Heat Pipes / Hot Exhaust Orange
]


# ==============================================================================
# BUILDINGS & SHELTERS
# ==============================================================================

def build_datacamp_terrace_01_modular_row():
    """10m wide tileable ramshackle tech shelter row for camp perimeter / streets."""
    bm = bmesh.new()
    faces = []
    # 10m wide, 7.5m deep, 4.5m high modular shelter
    # Scrap metal & plywood main shelter base
    faces += mkit.make_cuboid(bm, 10.0, 7.0, 3.2, center=(0, 0, 1.6), color_idx=0)
    
    # Asymmetric scrap metal lean-to roof panels (slanted front-to-back)
    faces += mkit.make_cuboid(bm, 5.2, 7.6, 0.15, center=(-2.5, 0, 3.4), color_idx=1)
    faces += mkit.make_cuboid(bm, 5.2, 7.6, 0.15, center=(2.5, 0, 3.6), color_idx=0)
    
    # Weatherproof Blue Tarpaulin draped over Unit A
    faces += mkit.make_cuboid(bm, 4.8, 4.0, 0.08, center=(-2.4, 1.0, 3.52), color_idx=4)
    
    # 2x Recessed Entrances with reinforced iron scrap doors & hazard yellow frames
    for dx in (-2.5, 2.5):
        faces += mkit.make_cuboid(bm, 1.4, 0.1, 2.4, center=(dx, -3.52, 1.2), color_idx=2)
        faces += mkit.make_cuboid(bm, 1.6, 0.15, 0.15, center=(dx, -3.53, 2.45), color_idx=3)
        
    # Roof-Mounted Server Cooling Exchanger on Unit A (X: -2.5)
    faces += mkit.make_cuboid(bm, 2.2, 1.8, 1.0, center=(-2.5, -1.0, 4.0), color_idx=2)
    # Dual cooling fans
    faces += mkit.make_cylinder(bm, 0.35, 0.1, segs=8, center=(-3.0, -1.0, 4.55), color_idx=0)
    faces += mkit.make_cylinder(bm, 0.35, 0.1, segs=8, center=(-2.0, -1.0, 4.55), color_idx=0)
    
    # Roof Antenna & Solar Array on Unit B (X: 2.5)
    faces += mkit.make_cuboid(bm, 2.4, 1.6, 0.1, center=(2.5, 0.5, 3.9), color_idx=6)
    # Antenna mast
    faces += mkit.make_cylinder(bm, 0.04, 2.5, segs=6, center=(4.0, -1.5, 4.8), color_idx=2)
    
    # Thick bundled cables running along facade
    faces += mkit.make_cylinder(bm, 0.06, 9.8, segs=6, center=(0, -3.6, 2.8), color_idx=2)
    # Status terminal screens glowing cyan
    faces += mkit.make_cuboid(bm, 0.6, 0.08, 0.5, center=(-0.5, -3.55, 1.6), color_idx=6)
    faces += mkit.make_cuboid(bm, 0.6, 0.08, 0.5, center=(0.5, -3.55, 1.6), color_idx=6)

    mkit.apply_bmesh_and_export("datacamp_terrace_01_modular_row", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


def build_datacamp_shack_01_server_container():
    """Retrofit shipping container data shack with rooftop server arrays and satellite link."""
    bm = bmesh.new()
    faces = []
    # Shipping container body: 8m wide, 4m deep, 3.2m high
    faces += mkit.make_cuboid(bm, 8.0, 4.0, 3.0, center=(0, 0, 1.5), color_idx=1) # Rusted container
    # Corrugated vertical ribs
    for rx in (-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5):
        faces += mkit.make_cuboid(bm, 0.1, 0.12, 2.9, center=(rx, -2.05, 1.5), color_idx=0)
        
    # Reinforced Security Airlock Door (Left side)
    faces += mkit.make_cuboid(bm, 1.4, 0.15, 2.4, center=(-2.5, -2.02, 1.2), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.0, 0.1, 2.1, center=(-2.5, -2.06, 1.15), color_idx=2)
    
    # Exterior Heavy-Duty Heat Sink & Radiator Exhaust (Right side)
    faces += mkit.make_cuboid(bm, 2.6, 0.6, 1.8, center=(2.0, -2.25, 1.4), color_idx=2)
    for fx in (1.2, 2.0, 2.8):
        faces += mkit.make_cylinder(bm, 0.28, 0.1, segs=8, center=(fx, -2.55, 1.4), color_idx=7)
        
    # Rooftop Server Rack Housing with Blue Weatherproof Tarp
    faces += mkit.make_cuboid(bm, 3.5, 2.6, 1.6, center=(-1.5, 0, 3.8), color_idx=2)
    faces += mkit.make_cuboid(bm, 3.8, 2.8, 0.1, center=(-1.5, 0, 4.65), color_idx=4)
    # Server blinking status slots
    faces += mkit.make_cuboid(bm, 2.8, 0.05, 1.0, center=(-1.5, -1.32, 3.8), color_idx=6)
    
    # Rooftop Satellite Uplink Dish (Right side)
    faces += mkit.make_cylinder(bm, 0.06, 1.4, segs=6, center=(2.5, 0.5, 3.7), color_idx=0)
    # Parabolic dish mesh
    faces += mkit.make_cylinder(bm, 0.8, 0.15, segs=8, center=(2.5, 0.5, 4.5), color_idx=0)
    faces += mkit.make_cylinder(bm, 0.04, 0.6, segs=6, center=(2.5, 0.0, 4.5), color_idx=3)

    mkit.apply_bmesh_and_export("datacamp_shack_01_server_container", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


def build_datacamp_shack_02_rig_lookout():
    """2-Storey Elevated Rig Lookout Tower on scaffold stilts with server core."""
    bm = bmesh.new()
    faces = []
    # 4 Heavy Steel Scaffold Stilts: 6m x 6m footprint, 7.5m total height
    for sx in (-2.6, 2.6):
        for sy in (-2.6, 2.6):
            faces += mkit.make_cuboid(bm, 0.2, 0.2, 4.0, center=(sx, sy, 2.0), color_idx=2)
            
    # Diagonal Cross-Bracing on stilts
    faces += mkit.make_cuboid(bm, 5.2, 0.1, 0.1, center=(0, -2.6, 2.0), color_idx=3)
    faces += mkit.make_cuboid(bm, 5.2, 0.1, 0.1, center=(0, 2.6, 2.0), color_idx=3)
    
    # Ground-Level Generator & Transformer Cage
    faces += mkit.make_cuboid(bm, 3.2, 3.2, 2.0, center=(0, 0, 1.0), color_idx=0)
    faces += mkit.make_cuboid(bm, 3.4, 0.1, 1.8, center=(0, -1.62, 1.0), color_idx=3)
    
    # Elevated Living & Server Rig Cabin (Z: 4.0 to 7.2)
    faces += mkit.make_cuboid(bm, 6.0, 6.0, 0.3, center=(0, 0, 4.15), color_idx=5) # Timber platform
    faces += mkit.make_cuboid(bm, 4.6, 4.6, 2.8, center=(0, 0, 5.7), color_idx=1) # Rusted cabin
    
    # Corrugated Roof with Solar Cells
    faces += mkit.make_cuboid(bm, 5.2, 5.2, 0.15, center=(0, 0, 7.15), color_idx=0)
    faces += mkit.make_cuboid(bm, 3.6, 3.6, 0.05, center=(0, 0, 7.25), color_idx=6)
    
    # Perimeter Walkway & Safety Railing around elevated cabin
    faces += mkit.make_cuboid(bm, 5.8, 0.06, 0.9, center=(0, -2.9, 4.75), color_idx=3)
    faces += mkit.make_cuboid(bm, 5.8, 0.06, 0.9, center=(0, 2.9, 4.75), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.06, 5.8, 0.9, center=(-2.9, 0, 4.75), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.06, 5.8, 0.9, center=(2.9, 0, 4.75), color_idx=3)
    
    # Access Ladder on side
    faces += mkit.make_cuboid(bm, 0.5, 0.08, 4.2, center=(-2.8, 0, 2.1), color_idx=3)
    
    # High-Gain Telemetry Antenna Mast
    faces += mkit.make_cylinder(bm, 0.05, 3.5, segs=6, center=(1.8, 1.8, 8.8), color_idx=2)
    faces += mkit.make_cylinder(bm, 0.5, 0.1, segs=6, center=(1.8, 1.8, 9.8), color_idx=7)

    mkit.apply_bmesh_and_export("datacamp_shack_02_rig_lookout", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


def build_datacamp_shack_03_generator_hub():
    """Heavy Power Hub Shack with Diesel Generator, Cooling Tower & Battery Banks."""
    bm = bmesh.new()
    faces = []
    # 9m wide, 6m deep, 4m high
    faces += mkit.make_cuboid(bm, 9.0, 6.0, 3.6, center=(0, 0, 1.8), color_idx=0)
    
    # Slanted Corrugated Industrial Roof
    faces += mkit.make_pitched_roof(bm, 9.0, 6.0, 1.2, overhang=0.2, center=(0, 0, 3.6), color_idx=1)
    
    # Large Industrial Diesel Exhaust Chimney Pipe (Left side)
    faces += mkit.make_cylinder(bm, 0.25, 4.8, segs=8, center=(-3.5, -1.8, 2.4), color_idx=2)
    faces += mkit.make_cylinder(bm, 0.35, 0.4, segs=8, center=(-3.5, -1.8, 4.9), color_idx=7)
    
    # External Transformer Coils & Battery Rack Banks (Front right)
    faces += mkit.make_cuboid(bm, 3.8, 1.2, 2.0, center=(2.0, -3.2, 1.0), color_idx=2)
    for bx in (0.6, 1.6, 2.6, 3.4):
        faces += mkit.make_cuboid(bm, 0.6, 0.8, 0.8, center=(bx, -3.2, 0.5), color_idx=3)
        faces += mkit.make_cuboid(bm, 0.6, 0.8, 0.8, center=(bx, -3.2, 1.4), color_idx=3)
        
    # High-Voltage Warning Signboard & Industrial Sliding Gate
    faces += mkit.make_cuboid(bm, 2.2, 0.1, 2.6, center=(-1.5, -3.02, 1.3), color_idx=3)
    faces += mkit.make_cuboid(bm, 1.6, 0.05, 0.6, center=(-1.5, -3.08, 2.2), color_idx=7)

    mkit.apply_bmesh_and_export("datacamp_shack_03_generator_hub", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


# ==============================================================================
# PROPS & RIG HARDWARE
# ==============================================================================

def build_datacamp_prop_server_rack_stack():
    """Free-standing outdoor rigged server tower / blade chassis cluster."""
    bm = bmesh.new()
    faces = []
    # Triple Server Rack Cluster: 2.2m wide, 1.0m deep, 2.2m high
    faces += mkit.make_cuboid(bm, 2.2, 1.0, 0.12, center=(0, 0, 0.06), color_idx=2)
    
    for rx in (-0.7, 0.0, 0.7):
        # 19-inch rack cabinet
        faces += mkit.make_cuboid(bm, 0.65, 0.9, 2.0, center=(rx, 0, 1.1), color_idx=2)
        # Server blade slots & activity LEDs
        for bz in (0.35, 0.75, 1.15, 1.55, 1.9):
            faces += mkit.make_cuboid(bm, 0.58, 0.05, 0.28, center=(rx, -0.46, bz), color_idx=0)
            faces += mkit.make_cuboid(bm, 0.15, 0.06, 0.08, center=(rx + 0.18, -0.47, bz), color_idx=6)
            
    # Overhead protective scrap metal rain-hood
    faces += mkit.make_cuboid(bm, 2.5, 1.3, 0.08, center=(0, 0, 2.18), color_idx=1)

    mkit.apply_bmesh_and_export("datacamp_prop_server_rack_stack", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


def build_datacamp_prop_satellite_rig():
    """Tripod-mounted jury-rigged satellite uplink dish with power inverter."""
    bm = bmesh.new()
    faces = []
    # Heavy tripod base: 1.8m diameter, 2.6m high
    faces += mkit.make_cylinder(bm, 0.06, 1.8, segs=6, center=(0, 0, 0.9), color_idx=2)
    for ang in (0.0, 2.1, 4.2):
        import math
        lx = 0.7 * math.cos(ang)
        ly = 0.7 * math.sin(ang)
        faces += mkit.make_cylinder(bm, 0.03, 1.2, segs=4, center=(lx, ly, 0.5), color_idx=3)
        
    # Parabolic Dish (1.6m diameter)
    faces += mkit.make_cylinder(bm, 0.8, 0.15, segs=10, center=(0, 0, 1.9), color_idx=0)
    # Feed horn
    faces += mkit.make_cylinder(bm, 0.03, 0.7, segs=6, center=(0, -0.4, 2.0), color_idx=7)
    
    # Ground Power Inverter & Battery Box
    faces += mkit.make_cuboid(bm, 0.7, 0.5, 0.45, center=(0.4, 0.4, 0.225), color_idx=3)
    faces += mkit.make_cuboid(bm, 0.3, 0.05, 0.15, center=(0.4, 0.14, 0.25), color_idx=6)

    mkit.apply_bmesh_and_export("datacamp_prop_satellite_rig", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


def build_datacamp_prop_cooling_tower():
    """Improvised swamp cooler / radiator fan rig with exhaust pipes."""
    bm = bmesh.new()
    faces = []
    # Cooler Unit: 1.8m wide, 1.2m deep, 2.2m high
    faces += mkit.make_cuboid(bm, 1.8, 1.2, 1.8, center=(0, 0, 0.9), color_idx=0)
    
    # 2x Large Industrial Extractor Fans
    faces += mkit.make_cylinder(bm, 0.4, 0.15, segs=8, center=(-0.45, -0.62, 0.9), color_idx=2)
    faces += mkit.make_cylinder(bm, 0.4, 0.15, segs=8, center=(0.45, -0.62, 0.9), color_idx=2)
    
    # Copper cooling coil piping on top
    faces += mkit.make_cylinder(bm, 0.08, 1.6, segs=6, center=(0, 0, 1.9), color_idx=7)
    
    # Side 55-Gallon Coolant Drum
    faces += mkit.make_cylinder(bm, 0.3, 0.9, segs=8, center=(1.2, 0, 0.45), color_idx=4)

    mkit.apply_bmesh_and_export("datacamp_prop_cooling_tower", bm, faces, PAL_DATACAMP, "datacenter_camps", tri_limit=1600)


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("--- BUILDING ALL 7 DATA CENTER CAMP ASSETS (<1600 TRIS) ---")
    build_datacamp_terrace_01_modular_row()
    build_datacamp_shack_01_server_container()
    build_datacamp_shack_02_rig_lookout()
    build_datacamp_shack_03_generator_hub()
    build_datacamp_prop_server_rack_stack()
    build_datacamp_prop_satellite_rig()
    build_datacamp_prop_cooling_tower()
    print("--- ALL 7 DATA CENTER CAMP ASSETS COMPLETE ---")


if __name__ == "__main__":
    main()
