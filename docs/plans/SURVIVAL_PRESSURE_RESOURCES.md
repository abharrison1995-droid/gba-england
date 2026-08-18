# Survival pressure — resources (stamina bar, percent-cost dodge, no mana regen)

```
Status:               APPROVED with three owner corrections, 2026-08-09 — see the amendment
                      block below. Written against the working tree, 2026-08-09. Every fact
                      below names the file and line it was verified in.
Verification scope:   code and asset/scene YAML read directly. No compiler, no Unity, no test
                      framework in this environment (CLAUDE.md §5). Nothing here has been
                      seen by either.
```

> **Implementer handoff.** Work strictly from the commit sequence in §7 — five small,
> single-concern commits, in order, nothing more. The mapping tables in §6 are binding: two field
> deletions, four field appends, no renames, no enum or save-key change, and **zero** edits to
> `Assets/c.unity`, any `.prefab` or any `.asset`. No scope improvisation — phases 2 and 3 (§11)
> are staged, not approved. Quest and dialogue prose is the owner's; none is needed here. Before
> and after, run `python Tools/asset_reachability.py --check-dangling` (§10.1) and report the exit
> code honestly — it is not a compile. When done, hand the diff to the reviewer subagent against
> this plan.

> **Amendment, 2026-08-09 — three corrections applied after review. They override the body of
> this plan wherever they disagree with it.**
>
> 1. **The roll cost floors, it does not round.** `Mathf.RoundToInt` rounds an odd maximum *up*
>    past half, and `PerformDodge` refuses on `CurrentStamina < cost`, so a Young Driller (55)
>    would get **one** roll from full, not two — and the count would flip with every level as the
>    maximum alternated odd and even. `Mathf.FloorToInt` guarantees `2 × cost ≤ max`, which is the
>    property §3 Q2 and §4 claim. The `Max(1, …)` floor stays. All arithmetic below is corrected.
> 2. **The concealment bar and stealth are sidelined**, by owner decision: they do not exist or
>    function at present and will be addressed in their own pass. `ConcealmentBar` is
>    `m_IsActive: 0` in `c.unity` and nothing activates it, so the stray duplicate `MPFill` inside
>    it renders nothing today. **Nothing in this plan touches either.** §2 finding 2 and §10.3
>    check 3 are rewritten accordingly.
> 3. **The bar pitch is 36.** HPTrack sits at y −22 and MPTrack at −58, so the stamina track goes
>    at **MP − 36 (y −94)** and the three bars are equally spaced down the column.
>    `TopLeftPortraitPanel` is 116 tall and the bar is 28, so −94 sits inside it and the panel does
>    **not** grow. *(Superseded the original "MP − 56 (y −114), panel 116 → 144" during the
>    2026-08-18 mobile HUD pass, which is the state of the code today.)*
>
> One consequence, accepted knowingly: `ConcealmentBar` is authored at −86 in the same column and
> is overlapped by the stamina bar's slot. It is `m_IsActive: 0`, so nothing is drawn over anything
> today — but the stealth pass has to place the bar somewhere rather than find a gap waiting.

Owner's brief, verbatim goals: add a third HUD bar for stamina; make the dodge roll cost 50% of
stamina; make stamina regenerate slowly; stop mana regenerating automatically; HP and mana are
replenished only through healing items, rest, or healing spells.

The brief arrived with a verified-facts list. Every claim in it checked out, and the corrections
and additions found while checking are in §2 — three of them change what the work actually is.

***

## 1. Scope

**In (phase 1 — the only phase this plan asks the implementer to land):**

* A third HUD bar for stamina in the top-left cluster, built at runtime like every other recent
  HUD addition — **no scene edit**.
* The dodge roll repriced from a flat 14 stamina to **50% of the maximum**, computed at press time.
* Stamina regen re-rated from a flat 7/s to **5% of maximum per second**, still scaled by the
  perk multiplier.
* Mana regen **deleted**. Mana comes back only through items, the pub, or (phase 2) a heal spell.
* The CLAUDE.md §5 ledger entry, per convention.

**Out — explicitly, and staged:**

* **Splitting the stamina and mana maxima.** Recommended against in phase 1 — see §3 Q1. The full
  consequence list is written there so the owner can pull that lever knowingly later.
* **A healing spell.** Machinery staged as phase 2 (§11): one appended field on `AbilityData`, one
  branch in the cast routine. No spell asset, no teacher, no prose — those are the owner's.
* **Placing a pub.** `Pub_TheWinchester.prefab` is referenced by nothing in the build (§2, row 3).
  Placement is world authoring, staged as phase 3 with a route; it is not a code change.
* **Rebalancing the heal items.** Blackberry heals 4 HP against 85–160 HP pools. That is a balance
  pass on `.asset` values, owner's call, phase 3. Named again in §3 Q7.
* **A load-time floor on mana or stamina.** Recommended against — §3 Q6.
* **Any rest mechanic with words.** If rest ever wants lines ("You bed down for the night…"),
  the owner writes them (CLAUDE.md §3). Nothing in phase 1 needs any.
* **A combat-state system.** Stamina regen ticks always; nothing invents global aggro state.
  §3 Q3 says why, citing the warning already in the code.
* **Fixing the two existing bars' per-frame string allocation.** Noted in §8 risk 7, deliberately
  not touched here.
* **The concealment bar and stealth, entirely.** Owner decision, 2026-08-09: they do not exist or
  function at present and get their own pass. No code, scene or check in phase 1 touches either.
* Any save-key change, enum reorder, prefab rebuild, `.unity` edit, or new script file. **No new
  `.cs` files, therefore no hand-authored `.meta` files.**

***

## 2. What was verified, and what the brief got wrong

Every brief fact was re-verified in place on 2026-08-09. The ones that checked out, with the
locations a reviewer should re-open:

| Brief claim | Verified at |
|---|---|
| `RegenResources()` ticks mana 2.5/s and stamina 7/s with integer carry accumulators | `CombatController.cs:218-237`; rates at `:69-72`; carries at `:88-89` |
| No automatic HP regen anywhere | `grep` for every `Heal(` call site: items (`InventoryController.cs:690`), tutorial chest (`TutorialSequence.cs:338`), pub (`PubInteractable.cs:34`). No tick exists |
| Mana and stamina share `CharacterData.MaxManaStamina`; both clamp against it | `CombatController.cs:220`, `:269-272`, `:294`; `InventoryController.cs:696`; `ReviveFull` at `:896-897`; `Awake` at `:129-130` |
| `RollStaminaCost` is a flat 14 | `CombatController.cs:51`; serialized in the scene at `c.unity:59535` |
| HUD = two bars + concealment; `EnsureDedicatedTrack` exists | `UIManager.cs:27-29`, `:261-287`; cluster scale at `:124-128`, constant at `EKVibe.cs:68` with the 1.75 ceiling documented at `:56-67` |
| `SaveData` holds Health/Mana/Stamina | `SaveGameManager.cs:37-39` |
| `PerkEffectType.ResourceRegenPercent = 6` scales both regen rates; no perk asset exists | `PerkData.cs:33`; `PlayerSession.cs:304-306`, `:350`; `CombatController.cs:275-276`. `Assets/Resources/Perks/` does not exist |
| `Health.Heal(int)` exists | `Health.cs:126-130` |

**Four things the brief got wrong or did not say.** Each changes the work:

1. **"Rest" exists as a mechanic but is unreachable in play.** `PubInteractable.HaveAPint()`
   (`PubInteractable.cs:15-44`) clears the wanted level, calls `ReviveFull()` — a **full restore of
   HP, mana and stamina** (`CombatController.cs:891-899`) — and saves. It is exactly the rest stop
   the brief hoped might exist. But `Pub_TheWinchester.prefab` (built by `ModernBritainSetup.cs:218-233`,
   with `OnInteract → HaveAPint` persistently wired at prefab lines 56-57) is referenced by **no
   chunk prefab, no preset, and not `c.unity`** — its GUID `e949c7f4f8c9d7e40a52b42502a4f07f`
   appears nowhere outside its own files. No player can ever order the pint. Rest is therefore a
   placement task, not a build task (phase 3, §11).
2. **There is a stray duplicate `MPFill` inside `ConcealmentBar` in `c.unity` — and the whole
   concealment bar is switched off.** The stray is GameObject fileID `870412552`, Image
   `870412554`, mana-blue `(0.2, 0.35, 0.75)`, `m_IsActive: 1`, referenced by nothing. But its
   parent `ConcealmentBar` (fileID `757388522`, the GameObject carrying the Image that
   `UIManager.PlayerConcealmentFill` binds) is **`m_IsActive: 0`**, and no code anywhere calls
   `SetActive` on it. So neither the bar nor the stray renders today, and CLAUDE.md §5 ledger
   item 2 cannot be checked while that stays true. The real `MPFill` (fileID `825450132`) lives
   under `MPTrack` where it belongs.

   **Owner decision, 2026-08-09: the concealment bar and stealth are sidelined for their own
   pass. Nothing in this plan touches them, including the stray** — deleting a child of a
   disabled object fixes nothing visible and would land a scene edit in a pass that is otherwise
   scene-free.
3. **The brief's reason for `EnsureDedicatedTrack` is slightly off, in a way that matters for the
   third bar.** The concealment bar was not "authored stretched across the whole cluster" — its
   authored rect is 260×28 at (244, −86), the same size as the other two bars. What sprawled was
   the *runtime fill*: its parent is `TopLeftPortraits` rather than a dedicated track
   (`UIManager.cs:250-259`). The lesson for the stamina bar is the opposite of the brief's framing:
   the authored layout is fine, and a runtime-built bar that gives the fill a dedicated track from
   birth avoids the whole failure class. §5.
4. **The load path is sharper than "values start to matter".** `LoadWorld` calls `ReviveFull()`
   first (`SaveGameManager.cs:215`), then floors **Health** at 1 (`:217`) but restores **mana and
   stamina raw** (`:223-224`). A pre-change save at 0 mana loads at 0 mana. With regen gone that is
   survivable — the backstops in §3 Q7 cover it — but it is the exact edge the brief worried about,
   and it is already written down in the code, not hypothetical.

Two more verified facts the plan leans on:

* **After `BindPlayerToSession`, `CombatController.PlayerData` *is* `PlayerSession.RuntimeStats`**
  (assigned at `GameFlowController.cs:157`). So `PlayerData.MaxManaStamina` at runtime is the
  level-grown, perk-adjusted maximum, not the template's 50. The percent-cost roll and percent
  regen both read the live maximum through this alias — and §8 risk 3 records what breaks if the
  alias is ever severed.
* **Stamina's only consumer today is the roll.** `CurrentStamina` is spent at
  `CombatController.cs:657` (roll) and `:962` (stamina abilities) — and **no `AbilityData` asset
  exists on disk** (script GUID `8f2d2a977b31ac846a94cc1b6509433a` appears in no `.asset`), so the
  ability path has never had content. The only spell is the runtime-built Spark (mana, 12 —
  `CombatController.cs:1099-1109`).

***

## 3. The seven questions

### Q1 — Does stamina get its own maximum? **Recommendation: no, keep the shared `MaxManaStamina`.**

The brief called this the central design decision, and it is — but the centre of it is that
**nothing the owner asked for needs the split.** The request is a bar (visibility), a price
(50%), and regen changes. All three work against a shared maximum.

The cost of splitting, honestly scoped, because "it's just one more int" is how these go wrong:

| Consequence | Where | Kind |
|---|---|---|
| New `CharacterData.MaxStamina` | `CharacterData.cs:40` area — **append**, safe per SAVE_AND_SERIALIZATION.md | Serialized. `PlayerStats.asset` and both NPC `CharacterData` assets carry no key and read **0** until re-saved — so every read needs a "0 means fall back to shared" rule forever, or the owner re-saves three assets |
| Per-class stamina baselines | `PlayerClassInfo.StartingMaxResource` (`PlayerClass.cs:151-163`) → a second five-class table | Code-only, cheap — but five new balance numbers that are **the owner's call**, not the architect's |
| Per-class stamina growth | `LevelGrowth` (`PlayerClass.cs:105-110`) → third field | Code-only, cheap — five more balance numbers |
| Derivation | `PlayerSession.RecalculateDerivedStats` (`PlayerSession.cs:233-334`) → new max to reset, grow, perk-clamp, and clamp currents against | Code |
| Perk semantics | `PerkEffectType.MaxResourceFlat = 5` currently raises the shared pool — does it raise mana, stamina, or both? | A design fork on an enum whose index is frozen |
| Creator screen | `CharacterCreatorUI.cs:73-76` prints `HP X   Resource Y` — becomes two numbers | Generated text, cheap |
| Six clamp/init sites | `CombatController.cs:129-130`, `:220`, `:269-272`, `:294`, `:896-897`; `InventoryController.cs:696` | Code |
| Saves | None — `SaveData.Stamina` already exists (`SaveGameManager.cs:39`) | — |

Total: one safe append, ~7 files, ten new balance numbers, one perk-semantics fork, and a
permanent fallback rule. What it buys that the owner asked for: nothing. What it buys that the
owner might *want* — per-class dodge economies (a Dynamo with a small stamina pool dodges less
than a Bunda Basher) — is a real lever, but it is a balance lever with their name on it.

**Recommendation: phase 1 shares the maximum.** Both bars read against the same N (`55 / 55` mana
and `55 / 55` stamina on a Young Driller). The one honest cost is comprehension: a player might
think spending stamina drains mana. It does not — the *currents* are independent fields; only the
maximum is shared. If that confusion shows in play, the fix is the split above, done knowingly —
not a label hack.

### Q2 — 50% of maximum or 50% of current? **Recommendation: maximum.**

* **50% of maximum, floored**: always exactly two dodges from full, then a hard stop. The bar
  halves on each roll — perfectly legible on a phone screen. The third dodge is a designed wait
  (§3 Q3: ~10 s). ⚠ **`Mathf.FloorToInt`, never `RoundToInt`** — see the amendment at the top.
  Rounding an odd maximum up puts the cost above half, and since `PerformDodge` refuses on
  `CurrentStamina < cost`, the second roll is refused: a Young Driller at 55 would get one roll,
  not two, and the count would flip every level. Flooring makes `2 × cost ≤ max` true always.
  The cooldown (`RollCooldown = 1f`, `CombatController.cs:61`) stops mattering as the pacing
  mechanism and the pool takes over — which is the stated point of the whole task.
* **50% of current**: infinitely divisible, so it never actually refuses. Worse, stamina is an
  `int`: below 2 points the cost rounds to 0 and rolls become **literally free**, which is the
  exact opposite of survival pressure. It would need a floor of 1, at which point low-stamina
  rolls cost 1 each and the mechanic has quietly become "spam forever". **Flagged as a bad idea —
  do not build this** (§9).

One consequence to name, because the brief did ("a different KIND of value"): the cost scales with
level and with `MaxResourceFlat` perks, because it is computed from the live maximum. A level-25
Dynamo (200 max) pays 100 a roll — still exactly two rolls from full, forever. That is the
intended shape; it also means any future stamina ability sharing the pool competes with a
level-scaled roll price. Accepted, and noted for the day a stamina ability is authored.

### Q3 — "Regenerate slowly": what rate, and in combat? **Recommendation: 5% of maximum per second, always ticking.**

**Rate, as a percent, not a flat number.** Today's 7/s flat (`CombatController.cs:72`) cannot
survive the repriced roll for scaling reasons: the pool grows from 40–80 at level 1 to ~120–200 at
the cap (`PlayerClass.cs:112-116`, growth at `:125-136`), and the roll always costs half of it. A
flat rate therefore makes dodge recovery *slower every level* — at 2/s flat, 12.5 s per roll at
level 1 but 50 s at level 25. A percent rate keeps the economy identical at every level:

* **5%/s → one roll (50%) repays in 10 s; empty to full in 20 s.** Sustained dodging is 5× slower
  than today (today: 14 cost at 7/s = a roll every 2 s), while the two-roll burst from full keeps
  combat responsive. That is "slowly" with the pressure where the owner wants it.
* The integer-carry accumulator (`CombatController.cs:230-236`) already handles fractional rates —
  5% of 55 is 2.75/s — unchanged mechanism, new input.

**In combat: yes, it ticks in combat, because nothing should gate it.** There is no global combat
state, and the code already warns against building one: `EnemyAI.cs:167-174` documents why a
static aggro counter drifts and never recovers, and `CombatController.cs:835-836` rejects both a
static counter (leaks on chunk teardown) and a per-frame scan (allocates). "Recently in combat"
could later be a timestamp on `CombatController` (written by `OnHealthDamaged` and the melee/spell
sites, read by `RegenResources` — allocation-free), but that is a refinement with its own edge
cases (how long is "recent"? does a missed swing count?), and it is **out of phase 1**. The
5%/s rate is slow enough that in-combat regen does not undercut the pressure: mid-fight it buys
one extra roll every 10 s, which reads as a comeback window, not a fountain.

### Q4 — `ResourceRegenPercent = 6`: survives, narrowed. **Do not delete it; do not rename it.**

With mana regen deleted, the multiplier's only remaining input is stamina regen, so the effect's
meaning narrows to "stamina regen %". It still has a live call site (`PlayerSession.cs:304-306`
into `ResourceRegenMultiplier`, read in the new regen tick), satisfying the enum's own
"every member has a live call site" remark (`PerkData.cs:11-13`).

Deleting the member is **forbidden**: it sits at index 6 with `MoveSpeedPercent = 7`,
`ExtraLootRolls = 8`, `MeleeKnockback = 9` after it, and the enum is serialized by integer index
(`PerkData.cs:6-9`) — removing 6 silently rewrites every future perk authored at 7, 8 or 9.
Renaming the member is serialization-safe by index but pointless: "resource regen" still
describes stamina regen accurately. Cost of the recommendation: a doc-remark edit on the enum and
on `PlayerSession.ResourceRegenMultiplier` (`PlayerSession.cs:349-350`) saying stamina-only. That
is all.

### Q5 — The replenishment routes, concretely.

| Route | Exists today? | Evidence | Phase 1 work |
|---|---|---|---|
| **Healing items (HP)** | **Yes, live.** `ItemData.HealHP`, consumed through `InventoryController.UseTooltipItem` (`InventoryController.cs:674-705`) into `Health.Heal` | Blackberry `HealHP 4`, Hemp Seed `HealHP 2` (`Assets/Resources/Items/`). Both roll in `Band1_Loot` — the game's **only** loot band, 4 entries, all consumables, `RollCount 3` (`Assets/Data/LootBands/Band1_Loot.asset`) — from every `SpriteContainer` and from pickpocketing (`SpriteContainer.cs:170`, `PickpocketInteractable.cs:137`). Tutorial chest heals 20 directly (`TutorialSequence.cs:338`) | None |
| **Mana items** | **Yes, live.** `ItemData.HealMana` at `InventoryController.cs:694-698`, clamped to the shared max | Snarlborough Cigarette `HealMana 15`, Crumpled Rizz `HealMana 1`, Blackberry `HealMana 2` — same loot band | None. Becomes the only field mana route |
| **Rest** | **Mechanic: yes. Reachable: no.** The pub pint is a full restore + save (`PubInteractable.cs:15-44`) but the prefab is placed nowhere (§2 row 1) | Arrest also fully restores (fine-clamped — `GameFlowController.cs:383-419`), and the pre-tutorial death-respawn fully restores (`:442-456`) | None. Phase 3 places a pub (§11) |
| **Healing spells** | **No.** `AbilityData` has `BaseDamage` and no heal field; `CastAbilityRoutine` only damages (`CombatController.cs:1012-1024`). Spark is the only spell | Machinery staged phase 2 (§11): one appended field (zero `AbilityData` assets on disk, so zero blast radius), one cast branch, no asset, no teacher, no prose | None |
| **Stamina items** | **No** — there is no `HealStamina` | With regen retained, not needed | None. Name it if item pressure ever wants it |

### Q6 — Load and pre-change saves: acceptable without a floor. **Recommendation: no floor.**

`SaveData` needs no new key — `Health`, `Mana`, `Stamina` all exist (`SaveGameManager.cs:37-39`)
and load exactly as saved (`:217`, `:223-224`). Three cases:

* **Stamina low on load:** harmless. Regen always ticks (Q3), so the worst case is ~10 s to the
  first dodge. No floor needed.
* **Mana at 0 on load:** the player has items (Q5), and the two universal backstops below.
  Pre-change saves usually hold near-full stamina (it self-healed in ~7 s) and arbitrary mana —
  survivable either way.
* **The genuine edge** — 0 mana, empty bag, no pounds, far from any help: covered by the same two
  backstops that answer Q7. A floor would be a hidden heal that undercuts the pressure this whole
  pass exists to create. **No floor.** §10.3 check 7 loads such a save deliberately.

No migration: the field names are the JSON keys, none change, and old values are valid values.

### Q7 — What stops this being simply punishing?

**The failure mode, named honestly:** post-tutorial, low HP, no consumables, no pounds, deep in
the Manor Cellars — no pub in the dungeon, the tutorial chest already looted, and post-tutorial
death does **not** auto-revive: it shows the death screen and reloads the last checkpoint at the
HP that checkpoint saved (`GameFlowController.cs:368-372`, `SaveGameManager.cs:217`). Crossing a
chunk edge at 3 HP autosaves 3 HP — **the low-HP autosave trap**.

What prevents it, in order of how often they fire:

1. **Every bin and every pocket is a consumable dispenser.** The only loot band is 100%
   consumables at 3 rolls a container (Q5). London's containers are dense. A player who loots
   carries HP and mana.
2. **Stamina always comes back** (Q3), so the defensive tool is never permanently gone — only
   rationed.
3. **The pub** — once placed (§11 phase 3) — is a free full restore, heat clear and save.
4. **Getting nicked is a heal.** Arrest fully restores HP/mana/stamina for a £50 fine clamped to
   the wallet (`GameFlowController.cs:383-419`, `EKVibe.ArrestFine = 50`). Expensive, diegetic, and
   already built.
5. **The heal spell** (phase 2) gives Dynamo-style builds a self-serve route.

What does **not** prevent it today: the heal items are snack-sized (2–4 HP against 85–160 HP
pools), and the pub is unplaced. Both are phase-3 owner calls (§11). If the owner wants phase 1 to
ship with a safety net beyond items, the cheapest honest one is **placing the pub**, not a code
change.

***

## 4. The economy after the change, in numbers

Young Driller (55 max), Mr Hood (60), Stabmeister (50), Bunda Basher (40), Dynamo (80) — per
`PlayerClass.cs:151-163`:

| | Today | Phase 1 |
|---|---|---|
| Roll cost | flat 14 | 50% of max, **floored** → 27, 30, 25, 20, 40 (min 1) |
| Rolls from full | 3–5 | exactly 2, every class, every level (this is what flooring buys) |
| Sustained roll cadence | one per 2 s | one per ~10 s |
| Mana | +2.5/s forever | items, pub, (phase 2) spell only |
| HP | items, pub, chest only (unchanged) | items, pub, (phase 2) spell |

`MaxResourceFlat` perks and level growth raise the roll price as they raise the pool — by design
(Q2). `ResourceRegenPercent` perks shorten the 10 s — by design (Q4).

***

## 5. File-by-file change list

| File | Change | Why |
|---|---|---|
| `Assets/Scripts/Combat/CombatController.cs` | **Regen:** delete the mana half of `RegenResources` (`:222-228`), `_manaRegenCarry` (`:88`), `ManaRegenPerSecond` (`:69-70`), `_baseManaRegen` (`:92`, captured `:123`), and the regen write `ManaRegenPerSecond = _baseManaRegen * …` (`:275`). Rewrite the stamina half to `_staminaRegenCarry += StaminaRegenPercentPerSecond * mult * max / 100f * Time.deltaTime`, where `mult` is `PlayerSession.Instance?.ResourceRegenMultiplier ?? 1f` read at tick time; delete `StaminaRegenPerSecond` (`:71-72`), `_baseStaminaRegen` (`:93`, `:124`) and the `:276` write. **Dodge:** append `RollStaminaPercent = 50f` beside the other `Roll*` fields; new `private int CurrentRollCost` = `PlayerData != null ? Max(1, FloorToInt(PlayerData.MaxManaStamina * RollStaminaPercent / 100f)) : RollStaminaCost`; `PerformDodge` reads it once into a local and uses it at the check (`:641`) and the spend (`:657`). Keep `"Not enough Stamina."` verbatim. Rewrite the `RollStaminaCost` tooltip (`:48-50`) — its "at 7/s regen 14 repays in two seconds" reasoning is dead. **HUD:** one line in `PushHud` (`:285-295`): `UpdatePlayerStamina(CurrentStamina, PlayerData != null ? PlayerData.MaxManaStamina : 50)` — the same max expression the mana push already uses | The economy |
| `Assets/Scripts/UI/UIManager.cs` | Append `PlayerStaminaFill` and `PlayerStaminaText` after `PlayerConcealmentText` (`:27-36` block). New `EnsureStaminaBar()`, called from `Start()` beside `BuildActionButtons` (`:75-82`): builds `StaminaTrack` under `TopLeftPortraitPanel` by copying `MPTrack`'s anchors/pivot/anchoredPosition/sizeDelta (via `PlayerManaFill.transform.parent`), sets `anchoredPosition.y -= 36` (**one authored bar pitch** below MP — HP −22, MP −58, stamina −94, equally spaced; derivation in a comment), adds a dark-amber track `Image`, adds `StaminaFill` child stretched 0→1 in `EKVibe.StaminaBar`, `raycastTarget = false`, assigns `PlayerStaminaFill`. `TopLeftPortraitPanel` is left alone — −94 already fits inside its authored 116. New `UpdatePlayerStamina(int current, int max)` mirroring `UpdatePlayerMana` (`:200-208`) but with **int-compare caching** (`_shownStamina`, `_shownStaminaMax`, the `_shownLevel` pattern at `:167`) so it never allocates a string on an unchanged frame; label built lazily by the existing `EnsureBarLabel` (`:297-320`) as `"SPText"` | The bar, runtime-built — **no scene edit** |
| `Assets/Scripts/Vibe/EKVibe.cs` | Append `public static readonly Color StaminaBar` beside `HealthBar`/`ManaBar` (`:30-37`) — amber, in the `XpBar`/`LevelBadge` family but a distinct constant so they can diverge. Suggested `(0.85f, 0.7f, 0.15f, 1f)`; implementer may darken for the track fill (computed, no second constant) | The one new colour; code constant, not serialized |
| `Assets/Scripts/Data/PerkData.cs` | Edit the `ResourceRegenPercent` **remark text only** (`:33` area) to say stamina-only. The enum member, its index and its name do not move | Q4 documentation |
| `Assets/Scripts/Flow/PlayerSession.cs` | Edit the `ResourceRegenMultiplier` doc comment (`:349-350`) to say stamina-only | Q4 documentation |
| `CLAUDE.md` §5 | Ledger entry: the pass is unverified, with the §10.3 routes | Convention |

**No new script files, no `.meta`, no `.unity`, `.prefab` or `.asset` change, no `SaveData`
change, no enum change.** `Assets/c.unity` must appear in `git status` after zero commits in this
plan — the two deleted regen fields leave orphan YAML keys there (`c.unity:59542-59543`), which
Unity ignores on load and drops on its next scene save. That is the intended state, exactly like
the pounds-rename keys documented in SAVE_AND_SERIALIZATION.md; **do not hand-edit the scene to
"finish" it.**

***

## 6. Mapping tables

**Nothing is renamed. Nothing is reordered. No enum is touched. No save key is touched.** The only
structural moves are two field deletions and four field appends.

### 6.1 Serialized fields deleted — `CombatController` (serialized on the player in `c.unity:59535-59543`)

| Field | Old value on disk | Blast radius | Handling |
|---|---|---|---|
| `ManaRegenPerSecond` | `2.5` (`c.unity:59542`) | Orphan YAML key; Unity ignores it on load, drops it on the next scene save. No code reads it after this plan | Delete the field, `_baseManaRegen`, `_manaRegenCarry`, the mana tick and the `:275` write — **one commit**, so no commit exists where the field is gone but its writers remain |
| `StaminaRegenPerSecond` | `7` (`c.unity:59543`) | Same orphan-key story. **The old 7 does not carry into the new field** — different name, different kind (flat → percent) | Delete beside `StaminaRegenPercentPerSecond`'s append, `_baseStaminaRegen` and the `:276` write |

### 6.2 Serialized fields appended — all new names, all safe per SAVE_AND_SERIALIZATION.md

| File | Field | Default | Lands in |
|---|---|---|---|
| `CombatController` | `RollStaminaPercent` | `50f` | `c.unity` player — no key on disk, so the default ships |
| `CombatController` | `StaminaRegenPercentPerSecond` | `5f` | same |
| `UIManager` | `PlayerStaminaFill` | `null` | `c.unity` UIManager — assigned at runtime by `EnsureStaminaBar`, never wired by hand |
| `UIManager` | `PlayerStaminaText` | `null` | same — built lazily by `EnsureBarLabel` |

### 6.3 Kept, but re-meaned

| Symbol | Change | Why |
|---|---|---|
| `CombatController.RollStaminaCost` (`:51`) | Kept as the `PlayerData == null` fallback in `CurrentRollCost` (title-screen edge before a session binds). Tooltip rewritten | Deleting it would orphan `c.unity:59535` harmlessly, but the fallback gives the field an honest job and the scene value stays meaningful where it is read |
| `PerkEffectType.ResourceRegenPercent = 6` | Meaning narrows to stamina regen; remark edited | Q4 — the index is frozen |
| `PlayerSession.ResourceRegenMultiplier` | Now read in the stamina tick instead of pushed into two rate fields (`CombatController.cs:275-276` deleted) | One multiplier, one remaining input |

### 6.4 Save keys

**None.** `SaveData` gains no field and renames none. Health/Mana/Stamina round-trip unchanged
(`SaveGameManager.cs:124-126` write, `:215-224` restore). A save made before this plan loads
unchanged; §10.3 check 7 proves it.

***

## 7. Commit sequence

Small, single-concern, each coherent alone. Commits 1–3 are `CombatController.cs` only and worth
reviewing as a set; commit 4 is pure UI.

1. **`Stop mana regenerating`** — delete the mana tick, `ManaRegenPerSecond`, `_baseManaRegen`,
   `_manaRegenCarry`, and the `:275` write. Stamina behaviour untouched (the `:276` write stays
   until commit 3). Perk multiplier doc remarks (`PerkData.cs`, `PlayerSession.cs`) ride along —
   they are the same concern.
2. **`Dodge roll costs a percent of max stamina`** — `RollStaminaPercent`, `CurrentRollCost`, the
   two `PerformDodge` sites, the two tooltip rewrites. Independent of commit 1; either order
   compiles.
3. **`Stamina regenerates slowly, scaled by the perk multiplier`** — `StaminaRegenPercentPerSecond`,
   the stamina-tick rewrite reading `ResourceRegenMultiplier` at tick time, and the deletion of
   `StaminaRegenPerSecond`, `_baseStaminaRegen` and the `:276` write. ⚠ Between commits 1 and 3 the
   perk multiplier applies to nothing — no perk asset exists, so no live behaviour changes; say so
   in the commit message.
4. **`Third HUD bar for stamina`** — `EKVibe.StaminaBar`, the two `UIManager` fields,
   `EnsureStaminaBar`, `UpdatePlayerStamina`, the `Start()` call, and the one `PushHud` line.
   Coherent alone: the bar shows the stamina the flat-14 roll already spends.
5. **`Ledger: survival pressure pass is unverified`** — `CLAUDE.md` §5 entry pointing at §10.3.

Phase 2 (heal-spell machinery) is a separate approval; §11 lists it so the plan reads whole.

***

## 8. Structural risk

Ranked by how quietly it fails.

1. ⚠ **The percent roll reads the maximum through the `PlayerData → RuntimeStats` alias.**
   `BindPlayerToSession` assigns it (`GameFlowController.cs:157`); before binding, `PlayerData` is
   the `PlayerStats.asset` template (50). If anything ever re-points `PlayerData` at the template
   mid-run, the roll silently re-prices to the level-1 value and the bar max drops with it —
   nothing throws. This alias already carries the mana bar and the regen clamp; the plan adds two
   more readers, so it is recorded here once.
2. ⚠ **Deleting serialized fields is safe; re-adding them later under a *different intent* is the
   trap.** The orphan keys (`ManaRegenPerSecond: 2.5`, `StaminaRegenPerSecond: 7` in `c.unity`) are
   ignored on load and dropped on Unity's next scene save. If mana regen ever returns it must be a
   new design with a new name-or-meaning decision, not a quiet resurrection that reads the stale
   2.5 back into a world that has learned to live without it.
3. **The two-commit multiplier gap** (between commits 1 and 3 the perk multiplier touches nothing)
   is deliberate and harmless — no perk asset exists. If one ever gets authored mid-flight, it
   behaves as today until commit 3, then scales stamina only. That is the narrowed contract (Q4).
4. **Mobile hot path.** `RegenResources` runs every frame. The rewrite adds one static-property
   read (`PlayerSession.Instance`) and three multiplies — no allocation. `UpdatePlayerStamina`
   must use the int-compare pattern (`UIManager.cs:167`) so the third bar does not add a third
   per-frame string. The integer-carry accumulator stays — it is what makes 2.75/s work in an
   `int` pool.
5. **The runtime bar must not fight `EnsureDedicatedTrack`.** `StaminaFill` is born an only child
   of `StaminaTrack`, so the wrapper returns at its first check forever (`UIManager.cs:263-264`).
   `EnsureStaminaBar` copies `MPTrack`'s rect — MPTrack is never re-parented, unlike
   `ConcealmentBar`, whose rect is only stable until its first update wraps it. Reading
   `ConcealmentBar`'s rect at build time instead would be the quiet layout bug; do not.
6. **The panel does not grow.** At the corrected pitch the stamina track spans −80 to −108, inside
   `TopLeftPortraitPanel`'s authored 116, so nothing resizes it — which also removes a
   non-idempotent `sizeDelta +=` that ran once per `EnsureStaminaBar` call. The 1.75 ceiling in
   `EKVibe.cs:56-67` constrains the panel's *right* edge (combat-log overlap), so 1.6 stays legal,
   and 116×1.6 ≈ 186 px from the top clears the joystick (bottom-anchored) on the 1920×1080
   reference. Reasoned, not measured — §10.3 check 2 looks at it.
7. **The two existing bars allocate a string every frame** (`UIManager.cs:197`, `:207` — `text =
   $"{…}"` inside `Update`, via `PushHud`). Known, pre-existing, **not fixed here**: fixing them
   changes two working bars in the same commit as a new one, and the diff stops being reviewable
   as one concern. Recorded so it is a decision, not an oversight.
8. ⚠ **`CurrentRollCost` must floor, not round.** `Mathf.FloorToInt` with a `Max(1, …)` guard.
   Rounding is the quiet failure this whole plan's headline claim rests on: `RoundToInt(27.5)` is
   28, `PerformDodge` refuses on `CurrentStamina < cost`, and the Young Driller's second roll
   never happens. Because `Mathf.RoundToInt` is banker's rounding, it fails on some odd maxima and
   not others, so it would look like an intermittent bug rather than an arithmetic one. Flooring
   makes `2 × cost ≤ max` an invariant. The `Max(1, …)` guard is separate, and keeps a future
   1-maximum perk or curse from making rolls free.
9. **Isometric and prefab discipline are untouched** — no movement, no chunk, no prefab, no
   `SetActive(false)` anywhere in this plan. Nothing here is near the seven chunk paths or the two
   suspended-root bans.

***

## 9. Bad ideas flagged — do not build these

* **50% of *current* stamina** (Q2): never refuses, and at 1 stamina the integer cost floors to
  free rolls. It is the opposite of the brief's intent dressed as the brief's wording.
* **Deleting `PerkEffectType.ResourceRegenPercent`** because "mana regen is gone": it sits at
  index 6 with three members after it, and the enum is serialized by index. Forbidden, full stop.
* **A combat-state system to gate stamina regen**: the codebase already documents why the two
  obvious versions fail (`EnemyAI.cs:167-174`, `CombatController.cs:835-836`). If a combat gate is
  ever wanted, it is the timestamp refinement in Q3, as its own approved change.
* **A hidden load-time floor on mana** (Q6): a concealed heal that teaches the player saves are
  safe to ignore. The backstops are diegetic; keep them diegetic.
* **Splitting the pools in phase 1** (Q1): ten new balance numbers and a perk-semantics fork to
  buy nothing the owner asked for.
* **Hand-editing `c.unity` to strip the two orphan keys**: the documented state for retired keys
  is that Unity drops them on its next save (SAVE_AND_SERIALIZATION.md, the pounds-rename
  precedent). Hand YAML edits to a live scene are how GUID accidents happen.
* **Silently retuning the heal items in the same pass**: 4 HP blackberries against 100+ HP pools
  may well be wrong for the new economy, but `.asset` value changes are owner balance calls and
  belong to phase 3 where they can be judged on their own.

***

## 10. Verification

### 10.1 What can be proved in this environment

```bash
git status                                          # Assets/c.unity must NOT appear in any commit
python Tools/asset_reachability.py --check-dangling # before AND after; exit 0 is clean, exit 2 means it checked nothing
grep -rn "m_MethodName: TakeDamage" Assets/         # untouched by this plan — must stay empty anyway
```

Nothing deletes, moves or renames an asset, so `--check-dangling` should read identically before
and after; there are no new GUIDs. A brace-balance scan catches a truncated edit. **It is not a
compile and must not be reported as one.**

The arithmetic is checkable by hand: 5% of 55 = 2.75/s; roll cost `FloorToInt(55 × 0.5) = 27`;
55 → 28 → 1 across two rolls, the third refused; 1 → 28 in ~9.8 s.

### 10.2 What cannot be proved here

Everything else. No C# compiler, no Unity, no test framework. In particular: that the project
builds; that the runtime-built bar lands where the arithmetic says; that the concealment bar's
stray blue child behaves as diagnosed; that 5%/s *feels* slow-but-fair on a device; that a
pre-change save round-trips.

### 10.3 Owner checks in the editor, with routes

**Stop Play mode before any Inspector or Hierarchy edit — changes made during Play are discarded**
(CLAUDE.md §5).

1. **It compiles.** Open Unity, wait for the recompile, **Window → General → Console**, Clear,
   confirm no red. Nothing below means anything until this passes.
2. **The third bar.** Play from the title screen, start a New Game (any class — Young Driller
   reads 55). Top-left cluster: directly under the blue mana bar, one bar-pitch down, there is now
   an **amber** bar reading `55 / 55`, evenly spaced with the two above it. Check it does not
   overlap the combat log on the right and does not reach the joystick. Then **Window → General →
   Device Simulator**, landscape, a notched device: the cluster is unchanged in height (the panel
   no longer grows) — confirm the safe-area fitter still keeps it clear. If the bar is missing
   entirely, `PlayerManaFill` was unbound and `EnsureStaminaBar` skipped itself — look for its
   warning in the Console.
3. **The concealment bar is expected to be absent — do not chase it.** `ConcealmentBar` is
   disabled in the scene and stealth is sidelined for its own pass (§2 row 2). There is no gap
   left for it: the stamina bar occupies the space it was authored in, and the stealth pass will
   have to place it. Nothing in this pass touches it, including the stray `MPFill` inside it,
   which renders nothing while its parent is off. **Not a phase-1 defect.**
4. **The roll economy.** Hold a direction and press **Space** (or the **DGE** button, third from
   the right on the bottom row — ATK, USE, DGE — built at runtime, visible only in Play at
   `UI/UICanvas/HUDPanel/ActionButtons/DGE`). On a Young Driller the amber bar should read
   **55 → 28** on the first roll and **28 → 1** on the second. Third press: refused with
   "Not enough Stamina." Then wait: roughly 3 points a second return — one roll back after ~10 s,
   full after ~20 s. ⚠ **Two rolls from full is the check.** One roll then a refusal means the cost
   rounded instead of floored — the exact defect the amendment exists to prevent.
5. **Mana does not come back.** In the editor, press **M** (dev shortcut — learns Spark and opens
   the naming box), confirm, then cast with **1**. Mana drops 12 (55 → 43). Stand still for 30 s:
   it must not move. (In the city it also drains concealment and pops the Potter toast — unchanged,
   just not this check's concern.)
6. **Items are the HP/mana route.** Loot London bins until a Blackberry and a Snarlborough
   Cigarette are in the bag (both roll in the same band; expect a few containers). Take a hit from
   the PCSO first so HP is short. Press **I**, click the Blackberry, **USE**: HP rises by 4, stack
   decrements. Same with the cigarette: mana rises by 15.
7. **A pre-change save still loads.** First copy `savegame.json` somewhere safe
   (`Application.persistentDataPath` on that machine). Continue. Whatever mana/stamina the save
   holds arrives verbatim — possibly low, possibly full — with **no error**, HP never at 0. Then
   play until mana is needed: the honest outcome is "items or nothing", which is the design.
8. **Zero perks is still the shipping state.** Open the bag (**I**), PERKS: empty list, and the
   game behaves identically. Nothing to author for this pass.
9. **No pub exists yet — that is expected, not a regression.** §11 phase 3 places one. Do not
   file the missing pint as a phase-1 defect.
10. **The magic tutorial still completes.** It is the one scripted sequence written while mana
    came back on its own: Daniel teaches Spark, then the geezer turns hostile and must be put
    down. Spark costs 12 against a 55–80 pool and melee is always available, so there should be
    no soft-lock — *walk it once end to end and confirm.* If a future scripted fight ever needs
    more mana than one pool holds, that is the first place it will show.

**Not to be claimed without a human:** that any of it compiles; that 50% feels right; that the
bar's amber reads distinctly from the gold level badge beside it on a real screen.

***

## 11. Later phases — staged, not approved

* **Phase 2 — heal-spell machinery (code; needs its own go-ahead).** Append `BaseHeal` to
  `AbilityData` (safe: **zero `AbilityData` assets exist on disk**, so nothing carries a missing
  key), branch `CastAbilityRoutine` to heal the caster through `Health.Heal` when `BaseHeal > 0`
  instead of seeking a target. No spell asset ships — the owner authors it (Create →
  `GBH England/Data/Ability Data`) and decides who teaches it; any teaching dialogue is the
  owner's prose. The mana-cost gate, cooldown, shout and city-concealment drain all already exist
  and apply unchanged.
* **Phase 3 — world and balance (owner actions, routes given when asked).** Place
  `Pub_TheWinchester` (it is fully wired — placement only, e.g. stamped into `Home_London`);
  retune `HealHP`/`HealMana` values on the four consumables if the new economy makes 2–4 HP read
  as nothing; decide whether rest ever costs pounds; decide whether the pool split (§3 Q1) is
  wanted, with the consequence table already written.
* **Possible refinement — combat-aware stamina regen.** The timestamp design in §3 Q3, if always-on
  regen proves generous in playtests. Its own plan, its own edge cases.

***

## 12. Documentation changes

* `CLAUDE.md` §5 — one ledger entry (commit 5). No `docs/reference/` file owns resource regen or
  the HUD bars — the routing table (CLAUDE.md §4) has no combat reference, and
  SAVE_AND_SERIALIZATION.md's claims are untouched by this plan (no save change, no rename, no
  enum change). If a combat reference is ever written, the economy table in §4 belongs to it.
