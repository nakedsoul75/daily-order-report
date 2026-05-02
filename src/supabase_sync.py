"""Supabase sync for daily-report orders.

Adds normalized orders to Supabase 'orders' table with:
- Mapping lookup (sub_channel + sku_code + option_norm → ea_code)
- UNMAPPED handling (ea_code = NULL when not found)
- UPSERT to prevent duplicates (UNIQUE: channel, order_no, sku_code, qty)
"""
from __future__ import annotations

import os
import re
from typing import Any

# Lazy import — supabase optional (skip sync if not installed/configured)
_client = None
_disabled = False


def _get_client():
    global _client, _disabled
    if _disabled:
        return None
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[SUPABASE] not configured — skipping sync (set SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env to enable)")
        _disabled = True
        return None
    try:
        from supabase import create_client
        _client = create_client(url, key)
        return _client
    except ImportError:
        print("[SUPABASE] 'supabase' package not installed — run: pip install supabase")
        _disabled = True
        return None
    except Exception as e:
        print(f"[SUPABASE] init failed: {e}")
        _disabled = True
        return None


def _normalize_option(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[\s\-/()\[\]:=,'\"`+_]+", "", str(s).lower())


def _normalize_name(s: str | None) -> str:
    """상품명 정규화 — 매칭 안정화."""
    if not s:
        return ""
    return re.sub(r"[\s\-/()\[\]★,.'\"`+_!?]+", "", str(s).lower())


def _short_subchannel(channel: str, shop_name: str | None) -> str:
    """daily-report channel → Supabase sub_channel (matches sku_mapping)."""
    if channel == "cafe24":
        if shop_name == "한국어몰":
            return "자사몰"
        if shop_name == "사업자몰":
            return "사업자몰"
        return shop_name or "자사몰"
    # smartstore
    return shop_name or "콤마캠핑"


def lookup_ea_code(
    sub_channel: str,
    sku_code: str | None,
    option: str | None,
    product_name: str | None = None,
) -> str | None:
    """Search sku_mapping table.

    Tries 4 strategies in order:
      1. (sub_channel, sku_code, option_norm)
      2. (sub_channel, sku_code, "")
      3. (sub_channel, name_norm, option_norm)  ← uses sku_code field for name
      4. (sub_channel, name_norm, "")
    """
    client = _get_client()
    if client is None:
        return None
    try:
        opt_n = _normalize_option(option)
        name_n = _normalize_name(product_name) if product_name else ""

        # Strategy 1+2: by sku_code
        if sku_code:
            sku = str(sku_code).strip()
            for opt_try in [opt_n, ""]:
                res = (
                    client.table("sku_mapping")
                    .select("ea_code")
                    .eq("sub_channel", sub_channel)
                    .eq("sku_code", sku)
                    .eq("option_norm", opt_try)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    return res.data[0]["ea_code"]

        # Strategy 3+4: by name (sku_code field stores name when learned from product_name)
        if name_n:
            for opt_try in [opt_n, ""]:
                res = (
                    client.table("sku_mapping")
                    .select("ea_code")
                    .eq("sub_channel", sub_channel)
                    .eq("sku_code", "name:" + name_n)
                    .eq("option_norm", opt_try)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    return res.data[0]["ea_code"]
    except Exception as e:
        print(f"[SUPABASE] lookup err: {e}")
    return None


def _build_order_row(o: dict[str, Any]) -> dict[str, Any]:
    """Convert normalized daily-report order → Supabase orders row."""
    channel = o.get("channel")
    sub_channel = _short_subchannel(channel, o.get("shop_name"))
    items = o.get("items", []) or []

    # daily-report 한 주문 = 한 채널/주문번호 — 여러 items 가능
    # Supabase orders 테이블은 line item 단위 (channel, order_no, sku_code, qty UNIQUE)
    # → 각 item을 별도 row로 분리
    rows = []
    base_amount = int(o.get("amount") or 0)
    base_cash = int(o.get("cash_paid") or 0)

    # Per-item amount split (proportional to qty * price if available)
    for it in items:
        qty = int(it.get("qty") or 1)
        sku_code = it.get("sku_code") or it.get("product_code") or ""
        option = it.get("option") or ""
        prod_name = it.get("name") or ""

        # Mapping lookup (4 strategies: sku→name, with/without option)
        ea_code = lookup_ea_code(sub_channel, sku_code, option, prod_name)

        rows.append({
            "channel": channel,
            "sub_channel": sub_channel,
            "order_no": str(o.get("order_id") or ""),
            "ea_code": ea_code,
            "product_name": it.get("name"),
            "option_name": option or None,
            "sku_code": str(sku_code).strip() if sku_code else None,
            "qty": qty,
            "amount": int(float(it.get("price") or 0)) * qty if it.get("price") else None,
            "cash_paid": None,  # cash split between items isn't accurate; keep order-level total separate
            "buyer_name": o.get("buyer_name"),
            "order_date": o.get("order_date"),
            "is_first_order": bool(o.get("first_order")),
            "status": o.get("status") or "NEW",
        })

    # Override per-item amount: only first row gets full order amount + cash
    # (avoid double-counting when summing). For accurate revenue: use first row.
    if rows:
        rows[0]["amount"] = base_amount
        rows[0]["cash_paid"] = base_cash
        for r in rows[1:]:
            r["amount"] = 0
            r["cash_paid"] = 0

    return rows


def sync_orders(orders: list[dict[str, Any]]) -> dict[str, int]:
    """Upsert normalized orders to Supabase. Returns {inserted, mapped, unmapped}."""
    client = _get_client()
    if client is None:
        return {"inserted": 0, "mapped": 0, "unmapped": 0, "skipped": True}

    all_rows = []
    for o in orders:
        all_rows.extend(_build_order_row(o))

    if not all_rows:
        return {"inserted": 0, "mapped": 0, "unmapped": 0}

    mapped = sum(1 for r in all_rows if r["ea_code"])
    unmapped = sum(1 for r in all_rows if not r["ea_code"])

    # Deduplicate within batch (same UNIQUE key = keep first)
    seen_keys = set()
    deduped = []
    for r in all_rows:
        key = (r["channel"], r["order_no"], r.get("sku_code") or "", r["qty"])
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(r)
    if len(deduped) < len(all_rows):
        print(f"[SUPABASE] dedup: {len(all_rows)} → {len(deduped)} (same UNIQUE key removed)")

    inserted = 0
    BATCH = 200
    for i in range(0, len(deduped), BATCH):
        chunk = deduped[i:i + BATCH]
        try:
            res = client.table("orders").upsert(
                chunk, on_conflict="channel,order_no,sku_code,qty"
            ).execute()
            inserted += len(res.data) if res.data else 0
        except Exception as e:
            print(f"[SUPABASE] orders upsert batch err: {str(e)[:200]}")

    return {"inserted": inserted, "mapped": mapped, "unmapped": unmapped, "total": len(deduped)}
