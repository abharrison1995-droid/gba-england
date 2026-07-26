using UnityEngine;
using UnityEngine.Events;
using System.Collections.Generic;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Anything the player can walk up to and press Interact on — chests, doors, NPCs.
    /// Registers itself in a static list while enabled; PlayerInteractor polls that list
    /// by distance each frame, so no colliders, tags, rigidbodies or trigger events are
    /// involved. What actually happens on interact is just a UnityEvent, so chests/NPCs
    /// don't need their own subclass, just their own listener.
    /// </summary>
    public class Interactable : MonoBehaviour
    {
        /// <summary>Every enabled Interactable in the scene. Polled by PlayerInteractor.</summary>
        public static readonly List<Interactable> Active = new List<Interactable>();

        public string Prompt = "Interact";
        [Tooltip("If false, this stops being interactable after the first use (e.g. a chest).")]
        public bool Reusable = true;
        [Tooltip("How close (horizontally) the player must stand to interact.")]
        public float InteractRange = 2.5f;

        public UnityEvent OnInteract = new UnityEvent();

        private bool _used;

        public bool CanInteract => Reusable || !_used;

        private void OnEnable()
        {
            if (!Active.Contains(this))
                Active.Add(this);
        }

        private void OnDisable()
        {
            Active.Remove(this);
        }

        /// <summary>Called by PlayerInteractor when the player presses Interact while this is the nearest option.</summary>
        public void Interact()
        {
            if (!CanInteract) return;
            _used = true;
            OnInteract?.Invoke();
        }
    }
}
