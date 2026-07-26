Drop ItemData assets (Create > ExiledAlvaston > Data > Item Data) anywhere under this folder.
ItemDatabase finds them by ItemID automatically at runtime (Resources.LoadAll) — no
registration step needed. Give each one a unique ItemID; it's what gets saved to disk and
resolved back on load.
