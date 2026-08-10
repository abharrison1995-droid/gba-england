using System;
using System.Collections.Generic;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;
using UnityEngine;

namespace ExiledAlvaston.Flow
{
    [Serializable]
    public sealed class PlayerClassVisualProfile
    {
        public PlayerClass Class;
        public RuntimeAnimatorController Controller;
        public Sprite RestingSprite;
        public Sprite[] IdlePreviewFrames;
        public float PreviewFps = 6f;
        public bool GameplayReady;
        public Sprite Portrait;
    }

    /// <summary>Serialized class-to-art mapping shared by character preview and gameplay.</summary>
    public sealed class PlayerClassVisualLibrary : MonoBehaviour
    {
        public PlayerClassVisualProfile[] Profiles;

        private readonly HashSet<PlayerClass> _warnedFallbacks = new HashSet<PlayerClass>();

        public PlayerClassVisualProfile GetProfile(PlayerClass playerClass)
        {
            if (Profiles == null) return null;
            for (int i = 0; i < Profiles.Length; i++)
            {
                PlayerClassVisualProfile profile = Profiles[i];
                if (profile != null && profile.Class == playerClass)
                    return profile;
            }
            return null;
        }

        public void ApplyToPlayer(CombatController combat, PlayerClass requestedClass)
        {
            if (combat == null) return;

            PlayerClassVisualProfile requested = GetProfile(requestedClass);
            PlayerClassVisualProfile effective = requested;
            if (requested == null || !requested.GameplayReady)
            {
                effective = GetProfile(PlayerClass.YoungDriller);
                if (_warnedFallbacks.Add(requestedClass))
                    Debug.LogWarning("Player class " + requestedClass +
                        " has incomplete visual art; using the full Young Driller visual profile.");
            }

            if (effective == null)
            {
                Debug.LogWarning("PlayerClassVisualLibrary has no Young Driller fallback profile.");
                return;
            }

            // Gameplay may fall back to the complete Young Driller animation set while a class is
            // still waiting on sheets, but the HUD should continue to show the class the player
            // actually chose. Only fall back for the portrait when that class has none of its own.
            if (combat.PlayerData != null)
                combat.PlayerData.Portrait = requested != null && requested.Portrait != null
                    ? requested.Portrait
                    : effective.Portrait;

            WorldActorVisual visual = combat.GetComponent<WorldActorVisual>();
            if (visual == null)
            {
                Debug.LogWarning("Player has no WorldActorVisual for class art.");
                return;
            }

            visual.ActorSprite = effective.RestingSprite;
            visual.ApplyVisual();

            Animator animator = visual.AttachAnimator(effective.Controller);
            if (animator == null) return;

            combat.PlayerAnimator = animator;
            animator.Play("Idle", 0, 0f);
            animator.Update(0f);
        }
    }
}
