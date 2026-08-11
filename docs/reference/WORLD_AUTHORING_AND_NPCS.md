# World authoring — the palette, presets and NPCs

```
Last verified against: working tree, 2026-08-08
Verification scope:    code; tracked preset/prefab YAML (32 presets read). The villager path was
                       exercised end to end in the editor and reported working by the owner.
                       The six London enemy prefabs have NEVER been seen in play, and a GUID scan
                       of the chunk prefabs and c.unity says none of them is placed anywhere. The
                       preset count, the "no preset has Prefab assigned" claim and the enemy-level
                       path below are from reading code and tracked YAML; nothing here has been
                       reopened in the editor, and no enemy has been placed with a level.
                       The Portal Placement section landed 2026-08-09 describing a rewritten tool
                       that has NEVER been compiled, opened or run, and no linked pair exists.
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
  [CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md)). No preset **currently on disk** has
  `Prefab` assigned, so this path is unexercised until someone runs
  `Tools → GBH → Content → Build Container Prefabs`, whose `Preset_Container_*` presets are
  `Prop` pointing at a container prefab.

The five `Place/…` windows still exist and still work. They have not been removed because none has
been checked for anything the palette cannot yet do.

## Portal Placement — linked location pairs

`Tools → GBH → Place → Portal Placement` (`Editor/PortalPlacementTool.cs`) no longer drops a single
portal. It authors **both ends of a door at once**: the entrance in the exterior chunk, the exit in
the interior chunk, and the arrival marker each one lands at.

A single portal is half a door. Authored one end at a time, its partner has to be remembered, its
return position typed as a raw coordinate, and its target chunk registered somewhere the save
system can find it — and every one of those fails quietly, either stranding the player inside a
building or producing a save that will not load after a restart.

### What it writes

For link id `police_station_front`, into each chunk **prefab**:

```
Exterior prefab                              Interior prefab
  LocationLinks/                               LocationLinks/
    police_station_front/                        police_station_front/
      Portal_Enter                                 Portal_Exit
      PlayerSpawn_police_station_front_outside     PlayerSpawn_police_station_front_inside
```

`Portal_Enter` targets the interior chunk and the `…_inside` marker; `Portal_Exit` targets the
exterior chunk and the `…_outside` marker. Each portal gets a `DungeonPortal` and an `Interactable`
(`Reusable = true`, the authored range). Both chunks are added to `MapChunkRegistry`.

**No door visual is added.** Most entrances already have geometry; the interaction point is
invisible and is drawn by `DungeonPortal`'s own amber gizmo, which also draws the interact radius
and an arrow for the way through.

### The rules it works under

- **Capture poses in Prefab Mode, create outside it.** Poses are stored relative to the chunk
  prefab root, which is the space the runtime uses — chunks are always instantiated at the origin.
  Creating is **disabled while any prefab stage is open**, because closed prefabs are edited
  through `LoadPrefabContents` and doing that to a prefab simultaneously open in a stage fights the
  stage's copy.
- **Re-running with the same link id updates.** Objects are found by name under
  `LocationLinks/<linkId>/`, so a second run edits what the first made. Nothing is deleted and
  re-created, so no `.meta` and no GUID changes. *Overwrite Poses On Update* can be turned off to
  change only prompts, targets or range and keep a door that has since been nudged by hand.
- **It refuses rather than guesses**: an empty or non-plain link id, a missing `ChunkPrefab`, an
  empty `ChunkName`, a `ChunkName` already used by another asset, the same chunk on both sides, or
  a `ChunkPrefab` pointing at a child instead of the prefab root.
- ⚠️ **`OnInteract` is deliberately not wired.** `DungeonPortal.Awake` adds its own listener at
  runtime; a persistent editor-time call alongside it would mean one press, two journeys.
- **A half-written pair is reported loudly.** If the exterior write succeeds and the interior write
  fails, the log says so explicitly — that state is a building you can enter and not leave.

### Create Empty Interior Bundle

Creates an empty `MapChunkData` and an empty chunk prefab for a new interior, and registers them.
It never overwrites an existing asset and does not decorate the interior. ⚠️ **The prefab it makes
has no floor** — give it geometry with a collider before wiring a door to it, or the player falls
through and `ChunkManager`'s void catcher returns them to the spawn point to fall again.

### Validate All Location Links

`Editor/LocationLinkValidator.cs`. Read-only — it reports and **never repairs**, because several of
the things it looks at are save keys and a tool that helpfully rewrote one would orphan saves in
silence. It checks empty and duplicate chunk names, missing prefabs, duplicate marker ids within a
prefab, broken `TargetSpawnPointId`s, portals targeting their own chunk, non-reciprocal pairs, link
ids used by more or fewer than two prefabs, arrival markers under 3.5 m from the door back out, and
chunks absent from the registry.

For chunks it infers to be **interiors** — no N/S/E/W adjacency, but targeted by some portal — it
also flags `ChunkEdge` triggers (which can only ever say "There's nothing that way"), a total
absence of colliders (no floor), and `NavMeshAgent`s with no `RuntimeNavMeshBaker` (chunks are
instantiated at runtime, so a scene-baked NavMesh does not cover them).

### The palette's portal path

`PlacementPreset.PortalTargetSpawnPointId` is appended at the end of the class and copied into
`DungeonPortal.TargetSpawnPointId` by `PlacementBuilders.BuildPortal`. Every preset on disk carries
no key for it, so they all read empty and keep the raw `PortalSpawnPosition` behaviour they have
always had. It is only worth setting on a preset stamped into chunks that all carry that marker —
an unresolved id aborts travel rather than falling back.

### Enemy levels

An enemy's level comes from **two** places, and the palette wins:

- `PlacementPreset.EnemyLevel` — the preset's default, appended at the end of the class. All 32
  presets on disk carry no key for it, so they read **0**.
- The palette's own **Level** field, drawn only while an `Enemy` preset is armed, held on the
  `EditorWindow` and stored in no asset. It is reset from the preset every time one is armed, so a
  level never carries over from the last enemy stamped. It exists because a preset is a single
  file: a level living only on it would mean one preset per band, or editing the asset between
  placements.

**0 means no `EnemyLevel` component is attached at all** — not level 1. The two are the same
behaviourally, but a level-1 component would still make `EnemyNameplate` read it (flipping every
badge from the prefab's authored 3 to 1) and switch `KillXP` from `EKVibe.KillXPBase` to the scaled
figure. `PlacementBuilders` also requires an `EnemyAI` before attaching and warns by name when a
level is set without one, because `EnemyLevel`'s `[RequireComponent(typeof(Health))]` would
otherwise give a chest a `Health` and make it killable.

⚠️ **Ordering with `OverrideHealth` / `OverrideDamage`: the override is the level-1 baseline.** The
override is baked into the placed instance in the editor; `EnemyLevel.ApplyTo` multiplies it at
runtime from `Health.Awake`. So a preset with `OverrideHealth = 100` and a level of 5 places an
enemy whose Inspector reads **100** and which has **240 HP in play**. That is not a bug to fix —
scaling first and overriding second would make the override silently cancel the level, invisibly.

`Tools → GBH → Place → Enemy Placement` has the same **Level** field, on the same rules, so the two
placement paths agree.

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

⚠️ **None of them is placed anywhere.** A GUID scan of all six `.prefab.meta` GUIDs across
`Assets/Prefabs/Chunks/*.prefab` and `Assets/c.unity` returns zero hits: the only `EnemyAI` in the
scene is the PCSO actor. There is no authored enemy in the world, so nothing needed migrating when
levels arrived, and there is nothing standing that a level could be added to without stamping it.

Build prefabs **in place** (`LoadPrefabContents` → `SaveAsPrefabAsset`), never delete-and-recreate.

⚠️ **Death sheets shrink in figure height as the body goes prone** (Neek's death: fill 81% → 17%).
`WorldActorVisual.FitScaleToHeight` refits per displayed frame against the sprite's bounds, so
verify in-editor that a prone corpse frame does not scale *up* to the target world height and
balloon. Death is height-exempt in the art precheck, which hints the runtime handles it, but it is
untested for these subjects.

## The London cast

`Assets/Data/Presets/` holds 32 presets, six of which are `Category: Enemy`. The London cast is
`Region: London`: Mayor Swalls, the
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
