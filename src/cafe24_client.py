"""Cafe24 Admin API client.

Spec source: https://developers.cafe24.com/docs/api/admin/
- OAuth 2.0 Authorization Code Grant + Refresh Token rotation
- Endpoint: https://{mall_id}.cafe24api.com/api/v2/admin/orders
- Required header: X-Cafe24-Api-Version
- Rate limit: 2/sec bucket (response header X-Cafe24-Call-Usage)

CRITICAL: Cafe24 rotates refresh_token on every refresh.
The new token MUST be persisted back to .env (or external secret store)
or the next run will fail with invalid_grant.
"""
from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

API_VERSION = "2026-03-01"


def _default_persist(new_token: str) -> None:
    """Update .env file's CAFE24_REFRESH_TOKEN line in-place."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("CAFE24_REFRESH_TOKEN="):
            lines[i] = f"CAFE24_REFRESH_TOKEN={new_token}"
            updated = True
            break
    if not updated:
        lines.append(f"CAFE24_REFRESH_TOKEN={new_token}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Cafe24Client:
    def __init__(
        self,
        mall_id: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        persist_refresh: Callable[[str], None] | None = None,
    ) -> None:
        self.mall_id = mall_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.base_url = f"https://{mall_id}.cafe24api.com/api/v2"
        self.persist_refresh = persist_refresh or _default_persist

    def _refresh_access_token(self) -> None:
        url = f"{self.base_url}/oauth/token"
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        self.access_token = body["access_token"]
        new_rtok = body["refresh_token"]
        if new_rtok != self.refresh_token:
            self.refresh_token = new_rtok
            try:
                self.persist_refresh(new_rtok)
            except Exception as e:
                print(f"[WARN] failed to persist new refresh_token: {e}")

    def fetch_orders(
        self,
        start_dt: datetime,
        end_dt: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch orders between start_dt and end_dt (KST datetimes)."""
        if not self.access_token:
            self._refresh_access_token()

        all_orders: list[dict[str, Any]] = []
        offset = 0
        while True:
            params = {
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "date_type": "order_date",
                "limit": limit,
                "offset": offset,
                "embed": "items,buyer,receivers",
            }
            resp = requests.get(
                f"{self.base_url}/admin/orders",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "X-Cafe24-Api-Version": API_VERSION,
                    "Content-Type": "application/json",
                },
                params=params,
                timeout=30,
            )
            if resp.status_code == 401:
                self._refresh_access_token()
                continue
            resp.raise_for_status()
            batch = resp.json().get("orders", [])
            all_orders.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        return all_orders

    @staticmethod
    def _derive_status(order: dict[str, Any]) -> str:
        """Derive Korean status label from Cafe24 v2026-03-01 fields."""
        if order.get("canceled") == "T" or order.get("cancel_date"):
            return "취소"
        if order.get("return_confirmed_date"):
            return "반품완료"
        if order.get("paid") != "T":
            return "결제대기"
        # paid == T → check shipping_status: F/A/B/C/D
        ship = (order.get("shipping_status") or "F").upper()
        return {
            "F": "결제완료",
            "A": "배송준비",
            "B": "배송중",
            "C": "배송완료",
            "D": "배송지연",
            "M": "배송보류",
            "T": "반품접수",
        }.get(ship, f"상태({ship})")

    @classmethod
    def normalize(cls, order: dict[str, Any]) -> dict[str, Any]:
        """Convert Cafe24 v2026-03-01 order to common schema.

        Amount = order_price_amount (실 매출, 적립금/할인 차감 전)
        Cash = payment_amount (실 카드 결제, 적립금 차감 후)
        """
        items = order.get("items", []) or []
        actual = order.get("actual_order_amount") or {}
        order_value = actual.get("order_price_amount") or order.get("payment_amount") or 0
        cash_paid = order.get("payment_amount") or 0

        return {
            "channel": "cafe24",
            "order_id": order.get("order_id"),
            "order_date": order.get("order_date"),
            "buyer_name": order.get("billing_name"),
            "amount": int(float(order_value)),
            "cash_paid": int(float(cash_paid)),
            "first_order": order.get("first_order") == "T",
            "status": cls._derive_status(order),
            "items": [
                {
                    "name": it.get("product_name") or it.get("product_name_default"),
                    "qty": int(it.get("quantity") or 0),
                    "price": int(float(it.get("product_price") or 0)),
                }
                for it in items
            ],
        }


def from_env() -> Cafe24Client:
    return Cafe24Client(
        mall_id=os.environ["CAFE24_MALL_ID"],
        client_id=os.environ["CAFE24_CLIENT_ID"],
        client_secret=os.environ["CAFE24_CLIENT_SECRET"],
        refresh_token=os.environ["CAFE24_REFRESH_TOKEN"],
    )
