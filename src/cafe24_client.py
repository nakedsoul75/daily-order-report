"""Cafe24 Admin API client.

Spec source: https://developers.cafe24.com/docs/api/admin/
- OAuth 2.0 Authorization Code Grant + Refresh Token rotation
- Endpoint: https://{mall_id}.cafe24api.com/api/v2/admin/orders
- Required header: X-Cafe24-Api-Version
- Rate limit: 2/sec bucket (response header X-Cafe24-Call-Usage)
"""
from __future__ import annotations

import base64
import os
from datetime import datetime
from typing import Any

import requests

# Cafe24 API version (latest stable as of 2026)
API_VERSION = "2024-09-01"


class Cafe24Client:
    def __init__(
        self,
        mall_id: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> None:
        self.mall_id = mall_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.base_url = f"https://{mall_id}.cafe24api.com/api/v2"

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
        # refresh_token rotates on every refresh — keep latest
        self.refresh_token = body["refresh_token"]

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
    def normalize(order: dict[str, Any]) -> dict[str, Any]:
        """Convert Cafe24 order to common schema."""
        items = order.get("items", []) or []
        return {
            "channel": "cafe24",
            "order_id": order.get("order_id"),
            "order_date": order.get("order_date"),
            "buyer_name": order.get("buyer_name") or order.get("billing_name"),
            "amount": int(float(order.get("payment_amount") or 0)),
            "status": order.get("order_status_name") or order.get("order_status"),
            "items": [
                {
                    "name": it.get("product_name"),
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
