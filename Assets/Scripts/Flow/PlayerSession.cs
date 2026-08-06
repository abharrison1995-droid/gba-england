using System;
using System.Collections.Generic;
using UnityEngine;
using ExiledAlvaston.Data;

namespace ExiledAlvaston.Flow
{
    /// <summary>One stack of a carried item — a quantity of the same ItemData.</summary>
    [Serializable]
    public class InventoryStack
    {
        public ItemData Item;
        public int Quantity;
    }

    /// <summary>
    /// Runtime session for Discover England — created character + tutorial flags.
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

        [Header("Wallet")]
        [Tooltip("Pounds carried. Whole pounds only — there are no pence anywhere in the game.")]
        public int Pounds;

        /// <summary>Fires whenever the wallet changes (payout, spend, restore from save).</summary>
        public event Action OnPoundsChanged;

        [Header("Magic")]
        [Tooltip("Set once Daniel Pauls teaches the first spell.")]
        public bool KnowsSpark;
        [Tooltip("The player-chosen name shouted when casting. Defaults to 'Spark Out'.")]
        public string SpellName = DefaultSpellName;

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

            // RestoreFromSave immediately repopulates these via RestoreInventory/RestorePounds — a
            // fresh New Game must not inherit whatever a previous playthrough carried or was
            // holding this app session.
            Inventory.Clear();
            OnInventoryChanged?.Invoke();

            // Same reason: without this a New Game started in the same app session would find
            // every bin the previous playthrough emptied still empty.
            _lootedContainers.Clear();

            Pounds = 0;
            OnPoundsChanged?.Invoke();

            if (RuntimeStats == null)
                RuntimeStats = ScriptableObject.CreateInstance<CharacterData>();

            if (template != null)
            {
                RuntimeStats.Portrait = template.Portrait;
                RuntimeStats.BaseResistances = template.BaseResistances;
            }

            RuntimeStats.CharacterName = CharacterName;
            RuntimeStats.ApplyClassDefaults(Class);
        }

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
    }
}
