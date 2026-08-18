"""Run a bpy script in headless Blender and stream back stdout/stderr.

This is the execution link for the local asset pipeline: no server, no addon,
no credits. Each call is one deterministic Blender subprocess:

    python Tools/blender/bpy_runner.py <script.py> [-- extra args for the script]

The script runs inside Blender with `Tools/blender/lib` on sys.path, so it can
`import asset_kit`. Anything after `--` is visible to the script via
`asset_kit.script_args()`.

Blender is located in this order:
  1. BLENDER_EXE environment variable
  2. Tools/blender/blender-portable/**/blender.exe  (unzipped portable build)
  3. Standard install locations / PATH

Exit code is Blender's own exit code; Python exceptions inside the script make
Blender exit non-zero, so failures are never silent.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE / "lib"


def find_blender():
    env = os.environ.get("BLENDER_EXE")
    if env and Path(env).is_file():
        return env
    portable = HERE / "blender-portable"
    if portable.is_dir():
        hits = sorted(portable.rglob("blender.exe"))
        if hits:
            return str(hits[0])
    candidates = []
    for root in (r"C:\Program Files\Blender Foundation",
                 os.path.expandvars(r"%LOCALAPPDATA%\Programs\Blender Foundation")):
        rootp = Path(root)
        if rootp.is_dir():
            candidates += sorted(rootp.rglob("blender.exe"), reverse=True)
    if candidates:
        return str(candidates[0])
    from shutil import which
    exe = which("blender")
    if exe:
        return exe
    return None


def run(script, extra_args=(), timeout=300):
    blender = find_blender()
    if not blender:
        print("ERROR: no Blender found. Set BLENDER_EXE, or unzip a portable "
              "build into Tools/blender/blender-portable/.", file=sys.stderr)
        return 2
    script = Path(script).resolve()
    if not script.is_file():
        print(f"ERROR: script not found: {script}", file=sys.stderr)
        return 2
    # --factory-startup: user preferences/addons cannot change behaviour.
    # Blender ignores PYTHONPATH unless --python-use-system-env is set, so the
    # lib/ path is injected with an expr that runs before the script.
    env = dict(os.environ)
    cmd = [blender, "--background", "--factory-startup",
           "--python-exit-code", "1",
           "--python-expr", f"import sys; sys.path.insert(0, {str(LIB)!r})",
           "--python", str(script)]
    if extra_args:
        cmd += ["--", *extra_args]
    print(f"[bpy_runner] {blender}")
    print(f"[bpy_runner] running {script.name} {' '.join(extra_args)}")
    proc = subprocess.run(cmd, env=env, timeout=timeout,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    print(f"[bpy_runner] exit code {proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    if "--" in args:
        split = args.index("--")
        script_path, extra = args[0], args[split + 1:]
    else:
        script_path, extra = args[0], []
    sys.exit(run(script_path, extra))
