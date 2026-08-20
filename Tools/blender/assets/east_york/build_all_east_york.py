"""Master batch runner for generating all 10 East York Chinese Landmark 3D assets (~3500 Tri limit).

Executes headless Blender 5.2 across each generator script in sequence.
Deploys .glb models, 512x512 pixel-art atlases, and isometric preview renders
directly into Assets/3DModels/East York/.
"""

import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent.parent
BPY_RUNNER = ROOT_DIR / "Tools" / "blender" / "bpy_runner.py"

LANDMARKS = [
    "landmark_01_forbidden_city.py",
    "landmark_02_temple_of_heaven.py",
    "landmark_03_great_wall.py",
    "landmark_04_oriental_pearl.py",
    "landmark_05_shanghai_tower.py",
    "landmark_06_yellow_crane_tower.py",
    "landmark_07_potala_palace.py",
    "landmark_08_giant_wild_goose_pagoda.py",
    "landmark_09_canton_tower.py",
    "landmark_10_tiananmen_gate.py",
]


def main():
    print("=" * 65)
    print("STARTING BATCH GENERATION OF 10 EAST YORK CHINESE LANDMARKS (~3500 TRIS)")
    print("=" * 65)

    failed = []

    for idx, script_name in enumerate(LANDMARKS, 1):
        script_path = SCRIPT_DIR / script_name
        if not script_path.exists():
            print(f"[{idx}/{len(LANDMARKS)}] ERROR: {script_name} not found at {script_path}!")
            failed.append(script_name)
            continue

        print(f"\n--> [{idx}/{len(LANDMARKS)}] Building {script_name}...")
        cmd = [sys.executable, str(BPY_RUNNER), str(script_path)]
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)

        if res.returncode != 0:
            print(f"    [FAIL] {script_name} returned error code {res.returncode}")
            print(res.stderr)
            print(res.stdout)
            failed.append(script_name)
        else:
            print(f"    [OK] {script_name} finished successfully.")
            for line in res.stdout.splitlines():
                if any(k in line for k in ["[asset_kit]", "[ForbiddenCity]", "[TempleOfHeaven]", "[GreatWall]", "[OrientalPearl]", "[ShanghaiTower]", "[YellowCraneTower]", "[PotalaPalace]", "[WildGoosePagoda]", "[CantonTower]", "[TiananmenGate]"]):
                    print(f"        {line}")

    print("\n" + "=" * 65)
    if failed:
        print(f"BATCH FINISHED WITH {len(failed)} FAILURES: {failed}")
        sys.exit(1)
    else:
        print("BATCH COMPLETE: All 10 East York Landmarks Generated & Deployed!")
        print("=" * 65)


if __name__ == "__main__":
    main()
