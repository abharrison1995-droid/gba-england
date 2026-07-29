using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Builds an NPC from a <see cref="PlacementPreset"/> — the one description of what an NPC is,
    /// used by everything that makes one.
    ///
    /// This is runtime code deliberately. The World Palette's builders live in `Assets/Editor/`,
    /// which is stripped from builds, so anything spawning an NPC while the game runs — the magic
    /// tutorial, most obviously — cannot call them and would have to keep a second copy of the
    /// recipe. That second copy is exactly how the tutorial's characters ended up outside the
    /// preset system, assigned a single static sprite each, while everything else moved on.
    ///
    /// `PlacementBuilders` wraps this and adds what only the editor cares about: undo registration,
    /// prefab-stage bookkeeping, and a placeholder body to click on when a preset has no art yet.
    /// Nothing in here may touch `UnityEditor`.
    /// </summary>
    public static class NpcFactory
    {
        /// <summary>
        /// Creates the NPC and returns its root. Never returns null for a non-null preset — a
        /// preset with no art still produces an object, because a caller that positioned it and
        /// wired it into a quest should not have to cope with getting nothing back. It complains
        /// loudly instead.
        /// </summary>
        public static GameObject Build(PlacementPreset preset, Vector3 position, Transform parent)
        {
            if (preset == null) return null;

            string npcName = string.IsNullOrEmpty(preset.NpcName) ? "Villager" : preset.NpcName;

            var go = new GameObject($"NPC_{npcName}");

            // worldPositionStays, then the world position — so a placement lands where it was asked
            // for, whatever transform the parent happens to be carrying.
            if (parent != null) go.transform.SetParent(parent, true);
            go.transform.position = position;

            var interactable = go.AddComponent<Interactable>();
            interactable.Prompt = $"Talk to {npcName}";
            interactable.InteractRange = 3f;

            // Only when there is something to say. NPCDialogueInteractable subscribes itself to
            // Interactable.OnInteract in Awake, so adding it unconditionally would give a character
            // who already owns their interaction — Daniel Pauls and his mentor script — a second
            // listener firing alongside the first.
            if (preset.Conversation != null)
                go.AddComponent<NPCDialogueInteractable>().Conversation = preset.Conversation;

            ApplyVisual(preset, go);

            if (preset.Roams)
            {
                var wander = go.AddComponent<AI.NPCWander>();
                wander.WanderRadius = preset.RoamRadius;
            }

            ApplyQuestKey(preset, go);

            return go;
        }

        /// <summary>
        /// The billboard, sized from the preset, plus the Animator if the subject's art has been
        /// imported.
        ///
        /// A missing sprite is an error rather than a shrug: the importer sets NpcSprite and
        /// NpcController together off the same idle sheet, so a preset carrying one without the
        /// other has been half-configured by hand. There is no placeholder body here on purpose —
        /// a capsule standing in the running game is worse than an obvious hole plus a console
        /// error, and the editor adds its own capsule for authoring.
        /// </summary>
        private static void ApplyVisual(PlacementPreset preset, GameObject go)
        {
            if (preset.NpcSprite == null)
            {
                string message =
                    $"NpcFactory: preset '{preset.Label}' has no NpcSprite, so '{go.name}' has " +
                    "nothing to draw. Import the subject's idle sheet, or run " +
                    "Tools > GBA > Content > Wire Presets From Imported Art.";

                // Severity depends on when this happens, because the two cases are not the same
                // problem. Authoring a character before their art exists is a normal step — the
                // editor stands a placeholder body in and carries on — so crying error over it
                // would train the console to be ignored. Reaching play mode still missing the art
                // is a real defect, and by then nobody is watching for warnings.
                if (Application.isPlaying) Debug.LogError(message, go);
                else Debug.LogWarning(message, go);
                return;
            }

            var visual = go.AddComponent<WorldActorVisual>();
            visual.ActorSprite = preset.NpcSprite;
            // Resize through Height, never by scaling ActorVisual — ApplyVisual positions that
            // child at Height/2 assuming scale 1, so scaling it buries the feet (CLAUDE.md §12).
            visual.Height = HeightFor(preset);
            visual.Width = EKVibe.CharacterWidth;
            visual.ApplyVisual();

            if (preset.NpcController != null)
                visual.AttachAnimator(preset.NpcController);
        }

        /// <summary>
        /// World height to build an actor at. <see cref="PlacementPreset.NpcHeight"/> of 0 means
        /// inherit: the art importer writes the subject's own <c>worldHeight</c> there when its
        /// sheets land, and the shared character height stands in until they do. Anything above 0
        /// was set deliberately and wins. An angry squirrel is 0.45 units against a councillor's
        /// 1.35, so this is the difference between a squirrel and a man in a squirrel suit.
        /// </summary>
        public static float HeightFor(PlacementPreset preset) =>
            preset != null && preset.NpcHeight > 0f ? preset.NpcHeight : EKVibe.CharacterHeight;

        /// <summary>
        /// Kept here rather than shared with PlacementBuilders' copy: that one also serves chests,
        /// portals and enemies, and reaching across the editor/runtime boundary for six lines would
        /// buy less than it costs.
        /// </summary>
        private static void ApplyQuestKey(PlacementPreset preset, GameObject go)
        {
            if (go == null || string.IsNullOrEmpty(preset.QuestKey)) return;

            var actor = go.GetComponent<QuestActor>();
            if (actor == null) actor = go.AddComponent<QuestActor>();
            actor.Key = preset.QuestKey;
        }
    }
}
