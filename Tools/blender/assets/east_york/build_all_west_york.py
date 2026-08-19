"""Master batch runner to build all 12 West York 3D Assets (1000 Tri limit each).

Categories:
1. Terraced Houses (3 variations)
2. Larger Homes (3 variations)
3. Martial Arts Dojo (3 variations)
4. Great Wall of China Tileable Variations (3 variations)

Executes headless via bpy_runner.py.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BPY_RUNNER = HERE.parent.parent / "bpy_runner.py"

SCRIPTS = [
    # Category 1: Terraced Houses
    "house_terrace_var1_redbrick.py",
    "house_terrace_var2_stone_render.py",
    "house_terrace_var3_shopfront.py",

    # Category 2: Larger Homes
    "house_large_var1_suburban_detached.py",
    "house_large_var2_manor_estate.py",
    "house_large_var3_tudor_revival.py",

    # Category 3: Martial Arts Dojo
    "building_dojo_var1_traditional_kwoon.py",
    "building_dojo_var2_modern_training_hall.py",
    "building_dojo_var3_courtyard_temple_dojo.py",

    # Category 4: Great Wall of China Tileable Variations
    "wall_great_wall_var1_straight_segment.py",
    "wall_great_wall_var2_corner_tower.py",
    "wall_great_wall_var3_gate_arch.py",
]


def main():
    print("=" * 65)
    print("STARTING BATCH BUILD OF 12 WEST YORK 3D ASSETS (<1000 TRIS)")
    print("=" * 65)

    failed = []
    for i, script_name in enumerate(SCRIPTS, start=1):
        script_path = HERE / script_name
        print(f"\n--> [{i}/{len(SCRIPTS)}] Building {script_name}...")
        cmd = [sys.executable, str(BPY_RUNNER), str(script_path)]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"    [FAIL] {script_name} returned exit code {res.returncode}")
            failed.append(script_name)
        else:
            print(f"    [OK] {script_name} finished successfully.")

    print("\n" + "=" * 65)
    if failed:
        print(f"BATCH FINISHED WITH {len(failed)} FAILURES: {failed}")
        sys.exit(1)
    else:
        print("BATCH COMPLETE: All 12 West York Assets Generated & Deployed!")
        print("=" * 65)


if __name__ == "__main__":
    main()
