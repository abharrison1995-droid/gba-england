using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;

namespace GBHEngland.World
{
    /// <summary>
    /// A dropped item lying on the ground: a billboarded icon with a one-shot Interactable
    /// ("Take X") that returns the item to the bag and destroys itself.
    ///
    /// Transient by design. The pickup is parented to the live chunk, so it dies on chunk
    /// unload like every other transient thing the chunk owns; the lifetime timer is the
    /// backstop for chunks the player lingers in. Never written to the save — persistence
    /// would contradict the despawn semantics.
    /// </summary>
    public class DroppedItemPickup : MonoBehaviour
    {
        /// <summary>Seconds before an unclaimed drop is cleaned up.</summary>
        public float LifetimeSeconds = 120f;

        private ItemData _item;
        private int _quantity;
        private float _expiresAt;

        /// <summary>
        /// Drops <paramref name="quantity"/> of the item at the position. The caller removes
        /// the item from the bag first (RemoveItem's all-or-nothing check), so by the time
        /// this runs the unit genuinely left the inventory.
        /// </summary>
        public static DroppedItemPickup Spawn(ItemData item, int quantity, Vector3 position)
        {
            if (item == null || quantity <= 0) return null;

            var go = new GameObject($"Dropped_{item.ItemID}");
            go.transform.position = position;

            // Parent to the live chunk so the drop dies on chunk unload. No current chunk
            // (title-screen edge cases) means scene root, where the timer still cleans up.
            var chunks = ChunkManager.Instance;
            if (chunks != null && chunks.CurrentChunkInstance != null)
                go.transform.SetParent(chunks.CurrentChunkInstance.transform, true);

            var pickup = go.AddComponent<DroppedItemPickup>();
            pickup._item = item;
            pickup._quantity = quantity;
            pickup._expiresAt = Time.time + pickup.LifetimeSeconds;
            pickup.BuildVisual();
            pickup.BuildInteractable();
            return pickup;
        }

        private void Update()
        {
            if (Time.time >= _expiresAt)
                Destroy(gameObject);
        }

        private void BuildVisual()
        {
            var renderer = gameObject.AddComponent<SpriteRenderer>();
            renderer.sprite = _item.Icon;

            // Ground clutter, not a character billboard: icons are 48 px/unit, so this reads
            // as a small thing on the floor rather than a person-sized poster.
            transform.localScale = Vector3.one * 0.35f;
            gameObject.AddComponent<SpriteBillboard>();
        }

        private void BuildInteractable()
        {
            var interactable = gameObject.AddComponent<Interactable>();
            interactable.Prompt = $"Take {_item.ItemName}";
            interactable.InteractRange = 2.75f;  // same reach as bins
            interactable.Reusable = false;       // one-shot: taken once, gone
            interactable.OnInteract.AddListener(Collect);
        }

        private void Collect()
        {
            PlayerSession.Instance?.AddItem(_item, _quantity);
            Destroy(gameObject);
        }
    }
}
