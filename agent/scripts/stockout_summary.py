"""
stockout_summary.py - Cross-table stockout analysis.

Usage:
    python stockout_summary.py --sku 1042
    python stockout_summary.py --region 3
    python stockout_summary.py --sku 1042 --region 3
    python stockout_summary.py --region 2 --threshold 10

Joins inventory + store + warehouse + purchase_order to report:
  - Stores below reorder level
  - Warehouse stock
  - Draft purchase orders
  - Whether the 6-store supply disruption rule fires
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "Retail data raw" / "Retail data raw"
EXCEL_FILE = DATA_DIR / "retail_enterprise_data_Azure_sql.xlsx"

# Short alias -> actual Excel tab name (same map as read_data.py)
SHEET_MAP = {
    "inventory":            "fact_inventory",
    "purchase_order":       "fact_purchase_order",
    "purchase_order_line":  "fact_purchase_order_line",
    "sales_transaction":    "fact_sales_transaction",
    "sales_line_item":      "fact_sales_line_item",
    "order":                "fact_order",
    "order_line":           "fact_order_line",
    "return":               "fact_return",
    "daily_sales_summary":  "fact_daily_sales_summary",
    "employee_schedule":    "fact_employee_schedule",
    "store":                "dim_store",
    "warehouse":            "dim_warehouse",
    "product":              "dim_product",
    "supplier":             "dim_supplier",
    "region":               "dim_region",
    "brand":                "dim_brand",
    "category":             "dim_category",
    "customer":             "dim_customer",
    "employee":             "dim_employee",
    "department":           "dim_department",
    "promotion":            "dim_promotion",
}

_CACHE = {}


def sheet(name: str) -> pd.DataFrame:
    actual = SHEET_MAP.get(name.lower().strip(), name)
    if actual not in _CACHE:
        df = pd.read_excel(EXCEL_FILE, sheet_name=actual)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        _CACHE[actual] = df
    return _CACHE[actual].copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", type=int)
    parser.add_argument("--region", type=int)
    parser.add_argument("--threshold", type=int, help="Override reorder threshold")
    args = parser.parse_args()

    try:
        inv = sheet("inventory")
        stores = sheet("store")
        po = sheet("purchase_order")
        pol = sheet("purchase_order_line")
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    # Filter by SKU
    if args.sku:
        inv = inv[inv["sku_id"] == args.sku]

    # Join store for region + name
    inv = inv.merge(stores[["store_id", "region_id", "store_name"]], on="store_id", how="left")
    if args.region:
        inv = inv[inv["region_id"] == args.region]

    # Stockout mask
    if args.threshold is not None:
        mask = inv["quantity_on_hand"] <= args.threshold
    elif "reorder_level" in inv.columns:
        mask = inv["quantity_on_hand"] <= inv["reorder_level"]
    else:
        mask = inv["quantity_on_hand"] == 0

    stockout = inv[mask]

    # Draft POs for the SKU
    draft_pos = []
    if args.sku and "sku_id" in pol.columns:
        sku_lines = pol[pol["sku_id"] == args.sku]
        merged = sku_lines.merge(po, on="po_id", how="left")
        status_col = "status" if "status" in merged.columns else None
        if status_col:
            draft = merged[merged[status_col].astype(str).str.upper() == "DRAFT"]
            keep = [c for c in ["po_id", "supplier_id", "status", "expected_delivery_date", "quantity_ordered"] if c in draft.columns]
            draft_pos = draft[keep].where(pd.notnull(draft[keep]), None).to_dict("records")

    result = {
        "sku_id": args.sku,
        "region_id": args.region,
        "total_stores_scanned": len(inv),
        "stores_below_reorder": len(stockout),
        "trigger_supply_disruption_rule": len(stockout) >= 6,
        "stockout_store_ids": stockout["store_id"].tolist(),
        "stockout_stores": stockout[
            [c for c in ["store_id", "store_name", "region_id", "quantity_on_hand", "reorder_level"] if c in stockout.columns]
        ].where(pd.notnull(stockout[[c for c in ["store_id", "store_name", "region_id", "quantity_on_hand", "reorder_level"] if c in stockout.columns]]), None)
        .to_dict("records"),
        "draft_pos": draft_pos,
    }

    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
