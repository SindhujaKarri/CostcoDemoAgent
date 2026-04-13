"""
tools.py - MCP Tools for Retail Stockout Prevention Agent

Tools:
1. read_retail_data   - Load inventory / PO / store data from Excel files
2. log_escalation     - Persist escalation events to a local JSONL log
3. get_stockout_summary - Quick cross-table stockout summary for a SKU/region
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from claude_agent_sdk import tool, create_sdk_mcp_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
)
logger = logging.getLogger("TOOLS")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "Retail data raw" / "Retail data raw"
EXCEL_FILE = DATA_DIR / "retail_enterprise_data_Azure_sql.xlsx"
ESCALATION_LOG = PROJECT_ROOT / "agent" / "escalations.jsonl"

# Cache sheets in memory so repeated calls are fast
_SHEET_CACHE: Dict[str, pd.DataFrame] = {}


def _load_sheet(sheet_name: str) -> pd.DataFrame:
    """Load (and cache) a sheet from the main Excel file."""
    if sheet_name not in _SHEET_CACHE:
        logger.info(f"Loading sheet: {sheet_name}")
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        # Normalise column names to lowercase_snake
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        _SHEET_CACHE[sheet_name] = df
    return _SHEET_CACHE[sheet_name].copy()


# ---------------------------------------------------------------------------
# Tool 1 – read_retail_data
# ---------------------------------------------------------------------------
@tool(
    name="read_retail_data",
    description=(
        "Read rows from the retail enterprise dataset (Azure SQL tables). "
        "Pass the sheet/table name and optional filter key-value pairs. "
        "Available sheets: inventory, purchase_order, purchase_order_line, "
        "store, warehouse, product, supplier, order, sales_transaction, "
        "region, brand, category, return, daily_sales_summary. "
        "Returns up to max_rows rows as a JSON list."
    ),
    input_schema={
        "sheet": str,
        "filters": Optional[Dict[str, Any]],
        "columns": Optional[List[str]],
        "max_rows": Optional[int],
    },
)
async def read_retail_data(args: Dict[str, Any]) -> Dict[str, Any]:
    sheet: str = args["sheet"]
    filters: Optional[Dict[str, Any]] = args.get("filters")
    columns: Optional[List[str]] = args.get("columns")
    max_rows: int = args.get("max_rows") or 200

    try:
        df = _load_sheet(sheet)

        # Apply filters
        if filters:
            for col, val in filters.items():
                col_norm = col.strip().lower().replace(" ", "_")
                if col_norm in df.columns:
                    if isinstance(val, list):
                        df = df[df[col_norm].isin(val)]
                    else:
                        df = df[df[col_norm] == val]

        # Select columns
        if columns:
            cols_norm = [c.strip().lower().replace(" ", "_") for c in columns]
            existing = [c for c in cols_norm if c in df.columns]
            df = df[existing]

        df = df.head(max_rows)

        # Replace NaN with None for JSON serialisation
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "sheet": sheet,
                            "row_count": len(records),
                            "columns": list(df.columns),
                            "data": records,
                        },
                        default=str,
                    ),
                }
            ]
        }

    except Exception as exc:
        logger.exception(f"read_retail_data error: {exc}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"error": str(exc), "sheet": sheet}),
                }
            ]
        }


# ---------------------------------------------------------------------------
# Tool 2 – log_escalation
# ---------------------------------------------------------------------------
@tool(
    name="log_escalation",
    description=(
        "Persist a structured escalation event to the local escalation log. "
        "Use this whenever the skill's escalation rules are triggered "
        "(e.g. E1–E8 in escalation.md). "
        "Returns the logged record as confirmation."
    ),
    input_schema={
        "escalation_code": str,       # e.g. "E3"
        "severity": str,              # "critical" | "high" | "medium"
        "sku_id": Optional[int],
        "region": Optional[str],
        "store_ids": Optional[List[int]],
        "warehouse_id": Optional[str],
        "message": str,
        "recommended_action": str,
        "notify": Optional[List[str]],  # e.g. ["Regional VP", "Merchandising"]
    },
)
async def log_escalation(args: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "escalation_code": args.get("escalation_code", "UNKNOWN"),
        "severity": args.get("severity", "high"),
        "sku_id": args.get("sku_id"),
        "region": args.get("region"),
        "store_ids": args.get("store_ids", []),
        "warehouse_id": args.get("warehouse_id"),
        "message": args.get("message", ""),
        "recommended_action": args.get("recommended_action", ""),
        "notify": args.get("notify", []),
    }

    try:
        ESCALATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ESCALATION_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        logger.info(f"Escalation logged: {record['escalation_code']} – {record['severity']}")
    except Exception as exc:
        logger.exception(f"log_escalation write error: {exc}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"error": str(exc)}),
                }
            ]
        }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"status": "logged", "record": record}),
            }
        ]
    }


# ---------------------------------------------------------------------------
# Tool 3 – get_stockout_summary
# ---------------------------------------------------------------------------
@tool(
    name="get_stockout_summary",
    description=(
        "Return a cross-table stockout summary for a given product (sku_id) "
        "and/or region. Joins inventory + store + warehouse to show which "
        "stores are below reorder level and whether the regional warehouse "
        "has stock. Also surfaces any Draft purchase orders for the SKU. "
        "Pass sku_id and/or region_id."
    ),
    input_schema={
        "sku_id": Optional[int],
        "region_id": Optional[int],
        "reorder_threshold": Optional[int],  # default 0 = use stored reorder_level
    },
)
async def get_stockout_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    sku_id: Optional[int] = args.get("sku_id")
    region_id: Optional[int] = args.get("region_id")
    reorder_threshold: Optional[int] = args.get("reorder_threshold")

    try:
        inventory = _load_sheet("inventory")
        store = _load_sheet("store")
        warehouse = _load_sheet("warehouse")
        po = _load_sheet("purchase_order")
        po_line = _load_sheet("purchase_order_line")

        # Filter by SKU
        inv = inventory.copy()
        if sku_id is not None:
            inv = inv[inv["sku_id"] == sku_id]

        # Join store for region
        inv = inv.merge(store[["store_id", "region_id", "store_name"]], on="store_id", how="left")
        if region_id is not None:
            inv = inv[inv["region_id"] == region_id]

        # Determine stockout rows
        if reorder_threshold is not None:
            stockout_mask = inv["quantity_on_hand"] <= reorder_threshold
        else:
            # Use stored reorder_level column if available
            if "reorder_level" in inv.columns:
                stockout_mask = inv["quantity_on_hand"] <= inv["reorder_level"]
            else:
                stockout_mask = inv["quantity_on_hand"] == 0

        stockout_stores = inv[stockout_mask]

        # Warehouse stock for the sku
        wh_stock = None
        if "sku_id" in warehouse.columns and sku_id is not None:
            wh_rows = warehouse[warehouse["sku_id"] == sku_id]
            wh_stock = wh_rows[["warehouse_id", "warehouse_name", "quantity_on_hand"]].to_dict("records")

        # Draft POs for the SKU
        draft_pos: List[Dict] = []
        if sku_id is not None and "sku_id" in po_line.columns:
            sku_po_lines = po_line[po_line["sku_id"] == sku_id]
            merged_po = sku_po_lines.merge(po, on="po_id", how="left")
            draft = merged_po[merged_po.get("status", pd.Series(dtype=str)).str.upper() == "DRAFT"]
            draft_pos = draft[["po_id", "supplier_id", "expected_delivery_date", "quantity_ordered"]].to_dict("records") if not draft.empty else []

        summary = {
            "sku_id": sku_id,
            "region_id": region_id,
            "stores_below_reorder": len(stockout_stores),
            "stockout_store_ids": stockout_stores["store_id"].tolist(),
            "stockout_stores": stockout_stores[
                ["store_id", "store_name", "quantity_on_hand"]
            ].where(pd.notnull(stockout_stores[["store_id", "store_name", "quantity_on_hand"]]), None)
            .to_dict("records"),
            "warehouse_stock": wh_stock,
            "draft_pos": draft_pos,
            "trigger_supply_disruption_rule": len(stockout_stores) >= 6,
        }

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(summary, default=str),
                }
            ]
        }

    except Exception as exc:
        logger.exception(f"get_stockout_summary error: {exc}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"error": str(exc)}),
                }
            ]
        }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
AGENT_MCP_SERVER = create_sdk_mcp_server(
    name="retail-tools",
    tools=[read_retail_data, log_escalation, get_stockout_summary],
)

ALLOWED_MCP_TOOLS = [
    "mcp__retail-tools__read_retail_data",
    "mcp__retail-tools__log_escalation",
    "mcp__retail-tools__get_stockout_summary",
]
