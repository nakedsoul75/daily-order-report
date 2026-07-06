"""build_daily_sales 매핑 테스트 — aggregate 결과가 bks-os daily_sales payload 로
정확히 변환되는지(총계·채널라벨·구매자 마스킹·상품TOP·주문내역) 검증.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import report_builder  # noqa: E402


def _order(channel, shop, amount, buyer, status="결제완료", first=False, items=None, oid="1", date="2026-07-05T13:32:06+09:00"):
    return {
        "channel": channel,
        "shop_name": shop,
        "amount": amount,
        "cash_paid": amount,
        "status": status,
        "first_order": first,
        "buyer_name": buyer,
        "order_id": oid,
        "order_date": date,
        "items": items or [{"name": "IGT 테이블", "option": "", "qty": 1}],
    }


class BuildDailySalesTest(unittest.TestCase):
    def setUp(self):
        self.orders = [
            _order("cafe24", "한국어몰", 210000, "김철수", first=True, oid="20260705-0001"),
            _order("cafe24", "사업자몰", 553500, "이수민", oid="20260705-0002",
                   items=[{"name": "원액션 체어", "option": "블랙", "qty": 2}]),
            _order("smartstore", "콤마캠핑", 25000, "박영", oid="2026070500001"),
        ]
        expected = [("cafe24", "한국어몰"), ("cafe24", "사업자몰"), ("smartstore", "콤마캠핑")]
        self.stats = report_builder.aggregate(self.orders, expected_subchannels=expected)
        self.p = report_builder.build_daily_sales("2026-07-05", self.stats, "2026-07-05 전일")

    def test_totals(self):
        self.assertEqual(self.p["sale_date"], "2026-07-05")
        self.assertEqual(self.p["total_count"], 3)
        self.assertEqual(self.p["total_amount"], 210000 + 553500 + 25000)
        self.assertEqual(self.p["new_buyer_count"], 1)

    def test_channel_labels(self):
        labels = {c["sub_channel"]: c for c in self.p["by_channel"]}
        self.assertIn("자사몰", labels)      # cafe24/한국어몰
        self.assertIn("제휴사", labels)      # cafe24/사업자몰
        self.assertIn("스토어", labels)      # smartstore
        self.assertEqual(labels["제휴사"]["amount"], 553500)

    def test_buyer_masked(self):
        buyers = {o["buyer"] for o in self.p["orders"]}
        self.assertIn("김**", buyers)       # 3자 → 김**
        self.assertIn("박*", buyers)        # 2자 → 박*
        # 원본 실명은 절대 노출되지 않음
        self.assertNotIn("김철수", buyers)
        self.assertNotIn("이수민", buyers)

    def test_orders_shape(self):
        o = next(o for o in self.p["orders"] if o["order_no"] == "20260705-0002")
        self.assertEqual(o["channel"], "제휴사")
        self.assertEqual(o["qty"], 2)
        self.assertEqual(o["amount"], 553500)
        self.assertNotIn("phone", o)        # 연락처 미포함(PII)

    def test_top_products_pairs(self):
        # [[name, qty], ...] 형태(bks-os 기대 shape)
        self.assertTrue(all(isinstance(p, list) and len(p) == 2 for p in self.p["top_products"]))
        names = {p[0] for p in self.p["top_products"]}
        self.assertTrue(any("원액션" in n for n in names))


if __name__ == "__main__":
    unittest.main()
