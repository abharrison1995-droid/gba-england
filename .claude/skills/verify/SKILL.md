---
name: verify
description: Run the only checks that can run without Unity — reference integrity, art status, brace-balance scans — and report honestly what they prove versus what still needs the editor, cross-referenced against the CLAUDE.md §5 never-verified ledger. Use before claiming anything works, or after an asset move/rename/edit. For GBH: England.
---

# Verify (honestly)

**There is no C# compiler, no Unity, and no test framework here.** This skill runs the mechanical
checks that *can* run, and — just as important — states plainly what they do **not** prove. The
project's single biggest failure mode is reporting "works" when nothing compiled it. Do not commit it.

## Run these

On Linux use `python3` (Mint has no bare `python`):

- `python Tools/asset_reachability.py --check-dangling` — reference integrity. Exit `0` clean,
  `1` dangling, `2` couldn't verify. It resolves GUIDs from `Assets/`, `Packages/` **and**
  `Library/PackageCache/`; `Library/` is gitignored, so on a fresh clone it reports `2` (checked
  nothing) rather than a false pass. Anything unresolved beyond the named `KNOWN_DANGLING` set fails.
- `python Tools/asset_reachability.py --packs` — which asset packs are fully unused.
- `python Tools/art_status.py` — what art exists and what is still owed.
- Brace/paren balance scans where relevant: `python Tools/check_quest_phase0.py`,
  `python Tools/precheck_sheets.py`.

Run `--check-dangling` **before and after** anything that deletes, moves or renames assets.

## What each result actually means

- **`--check-dangling` passing says nothing about whether the project builds.** It proves GUID
  references resolve, no more.
- **A brace/paren balance scan catches a truncated edit. It is NOT a compile.** Never report it as
  one. It says nothing about correctness or whether the code compiles.
- **The only agent-side proof a script compiled is that an editor tool which references it ran
  successfully** — and that proves compilation only, never behaviour.
- Reference integrity, art status, brace balance — all green still leaves the actual behaviour
  unproven. Say so.

## Report

Produce a short, honest summary in three buckets:

1. **Confirmed mechanically** — which checks ran, their exit codes, what that proves (narrowly).
2. **Not proven here** — compilation and behaviour, unless an editor tool run establishes
   compilation; name what still needs a human in the editor.
3. **Ledger** — cross-reference the change against the `CLAUDE.md §5` never-verified list: which
   entries this touches, and the exact in-editor routes to confirm them. If an item is now
   confirmed, note it should be deleted from the ledger rather than left hedged.

## Never

- Describe a balance scan or a passing dangling check as a compile or a test.
- Say a change "works", "is fixed", or "is verified" on mechanical checks alone.
- Leave the §5 ledger stale — a confirmed item is deleted, not struck through.
