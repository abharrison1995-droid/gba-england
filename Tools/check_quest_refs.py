#!/usr/bin/env python3
"""Unity-free reference validator for quests/*.quest.

Cross-checks the reference ids a hand-authored quest must resolve, so they can
be validated without opening Unity.

Complements (does NOT replace) the in-editor
`Assets/Editor/Validators/QuestContentValidator.cs`, which needs the Unity
AssetDatabase. That editor validator already covers the structural/contract
cross-checks (GRANT resolves, Collect/Manual has a COMPLETE route, duplicate
DIALOGUE npcId, empty objectives, TEACHSPARK gating, HIRE id). What it cannot do
without AssetDatabase — and what this script exists for — is resolve the lookups
the pipeline performs against what is on disk, before Unity runs:

  DIALOGUE <npcId>      -> PlacementPreset by filename or Label   (case-insensitive)
  ITEM: <itemId> ...    -> ItemData.ItemID under Resources/Items  (case-sensitive)
  MERCHANT: <id> ...    -> MerchantData by filename or MerchantName (case-insensitive)
  HIRE: <id> [free]     -> CompanionDefinition.Id under Resources/Companions (case-sensitive)

Only HIRE is deferred past the importer: it is stored verbatim and resolved at
runtime by DialogueManager -> CompanionDatabase.Find. ITEM and HIRE must therefore
match exactly (the case-sensitive dictionary lookups the runtime actually uses),
while DIALOGUE and MERCHANT match case-insensitively, exactly like the importer.

This is "the machinery", not the prose: it never reads or writes dialogue text,
only the reference ids that must resolve.

Not checked here (deliberately): stage QuestActor/SceneMarker keys (needs loading
chunk prefabs; deferred in QuestContentValidator too), and the GRANT/COMPLETE
contract (QuestContentValidator owns it).

Usage:
    python Tools/check_quest_refs.py            # report only
    python Tools/check_quest_refs.py --strict   # exit 1 if any problem
"""

import os
import re
import sys

ASSET_ENCODING = "utf-8-sig"
QUESTS_ROOT = "quests"
DIALOGUE_ROOT = os.path.join("quests", "dialogue")

PRESETS_DIR = "Assets/Data/Presets"
ITEMS_DIR = "Assets/Resources/Items"
MERCHANTS_DIR = "Assets/Data/Merchants"
COMPANIONS_DIR = "Assets/Resources/Companions"


def _read(path, errors="strict"):
    with open(path, encoding=ASSET_ENCODING, errors=errors) as f:
        return f.read()


def _lowerstrip(s):
    return (s or "").strip().lower()


def _asset_texts(root):
    """Yield the text of every .asset under root, recursively.

    ItemDatabase/CompanionDatabase resolve via Resources.LoadAll, which recurses
    under the named folder, so Items/Companions are walked; the preset and merchant
    matchers scan one directory because that is where those assets live.
    """
    if not os.path.isdir(root):
        return
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".asset"):
                yield _read(os.path.join(dirpath, name))


# ---------------------------------------------------------------------------
# Reference sets, built from tracked YAML on disk (no Unity).
# ---------------------------------------------------------------------------

def build_preset_keys():
    """Return the set of lowercase npcId keys a DIALOGUE <npcId> may resolve to.

    The importer matches "by label or filename (case-insensitive, Preset_ prefix
    ignored)", so each preset contributes two keys: its filename without the
    `Preset_` prefix, and its Label.
    """
    keys = set()
    if not os.path.isdir(PRESETS_DIR):
        return keys
    for name in os.listdir(PRESETS_DIR):
        if not name.endswith(".asset"):
            continue
        path = os.path.join(PRESETS_DIR, name)
        text = _read(path)

        stem = name[: -len(".asset")]
        if stem.lower().startswith("preset_"):
            keys.add(_lowerstrip(stem[len("preset_"):]))

        m = re.search(r"\n  Label: ([^\n]+)", text)
        if m:
            keys.add(_lowerstrip(m.group(1)))
    return keys


def build_item_ids():
    """Return the set of ItemData.ItemID values under Resources/Items (any depth).

    ItemDatabase.Find matches ItemID exactly (a case-sensitive dictionary lookup),
    so these keys are NOT lowercased — unlike the preset and merchant matchers.
    """
    ids = set()
    for text in _asset_texts(ITEMS_DIR):
        m = re.search(r"\n  ItemID: ([^\n]+)", text)
        if m:
            ids.add(m.group(1).strip())
    return ids


def build_merchant_keys():
    """Lowercase merchantId keys: filename minus `Merchant_` prefix, and MerchantName."""
    keys = set()
    if not os.path.isdir(MERCHANTS_DIR):
        return keys
    for name in os.listdir(MERCHANTS_DIR):
        if not name.endswith(".asset"):
            continue
        text = _read(os.path.join(MERCHANTS_DIR, name))

        stem = name[: -len(".asset")]
        if stem.lower().startswith("merchant_"):
            keys.add(_lowerstrip(stem[len("merchant_"):]))

        for m in re.finditer(r"\n  MerchantName: ([^\n]+)", text):
            keys.add(_lowerstrip(m.group(1)))
    return keys


def build_companion_ids():
    """Return the set of CompanionDefinition.Id values under Resources/Companions (any depth).

    CompanionDatabase.Find matches Id exactly (a case-sensitive dictionary lookup),
    so these keys are NOT lowercased.
    """
    ids = set()
    for text in _asset_texts(COMPANIONS_DIR):
        for m in re.finditer(r"\n  Id: ([^\n]+)", text):
            ids.add(m.group(1).strip())
    return ids


# ---------------------------------------------------------------------------
# .quest parsing
# ---------------------------------------------------------------------------

def _quest_files():
    files = []
    for root in (QUESTS_ROOT, DIALOGUE_ROOT):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if not name.endswith(".quest") or name.startswith("_"):
                continue
            files.append(os.path.join(root, name))
    return files


def _strip_comment(line):
    # Full-line comments only — an inline '#' is prose, not a comment marker.
    s = line.strip()
    return "" if s.startswith("#") else s


def _analyse_file(path):
    try:
        raw = _read(path)
    except OSError as e:
        yield ("ERROR", "", f"{path}: unreadable: {e}")
        return

    for lineno, rawline in enumerate(raw.splitlines(), 1):
        line = _strip_comment(rawline)
        if not line:
            continue
        upper = line.upper()
        kw = upper.split(" ")[0].split("\t")[0]

        if kw == "DIALOGUE":
            npc_id = _rest(line, len("DIALOGUE"))
            if npc_id:
                yield ("DIALOGUE", lineno, npc_id)
            else:
                yield ("WARNING", lineno, "DIALOGUE with no npcId — the importer logs 'no preset matched'")
        elif kw == "ITEM:":
            val = _value(line)
            first = val.split()[0] if val.split() else ""
            if first:
                yield ("ITEM", lineno, first)
        elif kw == "MERCHANT:":
            val = _value(line)
            first = val.split()[0] if val.split() else ""
            if first:
                yield ("MERCHANT", lineno, first)
        elif kw == "HIRE:":
            val = _value(line)
            first = val.split()[0] if val.split() else ""
            if first:
                yield ("HIRE", lineno, first)


def _value(line):
    colon = line.find(":")
    return line[colon + 1:].strip() if colon >= 0 else ""


def _rest(line, skip):
    return line[skip:].strip() if len(line) > skip else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(strict=False):
    problems = []

    preset_keys = build_preset_keys()
    item_ids = build_item_ids()
    merchant_keys = build_merchant_keys()
    companion_ids = build_companion_ids()

    for path in _quest_files():
        for kind, lineno, ref in _analyse_file(path):
            where = f"{path}:{lineno}"
            if kind == "DIALOGUE":
                key = _lowerstrip(ref)
                if key not in preset_keys:
                    problems.append(
                        ("WARNING", where,
                         f"DIALOGUE '{ref}' has no PlacementPreset (by filename or Label) - "
                         "the importer generates the DialogueData and leaves its preset unwired."))
            elif kind == "ITEM":
                key = ref.strip()
                if key not in item_ids:
                    problems.append(
                        ("WARNING", where,
                         f"ITEM '{ref}' has no ItemData.ItemID under Resources/Items - "
                         "the importer leaves the reference null (a choice-requirement miss also "
                         "aborts its DialogueValidator pass)."))
            elif kind == "MERCHANT":
                key = _lowerstrip(ref)
                if key not in merchant_keys:
                    problems.append(
                        ("ERROR", where,
                         f"MERCHANT '{ref}' resolves to no MerchantData (by filename or MerchantName) - "
                         "the importer errors and aborts the import."))
            elif kind == "HIRE":
                key = ref.strip()
                if key not in companion_ids:
                    problems.append(
                        ("ERROR", where,
                         f"HIRE '{ref}' has no CompanionDefinition.Id under Resources/Companions - "
                         "it is resolved only at runtime, where the hire logs 'no definition' and fails."))

    # Sort worst-first (ERROR before WARNING), then by location.
    order = {"ERROR": 0, "WARNING": 1}
    problems.sort(key=lambda p: (order[p[0]], p[1]))

    if not problems:
        print("check_quest_refs: every referenced asset resolves.")
        return 0

    n_err = sum(1 for p in problems if p[0] == "ERROR")
    n_warn = sum(1 for p in problems if p[0] == "WARNING")
    print(f"check_quest_refs: {n_err} error(s), {n_warn} warning(s).")
    for severity, where, msg in problems:
        print(f"  [{severity}] {where}: {msg}")
    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(run(strict="--strict" in sys.argv))