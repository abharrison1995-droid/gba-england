using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.World;

namespace GBHEngland.UI
{
    /// <summary>
    /// MAP OF BRITAIN — a Win95 window drawing the chunk graph: one node per chunk reachable
    /// from where the player is standing, linked by thin edges. Chunks the player has entered
    /// (PlayerSession's visited set, restored from the save) show their name; the rest read
    /// "???". The current chunk is the cornflower-blue node with a YOU ARE HERE marker.
    ///
    /// Entirely code-built from the same QuestUIBuilder/Win95Skin primitives as the journal,
    /// so no scene or prefab changes are needed. Opened from the bag's MAP OF BRITAIN button;
    /// dismissed via the X, clicking the dimmer, or E/M on desktop. Pauses while open.
    ///
    /// The graph is walked live from ChunkManager.CurrentChunkData through the N/S/E/W links —
    /// nothing is cached, so a newly authored chunk appears the moment it is linked and entered.
    /// </summary>
    public class MapOfBritainUI : MonoBehaviour
    {
        private static MapOfBritainUI _instance;

        private GameObject _root;
        private RectTransform _mapArea;   // the sunken field nodes and edges are drawn into

        /// <summary>The paper doll's early-Windows cornflower blue, reused for the "you are here" node.</summary>
        private static readonly Color CurrentBlue = new Color(0.392f, 0.584f, 0.929f); // #6495ED

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("MapOfBritainUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<MapOfBritainUI>();
                _instance.BuildUI();
            }
            _instance.OpenInternal();
        }

        /// <summary>Hotkey-style toggle, matching the journal: refuses to stack on another paused menu.</summary>
        public static void Toggle()
        {
            if (IsOpen)
            {
                _instance.Close();
                return;
            }
            if (Systems.PauseManager.IsPaused) return;
            Open();
        }

        private void OpenInternal()
        {
            if (IsOpen) return;

            // Standing in a chunk is having visited it — covers any entry path that never
            // marked (scene-autoload when debugging, legacy fallbacks).
            var chunkMgr = ChunkManager.Instance;
            if (chunkMgr != null && chunkMgr.CurrentChunkData != null)
                PlayerSession.Instance?.MarkChunkVisited(chunkMgr.CurrentChunkData.ChunkName);

            _root.SetActive(true);
            Systems.PauseManager.Push();
            // Populate measures the now-fullscreen field's live rect, so layout must be real
            // first — ForceUpdateCanvases computes it synchronously, no waiting a frame.
            Canvas.ForceUpdateCanvases();
            Populate();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        /// <summary>
        /// BACK returns to the bag the map was opened from: close (pops the map's pause),
        /// then reopen the inventory (pushes its own) — the same pause balance the quest
        /// popup uses when jumping to the journal. X / dimmer / E-M still close to gameplay.
        /// </summary>
        private void Back()
        {
            Close();
            var inv = FindObjectOfType<InventoryController>(true);
            if (inv != null && !inv.IsOpen)
                inv.ToggleInventory();
        }

        private void Update()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (IsOpen && (Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.M)))
                Close();
#endif
        }

        // ── Drawing ─────────────────────────────────────────────────────────────────────

        private void Populate()
        {
            foreach (Transform child in _mapArea)
                Destroy(child.gameObject);

            var chunkMgr = ChunkManager.Instance;
            MapChunkData current = chunkMgr != null ? chunkMgr.CurrentChunkData : null;

            if (current == null)
            {
                var empty = QuestUIBuilder.CreateTMP("Empty", _mapArea, "No world loaded yet.",
                    Win95Skin.FieldText, 20, TextAlignmentOptions.Center, FontStyles.Italic);
                QuestUIBuilder.Stretch(empty.gameObject, Vector2.zero, Vector2.one);
                return;
            }

            // BFS the neighbour graph from the chunk the player is standing in. Coordinates
            // come from each asset — links and grid positions are trusted to agree, as the
            // rest of the game already assumes.
            var nodes = new Dictionary<MapChunkData, Vector2IntCoords>();
            var queue = new Queue<MapChunkData>();
            nodes[current] = current.Coordinates;
            queue.Enqueue(current);
            while (queue.Count > 0)
            {
                MapChunkData c = queue.Dequeue();
                foreach (MapChunkData n in Neighbours(c))
                {
                    if (nodes.ContainsKey(n)) continue;
                    nodes[n] = n.Coordinates;
                    queue.Enqueue(n);
                }
            }

            // Layout: centre the graph's bounding box on the field's midpoint, spreading the
            // cells across the live (now fullscreen-sized) field measured in OpenInternal.
            // The 700x500 fallback covers a degenerate rect rather than a real one.
            int minX = int.MaxValue, maxX = int.MinValue, minY = int.MaxValue, maxY = int.MinValue;
            foreach (var pair in nodes)
            {
                minX = Mathf.Min(minX, pair.Value.X);
                maxX = Mathf.Max(maxX, pair.Value.X);
                minY = Mathf.Min(minY, pair.Value.Y);
                maxY = Mathf.Max(maxY, pair.Value.Y);
            }

            float spanX = Mathf.Max(1, maxX - minX);
            float spanY = Mathf.Max(1, maxY - minY);
            Rect fieldRect = _mapArea.rect;
            float fieldW = fieldRect.width > 100f ? fieldRect.width * 0.9f : 700f;
            float fieldH = fieldRect.height > 100f ? fieldRect.height * 0.9f : 500f;
            const float MaxCellX = 320f, MaxCellY = 240f;
            float cellX = Mathf.Min(MaxCellX, fieldW / spanX);
            float cellY = Mathf.Min(MaxCellY, fieldH / spanY);
            float midX = (minX + maxX) * 0.5f;
            float midY = (minY + maxY) * 0.5f;

            Vector2 NodePos(Vector2IntCoords c) => new Vector2((c.X - midX) * cellX, (c.Y - midY) * cellY);

            // Edges first so the nodes overpaint their ends. Each unordered pair draws once.
            var drawnEdges = new HashSet<long>();
            foreach (var pair in nodes)
            {
                foreach (MapChunkData n in Neighbours(pair.Key))
                {
                    if (!nodes.ContainsKey(n)) continue;
                    int a = pair.Key.GetInstanceID(), b = n.GetInstanceID();
                    long key = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
                    if (!drawnEdges.Add(key)) continue;
                    DrawEdge(NodePos(pair.Value), NodePos(nodes[n]));
                }
            }

            foreach (var pair in nodes)
                DrawNode(pair.Key, NodePos(pair.Value), pair.Key == current);
        }

        private static IEnumerable<MapChunkData> Neighbours(MapChunkData c)
        {
            if (c == null) yield break;
            if (c.NorthChunk != null) yield return c.NorthChunk;
            if (c.SouthChunk != null) yield return c.SouthChunk;
            if (c.EastChunk != null) yield return c.EastChunk;
            if (c.WestChunk != null) yield return c.WestChunk;
        }

        /// <summary>A thin bar between two node centres. Rotated, so a non-orthogonal link still connects.</summary>
        private void DrawEdge(Vector2 from, Vector2 to)
        {
            GameObject edge = QuestUIBuilder.CreateImage("Edge", _mapArea, Win95Skin.Shadow);
            var rt = edge.GetComponent<RectTransform>();
            Vector2 d = to - from;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = (from + to) * 0.5f;
            rt.sizeDelta = new Vector2(d.magnitude, 6f);
            rt.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            edge.GetComponent<Image>().raycastTarget = false;
        }

        private void DrawNode(MapChunkData chunk, Vector2 pos, bool isCurrent)
        {
            var session = PlayerSession.Instance;
            bool visited = isCurrent
                || (session != null && session.IsChunkVisited(chunk.ChunkName));

            GameObject node = QuestUIBuilder.CreateImage("Node_" + (chunk.ChunkName ?? "unnamed"), _mapArea,
                isCurrent ? CurrentBlue : visited ? Win95Skin.Face : Win95Skin.Shadow);
            Win95Skin.AddBevel((RectTransform)node.transform, sunken: false);
            var rt = node.GetComponent<RectTransform>();
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = new Vector2(150f, 72f);
            node.GetComponent<Image>().raycastTarget = false;

            string label = visited ? chunk.ChunkName ?? "?" : "???";
            Color textColor = isCurrent ? Color.white : visited ? Win95Skin.FieldText : Win95Skin.Face;
            var tmp = QuestUIBuilder.CreateTMP("Label", node.transform, label, textColor, 16,
                TextAlignmentOptions.Center, isCurrent ? FontStyles.Bold : FontStyles.Normal);
            QuestUIBuilder.Stretch(tmp.gameObject, Vector2.zero, Vector2.one);
            tmp.enableWordWrapping = true;

            if (isCurrent)
            {
                var here = QuestUIBuilder.CreateTMP("Here", node.transform, "YOU ARE HERE",
                    Win95Skin.HeaderYellow, 13, TextAlignmentOptions.Center, FontStyles.Bold);
                var hrt = here.rectTransform;
                hrt.anchorMin = new Vector2(0f, 1f);
                hrt.anchorMax = new Vector2(1f, 1f);
                hrt.pivot = new Vector2(0.5f, 0f);
                hrt.anchoredPosition = new Vector2(0f, 3f);
                hrt.sizeDelta = new Vector2(0f, 18f);
            }
        }

        // ── Chrome ──────────────────────────────────────────────────────────────────────

        private void BuildUI()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "MapOfBritainCanvas", 570);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("MapPanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            // Near-fullscreen like the bag/wiki windows — a thin screen margin on every side,
            // so the map fills a phone display instead of floating as a 760x620 box.
            prt.anchorMin = new Vector2(0.01f, 0.02f);
            prt.anchorMax = new Vector2(0.99f, 0.98f);
            prt.offsetMin = Vector2.zero;
            prt.offsetMax = Vector2.zero;

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0f, 1f);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0f, 52f);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "MAP OF BRITAIN",
                Win95Skin.TitleText, 24, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            GameObject field = QuestUIBuilder.CreateImage("MapField", panel.transform, Win95Skin.SlotFill);
            Win95Skin.AddBevel((RectTransform)field.transform, sunken: true);
            _mapArea = field.GetComponent<RectTransform>();
            _mapArea.anchorMin = Vector2.zero;
            _mapArea.anchorMax = Vector2.one;
            _mapArea.offsetMin = new Vector2(16f, 64f);   // bottom strip holds the BACK button
            _mapArea.offsetMax = new Vector2(-16f, -60f); // clear of the header

            // Back to the bag the map was opened from; X/dimmer/E-M close to gameplay instead.
            GameObject back = QuestUIBuilder.CreateButton("BackButton", panel.transform, "BACK", Back);
            var brt = back.GetComponent<RectTransform>();
            brt.anchorMin = brt.anchorMax = new Vector2(0f, 0f);
            brt.pivot = new Vector2(0f, 0f);
            brt.anchoredPosition = new Vector2(16f, 12f);
            brt.sizeDelta = new Vector2(160f, 40f);

            _root.SetActive(false);
        }
    }
}
