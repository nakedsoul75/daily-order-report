"""Diagnose Naver Commerce API issues."""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.smartstore_client import from_env  # noqa: E402

import pytz  # noqa: E402
import requests  # noqa: E402

KST = pytz.timezone("Asia/Seoul")


def main() -> int:
    smart = from_env()

    # Step 1: Token issue
    print("=== Step 1: Token issue ===")
    try:
        smart._refresh_access_token()
        print(f"  OK access_token len={len(smart.access_token)}")
        print(f"  expires_at: {smart.token_expires_at}")
    except requests.HTTPError as e:
        print(f"  FAIL status={e.response.status_code}")
        print(f"  body: {e.response.text[:500]}")
        return 1
    print()

    base = smart.BASE_URL
    headers = {"Authorization": f"Bearer {smart.access_token}"}

    # Step 2: try last-changed-statuses with various ranges/types
    now = datetime.now(KST)
    cases = [
        ("PAYED last 1h", {
            "lastChangedFrom": (now - timedelta(hours=1)).isoformat(timespec="milliseconds"),
            "lastChangedTo": now.isoformat(timespec="milliseconds"),
            "lastChangedType": "PAYED",
        }),
        ("PAY_WAITING last 1h", {
            "lastChangedFrom": (now - timedelta(hours=1)).isoformat(timespec="milliseconds"),
            "lastChangedTo": now.isoformat(timespec="milliseconds"),
            "lastChangedType": "PAY_WAITING",
        }),
        ("no type, last 1h", {
            "lastChangedFrom": (now - timedelta(hours=1)).isoformat(timespec="milliseconds"),
            "lastChangedTo": now.isoformat(timespec="milliseconds"),
        }),
        ("PAYED last 24h", {
            "lastChangedFrom": (now - timedelta(hours=24)).isoformat(timespec="milliseconds"),
            "lastChangedTo": now.isoformat(timespec="milliseconds"),
            "lastChangedType": "PAYED",
        }),
        ("PAYED yesterday only", {
            "lastChangedFrom": (now - timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(timespec="milliseconds"),
            "lastChangedTo": (now - timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat(timespec="milliseconds"),
            "lastChangedType": "PAYED",
        }),
    ]

    for name, params in cases:
        print(f"--- {name} ---")
        try:
            r = requests.get(
                f"{base}/v1/pay-order/seller/product-orders/last-changed-statuses",
                headers=headers, params=params, timeout=30
            )
            print(f"  status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                count = len(d.get("data", {}).get("lastChangeStatuses", [])) if d.get("data") else 0
                print(f"  changed orders: {count}")
                if count > 0:
                    sample = d["data"]["lastChangeStatuses"][0]
                    print(f"  sample keys: {list(sample.keys())}")
                print(f"  *** SUCCESS ***")
            else:
                print(f"  body: {r.text[:400]}")
        except Exception as e:
            print(f"  exception: {type(e).__name__}: {e}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
