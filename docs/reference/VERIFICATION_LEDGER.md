# Verification ledger — what's never been seen by a compiler or an editor

**Last verified against:** `main` @ 2026-08-18 (moved out of `CLAUDE.md` §5, content unchanged in
substance, tightened in wording; the mobile HUD layout pass added the same day).

Owned by [CLAUDE.md](../../CLAUDE.md) §5, which explains *why* this exists: there is no C#
compiler, no Unity, and no test framework in the agent environment, so this file is the honest
record of what's landed on `main` but not yet exercised.

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
- **The companion system (Alex).** Recruited and fought alongside the player against a placed
  `Enemy_Spicehead` in an editor session, 2026-08-16 — following, targeting, combat all confirmed
  good. Alex's rebuilt heal (now dual-target, no longer combat-gated) postdates that session and is
  still open — see Companions below.
- **Name unification namespace rename.** Compiles (2026-08-16 checkpoint). Behaviour below.

## Open — grouped by system

### Actors, art, sizing
- **`UIManager.EnsureDedicatedTrack`** wraps a bar fill in its own parent when the scene doesn't
  give it one — check the concealment/mana overlap is actually fixed, and that the concealment bar
  lands somewhere sane (it's been stretched across the whole cluster, so its real position is
  unknown). ⚠️ **Known follow-on bug, not yet fixed**: `EnsureDedicatedTrack` tests
  `parent.childCount == 1`, but `EnsureBarLabel` adds a label afterward — so the *second* bar wrapped
  (HP or MP, whichever loads second) inherits the first bar's fill fraction as its new track size.
  Would show as a health bar topping out at a third after loading at low health.
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
- **`ART_PIPELINE.md` still tells the art agent adults are 1.55** (the cast is now 1.35/65px). Next
  delivered batch will arrive wrong-density until someone decides whether the contract or the cast
  is what changes — undecided, not a bug.
- **Four sprites in `c.unity` point at missing files** (three on one texture, three on another, one
  on a third, plus the PCSO's `WorldActorVisual.ActorSprite` on a fourth) — old, listed in
  `KNOWN_DANGLING` in `Tools/asset_reachability.py`. Fix: reassign each in the Inspector, delete its
  `KNOWN_DANGLING` line. PCSO probably wants `sheet_char_police_pcso_idle` (on disk) — confirm before
  assuming.
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

### Wallet, quests, dialogue
- **Quest titles now resolve from the definition** (2026-08-18, never compiled). `DialogueManager`
  was substituting the raw quest id when a choice had no authored title, and because the id is a
  non-empty string it defeated `StartQuest`'s own fallback to `QuestDefinition.Title` — so every
  dialogue-granted quest read `spark_of_talent` in the tracker and journal. All 111 generated
  choices leave `GrantQuestTitle` blank, so this hit everything. *Check the tracker reads
  "Serendipity!" and the journal "Ah, Barnacles".*
  ⚠️ **`QuestProgress.Title` is persisted in `savegame.json`**, so the grant-path fix alone would
  have left existing saves ugly forever. `RestoreQuests` now re-resolves a title equal to the id
  from the definition on load. *Load the 2026-08-17 playthrough save and check the already-granted
  quests read properly — that path is the retroactive repair and is the more likely of the two to
  be wrong.* A title that differs from the id is left alone, so a bespoke dialogue title still wins.
- **The world level badge is bigger** (2026-08-18, never compiled). ⚠️ The number was parented
  *inside* the 0.28-scaled badge quad in both `EnemyNameplate` and `PlayerHealthBar`, so it rendered
  at 0.28 × its font size — growing the quad alone would not have fixed it. Both now parent the
  number to the plate root. Three new `EKVibe` constants: `LevelBadgeSize` 0.42,
  `LevelBadgeFontSize` 2.0, `LevelBadgeOffsetX` −0.62. *Check the number is centred on the badge and
  not overlapping the enemy's name — the offset tracks the size and must move out as it grows.*
  Nameplates are still combat-gated (aggro, or player within `SightRadius`); that was left alone.
- **The wallet has never run.** Pickpocket a civilian, get arrested, reload a save. Check the bag
  readout tracks all three and a pre-today save loads at £0 rather than failing.
- **Blank-name fallback never run.** `PlayerSession.BeginNewGame` should turn a blank name box into
  "Vince". Start a new game leaving the box untouched, check the nameplate reads Vince.
- **The three quest fixes**, never exercised: `ClearWanted` despawning police, `StartQuest` no
  longer rewinding a mid-flight objective, the watcher claiming a reward only after paying it. Needs
  a `QuestDefinition` in `Resources/Quests/` and a way to grant it — the throwaway test rig was
  deleted deliberately (quests are meant to be granted in-world, never from a menu).
- **Live defect, not yet fixed**: no `Police_*` prefab has `IsPolice` set, so arrest never fires and
  `DespawnPolice` destroys nothing. Fix: tick the box on all five prefabs in the Inspector — **never**
  by re-running `ModernBritainSetup`.
- **`spark_of_talent`** (the magic tutorial) was converted off bespoke code onto the `.quest`
  pipeline; `MagicTutorial.cs` is deleted. ✅ The import ran 2026-08-17, `NPC_Daniel Pauls` is placed
  in `Home_London_Prefab` (replacing the old `DanielPaulsSpawn` marker) and
  `Preset_DanielPauls.QuestKey` is `danielpauls`. What remains unexercised is the quest itself.
  Unverified: whether `Awake` runs on a
  disabled component — if the panicked geezer stands still or falls through the NavMesh, that's the
  answer and `HostileAfterDialogue` needs to snap him to the NavMesh itself. Check both a mid-flight
  save and a completed save (completed should retro-pay 0/0, not re-pay).
- **Four London doors are authored** (2026-08-17); two lead nowhere. Church → `Abandoned_Church` and
  Station → `Abandoned_Bus_Station` have no arrival marker on the interior side — pressing USE should
  leave the player standing still with a console warning naming the chunk/id (this is the first real
  exercise of the 2026-08-09 `TravelRoutine` reorder that makes that safe — a stranded player means
  the reorder didn't take). Finish both via `Tools → Place → Portal Placement`, reusing link ids
  `Abandoned_Church_Door` / `Bus_Station_Main_Door`. `Gang_Hideout`'s interior arrival point is still
  at chunk origin and needs moving when dressed. `NPC_Ralph`/`NPC_Sanjeet` were removed from London;
  `Dialogue_Ralph.asset`/`Dialogue_Sanjeet.asset` are still PascalCase on disk — a future
  `DIALOGUE ralph` block is the untested collision case above.
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
- **`HIRE: <companionId> [free]`** quest directive and Quest 8's text (committed 2026-08-17). Alex is
  now gated three ways on `rush_hour` (greeting only before, free hire during, £25 hire after) —
  confirm he can't be hired before Rush Hour completes. `Dialogue_Alex.asset` was renamed to
  lowercase and the 2026-08-17 import held it on GUID `750c809e…`; `Dialogue_Alex_Follower.asset` is
  still PascalCase in the same folder — a future `DIALOGUE alex_follower` block hits the same
  collision. `red_star_cigarettes` (new consumable, no icon) needs no new code. `rush_hour.quest` is
  only a beginning — East York isn't a chunk, Mayor Zhao has no preset/art, no
  `ProximityDialogueTrigger` exists, and Zhao's line asks the pipeline to *grant* an item on a choice,
  which it can't do (`ITEM:` is a requirement, not a grant).
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
- **Player knockback (phase 2)**: `EnemyAI.KnockbackDistance` defaults to 0 — nothing knocks the
  player until `Enemy_OG`/`Enemy_Tainted` are stamped and set to 2m (police stay 0, per the recorded
  decision, folded into the same Inspector pass as `Level: 3`/`IsPolice`). Check the slide is ~2m and
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
  — first `PerkData` asset authored freezes the enum indices forever. **No perk asset exists yet** —
  author one (Create → `GBH England/Data/Perk` in `Resources/Perks`, MeleeKnockback, Magnitude 2m
  flat, not %), spend the point, hit something, check ~2m slide stopping at walls.
  `PlayerSession.MeleeKnockbackDistance` resets in `RecalculateDerivedStats` step 6 — reload after
  taking the perk, shove should be the same, not doubled. A killed enemy is never shoved (gated on
  `!targetHealth.IsDead`, since `Health.Die` already disables the agent). `EnemyAI`'s three
  `SetTrigger` calls are now guarded, so an undefined `Knockback` trigger won't error (expected until
  band 10 sheets land).

### Progression, HUD, enemy levels
- **Enemy levels placed nowhere yet.** `PlacementPreset.EnemyLevel`/palette Level field attach an
  `EnemyLevel` component (0 = none attached, deliberately, since level-1 isn't inert — it flips the
  nameplate badge from the prefab's "3" to "1"). No enemy prefab is placed in any chunk or `c.unity` —
  stamp one at Level 4 vs Level 1 and check the difference. Nameplates now show on aggro or within
  `SightRadius`, hide a few seconds after — check one appears on approach, not just after first hit,
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
