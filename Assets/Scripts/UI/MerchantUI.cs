using System.Collections.Generic;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.Vibe;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace GBHEngland.UI
{
    /// <summary>
    /// Runtime-built Win95 merchant window. Merchant stock is unlimited; only the player's
    /// inventory and wallet mutate, so existing save machinery persists every transaction.
    /// </summary>
    public class MerchantUI : MonoBehaviour
    {
        private static MerchantUI _instance;

        private GameObject _panelRoot;
        private TextMeshProUGUI _titleText;
        private TextMeshProUGUI _walletText;
        private TextMeshProUGUI _statusText;
        private Transform _rowContainer;
        private Button _buyTab;
        private Button _sellTab;

        private MerchantData _merchant;
        private MerchantActionType _mode;

        public static bool IsOpen => _instance != null && _instance._panelRoot != null
                                     && _instance._panelRoot.activeSelf;

        public static void Show(MerchantData merchant, MerchantActionType mode)
        {
            if (merchant == null || mode == MerchantActionType.None) return;

            if (_instance == null)
            {
                var go = new GameObject("MerchantUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<MerchantUI>();
                _instance.BuildUI();
            }

            _instance.Open(merchant, mode);
        }

        private void Open(MerchantData merchant, MerchantActionType mode)
        {
            if (IsOpen) return;

            _merchant = merchant;
            _mode = merchant.SellOnly ? MerchantActionType.Sell : mode;
            _titleText.text = string.IsNullOrEmpty(merchant.MerchantName)
                ? "Shop"
                : merchant.MerchantName;
            _statusText.text = "";
            _panelRoot.SetActive(true);
            Systems.PauseManager.Push();
            Refresh();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _panelRoot.SetActive(false);
            _merchant = null;
            Systems.PauseManager.Pop();
        }

        private void SetMode(MerchantActionType mode)
        {
            if (!IsOpen || mode == MerchantActionType.None) return;
            _mode = mode;
            _statusText.text = "";
            Refresh();
        }

        private void Refresh()
        {
            var session = PlayerSession.Instance;
            _walletText.text = session != null ? EKVibe.FormatPounds(session.Pounds) : EKVibe.FormatPounds(0);
            _buyTab.interactable = _mode != MerchantActionType.Buy;
            _sellTab.interactable = _mode != MerchantActionType.Sell;
            _buyTab.gameObject.SetActive(!_merchant.SellOnly);

            foreach (Transform child in _rowContainer)
                Destroy(child.gameObject);

            if (_merchant == null || session == null) return;
            if (_mode == MerchantActionType.Buy) BuildBuyRows(session);
            else BuildSellRows(session);
        }

        private void BuildBuyRows(PlayerSession session)
        {
            if (_merchant.Stock == null) return;

            for (int i = 0; i < _merchant.Stock.Count; i++)
            {
                MerchantStockEntry entry = _merchant.Stock[i];
                if (entry == null || entry.Item == null) continue;

                int price = _merchant.PurchasePrice(entry);
                int owned = session.CountItem(entry.Item);
                string details = ItemDetails(entry.Item, owned);
                bool canBuy = price > 0 && session.Pounds >= price;
                BuildRow(entry.Item, details, EKVibe.FormatPounds(price), "BUY", canBuy,
                    () => Buy(entry));
            }
        }

        private void BuildSellRows(PlayerSession session)
        {
            var totals = new Dictionary<ItemData, int>();
            for (int i = 0; i < session.Inventory.Count; i++)
            {
                InventoryStack stack = session.Inventory[i];
                if (stack == null || stack.Item == null || stack.Quantity <= 0) continue;
                if (totals.ContainsKey(stack.Item)) totals[stack.Item] += stack.Quantity;
                else totals.Add(stack.Item, stack.Quantity);
            }

            if (totals.Count == 0)
            {
                if (string.IsNullOrEmpty(_statusText.text))
                    _statusText.text = "You have nothing to sell.";
                return;
            }

            foreach (var pair in totals)
            {
                ItemData item = pair.Key;
                int price = _merchant.SalePreviewPrice(item);
                bool accepted = _merchant.Accepts(item);
                MerchantPurchaseRule rule = _merchant.FindPurchaseRule(item);
                string priceLabel = accepted
                    ? (rule != null && rule.IsRandom
                        ? EKVibe.FormatPounds(rule.RandomMin) + " to " + EKVibe.FormatPounds(rule.RandomMax)
                        : EKVibe.FormatPounds(price))
                    : "NOT BUYING";
                BuildRow(item, ItemDetails(item, pair.Value), priceLabel, "SELL", accepted,
                    () => Sell(item));
            }
        }

        private void Buy(MerchantStockEntry entry)
        {
            var session = PlayerSession.Instance;
            if (_merchant == null || session == null || entry == null || entry.Item == null) return;

            int price = _merchant.PurchasePrice(entry);
            if (price <= 0 || !session.SpendPounds(price))
            {
                _statusText.text = "Not enough money.";
                Refresh();
                return;
            }

            // AddItem cannot refuse a valid item: the current backpack has no hard capacity.
            session.AddItem(entry.Item, 1);
            _statusText.text = "Bought " + entry.Item.ItemName + ".";
            Refresh();
        }

        private void Sell(ItemData item)
        {
            var session = PlayerSession.Instance;
            if (_merchant == null || session == null || !_merchant.Accepts(item)) return;

            MerchantPurchaseRule rule = _merchant.FindPurchaseRule(item);
            int price = rule != null ? rule.RollPrice() : MerchantData.ResalePrice(item);
            if (price <= 0 || !session.RemoveItem(item, 1))
            {
                Refresh();
                return;
            }

            session.AddPounds(price);
            string resultMessage = rule != null ? rule.MessageFor(price) : "";
            _statusText.text = string.IsNullOrEmpty(resultMessage)
                ? "Sold " + item.ItemName + " for " + EKVibe.FormatPounds(price) + "."
                : resultMessage + "  " + EKVibe.FormatPounds(price) + ".";
            Refresh();
        }

        private static string ItemDetails(ItemData item, int owned)
        {
            var parts = new List<string>();
            if (item.Damage > 0) parts.Add("Damage +" + item.Damage);
            if (item.Armor > 0) parts.Add("Armour +" + item.Armor);
            if (item.AttackBonus > 0) parts.Add("Attack +" + item.AttackBonus);
            if (item.PoisonResistance > 0) parts.Add("Poison resist +" + item.PoisonResistance);
            if (item.HealHP > 0) parts.Add("HP +" + item.HealHP);
            if (item.HealMana > 0) parts.Add("Mana +" + item.HealMana);
            if (item.ManaDamage > 0) parts.Add("Mana -" + item.ManaDamage);
            parts.Add("Owned: " + owned);
            return string.Join("   ", parts);
        }

        private void BuildUI()
        {
            var canvasGO = new GameObject("MerchantCanvas");
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 510;
            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGO.AddComponent<GraphicRaycaster>();

            GameObject dim = CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _panelRoot = dim;

            GameObject panel = CreateImage("MerchantPanel", dim.transform, Win95Skin.Face);
            Win95Skin.StyleWindow(panel.GetComponent<Image>());
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(1120, 760);
            panel.GetComponent<Image>().raycastTarget = true;

            RectTransform titleBar = Win95Skin.AddTitleBar(prt, "Shop", 48f);
            _titleText = titleBar.Find("TitleText").GetComponent<TextMeshProUGUI>();
            _titleText.fontSize = 24f;
            Button closeX = titleBar.Find("CloseButton").GetComponent<Button>();
            closeX.onClick.RemoveAllListeners();
            closeX.onClick.AddListener(Close);

            _buyTab = CreateButton("BuyTab", panel.transform, "BUY", () => SetMode(MerchantActionType.Buy));
            SetRect(_buyTab.gameObject, new Vector2(0f, 1f), new Vector2(0f, 1f),
                new Vector2(28, -122), new Vector2(190, 52), new Vector2(0f, 1f));

            _sellTab = CreateButton("SellTab", panel.transform, "SELL", () => SetMode(MerchantActionType.Sell));
            SetRect(_sellTab.gameObject, new Vector2(0f, 1f), new Vector2(0f, 1f),
                new Vector2(230, -122), new Vector2(190, 52), new Vector2(0f, 1f));

            _walletText = CreateTMP("Wallet", panel.transform, EKVibe.FormatPounds(0), Win95Skin.FieldText, 25,
                TextAlignmentOptions.Right);
            SetRect(_walletText.gameObject, new Vector2(1f, 1f), new Vector2(1f, 1f),
                new Vector2(-28, -122), new Vector2(300, 52), new Vector2(1f, 1f));

            GameObject viewport = CreateImage("RowsViewport", panel.transform, Win95Skin.SlotFill);
            var vrt = (RectTransform)viewport.transform;
            vrt.anchorMin = Vector2.zero;
            vrt.anchorMax = Vector2.one;
            vrt.offsetMin = new Vector2(28, 100);
            vrt.offsetMax = new Vector2(-28, -138);
            Win95Skin.AddBevel(vrt, sunken: true);
            var mask = viewport.AddComponent<Mask>();
            mask.showMaskGraphic = false;

            var rowsGO = new GameObject("Rows", typeof(RectTransform));
            rowsGO.transform.SetParent(viewport.transform, false);
            var rrt = (RectTransform)rowsGO.transform;
            rrt.anchorMin = new Vector2(0f, 1f);
            rrt.anchorMax = new Vector2(1f, 1f);
            rrt.pivot = new Vector2(0.5f, 1f);
            rrt.sizeDelta = Vector2.zero;
            var layout = rowsGO.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(12, 12, 12, 12);
            layout.spacing = 10;
            layout.childControlWidth = true;
            layout.childControlHeight = false;
            layout.childForceExpandHeight = false;
            var fitter = rowsGO.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            _rowContainer = rowsGO.transform;

            var scroll = viewport.AddComponent<ScrollRect>();
            scroll.viewport = vrt;
            scroll.content = rrt;
            scroll.horizontal = false;
            scroll.vertical = true;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 45f;

            _statusText = CreateTMP("Status", panel.transform, "", Win95Skin.FieldText, 20,
                TextAlignmentOptions.Left);
            SetRect(_statusText.gameObject, Vector2.zero, Vector2.zero,
                new Vector2(28, 22), new Vector2(650, 58), Vector2.zero);

            Button close = CreateButton("CloseButton", panel.transform, "CLOSE", Close);
            SetRect(close.gameObject, new Vector2(1f, 0f), new Vector2(1f, 0f),
                new Vector2(-28, 22), new Vector2(220, 58), new Vector2(1f, 0f));

            _panelRoot.SetActive(false);
        }

        private void BuildRow(ItemData item, string details, string price, string verb,
            bool interactable, UnityEngine.Events.UnityAction action)
        {
            GameObject row = CreateImage("MerchantRow", _rowContainer, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)row.transform, sunken: false);
            ((RectTransform)row.transform).sizeDelta = new Vector2(0, 112);

            GameObject icon = CreateImage("Icon", row.transform, Color.white);
            SetRect(icon, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f),
                new Vector2(12, 0), new Vector2(84, 84), new Vector2(0f, 0.5f));
            Image iconImage = icon.GetComponent<Image>();
            iconImage.sprite = item.Icon;
            iconImage.preserveAspect = true;
            iconImage.enabled = item.Icon != null;

            TextMeshProUGUI name = CreateTMP("Name", row.transform, item.ItemName,
                Win95Skin.FieldText, 22, TextAlignmentOptions.TopLeft);
            SetRect(name.gameObject, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f),
                new Vector2(112, 27), new Vector2(590, 42), new Vector2(0f, 0.5f));
            name.fontStyle = FontStyles.Bold;

            TextMeshProUGUI detail = CreateTMP("Details", row.transform, details,
                Win95Skin.FieldText, 17, TextAlignmentOptions.BottomLeft);
            SetRect(detail.gameObject, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f),
                new Vector2(112, -25), new Vector2(650, 42), new Vector2(0f, 0.5f));

            TextMeshProUGUI priceText = CreateTMP("Price", row.transform, price,
                Win95Skin.FieldText, 22, TextAlignmentOptions.Center);
            SetRect(priceText.gameObject, new Vector2(1f, 0.5f), new Vector2(1f, 0.5f),
                new Vector2(-350, 0), new Vector2(150, 62), new Vector2(0f, 0.5f));

            Button actionButton = CreateButton("Action", row.transform, verb, action);
            SetRect(actionButton.gameObject, new Vector2(1f, 0.5f), new Vector2(1f, 0.5f),
                new Vector2(-18, 0), new Vector2(170, 62), new Vector2(1f, 0.5f));
            actionButton.interactable = interactable;
        }

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var image = go.AddComponent<Image>();
            image.color = color;
            return go;
        }

        private static Button CreateButton(string name, Transform parent, string label,
            UnityEngine.Events.UnityAction action)
        {
            GameObject go = CreateImage(name, parent, Win95Skin.Face);
            var button = go.AddComponent<Button>();
            Win95Skin.StyleButton(button);
            button.onClick.AddListener(action);
            TextMeshProUGUI text = CreateTMP("Label", go.transform, label,
                Win95Skin.FieldText, 21, TextAlignmentOptions.Center);
            Stretch(text.gameObject, Vector2.zero, Vector2.one);
            return button;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions alignment)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = alignment;
            tmp.raycastTarget = false;
            return tmp;
        }

        private static void Stretch(GameObject go, Vector2 anchorMin, Vector2 anchorMax)
        {
            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        private static void SetRect(GameObject go, Vector2 anchorMin, Vector2 anchorMax,
            Vector2 position, Vector2 size, Vector2 pivot)
        {
            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.pivot = pivot;
            rt.anchoredPosition = position;
            rt.sizeDelta = size;
        }
    }
}
