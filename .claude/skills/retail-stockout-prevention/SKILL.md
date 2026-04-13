---
name: retail-stockout-prevention
description: "Use this skill whenever the agent detects or is asked about multi-store stockouts, supply chain disruptions, inventory shortages across regions, warehouse replenishment issues, or purchase order bottlenecks. Triggers include: 6+ stores in the same region below reorder level on the same SKU, warehouse quantity_on_hand at zero, purchase orders stuck in Draft status, supplier delivery delays, or any alert involving regional inventory depletion. Also use when assessing whether a stockout is demand-driven vs supply-driven, when deciding whether to initiate inter-store transfers, when evaluating private-label (RetailCorp Brand / Value Choice) stockout severity, or when checking competitor stock levels and commodity pricing for procurement decisions. Do NOT use for single-store inventory questions, demand forecasting, pricing strategy, or marketing campaign analysis."
owner: Rachel Torres (VP Supply Chain Operations, 18 years at RetailCo)
trust_level: 1 (supervised)
version: "1.0"
accuracy: "94.2% across 847 runs"
---

# Retail Stockout Prevention — Multi-Region

## Trigger

6+ stores **in the same region** reporting the same SKU below `reorder_level` simultaneously.

---

## Decision Steps

### Step 1 — Classify the event

Count affected stores **per region**.

- IF **≥ 6 stores** in one region → classify as **SUPPLY DISRUPTION**
- IF **< 6 stores** → classify as **LOCAL DEMAND SPIKE** (handle differently)

> ⚠️ Do NOT treat a supply disruption as a demand event. The response is completely different.

### Step 2 — Identify regional warehouse

Map the affected region to its warehouse:

| Region     | Warehouse                                | Code       |
|------------|------------------------------------------|------------|
| NA-EAST    | East Coast Distribution Center, Newark   | WH-EAST-01 |
| NA-WEST    | West Coast Fulfillment Center, LA        | WH-WEST-01 |
| NA-CENT    | Central Mega Warehouse, Chicago          | WH-CENT-01 |
| NA-SOUTH   | Southern Distribution Hub, Dallas        | WH-SOUTH-01|
| EU-WEST    | European Distribution Center, London     | WH-EU-01   |
| APAC       | Asia Pacific Hub, Tokyo                  | WH-APAC-01 |
| Cold Chain | Cold Storage Facility, Philadelphia      | WH-COLD-01 |

### Step 3 — Diagnose warehouse inventory

Query `fact_inventory` for the warehouse + product:

- `quantity_on_hand` = 0 **AND** `quantity_reserved` > 0 → **True shortage** (warehouse empty, allocations unfulfillable)
- `quantity_on_hand` > 0 **AND** `quantity_reserved` ≈ `quantity_on_hand` → **Shipping bottleneck** (stock exists but stuck in picking/packing)
- `quantity_on_hand` > 0 **AND** `quantity_reserved` low → **Distribution delay** (stock available, not shipped to stores)

### Step 4 — Check purchase order pipeline

Query `fact_purchase_order` for the relevant supplier + warehouse:

- Status = `Draft` → **Approval missed.** Flag immediately. This is the most common root cause.
- Status = `Approved` or `Submitted` → PO is in pipeline. Check `expected_delivery_date`.
- Status = `Shipped` → Delivery in transit. Check carrier and weather conditions.
- Status = `Received` but stores still low → **Distribution problem**, not supply.
- No active PO exists → **Reorder missed entirely.** Create emergency PO.

> ⚠️ Any PO over $1M that has been in Draft for more than 3 days is a **control failure**. Escalate immediately.

### Step 5 — Check supplier profile

Query `dim_supplier` for lead time, rating, and reliability:

- `lead_time_days` > 30 → Recovery is weeks away. Escalate immediately regardless of other factors.
- `rating` < 3.0 → Unreliable supplier. Initiate sourcing review if delivery is also late.
- Check delivery history: 2+ POs in last 90 days where `actual_delivery_date` > `expected_delivery_date` + 5 days → **Pattern of late delivery.** Flag for procurement.

### Step 6 — Check private label impact

Query `dim_brand` for the affected product:

- `brand_id` = 11 (RetailCorp Brand) AND 3+ stores affected → **Severity 1**
  - RetailCorp Brand customers migrate to branded competitors (Samsung, Nike, etc.)
  - 30% permanent customer loss
  - Restock RetailCorp Brand BEFORE Value Choice (brand_id=12)
- `brand_id` = 12 (Value Choice) → Standard priority
- Any other brand → Standard priority, but check product count (top brands = elevated visibility)

### Step 7 — Check external signals

Browse/fetch real-time data:

1. **Weather** → `weather.gov` for delivery corridor conditions (I-5 West, I-95 East, I-10 South)
2. **Competitors** → `bestbuy.com`, `target.com`, `walmart.com` for same-category stock status
   - If competitor also out → Regional shortage confirmed. Order 15-25% above normal.
3. **Commodity prices** → Check relevant indices for cost trend
   - Rising prices → Lock current supplier pricing before increase hits
4. **Internal signals** → `blob_customer_feedback` sentiment on the product, `fact_return` patterns

### Step 8 — Recommend action + guardrail check

Generate action list. Apply guardrails:

| Guardrail                    | Threshold     | Action if exceeded            |
|------------------------------|---------------|-------------------------------|
| Inventory value affected     | $500,000      | Immediate VP escalation       |
| Time unresolved              | 48 hours      | Auto-escalate to Regional VP  |
| PO value (new/modified)      | $500,000      | Requires VP approval          |
| Private label + 3 stores     | Severity 1    | Priority restock              |
| Supplier rating              | < 3.0         | Sourcing review               |

**Always:**
- Block inter-store transfers during supply disruption
- Log every action for audit trail
- Forward pricing signals to QEnvoy procurement agent
