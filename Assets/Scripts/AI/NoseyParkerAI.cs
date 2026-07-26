using UnityEngine;
using System.Collections;
using ExiledAlvaston.Systems;
using ExiledAlvaston.Combat;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.AI
{
    public class NoseyParkerAI : MonoBehaviour
    {
        [Header("Detection Settings")]
        public float DetectionRadius = 8f;
        public float ReportTime = 4f;
        
        private bool _isReporting = false;
        private Transform _playerTransform;
        private float _reportTimer = 0f;

        private void Start()
        {
            var player = CombatController.Instance;
            if (player != null)
                _playerTransform = player.transform;
        }

        private void Update()
        {
            if (_playerTransform == null) return;
            if (_isReporting)
            {
                _reportTimer -= Time.deltaTime;
                
                // Show reporting progress above head using a UI floating text or similar (placeholder implementation)
                if (Random.value < 0.02f) 
                {
                    UIManager.Instance?.ShowToast("Hello, police? There's a bloke doing weird sparks here!", 0.5f);
                }

                if (_reportTimer <= 0f)
                {
                    FinishReporting();
                }

                // If player runs far away, maybe cancel? For now, they commit to the call.
                return;
            }

            // Reduce detection radius if player is sneaking (ASBO Stealth)
            float currentDetectionRadius = DetectionRadius;
            if (ExiledAlvaston.World.StealthController.Instance != null && ExiledAlvaston.World.StealthController.Instance.IsCrouched)
            {
                currentDetectionRadius *= 0.5f;
            }

            // Check if player is near and their concealment is low (they just cast magic)
            if (Vector3.Distance(transform.position, _playerTransform.position) < currentDetectionRadius)
            {
                if (WantedManager.Instance != null && WantedManager.Instance.CurrentConcealment < WantedManager.Instance.MaxConcealment)
                {
                    // They saw something suspicious!
                    StartReporting();
                }
            }
        }

        private void StartReporting()
        {
            _isReporting = true;
            _reportTimer = ReportTime;
            
            // Visual feedback: phone comes out.
            UIManager.Instance?.ShowToast("Nosey Parker spotted you! Stop them dialing 999!", 2f);
            
            // Could set animator bool here: _animator.SetBool("IsPhoning", true);
        }

        private void FinishReporting()
        {
            _isReporting = false;
            
            if (WantedManager.Instance != null)
            {
                WantedManager.Instance.SpikeKnives();
                UIManager.Instance?.ShowToast("Police are on the way!", 2f);
            }
            
            // Run away after calling
            this.enabled = false; 
        }
    }
}
