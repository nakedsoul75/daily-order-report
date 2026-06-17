"""옵션 A 검증 — '조건형 상품주문 상세조회' (PAYED_DATETIME) 실응답 구조 파악.

GET /external/v1/pay-order/seller/product-orders
    rangeType=PAYED_DATETIME, from, to(<=24h), pageSize, page

목적: 페이지네이션 방식(page/totalPages vs moreSequence), status 필드명,
금액 필드명, 주문 1건의 키 구조를 실제 응답으로 확정한다.
개인정보(name/tel/address 등)는 출력 시 마스킹.
1회성 진단 — 운영 코드 아님.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from src.smartstore_client import from_env  # noqa: E402

import pytz  # noqa: E402
import requests  # noqa: E402

KST = pytz.timezone("Asia/Seoul")

SENSITIVE = (
    "name", "tel", "phone", "address", "email", "zip", "contact",
    "orderer", "receiver", "mobile",
)


def mask(obj, key=""):
    kl = str(key).lower()
    if isinstance(obj, dict):
        return {k: mask(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        head = [mask(v, key) for v in obj[:2]]
        if len(obj) > 2:
            head.append(f"...(+{len(obj) - 2} more, total {len(obj)})")
        return head
    if isinstance(obj, str):
        if any(s in kl for s in SENSITIVE):
            return "***"
        return obj if len(obj) <= 50 else obj[:50] + "..."
    return obj


def call(smart, params):
    return requests.get(
        f"{smart.BASE_URL}/v1/pay-order/seller/product-orders",
        headers={"Authorization": f"Bearer {smart.access_token}"},
        params=params,
        timeout=30,
    )


def main() -> int:
    smart = from_env()
    smart._refresh_access_token()
    print(f"token OK len={len(smart.access_token)}\n")

    now = datetime.now(KST)
    # 며칠 전 하루(24h window) — 결제 건이 있을 가능성이 높은 과거 날짜
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    d0 = (now - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)
    d1 = d0.replace(hour=23, minute=59, second=59)

    cases = [
        ("PAYED_DATETIME 24h from+to page1", {
            "rangeType": "PAYED_DATETIME",
            "from": d0.isoformat(timespec="milliseconds"),
            "to": d1.isoformat(timespec="milliseconds"),
            "pageSize": 100,
            "page": 1,
        }),
        ("PAYED_DATETIME from-only (no to)", {
            "rangeType": "PAYED_DATETIME",
            "from": d0.isoformat(timespec="milliseconds"),
            "pageSize": 100,
            "page": 1,
        }),
    ]

    for name, params in cases:
        print(f"===== {name} =====")
        print(f"params: {params}")
        try:
            r = call(smart, params)
            print(f"status: {r.status_code}")
            try:
                body = r.json()
            except Exception:
                print(f"non-json body: {r.text[:500]}")
                print()
                continue
            if r.status_code != 200:
                print(json.dumps(body, ensure_ascii=False, indent=2)[:1000])
                print()
                continue
            # 페이지네이션/카운트 키만 먼저 요약
            data = body.get("data")
            if isinstance(data, dict):
                meta = {k: v for k, v in data.items() if not isinstance(v, (list, dict))}
                print(f"data scalar keys: {meta}")
                for k, v in data.items():
                    if isinstance(v, list):
                        print(f"data['{k}'] is list, len={len(v)}")
                    elif isinstance(v, dict):
                        print(f"data['{k}'] is dict, keys={list(v.keys())}")
            elif isinstance(data, list):
                print(f"data is list, len={len(data)}")
            print("--- masked full body (truncated) ---")
            print(json.dumps(mask(body), ensure_ascii=False, indent=2)[:3500])
        except Exception as e:
            print(f"exception: {type(e).__name__}: {e}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
