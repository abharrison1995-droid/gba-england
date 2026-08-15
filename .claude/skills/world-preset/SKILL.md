---
name: world-preset
description: Talk a PlacementPreset through — NPC, enemy, chest, prop, portal, vehicle or spawn point — and spec its fields, then guide creating it and stamping it into a chunk via the World Palette. Proposes structure and wiring; leaves any spoken/ambient prose to the owner. Use when the user wants to author or place a world object/NPC for GBH: England.
---

# World preset author

You help the owner design **one `PlacementPreset`** and get it into the world. Presets are
Inspector-authored ScriptableObjects placed through the **World Palette** — there is no text
importer. So: interview, spec the fields, then guide creation, wiring and placement.

## Read first

- `Assets/Scripts/Data/PlacementPreset.cs` — the authoritative field list per category. Trust it.
- `docs/reference/WORLD_AUTHORING_AND_NPCS.md` — the palette/preset/NPC authoring flow.
- An existing preset under `Assets/Data/Presets/` as a shape to copy.

## The prose line

`AmbientLine` — a throwaway spoken line for an NPC not worth a full conversation — is **prose**.
Leave it blank; the owner writes it. Note the repo rule: `Tools → Content → Create Starter Presets`
generates a `DialogueData` from any preset with a non-blank `AmbientLine`, so **a blank AmbientLine
stays blank**. `NpcName`/`ChestName` and the like are labels the owner supplies, not lines you write.

## Pick the category first

A preset is one of: `Prop` (or any `Prefab` set — then the recipe fields are ignored), `NPC`,
`Enemy`, `Chest`, `Portal`, `Vehicle`, `SpawnPoint`. Ask which, then only spec that category's block:

- **NPC** — `NpcName`, `NpcSprite`/`NpcController` (or `ArtSubject` for the art pipeline),
  `NpcHeight` (0 inherits), `Roams`/`RoamRadius`, `Speaker`, `Conversation`, and `AmbientLine`
  (owner). A `QuestKey` if quest code must find it.
- **Enemy** — `EnemyPrefab`, optional `OverrideHealth`/`OverrideDamage`, `Loot` (empty = no
  LootOnDeath at all), and the palette's per-stamp Level (a Level of 0 attaches no `EnemyLevel`
  component — deliberate).
- **Chest** — `ChestName`, optional `ChestVisualPrefab`, `ChestLoot` (separate from enemy `Loot`).
- **Portal** — `TargetChunk`, `PortalSpawnPosition`/`SpawnPointId`, `PortalPrompt`,
  `RequireTutorialComplete`, door visual options. (Linked pairs: use `Tools → Place → Portal
  Placement`, not by hand.)
- **Vehicle** — `Vehicle`; note vehicles are authored onto a chunk's `MapChunkData`, not the scene.
- **SpawnPoint** — `SpawnPointId` (blank = a chunk's default arrival point).

`Label`/`Category`/`Icon` are the palette-facing fields for every preset.

## Produce

Spec the fields as a clear list, then guide:

- Create the preset (Project → Create under `ExiledAlvaston/Data/…`, or duplicate a similar one),
  save under `Assets/Data/Presets/Preset_<Label>.asset`, fill the fields you specced.
- Wire a conversation if wanted: right-click the preset → **Create Dialogue**
  (`CONTEXT/PlacementPreset/Create Dialogue`), or point its `Conversation` at a `.quest`-generated
  `DialogueData`. Leave `AmbientLine` for the owner.
- Set `QuestKey` if a quest's `TALKTO`/`KILL`/`REACH` must find this exact object — placing the
  preset stamps a `QuestActor` with that key.

## Place it

Guide the owner: `Tools → World Palette`, pick the preset, stamp it into the chunk (in Prefab Mode
on the chunk prefab, edit in place). For enemies, set the per-stamp Level there.

## Hand off (you can't run Unity)

1. Fill any `AmbientLine`/conversation prose.
2. Create + fill the preset; wire its `Conversation`/`QuestKey` as specced.
3. Stamp it into the chunk via the World Palette.
4. Play and confirm it appears, talks/fights/opens as intended, and any `QuestKey` is found by its
   quest.

## Never

- Write an `AmbientLine` or any spoken line — that is the owner's.
- Rebuild an existing prefab by delete-and-resave (mints a fresh GUID; edit in place).
- Hand-edit portal links — use the Portal Placement tool.
- Claim it "works" — you can only confirm the preset is well-formed, not that it runs.
