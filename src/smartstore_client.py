"""Naver Commerce API (SmartStore) client.

주문 조회는 '조건형 상품주문 상세조회'(GET /v1/pay-order/seller/product-orders)를
rangeType=PAYED_DATETIME(결제일시 기준)으로 호출한다.

이전 구현은 last-changed-statuses(lastChangedType=PAYED)를 사용했으나, 이는
"기간 내 결제완료로 *변경*된" 주문만 잡아 매출 집계 시 대량 누락이 발생했다
(예: 지난주 7일 86건 중 3건만 조회 — 96.5% 누락). 결제일시 범위 조회로
교체해 누락을 해소하고, 청크/페이지 사이 sleep + 429 백오프로 rate limit을 방지한다.
"""
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

# 페이지/청크 사이 최소 간격(초). 429 Too Many Requests 방지.
DEFAULT_RATE_LIMIT_SLEEP = 0.3
# from~to 최대 폭(네이버 제약: 24h). 23:59:59까지 안전하게 잡는다.
_CHUNK = timedelta(hours=24, seconds=-1)
# 페이지 순회 무한루프 방지 상한 (24h 윈도우당).
_MAX_PAGES = 1000


class SmartStoreClient:
    BASE_URL = "https://api.commerce.naver.com/external"
    PRODUCT_ORDERS_PATH = "/v1/pay-order/seller/product-orders"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        shop_name: str = "",
        rate_limit_sleep: float = DEFAULT_RATE_LIMIT_SLEEP,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.shop_name = shop_name
        self.rate_limit_sleep = rate_limit_sleep
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

    def _get(self, path: str, params: dict[str, Any], max_retries: int = 5) -> requests.Response:
        """GET with token refresh (401) and exponential backoff on 429 (rate limit)."""
        url = f"{self.BASE_URL}{path}"
        backoff = 1.0
        last_resp: requests.Response | None = None
        for _ in range(max_retries):
            self._ensure_token()
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params,
                timeout=30,
            )
            last_resp = resp
            if resp.status_code == 401:
                self._refresh_access_token()
                continue
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else backoff
                time.sleep(min(wait, 10.0))
                backoff = min(backoff * 2, 10.0)
                continue
            resp.raise_for_status()
            return resp
        # retries exhausted — surface the last error
        assert last_resp is not None
        last_resp.raise_for_status()
        return last_resp

    # --- Orders ---
    def fetch_orders(self, start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
        """결제일시(PAYED_DATETIME) 기준 [start_dt, end_dt] 결제 상품주문을 조회.

        - from~to 최대 24h 제약 → 24h 단위 chunk 로 분할 호출
        - pagination.hasNext 로 페이지 순회 (pageSize=100)
        - 첫 요청을 제외한 모든 요청 전 rate_limit_sleep 으로 429 방지
        반환: content dict 리스트 (각 {"order": {...}, "productOrder": {...}})
        """
        contents: list[dict[str, Any]] = []
        cur = start_dt
        is_first_request = True
        while cur < end_dt:
            chunk_end = min(cur + _CHUNK, end_dt)
            page = 1
            while page <= _MAX_PAGES:
                if not is_first_request and self.rate_limit_sleep:
                    time.sleep(self.rate_limit_sleep)
                is_first_request = False
                params = {
                    "rangeType": "PAYED_DATETIME",
                    "from": cur.isoformat(timespec="milliseconds"),
                    "to": chunk_end.isoformat(timespec="milliseconds"),
                    "pageSize": 100,
                    "page": page,
                }
                resp = self._get(self.PRODUCT_ORDERS_PATH, params)
                data = resp.json().get("data") or {}
                for row in data.get("contents") or []:
                    inner = row.get("content")
                    if inner:
                        contents.append(inner)
                pagination = data.get("pagination") or {}
                if not pagination.get("hasNext"):
                    break
                page += 1
            cur = chunk_end + timedelta(seconds=1)
        return contents

    def normalize(self, content: dict[str, Any]) -> dict[str, Any]:
        """조건형 상품주문 content({order, productOrder}) → 공통 스키마."""
        product_order = content.get("productOrder", {}) or {}
        order_main = content.get("order", {}) or {}
        shipping = (
            product_order.get("shippingAddress", {})
            or content.get("shippingAddress", {})
            or {}
        )
        amount = int(product_order.get("totalPaymentAmount") or 0)
        raw_status = product_order.get("productOrderStatus") or ""

        receiver_name = (shipping.get("name") or "").strip()
        addr_parts = [shipping.get("baseAddress") or "", shipping.get("detailedAddress") or ""]
        receiver_address = " ".join(p for p in addr_parts if p).strip()
        return {
            "channel": "smartstore",
            "shop_name": self.shop_name,
            "order_id": product_order.get("productOrderId"),
            # 결제일시 우선(조회 기준과 일치), 없으면 주문일시로 폴백
            "order_date": order_main.get("paymentDate") or order_main.get("orderDate"),
            "buyer_name": order_main.get("ordererName"),
            "receiver_name": receiver_name,
            "receiver_address": receiver_address,
            "amount": amount,
            "cash_paid": amount,
            "first_order": False,  # SmartStore doesn't expose this in basic order data
            "status": STATUS_KR.get(raw_status, raw_status or "기타"),
            "items": [
                {
                    "name": product_order.get("productName"),
                    "option": (product_order.get("productOption") or "").strip(),
                    "sku_code": str(
                        product_order.get("originalProductId")
                        or product_order.get("productId")
                        or ""
                    ),
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
