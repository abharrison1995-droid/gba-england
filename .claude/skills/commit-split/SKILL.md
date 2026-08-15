---
name: commit-split
description: Carve an intermixed working tree into ordered, single-concern commits, safely — .meta travels with its asset, moved assets keep their GUID, scenes and prefabs are never hunk-split, and mixed source files are split losslessly. Use when the working tree holds several features at once and needs clean, ordered commits. For GBH: England.
---

# Commit split

Turn one big intermixed working tree into a sequence of clean, single-concern commits — in an order
the user gives, or one you propose and they approve. This repo's working trees routinely hold
several features at once, and **uncommitted edits are discarded on a branch switch/merge**, so
committing as you go is the whole point.

## Read first

- `docs/reference/REPO_HYGIENE.md` — the project's git, asset-pruning and `.gitattributes` rules.

## Survey, then plan

1. `git status --short --untracked-files=all` and `git diff --stat`. Expand untracked dirs.
2. Group every path into feature buckets. Confirm the **order** with the user before committing —
   order is preserved by commit creation order, so go strictly front-to-back.
3. If on `main`/`master`, branch first. Never push unless asked.

## Safety rules — these prevent silent orphaning

- **A `.meta` travels in the same commit as the file it describes.** A script's `.meta` GUID is what
  binds prefabs/scene to the class.
- **A moved asset must keep its HEAD GUID.** Before committing a move, verify:
  `git show HEAD:<old.meta> | grep guid` equals the disk `<new.meta>` guid. A fresh GUID on a moved
  asset orphans every reference — investigate before proceeding.
- **Never hunk-split a `.unity` scene or a `.prefab`.** They land whole, in exactly one commit. If a
  scene/prefab genuinely spans features, give it its own commit rather than splitting it.
- **A source file (`.cs`, docs) whose diff mixes two features → split it losslessly:** snapshot the
  full file, edit it down to the earlier feature's hunks only, verify `git diff` shows just that
  feature, commit; then restore the snapshot so the remainder falls into the later commit. Confirm
  the recombination is byte-identical (ignoring CRLF/LF) before trusting it.
- **New enemy/asset placement in a scene or prefab** that references another commit's new asset is
  fine across commits (git has no per-commit build requirement) — but keep each `.png`+`.png.meta`,
  each `.asset`+`.asset.meta` pair together.

## Per bucket

- Stage exactly that bucket (`git add -- <paths>`; `git add -A -- <dir>` then `git reset` the
  strays). Print `git diff --cached --name-status` and eyeball it before committing.
- One concern per commit. Message body says what and why, and — for this repo — states honestly that
  the change is **unbuilt/unrun** if no editor or compiler has seen it.
- End the message with the repo's trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## Notes that trip people up

- `LF will be replaced by CRLF` warnings are benign — git normalises to LF in the blob; working-tree
  line endings don't affect committed content.
- Git's rename detection (`R###`) in a split is cosmetic pairing of a delete with an add; the blobs
  are independent — still verify GUIDs when it pairs two `.meta` files.
- Run `python Tools/asset_reachability.py --check-dangling` before and after the run (see the
  `verify` skill) to confirm no new breakage — exit 0 and "nothing beyond the known set".

## Finish

Report the commit list (`git log --oneline <base>..HEAD`), confirm the tree is clean, and flag
anything that appeared mid-session and was **not** yours to commit rather than sweeping it in.

## Never

- Hunk-split a scene or prefab, or commit a `.meta` apart from its asset.
- Let a moved asset take a new GUID.
- Push, force-push, or amend a pushed commit unless the user explicitly asks.
- Claim a committed change compiles or works — commit-split proves nothing about behaviour.
