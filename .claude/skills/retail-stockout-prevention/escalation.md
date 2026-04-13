---
name: escalation
description: "Escalation rules and chains for supply chain stockout events. Load this file to determine when the agent should auto-escalate to Regional VP, Procurement Lead, Loss Prevention, or Merchandising. Defines 8 automatic triggers with timelines, the full escalation chain from Store Manager to SVP, what counts as 'resolved', and trust-level override rules for autonomous vs supervised actions."
source: QDojo Knowledge Capture Interview
captured: "2026-03-27"
expert: Rachel Torres
---

# Escalation Rules — Supply Chain Operations

## Automatic Escalation Triggers

| #  | Trigger                                            | Escalate To          | Timeline    |
|----|----------------------------------------------------|----------------------|-------------|
| E1 | Stockout unresolved (no clear resolution path)     | Regional VP          | 48 hours    |
| E2 | Affected inventory value > $500,000                | Regional VP          | Immediate   |
| E3 | RetailCorp Brand stockout across 3+ stores         | Regional VP + Merch  | Immediate   |
| E4 | Perishable product stockout at WH-COLD-01          | Regional VP          | 24 hours    |
| E5 | PO > $1M stuck in Draft > 3 days                   | Procurement VP       | Immediate   |
| E6 | Supplier rating < 3.0 + missed delivery            | Procurement Lead     | Next day    |
| E7 | 2+ late deliveries from same supplier in 90 days   | Procurement Lead     | Auto-flag   |
| E8 | Negative inventory detected (qty_on_hand < 0)      | Loss Prevention      | Same day    |

---

## Escalation Chain

```
Store Manager
    ↓ (unresolved 24hrs)
Regional Operations Manager
    ↓ (unresolved 48hrs OR value > $500K)
Regional VP
    ↓ (multi-region OR value > $2M)
SVP Supply Chain
```

**Parallel notifications:**
- RetailCorp Brand issues → Merchandising VP (always, regardless of value)
- Supplier pattern flags → Procurement Lead (auto-flag, no delay)
- Negative inventory → Loss Prevention team (same day)
- Pricing signals → QEnvoy procurement agent (real-time forward)

---

## What Counts as "Resolved"

A stockout is resolved when ALL of these are true:

1. Root cause is identified and documented
2. A PO is approved and submitted (not Draft)
3. Supplier has confirmed delivery date
4. Affected store managers have been notified with ETA
5. If applicable: inter-store transfers are blocked to prevent drain

A stockout is NOT resolved just because a PO exists — it must be out of Draft and confirmed by the supplier.

---

## Trust Level Override Rules

- **Trust Level 1 (supervised):** Agent can auto-execute notifications and transfer blocks. All PO approvals and pricing decisions require human sign-off.
- **Trust Level 2 (semi-autonomous):** Agent can approve POs up to $100K and execute transfers within guardrails.
- **Trust Level 3 (autonomous):** Agent can approve POs up to $500K and negotiate pricing. VP approval only above threshold.

**Current deployment: Trust Level 1.**
