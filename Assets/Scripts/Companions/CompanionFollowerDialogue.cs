using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Dialogue;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Companions
{
    /// <summary>
    /// The conversation a FOLLOWING companion offers when the player talks to it: combat commands
    /// ("Back me" / "Chill a minute"), a confirmed dismiss, and a "Nevermind" exit. Attached by
    /// CompanionManager.SpawnFollower to the runtime follower, wired to the preset's
    /// <see cref="PlacementPreset.FollowerConversation"/>.
    ///
    /// Separate from <see cref="CompanionHomePresence"/> on purpose: that one is the recruit
    /// interaction on the idle figure in the home chunk, this one rides the live follower. The
    /// commands themselves are <see cref="DialogueChoice.CompanionCommand"/> values, applied by
    /// DialogueManager after the chat closes, so nothing here touches contract state directly.
    /// </summary>
    [RequireComponent(typeof(Interactable))]
    public class CompanionFollowerDialogue : MonoBehaviour
    {
        [Tooltip("Opened when the player talks to the follower. Its choices carry CompanionCommand " +
                 "values (fight beside me / stop fighting / dismiss) plus a plain Nevermind exit.")]
        public DialogueData Conversation;

        private Interactable _interactable;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            if (_interactable != null)
                _interactable.OnInteract.AddListener(OnInteractPressed);
        }

        private void OnDestroy()
        {
            if (_interactable != null)
                _interactable.OnInteract.RemoveListener(OnInteractPressed);
        }

        private void OnInteractPressed()
        {
            // A knocked-out follower cannot talk. Health.Die leaves the KO pose in place while
            // CompanionManager finishes the teardown, so the Interactable is still live for a beat
            // and must refuse rather than open a chat over a corpse.
            // Health is added AFTER this component in SpawnFollower, so it is resolved here at
            // interact time rather than cached in Awake (where it would be null).
            Health health = GetComponent<Health>();
            if (health != null && health.IsDead) return;
            if (Conversation == null)
            {
                Debug.LogWarning($"CompanionFollowerDialogue on {name}: no Conversation assigned.");
                return;
            }

            CharacterData playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
            DialogueManager.Ensure().StartDialogue(Conversation, playerData);
        }
    }
}