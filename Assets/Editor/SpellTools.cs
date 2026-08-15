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
}
