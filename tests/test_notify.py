"""FallbackNotifier 폴백 동작 테스트.

카카오(1차) 성공 시 폴백 미호출, 실패(예외) 시 dispatch(2차)로 폴백되어
메시지가 유실되지 않는지 검증한다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.notify import FallbackNotifier  # noqa: E402


class FakePrimary:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls: list[str] = []

    def send_text(self, text, link_url=""):
        self.calls.append(text)
        if self.fail:
            raise RuntimeError("kakao token expired")
        return {"result_code": 0}


class FakeFallback:
    def __init__(self):
        self.calls: list[str] = []

    def send_text(self, text, link_url=""):
        self.calls.append(text)
        return {"dispatched": True}


class TestFallbackNotifier(unittest.TestCase):
    def test_primary_success_no_fallback(self):
        p, f = FakePrimary(fail=False), FakeFallback()
        result = FallbackNotifier(p, f).send_text("hello", "http://x")
        self.assertEqual(result["result_code"], 0)
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(len(f.calls), 0)  # 폴백 호출 안 됨
        self.assertNotIn("fallback", result)

    def test_primary_failure_falls_back(self):
        p, f = FakePrimary(fail=True), FakeFallback()
        result = FallbackNotifier(p, f).send_text("hello", "http://x")
        self.assertTrue(result.get("fallback"))
        self.assertIn("primary_error", result)
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(len(f.calls), 1)  # 폴백으로 전송됨
        self.assertIn("hello", f.calls[0])  # 원문 보존
        self.assertIn("실패", f.calls[0])   # 실패 사실 표시


if __name__ == "__main__":
    unittest.main(verbosity=2)
