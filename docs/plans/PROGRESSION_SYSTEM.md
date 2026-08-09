# Plan — Progressive Levelling System (player + enemies)

**Status: agreed 2026-08-07, revised 2026-08-08 against the equipment/Win95/wiki work. Not
implemented.** Delete or archive this file when the work lands.

## Owner decisions (settled, don't re-ask)

- **XP sources:** enemy kills + quest rewards only. Crime/stealth XP may append later.
- **Curve:** EK-ish — cap ~20–25, steep. Constants in `EKVibe`.
- **Level gains:** small automatic per-class stat growth every level, **plus** a perk pick every
  2–3 levels. Perks are **passives only** in v1.
- **Enemy scaling:** formula from one base — one prefab per type, a `Level` int per placement
  scales HP/damage/XP. No hand-authored tier variants in v1.
- **Loot scaling:** tiered `LootBand`s — 2–3 bands per enemy family, level selects the band.

## What changed under the plan since it was written

The uncommitted branch work moved four things the plan depends on. Revisions are folded in below;
this section is why they exist.

1. **Equipment landed.** `PlayerSession` now owns a paper doll (`_equipment` by `ItemType`,
   `EquippedWeapon()`, `TotalArmor()`, saved as `SaveData.Equipment`). Melee damage in
   `CombatController` is `Strength*2+5 + weapon.Damage`; `Health.TakeDamage` subtracts
   `TotalArmor()` **flat** for the player only. Perks now have to compose with gear, and flat
   armour interacts badly with enemy damage scaling — see Phase 3.
2. **The UI is Win95 now.** `Win95Skin` (`Face`, `StyleButton`, `StyleWindow`, `AddBevel`…) is the
   house style, and `EKVibe.ButtonBrown` is being retired from the HUD. Every new screen in this
   plan must be skinned through it.
3. **The bag already reserves a level readout.** `InventoryWin95Builder` creates a `LevelXpText`
   in the left stats panel, commented *"static labels for now; no XP system feeds them yet"*, and
   `InventoryController.LevelText` is a declared-but-never-written field. The Phase 1 UI is
   therefore mostly wiring, not building.
4. **WIKIBRITAIN set the precedent this system needs.** `WikiEntryData.EntryID` is already
   documented as a save key with the never-rename rule, `PlayerSession` persists unlocked ids as an
   appended `List<string>`, and `WikiBritainUI` is a locked/unlocked list window with a
   `WikiEntryToastUI`. **Perks are the same shape** — copy that pattern rather than SpellbookUI's.

## Phase 1 — XP and player level

**New: `ProgressionManager`** (`Scripts/Systems/`, singleton).

- State: `TotalXP` (int, cumulative — level is *derived*, never stored, so the curve retunes
  without a save migration). `SpentPerkIds` (List<string>).
- API: `GrantXP(int amount, string source)`, `int Level`, `int XPIntoLevel`, `int XPForNextLevel`,
  `event OnLevelUp(int newLevel)`, `int UnspentPerkPoints`.
- `EKVibe` constants: `MaxLevel` (propose 25), `XPForLevel(n)` (propose cumulative `100*n*n`),
  `PerkPointsAtLevel(n)` — derived, not stored.

**Alternative worth considering:** put `TotalXP`/`PerkIds` on `PlayerSession` instead of a new
singleton. It already owns wallet, inventory, equipment, visited chunks and wiki unlocks, already
has the `OnXChanged` event convention, and is already the thing `SaveGameManager` reads. A separate
manager buys nothing except a second lifetime to get wrong. **Recommend: `PlayerSession`**, with the
curve maths as a static helper in `EKVibe`.

**Save (append-only):** append `TotalXP` (int) and `PerkIds` (List<string>) to `SaveData`, after
`UnlockedWikiEntries`. Pre-progression saves read back 0/empty → level 1, correct, no migration.
⚠️ **Perk ids are save keys** — same rule as `ItemID`, `ChunkName` and `EntryID`. Never rename a
shipped one. Add to CLAUDE.md §3 alongside the others when this lands.

**Feed points:**
- **Kills:** `Health.OnDeath` + `LastAttacker`, granting only when the last attacker was the player
  (identified by `GetComponent<CombatController>() != null`, as the armour code already does). That
  keeps police-kills-civilian and enemy-kills-enemy from paying out.

  `LastAttacker` **is** set to the player, as of the "Attribute player hits to the player" commit
  on `progression-levelling`. Before it, both player damage sites — `CombatController` melee and
  the spell path — called the three-argument `TakeDamage`, which forwards `attacker: null`, so
  attribution matched nothing and would have granted no XP at all with no log. Both now pass
  `gameObject` to the four-argument overload.
- **Quests:** append `public int XP;` to `QuestReward`; the payout site calls the grant. Safe
  append — `QuestDefinition` ships in every build, but an int adds no dependency graph.

**UI:** wire the **existing** `LevelXpText` / `InventoryController.LevelText` (currently dead) to
`Level` and `XP into / needed`. Level-up notice via the existing `UIManager.ShowToast`, or
`WikiEntryToastUI`'s richer panel if a perk point is awarded. No new window in Phase 1.

## Phase 2 — enemy levels

⚠️ **`EnemyNameplate.Level` already exists and is already `3`.** It is cosmetic today —
`GeneratedEnemyPrefabTool` hardcodes `plate.Level = 3` on every generated enemy prefab, and nothing
reads it. This is the single biggest silent-failure risk in the plan: **promote that field into the
real level and every enemy in the game is instantly level 3 and gets scaled up by the formula**,
with no error and no log.

**Decided 2026-08-08: option A.** A new `EnemyLevel` component with authored default `Level = 1`.
The nameplate reads `EnemyLevel` when present and falls back to its own field for display, so
existing prefabs stay unscaled until an owner deliberately sets a level and nothing changes behind
anyone's back. `GeneratedEnemyPrefabTool` stops hardcoding `plate.Level = 3`; the nameplate's own
field becomes display-only fallback.

(Rejected: reusing `EnemyNameplate.Level` as the real level. Fewer components, but it needs every
enemy prefab edited down to 1 *first*, and an enemy without a nameplate would then have no level.)

Scaling, whichever wins:

- Prefab stats are the **level-1 baseline**. Scale `Health.MaxHealth` and `EnemyAI.Damage` by
  `stat × (1 + K×(Level−1))`, `K_Health`/`K_Damage` in `EKVibe`. `MoveSpeed` deliberately not
  scaled — agent tuning is physical, not power.
- ⚠️ **Ordering:** `Health.Awake` does `CurrentHealth = MaxHealth`. The scale must happen before
  that or every enemy spawns at partial health. Use `[DefaultExecutionOrder]`, or scale from inside
  `Health.Awake` by reading the component — the second is harder to get wrong.
- ⚠️ **Armour interaction (new since the original plan).** Player armour is a *flat* subtraction in
  `Health.TakeDamage`, floored at 0. Once the doll is filled, low-level enemies literally cannot
  land damage, and the curve between "harmless" and "dangerous" is very sharp. Either scale
  `K_Damage` aggressively, or make armour proportional. Flag for the owner — it is a balance
  decision, not a code one.
- **Nameplate** shows the level (the badge already renders `Level.ToString()`).
- **XP:** base XP per enemy × the same level formula → what the kill grants.

Level is authored **at placement time**, so the same Roadman is Lv2 in Alvaston and Lv6 in London:
the World Palette carries a Level field beside the armed enemy preset, and stamping attaches an
`EnemyLevel` component at that level. The preset's own `EnemyLevel` is the default the palette
starts from, and 0 attaches no component at all. See
[../reference/WORLD_AUTHORING_AND_NPCS.md](../reference/WORLD_AUTHORING_AND_NPCS.md). Editing an
already-placed instance in the Inspector still works and touches chunk prefabs — edit prefabs in
place, never delete/re-save.

## Phase 3 — player gains

**Auto growth:** `GrowthPerLevel(PlayerClass)` next to `PlayerClassInfo.StartingTraits`, returning
a small per-level HP/resource/trait delta.

⚠️ **The derivation invariant, now with gear.** `PlayerSession.RestoreFromSave` calls
`BeginNewGame`, which rebuilds `RuntimeStats` from class defaults. It becomes
**baseline + (Level−1)×growth + perk effects**, recomputed deterministically from `TotalXP` +
`PerkIds` on both new-game and load. Equipment is *not* folded into `RuntimeStats` — it is already
read live at the two use sites (`CombatController` for weapon damage, `Health` for armour), and
duplicating it into derived stats would double-count. **Order of operations to fix once and
document:** base traits → level growth → perk flat adds → perk percent multipliers → equipment.

**Perk cadence — decided 2026-08-08: a point every 2 levels**, at 2, 4, 6 … 24. Twelve picks
across the cap of 25. One constant, derived from level, never stored.

⚠️ **Armour becomes proportional — decided 2026-08-08.** `Health.TakeDamage` currently subtracts
`TotalArmor()` flat and floors at zero, so a filled paper doll makes weak enemies do literally
nothing, and Phase 2's damage scaling sharpens that cliff rather than smoothing it. Armour becomes
a percentage reduction so a hit always lands for something and armour perks scale sanely. This
**changes the balance of gear already authored** — `ItemData.Armor` values were written against
subtraction and will read differently. Mapping the old numbers onto the new curve is part of the
work, not an afterthought.

**Perks:**
- `PerkData : ScriptableObject` in `Resources/Perks/`, modelled on `WikiEntryData`:
  `PerkId` (⚠️ save key), name, description, class restriction, min level, prereq perk, and a list
  of passive effects. Effects as an **append-only enum** + magnitude.
- **v1 effect set — decided 2026-08-08**, three families:
  - *Combat:* melee and spell damage, read at hit time so they compose with `weapon.Damage`.
    ⚠️ **There is no player ranged attack, so ranged damage is deferred and no enum member for it
    exists.** `CombatController` has exactly two damage sites, melee and spell; `RangedCaster` is an
    `EnemyAI` field. A ranged-damage perk would be spendable and do nothing. The effect enum is
    append-only, so adding it costs one line whenever a ranged attack exists.
  - *Survivability:* max health and armour.
    ⚠️ **Only `Resistances.Physical` is load-bearing, and only as of Phase 3.** It is now added to
    worn armour to form the single figure `EKVibe.ArmourReduction` reads, which is also what makes
    the character sheet's Armor line — which has always printed `Physical + TotalArmor()` — honest.
    The other four (Fire, Cold, Poison, Magic) are read by nothing at all: there is no damage-type
    system to attach them to, so a perk raising one would move a number on the sheet and no damage.
    No v1 perk touches them, and no effect enum member exists for them.
  - *Utility:* move speed, max mana/stamina and its regen, loot rolls.
- ⚠️ **The crime layer is deliberately excluded from v1** — no concealment, pickpocket-odds or
  wanted-decay perks. Owner's call; they can append later, and the effect enum is append-only
  precisely so they can.
- `PerkDatabase` mirroring `ItemDatabase`/`WikiDatabase` (Resources lookup by id).
- Combat-facing effects are read at hit time via query helpers
  (`float DamageMultiplier(DamageKind)`), applied in `CombatController` after `weapon.Damage`.
  Stat-facing effects go through the derivation above.

**Perk window:** copy `WikiBritainUI` — a `Win95Skin` window with a list, greyed locked entries, a
detail pane, and a spend button; plus its toast for "perk point earned". Do **not** model it on
SpellbookUI.

**Reaching it costs no editor step.** `InventoryController.BuildSpellsButton` already creates the
SPELLS rail button at runtime in `Awake`, styled through `Win95Skin`, and `InventoryWin95Builder`
documents that arrangement rather than owning it. PERKS follows the same precedent and exists as
soon as the code compiles; the rebuild tool uses `FindOrCreate` throughout, so it never deletes a
runtime-built button. The right rail is already full (QUEST JOURNAL, SPELLS, WIKIBRITAIN, MAP OF
BRITAIN), so the button hangs in the left stats panel, which is already the character sheet.

## Phase 4 — loot tiers

- Give `LootOnDeath` `LowBand / MidBand / HighBand` (`LootBand` refs) + two level thresholds. On
  death pick by level, `Roll()`, present through `LootMenuUI` as now — the component already
  populates `LootEntry.Icon`, so tiered results need no UI work.
- Keep the existing fixed `LootDrop[]` working as a fallback so authored enemies keep their drops
  before bands exist.
- Bands are plain assets in `Assets/Data/` (referenced, not Resources-resolved). v1 authors bands
  for the six London enemies only.
- `DroppedItemPickup` now exists; the death drop stays a menu, but a band result could spawn on the
  ground instead later. Out of scope for v1.

## Order of work

1. XP state on `PlayerSession` + `EKVibe` curve + `SaveData` append + quest XP + wire the existing
   bag readout.
2. `EnemyLevel` + kill XP + nameplate (playable loop: kill → ding).
3. Auto growth on the derivation path, with the invariant above.
4. `PerkData`/`PerkDatabase` + spent ids + derivation hook.
5. Perk window (Win95, wiki-shaped) + the `InventoryWin95Builder` button.
6. Loot bands + authored bands.
7. Owner editor pass: set enemy Levels, author bands, run the bag rebuild tool, verify saves.

Phases 1–2 alone give the whole visible loop.

## Verification (no compiler here — owner checks in-editor)

- A pre-progression save loads at level 1 with wallet, gear, map and wiki intact.
- Kill an enemy → XP; complete a quest → XP; ding at the right totals; bag shows level and XP.
- A Lv5 enemy visibly tanks and hits harder than a Lv1 of the same prefab; badge shows the level.
- ⚠️ Confirm no enemy became level 3 by accident (the `EnemyNameplate.Level` trap).
- With a full paper doll, check low-level enemies still do *something* — the flat-armour floor.
- Perk spend survives save/load; the perk window matches the Win95 skin.

## Open items (owner)

- Perk list and flavour per class — owner-editable copy, like the taglines. **This is the only
  thing still blocking Phase 3 content**; the machinery does not need it.

Settled: enemy `Level` field (option A), perk cadence (every 2 levels), the v1 effect set
(combat, survivability, utility — no crime layer), armour model (proportional). Police and
civilian kills grant no XP, as implemented.
