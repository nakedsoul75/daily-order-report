"""Aggregate normalized orders and format report text into one or more Kakao messages."""
from __future__ import annotations

from collections import Counter, OrderedDict
from datetime import datetime
from typing import Any

# Kakao text limit is 4000 chars; leave buffer for header/index suffix
MAX_TEXT = 3800


def _subchannel_key(o: dict[str, Any]) -> tuple[str, str]:
    """Return (channel, subname) tuple for grouping."""
    if o["channel"] == "cafe24":
        return ("cafe24", o.get("shop_name") or f"shop{o.get('shop_no', '?')}")
    return ("smartstore", o.get("shop_name") or "")


def _subchannel_label(ch: str, sub: str, *, full: bool = True) -> str:
    """Display label for header (full=True) or order line (full=False)."""
    if ch == "cafe24":
        if full:
            return f"카페24 ({sub})" if sub else "카페24"
        return f"C24/{sub[:3]}" if sub else "C24"
    # smartstore
    if full:
        return f"스마트스토어 ({sub})" if sub else "스마트스토어"
    return f"SS/{sub[:3]}" if sub else "SS"


def aggregate(
    orders: list[dict[str, Any]],
    expected_subchannels: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Aggregate normalized orders into report-ready stats.

    expected_subchannels: pre-populate these (channel, name) tuples with zeros
        so they always appear in the report even if 0 orders.
    """
    by_subchannel: "OrderedDict[tuple[str,str], dict[str,int]]" = OrderedDict()
    if expected_subchannels:
        for sk in expected_subchannels:
            by_subchannel[sk] = {"count": 0, "amount": 0, "cash": 0}

    by_status: Counter[str] = Counter()
    product_qty: Counter[str] = Counter()
    cs_count = 0
    new_buyer_count = 0

    for o in orders:
        sk = _subchannel_key(o)
        if sk not in by_subchannel:
            by_subchannel[sk] = {"count": 0, "amount": 0, "cash": 0}
        by_subchannel[sk]["count"] += 1
        by_subchannel[sk]["amount"] += int(o.get("amount") or 0)
        by_subchannel[sk]["cash"] += int(o.get("cash_paid") or 0)

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

    sorted_orders = sorted(orders, key=lambda o: o.get("order_date") or "", reverse=True)

    return {
        "by_subchannel": by_subchannel,
        "by_status": dict(by_status),
        "top_products": product_qty.most_common(5),
        "cs_count": cs_count,
        "new_buyer_count": new_buyer_count,
        "total_count": sum(c["count"] for c in by_subchannel.values()),
        "total_amount": sum(c["amount"] for c in by_subchannel.values()),
        "total_cash": sum(c["cash"] for c in by_subchannel.values()),
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
    """Format: [C24/한국어 #193] (홍**) 13:32 결제완료⭐신규 ₩25,500 — 상품×1"""
    ch, sub = _subchannel_key(o)
    ch = _subchannel_label(ch, sub, full=False)
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

    money_str = f"₩{amount:,}"
    if cash > 0 and cash != amount:
        money_str += f" (실결제 ₩{cash:,})"

    parts = [f"[{ch} #{oid}]", f"({buyer})", time_str, f"{status}{new_marker}", money_str, "—", item_str]
    return " ".join(p for p in parts if p)


def _format_grouped_line(group: list[dict[str, Any]]) -> str:
    """Format multiple orders by same buyer/minute as one line.

    Example:
      [SS/콤마 7건묶음] (이**) 10:44 결제완료 ₩631,000 — 행거프레임×1, r행어×1, ... +5
    """
    first = group[0]
    ch, sub = _subchannel_key(first)
    ch = _subchannel_label(ch, sub, full=False)
    n = len(group)
    buyer = _mask_name(first.get("buyer_name") or "")
    time_str = _extract_time(first.get("order_date") or "")
    status = first.get("status") or "?"
    new_marker = "⭐신규" if any(o.get("first_order") for o in group) else ""
    total_amount = sum(int(o.get("amount") or 0) for o in group)
    total_cash = sum(int(o.get("cash_paid") or 0) for o in group)

    # Collect items across all orders
    all_items = []
    for o in group:
        for it in o.get("items", []):
            name = (it.get("name") or "").strip()
            qty = int(it.get("qty") or 0)
            if name:
                all_items.append((name, qty))

    # Show first 3 items, then "+N more"
    shown_count = 3
    item_parts = []
    for name, qty in all_items[:shown_count]:
        if len(name) > 14:
            name = name[:13] + "…"
        item_parts.append(f"{name}×{qty}")
    item_str = ", ".join(item_parts)
    if len(all_items) > shown_count:
        item_str += f" +{len(all_items) - shown_count}"

    money_str = f"₩{total_amount:,}"
    if total_cash > 0 and total_cash != total_amount:
        money_str += f" (실결제 ₩{total_cash:,})"

    parts = [f"[{ch} {n}건묶음]", f"({buyer})", time_str, f"{status}{new_marker}", money_str, "—", item_str]
    return " ".join(p for p in parts if p)


def _group_orders(orders: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group orders by (channel, shop, buyer, time-minute). 1-order groups stay solo."""
    grouped: "OrderedDict[tuple, list[dict[str, Any]]]" = OrderedDict()
    for o in orders:
        ch, sub = _subchannel_key(o)
        buyer = (o.get("buyer_name") or "").strip()
        time_str = _extract_time(o.get("order_date") or "")
        key = (ch, sub, buyer, time_str)
        grouped.setdefault(key, []).append(o)
    return list(grouped.values())


def _build_header(slot_label: str, period_label: str, stats: dict[str, Any]) -> str:
    status_line = " / ".join(f"{k} {v}" for k, v in sorted(stats["by_status"].items()))

    # Cash note if different from amount
    cash_note = ""
    if stats["total_cash"] != stats["total_amount"]:
        cash_note = f"\n   (실 카드결제 합계: ₩{stats['total_cash']:,})"

    new_note = f" / 신규 {stats['new_buyer_count']}" if stats["new_buyer_count"] > 0 else ""

    # Build per-subchannel lines
    sub_lines = []
    by_sub = stats["by_subchannel"]
    if not by_sub:
        # Show empty default rows so user knows nothing came in
        sub_lines.append(f"   카페24       :   0건 / ₩0")
        sub_lines.append(f"   스마트스토어 :   0건 / ₩0")
    else:
        for (ch, sub), v in by_sub.items():
            label = _subchannel_label(ch, sub, full=True)
            # Pad label to ~14 chars
            sub_lines.append(f"   {label:<14}: {v['count']:>3}건 / ₩{v['amount']:,}")

    header = (
        f"📦 {slot_label} 일일 리포트\n"
        f"\n"
        f"▣ 기간: {period_label}\n"
        f"\n"
        f"▣ 채널별 (매출 기준)\n"
        + "\n".join(sub_lines) + "\n"
        f"   ─────────────────────\n"
        f"   합계          : {stats['total_count']:>3}건 / ₩{stats['total_amount']:,}{new_note}"
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

    # Group same-buyer/minute orders, then format
    groups = _group_orders(orders)
    order_lines: list[str] = []
    for g in groups:
        if len(g) == 1:
            order_lines.append("   " + _format_order_line(g[0]))
        else:
            order_lines.append("   " + _format_grouped_line(g))
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
