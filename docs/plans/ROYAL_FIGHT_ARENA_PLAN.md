# Castle Fight Arena

```
Last updated:          2026-08-17 (revised plan; nothing implemented)
Verification scope:    Existing code and tracked assets were inspected on 2026-08-16/17.
                       The castle hierarchy, current transition/save paths, EnemyAI fallback,
                       Enemy_Neek loot component, kill-XP path, dialogue hooks, and registry were
                       read from the working tree. Reference integrity passed with only the
                       documented known dangling references. Nothing was compiled or run in
                       Unity; this repository has no agent-side Unity or C# test environment.
```

> **Phase 0 remains a hard gate, but the old visual test was not sufficient.** `EnemyAI` falls
> back to collision-aware transform movement when it is not on a NavMesh, so seeing two Neeks
> chase the player does **not** prove that `RuntimeNavMeshBaker` worked. The gate passes only when
> the runtime bake reports success, both opponents report `NavMeshAgent.isOnNavMesh`, they route
> around an obstacle, and they avoid one another. If that cannot be demonstrated in Unity, stop
> after the requested arena shell and fix navigation before building the match loop.

---

## Goal

Create a dedicated interior chunk and prefab titled **Castle Fight Arena**, reached by speaking
to **Prince Mandrew outside the castle in Home London**. Agreeing to the next bout closes the
conversation and sends the player directly into the arena. There is no interior lobby.

A win pays one authored match purse, advances the ladder, and returns the player beside Mandrew.
A defeat or voluntary forfeit returns them to the same place with no purse and no ladder change.
The player enters alone, cannot use the arena to escape police, and cannot turn opponent loot or
partial kills into an infinite farm.

The Oblivion arena is the reference for the loop—host, bout, promotion, repeat—not for its fiction
or number of matches.

## Owner decisions

| Decision | Chosen |
|---|---|
| Name | **Castle Fight Arena**. The prefab root and location/save key use this exact wording. |
| Host | **Prince Mandrew**, positioned outside the existing castle in `Home_London_Prefab`. |
| Entry | A terminal dialogue choice marked `ARENA`; agreement travels directly to the fight floor. |
| Layout | One sealed arena room. **No lobby and no lobby↔pit `LocalTeleporter`.** |
| Return | Victory, defeat, and forfeit all return beside Mandrew automatically. |
| Defeat | No purse and no ladder advance; intercept ordinary death before the death screen. |
| Vitals | Snapshot health, mana, and stamina before entry and restore that snapshot on every exit. The arena cannot be used as a free full heal. |
| Rewards | Arena opponents grant **no ordinary kill XP and no corpse loot**. Only the completed match grants XP/pounds. |
| Ladder | Inspector-authored three-match vertical slice first; plain-text `.arena` importer after the loop is proven. |
| First bout | Two Neeks; **15 XP total for winning the bout**. Pounds remain an owner-authored slot. |
| Companions | Refused before entry. The pit is solo. |
| Wanted player | Refused before entry. Portal travel no longer launders wanted level, but unparented police must not leak into the arena. |
| Mounted player | Refused before entry, matching `DungeonPortal` safety. |

## Current state

Nothing arena-specific is implemented.

- `Home_London_Prefab` contains a `Castle` group at `(11.9, 0, 0)`. It currently has twelve
  castle-model prefab children plus scenery, with colliders and `EnvironmentBlocker`s. It has no
  arena marker, Prince Mandrew, or `DungeonPortal`.
- No Castle Fight Arena prefab, `MapChunkData`, ladder, match controller, Mandrew preset,
  conversation, or art subject exists.
- `MapChunkRegistry` contains the existing overworld/interior chunks, not the arena.
- `PlacementPresetLibrary` has no `neek` key.
- `DungeonPortal`/`ChunkManager.TravelTo` provides the correct chunk lifecycle, named arrival
  marker validation, pause, camera snap, visited-location registration, and `Portal` wanted-state
  notification. Arena entry should reuse `TravelTo`, not invent another chunk swap.
- `Enemy_Neek.prefab` has a `LootOnDeath` component with a non-null loot band even though
  `Preset_Neek.Loot` is empty. Empty preset loot is **not** proof that an arena spawn is clean.
- `Health.Die` always calls `KillXP.AwardFor` after `OnDeath`. A player can otherwise kill one
  opponent, lose the match, and repeat for unlimited partial-bout XP.
- Prince Mandrew has no art subject or owner-written dialogue. Machinery may be scaffolded, but
  quest/dialogue prose and ladder titles remain the owner's words.

---

## Player flow

```text
Talk to Prince Mandrew outside the castle
  -> choose the terminal ARENA agreement
  -> dialogue closes and releases its PauseManager token
  -> ArenaEntryCoordinator validates the request
       not transitioning
       player not wanted
       player not mounted
       no active companion
       next ladder match exists
       any future stake can be paid
  -> snapshot health / mana / stamina
  -> write a safe checkpoint in Home London beside Mandrew
  -> set one pending match request
  -> ChunkManager.TravelTo(Castle Fight Arena, "arena_player")
  -> arena controller waits for a successful runtime NavMesh bake
  -> spawn and activate the opponents
  -> fight
       victory -> match XP/pounds, ArenaWins++, restore entry vitals, return outside
       defeat  -> no reward/rank, restore entry vitals, return outside
       forfeit -> no reward/rank, restore entry vitals, return outside
  -> ordinary arrival save in Home London persists the final result
```

The pending request is runtime-only and is never saved. If travel cannot start or its target
cannot be validated, the request must be cleared and the player must remain outside with the
pre-entry checkpoint intact.

## The prefab and chunk

Files and visible names:

- `Assets/Prefabs/Chunks/Castle_Fight_Arena_Prefab.prefab`
- prefab root: `Castle Fight Arena`
- `Assets/Data/Chunks/Castle_Fight_Arena_Data.asset`
- `MapChunkData.ChunkName`: **`"Castle Fight Arena"`**
- coordinates: an unused off-grid coordinate, cosmetic because there is no adjacency
- `IsCity: false`; all four adjacency references null
- `SuppressCheckpointSaves: true`

`"Castle Fight Arena"` becomes a save key as soon as a build can save it. Freeze the value now.

```text
Castle Fight Arena
├─ RuntimeNavMeshBaker
├─ ArenaMatchController
├─ Environment
│  ├─ DirtyStoneFloor                 28 × 20 units
│  ├─ Wall_North                      full height
│  ├─ Wall_East                       full height
│  ├─ CutawayWall_South               low visual wall + full collision boundary
│  ├─ CutawayWall_West                low visual wall + full collision boundary
│  ├─ NavigationTestObstacle          removable after Phase 0
│  └─ ArenaLighting
├─ PlayerSpawn_arena_player           PlayerSpawnPoint.Id = "arena_player"
├─ OpponentSpawns
│  ├─ ArenaSpawn_1                    SceneMarker
│  ├─ ArenaSpawn_2
│  ├─ ArenaSpawn_3
│  └─ ArenaSpawn_4
└─ ForfeitReturn                      routed through ArenaMatchController, not a raw portal
```

Four opponent markers exist from the first build even though bout one needs two. Later ladder
content can reach four bodies without rebuilding a prefab that has already been dressed.

### Floor and isometric visibility

The floor uses the existing 256×256 tileable
`tex_ground_roadside_pavement_dark_worn_tile.png`: charcoal-grey rectangular slabs with mild
grime. Create an arena-specific material referencing that texture with repeated UV tiling and a
low-smoothness finish. Do not alter the shared material or texture settings, because they may be
used by London scenery.

The fixed camera is pitch 30°, yaw -45°, orthographic size 4. Tall south/west walls can hide the
player entirely. Those near-camera faces therefore use cutaway visuals while retaining solid
collision; north/east may remain full height.

### Creation tool

Build the shell with `Tools > Content > Build Castle Fight Arena`. The editor tool:

- creates the material, prefab, and chunk asset only when absent;
- refuses to overwrite an existing arena prefab or material;
- adds the chunk to `MapChunkRegistry` without duplicating it;
- creates all markers and colliders in one pass;
- uses `PrefabUtility` rather than hand-authored YAML;
- reports the exact Project paths it created and the Phase 0 Unity test route.

Once the prefab exists, later changes load and edit it in place with
`PrefabUtility.LoadPrefabContents`; never delete/re-create it and mint a new GUID.

## Runtime architecture

### ArenaEntryCoordinator

A runtime coordinator owns the transition boundary and the pending request. It is not parented to
either chunk, because Home London is destroyed on entry and the arena is destroyed on return.

Responsibilities:

- find `"Castle Fight Arena"` and the Home London return chunk through `ChunkManager`/registry;
- enforce wanted, mount, companion, transition, ladder, and future-stake rules;
- snapshot entry vitals and checkpoint the player outside;
- start `ChunkManager.TravelTo` with the exact `arena_player` marker;
- expose a single pending match to the arena controller;
- clear a failed or consumed request so a later arena load cannot start a stale match;
- return to an exact `PlayerSpawnPoint` beside Mandrew, not a raw coordinate.

Direct dialogue entry must repeat the safety currently living in `DungeonPortal.Travel`:
`ChunkManager.TravelTo` itself does not reject a mounted player.

### RuntimeNavMeshBaker readiness

`RuntimeNavMeshBaker` needs an observable runtime result (`IsReady`/`BuildSucceeded`, or an
equivalent callback). `ArenaMatchController` must not activate opponents until the bake has
completed successfully.

This is required for two independent reasons:

1. `RuntimeNavMeshBaker.Start` and an arena controller's `Start` have no guaranteed relative
   ordering.
2. `EnemyAI.Start` calls `SnapToNavMesh` once. If it runs before the interior mesh exists, the AI
   falls back to transform movement and never proves agent navigation worked.

Failure must keep the player safe: show a system error, consume no match, and return outside.

### EnemyFactory and shared configuration

Runtime spawning and editor placement need one configuration recipe but **different
instantiation mechanisms**:

- runtime uses `Object.Instantiate` under an inactive holder;
- editor placement keeps `PrefabUtility.InstantiatePrefab` so the placed object retains its
  prefab link;
- both call one runtime-safe configuration function for health/damage overrides, `EnemyLevel`,
  quest key, loot policy, and arena marker.

Do not make `PlacementBuilders` literally instantiate through the runtime factory; that would
detach every editor placement from its source prefab.

At runtime, instantiate every opponent beneath an inactive holder, configure it, and activate the
holder only after the NavMesh is ready. `Health.Awake` reads `EnemyLevel` synchronously, so adding
the level after an active `Instantiate` creates a higher badge over level-1 stats with no error.

Arena spawn configuration must:

- apply the preset's overrides as the level-1 baseline;
- attach exactly one `EnemyLevel` before `Health.Awake`;
- clear both `LootOnDeath.Loot` **and** `LootOnDeath.Band` on prefab-carried components;
- prevent `KillXP.AwardFor` from granting ordinary kill XP, using an explicit arena/no-kill-XP
  marker rather than a magic zero that later gets clamped to one;
- parent every opponent to the arena chunk/holder so teardown destroys it;
- never pool or deactivate an opponent after activation; destroy survivors on defeat/forfeit.

### ArenaMatchController

The controller is serialized on the arena prefab root and consumes the pending request only after
the chunk and NavMesh are ready.

```text
BeginPendingMatch
  -> validate pending match and all required markers
  -> build every opponent inactive
  -> subscribe to each Health.OnDeath
  -> activate the opponent holder
  -> live = true

OnOpponentDeath
  -> ignore when !live
  -> decrement the explicit remaining count
  -> only call Victory at zero

Victory
  -> set live = false first
  -> grant authored match XP and pounds
  -> increment PlayerSession.ArenaWins
  -> restore entry vitals
  -> return beside Mandrew

Defeat / Forfeit
  -> set live = false first
  -> destroy or disable combat on surviving opponents
  -> grant nothing and do not change ArenaWins
  -> restore entry vitals
  -> return beside Mandrew
```

Count `Health.OnDeath` events; do not poll for corpses. `Health.Die` invokes the event before its
delayed destroy, so a corpse poll can end early or never end depending on frame order.

The `GameFlowController.HandlePlayerDeath` arena interception must run before police-arrest and
ordinary death-screen handling. A live sanctioned match owns that zero-health event.

### Vitals and the healing exploit

The old full-revive proposal made Mandrew a free clinic: enter injured, lose immediately, return
at full health. Snapshot `CurrentHealth`, `CurrentMana`, and `CurrentStamina` immediately before
entry and restore those values on victory, defeat, and forfeit. Inventory changes—including used
consumables—are not rolled back.

### Checkpoint policy

`ChunkManager.TravelRoutine` currently saves after every portal arrival. An arena arrival save is
unsafe: reloading it would instantiate the room without a valid pending match and could leave the
player sealed in an empty pit.

Append `MapChunkData.SuppressCheckpointSaves` and enforce it centrally in `SaveGameManager.Save`,
not at only one travel call site. Existing chunk assets read `false` and keep current behaviour.

Entry writes the last safe checkpoint in Home London **before** travel. Return travel is allowed
to autosave normally after the player reaches the outside marker, thereby persisting rewards and
`ArenaWins`. `ContinueFromSave` should defensively redirect any transient-location save to Home
London, covering development builds or future accidental callers.

### Ladder and progress

```text
ArenaLadder
└─ List<ArenaMatch>
   ├─ Title                 owner-written title earned by winning
   ├─ Pounds                victory purse
   ├─ XP                    total victory XP; ordinary kill XP is suppressed
   ├─ StakeCost             present from day one, default 0
   └─ List<ArenaOpponent>
      ├─ PresetKey          PlacementPresetLibrary key
      ├─ Level
      └─ Count
```

`PlayerSession.ArenaWins` is the number of completed rungs and selects the next zero-based list
entry. The first playable vertical slice must persist it because every bout now returns outside
and destroys the arena controller. `SaveData` stores only `ArenaWins`; titles are derived from the
ladder and can be rewritten without migration.

The ladder may live in `Resources` only with strings and scalar data—never prefab, sprite, audio,
or `GameObject` references. Opponents resolve by `PlacementPresetLibrary` key.

### Prince Mandrew and dialogue

Prince Mandrew is a normal `PlacementPreset` NPC placed outside the castle in
`Home_London_Prefab`, beside a `PlayerSpawnPoint` with an exact stable id such as
`castle_arena_return`. The precise placement must be checked visually in Prefab Mode; the castle
YAML proves the group exists but does not safely identify its intended front doorway.

His conversation lives in `quests/dialogue/mandrew.quest`. Add a bare terminal directive:

```text
CHOICE [OWNER-WRITTEN AGREEMENT]
ARENA
```

The importer appends `DialogueChoice.StartsArena = true`. `DialogueManager` closes the
conversation first, then calls the coordinator, preserving the merchant pause-ordering rule.
There is no Arena window in the first slice: the agreement itself begins the bout. A bout card or
rank window is optional later polish.

Dialogue, refusal wording, promotion titles, and Mandrew's spoken lines are owner-authored. Code
and importer work may provide structural placeholders but must not invent the prose.

---

## Silent-failure and exploit checklist

1. **Fallback movement masquerading as NavMesh.** Chase motion alone does not pass Phase 0;
   inspect bake success and `isOnNavMesh` on both agents.
2. **Spawn-before-bake ordering.** Opponents activate only after the baker reports success.
3. **Enemy level added too late.** Configure under an inactive parent before `Health.Awake`.
4. **Prefab-carried loot.** Neek already has a loot band; clear fixed loot and band explicitly.
5. **Partial-kill XP farming.** Arena combatants award no ordinary kill XP, including on a bout
   the player later loses.
6. **Unsafe checkpoint inside the pit.** Suppress saves centrally for the arena and checkpoint
   outside before entry.
7. **Free healing.** Restore entry vitals, never `ReviveFull` as the arena outcome.
8. **Mounted direct entry.** Dialogue entry must reproduce the portal's mount refusal.
9. **Wanted/police leakage.** The current `ChunkTravelKind.Portal` path correctly retains wanted
   level; refuse entry because police are unparented and should not share the arena origin.
10. **Companion leakage.** Reject before travel rather than trying to hide or suspend a follower.
11. **Stale pending request.** Consume or clear it exactly once on success, abort, or timeout.
12. **Rank survives only in a dead controller.** Store `ArenaWins` in `PlayerSession` from the
    first playable loop and append it to the save.
13. **Double outcome.** Set `live = false` before reward, revive, destroy, or travel calls.
14. **No escape from a broken bout.** The forfeit interaction returns safely even when an enemy
    cannot be reached; a NavMesh/spawn authoring failure auto-returns instead of starting.
15. **Isometric wall occlusion.** Cut away the south/west visuals while keeping collision.

## Mapping table—serialized and save-key changes

Nothing is renamed, reordered, or removed. Every existing-type change is appended.

| Type | Change | Existing data reads | Migration |
|---|---|---|---|
| `SaveData` | append `int ArenaWins` | `0`—no bouts won | none |
| `PlayerSession` | add runtime `ArenaWins`, reset in `BeginNewGame`, restore on Continue | fresh runtime state | restore explicitly |
| `MapChunkData` | append `bool SuppressCheckpointSaves` | `false`—all current chunks save normally | none |
| `DialogueChoice` | append `bool StartsArena` | `false`—all current choices unchanged | none |
| `PlacementPresetLibrary` | new `neek` entry, then one per arena subject | current entries untouched | none |
| new types | `ArenaLadder`, `ArenaMatch`, `ArenaOpponent`, match/coordinator components | n/a | n/a |
| new save key | `Castle_Fight_Arena_Data.ChunkName = "Castle Fight Arena"` | n/a | freeze before first save |

The save writer must copy `PlayerSession.ArenaWins` to `SaveData`; Continue must restore it after
`BeginNewGame` has reset the session. Missing either side silently resets progress. A New Game
started in the same app session must also reset it to zero.

---

## Phases

Each phase is reviewed before the next. Do not commit or push unless requested.

### Phase 0—requested shell and honest NavMesh gate

1. Add the idempotent-create editor builder.
2. Create the **Castle Fight Arena** prefab contract, dirty tiled stone material, chunk data,
   registry entry, cutaway walls, player marker, four opponent markers, test obstacle, and forfeit
   anchor.
3. Add observable bake readiness/success to `RuntimeNavMeshBaker` if needed for an honest test.
4. In Unity with Play mode stopped, temporarily place two Neeks in the arena, enter through a
   temporary development route, then start Play mode.
5. Confirm bake success, both `NavMeshAgent.isOnNavMesh`, obstacle routing, mutual avoidance, and
   no console errors. Remove the temporary opponents/route and save the prefab.

**Gate:** if any agent is off-mesh or only using fallback motion, stop. The shell still satisfies
the prefab request, but match implementation is blocked until navigation is corrected.

### Phase 1—safe playable vertical slice

- `ArenaEntryCoordinator` and pending-request lifecycle.
- Shared enemy configuration + runtime factory with inactive-holder ordering.
- Explicit arena combatant policy suppressing fixed loot, loot bands, and ordinary kill XP.
- `ArenaMatchController`, victory, defeat interception, forfeit, automatic outside return.
- Entry-vital snapshot/restore.
- `SuppressCheckpointSaves`, outside pre-bout checkpoint, defensive load redirect.
- `ArenaWins` runtime state, reset, save, and restore.
- Three Inspector-authored matches; first is two level-1 Neeks and 15 total match XP.
- A temporary mechanical start hook is allowed only until Mandrew's owner-written dialogue exists.

**Exit:** win rung 1, return outside, trigger the temporary start hook again, and receive rung 2;
lose and forfeit without
reward/rank; save/reload still offers the correct next rung; partial kills grant no XP or loot.

### Phase 2—Prince Mandrew entry

- Create and wire `Preset_PrinceMandrew`.
- Add `castle_arena_return` marker and place Mandrew outside the castle in Prefab Mode.
- Append `DialogueChoice.StartsArena`.
- Add `ARENA` parsing/validation and the dialogue-manager branch.
- Import the owner-written `quests/dialogue/mandrew.quest`.
- Remove the temporary mechanical start hook.
- Exercise wanted, mounted, companion, exhausted-ladder, and future-stake refusals.

**Exit:** talk to Mandrew outside, agree, travel directly into the bout, and return beside him for
all three outcomes without pause imbalance.

### Phase 3—`.arena` authoring pipeline and fuller ladder

- `arena/ladder.arena`, format reference, importer, and validator.
- `Tools > Content > Import Arena Ladder` and `Validate Arena Ladder`.
- Validate contiguous ranks, non-empty owner titles, positive rewards/counts, resolvable enemy
  preset keys, enemy categories/prefabs, and no match exceeding four spawn markers.
- Expand only after the first three matches have been play-tested.

### Phase 4—optional polish

- Bout/rank card window before agreement.
- Crowd and ambience.
- Champion introductions and named opponents.
- Wagers/stakes after transaction ordering is designed and tested.
- Top-rank unique item and bag-window rank readout.

## Ladder shape—proposal, not authored content

Rung 1 is fixed: two Neeks and 15 total match XP. Pounds and all titles are owner slots.

| Rungs | Opponents | Level | Purpose |
|---|---|---|---|
| 1–6 | 2 | 1 → 3 | Introduce subjects at a stable count. |
| 7–14 | 2–3 | 3 → 6 | Mixed pairs and the first third body. |
| 15–24 | 3 | 6 → 10 | Let level scaling carry difficulty. |
| 25–34 | 3–4 | 10 → 15 | Use all four authored markers. |
| 35–40 | 4/champions | 14 → 20 | Endgame combinations and named bouts. |

With ordinary kill XP suppressed, the `XP` field is the total progression payout and can be
balanced directly. This replaces the old accidental ~65 XP first bout (two normal kills plus a
15 XP match award) with the intended 15 XP total.

## Art and owner-authored content

- Prince Mandrew needs an art subject before he is more than a temporary reused villager visual.
- His dialogue, refusal lines, promotion messages, and every rank title need owner text.
- The arena floor needs no new bitmap: reuse the existing 256×256 worn dark pavement tile through
  an arena-specific material.
- Tortured Neek still has only idle art; exclude him from the first ladder or accept sliding and no
  death pose as a known art gap.

## Unity verification route

Agent-side `python Tools/asset_reachability.py --check-dangling` verifies references only. It does
not prove compilation, prefab parsing, NavMesh, visuals, or play behaviour. The following requires
Unity and a human:

1. Run `Tools > Content > Build Castle Fight Arena` with Play mode stopped. Run it a second time
   and confirm it refuses to overwrite rather than minting new GUIDs.
2. Open the prefab and confirm one root, 28×20 dirty tiled floor, solid boundaries, cutaway
   south/west visuals, player marker, four opponent markers, and arena material.
3. Run the Phase 0 test and inspect bake success plus `isOnNavMesh` on **both** agents. Chase motion
   alone is a failure to verify.
4. Check both agents route around the test obstacle and do not overlap or shove through walls.
5. Talk to Mandrew outside while healthy, injured, wanted, mounted, and with Alex following.
6. Win: both deaths are required, no corpse menu opens, only 15 XP is paid, pounds pay once,
   `ArenaWins` advances once, entry vitals return, and arrival is beside Mandrew.
7. Lose after killing one opponent: no kill XP, loot, purse, or rank; entry vitals return.
8. Forfeit: same no-reward outcome and safe return.
9. Quit mid-bout and Continue: arrive at the pre-bout Home London checkpoint, never an empty pit.
10. Win two bouts, reload, and receive rung 3. Start a New Game in the same app session and receive
    rung 1, proving reset and restore both exist.
11. Check no tall near-camera wall hides the player at the south/west edges.
12. Re-import quests and confirm Mandrew's `ARENA` action survives generated-asset replacement.

## Explicitly out of scope

- General building-interior suspend/resume and location caching. The arena is intentionally fresh
  per bout and never suspended.
- A physical castle door or explorable castle lobby. Mandrew's agreement is the entry point.
- Rerouting arrest or making police follow into interiors.
- Arena corpse loot or arena-specific loot tables; the purse is authoritative.
- Full ladder prose, dialogue, titles, and Mandrew art without owner input.
