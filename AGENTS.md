# AGENTS.md

This is a **Unity 2D-sprite/3D-world mobile RPG**. Two agents work in this repo with different jobs.

| Agent | Job | Writes to |
|---|---|---|
| **Claude Code** | All code, Unity assets, scene and prefab work. Reads `CLAUDE.md`. | `Assets/`, `Tools/`, git |
| **Art agent** (Antigravity/Gemini) | Generates sprites, sheets and textures. Reads `ART_PIPELINE.md`. | `art_incoming/` **only** |

## If you are the art agent, read this and then `ART_PIPELINE.md`

**You produce image files and their sidecar JSON into `art_incoming/`. Nothing else.**

Hard rules:

- **Never write anything inside `Assets/`.** Unity is usually open; it imports partial writes and
  generates `.meta` files that then conflict. Everything you make goes in `art_incoming/`, and a
  Unity-side importer moves it in deliberately.
- **Never create or edit a `.meta` file.** Unity owns those. A hand-written `.meta` can break the
  GUID binding that holds the whole project together.
- **Never edit `.cs`, `.unity`, `.prefab`, `.asset`, `.controller` or `.anim`.**
- **Never run git.** Do not commit, stage, branch or push. Claude Code handles version control.
- **Never run Unity or any editor tool.**
- **Do not leave intermediates behind.** No `.psd`, no upscaler outputs, no "v2_final" duplicates.
  This repo has **no Git LFS** and its history already carries hundreds of MB of art blobs — every
  file committed is permanent weight. One PNG per asset, plus its `.json`.

If a request is ambiguous, write your question into the asset's `.json` as a `"question"` field
and produce your best attempt anyway. Do not guess at project structure to resolve it.

## If you are Claude Code

`CLAUDE.md` is your file — this one only tells you where the art handoff lives. `ART_PIPELINE.md`
§"Importing" is your side of the contract.
