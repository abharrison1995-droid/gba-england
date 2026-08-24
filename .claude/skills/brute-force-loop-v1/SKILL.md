---
name: brute-force-loop-v1
description: Heavy multi-agent improvement loop for one premise/idea/feature/bug — a Sonnet orchestrator runs a 16-Haiku assessment swarm, an Opus planner writes the plan, Sonnet implements, then 2 Sonnet + 6 Haiku reviewers judge it. Restart-from-reviewers on failure, always asking the owner first. For GBH: England.
---

# Brute Force Improvement Loop v1

A deliberately expensive, high-coverage loop for turning **one** request — a premise, idea,
feature, bug, or similar — into a reviewed, implemented change. You (the invoking session) are the
top-level driver and the **final judge** of sufficiency.

## Roster (this version)

| Role | Count | Model (Agent tool `model`) | Effort directive in the prompt |
|---|---|---|---|
| Orchestrator | 1 | `sonnet` | "Think hard." (High) |
| Assessment reviewers | 16 | `haiku` | brief, focused (default) |
| Planner | 1 | `opus` | "Think hard / ultrathink." (High) |
| Implementer | 1 | `sonnet` | "Think hard." (High) |
| Post-impl reviewers | 2 | `sonnet` | normal (Medium) |
| Post-impl reviewers | 6 | `haiku` | brief, focused (default) |

**Honesty note (per CLAUDE.md §6):** setting `model` and a think-directive is the best available
control. It launches without error, but nothing inside a session can *prove* which model/effort
actually served a subagent. Do not claim otherwise.

## Preconditions

- Read the relevant `docs/reference/*` for the request's subsystem before spawning anyone (§3/§4 of
  CLAUDE.md). Feed that routing into the swarm prompts so 16 agents don't each re-derive it cold.
- Confirm you have the request text captured verbatim. Everything downstream is judged against it.

## The loop

### Step 1 — Orchestrator (1× Sonnet, High)
Spawn one `general-purpose` agent, `model: sonnet`, prompt beginning "Think hard." Its job: read the
request, scope which files/subsystems it touches, and produce a **numbered assessment brief** — the
list of concrete questions the 16 reviewers must each answer against the codebase (e.g. "does X save
key move?", "which of the seven chunk-instantiation paths does this touch?"). It does **not** edit
code. Relay its brief back to you.

### Step 2 — Assessment swarm (16× Haiku)
Spawn 16 `general-purpose` agents, `model: haiku`, **read-only** (instruct them: no Edit/Write, only
Read/Grep/Glob/Bash-for-search). Partition the orchestrator's brief across them — assign each a slice
of files/questions so coverage doesn't collapse into 16 identical answers. Each returns findings:
risks, affected files, save/serialization hazards, and a go/no-go on feasibility. Background them;
collect all 16.

### Step 3 — Planner (1× Opus, High)
Spawn one `general-purpose` agent, `model: opus`, prompt beginning "Ultrathink." Hand it the original
request + orchestrator brief + all 16 findings. It produces the **implementation plan and mapping
table** (§3: explicit mapping table before any rename/serialized-field/save-key change). Read-only.

### Step 4 — Implementer (1× Sonnet, High)
Spawn one `general-purpose` agent, `model: sonnet`, prompt beginning "Think hard." It executes the
plan **strictly** — small single-concern commits, no scope improvisation. It reports what it changed.

### Step 5 — Post-implementation review (2× Sonnet Medium + 6× Haiku)
Spawn 2 `general-purpose` `model: sonnet` (normal effort) + 6 `general-purpose` `model: haiku`,
all **read-only**, reviewing the diff against the plan and against the original request. They hunt
silent failure modes (orphaned GUIDs, dropped save keys, `.meta` mismatches, `Physics2D` sneaking
in), not style. Collect all 8 verdicts.

### Step 6 — Judge (you)
You decide sufficiency: does the implemented change do **what was asked** and survive the reviewers?
- **Sufficient** → run the `verify` skill's mechanical checks, report the result and the diff to the
  owner, and stop.
- **Not sufficient** → **STOP and ask the owner for permission to re-engage the loop from Step 2**,
  showing them the reviewer findings and what the next pass would cover. Do not restart on your own.

## The restart rule (mandatory)

> You MUST ask the owner before re-engaging the loop, every time, so they can keep tabs on usage.

The first pass runs once invoked. Every subsequent pass needs an explicit yes. Re-entry is always at
Step 2 (reviewers first), carrying forward the plan and the prior failure findings.

## Cost note
One full pass ≈ 26 agent spawns. Say so if the owner seems unaware; never launch a restart silently.
