# -*- coding: utf-8 -*-
"""매출 수집 워커 — bks-os `sales_sync_request` 큐를 폴링해 그 날짜 매출을 수집하고
`daily_sales` 에 upsert + 요청을 done 처리한다.

왜 PC에서 도는가: 네이버 커머스 API는 호출 IP 화이트리스트가 필수(전체허용 불가)라
클라우드(bks-os/Vercel)는 직접 수집이 불가능하다. 그래서 bks-os 는 "이 날짜 수집해줘"
요청만 큐에 넣고, 화이트리스트에 등록된 이 PC의 워커가 실제 수집을 대신한다(설계상 다리).

사용:
  python sales_sync_worker.py --once                 # pending 전부 1회 처리 후 종료 (스케줄러용)
  python sales_sync_worker.py --watch                # 15초마다 폴링(상주) → bks-os 클릭 후 거의 즉시 반영
  python sales_sync_worker.py --watch --interval 30  # 폴링 주기 변경
  python sales_sync_worker.py --date 2026-07-05      # 특정 날짜 직접 수집(큐 무관, 테스트/보정)

필요 .env: BKS_SUPABASE_URL, BKS_SUPABASE_SERVICE_ROLE_KEY (= bks-os '웹디비' 프로젝트) + 카페24·네이버 키.
  (봇 기존 SUPABASE_URL 은 주문 동기화용 — 건드리지 않는다. 이 워커는 bks-os DB 로만 붙는다.)
service_role 로 RLS 우회. bks-os 화면은 15초마다 daily_sales 를 새로고침해 자동 표시.
"""
from __future__ import annotations

import argparse
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pytz
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import report_builder  # noqa: E402
from src.main import load_orders_real  # noqa: E402

KST = pytz.timezone("Asia/Seoul")


def _client():
    """bks-os(웹디비) Supabase service_role 클라이언트(RLS 우회).

    봇의 기존 SUPABASE_URL(주문 동기화용, 다른 프로젝트일 수 있음)과 섞이지 않게
    BKS_ 전용 키를 우선 사용한다(없으면 SUPABASE_ 로 폴백). 미설정/오설정이면 명확히 실패.
    """
    import os

    url = os.getenv("BKS_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = os.getenv("BKS_SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit(
            "✗ BKS_SUPABASE_URL / BKS_SUPABASE_SERVICE_ROLE_KEY 미설정 — "
            ".env 에 bks-os(웹디비) 프로젝트의 Project URL · service_role 키를 넣으세요."
        )
    from supabase import create_client

    return create_client(url, key)


def collect_date(date_str: str) -> tuple[dict, list[str]]:
    """해당 날짜(KST 00:00~23:59:59) 매출 수집 → daily_sales payload + 채널 오류목록.

    네이버 24h 제한 안(하루 = 24h 미만)이라 청크 분할 불필요.
    """
    y, m, d = (int(x) for x in date_str.split("-"))
    start = KST.localize(datetime(y, m, d, 0, 0, 0))
    end = KST.localize(datetime(y, m, d, 23, 59, 59))
    orders, expected, errors = load_orders_real(start, end)
    stats = report_builder.aggregate(orders, expected_subchannels=expected)
    period_label = f"{date_str} 00:00 ~ 23:59 (전일 마감)"
    payload = report_builder.build_daily_sales(date_str, stats, period_label, slot_label=f"{date_str} 매출")
    return payload, errors


def upsert_daily_sales(client, payload: dict) -> None:
    client.table("daily_sales").upsert(payload, on_conflict="sale_date").execute()


def process_one(client, date_str: str) -> str:
    """한 날짜 수집·저장 → 사람이 읽는 결과 note 반환(요청 상태 기록용)."""
    payload, errors = collect_date(date_str)
    upsert_daily_sales(client, payload)
    note = f"{payload['total_count']}건 / ₩{payload['total_amount']:,}"
    if errors:
        note += " · ⚠️ " + " / ".join(e.split(":")[0] for e in errors)
    return note


def process_pending(client) -> int:
    """pending 요청 전부 처리(오래된 것부터). 처리 건수 반환."""
    res = (
        client.table("sales_sync_request")
        .select("id, sale_date")
        .eq("status", "pending")
        .order("requested_at")
        .execute()
    )
    rows = res.data or []
    if not rows:
        return 0
    done = 0
    for r in rows:
        rid, date_str = r["id"], str(r["sale_date"])[:10]
        print(f"[수집] {date_str} …", flush=True)
        try:
            note = process_one(client, date_str)
            client.table("sales_sync_request").update(
                {"status": "done", "note": note, "done_at": datetime.now(KST).isoformat()}
            ).eq("id", rid).execute()
            print(f"  ✅ {date_str}: {note}", flush=True)
            done += 1
        except Exception as e:  # 한 날짜 실패가 다른 날짜를 막지 않게
            msg = f"{type(e).__name__}: {str(e)[:180]}"
            traceback.print_exc()
            client.table("sales_sync_request").update(
                {"status": "error", "note": msg, "done_at": datetime.now(KST).isoformat()}
            ).eq("id", rid).execute()
            print(f"  ✗ {date_str}: {msg}", flush=True)
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="pending 전부 1회 처리 후 종료")
    g.add_argument("--watch", action="store_true", help="상주하며 주기적으로 폴링")
    g.add_argument("--date", metavar="YYYY-MM-DD", help="특정 날짜 직접 수집(큐 무관)")
    ap.add_argument("--interval", type=int, default=15, help="--watch 폴링 주기(초, 기본 15)")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")

    if args.date:
        client = _client()
        print(f"[직접수집] {args.date}", flush=True)
        note = process_one(client, args.date)
        print(f"✅ {args.date}: {note}", flush=True)
        return 0

    client = _client()
    if args.once:
        n = process_pending(client)
        print(f"완료 — {n}건 처리." if n else "대기 중인 요청 없음.", flush=True)
        return 0

    # --watch: 상주 폴링
    print(f"[워커 시작] {args.interval}초마다 sales_sync_request 폴링 (Ctrl+C 중지)", flush=True)
    while True:
        try:
            process_pending(client)
        except Exception as e:
            print(f"[워커 오류] {type(e).__name__}: {e}", flush=True)
        time.sleep(max(3, args.interval))


if __name__ == "__main__":
    sys.exit(main())
