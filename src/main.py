"""Entry point — runs the daily order report based on time slot."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
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

try:
    from src import supabase_sync  # noqa: E402
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

KST = pytz.timezone("Asia/Seoul")

SLOTS = {
    "morning": "08:30 (어제 마감 요약)",
    "midday": "12:30 (오전 누적)",
    "evening": "18:00 (일일 마감)",
    "test": "TEST",
    "alert": "09:00 (지연/재고 알림)",
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

    expected = [("cafe24", name) for _, name in cafe.shops] + [("smartstore", smart.shop_name)]
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

    # ===== Alert mode (지연 + 재고 부족) =====
    if args.slot == "alert":
        from src import alerts
        if args.no_send or os.getenv("DRY_RUN") == "true":
            delays = alerts.detect_delays()
            low = alerts.detect_low_stock(threshold=5)
            print(f"[DRY] delays={len(delays)}, low_stock={len(low)}")
            if delays:
                print("\n=== 지연 메시지 ===\n" + alerts.format_delay_message(delays))
            if low:
                print("\n=== 재고 부족 메시지 ===\n" + alerts.format_low_stock_message(low))
            return 0
        result = alerts.run_morning_alerts(kakao_client.from_env)
        print(f"[ALERT] {result}")
        return 0

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

    # Sync orders to Supabase (silent if not configured)
    if HAS_SUPABASE and orders and not args.mock:
        try:
            sync_result = supabase_sync.sync_orders(orders)
            if not sync_result.get("skipped"):
                print(f"[SUPABASE] {sync_result.get('inserted', 0)} rows upserted "
                      f"(mapped={sync_result.get('mapped', 0)}, unmapped={sync_result.get('unmapped', 0)})")
        except Exception as e:
            print(f"[SUPABASE] sync error (continuing without sync): {e}")

    stats = report_builder.aggregate(orders, expected_subchannels=expected)

    # 1. Generate HTML report
    date_str = now_kst.strftime("%Y-%m-%d")
    slot_filename = f"{date_str}-{args.slot}.html"
    reports_dir = ROOT / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / slot_filename
    html = report_builder.format_html_report(
        slot_label, period_label, stats,
        generated_at=now_kst.strftime("%Y-%m-%d %H:%M KST"),
    )
    report_path.write_text(html, encoding="utf-8")
    print(f"[HTML] Saved: {report_path} ({len(html):,} chars)")

    # 2. Update reports index
    _update_reports_index(reports_dir)

    # 3. Build report URL (GitHub Pages)
    repo_url_env = os.getenv("REPORT_BASE_URL", "https://nakedsoul75.github.io/daily-order-report/reports")
    report_url = f"{repo_url_env.rstrip('/')}/{slot_filename}"

    # 4. Auto-commit and push (so GitHub Pages updates)
    if not args.no_send and not os.getenv("SKIP_GIT_PUSH"):
        _git_publish(report_path, slot_label)

    # 5. Build short Kakao message with URL
    short_msg = report_builder.format_short_kakao(slot_label, period_label, stats, report_url)
    print(f"\n{'=' * 50}\n[Kakao Message] ({len(short_msg)} chars)\n{'=' * 50}")
    print(short_msg)
    print("=" * 50 + "\n")

    if args.no_send or os.getenv("DRY_RUN") == "true":
        print(f"[DRY RUN] Skipping Kakao send. URL: {report_url}")
        return 0

    kc = kakao_client.from_env()
    result = kc.send_text(short_msg, link_url=report_url)
    print(f"[SEND] Kakao response: {result}")
    print(f"[REPORT URL] {report_url}")
    return 0


def _update_reports_index(reports_dir: Path) -> None:
    """Generate index.html listing all reports, newest first."""
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\w+)\.html$")
    entries = []
    for f in reports_dir.iterdir():
        m = pattern.match(f.name)
        if m and f.name != "index.html":
            entries.append((m.group(1), m.group(2), f.name))
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)
    index_html = report_builder.format_index_html(entries)
    (reports_dir / "index.html").write_text(index_html, encoding="utf-8")


def _git_publish(report_path: Path, slot_label: str) -> None:
    """Commit and push the new report so GitHub Pages updates."""
    try:
        subprocess.run(
            ["git", "add", "docs/reports/"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        # Check if anything actually changed
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=ROOT, capture_output=True,
        )
        if diff.returncode == 0:
            print("[GIT] No changes to push.")
            return
        subprocess.run(
            ["git", "commit", "-m", f"Report: {slot_label}"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=ROOT, check=True, capture_output=True, text=True, timeout=60,
        )
        print("[GIT] Pushed to GitHub. Pages will update in 1-2 min.")
    except subprocess.CalledProcessError as e:
        print(f"[GIT WARN] {e.stderr if e.stderr else e}")
    except Exception as e:
        print(f"[GIT WARN] {type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.exit(main())
