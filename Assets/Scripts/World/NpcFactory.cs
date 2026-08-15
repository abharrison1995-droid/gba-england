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

            ApplyPickpocket(preset, go, interactable);

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
        /// Makes a civilian robbable.
        ///
        /// This is the only way a mark is authored. Marks used to be hand-built prefabs carrying a
        /// persisted OnInteract → TryPickpocket call, which meant the only way to make a new one
        /// was to copy that prefab, and a civilian built from a preset could never be one. Adding
        /// the component here means the palette authors marks directly, from a preset.
        ///
        /// Note what this does *not* do: wire the listener. UnityEvent.AddListener produces a
        /// non-persistent listener that is never serialized, so wiring one while authoring a chunk
        /// prefab would look correct in the editor and be silently absent from the saved asset.
        /// PickpocketInteractable subscribes itself in Awake instead. Everything set here (the
        /// component, its tuning, the prompt) is serialized state that survives the save.
        ///
        /// Dialogue and pickpocketing are mutually exclusive, for the same reason the caller only
        /// adds NPCDialogueInteractable when there is something to say: two listeners answering one
        /// button press is the bug being avoided. Dialogue wins the clash because its failure is
        /// the recoverable one — a civilian you cannot rob is a shrug, a quest giver who will not
        /// talk is a broken quest.
        /// </summary>
        private static void ApplyPickpocket(PlacementPreset preset, GameObject go, Interactable interactable)
        {
            if (!preset.Pickpocketable) return;

            if (preset.Conversation != null)
            {
                Debug.LogWarning(
                    $"NpcFactory: preset '{preset.Label}' is marked Pickpocketable but also has a " +
                    "Conversation, and one button press cannot do both. Dialogue wins; nothing was " +
                    "made robbable. Clear Conversation and AmbientLine to make them a mark instead.",
                    go);
                return;
            }

            var pickpocket = go.AddComponent<PickpocketInteractable>();
            pickpocket.MinPounds = preset.PickpocketMinPounds;
            pickpocket.MaxPounds = preset.PickpocketMaxPounds;
            pickpocket.CatchChance = preset.PickpocketCatchChance;
            // Null is meaningful here: it is what selects the instant pounds roll over the
            // minigame, so copying it across unconditionally is correct.
            pickpocket.PickpocketBand = preset.PickpocketBand;

            // "Talk to X" is wrong for someone who has nothing to say. The prompt is what the HUD
            // shows while they are the closest interactable, so it is the only clue the player gets
            // that this civilian is worth crouching next to.
            string npcName = string.IsNullOrEmpty(preset.NpcName) ? "them" : preset.NpcName;
            interactable.Prompt = $"Pickpocket {npcName}";
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
                    "Tools > Content > Wire Presets From Imported Art.";

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
        /// was set deliberately and wins. This preserves deliberately short or tall authored
        /// characters instead of forcing every NPC to the shared adult height.
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
