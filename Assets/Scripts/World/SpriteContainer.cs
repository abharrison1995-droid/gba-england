using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.UI;
using GBHEngland.Vibe;

namespace GBHEngland.World
{
    /// <summary>
    /// A billboarded searchable thing — a bin, a crate, a locker. Expects a
    /// <see cref="SpriteRenderer"/> and a <see cref="SpriteBillboard"/> on the same object, and
    /// optionally an <see cref="UnityEngine.Animator"/> with states named "Open" and "Close".
    ///
    /// Two modes, and the difference is the whole point of the component:
    ///
    /// * <see cref="ContainerMode.Fixed"/> — an authored container that empties permanently. Its
    ///   looted state is written into the save under an id built from the chunk and the object
    ///   name, so it stays empty across a reload.
    /// * <see cref="ContainerMode.Respawning"/> — restocks after <see cref="RespawnVisits"/> visits
    ///   to its chunk. Both modes are saved; the difference is whether the container ever comes
    ///   back.
    ///
    /// Contents come from a <see cref="LootBand"/>, the same table type the pickpocket minigame
    /// rolls, so a band is authored once and works in both.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class SpriteContainer : MonoBehaviour
    {
        /// <summary>
        /// ⚠ Serialized by integer index — APPEND ONLY (CLAUDE.md §3). Fixed is 0 so a container
        /// authored before this enum grew reads as the remembering kind, which is the safer
        /// default: the wrong answer there is a container that refuses to refill, not one that
        /// pays out forever.
        /// </summary>
        public enum ContainerMode
        {
            Fixed = 0,
            Respawning = 1,
        }

        [Tooltip("Shown as the loot menu's title and in the interact prompt.")]
        public string ContainerName = "Bin";

        public ContainerMode Mode = ContainerMode.Fixed;

        [Tooltip("Respawning only. Visits to this chunk before the container restocks — 3 means " +
                 "it is available again on the third return. Zero or less uses the default (3).")]
        public int RespawnVisits = EKVibe.DefaultContainerRespawnVisits;

        [Tooltip("What might be inside. Empty means the container opens onto nothing.")]
        public LootBand Band;

        [Tooltip("Optional. Needs states called Open and Close. Left empty, the container just " +
                 "opens its menu with no animation.")]
        public Animator Animator;

        private Interactable _interactable;
        private List<LootEntry> _entries;

        /// <summary>
        /// "<ChunkName>/<GameObjectName>", computed once and cached.
        ///
        /// ⚠ This is a save key. It is compared as a plain string and must never be trimmed,
        /// lower-cased or slugified — `Manor_Cellars_Data` has `ChunkName: "Manor Cellars"`, with a
        /// space, and normalising it would orphan every container looted in that chunk.
        /// Renaming a container GameObject, or its chunk, refills it for everyone.
        /// </summary>
        private string _containerId;

        private void Awake()
        {
            // Mirrors LootChest: an authoring tool may or may not have put an Interactable on, so
            // the component supplies its own rather than failing silently when one is missing.
            _interactable = GetComponent<Interactable>();
            if (_interactable == null)
            {
                _interactable = gameObject.AddComponent<Interactable>();
                _interactable.InteractRange = 2.75f;
            }

            // Outside the null check on purpose, matching WorldContainer. Both shipped prefabs
            // already carry an authored Interactable, so a Prompt set only in the branch above
            // never ran and the player read the prefab's baked-in placeholder instead of
            // ContainerName. InteractRange stays inside the branch — an authored Interactable
            // carries its own range, and 2.75 is only the fallback for one we just added.
            _interactable.Prompt = $"Open {ContainerName}";
            // Reusable: closing a half-emptied container has to leave it openable again. It is
            // disabled explicitly once everything in it has been taken.
            _interactable.Reusable = true;
            _interactable.OnInteract.AddListener(Open);

            if (Animator == null) Animator = GetComponentInChildren<Animator>();

            // Both modes need a save id now: Fixed remembers being emptied forever, Respawning
            // remembers how many visits it still owes. Neither can do that without one.
            SetUpFromSave();
        }

        private void OnDestroy()
        {
            ContainerIdRegistry.Release(_containerId, this);
        }

        /// <summary>
        /// Builds the save id and either restores the spent state or rolls contents.
        ///
        /// Never throws. A container living outside a chunk — dropped straight into c.unity, or
        /// alive while ChunkManager is still starting up — has nothing to build an id from, so it
        /// falls back to rolling contents and remembering nothing, and says so once. Throwing in
        /// Awake would take the rest of the chunk's Awakes with it.
        /// </summary>
        private void SetUpFromSave()
        {
            var manager = ChunkManager.Instance;
            // ContentChunkName, never CurrentChunkData: this runs in Awake, and on the portal path
            // the chunk is instantiated before CurrentChunkData is reassigned, so asking directly
            // would build the id from the chunk the player just left.
            string chunkName = manager != null ? manager.ContentChunkName : null;

            if (string.IsNullOrEmpty(chunkName))
            {
                Debug.LogWarning(
                    $"SpriteContainer '{name}': no current chunk to build a save id from, so it " +
                    "cannot remember being looted. Rolling contents and remembering nothing for " +
                    "this session.", this);
                RollContents();
                return;
            }

            _containerId = chunkName + "/" + gameObject.name;

            ContainerIdRegistry.Claim(_containerId, this, chunkName);

            bool spent = Mode == ContainerMode.Fixed
                ? PlayerSession.Instance != null && PlayerSession.Instance.IsContainerLooted(_containerId)
                : PlayerSession.Instance != null && PlayerSession.Instance.IsContainerOnCooldown(_containerId);

            if (spent)
            {
                // Emptied earlier — permanently for Fixed, or still sitting out its visits for
                // Respawning. Show it open, hand it no contents, and take it out of the interact
                // list. Never SetActive(false) — the object stays present and visible, it is
                // simply spent.
                _entries = new List<LootEntry>();
                if (Animator != null) Animator.Play("Open", 0, 1f);
                if (_interactable != null) _interactable.enabled = false;
                return;
            }

            RollContents();
        }

        private void RollContents()
        {
            _entries = new List<LootEntry>();
            if (Band == null) return;

            // The explicit-count overload rather than Roll(), so a perk can add rolls on top of the
            // band's own count.
            //
            // ⚠ This runs in Awake, not on open, so a perk taken mid-run only affects containers
            // instantiated after it was taken — the bins already standing in the current chunk keep
            // the contents they rolled on arrival. Known and accepted, not a bug.
            //
            // Deliberately NOT applied to PickpocketInteractable, which uses the same overload:
            // that is the crime layer, which the owner excluded from the v1 perk set, and wiring it
            // there would smuggle a crime perk in through the back door.
            int extraRolls = PlayerSession.Instance != null ? PlayerSession.Instance.ExtraLootRolls : 0;

            foreach (LootBandResult result in Band.Roll(Mathf.Max(1, Band.RollCount) + extraRolls))
            {
                if (result == null || result.Item == null || result.Quantity <= 0) continue;

                ItemData item = result.Item;
                int quantity = result.Quantity;
                string label = quantity > 1 ? $"{item.ItemName} x{quantity}" : item.ItemName;

                _entries.Add(new LootEntry
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

        public void Open()
        {
            if (Animator != null) Animator.Play("Open", 0, 0f);
            if (_entries == null) _entries = new List<LootEntry>();

            LootMenuUI.Show(ContainerName, _entries, OnClosed);
        }

        /// <summary>
        /// Shuts the lid, and retires the container once there is nothing left in it. The save is
        /// written at this point rather than on each TAKE, so a half-emptied container reopens with
        /// the rest still inside.
        /// </summary>
        private void OnClosed()
        {
            if (Animator != null) Animator.Play("Close", 0, 0f);

            if (_entries == null) return;

            // A container that rolled nothing has vacuously been emptied, and retires here. That
            // is deliberate and differs from LootChest, which stays usable when its list is empty:
            // a bin the player has already looked in should not keep offering to be looked in.
            for (int i = 0; i < _entries.Count; i++)
                if (!_entries[i].Taken) return;   // still something in there — stay usable

            if (_interactable != null) _interactable.enabled = false;

            if (string.IsNullOrEmpty(_containerId)) return;   // no id — nothing to remember it by

            if (Mode == ContainerMode.Fixed)
            {
                PlayerSession.Instance?.MarkContainerLooted(_containerId);
            }
            else
            {
                // A count of zero or less would mean "already free", which reads as the old
                // refills-every-visit behaviour. Fall back rather than store it: an asset authored
                // before RespawnVisits existed deserializes the field as 0, not as its initializer.
                int visits = RespawnVisits > 0 ? RespawnVisits : EKVibe.DefaultContainerRespawnVisits;
                PlayerSession.Instance?.AddContainerCooldown(_containerId, visits);
            }
        }
    }
}
