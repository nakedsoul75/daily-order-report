# -*- coding: utf-8 -*-
"""Dispatch notifier — 카카오 대체.
보고서/알림 메시지를 로컬 아웃박스(dispatch_outbox/queue.jsonl)에 적재한다.
kakao_client 와 동일한 send_text(text, link_url) 인터페이스 → 드롭인 교체용.
실제 사용자 전달은 Claude 예약작업이 dispatch_reader.py 로 읽어 PushNotification 으로 보낸다.
(카카오 토큰 60일 만료 문제 영구 회피)
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

OUTBOX_DIR = Path(__file__).resolve().parent.parent / "dispatch_outbox"
QUEUE = OUTBOX_DIR / "queue.jsonl"


class DispatchNotifier:
    """카카오 KakaoClient 와 같은 인터페이스. 전송 대신 로컬 큐에 적재."""

    def send_text(self, text: str, link_url: str = "") -> dict[str, Any]:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "text": text,
            "link_url": link_url,
            "sent": False,
        }
        with open(QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[DISPATCH] 큐 적재 → {QUEUE.name} ({len(text)}자)")
        return {"dispatched": True, "outbox": str(QUEUE)}


class FallbackNotifier:
    """1차 채널(예: 카카오) 우선 발송, 실패 시 2차 채널(예: dispatch)로 전송해 유실 방지.

    카카오 토큰 만료(KOE322)·KOE010·네트워크 장애 등으로 send_text가 예외를 던지면
    2차 채널로 폴백하고, 본문 앞에 실패 사실을 표시한다.
    kakao_client / DispatchNotifier 와 동일한 send_text(text, link_url) 인터페이스.
    """

    def __init__(self, primary: Any, fallback: Any) -> None:
        self.primary = primary
        self.fallback = fallback

    def send_text(self, text: str, link_url: str = "") -> dict[str, Any]:
        try:
            return self.primary.send_text(text, link_url)
        except Exception as e:
            reason = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"[NOTIFY] 1차 채널 실패 → 폴백 전송: {reason}")
            note = f"⚠️ 카카오 발송 실패({type(e).__name__}) → 백업 전달\n\n"
            result = self.fallback.send_text(note + text, link_url)
            if isinstance(result, dict):
                result["fallback"] = True
                result["primary_error"] = reason
            return result


def from_env() -> "DispatchNotifier":
    return DispatchNotifier()
