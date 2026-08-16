using UnityEngine;

namespace GBHEngland.World
{
    /// <summary>
    /// Keeps a texture tiling at a fixed real-world density however the object is scaled.
    ///
    /// Unity's built-in Quad and Plane meshes carry UVs that run 0-1 across the whole surface, so
    /// stretching the transform stretches the texture with it. A 2m x 20m path built from a Quad
    /// shows one smeared copy of its texture rather than ten tiles. This reads the renderer's world
    /// size and writes _MainTex_ST so the tiling follows the scale instead.
    ///
    /// Written through a MaterialPropertyBlock, not the material, so every instance can be a
    /// different size while still sharing one material asset. Nothing is instanced and no material
    /// leaks.
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(MeshRenderer))]
    [AddComponentMenu("GBH/World/Tiling Surface")]
    public class TilingSurface : MonoBehaviour
    {
        /// <summary>
        /// Which two local axes to tile across. Auto works out the flat plane a Quad/Plane spans by
        /// finding the mesh's degenerate axis -- but a Cube has no degenerate axis (all three bounds
        /// are non-zero), so a wall built from one must say explicitly which face it's texturing:
        /// XY for a wall's front face (width x height, ignoring depth).
        /// </summary>
        public enum TilingPlane { Auto, XY, XZ, YZ }

        [Tooltip("How many times the texture repeats per metre. 0.5 means one copy every 2 metres.")]
        public float TilesPerMetre = 0.5f;

        [Tooltip("Extra tiling on the surface's second axis. Leave at 1 to keep the texture square.")]
        public float CrossAxisMultiplier = 1f;

        [Tooltip("Auto detects a flat Quad/Plane's spanning axes. Set explicitly for a solid mesh like a Cube.")]
        public TilingPlane Plane = TilingPlane.Auto;

        private MeshRenderer _renderer;
        private MaterialPropertyBlock _block;

        private void OnEnable()
        {
            Apply();
        }

        private void OnValidate()
        {
            Apply();
        }

#if UNITY_EDITOR
        // Live feedback while dragging the scale handle. OnValidate does not fire for transform
        // changes, and there is no cheap change notification for lossyScale. Compiled out of builds
        // entirely, and the play-mode guard keeps it off the hot path inside the editor too.
        private void Update()
        {
            if (Application.isPlaying) return;
            Apply();
        }
#endif

        /// <summary>
        /// Recompute and push the tiling. Call this after changing the scale from code.
        /// </summary>
        public void Apply()
        {
            if (_renderer == null) _renderer = GetComponent<MeshRenderer>();
            if (_renderer == null) return;

            var filter = GetComponent<MeshFilter>();
            var mesh = filter != null ? filter.sharedMesh : null;
            if (mesh == null) return;

            Vector3 size = mesh.bounds.size;
            Vector3 scale = transform.lossyScale;
            Vector3 world = new Vector3(
                Mathf.Abs(size.x * scale.x),
                Mathf.Abs(size.y * scale.y),
                Mathf.Abs(size.z * scale.z));

            float u, v;
            if (Plane == TilingPlane.XY) { u = world.x; v = world.y; }
            else if (Plane == TilingPlane.XZ) { u = world.x; v = world.z; }
            else if (Plane == TilingPlane.YZ) { u = world.y; v = world.z; }
            else
            {
                // Work out which two local axes the surface actually spans. A Quad spans X and Y; a
                // Plane spans X and Z with a degenerate Y. Taking the first two non-degenerate axes
                // in X, Y, Z order picks (X,Y) for the Quad and (X,Z) for the Plane, which is the
                // order their UVs run in both cases.
                u = 0f;
                v = 0f;
                int found = 0;
                for (int i = 0; i < 3 && found < 2; i++)
                {
                    if (world[i] <= 0.0001f) continue;
                    if (found == 0) u = world[i];
                    else v = world[i];
                    found++;
                }
                if (found < 2) return;
            }

            float density = Mathf.Max(0.0001f, TilesPerMetre);
            float cross = Mathf.Max(0.0001f, CrossAxisMultiplier);

            if (_block == null) _block = new MaterialPropertyBlock();
            _renderer.GetPropertyBlock(_block);
            _block.SetVector("_MainTex_ST", new Vector4(u * density, v * density * cross, 0f, 0f));
            _renderer.SetPropertyBlock(_block);
        }
    }
}
