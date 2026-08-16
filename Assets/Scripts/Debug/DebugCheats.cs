#if UNITY_EDITOR || DEVELOPMENT_BUILD
using UnityEngine;
using GBHEngland.Flow;
using GBHEngland.UI;
using GBHEngland.Vibe;

namespace GBHEngland.Debugging
{
    /// <summary>
    /// Dev-only cheats. Self-bootstraps in Play mode and is compiled ENTIRELY out of release builds
    /// (the whole file sits inside <c>#if UNITY_EDITOR || DEVELOPMENT_BUILD</c>), so none of this
    /// ships. Follows the existing F8-grants-test-gear convention in InventoryController.
    ///
    ///   F9 — grant £100 (enough to hire Alex and check the wallet updates).
    ///
    /// Add more keys here as testing needs them, each behind the same guard. Cheats act on
    /// PlayerSession, so they only do something once a run is actually in progress (the wallet is
    /// reset by StartNewGame / overwritten by Continue — press the key while playing, not on a menu).
    /// </summary>
    public class DebugCheats : MonoBehaviour
    {
        private static DebugCheats _instance;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (_instance != null) return;
            var go = new GameObject("~DebugCheats");
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<DebugCheats>();
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F9))
                GrantMoney(100);
        }

        private static void GrantMoney(int amount)
        {
            PlayerSession session = PlayerSession.Instance;
            if (session == null) return;

            session.AddPounds(amount);   // fires OnPoundsChanged, so the wallet readout updates

            if (UIManager.Instance != null)
                UIManager.Instance.ShowToast(
                    $"Dev: +{EKVibe.FormatPounds(amount)} (wallet {EKVibe.FormatPounds(session.Pounds)})", 1.6f);
        }
    }
}
#endif