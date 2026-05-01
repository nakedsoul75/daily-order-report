"""Kakao 'Send to Me' message client."""
from __future__ import annotations

import json
import os
from typing import Any

import requests


class KakaoClient:
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(self, rest_api_key: str, refresh_token: str) -> None:
        self.rest_api_key = rest_api_key
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.new_refresh_token: str | None = None  # if rotated

    def _refresh_access_token(self) -> None:
        resp = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.rest_api_key,
                "refresh_token": self.refresh_token,
            },
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        self.access_token = body["access_token"]
        # Kakao rotates refresh_token only when <1 month left
        if "refresh_token" in body:
            self.new_refresh_token = body["refresh_token"]
            self.refresh_token = body["refresh_token"]

    def send_text(self, text: str, link_url: str = "https://commerce.naver.com") -> dict[str, Any]:
        if not self.access_token:
            self._refresh_access_token()

        template = {
            "object_type": "text",
            "text": text[:3900],  # Kakao 4000자 제한, 여유 100자
            "link": {"web_url": link_url, "mobile_web_url": link_url},
            "button_title": "확인",
        }
        resp = requests.post(
            self.SEND_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            timeout=15,
        )
        if resp.status_code == 401:
            self._refresh_access_token()
            return self.send_text(text, link_url)
        resp.raise_for_status()
        return resp.json()


def from_env() -> KakaoClient:
    return KakaoClient(
        rest_api_key=os.environ["KAKAO_REST_API_KEY"],
        refresh_token=os.environ["KAKAO_REFRESH_TOKEN"],
    )
