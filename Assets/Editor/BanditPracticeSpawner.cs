using UnityEngine;
using UnityEditor;
using UnityEngine.AI;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Vibe;

/// <summary>
/// Spawns a practice Bandit in front of the player for combat testing.
/// </summary>
public static class BanditPracticeSpawner
{
    [MenuItem("Tools/Exiled Alvaston/Debug/Spawn Practice Bandit")]
    public static void SpawnBandit()
    {
        Sprite banditSprite = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/Placeholders/spr_bandit.png");

        Vector3 spawnPos = new Vector3(3f, 0f, 2f);
        var player = Object.FindObjectOfType<CombatController>();
        if (player != null)
        {
            Vector3 facing = player.FacingDirection.sqrMagnitude > 0.01f
                ? player.FacingDirection
                : player.transform.forward;
            facing.y = 0f;
            if (facing.sqrMagnitude < 0.01f) facing = Vector3.forward;
            facing.Normalize();
            spawnPos = player.transform.position + facing * 3.5f;
        }
        spawnPos.y = 0f;

        if (NavMesh.SamplePosition(spawnPos, out NavMeshHit navHit, 10f, NavMesh.AllAreas))
            spawnPos = navHit.position;
        else
            Debug.LogWarning("No NavMesh here — bandit will still spawn, but may not path. Run Tools/Bake Navigation Mesh.");

        GameObject bandit = new GameObject("Bandit");
        Undo.RegisterCreatedObjectUndo(bandit, "Spawn Practice Bandit");
        bandit.transform.position = spawnPos;

        var col = bandit.AddComponent<CapsuleCollider>();
        col.height = EKVibe.CharacterHeight;
        col.radius = 0.28f;
        col.center = new Vector3(0f, EKVibe.CharacterHeight * 0.5f, 0f);

        Health h = bandit.AddComponent<Health>();
        h.MaxHealth = 45;
        h.CurrentHealth = 45;
        h.DisplayName = "Bandit";

        var agent = bandit.AddComponent<NavMeshAgent>();
        agent.height = EKVibe.CharacterHeight;
        agent.radius = 0.28f;
        agent.speed = 3.8f;
        agent.stoppingDistance = 1.2f;
        if (agent.isOnNavMesh)
            agent.Warp(spawnPos);

        EnemyAI ai = bandit.AddComponent<EnemyAI>();
        ai.Damage = 7;
        ai.SightRadius = 16f;
        ai.AttackRange = 1.6f;
        ai.MoveSpeed = 3.8f;

        var visual = bandit.AddComponent<WorldActorVisual>();
        visual.ActorSprite = banditSprite;
        visual.Height = EKVibe.CharacterHeight;
        visual.Width = EKVibe.CharacterWidth;
        visual.ApplyVisual();

        if (banditSprite == null)
            Debug.LogWarning("Missing Assets/Art/Placeholders/spr_bandit.png — run Tools/Exiled Alvaston/Repair/Generate Placeholder Art.");

        var plate = bandit.AddComponent<EnemyNameplate>();
        plate.Level = 3;

        int enemyLayer = LayerMask.NameToLayer("Enemy");
        if (enemyLayer >= 0)
            bandit.layer = enemyLayer;

        Selection.activeGameObject = bandit;
        EditorGUIUtility.PingObject(bandit);
        Debug.Log($"Practice Bandit spawned at {spawnPos}. Enter Play Mode to fight.");
    }

    [MenuItem("Tools/Exiled Alvaston/Debug/Clear All Bandits")]
    public static void ClearBandits()
    {
        int removed = 0;
        foreach (var ai in Object.FindObjectsOfType<EnemyAI>())
        {
            if (ai == null) continue;
            string n = ai.gameObject.name;
            if (n.Contains("Bandit") || n.Contains("TestEnemy"))
            {
                Undo.DestroyObjectImmediate(ai.gameObject);
                removed++;
            }
        }
        Debug.Log(removed > 0 ? $"Removed {removed} bandit(s)." : "No bandits found.");
    }
}
