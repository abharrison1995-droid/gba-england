using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>One wire in the hotwire minigame: how many taps it needs to come loose.</summary>
    public class HotwireWire
    {
        public int TapsRemaining;
        public bool Banked;
    }

    /// <summary>
    /// The car-theft minigame: a handful of wires, a countdown, and a tap each to work something
    /// loose before the alarm goes off. Modelled on <see cref="PickpocketMenuUI"/> — code-built on
    /// its own overlay canvas, so nothing has to be wired in the scene.
    ///
    /// Deliberately **not** a pause, exactly like the pickpocket menu: a paused world with a
    /// running clock is a contradiction and a paused world with a stopped clock is a free win. The
    /// timer uses <c>Time.deltaTime</c> on purpose — if something else pauses the world mid-attempt,
    /// the attempt pauses with it.
    ///
    /// Every way out — banking the lot, CLOSE, the dimmer, walking away, the clock running out —
    /// funnels through <see cref="Close"/>, which is what keeps banked wires banked and stops two
    /// exits firing the callback twice. The callback hands the caller both outcomes: whether the
    /// car was hotwired, and whether the clock ran out (the alarm).
    ///
    /// The car's transform is tracked so the attempt closes if the player walks off or the car is
    /// destroyed mid-attempt — the same proximity rule as the pickpocket menu. The caller keeps the
    /// car held while the menu is open, so this is the only thing that needs to watch distance.
    /// </summary>
    public class HotwireMenuUI : MonoBehaviour
    {
        private static HotwireMenuUI _instance;

        private GameObject _panelRoot;
        private TextMeshProUGUI _titleText;
        private TextMeshProUGUI _timerText;
        private Transform _rowContainer;

        private List<HotwireWire> _wires;
        private Transform _car;
        private float _timeLeft;
        private bool _completed;
        private bool _expired;
        private Action<bool, bool> _onClosed;

        public static bool IsOpen => _instance != null && _instance._panelRoot != null
                                     && _instance._panelRoot.activeSelf;

        /// <summary>
        /// Opens a hotwire attempt on a car. <paramref name="onClosed"/> is handed
        /// <c>(completed, expired)</c>: completed when every wire was banked, expired when the
        /// clock ran out — the caller's cue to raise the alarm.
        /// </summary>
        public static void Show(string title, int wires, float seconds, Transform car,
            Action<bool, bool> onClosed = null)
        {
            if (_instance == null)
            {
                var go = new GameObject("HotwireMenuUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<HotwireMenuUI>();
                _instance.BuildUI();
            }
            _instance.Open(title, wires, seconds, car, onClosed);
        }

        private void Open(string title, int wires, float seconds, Transform car,
            Action<bool, bool> onClosed)
        {
            if (IsOpen) return;

            _wires = new List<HotwireWire>();
            for (int i = 0; i < Mathf.Max(1, wires); i++)
            {
                _wires.Add(new HotwireWire
                {
                    TapsRemaining = UnityEngine.Random.Range(EKVibe.HotwireMinTaps, EKVibe.HotwireMaxTaps + 1),
                });
            }

            _car = car;
            _onClosed = onClosed;
            _completed = false;
            _expired = false;
            _timeLeft = Mathf.Max(1f, seconds);

            _titleText.text = title;
            RefreshTimerLabel();

            foreach (Transform child in _rowContainer)
                Destroy(child.gameObject);
            foreach (HotwireWire wire in _wires)
                BuildRow(wire);

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

            // Walking off, or the car being destroyed under you, ends the attempt cleanly — the
            // same rule as the pickpocket menu. The car is held while the menu is open, so this is
            // the only distance check needed.
            if (_car == null)
            {
                Close();
                return;
            }

            var player = ExiledAlvaston.Combat.CombatController.Instance;
            if (player != null)
            {
                Vector3 a = player.transform.position;
                Vector3 b = _car.position;
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
            _car = null;

            Action<bool, bool> cb = _onClosed;
            _onClosed = null;
            cb?.Invoke(_completed, _expired);
        }

        /// <summary>
        /// One tap: work the wire looser, and bank it once it is free. Banking is immediate and
        /// per wire, so time running out costs the player only what was still stuck.
        /// </summary>
        private void Tap(HotwireWire wire, GameObject row)
        {
            if (wire == null || wire.Banked) return;

            wire.TapsRemaining--;
            if (wire.TapsRemaining > 0)
            {
                UpdateRowLabel(wire, row);
                return;
            }

            wire.Banked = true;
            MarkRowBanked(row);

            foreach (HotwireWire other in _wires)
                if (!other.Banked) return;

            _completed = true;
            Close();   // every wire free — hotwired
        }

        // ---------- one-time UI construction ----------

        private void BuildUI()
        {
            var canvasGO = new GameObject("HotwireCanvas");
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

            GameObject panel = CreateImage("HotwirePanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(640, 480);
            panel.GetComponent<Image>().raycastTarget = true;

            GameObject header = CreateImage("Header", panel.transform, Win95Skin.TitleBar);
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

        private void BuildRow(HotwireWire wire)
        {
            GameObject row = CreateImage("WireRow", _rowContainer, Win95Skin.SlotFill);
            Win95Skin.AddBevel((RectTransform)row.transform, sunken: true);
            var rrt = row.GetComponent<RectTransform>();
            rrt.sizeDelta = new Vector2(0, 72);

            var name = CreateTMP("Name", row.transform, "Wire", Win95Skin.FieldText, 24,
                TextAlignmentOptions.Left);
            Stretch(name.gameObject, Vector2.zero, Vector2.one);
            var nrt = name.GetComponent<RectTransform>();
            nrt.offsetMin = new Vector2(16, 0);
            nrt.offsetMax = new Vector2(-160, 0);

            GameObject tap = CreateButton("TapButton", row.transform, TapLabel(wire),
                () => Tap(wire, row));
            var trt = tap.GetComponent<RectTransform>();
            trt.anchorMin = trt.anchorMax = new Vector2(1, 0.5f);
            trt.pivot = new Vector2(1, 0.5f);
            trt.anchoredPosition = new Vector2(-12, 0);
            trt.sizeDelta = new Vector2(130, 52);

            if (wire.Banked) MarkRowBanked(row);
        }

        private static string TapLabel(HotwireWire wire) =>
            wire.TapsRemaining > 1 ? $"TAP x{wire.TapsRemaining}" : "TAP";

        private static void UpdateRowLabel(HotwireWire wire, GameObject row)
        {
            if (row == null) return;
            var btn = row.GetComponentInChildren<Button>(true);
            if (btn == null) return;
            var label = btn.GetComponentInChildren<TextMeshProUGUI>();
            if (label != null) label.text = TapLabel(wire);
        }

        private static void MarkRowBanked(GameObject row)
        {
            if (row == null) return;
            var btn = row.GetComponentInChildren<Button>(true);
            if (btn != null && btn.interactable)
            {
                btn.interactable = false;
                var label = btn.GetComponentInChildren<TextMeshProUGUI>();
                if (label != null) label.text = "CUT";
                var img = btn.GetComponent<Image>();
                if (img != null) img.color = Win95Skin.Shadow;
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
            GameObject go = CreateImage(name, parent, Win95Skin.Face);
            var btn = go.AddComponent<Button>();
            Win95Skin.StyleButton(btn);
            btn.onClick.AddListener(onClick);
            var tmp = CreateTMP("Label", go.transform, label, Win95Skin.FieldText, 22,
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