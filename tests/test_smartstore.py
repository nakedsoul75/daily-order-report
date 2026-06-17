"""SmartStoreClient 유닛/통합 테스트 (paymentDate 기준 재구현).

requests 를 mock 해 실제 API 호출 없이 검증한다.
- normalize: content({order, productOrder}) → 공통 스키마
- fetch_orders: hasNext 페이지 순회, 24h 청크 분할, 429/401 재시도, rate-limit sleep

실행: python -m unittest tests.test_smartstore  (레포 루트에서)
"""
from __future__ import annotations

import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytz
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.smartstore_client import SmartStoreClient  # noqa: E402

KST = pytz.timezone("Asia/Seoul")


class FakeResp:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


def make_content(pid="PO1", status="PAYED", amount=10000,
                 payment_date="2026-06-16T21:38:36.809+09:00",
                 order_date="2026-06-16T21:38:31.015+09:00",
                 name="홍길동"):
    """조건형 상품주문 응답의 content 한 건을 합성 (개인정보는 합성값)."""
    return {
        "order": {
            "orderId": "O" + pid,
            "orderDate": order_date,
            "paymentDate": payment_date,
            "ordererName": name,
        },
        "productOrder": {
            "productOrderId": pid,
            "totalPaymentAmount": amount,
            "productOrderStatus": status,
            "quantity": 1,
            "unitPrice": amount,
            "productName": "테스트상품",
            "productOption": "색상: 블랙",
            "originalProductId": "OP1",
            "productId": "P1",
            "shippingAddress": {
                "name": name,
                "baseAddress": "서울시",
                "detailedAddress": "101호",
            },
        },
    }


def make_page(contents, has_next=False, page=1):
    return {
        "data": {
            "contents": [
                {"productOrderId": c["productOrder"]["productOrderId"], "content": c}
                for c in contents
            ],
            "pagination": {"page": page, "size": 100, "hasNext": has_next},
        }
    }


def make_client(rate=0.0):
    c = SmartStoreClient("id", "secret", shop_name="콤마캠핑", rate_limit_sleep=rate)
    c.access_token = "tok"
    c.token_expires_at = time.time() + 9999
    return c


class TestNormalize(unittest.TestCase):
    def setUp(self):
        self.c = make_client()

    def test_basic_fields(self):
        o = self.c.normalize(make_content())
        self.assertEqual(o["channel"], "smartstore")
        self.assertEqual(o["shop_name"], "콤마캠핑")
        self.assertEqual(o["order_id"], "PO1")
        self.assertEqual(o["amount"], 10000)
        self.assertEqual(o["cash_paid"], 10000)
        self.assertEqual(o["status"], "결제완료")
        self.assertEqual(o["buyer_name"], "홍길동")
        self.assertEqual(o["receiver_name"], "홍길동")
        self.assertEqual(o["receiver_address"], "서울시 101호")
        self.assertFalse(o["first_order"])
        self.assertEqual(len(o["items"]), 1)
        it = o["items"][0]
        self.assertEqual(it["name"], "테스트상품")
        self.assertEqual(it["option"], "색상: 블랙")
        self.assertEqual(it["sku_code"], "OP1")
        self.assertEqual(it["qty"], 1)
        self.assertEqual(it["price"], 10000)

    def test_order_date_prefers_payment_date(self):
        o = self.c.normalize(make_content())
        self.assertEqual(o["order_date"], "2026-06-16T21:38:36.809+09:00")

    def test_order_date_fallback_to_order_date(self):
        content = make_content()
        del content["order"]["paymentDate"]
        o = self.c.normalize(content)
        self.assertEqual(o["order_date"], "2026-06-16T21:38:31.015+09:00")

    def test_status_mapping(self):
        self.assertEqual(self.c.normalize(make_content(status="CANCELED"))["status"], "취소")
        self.assertEqual(self.c.normalize(make_content(status="PURCHASE_DECIDED"))["status"], "구매확정")
        self.assertEqual(self.c.normalize(make_content(status="PAYMENT_WAITING"))["status"], "결제대기")
        # 매핑에 없는 코드는 원문 유지
        self.assertEqual(self.c.normalize(make_content(status="WEIRD_CODE"))["status"], "WEIRD_CODE")

    def test_empty_content_no_crash(self):
        o = self.c.normalize({})
        self.assertEqual(o["amount"], 0)
        self.assertEqual(o["cash_paid"], 0)
        self.assertEqual(o["status"], "기타")
        self.assertIsNone(o["order_id"])
        self.assertEqual(o["items"][0]["qty"], 0)


class TestFetchOrders(unittest.TestCase):
    def _range(self, h0, h1, d1=16):
        start = KST.localize(datetime(2026, 6, 16, h0, 0, 0))
        end = KST.localize(datetime(2026, 6, d1, h1, 0, 0))
        return start, end

    def test_single_window_paginates_until_hasnext_false(self):
        c = make_client()
        start, end = self._range(0, 12)
        responses = [
            FakeResp(200, make_page([make_content("A"), make_content("B")], has_next=True, page=1)),
            FakeResp(200, make_page([make_content("C")], has_next=False, page=2)),
        ]
        with mock.patch("src.smartstore_client.requests.get", side_effect=responses) as mg:
            out = c.fetch_orders(start, end)
        self.assertEqual(len(out), 3)
        self.assertEqual(mg.call_count, 2)
        self.assertEqual(mg.call_args_list[0].kwargs["params"]["page"], 1)
        self.assertEqual(mg.call_args_list[1].kwargs["params"]["page"], 2)
        # 반환은 content dict (normalize 입력 형태)
        self.assertIn("productOrder", out[0])

    def test_multi_chunk_splits_24h(self):
        c = make_client()
        start, end = self._range(0, 1, d1=17)  # 25h → 2 chunks
        responses = [
            FakeResp(200, make_page([make_content("A")], has_next=False)),
            FakeResp(200, make_page([make_content("B")], has_next=False)),
        ]
        with mock.patch("src.smartstore_client.requests.get", side_effect=responses) as mg:
            out = c.fetch_orders(start, end)
        self.assertEqual(len(out), 2)
        self.assertEqual(mg.call_count, 2)
        p0 = mg.call_args_list[0].kwargs["params"]
        p1 = mg.call_args_list[1].kwargs["params"]
        self.assertEqual(p0["rangeType"], "PAYED_DATETIME")
        self.assertTrue(p0["from"].startswith("2026-06-16T00:00:00.000"))
        self.assertTrue(p0["to"].startswith("2026-06-16T23:59:59.000"))
        self.assertTrue(p1["from"].startswith("2026-06-17T00:00:00.000"))
        self.assertTrue(p1["to"].startswith("2026-06-17T01:00:00.000"))

    def test_429_then_success_retries(self):
        c = make_client()
        start, end = self._range(0, 6)
        responses = [
            FakeResp(429, {}, headers={"Retry-After": "0"}),
            FakeResp(200, make_page([make_content("A")], has_next=False)),
        ]
        with mock.patch("src.smartstore_client.requests.get", side_effect=responses) as mg, \
             mock.patch("src.smartstore_client.time.sleep"):
            out = c.fetch_orders(start, end)
        self.assertEqual(len(out), 1)
        self.assertEqual(mg.call_count, 2)

    def test_401_refreshes_token_and_retries(self):
        c = make_client()
        start, end = self._range(0, 6)
        responses = [
            FakeResp(401, {}),
            FakeResp(200, make_page([make_content("A")], has_next=False)),
        ]
        with mock.patch("src.smartstore_client.requests.get", side_effect=responses) as mg, \
             mock.patch.object(c, "_refresh_access_token") as mref:
            out = c.fetch_orders(start, end)
        self.assertEqual(len(out), 1)
        self.assertEqual(mg.call_count, 2)
        self.assertTrue(mref.called)

    def test_rate_limit_sleep_between_requests_only(self):
        c = make_client(rate=0.3)
        start, end = self._range(0, 1, d1=17)  # 2 chunks → 2 requests
        responses = [
            FakeResp(200, make_page([make_content("A")], has_next=False)),
            FakeResp(200, make_page([make_content("B")], has_next=False)),
        ]
        with mock.patch("src.smartstore_client.requests.get", side_effect=responses), \
             mock.patch("src.smartstore_client.time.sleep") as msleep:
            c.fetch_orders(start, end)
        # 첫 요청은 sleep 스킵, 두 번째 요청 전 1회만 sleep
        msleep.assert_called_once_with(0.3)

    def test_empty_result(self):
        c = make_client()
        start, end = self._range(0, 6)
        with mock.patch("src.smartstore_client.requests.get",
                        side_effect=[FakeResp(200, make_page([], has_next=False))]):
            out = c.fetch_orders(start, end)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
