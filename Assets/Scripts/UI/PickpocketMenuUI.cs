using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>One pocket in the minigame: what is in it and how much work it is to get out.</summary>
    public class PickpocketSlot
    {
        public string Name;
        /// <summary>Null for the pounds slot, which pays into the wallet rather than the bag.</summary>
        public ItemData Item;
        public int Quantity;
        public int Pounds;

        public int TapsRemaining;
        public bool Banked;
    }

    /// <summary>
    /// The pickpocket minigame: a handful of pockets, a countdown, and a tap each to work something
    /// loose before the mark notices.
    ///
    /// Code-built on its own overlay canvas, like <see cref="LootMenuUI"/>, so nothing has to be
    /// wired in the scene. It is deliberately **not** a pause: `PauseManager.Push`/`Pop` are the one
    /// thing not copied from the loot menu, because a paused world with a running clock is a
    /// contradiction and a paused world with a stopped clock is a free win. The timer uses
    /// <c>Time.deltaTime</c> on purpose — if something else pauses the world mid-attempt, the
    /// attempt pauses with it.
    ///
    /// Every way out — banking the lot, CLOSE, the dimmer, walking away, the victim dying, the clock
    /// running out — funnels through <see cref="Close"/>, which is what keeps banked loot banked and
    /// stops two exits firing the callback twice.
    /// </summary>
    public class PickpocketMenuUI : MonoBehaviour
    {
        private static PickpocketMenuUI _instance;

        private GameObject _panelRoot;
        private TextMeshProUGUI _titleText;
        private TextMeshProUGUI _timerText;
        private Transform _rowContainer;

        private List<PickpocketSlot> _slots;
        private Transform _victim;
        private float _timeLeft;
        private bool _expired;
        private Action<bool> _onClosed;

        public static bool IsOpen => _instance != null && _instance._panelRoot != null
                                     && _instance._panelRoot.activeSelf;

        /// <summary>
        /// Opens an attempt on <paramref name="victim"/>. <paramref name="onClosed"/> is handed true
        /// when the clock ran out, which is the caller's cue to spike the wanted level.
        /// </summary>
        public static void Show(string title, List<PickpocketSlot> slots, Transform victim,
            Action<bool> onClosed = null)
        {
            if (_instance == null)
            {
                var go = new GameObject("PickpocketMenuUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<PickpocketMenuUI>();
                _instance.BuildUI();
            }
            _instance.Open(title, slots, victim, onClosed);
        }

        private void Open(string title, List<PickpocketSlot> slots, Transform victim, Action<bool> onClosed)
        {
            if (IsOpen) return;

            _slots = slots ?? new List<PickpocketSlot>();
            _victim = victim;
            _onClosed = onClosed;
            _expired = false;
            _timeLeft = EKVibe.PickpocketSeconds;

            _titleText.text = title;
            RefreshTimerLabel();

            foreach (Transform child in _rowContainer)
                Destroy(child.gameObject);
            foreach (PickpocketSlot slot in _slots)
                BuildRow(slot);

            _panelRoot.SetActive(true);
        }

        private void Update()
        {
            if (!IsOpen) return;

            // Deliberately Time.deltaTime, not unscaledDeltaTime: pausing the world pauses the
            // attempt. Nothing can pause it from in here — this menu does not push a pause — so the
            // only way that happens is something else taking over, and the attempt waiting is the
            // kinder answer.
            _timeLeft -= Time.deltaTime;
            RefreshTimerLabel();

            if (_timeLeft <= 0f)
            {
                _expired = true;
                Close();
                return;
            }

            // Walking off, or the mark dying under you, ends the attempt and keeps what was banked.
            if (_victim == null)
            {
                Close();
                return;
            }

            var player = ExiledAlvaston.Combat.CombatController.Instance;
            if (player != null)
            {
                Vector3 a = player.transform.position;
                Vector3 b = _victim.position;
                // Horizontal only: the isometric world moves on X/Z and a kerb should not count.
                float dx = a.x - b.x;
                float dz = a.z - b.z;
                if (dx * dx + dz * dz > EKVibe.PickpocketRange * EKVibe.PickpocketRange)
                    Close();
            }
        }

        private void RefreshTimerLabel()
        {
            if (_timerText == null) return;
            _timerText.text = Mathf.Max(0f, _timeLeft).ToString("0.0") + "s";
        }

        /// <summary>
        /// The single exit. Guarded by <see cref="IsOpen"/> so the several things that can call it
        /// in the same frame — the clock and a tap, say — only close once, and the callback is
        /// cleared before it is invoked so a handler that reopens the menu cannot re-enter this.
        /// </summary>
        private void Close()
        {
            if (!IsOpen) return;
            _panelRoot.SetActive(false);
            _victim = null;

            Action<bool> cb = _onClosed;
            _onClosed = null;
            cb?.Invoke(_expired);
        }

        /// <summary>
        /// One tap: work the pocket looser, and bank it once it is free. Banking is immediate and
        /// per pocket, so time running out costs the player only what was still stuck.
        /// </summary>
        private void Tap(PickpocketSlot slot, GameObject row)
        {
            if (slot == null || slot.Banked) return;

            slot.TapsRemaining--;
            if (slot.TapsRemaining > 0)
            {
                UpdateRowLabel(slot, row);
                return;
            }

            slot.Banked = true;

            var session = PlayerSession.Instance;
            if (session != null)
            {
                if (slot.Item != null) session.AddItem(slot.Item, Mathf.Max(1, slot.Quantity));
                if (slot.Pounds > 0) session.AddPounds(slot.Pounds);
            }

            MarkRowBanked(row);

            foreach (PickpocketSlot other in _slots)
                if (!other.Banked) return;

            Close();   // nothing left in their pockets
        }

        // ---------- one-time UI construction ----------

        private void BuildUI()
        {
            var canvasGO = new GameObject("PickpocketCanvas");
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 500;
            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGO.AddComponent<GraphicRaycaster>();

            GameObject dim = CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.4f));
            Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);

            _panelRoot = dim;

            GameObject panel = CreateImage("PickpocketPanel", dim.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(640, 480);
            panel.GetComponent<Image>().raycastTarget = true;

            GameObject header = CreateImage("Header", panel.transform, EKVibe.ParchmentDark);
            Stretch(header, new Vector2(0, 1), Vector2.one);
            var hrt = header.GetComponent<RectTransform>();
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 64);

            _titleText = CreateTMP("Title", header.transform, "", EKVibe.TextLight, 30,
                TextAlignmentOptions.Left);
            Stretch(_titleText.gameObject, Vector2.zero, Vector2.one);
            _titleText.GetComponent<RectTransform>().offsetMin = new Vector2(20, 0);

            _timerText = CreateTMP("Timer", header.transform, "", EKVibe.TextLight, 30,
                TextAlignmentOptions.Right);
            Stretch(_timerText.gameObject, Vector2.zero, Vector2.one);
            _timerText.GetComponent<RectTransform>().offsetMax = new Vector2(-20, 0);

            var containerGO = new GameObject("Rows", typeof(RectTransform));
            containerGO.transform.SetParent(panel.transform, false);
            var crt = containerGO.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0, 0);
            crt.anchorMax = new Vector2(1, 1);
            crt.offsetMin = new Vector2(20, 90);
            crt.offsetMax = new Vector2(-20, -74);
            var layout = containerGO.AddComponent<VerticalLayoutGroup>();
            layout.spacing = 10;
            layout.childControlHeight = false;
            layout.childControlWidth = true;
            layout.childForceExpandHeight = false;
            layout.childAlignment = TextAnchor.UpperCenter;
            _rowContainer = containerGO.transform;

            GameObject closeBtn = CreateButton("CloseButton", panel.transform, "CLOSE", Close);
            var clrt = closeBtn.GetComponent<RectTransform>();
            clrt.anchorMin = clrt.anchorMax = new Vector2(0.5f, 0f);
            clrt.pivot = new Vector2(0.5f, 0f);
            clrt.anchoredPosition = new Vector2(0, 16);
            clrt.sizeDelta = new Vector2(240, 60);

            _panelRoot.SetActive(false);
        }

        private void BuildRow(PickpocketSlot slot)
        {
            GameObject row = CreateImage("PocketRow", _rowContainer, EKVibe.SlotFrame);
            var rrt = row.GetComponent<RectTransform>();
            rrt.sizeDelta = new Vector2(0, 72);

            var name = CreateTMP("Name", row.transform, slot.Name, EKVibe.TextLight, 24,
                TextAlignmentOptions.Left);
            Stretch(name.gameObject, Vector2.zero, Vector2.one);
            var nrt = name.GetComponent<RectTransform>();
            nrt.offsetMin = new Vector2(16, 0);
            nrt.offsetMax = new Vector2(-160, 0);

            GameObject tap = CreateButton("TapButton", row.transform, TapLabel(slot),
                () => Tap(slot, row));
            var trt = tap.GetComponent<RectTransform>();
            trt.anchorMin = trt.anchorMax = new Vector2(1, 0.5f);
            trt.pivot = new Vector2(1, 0.5f);
            trt.anchoredPosition = new Vector2(-12, 0);
            trt.sizeDelta = new Vector2(130, 52);

            if (slot.Banked) MarkRowBanked(row);
        }

        private static string TapLabel(PickpocketSlot slot) =>
            slot.TapsRemaining > 1 ? $"TAP x{slot.TapsRemaining}" : "TAP";

        private static void UpdateRowLabel(PickpocketSlot slot, GameObject row)
        {
            if (row == null) return;
            var btn = row.GetComponentInChildren<Button>(true);
            if (btn == null) return;
            var label = btn.GetComponentInChildren<TextMeshProUGUI>();
            if (label != null) label.text = TapLabel(slot);
        }

        private static void MarkRowBanked(GameObject row)
        {
            if (row == null) return;
            var btn = row.GetComponentInChildren<Button>(true);
            if (btn != null && btn.interactable)
            {
                btn.interactable = false;
                var label = btn.GetComponentInChildren<TextMeshProUGUI>();
                if (label != null) label.text = "NICKED";
                var img = btn.GetComponent<Image>();
                if (img != null) img.color = EKVibe.SlotEmpty;
            }
        }

        // ---------- tiny builders ----------

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = color;
            return go;
        }

        private static GameObject CreateButton(string name, Transform parent, string label,
            UnityEngine.Events.UnityAction onClick)
        {
            GameObject go = CreateImage(name, parent, EKVibe.ButtonBrown);
            var btn = go.AddComponent<Button>();
            btn.onClick.AddListener(onClick);
            var tmp = CreateTMP("Label", go.transform, label, EKVibe.TextLight, 22,
                TextAlignmentOptions.Center);
            Stretch(tmp.gameObject, Vector2.zero, Vector2.one);
            return go;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions align)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = align;
            tmp.raycastTarget = false;
            return tmp;
        }

        private static void Stretch(GameObject go, Vector2 anchorMin, Vector2 anchorMax)
        {
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }
    }
}
