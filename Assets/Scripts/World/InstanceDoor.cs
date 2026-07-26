using UnityEngine;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Overworld door that loads an instance chunk (e.g. Manor Cellars from London).
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class InstanceDoor : MonoBehaviour
    {
        public enum Destination
        {
            ManorCellars
        }

        public Destination Target = Destination.ManorCellars;
        public string Prompt = "Enter Manor Cellars";
        public bool RequireTutorialComplete = true;

        private void Reset()
        {
            var col = GetComponent<Collider>();
            col.isTrigger = true;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (!other.CompareTag("Player") && other.GetComponentInParent<Combat.CombatController>() == null)
                return;

            if (RequireTutorialComplete
                && (PlayerSession.Instance == null || !PlayerSession.Instance.TutorialComplete))
            {
                return;
            }

            if (GameFlowController.Instance == null)
            {
                Debug.LogWarning("InstanceDoor: no GameFlowController.");
                return;
            }

            if (!GameFlowController.Instance.CanUseInstanceDoors)
                return;

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat(Prompt + "...");

            switch (Target)
            {
                case Destination.ManorCellars:
                    GameFlowController.Instance.EnterManorCellarsOptional();
                    break;
            }
        }
    }
}
