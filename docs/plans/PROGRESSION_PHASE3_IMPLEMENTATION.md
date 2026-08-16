# Implementation plan — Progression, Phase 3 (player gains)

**Status: plan only, nothing implemented.** Phases 1 and 2 are merged and live on `main`; this
builds on the code that actually exists, not on what the parent plan predicted. Phase 4 (loot
tiers) is **out of scope**.

```
Grounded against: main @ 70dbb41, 2026-08-08
Verification:     every claim below was read in the named file at the named line. There is no C#
                  compiler, no Unity and no test framework in this environment — see §10.
```

---

## 1. Scope

**In**

- Per-class automatic stat growth per level (`PlayerClassInfo.GrowthPerLevel`).
- The **derivation path**: one deterministic `RecalculateDerivedStats()` on `PlayerSession`,
  recomputed identically on new game, on load, on level-up and on perk spend.
- `PerkData` + `PerkEffect` + `PerkEffectType` (append-only enum) + `PerkDatabase`.
- `SaveData.PerkIds` — the appended save-key list deliberately deferred out of Phase 1.
- Armour becomes **proportional**, plus the balance mapping for the gear already authored.
- Perk effect application: stat-facing through the derivation, combat-facing through cached
  query fields read at hit time.
- `PerkWindowUI` — a `Win95Skin` window shaped like `WikiBritainUI`, and the button that opens it.
- The doc corrections this work forces (§8).

**Out**

- Loot bands / `LootOnDeath` tiers (Phase 4).
- Any crime-layer perk (concealment, pickpocket, wanted decay). Owner's settled exclusion.
- **All perk prose.** Perk titles, descriptions and the level-up toast line are the owner's own
  work (CLAUDE.md §3). Everything this plan ships carries a placeholder string, marked as such in
  the code, and §7.4 tells the owner exactly where to write.
- Authoring any actual `PerkData` asset. The machinery lands with **zero** perk assets on disk, so
  the window opens and honestly says the list is empty. Authoring is an owner pass (§10.3).
- Trait auto-growth — see §3.2 for why, and the alternative if the owner disagrees.

---

## 2. What was verified, and four things the parent plan gets wrong

Confirmed against live code:

| Claim | Verified at |
|---|---|
| `RestoreFromSave` calls `BeginNewGame`, which calls `ApplyClassDefaults` | `Assets/Scripts/Flow/PlayerSession.cs:176`, `:170` |
| `ContinueFromSave` order is `RestoreFromSave` -> restores -> `RestoreTotalXP` -> `BindPlayerToSession` | `Assets/Scripts/Flow/GameFlowController.cs:199, 215, 220` |
| `BindPlayerToSession` pushes `RuntimeStats.MaxHealth` onto `Health` and `CombatController` | `Assets/Scripts/Flow/GameFlowController.cs:155-169` |
| Melee damage is `Strength*2+5` then `+ weapon.Damage` | `Assets/Scripts/Combat/CombatController.cs:436, 441` |
| Spell damage is `ability.BaseDamage`, unmodified | `Assets/Scripts/Combat/CombatController.cs:660` |
| `Health.TakeDamage` subtracts `TotalArmor()` flat, floored at 0, player only | `Assets/Scripts/Combat/Health.cs:57-62` |
| `TotalArmor()` sums `ItemData.Armor` over the doll | `Assets/Scripts/Flow/PlayerSession.cs:494-500` |
| `SaveData` ends at `TotalXP`; appends are the house pattern | `Assets/Scripts/Flow/SaveGameManager.cs:44-81` |
| `WikiEntryData.EntryID` is the save-key precedent to copy | `Assets/Scripts/Data/WikiEntryData.cs:21-29` |
| `WikiDatabase` is the Resources-lookup precedent to copy | `Assets/Scripts/Data/WikiDatabase.cs:45-61` |
| `PlayerSession.OnLevelUp` exists and has **no consumer** | `Assets/Scripts/Flow/PlayerSession.cs:72`; grep across `Assets/Scripts` finds only the declaration and the raise |
| The bag's right rail is genuinely full — backpack occupies y 0.34–0.948, top rail slot is 0.245–0.305 | `Assets/Editor/InventoryWin95Builder.cs:390, 448, 462`; `InventoryController.cs:187-188` |
| The rebuild tool's menu path | `Assets/Editor/InventoryWin95Builder.cs:26` — `Tools/UI/Rebuild Inventory Panel (Win95)` |
| Speed modifiers compose by source and are cached, not walked per frame | `Assets/Scripts/Combat/CombatController.cs:219-249` |

New facts, checked here, that change the work:

1. ⚠️ **`Resistances` is not "barely used" — it is not used at all.** The only read of
   `BaseResistances` outside the assignment in `PlayerSession.cs:166` is a text readout at
   `Assets/Scripts/UI/InventoryController.cs:452-459`. Nothing in `Health.TakeDamage` consults it.
   A v1 perk that raises a resistance would change a number on the character sheet and nothing
   else. **This plan makes `BaseResistances.Physical` real** by feeding it into the armour formula
   (§4), which is also the only reading that makes the existing readout honest — see fact 2. The
   other four (Fire, Cold, Poison, Magic) have no damage-type system to attach to and stay
   cosmetic; **no v1 perk should touch them** (§5.2).
   *`docs/plans/PROGRESSION_SYSTEM.md` owns that sentence and must be corrected (§8).*

2. ⚠️ **The character sheet already lies.** `InventoryController.cs:455` prints
   `BaseResistances.Physical + TotalArmor()` as one **Armor** figure, but only `TotalArmor()`
   reduces damage (`Health.cs:61`). Today `Physical` is 0 for every class so nobody has noticed.
   Wiring `Physical` into the formula fixes the readout rather than changing it.

3. ⚠️ **There is no player ranged attack.** `CombatController` has exactly two damage sites: melee
   (`:470`) and spell (`:660`). `RangedCaster` is an `EnemyAI` field (`EnemyAI.cs:22`), enemy-only.
   The owner's settled effect set names "melee/ranged/spell damage"; **ranged has no call site to
   read it at hit time.** Recommendation in §5.2; correction to the parent plan in §8.

4. ⚠️ **The perk button does *not* need an editor step.** The parent plan says it does, because
   `InventoryWin95Builder` builds the bag. But `InventoryController.BuildSpellsButton`
   (`InventoryController.cs:179-209`) already creates the SPELLS rail button **at runtime in
   `Awake`**, styled through `Win95Skin.StyleButton`, and the tool explicitly documents that
   arrangement (`InventoryWin95Builder.cs:439-440`). PERKS follows that precedent and works the
   moment the code compiles. §6.2. *Correction to the parent plan (§8).*

Three smaller facts that shape specific decisions:

5. **`ApplyClassDefaults` does not reset `BaseResistances` or `BaseMovementSpeed`**
   (`Assets/Scripts/Data/CharacterData.cs:48-55`). `BaseResistances` is written once from the
   template (`PlayerSession.cs:166`) and `BaseMovementSpeed` is guarded by `if (<= 0)`. Any
   derivation that *adds* to either would compound on every recompute. This is the single nastiest
   trap in Phase 3 — §3.1 and §9 row 2.
6. **Only one `ItemData` asset in the whole repo has non-zero `Armor`.** Seven assets reference
   `ItemData.cs` (guid `7fc51ae09f9646d48896705b87b1ac3f`), all under `Assets/Resources/Items/`;
   `TestRing.asset:23` reads `Armor: 4` and the other six read `Armor: 0`. The armour balance
   migration is therefore one row, not a re-authoring pass — §4.3.
7. **`SpriteContainer` rolls its band in `Awake`**, not on open (`SpriteContainer.cs:150, 158`). An
   extra-loot-roll perk taken mid-run affects only containers instantiated *after* it is taken.
   Acceptable, but it must be stated rather than discovered — §5.4.

---

## 3. The derivation invariant — fix once, document once

### 3.1 The order of operations

`PlayerSession` gains one method that is the **only** place derived stats are computed:

```
RecalculateDerivedStats()
  1. RuntimeStats.ApplyClassDefaults(Class)        // resets BaseTraits, MaxHealth, MaxManaStamina
  2. RuntimeStats.BaseResistances = copy of _baselineResistances   // ⚠ ApplyClassDefaults does NOT
  3. + (Level - 1) * GrowthPerLevel(Class)         // auto growth: MaxHealth, MaxManaStamina
  4. + perk FLAT adds                              // MaxHealthFlat, ArmourFlat, MaxResourceFlat
  5. * perk PERCENT multipliers                    // MaxHealthPercent, ...
  6. cache the combat/utility query values         // melee/spell multipliers, extra loot rolls
  -- equipment is NOT folded in; it is read live at its two use sites --
  7. fire OnStatsChanged
```

Every step overwrites, none accumulates. Calling it twice in a row must produce byte-identical
results — that property is what makes it safe to call from five places.

**Step 2 is the trap.** `_baselineResistances` is a new private `Resistances` field on
`PlayerSession`, captured in `BeginNewGame` from `template.BaseResistances` at the point where
line 166 assigns it today. Without it, a perk adding `+5 Physical` adds 5 more on every recompute —
five level-ups later the player has +25 and nothing logged it.

**Equipment stays out**, per the owner's instruction. It is read live at exactly two places —
`CombatController.cs:439-441` for weapon damage and `Health.cs:57-62` for armour — and both are
untouched by this. Folding equipment into `RuntimeStats` would double-count against both.

### 3.2 Auto growth

New in `Assets/Scripts/Data/PlayerClass.cs`, next to `StartingTraits`:

```csharp
[System.Serializable] public class LevelGrowth { public int MaxHealth; public int MaxManaStamina; }
public static LevelGrowth GrowthPerLevel(PlayerClass c)
```

| Class | HP/level | Resource/level | HP at L25 | Resource at L25 |
|---|---|---|---|---|
| YoungDriller | 6 | 3 | 100 -> 244 | 55 -> 127 |
| Stabmeister | 7 | 2 | 120 -> 288 | 50 -> 98 |
| MrHood | 5 | 3 | 90 -> 210 | 60 -> 132 |
| Dynamo | 4 | 5 | 85 -> 181 | 80 -> 200 |
| BundaBasher | 9 | 2 | 160 -> 376 | 40 -> 88 |

Starting values verified at `PlayerClass.cs:101-126`. Sanity check against Phase 2's enemy scaling:
a level-25 Roadman does `7 * (1 + 0.25*24) = 49` (`EKVibe.EnemyDamagePerLevel = 0.25f`;
`Enemy_Roadman.prefab:124` `Damage: 7`). BundaBasher takes ~7.7 hits, Dynamo ~3.7, before armour.
Tunable, and tuning costs nothing — these are code constants, not save data.

⚠️ **Traits deliberately do not auto-grow.** `CombatController.cs:436` reads
`BaseTraits.Strength * 2 + 5`. At +1 Strength per level a level-25 Young Driller swings for 67
before weapon or perks, against 19 at level 1 — that retunes the entire enemy roster at once.
Traits are perk territory in v1. **If the owner wants trait growth**, the honest shape is a
"point every N levels" divisor rather than a per-level integer, and the enemy damage/health
constants need revisiting in the same change. Flagged, not decided here.

### 3.3 Where `RecalculateDerivedStats` is called

| Call site | Why |
|---|---|
| End of `PlayerSession.BeginNewGame`, after `ApplyClassDefaults` (`:170`) | new game — level 1, no perks, so near-identity, but it must run so there is one code path |
| End of `PlayerSession.RestoreTotalXP` (`:345-349`) | load — the level is now known |
| End of `PlayerSession.RestorePerkIds` (new) | load — the perks are now known |
| Inside `GrantXP` (`:331-342`), once, **after** the level-up loop, only if the level changed | level-up mid-run |
| End of `SpendPerkPoint` (new) | perk taken mid-run |

Because it is idempotent, `ContinueFromSave` calling it twice (once via `RestoreTotalXP:215`, once
via the new `RestorePerkIds`) is harmless — and `BindPlayerToSession` at `GameFlowController.cs:220`
still runs after both, so the load path already pushes the final figures onto the player.

### 3.4 Propagating to the live player

`RuntimeStats.MaxHealth` changing is not enough: the running player's `Health.MaxHealth` and
`CombatController.CurrentHealth` are separate values, and `BindPlayerToSession` only runs on
new-game and load. A mid-run level-up needs a push.

Add `public event Action OnStatsChanged;` to `PlayerSession`, fired at the end of
`RecalculateDerivedStats`. `CombatController` subscribes in `Start` (not `Awake` — `PlayerSession`
may not exist yet; it is created by `GameFlowController.EnsureSession`, `GameFlowController.cs:69-73`)
and unsubscribes in `OnDestroy`, using the same subscribe/unsubscribe pairing
`InventoryController.cs:106-126` uses.

The handler:

- `int delta = newMax - _health.MaxHealth;`
- `_health.MaxHealth = newMax;`
- if `delta > 0`, `_health.CurrentHealth += delta` (clamped to the new max), so levelling **grants
  the new hit points without being a free full heal**. State this in the comment: the alternative
  (full heal on level-up) is a design choice, not an accident, and someone will otherwise "fix" it.
- refresh the `CurrentMana`/`CurrentStamina` caps the same way — both are clamped against
  `PlayerData.MaxManaStamina` at `CombatController.cs:156, 163, 171`.
- regen: multiply the authored `ManaRegenPerSecond` / `StaminaRegenPerSecond` (`:48, 50`) by
  `session.ResourceRegenMultiplier`. ⚠️ These are serialized prefab fields, so the handler must
  multiply a **remembered baseline** captured in `Awake`, not the current value — otherwise every
  level-up compounds the multiplier.
- move speed: `CombatController.SetSpeedMultiplier(session, session.MoveSpeedMultiplier)`
  (`:226-231`). ⚠️ **Do not write `MovementSpeed` directly** — its own tooltip (`:31-32`) says treat
  it as read-only at runtime, and writing it corrupts the crouch/vehicle composition the modifier
  system exists to protect (`:215-218`). Registering with the session as the key replaces rather
  than stacks.

---

## 4. Armour becomes proportional

### 4.1 The formula

New in `EKVibe`, in the existing `// --- Progression ---` block (`EKVibe.cs:109`):

```
ArmourSoftCap      = 20     // armour equal to this halves incoming damage
ArmourMaxReduction = 0.75f  // never more than three-quarters off

static float ArmourReduction(int armour) =>
    armour <= 0 ? 0f
    : Mathf.Min(ArmourMaxReduction, (float)armour / (armour + ArmourSoftCap));
```

New on `PlayerSession`, replacing nothing:

```csharp
/// <summary>Worn armour plus derived Physical resistance — the single number the formula reads.</summary>
public int EffectiveArmour() =>
    TotalArmor() + (RuntimeStats != null ? RuntimeStats.BaseResistances.Physical : 0);
```

`Health.TakeDamage` (`Health.cs:57-62`) becomes, keeping the same player gate:

```csharp
if (GetComponent<CombatController>() != null && damage > 0)
{
    var session = Flow.PlayerSession.Instance;
    if (session != null)
        damage = Mathf.Max(1,
            Mathf.RoundToInt(damage * (1f - EKVibe.ArmourReduction(session.EffectiveArmour()))));
}
```

Three things in that snippet are load-bearing:

- the `damage > 0` guard — without it a 0-damage call would be floored **upward** to 1 and start
  hurting the player. There is no such caller today, but `TakeDamage(int)` is public (`Health.cs:40`).
- `Mathf.Max(1, …)` is the owner's "a hit always lands for something".
- `Health.cs` needs `using ExiledAlvaston.Vibe;` added — it currently imports only `UnityEngine`,
  `UnityEngine.Events` and `ExiledAlvaston.UI` (`Health.cs:1-3`).

Perk armour flows in through `BaseResistances.Physical` (§5.2), so it also appears in the bag's
Armor line automatically — no UI change needed, and fact 2's discrepancy closes.

### 4.2 Old value to new value, at the numbers that actually exist

Against a level-1 Roadman (`Damage: 7`, `Enemy_Roadman.prefab:124`) and an Occult Commander
(`Damage: 30`, `Police_OccultCommander.prefab:206`):

| Effective armour | Old: dmg from 7 | New: dmg from 7 | Old: dmg from 30 | New: dmg from 30 | New reduction |
|---|---|---|---|---|---|
| 0 | 7 | 7 | 30 | 30 | 0% |
| **4** (TestRing today) | **3** | **6** | 26 | 25 | 16.7% |
| 8 | 0 — **whiff** | 5 | 22 | 21 | 28.6% |
| 12 | 0 — whiff | 4 | 18 | 19 | 37.5% |
| 20 | 0 — whiff | 4 | 10 | 15 | 50.0% |
| 40 | 0 — whiff | 2 | 0 — whiff | 10 | 66.7% |
| 60+ | 0 — whiff | 2 | 0 — whiff | 8 | 75% (cap) |

The cliff the change exists to remove is visible at armour 8: today a second armour piece makes a
Roadman literally unable to connect, and Phase 2's `EnemyDamagePerLevel` sharpens that rather than
smoothing it.

### 4.3 Which assets need re-authoring, and by whom

**None.** Verified: seven `ItemData` assets exist in the repo, all under
`Assets/Resources/Items/`; `TestRing.asset:23` is the only one with `Armor` above 0, at 4. Under
`ArmourSoftCap = 20` a 4 still reads as a meaningful 16.7% reduction, so no asset edit is required
for the change to land coherently.

`ArmourSoftCap = 20` was chosen **specifically** so that no asset needs re-authoring. The
alternative worth naming: a softer cap (50) gives more integer headroom for future gear tiers but
makes TestRing's 4 worth 7.4%, at which point the owner would want it re-authored upward. That is
a balance call, not a code one — **the owner's, not the implementer's.** If the owner picks 50, the
single required edit is Project, `Assets/Resources/Items/TestRing.asset`, Inspector,
**Armor** 4 to 12, with Play mode stopped.

**Authoring guidance to record for future gear** (at soft cap 20): a light piece ~3-5, a heavy
piece ~8-12, a full endgame doll landing around 40-60 effective, i.e. 67-75%.

---

## 5. Perks

### 5.1 The data

New file `Assets/Scripts/Data/PerkData.cs` (+ `.meta`), namespace `ExiledAlvaston.Data`, modelled
on `WikiEntryData.cs`:

```csharp
public enum PerkEffectType { ... }        // append-only — see 5.2

[System.Serializable]
public class PerkEffect { public PerkEffectType Type; public float Magnitude; }

[CreateAssetMenu(fileName = "NewPerk", menuName = "GBH England/Data/Perk")]
public class PerkData : ScriptableObject
{
    public string PerkId;                  // SAVE KEY — never rename once shipped
    public string Title;                   // owner's copy
    [TextArea] public string Description;  // owner's copy
    public PlayerClass[] AllowedClasses;   // empty = any class, mirroring ItemData.AllowedClasses
    public int MinLevel = 2;
    public PerkData Prerequisite;          // null = none
    public List<PerkEffect> Effects = new List<PerkEffect>();
}
```

New file `Assets/Scripts/Data/PerkDatabase.cs` (+ `.meta`), a line-for-line mirror of
`WikiDatabase.cs:45-61` over `Resources.LoadAll<PerkData>("Perks")`: `All`, `Find(id)`, the
duplicate-id warning, the null/empty-id skip. `Assets/Resources/Perks/` is created by the first
asset the owner authors; `Resources.LoadAll` on a missing folder returns an empty array, not an
error, so the code is safe before then.

### 5.2 The v1 effect set — only effects that have a call site

| Enum member | Index | Applied where | Live? |
|---|---|---|---|
| `MeleeDamagePercent` | 0 | `CombatController.cs:441`, after `weapon.Damage` | yes |
| `SpellDamagePercent` | 1 | `CombatController.cs:660` | yes |
| `MaxHealthFlat` | 2 | derivation step 4 | yes |
| `MaxHealthPercent` | 3 | derivation step 5 | yes |
| `ArmourFlat` | 4 | derivation step 4, into `BaseResistances.Physical`, then the §4 formula | yes |
| `MaxResourceFlat` | 5 | derivation step 4, into `MaxManaStamina` | yes |
| `ResourceRegenPercent` | 6 | `CombatController` regen fields via `OnStatsChanged` (§3.4) | yes |
| `MoveSpeedPercent` | 7 | `SetSpeedMultiplier(session, m)` (§3.4) | yes |
| `ExtraLootRolls` | 8 | `SpriteContainer.cs:158` (§5.4) | yes |

**Recommended deferrals — each is a one-line append later, because the enum is append-only:**

- **`RangedDamagePercent`.** The owner settled it as v1, but fact 3 says there is no player ranged
  attack to read it. Shipping it means a perk the owner can author, a player can spend a point on,
  and that does nothing, with nothing logged. **Recommend appending it the day a ranged attack
  lands.** If the owner would rather have it declared now, it is one enum member plus a comment
  saying it is inert — say so and the implementer adds it.
- **Fire/Cold/Poison/Magic resistances.** No damage-type system exists to read them (fact 1). A
  perk raising them would move only the bag's readout. Same recommendation, same one-line cost.
- **Everything crime-layer.** The owner's settled exclusion. No entry.

**Enums serialize by integer index** (CLAUDE.md §3). Every future addition goes on the end. The
enum must carry that sentence as a comment, exactly as `WikiCategory` does
(`WikiEntryData.cs:5-8`).

### 5.3 Combat query values — read at hit time, allocation-free

CLAUDE.md §2 forbids per-frame allocation, and this project already avoids per-hit dictionary
iteration (`CombatController.cs:241-249` caches `_speedProduct` for exactly this reason). Perk
multipliers follow the same shape: **plain float fields on `PlayerSession`**, recomputed only in
`RecalculateDerivedStats` step 6, never walked at hit time.

```csharp
public float MeleeDamageMultiplier   { get; private set; } = 1f;
public float SpellDamageMultiplier   { get; private set; } = 1f;
public float MoveSpeedMultiplier     { get; private set; } = 1f;
public float ResourceRegenMultiplier { get; private set; } = 1f;
public int   ExtraLootRolls          { get; private set; }
```

Hit-site edits, both one line, both **after** the existing composition:

- `CombatController.cs`, immediately after line 441 (`if (weapon != null) damage += weapon.Damage;`):
  `if (session != null) damage = Mathf.RoundToInt(damage * session.MeleeDamageMultiplier);`
  — after the weapon so the perk multiplies the whole swing, which is the owner's "compose with
  `weapon.Damage`". `session` is already in scope from line 439.
- `CombatController.cs:660`, the spell site: pass `Mathf.RoundToInt(ability.BaseDamage * mult)`
  instead of `ability.BaseDamage`. `PlayerSession.Instance` is already fetched at `:645`, but into a
  `string` — hoist a local `var session` rather than calling `Instance` twice.

Both sites must keep passing `gameObject` as the fourth argument — that is what sets
`Health.LastAttacker`, and therefore what makes kill XP work at all (`KillXP.cs:25-29`).

### 5.4 Loot rolls

`SpriteContainer.RollContents` (`SpriteContainer.cs:153-158`) calls `Band.Roll()`, the
`RollCount`-based overload (`LootBand.cs:128`). Change it to use the explicit-count overload that
already exists (`LootBand.cs:66`), passing `Mathf.Max(1, Band.RollCount)` plus the session's
`ExtraLootRolls` (0 when there is no session).

**Do not apply it to `PickpocketInteractable.cs:137`.** That is the crime layer, which the owner
excluded from v1; applying it there smuggles a crime perk in through the back door.

**Fact 7 applies:** containers roll in `Awake`, so the perk affects only containers built after it
is taken. Comment it at the call site so nobody reports it as a bug.

### 5.5 Perk points and spending

In `EKVibe`:

```csharp
/// <summary>One point every 2 levels: 2, 4, 6 ... 24. Twelve across the cap of 25. Derived, never stored.</summary>
public static int PerkPointsAtLevel(int level) => Mathf.Clamp(level, 1, MaxPlayerLevel) / 2;
```

On `PlayerSession`, following the `_unlockedWikiEntries` pattern exactly (`PlayerSession.cs:420-456`)
— a private `HashSet<string>`, a read-only `IEnumerable` view for the saver, and a `Restore` that
clears first:

- `private readonly HashSet<string> _spentPerkIds`
- `public IEnumerable<string> SpentPerkIds => _spentPerkIds;`
- `public int UnspentPerkPoints => Mathf.Max(0, EKVibe.PerkPointsAtLevel(Level) - _spentPerkIds.Count);`
- `public bool HasPerk(string perkId)`
- `public bool SpendPerkPoint(PerkData perk)` — refuses if the perk is null, the id empty, already
  owned, `UnspentPerkPoints <= 0`, `Level < perk.MinLevel`, the class not allowed, or the
  prerequisite not owned; otherwise adds, calls `RecalculateDerivedStats()`, fires `OnPerksChanged`,
  returns true.
- `public void RestorePerkIds(List<string> saved)` — clear, add every non-empty id, then
  `RecalculateDerivedStats()`.
- `_spentPerkIds.Clear()` in `BeginNewGame`, next to `_unlockedWikiEntries.Clear()` at `:149`.

**`UnspentPerkPoints` clamps at 0 deliberately.** If the curve is ever retuned downward, a loaded
player can hold more spent ids than the new curve pays for. The clamp keeps the figure from going
negative; the derivation still honours **every** spent id, so nothing is silently unspent.

**An unresolvable `PerkId` on load is kept, not dropped.** `RestorePerkIds` stores the raw string;
the derivation skips ids `PerkDatabase.Find` cannot resolve (logging once, as `ItemDatabase` and
`WikiDatabase` both do). Keeping it means the point stays spent, so a temporarily missing asset does
not hand out a free respec, and re-adding the asset restores the perk. `RestoreInventory` drops
unresolvable ids (`PlayerSession.cs:467-469`) — this is deliberately the opposite choice, and the
reason belongs in a comment.

---

## 6. The perk window

### 6.1 `Assets/Scripts/UI/PerkWindowUI.cs` (+ `.meta`)

Copy `WikiBritainUI` (`Assets/Scripts/UI/WikiBritainUI.cs:152-531`), **not** `SpellbookUI`. Same
skeleton, so only the differences are listed:

- `QuestUIBuilder.CreateCanvas(transform, "PerkWindowCanvas", 575)`. **575 is free** — the orders in
  use are 550, 560, 565, 570, 580, 600 and 610 (`QuestJournalUI.cs:96, 346`,
  `WikiBritainUI.cs:103, 363`, `MapOfBritainUI.cs:243`, `SpellbookUI.cs:40`, `SpellNamingUI.cs:36`).
- Same dimmer, panel, `Win95Skin.TitleBar` header, `CreateCloseX`, list pane left, detail pane
  right, BACK bottom-left, count text bottom-right. Header label `PERKS`.
- Same `Open` / `Toggle` / `Close` / `Back` lifetime, including the `Systems.PauseManager.Push()` /
  `Pop()` balance and the `Back()` hand-off to `InventoryController` (`WikiBritainUI.cs:211-218`).
- **List**: `PerkDatabase.All`, filtered to perks whose `AllowedClasses` admits the session's class
  (`ItemData.CanBeUsedBy` is the shape to copy, `ItemData.cs:68-76`), ordered by `MinLevel` then
  `PerkId`. Section labels are the string `"LEVEL " + MinLevel` — generated, so no new enum and no
  copy to write.
- **Row states**, three not two:

  | State | Fill | Label | Clickable |
  |---|---|---|---|
  | Taken | `Win95Skin.SlotFill`, bold | `Title` plus a tick | yes |
  | Available | `Win95Skin.SlotFill` | `Title` | yes |
  | Locked | `Win95Skin.Shadow` | `Title`, non-bold | **yes** |

  **Deliberate deviation from the wiki**, which makes locked rows unclickable and shows "???"
  (`WikiBritainUI.cs:307-313`). A wiki entry is a discovery; a perk is a *plan*, and a player
  choosing where to spend needs to read what is ahead. Locked rows therefore open in the detail
  pane; only the SPEND button is disabled.
- **Detail pane**: title, a generated effect list (`"+15% melee damage"`, built from
  `PerkEffectType` and `Magnitude` — machinery text, not flavour), a requirements line
  (`"Requires level 6"` / `"Requires <prereq Title>"` / `"<Class> only"`), then `Description`
  (owner's prose; prints `(nothing written yet)` while empty, copying `WikiBritainUI.cs:330`), then
  a SPEND button. The banner image slot is dropped — perks have no art.
- **SPEND**: calls `PlayerSession.SpendPerkPoint(perk)`, then repopulates the list and re-shows the
  detail. `interactable = false` whenever `SpendPerkPoint` would refuse, with the reason on the
  requirements line.
- **Count text** bottom-right: `"<n> points unspent"`, mirroring the wiki's `"n / m entries"`
  (`WikiBritainUI.cs:269`).
- **Empty state**: with zero `PerkData` assets on disk the list shows one section label saying so,
  the same shape as `WikiBritainUI.cs:264-265`. **This is the state the code ships in.**

### 6.2 Reaching it

Add `BuildPerksButton()` to `InventoryController`, called from `Awake` next to `BuildSpellsButton()`
(`InventoryController.cs:91`) and written in its image (`:179-209`): the same idempotence guard
(`if (Find("PerksButton") != null) return;`), the same `Win95Skin.StyleButton` and `StyleLabel`, and
an `OnPerksPressed()` handler with the same pause-balance contract as `OnWikiBritainPressed`
(`:265-269`) — close the bag first, then `PerkWindowUI.Open()`.

**Placement — verified against the scene, not just the tool.** The right rail is full (the backpack
occupies y 0.34-0.948; QUEST JOURNAL 0.245-0.305, SPELLS 0.175-0.235, WIKIBRITAIN 0.105-0.165). The
left stats panel is the character sheet and has one free band. Scene-confirmed anchors inside
`LeftStats`: `LevelXpText` `(0.08, 0.66)-(0.92, 0.88)`, `Resistances` `(0.08, 0.16)-(0.92, 0.38)`,
`MapOfBritainButton` bottom `0.03`, top `0.115` (`Assets/c.unity`, GameObjects `1254143439`,
`1654208314`, `1766914765`; matching `InventoryWin95Builder.cs:171, 185, 194`).

Free band: **local y 0.115 to 0.16**. Proposed `PerksButton` anchors, parented to `LeftStats`:
`(0.10, 0.118)-(0.90, 0.156)`, label `PERKS`, font 18.

**Height check, and it is tight.** The canvas reference resolution is 1920x1080 (`c.unity:58558`);
`LeftStats` spans y 0.006-0.948, about 1017 px, so 0.038 of that is roughly **39 px**, against about
65 px for a rail button. An 18 pt label fits (line height about 24 px) but there is little margin.
**This needs the owner's eye** (§10.3, check 6). If it reads cramped, the fix is in the editor tool
— raise `Resistances` to `(0.08, 0.20)-(0.92, 0.38)` (`InventoryWin95Builder.cs:185`) and widen
PERKS to 0.118-0.19 — and then the owner must run
**`Tools > UI > Rebuild Inventory Panel (Win95)`** with Play mode stopped.

**No editor step is required for the button to exist**, because it is runtime-built (fact 4). The
tool never deletes unknown children — it uses `FindOrCreate` throughout — so a runtime button and a
future tool run do not conflict.

### 6.3 The perk-point notice

Use the existing `UIManager.Instance.ShowToast(message)` (`UIManager.cs:296`), driven from a
`PlayerSession.OnLevelUp` subscription. Do **not** reuse `WikiEntryToastUI` as the parent plan
suggests: it is hard-typed to `WikiEntryData` throughout (`WikiBritainUI.cs:50, 60, 82`), and
reusing it means generalising a working class for one caller.

The toast **string is prose and therefore the owner's.** Ship
`"[perk point earned - owner to write]"` and list it in §7.4.

Fire it only when `EKVibe.PerkPointsAtLevel(newLevel) > EKVibe.PerkPointsAtLevel(newLevel - 1)`,
i.e. on even levels — otherwise every level-up claims a point that odd levels do not pay.

---

## 7. Mapping table — serialized fields, save keys, enums

**No renames. No insertions. No enum reordering. Every row is an append or a new file.**

| # | Change | Kind | Storage | Files holding old data | Blast radius if got wrong |
|---|---|---|---|---|---|
| 1 | `SaveData.PerkIds` (`List<string>`), appended **after** `TotalXP` (`SaveGameManager.cs:80`) | new serialized field | `persistentDataPath/savegame.json`, JSON key `PerkIds` | every existing save (key absent) | Absent key means `JsonUtility` yields an empty list, so no perks — correct for a pre-perk save. **The field name IS the JSON key**; `JsonUtility` ignores `[FormerlySerializedAs]`. Renaming it later silently un-spends every perk every player has taken. Never rename. Nothing may be inserted above it. |
| 2 | `PerkData.PerkId` (`string`) | **new save key**, joining `ItemID`, `ChunkName` and `EntryID` | `savegame.json` inside `PerkIds`; resolved via `PerkDatabase.Find` | none yet — no perk asset exists | Changing a shipped **value** orphans that perk: the id is read, fails to resolve, is kept in the list (§5.5), and the perk silently does nothing. Must be added to CLAUDE.md §3 and to `SAVE_AND_SERIALIZATION.md` (§8). |
| 3 | `PerkEffectType` (new enum, 9 members) | enum, serialized **by integer index** | future `Assets/Resources/Perks/*.asset` | none yet | Inserting or reordering a member silently rewrites every authored perk's effect into a different effect. **Always append.** Carry the same comment `WikiCategory` does (`WikiEntryData.cs:5-8`). |
| 4 | `PerkData`, `PerkEffect`, `PerkDatabase`, `PerkWindowUI` | new scripts | — | none | **Each `.cs` must be committed with its `.meta`.** A missing `.meta` re-mints the GUID on a fresh clone and every `PerkData` asset loses its script binding — silently, and only on someone else's machine. CLAUDE.md §3; this has gone wrong here twice. |
| 5 | `PlayerClassInfo.LevelGrowth` + `GrowthPerLevel` | new `[Serializable]` class, code-only | none | none | None — no asset or prefab stores it. |
| 6 | `PlayerSession`: `_baselineResistances`, `_spentPerkIds`, the cached multipliers, `OnStatsChanged`, `OnPerksChanged` | new fields/events on a MonoBehaviour | **nowhere** | none | None. `PlayerSession` has no scene or prefab instance — `GameFlowController.EnsureSession` creates it with `new GameObject(...).AddComponent` (`GameFlowController.cs:69-73`), so its fields come from C# initialisers every run. |
| 7 | `EKVibe.ArmourSoftCap`, `ArmourMaxReduction`, `ArmourReduction`, `PerkPointsAtLevel` | `const` / `static` | none | none | None — compile-time. But `ArmourSoftCap` is a **balance** constant: changing it retunes every piece of gear at once. |
| 8 | `ItemData.Armor` | **unchanged field, changed meaning** | 7 `Resources/Items/*.asset` | `TestRing.asset:23` = 4; the other six = 0 | Not a serialization risk — a **balance** one. The number is reinterpreted from "flat points removed" to "input to a curve". §4.2 is the mapping; §4.3 says no asset needs editing at soft cap 20. |
| 9 | `CharacterData.BaseResistances.Physical` | **unchanged field, newly load-bearing** | `RuntimeStats` is a runtime-only `CreateInstance` (`PlayerSession.cs:161`); no `.asset` on disk carries a non-zero one | none | Becomes real damage reduction (§4). Any `CharacterData` asset an author later gives a Physical value now changes combat, not just a readout. Worth a tooltip on the field. |
| 10 | `MapChunkData.ChunkName`, `ItemData.ItemID`, `WikiEntryData.EntryID`, `SaveData.TotalXP` | **untouched** | — | — | Explicitly out of scope. If a diff touches any of these, it is out of plan. |

### 7.4 Every placeholder string the owner must replace

The implementer writes none of these as real copy. Each ships as a bracketed placeholder so it is
greppable:

| String | Where |
|---|---|
| Perk `Title` and `Description` | every `PerkData` asset — the owner authors them; none ship |
| The level-up / perk-point toast line | the `OnLevelUp` subscriber (§6.3) |
| The empty-list line in the perk window | `PerkWindowUI`, mirroring `WikiBritainUI.cs:265` |

Generated text is **not** prose and is fine to write: `"LEVEL 6"`, `"+15% melee damage"`,
`"Requires level 6"`, `"3 points unspent"`, `"(nothing written yet)"`.

---

## 8. Documentation changes (part of the work, not an aside)

- **`docs/plans/PROGRESSION_SYSTEM.md`** — three corrections, replacing the wording rather than
  annotating beside it (CLAUDE.md §7):
  1. "the `Resistances` block ... barely used" — it is unused in combat entirely; Phase 3 makes
     `Physical` load-bearing and leaves the elemental four cosmetic (fact 1).
  2. "*Combat:* melee, ranged and spell damage" — there is no player ranged attack; ranged is
     deferred until one exists (fact 3).
  3. "Reaching it costs an editor step" — it does not; `BuildSpellsButton` is the runtime
     precedent (fact 4).
- **`docs/reference/SAVE_AND_SERIALIZATION.md`** — owner of the save format. Add `PerkIds` to the
  "`SaveData` holds:" list, add `PerkData.PerkId` to the **Save keys** section alongside
  `ChunkName` / `ItemID` / `EntryID`, and record the keep-unresolvable-ids decision (§5.5). Update
  the `Last verified against:` header and **keep its scope honest** — code-read, not Unity-tested,
  no save round-tripped with `PerkIds` present.
- **`CLAUDE.md` §3** — add `PerkData.PerkId` to the save-keys capsule. This is the first Phase-3
  change that earns a CLAUDE.md edit; Phases 1-2 correctly did not.
- **`docs/README.md`** — add this file to the active-plans table and mark
  `PROGRESSION_PHASE1_2_IMPLEMENTATION.md` as landed.
- **Minor, `CLAUDE.md` §2**: the menu-category list names `Place, Art, World, Debug, Repair,
  Content, Danger Zone`, but a **`UI`** category exists and has done since the bag rebuild
  (`InventoryWin95Builder.cs:26`). One word, worth fixing while §3 is open.

---

## 9. Silent failure modes, and how the implementer avoids each

| # | Failure | Why it is silent | Guard |
|---|---|---|---|
| 1 | Load resets stats to class defaults | `RestoreFromSave` calls `BeginNewGame` calls `ApplyClassDefaults` (`PlayerSession.cs:176, 170`), rebuilding from scratch. Without a recompute after `RestoreTotalXP`/`RestorePerkIds`, every load silently strips growth and perks — and the player looks fine, just weaker | §3.3: recompute at the end of **both** restores; `BindPlayerToSession` (`GameFlowController.cs:220`) already runs after them |
| 2 | Resistances compound on every recompute | `ApplyClassDefaults` does **not** reset `BaseResistances` (`CharacterData.cs:48-55`); it is written once at `PlayerSession.cs:166`. A perk adding to it adds again on every level-up | §3.1 step 2 — reset from `_baselineResistances` before adding anything |
| 3 | Regen or move speed compounds | Same shape as row 2: `ManaRegenPerSecond` and `MovementSpeed` are authored prefab fields with no reset. Multiplying the current value on each level-up compounds | §3.4 — multiply a baseline captured in `Awake`; speed goes through `SetSpeedMultiplier`, keyed by the session so it replaces rather than stacks |
| 4 | Move speed eats the crouch/vehicle multiplier | Writing `CombatController.MovementSpeed` directly is exactly the bug `_speedModifiers` was built to fix (`:215-218`), and it fails by leaving a dismounted player permanently fast | §3.4 — never write `MovementSpeed` |
| 5 | Equipment double-counts | Folding gear into `RuntimeStats` while `CombatController.cs:441` and `Health.cs:61` still read it live doubles every weapon and every shield, with no error | §3.1 — equipment is explicitly out of the derivation. A reviewer should grep the diff for `EquippedWeapon` / `TotalArmor` inside `RecalculateDerivedStats` and find nothing |
| 6 | Max health rises but current health does not | `Health.MaxHealth` and `CombatController.CurrentHealth` are separate values, and `BindPlayerToSession` does not run mid-run. The bar would read 100/244 after a level-up | §3.4 — add the delta to `CurrentHealth`, clamped |
| 7 | A 0-damage call starts hurting the player | `Mathf.Max(1, ...)` floors **upward**, and `TakeDamage(int)` is public (`Health.cs:40`) | §4.1 — the `damage > 0` gate before the whole block |
| 8 | Armour perk raises the readout but not the mitigation | The readout already prints a number `Health` does not use (fact 2). Putting perk armour anywhere else re-opens that gap | §4.1 / §5.2 — `ArmourFlat` lands in `BaseResistances.Physical`, which is what **both** the readout and `EffectiveArmour()` read |
| 9 | Perk points go negative after a curve retune | `PerkPointsAtLevel` is derived; a downward retune can leave more spent ids than points | §5.5 — `Mathf.Max(0, ...)`, and the derivation still honours every spent id |
| 10 | A missing perk asset hands out a free respec | Dropping unresolvable ids on load looks tidy and quietly refunds points | §5.5 — ids are kept; the derivation skips what it cannot resolve and logs once |
| 11 | `PerkEffectType` reordered | Enums serialize by integer index; every authored perk becomes a different perk, with nothing logged | §7 row 3 — append-only, comment on the enum, reviewer checks the diff for insertions |
| 12 | A new script's `.meta` not committed | A fresh clone re-mints the GUID; every `PerkData` asset loses its script silently, and only on someone else's machine | §7 row 4 — four `.cs`/`.meta` pairs committed together; §10.1's dangling check catches a mismatch |
| 13 | Perk multiplier walked per hit | Nothing fails; it just allocates and iterates on a mobile hot path, against CLAUDE.md §2 | §5.3 — plain float fields, recomputed on discrete events only |
| 14 | `OnStatsChanged` handler leak | A destroyed `CombatController` keeps receiving events after a reload; no error, just a growing list | §3.4 — subscribe in `Start`, unsubscribe in `OnDestroy`, per `InventoryController.cs:106-126` |
| 15 | Perk-point toast fires on odd levels | Every level-up claims a point; half of them are a lie | §6.3 — compare `PerkPointsAtLevel(new)` against `PerkPointsAtLevel(new - 1)` |
| 16 | The loot-roll perk secretly buffs pickpocketing | `PickpocketInteractable.cs:137` uses the same `Roll(count)` overload; wiring it there quietly re-adds the excluded crime layer | §5.4 — container site only, with a comment saying why |
| 17 | The perk window reads as broken on arrival | It opens, lists nothing, and looks like a bug | §6.1 — an explicit empty-state line, and §10.3 check 5 telling the owner this is the expected shipping state |

---

## 10. Verification

### 10.1 What can be proved in this environment

```bash
python Tools/asset_reachability.py --check-dangling   # run before AND after; exit 0 is clean
```

Nothing here deletes, moves or renames an asset, so the result should read identically before and
after. Four new `.cs` + `.meta` pairs are added: **a new GUID appearing as dangling means a `.meta`
was committed without its script, or the reverse.** On a machine without `Library/` the tool exits
`2` ("couldn't verify") — that is **not** a pass.

A brace/paren balance scan catches a truncated edit. **It is not a compile and must not be reported
as one.**

The armour arithmetic in §4.2 is pure integer maths and can — and should — be checked by hand here.

### 10.2 What cannot be proved here

Everything else. No C# compiler, no Unity, no test framework. In particular: that the project
builds; that `RecalculateDerivedStats` is genuinely idempotent when run twice; that the perk button
is legible at 39 px; that the derivation survives a real save round-trip.

### 10.3 Owner checks in the editor, with routes

**Stop Play mode before any Inspector edit — changes made during Play are discarded** (CLAUDE.md §5).

1. **It compiles.** Unity, wait for the recompile, then **Window > General > Console**, Clear, and
   confirm no red. Nothing below means anything until this passes.
2. **A pre-Phase-3 save still loads.** First copy `savegame.json` somewhere safe — its folder is
   whatever `Application.persistentDataPath` reports on that machine. Then Play, title screen,
   **Continue**. Wallet, gear, map, WIKIBRITAIN and **level** should all be intact, and the bag's
   left panel should show the level it showed before the update. Cross one chunk edge (which
   autosaves) and reopen the JSON: it should now contain a `PerkIds` key holding an empty list.
3. **Growth is real and survives a reload.** Play, press **I** for the bag, note **Player level**
   and the HP bar. Level up (kill enemies, or complete a quest carrying an XP reward). The HP bar's
   maximum should rise, and current HP should rise by the same amount **without** filling to full.
   Then cross a chunk edge to autosave, quit to title, **Continue** — the maximum must be the same
   number, not back at the class default. If it drops back, the recompute is missing from a restore
   path (§9 row 1).
4. **Armour is proportional.** Press **F8** in Play (the dev shortcut at
   `InventoryController.cs:222`) to get the test sword and shield, press **I**, click the shield in
   the backpack, EQUIP. Then let a Roadman hit you and read the combat log line (`Health.cs:73`).
   Before this change a shield made a 7-damage hit land for 3; it should now land for **6**. Equip
   more armour and confirm the hit never falls to 0 — the whole point of the change. Also check that
   the left panel's **Armor** line now matches what the mitigation implies.
5. **The perk window opens and is honest.** Play, **I**, then the new **PERKS** button in the left
   stats panel, under MAP OF BRITAIN. It should open a Win95 window titled PERKS, list nothing, and
   read "0 points unspent" at level 1. **This is the correct shipping state** — no `PerkData` asset
   exists yet. BACK must return to the bag with the pause balanced (open the bag, open perks, press
   BACK, press **I**: the bag must close, not deepen).
6. **The button's height.** Look at the PERKS button specifically. It is about 39 px tall against
   about 65 px for the right-rail buttons (§6.2) and may read cramped or clipped. If it does, the
   fix is `Assets/Editor/InventoryWin95Builder.cs:185` (raise `Resistances` to 0.20) plus the
   button's own anchors, followed by **`Tools > UI > Rebuild Inventory Panel (Win95)`** with
   Play stopped. **This is the one layout number in the plan that was reasoned about rather than
   seen.**
7. **Author one perk and spend a point.** Exit Play. Project panel, right-click `Assets/Resources/`,
   **Create > Folder**, name it `Perks`. Right-click that folder, **Create > GBH England > Data >
   Perk**. In the Inspector set **Perk Id** to a lowercase id you will never change (it is a save
   key), **Min Level** 2, one **Effect** of `Max Health Flat` magnitude 20, and write the Title and
   Description yourself. Ctrl+S. Play, reach level 2, open PERKS: the perk should be listed and
   SPEND enabled. Spend it, watch the HP maximum rise by 20, autosave by crossing a chunk edge, quit
   to title, **Continue** — the perk must still be listed as taken and the 20 HP must still be
   there. If the perk is taken but the HP is gone, the derivation is not running after
   `RestorePerkIds` (§9 row 1).
8. **Nothing free.** With 0 unspent points, SPEND must be disabled on every row. Try a perk above
   your level and one restricted to another class: both must refuse and say why.

### 10.4 Known gaps, to be reported as gaps

- `ArmourMaxReduction` (75%) is unreachable with any gear that exists — 60 effective armour needs
  roughly five heavy pieces nobody has authored. **Unverified until gear exists.**
- `PerkPointsAtLevel` at the cap (12 points at level 25) is not reachable in normal play. The honest
  check is a temporary `GrantXP(60000)` behind a debug key — **and that key must not be committed.**
- Idempotence of `RecalculateDerivedStats` is argued structurally in §3.1, not demonstrated. The
  closest real check is #3 above (load, reload, same numbers).

---

## 11. Commits, in dependency order

Each is coherent alone; none leaves the tree in a state where a half-feature silently misreports.

| # | Commit | Contents |
|---|---|---|
| 1 | Make armour proportional | §4 — the `EKVibe` constants and `ArmourReduction`, `PlayerSession.EffectiveArmour`, the `Health.TakeDamage` rewrite and its `using`. Self-contained; needs no perk and no derivation. Independently checkable by owner check 4 |
| 2 | Add the per-class growth table | §3.2 — `LevelGrowth` and `GrowthPerLevel` in `PlayerClass.cs`. Data only; nothing calls it yet |
| 3 | Derive player stats from level | §3.1, §3.3, §3.4 — `_baselineResistances`, `RecalculateDerivedStats`, `OnStatsChanged`, the five call sites, and `CombatController`'s subscriber. **Growth goes live here.** Perks are still absent, so the perk steps are no-ops over an empty set |
| 4 | Add the perk data model | §5.1, §5.2 — `PerkData.cs`, `PerkDatabase.cs`, both `.meta` files. Nothing reads them yet |
| 5 | Persist which perks were taken | §5.5, the `SaveData.PerkIds` append, the `Save()` write, and `ContinueFromSave`'s `RestorePerkIds`. The save round-trips before any perk can be spent |
| 6 | Apply perk effects | §5.2 to §5.4 — the derivation's perk steps, the two `CombatController` hit sites, the `SpriteContainer` roll |
| 7 | Add the perk window and its button | §6.1, §6.2, §6.3 — `PerkWindowUI.cs` + `.meta`, `BuildPerksButton`, `OnPerksPressed`, the level-up toast |
| 8 | Update the save reference, CLAUDE.md and the parent plan | §8. Last, so it describes what landed |

Commits 1-3 are independently playable and worth stopping at for owner checks 2-4. Commits 4-6 land
the machinery with no content. Commit 7 is the only UI change.

---

## 12. One thing this plan does not decide

**The perk list itself.** The parent plan's open item stands: perk names, flavour and the actual
per-class spread are the owner's work, exactly like the class taglines and quest prose
(CLAUDE.md §3). Everything above is machinery that runs correctly against **zero** perk assets and
starts paying out the moment the first one is authored. Owner check 7 is the route for authoring one.
