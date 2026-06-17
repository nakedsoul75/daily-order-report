"""Kakao 'Send to Me' message client.

카카오는 refresh_token을 회전시킨다(잔여 1개월 미만일 때 토큰 갱신 응답에 새 refresh_token 포함).
회전값을 .env에 저장하지 않으면 다음 실행에서 KOE322(expired_or_invalid_refresh_token)로
실패하므로, cafe24_client 와 동일하게 persist_refresh 콜백으로 .env 에 즉시 저장한다.
또한 client_secret 은 앱에 시크릿이 '사용함(필수)'이면 토큰 요청에 반드시 포함해야 한다
(누락 시 KOE010).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import requests


def _default_persist(new_token: str) -> None:
    """Update .env file's KAKAO_REFRESH_TOKEN line in-place."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("KAKAO_REFRESH_TOKEN="):
            lines[i] = f"KAKAO_REFRESH_TOKEN={new_token}"
            updated = True
            break
    if not updated:
        lines.append(f"KAKAO_REFRESH_TOKEN={new_token}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class KakaoClient:
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(
        self,
        rest_api_key: str,
        refresh_token: str,
        client_secret: str | None = None,
        persist_refresh: Callable[[str], None] | None = None,
    ) -> None:
        self.rest_api_key = rest_api_key
        self.refresh_token = refresh_token
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.new_refresh_token: str | None = None  # if rotated
        self.persist_refresh = persist_refresh or _default_persist

    def _refresh_access_token(self) -> None:
        data = {
            "grant_type": "refresh_token",
            "client_id": self.rest_api_key,
            "refresh_token": self.refresh_token,
        }
        # 앱에 client_secret '사용함(필수)'이면 누락 시 KOE010
        if self.client_secret:
            data["client_secret"] = self.client_secret
        resp = requests.post(self.TOKEN_URL, data=data, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        self.access_token = body["access_token"]
        # Kakao rotates refresh_token only when <1 month left.
        # 회전 시 반드시 .env에 저장해야 다음 실행에서 KOE322(만료/무효)를 피한다.
        new_rtok = body.get("refresh_token")
        if new_rtok and new_rtok != self.refresh_token:
            self.refresh_token = new_rtok
            self.new_refresh_token = new_rtok
            try:
                self.persist_refresh(new_rtok)
            except Exception as e:
                print(f"[WARN] failed to persist new kakao refresh_token: {e}")

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
        client_secret=os.environ.get("KAKAO_CLIENT_SECRET") or None,
    )
