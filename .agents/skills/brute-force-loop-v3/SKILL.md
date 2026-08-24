---
name: brute-force-loop-v3
description: >-
  Iterative improvement loop (Premium / Opus-Orchestrated tier). Employs 8 parallel Gemini 3.7 Flash reviewers, Claude Opus 4.6 Orchestrator, Gemini 3.7 Flash Implementor, 6× Flash verification swarm, and usage checkpoints (A-D). Auto-loops up to 3 times.
---

# Brute-Force Loop v3 (Premium / Opus-Orchestrated Tier)

An advanced multi-stage autonomous development loop combining an 8-agent parallel Gemini 3.7 Flash review swarm with Claude Opus 4.6 master orchestration, high-speed Gemini 3.7 Flash implementation, 6× Flash verification swarm, and non-obstructive usage checkpoints.

---

## Architecture & Flow

```
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint A: Pre-Flight Gate (Headroom Verification)       │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 1: Initial Reviewers (8× Parallel 3.7 Flash Swarm)     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 2: Orchestrator (Claude Opus 4.6 / Top Tier)           │
   │ Deep architectural synthesis, trade-off analysis & plan     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint B: Pre-Execution Safety Gate                     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 3: Implementor (Gemini 3.7 Flash)                      │
   │ High-velocity, exact code modification and syntax check     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint C: Pre-Verification Swarm Gate                   │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 4: Verification Swarm (review-swarm-v1)                 │
   │ 6× Parallel 3.7 Flash reviewers inspect changes and diffs   │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 5: Orchestrator Decision (Claude Opus 4.6)             │
   │ Evaluates: Invariants preserved? Game feel/UX optimized?    │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint D: Inter-Loop Re-entry Gate (Max 3 Loops)        │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
          Issues / Improvements Found     All Standards Met OR
          & Iterations < 3                Iterations == 3
                 │                                 │
                 ▼                                 ▼
        [Loop Back to Step 2]             [Final State Report]
```

---

## Detailed Execution Steps

### Checkpoint A: Pre-Flight Gate
- Verify operational headroom for Opus master orchestration.

### Step 1: 8× Parallel Review Swarm (Gemini 3.7 Flash)
Spawn 8 subagents simultaneously via `invoke_subagent` (`Model: "flash"`):
- **Reviewer 1 & 2**: Real-time logic, intent matching & feature completeness.
- **Reviewer 3 & 4**: Control flow, state invariants, edge conditions.
- **Reviewer 5 & 6**: Syntax validation, dead code, linting & allocations.
- **Reviewer 7 & 8**: System architecture, subsystem contracts, memory safety.

### Step 2: Opus Orchestration & Master Planning
The Orchestrator (`Model: inherit` / Claude Opus 4.6):
- Conducts master synthesis of all 8 reviews, identifying systemic root causes rather than surface symptoms.
- Authors an airtight **Implementation Plan** preserving backward compatibility, serialization keys, and clean modular boundaries.

### Checkpoint B: Pre-Execution Safety Gate
- Ensure the plan is fully recorded to an artifact before beginning file operations.

### Step 3: Fast Flash Implementor
The Implementor (`Model: flash` / 3.7 Flash):
- Executes the planned changes with atomic file operations.
- Guarantees clean code structure and zero dangling references.

### Checkpoint C: Pre-Verification Gate
- Verify capacity before triggering the 6-agent verification swarm.

### Step 4: Verification Swarm (`review-swarm-v1`)
Spawn the 6× 3.7 Flash parallel review swarm to test the implementation across all 6 core pillars (Correctness, Security, Performance, Architecture, Edge Cases, Maintainability).

### Step 5: Opus Decision & Quality Assessment
The Orchestrator (Claude Opus 4.6):
- Assesses blocker/major defects.
- Evaluates UX, responsiveness, playability, and architectural polish.

### Checkpoint D & Autonomous Looping
Maintain `iteration_count` (starting at 1):
- **IF** any issues, risks, or high-value improvements remain **AND** `iteration_count < 3`:
  - Increment `iteration_count += 1`.
  - Log: `"[Loop iteration_count/3] Opus Orchestrator re-routing fixes and refinements..."`.
  - Return to **Step 2** to update the plan and re-execute without prompting the user.
- **ELSE** (Clean pass OR `iteration_count == 3`):
  - Terminate the loop.
  - Emit the **Final State Report** with comprehensive diff breakdown, iteration history, and final sign-off.
