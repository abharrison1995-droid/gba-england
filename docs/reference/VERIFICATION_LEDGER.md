# Verification ledger — what's never been seen by a compiler or an editor

**Last verified against:** `main` @ 2026-08-20, reconciled against `CLAUDE.md` §5 and against the
prefab/asset YAML on disk. Fight Pit entry added 2026-08-21; player special attacks
added 2026-08-24 from branch `feat/player-special-attacks`; chunk ground/road repair added
2026-08-25.

**This file is the sole canonical owner of verification status.**

*Why this exists*: there is no C# compiler, no Unity, and no test framework in the agent
environment, so this file is the honest record of what's landed on `main` but not yet exercised.

**Read this before claiming a feature works, or before touching one of the systems below.** Not a
routine read — CLAUDE.md's own routing table (§4) still tells you which reference doc a task
actually needs; open this one when you're about to report on verification status, or about to
touch something listed here.

**Maintenance rule, unchanged from before the move: delete an item the moment it's confirmed.**
Don't leave it hedged, and don't let a confirmation turn into a permanent "it works" essay — one
line ("✅ confirmed <date>: <what was seen>") and then delete it next pass. This file grows every
time something lands; it only shrinks when someone opens Unity.

---

## Compile checkpoints

The project is known to have compiled — i.e. `Assembly-CSharp` and the editor assembly built — as
of these points, each proven by an editor tool running successfully that day (an editor tool can't
load unless its dependencies compiled). **A compile checkpoint proves the files changed up to that
point compile. It proves nothing about their behaviour.**

- **2026-08-09**: `Tools → Art → Import Generated Art` ran. Clears everything up to and including
  the mobile performance pass, `CombatController`, `ArtImportTool`.
- **2026-08-16**: `Tools → Content → Import Quests` and `Build Enemies From Generated Art` ran,
  writing 7 `QuestDefinition`s, 2 `DialogueData` assets, `Enemy_UnderHoused.prefab`. Clears the
  147-file `GBHEngland` namespace rename.
- **2026-08-17**: A full `Import Quests` run wrote all ten `QuestDefinition`s and rebuilt every
  generated `DialogueData`. Also **behaviourally confirms** the `QuestTextImporter.cs`
  case-sensitivity fix (see below) — `Preset_CouncillorMosley` / `Preset_Scrapman` round-tripped
  their `Conversation` GUIDs unchanged, `Preset_Alex` / `Preset_MadFisherman` resolved fresh ones.

## Confirmed and closed

- **Pounds rename.** `Preset_Stabmeister.asset` round-tripped `PickpocketMinPounds`/`MaxPounds`
  through `[FormerlySerializedAs]` on 2026-08-09. The remaining 24 `Preset_*.asset` files convert
  the same way on next touch. Nothing to do.
- **`QuestTextImporter` case-collision fix.** Proven by the 2026-08-17 full import (see above).
  Still open: a *deliberate* new case-collision (`DIALOGUE ralph` targeting `Dialogue_Ralph.asset`
  / `Preset_Ralph.Conversation`) hasn't been tried, and neither has a forced validation error to
  confirm the failure path logs rather than throws.
- **The companion system (Alex).** ✅ confirmed 2026-08-16: recruited and fought a placed
  `Enemy_Spicehead` in an editor session — following, targeting and combat all good. His rebuilt
  heal postdates that session and is still open — see Companions below.
- **`IsPolice` on the police prefabs.** ✅ confirmed 2026-08-20: all five `Police_*` prefabs carry
  `IsPolice: 1` (commit `fb5f514`) — `Police_ArmedResponse`, `Police_Bobby`, `Police_OccultAgent`,
  `Police_OccultCommander`, `Police_PCSO`. Still to check in Play mode: die to a police officer and
  confirm arrest fires instead of death.
- **Name unification namespace rename.** ✅ confirmed 2026-08-16: the 147-file `GBHEngland` rename
  compiles. Its behaviour is unexercised — see *Name unification and product identity* below.

## Open — grouped by system

### Actors, art, sizing
- **`UIManager.EnsureDedicatedTrack`** wraps a bar fill in its own parent when the scene doesn't
  give it one — check the concealment/mana overlap is actually fixed, and that the concealment bar
  lands somewhere sane (it's been stretched across the whole cluster, so its real position is
  unknown). Its follow-on bug (bars capping at their first-paint fraction) was fixed in `8d4b60c`
  by guarding on `parent.name.EndsWith("Track")`. *Still to check in an editor: load a save at low
  health and confirm the bar reads its real fraction, not capped at a third.*
- **Actor heights** (+0.2: player 1.8, NPC 1.55, child 1.3) with matched colliders/agents/nameplates.
  Check nobody's feet are underground, no nameplate sits on a head.
- **`EnemyAI.Awake`** reads `WorldActorVisual.Height` instead of hardcoding 1.35. Check enemies path
  around buildings, not through them (needs a NavMesh bake after collision).
- **Six enemy prefabs never seen in play**: Neek, OG, Roadman, Spicehead, Tainted, Tortured Neek.
  Tortured Neek is expected to slide/have no death pose — art gap (idle sheet only), not a defect.
- **`murtaugh_Controller`** is hand-authored YAML, verified only structurally. Check he animates
  while roaming instead of sliding; if Unity rejects it, re-stage from `art_incoming/processed/`.
- **Eleven sheets mirrored to face camera-right** by `Tools/flip_sheets.py` (no GUID/clip/controller
  touched): `murtaugh_walk`, `neek_hurt`, `og_hurt`, `police_pcso_walk`, `roadman_death`,
  `spicehead_hurt`, `spicehead_walk`, all four villager walks. Facing was called by eye. Check each
  plays facing right and cycles forward. Undo a wrong call: `python Tools/flip_sheets.py --force <name>`.
  `player_stabmeister_walk` was flipped too but is still in `art_incoming/`, never imported.
- **The cast is uniformly 65 px** as of 2026-08-08. Every character sidecar declares
  `worldHeight: 1.35`, which imports at 65 px cells. `sheet_char_player_mrhood_idle` and
  `sheet_char_player_stabmeister_idle` were the last two on disk at 74; the importer re-did them
  in place, **GUIDs intact**, and both measure 65 px. Not looked at in an editor since.
- ⚠️ **`ART_PIPELINE.md` still tells the art agent adults are 1.55**, so the **next delivered batch
  will arrive at the wrong density again** and need the same correction. Whether the contract or
  the cast is the thing to change is the owner's call and has not been made — undecided, not a bug.
- **Seven sprites in `c.unity` point at three missing textures** (three `Visual` SpriteRenderers on
  one, three on another, one on a third) — old, listed in `KNOWN_DANGLING` in
  `Tools/asset_reachability.py`. Fix: reassign each in the Inspector, delete its `KNOWN_DANGLING`
  line. ✅ **The PCSO's `WorldActorVisual.ActorSprite` is no longer one of them** — confirmed
  2026-08-20: `c.unity` line 148659 now resolves to `sheet_char_police_pcso_idle`, and its GUID is
  not in `KNOWN_DANGLING`. Fixed at some point without a log entry; caught by
  `python Tools/asset_reachability.py --check-dangling`, which reports exactly 3 known GUIDs, not 4.
- **£ may not render.** `EKVibe.FormatPounds` emits U+00A3; TMP's default static atlas is often
  ASCII-only. Check the bag readout and the pickpocket toast. Fix: TMP font asset → add £ to
  character set + regenerate, or switch Atlas Population Mode to Dynamic.
- **The importer's slicing moved to `ISpriteEditorDataProvider`** (`ArtImportTool.cs`, needs
  `using UnityEditor.U2D.Sprites;` — confirmed resolvable, `Unity.2D.Sprite.Editor.asmdef` is
  auto-referenced). Fixes a real bug: growing a sheet's frame count used to assign new frames
  `fileID: 0` (caused the 2026-08-09 player-walk flicker, hand-repaired in `fefe311`). New frames now
  get an id from their GUID; existing frame names keep their old id, so already-repaired sheets don't
  move again. ⚠️ Slicing must run **after** import settings are set and **before** `SaveAndReimport`
  — the captured `spriteImportMode` branches on that order, and getting it wrong silently no-ops
  (no throw, no warning). `VerifySliced` now also checks each sub-sprite's local file id is non-zero
  and unique, so this can't be silent again. Check: re-import one pair from
  `art_incoming/processed/`, expect no "Identifier uniqueness violation", no new Animator
  transitions, `0 duplicate transition(s) removed` (also settles reimport idempotency, still unproven
  otherwise).

### Chunk placement

Landed 2026-08-25, unseen by an editor.

- **Three placeholder chunks deleted** — North Wasteland, West Canal, East Retail Park, with their
  prefabs and their `WikiEntry_*` assets. All three were unreachable (nothing linked back to them),
  and a wiki entry unlocks only by entering its `LinkedChunk`, so no save can hold those `EntryID`s.
  Their entries were `Entry not yet written.` placeholders. Removed from `ChunkManager.AllChunks` in
  `c.unity` and from `MapChunkRegistry` as well; `--check-dangling` is clean. *If a save somehow
  names one as the current chunk it will not resolve — none should exist, but it is the one way this
  could bite.*
- **The eleven interiors moved from the `x = -3` column to `y = -99`, `x = 1..11`.** Nothing in
  travel reads `Coordinates`, so doors and portals are unaffected by construction — but *check one
  interior still opens from its door*, because that claim is read from the code, not run.
- **`DiscoverEnglandSetup` was writing `manor.Coordinates = (-1, 0)`** — Barren Lands' cell — while
  the asset itself said `(-1, -99)`. Running that Danger Zone tool would have dropped the tutorial
  dungeon onto a real chunk. Now `(-1, -99)`, matching the asset. Uncompiled.

### Chunk grounds and roads

Landed 2026-08-25. Ten chunk prefabs edited as YAML in place — no `.meta` touched, no GUID minted
for anything that already existed, round-trip proven byte-identical on all 27 chunk prefabs before
any edit, and `asset_reachability --check-dangling` reports the same known set afterwards as
before. None of it has been opened in Unity.

- ⚠️ **The magenta diagnosis is inferred, not proven.** Every road and track `MeshRenderer` in the
  project was a truncated ten-line stub where Unity's own writer emits forty-two, missing
  `m_StaticBatchInfo`, `m_CastShadows`, `m_LightProbeUsage` and `m_RenderingLayerMask`. All sixteen
  were roads, and the `Ground` beside them carrying the **same material** rendered correctly, which
  rules the material out and leaves the renderer as the only difference. Which missing field
  actually triggers the error shader was never established. They are now full blocks. *Check the
  roads render; if any is still magenta the cause is something else entirely and this whole entry
  is wrong.*
- ⚠️ **Road texture orientation is the one guess in the change.** Every strip is rotated so its
  tarmac runs along local **+X**, on the assumption that a built-in Cube's top face maps U→X and
  V→Z. If that is backwards the roads will read sideways — bands across the carriageway instead of
  along it. *One-line fix if so: swap the tiling on `Road_Asphalt` from `22 x 1` to `1 x 22` and
  drop the 90° yaw from the north-south strips.*
- **Three of those four grounds are textured now** (Band 13 delivered 2026-08-25) and their
  tints are back to white. `Track_Dirt` is **still flat colour** and still carries its tint —
  `track_dirt_strip` was never delivered, so The Peaks and Knob Moor have plain brown tracks.
  **Reset that tint to white when it lands**, or it multiplies against the texture.
- **Ground tiling is 44 on the three new materials, 80 on the older `Grass.mat`.** Not an
  oversight — 80 minified the new textures into flat noise at the real camera distance. If the
  moor and the grass ever need to read as the same family, that difference is why they do not.
- ⚠️ **The arena's 1 m walls read the top quarter of the tall wall's texture** through
  `mat_arena_regal_wall_low` at tiling `8 x 0.25`, offset `0 x 0.75`. Simulated before landing and
  it comes out right way up — cornice, gold band, marble — but a **UV offset on a cube face is
  still the single most likely thing here to be wrong in Unity**. *Check Wall_South and Wall_East
  show a gold-capped parapet and not a slice of skirting.* If it is inverted the fix is
  `offset 0 x 0` with tiling `8 x 0.25`; if it is upside down the texture is being sampled from
  the bottom and the whole approach needs a second wall asset instead.
- **The arena has never been entered.** Its floor and walls had no texture at all until
  2026-08-25, so nothing about how that room reads has ever been seen.
- **Brighton and West York gained an `Intersection_Centre`** they did not have, at `y=0.06`,
  matching what the generator's own `Crossroad_Intersection` style produces. Without it the two
  strips are coplanar where they cross. *Check the junction does not z-fight.*
- **`ChunkPrefabGeneratorTool`'s dead `Ground UV Tiling` field is gone**, replaced by a read-out of
  what the assigned material actually does. Uncompiled — the balance scan is not a compile. *Opening
  `Tools → World → Generate Chunk Prefab` at all proves the editor assembly built.*

### Wallet, quests, dialogue
- **The wallet has never run.** Pickpocket a civilian, get arrested, reload a save. Check the bag
  readout tracks all three and a pre-today save loads at £0 rather than failing.
- **Blank-name fallback never run.** `PlayerSession.BeginNewGame` should turn a blank name box into
  "Vince". Start a new game leaving the box untouched, check the nameplate reads Vince.
- **The three quest fixes**, never exercised: `ClearWanted` despawning police, `StartQuest` no
  longer rewinding a mid-flight objective, the watcher claiming a reward only after paying it. Needs
  a `QuestDefinition` in `Resources/Quests/` and a way to grant it — the throwaway test rig was
  deleted deliberately (quests are meant to be granted in-world, never from a menu).
- **`spark_of_talent`** (the magic tutorial) was converted off bespoke code onto the `.quest`
  pipeline; `MagicTutorial.cs` is deleted. ✅ confirmed 2026-08-17: the import ran, `NPC_Daniel
  Pauls` is placed in `Home_London_Prefab` and `Preset_DanielPauls.QuestKey` is `danielpauls`. The
  quest itself is unexercised. ⚠️ Unverified Unity behaviour: whether `Awake` runs on a disabled
  component — if the panicked geezer stands still or falls through the NavMesh, that is the answer
  and `HostileAfterDialogue` must snap him to the NavMesh itself. Check both a mid-flight save and
  a completed save (completed should retro-pay 0/0, not re-pay).
- **Four London doors are authored** (2026-08-17); two lead nowhere. Church → `Abandoned_Church` and
  Station → `Abandoned_Bus_Station` have no arrival marker on the interior side — pressing USE should
  leave the player standing still with a console warning naming the chunk/id (this is the first real
  exercise of the 2026-08-09 `TravelRoutine` reorder that makes that safe — a stranded player means
  the reorder didn't take). Finish both via `Tools → Place → Portal Placement`, reusing link ids
  `Abandoned_Church_Door` / `Bus_Station_Main_Door`. `Gang_Hideout`'s interior arrival point is still
  at chunk origin and needs moving when dressed. `NPC_Ralph`/`NPC_Sanjeet` were removed from London;
  a real `DIALOGUE ralph`/`DIALOGUE sanjeet` block has since been imported, producing lowercase
  `Dialogue_ralph.asset`/`Dialogue_sanjeet.asset` with no collision and no nulled preset — the
  collision case above is answered by real use, not just a deliberate test.
- **The duplicate Councillor Mosley is gone** (2026-08-18). `Home_London_Prefab` held two identical
  `NPC_Councillor Mosley` stamps under `NPCs`; the one in the crowd at `(-141.2, -2.5, 4.0)` was
  removed agent-side with Unity closed — 8 YAML documents, a pure 140-line deletion with no
  reformatting churn, `--check-dangling` clean. The survivor is at `(-163.1, -2.5, -28.2)`.
  *Confirm on first open that exactly one Mosley stands in London and he still resolves his
  conversation.* Neither was a nested prefab instance, so the reason one "couldn't be deleted" was
  almost certainly a Play-mode edit being discarded — chunk contents live in the chunk prefab, not
  in `c.unity`.
- **Six empty interior shells** (`Quidland`, `FU_Sports`, `City_Hall`, `Police_Station`,
  `Gang_Hideout`, `The_Winchester`) and **four more for the vape arc** (`Abandoned_Bus_Station`,
  `Mosley_Mansion`, `DP_Academy`, `Abandoned_Church`) are hand-authored YAML — every GUID assigned
  without Unity available. Open each prefab once, confirm Unity accepts it (one root with
  `RuntimeNavMeshBaker`, six children, lit floor, no console error) rather than reimporting it into
  something different. ⚠️ Their `ChunkName` values become save keys the instant anyone saves inside
  one — free to rename only until then. `The_Winchester` already has a working
  `PubInteractable`/`Pub_TheWinchester.prefab` flow but isn't placed in any chunk; whether it should
  sit behind a door is an open design question. None of the five exterior building models
  (City Hall, Quidland, F.U. Sports, Police Station, Gang Hideout) exist yet — not a blocker for the
  interiors, but the blocker for a satisfying test.
- **Linked location portals**: no `DungeonPortal` existed anywhere until the four London doors above,
  so this is now partially exercised (see above) but the rest isn't: `DungeonPortal.TargetSpawnPointId`
  arrival-facing via `CombatController.FaceTowards`, refusing while mounted ("Get off the vehicle
  first"), `Awake` no longer overwriting an authored `InteractRange`, the hand-authored
  `MapChunkRegistry.asset` (confirm Unity accepts it rather than minting new GUIDs), and
  `Tools → Place → Portal Placement`'s validator (author one deliberately broken pair, confirm each
  rule fires — the case it was written for, a self-targeting `Portal_Home_London`, no longer exists
  in the project). Scoped out on purpose: `TravelRoutine` still destroys/re-instantiates on return,
  so exact interior state isn't preserved yet (see `BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md`)
  — don't ship reward-bearing interiors until that lands.
- **A door no longer launders the wanted level.** `WantedManager.OnChunkTransition` takes a required
  `ChunkTravelKind`; only `EdgeCrossing` clears knives. Check, now that real doors exist: commit a
  crime in London, step through a door, knives should **not** drop (console: "Slipped indoors…");
  walk out over a chunk edge, knives **should** clear ("Evaded Police"). Untouched: a portal leading
  *into* a city walks past an active lockout, since only `OnPlayerHitEdge` consults it.
- **Knives now decay over time** (2026-08-18, never compiled). `WantedManager.Update()` drops one
  Knife every `KnifeDecayInterval` seconds (60s default) while `CurrentKnives > 0`;
  `SpikeKnives()` resets the timer, so a fresh offense restarts the countdown rather than letting
  an old one's fade finish it off. Check: commit one crime, wait ~60s doing nothing else, the top
  knife should dim and the HUD meter update on its own with no player input. Then check the reset:
  spike to 2, wait 40s, spike again, the fade should restart from 0 rather than firing at the
  20s-remaining mark. Flat and ungated — ticks the same whether the player is in a firefight or
  hiding in an alley; that's a placeholder simplification, not a tested design choice.
- **`HIRE: <companionId> [free]`** quest directive and Quest 8's text (committed 2026-08-17). Alex is
  now gated three ways on `rush_hour` (greeting only before, free hire during, £25 hire after) —
  confirm he can't be hired before Rush Hour completes. `Dialogue_Alex.asset` was renamed to
  lowercase and the 2026-08-17 import held it on GUID `750c809e…`; `Dialogue_Alex_Follower.asset` is
  also lowercase now, so that collision risk is resolved too. `red_star_cigarettes` (new consumable,
  no icon) needs no new code. `rush_hour.quest` is only a beginning. **East York is committed**
  (`d5bd032`) — `East_York_Data.asset`, `East_York_Prefab.prefab` and an entry in
  `MapChunkRegistry`, which now lists **19 chunks** (East York is guid
  `e819a42f6c8d4732b1154c93a027df91`). Still open: `Preset_MayorZhao.asset` exists with sprite,
  controller, speaker and a generated `Dialogue_mayorzhao`, but **Zhao is not placed in
  `East_York_Prefab`**; `ProximityDialogueTrigger.cs` exists but is **not on any prefab or in
  `c.unity`** (GUID scan, 2026-08-20); and Zhao's line still asks the pipeline to *grant* the
  cigarettes on a choice, which it cannot do — inside a choice `ITEM:` routes to
  `ParseItemRequirement`, so it is a **requirement**, not a grant. The only item payout is a quest
  `REWARD`, paid at completion.
- **Merchant stores and the equipment/paper-doll thread** (three merchants, Win95 shop window,
  fifteen tradeable items, flat equip bonuses). Check a clerk conversation → Buy opens/closes the
  shop without freezing (⚠️ the conversation's pause releases *before* the merchant window takes its
  own — wrong order leaves the world one `PauseManager.Push` ahead on close). Check buying moves
  pounds and adds to bag, a `Tradeable: 0` item can't be listed, equipping a weapon/armour changes
  the melee number / incoming damage.
- **Quest pipeline Phase 0–1**: multi-quest `QuestConditionWatcher` binding every active quest,
  `FocusedQuestId` (appended to `SaveData`, no migration — a pre-focus save should fall back to the
  first active quest without error), quest-gated dialogue choices, and the `.quest` importer/validator
  itself. `Tools/check_quest_phase0.py` passing is a brace-balance scan, not a compile.

### Containers and foraging

The 3D container system and visit-counted respawn (committed 2026-08-17), never compiled. **No
container of either kind is placed anywhere yet, and none of the three 3D models exists** — the
bush, the vending machine and the bus wreckage still have to be made and imported, so the tool can
only be exercised against placeholder geometry.

- ⚠️ **A latent save-key defect is fixed, and it is why the portal path is the first thing to
  check.** `TravelRoutine` instantiates the destination *before* assigning `CurrentChunkData`, so
  anything resolving its own chunk in `Awake` got the chunk the player just **left** —
  `SpriteContainer` did exactly that. Content now asks `ChunkManager.ContentChunkName` (which
  prefers the new `ChunkBeingBuilt`). *Loot a `Fixed` container reached **by portal**, quit, reload,
  confirm it is still empty; then read `LootedContainers` in `savegame.json` and confirm the id
  names the **destination** chunk, not the origin.* Nothing logs if this is wrong.
- ⚠️ **`WorldContainer.SaveId` is why the component is safe on a child object.** Every container
  child the placement tool makes is called `Container`, so without an explicit id ten of them would
  share one save key and looting one would empty all ten. The tool uniquifies against
  `SpriteContainer` too — the two share one key space. `ContainerIdRegistry` (2026-08-20, `fe122f0`)
  warns across both types: a `WorldContainer` and a `SpriteContainer` claiming the same id in the
  same chunk are both named in the console, whichever Awakes second. *Force a duplicate, check
  `Validate All Containers` names it, and check a cross-type collision logs the same warning.*
- ⚠️ **`WorldContainer.ContainerMode` and `TrapType` serialize by integer index** and are frozen by
  the first authored container. None is placed yet — **still the free moment**.
- ⚠️ **Only the edge crossing and the portal tick a container visit.** The other five instantiate
  paths do not, and `LoadWorld` especially **must not** — a reload that advanced cooldowns would
  make reload-spam the fastest way to farm. The table lives in `ChunkManager`. *Loot a Respawning
  container, save, quit, reload twice, confirm it is still empty.*
- ⚠️ **`SpriteContainer.Respawning` changed meaning**, and two of them are live in `c.unity`. It
  used to refill on every chunk entry and save nothing; it now sits out `RespawnVisits` entries like
  the new component. `RespawnVisits` was **appended**, so an existing asset reads it as `0` — both
  components treat `<= 0` as "use the default (3)", *not* as the field's literal initializer.
  `Container_Respawning.prefab` was given the key explicitly.
- ⚠️ **`c.unity` was hand-edited to delete two scene-root test containers.** `Container_Fixed` and
  `Container_Respawning` sat active at the scene root, in no chunk. A scene-root container is never
  destroyed and rebuilt, so its `Awake` runs once per scene load, and `Container_Respawning` would
  have started writing a cooldown that survived a restart under a save key naming a chunk it did not
  belong to. Removed on instruction — two `!u!1001` documents and their two `SceneRoots.m_Roots`
  entries, 128 deletions, no insertions. The two prefab *assets* are untouched and remain authoring
  templates. *Confirm on first open that the scene loads with exactly five roots — SYSTEM, MANAGERS,
  ACTORS, ENVIRONMENT, UI — and no console error.*
- **`SaveData.ContainerCooldowns` is appended.** *Load a save made before 2026-08-17, confirm it
  arrives with no error and every container fresh.* `BeginNewGame` clears the table — *loot a
  Respawning container, return to the title screen **without quitting**, start a New Game, confirm
  it is full.* That clear fails silently.
- **`WorldContainer` and `Tools → Place → Container Placement` are new**; their two `.meta` files
  plus three `LootBand_*.asset` metas were hand-authored. *Confirm on first open that Unity accepts
  all five rather than minting fresh GUIDs.*
- **The trap, lock and quest-gate fields are declared and inert.** Every tooltip opens with
  "NOT WIRED" and the validator reports any that are set. Nothing reads them.
- ⚠️ **The three forage items were retuned, ids untouched** — barnacles and fungus are now Junk,
  blueberries heal 5 HP / 8 mana. Their `ItemID`s appear as literals in three `.quest` files;
  renaming one would make `Import Quests` write `{fileID: 0}` into a Collect stage with **nothing
  logged**.

### Combat: dodge, knockback, perks
- **Dodge roll** (Space, 2.4m/0.40s, 14 stamina, i-frames 0.05-0.30s in, 1s cooldown) — animation
  confirmed playing (2026-08-09 import). Still open: distance matches the field, a second Space
  within a second is refused, rolling off a kerb falls rather than hovers, `Health.IsInvulnerable`
  blocks the PCSO's swing with a "Dodged!" toast and no damage, rolling breaks stealth (toast reads
  "Out of stealth.", CRO pops out, walk speed returns), the DGE button is reachable by thumb in the
  Device Simulator landscape (invisible in a 16:9 Game view; built at runtime, won't appear in
  Hierarchy until Play starts). ⚠️ `RollSpeedCurve` must integrate to exactly 1 over [0,1] — that's
  the only reason the roll travels `RollDistance`; reshaping it without preserving that decouples the
  two silently.
- **Player knockback (phase 2)**: `Enemy_OG` and `Enemy_Tainted` are authored at
  `KnockbackDistance: 2` on disk (commit `fb5f514`); police stay at 0, per the recorded decision.
  **The slide itself has never been seen in Play mode** — still to check. Check it is ~2m and
  stops at walls; a dodged hit no longer shoves (`TakeDamage` returning false gates it — "Dodged!",
  no slide); knockback wins over an in-progress roll; 0.4s recovery i-frames stop two enemies
  chain-stunning. `Health.TakeDamage` now returns `bool` — **no longer bindable in a UnityEvent
  dropdown** (Unity only lists void methods there); nothing binds it today
  (`grep -rn "m_MethodName: TakeDamage" Assets/` was empty pre-change) — re-check that grep if
  anything ever silently stops taking damage.
- **`ApplyKnockback` clears the `Hit` trigger before setting `Knockback`** so the Animator doesn't
  race between them. Check the tumble plays whole, not flickering through a Hurt frame. Knockback
  clip is 0.50s against a 0.22s slide **on purpose** — check the player can move ~0.28s before the
  tumble finishes, and walking during that window keeps it on screen (exit-time return, not a bug).
  ⚠️ Reimport idempotency for this batch is unproven — see the sprite-slicing item above.
  `knockback` is now a shape-changing action (6 frames/12fps, was 3) exempt from the standing-height
  check, same as `death`/`cycle`/`roll`.
- **Melee knockback perk (phase 4)**: `PerkEffectType.MeleeKnockback = 9`, appended, never reordered
  — first `PerkData` asset authored freezes the enum indices forever. `Perk_melee_knockback` exists
  in `Resources/Perks`, Magnitude 2m flat, not %. *Still to check: spend the point, hit something,
  confirm ~2m slide stopping at walls.* `PlayerSession.MeleeKnockbackDistance` resets in
  `RecalculateDerivedStats` step 6 — reload after
  taking the perk, shove should be the same, not doubled. A killed enemy is never shoved (gated on
  `!targetHealth.IsDead`, since `Health.Die` already disables the agent). `EnemyAI`'s three
  `SetTrigger` calls are now guarded, so an undefined `Knockback` trigger won't error (expected until
  band 10 sheets land).

- **The two player special attacks (spin and dash) have never been compiled or run.** Landed
  2026-08-24 on `feat/player-special-attacks`: the `ResolveMeleeSweep` / `ComputeMeleeDamage`
  extraction, `_hitResults` widened 32 → 64, three appended `AbilityData` fields plus the
  `SpecialAttackKind` enum, both coroutines, the `TryUseAbility` split, `ActionKind.Special`, the
  SPN and DSH buttons, and `Tools → Content → Create Special Attack Assets`. Owned by
  [PLAYER_COMBAT.md](PLAYER_COMBAT.md); the owner's step-by-step is §11 of
  [../plans/PLAYER_SPECIAL_ATTACKS_PLAN.md](../plans/PLAYER_SPECIAL_ATTACKS_PLAN.md).
  **Nothing works yet even if it compiles**: the editor tool has not been run, so
  `Special_spin.asset` / `Special_dash.asset` do not exist, and the player's `SpecialAttacks` list
  in `c.unity` is unassigned — both buttons render dimmed and do nothing until steps 2 and 6 of
  that checklist are done. Still to check, in order: the project compiles at all; the two buttons
  land where the arithmetic says (SPN −517, DSH −673, in the Device Simulator, not a 16:9 Game
  view, and they are built at runtime so they do not appear in the Hierarchy until Play starts);
  the radial sweep runs and stamina drops by the expected percent; both are refused while riding
  and both hide while driving; the dash stopping dead on the first enemy capsule reads as
  "connected" rather than "stuck" (the single most likely thing to need retuning); and
  ⚠ **dashing into a chunk edge lands the player on the arrival marker rather than sliding away
  from it** — the chunk-snapshot guard, and the one item here most worth a hand test.
  Deferred, not verifiable yet: whether `ClearAnimatorTrigger("SpecialAttack")` prevents the
  latch, which cannot be seen until a player `special` sheet exists and the importer authors a
  `Special` state. Also unproven: whether widening the overlap buffer changes anything observable
  — it only matters in a crowded, built-up chunk.
- **`RollRoutine` gained the chunk-change and pause bails** (commit `b188090`), mirroring
  `DashAttackRoutine`: the chunk identity is snapshotted before the loop and polled each step
  alongside `IsTransitioning`. Rolling into a chunk edge could previously resume the roll on the
  far side and drive the player off the arrival marker. **Unverified** — reproducing it means
  rolling into an edge trigger in the editor, which is a hand test.

### Progression, HUD, enemy levels
- **Enemy levels are authorable, and one is now authored.** `PlacementPreset.EnemyLevel`/palette
  Level field attach an `EnemyLevel` component (0 = none attached, deliberately, since level-1 isn't
  inert — it flips the nameplate badge from the prefab's "3" to "1"). `TutorialSequence.cs` sets the
  tutorial bandit's badge to Level 1 on spawn — the first real exercise of this path. *Still to
  check: stamp a second enemy from the palette at Level 4 and confirm it reads tougher.* Nameplates
  now show on aggro or within `SightRadius`, hiding a few seconds after — check one appears on
  approach, not just after first hit,
  and doesn't linger over a corpse. ⚠️ `EnemyAI` resolves its nameplate in `Start`, not `Awake` — a
  refactor moving that would cache null for the tutorial bandit (which gets `EnemyAI` added before
  `EnemyNameplate`). Every existing enemy prefab still wears a cosmetic "3" badge while actually
  level 1 (11 prefabs, `Level: 3` on disk) — will look wrong until levels are authored.
- **HUD cluster scaled 1.6× at runtime** (`EKVibe.HudClusterScale`, ceiling 1.75 before it overlaps
  the combat log), `SafeAreaFitter` added at runtime — invisible in a 16:9 Game view, needs the
  Device Simulator. Player bar's level badge should rise on dealing damage or drawing aggro, not
  only when hit.
- **The whole 2026-08-18 mobile HUD layout pass.** Every position and size below was reasoned from
  scene YAML and the 1920×1080 reference, **not measured and not seen** — no compiler and no editor
  has touched any of it. Check in **Window → General → Device Simulator**, landscape, since half of
  it is built at runtime and will not appear in the Hierarchy until Play starts.
  - **The 5-icon wanted meter** (`UIManager.EnsureWantedMeter`, top centre, 416×72 at (0,−10),
    icons 72 px on an 86 pitch). ⚠ **It does not exist until two manual steps are done**: run
    `Tools → Art → Import Generated Art`, then drag the imported
    `Assets/Art/Generated/ui/spr_ui_wanted_knife.png` onto `UIManager.WantedKnifeIcon`. Until then
    the only symptom is one console warning. Once wired: commit a crime, check knives light left to
    right and unlit ones dim rather than vanish; a pint or an arrest should blank all five.
    `WantedKnivesText` was deleted from `UIManager` — it was `{fileID: 0}`, so nothing was lost, but
    the orphan key is still in `c.unity` until Unity next re-saves the scene. **Don't hand-edit it
    out.**
  - **The combat log moved to y −144 and toasts to anchor 0.72** to clear the meter. Check a toast
    (leave a pub, or cast in a city) does not land on the log's last line.
  - **The action cluster resized**: ATK 165, USE/DGE 140, spell slots 125 on a 137 pitch, and
    `ActionButtons` is now a full stretch rather than a zero-size rect. Check nothing runs off the
    bottom or right edge, and that the top spell slot (y 626 on the reference) is still on screen.
  - **CRO moved to the left thumb**, centred above the joystick, its position **computed** from the
    joystick's live rect (`UIManager.CrouchButtonPosition`). Check it is centred over the stick and
    does not eat the stick's own touches — it is a sibling, not a child, so overlap would steal
    input. The literal fallback (120,344) is only used if `Joystick` is unwired.
  - **The LOG button moved top-left** to (16,−216), below the bars. Check it isn't under the
    portrait cluster's 1.6× scale footprint.
  - **The stamina bar pitch fix**: 36 not 28, once not twice, so HP/MP/SP sit at −22/−58/−94 and
    `TopLeftPortraitPanel` no longer grows. Check the three bars look equally spaced. ⚠ The
    inactive `ConcealmentBar` is authored at −86 and now overlaps the stamina slot — invisible
    today, a real collision the moment stealth is switched back on.
  - **The level badge z-order fix**: `PreparePlayerPortraitFrame` sends `LevelBadge` to the end of
    the sibling list because `Win95Skin.AddBevel` appends its four `Edge` strips after it. Check no
    grey bevel line crosses the badge.
  - **Five hand-edited `c.unity` RectTransform values** (badge 28→40 at (2,2), its text 18→24,
    joystick 220→280, handle 70→88, `LocationTime` y 290→500). Seven numeric lines, no GUID or
    structural change, `--check-dangling` clean before and after — but **confirm Unity opens the
    scene without complaint** rather than assuming, and check `LocationTime` at y 500 has not
    collided with anything on a shorter aspect ratio.
- **Armour is now proportional** (`EKVibe.ArmourSoftCap` 20, capped at 75% reduction) — `TestShield`'s
  Armor 4 should read ~16.7% off a hit, not a flat 4. Check with and without the shield.
- ⚠️ **Stats recompute from level+perks on every load** — baseline capture is guarded against the
  character template aliasing `RuntimeStats`; without that guard a second load in one session bakes
  growth/perks into the baseline permanently. Load the same save twice in one sitting, stats should
  read identically both times — **the failure most likely to go unnoticed**.
- **Kill XP** depends on both player damage sites now passing `gameObject` into `TakeDamage` so
  `Health.LastAttacker` is set (was always null for player hits). Kill an enemy, check XP moves off
  zero — if not, this fix didn't take and nothing will say so.
- **`EnemyLevel` scales from the prefab's level-1 baseline**, applied in `Health.Awake` before
  `CurrentHealth = MaxHealth`. Set Level 5 on an enemy, check it spawns at full (not partial) health.
- **`SaveData.TotalXP`/`FocusedQuestId`/`PerkIds` are appended, no migration.** Load a pre-today save,
  check it arrives at level 1 / first-active-quest-focused / with intact spent perks rather than
  failing. A perk id that stops resolving is deliberately **kept**, not dropped — the point stays
  spent even if its effect silently stops existing.
- **The bag readout only binds after** `Tools → UI → Rebuild Inventory Panel (Win95)` is run once
  (the HUD badge is already wired).
- **The paper doll**: equip a weapon, melee number should rise by its `Damage`; equip armour,
  incoming hits should drop by `TotalArmor` (flat, floored at 0 — a full doll may make weak enemies
  harmless; a balance question, not a bug). Check the rebuilt bag window's rail buttons, equipment
  slots and tooltip sit where they should.
- **Map of Britain / WIKIBRITAIN**: first arrival should toast, a reload shouldn't; a pre-today save
  should open a populated encyclopedia, not a toast storm — the `ContinueFromSave` backfill path is
  the most likely thing to be wrong. Check a pre-equipment save arrives with an empty doll and blank
  map instead of failing (`Equipment`/`VisitedChunks`/`UnlockedWikiEntries` are new save fields).

### Survival pressure (stamina/mana)
- ⚠️ **Mana no longer regenerates at all** — only consumables, the pub, and a heal spell that doesn't
  exist yet bring it back. Cast Spark, stand still 30s, mana should not move. `ManaRegenPerSecond` is
  deleted; don't hand-edit the scene to remove the resulting orphan key, Unity drops it on next save.
- ⚠️ **Dodge roll costs 50% of max stamina, floored** (`FloorToInt` is load-bearing — a cost above
  half the pool makes the second roll impossible). A 55 pool: 55→28→1, third roll refused. One roll
  then a refusal means the floor was lost.
- **Stamina regenerates at 5%/sec of max** (percent, not flat, so it doesn't drift with level). ~3
  pts/sec on a 55 pool: one roll back in ~10s, full in ~20s. Ticks in combat deliberately.
- **Third HUD bar (amber, stamina)** built at runtime by `UIManager.EnsureStaminaBar` — check it
  reads 55/55, sits below mana, doesn't reach the combat log or joystick, survives the Device
  Simulator landscape.
- **Concealment bar/stealth are sidelined by decision, not a bug** — inactive in `c.unity`. No gap
  is reserved for it any more: the 2026-08-18 pitch fix puts the stamina bar over the slot it was
  authored in, so the stealth pass has to place it. No save key changed in this pass; a pre-today
  save should arrive with whatever mana it held, no error, HP never at 0.

### Traffic and vehicles

**The ambient traffic and car theft work is landed and entirely unexercised** — unseen by a
compiler or an editor.

- **Four new scripts** — `TrafficRoute`, `TrafficCar`, `HotwireMenuUI`, `BuildTrafficCarPrefabTool`
  — plus edits to `EKVibe`, `VehicleData`, `VehicleController` and `WorldActorVisual`. ⚠️ **Their
  four `.meta` files were hand-authored, and rewritten byte-exact after Unity rejected the first
  pass.** *Confirm on first open that Unity accepts them rather than minting fresh GUIDs.*
- **The check list is §10.2 of
  [`TRAFFIC_AND_CAR_THEFT_PLAN.md`](../plans/TRAFFIC_AND_CAR_THEFT_PLAN.md)**: compile on open; run
  the builder tool twice (Reliant Robin common, Vauxhall Corsa better); author two routes in
  `Home_London_Prefab`; cars drive, brake, honk and resume; hotwire success → driver flees, 2
  knives, two officers, hidden rider; timeout → 1 knife, car drives off; ride across a chunk edge;
  reload → traffic fresh, stolen car gone.
- ⚠️ **The FU Sports nested prefab in `Home_London_Prefab` was re-pointed** to its
  post-reorganisation `Shops/` path (committed 2026-08-12) and **that edit has never been opened in
  an editor**. *Confirm on first open that the FU Sports building resolves rather than showing as a
  missing prefab.*
- ⚠️ **Never `SetActive(false)` a vehicle root** — `OnDisable` clears the speed multiplier, so the
  vehicle cancels its own boost the instant it is mounted. Hide `ParkedModel` instead. (Invariant,
  not a check.)

### Name unification and product identity

The 147-file `GBHEngland` rename compiles (2026-08-16 checkpoint); none of its behaviour has been
exercised.

- ⚠️ **Three `UnityEvent` bindings store the namespace as a literal string**, not as a GUID, and
  were rewritten in the same commit: `EBike.prefab` (`VehicleController`),
  `Pub_TheWinchester.prefab` (`PubInteractable`) and `c.unity` (`InventoryController`). **A miss
  fails silently with a clean console.** *Mount the e-bike, USE the Winchester, open the bag and
  click the rebuilt buttons. If one is dead, look at its `m_TargetAssemblyTypeName`, not the C#.*
- ⚠️ **`productName` is now `GBH England`** — no colon, because it becomes a real folder inside
  `persistentDataPath`. **Every save made before 2026-08-16 is orphaned**, along with the graphics
  `PlayerPrefs`. Accepted deliberately; there is no migration shim. *Play once and confirm a save
  appears under `…/LocalLow/DefaultCompany/GBH England/`. Expect graphics settings to reset once.*
- **`Create →` menus moved to `GBH England/Data/…`.** Existing assets are unaffected — `menuName`
  is not stored in the asset. *Check `Create → GBH England → Data → Item Data` still makes a working
  `ItemData`.*

### Platform/mobile
- **Mobile performance pass**: `Tools → Art → Apply Mobile Texture Settings` never run — Dry Run
  first, confirm the sprite cast under `Assets/Art/Generated/` never appears applied, then run for
  real (~50-60 `.meta` files expected to change). Check the Animated Chest's three TGAs shrink from
  ~2048² uncompressed to 512² ASTC. ⚠️ `GraphicsPrefs.Apply()` re-applies the shadow override *after*
  `SetQualityLevel` on purpose (`SetQualityLevel` overwrites `QualitySettings.shadows` as a side
  effect) — turn Shadows off, cycle Quality, shadows should stay off. Settings window never opened —
  check it sits above Quit on the title screen, doesn't freeze on repeated open/close (PauseManager
  push/pop balance), and a chosen quality level survives a Play-mode stop/start. Android is still
  ARMv7-only with no scripting backend set (falls through to Mono) — can't currently publish to Play
  Store, independent of this pass.
- **Three new hand-authored `.meta` files** (two runtime scripts, one editor script) — confirm Unity
  accepts them rather than minting new GUIDs.

### Companions
- Alex's rebuilt heal (dual-target — heals player *and* Alex 12hp each, 35s cooldown, no mana cost,
  no longer combat-gated) postdates the 2026-08-16 session that confirmed following/targeting/combat.
  Take a fight below half health, check the log reads "Alex restores 12 health.", both bars move,
  can't repeat inside 35s. Still fully unexercised: the HUD bar, dismissal, home presence,
  death/downed handling (C4/C6 partial, C5/C7 not started per `COMPANION_PIPELINE_PLAN.md`).
  `Companion_alex.asset`'s `Id: alex` is a save key and must keep matching
  `Preset_DanielPauls`-style `QuestKey` anchors — don't rename it.

### Castle Fight Arena (Fight Pit)

The whole arena loop is implemented and **never compiled or run** — `FightPitController.cs`
(652 lines: 10-round tournament, defeat interception, cash-out, return to Home_London),
`FightPitEntryCoordinator.cs`, `FightPitDialogue.cs`, `FightPitConfig.cs` (10 config-driven
rounds, first-completion bonus), save fields `PitTournamentWon` / `HighestPitRound` /
`HasPurchasedRoyalCrown`, `Castle_Fight_Arena_Data.asset`, `Castle_Fight_Arena_Prefab.prefab`, and
a `MapChunkRegistry` entry. `Home_London_Prefab` holds the placed `NPC_Prince Mandrew`.

- **The controller drives `castle_arena_quest`** via `StartQuest` / `UpdateObjective` /
  `CompleteQuest` inside the bout flow — whether re-entering the arena after a first clear freezes
  or re-opens the journal is unverified; confirm in Play mode (a repeatable tournament over a
  one-shot quest completion is the suspect path).
- **Two `Dialogue_PrinceMandrew` assets exist** — one hand-written in `Assets/Data/Dialogue/`, one
  generated in `Assets/Data/Dialogue/Generated/`. Reconcile via `Tools → Content → Import Quests`
  in the editor; do not hand-merge.
- **Mandrew art subject (`mandrew`)** has idle/walk/attack/hurt sheets and a `mandrew_Controller`;
  `Preset_PrinceMandrew` carries `Speaker`, `NpcController`, `NpcSprite` and `Conversation`.
- Confirm in Play: entry validation (wanted / mounted / companion refusals), the victory purse and
  first-completion bonus pay once, defeat/forfeit grant nothing, partial kills grant no XP/loot,
  entry vitals restore rather than full-heal, and a mid-bout quit Continues at the pre-bout Home
  London checkpoint (see `ROYAL_FIGHT_ARENA_PLAN.md` Unity verification route §1–12).
