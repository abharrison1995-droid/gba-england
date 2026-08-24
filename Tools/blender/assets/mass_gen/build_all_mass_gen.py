"""Master Batch Runner for Mass Generation of Modular Prefab Chunks & Interior 3D Assets.

Generates:
- 12 London Architecture Models (4 Sets: Victorian Redbrick, London Stock Yellow Brick, Post-War Council, Modern Suburbia)
- 12 West York Architecture Models (4 Sets: Yorkshire Gritstone, Anglo-Asian Fusion, Northern Redbrick, Tudor Revival)
- 12 East York Chinese Architecture Models (4 Sets: Imperial Forbidden City, Jiangnan Suzhou, Lingnan Qilou Chinatown, Modern Sino)
- 15 Interior Props Modular Models (Shops, Police Station, City Hall, The Winchester Pub, Residential Flats)

Total: 51 3D Low-Poly Models with embedded palettes, .glb exports and isometric Workbench previews.
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent.parent
BPY_RUNNER = ROOT_DIR / "Tools" / "blender" / "bpy_runner.py"

SUITES = [
    ("London Modular Sets (12 Models)", SCRIPT_DIR / "london_sets" / "build_london_sets.py"),
    ("West York Modular Sets (12 Models)", SCRIPT_DIR / "westyork_sets" / "build_westyork_sets.py"),
    ("East York Chinese Modular Sets (12 Models)", SCRIPT_DIR / "eastyork_sets" / "build_eastyork_sets.py"),
    ("Interior Modular Kits (15 Models)", SCRIPT_DIR / "interiors" / "build_interiors.py"),
]


def main():
    print("=" * 75)
    print("STARTING MASS ASSET GENERATION: 51 3D MODELS (<1600 TRIS)")
    print("=" * 75)

    failed = []

    for name, script_path in SUITES:
        print(f"\n--> Running Suite: {name}...")
        if not script_path.exists():
            print(f"    [ERROR] Script not found: {script_path}")
            failed.append(name)
            continue

        cmd = [sys.executable, str(BPY_RUNNER), str(script_path)]
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)

        if res.returncode != 0:
            print(f"    [FAIL] {name} failed with exit code {res.returncode}")
            print(res.stderr)
            print(res.stdout)
            failed.append(name)
        else:
            print(f"    [OK] {name} completed successfully.")
            for line in res.stdout.splitlines():
                if any(k in line for k in ["[building_", "[interior_", "Triangles:", "Deployed to:"]):
                    print(f"        {line}")

    print("\n" + "=" * 75)
    if failed:
        print(f"MASS GENERATION COMPLETED WITH FAILURES: {failed}")
        sys.exit(1)
    else:
        print("MASS GENERATION COMPLETE: All 51 3D Models Successfully Built & Deployed!")
        print("=" * 75)


if __name__ == "__main__":
    main()
