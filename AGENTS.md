# AGENTS.md — GBH: England

Cross-agent bootloader. **Identity, hard rules, and where to go next.** Detail lives in `docs/`,
routed from [docs/README.md](docs/README.md) — read the one or two documents your task needs,
never the whole folder.

## The project

A Unity **mobile RPG**, working title **Exiled Alvaston** (`productName`), shown to the player as
**GBH: England** (`EKVibe.DisplayTitle`). Modern Britain, magic played straight, a GTA-like
consequence layer (wanted level, police, stealth, pickpocketing, vehicle theft) over a classic RPG
core.

**Isometric by design** — a 3D world drawn with billboarded 2D sprites and a fixed isometric
camera. It is **not** a 2D project, whatever any older brief says. Movement is on the X/Z plane
using `Rigidbody`/`Collider`. Never introduce `Physics2D`, `Rigidbody2D` or `Vector2` movement:
nothing throws, things simply pass through each other.

**Naming is deliberately inconsistent — do not "unify" it.** `Exiled Alvaston` is the product name
and C# root namespace; `GBH: England` is the display title; `Discover England` survives only as an
editor-tool name; `EK*` prefixes refer to *Exiled Kingdoms*, the inspiration game.

Unity 2022.3 · one gameplay scene, `Assets/c.unity` · no `.asmdef`, so `Assets/Editor/` is the only
thing keeping editor code out of builds · no Git LFS.

---

## Two agents work in this repo

| Agent | Job | Writes to |
|---|---|---|
| **Claude Code** | All code, Unity assets, scene and prefab work. Reads `CLAUDE.md`. | `Assets/`, `Tools/`, `docs/`, git |
| **Art agent** (Antigravity/Gemini) | Generates sprites and sheets. Reads `ART_PIPELINE.md`. | `art_incoming/` **only** |

### If you are the art agent

**You produce image files and their sidecar JSON into `art_incoming/`. Nothing else.**

Read [ART_PIPELINE.md](ART_PIPELINE.md) for the contract and
[docs/art/ART_QUEUE.md](docs/art/ART_QUEUE.md) for what is actually wanted — **check the queue
before drawing anything, so you do not redraw something that already exists.**

Hard rules:

- **Never write anything inside `Assets/`.** Unity is usually open; it imports partial writes and
  generates `.meta` files that then conflict. Everything you make goes in `art_incoming/`, and a
  Unity-side importer moves it in deliberately.
- **Never create or edit a `.meta` file.** Unity owns those. A hand-written `.meta` can break the
  GUID binding that holds the whole project together.
- **Never edit `.cs`, `.unity`, `.prefab`, `.asset`, `.controller` or `.anim`.**
- **Never run git.** Do not commit, stage, branch or push.
- **Never run Unity or any editor tool.**
- **Do not leave intermediates behind.** No `.psd`, no upscaler outputs, no "v2_final" duplicates.
  There is no Git LFS and history already carries hundreds of MB of art blobs — every file
  committed is permanent weight. One PNG per asset, plus its `.json`.

**You produce 2D only, and cannot supply 3D.** London's buildings arrived as imported 3D models by
a separate route; that does not open a 3D lane for you. Do not produce a model, a substitute PNG or
a sidecar for a 3D request — a placeholder there is worse than nothing, because it would be
imported as a billboard sprite and crushed to 48 px per world unit. Building interiors are not an
art deliverable at all; they are Unity-side chunk prefabs.

If a **supported 2D** request is ambiguous, write your question into the asset's `.json` as a
`"question"` field and produce your best attempt anyway. Do not guess at project structure.
**Unsupported asset classes are the exception: ask and stop.**

### If you are Claude Code

[CLAUDE.md](CLAUDE.md) is your bootloader. This file only tells you where the art handoff lives:
the art agent drops PNG+JSON pairs into `art_incoming/` (gitignored staging), and
`Tools → Art → Import Generated Art` keys out the magenta backdrop, trims, reduces to 48 px
per world unit, slices sheets, builds clips and animator controllers, and archives clean pairs to
`art_incoming/processed/`. See [docs/reference/ART_IMPORTER.md](docs/reference/ART_IMPORTER.md).

---

## Hard rules for anyone touching code or assets

These are repeated here on purpose. A reference that was never opened cannot prevent a mistake.

- **Save keys.** Changing the *value* of `MapChunkData.ChunkName` or `ItemData.ItemID` silently
  orphans existing saves — nothing throws, nothing logs.
- **Serialized fields are matched by name; enums by integer index.** Renaming a public field drops
  its value everywhere without `[FormerlySerializedAs]`. **Always append to an enum.**
- **Commit a script's `.meta` with the script.** Its GUID is what binds prefabs and the scene to
  the class. This has gone wrong twice and fails silently on a fresh clone.
- **Never rebuild an existing prefab by deleting and re-saving it** — that mints a fresh GUID and
  orphans every placed instance. Edit in place with `PrefabUtility.LoadPrefabContents`.
- **Seven runtime paths instantiate a chunk; only two do the full lifecycle.** Change transition
  behaviour and you must touch all seven.
- **Never `SetActive(false)` a chunk root or a vehicle root.** The first permanently blinds every
  `EnemyAI` and leaks a NavMesh; the second makes a vehicle cancel its own boost on mount.
- **Quest and dialogue prose is the owner's own work.** Build the machinery, leave the words.

## Verification — be honest about it

**There is no C# compiler, no Unity and no test framework in the agent environment.**

```bash
python Tools/asset_reachability.py --check-dangling   # reference integrity; 17-GUID baseline
python Tools/art_status.py                            # what art exists and what is still owed
```

On Linux, `python3`. Everything else — does it compile, does the scene load, is anything pink, do
the mechanics behave — **needs a human in the Unity editor.** Say so plainly. Reference integrity
passing says nothing about whether the project builds, and a brace-balance scan is not a compile.

## Working agreement

**plan → implement → review → merge**, via the three agents in `.claude/agents/` (`architect`,
`implementer`, `reviewer`). Skip the ceremony for genuinely small, low-risk changes; use it for
anything touching saves, serialization, the chunk world, prefabs or the scene.

Small single-concern commits. Branch off `main`; do not commit or push unless asked.
