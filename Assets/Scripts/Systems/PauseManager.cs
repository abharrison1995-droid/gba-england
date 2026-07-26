using UnityEngine;

namespace ExiledAlvaston.Systems
{
    /// <summary>
    /// Ref-counted owner of Time.timeScale so inventory, dialogue and chunk
    /// transitions can pause independently without clobbering each other.
    /// </summary>
    public static class PauseManager
    {
        private static int _pauseCount;

        public static bool IsPaused => _pauseCount > 0;

        public static void Push()
        {
            _pauseCount++;
            Apply();
        }

        public static void Pop()
        {
            _pauseCount = Mathf.Max(0, _pauseCount - 1);
            Apply();
        }

        /// <summary>Hard reset (title screen / new game).</summary>
        public static void Reset()
        {
            _pauseCount = 0;
            Apply();
        }

        private static void Apply()
        {
            Time.timeScale = _pauseCount > 0 ? 0f : 1f;
        }
    }
}
