"""Aggregate normalized orders and format report text."""
from __future__ import annotations

from collections import Counter
from typing import Any


def aggregate(orders: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate normalized orders into report-ready stats."""
    by_channel: dict[str, dict[str, int]] = {
        "cafe24": {"count": 0, "amount": 0},
        "smartstore": {"count": 0, "amount": 0},
    }
    by_status: Counter[str] = Counter()
    product_qty: Counter[str] = Counter()
    cs_count = 0

    for o in orders:
        ch = o["channel"]
        if ch in by_channel:
            by_channel[ch]["count"] += 1
            by_channel[ch]["amount"] += int(o.get("amount") or 0)
        status = (o.get("status") or "기타").upper()
        by_status[status] += 1
        if any(k in status for k in ("CANCEL", "취소", "REFUND", "환불", "RETURN", "반품")):
            cs_count += 1
        for it in o.get("items", []):
            name = (it.get("name") or "").strip()[:30]
            if name:
                product_qty[name] += int(it.get("qty") or 0)

    return {
        "by_channel": by_channel,
        "by_status": dict(by_status),
        "top_products": product_qty.most_common(3),
        "cs_count": cs_count,
        "total_count": sum(c["count"] for c in by_channel.values()),
        "total_amount": sum(c["amount"] for c in by_channel.values()),
    }


def format_report(
    slot_label: str,
    period_label: str,
    stats: dict[str, Any],
) -> str:
    cafe24 = stats["by_channel"]["cafe24"]
    smart = stats["by_channel"]["smartstore"]

    status_line = " / ".join(f"{k} {v}" for k, v in sorted(stats["by_status"].items()))
    top_lines = "\n".join(
        f"   {i+1}. {name} — {qty}건"
        for i, (name, qty) in enumerate(stats["top_products"])
    ) or "   (데이터 없음)"

    return (
        f"📦 {slot_label} 일일 리포트\n"
        f"\n"
        f"▣ 기간: {period_label}\n"
        f"\n"
        f"▣ 채널별\n"
        f"   카페24       : {cafe24['count']:>3}건 / ₩{cafe24['amount']:,}\n"
        f"   스마트스토어 : {smart['count']:>3}건 / ₩{smart['amount']:,}\n"
        f"   ─────────────────────\n"
        f"   합계         : {stats['total_count']:>3}건 / ₩{stats['total_amount']:,}\n"
        f"\n"
        f"▣ 상태\n"
        f"   {status_line or '(없음)'}\n"
        f"\n"
        f"▣ 상품 TOP3\n"
        f"{top_lines}\n"
        f"\n"
        f"▣ CS (취소/환불/반품)\n"
        f"   {stats['cs_count']}건"
    )
