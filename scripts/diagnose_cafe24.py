"""Diagnose Cafe24 orders API parameter issue.

Tries multiple parameter combinations to identify which one causes 400.
Saves rotated refresh_token automatically.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.cafe24_client import from_env  # noqa: E402

import requests  # noqa: E402

API_VERSION = "2026-03-01"


def main() -> int:
    cafe = from_env()
    cafe._refresh_access_token()  # forces refresh + persists rotation
    print(f"[OK] access_token issued ({len(cafe.access_token)} chars)")
    print(f"[OK] refresh_token now ({len(cafe.refresh_token)} chars) — saved to .env")
    print()

    base_url = f"{cafe.base_url}/admin/orders"
    headers = {
        "Authorization": f"Bearer {cafe.access_token}",
        "X-Cafe24-Api-Version": API_VERSION,
    }

    test_cases = [
        ("minimal (start/end only)", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3}),
        ("+ date_type=order_date", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3, "date_type": "order_date"}),
        ("+ date_type=pay_date", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3, "date_type": "pay_date"}),
        ("with embed=items", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3, "embed": "items"}),
        ("with embed=items,buyer", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3, "embed": "items,buyer"}),
        ("with embed=items,receivers", {"start_date": "2026-04-25", "end_date": "2026-05-01", "limit": 3, "embed": "items,receivers"}),
        ("today only", {"start_date": "2026-05-01", "end_date": "2026-05-01", "limit": 3}),
        ("yesterday only", {"start_date": "2026-04-30", "end_date": "2026-04-30", "limit": 3}),
    ]

    for name, params in test_cases:
        print(f"--- {name} ---")
        try:
            r = requests.get(base_url, headers=headers, params=params, timeout=30)
            print(f"  status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                orders = data.get("orders", [])
                print(f"  orders returned: {len(orders)}")
                if orders:
                    keys = list(orders[0].keys())[:8]
                    print(f"  first order keys (sample): {keys}")
                print(f"  *** SUCCESS — use these params ***")
            else:
                print(f"  body: {r.text[:300]}")
        except Exception as e:
            print(f"  exception: {e}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
