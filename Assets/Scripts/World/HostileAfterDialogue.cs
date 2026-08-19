using System.Collections;
using UnityEngine;
using GBHEngland.Combat;
using GBHEngland.Dialogue;
using GBHEngland.UI;

namespace GBHEngland.World
{
    /// <summary>
    /// An NPC who is harmless until you talk to him, then turns on you when the conversation ends.
    ///
    /// This is the placed-content replacement for what <c>MagicTutorial.UnderHousedNPC</c> did in
    /// code. The important difference: that class <i>built</i> the enemy at the moment it turned
    /// hostile — adding the collider, Rigidbody, Health, NavMeshAgent and EnemyAI on the spot.
    /// Nothing is built here. The prefab carries a fully authored <see cref="EnemyAI"/> that is
    /// simply <b>disabled</b>, and all this does is switch it on.
    ///
    /// That distinction is what makes a quest Kill stage work at all:
    /// <see cref="Quests.QuestConditionWatcher"/> subscribes to <c>Health.OnDeath</c> on every
    /// keyed actor <i>at bind time</i>, and rebinds only on a quest, chunk or manager change —
    /// never when a component appears later. A Health added at hostility time would therefore
    /// never be subscribed, and the kill would not count.
    /// </summary>
    [RequireComponent(typeof(Interactable))]
    public class HostileAfterDialogue : MonoBehaviour
    {
        [Tooltip("Logged to the combat feed the moment this actor turns hostile. Leave blank for no line.")]
        [TextArea] public string TurnHostileLine;

        [Tooltip("If true, the Interactable is disabled once hostile, so the talk prompt stops " +
                 "appearing on someone actively trying to kill you.")]
        public bool DisableInteractionWhenHostile = true;

        [Tooltip("If set, this NPC will only turn hostile if this quest is currently active. " +
                 "If the quest has not been started or is complete, the NPC remains peaceful.")]
        public string RequiredQuestId;

        private bool _hostile;
        private bool _watching;

        private void Reset()
        {
            // Authoring convenience only — the real value is set in the Inspector.
            TurnHostileLine = "";
        }

        /// <summary>
        /// Hook this to the <see cref="Interactable"/>'s OnInteract in the prefab. Safe to call
        /// repeatedly: it does nothing once hostile, and the watch coroutine is single-flight.
        /// </summary>
        public void OnTalked()
        {
            if (_hostile || _watching) return;
            _watching = true;
            StartCoroutine(WaitForDialogueToClose());
        }

        /// <summary>
        /// Waits a frame so the panel has actually opened before testing, then polls until it
        /// closes. Same shape as the sequence this replaces — the dialogue system exposes no
        /// "conversation ended" event to subscribe to.
        /// </summary>
        private IEnumerator WaitForDialogueToClose()
        {
            yield return null;
            while (DialogueManager.IsDialogueOpen) yield return null;
            _watching = false;
            TurnHostile();
        }

        /// <summary>
        /// Enables the authored AI. Everything it needs is already on the prefab, so this cannot
        /// half-build an enemy the way the old runtime path could.
        /// </summary>
        public void TurnHostile()
        {
            if (_hostile) return;

            // If a quest is required, only turn hostile while that quest is actively in progress
            if (!string.IsNullOrEmpty(RequiredQuestId))
            {
                if (Quests.QuestManager.Instance == null || !Quests.QuestManager.Instance.IsActive(RequiredQuestId))
                    return;
            }

            _hostile = true;

            if (DisableInteractionWhenHostile)
            {
                var interactable = GetComponent<Interactable>();
                if (interactable != null) interactable.enabled = false;
            }

            var ai = GetComponent<EnemyAI>();
            if (ai != null)
            {
                ai.enabled = true;
            }
            else
            {
                // Worth shouting about: without an EnemyAI this actor is permanently harmless, and
                // any quest waiting on his death waits forever.
                Debug.LogWarning($"HostileAfterDialogue on '{name}' found no EnemyAI to enable — " +
                                 "this actor will never fight back.", this);
            }

            if (!string.IsNullOrEmpty(TurnHostileLine) && UIManager.Instance != null)
                UIManager.Instance.LogCombat(TurnHostileLine);
        }
    }
}
