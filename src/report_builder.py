"""Aggregate normalized orders and format report text into one or more Kakao messages."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

# Kakao text limit is 4000 chars; leave buffer for header/index suffix
MAX_TEXT = 3800

CHANNEL_LABEL = {"cafe24": "C24", "smartstore": "SS"}


def aggregate(orders: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate normalized orders into report-ready stats."""
    by_channel: dict[str, dict[str, int]] = {
        "cafe24": {"count": 0, "amount": 0, "cash": 0},
        "smartstore": {"count": 0, "amount": 0, "cash": 0},
    }
    by_status: Counter[str] = Counter()
    product_qty: Counter[str] = Counter()
    cs_count = 0
    new_buyer_count = 0

    for o in orders:
        ch = o["channel"]
        if ch in by_channel:
            by_channel[ch]["count"] += 1
            by_channel[ch]["amount"] += int(o.get("amount") or 0)
            by_channel[ch]["cash"] += int(o.get("cash_paid") or 0)
        status = o.get("status") or "기타"
        by_status[status] += 1
        if any(k in status for k in ("취소", "환불", "반품", "CANCEL", "REFUND", "RETURN")):
            cs_count += 1
        if o.get("first_order"):
            new_buyer_count += 1
        for it in o.get("items", []):
            name = (it.get("name") or "").strip()[:30]
            if name:
                product_qty[name] += int(it.get("qty") or 0)

    sorted_orders = sorted(
        orders,
        key=lambda o: o.get("order_date") or "",
        reverse=True,
    )

    return {
        "by_channel": by_channel,
        "by_status": dict(by_status),
        "top_products": product_qty.most_common(5),
        "cs_count": cs_count,
        "new_buyer_count": new_buyer_count,
        "total_count": sum(c["count"] for c in by_channel.values()),
        "total_amount": sum(c["amount"] for c in by_channel.values()),
        "total_cash": sum(c["cash"] for c in by_channel.values()),
        "orders_sorted": sorted_orders,
    }


def _short_order_id(oid: str) -> str:
    if not oid:
        return "?"
    if "-" in oid:
        return oid.split("-")[-1].lstrip("0") or "0"
    return oid[-6:]


def _mask_name(name: str) -> str:
    """홍길동 → 홍**, 김철 → 김*, 이수민철 → 이**철."""
    if not name:
        return "익명"
    name = name.strip()
    n = len(name)
    if n == 1:
        return name
    if n == 2:
        return name[0] + "*"
    if n == 3:
        return name[0] + "**"
    # n >= 4: keep first and last, mask middle
    return name[0] + "*" * (n - 2) + name[-1]


def _extract_time(order_date: str) -> str:
    """'2026-05-01T13:32:06+09:00' → '13:32'."""
    if not order_date:
        return ""
    try:
        # Handle ISO 8601 with various forms
        if "T" in order_date:
            time_part = order_date.split("T")[1]
            return time_part[:5]  # HH:MM
    except Exception:
        pass
    return ""


def _format_order_line(o: dict[str, Any]) -> str:
    """Format: [C24 #193] (홍**) 13:32 결제완료⭐ ₩25,500 — 상품×1, 상품×2"""
    ch = CHANNEL_LABEL.get(o.get("channel"), "?")
    oid = _short_order_id(o.get("order_id") or "")
    buyer = _mask_name(o.get("buyer_name") or "")
    time_str = _extract_time(o.get("order_date") or "")
    status = o.get("status") or "?"
    new_marker = "⭐신규" if o.get("first_order") else ""
    amount = int(o.get("amount") or 0)
    cash = int(o.get("cash_paid") or 0)
    items = o.get("items", []) or []

    item_parts = []
    for it in items:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        if len(name) > 18:
            name = name[:17] + "…"
        qty = int(it.get("qty") or 0)
        item_parts.append(f"{name}×{qty}")
    item_str = ", ".join(item_parts) or "(상품정보없음)"

    # If amount differs from cash (적립금/할인 사용), show both compactly
    money_str = f"₩{amount:,}"
    if cash > 0 and cash != amount:
        money_str += f" (실결제 ₩{cash:,})"

    parts = [f"[{ch} #{oid}]", f"({buyer})", time_str, f"{status}{new_marker}", money_str, "—", item_str]
    return " ".join(p for p in parts if p)


def _build_header(slot_label: str, period_label: str, stats: dict[str, Any]) -> str:
    cafe24 = stats["by_channel"]["cafe24"]
    smart = stats["by_channel"]["smartstore"]
    status_line = " / ".join(f"{k} {v}" for k, v in sorted(stats["by_status"].items()))

    # Show 매출 (amount) and 실결제 (cash) if they differ
    cash_note = ""
    if stats["total_cash"] != stats["total_amount"]:
        cash_note = f"\n   (실 카드결제 합계: ₩{stats['total_cash']:,})"

    new_note = f" / 신규 {stats['new_buyer_count']}" if stats["new_buyer_count"] > 0 else ""

    header = (
        f"📦 {slot_label} 일일 리포트\n"
        f"\n"
        f"▣ 기간: {period_label}\n"
        f"\n"
        f"▣ 채널별 (매출 기준)\n"
        f"   카페24       : {cafe24['count']:>3}건 / ₩{cafe24['amount']:,}\n"
        f"   스마트스토어 : {smart['count']:>3}건 / ₩{smart['amount']:,}\n"
        f"   ─────────────────────\n"
        f"   합계         : {stats['total_count']:>3}건 / ₩{stats['total_amount']:,}{new_note}"
        f"{cash_note}\n"
        f"\n"
        f"▣ 상태\n"
        f"   {status_line or '(없음)'}\n"
        f"\n"
        f"▣ CS (취소/환불/반품)\n"
        f"   {stats['cs_count']}건"
    )

    if stats["top_products"]:
        top_lines = "\n".join(
            f"   {i+1}. {name} — {qty}건"
            for i, (name, qty) in enumerate(stats["top_products"])
        )
        header += f"\n\n▣ 상품 TOP5\n{top_lines}"

    return header


def format_report(
    slot_label: str,
    period_label: str,
    stats: dict[str, Any],
) -> list[str]:
    """Return a list of messages — split if too long for one Kakao message.

    Returns:
        List of strings, each <= MAX_TEXT chars. First message contains header.
    """
    header = _build_header(slot_label, period_label, stats)
    orders = stats["orders_sorted"]

    if not orders:
        return [header]

    # Build all order lines first
    order_lines = ["   " + _format_order_line(o) for o in orders]
    total = len(orders)

    # Pack into messages: first message has header + as many lines as fit, rest pack lines only
    messages: list[str] = []
    section_title = f"\n\n▣ 전체 주문 ({total}건)\n"

    current = header + section_title
    current_lines: list[str] = []
    line_idx = 0

    while line_idx < len(order_lines):
        candidate = current + "\n".join(current_lines + [order_lines[line_idx]])
        # Reserve room for "(N/M)" footer
        if len(candidate) > MAX_TEXT - 20:
            # Flush current message and start a new one
            if current_lines:
                messages.append(current + "\n".join(current_lines))
                current = f"📦 {slot_label} 일일 리포트 — 전체 주문 (이어서)\n\n"
                current_lines = []
            else:
                # Edge case: header alone too big — force append the line anyway
                messages.append(current + order_lines[line_idx])
                current = f"📦 {slot_label} 일일 리포트 — 전체 주문 (이어서)\n\n"
                current_lines = []
                line_idx += 1
        else:
            current_lines.append(order_lines[line_idx])
            line_idx += 1

    if current_lines:
        messages.append(current + "\n".join(current_lines))

    # Add (N/M) suffix to each message if more than one
    if len(messages) > 1:
        n = len(messages)
        messages = [m + f"\n\n— ({i+1}/{n}) —" for i, m in enumerate(messages)]

    return messages
