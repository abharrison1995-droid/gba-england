# GEMINI.md

**Read [`AGENTS.md`](AGENTS.md) first.** It defines two roles this tool can run in — art generation
or full implementation — chosen per task, not fixed to this tool. This file adds the
Antigravity-specific detail for each.

---

## If you are implementing

Read [`CLAUDE.md`](CLAUDE.md) and follow it exactly — same rules as Claude Code, no separate
rulebook for this mode.

**Internal agent structure, Antigravity-only.** This section applies only inside this IDE; Claude
Code does not read this file and does not follow it. Set up as three model switches in Antigravity's
own agent configuration, mirroring the plan → implement → review shape in `CLAUDE.md` §6:

1. **Claude Opus 4.6 — planner/architect.** Scopes the task, produces the plan and a mapping table
   for anything touching saves, serialized fields, prefabs or the scene, flags structural risk.
   Never edits code.
2. **Gemini Flash 3.7, High reasoning — implementer.** Works strictly from the plan. Small,
   single-concern commits. No scope improvisation.
3. **Claude Opus 4.6 — reviewer.** Reviews the diff against the plan, hunting silent failure modes —
   orphaned references, broken GUIDs, save incompatibility — not style.

Which model runs which step is set in Antigravity's own agent configuration; nothing in this repo
can select it for you. Skip the ceremony for genuinely small, low-risk changes, same latitude
`CLAUDE.md` §6 gives Claude Code's own three agents.

## If you are generating art

Read [`ART_PIPELINE.md`](ART_PIPELINE.md), then [`docs/art/ART_QUEUE.md`](docs/art/ART_QUEUE.md).

`ART_PIPELINE.md` is *how* to draw and deliver. `ART_QUEUE.md` is *what* is wanted — and it is the
only file that records what already exists. **Check it before drawing anything**, or you will
redraw something that is already in the game.

This file exists only so the context loads whichever filename your tool looks for. It is a pointer,
not a second copy — there is one set of rules and it lives in those two files. If you find guidance
here that contradicts them, they win.

The short version, so you cannot miss it:

- You generate **art only** in this mode. PNG plus a sidecar JSON, into `art_incoming/`.
- **Never write inside `Assets/`.** Unity is often open and will import half-written files.
- **Never create or edit a `.meta` file**, never touch `.cs`/`.unity`/`.prefab`/`.asset`.
- **Never run git.** Claude Code owns version control.
- Draw characters in three-quarter view **facing camera-right** — the engine flips for left.
- An adult is `worldHeight` **1.55** (this changed from 1.35 — do not copy an older sheet's JSON).
- **2D only.** You cannot deliver 3D, and must not substitute a PNG for a 3D request.
- **Trim single sprites tight to the artwork.** Sizing is scaled from full image bounds, so
  transparent margin silently shrinks the subject.
