using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.UI;

/// <summary>Spell content wiring plus reversible Play Mode spellbook shortcuts.</summary>
public static class SpellTools
{
    private const string LearnMenu = "Tools/Debug/Learn All Current Spells";
    private const string ForgetMenu = "Tools/Debug/Forget All Spells";
    private const string PreviewVfxMenu = "Tools/Debug/Preview Current Spell VFX";

    [MenuItem(LearnMenu)]
    public static void LearnAllCurrentSpells()
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Learn All Current Spells: enter Play Mode first.");
            return;
        }

        CombatController combat = CombatController.Instance ?? Object.FindObjectOfType<CombatController>();
        if (combat == null)
        {
            Debug.LogWarning("Learn All Current Spells: no live CombatController found.");
            return;
        }

        SpellDatabase.ResetCache();
        int learned = combat.LearnAllCurrentSpells();
        SpellbookUI.Open();
        Debug.Log($"Learn All Current Spells: learned {learned}; spellbook now contains " +
                  $"{combat.KnownSpells.Count} spell(s). The first four are equipped.");
    }

    [MenuItem(ForgetMenu)]
    public static void ForgetAllSpells()
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Forget All Spells: enter Play Mode first.");
            return;
        }

        CombatController combat = CombatController.Instance ?? Object.FindObjectOfType<CombatController>();
        if (combat == null)
        {
            Debug.LogWarning("Forget All Spells: no live CombatController found.");
            return;
        }

        combat.ClearLearnedSpells();
        SpellbookUI.Open();
        Debug.Log("Forget All Spells: cleared the live spellbook and all four equipped slots.");
    }

    [MenuItem(LearnMenu, true)]
    private static bool ValidateLearnTool() => Application.isPlaying;

    [MenuItem(ForgetMenu, true)]
    private static bool ValidateForgetTool() => Application.isPlaying;

    /// <summary>
    /// Spawns every distinct clip currently wired to the six spells in a grid around the player.
    /// This isolates imported clip playback from targeting, mana, cooldowns and spellbook input.
    /// </summary>
    [MenuItem(PreviewVfxMenu)]
    public static void PreviewCurrentSpellVfx()
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Preview Current Spell VFX: enter Play Mode first.");
            return;
        }
        if (ExiledAlvaston.Systems.PauseManager.IsPaused)
        {
            Debug.LogWarning("Preview Current Spell VFX: close the spellbook or other paused window first.");
            return;
        }

        CombatController combat = CombatController.Instance ?? Object.FindObjectOfType<CombatController>();
        if (combat == null)
        {
            Debug.LogWarning("Preview Current Spell VFX: no live CombatController found.");
            return;
        }

        SpellDatabase.ResetCache();
        var clips = new List<AnimationClip>();
        foreach (string abilityId in SpellDatabase.CurrentSpellIds)
        {
            AbilityData ability = SpellDatabase.Find(abilityId);
            if (ability == null) continue;
            AddDistinct(clips, ability.CastEffectClip);
            AddDistinct(clips, ability.ProjectileClip);
            AddDistinct(clips, ability.ImpactClip);
            AddDistinct(clips, ability.LingeringClip);
        }

        int sampled = 0;
        var failed = new List<string>();
        for (int i = 0; i < clips.Count; i++)
        {
            int column = i % 5;
            int row = i / 5;
            Vector3 position = combat.transform.position
                             + new Vector3((column - 2) * 1.35f, 0.9f + row * 1.35f, 1.5f);
            SpellFxPlayer player = SpellFxPlayer.Spawn(clips[i], position);
            SpriteRenderer renderer = player != null ? player.GetComponent<SpriteRenderer>() : null;
            if (renderer != null && renderer.sprite != null) sampled++;
            else failed.Add(clips[i].name);
        }

        if (failed.Count == 0)
            Debug.Log($"Preview Current Spell VFX: sampled {sampled}/{clips.Count} wired clips around the player.");
        else
            Debug.LogWarning($"Preview Current Spell VFX: {sampled}/{clips.Count} clips sampled a sprite; failed: " +
                             string.Join(", ", failed));
    }

    [MenuItem(PreviewVfxMenu, true)]
    private static bool ValidatePreviewVfxTool() => Application.isPlaying;

    /// <summary>
    /// Reconnects generated clips after an art import. It only writes VFX references; all authored
    /// costs, cooldowns and magnitudes survive a re-run.
    /// </summary>
    [MenuItem("Tools/Content/Wire Current Spell VFX")]
    public static void WireCurrentSpellVfx()
    {
        var missing = new List<string>();

        Wire("spark", projectile: "sheet_fx_spark_effect", impact: "sheet_fx_spark_impact",
            missing: missing);
        Wire("fireball", projectile: "sheet_fx_fireball_effect", impact: "sheet_fx_fireball_impact",
            missing: missing);
        Wire("healing_aura", cast: "sheet_fx_healing_aura_effect", missing: missing);
        Wire("iron_skin", cast: "sheet_fx_iron_skin_effect", missing: missing);
        Wire("sludge_bolt", projectile: "sheet_fx_sludge_bolt_effect",
            impact: "sheet_fx_sludge_bolt_impact", lingering: "sheet_fx_sludge_bolt_puddle",
            missing: missing);
        Wire("light_feet", cast: "sheet_fx_light_feet_effect", missing: missing);

        AssetDatabase.SaveAssets();
        SpellDatabase.ResetCache();
        if (missing.Count == 0)
            Debug.Log("Wire Current Spell VFX: all six spell definitions are wired.");
        else
            Debug.LogWarning("Wire Current Spell VFX: missing imported clips: " +
                             string.Join(", ", missing));
    }

    [MenuItem("Tools/Content/Wire Current Spell VFX", true)]
    private static bool ValidateWireTool() => !Application.isPlaying;

    private static void Wire(string abilityId, string cast = null, string projectile = null,
        string impact = null, string lingering = null, List<string> missing = null)
    {
        AbilityData ability = FindAsset(abilityId);
        if (ability == null)
        {
            missing?.Add($"AbilityData '{abilityId}'");
            return;
        }

        Undo.RecordObject(ability, "Wire spell VFX");
        AssignClip(ref ability.CastEffectClip, cast, missing);
        AssignClip(ref ability.ProjectileClip, projectile, missing);
        AssignClip(ref ability.ImpactClip, impact, missing);
        AssignClip(ref ability.LingeringClip, lingering, missing);
        EditorUtility.SetDirty(ability);
    }

    private static AbilityData FindAsset(string abilityId)
    {
        foreach (string guid in AssetDatabase.FindAssets("t:AbilityData", new[] { "Assets/Resources/Abilities" }))
        {
            AbilityData ability = AssetDatabase.LoadAssetAtPath<AbilityData>(AssetDatabase.GUIDToAssetPath(guid));
            if (ability != null && string.Equals(ability.AbilityID, abilityId,
                System.StringComparison.OrdinalIgnoreCase))
                return ability;
        }
        return null;
    }

    private static void AssignClip(ref AnimationClip destination, string clipName, List<string> missing)
    {
        if (string.IsNullOrEmpty(clipName)) return;
        string path = $"Assets/Animations/Generated/{clipName}.anim";
        AnimationClip clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
        if (clip == null)
        {
            missing?.Add(clipName);
            return; // preserve an existing reference if an import is temporarily absent
        }
        destination = clip;
    }

    private static void AddDistinct(List<AnimationClip> clips, AnimationClip clip)
    {
        if (clip != null && !clips.Contains(clip)) clips.Add(clip);
    }
}
