---
name: review-swarm-v2
description: >-
  Spawns a hybrid deep-reasoning code review swarm (4× Gemini 3.7 Flash on High reasoning + 2× Flash-Lite) to thoroughly evaluate complex code, diffs, or architecture without editing files. Consolidates findings into a severity-ranked report.
---

# Review Swarm v2 — Hybrid Deep-Reasoning Code Review

A deep-reasoning parallel review workflow combining 4 high-reasoning Gemini 3.7 Flash reviewers for architectural and logical deep-dives with 2 fast Flash-Lite reviewers for syntax and interfaces. Review only — no file modifications.

---

## Workflow

```
                        ┌─────────────────────────────────┐
                        │   Initiate Review Request       │
                        └────────────────┬────────────────┘
                                         │
        ┌────────────────────────┬───────┴────────┬────────────────────────┐
        ▼                        ▼                ▼                        ▼
 [Flash - High Reasoning] [Flash - High Reasoning] [Flash - High Reasoning] [Flash - High Reasoning]
 Architecture & Design    Deep Logic & Math    Security & State     Edge & Failure Modes
        │                        │                │                        │
        └────────────────────────┼────────────────┴────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
          [Flash-Lite]                    [Flash-Lite]
       Syntax, Style & Lints           APIs, Docs & Fast Checks
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │ Consolidate & Rank by Severity│
                 └───────────────────────────────┘
```

---

## Step 1: Spawn Parallel Review Swarm

Invoke 6 subagents concurrently using `invoke_subagent`:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Deep Architecture & Design Reviewer",
      "Model": "flash",
      "Prompt": "Perform a deep-reasoning architectural code review. Analyze decoupling, encapsulation, modularity, adherence to system invariants, and structural sustainability. Cite exact lines and risks."
    },
    {
      "TypeName": "research",
      "Role": "Deep Logic & State Machine Reviewer",
      "Model": "flash",
      "Prompt": "Perform a deep-reasoning logic and algorithmic review. Hunt for race conditions, subtle state corruption, off-by-one errors, math/physics discrepancies, and lifecycle leaks. Cite exact lines and risks."
    },
    {
      "TypeName": "research",
      "Role": "Deep Security & Integrity Reviewer",
      "Model": "flash",
      "Prompt": "Perform a deep-reasoning security and data-integrity review. Inspect serialization compatibility, input validation, permission leaks, and data consistency across boundaries. Cite exact lines and risks."
    },
    {
      "TypeName": "research",
      "Role": "Deep Edge Cases & Failure Modes Reviewer",
      "Model": "flash",
      "Prompt": "Perform a deep-reasoning edge case review. Hunt for unhandled exceptions, null dereferences, resource exhaustion, timeout handling, and recovery paths. Cite exact lines and risks."
    },
    {
      "TypeName": "research",
      "Role": "Syntax & Lint Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast sweep for syntax cleanliness, naming conventions, dead code, redundant allocations, and formatting inconsistencies."
    },
    {
      "TypeName": "research",
      "Role": "API & Interface Reviewer",
      "Model": "flash_lite",
      "Prompt": "Perform a fast sweep of public API signatures, documentation accuracy, comment freshness, and public interface ergonomics."
    }
  ]
}
```

---

## Step 2: Consolidate & Rank Findings

Consolidate findings across all 6 reviewers:
1. **Deduplicate**: Merge overlapping points.
2. **Rank by Severity**:
   - 🔴 **BLOCKER / CRITICAL**: Crashing bugs, state corruption, security leaks, broken save/serialization.
   - 🟠 **MAJOR**: High-risk logic flaws, race conditions, architecture violations.
   - 🟡 **MINOR**: Suboptimal code patterns, minor performance inefficiencies, outdated comments.
   - 🔵 **NIT**: Stylistic tweaks, naming conventions.

---

## Step 3: Present Consolidated Report

Format output as follows:

```markdown
# 🔍 Hybrid Deep-Reasoning Review Report (review-swarm-v2)

## Executive Summary
- **Swarm Composition**: 4× Gemini 3.7 Flash (High Reasoning) + 2× Flash-Lite (Parallel)
- **Status**: [PASSED / ACTION REQUIRED / BLOCKED]
- **Issues Found**: X Blocker, Y Major, Z Minor, W Nit

---

## 🔴 Blocker / Critical Issues
- **[File & Line]**: Deep architectural or crashing flaw details.

## 🟠 Major Issues
- **[File & Line]**: High-risk logic or data-integrity issue.

## 🟡 Minor Issues
- **[File & Line]**: Code quality improvement recommendation.

## 🔵 Nits
- **[File & Line]**: Stylistic suggestion.

---
## Recommended Action Plan
1. Step 1...
2. Step 2...
```
