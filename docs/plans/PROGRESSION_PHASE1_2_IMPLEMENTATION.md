# Implementation plan — Progression, Phases 1 and 2

**Status: implemented — Phases 1–2 are merged and live on `main`** (`PlayerSession.TotalXP`,
`EnemyLevel`, the kill-XP award in `Health`). Never seen by a compiler or the editor — see
CLAUDE.md §5. Derived from [PROGRESSION_SYSTEM.md](PROGRESSION_SYSTEM.md), whose owner decisions
are settled and are not reopened here. Phases 3–5 (auto growth, perks, loot bands) are
**out of scope**.

```
Grounded against: working tree on branch art-facing-and-density, 2026-08-08
Verification:     every claim below was read in the named file at the named line. No compiler,
                  no Unity, no test framework in this environment — see the Verification section.
```

---

## 1. Scope

**In**

- XP state on `PlayerSession`, level derived from it, never stored.
- Curve constants and helpers in `EKVibe`.
- One appended `SaveData` field (`TotalXP`) plus its write and restore sites.
- Quest XP: an appended `QuestReward.XP` and the payout call site.
- Kill XP attribution, **including the prerequisite fix that makes attribution possible at all**
  (§2.1 — the parent plan's assumption here is wrong today).
- Wiring the two dead level readouts: `LevelXpText` in the bag, and the HUD's `LevelText`.
- Phase 2: a new `EnemyLevel` component (option A, default `Level = 1`), HP/damage/XP scaling from
  the level-1 prefab baseline, nameplate showing the level.

**Out**

- Perks, `PerkData`, `PerkDatabase`, `SaveData.PerkIds`, the perk window, the
  `InventoryWin95Builder` PERKS button (all Phase 4/5).
- Per-level class stat growth and the `RestoreFromSave` derivation invariant (Phase 3).
- Loot bands (Phase 4).
- Authoring actual enemy levels on placed instances. The code lands neutral; setting levels is an
  owner editor pass (§9.3).
- The flat-armour balance question. It is a balance decision, not a code one; §7 flags it.

**Deliberate deviation from the parent plan, for the owner to accept or reject:** the parent plan
appends *both* `TotalXP` and `PerkIds` to `SaveData` in Phase 1. This plan appends **`TotalXP`
only**. Appends are safe at any time, so adding `PerkIds` in Phase 4 costs nothing, and shipping a
save key whose id vocabulary does not exist yet is the one way to get a save key wrong for free.

---

## 2. What was verified, and one thing the parent plan gets wrong

Confirmed as stated in the parent plan:

| Claim | Verified at |
|---|---|
| `PlayerSession` already owns wallet/inventory/equipment/visited/wiki with an `OnXChanged` + `RestoreX` convention | `Assets/Scripts/Flow/PlayerSession.cs:55-60, 267-292, 327-399` |
| `SaveData` appends are the house pattern; three lists were appended for equipment/map/wiki | `Assets/Scripts/Flow/SaveGameManager.cs:44-69` |
| `Health.Awake` does `CurrentHealth = MaxHealth` — the ordering trap | `Assets/Scripts/Combat/Health.cs:26-31` |
| `Health.LastAttacker` exists | `Assets/Scripts/Combat/Health.cs:24` |
| The player is identified by `GetComponent<CombatController>() != null` | `Assets/Scripts/Combat/Health.cs:50` |
| `EnemyNameplate.Level` exists, defaults to 3, is display-only | `Assets/Scripts/World/EnemyNameplate.cs:14, 72` |
| `GeneratedEnemyPrefabTool` hardcodes `plate.Level = 3` | `Assets/Editor/GeneratedEnemyPrefabTool.cs:316` |
| `QuestReward` has no XP field; `ApplyReward` is the payout site | `Assets/Scripts/Data/QuestDefinition.cs:64-76`; `Assets/Scripts/Quests/QuestConditionWatcher.cs:621-651` |
| `InventoryController.LevelText` is declared and never written | `Assets/Scripts/UI/InventoryController.cs:21` |
| `LevelXpText` is built with a static label | `Assets/Editor/InventoryWin95Builder.cs:164-170` |

New facts, checked here, that change the work:

1. ⚠️ **`Health.LastAttacker` is never set to the player.** The player's melee
   (`CombatController.cs:467`) and spell (`CombatController.cs:656`) both call the **three-argument**
   `TakeDamage(damage, attackerName, targetLabel)`, which forwards `attacker: null`
   (`Health.cs:38-41`). Only `EnemyAI.cs:341` passes a `GameObject`. So "grant XP only when the last
   attacker was the player" would today grant **nothing at all, silently**. Fixing the two call
   sites is a prerequisite commit, not a detail. *This is the correction the parent plan needs;
   `docs/plans/PROGRESSION_SYSTEM.md` owns that sentence and should be amended when this lands.*
2. **`InventoryController.LevelText` is unassigned in the scene** — `c.unity:70905` reads
   `LevelText: {fileID: 0}` — and `InventoryWin95Builder` never assigns it (the only `controller.`
   writes in that file are lines 30, 38, 440). So "wire the existing readout" is not a one-liner:
   without a runtime fallback the readout stays dead until an owner does an Inspector drag. §5.11
   solves it in code so no editor step is required.
3. **A second dead readout exists.** `UIManager.LevelText` **is** assigned in the scene
   (`c.unity:70942` → the `LevelText` GameObject at `c.unity:90407`) and `UIManager.SetLevel(int)`
   (`UIManager.cs:244-248`) is **called from nowhere**. It is a HUD level badge showing whatever was
   authored. Included here; it is three lines.
4. **`PlayerSession` has no scene or prefab instance.** `c.unity` contains zero references to it;
   `GameFlowController.EnsureSession` creates it at runtime with `new GameObject(...).AddComponent`
   (`GameFlowController.cs:69-73`). Consequence: **new public fields on `PlayerSession` carry no
   serialized-data blast radius at all** — their values come from the C# field initialiser every
   run. This is why `TotalXP` can be a plain public field like `Pounds`.
5. **All eleven nameplate-carrying prefabs store `Level: 3` explicitly on disk** — the six
   `Assets/Prefabs/Enemies/Enemy_*.prefab` and the five
   `Assets/Prefabs/ModernBritain/Police_*.prefab`. Changing the C# default does **not** change them.
   Option A's fallback therefore means a level-1 enemy keeps showing a "3" badge until the owner
   either adds `EnemyLevel` or edits the nameplate field. That is the status quo, not a regression,
   but say it out loud (§9.3).
6. **`EnemyAI.Damage` is read live at swing time** (`EnemyAI.cs:341`) and is not cached in
   `Awake` (`EnemyAI.cs:45-71`). So damage scaling has no ordering constraint; only health does.
7. **`docs/reference/SAVE_AND_SERIALIZATION.md` is stale.** Its "`SaveData` holds:" list stops at
   looted containers and omits `Equipment`, `VisitedChunks` and `UnlockedWikiEntries`, all of which
   are in `SaveGameManager.cs:44-69` today. That reference owns the fact; correcting it is part of
   this work (§6, commit 11).

---

## 3. Mapping table — serialized fields, save keys, enums

**No renames. No insertions. No enum changes. Every entry below is an append.** That is the whole
reason this table is short.

| # | Change | Kind | Storage | Files holding old data | Blast radius if got wrong |
|---|---|---|---|---|---|
| 1 | `SaveData.TotalXP` (`int`), appended **after** `UnlockedWikiEntries` | new serialized field | `persistentDataPath/savegame.json`, JSON key `TotalXP` | every existing save (key absent) | Absent key → `JsonUtility` yields `0` → level 1, correct. **If it were ever renamed later**, every player silently reverts to level 1 with no error. Never rename: `[FormerlySerializedAs]` does nothing for `JsonUtility` JSON keys — the field name *is* the key. |
| 2 | `QuestReward.XP` (`int`), appended **after** `ClearsWantedLevel` | new serialized field on a `[Serializable]` class inside a `ScriptableObject` | every `Assets/Resources/Quests/*.asset` | existing quest assets (field absent in YAML) | Absent → `0` → no XP, the correct default for quests authored before XP existed. Appending after the last field means no existing field shifts. A rename later needs `[FormerlySerializedAs]`, exactly as `PoundsAmount` already carries for `GoldAmount` (`QuestDefinition.cs:67`). |
| 3 | `PlayerSession.TotalXP` (`int`) | new public serialized field | **nowhere** — see §2.4 | none | None. `PlayerSession` is instantiated in code; no prefab or scene stores its fields. |
| 4 | New component `EnemyLevel` with `Level` (`int`, default 1) and `BaseXP` (`int`) | new script + new `.meta` GUID | not yet on any asset | none | ⚠️ **The `.meta` must be committed with the `.cs`.** Without it a fresh clone mints a new GUID and every prefab an owner later adds the component to loses it silently. |
| 5 | `EnemyNameplate.Level` | **unchanged** | 11 prefabs + `c.unity` | — | Explicitly *not* repurposed. Repurposing it is the rejected option B and would make every enemy in the game level 3 with no log. |
| 6 | `EKVibe` constants | `const` / `static readonly` in code | none | none | None — compile-time only, no serialized data. |

Save keys of the *string* class (`ChunkName`, `ItemID`, `EntryID`) are **not touched by this work**.
Phase 4 introduces one (`PerkData.PerkId`); when it does, it must be added to CLAUDE.md §3 alongside
the others. Nothing in Phases 1–2 needs that entry yet.

---

## 4. Curve and scaling constants (all in `EKVibe`)

Balance numbers, chosen to satisfy "EK-ish, cap ~20–25, steep". They are **free to retune later
without a save migration**, because level is derived from `TotalXP` on read and never stored — say
this in the code comment so the next person does not treat them as frozen.

```
MaxPlayerLevel      = 25
XPCurveFactor       = 100    // cumulative XP to reach level n = XPCurveFactor * (n-1)^2
                             // L2 = 100, L5 = 1,600, L10 = 8,100, L25 = 57,600
KillXPBase          = 25     // a level-1 enemy kill
EnemyHealthPerLevel = 0.35f  // MaxHealth * (1 + K*(Level-1))
EnemyDamagePerLevel = 0.25f
EnemyXPPerLevel     = 0.5f
```

Helpers, all pure static, all allocation-free (they are polled — §5.12):

- `int TotalXPForLevel(int level)` — cumulative threshold; `level <= 1` returns 0.
- `int LevelForXP(int totalXp)` — closed form `1 + floor(sqrt(totalXp / XPCurveFactor))`, clamped to
  `[1, MaxPlayerLevel]`. Closed form rather than a loop because §5.12 calls it every frame.
- `int XPIntoLevel(int totalXp)` and `int XPForNextLevel(int totalXp)` — the second returns `0` at
  the cap, and the UI must read `0` as "MAX", not as "0 XP needed".
- `int ScaledHealth / ScaledDamage / ScaledKillXP(int baseValue, int level)` — one shared
  `Mathf.RoundToInt(baseValue * (1 + K * (level - 1)))` shape, `level` clamped to `>= 1`.

---

## 5. File-by-file change list

### 5.1 `Assets/Scripts/Vibe/EKVibe.cs` — add only

A new `// --- Progression ---` block with everything in §4. No existing member is touched. `XpBar`
and `LevelBadge` colours already exist (`EKVibe.cs:33-34`) and are reused, not redefined.

### 5.2 `Assets/Scripts/Flow/PlayerSession.cs`

Add, modelled line-for-line on the wallet (`PlayerSession.cs:55-60, 267-292`):

- `[Header("Progression")] public int TotalXP;` with a comment that level is derived, never stored.
- `public event Action OnXPChanged;` and `public event Action<int> OnLevelUp;`
- `public int Level => EKVibe.LevelForXP(TotalXP);`, plus `XPIntoLevel` / `XPForNextLevel`
  pass-throughs so no UI does curve maths itself.
- `public void GrantXP(int amount, string source = null)` — ignores `amount <= 0` (same guard as
  `AddPounds`, `PlayerSession.cs:267-272`); captures `int before = Level`; adds; fires
  `OnXPChanged`; then fires `OnLevelUp` **once per level crossed** if `Level > before` — a single
  large grant can cross two, so loop rather than assume one.
- `public void RestoreTotalXP(int saved)` — `Mathf.Max(0, saved)` then `OnXPChanged`, mirroring
  `RestorePounds` (`PlayerSession.cs:288-292`).
- ⚠️ **`BeginNewGame` must zero it.** Add `TotalXP = 0; OnXPChanged?.Invoke();` next to
  `Pounds = 0;` (`PlayerSession.cs:130-131`). Missing this is a silent bug in two directions: a New
  Game started in the same app session inherits the last run's XP, **and** `RestoreFromSave` calls
  `BeginNewGame` first (`PlayerSession.cs:149`), so clear-then-restore is what makes load correct.

`EKVibe` is `GBHEngland.Vibe`; `PlayerSession.cs` does not currently import it. Add the `using`.

### 5.3 `Assets/Scripts/Flow/SaveGameManager.cs`

- `SaveData`: append `public int TotalXP;` **after** `UnlockedWikiEntries` (`SaveGameManager.cs:69`),
  with the same explanatory comment style as `Pounds` (`:47-50`). Nothing may be inserted above it.
- `Save()`: `data.TotalXP = session != null ? session.TotalXP : 0;` alongside `data.Pounds`
  (`SaveGameManager.cs:95`) — outside the `if (session != null)` block at `:109`, matching `Pounds`.

### 5.4 `Assets/Scripts/Flow/GameFlowController.cs`

One line in `ContinueFromSave`: `PlayerSession.Instance.RestoreTotalXP(data.TotalXP);` immediately
after `RestoreWikiEntries` (`GameFlowController.cs:211`). It must be **after** the `RestoreFromSave`
call at `:199` (which clears via `BeginNewGame`). It can go before or after the world builds — XP has
no Awake-ordering dependency of the kind `RestoreLootedContainers` has (`:205-208`).

### 5.5 `Assets/Scripts/Combat/CombatController.cs` — the attribution prerequisite

- Line 467: `targetHealth.TakeDamage(damage, "you", foeName, gameObject);`
- Line 656: `target.TakeDamage(ability.BaseDamage, shout, target.DisplayName, gameObject);`

The four-argument overload already exists (`Health.cs:43`). Nothing else changes: `LastAttacker` is
`[System.NonSerialized]` (`Health.cs:24`) and is assigned *before* the health subtraction
(`Health.cs:57`), so it is already correct at the moment `Die()` runs.

### 5.6 New file `Assets/Scripts/Combat/KillXP.cs` (+ `.meta`)

`internal static class KillXP` in `GBHEngland.Combat`, one method
`public static void AwardFor(Health victim)`, called from `Health.Die`. Kept out of `Health` so the
eligibility rules live in one greppable place and `Health` stays generic.

Rules, each with its reason in a comment:

1. `victim.LastAttacker == null` → return. Environmental or unattributed death.
2. `LastAttacker.GetComponent<CombatController>() == null` → return. This is the established player
   test (`Health.cs:50`); it keeps police-kills-civilian and enemy-kills-enemy from paying out.
3. `victim.GetComponent<EnemyAI>() == null` → return. Civilians, props, `LootChest`s and
   `SpriteContainer`s all carry `Health` but no AI; this is what stops a murdered shopkeeper paying.
4. `ai.IsPolice` → return. The parent plan's open item proposes no XP for police; this implements
   that proposal as one line so reversing it is one line. **Flag to owner** (§7).
5. Amount: Phase 1 uses `EKVibe.KillXPBase`. Commit 9 replaces that with
   `EKVibe.ScaledKillXP(level.BaseXP, level.Level)` when an `EnemyLevel` is present, falling back to
   `KillXPBase` when it is not.
6. `PlayerSession.Instance?.GrantXP(amount, victim.DisplayName)`.

### 5.7 `Assets/Scripts/Combat/Health.cs`

Two edits, both small, both load-bearing:

- In `Die()` (`Health.cs:86-105`), call `KillXP.AwardFor(this);` **after** `OnDeath?.Invoke()` and
  **before** `if (!DestroyOnDeath) return;`. After the event so `LootOnDeath` still opens its menu
  first; before the early return so a non-destroying enemy still pays.
- In `Awake()` (`Health.cs:26-31`), **before** `CurrentHealth = MaxHealth`:
  `GetComponent<EnemyLevel>()?.ApplyTo(this);` — the ordering trap, solved by call order rather than
  by `[DefaultExecutionOrder]`, as the parent plan recommends. Comment it as such: whoever next
  reorders that `Awake` needs to know why the call sits above that line.

### 5.8 New file `Assets/Scripts/Combat/EnemyLevel.cs` (+ `.meta`) — Phase 2

Shape: `[RequireComponent(typeof(Health))] public class EnemyLevel : MonoBehaviour` in
`GBHEngland.Combat`, with `public int Level = 1;` (authored per placement),
`public int BaseXP = EKVibe.KillXPBase;` (the same initialiser style `WorldActorVisual.Height` uses
for `EKVibe.CharacterHeight`), a private `_applied` flag, and one method
`public void ApplyTo(Health health)` called from `Health.Awake`.

`ApplyTo` must:

- return immediately if `_applied`, then set it — a second call must never re-multiply;
- clamp `Level` to `>= 1`;
- return without touching anything when `Level <= 1`, so an authored default-1 component is exactly
  as inert as no component at all;
- set `health.MaxHealth = EKVibe.ScaledHealth(health.MaxHealth, Level)` — the prefab value **is** the
  level-1 baseline, read once and overwritten once;
- scale `EnemyAI.Damage` the same way if an `EnemyAI` is present (no ordering constraint — §2.6);
- deliberately **not** touch `MoveSpeed` or the `NavMeshAgent`. Agent tuning is physical, not power.

Absent component means level 1 means nothing scales. That is what makes this commit land neutral
across all eleven existing prefabs and every placed instance.

### 5.9 `Assets/Scripts/World/EnemyNameplate.cs` — Phase 2

In `Build()` (`EnemyNameplate.cs:54-92`), replace `Level.ToString()` at line 72 with a value resolved
from `GetComponent<EnemyLevel>()` when one is present, falling back to the field otherwise. The file
already imports `GBHEngland.Combat` (line 3), so no new `using`.

Leave the `Level` field and its default of 3 alone (mapping row 5). Note in its tooltip that it is a
**display-only fallback** used when no `EnemyLevel` is present. The badge is built once in `Awake`
and never refreshed in `LateUpdate`, which is fine: level does not change at runtime in this phase.

Known cosmetic consequence, accepted: until an owner adds `EnemyLevel`, existing enemies keep showing
a "3" badge while being level 1. Unchanged from today.

### 5.10 `Assets/Editor/GeneratedEnemyPrefabTool.cs` and `Assets/Editor/BanditPracticeSpawner.cs`

- `GeneratedEnemyPrefabTool.cs:314-317`: change `plate.Level = 3;` to `plate.Level = 1;` and update
  the comment. This affects **only newly created prefabs** — the tool's update path never touches the
  nameplate, stated in its header comment (`:332-336`) and true of the code at `:342-399`.
- `BanditPracticeSpawner.cs:74-75`: same change, same reason.
- `TutorialSequence.cs:173-174` already sets `plate.Level = 1` at runtime. No change.

Neither tool gains an `EnemyLevel` component in this phase. Adding one at generation time would put a
level on eleven prefabs whose levels the owner has not decided, which is exactly the class of silent
change this plan exists to avoid.

### 5.11 `Assets/Scripts/UI/InventoryController.cs` — the bag readout

- In `Awake`, after the existing button wiring: if `LevelText == null`, resolve it by name using the
  helper already in the file — `FindChildByName(InventoryUIPanel.transform, "LevelXpText")` then
  `GetComponent<TextMeshProUGUI>()` (`InventoryController.cs:234-241`). **This is what makes the
  readout work with no editor step**, given the scene reference is `fileID: 0` (§2.2).
- New `RefreshLevel()` writing the three-line shape the builder authored
  (`InventoryWin95Builder.cs:166`): player level, current XP, XP to next level — printing `MAX` when
  `XPForNextLevel` is 0.
- Call it from `RefreshUI()` (`:389`) next to `RefreshCurrency()`, and subscribe
  `PlayerSession.OnXPChanged` in `EnsureInventorySubscription` (`:106-113`) with the matching
  unsubscribe in `OnDestroy` (`:95-103`). ⚠️ Subscribing without unsubscribing leaks a dead handler
  across reloads — the existing three events show the required pairing.
- The handler follows `HandlePoundsChanged` (`:127-132`), **not** `HandleInventoryChanged`: refresh
  unconditionally rather than gating on `IsOpen`, so opening the bag after a kill cannot show a
  stale figure.

### 5.12 `Assets/Scripts/UI/UIManager.cs` — the HUD badge

Poll, do not subscribe: `UIManager` already polls in `Update` (`RefreshSpellSlots`,
`UIManager.cs:99-101`), and polling avoids subscribing to a `DontDestroyOnLoad` singleton that may
not exist when `Start` runs.

Add `private int _shownLevel = -1;`, and in `Update` read `PlayerSession.Instance?.Level`, compare to
`_shownLevel`, and only on a change call the existing `SetLevel(level)` (`:244-248`) and store it.
⚠️ **Do not call `SetLevel` unconditionally each frame** — `level.ToString()` allocates a string per
frame on a mobile hot path, which CLAUDE.md §2 forbids. The int compare is the whole point of the
cached field.

### 5.13 `Assets/Editor/InventoryWin95Builder.cs`

Minimal: replace the now-false comment at `:164` and leave the placeholder text as the pre-runtime
state. Optionally also assign `controller.LevelText = level;`, guarded by
`Undo.RecordObject(controller, ...)` and `EditorUtility.SetDirty(controller)`, so the scene holds a
real reference after the next tool run. That assignment is a **convenience, not the mechanism** —
5.11's runtime fallback is what guarantees the readout works, and it must not be dropped in favour
of this.

### 5.14 `Assets/Scripts/Data/QuestDefinition.cs`

Append to `QuestReward`, after `ClearsWantedLevel` (`:75`): a tooltipped `public int XP;` meaning
"XP granted on completion; leave at 0 for none". An `int` adds nothing to the build dependency
graph, so the "this type ships in every build" warning at `:84-89` is respected.

### 5.15 `Assets/Scripts/Quests/QuestConditionWatcher.cs`

In `ApplyReward` (`:621-651`):

- add `bool paysXP = reward.XP > 0;`
- extend the deferral guard at `:629` to
  `if ((paysItem || paysPounds || paysXP) && PlayerSession.Instance == null) return false;`
  ⚠️ Missing this is the silent failure: an XP-only reward would return `true`, the caller would set
  `RewardsClaimed` (`:601-607`), and the XP would be lost forever with no log. The all-or-nothing
  contract in the method's own doc comment (`:613-620`) is exactly about this.
- grant with `if (paysXP) PlayerSession.Instance.GrantXP(reward.XP, quest.Id);` next to the
  `AddPounds` call at `:635-636`.

---

## 6. Documentation changes (part of the work, not an aside)

- `docs/reference/SAVE_AND_SERIALIZATION.md` — owner of the save format. Two edits: correct the
  "`SaveData` holds:" list, which omits `Equipment`, `VisitedChunks` and `UnlockedWikiEntries`
  (§2.7), and add `TotalXP` to it. Update the `Last verified against:` header, keeping the scope
  honest — code-read, not Unity-tested.
- `docs/plans/PROGRESSION_SYSTEM.md` — amend the Phase 1 kill-XP bullet, which asserts `LastAttacker`
  is ready to use. It is not (§2.1). Replace the wording; do not annotate beside it.
- `docs/README.md` — add this file to the active plans table.
- **Not** CLAUDE.md. Nothing here adds a string save key. Phase 4's `PerkId` will.

---

## 7. Silent failure modes, and how the implementer avoids each

| # | Failure | Why it is silent | Guard |
|---|---|---|---|
| 1 | Kill XP never fires | `LastAttacker` is null for every player hit today (§2.1). No exception, no log — just no XP, forever | Commit 4 lands **before** commit 5; the owner check in §9.3 is "kill something and watch the number move" |
| 2 | New Game inherits the last run's XP | `BeginNewGame` clears every other piece of state; a missed `TotalXP = 0` looks like nothing at all until a second playthrough starts mid-level | §5.2, next to `Pounds = 0` |
| 3 | Load resets XP to 0 | `RestoreFromSave` calls `BeginNewGame`, which clears; without `RestoreTotalXP` after it every load silently de-levels the player | §5.4, placed after `:211` |
| 4 | Enemies spawn at partial health | `Health.Awake` sets `CurrentHealth = MaxHealth`; scaling after it leaves a level-5 enemy at level-1 HP under a raised max — reads as a health-bar bug, not a scaling bug | §5.7: the `ApplyTo` call sits above that line, with a comment saying why |
| 5 | Scaling applied twice | Compounding 1.35 x 1.35 with nothing to show it happened | `_applied` flag in `ApplyTo` |
| 6 | Every enemy becomes level 3 | The `EnemyNameplate.Level` trap: all 11 prefabs store 3 on disk (§2.5). Repurposing that field scales the whole cast with no log | Option A. `EnemyNameplate.Level` is never read as a level. The reviewer should grep `.Level` on `EnemyNameplate` and confirm the only read is the display fallback at `:72` |
| 7 | XP-only quest reward claimed and lost | `ApplyReward` returns `true`, the caller sets `RewardsClaimed` | §5.15, extend the null-session guard |
| 8 | Bag readout stays dead | `LevelText` is `fileID: 0` and no tool assigns it; the code looks correct and shows nothing | §5.11 runtime name fallback, which depends on no tool run |
| 9 | Per-frame string allocation on the HUD | Nothing fails; it just allocates on a mobile hot path, against CLAUDE.md §2 | §5.12 `_shownLevel` int compare |
| 10 | Handler leak from the new event | No error; a destroyed `InventoryController` keeps receiving events after a reload | §5.11 subscribe/unsubscribe pairing |
| 11 | A new script's `.meta` not committed | A fresh clone re-mints the GUID and any prefab carrying `EnemyLevel` loses it silently | Both new `.cs` files committed **with** their `.meta` (mapping row 4) |
| 12 | Civilian or shopkeeper kills pay XP | Would quietly make murder the optimal grind | §5.6 rule 3, requiring an `EnemyAI` |

**Two balance items for the owner — flagged, not decided here:**

- Police kills grant no XP (§5.6 rule 4), per the parent plan's proposal. One line to reverse.
- Flat armour versus scaled enemy damage. `Health.TakeDamage` subtracts `TotalArmor()` flat and
  floors at 0 (`Health.cs:50-55`), so with a filled paper doll a low-level enemy literally cannot
  connect. Phase 2 sharpens that, it does not soften it. No code here attempts to solve it.

---

## 8. Commits, in dependency order

Each is coherent alone; none leaves the tree in a state where a half-feature silently misreports.

| # | Commit | Contents |
|---|---|---|
| 1 | Add the XP curve constants to EKVibe | §5.1. No behaviour change; nothing calls it yet |
| 2 | Give PlayerSession its XP total and derived level | §5.2, including the `BeginNewGame` reset |
| 3 | Persist the XP total | §5.3 + §5.4 — append, write, restore. The save round-trips before anything can grant XP |
| 4 | Attribute player hits to the player | §5.5 only. Self-contained fix; must precede commit 5 |
| 5 | Grant XP for a kill | §5.6 + the `Die()` half of §5.7 |
| 6 | Pay quest XP | §5.14 + §5.15 |
| 7 | Show the level and XP in the bag and on the HUD | §5.11, §5.12, §5.13 |
| 8 | Add the EnemyLevel component | New file + `.meta` (§5.8) + the `Awake` half of §5.7. Neutral: nothing carries the component yet |
| 9 | Scale kill XP by enemy level | §5.6 rule 5 switched to `ScaledKillXP` |
| 10 | Show the enemy's real level on its nameplate | §5.9 + §5.10 |
| 11 | Update the save reference and the parent plan | §6 |

Commits 1–7 are Phase 1 and are independently playable. Commits 8–10 are Phase 2.

---

## 9. Verification

### 9.1 What can be proved in this environment

```bash
python Tools/asset_reachability.py --check-dangling   # run before AND after; exit 0 is clean
```

Nothing in this plan deletes, moves or renames an asset, so the result should read identically before
and after. Two new `.cs` + `.meta` pairs are added; **a new GUID appearing as dangling would mean a
`.meta` was committed without its script, or the reverse.** On a machine without `Library/` the tool
exits `2` ("couldn't verify") — that is not a pass.

A brace/paren balance scan of the edited `.cs` files catches a truncated edit. **It is not a compile
and must not be reported as one.**

### 9.2 What cannot be proved here

Everything else. There is no C# compiler, no Unity and no test framework. In particular: that the
project builds; that `LevelForXP`'s closed form agrees with `TotalXPForLevel` at every boundary
(check L2, L5 and L25 by hand in play); and every behaviour listed below.

### 9.3 Owner checks in the editor, with routes

**Stop Play mode before any Inspector edit — changes made during Play are discarded** (CLAUDE.md §5).

1. **It compiles.** Unity, wait for the recompile to finish, then Window → General → Console, Clear,
   and confirm no red. Nothing below means anything until this passes.
2. **A pre-progression save still loads.** Before pulling, copy
   `%USERPROFILE%\AppData\LocalLow\<company>\GBH England\savegame.json` somewhere safe (the
   folder is whatever `Application.persistentDataPath` reports on that machine). ⚠️ **`productName`
   changed on 2026-08-16**, so any save written before that date is under the old
   `…\Exiled Alvaston\` folder and will not be found — that orphaning was accepted deliberately, see
   [NAME_UNIFICATION_PLAN.md](NAME_UNIFICATION_PLAN.md). Then Play → title
   screen → **Continue**. The character should load with wallet, gear, map and WIKIBRITAIN intact,
   and the bag should read **Player level: 1, Current XP: 0**. Then cross one chunk edge, which
   autosaves, and reopen the JSON: it should now contain a `TotalXP` key.
3. **Kill XP.** Play, reach an enemy, kill it. Press **I** for the bag: `Current XP` should be up by
   25 and `XP to next level` down by 25. Watch the HUD's small `LevelText` badge tick to 2 at 100 XP.
   ⚠️ If XP stays at 0 after a kill, commit 4 did not land — check `CombatController.cs:467` passes
   `gameObject`.
4. **Nobody else pays.** Kill a civilian, and if reachable let a police officer die. Neither should
   move the XP figure.
5. **Quest XP.** Project → `Assets/Resources/Quests/` → select a `QuestDefinition` → Inspector, under
   **Reward**: confirm a new **XP** field reading **0**, and that **Pounds Amount** still reads its
   authored value. A 0 there would mean the append disturbed something — restore from git rather than
   retyping. Set XP to 200, complete that quest in Play, and check the bag.
6. **Enemy levels.** Exit Play. For a **single placement**: Project →
   `Assets/Prefabs/Chunks/<chunk>.prefab` → double-click to open Prefab Mode → Hierarchy → select the
   enemy instance → Inspector → **Add Component** → *Enemy Level* → set **Level** to 5 → Ctrl+S. For
   **every instance of a type**, do the same on `Assets/Prefabs/Enemies/Enemy_Roadman.prefab`, aware
   that it hits every placement everywhere. Then Play into that chunk: the Lv5 one should visibly
   tank longer and hit harder than an untouched one, its badge should read **5**, and killing it
   should pay more XP than an unlevelled one of the same prefab.
7. ⚠️ **The level-3 check.** Before adding any `EnemyLevel`, walk past several enemies and confirm
   they still die in the same number of hits as before this work. Badges will still read "3" — that
   is the pre-existing display value in all eleven prefabs, not a level. If enemies became *tougher*
   without anyone adding a component, `EnemyNameplate.Level` is being read as a real level somewhere
   and the change must be reverted.
8. **The cap.** Not reachable in normal play. The honest check is a temporary `GrantXP(60000)` behind
   a debug key — and that key must not be committed.

### 9.4 Known gap

`XPForNextLevel` returning 0 at level 25, rendered as `MAX` by §5.11, is exercised by nothing in
Phases 1–2. It stays **unverified** until either the cap is reached or the curve constants are
lowered temporarily to test it. Report it that way rather than implying it was checked.
