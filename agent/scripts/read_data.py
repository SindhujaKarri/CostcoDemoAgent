"""
read_data.py - Load rows from the retail Excel dataset.

Usage:
    python read_data.py --sheet inventory
    python read_data.py --sheet purchase_order --filter status=Draft
    python read_data.py --sheet supplier --filter supplier_id=4
    python read_data.py --sheet store --cols store_id,store_name --max 20

Sheet aliases (use short names — auto-mapped to actual Excel tab names):
    inventory            -> fact_inventory
    purchase_order       -> fact_purchase_order
    purchase_order_line  -> fact_purchase_order_line
    sales_transaction    -> fact_sales_transaction
    sales_line_item      -> fact_sales_line_item
    order                -> fact_order
    order_line           -> fact_order_line
    return               -> fact_return
    daily_sales_summary  -> fact_daily_sales_summary
    employee_schedule    -> fact_employee_schedule
    store                -> dim_store
    warehouse            -> dim_warehouse
    product              -> dim_product
    supplier             -> dim_supplier
    region               -> dim_region
    brand                -> dim_brand
    category             -> dim_category
    customer             -> dim_customer
    employee             -> dim_employee
    department           -> dim_department
    promotion            -> dim_promotion
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

DATA_DIR   = Path(__file__).parent.parent.parent / "data" / "Retail data raw" / "Retail data raw"
EXCEL_FILE = DATA_DIR / "retail_enterprise_data_Azure_sql.xlsx"

# Short alias -> actual Excel tab name
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


def resolve_sheet(name: str) -> str:
    """Return the actual Excel tab name for a short alias or pass through."""
    return SHEET_MAP.get(name.lower().strip(), name)


def load_sheet(sheet: str) -> pd.DataFrame:
    actual = resolve_sheet(sheet)
    df = pd.read_excel(EXCEL_FILE, sheet_name=actual)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--filter", action="append", default=[], metavar="col=val")
    parser.add_argument("--cols", default="", help="Comma-separated column list")
    parser.add_argument("--max", type=int, default=200)
    args = parser.parse_args()

    try:
        df = load_sheet(args.sheet)
    except Exception as e:
        print(json.dumps({"error": str(e), "hint": f"Try one of: {list(SHEET_MAP.keys())}"}))
        sys.exit(1)

    for f in args.filter:
        if "=" in f:
            col, val = f.split("=", 1)
            col = col.strip().lower().replace(" ", "_")
            if col in df.columns:
                try:
                    df = df[df[col] == int(val)]
                except ValueError:
                    df = df[df[col].astype(str).str.upper() == val.strip().upper()]

    if args.cols:
        cols = [c.strip().lower().replace(" ", "_") for c in args.cols.split(",")]
        df = df[[c for c in cols if c in df.columns]]

    df = df.head(args.max)
    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    print(json.dumps({
        "sheet": args.sheet,
        "actual_tab": resolve_sheet(args.sheet),
        "row_count": len(records),
        "columns": list(df.columns),
        "data": records,
    }, default=str))


if __name__ == "__main__":
    main()
