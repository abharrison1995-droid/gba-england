using UnityEngine;
using UnityEngine.UI;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Wires a UI button to UIManager ability / attack actions (survives scene save).
    /// Ability buttons also show a radial cooldown sweep.
    /// </summary>
    [RequireComponent(typeof(Button))]
    public class HUDActionButton : MonoBehaviour
    {
        public enum ActionKind { Attack, Ability, Inventory, Interact }

        public ActionKind Kind = ActionKind.Ability;
        public int AbilityIndex;

        private Image _cooldownOverlay;

        private void Awake()
        {
            GetComponent<Button>().onClick.AddListener(Invoke);

            if (Kind == ActionKind.Ability)
                BuildCooldownOverlay();
        }

        private void BuildCooldownOverlay()
        {
            var go = new GameObject("CooldownOverlay", typeof(RectTransform));
            go.transform.SetParent(transform, false);

            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;

            _cooldownOverlay = go.AddComponent<Image>();
            _cooldownOverlay.color = new Color(0f, 0f, 0f, 0.6f);
            _cooldownOverlay.raycastTarget = false;
            _cooldownOverlay.type = Image.Type.Filled;
            _cooldownOverlay.fillMethod = Image.FillMethod.Radial360;
            _cooldownOverlay.fillOrigin = (int)Image.Origin360.Top;
            _cooldownOverlay.fillClockwise = false;
            _cooldownOverlay.fillAmount = 0f;
        }

        private void Update()
        {
            if (_cooldownOverlay == null) return;

            var combat = Combat.CombatController.Instance;
            if (combat == null)
            {
                _cooldownOverlay.fillAmount = 0f;
                return;
            }

            float remaining = combat.GetCooldownRemaining(AbilityIndex, out float total);
            _cooldownOverlay.fillAmount = (remaining > 0f && total > 0f)
                ? Mathf.Clamp01(remaining / total)
                : 0f;
        }

        private void Invoke()
        {
            if (UIManager.Instance == null) return;

            switch (Kind)
            {
                case ActionKind.Attack:
                    UIManager.Instance.OnAttackPressed();
                    break;
                case ActionKind.Inventory:
                    UIManager.Instance.OnInventoryPressed();
                    break;
                case ActionKind.Interact:
                    UIManager.Instance.OnInteractPressed();
                    break;
                default:
                    UIManager.Instance.OnActionButtonPressed(AbilityIndex);
                    break;
            }
        }
    }
}
