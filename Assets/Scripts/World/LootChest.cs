using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Generic, drag-and-drop chest: Interact opens the lid and a loot menu built from
    /// <see cref="Loot"/>; taking an entry adds it to <see cref="PlayerSession"/>'s inventory.
    /// Pair with the Chest Placement editor tool, or add by hand and assign Loot yourself.
    /// Give it a <see cref="QuestActor"/> alongside it if quest code needs to find this
    /// specific chest (e.g. to react to <see cref="OnLooted"/>).
    /// </summary>
    public class LootChest : MonoBehaviour
    {
        [Tooltip("Shown as the loot menu's title.")]
        public string ChestName = "Chest";
        public LootDrop[] Loot;

        [Tooltip("Real chest prefab's opening clip, if one is assigned. Leave empty to use the procedural fallback box+lid.")]
        public Animation ChestAnimation;
        [Tooltip("Only used by the procedural fallback visual (no ChestAnimation assigned).")]
        public Transform Lid;

        [Tooltip("Fires once every entry has been taken.")]
        public UnityEvent OnLooted = new UnityEvent();

        private Interactable _interactable;
        private bool _lidOpened;
        private List<LootEntry> _entries;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            if (_interactable == null)
            {
                _interactable = gameObject.AddComponent<Interactable>();
                _interactable.Prompt = $"Open {ChestName}";
                _interactable.InteractRange = 2.75f;
            }
            _interactable.OnInteract.AddListener(Open);
        }

        public void Open()
        {
            if (!_lidOpened)
            {
                _lidOpened = true;
                if (ChestAnimation != null)
                    ChestAnimation.Play();
                else
                    StartCoroutine(OpenLidRoutine());
            }

            if (_entries == null)
                _entries = BuildEntries();

            LootMenuUI.Show(ChestName, _entries, OnLootMenuClosed);
        }

        private List<LootEntry> BuildEntries()
        {
            var entries = new List<LootEntry>();
            if (Loot == null) return entries;

            foreach (LootDrop drop in Loot)
            {
                if (drop == null || drop.Item == null || drop.Quantity <= 0) continue;

                ItemData item = drop.Item;
                int quantity = drop.Quantity;
                string label = quantity > 1 ? $"{item.ItemName} x{quantity}" : item.ItemName;

                entries.Add(new LootEntry
                {
                    Name = label,
                    Description = item.Description,
                    OnTaken = () =>
                    {
                        if (PlayerSession.Instance != null)
                            PlayerSession.Instance.AddItem(item, quantity);
                    }
                });
            }
            return entries;
        }

        private void OnLootMenuClosed()
        {
            if (_entries == null || _entries.Count == 0) return;

            foreach (LootEntry entry in _entries)
                if (!entry.Taken) return; // something's still in there — stay usable

            if (_interactable != null)
                _interactable.enabled = false;
            OnLooted?.Invoke();
        }

        private IEnumerator OpenLidRoutine()
        {
            if (Lid == null) yield break;

            Quaternion start = Lid.localRotation;
            Quaternion end = Quaternion.Euler(-100f, 0f, 0f) * start;
            float duration = 0.4f;
            float t = 0f;

            while (t < duration)
            {
                t += Time.deltaTime;
                Lid.localRotation = Quaternion.Slerp(start, end, Mathf.Clamp01(t / duration));
                yield return null;
            }
            Lid.localRotation = end;
        }
    }
}
