using UnityEngine;
using UnityEngine.UI;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Flow;
using ExiledAlvaston.Systems;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Standalone death screen — works even without GameFlowController wired up. Shows on
    /// player death, offers Load Last Game / New Game / Quit.
    /// </summary>
    public class DeathScreenUI : MonoBehaviour
    {
        public static DeathScreenUI Instance { get; private set; }

        public CanvasGroup Root;
        public Button LoadLastGameButton;
        public Button NewGameButton;
        public Button QuitButton;

        private void Awake()
        {
            Instance = this;

            if (Root != null)
            {
                // Hidden via CanvasGroup, not SetActive(false) — an inactive GameObject never
                // runs Awake() on scene load, which would leave Instance permanently null.
                Root.alpha = 0f;
                Root.interactable = false;
                Root.blocksRaycasts = false;
            }

            if (LoadLastGameButton != null) LoadLastGameButton.onClick.AddListener(OnLoadLastGame);
            if (NewGameButton != null) NewGameButton.onClick.AddListener(OnNewGame);
            if (QuitButton != null) QuitButton.onClick.AddListener(OnQuit);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        public void Show()
        {
            if (Root == null) return;

            Root.alpha = 1f;
            Root.interactable = true;
            Root.blocksRaycasts = true;

            if (LoadLastGameButton != null)
                LoadLastGameButton.interactable = SaveGameManager.HasSave;

            PauseManager.Push();
        }

        private void Hide()
        {
            if (Root == null) return;

            Root.alpha = 0f;
            Root.interactable = false;
            Root.blocksRaycasts = false;

            PauseManager.Pop();
        }

        private void OnLoadLastGame()
        {
            // Full restore (session + quests + world) via GameFlow; raw world load as fallback
            bool loaded = GameFlowController.Instance != null
                ? GameFlowController.Instance.ContinueFromSave()
                : SaveGameManager.Load();

            if (loaded)
                Hide();
            else if (LoadLastGameButton != null)
                LoadLastGameButton.interactable = false;
        }

        private void OnNewGame()
        {
            SaveGameManager.ClearSave();
            Hide();

            if (GameFlowController.Instance != null)
            {
                // Title → Creator flow owns the reset (session, quests, spawn)
                GameFlowController.Instance.ShowTitle();
                return;
            }

            // Legacy fallback when no GameFlowController exists in the scene
            CombatController player = CombatController.Instance;
            ChunkManager chunkMgr = ChunkManager.Instance;

            if (chunkMgr != null && player != null)
            {
                Data.MapChunkData home = chunkMgr.FindChunkByName("Home_Alvaston");
                if (home != null && home.ChunkPrefab != null)
                {
                    if (chunkMgr.CurrentChunkInstance != null)
                        Destroy(chunkMgr.CurrentChunkInstance);

                    chunkMgr.CurrentChunkData = home;
                    GameObject instance = Instantiate(home.ChunkPrefab, Vector3.zero, Quaternion.identity);
                    instance.name = home.ChunkPrefab.name;
                    chunkMgr.CurrentChunkInstance = instance;
                    chunkMgr.TeleportPlayer(Vector3.up);
                }
            }

            if (player != null) player.ReviveFull();
        }

        private void OnQuit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
