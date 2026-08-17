# CLAUDE.md — GBH: England

**This file is a bootloader, not a manual.** It holds project identity, the rules that must never
be missed, and a routing table. Detail lives in `docs/`, loaded on demand.

**Read [docs/README.md](docs/README.md) to find what your task needs. Never read all of `docs/`.**

---

## 1. What this project is

A Unity **mobile RPG** called **GBH: England** (`EKVibe.DisplayTitle`).

Set in a hostile modern Britain, with magic played straight. A GTA-like consequence layer — wanted
level, police, stealth, pickpocketing, vehicle theft — sits on top of a classic RPG core.

**The name is unified.** The old working title `Exiled Alvaston` and the older `Discover England`
were swept out on 2026-08-16 — root C# namespace `GBHEngland`, `productName` **`GBH England`** (no
colon: it becomes a real folder inside `persistentDataPath`), `Create →` menus under
`GBH England/Data/…`, and the repo itself still `gba-england` because a colon is illegal in a path.
**Do not reintroduce the old names.** The one deliberate survivor is the `EK*` prefix (`EKVibe`,
`EKNavMeshBaker`) — it refers to *Exiled Kingdoms*, the inspiration game, and is a lineage marker
rather than a stale title.
→ [docs/plans/NAME_UNIFICATION_PLAN.md](docs/plans/NAME_UNIFICATION_PLAN.md)

### Presentation model — read this before touching movement or combat

**Isometric, by design.** A 3D world rendered with billboarded 2D sprites and a fixed isometric
camera — the Exiled Kingdoms presentation model. This is the intended target, not a legacy
artifact. **It is not a 2D project**, whatever any older brief says.

- 3D physics: `Rigidbody`, `Collider`, `Physics.OverlapSphere`
- Movement is on the **X/Z plane**; `Y` is up. Chunk edges are `pos.x` / `pos.z`.
- Fixed isometric camera (`IsometricCameraFollow`, pitch 30°, yaw -45°, ortho size 7)
- Sprites face camera via `SpriteBillboard`; actors composed by `WorldActorVisual`
- Input is screen-relative (`GetScreenRelativeMoveDirection`), not world-axis

⚠️ **Never introduce `Physics2D` / `Rigidbody2D` / `Vector2` movement.** It will not interact with
any existing collider — nothing will throw, things will simply pass through each other.

---

## 2. Layout and conventions

```
Assets/
  Scripts/          # runtime code, namespace GBHEngland.<Folder>
    AI/ Camera/ Combat/ Data/ Dialogue/ Flow/ Quests/ Systems/ UI/ Vibe/ World/
  Editor/           # editor-only tools (no asmdef — see below)
  Data/Chunks/      # 6 MapChunkData .asset files
  Data/Presets/     # 30 PlacementPreset assets
  Data/Dialogue/    # DialogueData assets
  Prefabs/          # Chunks/, ModernBritain/, Enemies/
  Resources/        # loaded by name at runtime — Items/, Quests/, PlacementPresetLibrary
  Art/ Sprites/ Animations/ 3DModels/ Materials/
  6twelve/          # third-party pack, not our code
  c.unity           # THE only gameplay scene
  c/                # NavMesh data for c.unity, auto-linked by scene name
Tools/              # python helpers (see §5)
docs/               # everything else — routed from docs/README.md
```

- **Namespaces mirror folders**: `GBHEngland.World`, `GBHEngland.Combat`. Keep it that way.
- **Public fields, PascalCase**, for anything Unity serializes (`CurrentKnives`, `ChunkPrefab`).
- **Private fields `_camelCase`** (`_isTransitioning`, `_hitThisSwing`).
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`. Access pattern
  is `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Scripts/Vibe/EKVibe.cs`) — colours, sizes, camera,
  `ChunkSize`, `CharacterHeight`. Prefer adding there over new magic numbers.
- **ScriptableObject menu path**: `GBH England/Data/...`
- **Editor menu path**: `Tools/<Category>/...` — `Place`, `Art`, `World`, `UI`, `Debug`,
  `Repair`, `Content`, plus **`Danger Zone`** for the five tools that overwrite or re-create assets. Each of
  those confirms first and names what it destroys. **Nothing destructive may go anywhere else.**
  `Tools/World Palette` is the one deliberate uncategorised exception.
- **Mobile-first**: hot paths avoid allocation deliberately (preallocated `Collider[] _hitResults`,
  parallel key lists to avoid dictionary-iteration garbage). Respect this in `Update()` paths.
- **`Assets/Editor/` is stripped from builds** and there are **no `.asmdef` files**, so it is the
  only thing keeping editor code out of the build. Editor-only code must live there; anything the
  running game needs must not.

---

## 3. Safety capsule — these are never safe to get wrong

Each item below is repeated deliberately from its canonical reference, because a reference that
was never loaded cannot stop a mistake.

### Save keys

Changing the **value** of any of these silently orphans existing saves — nothing throws, nothing
logs, the data is gone:

- **`MapChunkData.ChunkName`** — stored as a string, resolved via `ChunkManager.FindChunkByName`.
  `Manor_Cellars_Data` uses `"Manor Cellars"` **with a space**. Do not normalise it.
- **`ItemData.ItemID`** — inventory is saved as `ItemID` + `Quantity` and resolved through
  `Resources/Items`. A changed id is read, fails to resolve, and is dropped in silence.
- **`AbilityData.AbilityID`** — learned and equipped spells are saved as ids and resolved through
  `Resources/Abilities`. Never rename a shipped spell id.
- **`WikiEntryData.EntryID`** — unlocked encyclopedia entries are saved as a list of these.
- **`PerkData.PerkId`** — spent perks are saved as a list of these and resolved through
  `Resources/Perks`. A changed id is read, fails to resolve, and the perk's effects quietly stop
  existing — the id is deliberately **kept** rather than dropped, so the point stays spent.

There is **one** save file: `persistentDataPath/savegame.json`, written with `JsonUtility`. Not
PlayerPrefs. Five call sites write it.

→ [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md)

### Unity serialization

- **Renaming a public serialized field drops its value everywhere** unless you add
  `[FormerlySerializedAs]`. Appending a field is safe; inserting is not.
- **Enums are serialized by integer index. Always append.** Twenty-one are live.
- **Commit a script's `.meta` with the script.** The GUID inside it is what binds prefabs and the
  scene to the class. This has gone wrong twice, and it fails silently on a fresh clone.
- ⚠️ **Never rebuild an existing prefab by deleting and re-saving it.** That takes the `.meta` with
  it and mints a fresh GUID, orphaning every instance already placed. Edit in place:
  `PrefabUtility.LoadPrefabContents` → modify → `SaveAsPrefabAsset` → `UnloadPrefabContents`.
- **`UnityEvent.AddListener` does not survive being saved into a prefab.** Only
  `UnityEditor.Events.UnityEventTools` writes a persistent call.

**Before any rename or refactor touching a save key or a serialized field, produce an explicit
mapping table first.**

### The chunk world

- **Seven runtime code paths instantiate a chunk. Two do the full lifecycle**
  (`TransitionToChunkRoutine`, `TravelRoutine`); five are direct replacements. Change transition
  behaviour and you must touch all seven.
- **`CurrentChunkData` is written from eight places across six files.** To react to a chunk change,
  **poll a remembered reference** — do not hook one transition and assume you caught them all.
- ⚠️ **In `Awake`, ask `ChunkManager.ContentChunkName`, never `CurrentChunkData`.** `TravelRoutine`
  instantiates the destination *before* assigning `CurrentChunkData` — deliberately, so a broken
  arrival marker leaves the world untouched — and every `Awake` in the new chunk runs inside that
  `Instantiate`. Content that asks directly gets the chunk the player just **left**, on that one
  path of the seven, silently. This is a save-key bug wherever the answer is persisted.
- ⚠️ **A chunk root cannot be suspended with `SetActive(false)`.** It permanently blinds every
  `EnemyAI`, leaks a registered NavMesh, strands two tutorial singletons and leaves scene-root
  nameplates visible. Chunks are only ever destroyed.
- ⚠️ **`OnChunkTransition` takes a `ChunkTravelKind`, and only `EdgeCrossing` shakes the police.**
  A door is not an escape: every interior and dungeon carries `IsCity: 0`, so a new path that
  passes `EdgeCrossing` because it is the first enum value hands the player a free wanted-level
  wipe, silently. Pass `Portal` unless the player genuinely walked out of town.

→ [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md)

### Vehicles

⚠️ **Never `SetActive(false)` a vehicle root.** `OnDisable` clears the speed multiplier, so the
vehicle cancels its own boost the instant it is mounted. Hide `ParkedModel` instead.

→ [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md)

### Writing

⚠️ **Quest and dialogue prose is the owner's own work.** Build the machinery, leave the words.
Wiring, presets, quest definitions, conditions and tools are all fair game; the lines an NPC says
are not. If a task seems to need dialogue, ask for it rather than drafting it.

Note that `Tools > Content > Create Starter Presets` will generate a `DialogueData` from any
preset that has an `AmbientLine` and no `Conversation`. Leave a blank `AmbientLine` blank.

---

## 4. Where to look

| Task touches… | Read |
|---|---|
| Chunks, transitions, edges, building interiors | [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md) |
| Saves, serialized fields, enums, `.meta`/GUIDs | [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md) |
| Wanted level, police, stealth, pickpocketing, mounts, movement speed | [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md) |
| World Palette, presets, NPCs, enemy prefabs | [docs/reference/WORLD_AUTHORING_AND_NPCS.md](docs/reference/WORLD_AUTHORING_AND_NPCS.md) |
| Containers, foraging, loot respawn | [docs/plans/CONTAINER_SYSTEM_PLAN.md](docs/plans/CONTAINER_SYSTEM_PLAN.md) + save keys in [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md) |
| Quests, quest conditions, dialogue graphs | [docs/reference/QUESTS_AND_DIALOGUE.md](docs/reference/QUESTS_AND_DIALOGUE.md) |
| Spells, spell tuning, spellbook persistence and spell VFX | [docs/reference/SPELLS.md](docs/reference/SPELLS.md) |
| The art importer, sprite sizing, animator controllers | [docs/reference/ART_IMPORTER.md](docs/reference/ART_IMPORTER.md) |
| Title screen, character creator, their layout and art | the two `Assets/Editor/*ScreenSetup.cs` / `*CreatorSetup.cs` builders — no reference doc; the anchors and the reasons for them are commented at each call site, because they are only true of the code that writes them |
| Git, asset pruning, `.gitattributes`, project naming | [docs/reference/REPO_HYGIENE.md](docs/reference/REPO_HYGIENE.md) |
| Generating art (the art agent's contract) | [ART_PIPELINE.md](ART_PIPELINE.md) + [docs/art/ART_QUEUE.md](docs/art/ART_QUEUE.md) |
| What to work on next | [docs/README.md](docs/README.md) → `docs/plans/` |

---

## 5. Verification — read this before claiming something works

**There is no C# compiler, no Unity, and no test framework in the agent environment.** This is the
single most important thing to be honest about in this repo, because the whole convention here is
that documentation records what the code *actually does*.

What can be checked mechanically:

```bash
python Tools/asset_reachability.py --check-dangling   # reference integrity; exits 1 on breakage
python Tools/asset_reachability.py --packs            # which asset packs are fully unused
python Tools/art_status.py                            # what art exists and what is still owed
```

On Linux that is `python3` — Mint has no bare `python`.

`--check-dangling` resolves GUIDs from `Assets/`, `Packages/` **and `Library/PackageCache/`** —
every script Unity ships lives in a package, so without that last root `LayoutElement` and friends
read as missing and the check fails the moment the scene uses a UI component it had not used
before. Unity's two sentinel GUIDs are filtered. Everything still unresolved is real breakage and
is listed by name in `KNOWN_DANGLING`, not absorbed into a tolerated count; **anything not on that
list fails the run**, naming the GameObject and field that points at nothing. Exit codes are `0`
clean, `1` dangling, `2` couldn't verify — `Library/` is gitignored, so on a fresh clone it reports
that it checked nothing rather than passing. Run it before and after anything that deletes, moves
or renames assets.

**Everything else needs the Unity editor and therefore needs a human.** Say so plainly rather than
implying otherwise:

- Reference integrity passing says **nothing** about whether the project builds.
- A brace/paren balance scan catches a truncated edit. It says nothing about whether the code is
  correct or even compiles. **Do not report it as though it were a compile.**
- An editor tool that *generates* content has not changed anything until a human runs the menu
  item. Say that, rather than describing the change as landed.

⚠️ **Changes made in the Inspector while Play mode is running are discarded when it stops.** This
has wasted real time. When asking for an editor change, say whether Play must be stopped first.

⚠️ **Give the route through the editor UI, not just the field name** — name the panel (Hierarchy,
Inspector, Project), the full menu path, which GameObject to select and how to reach it, and any
precondition (exit Play mode, wait for the recompile, Ctrl+S). Naming a field alone is not enough.

### Never verified — the standing ledger

Everything here is on `main` and pushed. **None has been seen by a compiler or an editor.** Check
these the next time Unity is open, and keep this list current — delete an item when it is
confirmed, rather than leaving it hedged.

1. **The project compiled on 2026-08-05.** Both Danger Zone screen tools were run successfully
   that day, and `CharacterCreatorSetup` references `CharacterCreatorUI`, `PlayerClass` and
   `GameFlowController`, so the editor assembly could not have loaded unless `Assembly-CSharp`
   built too. That clears the whole backlog of never-compiled files — `EKVibe`, `EnemyAI`,
   `UIManager` and everything the pounds rename touched. **It proves they compile, nothing more:
   none of their behaviour has been exercised.** The creator tool was run again later the same
   day, after `CharacterCreatorUI`, `PlayerSession`, `SaveGameManager` and `CharacterCreatorSetup`
   changed, so those compile too. **The project compiled again on 2026-08-09**, when
   `Tools → Art → Import Generated Art` ran successfully — that clears everything changed
   between those two dates, including `CombatController`, `ArtImportTool` and the whole mobile
   performance pass. Again: it proves they compile and nothing else.
2. **`UIManager.EnsureDedicatedTrack`** — wraps a bar fill in its own parent when the scene did not
   give it one, fixing the concealment readout overlapping the mana bar. *Check the readouts no
   longer overlap, and that the concealment bar snaps back to wherever it was actually authored* —
   it has been stretched across the whole cluster until now, so its real size and position are
   unknown and may need moving.
3. **Every actor is 0.2 taller** — player 1.8, NPCs 1.55, child 1.3. Colliders, agents and
   nameplates were matched to each actor's sprite. *Check nobody's feet are underground and no
   nameplate sits on a head.*
4. **`EnemyAI.Awake` no longer hardcodes `_agent.height = 1.35f`** — it takes
   `WorldActorVisual.Height`. *Check enemies path around buildings, not through them* (needs a
   NavMesh bake after collision).
5. **Six enemy prefabs never seen in play** — Neek, OG, Roadman, Spicehead, Tainted, Tortured Neek.
   Expect Tortured Neek to slide and to have no death pose: he has only an idle sheet, which is an
   art gap, not a defect.
6. **The three quest fixes** — `ClearWanted` despawning police, `StartQuest` no longer rewinding a
   mid-flight objective, and the watcher claiming a reward only after paying it. The editor session
   that exercised the quest system predates all three. Re-testing needs a `QuestDefinition` in
   `Resources/Quests/` and some way to grant a quest; the throwaway rig was deleted deliberately,
   because quests are meant to be granted by an NPC or a world trigger, never a menu item.
7. **`murtaugh_Controller` is hand-authored YAML**, verified only structurally. *Check Murtaugh
   animates while roaming instead of sliding.* If Unity rejects it, re-stage the walk pair from
   `art_incoming/processed/` and re-run the importer.
8. **The pounds rename works.** `Preset_Stabmeister.asset` was rewritten by Unity on 2026-08-09
   and came out holding `PickpocketMinPounds: 5` / `PickpocketMaxPounds: 25` — the
   `[FormerlySerializedAs]` remap carried the values across intact. The remaining 24
   `Preset_*.asset` files still hold the old `…Gold` keys on disk and will convert the same way
   the first time each is touched. Nothing to do; no longer a risk.
9. **£ may not be in the TMP font atlas.** `EKVibe.FormatPounds` emits U+00A3, and TMP's default
   static atlases are often ASCII-only, which renders it as a missing-glyph box. *Check the bag's
   money readout and the pickpocket toast.* Fix is on the font asset (Project → the TMP font →
   Inspector): add £ to the character set and regenerate, or switch Atlas Population Mode to
   Dynamic.
10. **The wallet has never run.** Pickpocket a civilian authored `Pickpocketable`, get arrested,
    and reload a save.
    *Check the bag readout tracks all three, and that a save made before today loads at £0 rather
    than failing.*
11. **The blank-name fallback has never run.** The creator's name box starts empty behind a
    "Player name here!" placeholder, and `PlayerSession.BeginNewGame` turns a blank into
    **Vince**. The screen itself is confirmed; what is not is what happens on confirming without
    typing. *Start a new game leaving the box untouched and check the nameplate reads Vince, not
    blank.*

12. **Eleven sheets were mirrored to face camera-right** by `Tools/flip_sheets.py`, in place, so no
    `.meta`, GUID, clip or controller changed: `murtaugh_walk`, `neek_hurt`, `og_hurt`,
    `police_pcso_walk`, `roadman_death`, `spicehead_hurt`, `spicehead_walk`, and all four villager
    walks. The facing call was made from the art by eye, not measured — *check each one plays
    facing right and that the walk cycles still run forwards, not backwards.* A wrong call is
    undone with `python Tools/flip_sheets.py --force <name>`. `player_stabmeister_walk` was flipped
    too but is still in `art_incoming/` and has never been imported.

13. **The ambient traffic and car theft work, none of it exercised.** Four new scripts
    (`TrafficRoute`, `TrafficCar`, `HotwireMenuUI`, `BuildTrafficCarPrefabTool`) and edits to
    `EKVibe`, `VehicleData`, `VehicleController` and `WorldActorVisual` — all unseen by a compiler
    or an editor. The four `.meta` files were hand-authored and then rewritten byte-exact after
    Unity rejected the first pass. *Check the §10.2 list in
    [docs/plans/TRAFFIC_AND_CAR_THEFT_PLAN.md](docs/plans/TRAFFIC_AND_CAR_THEFT_PLAN.md):* compile
    on open; run the builder tool twice (Reliant Robin common, Vauxhall Corsa better); author two
    routes in `Home_London_Prefab`; cars drive/brake/honk/resume; hotwire success → driver flees,
    2 knives, two officers, hidden rider; timeout → 1 knife, car drives off; ride across a chunk
    edge; reload → traffic fresh, stolen car gone. **The FU Sports nested prefab in
    `Home_London_Prefab` was re-pointed** to its post-reorganisation `Shops/` path (committed
    2026-08-12) — but that edit has never been opened in an editor, so *confirm on first open that
    the FU Sports building resolves rather than showing as a missing prefab.*

**The cast is now uniformly 65 px.** Every character sidecar declares `worldHeight: 1.35`, which
imports at 65 px cells. `sheet_char_player_mrhood_idle` and `sheet_char_player_stabmeister_idle`
were the last two still on disk at 74; the importer has re-done them in place, GUIDs intact, and
both measure 65 px tall as of 2026-08-08.

⚠️ **`ART_PIPELINE.md` still tells the art agent adults are `1.55`**, so the next delivered batch
will arrive at the wrong density again and need the same correction. Deciding whether the contract
or the cast is the thing to change is the owner's call, and nothing here has made it.

**Also outstanding — a live defect, not a verification:** no `Police_*` prefab has `IsPolice` set,
so arrest never fires and `DespawnPolice` destroys nothing. Fix is ticking the box on all five
prefabs in the Inspector, **never** by re-running `ModernBritainSetup`.

⚠️ **Also a live defect — `Import Quests` silently nulls a preset's `Conversation` when the
dialogue asset's filename differs only by case.** Found 2026-08-16 on the first real import.
`QuestTextImporter.DialoguePathFor` builds `Dialogue_<npcId>.asset` from the `DIALOGUE` block name,
which is lowercase. `SaveAsset` then calls `AssetDatabase.LoadAssetAtPath` on that exact path —
**Unity's AssetDatabase is case-sensitive even on Windows**, so a pre-existing PascalCase asset is
not found, `CreateAsset` fails against the case-insensitive filesystem, and the unsaved in-memory
object is assigned to `preset.Conversation`, which serializes as `{fileID: 0}`.

Observed: `Preset_CouncillorMosley` and `Preset_Scrapman` both went from a valid GUID to
`{fileID: 0}`, and neither `Dialogue_CouncillorMosley.asset` nor `Dialogue_Scrapman.asset` received
its new lines. `danielpauls` and `underhoused` had no pre-existing asset and imported correctly.
**Nothing was logged** — the `no preset matched` warning does not fire, because the preset matcher
lowercases both sides and matches fine. Only the filename is case-sensitive.

Consequence: the placed Mosley still points at his old one-liner by GUID, so the arc cannot start;
and re-stamping him from the palette gives him **no conversation at all**, which is worse.

**Repaired for these two on 2026-08-16, agent-side, with Unity closed.**
`Dialogue_CouncillorMosley` → `Dialogue_councillormosley` and `Dialogue_Scrapman` →
`Dialogue_scrapman`, renamed with `git mv` in two hops (temp name, then target — a case-only rename
cannot be done in one on Windows), `.meta` moved with each so **both GUIDs are unchanged**; internal
`m_Name` aligned to the new filenames; and both presets' nulled `Conversation` fields restored to
the original GUIDs. All four live `DIALOGUE` ids now match their asset filenames exactly.
*Confirm on next open that Unity accepts the renames without re-importing, and that the placed
Mosley and Scrap Man in `Home_London_Prefab` still resolve their conversations.*

**The importer itself was fixed the same day — never compiled.** Three changes in
`QuestTextImporter.cs`, which protect the other sixteen PascalCase assets still on disk (including
**`Dialogue_Ralph` and `Dialogue_Sanjeet`**, the cast of the unwritten Quest 6, which the next quest
written would have hit):

- **`ResolveAssetPath`** maps a desired path onto the real file when the two differ only by case,
  by enumerating the directory. ⚠️ It deliberately does **not** shortcut on `File.Exists` — on a
  case-insensitive filesystem that answers true for the wrong casing, which is the entire bug.
  Applied to the dialogue path and to the quest path, which had the same latent collision.
- **The dialogue branch now loads-then-mutates**, mirroring `WriteQuestAsset`. It previously always
  built a fresh `CreateInstance<DialogueData>()`, so even with the path fixed it would have dirtied
  a detached instance — writing nothing and still nulling the preset. Path resolution alone would
  have moved this bug, not fixed it.
- ⚠️ **`Cleanup` now destroys only assets this run created**, tracked by an `isNew` flag added to
  the `builtDialogues` tuple. Reusing a loaded asset made the old unconditional `DestroyImmediate`
  a live hazard: Unity throws on destroying a persistent object rather than ignoring it, so a
  validation failure would have aborted the import with an exception.
- **`SaveAsset` now tests `AssetDatabase.Contains(asset)`** rather than probing the path, so it can
  never dirty an object that is not the asset on disk.

*Check on next open: re-import with an unchanged tree and confirm the four conversations keep their
GUIDs; author a deliberate case-collision (a `DIALOGUE ralph` block) and confirm it updates
`Dialogue_Ralph.asset` in place instead of nulling `Preset_Ralph.Conversation`; and force a
validation error in a `.quest` file to confirm the failure path logs errors rather than throwing.*

**Also outstanding — four sprites in `c.unity` point at files that do not exist.** Three `Visual`
SpriteRenderers on one missing texture, three on another, one more on a third, and the **PCSO**
actor's `WorldActorVisual.ActorSprite` on a fourth. They are as old as commit `fc1d035` at least,
and were hidden until now inside a `--check-dangling` baseline that called them built-in Unity
GUIDs. They are listed in `KNOWN_DANGLING` in `Tools/asset_reachability.py`. Fix is reassigning
each sprite in the Inspector, then deleting its line from that list. The PCSO one probably wants
`sheet_char_police_pcso_idle`, which is on disk — *check that before assuming it.*

**Also outstanding — the dodge roll, phase 1.** On `dodge-roll-phase2` (which carries phase 1),
never compiled:

- **`Health.TakeDamage` now returns `bool`** — true if the hit landed. Nothing in phase 1 reads it;
  it exists so enemy knockback can tell a connected hit from a dodged one. ⚠ **The method is no
  longer bindable in a `UnityEvent` dropdown**, because Unity only offers void methods there.
  Nothing binds it today — `grep -rn "m_MethodName: TakeDamage" Assets/` was empty before it
  landed, and is the check to re-run if anything ever stops taking damage for no visible reason.
- **Space rolls the player**, 2.4 m over 0.40 s for 14 stamina, i-frames 0.05–0.30 s in, 1 s
  cooldown. *Check the distance looks like the field says, that a second Space inside a second
  does nothing, and that rolling off a kerb still falls rather than hovering* — hovering means the
  velocity zeroing has been moved inside the loop.
- **`Health` refuses damage outright while `IsInvulnerable`.** *Stand in the PCSO's range — the
  only `EnemyAI` in `c.unity` — and roll through its swing. A white **"Dodged!"** should appear, no
  red number, and health should not move.*
- **Rolling breaks stealth.** *Crouch with **C**, roll, and check the toast reads "Out of stealth.",
  the CRO button pops back out and walk speed returns.*
- **The DGE button is built at runtime**, fourth in the bottom row. It will not appear in the
  Hierarchy until Play starts — look for `UI/UICanvas/HUDPanel/ActionButtons/DGE`. *Check it is
  reachable with a thumb in the Device Simulator, landscape;* it is invisible in a 16:9 Game view.
- **The roll animation landed 2026-08-09 and plays.** `player_Controller` holds a `Roll` state on
  a 6-frame clip, and the other four class controllers do too.
- ⚠ **`RollSpeedCurve` integrates to exactly 1 over [0,1]**, and that is the only reason the roll
  travels `RollDistance`. Reshaping it without preserving that decouples the two silently.

→ [docs/plans/DODGE_AND_KNOCKBACK_PLAN.md](docs/plans/DODGE_AND_KNOCKBACK_PLAN.md) §12 for the routes.

**Also outstanding — enemy knockback of the player, phase 2.** On `dodge-roll-phase2` (built on
the phase 1 branch), never compiled:

- **`EnemyAI.KnockbackDistance`, default 0** — no prefab or scene file changed, so nothing knocks
  the player back until the Inspector pass sets it. Per the recorded decision: `Enemy_OG` and
  `Enemy_Tainted` at **2 m**, police at **0**, folded into the same Inspector session as the
  `Level: 3` and `IsPolice` prefab passes. *Stamp `Enemy_OG` from the palette, set Knockback
  Distance = 2 outside Play mode, take a hit, and check the slide is ~2 m and stops at walls.*
- **A dodged hit no longer shoves.** Both `AttackRoutine` damage branches gate the shove on
  `TakeDamage` returning true. *Roll through the stamped enemy's swing: "Dodged!", no red number,
  and crucially no slide.* This is the defect the whole return value exists to fix.
- **Knockback wins over a roll in progress** — the roll polls `_isKnockedBack` and yields the
  body to it. *Roll into a 2 m hit and check the player ends up shoved, not rolled.*
- **0.4 s of recovery i-frames as the slide ends** (`KnockbackRecoveryIFrames`), so two enemies
  cannot chain-stun. *With two knockers in range, check a second hit during the recovery is
  refused — "Dodged!" over the player, no damage.*
- **The player's knockback animation landed 2026-08-09** and is wired into all five class
  controllers, but has never been seen play because nothing sets `KnockbackDistance`. **No enemy
  subject has a knockback sheet**, so `EnemyAI`'s own `SetAnimatorTrigger("Knockback")` still
  no-ops — guarded, so no console errors — and the `Hit` trigger carries the feedback there.
- **The slide uses the same `MovePosition` sweep as walking** — deliberate asymmetry with the
  enemy-side knockback coming in phase 4, which must capsule-cast because enemies move by
  transform. *If the player ever slides through a wall here, the Rigidbody has been switched to
  kinematic somewhere — check that first.*

→ [docs/plans/DODGE_AND_KNOCKBACK_PLAN.md](docs/plans/DODGE_AND_KNOCKBACK_PLAN.md) §12 for the routes.

**Also outstanding — the melee knockback perk, phase 4.** On `dodge-roll-phase2`, never compiled:

- **`PerkEffectType.MeleeKnockback = 9` is appended, never reordered** — the enum is serialized by
  integer index inside every `PerkData` asset, and the first asset authored freezes these indices
  forever. Magnitude is a **flat metre value**, not a percentage. **No perk asset exists** — the
  owner authors it: Create → `GBH England/Data/Perk`, into a `Resources/Perks` folder, one
  effect of type MeleeKnockback, Magnitude 2. *Then spend a point and hit something: the enemy
  should slide ~2 m and stop at walls.*
- **`PlayerSession.MeleeKnockbackDistance` resets with the other cached query values** in
  `RecalculateDerivedStats` step 6 — stats recompute on every load, so a cached value that is added
  to but never reset would accumulate per load. *Take the perk, note the shove, reload the save,
  and check the shove is the same rather than doubled.*
- **Enemies slide by transform through a capsule cast** (`TryStep`, factored out of
  `TryCollideMove`), the mirror image of the player's `MovePosition` slide — each side uses the
  mechanism its body type requires, and the comments at both sites say so. The agent is paused by
  `updatePosition = false`, never `agent.enabled`.
- **A killed enemy is never shoved** — the melee site gates on `!targetHealth.IsDead` because
  `Health.Die` has already disabled the agent and the AI. *Kill something with the perk on and
  check the corpse does not slide.*
- **EnemyAI's three `SetTrigger` sites are now guarded** like CombatController's — before this,
  firing an undefined trigger logged an error every call, and no enemy controller defines
  `Knockback` yet. Expected silence until the band 10 sheets are delivered and imported.

→ [docs/plans/DODGE_AND_KNOCKBACK_PLAN.md](docs/plans/DODGE_AND_KNOCKBACK_PLAN.md) §12 for the routes.

**Also outstanding — enemy levels in the world, combat nameplates, bigger HUD.** Merged
2026-08-08, code-reviewed against its plan, never compiled:

- **Enemy levels are authorable but nothing is authored.** `PlacementPreset.EnemyLevel` and the
  palette's per-stamp Level field attach an `EnemyLevel` at placement. **A level of 0 attaches no
  component at all** — deliberate, because a level-1 component is not inert: the nameplate starts
  reading it and the badge flips from the prefab's "3" to "1". ⚠️ **No enemy prefab is placed
  anywhere in any chunk or in `c.unity`** — the only `EnemyAI` in the scene is the PCSO — so this
  path has never run. *Stamp an enemy from the palette at Level 4 and check it is tougher than
  one stamped at Level 1.*
- **Nameplates are combat-gated and now build lazily.** They show on aggro **or** when the player
  is within `SightRadius`, and hide a few seconds after. *Check a plate appears as you approach
  rather than only after the first hit, and that it does not reappear over a corpse.* The tutorial
  bandit's badge should now read **1, not 3** — that line was a real bug, set after the badge had
  already been drawn.
- ⚠️ **`EnemyAI` resolves its nameplate in `Start`, not `Awake`.** `TutorialSequence` adds
  `EnemyAI` before `EnemyNameplate`, and `AddComponent` runs `Awake` synchronously, so caching in
  `Awake` would cache null and leave the tutorial bandit with no plate at all. Do not move it.
- **The player's bar carries a level badge** and now rises when they deal damage or draw aggro,
  not only when hit. *Check the badge tracks a level-up while the bar is visible.*
- **The top-left HUD cluster is scaled 1.6× at runtime** from `EKVibe.HudClusterScale`. The
  ceiling is 1.75, where it would overlap the combat log. A `SafeAreaFitter` is added to the HUD
  panel at runtime — *invisible in a 16:9 Game view; needs the Device Simulator.*

→ [docs/plans/LEVELS_IN_WORLD_AND_HUD.md](docs/plans/LEVELS_IN_WORLD_AND_HUD.md) §10.3 for the routes.

**Also outstanding — perks, growth and proportional armour, phase 3.** Merged 2026-08-08,
code-reviewed against its plan, never compiled:

- ⚠️ **Armour is now proportional, not a flat subtraction.** `EKVibe.ArmourSoftCap` is 20, capped
  at 75% reduction. `TestShield`'s Armor 4 now reads as ~16.7% off a hit instead of a flat 4.
  *Take a hit with and without the shield equipped and check the numbers look sane.*
- **Stats are recomputed from level and perks on every new game and every load.** The baseline
  capture is guarded against the character template aliasing `RuntimeStats` — without that guard a
  second load in one app session bakes growth and perks into the baseline and inflates stats
  permanently. *Load the same save twice in one sitting and check the stats read identically the
  second time.* This is the failure most likely to go unnoticed.
- **No perk assets exist yet**, so the perk window has only ever had an empty state to draw.
  Prose is the owner's: grep `[no perks written yet` and `[perk point earned`.
- **`SaveData.PerkIds` is appended.** An id that no longer resolves is deliberately **kept**, so
  the point stays spent rather than being silently refunded.
- **Traits do not auto-grow** — only HP and resource. Deliberate: `CombatController` reads
  `Strength*2+5`, so growing Strength would retune the whole enemy roster at once.

**Also outstanding — XP and levels, phases 1–2, none of it exercised.** Merged 2026-08-08,
code-reviewed against its plan, never compiled:

- **Kill XP depends on a one-line fix landing.** Both player damage sites now pass `gameObject`
  into `TakeDamage` so `Health.LastAttacker` is set; before, it was always null for player hits.
  *Kill an enemy and check XP moves off zero.* If it does not, that fix did not take, and nothing
  will say so.
- **`EnemyLevel` scales from the prefab's level-1 baseline**, applied inside `Health.Awake` before
  `CurrentHealth = MaxHealth`. *Add one to an enemy, set Level 5, and check it spawns at full
  health, not partial.* An enemy without the component is untouched and stays level 1.
- ⚠️ **Every existing enemy still wears a "3" badge** while actually being level 1 — eleven
  prefabs store `Level: 3` on disk from when the nameplate's level was cosmetic. Cosmetic only,
  but it will look wrong until levels are authored.
- **`SaveData.TotalXP` is appended.** *Load a save made before today and check it arrives at
  level 1 rather than failing.*
- **The bag readout binds only after** `Tools → UI → Rebuild Inventory Panel (Win95)` is
  run — the scene's `LevelText` is unassigned until then. The HUD badge is already wired.

→ [docs/plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md](docs/plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md) §9.3 for the full routes.

**Also outstanding — the equipment, map and encyclopedia work, none of it exercised.** Committed
2026-08-08, never in an editor:

- **The paper doll.** *Equip a weapon and check the melee number goes up by its `Damage`; equip
  armour and check incoming hits drop by `TotalArmor`.* ⚠️ Armour is a **flat** subtraction floored
  at zero, so a full doll may make weak enemies harmless — a balance question, not a bug.
- **The bag window was rebuilt by `InventoryWin95Builder`.** The scene edit is committed, but
  *check the rail buttons, the equipment slots and the tooltip all sit where they should* — the
  builder is an editor tool and its output has never been looked at in Play mode.
- **Map of Britain and WIKIBRITAIN.** *Check a first arrival toasts and a reload does not, and that
  a save made before today opens a populated encyclopedia rather than a toast storm* — the
  backfill path in `ContinueFromSave` is the one most likely to be wrong.
- **Three new save fields** (`Equipment`, `VisitedChunks`, `UnlockedWikiEntries`). *Load a
  pre-equipment save and check it arrives with an empty doll and a blank map instead of failing.*

**Also outstanding — the survival pressure pass, none of it exercised.** Committed 2026-08-09,
never compiled:

- ⚠️ **Mana no longer regenerates at all.** It comes back through consumables, the pub's full
  restore, and a heal spell that does not exist yet. `ManaRegenPerSecond` is deleted and leaves an
  orphan key in `c.unity` that Unity drops on the scene's next save — **do not hand-edit the scene
  to remove it.** *Cast Spark, stand still 30 s, and check mana does not move.*
- ⚠️ **The dodge roll costs 50% of maximum stamina, floored.** `CurrentRollCost` uses
  `FloorToInt`, and that is load-bearing: `PerformDodge` refuses on `CurrentStamina < cost`, so a
  cost above half the pool makes the second roll impossible. Rounding put a 55 pool's cost at 28,
  which left 27 and refused. *Check a Young Driller gets exactly two rolls from full — 55 → 28 →
  1 — and that the third is refused. One roll then a refusal means the floor was lost.*
- **Stamina regenerates at 5% of maximum per second**, a percent rather than a flat rate so the
  economy does not drift as the pool grows with level. *Check ~3 points a second on a 55 pool: one
  roll back after ~10 s, full after ~20 s.* It ticks in combat deliberately — there is no combat
  state and the code documents why the two obvious ways to build one fail.
- **A third HUD bar, amber, built at runtime** by `UIManager.EnsureStaminaBar` — nothing to wire.
  *Check it reads `55 / 55`, sits below the mana bar, does not reach the combat log or the
  joystick, and survives the Device Simulator in landscape.*
- **The concealment bar and stealth are sidelined by decision**, not overlooked. `ConcealmentBar`
  is inactive in `c.unity` and nothing activates it, so there is a deliberate 28 px gap where its
  slot is reserved. The stray duplicate `MPFill` inside it was left alone. **Not a defect of this
  pass.**
- ⚠️ **A pre-existing bug is now written up but not fixed**: `UIManager.EnsureDedicatedTrack`
  tests `parent.childCount == 1`, and `EnsureBarLabel` later adds the readout beside the fill, so
  the next call wraps a fill that never needed it — inheriting the fill fraction as the new track's
  size. HP and MP both take that path, invisibly, because their first paint is a full bar. *It
  would show as a health bar that tops out at a third after loading a save at low health.* Its own
  pass; the stamina bar is built so it cannot be reached.
- **No save key changed**, and `Health`/`Mana`/`Stamina` already round-trip. *Load a save made
  before today and check it arrives with whatever mana it held, no error, and HP never at 0.*
- **The magic tutorial is the one scripted sequence written while mana came back.** Spark costs 12
  against a 55–80 pool and melee is always available. *Walk it end to end once.*

→ [docs/plans/SURVIVAL_PRESSURE_RESOURCES.md](docs/plans/SURVIVAL_PRESSURE_RESOURCES.md) §10.3 for
the full routes.

**Also outstanding — `spark_of_talent` converted off bespoke code onto the `.quest` pipeline.**
Committed 2026-08-15, never compiled, and **not importable until the editor pass below is done**:

- ⚠️ **`MagicTutorial.cs` is deleted and the import has not run.** These must happen in **one
  editor session with no Play mode in between.** Until the import runs and both characters are
  placed, London has **no Daniel Pauls and no geezer at all** — the quest cannot be started. Run
  it in this order: compile → `Tools → Content → Validate Quests` → `Import Quests` → build
  `Enemy_UnderHoused` → wire it → place both → only then Play.
- **A GUID scan found no prefab, scene or asset holding `MagicTutorial`'s script**, and its only
  two live C# references (`GameFlowController`, `StarterPresetGenerator`) were removed. The two
  preset keys became the literals `"DanielPauls"` / `"TracksuitGeezer"` — unchanged values, and
  they are what `PlacementPresetLibrary.asset` stores.
- ⚠️ **`QuestGateType.ActiveAtStage = 4` is appended, never reordered** — serialized by integer
  index inside every choice in all sixteen generated `DialogueData` assets.
- **Daniel now opens with one fixed line at every beat**, because a conversation has a single
  start node. The four beats are gated choices. *Check exactly one is offered at a time, and that
  the reward branch is gone after the quest completes* — if it reappears, `QuestGateStage` is not
  being read, which most likely means `BuildDialogue` lost its two new field assignments.
- **Stage 1 is `MANUAL`, not `TALKTO`.** A TalkTo final stage completes on the interact, before
  any choice is picked, which would skip the reward beat entirely.
- **`Enemy_UnderHoused` does not exist yet.** `Tools → Content → Build Enemies From Generated Art`
  creates it — **run it on a clean tree**, it rewrites the YAML of every enemy prefab on its
  update path. Then in Prefab Mode: confirm `EnemyAI` is **unticked**, add `Interactable`
  (prompt "Talk to the twitchy geezer", range 3, Reusable on), add `NPCDialogueInteractable` with
  `Dialogue_underhoused`, add `HostileAfterDialogue` and hook `Interactable.OnInteract` →
  `HostileAfterDialogue.OnTalked`, and set its hostile line.
- ⚠️ **Unverified Unity behaviour: whether `Awake` runs on a disabled component.** If the geezer,
  once panicked, stands still or falls through the NavMesh, that is the answer and
  `HostileAfterDialogue` must snap him to the NavMesh itself.
- **He is placed content now**, so he stands in London from the start and can be killed before the
  quest is taken — which pre-completes the kill stage. Accepted deliberately.
- **Two live defects this fixes**: loading a save directly into London used to produce no Daniel
  and no geezer; and reloading mid-quest used to require killing a second geezer.
- **`Preset_DanielPauls.QuestKey` is blank** and must be set to `danielpauls` for
  `daniel_pauls_quest_one`. His `Conversation` is written by the importer.
- **`spark_of_talent` is unchanged as a save key.** *Load a save holding it mid-flight (should bind
  the kill stage to the placed geezer) and one holding it complete (should pay nothing — the
  reward is deliberately 0/0, since the reward scan retro-pays any completed unclaimed quest).*
- **`quests/dialogue/danielpauls.quest` owns Daniel Pauls' conversation permanently.** One
  `DIALOGUE` block per npcId across the whole folder; every future Daniel quest adds gated nodes to
  that file.
- **`PlayerSession.KnowsSpark` is still written by nobody who reads it and is not saved.**
  Pre-existing, unchanged by this, and now harder to spot: the spellbook's `KnownSpellIds` is what
  actually persists a learnt spell.

**Also outstanding — the importer's slicing moved onto `ISpriteEditorDataProvider`.** Committed
2026-08-16, never compiled:

- **The defect it fixes:** `TextureImporter.spritesheet` takes `SpriteMetaData`, which carries no
  sprite id, so Unity re-linked frames by name against the `nameFileIdTable` in the `.meta` — known
  names kept their ids, new names got **zero**. Only a sheet that *gained* frames broke.
  `sheet_char_player_walk` went 4 frames to 6 and frame 5 of the clip took `fileID: 0`, so the
  player flickered invisible once per stride. Repaired by hand in `fefe311`; this stops it
  recurring. Ids for existing frame names are reused, so nothing that references a frame moves.
- **`Assets/Editor/ArtImportTool.cs` now has `using UnityEditor.U2D.Sprites;`** — from
  `com.unity.2d.sprite`, added in `e1dc5b0` for exactly this. `Assets/Editor/` has no `.asmdef`, so
  this was raised as a risk that the editor assembly might not see the package and would fail to
  load wholesale. **It is not a risk:** `Unity.2D.Sprite.Editor.asmdef` declares
  `"autoReferenced": true` and is Editor-only, so `Assembly-CSharp-Editor` references it with no
  `.asmdef` of ours, and the package is resolved on disk at
  `Library/PackageCache/com.unity.2d.sprite@1.0.0`. Rollback, if it is ever wanted for another
  reason, is `git checkout -- Assets/Editor/ArtImportTool.cs`.
- **The id a new frame gets comes from its GUID, not from us.** `SpriteDataExt(SpriteRect)` sets
  `internalID = spriteID.GetHashCode()`, so assigning a real `spriteID` per frame is the whole fix —
  that step is what `SpriteMetaData` had no field for. Conversely `CopyFromSpriteRect` copies name,
  rect, pivot and `spriteID` but **deliberately not `internalID`**, so a frame Unity already knows
  keeps the id it has. That is why re-importing `sheet_char_player_walk` does not repoint the clip
  `fefe311` repaired by hand.
- ⚠️ **Slicing runs after the importer's own settings and before `SaveAndReimport`, and that order
  is the difference between working and silently doing nothing.** The provider captures
  `spriteImportMode` once, at `InitSpriteEditorDataProvider`; `SetSpriteRects` then branches on the
  captured value. Built before the mode is set to Multiple, a six-rect array matches neither branch
  and **no slicing happens at all** — it does not throw and it does not warn. `VerifySliced` is what
  would catch it.
- **`VerifySliced` now also checks each sub-sprite's local file id is non-zero and unique**, so the
  failure above can never again be silent. *Re-import one pair from `art_incoming/processed/` and
  check there is no "Identifier uniqueness violation", no new Animator transitions, and
  `0 duplicate transition(s) removed`* — which also settles the reimport-idempotency item below.

**Also outstanding — roll and knockback, imported 2026-08-09, only half exercised.**

The import ran and accepted all ten sheets, so `Assembly-CSharp` compiled and the importer's own
checks passed on real art. **The roll has been seen playing and is good.** What that does *not*
cover is below:

- **The knockback has never been seen play.** It needs an enemy with `KnockbackDistance` set,
  which no prefab has — see the phase 2 entry above. *Stamp `Enemy_OG`, set Knockback Distance = 2
  outside Play mode, and take a hit.*
- **`ApplyKnockback` clears the `Hit` trigger before setting `Knockback`.** Both were being set in
  the same frame, since a knockback only ever follows a landed hit, and the Animator would take
  whichever Any State transition it evaluated first while holding the other for the next frame.
  Compiles; never run. *Check the tumble plays whole rather than flickering through a Hurt frame.*
- **The knockback clip is 0.50 s against a 0.22 s slide, deliberately.** *Check the player can move
  ~0.28 s before the tumble finishes drawing, and that walking during that window keeps the tumble
  on screen until it ends.* That is the exit-time return, not a defect.
- ⚠️ **Reimport idempotency is unproven.** The second run reported nothing waiting, which proves
  the archive step worked and nothing more. *Move one pair back from `art_incoming/processed/`,
  re-run the import, and check the Animator window shows no new transitions and the report says
  `0 duplicate transition(s) removed`.*
- ⚠️ **`knockback` is now a shape-changing action** alongside `death`, `cycle` and `roll` — exempt
  from the standing height and baseline checks in both `ArtImportTool` and `Tools/precheck_sheets.py`,
  and its contract is now 6 frames at 12 fps, was 3. The delivered art is an airborne tumble, not
  the standing stagger the action was first specified as. Feet moved 90–134 px between frames on
  these sheets and were correctly not flagged. **Width is still checked.** *If a stagger-style
  knockback is ever wanted instead, this is the line that changed.*
- **`player_bundabasher` has no `idle`**, so its two sheets imported with the width comparison
  skipped, and the class is still a Young Driller fallback — roll and knockback do not count toward
  the six core actions that release a class into gameplay. Its controller now exists holding only
  those two states.
- **`Tools/precheck_sheets.py` compares width as a fraction of the cell**, not in raw pixels. Three
  class idles are drawn on 1024 px cells against these sheets' 512, which was reporting correct art
  as "2× narrower".

→ [docs/reference/ART_IMPORTER.md](docs/reference/ART_IMPORTER.md) for the wiring.

**Also outstanding — linked location portals, none of it exercised.** Committed 2026-08-09, never
compiled, and **no linked pair and no `DungeonPortal` exists anywhere in the project** — a GUID
scan of `Assets/` finds none, and `git log -S` says the last one went in `8bd1520`. Every route
below therefore needs content authoring before it can even be attempted:

- ⚠️ **`ChunkManager.TravelRoutine` was reordered so nothing commits until the arrival marker
  resolves.** The destination is instantiated, the marker looked up, and only then are wanted
  state, `CurrentChunkData`, the visited list, the wiki toast and the autosave touched. *Point a
  portal at a marker id that does not exist, press USE, and check the player stays put with a
  warning naming the chunk and the id — not a black screen, not a half-loaded chunk.* This is the
  one behavioural change to a path that already worked.
- **`DungeonPortal.TargetSpawnPointId` is appended** and takes the marker's rotation as arrival
  facing, via a new `CombatController.FaceTowards`. Empty keeps the old raw-`SpawnPosition`
  behaviour. *Check the player arrives facing the marker's blue arrow and that the sprite faces
  that way too, rather than only the invisible transform.*
- **A portal refuses while mounted** — "Get off the vehicle first." *Ride a moped to a door and
  check it refuses and the vehicle is untouched.*
- **`DungeonPortal.Awake` no longer overwrites an authored `Interactable.InteractRange`**; it only
  sets 3 on a component it created itself. *Set a range of 6 in the Inspector and check the prompt
  appears from further away.*
- **`Assets/Resources/MapChunkRegistry.asset` and its `.meta` were hand-authored** with fresh
  GUIDs, holding all six existing chunks — no Unity was available. *Confirm on first open that
  Unity accepts them rather than minting new ones, and that the asset's Inspector shows six
  chunks.* `FindChunkByName` consults `AllChunks` first and this second.
- **`Tools → Place → Portal Placement` is a rewritten window** — linked pairs, an interior
  bundle creator, and `Validate All Location Links`. *Open it once and check it draws without
  console errors before trusting any of it.* It refuses to create while Prefab Mode is open, by
  design.
- ⚠️ **The validator has never run against real content.** With no portal in the project it can
  only report chunk-name and registry findings. The plan this came from expected it to catch a
  self-targeting `Portal_Home_London` in `Home_London_Prefab`; **that object no longer exists**, so
  that check is unproven. *Author one deliberately broken pair and confirm each rule fires.*
- **Interiors are inferred, not flagged** — a chunk with no N/S/E/W adjacency that some portal
  targets. Nothing on `MapChunkData` declares it, deliberately, to avoid a serialized field for
  something derivable.
- **Scoped out on purpose:** `TravelRoutine` still destroys and re-instantiates, so returning
  outside rebuilds the exterior and resets unsaved NPC, enemy and chest state. Exact preservation
  belongs to [docs/plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](docs/plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md).
  **Do not ship reward-bearing interiors until that lands.**

→ [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md) and
[docs/reference/WORLD_AUTHORING_AND_NPCS.md](docs/reference/WORLD_AUTHORING_AND_NPCS.md).

**Also outstanding — six empty interior shells, hand-authored YAML.** Committed 2026-08-09.
`Quidland`, `FU_Sports`, `City_Hall`, `Police_Station`, `Gang_Hideout` and `The_Winchester` — each a
`MapChunkData` plus a chunk prefab holding a floor, four walls, a `RuntimeNavMeshBaker` and one
id-less `PlayerSpawn`. All six are in `MapChunkRegistry`, which now lists twelve chunks.

- ⚠️ **Twelve `.asset`/`.prefab` files and their twelve `.meta` files were written by hand** — no
  Unity was available, so every GUID and every `fileID` was assigned by a script rather than by the
  editor. *Open each prefab once and confirm Unity accepts it rather than reimporting it into
  something different:* the root should be one object with a `RuntimeNavMeshBaker`, six children, a
  lit floor and four walls, and no console error. `--check-dangling` resolves every reference in
  them, which proves the GUIDs point at real assets and **nothing about whether the YAML parses**.
- ⚠️ **The six `ChunkName` values are save keys from the moment a save is made inside one.**
  Changing one later orphans those saves in silence. Nothing has saved in any of them yet, so this
  is still the free moment.
- **They have no doors.** Nothing points at them and they point at nothing. Wiring one is a run of
  `Tools → Place → Portal Placement` against `Home_London_Data` — which is also the first
  real exercise of that tool, and of the marker travel path above.
- ⚠️ **None of the five exterior building models exists.** [docs/art/ART_QUEUE.md](docs/art/ART_QUEUE.md)
  band 6 owes City Hall, Quidland, F.U. Sports, Police Station and Gang Hideout as 3D shells, and
  says the delivery route is **not decided**. Until they land, a door wired to any of these hangs in
  open air. Not a blocker for the interiors; it is the blocker for a satisfying test.
- **`The_Winchester` is the odd one out.** It is not in band 6, and `PubInteractable` already does
  the whole pint-clears-wanted-heals-saves flow from one USE on `Pub_TheWinchester.prefab` — which
  is **not placed in any chunk**. The shell exists; whether the pub should go behind a door at all
  is an open design question, not a decision this made.
- **Each is a bare box.** `mat_dungeon_wall` and `mat_dungeon_floor` are placeholders, not a view on
  how a pound shop should look.
- **Downstream, not done:** arrest still teleports to Manor Cellars (`GameFlowController.ArrestRoutine`),
  not the police station. `WantedManager`'s own comment already calls rerouting the arrest path a
  separate job.

**Also outstanding — the name unification. It compiles; behaviour unexercised.** Committed
2026-08-16, phases 1–4 (`b763080`, `44b0fd8`, `947ded5`, `0b9301f`):

- ✅ **The root namespace `GBHEngland` compiles.** On 2026-08-16 the owner successfully ran
  `Tools → Content → Import Quests` and `Tools → Content → Build Enemies From Generated Art`,
  which wrote 7 `QuestDefinition`s, two `DialogueData` assets and `Enemy_UnderHoused.prefab`. The
  editor assembly cannot load unless `Assembly-CSharp` built, so the 147-file rename **has been
  through a compiler**. Per §5 that proves it compiles and **nothing else** — none of the renamed
  code's behaviour has been exercised.
- ⚠️ **Three `UnityEvent` bindings store the namespace as a literal string** and were rewritten in
  the same commit: `EBike.prefab` (`VehicleController`), `Pub_TheWinchester.prefab`
  (`PubInteractable`) and `c.unity` (`InventoryController`). These are **not** GUID-bound, so a miss
  fails **silently** with a clean console. *Mount the e-bike, USE the Winchester, open the bag and
  click the rebuilt buttons.* If one is dead, look at its `m_TargetAssemblyTypeName`, not the C#.
- ⚠️ **`productName` is now `GBH England`** (no colon — it is a real folder in
  `persistentDataPath`). **Every save made before 2026-08-16 is orphaned**, along with the graphics
  `PlayerPrefs`. Accepted deliberately; there is no migration shim. *Play once and confirm a save
  appears under `…/LocalLow/DefaultCompany/GBH England/`. Expect graphics settings to reset once.*
- **`Create →` menus moved to `GBH England/Data/…`.** Existing assets are unaffected — `menuName`
  is not stored in the asset. *Check `Create → GBH England → Data → Item Data` still makes a working
  `ItemData`.*
- **`EK*` is deliberately kept** (`EKVibe`, `EKNavMeshBaker`) — it marks *Exiled Kingdoms*, the
  inspiration game. `DiscoverEnglandSetup.cs` keeps its filename too; renaming a `.cs` moves its
  `.meta`, which is the one thing here that can mint a fresh GUID.

→ [docs/plans/NAME_UNIFICATION_PLAN.md](docs/plans/NAME_UNIFICATION_PLAN.md)

**Also outstanding — four more interior shells for the vape arc, hand-authored YAML.** Committed
2026-08-16. `Abandoned_Bus_Station`, `Mosley_Mansion`, `DP_Academy` and `Abandoned_Church` — each
cloned byte-for-byte from the `Quidland` shell (floor + MeshCollider, four walls, a
`RuntimeNavMeshBaker`, one id-less `PlayerSpawn`), differing only in `m_Name`, `ChunkName`,
`Coordinates` (the `-2` interior column, Y −8…−11), and fresh file GUIDs. All four are appended to
`MapChunkRegistry`, which now lists **seventeen** chunks.

- ⚠️ **Eight `.asset`/`.prefab` files and their eight `.meta` files were written by hand** — no Unity
  was available, so every GUID was assigned by a script. *Open each `*_Prefab` once and confirm Unity
  accepts it rather than reimporting:* one root with a `RuntimeNavMeshBaker`, six children, lit floor,
  no console error. `--check-dangling` was clean (exit 0) — proves the GUIDs resolve, **nothing about
  whether the YAML parses**.
- ⚠️ **The four `ChunkName` values are save keys the instant a save is made inside one.** Nothing has
  saved yet, so renaming is still free. Guide: [docs/plans/VAPE_ARC_BUILD_GUIDE.md](docs/plans/VAPE_ARC_BUILD_GUIDE.md).
- **These are the arc's church and bus-station interiors** (models `abandoned+church+3d+model.glb`
  and `bus+station+3d+model.glb` are imported and want dropping in); `Mosley_Mansion` and `DP_Academy`
  are built ahead of need and not required by the current arc. All are bare `mat_dungeon_*` boxes with
  no doors — wiring is a `Tools → Place → Portal Placement` run against `Home_London_Data`.

**Also outstanding — a door no longer launders the wanted level.** Committed 2026-08-15, never
compiled:

- **`WantedManager.OnChunkTransition` gained a third parameter**, `ChunkTravelKind`, and only
  `EdgeCrossing` can now clear `CurrentKnives`. Before this, every interior and dungeon carried
  `IsCity: 0` and was reached by portal, so the first door wired to one would have let the player
  rob London, step into a shop, and step back out clean — with a police cooldown on London as a
  bonus. It was never live: no `DungeonPortal` is placed anywhere (GUID scan, 2026-08-15).
- ⚠️ **The parameter is required, with no default, on purpose.** An eighth transition path that
  notifies the wanted system must state its kind rather than inherit one. Both existing callers are
  in `ChunkManager`: `TransitionToChunkRoutine` sends `EdgeCrossing`, `TravelRoutine` sends
  `Portal`.
- **`ChunkTravelKind` is declared beside `Direction` in `ChunkManager.cs`** rather than in its own
  file, so no `.meta` had to be hand-authored. It is **not serialized anywhere** — a method
  parameter only — so the append-only enum rule in §3 does not bind it.
- **No asset, prefab or scene file changed**, and no save key is involved. Nothing to author and
  nothing to tick; the rule is behavioural, which is the point — a per-chunk `IsInterior` flag would
  have needed remembering on every future interior, the way `IsPolice` still needs remembering on
  five police prefabs.
- *Check, once a first door is authored:* commit a crime in London, step through the door, and check
  the knives readout **does not** drop and the console logs "Slipped indoors…". Then walk out to
  `North_Wasteland` over the chunk edge and check it **does** clear and logs "Evaded Police". Both
  need a `DungeonPortal` that does not exist yet, so neither can be run today.
- **Untouched next door:** the city lockout is only ever consulted by `ChunkManager.OnPlayerHitEdge`,
  never by `TravelRoutine`, so a portal leading *into* a city would walk past an active lockout.
  None exists; noted, not fixed.

**Also outstanding — the 3D container system and visit-counted respawn, none of it exercised.**
Committed 2026-08-17 on `claude/forage-asset-containers-ahhwdf`, never compiled:

- ⚠️ **A latent save-key defect is fixed, and it is the reason to check the portal path first.**
  `TravelRoutine` instantiates the destination *before* assigning `CurrentChunkData`, so anything
  resolving its own chunk in `Awake` got the chunk the player just left. `SpriteContainer` did
  exactly that. `ChunkManager.ContentChunkName` (preferring the new `ChunkBeingBuilt`) is now what
  content asks. *Loot a `Fixed` container reached **by portal**, quit, reload, and check it is still
  empty; then read `LootedContainers` in `savegame.json` and confirm the id names the destination
  chunk, not the origin.* Nothing logs if this is wrong.
- ⚠️ **`SpriteContainer.Respawning` changed meaning.** It used to refill on every chunk entry and
  save nothing; it now sits out `RespawnVisits` entries like the new component. `RespawnVisits` was
  **appended**, so an existing asset reads it as `0`, not as the initializer — both components treat
  `<= 0` as "use the default (3)". `Container_Respawning.prefab` was given the key explicitly.
  Neither container prefab is placed in any chunk, so no save is affected.
- **`SaveData.ContainerCooldowns` is appended.** *Load a save made before today and check it arrives
  with no error and every container fresh.* `BeginNewGame` clears the table — *loot a Respawning
  container, return to the title screen **without quitting**, start a New Game, and check it is
  full.* That clear fails silently.
- ⚠️ **Only the edge crossing and the portal tick a visit**; the other five instantiate paths do not,
  and `LoadWorld` especially must not — a reload that advanced cooldowns would make reload-spam the
  fastest way to farm. The table lives in `ChunkManager`. *Loot a Respawning container, save, quit,
  reload twice, and check it is still empty.*
- **`WorldContainer` and `Tools → Place → Container Placement` are new**, and their two `.meta`
  files plus three `LootBand_*.asset` metas were hand-authored. *Confirm on first open that Unity
  accepts all five rather than minting fresh GUIDs.* `--check-dangling` cannot speak to this here:
  it exits **2, "nothing was verified"**, because `Library/PackageCache` is absent.
- ⚠️ **`WorldContainer.SaveId` is why the component is safe on a child object.** Every container
  child the tool makes is called `Container`, so without an explicit id ten of them would share one
  save key and looting one would empty all ten. The tool uniquifies it against `SpriteContainer`
  too — the two share one key space and **neither warns across the other**. *Force a duplicate and
  check Validate All Containers names it.*
- **`WorldContainer.ContainerMode` and `TrapType` are serialized by integer index** and are frozen
  by the first authored container. No container is placed yet, so this is still the free moment.
- **The trap, lock and quest-gate fields are declared and inert.** Every tooltip opens with
  "NOT WIRED" and the validator reports any that are set. Nothing reads them.
- **No container is placed anywhere, and none of the three 3D models exists yet** — the bush, the
  vending machine and the bus wreckage still have to be made and imported. Until then the tool can
  only be exercised against placeholder geometry.
- **The three forage items were retuned, ids untouched.** Barnacles and fungus are now Junk (sell
  to the fisherman); blueberries heal 5 HP / 8 mana. ⚠️ Their `ItemID`s appear as literals in three
  `.quest` files and `Import Quests` is an owed run — renaming one would make the importer write
  `{fileID: 0}` into a Collect stage with **nothing logged**.

→ [docs/plans/CONTAINER_SYSTEM_PLAN.md](docs/plans/CONTAINER_SYSTEM_PLAN.md) §6 for the full routes.

**Also outstanding — the mobile performance pass, none of it exercised.** Landed on `main`, never
compiled:

- **Two runtime scripts and one editor script are new, and their `.meta` files were hand-authored**
  with fresh GUIDs — no Unity was available to generate them. *Confirm on first open that Unity
  accepts them rather than minting new ones,* which would silently break nothing yet but is worth
  knowing either way.
- **`Tools → Art → Apply Mobile Texture Settings` has never been run.** Creating the tool
  changed no texture. Run the Dry Run first and confirm the sprite cast under
  `Assets/Art/Generated/` never appears in the applied list, then run it for real — expect ~50-60
  `.meta` files to change. *Check the Animated Chest afterward in `c.unity` at normal camera
  distance* — its three TGAs should have gone from ~2048² uncompressed to 512² ASTC.
- ⚠️ **`GraphicsPrefs.Apply()` re-applies the shadow override after `SetQualityLevel`, on
  purpose** — `SetQualityLevel` overwrites `QualitySettings.shadows` as a side effect, so doing it
  in the other order would silently revert a disabled shadow setting the next time quality changes.
  *Turn Shadows OFF in the new settings window, then cycle Quality, and check shadows stay off.*
- **The settings window has never been opened.** *Check `Settings` appears directly above `Quit`
  on the title screen, that opening and closing it twice doesn't leave the game frozen (a
  `PauseManager` push/pop imbalance), and that a chosen quality level survives a Play-mode
  stop/start* — that last one is the only proof the boot hook actually fires.
- **Android is still ARMv7-only with no scripting backend set** (falls through to Mono) — the
  project cannot currently publish to the Play Store, independent of this pass. Not scriptable;
  see [docs/plans/MOBILE_PERFORMANCE_PASS.md](docs/plans/MOBILE_PERFORMANCE_PASS.md) §10.3 check 9
  for the Project Settings route.

→ [docs/plans/MOBILE_PERFORMANCE_PASS.md](docs/plans/MOBILE_PERFORMANCE_PASS.md) §10.3 for the full
check list.

**Also outstanding — merchant stores and the equipment thread, none of it exercised.** Committed
2026-08-12 on `codex/merchant-store-screens`, not yet pushed, never compiled:

- **Three merchants** (Roaming Pharmacist, F.U. Sports, Quidland) with Buy/Sell catalogues, a Win95
  shop window (`MerchantUI`) and a `MerchantValidator`. A `DialogueChoice` now carries an optional
  `Merchant` + `MerchantAction`; picking it closes the conversation and opens the shop. ⚠️ **The
  shop's pause is released before the merchant window takes its own** — closing the conversation
  first, then `MerchantUI.Show` — so a wrong order leaves the world one `PauseManager.Push` ahead
  when the shop closes. *Open a clerk conversation, pick Buy, and check the shop opens and closes
  without freezing the game.*
- **Fifteen new tradeable items with icons.** Existing items gained `Value`/`Tradeable`. *Buy one
  and check pounds drop and it enters the bag; try to sell a `Tradeable: 0` item and check it
  cannot be listed.* £ glyph caveat (§5 item 9) applies to the price readouts.
- **The equipment/paper-doll thread the store needs rode in on the same commit** (no separate
  equipment commit). `ItemData` gained flat equip bonuses (`MeleeBonus`, poison resistance) and
  `IsEquippable`; `PlayerSession` sums equipped contributions; `CombatController` adds
  `TotalAttackBonus()` to the swing; the paper-doll slots were rebuilt
  (`InventoryWin95Builder`/`EquipmentSlotMap`/`InventoryController`); loot rows now show the item
  icon (`LootMenuUI`/`SpriteContainer`). *Equip a weapon and check the melee number rises by its
  bonus; equip armour and check incoming hits drop.*
- **The exercise rig is the all-items test container** (`Container_AllItems_Test`, placed in
  `Home_London_Prefab`) — see the art/tooling commit. Nothing has been placed or played yet.

**Also outstanding — the quest pipeline, Phase 0 and Phase 1, none of it exercised.** Committed
2026-08-12 on `codex/merchant-store-screens`, not yet pushed, never compiled:

- **Phase 0 (own commit): the multi-quest foundation.** `QuestConditionWatcher` now binds EVERY
  active quest, each with its own `QuestBinding`, instead of only the first; `QuestManager` gained
  a player-chosen `FocusedQuestId` (auto-focused on a new grant; stale/none falls back to the first
  active quest), the tracker shows it and the journal has a per-row FOCUS button. *Grant two quests
  and check both advance while only the focused one shows in the tracker, and that the journal's
  FOCUS button switches it.*
- ⚠️ **`FocusedQuestId` is appended to `SaveData`** (append-only, no migration — a pre-focus save
  reads it back as null and the tracker falls back to the first active quest). *Load a save made
  before today and check it arrives with no error and a sensible tracker.* `GameFlowController`
  restores and revalidates the focus after `RestoreQuests`.
- **Quest-gated dialogue choices.** `DialogueChoice.QuestGate` + `MeetsQuestGate` hide (not grey) a
  choice whose quest is not in the chosen state, so a gated branch never leaks a quest's existence;
  `DialogueManager` renumbers the shown choices and keeps the escape search in step. *Author a
  gated choice and check it appears only once its quest reaches the right state.*
- **Phase 1: the plain-text `.quest` pipeline.** `QuestTextImporter` turns a `.quest` file into a
  `QuestDefinition`; `QuestContentValidator` checks it; `QUEST_TEXT_FORMAT.md` and `_template.quest`
  are the contract. *Run the importer on `_template.quest` from the menu and check it produces a
  `QuestDefinition` without errors.* Editor tooling — it has generated nothing yet.
- **`Tools/check_quest_phase0.py` passes its brace-balance scan.** That is NOT a compile (§5) — it
  only rules out a truncated edit. No `.quest` has been imported and no `QuestDefinition` exists to
  exercise the watcher or focus.

**The companion system — ALEX has been played, and works.** On `main` (`ab2d6c5`, namespaced in
`947ded5`). ✅ **Exercised in an editor session on 2026-08-16**: Alex was recruited and fought
alongside the player against a placed `Enemy_Spicehead`, and the owner reports following, targeting
and combat all good. That is the first time any of C0–C3 has run.

- **Data-driven companions.** `CompanionDefinition`/`CompanionDatabase` describe them;
  `CompanionAI` is the runtime follower/combatant; `CompanionManager` and `CompanionHomePresence`
  own the lifecycle; `CompanionHUDUI` draws the bar. `EnemyAI` exposes `AggroTarget` so a companion
  targets only hostiles already fighting the player, and nothing else.
- **`Companion_alex.asset` is the one authored definition**, in `Resources/Companions/`. ⚠️ **`Id:
  alex` is a save key** — it is what the save resolves the hired companion through, and it must
  also match the `PlacementPreset.QuestKey` used as his home anchor. Do not rename it.
- ⚠️ **Alex's heal was rebuilt on 2026-08-16 and has NEVER been compiled or played.** It was
  previously single-target and gated on `_target == null`, so it **only ever fired out of combat** —
  which is why it was never seen. It now heals the player *and* Alex for `HealAmount` each, mirroring
  the player's own `Spell_healing_aura`, and the tick no longer gates it on being out of combat.
  Retuned on the asset: `HealAmount` 18 → **12**, `HealCooldown` 20 → **35**,
  `HealPlayerPriorityFraction` 0.4 → **0.5**. The numbers are deliberately weaker and slower than the
  player's own aura (35 each, 30 s) **because Alex's costs no mana and mana no longer regenerates** —
  the player's aura is hard-limited by a resource, Alex's is free forever. *Take a fight below half
  health and check the combat log reads "Alex restores 12 health.", that both bars move, and that it
  cannot repeat inside 35 s.*
- **`HealPlayerPriorityFraction` now gates the whole cast**, not just player priority — either party
  at or below it triggers one, and out of combat any missing health does. The field was
  **deliberately not renamed**: renaming a public serialized field drops its value everywhere without
  `[FormerlySerializedAs]`. The name is stale; the data is intact.
- **Still unexercised:** the HUD bar, dismissal, the home presence, and death/downed handling. C4/C6
  are partial and C5/C7 outstanding per the plan.

→ [docs/plans/QUEST_PIPELINE_PLAN.md](docs/plans/QUEST_PIPELINE_PLAN.md) and
[docs/plans/COMPANION_PIPELINE_PLAN.md](docs/plans/COMPANION_PIPELINE_PLAN.md) for the phase gates.

---

## 6. Working agreement

Multi-agent workflow: **plan → implement → review → merge.** Three agents in `.claude/agents/`,
invoked by name.

| Agent | Role |
|---|---|
| `architect` | Scopes, produces the plan and mapping table, flags structural risk. **Never edits code.** |
| `implementer` | Works strictly from the plan. Small single-concern commits. No scope improvisation. |
| `reviewer` | Reviews the diff against the plan, hunting silent failure modes — not style. |

Typical use: *"use the architect subagent to plan X"* → approve → *"use the implementer subagent to
execute it"* → *"use the reviewer subagent to review the diff against the plan"*.

**Skip the ceremony for genuinely small, low-risk changes.** It exists for anything touching §3.

The `model:` frontmatter takes an **exact model id**, not the `opus`/`sonnet` tier alias the `Agent`
tool's own parameter is limited to. ⚠️ An exact id launches without error — that proves the launch
path accepts it, **not** that the named model served the request. There is no way from inside a
session to confirm which model ran a subagent, so never report a pin as "working" beyond that.

---

## 7. Documentation rules

- **Each operational fact has one canonical owner** (the table in §4). A subsystem change updates
  that one reference, not four files. Critical invariants may be repeated in §3 as short
  guardrails, because a reference is not guaranteed to be loaded.
- **Replace a stale statement — never strike it through and correct it beside itself.** The old
  wording is what a reader carries away. Git holds the history.
- **Do not put branch history, PR numbers or completed bug postmortems in a bootloader.** Git
  already has them, in more detail and better indexed.
- **Volatile snapshots are dated and archived**, not nursed into looking current.
- **"What's next" belongs in `docs/plans/`**, never here.
- **Every reference carries a verification header.** If you change what a reference describes,
  update its header — including downgrading its scope when you could not verify.
