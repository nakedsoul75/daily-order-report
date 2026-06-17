"""KakaoClient 토큰 회전·영속화 + client_secret 포함 테스트.

핵심 회귀 방지: 카카오가 refresh_token을 회전시킬 때 .env 저장(persist)을
빠뜨리면 KOE322(만료/무효)로 발송이 끊긴다. client_secret 누락은 KOE010.
requests.post 를 mock 해 실제 호출 없이 검증한다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.kakao_client import KakaoClient  # noqa: E402


class FakeResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


def make_client(persisted, secret="secret32"):
    return KakaoClient(
        "restkey", "OLD_RTOK",
        client_secret=secret,
        persist_refresh=lambda t: persisted.append(t),
    )


class TestKakaoTokenRotation(unittest.TestCase):
    def test_rotation_persists_new_refresh_token(self):
        persisted: list[str] = []
        c = make_client(persisted)
        resp = FakeResp(200, {"access_token": "AT", "refresh_token": "NEW_RTOK"})
        with mock.patch("src.kakao_client.requests.post", return_value=resp):
            c._refresh_access_token()
        self.assertEqual(c.refresh_token, "NEW_RTOK")
        self.assertEqual(c.new_refresh_token, "NEW_RTOK")
        self.assertEqual(persisted, ["NEW_RTOK"])  # .env 저장 호출됨

    def test_no_refresh_token_in_response_no_persist(self):
        persisted: list[str] = []
        c = make_client(persisted)
        resp = FakeResp(200, {"access_token": "AT"})  # 회전 없음
        with mock.patch("src.kakao_client.requests.post", return_value=resp):
            c._refresh_access_token()
        self.assertEqual(c.refresh_token, "OLD_RTOK")
        self.assertEqual(persisted, [])

    def test_same_refresh_token_no_persist(self):
        persisted: list[str] = []
        c = make_client(persisted)
        resp = FakeResp(200, {"access_token": "AT", "refresh_token": "OLD_RTOK"})
        with mock.patch("src.kakao_client.requests.post", return_value=resp):
            c._refresh_access_token()
        self.assertEqual(persisted, [])  # 동일 토큰이면 저장 안 함


class TestKakaoClientSecret(unittest.TestCase):
    def _capture_post(self, secret):
        persisted: list[str] = []
        c = make_client(persisted, secret=secret)
        captured = {}

        def fake_post(url, data=None, timeout=None):
            captured.update(data or {})
            return FakeResp(200, {"access_token": "AT"})

        with mock.patch("src.kakao_client.requests.post", side_effect=fake_post):
            c._refresh_access_token()
        return captured

    def test_client_secret_included_when_present(self):
        captured = self._capture_post("secret32")
        self.assertEqual(captured.get("client_secret"), "secret32")  # KOE010 방지

    def test_client_secret_omitted_when_absent(self):
        captured = self._capture_post(None)
        self.assertNotIn("client_secret", captured)


if __name__ == "__main__":
    unittest.main(verbosity=2)
