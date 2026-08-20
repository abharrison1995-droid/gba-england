using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Dialogue;
using GBHEngland.Quests;
using GBHEngland.Combat;

namespace GBHEngland.World
{
    /// <summary>
    /// Starts a conversation on its own the moment the player walks into a trigger collider —
    /// no USE press, unlike every other conversation in the project (see
    /// <see cref="NPCDialogueInteractable"/>). Written for Mayor Zhao's ambush at the East York
    /// gate (quests/rush_hour.quest), where the writing is explicit that he accosts the player
    /// rather than being sought out.
    ///
    /// ⚠ THE RE-FIRE PROBLEM IS THE HARD PART, NOT THE FIRING. A chunk is destroyed and rebuilt
    /// on every entry (ChunkManager.TravelRoutine), so a plain "already seen this" bool on this
    /// component would reset every time and re-ambush the player forever. Gating on quest state
    /// instead — active AND on the exact stage this trigger is meant for — needs no new save
    /// field: once the quest's own progression moves it past <see cref="RequiredStage"/>, this
    /// trigger disarms itself permanently, including across saves, because quest state is
    /// already serialized.
    /// </summary>
    [RequireComponent(typeof(BoxCollider))]
    public class ProximityDialogueTrigger : MonoBehaviour
    {
        [Tooltip("Only fires while this quest id is active (started, not yet complete).")]
        public string QuestId;

        [Tooltip("Only fires while the quest is sitting on exactly this stage index. Once the " +
                 "quest advances past it, this trigger is disarmed for good — no separate flag.")]
        public int RequiredStage;

        [Tooltip("The conversation to open. Same direct-reference resolution as " +
                 "NPCDialogueInteractable.Conversation.")]
        public DialogueData Conversation;

        // Same grace-window idiom as TutorialExitGate: without it, a chunk that rebuilds with the
        // player already standing inside this collider would fire on the very first frame, before
        // the arrival has settled.
        private float _readyAt;

        private void Reset()
        {
            var box = GetComponent<BoxCollider>();
            box.isTrigger = true;
        }

        private void OnEnable()
        {
            _readyAt = Time.unscaledTime + 0.75f;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (Time.unscaledTime < _readyAt) return;

            bool isPlayer = other.CompareTag("Player") || other.GetComponentInParent<CombatController>() != null;
            if (!isPlayer) return;

            // Mirrors DungeonPortal/ChunkEdge/InstanceDoor: a mounted player is a separate root
            // that would be left behind, and refusing is the player's cue to dismount rather than
            // this trying to handle it for them.
            if (MountController.IsPlayerRiding) return;

            // Mirrors PlayerInteractor.Update's own guard: while any dialogue, merchant window or
            // other pause-stack owner is open, nothing here should interrupt or stack on top of it.
            if (GBHEngland.Systems.PauseManager.IsPaused) return;

            if (string.IsNullOrEmpty(QuestId) || QuestManager.Instance == null) return;

            QuestProgress progress = QuestManager.Instance.Find(QuestId);
            if (progress == null || !progress.IsActive || progress.IsComplete) return;
            if (progress.StageIndex != RequiredStage) return;

            if (Conversation == null)
            {
                Debug.LogWarning($"ProximityDialogueTrigger on {name}: no Conversation assigned.");
                return;
            }

            CharacterData playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
            DialogueManager.Ensure().StartDialogue(Conversation, playerData);
        }
    }
}
