"""Aggregate normalized orders and format report text."""
from __future__ import annotations

from collections import Counter
from typing import Any

# Kakao text message limit is 4000 chars; reserve buffer for header/footer
MAX_TEXT = 3800

CHANNEL_LABEL = {"cafe24": "C24", "smartstore": "SS"}


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
        status = (o.get("status") or "기타")
        by_status[status] += 1
        if any(k in status for k in ("취소", "환불", "반품", "CANCEL", "REFUND", "RETURN")):
            cs_count += 1
        for it in o.get("items", []):
            name = (it.get("name") or "").strip()[:30]
            if name:
                product_qty[name] += int(it.get("qty") or 0)

    # Sort orders for listing: newest first
    sorted_orders = sorted(
        orders,
        key=lambda o: o.get("order_date") or "",
        reverse=True,
    )

    return {
        "by_channel": by_channel,
        "by_status": dict(by_status),
        "top_products": product_qty.most_common(5),
        "all_products": product_qty.most_common(),
        "cs_count": cs_count,
        "total_count": sum(c["count"] for c in by_channel.values()),
        "total_amount": sum(c["amount"] for c in by_channel.values()),
        "orders_sorted": sorted_orders,
    }


def _short_order_id(oid: str) -> str:
    """Trim '20260501-0000193' to '193' or last 4 digits for compact display."""
    if not oid:
        return "?"
    if "-" in oid:
        return oid.split("-")[-1].lstrip("0") or "0"
    return oid[-6:]


def _format_order_line(o: dict[str, Any]) -> str:
    ch = CHANNEL_LABEL.get(o.get("channel"), "?")
    oid = _short_order_id(o.get("order_id") or "")
    status = o.get("status") or "?"
    amount = int(o.get("amount") or 0)
    items = o.get("items", []) or []

    # Item summary: "상품A×1, 상품B×2"
    item_parts = []
    for it in items:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        # Truncate long names
        if len(name) > 18:
            name = name[:17] + "…"
        qty = int(it.get("qty") or 0)
        item_parts.append(f"{name}×{qty}")
    item_str = ", ".join(item_parts) or "(상품정보없음)"

    return f"[{ch} #{oid}] {status} ₩{amount:,} — {item_str}"


def format_report(
    slot_label: str,
    period_label: str,
    stats: dict[str, Any],
) -> str:
    cafe24 = stats["by_channel"]["cafe24"]
    smart = stats["by_channel"]["smartstore"]

    status_line = " / ".join(f"{k} {v}" for k, v in sorted(stats["by_status"].items()))

    # Header section (always included)
    header = (
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
        f"▣ CS (취소/환불/반품)\n"
        f"   {stats['cs_count']}건"
    )

    # Top products (compact, 5 max)
    if stats["top_products"]:
        top_lines = "\n".join(
            f"   {i+1}. {name} — {qty}건"
            for i, (name, qty) in enumerate(stats["top_products"])
        )
        header += f"\n\n▣ 상품 TOP5\n{top_lines}"

    # Full order list (truncated to fit Kakao limit)
    orders = stats["orders_sorted"]
    if not orders:
        return header

    order_section = f"\n\n▣ 전체 주문 ({len(orders)}건)\n"
    available = MAX_TEXT - len(header) - len(order_section) - 50  # buffer for "..." line

    lines = []
    used = 0
    shown = 0
    for o in orders:
        line = "   " + _format_order_line(o) + "\n"
        if used + len(line) > available:
            break
        lines.append(line)
        used += len(line)
        shown += 1

    truncated = shown < len(orders)
    body = "".join(lines)
    if truncated:
        body += f"   ⋯ 외 {len(orders) - shown}건 (지면 한계로 생략)\n"

    return header + order_section + body.rstrip()
