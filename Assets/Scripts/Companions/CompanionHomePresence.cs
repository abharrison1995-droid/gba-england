using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Dialogue;
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
    /// - Pressing Interact opens <see cref="Conversation"/>; the hire itself is a dialogue choice
    ///   carrying <c>HireCompanionId</c> (DialogueManager runs it through CompanionManager, so the
    ///   charge and its refusal live in exactly one place). With no Conversation assigned the
    ///   presence falls back to hiring directly, the way it did before the dialogue existed.
    /// - It shows itself when nobody is hired and hides itself while THIS companion is the active
    ///   follower, re-evaluated on enable and on CompanionManager.ContractChanged, so hiring from
    ///   the dialogue hides the figure the moment the chat closes and a knockout/dismissal brings
    ///   it back home. It toggles only its own GameObject - never a chunk root or vehicle root
    ///   (CLAUDE.md), so SetActive here is safe.
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

        [Tooltip("Opened when the player interacts. The hire is a choice inside it carrying " +
                 "HireCompanionId for this companion. Left empty, interacting hires directly " +
                 "(the pre-dialogue behaviour).")]
        public DialogueData Conversation;

        private Interactable _interactable;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            if (_interactable != null)
                _interactable.OnInteract.AddListener(OnInteractPressed);

            // Match the interactable's prompt to the situation.
            RefreshPrompt();
        }

        private void Start()
        {
            ApplyDefinitionSize();
        }

        /// <summary>Sizes the home presence from the definition so it matches the runtime follower.</summary>
        private void ApplyDefinitionSize()
        {
            if (Definition == null) return;
            var visual = GetComponent<WorldActorVisual>();
            if (visual == null) return;
            visual.Height = Definition.Height;
            visual.Width = Definition.Width;
            visual.IndependentWidth = Definition.Width > 0f;
            visual.ApplyVisual();
        }

        private void OnEnable()
        {
            // Deliberately NOT mirrored by an OnDisable unsubscribe: hiding IS SetActive(false) on
            // this object, and the hidden figure must still hear ContractChanged so it can come
            // back when the contract ends (a knockout in the home chunk must not leave Alex
            // invisible until the chunk reloads). OnDestroy is the only unsubscribe, and the
            // remove-then-add keeps a re-enable from double-subscribing.
            if (CompanionManager.Instance != null)
            {
                CompanionManager.Instance.ContractChanged -= ApplyVisibility;
                CompanionManager.Instance.ContractChanged += ApplyVisibility;
            }
            ApplyVisibility();
        }

        private void OnDestroy()
        {
            if (CompanionManager.Instance != null)
                CompanionManager.Instance.ContractChanged -= ApplyVisibility;
            if (_interactable != null)
                _interactable.OnInteract.RemoveListener(OnInteractPressed);
        }


        private void ApplyVisibility()
        {
            CompanionManager mgr = CompanionManager.Instance;
            bool hide = mgr != null && mgr.HasActiveCompanion
                && Definition != null && mgr.CurrentCompanionId == Definition.Id;
            if (gameObject.activeSelf == hide)
                gameObject.SetActive(!hide);
        }

        private void OnInteractPressed()
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

            // The conversation owns the hire when there is one: the recruit choice inside it
            // carries HireCompanionId, and DialogueManager runs the contract from there.
            if (Conversation != null)
            {
                CharacterData playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
                DialogueManager.Ensure().StartDialogue(Conversation, playerData);
                return;
            }

            // No conversation authored: hire on the button, as before.
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
            _interactable.Prompt = Conversation != null
                ? "Talk to " + who
                : "Hire " + who + " (" + (Definition != null ? Definition.PricePounds.ToString() : "?") + ")";
        }
    }
}
