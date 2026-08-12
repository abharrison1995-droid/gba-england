using System.Collections.Generic;
using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
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
    /// * <see cref="ContainerMode.Respawning"/> — rolls fresh contents every time its chunk is
    ///   built, and remembers nothing. Chunks are destroyed and rebuilt on every visit, so this is
    ///   simply the mode that opts out of the save.
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

        /// <summary>Every id an active Fixed container has claimed, so collisions can be reported.</summary>
        private static readonly Dictionary<string, SpriteContainer> _claimedIds =
            new Dictionary<string, SpriteContainer>();

        private void Awake()
        {
            // Mirrors LootChest: an authoring tool may or may not have put an Interactable on, so
            // the component supplies its own rather than failing silently when one is missing.
            _interactable = GetComponent<Interactable>();
            if (_interactable == null)
            {
                _interactable = gameObject.AddComponent<Interactable>();
                _interactable.Prompt = $"Open {ContainerName}";
                _interactable.InteractRange = 2.75f;
            }
            // Reusable: closing a half-emptied container has to leave it openable again. It is
            // disabled explicitly once everything in it has been taken.
            _interactable.Reusable = true;
            _interactable.OnInteract.AddListener(Open);

            if (Animator == null) Animator = GetComponentInChildren<Animator>();

            if (Mode == ContainerMode.Fixed) SetUpFixed();
            else RollContents();
        }

        private void OnDestroy()
        {
            if (!string.IsNullOrEmpty(_containerId) &&
                _claimedIds.TryGetValue(_containerId, out var owner) && owner == this)
            {
                _claimedIds.Remove(_containerId);
            }
        }

        /// <summary>
        /// Builds the save id and either restores the looted state or rolls contents.
        ///
        /// Never throws. A container living outside a chunk — dropped straight into c.unity, or
        /// alive while ChunkManager is still starting up — has nothing to build an id from, so it
        /// falls back to behaving as Respawning and says so once. Throwing in Awake would take the
        /// rest of the chunk's Awakes with it.
        /// </summary>
        private void SetUpFixed()
        {
            var manager = ChunkManager.Instance;
            string chunkName = manager != null && manager.CurrentChunkData != null
                ? manager.CurrentChunkData.ChunkName
                : null;

            if (string.IsNullOrEmpty(chunkName))
            {
                Debug.LogWarning(
                    $"SpriteContainer '{name}': no current chunk to build a save id from, so it " +
                    "cannot remember being looted. Behaving as Respawning for this session.", this);
                RollContents();
                return;
            }

            _containerId = chunkName + "/" + gameObject.name;

            if (_claimedIds.TryGetValue(_containerId, out var existing) && existing != null)
            {
                Debug.LogWarning(
                    $"SpriteContainer: two containers in '{chunkName}' are both called " +
                    $"'{gameObject.name}', so they share the save id '{_containerId}' and looting " +
                    "either empties both. Rename one in the Hierarchy.", this);
            }
            else
            {
                _claimedIds[_containerId] = this;
            }

            if (PlayerSession.Instance != null && PlayerSession.Instance.IsContainerLooted(_containerId))
            {
                // Already emptied in an earlier session. Show it open, hand it no contents, and
                // take it out of the interact list. Never SetActive(false) — the object stays
                // present and visible, it is simply spent.
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
        /// Shuts the lid, and retires the container once there is nothing left in it. A Fixed
        /// container also records that in the save at this point rather than on each TAKE, so a
        /// half-emptied one reopens with the rest still inside.
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

            if (Mode == ContainerMode.Fixed && !string.IsNullOrEmpty(_containerId))
                PlayerSession.Instance?.MarkContainerLooted(_containerId);
        }
    }
}
