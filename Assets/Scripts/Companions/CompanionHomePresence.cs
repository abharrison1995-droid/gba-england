using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Companions
{
    /// <summary>
    /// The recruitable home presence: the idle companion standing in their home chunk. Attached to
    /// the object NpcFactory builds from the companion's PlacementPreset.
    ///
    /// It is an INTERACTION on the home Interactable and a visibility toggle over the contract:
    ///
    /// - OnEnable (which runs on every chunk instantiation) it shows itself when nobody is hired and
    ///   hides itself while THIS companion is the active follower. It toggles only its own GameObject
    ///   - never a chunk root or vehicle root (CLAUDE.md), so SetActive here is safe.
    /// - The hire interaction calls CompanionManager.BeginContract; insufficient funds are refused
    ///   atomically there and surfaced as a toast.
    ///
    /// Authoring: the World Palette stamps the companion preset (with CompanionDefinition assigned)
    /// into a chunk; the palette adds this component. The home anchor is the preset's QuestKey, and
    /// CompanionDefinition.HomeAnchorId must match it so CompanionManager can find the home for the
    /// eventual "returns home" beat.
    /// </summary>
    public class CompanionHomePresence : MonoBehaviour
    {
        [Tooltip("The companion definition this presence represents. Assigned by the palette / preset.")]
        public CompanionDefinition Definition;

        private Interactable _interactable;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            if (_interactable != null)
                _interactable.OnInteract.AddListener(OnHirePressed);

            // Match the interactable's prompt to the situation.
            RefreshPrompt();
        }

        private void OnEnable()
        {
            ApplyVisibility();
        }

        private void OnDestroy()
        {
            if (_interactable != null)
                _interactable.OnInteract.RemoveListener(OnHirePressed);
        }

        private void ApplyVisibility()
        {
            CompanionManager mgr = CompanionManager.Instance;
            bool hide = mgr != null && mgr.HasActiveCompanion
                && Definition != null && mgr.CurrentCompanionId == Definition.Id;
            if (gameObject.activeSelf == hide)
                gameObject.SetActive(!hide);
        }

        private void OnHirePressed()
        {
            if (Definition == null) return;

            CompanionManager mgr = CompanionManager.Instance;
            if (mgr == null) return;
            if (mgr.HasActiveCompanion)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast((mgr.ActiveDefinition != null ? mgr.ActiveDefinition.DisplayName : "Companion") + " is already with you.", 1.6f);
                return;
            }

            if (mgr.BeginContract(Definition.Id))
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast(Definition.DisplayName + " joins you.", 1.8f);
                // The follower now exists; hide ourselves.
                ApplyVisibility();
            }
            else
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Not enough money for " + Definition.DisplayName + ".", 1.8f);
            }
        }

        private void RefreshPrompt()
        {
            if (_interactable == null) return;
            string who = Definition != null && !string.IsNullOrEmpty(Definition.DisplayName)
                ? Definition.DisplayName
                : "Companion";
            _interactable.Prompt = "Hire " + who + " (" +
                (Definition != null ? Definition.PricePounds.ToString() : "?") + ")";
        }
    }
}
