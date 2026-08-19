using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.UI;
using GBHEngland.World;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Corpse loot container for enemies: on <see cref="Health.OnDeath"/>, rolls loot from fixed
    /// <see cref="Loot"/> and weighted <see cref="Band"/>, poses as a dead corpse container with an
    /// <see cref="Interactable"/> prompt, and opens <see cref="LootMenuUI"/> when searched by the player.
    /// This allows players to finish multi-enemy combat encounters uninterrupted before looting corpses.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class LootOnDeath : MonoBehaviour
    {
        public LootDrop[] Loot;

        [Tooltip("Optional weighted drops rolled once on death, in addition to fixed Loot.")]
        public LootBand Band;

        [Tooltip("Horizontal distance in metres the player must stand within to search this corpse.")]
        public float InteractRange = 2.2f;

        [Tooltip("Seconds an emptied/looted corpse lingers before being destroyed. 0 or negative = keep until chunk unload.")]
        public float DespawnLootedDelay = 15f;

        [Tooltip("Seconds an unlooted corpse lingers before being destroyed. 0 or negative = keep until chunk unload.")]
        public float DespawnUnlootedDelay = 180f;

        private Health _health;
        private Interactable _interactable;
        private List<LootEntry> _storedEntries;
        private bool _isCorpseInitialized;
        private float _despawnAt = -1f;

        private void Awake()
        {
            _health = GetComponent<Health>();
            if (_health != null)
                _health.OnDeath.AddListener(OnDied);
        }

        private void OnDestroy()
        {
            if (_health != null)
                _health.OnDeath.RemoveListener(OnDied);
        }

        private void OnDied()
        {
            if (_isCorpseInitialized) return;
            _isCorpseInitialized = true;

            _storedEntries = new List<LootEntry>();
            if (Loot != null)
            {
                foreach (LootDrop drop in Loot)
                {
                    if (drop == null || drop.Item == null || drop.Quantity <= 0) continue;
                    AddEntry(_storedEntries, drop.Item, drop.Quantity);
                }
            }

            if (Band != null)
            {
                foreach (LootBandResult result in Band.Roll())
                {
                    if (result == null || result.Item == null || result.Quantity <= 0) continue;
                    AddEntry(_storedEntries, result.Item, result.Quantity);
                }
            }

            if (_storedEntries.Count > 0)
            {
                string targetName = _health != null && !string.IsNullOrEmpty(_health.DisplayName)
                    ? _health.DisplayName
                    : "Corpse";

                _interactable = gameObject.AddComponent<Interactable>();
                _interactable.Prompt = $"Search {targetName}";
                _interactable.InteractRange = InteractRange;
                _interactable.Reusable = true;
                _interactable.OnInteract.AddListener(OpenCorpseLoot);

                if (DespawnUnlootedDelay > 0f)
                    _despawnAt = Time.time + DespawnUnlootedDelay;
            }
            else
            {
                // No loot was dropped on this corpse; begin looted decay timer
                if (DespawnLootedDelay > 0f)
                    _despawnAt = Time.time + DespawnLootedDelay;
            }
        }

        private void OpenCorpseLoot()
        {
            if (_storedEntries == null || _storedEntries.Count == 0) return;

            string title = _health != null && !string.IsNullOrEmpty(_health.DisplayName)
                ? _health.DisplayName
                : "Corpse";

            LootMenuUI.Show(title, _storedEntries, OnLootMenuClosed);
        }

        private void OnLootMenuClosed()
        {
            if (_storedEntries == null) return;

            bool hasUntaken = false;
            for (int i = 0; i < _storedEntries.Count; i++)
            {
                if (_storedEntries[i] != null && !_storedEntries[i].Taken)
                {
                    hasUntaken = true;
                    break;
                }
            }

            if (!hasUntaken)
            {
                // All items taken; remove interactable prompt and schedule cleanup
                if (_interactable != null)
                {
                    _interactable.enabled = false;
                    Destroy(_interactable);
                    _interactable = null;
                }

                if (DespawnLootedDelay > 0f)
                    _despawnAt = Time.time + DespawnLootedDelay;
            }
        }

        private void Update()
        {
            if (!_isCorpseInitialized || _despawnAt <= 0f) return;

            // Do not despawn while the loot menu is open
            if (LootMenuUI.IsOpen) return;

            if (Time.time >= _despawnAt)
            {
                Destroy(gameObject);
            }
        }

        private static void AddEntry(List<LootEntry> entries, ItemData item, int quantity)
        {
            string label = quantity > 1 ? $"{item.ItemName} x{quantity}" : item.ItemName;
            entries.Add(new LootEntry
            {
                Name = label,
                Description = item.Description,
                Icon = item.Icon,
                OnTaken = () =>
                {
                    if (PlayerSession.Instance != null)
                        PlayerSession.Instance.AddItem(item, quantity);
                }
            });
        }
    }
}
