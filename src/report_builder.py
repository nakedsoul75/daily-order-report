"""Aggregate normalized orders and format report text into one or more Kakao messages.

Three output formats:
- format_report(): list[str] for Kakao text messages (split if > 3800 chars)
- format_short_kakao(): single short summary with URL (for HTML-link mode)
- format_html_report(): standalone HTML document for browser viewing
"""
from __future__ import annotations

import html as _html
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
    """Business-friendly display labels.

    User's preferred labels:
      cafe24 / 한국어몰 → 자사몰
      cafe24 / 사업자몰 → 제휴사
      smartstore / *   → 스토어
    Other shops fall back to the underlying name.
    """
    if ch == "cafe24":
        if sub == "한국어몰":
            return "자사몰"
        if sub == "사업자몰":
            return "제휴사"
        # Fallback for other cafe24 shops
        if full:
            return f"카페24 ({sub})" if sub else "카페24"
        return f"C24/{sub[:3]}" if sub else "C24"
    # smartstore
    return "스토어"


def _product_key(item: dict[str, Any]) -> str:
    """Build product key including option (so 색상별로 카운트). e.g. '바이런 쉘프 (색상=스텐)'."""
    name = (item.get("name") or "").strip()
    opt = (item.get("option") or "").strip()
    if opt:
        return f"{name} ({opt})"
    return name


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
            key = _product_key(it)
            if key:
                product_qty[key] += int(it.get("qty") or 0)

    sorted_orders = sorted(orders, key=lambda o: o.get("order_date") or "", reverse=True)

    return {
        "by_subchannel": by_subchannel,
        "by_status": dict(by_status),
        "top_products": product_qty.most_common(5),
        "all_products": product_qty.most_common(),  # full list for HTML report
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


def format_short_kakao(
    slot_label: str,
    period_label: str,
    stats: dict[str, Any],
    report_url: str,
) -> str:
    """Compact Kakao message: summary + URL to full HTML report."""
    sub_lines = []
    for (ch, sub), v in stats["by_subchannel"].items():
        if v["count"] == 0:
            continue
        label = _subchannel_label(ch, sub, full=True)
        sub_lines.append(f"  • {label} {v['count']}건 / ₩{v['amount']:,}")
    if not sub_lines:
        sub_lines = ["  • (주문 없음)"]

    new_note = f" / 신규 {stats['new_buyer_count']}명" if stats["new_buyer_count"] > 0 else ""
    cash_note = ""
    if stats["total_cash"] != stats["total_amount"]:
        cash_note = f"\n  (실 카드결제: ₩{stats['total_cash']:,})"

    return (
        f"📦 {slot_label} 일일 리포트\n"
        f"\n"
        f"⏱ {period_label}\n"
        f"\n"
        f"💰 총 {stats['total_count']}건 / ₩{stats['total_amount']:,}{new_note}"
        f"{cash_note}\n"
        + "\n".join(sub_lines) + "\n"
        f"\n"
        f"📄 상세 리포트:\n"
        f"{report_url}"
    )


# ---- HTML report ----

_HTML_CSS = """
:root {
  --primary: #ea580c;
  --primary-light: #fed7aa;
  --bg: #fafaf9;
  --card: #ffffff;
  --border: #e7e5e4;
  --text: #1c1917;
  --text-muted: #78716c;
  --green: #16a34a;
  --blue: #2563eb;
  --red: #dc2626;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", "Malgun Gothic", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  padding: 16px;
}
.container { max-width: 900px; margin: 0 auto; }
header {
  background: linear-gradient(135deg, var(--primary), #f97316);
  color: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 16px;
}
header h1 { font-size: 22px; margin-bottom: 4px; }
header .meta { font-size: 13px; opacity: 0.9; }
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
.kpi {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  text-align: center;
}
.kpi .label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.kpi .value { font-size: 28px; font-weight: 700; color: var(--primary); }
.kpi .sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 16px;
}
.card h2 { font-size: 14px; color: var(--text-muted); margin-bottom: 12px; font-weight: 600; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; }
.bar-label { width: 140px; flex-shrink: 0; color: var(--text-muted); }
.bar-bg { flex: 1; height: 22px; background: #f5f5f4; border-radius: 4px; position: relative; overflow: hidden; }
.bar-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.3s; }
.bar-fill.alt { background: var(--blue); }
.bar-value { width: 110px; flex-shrink: 0; text-align: right; font-size: 12px; font-weight: 500; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 8px 6px; text-align: left; border-bottom: 1px solid var(--border); }
th { font-weight: 600; color: var(--text-muted); font-size: 11px; text-transform: uppercase; background: #fafaf9; position: sticky; top: 0; }
tr.new { background: linear-gradient(90deg, #fef3c7 0%, transparent 30%); }
tr:hover { background: #fafaf9; }
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}
.tag.c24 { background: #dbeafe; color: #1e40af; }
.tag.ss { background: #dcfce7; color: #166534; }
.tag.new { background: #fde68a; color: #92400e; margin-left: 4px; }
.amount { text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }
.cash { color: var(--text-muted); font-size: 11px; }
.items-cell { color: var(--text-muted); font-size: 12px; max-width: 320px; }
.items-cell .opt { color: var(--blue); font-size: 11px; }
.product-table { width: 100%; }
.product-table td { padding: 8px 4px; border-bottom: 1px dashed var(--border); }
.product-table tr:last-child td { border-bottom: none; }
.product-table .pname { font-weight: 500; line-height: 1.5; }
.product-table .pname .opt-tag {
  display: inline-block;
  background: #dbeafe;
  color: #1e40af;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  margin-left: 4px;
  font-weight: 400;
}
.product-table .pqty { text-align: right; font-variant-numeric: tabular-nums; color: var(--primary); font-weight: 700; width: 70px; font-size: 15px; }
.highlight-products {
  background: linear-gradient(135deg, #fff7ed, #fef3c7);
  border: 2px solid var(--primary-light);
}
footer {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 24px 0 16px;
}
@media (max-width: 600px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .bar-label { width: 90px; font-size: 11px; }
  .bar-value { width: 80px; font-size: 11px; }
  .items-cell { max-width: 160px; font-size: 11px; }
  th, td { padding: 6px 4px; font-size: 11px; }
  th:nth-child(7), td:nth-child(7) { display: none; }
}
"""


def _esc(s: Any) -> str:
    return _html.escape(str(s) if s is not None else "")


def format_html_report(
    slot_label: str,
    period_label: str,
    stats: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> str:
    """Generate standalone HTML report (no external dependencies)."""
    if generated_at is None:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Channel breakdown bars
    max_amount = max((v["amount"] for v in stats["by_subchannel"].values()), default=1)
    channel_bars = []
    for (ch, sub), v in stats["by_subchannel"].items():
        label = _subchannel_label(ch, sub, full=True)
        pct = (v["amount"] / max_amount * 100) if max_amount > 0 else 0
        channel_bars.append(
            f'<div class="bar-row">'
            f'  <div class="bar-label">{_esc(label)}</div>'
            f'  <div class="bar-bg"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>'
            f'  <div class="bar-value">{v["count"]}건 / ₩{v["amount"]:,}</div>'
            f'</div>'
        )

    # Status breakdown
    status_chips = " ".join(
        f'<span class="tag c24">{_esc(k)} {v}</span>'
        for k, v in sorted(stats["by_status"].items())
    ) or '<span class="tag c24">(없음)</span>'

    # All products (for production prep) — sorted by quantity desc
    # Product key includes option, so split for visual highlighting
    all_products = stats.get("all_products", []) or stats.get("top_products", [])
    total_qty = sum(q for _, q in all_products)
    product_rows = []
    for i, (full_key, qty) in enumerate(all_products, 1):
        # Parse "상품명 (옵션값)" pattern
        if " (" in full_key and full_key.endswith(")"):
            name_part, opt_part = full_key.rsplit(" (", 1)
            opt_part = opt_part.rstrip(")")
            name_html = f'{_esc(name_part)} <span class="opt-tag">{_esc(opt_part)}</span>'
        else:
            name_html = _esc(full_key)
        product_rows.append(
            f'<tr><td style="width:30px;color:var(--text-muted);text-align:right">{i}</td>'
            f'<td class="pname">{name_html}</td>'
            f'<td class="pqty">{qty}개</td></tr>'
        )
    if not product_rows:
        product_rows = ['<tr><td colspan="3" style="text-align:center;color:var(--text-muted)">(판매 상품 없음)</td></tr>']

    # Order rows (full list, no truncation here)
    order_rows = []
    groups = _group_orders(stats["orders_sorted"])
    for g in groups:
        is_grouped = len(g) > 1
        first = g[0]
        ch, sub = _subchannel_key(first)
        ch_label = _subchannel_label(ch, sub, full=False)
        ch_class = "c24" if ch == "cafe24" else "ss"
        time_str = _extract_time(first.get("order_date") or "")
        buyer = _mask_name(first.get("buyer_name") or "")
        status = first.get("status") or "?"
        is_new = any(o.get("first_order") for o in g)
        new_chip = '<span class="tag new">⭐신규</span>' if is_new else ''
        row_class = ' class="new"' if is_new else ''

        if is_grouped:
            total_amount = sum(int(o.get("amount") or 0) for o in g)
            total_cash = sum(int(o.get("cash_paid") or 0) for o in g)
            oid = f"{len(g)}건묶음"
            all_items_data: list[tuple[str, str, int]] = []
            for o in g:
                for it in o.get("items", []):
                    nm = (it.get("name") or "").strip()
                    opt = (it.get("option") or "").strip()
                    qty = int(it.get("qty") or 0)
                    if nm:
                        all_items_data.append((nm, opt, qty))
        else:
            o = first
            total_amount = int(o.get("amount") or 0)
            total_cash = int(o.get("cash_paid") or 0)
            oid = "#" + _short_order_id(o.get("order_id") or "")
            all_items_data = [
                ((it.get("name") or "").strip(), (it.get("option") or "").strip(), int(it.get("qty") or 0))
                for it in o.get("items", []) if (it.get("name") or "").strip()
            ]

        # Single-line comma-separated items, with option in blue parentheses
        item_parts = []
        for nm, opt, qty in all_items_data:
            opt_html = f' <span class="opt">({_esc(opt)})</span>' if opt else ""
            item_parts.append(f"{_esc(nm)}{opt_html}×{qty}")
        items_html = ", ".join(item_parts) or '<span style="color:var(--text-muted)">(상품 정보 없음)</span>'

        cash_note = ""
        if total_cash > 0 and total_cash != total_amount:
            cash_note = f'<div class="cash">실결제 ₩{total_cash:,}</div>'

        order_rows.append(
            f'<tr{row_class}>'
            f'<td>{_esc(time_str)}</td>'
            f'<td><span class="tag {ch_class}">{_esc(ch_label)}</span></td>'
            f'<td>{_esc(oid)}</td>'
            f'<td>{_esc(buyer)}{new_chip}</td>'
            f'<td>{_esc(status)}</td>'
            f'<td class="amount">₩{total_amount:,}{cash_note}</td>'
            f'<td class="items-cell">{items_html}</td>'
            f'</tr>'
        )
    if not order_rows:
        order_rows = ['<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:24px">주문이 없습니다.</td></tr>']

    title = f"{slot_label} 일일 리포트"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>{_esc(title)}</title>
<style>{_HTML_CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>📦 {_esc(title)}</h1>
    <div class="meta">📅 {_esc(period_label)}</div>
  </header>

  <div class="kpi-grid">
    <div class="kpi">
      <div class="label">총 매출</div>
      <div class="value">₩{stats['total_amount']:,}</div>
      <div class="sub">{'실 카드결제 ₩' + format(stats['total_cash'], ',') if stats['total_cash'] != stats['total_amount'] else ''}</div>
    </div>
    <div class="kpi">
      <div class="label">총 주문</div>
      <div class="value">{stats['total_count']}건</div>
      <div class="sub">{'신규 ' + str(stats['new_buyer_count']) + '명' if stats['new_buyer_count'] > 0 else ''}</div>
    </div>
  </div>

  <div class="card">
    <h2>📊 채널별 매출</h2>
    {''.join(channel_bars)}
  </div>

  <div class="card">
    <h2>📌 상태 / CS</h2>
    <div>{status_chips}</div>
    <div style="margin-top:12px;font-size:13px;color:var(--text-muted)">
      취소·환불·반품: <strong>{stats['cs_count']}건</strong>
    </div>
  </div>

  <div class="card highlight-products">
    <h2>📦 판매 상품 전체 ({len(all_products)}종 / 총 {total_qty}개) — 제품 준비용</h2>
    <table class="product-table">{''.join(product_rows)}</table>
  </div>

  <div class="card">
    <h2>📋 전체 주문 ({stats['total_count']}건)</h2>
    <div style="overflow-x:auto">
    <table>
      <thead><tr>
        <th>시간</th><th>채널</th><th>주문</th><th>고객</th><th>상태</th><th>매출</th><th>상품</th>
      </tr></thead>
      <tbody>{''.join(order_rows)}</tbody>
    </table>
    </div>
  </div>

  <footer>
    Generated at {_esc(generated_at)} · <a href="../">전체 리포트 목록</a>
  </footer>
</div>
</body>
</html>"""


def format_index_html(reports: list[tuple[str, str, str]]) -> str:
    """reports = [(date, slot, filename), ...] sorted newest first."""
    rows = []
    for date, slot, fn in reports:
        slot_kr = {"morning": "08:30", "midday": "12:30", "evening": "18:00", "test": "TEST"}.get(slot, slot)
        rows.append(f'<li><a href="{_esc(fn)}">{_esc(date)} · {_esc(slot_kr)}</a></li>')

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>일일 주문 리포트</title>
<style>{_HTML_CSS}
ul {{ list-style: none; padding: 0; }}
li {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; }}
li a {{ display: block; padding: 14px 18px; color: var(--text); text-decoration: none; font-weight: 500; }}
li a:hover {{ background: var(--primary-light); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>📚 일일 주문 리포트</h1>
    <div class="meta">최신순 · 총 {len(reports)}건</div>
  </header>
  <ul>{''.join(rows) if rows else '<li style="padding:24px;text-align:center;color:var(--text-muted)">아직 리포트가 없습니다.</li>'}</ul>
  <footer>Daily Order Report · COMMANINE</footer>
</div>
</body>
</html>"""
