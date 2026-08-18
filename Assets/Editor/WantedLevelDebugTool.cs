using UnityEngine;
using UnityEditor;
using GBHEngland.Systems;
using GBHEngland.UI;

/// <summary>
/// Dev shortcut: force the Knives (wanted) level to a specific value during Play Mode, so the
/// HUD meter can be checked at every level without actually provoking the police. Sets
/// WantedManager.CurrentKnives directly and repaints UIManager — does not call SpikeKnives, so
/// no police are spawned.
/// </summary>
public static class WantedLevelDebugTool
{
    [MenuItem("Tools/Debug/Wanted Level/0 (Clear)")] public static void Set0() => Set(0);
    [MenuItem("Tools/Debug/Wanted Level/1")] public static void Set1() => Set(1);
    [MenuItem("Tools/Debug/Wanted Level/2")] public static void Set2() => Set(2);
    [MenuItem("Tools/Debug/Wanted Level/3")] public static void Set3() => Set(3);
    [MenuItem("Tools/Debug/Wanted Level/4")] public static void Set4() => Set(4);
    [MenuItem("Tools/Debug/Wanted Level/5")] public static void Set5() => Set(5);

    private static void Set(int level)
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("WantedLevelDebugTool: enter Play Mode first — this sets the live WantedManager at runtime.");
            return;
        }

        WantedManager wanted = WantedManager.Instance;
        if (wanted == null)
        {
            Debug.LogWarning("WantedLevelDebugTool: no live WantedManager found.");
            return;
        }

        wanted.CurrentKnives = level;

        if (UIManager.Instance != null)
            UIManager.Instance.UpdateKnivesUI(level);

        Debug.Log($"WantedLevelDebugTool: Knives set to {level}.");
    }
}
