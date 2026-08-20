using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.UI;
using GBHEngland.Vibe;

namespace GBHEngland.World
{
    /// <summary>
    /// A searchable point on a 3D world object — a berry bush, a broken vending machine, a heap of
    /// bus wreckage. Lives on a CHILD of the model, positioned where the player should interact,
    /// so one model can carry a container without the container owning the model.
    ///
    /// The 2D counterpart is <see cref="SpriteContainer"/>, which expects a SpriteRenderer and a
    /// billboard on its own object. The two share one save-key space and one set of modes; this one
    /// adds a fixed-loot source, a full/empty visual swap, and an authored save id.
    ///
    /// Two modes:
    ///
    /// * <see cref="ContainerMode.Fixed"/> — empties permanently, remembered in the save forever.
    /// * <see cref="ContainerMode.Respawning"/> — restocks after <see cref="RespawnVisits"/> visits
    ///   to its chunk. A count of 1 is the "refills every visit" behaviour.
    ///
    /// Loot comes from EITHER a <see cref="LootBand"/> (weighted, varied quantity) or a fixed
    /// <see cref="FixedLoot"/> list (exact items, exact counts). Quest containers want the fixed
    /// list — a band that can roll nothing cannot promise the player the thing the quest needs.
    /// </summary>
    public class WorldContainer : MonoBehaviour
    {
        /// <summary>
        /// ⚠ Serialized by integer index — APPEND ONLY (CLAUDE.md §3). Frozen by the first authored
        /// container. Fixed is 0 for the same reason as <see cref="SpriteContainer.ContainerMode"/>:
        /// the wrong answer there is a container that refuses to refill, not one that pays forever.
        /// </summary>
        public enum ContainerMode
        {
            Fixed = 0,
            Respawning = 1,
        }

        /// <summary>
        /// ⚠ Serialized by integer index — APPEND ONLY. Nothing reads this yet; see the trap fields.
        /// </summary>
        public enum TrapType
        {
            None = 0,
            Damage = 1,
            WantedSpike = 2,
        }

        [Header("Identity")]
        [Tooltip("Shown as the loot menu's title.")]
        public string ContainerName = "Wreckage";

        [Tooltip("What the USE prompt says. Blank falls back to \"Search <name>\".")]
        public string InteractPrompt = "";

        /// <summary>
        /// The container's half of its save key, written by the Container Placement tool.
        ///
        /// ⚠ This exists because the component lives on a CHILD object. Ten containers each called
        /// "Container" under ten different pillars are ten perfectly legal GameObjects that would
        /// share one save key — loot one and all ten empty, silently. Blank falls back to the
        /// GameObject name, which is the SpriteContainer behaviour and is only safe when the names
        /// happen to be unique.
        ///
        /// ⚠ Part of a save key. Compared verbatim — never trimmed, lower-cased or slugified.
        /// Changing it after a container has been looted refills it for everyone.
        /// </summary>
        [Tooltip("Unique within the chunk. Part of the save key — changing it refills the " +
                 "container for every existing save. Blank falls back to the GameObject name.")]
        public string SaveId = "";

        [Header("Behaviour")]
        public ContainerMode Mode = ContainerMode.Fixed;

        [Tooltip("Respawning only. Visits to this chunk before it restocks — 3 means it is " +
                 "available again on the third return. 1 refills every visit. Zero or less uses " +
                 "the default (3).")]
        public int RespawnVisits = EKVibe.DefaultContainerRespawnVisits;

        [Tooltip("How close the player has to be, in metres.")]
        public float InteractRange = EKVibe.DefaultContainerInteractRange;

        [Header("Loot — use one or the other, not both")]
        [Tooltip("Weighted random table. Wins if a fixed list is also set.")]
        public LootBand Band;

        [Tooltip("Exact items in exact quantities. Use this for anything a quest depends on.")]
        public List<LootDrop> FixedLoot = new List<LootDrop>();

        [Header("Visuals")]
        [Tooltip("Shown while there is something left. Hidden once emptied. Optional.")]
        public GameObject FullVisual;

        [Tooltip("Shown once emptied — the picked-clean version. Optional.")]
        public GameObject EmptyVisual;

        [Header("NOT WIRED — declared for later, these do nothing yet")]
        [Tooltip("NOT WIRED — no trap fires. Declared so the enum indices are settled early.")]
        public TrapType Trap = TrapType.None;

        [Tooltip("NOT WIRED — chance the trap fires, 0 to 1.")]
        [Range(0f, 1f)] public float TrapChance = 0f;

        [Tooltip("NOT WIRED — damage a Damage trap would deal.")]
        public int TrapDamage = 0;

        [Tooltip("NOT WIRED — knives a WantedSpike trap would add.")]
        public int TrapKnives = 0;

        [Tooltip("NOT WIRED — the lockpick minigame does not exist yet. Ticking this does nothing.")]
        public bool Locked = false;

        [Tooltip("NOT WIRED — how hard the lock would be.")]
        public int LockDifficulty = 0;

        [Tooltip("NOT WIRED — quest gating is not evaluated.")]
        public QuestGateType QuestGate = QuestGateType.None;

        [Tooltip("NOT WIRED — the quest id the gate would test.")]
        public string QuestKey = "";

        [Tooltip("NOT WIRED — the stage index ActiveAtStage would test.")]
        public int QuestStage = 0;

        private Interactable _interactable;
        private List<LootEntry> _entries;

        /// <summary>
        /// "&lt;ChunkName&gt;/&lt;SaveId&gt;", computed once in Awake and cached. Empty when the
        /// container could not work out which chunk it is in, which makes it forget everything.
        /// </summary>
        private string _containerId;

        /// <summary>
        /// Every id an active container has claimed, so collisions can be reported.
        ///
        /// ⚠ Must be unregistered in OnDestroy. Chunks are destroyed and rebuilt on every visit, so
        /// without that every re-entry would warn about the previous instance of itself.
        /// </summary>
        private static readonly Dictionary<string, WorldContainer> _claimedIds =
            new Dictionary<string, WorldContainer>();

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            if (_interactable == null) _interactable = gameObject.AddComponent<Interactable>();

            _interactable.Prompt = !string.IsNullOrEmpty(InteractPrompt)
                ? InteractPrompt
                : $"Search {ContainerName}";
            _interactable.InteractRange = InteractRange > 0f
                ? InteractRange
                : EKVibe.DefaultContainerInteractRange;

            // Reusable: closing a half-emptied container has to leave it openable again. It is
            // disabled explicitly once everything in it has been taken.
            _interactable.Reusable = true;

            // AddListener, not UnityEventTools: this binding is rebuilt every time the object is
            // instantiated and must NOT be persisted into the prefab, or a placed container would
            // open its menu twice per press.
            _interactable.OnInteract.AddListener(Open);

            ValidateVisuals();
            SetUpFromSave();
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
        /// Refuses a visual reference that would take something else down with it.
        ///
        /// ⚠ SetActive(false) on this object disables the container and its Interactable, so it can
        /// never be re-enabled by anything here. On an ancestor it does the same and takes the model
        /// with it. On a chunk root it is the §3 four-system break — every EnemyAI blinded, a
        /// NavMesh leaked, two tutorial singletons stranded. Warn and drop the reference rather than
        /// obey it.
        /// </summary>
        private void ValidateVisuals()
        {
            FullVisual = RejectUnsafeVisual(FullVisual, nameof(FullVisual));
            EmptyVisual = RejectUnsafeVisual(EmptyVisual, nameof(EmptyVisual));
        }

        private GameObject RejectUnsafeVisual(GameObject candidate, string fieldName)
        {
            if (candidate == null) return null;

            if (candidate == gameObject || transform.IsChildOf(candidate.transform))
            {
                Debug.LogWarning(
                    $"WorldContainer '{name}': {fieldName} points at this object or one of its " +
                    "ancestors. Hiding it would disable the container itself, so the reference is " +
                    "ignored. Point it at a child of the model instead.", this);
                return null;
            }

            return candidate;
        }

        /// <summary>
        /// Builds the save id and either restores the spent state or fills the container.
        ///
        /// Never throws. A container with no chunk to key against — dropped straight into c.unity,
        /// or alive while ChunkManager is still starting up — fills itself and remembers nothing,
        /// and says so once. Throwing in Awake would take the rest of the chunk's Awakes with it.
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
                    $"WorldContainer '{name}': no current chunk to build a save id from, so it " +
                    "cannot remember being looted. Filling it and remembering nothing for this " +
                    "session.", this);
                Fill();
                ApplyVisualState(spent: false);
                return;
            }

            string key = !string.IsNullOrEmpty(SaveId) ? SaveId : gameObject.name;
            _containerId = chunkName + "/" + key;

            if (_claimedIds.TryGetValue(_containerId, out var existing) && existing != null)
            {
                Debug.LogWarning(
                    $"WorldContainer: two containers in '{chunkName}' both key on '{key}', so they " +
                    $"share the save id '{_containerId}' and looting either empties both. Give one " +
                    "a different Save Id — Tools > Place > Container Placement > Validate All " +
                    "Containers finds these.", this);
            }
            else
            {
                _claimedIds[_containerId] = this;
            }

            bool spent = Mode == ContainerMode.Fixed
                ? PlayerSession.Instance != null && PlayerSession.Instance.IsContainerLooted(_containerId)
                : PlayerSession.Instance != null && PlayerSession.Instance.IsContainerOnCooldown(_containerId);

            if (spent)
            {
                // Emptied earlier — permanently for Fixed, or still sitting out its visits for
                // Respawning. Hand it no contents and take it out of the interact list. Never
                // SetActive(false) on the container: it stays present, it is simply spent.
                _entries = new List<LootEntry>();
                if (_interactable != null) _interactable.enabled = false;
                ApplyVisualState(spent: true);
                return;
            }

            Fill();
            ApplyVisualState(spent: false);
        }

        /// <summary>
        /// Builds the contents. A band wins over a fixed list when both are set, and says so —
        /// silently preferring one would make a quest container that also has a band pay out
        /// something other than what the quest promised.
        /// </summary>
        private void Fill()
        {
            _entries = new List<LootEntry>();

            bool hasFixed = FixedLoot != null && FixedLoot.Count > 0;

            if (Band != null && hasFixed)
            {
                Debug.LogWarning(
                    $"WorldContainer '{name}': both a Loot Band and a Fixed Loot list are set. " +
                    "The band wins and the fixed list is ignored — clear one of them.", this);
            }

            if (Band != null) FillFromBand();
            else if (hasFixed) FillFromFixed();
        }

        private void FillFromBand()
        {
            // The explicit-count overload rather than Roll(), so a perk can add rolls on top of the
            // band's own count.
            //
            // ⚠ This runs in Awake, not on open, so a perk taken mid-run only affects containers
            // instantiated after it was taken — the ones already standing in the current chunk keep
            // what they rolled on arrival. Same known limitation as SpriteContainer.
            int extraRolls = PlayerSession.Instance != null ? PlayerSession.Instance.ExtraLootRolls : 0;

            foreach (LootBandResult result in Band.Roll(Mathf.Max(1, Band.RollCount) + extraRolls))
            {
                if (result == null || result.Item == null || result.Quantity <= 0) continue;
                AddEntry(result.Item, result.Quantity);
            }
        }

        private void FillFromFixed()
        {
            foreach (LootDrop drop in FixedLoot)
            {
                if (drop == null || drop.Item == null || drop.Quantity <= 0) continue;
                AddEntry(drop.Item, drop.Quantity);
            }
        }

        private void AddEntry(ItemData item, int quantity)
        {
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

        /// <summary>
        /// Swaps between the full and picked-clean models. Drives BOTH references every time, so a
        /// prefab authored with the empty version left active does not draw both at once. Either
        /// reference being null skips the swap entirely rather than half-applying it.
        /// </summary>
        private void ApplyVisualState(bool spent)
        {
            if (FullVisual != null) FullVisual.SetActive(!spent);
            if (EmptyVisual != null) EmptyVisual.SetActive(spent);
        }

        public void Open()
        {
            if (_entries == null) _entries = new List<LootEntry>();
            LootMenuUI.Show(ContainerName, _entries, OnClosed);
        }

        /// <summary>
        /// Retires the container once there is nothing left in it, and records that. The save is
        /// written here rather than on each TAKE, so a half-emptied container reopens with the rest
        /// still inside.
        /// </summary>
        private void OnClosed()
        {
            if (_entries == null) return;

            // A container that rolled nothing has vacuously been emptied, and retires here. That is
            // deliberate and differs from LootChest, which stays usable when its list is empty:
            // something the player has already searched should not keep offering to be searched.
            for (int i = 0; i < _entries.Count; i++)
                if (!_entries[i].Taken) return;   // still something in there — stay usable

            if (_interactable != null) _interactable.enabled = false;
            ApplyVisualState(spent: true);

            if (string.IsNullOrEmpty(_containerId)) return;   // no id — nothing to remember it by

            if (Mode == ContainerMode.Fixed)
            {
                PlayerSession.Instance?.MarkContainerLooted(_containerId);
            }
            else
            {
                int visits = RespawnVisits > 0 ? RespawnVisits : EKVibe.DefaultContainerRespawnVisits;
                PlayerSession.Instance?.AddContainerCooldown(_containerId, visits);
            }
        }
    }
}
