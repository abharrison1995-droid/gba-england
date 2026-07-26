using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Handles the ASBO/Hoodie Stealth state. When crouching, movement is slowed but detection radius drops.
    /// </summary>
    public class StealthController : MonoBehaviour
    {
        public static StealthController Instance { get; private set; }

        public bool IsCrouched { get; private set; } = false;
        
        [Tooltip("Speed multiplier while sneaking.")]
        public float SneakSpeedMultiplier = 0.5f;

        private float _originalSpeed = 0f;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            var player = CombatController.Instance;
            if (player != null)
                _originalSpeed = player.MovementSpeed;
        }

        private void Update()
        {
            // Simple toggle for PC. On mobile, this would be wired to a UI button.
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
                    // Save current speed in case it was modified by a vehicle/buff, then halve it.
                    _originalSpeed = player.MovementSpeed;
                    player.MovementSpeed *= SneakSpeedMultiplier;
                    
                    // Visual feedback placeholder (darken sprite)
                    var spriteRenderer = player.GetComponentInChildren<SpriteRenderer>();
                    if (spriteRenderer != null) spriteRenderer.color = Color.gray;
                    
                    UIManager.Instance?.ShowToast("Sneaking...");
                }
                else
                {
                    player.MovementSpeed = _originalSpeed;
                    
                    var spriteRenderer = player.GetComponentInChildren<SpriteRenderer>();
                    if (spriteRenderer != null) spriteRenderer.color = Color.white;
                    
                    UIManager.Instance?.ShowToast("Out of stealth.");
                }
            }
        }
    }
}
