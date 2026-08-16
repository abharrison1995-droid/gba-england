using System;
using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// The handful of <see cref="PlacementPreset"/> assets that runtime code needs to find by name.
    ///
    /// Presets live in `Assets/Data/Presets/`, which is not under `Resources/` and should not be:
    /// everything reachable from `Resources/` ships in the build, and the chest preset alone would
    /// drag a 45 MB prop pack in with it. So a single small asset lives there instead and points at
    /// the few presets the game itself has to resolve — the tutorial's characters, today.
    ///
    /// Lookup is by an authored <see cref="Entry.Key"/> rather than by asset name, so a preset can
    /// be renamed, moved or relabelled without silently breaking the code that asks for it. The key
    /// is the contract; everything else about the preset is free to change.
    /// </summary>
    [CreateAssetMenu(fileName = "PlacementPresetLibrary",
                     menuName = "GBH England/Data/Placement Preset Library")]
    public class PlacementPresetLibrary : ScriptableObject
    {
        /// <summary>Where <see cref="Resources.Load"/> expects this: Assets/Resources/&lt;this&gt;.asset.</summary>
        public const string ResourcePath = "PlacementPresetLibrary";

        [Serializable]
        public class Entry
        {
            [Tooltip("The name runtime code asks for. Renaming the preset asset is safe; changing " +
                     "this is not — it is what the code looks up.")]
            public string Key = "";

            public PlacementPreset Preset;
        }

        public List<Entry> Entries = new List<Entry>();

        private static PlacementPresetLibrary _loaded;

        /// <summary>The library asset, loaded once. Null if nobody has created it yet.</summary>
        public static PlacementPresetLibrary Instance
        {
            get
            {
                if (_loaded == null)
                    _loaded = Resources.Load<PlacementPresetLibrary>(ResourcePath);
                return _loaded;
            }
        }

        /// <summary>
        /// The preset keyed <paramref name="key"/>, or null with an error saying which of the three
        /// things went wrong. Spawning nothing and saying nothing is how a missing tutorial
        /// character becomes twenty minutes of looking in the wrong place.
        /// </summary>
        public static PlacementPreset Get(string key)
        {
            PlacementPresetLibrary library = Instance;

            if (library == null)
            {
                Debug.LogError(
                    $"PlacementPresetLibrary: no Assets/Resources/{ResourcePath}.asset, so '{key}' " +
                    "cannot be resolved. Run Tools > Content > Create Starter Presets.");
                return null;
            }

            foreach (Entry entry in library.Entries)
            {
                if (entry == null) continue;
                if (!string.Equals(entry.Key, key, StringComparison.Ordinal)) continue;

                if (entry.Preset == null)
                {
                    Debug.LogError(
                        $"PlacementPresetLibrary: the entry keyed '{key}' has no preset assigned.",
                        library);
                    return null;
                }
                return entry.Preset;
            }

            Debug.LogError($"PlacementPresetLibrary: nothing keyed '{key}'. Add an entry for it, or " +
                           "run Tools > Content > Create Starter Presets to restore the " +
                           "standard ones.", library);
            return null;
        }
    }
}
