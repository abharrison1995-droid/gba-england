---
name: merchant-author
description: Talk a shop through and design its MerchantData catalogue — what it sells, what it buys, pricing — then walk the owner through creating the asset, wiring it to a dialogue choice, and validating it. Proposes structure and numbers; leaves any status-message prose to the owner. Use when the user wants to create or wire up a merchant/shop for GBH: England.
---

# Merchant author

You help the owner design **one shop** (`MerchantData`) and wire it in. Unlike quests, merchants
have **no text importer** — `MerchantData` is an Inspector-authored ScriptableObject. So your job is:
interview, propose the full catalogue and numbers, then guide the owner through creating the asset
and wiring it. You may hand-author the `.asset` YAML if asked, but default to guiding.

## Read first

- `Assets/Scripts/Data/MerchantData.cs` — the authoritative field list and economy rules. Trust it.
- An existing shop under `Assets/Data/Merchants/` (e.g. `Merchant_Quidland.asset`) as a shape to copy.

## The prose line

Names and numbers are yours to propose freely. The **status messages** on a `PurchaseRule`
(`LowResultMessage` / `MidResultMessage` / `HighResultMessage` — the "you got robbed / fair price /
tidy sum" flavour lines) are prose: leave them for the owner, `[TODO:]`. Don't write them.

## The economy, so your numbers are right

- **Selling (shop → player):** each `Stock` entry is an `Item` + optional `PriceOverride`. Price 0
  falls back to the item's canonical `Value`.
- **Buying (player → shop):** an item is accepted only if it is `Tradeable`, not `ItemType.Quest`,
  has `Value > 0`, and either its `Type` is in `AcceptedTypes` **or** it has a specialist
  `PurchaseRule`. Default payout is **30%** of `Value` (`ResalePercent`); a `PurchaseRule` overrides
  that with a `FixedPrice` or an inclusive `RandomMin..RandomMax` roll.
- **`SellOnly`** opens the shop with no BUY tab.

## The interview

Small batches, propose defaults to approve:

1. **Identity** — `MerchantName`, and where it lives (which NPC/clerk opens it).
2. **Sells what** — the `Stock` list: which items (must exist in `Resources/Items`), and any
   `PriceOverride`s, else canonical `Value`.
3. **Buys what** — `AcceptedTypes` (broad categories), plus any `PurchaseRule`s for items that
   should pay more/less than the flat 30% (fixed or random range). Flag the three status messages as
   owner prose.
4. **Shape** — `SellOnly`? Anything a first pass should keep simple (stock is unlimited in pass one,
   no save state).

## Produce

Propose the catalogue as a clear table the owner can eyeball, then either:

- **Guide (default):** Project → Create → `GBH England/Data/Merchant Data`, save under
  `Assets/Data/Merchants/Merchant_<Name>.asset`, and fill the fields you specced. Drag item assets
  into `Stock`/`PurchaseRules`. Leave the status messages blank for the owner.
- **Hand-author (only if asked):** write the `.asset` YAML directly, resolving each `Item` to its
  real GUID from `Resources/Items`. If you do, **never delete-and-resave an existing asset** (it
  mints a fresh GUID and orphans references), and tell the owner to confirm Unity accepts the file
  on first open.

## Wire it up

The shop opens from a **dialogue choice**, not a menu. On the clerk's `DialogueData`, a
`DialogueChoice` gets its `Merchant` field set to this asset and `MerchantAction` = `Buy` or `Sell`;
picking it closes the conversation and calls `MerchantUI.Show`. Point the owner at the clerk's
conversation asset (or the `.quest`/preset that owns it) to set those two fields.

## Before hand-off, self-check

Mirror `Tools → Content → Validate Merchants`:

- Every `Stock`/`PurchaseRule` `Item` is assigned and exists in `Resources/Items`.
- Anything the shop is meant to buy actually passes `Accepts` (Tradeable, non-Quest, in
  `AcceptedTypes` or ruled) — otherwise it silently won't appear.
- Prices are non-negative; random rules have `RandomMax >= RandomMin`.

## Hand off (you can't run Unity)

1. Fill any status-message prose.
2. `Tools → Content → Validate Merchants` — read the Console, fix, repeat.
3. Set the clerk choice's `Merchant` + `MerchantAction`.
4. Place the clerk in the chunk so the player can open the shop; Play, buy and sell, confirm pounds
   move and a non-`Tradeable` item is refused.

## Never

- Write the shop's status-message flavour lines.
- Delete-and-resave an existing `MerchantData` asset.
- Claim the shop "works" — you can only confirm the catalogue is well-formed, not that it runs.
