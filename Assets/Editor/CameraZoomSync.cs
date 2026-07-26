using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.World;

/// <summary>
/// Re-applies EKVibe's camera constants (pitch/yaw/distance/ortho size) to the Main
/// Camera's IsometricCameraFollow in the open scene. Needed because those fields were
/// serialized with their old default values when the camera was first created —
/// changing the const in code alone doesn't move an already-saved component.
/// </summary>
public static class CameraZoomSync
{
    [MenuItem("Tools/Exiled Alvaston/Repair/Sync Camera Zoom")]
    public static void Run()
    {
        var follow = Object.FindObjectOfType<IsometricCameraFollow>();
        if (follow == null)
        {
            Debug.LogWarning("CameraZoomSync: no IsometricCameraFollow found on the Main Camera in this scene.");
            return;
        }

        Undo.RecordObject(follow, "Sync Camera Zoom");
        follow.OrthoSize = ExiledAlvaston.Vibe.EKVibe.CameraOrthoSize;
        follow.ApplyVibeLock();

        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        Debug.Log($"Camera ortho size synced to {ExiledAlvaston.Vibe.EKVibe.CameraOrthoSize}.");
    }
}
