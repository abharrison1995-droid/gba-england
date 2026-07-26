using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// EK-style HUD: portrait + bars, combat log, location/time, joystick, action cluster.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        public static UIManager Instance { get; private set; }

        [Header("HUD Panels")]
        public RectTransform TopLeftPortraitPanel;
        public RectTransform BottomCenterQuickSlotPanel;
        public RectTransform RightActionPanel;
        public RectTransform CombatLogPanel;
        public VirtualJoystick Joystick;

        [Header("Player HUD")]
        public Image PlayerPortrait;
        public Image PlayerHealthFill;
        public Image PlayerManaFill;
        public Image PlayerConcealmentFill;
        [Tooltip("Numeric \"current / max\" readouts drawn over the bars. Auto-built at runtime if left empty.")]
        public TextMeshProUGUI PlayerHealthText;
        public TextMeshProUGUI PlayerManaText;
        public TextMeshProUGUI PlayerConcealmentText;
        public TextMeshProUGUI LevelText;
        public TextMeshProUGUI LocationTimeText;
        public TextMeshProUGUI WantedKnivesText;

        [Header("Combat Log")]
        public TextMeshProUGUI CombatLogText;
        public int MaxCombatLogLines = 5;

        [Header("Companion HUD")]
        public GameObject CompanionHUDTemplate;
        public Transform CompanionHUDContainer;

        [Header("Interact")]
        [Tooltip("Small label showing what's interactable nearby, e.g. 'Open Chest'.")]
        public TextMeshProUGUI InteractPromptText;
        [Tooltip("The Interact HUD button itself — disabled/hidden when nothing is in range.")]
        public GameObject InteractButtonRoot;

        private readonly Queue<string> _logLines = new Queue<string>();
        private float _playerHpMax = 100f;
        private float _playerMpMax = 50f;
        private float _playerConcealmentMax = 100f;

        /// <summary>The 4 spell-slot button backgrounds + labels, refreshed to show bound spells.</summary>
        private readonly Image[] _spellSlotImages = new Image[4];
        private readonly TextMeshProUGUI[] _spellSlotLabels = new TextMeshProUGUI[4];

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            EnsureJournalButton();
            BuildActionButtons();
        }

        private void Update()
        {
            RefreshSpellSlots();
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (Input.GetKeyDown(KeyCode.J))
            {
                var flow = Flow.GameFlowController.Instance;
                if (flow == null || flow.State == Flow.GameFlowState.Playing)
                    QuestJournalUI.Toggle();
            }
#endif
        }

        public void UpdatePlayerHealth(int current, int max)
        {
            _playerHpMax = Mathf.Max(1, max);
            SetBarFill(PlayerHealthFill, current / _playerHpMax);

            EnsureBarLabel(ref PlayerHealthText, PlayerHealthFill, "HPText");
            if (PlayerHealthText != null)
                PlayerHealthText.text = $"{Mathf.Max(0, current)} / {(int)_playerHpMax}";
        }

        public void UpdatePlayerMana(int current, int max)
        {
            _playerMpMax = Mathf.Max(1, max);
            SetBarFill(PlayerManaFill, current / _playerMpMax);

            EnsureBarLabel(ref PlayerManaText, PlayerManaFill, "MPText");
            if (PlayerManaText != null)
                PlayerManaText.text = $"{Mathf.Max(0, current)} / {(int)_playerMpMax}";
        }

        public void UpdatePlayerConcealment(float current, float max)
        {
            _playerConcealmentMax = Mathf.Max(1, max);
            SetBarFill(PlayerConcealmentFill, current / _playerConcealmentMax);

            EnsureBarLabel(ref PlayerConcealmentText, PlayerConcealmentFill, "ConcealmentText");
            if (PlayerConcealmentText != null)
                PlayerConcealmentText.text = $"{Mathf.Max(0, (int)current)} / {(int)_playerConcealmentMax}";
        }

        /// <summary>
        /// Sets a bar's fill to <paramref name="frac"/> (0..1) by resizing the fill rect's width.
        /// The bar fills are plain Images with no sprite, and a spriteless Image ignores
        /// <c>fillAmount</c> (it always draws the full rect) — so we drive the width via the
        /// right anchor instead. fillAmount is left at 1 so that if a sprite is ever assigned it
        /// simply fills the (already width-scaled) rect — no double scaling.
        /// </summary>
        private static void SetBarFill(Image fill, float frac)
        {
            if (fill == null) return;
            frac = Mathf.Clamp01(frac);
            fill.fillAmount = 1f;

            var rt = fill.rectTransform;
            rt.anchorMin = new Vector2(0f, 0f);
            rt.anchorMax = new Vector2(frac, 1f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        /// <summary>
        /// Draws a "current / max" readout centered over a bar so the fill reads as an actual
        /// amount, not just a colored strip. Built lazily over the fill's track the first time
        /// the bar updates (like the other runtime HUD bits), so no scene wiring is required.
        /// </summary>
        private void EnsureBarLabel(ref TextMeshProUGUI label, Image fill, string name)
        {
            if (label != null || fill == null) return;

            Transform track = fill.transform.parent != null ? fill.transform.parent : fill.transform;
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(track, false);       // after the fill child → renders on top
            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;

            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.enableAutoSizing = false;
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.color = EKVibe.TextLight;
            tmp.raycastTarget = false;
            tmp.enableWordWrapping = false;
            tmp.overflowMode = TextOverflowModes.Overflow;
            label = tmp;
        }

        public void SetLevel(int level)
        {
            if (LevelText != null)
                LevelText.text = level.ToString();
        }

        public void SetLocationTime(string location, int day, string clock)
        {
            if (LocationTimeText != null)
                LocationTimeText.text = $"{location}; Day {day}, {clock}";
        }

        public void UpdateKnivesUI(int knives)
        {
            if (WantedKnivesText != null)
                WantedKnivesText.text = $"Knives: {knives}";
        }

        /// <summary>EK combat log style: "> Elite Bandit hits you, 14-7=7"</summary>
        public void LogCombat(string message)
        {
            if (string.IsNullOrEmpty(message)) return;
            if (!message.StartsWith(">"))
                message = "> " + message;

            _logLines.Enqueue(message);
            while (_logLines.Count > MaxCombatLogLines)
                _logLines.Dequeue();

            if (CombatLogText != null)
                CombatLogText.text = string.Join("\n", _logLines);
        }

        /// <summary>Faint transient message near the top of the screen (e.g. the city-magic warning).</summary>
        public void ShowToast(string message, float hold = 1.8f, float fade = 0.7f)
        {
            if (string.IsNullOrEmpty(message)) return;

            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            var go = new GameObject("Toast", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.8f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(960, 60);

            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = message;
            tmp.fontSize = 30;
            tmp.fontStyle = FontStyles.Italic;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.color = new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.85f);
            tmp.raycastTarget = false;

            StartCoroutine(ToastRoutine(go, tmp, hold, fade));
        }

        private IEnumerator ToastRoutine(GameObject go, TextMeshProUGUI tmp, float hold, float fade)
        {
            Color baseC = tmp.color;
            yield return new WaitForSecondsRealtime(hold);
            float t = 0f;
            while (t < fade)
            {
                t += Time.unscaledDeltaTime;
                if (tmp != null)
                {
                    Color c = baseC;
                    c.a = baseC.a * (1f - t / fade);
                    tmp.color = c;
                }
                yield return null;
            }
            if (go != null) Destroy(go);
        }

        public void OnActionButtonPressed(int abilityIndex)
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.TryCastAbility(abilityIndex);
        }

        public void OnAttackPressed()
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.PerformMeleeAttack();
        }

        public void OnInventoryPressed()
        {
            var inv = FindObjectOfType<InventoryController>();
            if (inv != null)
                inv.ToggleInventory();
        }

        public void OnInteractPressed()
        {
            World.PlayerInteractor.Instance?.TryInteract();
        }

        /// <summary>Called by PlayerInteractor whenever the closest in-range Interactable changes.</summary>
        public void SetInteractPrompt(string prompt)
        {
            bool has = !string.IsNullOrEmpty(prompt);

            if (has)
                EnsureInteractUI();

            if (InteractPromptText != null)
                InteractPromptText.text = has ? prompt : "";

            if (InteractButtonRoot != null)
                InteractButtonRoot.SetActive(has);
        }

        /// <summary>
        /// Small always-visible HUD button (top-right, under the location text) that opens
        /// the quest journal. Built at runtime; sits inside HUDPanel so it hides with the HUD.
        /// </summary>
        private void EnsureJournalButton()
        {
            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            if (parent.Find("JournalButton") != null) return;

            var btn = new GameObject("JournalButton", typeof(RectTransform));
            btn.transform.SetParent(parent, false);
            var rt = (RectTransform)btn.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1, 1);
            rt.pivot = new Vector2(1, 1);
            rt.anchoredPosition = new Vector2(-24, -120);
            rt.sizeDelta = new Vector2(72, 56);
            var img = btn.AddComponent<Image>();
            img.color = EKVibe.ButtonBrown;
            btn.AddComponent<Button>().onClick.AddListener(QuestJournalUI.Toggle);

            var labelGO = new GameObject("Label", typeof(RectTransform));
            labelGO.transform.SetParent(btn.transform, false);
            var lrt = (RectTransform)labelGO.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGO.AddComponent<TextMeshProUGUI>();
            tmp.text = "LOG";
            tmp.color = EKVibe.TextLight;
            tmp.fontSize = 20;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.raycastTarget = false;
        }

        /// <summary>
        /// Builds the USE button + prompt label at runtime if the scene doesn't have them
        /// wired (the old editor setup tool is no longer required).
        /// </summary>
        private void EnsureInteractUI()
        {
            if (InteractButtonRoot != null && InteractPromptText != null) return;

            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;

            if (InteractButtonRoot == null)
            {
                var btn = new GameObject("InteractButton", typeof(RectTransform));
                btn.transform.SetParent(parent, false);
                var rt = (RectTransform)btn.transform;
                rt.anchorMin = rt.anchorMax = new Vector2(1, 0);
                rt.pivot = new Vector2(1, 0);
                rt.anchoredPosition = new Vector2(-140, 260);
                rt.sizeDelta = new Vector2(90, 90);
                var img = btn.AddComponent<Image>();
                img.color = EKVibe.ButtonBrown;
                btn.AddComponent<Button>();
                var action = btn.AddComponent<HUDActionButton>();
                action.Kind = HUDActionButton.ActionKind.Interact;

                var labelGO = new GameObject("InteractLabel", typeof(RectTransform));
                labelGO.transform.SetParent(btn.transform, false);
                var lrt = (RectTransform)labelGO.transform;
                lrt.anchorMin = Vector2.zero;
                lrt.anchorMax = Vector2.one;
                lrt.offsetMin = Vector2.zero;
                lrt.offsetMax = Vector2.zero;
                var labelTmp = labelGO.AddComponent<TextMeshProUGUI>();
                labelTmp.text = "USE";
                labelTmp.color = EKVibe.TextLight;
                labelTmp.fontSize = 20;
                labelTmp.alignment = TextAlignmentOptions.Center;
                labelTmp.raycastTarget = false;

                InteractButtonRoot = btn;
            }

            if (InteractPromptText == null)
            {
                var promptGO = new GameObject("InteractPrompt", typeof(RectTransform));
                promptGO.transform.SetParent(parent, false);
                var prt = (RectTransform)promptGO.transform;
                prt.anchorMin = prt.anchorMax = new Vector2(1, 0);
                prt.pivot = new Vector2(1, 0);
                prt.anchoredPosition = new Vector2(-30, 360);
                prt.sizeDelta = new Vector2(280, 40);
                var tmp = promptGO.AddComponent<TextMeshProUGUI>();
                tmp.text = "";
                tmp.color = EKVibe.TextLight;
                tmp.fontSize = 22;
                tmp.alignment = TextAlignmentOptions.Right;
                tmp.raycastTarget = false;

                InteractPromptText = tmp;
            }
        }

        /// <summary>
        /// Builds the bottom-right action controls in code: a vertical column of 4 spell buttons
        /// (ability slots 0-3), the big ATK melee button, and repositions USE beside ATK. Replaces
        /// the old scene cluster + quick-slot bar so the layout lives in one place and is easy to tweak.
        /// </summary>
        private void BuildActionButtons()
        {
            Transform hud = FindChildRecursive(transform, "HUDPanel") ?? transform;

            // Retire the old scene controls.
            if (RightActionPanel != null) RightActionPanel.gameObject.SetActive(false);
            if (BottomCenterQuickSlotPanel != null) BottomCenterQuickSlotPanel.gameObject.SetActive(false);

            var panel = new GameObject("ActionButtons", typeof(RectTransform));
            panel.transform.SetParent(hud, false);
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = prt.anchorMax = new Vector2(1f, 0f);
            prt.pivot = new Vector2(1f, 0f);
            prt.anchoredPosition = Vector2.zero;
            prt.sizeDelta = Vector2.zero;

            // ATK — big melee button, bottom-right.
            CreateActionButton(panel.transform, "ATK", HUDActionButton.ActionKind.Attack, 0,
                new Vector2(130f, 130f), new Vector2(-24f, 30f), new Color(0.55f, 0.3f, 0.22f, 1f));

            // 4 spell slots, vertical column above ATK, right-aligned.
            const float size = 100f, gap = 12f, baseY = 175f;
            for (int i = 0; i < 4; i++)
            {
                float y = baseY + i * (size + gap);
                var b = CreateActionButton(panel.transform, (i + 1).ToString(),
                    HUDActionButton.ActionKind.Ability, i, new Vector2(size, size),
                    new Vector2(-24f, y), EKVibe.ButtonBrown);
                _spellSlotImages[i] = b.GetComponent<Image>();
                _spellSlotLabels[i] = b.GetComponentInChildren<TextMeshProUGUI>();
            }

            RepositionInteractButton();
        }

        private GameObject CreateActionButton(Transform parent, string label, HUDActionButton.ActionKind kind,
            int abilityIndex, Vector2 size, Vector2 pos, Color color)
        {
            var go = new GameObject(kind == HUDActionButton.ActionKind.Ability ? $"Spell{abilityIndex}" : label,
                typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 0f);
            rt.pivot = new Vector2(1f, 0f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;

            var img = go.AddComponent<Image>();
            img.color = color;
            go.AddComponent<Button>();
            var action = go.AddComponent<HUDActionButton>(); // wires click + cooldown sweep
            action.Kind = kind;
            action.AbilityIndex = abilityIndex;

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false); // after the cooldown overlay → on top
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = label;
            tmp.color = EKVibe.TextLight;
            tmp.fontSize = kind == HUDActionButton.ActionKind.Attack ? 26 : 24;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.raycastTarget = false;
            return go;
        }

        /// <summary>Moves USE in line with ATK, ~half an inch to its left, a touch smaller.</summary>
        private void RepositionInteractButton()
        {
            EnsureInteractUI();
            if (InteractButtonRoot != null)
            {
                var rt = InteractButtonRoot.GetComponent<RectTransform>();
                if (rt != null)
                {
                    rt.anchorMin = rt.anchorMax = new Vector2(1f, 0f);
                    rt.pivot = new Vector2(1f, 0f);
                    rt.sizeDelta = new Vector2(110f, 110f);
                    rt.anchoredPosition = new Vector2(-224f, 40f);
                }
            }
            if (InteractPromptText != null)
            {
                var prt = InteractPromptText.GetComponent<RectTransform>();
                if (prt != null)
                {
                    prt.anchorMin = prt.anchorMax = new Vector2(1f, 0f);
                    prt.pivot = new Vector2(1f, 0f);
                    prt.sizeDelta = new Vector2(260f, 36f);
                    prt.anchoredPosition = new Vector2(-149f, 158f); // just above USE
                    InteractPromptText.alignment = TextAlignmentOptions.Center;
                }
            }
        }

        /// <summary>Shows each bound spell's glyph and dims empty slots.</summary>
        private void RefreshSpellSlots()
        {
            var combat = Combat.CombatController.Instance;
            for (int i = 0; i < _spellSlotImages.Length; i++)
            {
                AbilityData ability = null;
                if (combat != null && combat.EquippedAbilities != null && i < combat.EquippedAbilities.Count)
                    ability = combat.EquippedAbilities[i];
                bool bound = ability != null;

                if (_spellSlotImages[i] != null)
                {
                    Color c = EKVibe.ButtonBrown;
                    if (!bound) c.a = 0.35f;
                    _spellSlotImages[i].color = c;
                }
                if (_spellSlotLabels[i] != null)
                {
                    if (bound)
                    {
                        string glyph = !string.IsNullOrEmpty(ability.IconGlyph) ? ability.IconGlyph
                            : (!string.IsNullOrEmpty(ability.AbilityName) ? ability.AbilityName.Substring(0, 1) : (i + 1).ToString());
                        _spellSlotLabels[i].text = glyph;
                        _spellSlotLabels[i].fontSize = 40;
                        _spellSlotLabels[i].color = EKVibe.TextLight;
                    }
                    else
                    {
                        _spellSlotLabels[i].text = (i + 1).ToString();
                        _spellSlotLabels[i].fontSize = 24;
                        _spellSlotLabels[i].color = new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.5f);
                    }
                }
            }
        }

        private static Transform FindChildRecursive(Transform root, string name)
        {
            foreach (Transform child in root)
            {
                if (child.name == name) return child;
                Transform found = FindChildRecursive(child, name);
                if (found != null) return found;
            }
            return null;
        }
    }
}
