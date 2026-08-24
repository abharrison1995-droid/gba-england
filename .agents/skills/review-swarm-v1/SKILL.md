---
name: review-swarm-v1
description: >-
  Spawns 6 independent parallel Gemini 3.7 Flash reviewers to simultaneously evaluate code, diffs, PRs, or architecture without editing files. Consolidates all findings into a unified severity-ranked report. Review only.
---

# Review Swarm v1 — 6× Parallel Gemini 3.7 Flash Code Review

A high-capability, fast parallel code review workflow utilizing 6 concurrent Gemini 3.7 Flash subagents across 6 distinct inspection dimensions. Review only — no file modifications.

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
       Architecture & API       Edge Cases & Nulls       Style & Cleanliness
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │ Consolidate & Rank by Severity  │
                        └─────────────────────────────────┘
```

---

## Step 1: Spawn Parallel Review Swarm

Invoke 6 subagents concurrently using `invoke_subagent` with `Model: "flash"`:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Correctness & Logic Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on correctness, logic bugs, off-by-one errors, state management, and algorithmic accuracy. Document findings with exact file paths, line numbers, and impact."
    },
    {
      "TypeName": "research",
      "Role": "Security & Data Integrity Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on security vulnerabilities, data integrity, race conditions, unsanitized inputs, and serialization hazards. Document findings with exact file paths, line numbers, and impact."
    },
    {
      "TypeName": "research",
      "Role": "Performance & Memory Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on runtime performance, CPU spikes, garbage collection allocations, memory leaks, and redundant operations. Document findings with exact file paths, line numbers, and impact."
    },
    {
      "TypeName": "research",
      "Role": "Architecture & Contracts Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on architectural consistency, public API contracts, encapsulation, modularity, and adherence to project rules. Document findings with exact file paths, line numbers, and impact."
    },
    {
      "TypeName": "research",
      "Role": "Edge Cases & Error Handling Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on edge cases, boundary conditions, unexpected nulls, unhandled exceptions, and failure recovery. Document findings with exact file paths, line numbers, and impact."
    },
    {
      "TypeName": "research",
      "Role": "Maintainability & Clean Code Reviewer",
      "Model": "flash",
      "Prompt": "Perform an independent code review focused on code clarity, maintainability, naming conventions, dead code, and readability. Document findings with exact file paths, line numbers, and impact."
    }
  ]
}
```

---

## Step 2: Consolidate & Rank Findings

Once all subagents report back:
1. **Deduplicate**: Merge findings identified across reviewers.
2. **Rank by Severity**:
   - 🔴 **BLOCKER / CRITICAL**: Crashing bugs, silent corruption, security vulnerabilities, broken serialization/saves.
   - 🟠 **MAJOR**: Logic errors, performance bottlenecks, unhandled boundary cases, broken contracts.
   - 🟡 **MINOR**: Suboptimal implementations, code duplication, missing docstrings, minor styling inconsistencies.
   - 🔵 **NIT**: Cosmetic suggestions, naming preferences.

---

## Step 3: Present Consolidated Report

Format output as follows:

```markdown
# 🔍 Swarm Review Report (review-swarm-v1)

## Executive Summary
- **Total Reviewers**: 6× Gemini 3.7 Flash (Parallel)
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
