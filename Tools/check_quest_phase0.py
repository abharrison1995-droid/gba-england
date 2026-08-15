"""Brace/paren/bracket balance scan for the Phase 0 quest changes.

This is NOT a compile. It only catches a truncated edit. See CLAUDE.md §5.
"""
import sys

FILES = [
    "Assets/Scripts/Quests/QuestManager.cs",
    "Assets/Scripts/Quests/QuestConditionWatcher.cs",
    "Assets/Scripts/UI/QuestTrackerUI.cs",
    "Assets/Scripts/UI/QuestJournalUI.cs",
    "Assets/Scripts/Flow/SaveGameManager.cs",
    "Assets/Scripts/Flow/GameFlowController.cs",
    "Assets/Scripts/Data/DialogueData.cs",
    "Assets/Scripts/Dialogue/DialogueManager.cs",
    "Assets/Editor/DialogueValidator.cs",
    "Assets/Editor/QuestTextImporter.cs",
    "Assets/Editor/QuestContentValidator.cs",
]

PAIRS = [("{", "}"), ("(", ")"), ("[", "]")]

ok = True
for f in FILES:
    try:
        s = open(f, encoding="utf-8").read()
    except OSError as e:
        print(f"{f}: could not read ({e})")
        ok = False
        continue
    for a, b in PAIRS:
        ca, cb = s.count(a), s.count(b)
        if ca != cb:
            print(f"{f}: {a}{b} imbalance {ca} vs {cb}")
            ok = False

print("BALANCE OK" if ok else "IMBALANCE FOUND")
sys.exit(0 if ok else 1)
