---
name: review-swarm-v2
description: Summon 6 Haiku + 2 Sonnet reviewers to assess a given task, diff, or piece of code in parallel and consolidate their findings. Review only — no implementation, no loop. For GBH: England.
---

# Review Swarm v2

Fan out **6 Haiku + 2 Sonnet reviewers** across a task and consolidate what they find. A pure review
pass — implements nothing, does not loop. The two Sonnets carry the higher-risk lenses; the six
Haikus carry breadth.

## Roster

| Role | Count | Model (Agent tool `model`) | Effort |
|---|---|---|---|
| Reviewers | 2 | `sonnet` | normal |
| Reviewers | 6 | `haiku` | brief, focused (default) |

**Honesty note (per CLAUDE.md §6):** `model` + a directive is the best available control; nothing
inside a session can prove which model served a subagent.

## Run it

1. **Fix the target.** Be explicit about what's under review — a diff (`git diff`), specific files,
   a plan doc, or the working tree. Capture it so all 8 review the same thing.
2. **Feed the routing.** Read the relevant `docs/reference/*` for the subsystem first and include it
   in each prompt, so the swarm doesn't re-derive the project's invariants cold.
3. **Spawn the swarm, all read-only** (Read/Grep/Glob/Bash-for-search only; no Edit/Write):
   - **2 `general-purpose` `model: sonnet`** — the high-risk lenses: save keys & serialization,
     chunk lifecycle (the seven instantiation paths, the eight `CurrentChunkData` writers,
     `SetActive(false)` hazards), `.meta`/GUID integrity, and request-fidelity.
   - **6 `general-purpose` `model: haiku`** — breadth: partition the files/questions so you get
     coverage, not identical summaries (correctness, `Physics2D` creep, orphaned refs, per-area
     file sweeps).
   - Background them all; collect 8.
4. **Consolidate.** Merge into one deduplicated, severity-ranked list: confirmed first, then
   plausible/uncertain, then noise. Attribute each finding to `file:line`. Where a Sonnet and a
   Haiku disagree, prefer the Sonnet's read but surface both. Report to the owner.

## What this does not do

- It does not fix anything and does not re-run itself. Fixes are a separate step (or a brute-force
  loop).
- Green reviews prove nothing about whether the project compiles or runs — say so (there is no
  compiler/Unity here; see the `verify` skill).
