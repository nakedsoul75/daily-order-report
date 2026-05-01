"""Naver Commerce API (SmartStore) client."""
from __future__ import annotations

import base64
import os
import time
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import requests

# Naver Commerce productOrderStatus → Korean label
STATUS_KR = {
    "PAYMENT_WAITING": "결제대기",
    "PAYED": "결제완료",
    "DELIVERING": "배송중",
    "DELIVERED": "배송완료",
    "PURCHASE_DECIDED": "구매확정",
    "EXCHANGED": "교환",
    "CANCELED": "취소",
    "RETURNED": "반품완료",
    "CANCELED_BY_NOPAYMENT": "미결제취소",
}


class SmartStoreClient:
    BASE_URL = "https://api.commerce.naver.com/external"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        shop_name: str = "",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.shop_name = shop_name
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
        Naver uses 'lastChangedFrom/To' (ISO8601 millisec with timezone).
        Time range is limited to 24h per call — auto-chunk if longer.
        """
        self._ensure_token()
        all_ids: list[str] = []

        # Chunk into 24h windows
        cur = start_dt
        while cur < end_dt:
            chunk_end = min(cur + timedelta(hours=24, seconds=-1), end_dt)
            params = {
                "lastChangedFrom": cur.isoformat(timespec="milliseconds"),
                "lastChangedTo": chunk_end.isoformat(timespec="milliseconds"),
                "lastChangedType": "PAYED",
            }
            resp = requests.get(
                f"{self.BASE_URL}/v1/pay-order/seller/product-orders/last-changed-statuses",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params,
                timeout=30,
            )
            if resp.status_code == 401:
                self._refresh_access_token()
                continue  # retry same window
            resp.raise_for_status()
            change_data = resp.json().get("data") or {}
            for row in change_data.get("lastChangeStatuses", []):
                pid = row.get("productOrderId")
                if pid:
                    all_ids.append(pid)
            cur = chunk_end + timedelta(seconds=1)

        if not all_ids:
            return []

        # Detail fetch (max 300 IDs per call)
        all_orders: list[dict[str, Any]] = []
        for chunk_start in range(0, len(all_ids), 300):
            chunk = all_ids[chunk_start : chunk_start + 300]
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

    def normalize(self, order: dict[str, Any]) -> dict[str, Any]:
        """Convert Naver order to common schema."""
        product_order = order.get("productOrder", {}) or {}
        order_main = order.get("order", {}) or {}
        amount = int(product_order.get("totalPaymentAmount") or 0)
        raw_status = product_order.get("productOrderStatus") or ""
        return {
            "channel": "smartstore",
            "shop_name": self.shop_name,
            "order_id": product_order.get("productOrderId"),
            "order_date": order_main.get("orderDate"),
            "buyer_name": order_main.get("ordererName"),
            "amount": amount,
            "cash_paid": amount,
            "first_order": False,  # SmartStore doesn't expose this in basic order data
            "status": STATUS_KR.get(raw_status, raw_status or "기타"),
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
        shop_name=os.getenv("NAVER_COMMERCE_STORE_NAME", ""),
    )
