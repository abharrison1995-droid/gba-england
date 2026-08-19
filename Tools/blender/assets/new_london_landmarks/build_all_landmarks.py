"""Master Batch Runner for all 10 London Landmarks.

Runs:
1. landmark_01_westminster.py
2. landmark_02_tower_of_london.py
3. landmark_03_st_pauls.py
4. landmark_04_battersea.py
5. landmark_05_the_shard.py
6. landmark_06_tower_bridge.py
7. landmark_07_royal_courts.py
8. landmark_08_the_gherkin.py
9. landmark_09_natural_history_museum.py
10. landmark_10_buckingham_palace.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "landmark_01_westminster.py",
    "landmark_02_tower_of_london.py",
    "landmark_03_st_pauls.py",
    "landmark_04_battersea.py",
    "landmark_05_the_shard.py",
    "landmark_06_tower_bridge.py",
    "landmark_07_royal_courts.py",
    "landmark_08_the_gherkin.py",
    "landmark_09_natural_history_museum.py",
    "landmark_10_buckingham_palace.py",
]

def main():
    root = Path(__file__).resolve().parent
    runner = root.parent.parent / "bpy_runner.py"

    print("=========================================================")
    print("STARTING BATCH GENERATION OF 10 LONDON LANDMARKS (~3500 TRIS)")
    print("=========================================================\n")

    success_count = 0
    for s_name in SCRIPTS:
        script_path = root / s_name
        print(f"--> Building {s_name}...")
        cmd = [sys.executable, str(runner), str(script_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"    [OK] {s_name} finished successfully.")
            for line in res.stdout.splitlines():
                if "[asset_kit]" in line or "[Westminster]" in line or "[TowerOfLondon]" in line or "[StPauls]" in line or "[Battersea]" in line or "[TheShard]" in line or "[TowerBridge]" in line or "[RoyalCourts]" in line or "[TheGherkin]" in line or "[NaturalHistoryMuseum]" in line or "[BuckinghamPalace]" in line:
                    print(f"        {line}")
            success_count += 1
        else:
            print(f"    [ERROR] {s_name} failed with code {res.returncode}:")
            print(res.stderr or res.stdout)

    print(f"\n=========================================================")
    print(f"BATCH COMPLETE: {success_count}/{len(SCRIPTS)} Landmarks Generated.")
    print("=========================================================")

if __name__ == "__main__":
    main()
