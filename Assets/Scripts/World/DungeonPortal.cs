using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Generic two-way door between chunks: drop one in the overworld pointing at a dungeon
    /// chunk, and one inside the dungeon prefab pointing back. Uses the range-based interact
    /// system (walk up, press USE). Place via Tools/Exiled Alvaston/Portal Placement, or add
    /// by hand and fill in the fields.
    /// </summary>
    public class DungeonPortal : MonoBehaviour
    {
        [Tooltip("Chunk this portal loads. Must have a ChunkPrefab assigned.")]
        public MapChunkData TargetChunk;
        [Tooltip("Where the player appears in the target chunk. Put it a few units clear of the return portal.")]
        public Vector3 SpawnPosition;
        public string Prompt = "Enter";
        [Tooltip("Barred until the Manor Cellars tutorial is finished.")]
        public bool RequireTutorialComplete;

        // Shared across all portals so arriving next to a paired return portal
        // can't immediately bounce the player back where they came from.
        private static float _nextUseAt;

        private void Awake()
        {
            var interactable = GetComponent<Interactable>();
            if (interactable == null)
                interactable = gameObject.AddComponent<Interactable>();
            interactable.Prompt = Prompt;
            interactable.InteractRange = 3f;
            interactable.OnInteract.AddListener(Travel);
        }

        private void OnEnable()
        {
            _nextUseAt = Mathf.Max(_nextUseAt, Time.unscaledTime + 0.75f);
        }

        public void Travel()
        {
            if (Time.unscaledTime < _nextUseAt) return;

            if (RequireTutorialComplete
                && (PlayerSession.Instance == null || !PlayerSession.Instance.TutorialComplete))
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("The way is barred for now.");
                return;
            }

            if (TargetChunk == null || TargetChunk.ChunkPrefab == null)
            {
                Debug.LogWarning($"DungeonPortal '{name}': TargetChunk missing or has no prefab.");
                return;
            }
            if (ChunkManager.Instance == null)
            {
                Debug.LogWarning($"DungeonPortal '{name}': no ChunkManager in scene.");
                return;
            }

            _nextUseAt = Time.unscaledTime + 1.5f;

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat(Prompt + "...");

            ChunkManager.Instance.TravelTo(TargetChunk, SpawnPosition);
        }
    }
}
