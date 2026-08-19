using UnityEngine;
using GBHEngland.Flow;
using GBHEngland.UI;

namespace GBHEngland.World
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
            bool isPlayer = other.CompareTag("Player") || other.GetComponentInParent<Combat.CombatController>() != null;
            bool isRiddenVehicle = MountController.IsPlayerRiding && MountController.Current != null &&
                                   MountController.Current.CurrentVehicle != null &&
                                   (other.transform.IsChildOf(MountController.Current.CurrentVehicle.transform) ||
                                    other.gameObject == MountController.Current.CurrentVehicle.gameObject);

            if (!isPlayer && !isRiddenVehicle)
                return;

            if (MountController.IsPlayerRiding)
            {
                UIManager.Instance?.ShowToast("Get out of the vehicle first.");
                return;
            }

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
