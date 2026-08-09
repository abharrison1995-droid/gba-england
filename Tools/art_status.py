#!/usr/bin/env python3
"""Generated-art status: what exists, what is wired, what is still owed.

The point of this script is that the art register is *derived* rather than
remembered. A hand-maintained "what's delivered" table goes stale the moment
someone forgets to update it, and the cost of that is a wasted generation
cycle drawing something that already exists.

It reads four things off disk and joins them by subject name:

  sheets       Assets/Art/Generated/characters/sheet_char_<subject>_<action>.png
  controllers  Assets/Animations/Generated/<subject>_Controller.controller
  presets      Assets/Data/Presets/*.asset          (their ArtSubject field)
  wiring       whether that preset has NpcController / NpcSprite resolved

Usage:
    python Tools/art_status.py              # the matrix, plus anything inconsistent
    python Tools/art_status.py --queue      # only what is outstanding
    python Tools/art_status.py --markdown   # a table to paste into docs/art/ART_QUEUE.md

On Linux this is python3 — Mint has no bare `python`.

It reports, it never writes. Nothing here touches Unity or the asset database,
so a green run says the *files* line up, not that anything imported correctly
or renders. That still needs the editor.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET_DIR = os.path.join(REPO, "Assets", "Art", "Generated", "characters")
CONTROLLER_DIR = os.path.join(REPO, "Assets", "Animations", "Generated")
PRESET_DIR = os.path.join(REPO, "Assets", "Data", "Presets")

# The importer builds a clip per action; these are the ones the pipeline asks for, and they are
# the matrix's columns. `cycle` is deliberately absent — it was cancelled, see CLAUDE.md §11.
KNOWN_ACTIONS = ["idle", "walk", "attack", "cast", "hurt", "death"]

# Recognised by the importer and wired into a controller, but NOT part of what any subject owes
# and deliberately not a matrix column. `roll` and `knockback` are bonus feedback on mechanics
# that already work silently — a class is released into gameplay by the six core actions above
# and by nothing else, so counting these would weaken the Young Driller fallback. Listed here
# only so they stop reading as "unrecognised action" once a subject has them.
BONUS_ACTIONS = ["roll", "knockback"]

RECOGNISED_ACTIONS = KNOWN_ACTIONS + BONUS_ACTIONS

# A full hostile set. A talker needs nothing like this, so asking every subject for
# it produces a queue that is mostly noise. Role is inferred instead, in role_of():
# a subject that already has any combat action is treated as hostile and owes the
# whole set; everything else owes an idle, plus a walk only if a preset makes it roam.
COMBAT_SET = ["idle", "walk", "attack", "hurt", "death"]
COMBAT_MARKERS = ("attack", "hurt", "death")

# Player-class requirements differ from inferred NPC roles, and four requested subjects exist
# before their first sheet does. Keep this small declarative exception in the derived report: the
# queue owns the request, while the rest of each row is still measured from disk.
PLAYER_CLASS_SETS = {
    "player": ["idle", "walk", "attack", "cast", "hurt", "death"],
    "player_stabmeister": ["idle", "walk", "attack", "cast", "hurt", "death"],
    "player_mrhood": ["idle", "walk", "attack", "cast", "hurt", "death"],
    "player_dynamo": ["idle", "walk", "attack", "cast", "hurt", "death"],
    "player_bundabasher": ["idle", "walk", "attack", "cast", "hurt", "death"],
}

SHEET_RE = re.compile(r"^sheet_char_(.+)_([a-z]+)\.png$")
ART_SUBJECT_RE = re.compile(r"^\s*ArtSubject:\s*(\S+)\s*$", re.M)
LABEL_RE = re.compile(r"^\s*Label:\s*(.+?)\s*$", re.M)
NPC_CONTROLLER_RE = re.compile(r"^\s*NpcController:\s*\{fileID:\s*(\d+)", re.M)
NPC_SPRITE_RE = re.compile(r"^\s*NpcSprite:\s*\{fileID:\s*(-?\d+)", re.M)
ROAMS_RE = re.compile(r"^\s*Roams:\s*(\d+)\s*$", re.M)


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def collect_sheets():
    """subject -> set(actions). Unknown actions are kept and flagged separately."""
    sheets = defaultdict(set)
    if not os.path.isdir(SHEET_DIR):
        return sheets
    for name in sorted(os.listdir(SHEET_DIR)):
        match = SHEET_RE.match(name)
        if match:
            sheets[match.group(1)].add(match.group(2))
    return sheets


def collect_controllers():
    if not os.path.isdir(CONTROLLER_DIR):
        return set()
    return {
        name[: -len("_Controller.controller")]
        for name in os.listdir(CONTROLLER_DIR)
        if name.endswith("_Controller.controller")
    }


def collect_presets():
    """art subject -> list of (preset filename, label, controller wired, sprite wired)."""
    presets = defaultdict(list)
    if not os.path.isdir(PRESET_DIR):
        return presets
    for name in sorted(os.listdir(PRESET_DIR)):
        if not name.endswith(".asset"):
            continue
        body = read(os.path.join(PRESET_DIR, name))
        subject = ART_SUBJECT_RE.search(body)
        if not subject:
            continue
        subject = subject.group(1)
        if subject in ("", "{}"):
            continue
        label = LABEL_RE.search(body)
        controller = NPC_CONTROLLER_RE.search(body)
        sprite = NPC_SPRITE_RE.search(body)
        roams = ROAMS_RE.search(body)
        presets[subject].append(
            {
                "file": name,
                "label": label.group(1) if label else name,
                "controller": bool(controller and controller.group(1) != "0"),
                "sprite": bool(sprite and sprite.group(1) != "0"),
                "roams": bool(roams and roams.group(1) != "0"),
            }
        )
    return presets


def collect_hostile_subjects():
    """Subjects whose controller is referenced by an enemy or police prefab.

    Derived rather than listed, so a new enemy is classified correctly the moment its
    prefab exists. Matching is by controller GUID, not by prefab name: Enemy_TorturedNeek
    happening to resemble `torturedneek` is a convention, and conventions drift.
    """
    controller_meta = {}
    if os.path.isdir(CONTROLLER_DIR):
        for name in os.listdir(CONTROLLER_DIR):
            if not name.endswith("_Controller.controller.meta"):
                continue
            match = re.search(r"^guid:\s*([0-9a-f]{32})", read(os.path.join(CONTROLLER_DIR, name)), re.M)
            if match:
                subject = name[: -len("_Controller.controller.meta")]
                controller_meta[match.group(1)] = subject

    hostile = set()
    prefab_dirs = [
        os.path.join(REPO, "Assets", "Prefabs", "Enemies"),
        os.path.join(REPO, "Assets", "Prefabs", "ModernBritain"),
    ]
    for directory in prefab_dirs:
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if not name.endswith(".prefab"):
                continue
            body = read(os.path.join(directory, name))
            for guid in re.findall(r"guid:\s*([0-9a-f]{32})", body):
                if guid in controller_meta:
                    hostile.add(controller_meta[guid])
    return hostile


def owed(actions, preset_list, hostile_subjects, subject):
    """Which actions this subject is still missing, judged against its role."""
    if subject in PLAYER_CLASS_SETS:
        role = "player"
        wanted = PLAYER_CLASS_SETS[subject]
    elif subject in hostile_subjects or any(a in actions for a in COMBAT_MARKERS):
        role = "hostile"
        wanted = list(COMBAT_SET)
    else:
        role = "talker"
        wanted = ["idle"]
        if any(p["roams"] for p in preset_list):
            wanted.append("walk")
    return role, [a for a in wanted if a not in actions]


def build_rows(sheets, controllers, presets, hostile_subjects):
    subjects = sorted(set(sheets) | set(controllers) | set(presets) | set(PLAYER_CLASS_SETS))
    rows = []
    for subject in subjects:
        actions = sheets.get(subject, set())
        preset_list = presets.get(subject, [])
        role, missing = owed(actions, preset_list, hostile_subjects, subject)
        rows.append(
            {
                "subject": subject,
                "actions": sorted(
                    actions,
                    key=lambda a: (
                        a not in RECOGNISED_ACTIONS,
                        RECOGNISED_ACTIONS.index(a) if a in RECOGNISED_ACTIONS else 0,
                        a,
                    ),
                ),
                "unknown": sorted(a for a in actions if a not in RECOGNISED_ACTIONS),
                "role": role,
                "missing": missing,
                "controller": subject in controllers,
                "presets": preset_list,
            }
        )
    return rows


def print_matrix(rows):
    width = max([len(r["subject"]) for r in rows] + [8])
    header = "subject".ljust(width) + "  " + "  ".join(a[:4].ljust(4) for a in KNOWN_ACTIONS)
    print(header + "   role     ctrl  presets")
    print("-" * len(header) + "   -------  ----  -------")
    for row in rows:
        cells = "  ".join(
            ("  X " if action in row["actions"] else "  . ") for action in KNOWN_ACTIONS
        )
        ctrl = " yes" if row["controller"] else "  - "
        names = ", ".join(p["label"] for p in row["presets"]) or "-"
        print(
            row["subject"].ljust(width)
            + "  "
            + cells
            + "   "
            + row["role"].ljust(7)
            + "  "
            + ctrl
            + "  "
            + names
        )


def print_markdown(rows):
    print(
        "| Subject | Role | "
        + " | ".join(a.capitalize() for a in KNOWN_ACTIONS)
        + " | Controller | Preset | Outstanding |"
    )
    print("|---" * (len(KNOWN_ACTIONS) + 5) + "|")
    for row in rows:
        cells = " | ".join("Y" if a in row["actions"] else "" for a in KNOWN_ACTIONS)
        names = ", ".join(p["label"] for p in row["presets"]) or "-"
        print(
            "| `%s` | %s | %s | %s | %s | %s |"
            % (
                row["subject"],
                row["role"],
                cells,
                "Y" if row["controller"] else "",
                names,
                ", ".join(row["missing"]) or "-",
            )
        )


def print_problems(rows, sheets, controllers, presets):
    problems = []

    for row in rows:
        subject = row["subject"]
        if row["actions"] and not row["controller"]:
            problems.append(
                "%s has %d sheet(s) but no controller — the importer has not run over it"
                % (subject, len(row["actions"]))
            )
        if row["controller"] and not row["actions"]:
            problems.append(
                "%s has a controller but no sheets — orphaned, or the sheets were moved" % subject
            )
        if row["unknown"]:
            problems.append(
                "%s has unrecognised action(s) %s — not in the pipeline's action list"
                % (subject, ", ".join(row["unknown"]))
            )
        for preset in row["presets"]:
            if row["actions"] and not (preset["controller"] and preset["sprite"]):
                unset = []
                if not preset["controller"]:
                    unset.append("NpcController")
                if not preset["sprite"]:
                    unset.append("NpcSprite")
                problems.append(
                    "%s: art exists but %s is unset on %s - run Tools > GBH > Content > "
                    "Wire Presets From Imported Art" % (subject, " and ".join(unset), preset["file"])
                )
            if preset["roams"] and "walk" not in row["actions"]:
                problems.append(
                    "%s: %s has Roams set but there is no walk sheet - it will slide"
                    % (subject, preset["file"])
                )
        if not row["actions"] and row["presets"]:
            problems.append(
                "%s: preset(s) %s are waiting on art that does not exist yet"
                % (subject, ", ".join(p["file"] for p in row["presets"]))
            )

    if problems:
        print("\nInconsistencies (%d):" % len(problems))
        for problem in problems:
            print("  ! " + problem)
    else:
        print("\nNo inconsistencies: every subject with art has a controller and a wired preset.")
    return problems


def print_queue(rows):
    print("Outstanding, judged against each subject's inferred role:")
    any_outstanding = False
    for row in rows:
        if row["missing"] and (row["actions"] or row["subject"] in PLAYER_CLASS_SETS):
            any_outstanding = True
            delivered = ", ".join(row["actions"]) if row["actions"] else "no art"
            print(
                "  %-18s %-8s has %-24s owes %s"
                % (
                    row["subject"],
                    row["role"],
                    delivered,
                    ", ".join(row["missing"]),
                )
            )
    if not any_outstanding:
        print("  (none)")

    print("\nNo art at all - requested player sets or presets waiting on a subject:")
    any_waiting = False
    for row in rows:
        if not row["actions"] and (row["presets"] or row["subject"] in PLAYER_CLASS_SETS):
            any_waiting = True
            labels = ", ".join(p["label"] for p in row["presets"])
            print("  %-18s %s" % (row["subject"], labels or "requested player class"))
    if not any_waiting:
        print("  (none)")

    print(
        "\nRole: hostile if an enemy or police prefab references the subject's controller, or if\n"
        "any attack/hurt/death sheet already exists. Everything else is a talker, which owes an\n"
        "idle plus a walk only if one of its presets roams. Reserved player-class subjects owe\n"
        "all six actions even before their first sheet exists.\n"
        "\nThis reads filenames and GUIDs, not controller contents - a controller that exists but\n"
        "never references its walk clip looks complete here and still slides in game."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--markdown", action="store_true", help="emit a Markdown table")
    parser.add_argument("--queue", action="store_true", help="only what is still outstanding")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any inconsistency is found (for a pre-commit or CI check)",
    )
    args = parser.parse_args()

    sheets = collect_sheets()
    controllers = collect_controllers()
    presets = collect_presets()
    hostile_subjects = collect_hostile_subjects()
    rows = build_rows(sheets, controllers, presets, hostile_subjects)

    if not rows:
        print("No generated art found under %s" % SHEET_DIR)
        return 0

    if args.markdown:
        print_markdown(rows)
        return 0

    if args.queue:
        print_queue(rows)
        return 0

    print(
        "%d subjects, %d sheets, %d controllers, %d presets with an ArtSubject\n"
        % (
            len(rows),
            sum(len(a) for a in sheets.values()),
            len(controllers),
            sum(len(p) for p in presets.values()),
        )
    )
    print_matrix(rows)
    problems = print_problems(rows, sheets, controllers, presets)
    print_queue(rows)

    return 1 if (args.strict and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
