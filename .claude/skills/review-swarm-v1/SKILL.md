---
name: review-swarm-v1
description: Summon 6 Haiku reviewers to assess a given task, diff, or piece of code in parallel and consolidate their findings. Review only — no implementation, no loop. For GBH: England.
---

# Review Swarm v1

Fan out **6 Haiku reviewers** across a task and consolidate what they find. This is a pure review
pass — it implements nothing and does not loop. Use it to pressure-test a diff, a plan, or a chunk
of code before trusting it.

## Roster

| Role | Count | Model (Agent tool `model`) | Effort |
|---|---|---|---|
| Reviewers | 6 | `haiku` | brief, focused (default) |

**Honesty note (per CLAUDE.md §6):** `model` + a directive is the best available control; nothing
inside a session can prove which model served a subagent.

## Run it

1. **Fix the target.** Be explicit about what's under review — a diff (`git diff`), specific files,
   a plan doc, or the working tree. Capture it so all 6 review the same thing.
2. **Feed the routing.** Read the relevant `docs/reference/*` for the subsystem first and include it
   in each prompt, so 6 agents don't each re-derive the project's invariants cold.
3. **Spawn 6 `general-purpose` agents, `model: haiku`, read-only** (Read/Grep/Glob/Bash-for-search
   only; no Edit/Write). Partition the target across them — assign each a slice of files or a
   distinct lens (save keys & serialization, chunk lifecycle, `.meta`/GUID integrity, `Physics2D`
   creep, correctness, request-fidelity) so you get coverage, not 6 identical summaries. Background
   them and collect all 6.
4. **Consolidate.** Merge into one deduplicated, severity-ranked list: confirmed issues first, then
   plausible/uncertain, then noise. Attribute each finding to `file:line`. Report to the owner.

## What this does not do

- It does not fix anything and does not re-run itself. If the owner wants fixes, that's a separate
  step (or a brute-force loop).
- Green reviews prove nothing about whether the project compiles or runs — say so (there is no
  compiler/Unity here; see the `verify` skill).
