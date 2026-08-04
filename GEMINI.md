# GEMINI.md

**Read [`AGENTS.md`](AGENTS.md), then [`ART_PIPELINE.md`](ART_PIPELINE.md), then
[`docs/art/ART_QUEUE.md`](docs/art/ART_QUEUE.md).**

`ART_PIPELINE.md` is *how* to draw and deliver. `ART_QUEUE.md` is *what* is wanted — and it is the
only file that records what already exists. **Check it before drawing anything**, or you will
redraw something that is already in the game.

This file exists only so the context loads whichever filename your tool looks for. It is a pointer,
not a second copy — there is one set of rules and it lives in those two files. If you find guidance
here that contradicts them, they win.

The short version, so you cannot miss it:

- You generate **art only**. PNG plus a sidecar JSON, into `art_incoming/`.
- **Never write inside `Assets/`.** Unity is often open and will import half-written files.
- **Never create or edit a `.meta` file**, never touch `.cs`/`.unity`/`.prefab`/`.asset`.
- **Never run git.** Claude Code owns version control.
- Draw characters in three-quarter view **facing camera-right** — the engine flips for left.
- An adult is `worldHeight` **1.55** (this changed from 1.35 — do not copy an older sheet's JSON).
- **2D only.** You cannot deliver 3D, and must not substitute a PNG for a 3D request.
- **Trim single sprites tight to the artwork.** Sizing is scaled from full image bounds, so
  transparent margin silently shrinks the subject.
