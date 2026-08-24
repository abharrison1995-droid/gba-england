---
name: brute-force-loop-v1
description: >-
  Iterative autonomous development & improvement loop (Budget tier). Uses 3× Gemini 3.7 Flash reviewers, Gemini 3.7 Flash Orchestrator & Implementor, 6× Gemini 3.7 Flash review swarm, and non-obstructive usage checkpoints (A-D). Auto-loops up to 3 times.
---

# Brute-Force Loop v1 (Budget / All-Flash Tier)

An autonomous multi-stage iteration loop powered entirely by Gemini 3.7 Flash for fast, intelligent development and refactoring with a rigorous 6× verification swarm and usage checkpoints.

---

## Architecture & Flow

```
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint A: Pre-Flight Gate (Headroom Verification)       │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 1: Initial Review (3× Gemini 3.7 Flash Reviewers)      │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 2: Orchestrator (Gemini 3.7 Flash)                     │
   │ Synthesizes findings and authors implementation plan        │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint B: Pre-Execution Safety Gate                     │
   │ Ensures plan is safely staged before modifying codebase     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 3: Implementor (Gemini 3.7 Flash)                      │
   │ Applies code changes and executes modifications             │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint C: Pre-Verification Swarm Gate                   │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 4: Verification Review Swarm (review-swarm-v1)         │
   │ 6× Parallel 3.7 Flash reviewers inspect changes and diffs   │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 5: Orchestrator Decision                               │
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
- Verify operational headroom before firing initial swarm.

### Step 1: Initial Reviewers (3× Gemini 3.7 Flash)
Spawn 3 parallel `flash` reviewers via `invoke_subagent`:
- **Reviewer A**: Demands & Requirements Compliance.
- **Reviewer B**: Logic, Bugs & Edge Cases.
- **Reviewer C**: Performance & User Experience / Playability.

### Step 2: Orchestrator Planning (Gemini 3.7 Flash)
The Orchestrator (`Model: flash`):
- Consolidates findings from the initial review (or from Step 4 if in an active loop).
- Formulates a targeted, minimal-risk **Implementation Plan** with concrete code edit steps.

### Checkpoint B: Pre-Execution Safety Gate
- If large modifications are planned, ensure the plan is saved to an artifact before starting file modifications.

### Step 3: Implementor Execution (Gemini 3.7 Flash)
The Implementor subagent (`Model: flash`):
- Executes the planned changes using `replace_file_content` or `write_to_file`.
- Verifies edits are syntactically sound and preserves existing code contracts.

### Checkpoint C: Pre-Verification Gate
- Verify capacity before triggering the 6-agent verification swarm.

### Step 4: Verification Swarm (`review-swarm-v1`)
Spawn 6 parallel `flash` reviewers to assess the resulting code and diffs across:
1. Correctness & State Logic
2. Security & Data Integrity
3. Performance & Memory
4. Architecture & Contracts
5. Edge Cases & Error Handling
6. Maintainability & Code Quality

### Step 5: Orchestrator Decision
Evaluate all findings:
- Check if Blocker/Major issues remain.
- Identify straightforward playability/experience improvements.

### Checkpoint D & Auto-Loop Logic
Maintain `iteration_count` (starting at 1):
- **IF** issues/improvements exist **AND** `iteration_count < 3`:
  - Increment `iteration_count += 1`.
  - Log: `"[Loop iteration_count/3] Auto-looping to implement fixes & refinements..."`.
  - Return to **Step 2** to update the plan and re-implement without waiting for user input.
- **ELSE** (Clean pass OR `iteration_count == 3`):
  - Present the **Final State Report** summarizing all iterations, changes made, and final review verdicts.
