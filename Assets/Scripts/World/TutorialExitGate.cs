using UnityEngine;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Exit trigger inside Manor Cellars — drops player outside London's west gates
    /// (completes tutorial on first use; still returns on revisits).
    /// </summary>
    [RequireComponent(typeof(BoxCollider))]
    public class TutorialExitGate : MonoBehaviour
    {
        public string Prompt = "Exit to the manor gates";

        private float _readyAt;

        private void Reset()
        {
            var box = GetComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = new Vector3(4f, 3f, 2f);
        }

        private void OnEnable()
        {
            _readyAt = Time.unscaledTime + 0.75f;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (Time.unscaledTime < _readyAt) return;

            if (!other.CompareTag("Player") && other.GetComponentInParent<Combat.CombatController>() == null)
                return;

            // Barred until the tutorial stages are done (no sequence = free exit, e.g. revisits)
            var sequence = TutorialSequence.Instance;
            if (sequence != null && !sequence.ReadyToExit)
            {
                sequence.NudgeLockedGate();
                return;
            }

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You force the outer doors of the Manor Cellars...");

            if (GameFlowController.Instance != null)
                GameFlowController.Instance.OnTutorialExitToGates();
            else
                Debug.LogWarning("TutorialExitGate: no GameFlowController in scene.");
        }
    }
}
