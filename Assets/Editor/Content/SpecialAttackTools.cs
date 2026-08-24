using UnityEditor;
using UnityEngine;
using GBHEngland.Data;

/// <summary>
/// Creates the two special-attack AbilityData assets the HUD's SPN and DSH buttons run.
///
/// ⚠ Creates only if absent and never overwrites, which is why this sits under Tools/Content
/// and not under Tools/Danger Zone: run it twice and the second run reports two skips and edits
/// nothing. Re-running after the owner has authored the prose is safe.
///
/// ⚠ The destination is Assets/Data/Abilities/, deliberately OUTSIDE Resources/. A special
/// attack is an AbilityData but it is not a spell: SpellDatabase loads Resources/Abilities, so an
/// asset placed there would be learned by Learn All Current Spells, slotted into the spellbook and
/// written into savegame.json - at which point its AbilityID is a save key that can never be
/// renamed. See docs/reference/PLAYER_COMBAT.md.
///
/// The prose fields - AbilityName, Description and IconGlyph - are deliberately left blank. They
/// are the owner's words, and the HUD falls back to its SPN / DSH placeholders until they are set.
/// </summary>
public static class SpecialAttackTools
{
    private const string MenuPath = "Tools/Content/Create Special Attack Assets";
    private const string Folder = "Assets/Data/Abilities";

    [MenuItem(MenuPath)]
    public static void CreateSpecialAttackAssets()
    {
        // Cheap standing guard on the invariant above: if this constant is ever edited to point
        // inside a Resources folder, refuse rather than mint a future save key.
        if (Folder.Contains("/Resources/") || Folder.EndsWith("/Resources"))
        {
            Debug.LogError("Create Special Attack Assets: refusing to write special attacks into a " +
                           "Resources folder - SpellDatabase would load them and their AbilityIDs " +
                           "would become save keys. See docs/reference/PLAYER_COMBAT.md.");
            return;
        }

        EnsureFolder(Folder);

        int created = 0, skipped = 0;
        created += CreateIfAbsent("Special_spin", "special_spin", SpecialAttackKind.Spin, 6f, ref skipped) ? 1 : 0;
        created += CreateIfAbsent("Special_dash", "special_dash", SpecialAttackKind.Dash, 5f, ref skipped) ? 1 : 0;

        if (created > 0)
        {
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        Debug.Log($"Create Special Attack Assets: created {created}, left {skipped} existing asset(s) " +
                  $"untouched in {Folder}. Next: fill in AbilityName, Description and IconGlyph on " +
                  "each, then drag Special_spin into element 0 and Special_dash into element 1 of " +
                  "the player CombatController's Special Attacks list and save the scene.");
    }

    /// <summary>
    /// Returns true if it created the asset. An existing asset is left exactly as it is - the
    /// owner's prose, cooldowns and class gates are edits this tool must never undo.
    /// </summary>
    private static bool CreateIfAbsent(string fileName, string abilityId, SpecialAttackKind kind,
                                       float cooldown, ref int skipped)
    {
        string path = $"{Folder}/{fileName}.asset";
        if (AssetDatabase.LoadAssetAtPath<AbilityData>(path) != null)
        {
            skipped++;
            return false;
        }

        var ability = ScriptableObject.CreateInstance<AbilityData>();
        ability.AbilityID = abilityId;

        // AbilityName, Description and IconGlyph stay blank on purpose - the owner's words.
        ability.IsSpecialAttack = true;
        ability.SpecialKind = kind;

        // ⚠ None, not the enum's zero default of Mana. The stamina cost is a percent of the live
        // maximum charged by CombatController.SpecialStaminaCost, for the reason CurrentRollCost
        // documents: a flat cost silently gets cheaper at every level as the pool grows. Leaving
        // this as Mana would charge a second, flat cost from the wrong pool.
        ability.ResourceType = AbilityResourceType.None;
        ability.ResourceCost = 0;

        // Drives the HUD button's radial sweep. A starting suggestion; tune on the asset.
        ability.CooldownTime = cooldown;

        // AllowedClasses left null - an empty gate admits every class, the house semantic shared
        // with PerkData and ItemData.
        AssetDatabase.CreateAsset(ability, path);
        return true;
    }

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;

        string[] parts = assetFolder.Split('/');
        string running = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = $"{running}/{parts[i]}";
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(running, parts[i]);
            running = next;
        }
    }
}
