"""Naver Commerce API (SmartStore) client."""
from __future__ import annotations

import base64
import os
import time
from datetime import datetime
from typing import Any

import bcrypt
import requests


class SmartStoreClient:
    BASE_URL = "https://api.commerce.naver.com/external"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.token_expires_at: float = 0.0

    # --- Auth ---
    def _sign(self, timestamp: int) -> str:
        """네이버 커머스 API 서명: bcrypt(client_id_timestamp, client_secret) -> base64."""
        password = f"{self.client_id}_{timestamp}".encode()
        hashed = bcrypt.hashpw(password, self.client_secret.encode())
        return base64.standard_b64encode(hashed).decode()

    def _refresh_access_token(self) -> None:
        timestamp = int(time.time() * 1000)
        signature = self._sign(timestamp)
        resp = requests.post(
            f"{self.BASE_URL}/v1/oauth2/token",
            data={
                "client_id": self.client_id,
                "timestamp": timestamp,
                "client_secret_sign": signature,
                "grant_type": "client_credentials",
                "type": "SELF",
            },
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        self.access_token = body["access_token"]
        self.token_expires_at = time.time() + int(body.get("expires_in", 10800)) - 60

    def _ensure_token(self) -> None:
        if not self.access_token or time.time() >= self.token_expires_at:
            self._refresh_access_token()

    # --- Orders ---
    def fetch_orders(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch orders changed within [start_dt, end_dt].
        Naver uses 'lastChangedFrom/To' (ISO8601 with timezone).
        """
        self._ensure_token()
        all_orders: list[dict[str, Any]] = []

        params = {
            "lastChangedFrom": start_dt.isoformat(timespec="seconds"),
            "lastChangedTo": end_dt.isoformat(timespec="seconds"),
            "lastChangedType": "PAYED",  # 결제완료 기준
        }
        resp = requests.get(
            f"{self.BASE_URL}/v1/pay-order/seller/product-orders/last-changed-statuses",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
            timeout=30,
        )
        if resp.status_code == 401:
            self._refresh_access_token()
            return self.fetch_orders(start_dt, end_dt)
        resp.raise_for_status()
        change_data = resp.json().get("data", {})
        product_order_ids = [
            row["productOrderId"]
            for row in change_data.get("lastChangeStatuses", [])
        ]
        if not product_order_ids:
            return []

        # 상세 조회 (최대 300개씩)
        for chunk_start in range(0, len(product_order_ids), 300):
            chunk = product_order_ids[chunk_start : chunk_start + 300]
            detail_resp = requests.post(
                f"{self.BASE_URL}/v1/pay-order/seller/product-orders/query",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={"productOrderIds": chunk},
                timeout=30,
            )
            detail_resp.raise_for_status()
            all_orders.extend(detail_resp.json().get("data", []))
        return all_orders

    @staticmethod
    def normalize(order: dict[str, Any]) -> dict[str, Any]:
        """Convert Naver order to common schema."""
        product_order = order.get("productOrder", {}) or {}
        order_main = order.get("order", {}) or {}
        return {
            "channel": "smartstore",
            "order_id": product_order.get("productOrderId"),
            "order_date": order_main.get("orderDate"),
            "buyer_name": order_main.get("ordererName"),
            "amount": int(product_order.get("totalPaymentAmount") or 0),
            "status": product_order.get("productOrderStatus"),
            "items": [
                {
                    "name": product_order.get("productName"),
                    "qty": int(product_order.get("quantity") or 0),
                    "price": int(product_order.get("unitPrice") or 0),
                }
            ],
        }


def from_env() -> SmartStoreClient:
    return SmartStoreClient(
        client_id=os.environ["NAVER_COMMERCE_CLIENT_ID"],
        client_secret=os.environ["NAVER_COMMERCE_CLIENT_SECRET"],
    )
