---
name: brute-force-loop-v0
description: >-
  Ultra-budget autonomous iteration loop. Employs 3× Flash-Lite reviewers, Gemini 3.7 Flash (Low Effort) Orchestrator & Implementor, 6× Flash-Lite verification swarm, and non-obstructive usage checkpoints (A-D). Auto-loops up to 3 times.
---

# Brute-Force Loop v0 (Ultra-Budget Tier)

An ultra-budget autonomous iteration loop designed for fast, continuous development with near-zero quota impact, verified by lightweight parallel swarms and guarded by usage checkpoints.

---

## Architecture & Flow

```
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint A: Pre-Flight Gate (Verify Init Headroom)        │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 1: Initial Review (3× Flash-Lite Reviewers)            │
   │ Model: flash_lite | Ultra-low token footprint               │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 2: Orchestrator (Gemini 3.7 Flash - Low Effort)        │
   │ Synthesizes findings into a clear implementation plan       │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint B: Pre-Execution Safety Gate                     │
   │ Ensures plan is intact before modifying files               │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 3: Implementor (Gemini 3.7 Flash - Low Effort)         │
   │ Executes code changes and verifies clean syntax             │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Checkpoint C: Pre-Verification Gate                         │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 4: Verification Swarm (review-swarm-v0)                │
   │ 6× Parallel Flash-Lite reviewers inspect changes and diffs  │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Step 5: Orchestrator Decision (Flash - Low Effort)          │
   │ Evaluates: Standards met? UX / Playability enhanced?        │
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
- Verify connectivity and ensure session state is clean before initiating swarm.

### Step 1: Initial Reviewers (3× Flash-Lite)
Spawn 3 parallel `flash_lite` subagents via `invoke_subagent`:
- **Reviewer A**: Demands & Requirements Compliance.
- **Reviewer B**: Logic, Bugs & Edge Cases.
- **Reviewer C**: Performance & User Experience.

### Step 2: Orchestrator Planning (Gemini 3.7 Flash - Low Effort)
- Consolidates findings from initial review (or verification swarm on loop iterations).
- Formulates a targeted **Implementation Plan** with concrete code edit steps.

### Checkpoint B: Pre-Execution Safety Gate
- Ensure the planned code edits are self-contained. If rate limits are constrained, save the plan to an artifact first so work is never lost.

### Step 3: Implementor Execution (Gemini 3.7 Flash - Low Effort)
- Executes planned file modifications using file editing tools (`replace_file_content` / `write_to_file`).
- Confirms syntax and interface integrity.

### Checkpoint C: Pre-Verification Gate
- Verifies system readiness for parallel swarm review.

### Step 4: Verification Swarm (`review-swarm-v0`)
Spawn 6 parallel `flash_lite` reviewers to test the implementation across:
1. Correctness & State Logic
2. Security & Data Integrity
3. Performance & Memory
4. Architecture & Contracts
5. Edge Cases & Errors
6. Code Style & Lint Cleanliness

### Step 5: Orchestrator Decision
- Check for any remaining Blocker/Major issues.
- Check for high-value UX/playability improvements.

### Checkpoint D & Auto-Loop Logic
Maintain `iteration_count` (starting at 1):
- **IF** issues/improvements remain **AND** `iteration_count < 3`:
  - Increment `iteration_count += 1`.
  - Log: `"[Loop iteration_count/3] Auto-looping to resolve remaining issues..."`.
  - Loop back to **Step 2** without prompting user.
- **ELSE** (Clean pass OR `iteration_count == 3`):
  - Present **Final State Report** summarizing iteration history, diffs, and test status.
