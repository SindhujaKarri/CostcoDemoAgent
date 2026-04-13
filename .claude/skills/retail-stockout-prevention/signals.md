---
name: signals
description: "External web sources and internal data signals the agent monitors during stockout investigation. Load this file to know which websites to browse (weather.gov, bestbuy.com, supplier portals, BLS commodity indices), which internal tables to query for anomalies (fact_inventory negatives, fact_return spikes, blob_customer_feedback sentiment, fact_purchase_order stuck in Draft), and the priority order for checking signals. Without this file, the agent misses competitive intelligence and commodity pricing signals that change the recommended action."
source: QDojo Knowledge Capture Interview
captured: "2026-03-27"
expert: Rachel Torres
---

# Monitoring Signals — Supply Chain Intelligence

## External Signals (Web Sources)

### 1. Weather & Logistics — weather.gov

| Region   | Corridor to Monitor | Route                      |
|----------|---------------------|----------------------------|
| NA-WEST  | I-5                 | San Francisco → Los Angeles|
| NA-WEST  | I-10                | Los Angeles → Phoenix      |
| NA-WEST  | I-15                | Los Angeles → Las Vegas    |
| NA-EAST  | I-95                | Newark → Philadelphia      |
| NA-SOUTH | I-10                | Dallas → Houston           |
| NA-CENT  | I-90                | Chicago → regional         |

**What to look for:** Active advisories (ice, flood, wind), road closures, 3-day forecast for clearing.

**Agent action:** If advisory active on delivery corridor → flag as logistics disruption, adjust delivery ETAs, notify warehouse managers.

### 2. Competitor Stock — Retail Websites

| Category        | Check First         | Then Check               |
|-----------------|---------------------|--------------------------|
| Electronics     | bestbuy.com         | target.com, walmart.com  |
| Apparel         | amazon.com          | nordstrom.com            |
| Home Appliances | homedepot.com       | lowes.com                |
| Grocery/Fresh   | instacart.com       | walmart.com/grocery      |
| General Retail  | walmart.com         | target.com               |

**What to look for:** "Limited Availability", "Out of Stock", "Check Store", delivery date slipping past 7 days.

**Agent action:** If competitor also out in same region + category → confirm regional shortage. Increase order quantity 15-25% above standard.

### 3. Commodity Prices — Index Sources

| Product Category      | Index to Monitor                   | Source              |
|-----------------------|------------------------------------|---------------------|
| Electronics           | Consumer Electronics Price Index   | bls.gov/cpi         |
| Paper/Packaging       | Pulp & Paper Index                 | usda.gov            |
| Apparel (cotton)      | Cotton Futures                     | cme group           |
| Food/Perishables      | Food CPI                           | bls.gov/cpi         |

**What to look for:** Week-over-week increase > 2%, quarter-over-quarter increase > 5%.

**Agent action:** Rising prices → forward to QEnvoy to lock current supplier pricing before increase hits. Recommend 90-day contract.

### 4. Supplier Portals — Direct Check

Check supplier's own portal/status page for:
- Manufacturing status (Normal / Reduced / Shutdown)
- Facility capacity utilization (alert if < 70% or > 95%)
- PO status from supplier's side ("Awaiting Approval", "In Production", "Shipped")
- Lead time changes or advisories

**Agent action:** If supplier shows "Awaiting Customer Approval" → match to internal Draft POs. If manufacturing reduced/shutdown → escalate immediately.

---

## Internal Signals (RetailCo Data)

### 5. Customer Feedback — blob_customer_feedback

1,000 feedback records in Azure Blob Storage. Monitor for:

| Signal                                  | Query                                                  |
|-----------------------------------------|--------------------------------------------------------|
| Negative sentiment spike on product     | `sentiment = 'Negative'` grouped by `product` topic    |
| "Out of stock" mentions in feedback     | `feedback_text LIKE '%out of stock%'`                  |
| Rating drop below 2.0                   | `rating < 2.0` for specific store + timeframe          |

**Agent action:** Sentiment spike on affected product confirms customer-facing impact. Elevate priority.

### 6. Return Patterns — fact_return

500 return records. Monitor for:

| Signal                                        | What It Means                                 |
|-----------------------------------------------|-----------------------------------------------|
| Spike in reason = "Product Defective" (id: 1) | Quality issue from supplier batch             |
| Spike in reason = "Damaged in Shipping" (id: 8)| Carrier/logistics handling problem            |
| Same product returned 5+ times in 7 days      | Systemic product quality issue                |
| Same store_id in top returns repeatedly        | Store-level operational issue                 |

**Agent action:** If return spike correlates with a supplier batch → flag supplier quality. If "Damaged in Shipping" spike → flag carrier. Do NOT reorder from flagged supplier without quality review.

### 7. Inventory Anomalies — fact_inventory

| Signal                        | Count in Current Data | What It Means                    |
|-------------------------------|----------------------|----------------------------------|
| quantity_on_hand < 0          | 128 records          | Receiving dock discrepancy       |
| quantity_on_hand = 0          | 10 records           | Complete stockout at location    |
| quantity_on_hand < 20         | 273 records          | Critical low stock               |

**Agent action:** Negative inventory → flag for Loss Prevention (potential shrinkage or vendor short-ship). Zero inventory → confirm if intentional (discontinued) or stockout.

### 8. Purchase Order Anomalies — fact_purchase_order

| Signal                                       | What It Means                         |
|----------------------------------------------|---------------------------------------|
| Status = Draft for > 3 days                  | Approval bottleneck                   |
| actual_delivery > expected_delivery + 5 days | Supplier late delivery                |
| Status inconsistency (mixed case)            | Data quality issue — normalize first  |

**Agent action:** Draft POs are the #1 missed root cause. Always check PO status before investigating external factors.

---

## Signal Priority Order

When investigating a stockout, check signals in this order:

1. **Purchase orders** (internal) — most common root cause
2. **Warehouse inventory** (internal) — confirm shortage vs bottleneck
3. **Supplier status** (external) — manufacturing/capacity
4. **Weather/logistics** (external) — delivery corridor
5. **Competitors** (external) — regional shortage confirmation
6. **Commodity prices** (external) — pricing/contract urgency
7. **Returns + feedback** (internal) — quality overlay

> Rachel: "90% of the time, the answer is in steps 1-3. But steps 4-6 change what you DO about it."
