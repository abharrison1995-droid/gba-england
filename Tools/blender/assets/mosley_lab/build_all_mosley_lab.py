"""Master batch runner to build all 10 Mosley Lab 3D Props (<3200 Tris each).

Props:
1. prop_vape_mixing_station.py
2. prop_chem_synthesis_rig.py
3. prop_filling_machine.py
4. prop_fume_hood.py
5. prop_server_rack.py
6. prop_centrifuge_rotovap.py
7. prop_vape_testing_rig.py
8. prop_chemical_storage_drum_rack.py
9. prop_microscope_analysis_bench.py
10. prop_gas_cylinder_manifold.py

Executes headless via bpy_runner.py.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BPY_RUNNER = HERE.parent.parent / "bpy_runner.py"

SCRIPTS = [
    "prop_vape_mixing_station.py",
    "prop_chem_synthesis_rig.py",
    "prop_filling_machine.py",
    "prop_fume_hood.py",
    "prop_server_rack.py",
    "prop_centrifuge_rotovap.py",
    "prop_vape_testing_rig.py",
    "prop_chemical_storage_drum_rack.py",
    "prop_microscope_analysis_bench.py",
    "prop_gas_cylinder_manifold.py",
]


def main():
    print("=" * 65)
    print("STARTING BATCH BUILD OF 10 MOSLEY LAB 3D PROPS (<3200 TRIS)")
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
        print("BATCH COMPLETE: All 10 Mosley Lab Props Generated & Deployed!")
        print("=" * 65)


if __name__ == "__main__":
    main()
