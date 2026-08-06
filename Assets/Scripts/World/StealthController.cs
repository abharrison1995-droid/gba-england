using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Handles the ASBO/Hoodie Stealth state. Crouching halves movement speed and is the gate on
    /// pickpocketing. Nothing else currently reads IsCrouched — the snitch mechanic that used to
    /// have its detection radius halved by crouching has been removed.
    /// </summary>
    public class StealthController : MonoBehaviour
    {
        public static StealthController Instance { get; private set; }

        public bool IsCrouched { get; private set; } = false;
        
        [Tooltip("Speed multiplier while sneaking.")]
        public float SneakSpeedMultiplier = 0.5f;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Update()
        {
            // Kept alongside the HUD's CRO button (UIManager.OnCrouchPressed) rather than replaced
            // by it — the keyboard toggle is how this gets tested in the editor.
            if (Input.GetKeyDown(KeyCode.C))
            {
                ToggleStealth();
            }
        }

        public void ToggleStealth()
        {
            IsCrouched = !IsCrouched;
            var player = CombatController.Instance;
            
            if (player != null)
            {
                if (IsCrouched)
                {
                    // Registered by source, so mounting a vehicle while crouched composes
                    // instead of overwriting either system's idea of base speed.
                    player.SetSpeedMultiplier(this, SneakSpeedMultiplier);

                    // Visual feedback placeholder (darken sprite)
                    var spriteRenderer = FindPlayerRenderer(player);
                    if (spriteRenderer != null) spriteRenderer.color = Color.gray;

                    UIManager.Instance?.ShowToast("Sneaking...");
                }
                else
                {
                    player.ClearSpeedMultiplier(this);

                    var spriteRenderer = FindPlayerRenderer(player);
                    if (spriteRenderer != null) spriteRenderer.color = Color.white;

                    UIManager.Instance?.ShowToast("Out of stealth.");
                }
            }

            // Outside the null-player branch: the button must still repaint even if the toggle
            // could not be applied, or it would show a crouch state the player is not in.
            UIManager.Instance?.RefreshCrouchButton();
        }

        /// <summary>
        /// The actor's own renderer. GetComponentInChildren would do until the player carries a
        /// second SpriteRenderer — the layered vehicle sprite while riding — after which it can
        /// hand back the moped and leave the player untinted.
        /// </summary>
        private static SpriteRenderer FindPlayerRenderer(CombatController player)
        {
            var visual = player.GetComponent<WorldActorVisual>();
            if (visual != null) return visual.ActorRenderer;
            return player.GetComponentInChildren<SpriteRenderer>();
        }
    }
}
