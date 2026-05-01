"""Entry point — runs the daily order report based on time slot."""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Ensure UTF-8 output on Windows (cp949 default cannot handle emoji/Korean reliably)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pytz
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import cafe24_client, kakao_client, report_builder, smartstore_client  # noqa: E402

KST = pytz.timezone("Asia/Seoul")

SLOTS = {
    "morning": "08:30 (어제 마감 요약)",
    "midday": "12:30 (오전 누적)",
    "evening": "18:00 (일일 마감)",
    "test": "TEST",
}


def slot_period(slot: str, now_kst: datetime) -> tuple[datetime, datetime, str]:
    """Return (start_dt, end_dt, period_label) for the given slot."""
    today_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_kst = today_kst - timedelta(days=1)

    if slot == "morning":
        start = yesterday_kst
        end = today_kst - timedelta(seconds=1)
        label = f"{start:%Y-%m-%d} 00:00 ~ 23:59 (전일)"
    elif slot == "midday":
        start = today_kst
        end = today_kst.replace(hour=12, minute=30)
        label = f"{start:%Y-%m-%d} 00:00 ~ 12:30"
    elif slot == "evening":
        start = today_kst
        end = today_kst.replace(hour=18, minute=0)
        label = f"{start:%Y-%m-%d} 00:00 ~ 18:00"
    elif slot == "test":
        start = today_kst - timedelta(days=1)
        end = now_kst
        label = f"{start:%Y-%m-%d %H:%M} ~ {end:%Y-%m-%d %H:%M} (TEST)"
    else:
        raise ValueError(f"Unknown slot: {slot}")
    return start, end, label


def load_orders_real(start: datetime, end: datetime) -> tuple[list[dict], list[tuple[str, str]]]:
    """Returns (orders, expected_subchannels) so report shows 0-count channels too."""
    cafe = cafe24_client.from_env()
    smart = smartstore_client.from_env()

    cafe_orders = [cafe.normalize(o) for o in cafe.fetch_orders(start, end)]
    smart_orders = [smart.normalize(o) for o in smart.fetch_orders(start, end)]

    expected = [("cafe24", name) for _, name in cafe.shops] + [("smartstore", "")]
    return cafe_orders + smart_orders, expected


def load_orders_mock() -> tuple[list[dict], list[tuple[str, str]]]:
    """Load fixture data for local development without real API keys."""
    fixtures = [
        ROOT / "tests" / "mock_cafe24.json",
        ROOT / "tests" / "mock_smartstore.json",
    ]
    orders: list[dict] = []
    for f in fixtures:
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            orders.extend(data)
    expected = [("cafe24", "기본몰"), ("smartstore", "")]
    return orders, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=SLOTS.keys(), required=True)
    parser.add_argument("--mock", action="store_true", help="Use mock fixtures (no API call)")
    parser.add_argument("--no-send", action="store_true", help="Print only, don't send Kakao")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    now_kst = datetime.now(KST)
    start, end, period_label = slot_period(args.slot, now_kst)
    slot_label = f"{now_kst:%Y-%m-%d} {SLOTS[args.slot]}"

    try:
        if args.mock or os.getenv("USE_MOCK") == "1":
            orders, expected = load_orders_mock()
            print(f"[MOCK] {len(orders)} orders loaded from fixtures")
        else:
            orders, expected = load_orders_real(start, end)
            print(f"[LIVE] {len(orders)} orders fetched ({start} ~ {end})")
    except Exception as e:
        traceback.print_exc()
        # Send error notification to Kakao instead of silently failing
        if not args.no_send and os.getenv("KAKAO_REFRESH_TOKEN"):
            try:
                kakao_client.from_env().send_text(
                    f"⚠️ 주문 리포트 실패\nslot={args.slot}\n{type(e).__name__}: {e}"
                )
            except Exception:
                pass
        return 1

    stats = report_builder.aggregate(orders, expected_subchannels=expected)
    messages = report_builder.format_report(slot_label, period_label, stats)

    for i, msg in enumerate(messages, 1):
        print(f"\n{'=' * 50}\n[Message {i}/{len(messages)}] ({len(msg)} chars)\n{'=' * 50}")
        print(msg)
    print("=" * 50 + "\n")

    if args.no_send or os.getenv("DRY_RUN") == "true":
        print(f"[DRY RUN] Skipping Kakao send ({len(messages)} message(s) would be sent).")
        return 0

    kc = kakao_client.from_env()
    import time as _t
    for i, msg in enumerate(messages, 1):
        result = kc.send_text(msg)
        print(f"[SEND {i}/{len(messages)}] Kakao response: {result}")
        if i < len(messages):
            _t.sleep(1)  # avoid rate-limit on consecutive sends
    return 0


if __name__ == "__main__":
    sys.exit(main())
