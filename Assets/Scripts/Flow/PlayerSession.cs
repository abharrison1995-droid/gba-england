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
        public string CharacterName = "Exile";
        public PlayerClass Class = PlayerClass.YoungDriller;
        public CharacterData RuntimeStats;

        [Header("Progress")]
        public bool TutorialComplete;
        public bool HasStartedNewGame;

        [Header("Inventory")]
        public List<InventoryStack> Inventory = new List<InventoryStack>();

        /// <summary>Fires whenever the carried inventory changes (pickup, restore from save).</summary>
        public event Action OnInventoryChanged;

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
            CharacterName = string.IsNullOrWhiteSpace(characterName) ? "Exile" : characterName.Trim();
            Class = playerClass;
            TutorialComplete = false;
            HasStartedNewGame = true;

            // RestoreFromSave immediately repopulates this via RestoreInventory — a fresh New
            // Game must not inherit whatever a previous playthrough carried this app session.
            Inventory.Clear();
            OnInventoryChanged?.Invoke();

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

        /// <summary>Adds a quantity of an item, stacking onto an existing entry if present.</summary>
        public void AddItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return;

            InventoryStack stack = Inventory.Find(s => s.Item == item);
            if (stack != null)
                stack.Quantity += quantity;
            else
                Inventory.Add(new InventoryStack { Item = item, Quantity = quantity });

            OnInventoryChanged?.Invoke();
        }

        /// <summary>True if the player carries at least the given quantity of an item.</summary>
        public bool HasItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return false;
            InventoryStack stack = Inventory.Find(s => s.Item == item);
            return stack != null && stack.Quantity >= quantity;
        }

        /// <summary>Removes a quantity of an item; the stack is dropped once it hits zero. Returns false if there wasn't enough.</summary>
        public bool RemoveItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return false;

            InventoryStack stack = Inventory.Find(s => s.Item == item);
            if (stack == null || stack.Quantity < quantity) return false;

            stack.Quantity -= quantity;
            if (stack.Quantity <= 0)
                Inventory.Remove(stack);

            OnInventoryChanged?.Invoke();
            return true;
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
