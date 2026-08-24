---
name: brute-force-loop-v2
description: >-
  Iterative improvement loop (Mid-Budget / All-Flash Multi-Pass). Employs 7 parallel Gemini 3.7 Flash reviewers, Gemini 3.7 Flash (High Reasoning) Orchestrator, Gemini 3.7 Flash Implementor, 6× Flash verification swarm, and non-obstructive usage checkpoints (A-D). Auto-loops up to 3 times.
---

# Brute-Force Loop v2 (Mid-Tier / All-Flash Multi-Pass)

An autonomous multi-stage iteration loop leveraging specialized parallel Gemini 3.7 Flash reviewers, orchestrated by a High-Reasoning Gemini 3.7 Flash architect and verified by a 6× Flash swarm.

---

## Architecture & Flow

```
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint A: Pre-Flight Gate (Headroom Verification)       │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 1: Initial Reviewers (7× Parallel 3.7 Flash Swarm)     │
   │ Multi-angle code, invariant & performance analysis          │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 2: Orchestrator (Gemini 3.7 Flash - High Reasoning)    │
   │ Deep synthesis, resolves conflicts, crafts plan             │
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
   │ Executes changes, applies edits, verifies syntax            │
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
   │ Step 5: Orchestrator Decision (Flash - High Reasoning)      │
   │ Evaluates: Standards met? Gameplay/playability improved?    │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint D: Inter-Loop Re-entry Gate (Max 3 Loops)        │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
          Issues / Fixes Found            All Standards Met OR
          & Iterations < 3                Iterations == 3
                 │                                 │
                 ▼                                 ▼
        [Loop Back to Step 2]             [Final State Report]
```

---

## Detailed Execution Steps

### Checkpoint A: Pre-Flight Gate
- Verify headroom before initiating 7-agent initial review.

### Step 1: Diverse Initial Review Swarm (7× Gemini 3.7 Flash Subagents)
Spawn 7 subagents simultaneously via `invoke_subagent` (`Model: "flash"`):
- **Reviewer 1 & 2**: Real-time logic, API ergonomics & requirements matching.
- **Reviewer 3 & 4**: Control flow, state invariants, edge conditions.
- **Reviewer 5 & 6**: Syntax validation, dead code, performance & allocations.
- **Reviewer 7**: High-level architecture, subsystem boundaries & contracts.

### Step 2: High-Reasoning Flash Orchestrator Planning
The Orchestrator (`Model: flash`, High reasoning):
- Synthesizes all 7 reviewer inputs, eliminating noise and deduplicating insights.
- Formulates a robust **Implementation Plan** prioritizing critical bugfixes, contract preservation, and game feel/performance.

### Checkpoint B: Pre-Execution Safety Gate
- Ensure the plan is fully documented and structured before modifying files.

### Step 3: Implementor Execution (Gemini 3.7 Flash)
The Implementor (`Model: flash`):
- Executes all plan items accurately using file editing tools.
- Ensures atomic edits without orphaned references or broken dependencies.

### Checkpoint C: Pre-Verification Gate
- Verify capacity before launching the 6-agent verification swarm.

### Step 4: Verification Swarm (`review-swarm-v1`)
Run the 6× 3.7 Flash parallel review swarm on the modified files to evaluate:
- Logic & Correctness
- Security & Data Integrity
- Performance & Memory
- System Architecture & Contracts
- Edge Cases & Exceptions
- Code Quality & Maintainability

### Step 5: Orchestrator Decision (High Reasoning)
- Check if any blocker, major defect, or gameplay degradation remains.
- Check if obvious playability/performance improvements can be made.

### Checkpoint D & Auto-Loop Logic
Track `iteration_count` (starting at 1):
- **IF** issues/improvements remain **AND** `iteration_count < 3`:
  - Increment `iteration_count += 1`.
  - Log: `"[Loop iteration_count/3] Auto-looping to resolve remaining issues..."`.
  - Loop back to **Step 2** to update the plan and re-implement without waiting for user input.
- **ELSE** (Clean pass OR `iteration_count == 3`):
  - Emit the **Final State Report** with diff summaries, iteration history, and final sign-off.
