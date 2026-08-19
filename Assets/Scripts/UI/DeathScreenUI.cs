using UnityEngine;
using UnityEngine.UI;
using GBHEngland.Combat;
using GBHEngland.World;
using GBHEngland.Flow;
using GBHEngland.Systems;

namespace GBHEngland.UI
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

            RestyleWin95();
        }

        /// <summary>One-time Win95 skin for the scene-authored death-screen buttons.</summary>
        private void RestyleWin95()
        {
            Win95Skin.StyleButtonWithLabel(LoadLastGameButton);
            Win95Skin.StyleButtonWithLabel(NewGameButton);
            Win95Skin.StyleButtonWithLabel(QuitButton);
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
            WantedManager.Instance?.ClearWanted();
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
                Data.MapChunkData home = chunkMgr.FindChunkByName("Home_London");
                if (home != null && home.ChunkPrefab != null)
                {
                    Data.MapChunkData previousChunk = chunkMgr.CurrentChunkData;

                    if (chunkMgr.CurrentChunkInstance != null)
                        Destroy(chunkMgr.CurrentChunkInstance);

                    WantedManager.Instance?.OnChunkTransition(previousChunk, home, ChunkTravelKind.Portal);

                    chunkMgr.CurrentChunkData = home;
                    PlayerSession.Instance?.MarkChunkVisited(home.ChunkName);
                    // Silent: a death-screen respawn is not a discovery.
                    WikiUnlock.GrantForChunk(home.ChunkName, silent: true);
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
