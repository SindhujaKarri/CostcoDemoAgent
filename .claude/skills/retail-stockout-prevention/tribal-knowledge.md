---
name: tribal-knowledge
description: "Operational heuristics captured from Rachel Torres (VP Supply Chain, 18 years). These rules are NOT in any dashboard, report, or SOP. Load this file alongside SKILL.md to give the agent expert-level judgment on stockout classification, warehouse diagnosis, transfer decisions, private-label priority, supplier reliability, and competitive intelligence. Without this file, the agent makes junior-analyst mistakes — especially around inter-store transfers and private-label severity."
source: QDojo Knowledge Capture Interview
captured: "2026-03-27"
expert: Rachel Torres
---

# Tribal Knowledge — Supply Chain Operations

## Stockout Classification

- **"6+ stores in the same region dropping on the same SKU = supply disruption, NOT demand spike."**
  Every time. Don't second-guess it. The response for supply disruption is fundamentally different from demand spike.

- **"CA stores: always check WH-WEST-01 first."**
  15 stores in California, all fed from the West Coast Fulfillment Center in LA. When CA stores drop, it's always WH-WEST-01 or a supplier shipping into WH-WEST-01.

---

## Warehouse Diagnosis

- **"quantity_reserved high + quantity_on_hand normal = shipping bottleneck, not shortage."**
  The stock exists. It's stuck in picking or packing. Completely different fix than a supply shortage.

- **"quantity_reserved high + quantity_on_hand ZERO = true shortage."**
  Units are allocated to stores but the warehouse is empty. You can't ship what you don't have. Don't waste time investigating picking — the product isn't there.

- **"Negative inventory values are NOT data errors."**
  We have 128 records with negative quantity_on_hand. Those are receiving dock discrepancies — someone scanned items out that weren't properly scanned in. Every negative is a potential shrinkage event or vendor short-ship.

---

## Transfer Rules

- **"DO NOT rebalance inventory during a regional supply disruption."**
  You drain the healthy stores. Then one more hiccup and you have 15 stores short instead of 7. Wait for warehouse replenishment.

- **"Never transfer from a store with less than 7 days of supply."**
  Doesn't matter how bad the receiving store looks. If the sending store has < 7 days, it's not a donor — it's the next patient.

- **"During regional disruption: NO inter-store transfers. Period."**
  Not even from stores that look healthy. The disruption could widen before the warehouse restocks.

---

## Purchase Orders

- **"A PO stuck in Draft is the #1 root cause people miss."**
  Junior analysts look at supplier portals, check weather, call logistics — meanwhile a $400K purchase order is sitting in Draft because someone forgot to click Approve. Check PO status FIRST.

- **"Any PO over $1M in Draft for more than 3 days = control failure."**
  Doesn't matter what the excuse is. That's a process breakdown. Escalate.

- **"No active PO for a product below reorder level = the reorder was missed entirely."**
  Create an emergency PO immediately. Don't wait to investigate why it was missed.

---

## Private Label

- **"RetailCorp Brand stockout is a Severity 1 event at 3+ stores."**
  Not because of lost revenue — because of permanent customer migration. Customers don't switch to Value Choice. They switch to Samsung, Nike, Adidas. 30% never come back to private label.

- **"Value Choice stockouts are standard priority."**
  Value Choice is the budget line. Customers who buy Value Choice are price-driven — they'll wait or substitute within the budget tier. Not the same loyalty dynamics.

- **"Restock RetailCorp Brand BEFORE Value Choice. Always."**
  Even if Value Choice has lower absolute stock. The brand equity damage from RetailCorp Brand is 10x worse.

---

## Supplier Patterns

- **"Supplier rating below 3.0 + missed delivery = sourcing review, not just a warning."**
  We keep reordering from bad suppliers because 'the price is good.' Price doesn't matter if they can't deliver.

- **"Toy Kingdom (supplier_id 4, rating 2.54) — consistent underperformer."**
  Don't trust their lead times. Add 30% buffer to whatever they quote.

- **"Long-lead suppliers (> 30 days): if a stockout hits, recovery is WEEKS away."**
  These need earlier intervention. By the time you see a stockout, the reorder window was missed a month ago.

- **"2+ late deliveries from the same supplier in 90 days = a pattern."**
  Where actual_delivery_date exceeds expected_delivery_date by 5+ days. Don't treat as isolated incidents.

---

## Competitive Intelligence

- **"When a competitor is also out of stock on the same category + region: order 15-25% above normal."**
  Two reasons: (1) You're competing for the same supplier capacity when the disruption clears. (2) Displaced competitor customers will shop at RetailCo. You need buffer for both.

- **"Check Best Buy, Target, Walmart — in that order for electronics. For apparel, check Amazon first."**
  Different categories have different competitive dynamics. Electronics is physical-store driven. Apparel is online-first.

---

## Escalation Timing

- **"48 hours is the hard line."**
  If a stockout doesn't have a clear resolution path within 48 hours, it goes to the Regional VP. No exceptions.

- **"Inventory value over $500K goes up immediately."**
  Don't wait for the 48-hour clock. That dollar amount means the situation is material.

- **"Perishable products at Cold Storage (WH-COLD-01) get a 24-hour clock, not 48."**
  45 perishable SKUs in the system. Cold chain disruption = product loss, not just delay.
