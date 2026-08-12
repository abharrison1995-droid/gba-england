# CLAUDE.md — GBH: England

**This file is a bootloader, not a manual.** It holds project identity, the rules that must never
be missed, and a routing table. Detail lives in `docs/`, loaded on demand.

**Read [docs/README.md](docs/README.md) to find what your task needs. Never read all of `docs/`.**

---

## 1. What this project is

A Unity **mobile RPG**, working title **Exiled Alvaston** (`ProjectSettings` → `productName`),
displayed to the player as **GBH: England** (`EKVibe.DisplayTitle`).

Set in a hostile modern Britain, with magic played straight. A GTA-like consequence layer — wanted
level, police, stealth, pickpocketing, vehicle theft — sits on top of a classic RPG core.

Three names are live and **deliberately not unified**: `Exiled Alvaston` (product name and C#
namespace), `GBH: England` (display title), and `EK*` prefixes referring to *Exiled Kingdoms*, the
inspiration game. `Discover England` survives only as the name of one editor tool.

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
  Scripts/          # runtime code, namespace ExiledAlvaston.<Folder>
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

- **Namespaces mirror folders**: `ExiledAlvaston.World`, `ExiledAlvaston.Combat`. Keep it that way.
- **Public fields, PascalCase**, for anything Unity serializes (`CurrentKnives`, `ChunkPrefab`).
- **Private fields `_camelCase`** (`_isTransitioning`, `_hitThisSwing`).
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`. Access pattern
  is `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Scripts/Vibe/EKVibe.cs`) — colours, sizes, camera,
  `ChunkSize`, `CharacterHeight`. Prefer adding there over new magic numbers.
- **ScriptableObject menu path**: `ExiledAlvaston/Data/...`
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
- **Enums are serialized by integer index. Always append.** Fifteen are live.
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
- ⚠️ **A chunk root cannot be suspended with `SetActive(false)`.** It permanently blinds every
  `EnemyAI`, leaks a registered NavMesh, strands two tutorial singletons and leaves scene-root
  nameplates visible. Chunks are only ever destroyed.

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
| Quests, quest conditions, dialogue graphs | [docs/reference/QUESTS_AND_DIALOGUE.md](docs/reference/QUESTS_AND_DIALOGUE.md) |
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
    edge; reload → traffic fresh, stolen car gone. ⚠️ **The FU Sports model is a missing nested
    prefab in `Home_London_Prefab`** after the model reorganisation — re-point it in Prefab Mode,
    never by hand-editing the prefab YAML.

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
  owner authors it: Create → `ExiledAlvaston/Data/Perk`, into a `Resources/Perks` folder, one
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
