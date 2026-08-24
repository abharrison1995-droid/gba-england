---
name: review-swarm-v0
description: >-
  Ultra-budget parallel code review skill. Spawns 6 independent Flash-Lite reviewers simultaneously to assess code, diffs, or tasks with near-zero token cost. Consolidates findings into a severity-ranked report. Review only — no file modifications.
---

# Review Swarm v0 — 6× Parallel Flash-Lite Code Review

An ultra-budget, high-velocity parallel code review workflow utilizing 6 concurrent `flash_lite` subagents. Designed for low-overhead, continuous code inspections without depleting standard rate limits.

---

## Workflow

```
                        ┌─────────────────────────────────┐
                        │   Initiate Review Request       │
                        └────────────────┬────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
          [Reviewer 1]             [Reviewer 2]             [Reviewer 3]
       Correctness & Logic       Security & Data Flow    Performance & Memory
                 │                       │                       │
                 ▼                       ▼                       ▼
          [Reviewer 4]             [Reviewer 5]             [Reviewer 6]
       Architecture & API       Edge Cases & Nulls       Style & Lint Sweep
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │ Consolidate & Rank by Severity  │
                        └─────────────────────────────────┘
```

---

## Step 1: Spawn Parallel Flash-Lite Swarm

Invoke 6 subagents concurrently using `invoke_subagent` with `Model: "flash_lite"`:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Correctness & Logic Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast code review focused on correctness, logic bugs, off-by-one errors, state management, and algorithmic accuracy. Document findings with exact file paths and line numbers."
    },
    {
      "TypeName": "research",
      "Role": "Security & Data Integrity Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast code review focused on security vulnerabilities, data integrity, race conditions, unsanitized inputs, and serialization hazards. Document findings with exact file paths and line numbers."
    },
    {
      "TypeName": "research",
      "Role": "Performance & Memory Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast code review focused on runtime performance, CPU spikes, unnecessary allocations, memory leaks, and redundant operations. Document findings with exact file paths and line numbers."
    },
    {
      "TypeName": "research",
      "Role": "Architecture & Contracts Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast code review focused on architectural consistency, public API contracts, encapsulation, modularity, and adherence to project rules. Document findings with exact file paths and line numbers."
    },
    {
      "TypeName": "research",
      "Role": "Edge Cases & Error Handling Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast code review focused on edge cases, boundary conditions, unexpected nulls, unhandled exceptions, and failure recovery. Document findings with exact file paths and line numbers."
    },
    {
      "TypeName": "research",
      "Role": "Style & Lint Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast sweep for syntax cleanliness, naming conventions, dead code, formatting inconsistencies, and readability. Document findings with exact file paths and line numbers."
    }
  ]
}
```

---

## Step 2: Consolidate & Rank Findings

Once all subagents report back:
1. **Deduplicate**: Merge overlapping points.
2. **Rank by Severity**:
   - 🔴 **BLOCKER / CRITICAL**: Crashing bugs, silent corruption, security vulnerabilities, broken serialization/saves.
   - 🟠 **MAJOR**: Logic errors, performance bottlenecks, unhandled boundary cases.
   - 🟡 **MINOR**: Suboptimal code patterns, dead code, minor formatting issues.
   - 🔵 **NIT**: Cosmetic suggestions, naming tweaks.

---

## Step 3: Present Consolidated Report

Format output as follows:

```markdown
# 🔍 Ultra-Budget Swarm Review Report (review-swarm-v0)

## Executive Summary
- **Total Reviewers**: 6× Flash-Lite (Parallel)
- **Status**: [PASSED / ACTION REQUIRED / BLOCKED]
- **Issues Found**: X Blocker, Y Major, Z Minor, W Nit

---

## 🔴 Blocker / Critical Issues
- **[File & Line]**: Description of issue and why it breaks functionality.

## 🟠 Major Issues
- **[File & Line]**: Description of issue and operational risk.

## 🟡 Minor Issues
- **[File & Line]**: Improvement recommendation.

## 🔵 Nits
- **[File & Line]**: Stylistic note.

---
## Recommended Action Items
1. Fix item 1...
2. Fix item 2...
```
