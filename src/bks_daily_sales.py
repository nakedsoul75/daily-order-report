"""bks-os '웹디비' daily_sales 동기화.

자동봇(main.py)이 이미 집계한 stats 를 bks-os 영업·매출 화면이 읽는 daily_sales 테이블에
그대로 upsert 한다. sales_sync_worker.py(PC 폴링) 없이도 매일 자동으로 보드가 채워지게 하는 목적.

필요 env: BKS_SUPABASE_URL, BKS_SUPABASE_SERVICE_ROLE_KEY (= bks-os '웹디비' 프로젝트).
미설정이면 조용히 skip(비차단) — 기존 리포트/알림 흐름엔 영향 없음.
"""
from __future__ import annotations

import os
from typing import Any

from src import report_builder


def _client():
    url = os.getenv("BKS_SUPABASE_URL")
    key = os.getenv("BKS_SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[BKS] BKS_SUPABASE_URL / BKS_SUPABASE_SERVICE_ROLE_KEY 미설정 — daily_sales 동기화 skip")
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except ImportError:
        print("[BKS] 'supabase' 패키지 없음 — pip install supabase")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[BKS] init 실패: {e}")
        return None


def push_daily_sales(sale_date: str, stats: dict[str, Any], period_label: str) -> bool:
    """집계 stats → daily_sales payload upsert(on_conflict=sale_date). 성공 시 True.

    비차단: env 미설정·오류여도 예외를 던지지 않고 False 반환(리포트 흐름 보호).
    """
    client = _client()
    if client is None:
        return False
    try:
        payload = report_builder.build_daily_sales(
            sale_date, stats, period_label, slot_label=f"{sale_date} 매출"
        )
        client.table("daily_sales").upsert(payload, on_conflict="sale_date").execute()
        print(
            f"[BKS] daily_sales upsert {sale_date}: "
            f"{payload.get('total_count', 0)}건 / ₩{payload.get('total_amount', 0):,}"
        )
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[BKS] daily_sales 실패(무시): {e}")
        return False
