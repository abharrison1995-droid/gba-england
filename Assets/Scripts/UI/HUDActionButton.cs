using UnityEngine;
using UnityEngine.UI;

namespace GBHEngland.UI
{
    /// <summary>
    /// Wires a UI button to UIManager ability / attack actions (survives scene save).
    /// Ability buttons also show a radial cooldown sweep.
    /// </summary>
    [RequireComponent(typeof(Button))]
    public class HUDActionButton : MonoBehaviour
    {
        /// <summary>
        /// ⚠ Serialized by integer index — APPEND ONLY (CLAUDE.md §7). All four original values are
        /// live in c.unity's legacy action cluster (Attack=0 on AttackButton, Ability=1 on Skill0-2,
        /// Inventory=2 on MapBagShortcut, Interact=3 on InteractButton), so reordering would silently
        /// turn the attack button into something else. Crouch was appended as 4, Dodge as 5 —
        /// both are built at runtime by UIManager.BuildActionButtons and so are absent from the
        /// scene, but they are indices in the same sequence and the append rule covers them.
        /// Special was appended as 6, on the same terms.
        /// </summary>
        public enum ActionKind { Attack, Ability, Inventory, Interact, Crouch, Dodge, Special }

        public ActionKind Kind = ActionKind.Ability;
        public int AbilityIndex;

        private Image _cooldownOverlay;

        private void Awake()
        {
            GetComponent<Button>().onClick.AddListener(Invoke);

            // The two special-attack buttons get the same radial sweep as a spell button; they
            // are on a cooldown the player has to read just as much.
            if (Kind == ActionKind.Ability || Kind == ActionKind.Special)
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

            // ⚠ The source has to branch: GetCooldownRemaining indexes EquippedAbilities, so a
            // Special button reading it would sweep to whatever spell happened to be in slot 0 or 1.
            float remaining = Kind == ActionKind.Special
                ? combat.GetSpecialCooldownRemaining(AbilityIndex, out float total)
                : combat.GetCooldownRemaining(AbilityIndex, out total);
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
                case ActionKind.Crouch:
                    UIManager.Instance.OnCrouchPressed();
                    break;
                case ActionKind.Dodge:
                    UIManager.Instance.OnDodgePressed();
                    break;
                // ⚠ Must stay ABOVE default: Ability is the kind default serves, so a case
                // added below it would never be reached.
                case ActionKind.Special:
                    UIManager.Instance.OnSpecialAttackPressed(AbilityIndex);
                    break;
                default:
                    UIManager.Instance.OnActionButtonPressed(AbilityIndex);
                    break;
            }
        }
    }
}
