---
name: brute-force-loop-v2
description: Heavier variant of the improvement loop for one premise/idea/feature/bug — Opus orchestrator AND Opus planner, a 5-Sonnet + 10-Haiku assessment swarm, Sonnet implements, then 4 Sonnet-medium reviewers judge it. Restart-from-reviewers on failure, always asking the owner first. For GBH: England.
---

# Brute Force Improvement Loop v2

Same shape as v1, a heavier and more Opus/Sonnet-weighted roster. You (the invoking session) are the
top-level driver and the **final judge** of sufficiency.

## Roster (this version)

| Role | Count | Model (Agent tool `model`) | Effort directive in the prompt |
|---|---|---|---|
| Orchestrator | 1 | `opus` | "Ultrathink." (High) |
| Assessment reviewers | 5 | `sonnet` | normal |
| Assessment reviewers | 10 | `haiku` | brief, focused (default) |
| Planner | 1 | `opus` | "Ultrathink." (High) |
| Implementer | 1 | `sonnet` | "Think hard." |
| Post-impl reviewers | 4 | `sonnet` | normal (Medium) |

**Honesty note (per CLAUDE.md §6):** `model` + a think-directive is the best available control. It
launches without error but nothing inside a session can *prove* which model/effort served a
subagent. Do not claim otherwise.

## Preconditions

- Read the relevant `docs/reference/*` for the request's subsystem before spawning anyone (§3/§4).
  Feed that routing into the swarm prompts so the swarm doesn't re-derive it cold.
- Capture the request text verbatim; everything downstream is judged against it.

## The loop

### Step 1 — Orchestrator (1× Opus, High)
Spawn one `general-purpose` agent, `model: opus`, prompt beginning "Ultrathink." It scopes the
request, identifies touched files/subsystems, and produces a **numbered assessment brief** — the
questions the assessment swarm must each answer against the codebase. Read-only. Relay it back.

### Step 2 — Assessment swarm (5× Sonnet + 10× Haiku)
Spawn 5 `general-purpose` `model: sonnet` + 10 `general-purpose` `model: haiku`, all **read-only**
(no Edit/Write). Partition the orchestrator's brief across the 15 so coverage doesn't collapse into
identical answers — give the 5 Sonnets the harder/higher-risk slices (save keys, serialization,
chunk lifecycle), the 10 Haikus the broader file sweep. Background them; collect all 15 findings.

### Step 3 — Planner (1× Opus, High)
Spawn one `general-purpose` agent, `model: opus`, prompt beginning "Ultrathink." Hand it the request
+ orchestrator brief + all 15 findings. It produces the **implementation plan and mapping table**
(§3). Read-only.

### Step 4 — Implementer (1× Sonnet)
Spawn one `general-purpose` agent, `model: sonnet`, prompt beginning "Think hard." Executes the plan
**strictly** — small single-concern commits, no scope improvisation. Reports what it changed.

### Step 5 — Post-implementation review (4× Sonnet, Medium)
Spawn 4 `general-purpose` `model: sonnet` (normal effort), **read-only**, reviewing the diff against
the plan and the original request. Hunt silent failure modes, not style. Collect all 4 verdicts.

### Step 6 — Judge (you)
- **Sufficient** → run the `verify` skill's mechanical checks, report the result and diff to the
  owner, and stop.
- **Not sufficient** → **STOP and ask the owner for permission to re-engage the loop from Step 2**,
  showing the reviewer findings and what the next pass would cover. Never restart on your own.

## The restart rule (mandatory)

> You MUST ask the owner before re-engaging the loop, every time, so they can keep tabs on usage.

The first pass runs once invoked. Every subsequent pass needs an explicit yes. Re-entry is always at
Step 2 (reviewers first), carrying forward the plan and the prior failure findings.

## Cost note
One full pass ≈ 21 agent spawns, weighted toward Opus/Sonnet. Say so if the owner seems unaware;
never launch a restart silently.
