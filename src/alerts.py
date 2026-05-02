"""출하 지연 + 재고 부족 알림 — Supabase 조회 기반."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytz

KST = pytz.timezone("Asia/Seoul")
DELAY_DAYS = 5  # 주문 후 N일 지나면 지연


def _get_client():
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"[ALERTS] Supabase init failed: {e}")
        return None


def detect_delays() -> list[dict]:
    """주문 후 DELAY_DAYS+ 경과 + 송장 없음 + 취소 아님 → DELAYED 마킹 + 반환."""
    client = _get_client()
    if client is None:
        return []

    now = datetime.now(KST)
    cutoff = (now - timedelta(days=DELAY_DAYS)).isoformat()

    # 지연 후보: tracking_no NULL + status != CANCELED + order_date < cutoff
    res = (
        client.table("orders")
        .select("id,sub_channel,order_no,product_name,option_name,qty,amount,buyer_name,order_date,ea_code")
        .is_("tracking_no", "null")
        .neq("status", "CANCELED")
        .lt("order_date", cutoff)
        .order("order_date")
        .execute()
    )
    delayed = res.data or []

    # 상태 업데이트 (한 번에)
    if delayed:
        ids = [r["id"] for r in delayed]
        try:
            client.table("orders").update({"status": "DELAYED"}).in_("id", ids).execute()
        except Exception as e:
            print(f"[ALERTS] status update err: {e}")

    return delayed


def detect_low_stock(threshold: int = 5) -> list[dict]:
    """재고 N개 이하 SKU 조회."""
    client = _get_client()
    if client is None:
        return []

    try:
        # inventory view from Supabase
        res = client.table("inventory").select("ea_code,name,option_name,current_stock,outbound_total")\
            .lte("current_stock", threshold).order("current_stock").limit(50).execute()
        return res.data or []
    except Exception as e:
        print(f"[ALERTS] low stock query err: {e}")
        return []


def format_delay_message(delays: list[dict]) -> str:
    if not delays:
        return ""

    now = datetime.now(KST)
    lines = [f"⚠️ 출하 지연 알림 ({len(delays)}건)\n", f"{DELAY_DAYS}일 이상 미출하:\n"]

    for d in delays[:25]:  # 최대 25건만
        try:
            od = datetime.fromisoformat(d["order_date"].replace("Z", "+00:00"))
            days_ago = (now - od.astimezone(KST)).days
        except Exception:
            days_ago = "?"
        ch = d.get("sub_channel") or "?"
        nm = (d.get("product_name") or "?")[:30]
        opt = d.get("option_name") or ""
        opt_str = f" ({opt[:20]})" if opt else ""
        lines.append(f"\n🔴 [{ch} #{d['order_no']}]")
        lines.append(f"   {nm}{opt_str} ×{d.get('qty', 1)}")
        lines.append(f"   주문 {od.strftime('%m-%d')} → {days_ago}일 경과")

    if len(delays) > 25:
        lines.append(f"\n... 외 {len(delays) - 25}건")

    return "\n".join(lines)


def format_low_stock_message(items: list[dict], threshold: int = 5) -> str:
    if not items:
        return ""

    lines = [f"🟡 재고 부족 알림 ({len(items)}개 SKU)\n", f"{threshold}개 이하:\n"]
    for it in items[:30]:
        nm = (it.get("name") or "?")[:25]
        opt = it.get("option_name") or ""
        opt_str = f" / {opt[:15]}" if opt else ""
        stock = it.get("current_stock", 0)
        out = it.get("outbound_total", 0)
        lines.append(f"\n• {nm}{opt_str}")
        lines.append(f"  현재 {stock}개 (누적 출하 {out}개)")

    if len(items) > 30:
        lines.append(f"\n... 외 {len(items) - 30}개 SKU")
    return "\n".join(lines)


def run_morning_alerts(kakao_client_factory) -> dict:
    """매일 09:00 실행. 지연 + 재고 부족 알림 발송."""
    result = {"delayed": 0, "low_stock": 0, "messages_sent": 0}

    # 지연
    delays = detect_delays()
    result["delayed"] = len(delays)
    if delays:
        msg = format_delay_message(delays)
        try:
            kc = kakao_client_factory()
            kc.send_text(msg)
            result["messages_sent"] += 1
            print(f"[ALERT] delay message sent ({len(delays)} orders)")
        except Exception as e:
            print(f"[ALERT] delay send fail: {e}")

    # 재고 부족
    low = detect_low_stock(threshold=5)
    result["low_stock"] = len(low)
    if low:
        msg = format_low_stock_message(low, threshold=5)
        try:
            kc = kakao_client_factory()
            kc.send_text(msg)
            result["messages_sent"] += 1
            print(f"[ALERT] low stock message sent ({len(low)} SKUs)")
        except Exception as e:
            print(f"[ALERT] low stock send fail: {e}")

    if not delays and not low:
        print("[ALERT] no delays / no low stock — no message sent")

    return result
