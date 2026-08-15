# The Royal Fight Arena

```
Last updated:          2026-08-15 (plan only — nothing implemented)
Verification scope:    Nothing here has been implemented. Every claim about existing code was read
                       line by line from the working tree on `codex/quest-dialogue-split` on this
                       date (ChunkManager, DungeonPortal, LocalTeleporter, TutorialSequence,
                       Health, EnemyLevel, PlacementBuilders, DialogueManager, GameFlowController,
                       SaveGameManager, WantedManager, EnemyNameplate, CompanionManager,
                       QuestTextImporter). Preset_Neek, PlacementPresetLibrary.asset and the
                       Castle's position in Home_London_Prefab were read from their YAML.
                       Nothing was compiled or run — there is no compiler in the agent
                       environment (CLAUDE.md §5).
```

> **Phase 0 is a hard gate.** The arena is the first interior content in this project that
> contains anything which *navigates*. Whether `RuntimeNavMeshBaker` produces a usable NavMesh
> inside a portal-reached interior chunk has **never been tested** — the six shells committed
> 2026-08-09 are empty boxes and nobody has walked an agent around one. The first bout is **two**
> opponents, so it needs two agents pathing and avoiding each other, not one. If it does not work,
> the arena is blocked behind
> [BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md)
> and no amount of arena code helps. **Prove it before building anything else.**

---

## Goal

The **Royal Fight Arena**, under the castle in London, hosted by **Prince Mandrew**. He signs you
up; you are taken into the castle interior and fight what he puts in front of you. Win and you
take a small purse and climb a ladder of ranks, each carrying a title. Every rung is harder —
higher-level opponents, then more of them at once, then both.

The Oblivion arena is the reference for the *loop*, not the fiction: talk to the host, get sent
into the pit, fight, come back out, talk again. Where Oblivion has ~21 matches, this has many more.

> ⚠ **Spelling check before anything is authored.** The brief said "Price Mandrew"; this plan uses
> **Prince Mandrew** throughout, on the reading that it belongs with "Royal" and a castle. The name
> ends up in a `PlacementPresetLibrary` key, a `DIALOGUE <npcId>` block and an asset filename — all
> contracts — so correct it here first if the reading is wrong. Nothing depends on it yet.

## Owner decisions (confirmed 2026-08-15)

| Decision | Chosen |
|---|---|
| Layout | **One chunk holding both lobby and pit.** Prince Mandrew stands in the lobby; each match is a `LocalTeleporter` hop into the pit and back, with no loading screen between bouts. |
| Defeat | **Ejected to the lobby with no purse and no rank change.** A sanctioned bout must not read as "you died, load your save". |
| Ladder authoring | **A plain-text `.arena` file plus an importer**, mirroring the `.quest` pipeline. |
| First bout | **Two Neeks**, 15 XP. Purse in pounds is still an owner slot. |
| Companions | **Refused at the door.** The pit is solo. |

## What already exists, and what it costs us

The arena is unusual in that the project's biggest known interior weakness is, here, a feature.

**`ChunkManager.TravelRoutine` destroys and re-instantiates the destination chunk on every
entry.** For an ordinary building interior that is a defect — it resets unsaved NPC, enemy and
chest state, which is why CLAUDE.md says *do not ship reward-bearing interiors until the location
cache lands*. The arena wants no carried state inside the chunk at all: a fresh pit every entry is
the correct behaviour. **The arena therefore sidesteps that blocker rather than tripping it**, and
this should be stated plainly in the commit message so nobody later reads it as a violation.

| Piece | What it gives the arena |
|---|---|
| `Castle` empty at `(11.9, 0, 0)` in `Home_London_Prefab` | The building. Wall, turret and gothic-castle GLBs are already placed. It has no interior and no door. |
| `DungeonPortal` + `MapChunkData` + `PlayerSpawnPoint` | The way in and out. Portal travel is the one canonical USE-driven door. |
| `LocalTeleporter` + `SceneMarker` | The lobby↔pit hop, no chunk swap, no loading screen. Exactly the two-field component this needs. |
| `TutorialSequence` | The precedent for a runtime controller parented to the chunk instance so it dies with the chunk. `ArenaMatchController` is the same shape. |
| `EnemyLevel` + `EKVibe.Scaled*` | The whole difficulty curve. The prefab's authored stats are the level-1 baseline and the level multiplies them. Nothing new is needed to make an opponent harder. |
| `Preset_Neek` | The first opponent, already authored: category `Enemy`, `EnemyPrefab` → `Enemy_Neek.prefab`, no overrides, **`Loot: []`**. The empty loot list means no `LootOnDeath` is attached, so "the pit drops nothing" comes free for Neek. |
| `MerchantUI` + `Win95Skin` | The window pattern, including the pause-ordering trap it already paid for. |
| `QuestTextImporter`'s `MERCHANT:` directive | Added 2026-08-15. The exact template for an `ARENA` choice directive — see below. |
| `quests/dialogue/*.quest` | Dialogue-only files. Prince Mandrew owns a conversation and no quest, which is precisely what this folder was added for. |
| `CompanionManager.HasActiveCompanion` | The companion refusal, one property. |

**Not reusable, and worth saying:** `PlacementBuilders.BuildEnemy` is in `Assets/Editor/`, which is
stripped from builds. Runtime enemy spawning has no shared recipe today — `TutorialSequence` hand-
builds its bandit component by component, which is precisely how the tutorial cast ended up outside
the preset system. **Do not repeat that.** See §EnemyFactory.

**Two gaps in existing content this work has to close:**

- ⚠ **`Preset_Neek` is not in `PlacementPresetLibrary`.** That asset holds three entries today —
  `DanielPauls`, `TracksuitGeezer`, `alex`. The ladder resolves opponents by library key, so
  Phase 1 adds a `neek` entry, and every later opponent subject adds one more.
- ⚠ **`Enemy_Neek` has never been seen in play.** It is one of the six enemy prefabs on the
  CLAUDE.md §5 ledger. The first bout is its debut as well as the arena's.

---

## Architecture

### The chunk

One new `MapChunkData` + chunk prefab, built the same way as the six interior shells but **by an
editor tool, not hand-authored YAML**. The six existing shells were written by hand because no
Unity was available, and all twelve of their files are still unverified; there is no reason to add
a thirteenth to that pile.

```
Royal_Arena  (MapChunkData, ChunkName "Royal Fight Arena")
└─ Royal_Arena_Prefab
   ├─ RuntimeNavMeshBaker            (on the root, as the shells have)
   ├─ Lobby                          floor + walls
   │  ├─ PlayerSpawn  id "arena_entrance"    ← arrival from London
   │  ├─ SceneMarker  key "ArenaLobby"       ← where a match returns you
   │  ├─ Portal_ToLondon (DungeonPortal → Home_London, marker "castle_door")
   │  ├─ Gate (LocalTeleporter → "ArenaPitEntry", prompt on the portcullis)
   │  └─ NPC_PrinceMandrew                   (stamped from a PlacementPreset)
   └─ Pit                            floor + walls, open sand
      ├─ SceneMarker  key "ArenaPitEntry"    ← where the player lands for a bout
      └─ SceneMarker  keys "ArenaSpawn_1".."ArenaSpawn_4"   ← opponent spawn points
```

**Four spawn markers from day one**, not two. Rung 1 already needs two, and the ladder reaches four
opponents; adding markers later means re-running the builder against a chunk prefab that has since
been dressed by hand.

And in `Home_London_Prefab`, one `DungeonPortal` at the castle gate targeting
`Royal_Arena` / `arena_entrance`, plus a `PlayerSpawnPoint` id `castle_door` for the return trip.
Both ends are authored with `Tools → Place → Portal Placement`, which creates the pair and adds
both chunks to `MapChunkRegistry` — ⚠ **and which has itself never been opened**, so its first run
is part of this work.

⚠ **`"Royal Fight Arena"` becomes a save key the moment the player first walks in**, via
`PlayerSession.MarkChunkVisited` → `SaveData.VisitedChunks`. Freeze the string now. The space is
deliberate and follows the `"Manor Cellars"` precedent; do not later normalise it.

### The match controller

`ArenaMatchController` — runtime, `Assets/Scripts/World/`, instantiated by the FIGHT action and
parented to `ChunkManager.CurrentChunkInstance`, so it dies with the chunk exactly as
`TutorialSequence` does.

```
StartMatch(rank)
  ├─ resolve ArenaMatch for rank from the ladder
  ├─ teleport player to "ArenaPitEntry"
  ├─ for each opponent entry: EnemyFactory.Spawn(preset, level, at "ArenaSpawn_n")
  ├─ subscribe each Health.OnDeath
  └─ live = true

OnOpponentDown → if any remain, return; else Victory()

Victory()
  ├─ pay Pounds + XP
  ├─ PlayerSession.ArenaRank = rank + 1
  ├─ toast the new title
  ├─ teleport player to "ArenaLobby"
  └─ live = false

Defeat()  ← called from GameFlowController.HandlePlayerDeath
  ├─ ReviveFull()
  ├─ destroy surviving opponents
  ├─ teleport player to "ArenaLobby"
  └─ live = false, no purse, no rank change
```

`live` is deliberately not saved. A match is a thing that happens between two saves, never across
one — see the autosave trap below.

⚠ **Counting deaths, not corpses.** Subscribe to each opponent's `Health.OnDeath` and decrement a
counter. Do not poll for surviving `EnemyAI` objects: `Health.Die` destroys the GameObject after
the event when `DestroyOnDeath` is set, and a poll that runs on the wrong side of that frame ends
the bout early or never.

### EnemyFactory

A new runtime `EnemyFactory` in `Assets/Scripts/World/`, mirroring `NpcFactory`: one description of
what a placed enemy is, callable from both the running game and `Assets/Editor/`.

It is a near-copy of `PlacementBuilders.ApplyEnemyOverrides` — instantiate `preset.EnemyPrefab`,
apply `OverrideHealth`/`OverrideDamage`, attach `EnemyLevel`, attach `LootOnDeath` — and
`PlacementBuilders.BuildEnemy` should then delegate to it so there is one recipe, not two. That
delegation is the same move already made for NPCs and is worth doing in the same commit; doing it
later means the two copies drift first.

⚠ **The trap that makes this non-obvious.** `Health.Awake` reads:

```csharp
GetComponent<EnemyLevel>()?.ApplyTo(this);
CurrentHealth = MaxHealth;
```

`Instantiate` runs `Awake` **synchronously**, so a naive `Instantiate(prefab)` followed by
`AddComponent<EnemyLevel>()` scales nothing at all — every arena opponent would spawn at level-1
stats wearing a higher badge, and **nothing would log**. The editor path is immune only because
`PrefabUtility.InstantiatePrefab` does not run `Awake` in edit mode and the component is serialized
into the placed instance.

The fix: instantiate under a **deactivated holder**, add `EnemyLevel`, then activate. `Awake` and
`Start` both run on that first activation.

⚠ And the corollary, which is the same mechanism as the chunk-root rule in CLAUDE.md §3: **an
arena opponent must never be deactivated again after that.** `EnemyAI` starts its
`PerceptionRoutine` only in `Start`, so a re-deactivated enemy is permanently blind. Destroy
surviving opponents on defeat; do not pool them.

### The ladder

Phase 1 uses a small Inspector-authored `ArenaLadder` ScriptableObject so the loop can be proven
against three matches. Phase 3 replaces its *authoring surface* with a `.arena` text file and an
importer that regenerates the same asset — the runtime type does not change, only where its
contents come from. This is the shape the `.quest` pipeline already took, and that pipeline is now
being used in anger across six quest files, which is good evidence it was the right call.

```
ArenaLadder  (ScriptableObject, Assets/Resources/ArenaLadder.asset)
└─ List<ArenaMatch>
   ├─ Title          the rank earned by WINNING this match  ← owner's words
   ├─ Pounds, XP     the purse
   ├─ StakeCost      entry fee in pounds, 0 for free        (field exists from day one, default 0)
   └─ List<ArenaOpponent>
      ├─ PresetKey   a PlacementPresetLibrary key (string)
      ├─ Level       EnemyLevel to attach
      └─ Count       how many
```

⚠ **`ArenaLadder` lives in `Resources/`, so everything it references ships in every build.**
`QuestDefinition`'s remarks spell out why that matters and the rule it produced: no `GameObject`,
`Prefab`, `Sprite` or `AudioClip` field on a `Resources`-resident type, because one prefab
reference drags its entire dependency graph in. **Opponents are therefore referenced by
`PlacementPresetLibrary` key — a plain string — not by prefab.** That is the same indirection the
tutorial characters already use, and it costs one library entry per opponent subject.

**The title is not saved.** `SaveData` stores the rank as an integer and the title is looked up
from the ladder on every read, exactly as the player's level is derived from `TotalXP` and never
stored. The owner can rewrite every title in the game without a save migration.

### Entry from dialogue

Prince Mandrew's conversation is a **dialogue-only file**, `quests/dialogue/mandrew.quest`. He owns
a conversation and no quest, which is exactly what that folder was added for on 2026-08-15. The
file owns his conversation permanently: every future line he says goes in it, gated, because each
import regenerates `Dialogue_Mandrew.asset` wholesale.

The hook is a new **`ARENA` choice directive** in `QuestTextImporter`, modelled directly on the
`MERCHANT:` directive added the same day:

```
CHOICE [TODO: ask for a bout]
ARENA
```

Bare, with no argument — there is one arena, and unlike `MERCHANT:` there is no paired action to
name. That also means there is no half-set-pair for `DialogueValidator` to reject, which is the
check `MERCHANT:` had to be careful about. Like a merchant choice it takes no `-> id`: it ends the
conversation.

It sets one appended field on `DialogueChoice`, and `DialogueManager.OnChoiceSelected` gets one
branch that mirrors the merchant branch verbatim:

```csharp
// A shop owns its own modal pause. Close the conversation first so its pause token is
// released, then let the arena window acquire one; doing this in the other order
// leaves the world one Push ahead when the window closes.
if (choice != null && choice.OpensArena)
{
    EndDialogue();
    UI.ArenaUI.Show();
    return;
}
```

⚠ That ordering is not a style preference. It is a bug the merchant work already paid for once, and
it is written into CLAUDE.md as an outstanding verification item. Copy the shape, copy the comment.

### The window

`ArenaUI`, Win95-skinned like `MerchantUI`. Shows: current title and rank, the next opponent(s) and
their levels, the purse, and FIGHT / LEAVE. Refusals live here, all in one place, each with the
owner's own line:

| Refusal | Check | Why |
|---|---|---|
| Wanted level above 0 | `WantedManager.Instance.CurrentKnives > 0` | See the laundering trap below. Also good fiction. |
| A companion is following | `CompanionManager.Instance.HasActiveCompanion` | The pit is solo — owner's decision. **Live, not hypothetical: Alex ships as of `ab2d6c5`.** |
| Ladder exhausted | rank past the last rung | The player has cleared everything. |
| Cannot pay `StakeCost` | `PlayerSession.Pounds` | Only once a stake is authored above 0. |

---

## Traps

Each of these is a silent failure — nothing throws, nothing logs.

### 1. The arrival autosave puts a save inside the pit

`TravelRoutine` calls `SaveGameManager.Save()` on arrival. So walking through the castle door
writes a checkpoint whose `ChunkName` is `Royal Fight Arena`. Quit there and reload, and
`SaveGameManager.LoadWorld` rebuilds the arena chunk with **no `ArenaMatchController`** — it was
parented to the destroyed instance and nothing re-creates it. If the save was taken mid-bout the
player reloads sealed in the pit with no opponents, no exit and no reason for any of it.

**Fix, in two layers:**

- **Append `bool NoAutosave` to `MapChunkData`** and have `TravelRoutine` skip its `Save()` for a
  chunk carrying it. Appending a serialized field is safe; the twelve existing `MapChunkData`
  assets read `false` and behave exactly as today (CLAUDE.md §3).
- **Save before travelling**, in the portal's own path, so the last checkpoint is London *outside*
  the castle. Losing a bout then costs nothing but the walk back in.
- **Belt and braces:** `GameFlowController.ContinueFromSave` redirects a save whose chunk carries
  `NoAutosave` to London. This recovers a save file already written by an earlier build, which the
  first two layers cannot.

### 2. Ducking into the arena launders the wanted level

`WantedManager.OnChunkTransition` clears `CurrentKnives` outright when the player moves from a
chunk with `IsCity` set into one without it. `Royal_Arena` will have `IsCity: 0`, so **commit a
crime, walk through the castle door, walk back out clean.** Free laundering, with a police cooldown
applied to London as a bonus.

The chosen fix is the entry refusal above: **the arena will not take you while you are wanted.**
That gates the exploit and dodges the separate question of whether police — which `WantedManager`
spawns *unparented*, so they survive the chunk swap — should be able to follow you into a bout.

⚠ **This hole is not new and is not the arena's.** All six interior shells committed 2026-08-09
have `IsCity: 0` and are reached by portal, so every one of them launders the wanted level the same
way the moment a door is wired to it. That is a pre-existing defect this work merely walks past;
fixing it properly is a `WantedManager` job (an interior is not "the wilderness") and is being
handled separately.

### 3. `EnemyLevel` added after `Instantiate` does nothing

Covered under EnemyFactory above. Repeated here because it is the one that produces a high badge
over a level-1 opponent with an empty console.

### 4. NavMesh inside an interior chunk is unproven

`c.unity` registers `Assets/c/NavMesh.asset` for the life of the scene, every chunk instantiates at
the origin, and every interior carries its own `RuntimeNavMeshBaker`. Whether an agent can actually
path inside a portal-reached interior has never been observed, because no interior has ever
contained anything that paths. **This is Phase 0 and it gates everything.**

### 5. Loot on death vs. the purse

If arena opponents keep their preset `Loot`, the pit becomes a farm and the ladder stops being the
economy. `Preset_Neek` has `Loot: []` so rung 1 is already clean, **but that is luck, not a
guarantee** — the moment a subject with loot joins the roster the pit becomes farmable. Make it
explicit: `EnemyFactory` takes a "suppress loot" flag which the arena sets and the World Palette
does not. The purse and the title are the reward.

### 6. `DialogueChoice` is serialized into every generated asset

The new field is **appended, never inserted**, same rule that `QuestGateType.ActiveAtStage = 4`,
`MerchantActionType` and every other addition to that class followed.

---

## Mapping table — serialized and save-key changes

Nothing here is a rename. Every entry is an append, and the append-only rule is what makes each of
them safe to read back from an existing asset or save.

| Type | Change | What an existing asset/save reads | Migration |
|---|---|---|---|
| `SaveData` | append `int ArenaRank` | `0` — unranked, never fought | none |
| `MapChunkData` | append `bool NoAutosave` | `false` — autosaves as today | none |
| `DialogueChoice` | append `bool OpensArena` | `false` — no arena branch | none |
| `PlacementPresetLibrary` | new entry `neek`, then one per opponent subject | untouched | none |
| — new — | `ArenaLadder`, `ArenaMatch`, `ArenaOpponent` | n/a | n/a |
| — new — | `Royal_Arena_Data.ChunkName` = `"Royal Fight Arena"` | **new save key — freeze before first save** | n/a |

**No existing field is renamed, reordered or removed**, so no `[FormerlySerializedAs]` is needed
anywhere in this work. If that stops being true, this table is what must be rewritten first.

---

## Phases

Each is a single-concern commit, plan → implement → review per CLAUDE.md §6.

### Phase 0 — prove the NavMesh (gate)

No arena code. Build a throwaway: stamp **two** `Enemy_Neek` into `Quidland_Prefab` (an existing
shell), wire a `DungeonPortal` from London to it with `Tools → Place → Portal Placement`, walk in,
and see whether they chase you and path around each other. **If they stand still, stop and report —
the arena is blocked behind the chunk-lifetime work and nothing below is worth writing.**

Two, not one, because rung 1 is two: agent-vs-agent avoidance inside a small interior is a separate
question from whether a single agent can path at all.

This also gets four other unverified things exercised for free: the portal travel path, the Portal
Placement tool's first ever run, `MapChunkRegistry` being accepted by Unity, and `Enemy_Neek`'s
debut.

Discard the throwaway afterwards.

### Phase 1 — the chunk and the loop

- `Tools → Content → Build Royal Arena Chunk` — an editor tool creating the `MapChunkData`, the
  chunk prefab, its two rooms, markers and four spawn points. Creates only; refuses to overwrite,
  so it stays out of Danger Zone.
- Portal pair London ↔ arena; `PlayerSpawnPoint castle_door` in London.
- `EnemyFactory`, with `PlacementBuilders.BuildEnemy` delegating to it.
- `PlacementPresetLibrary` entry `neek`.
- `ArenaMatchController`, `ArenaLadder` with **three** matches, no UI — FIGHT is a plain dialogue
  choice for now.
- The two autosave layers (`MapChunkData.NoAutosave`, save-before-travel).

**Exit criterion:** walk in, talk, fight two Neeks, win, get paid 15 XP, land back in the lobby,
fight rung 2. No window, no ranks, no persistence.

### Phase 2 — ranks, defeat, the window and the dialogue hook

- `SaveData.ArenaRank`, restored in `GameFlowController.ContinueFromSave` alongside the other
  session restores.
- The `HandlePlayerDeath` hook: a live match takes the ejection path instead of `DeathScreenUI`.
- `ArenaUI` (Win95), `DialogueChoice.OpensArena`, the `DialogueManager` branch, the `ARENA`
  importer directive, and the four refusals.
- `quests/dialogue/mandrew.quest` — structure and gating scaffolded, **words the owner's**.
- Titles read from the ladder and toasted on promotion.

### Phase 3 — the `.arena` pipeline and the full ladder

- A repo-root `arena/ladder.arena`, a format doc, `ArenaTextImporter`, `ArenaContentValidator`, and
  `Tools → Content → Import Arena Ladder` / `Validate Arena Ladder`.
- Validator rules: every `PresetKey` resolves in `PlacementPresetLibrary`; every referenced preset
  is category `Enemy` and has an `EnemyPrefab`; ranks are contiguous from 1; every match has a
  non-empty title and at least one opponent; `Count` never exceeds the number of `ArenaSpawn_n`
  markers in the chunk prefab.
- The full ladder authored — see the shape below.

### Phase 4 — polish, if wanted

Wagering on your own bout, a crowd, champion bouts with a named opponent and their own arrival
line, an arena-only reward item at the top rung, a rank readout in the bag window.

---

## Ladder shape — a starting proposal, not a decision

Rung 1 is fixed by the owner: **two Neeks, 15 XP.** Everything below it is a proposal.

The roster is seven subjects. A forty-rung ladder built from seven enemies has to escalate along
three axes or it will feel like the same fight forty times — and since rung 1 already starts at two
opponents, count is the *later* axis, not the first:

| Rungs | Opponents | Level | What changes |
|---|---|---|---|
| 1–6 | 2 | 1 → 3 | Each subject introduced against a familiar count. |
| 7–14 | 2–3 | 3 → 6 | First mixed pairs, first third body. |
| 15–24 | 3 | 6 → 10 | Level does the work. |
| 25–34 | 3–4 | 10 → 15 | Four at once needs all four spawn markers. |
| 35–40 | 4 + champions | 14 → 20 | Named opponents well above the curve. |

Levels multiply through `EKVibe.EnemyHealthPerLevel` (0.35) and `EnemyDamagePerLevel` (0.25), so a
level-20 opponent has ~7.65× the health and ~5.75× the damage of the level-1 prefab. Against
`MaxPlayerLevel` 25 that is roughly the right shape, but **it is arithmetic, not playtesting.**

⚠ **The purse is a garnish, not the reward — check this is intended.** `EKVibe.KillXPBase` is 25,
so two level-1 Neeks already pay about **50 XP in kill XP** before the arena's own purse is added.
The 15 XP match reward is therefore roughly a quarter of what the bout pays anyway, and rung 1
totals ~65 XP against the 100 needed for level 2. That may be exactly right — the fight is the
reward and the purse is a nod — but it is worth knowing rather than discovering. The **pounds**
purse for rung 1 is still an owner slot, and it is the number with room to carry weight.

⚠ **Titles are the owner's words.** The importer scaffolds a `TITLE:` slot per rung; it does not
fill them. Same rule as quest and dialogue prose (CLAUDE.md §3).

---

## Art asks

Nothing is blocking, but three things are worth knowing:

- **Prince Mandrew has no subject.** He needs one to be anything other than a reskinned villager.
  [../art/ART_QUEUE.md](../art/ART_QUEUE.md) is where that ask belongs.
- **The arena interior is a bare box** until it is dressed, exactly like the six shells —
  `mat_dungeon_wall` and `mat_dungeon_floor` are placeholders. A sand floor and a stone ring would
  carry the whole fiction; that is a materials job, not a sheet job.
- **Tortured Neek has only an idle sheet.** He will slide and has no death pose. Either keep him
  off the ladder for now or accept it — an art gap, not a defect.

---

## Verification

Per CLAUDE.md §5: **nothing below can be checked without the editor.** What can be run agent-side
is reference integrity only, and it proves nothing about whether any of this works:

```bash
python Tools/asset_reachability.py --check-dangling
```

Routes for the owner, once each phase lands:

1. **Phase 0 gate.** Portal into `Quidland`, stand in front of the two stamped Neeks. Both should
   chase and neither should shove the other through a wall. Standing still means no NavMesh and the
   plan stops here.
2. **The door.** Walk to the castle in London, press USE, arrive in the lobby facing the marker's
   blue arrow. Walk back out and arrive at `castle_door`, not at the origin.
3. **The first bout.** Talk to Prince Mandrew, FIGHT, land in the pit, kill both Neeks, take 15 XP,
   land back in the lobby. Check the purse readout moves and the £ glyph renders rather than showing
   a missing-glyph box (CLAUDE.md §5 item 9).
4. **Both deaths counted.** Kill one Neek and check the bout does **not** end. Ending on the first
   kill means the controller is polling for survivors instead of counting `OnDeath`.
5. **The level actually applied.** Author rung 3 at level 8 and check the opponent is visibly
   tougher than rung 1's, *and* that its nameplate badge reads 8. A badge reading 8 over an
   opponent that dies in two hits is the `Instantiate`/`Awake` trap — the deactivated-holder step
   was lost.
6. **Defeat.** Lose a bout deliberately. Expect the lobby, full health, no purse, no rank change —
   **not** the death screen.
7. **The autosave.** Enter the arena, quit to desktop mid-bout, relaunch, Continue. Expect to
   arrive in London outside the castle. Arriving inside the pit means `NoAutosave` is not being
   read.
8. **Laundering.** Get to 1 knife, walk to the castle door, press USE. Expect a refusal. Being let
   in — and coming out clean — means the entry gate is not wired.
9. **Rank persistence.** Win two bouts, save, reload, and check Prince Mandrew still offers rung 3.
   Then load a save made *before* today and check it arrives unranked at rung 1 rather than
   failing.
10. **The window's pause.** Open Prince Mandrew's chat, pick FIGHT, close the arena window, and
    check the world is not frozen. A freeze is the merchant pause-ordering bug, repeated.
11. **Companion refusal.** Hire Alex, walk to Prince Mandrew, and check FIGHT refuses rather than
    letting a follower into the pit.
12. **The dialogue file owns his conversation.** Re-run `Tools → Content → Import Quests` and check
    `Dialogue_Mandrew.asset` regenerates with the arena choice intact — an `ARENA` directive lost in
    a re-import is the failure mode that folder's wholesale-regeneration rule creates.

---

## Explicitly out of scope

- **Chunk suspend/resume.** The arena wants a fresh pit each entry, so it needs none of
  [BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md).
  It does not advance that plan either.
- **Fixing the interior wanted-level hole.** Gated around, not fixed; handled separately.
- **Rerouting arrest to the police station.** Unrelated and already noted elsewhere.
- **Arena-specific loot tables.** Phase 4 at the earliest; the purse is the economy until then.
