using System;
using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Vibe;

namespace GBHEngland.Flow
{
    /// <summary>One stack of a carried item — a quantity of the same ItemData.</summary>
    [Serializable]
    public class InventoryStack
    {
        public ItemData Item;
        public int Quantity;
    }

    /// <summary>
    /// Runtime session for GBH: England — created character + tutorial flags.
    /// Survives scene loads via DontDestroyOnLoad.
    /// </summary>
    public class PlayerSession : MonoBehaviour
    {
        public static PlayerSession Instance { get; private set; }

        [Header("Created Character")]
        public string CharacterName = "Vince";
        public PlayerClass Class = PlayerClass.YoungDriller;
        public CharacterData RuntimeStats;

        [Header("Progress")]
        public bool TutorialComplete;
        public bool HasStartedNewGame;

        [Header("Inventory")]
        public List<InventoryStack> Inventory = new List<InventoryStack>();

        /// <summary>Fires whenever the carried inventory changes (pickup, restore from save).</summary>
        public event Action OnInventoryChanged;

        /// <summary>
        /// Ids of every Fixed <see cref="World.SpriteContainer"/> already emptied, as
        /// "&lt;ChunkName&gt;/&lt;GameObjectName&gt;".
        ///
        /// Deliberately not a serialized field: it is runtime state that reaches the save through
        /// <see cref="SaveData.LootedContainers"/>, and a public List here would show up in the
        /// Inspector as something an author could edit into a save key.
        ///
        /// A HashSet because the only questions asked of it are "is this one in?" and "put this one
        /// in", and a chunk full of bins asks the first on every Awake.
        /// </summary>
        private readonly HashSet<string> _lootedContainers = new HashSet<string>();

        /// <summary>Read-only view for the saver. Enumeration order is not meaningful.</summary>
        public IEnumerable<string> LootedContainers => _lootedContainers;

        /// <summary>
        /// Restockable containers that have been emptied and are waiting to refill, keyed the same
        /// way as <see cref="_lootedContainers"/> and mapped to the number of visits still owed.
        ///
        /// Same split as the looted set: a Dictionary at runtime because a chunk full of containers
        /// asks "is this one waiting?" on every Awake, and a List&lt;ContainerCooldown&gt; on SaveData.
        /// </summary>
        private readonly Dictionary<string, int> _containerCooldowns = new Dictionary<string, int>();

        /// <summary>
        /// Read-only view for the saver, already shaped for the save file. Order is not meaningful.
        /// </summary>
        public IEnumerable<ContainerCooldown> ContainerCooldowns
        {
            get
            {
                foreach (var pair in _containerCooldowns)
                    yield return new ContainerCooldown { Id = pair.Key, VisitsRemaining = pair.Value };
            }
        }

        [Header("Wallet")]
        [Tooltip("Pounds carried. Whole pounds only — there are no pence anywhere in the game.")]
        public int Pounds;

        /// <summary>Fires whenever the wallet changes (payout, spend, restore from save).</summary>
        public event Action OnPoundsChanged;

        [Header("Progression")]
        [Tooltip("Cumulative XP earned this run. The level is DERIVED from this and never stored, " +
                 "so retuning the curve in EKVibe needs no save migration.")]
        public int TotalXP;

        /// <summary>Fires whenever the XP total changes (kill, quest reward, restore from save).</summary>
        public event Action OnXPChanged;

        /// <summary>Fires once per level crossed, with the level just reached.</summary>
        public event Action<int> OnLevelUp;

        /// <summary>
        /// Fires at the end of every <see cref="RecalculateDerivedStats"/>, i.e. whenever the
        /// derived figures in <see cref="RuntimeStats"/> or the cached multipliers below may have
        /// moved. <see cref="Combat.CombatController"/> listens so a mid-run level-up reaches the
        /// running player — <c>GameFlowController.BindPlayerToSession</c> only runs on new-game and
        /// load, so without this the health bar would keep the old maximum until the next reload.
        /// </summary>
        public event Action OnStatsChanged;

        /// <summary>The player's level, derived from <see cref="TotalXP"/>. Never stored.</summary>
        public int Level => EKVibe.LevelForXP(TotalXP);

        /// <summary>XP earned into the current level's band. Pass-through so no UI does curve maths.</summary>
        public int XPIntoLevel => EKVibe.XPIntoLevel(TotalXP);

        /// <summary>XP still needed for the next level; 0 at the cap, which means "MAX", not "none needed".</summary>
        public int XPForNextLevel => EKVibe.XPForNextLevel(TotalXP);

        [Header("Magic")]
        [Tooltip("Set once Daniel Pauls teaches the first spell.")]
        public bool KnowsSpark;
        [Tooltip("The player-chosen name shouted when casting. Defaults to 'Spark Out'.")]
        public string SpellName = DefaultSpellName;

        [Header("Fight Pit")]
        [Tooltip("True after completing all 10 pit rounds for the first time.")]
        public bool PitTournamentWon;

        [Tooltip("Highest arena round ever completed (Personal Best).")]
        public int HighestPitRound;

        [Tooltip("True once the player has purchased their 1 unique royal crown.")]
        public bool HasPurchasedRoyalCrown;

        public const string DefaultSpellName = "Spark Out";

        /// <summary>
        /// Cleans a player-typed spell name to the allowed set: letters, digits and spaces, max
        /// 16 chars. Empty/blank falls back to <see cref="DefaultSpellName"/>.
        /// </summary>
        public static string SanitizeSpellName(string raw)
        {
            if (string.IsNullOrWhiteSpace(raw)) return DefaultSpellName;

            var sb = new System.Text.StringBuilder(16);
            foreach (char c in raw)
            {
                bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
                          || (c >= '0' && c <= '9') || c == ' ';
                if (ok) sb.Append(c);
                if (sb.Length >= 16) break;
            }
            string cleaned = sb.ToString().Trim();
            return string.IsNullOrEmpty(cleaned) ? DefaultSpellName : cleaned;
        }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        public void BeginNewGame(string characterName, PlayerClass playerClass, CharacterData template)
        {
            // The creator's name box starts empty behind a placeholder, so a blank arriving here
            // is the ordinary "player did not type one" case, not an error.
            CharacterName = string.IsNullOrWhiteSpace(characterName) ? "Vince" : characterName.Trim();
            Class = playerClass;
            TutorialComplete = false;
            HasStartedNewGame = true;
            KnowsSpark = false;
            SpellName = DefaultSpellName;
            // Fight-pit progress must not leak into a same-session New Game: HighestPitRound would
            // show a bogus "Personal Best" on the first fight and HasPurchasedRoyalCrown would
            // permanently bar the new character from the one-per-save crown they never bought.
            PitTournamentWon = false;
            HighestPitRound = 0;
            HasPurchasedRoyalCrown = false;

            // RestoreFromSave immediately repopulates these via RestoreInventory/RestorePounds — a
            // fresh New Game must not inherit whatever a previous playthrough carried or was
            // holding this app session.
            Inventory.Clear();
            OnInventoryChanged?.Invoke();

            // Same contract for worn gear: a New Game starts with an empty paper doll.
            _equipment.Clear();
            OnEquipmentChanged?.Invoke();

            // Same reason: without this a New Game started in the same app session would find
            // every bin the previous playthrough emptied still empty.
            _lootedContainers.Clear();

            // And the same again for restockable containers, which would otherwise start the new
            // run still sitting out the last run's cooldowns.
            _containerCooldowns.Clear();

            // And the map starts blank again: none of the previous run's travels happened.
            _visitedChunks.Clear();

            // So does the encyclopedia: no entries carry over from the last run.
            _unlockedWikiEntries.Clear();

            // And no perks. Load depends on this too — RestoreFromSave calls this method first, so
            // clearing here is what lets RestorePerkIds put the saved set back cleanly.
            _spentPerkIds.Clear();
            OnPerksChanged?.Invoke();

            Pounds = 0;
            OnPoundsChanged?.Invoke();

            // Same contract again, and load depends on it: RestoreFromSave calls this method first,
            // so clearing here is what lets RestoreTotalXP put the saved figure back cleanly. Miss
            // it and a New Game in the same app session starts mid-level with no error anywhere.
            TotalXP = 0;
            OnXPChanged?.Invoke();

            if (RuntimeStats == null)
                RuntimeStats = ScriptableObject.CreateInstance<CharacterData>();

            // ⚠ template may BE RuntimeStats. Both callers pass the scene player's
            // CombatController.PlayerData, and BindPlayerToSession assigns RuntimeStats to that
            // field — so from the second new-game or load in an app session onwards, the
            // "template" is this session's own derived stats, already mutated by growth and
            // perks. Portrait is never itself mutated by the derivation, so it can still be read
            // off the (possibly aliased) template safely — resistances cannot; see
            // _pristineTemplateResistances just below.
            if (template != null && template != RuntimeStats)
                RuntimeStats.Portrait = template.Portrait;

            // BeginNewGame means "start over," every time it runs — including a second New Game
            // in the same app session with a different class, which is exactly the case the old
            // `template != RuntimeStats` guard above got wrong for resistances: by then
            // BindPlayerToSession had already pointed the caller's template at RuntimeStats
            // itself, so the guard silently kept whatever baseline the FIRST character left
            // behind (and would have carried forward any perk baked into it) instead of
            // resetting for the new one. _pristineTemplateResistances is captured once, the
            // first time this app session ever reaches this point — before any template can
            // alias RuntimeStats — and _baselineResistances is reset from that pinned snapshot on
            // every later call, so neither a second New Game nor a same-session reload can ever
            // read resistances back off an already-mutated RuntimeStats.
            if (!_hasCapturedPristineTemplateResistances)
            {
                _pristineTemplateResistances = CopyOf(template != null ? template.BaseResistances : null);
                _hasCapturedPristineTemplateResistances = true;
            }
            _baselineResistances = CopyOf(_pristineTemplateResistances);

            RuntimeStats.CharacterName = CharacterName;
            RecalculateDerivedStats();
        }

        // ── Derived stats ───────────────────────────────────────────────────────────────
        // One deterministic recompute, and the only place derived figures are written. Every step
        // OVERWRITES; nothing accumulates. Running it twice in a row must produce identical
        // results — that property is what makes it safe to call from every place below.

        /// <summary>
        /// The class template's resistances, held apart from <see cref="RuntimeStats"/> so the
        /// recompute has something to reset to.
        ///
        /// ⚠ <c>CharacterData.ApplyClassDefaults</c> does NOT reset <c>BaseResistances</c>. Without
        /// this snapshot, anything that ADDS to a resistance would add again on every recompute:
        /// five level-ups later the player quietly has five times the armour they earned, and
        /// nothing logs it.
        /// </summary>
        private Resistances _baselineResistances = new Resistances();

        /// <summary>
        /// The class template's resistances as they stood the FIRST time <see cref="BeginNewGame"/>
        /// ever ran this app session — before BindPlayerToSession had a chance to repoint the
        /// caller's template at <see cref="RuntimeStats"/> itself. Never touched again after that
        /// first capture, so every later <see cref="BeginNewGame"/> call (a second New Game with a
        /// different class, or a same-session reload) can reset <see cref="_baselineResistances"/>
        /// from something guaranteed never to have been mutated by growth or perks, instead of
        /// gambling on reference-equality against RuntimeStats to decide whether the incoming
        /// template is trustworthy.
        /// </summary>
        private Resistances _pristineTemplateResistances;

        /// <summary>True once <see cref="_pristineTemplateResistances"/> has been captured this app session.</summary>
        private bool _hasCapturedPristineTemplateResistances;

        /// <summary>Value copy — assigning the reference would let the derivation write back into the template asset.</summary>
        private static Resistances CopyOf(Resistances source)
        {
            if (source == null) return new Resistances();
            return new Resistances
            {
                Physical = source.Physical,
                Magic = source.Magic,
                Fire = source.Fire,
                Cold = source.Cold,
                Poison = source.Poison,
            };
        }

        /// <summary>
        /// Recomputes everything derived from level and perks: <see cref="RuntimeStats"/>'s maxima
        /// and resistances, plus the cached query multipliers read at hit time.
        ///
        /// Order is fixed: class defaults, baseline resistances, level growth, perk flat adds, perk
        /// percentages, cached query values, event. Equipment is deliberately NOT folded in — it is
        /// read live at its two use sites (<c>CombatController</c> for weapon damage,
        /// <c>Health</c> for armour), and duplicating it here would double-count every weapon and
        /// every shield with nothing to show for it but wrong numbers.
        /// </summary>
        public void RecalculateDerivedStats()
        {
            if (RuntimeStats == null) return;

            // 1. Class baseline: resets BaseTraits, MaxHealth, MaxManaStamina.
            RuntimeStats.ApplyClassDefaults(Class);

            // 2. ApplyClassDefaults leaves BaseResistances alone, so reset it here or every
            //    later addition compounds. See _baselineResistances.
            RuntimeStats.BaseResistances = CopyOf(_baselineResistances);

            // 3. Automatic per-class growth. Traits deliberately do not grow — see GrowthPerLevel.
            var growth = PlayerClassInfo.GrowthPerLevel(Class);
            int levelsGained = Mathf.Max(0, Level - 1);
            RuntimeStats.MaxHealth += growth.MaxHealth * levelsGained;
            RuntimeStats.MaxManaStamina += growth.MaxManaStamina * levelsGained;

            // 6. Cached query values, reset here so they never accumulate either. Reset before the
            //    perk passes below, which add into them.
            MeleeDamageMultiplier = 1f;
            SpellDamageMultiplier = 1f;
            MoveSpeedMultiplier = 1f;
            ResourceRegenMultiplier = 1f;
            ExtraLootRolls = 0;
            MeleeKnockbackDistance = 0f;

            // 4. Perk FLAT adds. Percentages are gathered here and applied after the loop (step 5),
            //    so a percentage perk multiplies the flat ones rather than the other way round.
            //    One pass over a handful of ids, on level-up, load and spend only — nothing in
            //    here runs per frame or per hit.
            float maxHealthPercent = 0f;

            foreach (string perkId in _spentPerkIds)
            {
                PerkData perk = PerkDatabase.Find(perkId);
                // Null means the asset is missing or the id was renamed. The id stays spent (see
                // RestorePerkIds); PerkDatabase.Find has already logged it, so say nothing more.
                if (perk == null || perk.Effects == null) continue;

                for (int i = 0; i < perk.Effects.Count; i++)
                {
                    PerkEffect effect = perk.Effects[i];
                    if (effect == null) continue;

                    switch (effect.Type)
                    {
                        // Flat adds (step 4).
                        case PerkEffectType.MaxHealthFlat:
                            RuntimeStats.MaxHealth += Mathf.RoundToInt(effect.Magnitude);
                            break;
                        case PerkEffectType.MaxResourceFlat:
                            RuntimeStats.MaxManaStamina += Mathf.RoundToInt(effect.Magnitude);
                            break;
                        case PerkEffectType.ArmourFlat:
                            // Into Physical, which is what BOTH the character sheet's Armor line and
                            // EffectiveArmour read — so the readout and the mitigation move together.
                            RuntimeStats.BaseResistances.Physical += Mathf.RoundToInt(effect.Magnitude);
                            break;

                        // Percentages (step 5), gathered here and applied after the loop.
                        case PerkEffectType.MaxHealthPercent:
                            maxHealthPercent += effect.Magnitude;
                            break;

                        // Cached query values (step 6). Magnitude is a percentage: 15 means +15%.
                        case PerkEffectType.MeleeDamagePercent:
                            MeleeDamageMultiplier += effect.Magnitude / 100f;
                            break;
                        case PerkEffectType.SpellDamagePercent:
                            SpellDamageMultiplier += effect.Magnitude / 100f;
                            break;
                        case PerkEffectType.ResourceRegenPercent:
                            ResourceRegenMultiplier += effect.Magnitude / 100f;
                            break;
                        case PerkEffectType.MoveSpeedPercent:
                            MoveSpeedMultiplier += effect.Magnitude / 100f;
                            break;
                        case PerkEffectType.ExtraLootRolls:
                            ExtraLootRolls += Mathf.RoundToInt(effect.Magnitude);
                            break;
                        case PerkEffectType.MeleeKnockback:
                            // Flat metres, not a percentage — two such perks stack by addition.
                            MeleeKnockbackDistance += effect.Magnitude;
                            break;
                    }
                }
            }

            // 5. Percentages last, over the flat total.
            if (maxHealthPercent != 0f)
                RuntimeStats.MaxHealth = Mathf.RoundToInt(RuntimeStats.MaxHealth * (1f + maxHealthPercent / 100f));

            ExtraLootRolls = Mathf.Max(0, ExtraLootRolls);
            MeleeKnockbackDistance = Mathf.Max(0f, MeleeKnockbackDistance);
            MoveSpeedMultiplier = Mathf.Max(0.1f, MoveSpeedMultiplier);
            ResourceRegenMultiplier = Mathf.Max(0f, ResourceRegenMultiplier);

            RuntimeStats.MaxHealth = Mathf.Max(1, RuntimeStats.MaxHealth);
            RuntimeStats.MaxManaStamina = Mathf.Max(0, RuntimeStats.MaxManaStamina);

            OnStatsChanged?.Invoke();
        }

        // Cached query values, recomputed only in RecalculateDerivedStats and read raw at hit time.
        // Plain fields on purpose: this project keeps hot paths allocation-free (CLAUDE.md §2), and
        // walking a perk list on every swing would allocate an enumerator per hit.

        /// <summary>Multiplies the whole melee swing, weapon included. 1 = unmodified.</summary>
        public float MeleeDamageMultiplier { get; private set; } = 1f;

        /// <summary>Multiplies a cast ability's BaseDamage. 1 = unmodified.</summary>
        public float SpellDamageMultiplier { get; private set; } = 1f;

        /// <summary>Registered with CombatController.SetSpeedMultiplier, never written to MovementSpeed.</summary>
        public float MoveSpeedMultiplier { get; private set; } = 1f;

        /// <summary>Scales the authored STAMINA regen rate. 1 = unmodified. Mana has no regen rate
        /// to scale — it is replenished by items, the pub and heal spells only.</summary>
        public float ResourceRegenMultiplier { get; private set; } = 1f;

        /// <summary>Extra rolls a loot container makes on top of its band's own count.</summary>
        public int ExtraLootRolls { get; private set; }

        /// <summary>Metres the player's melee hits shove a living enemy. 0 = no shove.</summary>
        public float MeleeKnockbackDistance { get; private set; }

        /// <summary>Rebuild the session from a save file (same stat derivation as a new game).</summary>
        public void RestoreFromSave(string characterName, PlayerClass playerClass, bool tutorialComplete, CharacterData template)
        {
            BeginNewGame(characterName, playerClass, template);
            TutorialComplete = tutorialComplete;
        }

        public void CompleteTutorial()
        {
            TutorialComplete = true;
        }

        /// <summary>
        /// Adds a quantity of an item, honouring <see cref="ItemData.Stackable"/> and
        /// <see cref="ItemData.MaxStack"/>.
        ///
        /// One item can therefore occupy several entries in <see cref="Inventory"/>, which is why
        /// every read below sums across entries rather than finding the first one. A non-stackable
        /// item takes one entry per unit — that is what a sword or a piece of armour wants, since
        /// the paper doll equips a single object.
        ///
        /// Fires <see cref="OnInventoryChanged"/> exactly once, however many entries it touched:
        /// the HUD rebuilds the whole backpack on each event, and firing per stack would rebuild it
        /// several times for one pickup.
        /// </summary>
        public void AddItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return;

            if (!item.Stackable)
            {
                for (int i = 0; i < quantity; i++)
                    Inventory.Add(new InventoryStack { Item = item, Quantity = 1 });

                OnInventoryChanged?.Invoke();
                return;
            }

            // 0 or less means unlimited, so the whole lot goes on one stack.
            int cap = item.MaxStack > 0 ? item.MaxStack : int.MaxValue;
            int remaining = quantity;

            // Top up existing stacks in list order first, so the backpack fills from the left
            // rather than sprouting a new half-empty stack next to a half-empty one.
            for (int i = 0; i < Inventory.Count && remaining > 0; i++)
            {
                var existing = Inventory[i];
                if (existing == null || existing.Item != item) continue;

                int room = cap - existing.Quantity;
                if (room <= 0) continue;

                int moved = Mathf.Min(room, remaining);
                existing.Quantity += moved;
                remaining -= moved;
            }

            while (remaining > 0)
            {
                int moved = Mathf.Min(cap, remaining);
                Inventory.Add(new InventoryStack { Item = item, Quantity = moved });
                remaining -= moved;
            }

            OnInventoryChanged?.Invoke();
        }

        /// <summary>
        /// True if the player carries at least the given quantity of an item, counted across every
        /// stack of it. Quest conditions read this, so a requirement for three of something must
        /// still be met when those three are split over two stacks.
        /// </summary>
        public bool HasItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return false;
            return CountItem(item) >= quantity;
        }

        /// <summary>Total carried, summed across every stack of the item.</summary>
        public int CountItem(ItemData item)
        {
            if (item == null) return 0;

            int total = 0;
            for (int i = 0; i < Inventory.Count; i++)
            {
                var stack = Inventory[i];
                if (stack != null && stack.Item == item) total += stack.Quantity;
            }
            return total;
        }

        /// <summary>
        /// Removes a quantity of an item, draining stacks from the end of the list backwards and
        /// dropping each as it empties. Returns false and changes nothing if the player does not
        /// carry enough — the all-or-nothing contract callers already rely on, which is why the
        /// total is checked before anything is taken.
        /// </summary>
        public bool RemoveItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return false;
            if (CountItem(item) < quantity) return false;

            int remaining = quantity;
            for (int i = Inventory.Count - 1; i >= 0 && remaining > 0; i--)
            {
                var stack = Inventory[i];
                if (stack == null || stack.Item != item) continue;

                int taken = Mathf.Min(stack.Quantity, remaining);
                stack.Quantity -= taken;
                remaining -= taken;

                if (stack.Quantity <= 0) Inventory.RemoveAt(i);
            }

            OnInventoryChanged?.Invoke();
            return true;
        }

        /// <summary>Pays the player. Non-positive amounts are ignored rather than silently reversing a payout.</summary>
        public void AddPounds(int amount)
        {
            if (amount <= 0) return;
            Pounds += amount;
            OnPoundsChanged?.Invoke();
        }

        /// <summary>
        /// Takes money off the player. Returns false and changes nothing if they cannot afford it,
        /// the same all-or-nothing contract as <see cref="RemoveItem"/> — a caller that wants to
        /// take whatever is there (a fine, say) clamps to <see cref="Pounds"/> first.
        /// </summary>
        public bool SpendPounds(int amount)
        {
            if (amount <= 0 || Pounds < amount) return false;
            Pounds -= amount;
            OnPoundsChanged?.Invoke();
            return true;
        }

        /// <summary>Replace the wallet with a saved snapshot (load game).</summary>
        public void RestorePounds(int saved)
        {
            Pounds = Mathf.Max(0, saved);
            OnPoundsChanged?.Invoke();
        }

        /// <summary>
        /// Awards XP. Non-positive amounts are ignored rather than silently taking XP back, the
        /// same guard <see cref="AddPounds"/> uses.
        ///
        /// <paramref name="source"/> is a label for whoever granted it (an enemy's display name, a
        /// quest id) — carried for future toasts and debugging, not used for any arithmetic.
        ///
        /// <see cref="OnLevelUp"/> fires once per level crossed: a single large grant (a quest
        /// reward, say) can cross more than one, so this loops rather than assuming one.
        /// </summary>
        public void GrantXP(int amount, string source = null)
        {
            if (amount <= 0) return;

            int before = Level;
            TotalXP += amount;
            OnXPChanged?.Invoke();

            int after = Level;

            // Once, after the loop rather than per level crossed: the derivation reads Level, not
            // a delta, so recomputing inside the loop would do identical work several times.
            if (after != before) RecalculateDerivedStats();

            for (int level = before + 1; level <= after; level++)
                OnLevelUp?.Invoke(level);
        }

        /// <summary>
        /// Replace the XP total with a saved snapshot (load game).
        ///
        /// The recompute is not optional: loading calls RestoreFromSave -> BeginNewGame ->
        /// ApplyClassDefaults, which rebuilds RuntimeStats from the level-1 class baseline. Without
        /// this the level is restored but every level's growth is silently stripped, and the player
        /// looks fine — just weaker than when they saved.
        /// </summary>
        public void RestoreTotalXP(int saved)
        {
            TotalXP = Mathf.Max(0, saved);
            OnXPChanged?.Invoke();
            RecalculateDerivedStats();
        }

        /// <summary>Records that a Fixed container has been emptied. Ids are compared verbatim.</summary>
        public void MarkContainerLooted(string containerId)
        {
            if (string.IsNullOrEmpty(containerId)) return;
            _lootedContainers.Add(containerId);
        }

        /// <summary>True if this container was emptied earlier in the run, or in a loaded save.</summary>
        public bool IsContainerLooted(string containerId)
        {
            if (string.IsNullOrEmpty(containerId)) return false;
            return _lootedContainers.Contains(containerId);
        }

        /// <summary>
        /// Replace the looted-container set with a saved snapshot (load game).
        ///
        /// ⚠ Must run before the world is built. Every SpriteContainer reads this in its own Awake,
        /// and a chunk instantiated first would populate its bins from an empty set and refill
        /// everything the player had already cleared. GameFlowController.ContinueFromSave calls
        /// this immediately after RestorePounds, before LoadWorld.
        /// </summary>
        public void RestoreLootedContainers(List<string> saved)
        {
            _lootedContainers.Clear();
            if (saved == null) return;

            foreach (string id in saved)
            {
                if (!string.IsNullOrEmpty(id)) _lootedContainers.Add(id);
            }
        }

        // ── Container cooldowns ─────────────────────────────────────────────────────────
        // A restockable container empties, sits out a number of visits to its chunk, and refills.
        // Chunks are destroyed and rebuilt on every visit, so "a visit" is the only clock the world
        // already has — there is no in-chunk timer here and nothing below adds one.
        //
        // ⚠ Every id is save-key text and is compared verbatim. Never trim, lower-case or slugify:
        // Manor_Cellars_Data has ChunkName "Manor Cellars", with a space.

        /// <summary>
        /// Starts a container's cooldown, replacing any it already had. A count at or below zero is
        /// ignored rather than stored, since it would mean "already free".
        /// </summary>
        public void AddContainerCooldown(string containerId, int visits)
        {
            if (string.IsNullOrEmpty(containerId) || visits <= 0) return;
            _containerCooldowns[containerId] = visits;
        }

        /// <summary>
        /// True only while a container still owes visits. An entry sitting at zero reads as free,
        /// which is what lets <see cref="DecrementContainerCooldowns"/> clamp instead of removing.
        /// </summary>
        public bool IsContainerOnCooldown(string containerId)
        {
            if (string.IsNullOrEmpty(containerId)) return false;
            return _containerCooldowns.TryGetValue(containerId, out int remaining) && remaining > 0;
        }

        /// <summary>
        /// Counts one visit against every container in a chunk, clamped at zero. Returns exactly
        /// the ids this call decremented, so <see cref="IncrementContainerCooldowns"/> can undo
        /// precisely this tick rather than re-deriving "everything in the chunk" — an entry already
        /// sitting at zero (spent, not yet pruned) is correctly left out of the returned list, so a
        /// later give-back cannot mistake it for one this tick touched and bump it back to 1.
        ///
        /// Two passes because a Dictionary cannot be written while it is being enumerated; the key
        /// list is built fresh rather than kept as a parallel field, since this runs once per chunk
        /// transition behind a loading screen and not in any Update path.
        /// </summary>
        public List<string> DecrementContainerCooldowns(string chunkName)
        {
            var touched = new List<string>();
            if (string.IsNullOrEmpty(chunkName) || _containerCooldowns.Count == 0) return touched;

            string prefix = chunkName + "/";
            foreach (var pair in _containerCooldowns)
            {
                if (pair.Key.StartsWith(prefix, StringComparison.Ordinal) && pair.Value > 0)
                    touched.Add(pair.Key);
            }

            foreach (string id in touched)
                _containerCooldowns[id] = _containerCooldowns[id] - 1;

            return touched;
        }

        /// <summary>
        /// Gives back a visit to exactly the ids passed in — the compensating inverse of
        /// <see cref="DecrementContainerCooldowns"/>, for a journey that was aborted after the tick.
        /// Takes the exact list <c>DecrementContainerCooldowns</c> returned rather than re-deriving
        /// "everything in the chunk" by prefix: a container already at zero before the tick (spent,
        /// not yet pruned) was correctly skipped by the decrement and must stay skipped here too, or
        /// an unrelated aborted journey would re-lock an already-free container.
        /// </summary>
        public void IncrementContainerCooldowns(List<string> containerIds)
        {
            if (containerIds == null) return;

            foreach (string id in containerIds)
            {
                if (_containerCooldowns.TryGetValue(id, out int remaining))
                    _containerCooldowns[id] = remaining + 1;
            }
        }

        /// <summary>
        /// Drops entries that have run out. Housekeeping only — <see cref="IsContainerOnCooldown"/>
        /// already treats a spent entry as free — so this exists to stop the save file growing an
        /// entry per container the player has ever emptied.
        /// </summary>
        public void RemoveExpiredCooldowns()
        {
            if (_containerCooldowns.Count == 0) return;

            var spent = new List<string>();
            foreach (var pair in _containerCooldowns)
            {
                if (pair.Value <= 0) spent.Add(pair.Key);
            }

            foreach (string id in spent) _containerCooldowns.Remove(id);
        }

        /// <summary>
        /// Replace the cooldown table with a saved snapshot (load game).
        ///
        /// ⚠ Must run before the world is built, for the same reason as
        /// <see cref="RestoreLootedContainers"/>: every container reads this in its own Awake, and a
        /// chunk instantiated first would find an empty table and refill everything.
        /// A null list is a pre-cooldown save and correctly leaves every container fresh.
        /// </summary>
        public void RestoreContainerCooldowns(List<ContainerCooldown> saved)
        {
            _containerCooldowns.Clear();
            if (saved == null) return;

            foreach (var entry in saved)
            {
                if (entry == null || string.IsNullOrEmpty(entry.Id) || entry.VisitsRemaining <= 0)
                    continue;
                _containerCooldowns[entry.Id] = entry.VisitsRemaining;
            }
        }

        // ── Visited chunks ──────────────────────────────────────────────────────────────
        // Every chunk the player has set foot in, by ChunkName — the Map of Britain draws a
        // named node for each of these and "???" for the rest. Same save contract as
        // _lootedContainers: a runtime HashSet here, a List<string> on SaveData.

        private readonly HashSet<string> _visitedChunks = new HashSet<string>();

        /// <summary>Read-only view for the saver. Enumeration order is not meaningful.</summary>
        public IEnumerable<string> VisitedChunks => _visitedChunks;

        /// <summary>Records that the player has entered a chunk. Names are compared verbatim.</summary>
        public void MarkChunkVisited(string chunkName)
        {
            if (string.IsNullOrEmpty(chunkName)) return;
            _visitedChunks.Add(chunkName);
        }

        /// <summary>True if the player entered this chunk earlier in the run, or in a loaded save.</summary>
        public bool IsChunkVisited(string chunkName)
        {
            if (string.IsNullOrEmpty(chunkName)) return false;
            return _visitedChunks.Contains(chunkName);
        }

        /// <summary>Replace the visited set with a saved snapshot (load game). Null means a pre-map save → nothing visited yet.</summary>
        public void RestoreVisitedChunks(List<string> saved)
        {
            _visitedChunks.Clear();
            if (saved == null) return;

            foreach (string name in saved)
            {
                if (!string.IsNullOrEmpty(name)) _visitedChunks.Add(name);
            }
        }

        // ── Wiki unlocks ────────────────────────────────────────────────────────────────
        // WIKIBRITAIN entries the player has unlocked, by EntryID. The encyclopedia window
        // greys out everything not in here; the toast pops when an id first lands in it.

        private readonly HashSet<string> _unlockedWikiEntries = new HashSet<string>();

        /// <summary>Read-only view for the saver. Enumeration order is not meaningful.</summary>
        public IEnumerable<string> UnlockedWikiEntries => _unlockedWikiEntries;

        /// <summary>
        /// Records an unlocked WIKIBRITAIN entry. Returns true only the first time an id is
        /// unlocked — callers use that to fire the toast on genuinely new entries.
        /// </summary>
        public bool UnlockWikiEntry(string entryId)
        {
            if (string.IsNullOrEmpty(entryId)) return false;
            return _unlockedWikiEntries.Add(entryId);
        }

        /// <summary>True if this entry was unlocked earlier in the run, or in a loaded save.</summary>
        public bool IsWikiEntryUnlocked(string entryId)
        {
            if (string.IsNullOrEmpty(entryId)) return false;
            return _unlockedWikiEntries.Contains(entryId);
        }

        /// <summary>Replace the unlock set with a saved snapshot (load game). Null = pre-wiki save → nothing unlocked yet.</summary>
        public void RestoreWikiEntries(List<string> saved)
        {
            _unlockedWikiEntries.Clear();
            if (saved == null) return;

            foreach (string id in saved)
            {
                if (!string.IsNullOrEmpty(id)) _unlockedWikiEntries.Add(id);
            }
        }

        // ── Perks ───────────────────────────────────────────────────────────────────────
        // Which perks the player has spent points on, by PerkId. Same save contract as the wiki
        // unlocks above: a runtime HashSet here, a List<string> on SaveData.

        private readonly HashSet<string> _spentPerkIds = new HashSet<string>();

        /// <summary>Read-only view for the saver. Enumeration order is not meaningful.</summary>
        public IEnumerable<string> SpentPerkIds => _spentPerkIds;

        /// <summary>Fires whenever the set of taken perks changes (spend, restore from save).</summary>
        public event Action OnPerksChanged;

        /// <summary>
        /// Points earned by the current level, less those already spent.
        ///
        /// Clamped at 0 deliberately: if the curve in <see cref="EKVibe.PerkPointsAtLevel"/> is ever
        /// retuned downward, a loaded player can hold more spent ids than the new curve pays for.
        /// The clamp only keeps this figure from going negative — the derivation still honours
        /// EVERY spent id, so nothing is quietly unspent behind the player's back.
        /// </summary>
        public int UnspentPerkPoints =>
            Mathf.Max(0, EKVibe.PerkPointsAtLevel(Level) - _spentPerkIds.Count);

        /// <summary>True if the player has taken this perk. Ids are compared verbatim.</summary>
        public bool HasPerk(string perkId)
        {
            if (string.IsNullOrEmpty(perkId)) return false;
            return _spentPerkIds.Contains(perkId);
        }

        /// <summary>
        /// Everything that would stop <see cref="SpendPerkPoint"/> succeeding, so the UI can grey
        /// its button and say why without attempting the spend. Null when the perk can be taken.
        /// Generated text, not prose.
        /// </summary>
        public string PerkRefusalReason(PerkData perk)
        {
            if (perk == null || string.IsNullOrEmpty(perk.PerkId)) return "Unavailable";
            if (HasPerk(perk.PerkId)) return "Already taken";
            if (!perk.CanBeTakenBy(Class)) return PlayerClassInfo.DisplayName(Class) + " cannot take this";
            if (Level < perk.MinLevel) return "Requires level " + perk.MinLevel;
            if (perk.Prerequisite != null && !HasPerk(perk.Prerequisite.PerkId))
                return "Requires " + (string.IsNullOrEmpty(perk.Prerequisite.Title)
                    ? perk.Prerequisite.PerkId
                    : perk.Prerequisite.Title);
            if (UnspentPerkPoints <= 0) return "No points to spend";
            return null;
        }

        /// <summary>
        /// Spends a point on a perk. Returns false and changes nothing if anything refuses it —
        /// the same all-or-nothing contract as <see cref="RemoveItem"/> and
        /// <see cref="SpendPounds"/>.
        /// </summary>
        public bool SpendPerkPoint(PerkData perk)
        {
            if (PerkRefusalReason(perk) != null) return false;

            _spentPerkIds.Add(perk.PerkId);
            RecalculateDerivedStats();
            OnPerksChanged?.Invoke();
            return true;
        }

        /// <summary>
        /// Replace the taken-perk set with a saved snapshot (load game). Null = a pre-perk save →
        /// nothing taken yet.
        ///
        /// Ids that no longer resolve to an asset are KEPT, which is deliberately the opposite of
        /// what <see cref="RestoreInventory"/> does with an unresolvable item. Dropping them looks
        /// tidy but quietly refunds the point, so a temporarily missing or renamed asset would hand
        /// out a free respec. Keeping the id leaves the point spent; the derivation skips what it
        /// cannot resolve, and re-adding the asset restores the perk.
        ///
        /// The recompute at the end is not optional: loading rebuilds RuntimeStats from the class
        /// baseline, so without it the perks are listed as taken and none of their effects exist.
        /// </summary>
        public void RestorePerkIds(List<string> saved)
        {
            _spentPerkIds.Clear();
            if (saved != null)
            {
                foreach (string id in saved)
                {
                    if (!string.IsNullOrEmpty(id)) _spentPerkIds.Add(id);
                }
            }
            RecalculateDerivedStats();
            OnPerksChanged?.Invoke();
        }

        /// <summary>Replace the carried inventory with a saved snapshot (load game). Unresolvable item ids are skipped.</summary>
        public void RestoreInventory(List<InventorySaveEntry> saved)
        {
            Inventory.Clear();
            if (saved != null)
            {
                foreach (var entry in saved)
                {
                    if (entry == null || entry.Quantity <= 0) continue;
                    ItemData item = ItemDatabase.Find(entry.ItemID);
                    if (item != null)
                        Inventory.Add(new InventoryStack { Item = item, Quantity = entry.Quantity });
                }
            }
            OnInventoryChanged?.Invoke();
        }

        // ── Equipment ─────────────────────────────────────────────────────────────────
        // What the paper doll wears: one item per equippable ItemType, the bag holds the rest.
        // Equip/Unequip move items between the two, so the bag and doll redraw together.

        private readonly Dictionary<ItemType, ItemData> _equipment = new Dictionary<ItemType, ItemData>();

        public event Action OnEquipmentChanged;

        public IReadOnlyDictionary<ItemType, ItemData> Equipment => _equipment;

        public ItemData EquippedIn(ItemType type)
        {
            _equipment.TryGetValue(type, out ItemData item);
            return item;
        }

        public ItemData EquippedWeapon() => EquippedIn(ItemType.Weapon);

        /// <summary>Sum of Armor across every worn piece.</summary>
        public int TotalArmor()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.Armor;
            return total;
        }

        /// <summary>Flat melee attack supplied by all equipped items.</summary>
        public int TotalAttackBonus()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.AttackBonus;
            return total;
        }

        /// <summary>Poison resistance supplied by all equipped items.</summary>
        public int TotalPoisonResistance()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.PoisonResistance;
            return total;
        }

        /// <summary>Base/perk poison resistance plus the live equipment contribution.</summary>
        public int EffectivePoisonResistance() =>
            TotalPoisonResistance() + (RuntimeStats != null ? RuntimeStats.BaseResistances.Poison : 0);

        /// <summary>Fire resistance supplied by all equipped items (e.g. Crown of the Bastion).</summary>
        public int TotalFireResistance()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.FireResistance;
            return total;
        }

        /// <summary>Base/perk fire resistance plus live equipment contribution.</summary>
        public int EffectiveFireResistance() =>
            TotalFireResistance() + (RuntimeStats != null ? RuntimeStats.BaseResistances.Fire : 0);

        /// <summary>Flat bonus Max HP granted by equipped items (e.g. Crown of Vitality).</summary>
        public int TotalMaxHealthBonus()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.MaxHealthBonus;
            return total;
        }

        /// <summary>Total effective Max Health (base runtime stats + equipment bonuses).</summary>
        public int EffectiveMaxHealth() =>
            (RuntimeStats != null ? RuntimeStats.MaxHealth : 100) + TotalMaxHealthBonus();

        /// <summary>Flat bonus Max Mana granted by equipped items (e.g. Crown of the Archmage).</summary>
        public int TotalMaxManaBonus()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.MaxManaBonus;
            return total;
        }

        /// <summary>Total effective Max Mana (base runtime stats + equipment bonuses).</summary>
        public int EffectiveMaxMana() =>
            (RuntimeStats != null ? RuntimeStats.MaxManaStamina : 50) + TotalMaxManaBonus();

        /// <summary>Magic damage bonus added to spells and magic ranged attacks from gear.</summary>
        public int TotalMagicDamageBonus()
        {
            int total = 0;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.MagicDamageBonus;
            return total;
        }

        public int EffectiveMagicDamage() => TotalMagicDamageBonus();

        /// <summary>Passive health regeneration per second from gear (e.g. Crown of Vitality).</summary>
        public float TotalHealthRegenPerSecond()
        {
            float total = 0f;
            foreach (var pair in _equipment)
                if (pair.Value != null) total += pair.Value.HealthRegenPerSecond;
            return total;
        }

        /// <summary>
        /// Worn armour plus derived Physical resistance — the single number the mitigation curve
        /// reads (<see cref="EKVibe.ArmourReduction"/>).
        /// </summary>
        public int EffectiveArmour() =>
            TotalArmor() + (RuntimeStats != null ? RuntimeStats.BaseResistances.Physical : 0);

        /// <summary>
        /// Moves one of the item from the bag into its paper-doll slot; the piece already
        /// there goes back to the bag (a swap). Refuses class-gated and non-equippable items,
        /// and items the player does not actually carry — RemoveItem's all-or-nothing check
        /// runs before anything moves.
        /// </summary>
        public bool Equip(ItemData item)
        {
            if (item == null || !item.IsEquippable) return false;
            if (!item.CanBeUsedBy(Class)) return false;
            if (!RemoveItem(item, 1)) return false;

            ItemData previous = EquippedIn(item.Type);
            _equipment[item.Type] = item;
            if (previous != null)
                AddItem(previous, 1);

            OnEquipmentChanged?.Invoke();
            return true;
        }

        /// <summary>Returns the slot's item to the bag. False if the slot is already empty.</summary>
        public bool Unequip(ItemType type)
        {
            ItemData item = EquippedIn(type);
            if (item == null) return false;

            _equipment.Remove(type);
            AddItem(item, 1);
            OnEquipmentChanged?.Invoke();
            return true;
        }

        /// <summary>
        /// Replace equipment with a saved snapshot (load game). Entries whose id no longer
        /// resolves, whose slot index is out of range, or whose item type no longer matches
        /// the slot are skipped rather than breaking the load.
        /// </summary>
        public void RestoreEquipment(List<EquipSaveEntry> saved)
        {
            _equipment.Clear();
            if (saved != null)
            {
                foreach (var entry in saved)
                {
                    if (entry == null) continue;
                    if (!Enum.IsDefined(typeof(ItemType), entry.Slot)) continue;

                    ItemData item = ItemDatabase.Find(entry.ItemID);
                    if (item != null && item.IsEquippable && item.Type == (ItemType)entry.Slot)
                        _equipment[(ItemType)entry.Slot] = item;
                }
            }
            OnEquipmentChanged?.Invoke();
        }
    }
}
