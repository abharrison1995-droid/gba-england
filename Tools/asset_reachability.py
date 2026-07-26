#!/usr/bin/env python3
"""Unity asset reachability and reference-integrity checker.

Two jobs:

  --check-dangling   Does any tracked asset point at a file that does not exist?
                     Exit 1 if the count exceeds the known built-in baseline.

  --packs            Which asset packs have zero reachable assets? Those are safe to
                     delete wholesale. Partially-used packs must be trimmed per-file
                     or left alone.

Reachability is a transitive GUID walk, not a text search. Roots are:
  - the build scene (Assets/c.unity)
  - everything under Resources/  (loaded by name at runtime, never GUID-reachable)
  - everything under Editor/ and StreamingAssets/
  - all .cs / .asmdef / .dll     (code is not GUID-reachable either)
  - GUIDs referenced from ProjectSettings/
  - hardcoded "Assets/..." paths inside .cs  (editor tools use AssetDatabase.LoadAssetAtPath)

Edges are read from text assets *and from .meta files* — a model importer remaps its
materials in the .meta, so skipping those makes a model's materials look unused.

Usage:
    python Tools/asset_reachability.py --check-dangling
    python Tools/asset_reachability.py --packs
"""
import argparse
import os
import re
import sys
from collections import defaultdict, deque

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "Assets")
BUILD_SCENE = "Assets/c.unity"

# c.unity legitimately references this many built-in Unity GUIDs that resolve to no
# file on disk. Measured, not guessed. Exceeding it means something actually broke.
BUILTIN_BASELINE = 17

GUID_REF = re.compile(rb"guid:\s*([0-9a-f]{32})")
META_GUID = re.compile(rb"^guid:\s*([0-9a-f]{32})", re.M)
CS_ASSET_PATH = re.compile(r'"(Assets/[^"]+?\.[A-Za-z0-9]+)"')

EDGE_EXT = {".unity", ".prefab", ".asset", ".mat", ".controller", ".anim",
            ".overridecontroller", ".physicmaterial", ".spriteatlas", ".shadervariants",
            ".mixer", ".playable", ".terrainlayer", ".guiskin", ".fontsettings", ".meta"}

# folders whose immediate children are each their own pack
CONTAINERS = {"Assets/3DModels", "Assets/Sprites", "Assets/Art",
              "Assets/Materials", "Assets/Animations", "Assets/Prefabs"}
PROTECTED = {"Assets/Scripts", "Assets/Editor", "Assets/Data", "Assets/Resources",
             "Assets/c", "Assets/Plugins", "Assets/Settings", "Assets/TextMesh Pro"}


def build_index():
    guid_to_path, path_to_guid, assets = {}, {}, []
    for dirpath, _, filenames in os.walk(ASSETS):
        for fn in filenames:
            if not fn.endswith(".meta"):
                continue
            meta = os.path.join(dirpath, fn)
            try:
                with open(meta, "rb") as fh:
                    m = META_GUID.search(fh.read(4096))
            except OSError:
                continue
            if not m:
                continue
            rel = os.path.relpath(meta[:-5], REPO).replace("\\", "/")
            guid = m.group(1).decode()
            guid_to_path[guid] = rel
            path_to_guid[rel] = guid
            assets.append(rel)
    return guid_to_path, path_to_guid, assets


def build_edges(path_to_guid, assets):
    edges = defaultdict(set)
    for rel in assets:
        src = path_to_guid[rel]
        # the asset's own file, and its .meta (importers remap materials there)
        for candidate in (rel, rel + ".meta"):
            if os.path.splitext(candidate)[1].lower() not in EDGE_EXT:
                continue
            full = os.path.join(REPO, candidate.replace("/", os.sep))
            if not os.path.isfile(full):
                continue
            try:
                with open(full, "rb") as fh:
                    blob = fh.read()
            except OSError:
                continue
            for g in GUID_REF.findall(blob):
                g = g.decode()
                if g != src:
                    edges[src].add(g)
    return edges


def collect_roots(path_to_guid, assets):
    roots = set()

    def add(rel):
        g = path_to_guid.get(rel)
        if g:
            roots.add(g)

    add(BUILD_SCENE)
    for rel in assets:
        if {"Resources", "Editor", "StreamingAssets"} & set(rel.split("/")):
            add(rel)
        if rel.endswith((".cs", ".asmdef", ".dll")):
            add(rel)

    settings_dir = os.path.join(REPO, "ProjectSettings")
    if os.path.isdir(settings_dir):
        for fn in os.listdir(settings_dir):
            p = os.path.join(settings_dir, fn)
            if os.path.isfile(p):
                try:
                    with open(p, "rb") as fh:
                        for g in GUID_REF.findall(fh.read()):
                            roots.add(g.decode())
                except OSError:
                    pass

    # editor tools pass literal paths to AssetDatabase.LoadAssetAtPath
    for dirpath, _, filenames in os.walk(ASSETS):
        for fn in filenames:
            if not fn.endswith(".cs"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore") as fh:
                    for hit in CS_ASSET_PATH.findall(fh.read()):
                        add(hit)
            except OSError:
                pass
    return roots


def reachable(guid_to_path, edges, roots):
    seen = {g for g in roots if g in guid_to_path}
    queue = deque(seen)
    while queue:
        for nxt in edges.get(queue.popleft(), ()):
            if nxt in guid_to_path and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def size_of(rel):
    full = os.path.join(REPO, rel.replace("/", os.sep))
    try:
        return 0 if os.path.isdir(full) else os.path.getsize(full)
    except OSError:
        return 0


def check_dangling(guid_to_path):
    known = set(guid_to_path)
    worst = 0
    offenders = {}
    for dirpath, _, filenames in os.walk(ASSETS):
        for fn in filenames:
            if not fn.endswith(tuple(EDGE_EXT)):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, "rb") as fh:
                    blob = fh.read()
            except OSError:
                continue
            missing = {g.decode() for g in GUID_REF.findall(blob)} - known
            if missing:
                rel = os.path.relpath(p, REPO).replace("\\", "/")
                offenders[rel] = len(missing)
                worst = max(worst, len(missing))

    scene = offenders.get(BUILD_SCENE, 0)
    print(f"files containing unresolved GUIDs : {len(offenders)}")
    print(f"{BUILD_SCENE} unresolved           : {scene} (baseline {BUILTIN_BASELINE})")
    for rel, n in sorted(offenders.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:5d}  {rel}")

    if scene > BUILTIN_BASELINE:
        print(f"\nFAIL: {BUILD_SCENE} is above the built-in baseline — something is missing.")
        return 1
    print("\nOK: build scene is at or below the known built-in baseline.")
    return 0


def report_packs(guid_to_path, path_to_guid, assets, seen):
    def pack_of(rel):
        parts = rel.split("/")
        for c in CONTAINERS:
            cp = c.split("/")
            if parts[:len(cp)] == cp and len(parts) > len(cp):
                return "/".join(parts[:len(cp) + 1])
        return "/".join(parts[:2]) if len(parts) > 1 else rel

    packs = defaultdict(lambda: {"total": 0, "used": 0, "bytes": 0})
    for rel in assets:
        if os.path.isdir(os.path.join(REPO, rel.replace("/", os.sep))):
            continue
        entry = packs[pack_of(rel)]
        entry["total"] += 1
        entry["bytes"] += size_of(rel)
        if path_to_guid[rel] in seen:
            entry["used"] += 1

    dead, partial = [], []
    for name, s in sorted(packs.items(), key=lambda kv: -kv[1]["bytes"]):
        if any(name == p or name.startswith(p + "/") for p in PROTECTED):
            continue
        (dead if s["used"] == 0 else partial).append((name, s))

    print(f"reachable: {len(seen & set(guid_to_path))} / {len(assets)} assets\n")
    print("FULLY UNUSED PACKS — safe to delete wholesale")
    total = 0
    for name, s in dead:
        total += s["bytes"]
        print(f"  {s['bytes']/1e6:8.1f} MB  {s['total']:5d} files  {name}")
    print(f"  reclaimable: {total/1e6:.1f} MB\n")
    print("PARTIALLY USED — trim per-file or leave alone")
    for name, s in partial:
        print(f"  {s['bytes']/1e6:8.1f} MB  {s['used']:4d}/{s['total']:-5d}  {name}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-dangling", action="store_true",
                    help="fail if the build scene has more unresolved GUIDs than the baseline")
    ap.add_argument("--packs", action="store_true",
                    help="list asset packs with zero reachable assets")
    args = ap.parse_args()
    if not (args.check_dangling or args.packs):
        ap.print_help()
        return 2

    guid_to_path, path_to_guid, assets = build_index()
    if args.check_dangling:
        return check_dangling(guid_to_path)

    edges = build_edges(path_to_guid, assets)
    roots = collect_roots(path_to_guid, assets)
    seen = reachable(guid_to_path, edges, roots)
    return report_packs(guid_to_path, path_to_guid, assets, seen)


if __name__ == "__main__":
    sys.exit(main())
