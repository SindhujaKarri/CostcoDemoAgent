"""
log_escalation.py - Append a structured escalation record to escalations.jsonl

Usage:
    python log_escalation.py \
        --code E3 \
        --severity critical \
        --message "RetailCorp Brand SKU 88 out at 7 NA-WEST stores" \
        --action "Expedite PO with supplier, alert Regional VP + Merchandising" \
        --notify "Regional VP,Merchandising" \
        --sku 88 --region "NA-WEST" --stores "101,104,107,110,113,116,119"
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "escalations.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True, help="Escalation code e.g. E3")
    parser.add_argument("--severity", default="high", choices=["critical", "high", "medium", "low"])
    parser.add_argument("--message", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--notify", default="", help="Comma-separated list of stakeholders")
    parser.add_argument("--sku", type=int)
    parser.add_argument("--region", default="")
    parser.add_argument("--stores", default="", help="Comma-separated store IDs")
    parser.add_argument("--warehouse", default="")
    args = parser.parse_args()

    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "escalation_code": args.code,
        "severity": args.severity,
        "sku_id": args.sku,
        "region": args.region,
        "store_ids": [int(s.strip()) for s in args.stores.split(",") if s.strip()],
        "warehouse_id": args.warehouse,
        "message": args.message,
        "recommended_action": args.action,
        "notify": [n.strip() for n in args.notify.split(",") if n.strip()],
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

    print(json.dumps({"status": "logged", "record": record}, default=str))


if __name__ == "__main__":
    main()
