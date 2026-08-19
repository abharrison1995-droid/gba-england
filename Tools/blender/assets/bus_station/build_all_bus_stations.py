"""Batch runner for compiling and deploying all 4 Bus Station building variants.

Executes headless Blender 5.2 across each generator script in sequence and deploys
models, atlases, and preview renders to Assets/3DModels/bus_station/.
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent.parent
BPY_RUNNER = ROOT_DIR / "Tools" / "blender" / "bpy_runner.py"

VARIANTS = [
    "building_bus_station_var1_modern.py",
    "building_bus_station_var2_art_deco.py",
    "building_bus_station_var3_brutalist.py",
    "building_bus_station_var4_victorian.py",
]


def main():
    print("=" * 65)
    print("STARTING BATCH BUILD OF 4 BUS STATION VARIANTS")
    print("=" * 65)

    failed = []

    for idx, script_name in enumerate(VARIANTS, 1):
        script_path = SCRIPT_DIR / script_name
        if not script_path.exists():
            print(f"[{idx}/{len(VARIANTS)}] ERROR: {script_name} not found at {script_path}!")
            failed.append(script_name)
            continue

        print(f"\n--> [{idx}/{len(VARIANTS)}] Building {script_name}...")
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
                if any(k in line for k in ["[asset_kit]", "[BusStation_Var1]", "[BusStation_Var2]", "[BusStation_Var3]", "[BusStation_Var4]"]):
                    print(f"        {line}")

    print("\n" + "=" * 65)
    if failed:
        print(f"BATCH FINISHED WITH {len(failed)} FAILURES: {failed}")
        sys.exit(1)
    else:
        print("BATCH COMPLETE: All 4 Bus Station Variants Generated & Deployed!")
        print("=" * 65)


if __name__ == "__main__":
    main()
