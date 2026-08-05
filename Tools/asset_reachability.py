#!/usr/bin/env python3
"""Unity asset reachability and reference-integrity checker.

Two jobs:

  --check-dangling   Does any tracked asset point at a file that does not exist?
                     Exit 1 on any dangling reference that is not already documented
                     in KNOWN_DANGLING below.

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

What is indexed, and why it matters
-----------------------------------
GUIDs are resolved from `.meta` files under **`Assets/`, `Packages/` and
`Library/PackageCache/`**. The package roots are not optional decoration: every script
Unity ships — `LayoutElement`, `RectMask2D`, `AspectRatioFitter`, all of TextMesh Pro —
lives in a package, and a scene referencing one is perfectly healthy. Indexing `Assets/`
alone made all of them read as missing, which is how this check used to fail the moment
the scene started using a UI component type it had not used before.

`Library/` is gitignored and machine-local, so on a fresh clone it does not exist until
Unity has resolved packages once. That case exits 2 — *could not verify* — rather than
guessing. A silent pass would be worse than an honest refusal.

Two GUIDs never resolve anywhere and are not breakage: the all-zero-then-`e` one (Unity
default resources) and the all-zero-then-`f` one (unity_builtin_extra). Both are listed in
full in BUILTIN_GUIDS below. They are filtered out, not counted.

Everything left over is a real dangling reference. Those are listed one by one in
KNOWN_DANGLING with what they point at, rather than absorbed into a single tolerated
count — a bare number cannot distinguish a long-known breakage from a new one, and this
repo had four broken sprite references hiding inside such a number.

Exit codes:
    0   nothing dangling beyond the documented known set
    1   something references a file that does not exist
    2   packages could not be indexed, so nothing was verified

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

# Where Unity's own code and assets live. PackageCache is the real one — Packages/ holds
# only manifest.json here, but an embedded package would land there and must resolve too.
PACKAGE_ROOTS = ("Library/PackageCache", "Packages")

# Unity's two sentinel GUIDs. They resolve to no file in any project on any machine and
# never will; they are how the format says "this is a built-in". Not breakage.
BUILTIN_GUIDS = {
    "0000000000000000e000000000000000",  # unity default resources — meshes, cookies
    "0000000000000000f000000000000000",  # unity_builtin_extra — shaders, skybox
}

# Real dangling references, listed rather than tolerated as a count.
#
# These are sprites the build scene still points at and no file on disk provides. They
# predate this list — they were sitting inside a baseline of 17 that claimed to be
# "built-in Unity GUIDs", which is exactly why they went unnoticed for so long. A count
# cannot tell a known breakage from a new one; a name can.
#
# Fixing one means reassigning the sprite in the Inspector and deleting its line here.
# ⚠️ Do not add to this list to make a red run go green. A new entry means something was
# deleted that the scene still needs, and the fix is almost always to restore it.
KNOWN_DANGLING = {
    "6ffcdb3bd81b57a4e840ef49beac20d9": "m_Sprite on three 'Visual' SpriteRenderers",
    "d58ea49aed1f53f409b496b426f04c11": "m_Sprite on three 'Visual' SpriteRenderers",
    "cacf62d2d709101468ca64fb99c7e20a": "m_Sprite on a 'Visual' SpriteRenderer",
    "77ba605bbd83f4448bc8683510c3155e": "ActorSprite on the PCSO actor",
}

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


def index_metas(root):
    """Every (guid, repo-relative path) a .meta under root declares.

    Pairs rather than a dict: two .meta files sharing a guid is a real Unity hazard (a
    copied .meta) and the caller decides what to do about it, instead of one silently
    winning here.
    """
    pairs = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".meta"):
                continue
            meta = os.path.join(dirpath, fn)
            try:
                with open(meta, "rb") as fh:
                    m = META_GUID.search(fh.read(4096))
            except OSError:
                continue
            if m:
                rel = os.path.relpath(meta[:-5], REPO).replace("\\", "/")
                pairs.append((m.group(1).decode(), rel))
    return pairs


def build_index():
    guid_to_path, path_to_guid, assets = {}, {}, []
    for guid, rel in index_metas(ASSETS):
        guid_to_path[guid] = rel
        path_to_guid[rel] = guid
        assets.append(rel)
    return guid_to_path, path_to_guid, assets


def build_package_index():
    """Guids Unity's own packages declare.

    Deliberately kept apart from the Assets index. This is only ever used to *resolve* a
    reference; letting package assets into guid_to_path would make them reachability
    roots and list every Unity package as a deletable "pack" under --packs.
    """
    packages = {}
    for rel in PACKAGE_ROOTS:
        root = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.isdir(root):
            packages.update(index_metas(root))
    return packages


def describe_scene_refs(guids):
    """Name what holds each guid in the build scene, so a failure is actionable.

    A bare guid tells you nothing about what broke. This walks the scene's YAML documents
    and reports the owning GameObject and the field, turning "77ba605b… is missing" into
    "PCSO.ActorSprite points at a texture that is not there".
    """
    path = os.path.join(REPO, BUILD_SCENE.replace("/", os.sep))
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except OSError:
        return {}

    docs = re.split(r"^--- ", text, flags=re.M)
    names, described = {}, defaultdict(list)
    for doc in docs:
        head = re.match(r"!u!(\d+) &(\d+)", doc)
        if not head:
            continue
        name = re.search(r"^  m_Name:\s*(.*)$", doc, re.M)
        if name:
            names[head.group(2)] = name.group(1).strip()

    for doc in docs:
        for guid in guids:
            if guid not in doc:
                continue
            owner = re.search(r"m_GameObject:\s*\{fileID:\s*(\d+)\}", doc)
            field = re.search(r"^\s*(\w+):\s*\{fileID:\s*-?\d+,\s*guid:\s*" + guid, doc, re.M)
            described[guid].append("%s.%s" % (
                names.get(owner.group(1), "?") if owner else "(scene object)",
                field.group(1) if field else "?"))
    return described


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


def check_dangling(guid_to_path, packages):
    if not packages:
        print("Library/PackageCache and Packages/ hold no .meta files, so every script Unity")
        print("ships would read as missing. Open the project in Unity once to resolve packages.")
        print("\nSKIPPED: nothing was verified.")
        return 2

    known = set(guid_to_path) | set(packages) | BUILTIN_GUIDS
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
                offenders[os.path.relpath(p, REPO).replace("\\", "/")] = missing

    scene = offenders.get(BUILD_SCENE, set())
    unknown = scene - set(KNOWN_DANGLING)

    print(f"indexed                           : {len(guid_to_path)} project + "
          f"{len(packages)} package GUIDs")
    print(f"files containing unresolved GUIDs : {len(offenders)}")
    print(f"{BUILD_SCENE} unresolved           : {len(scene)} "
          f"({len(scene & set(KNOWN_DANGLING))} known, {len(unknown)} new)")
    for rel, missing in sorted(offenders.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"  {len(missing):5d}  {rel}")

    if scene & set(KNOWN_DANGLING):
        print("\nKnown dangling references in the build scene (real, and still broken):")
        for guid in sorted(scene & set(KNOWN_DANGLING)):
            print(f"  {guid}  {KNOWN_DANGLING[guid]}")

    if unknown:
        described = describe_scene_refs(unknown)
        print(f"\nFAIL: {BUILD_SCENE} references {len(unknown)} GUID(s) no file provides.")
        for guid in sorted(unknown):
            where = described.get(guid) or ["(could not locate in the scene)"]
            print(f"  {guid}")
            for w in where[:6]:
                print(f"      {w}")
        return 1

    print("\nOK: nothing dangling beyond the documented known set.")
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
        return check_dangling(guid_to_path, build_package_index())

    edges = build_edges(path_to_guid, assets)
    roots = collect_roots(path_to_guid, assets)
    seen = reachable(guid_to_path, edges, roots)
    return report_packs(guid_to_path, path_to_guid, assets, seen)


if __name__ == "__main__":
    sys.exit(main())
