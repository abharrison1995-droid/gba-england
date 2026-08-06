# World authoring — the palette, presets and NPCs

```
Last verified against: working tree, 2026-08-06
Verification scope:    code; tracked preset/prefab YAML (30 presets read). The villager path was
                       exercised end to end in the editor and reported working by the owner.
                       The six London enemy prefabs have NEVER been seen in play. The preset
                       count and the "no preset has Prefab assigned" claim are from grep over
                       tracked YAML; nothing here has been reopened in the editor.
```

## The World Palette

`Tools → GBH → World Palette` (`Editor/WorldPaletteWindow.cs`). Arm a preset, click in the Scene
view, Shift to keep stamping, Esc to disarm.

It sits directly at `Tools/GBH/World Palette`, uncategorised — the one deliberate exception to the
`Tools/GBH/<Category>/` rule, because it is the entry point rather than one tool among many.

| Piece | File | What it does |
|---|---|---|
| The thing to place | `Data/PlacementPreset` | Label, category, region, icon, and either a `Prefab` or the recipe fields. |
| How to build it | `Editor/PlacementBuilders` | Each old window's `Create…()` body, taking a position and a parent. |
| Where to build it | `Editor/WorldPaletteWindow` | Grid, arming, SceneView raycast, ghost, parenting. |
| A starting set | `Editor/StarterPresetGenerator` | `Tools → GBH → Content → Create Starter Presets`. Skips what exists; never overwrites. |

### Things that will catch you out

- **`PlacementCategory` and `PlacementPreset.Region` are serialized by index — append only.**
  The field is `Region`, its type is `CityRegion` (`Assorted = 0`, `London = 1`, `Birmingham = 2`),
  and the YAML key is `Region:`.
- **The NPC section is the only one split by region.** The split iterates the *enum*, not the
  presets, so **a region with nothing in it still shows its heading** — Birmingham is empty on
  purpose and the heading is the reminder that it is next. `Region` is read by nothing but this
  window: it never reaches `NpcFactory` and changes nothing about the NPC that gets built.
- **Vehicles are not GameObjects here.** They are authored onto `MapChunkData.VehicleSpawns`, so
  the palette shows a target-chunk field and a click appends a spawn entry.
- **Prefab Mode uses the stage's own physics scene** for the placement raycast. `Physics.Raycast`
  would hit the main scene's colliders, which are not even visible in the stage.
- **A placement of the palette's own is never the parent of the next one.** Placing selects what
  it made, and the parent is read from the selection, so a Shift-held run of five used to bury the
  fifth four levels deep. It reuses the parent that placement went into instead. Selecting
  anything else still re-targets.
- **A placement is a copy, not a link.** Editing a preset — or importing art that rewires it —
  changes what you place *next*. To update something already standing, delete it and stamp it
  again. There is deliberately no resync tool.
- **A preset with a `Prefab` assigned short-circuits the whole recipe.** `PlacementBuilders.Build`
  checks `preset.Prefab != null` *before* the category switch, so `Category` is only a palette
  heading for those. Such a preset is placed with `PrefabUtility.InstantiatePrefab`, so the prefab
  link and any persisted UnityEvents survive the stamp. The worked example used to be
  `Preset_NoseyParker` — `Prop`, pointing at a hand-built prefab — which has been deleted along
  with the rest of the snitch mechanic (see
  [CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md)). There is no longer a preset in the
  project with `Prefab` assigned, so this path is currently unexercised.

The five `Place/…` windows still exist and still work. They have not been removed because none has
been checked for anything the palette cannot yet do.

---

## Adding an NPC

Two clicks in Unity and no code:

1. Spec the subject in `ART_PIPELINE.md` and have the art agent deliver
   `sheet_char_<subject>_*.png` + JSON to `art_incoming/`.
2. Create a `PlacementPreset`: `Label`, `Category: NPC`, `Region`, `ArtSubject`, `AmbientLine` or
   a `Conversation`, `Roams` if it should wander, `Pickpocketable` if they should be robbable
   instead of talkable.
3. `Tools → GBH → Art → Import Generated Art`. Sheets slice, clips build, a controller builds, and
   **the preset wires itself** — controller, resting sprite, palette icon, height.
4. `Tools → GBH → World Palette`: arm it, click it into a chunk prefab.

| Piece | File | What it owns |
|---|---|---|
| What an NPC *is* | `Data/PlacementPreset` | Art subject, height, dialogue, temperament, quest key, robbable. |
| Building one | `World/NpcFactory` | The recipe. **Runtime**, so the game can call it too. |
| Editor extras | `Editor/PlacementBuilders` | Undo, and the authoring capsule. Nothing else. |
| Wiring art to presets | `Editor/ArtImportTool` | `AutoAssign`, plus a re-runnable menu item. |
| Wandering | `AI/NPCWander` | Stroll, dwell, face, drive `Speed`. |
| Ambient dialogue | `Editor/PresetDialogueTools` | Generates `DialogueData` from a one-liner. |
| Runtime lookup | `Data/PlacementPresetLibrary` | The few presets code resolves by name. |

### Things that will catch you out

- **`NpcFactory` is runtime and must stay that way.** `Assets/Editor/` is stripped from builds, so
  a recipe living there is unreachable from anything spawning an NPC while the game runs — which
  is exactly how `MagicTutorial`'s characters ended up composed by hand, sharing one sprite.
  Nothing in `NpcFactory` may touch `UnityEditor`.
- **Dialogue is generated at authoring time, never at build time.** `AssetDatabase.CreateAsset`
  does not exist at runtime. `NpcFactory` only ever *reads* `preset.Conversation`.
- **`NpcHeight` of 0 means inherit `EKVibe.CharacterHeight`, currently 1.55.** Of the 30 presets,
  12 are 0, 13 are an explicit 1.55, and one — the child — is 1.3. The squirrel is 0, so until his
  sheets land he builds at 1.55 and reads as a man in a squirrel suit; his intended `worldHeight`
  is 0.45 and the importer will write it.
- **The importer always wins on controller and sprite, never on height.** Those two are derived
  from the art, so a fresh import replaces placeholder wiring with no manual step; height is
  tunable, so a hand-set value survives.
- **`Wire Presets From Imported Art`** (`Tools/GBH/Content/`) exists because an import only knows
  the batch in front of it, and a clean batch is archived out of staging immediately. Art imported
  months ago, or a preset written after its subject arrived, is only reachable this way.
- **`NPCWander` is deliberately NavMesh-free.** `EKNavMeshBaker` bakes one mesh from whichever
  chunk is loaded, and all six instantiate at the same origin. `RuntimeNavMeshBaker` exists and
  would fix it at the cost of a runtime bake per chunk crossing on a mobile-first game. `NPCWander`
  probes ahead with a `SphereCast` and gives up on the stroll instead.
- **`NPCWander` calls `SetFacing` every step.** Without it half of every wander is walked
  backwards, which reads as a rendering bug.
- **A roamer with no walk sheet slides.** Three presets currently do:
  `Preset_OfficerMurtaugh` (has the sheet; his controller ignores it),
  `Preset_RoamingPharmacist` (no sheet) and `Preset_AngrySquirrel` (no art at all).
  `python Tools/art_status.py` finds the last two.
- **Tutorial presets must not carry a `Conversation`.** Daniel Pauls and the geezer run dialogue
  off quest state and own their own `Interactable`; a preset conversation would answer the same
  button press. `MagicTutorial.OwnInteraction` warns if it finds one.
- **`PlacementPresetLibrary` lives in `Resources/`; the presets do not.** Everything reachable from
  `Resources/` ships in the build, and the chest preset alone would drag in a 45 MB prop pack.
  Entries are keyed by an authored string, so renaming a preset asset is safe.
- ⚠️ **`UnityEvent.AddListener` does not survive being saved into a prefab.** It creates a
  *non-persistent* listener; only calls written through `UnityEditor.Events.UnityEventTools` are
  serialized. An authoring tool that wires `OnInteract` with `AddListener` looks correct in the
  Scene view and produces a prefab with the component present and nothing connected.
  This is why `PickpocketInteractable` **subscribes itself in `Awake`**. That `Awake` also walks
  `OnInteract.GetPersistentEventCount()` looking for a persistent call already pointing at itself,
  which would otherwise rob the player twice per press. Nothing on disk carries such a call any
  more — `NoseyParker.prefab` was the only one and has been deleted — so that scan is now purely
  defensive, kept for any future tool that writes one through `UnityEventTools`.
- **A preset is either a talker or a mark, never both.** `Pickpocketable` plus a `Conversation` is
  two listeners answering one button press. `NpcFactory.ApplyPickpocket` warns and **dialogue
  wins**, because the failure that leaves is a civilian you cannot rob rather than a quest giver
  who will not talk. A mark's prompt becomes "Pickpocket <name>", which is the player's only cue
  to crouch.
- **`EnemyAI.Animator` is a public field nothing assigns unless asked.** An animated enemy's sheets
  will import, build a controller, and never play a frame. `MagicTutorial` sets it from
  `WorldActorVisual.SpriteAnimator` when the geezer turns hostile; anything else spawning an
  animated enemy in code needs the same line.

## Enemies need a hand-built prefab

There is no path that turns a generated sprite into an enemy automatically —
`PlacementBuilders.BuildEnemy` only *instantiates* an `EnemyPrefab`. Each hostile subject needs a
prefab (`WorldActorVisual` → `ActorSprite` = idle frame 0, Animator on `ActorVisual/SwingRoot`
wired to `<subject>_Controller`, `EnemyAI.Animator` set, `Health`, Rigidbody/Collider), then an
Enemy-category preset pointing at it.

Six exist — Neek, OG, Roadman, Spicehead, Tainted, Tortured Neek — built by
`Tools > GBH > Content > Build Enemies From Generated Art`. **None has been seen in play.**

Build prefabs **in place** (`LoadPrefabContents` → `SaveAsPrefabAsset`), never delete-and-recreate.

⚠️ **Death sheets shrink in figure height as the body goes prone** (Neek's death: fill 81% → 17%).
`WorldActorVisual.FitScaleToHeight` refits per displayed frame against the sprite's bounds, so
verify in-editor that a prone corpse frame does not scale *up* to the target world height and
balloon. Death is height-exempt in the art precheck, which hints the runtime handles it, but it is
untested for these subjects.

## The London cast

`Assets/Data/Presets/` holds 30 presets. The London cast is `Region: London`: Mayor Swalls, the
Quidland and F.U. Sports clerks, Commissioner Spencer, Officer Riggs, Officer Murtaugh, Ralph and
Sanjeet, plus Councillor Mosley and Daniel Pauls. The villagers stay `Assorted`, since they are
placed everywhere.

Eleven NPCs stand in `Home_London_Prefab`. **Commissioner Spencer is the one cast member still
unplaced.**

- **`Preset_FUSportsClerk.asset` does not match `Sanitise("F.U. Sports Clerk")`.** Nothing resolves
  these by path, so it is harmless — but `StarterPresetGenerator.BackfillNpcPresets` and
  `EnsureLibraryEntry` *do* look presets up as `Preset_{Sanitise(Label)}.asset`, so anything added
  to the generator later must either match or be found another way.
- **Neither clerk's name is settled**, and neither is Swalls' first name.
- **These presets were hand-written**, so they are not in `StarterPresetGenerator`'s `StarterNpcs`
  list. Deleting one and re-running Create Starter Presets will not bring it back.

### Three things these presets imply and do not build

- **No vendor system.** Quidland sells weapons and F.U. Sports sells armour, and both clerks are
  currently just people who say a line. No shop UI, no buying, no selling. The player does now
  carry money (`PlayerSession.Pounds`, spendable via `SpendPounds`) — there is simply nowhere to
  spend it.
- **No bounty pay-off for Riggs.** The intent is that he hands out missions and clears your wanted
  level on completion. `WantedManager.ClearWanted()` exists and `QuestReward.ClearsWantedLevel`
  calls it, but nothing is authored.
- **No quest gate on Mayor Swalls.** He carries `QuestKey: mayor_swalls` so quest code can find the
  placed object, but nothing hides him. There is no visibility-gating mechanism on presets at all;
  `RequireTutorialComplete` exists only on the Portal recipe.
