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

from src import cafe24_client, kakao_client, notify, report_builder, smartstore_client  # noqa: E402

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
    "today": "오늘 누적 (지금까지)",
    "last_week": "지난주 (월~일)",
    "this_month": "이번달 (1일~지금)",
    "last_month": "지난달 전체",
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
    elif slot == "today":
        start = today_kst
        end = now_kst
        label = f"{start:%Y-%m-%d} 00:00 ~ {end:%H:%M} (오늘 누적)"
    elif slot == "last_week":
        # 이번주 월요일 - 7일 = 지난주 월요일
        days_since_monday = today_kst.weekday()  # 월=0, 일=6
        this_monday = today_kst - timedelta(days=days_since_monday)
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(seconds=1)
        start = last_monday
        end = last_sunday
        label = f"{start:%Y-%m-%d}(월) ~ {end:%Y-%m-%d}(일) 지난주"
    elif slot == "this_month":
        start = today_kst.replace(day=1)
        end = now_kst
        label = f"{start:%Y-%m} 1일 ~ {end:%m-%d %H:%M} (이번달 누적)"
    elif slot == "last_month":
        # 이번 달 1일 - 1일 = 지난달 마지막 날
        first_this_month = today_kst.replace(day=1)
        last_day_last_month = first_this_month - timedelta(seconds=1)
        first_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start = first_last_month
        end = last_day_last_month
        label = f"{start:%Y-%m} 1일 ~ {end:%Y-%m-%d} (지난달 전체)"
    else:
        raise ValueError(f"Unknown slot: {slot}")
    return start, end, label


def load_orders_real(start: datetime, end: datetime) -> tuple[list[dict], list[tuple[str, str]], list[str]]:
    """Returns (orders, expected_subchannels, errors)."""
    cafe = cafe24_client.from_env()
    smart = smartstore_client.from_env()
    errors: list[str] = []

    cafe_orders: list[dict] = []
    try:
        cafe_orders = [cafe.normalize(o) for o in cafe.fetch_orders(start, end)]
    except Exception as e:
        errors.append(f"카페24: {type(e).__name__}: {str(e)[:200]}")
        print(f"[ERR cafe24] {e}")

    smart_orders: list[dict] = []
    try:
        smart_orders = [smart.normalize(o) for o in smart.fetch_orders(start, end)]
    except Exception as e:
        errors.append(f"스마트스토어: {type(e).__name__}: {str(e)[:200]}")
        print(f"[ERR smartstore] {e}")

    expected = [("cafe24", name) for _, name in cafe.shops] + [("smartstore", smart.shop_name)]
    return cafe_orders + smart_orders, expected, errors


def load_orders_mock() -> tuple[list[dict], list[tuple[str, str]], list[str]]:
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
    return orders, expected, []


def _notifier_factory():
    """알림 채널 팩토리.
    - NOTIFY_CHANNEL=kakao (기본 운영): 카카오 우선 + 실패 시 dispatch 폴백(유실 방지).
    - NOTIFY_CHANNEL=kakao_only: 카카오만(폴백 없음).
    - 그 외(dispatch): 로컬 아웃박스 → Claude PushNotification."""
    ch = os.getenv("NOTIFY_CHANNEL", "dispatch").lower()
    if ch == "kakao":
        return notify.FallbackNotifier(kakao_client.from_env(), notify.from_env())
    if ch == "kakao_only":
        return kakao_client.from_env()
    return notify.from_env()


def run_backfill(days: int) -> int:
    """최근 N일(어제부터 과거로) 하루치 매출을 수집해 bks-os daily_sales 에 채운다.
    리포트/알림/커밋 없이 웹디비만 갱신 — 보드 공백 메우기용(workflow_dispatch)."""
    from src import bks_daily_sales
    now_kst = datetime.now(KST)
    today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    ok = 0
    for i in range(1, days + 1):
        d = today - timedelta(days=i)
        start = d
        end = d.replace(hour=23, minute=59, second=59)
        date_str = d.strftime("%Y-%m-%d")
        try:
            orders, expected, errs = load_orders_real(start, end)
            stats = report_builder.aggregate(orders, expected_subchannels=expected)
            label = f"{date_str} 00:00 ~ 23:59 (백필)"
            done = bks_daily_sales.push_daily_sales(date_str, stats, label)
            ok += 1 if done else 0
            print(f"[BACKFILL] {date_str}: {len(orders)}건 (errors={len(errs)}, saved={done})")
        except Exception as e:  # noqa: BLE001
            print(f"[BACKFILL] {date_str} 실패(계속): {e}")
    print(f"[BACKFILL] 완료 — {ok}/{days}일 daily_sales 채움")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=SLOTS.keys(), default="morning")
    parser.add_argument("--mock", action="store_true", help="Use mock fixtures (no API call)")
    parser.add_argument("--no-send", action="store_true", help="Print only, don't send/dispatch")
    parser.add_argument("--backfill-days", type=int, default=0,
                        help="최근 N일 daily_sales 백필(리포트·알림 없이 웹디비만 채움)")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    # ===== 백필 모드: 최근 N일 daily_sales 만 채움(웹디비 보드 공백 메우기) =====
    if args.backfill_days and args.backfill_days > 0:
        return run_backfill(args.backfill_days)

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
        result = alerts.run_morning_alerts(_notifier_factory)
        print(f"[ALERT] {result}")
        return 0

    now_kst = datetime.now(KST)
    start, end, period_label = slot_period(args.slot, now_kst)
    slot_label = f"{now_kst:%Y-%m-%d} {SLOTS[args.slot]}"

    fetch_errors: list[str] = []
    try:
        if args.mock or os.getenv("USE_MOCK") == "1":
            orders, expected, fetch_errors = load_orders_mock()
            print(f"[MOCK] {len(orders)} orders loaded from fixtures")
        else:
            orders, expected, fetch_errors = load_orders_real(start, end)
            print(f"[LIVE] {len(orders)} orders fetched (errors={len(fetch_errors)})")
            for e in fetch_errors:
                print(f"  [WARN] {e}")
    except Exception as e:
        # Catastrophic failure (e.g., env missing)
        traceback.print_exc()
        if not args.no_send:
            try:
                _notifier_factory().send_text(
                    f"⚠️ 주문 리포트 치명적 오류\nslot={args.slot}\n{type(e).__name__}: {e}"
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

    # bks-os 웹디비 daily_sales 동기화 — 단일 하루치 슬롯만(morning=전일 완전, today=오늘 누적).
    # 비차단: 실패해도 리포트/알림은 계속. env(BKS_SUPABASE_*) 없으면 조용히 skip.
    if not args.mock and args.slot in ("morning", "today"):
        try:
            from src import bks_daily_sales
            bks_daily_sales.push_daily_sales(start.strftime("%Y-%m-%d"), stats, period_label)
        except Exception as e:  # noqa: BLE001
            print(f"[BKS] daily_sales 동기화 skip: {e}")

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

    # 5. Build short Kakao message with URL (+ error footer if any channel failed)
    short_msg = report_builder.format_short_kakao(slot_label, period_label, stats, report_url)
    if fetch_errors:
        short_msg += "\n\n⚠️ 일부 채널 호출 실패:"
        for e in fetch_errors[:2]:
            # Show only channel name + status code, not full body
            short_e = e.split(":")[0] + " — " + (e.split("status=")[1].split(",")[0] if "status=" in e else "오류")
            short_msg += f"\n  {short_e}"
    print(f"\n{'=' * 50}\n[알림 메시지] ({len(short_msg)} chars)\n{'=' * 50}")
    print(short_msg)
    print("=" * 50 + "\n")

    if args.no_send or os.getenv("DRY_RUN") == "true":
        print(f"[DRY RUN] Skipping Kakao send. URL: {report_url}")
        return 0

    kc = _notifier_factory()
    result = kc.send_text(short_msg, link_url=report_url)
    print(f"[SEND] dispatch: {result}")
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
