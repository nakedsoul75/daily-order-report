"""Kakao OAuth helper — get refresh_token for "send to me" messaging.

Usage:
  1. Make sure KAKAO_REST_API_KEY is set in .env
  2. python scripts/get_kakao_token.py --redirect-uri "https://nakedsoul75.github.io/daily-order-report/callback.html"
  3. Open URL in browser, approve, copy code from callback page, paste here
  4. refresh_token auto-saved to .env
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--rest-api-key", default=os.getenv("KAKAO_REST_API_KEY"))
    parser.add_argument(
        "--redirect-uri",
        required=True,
        help="카카오 디벨로퍼스 앱에 등록한 Redirect URI",
    )
    parser.add_argument(
        "--scope",
        default="talk_message",
        help="요청할 권한 (default: talk_message)",
    )
    args = parser.parse_args()

    if not args.rest_api_key:
        print("[ERROR] KAKAO_REST_API_KEY not set in .env or --rest-api-key")
        return 1

    auth_url = "https://kauth.kakao.com/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": args.rest_api_key,
        "redirect_uri": args.redirect_uri,
        "scope": args.scope,
    })

    print("\n=== STEP 1. Open in browser, login + approve ===\n")
    print(auth_url)
    print("\n→ Copy the 'code' value from the callback page.")
    code = input("\nPaste code here and press Enter: ").strip()
    if not code:
        print("[ERROR] code empty")
        return 1

    print("\n=== STEP 2. Exchanging code for token... ===")
    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": args.rest_api_key,
            "redirect_uri": args.redirect_uri,
            "code": code,
        },
        timeout=15,
    )
    if not resp.ok:
        print(f"[ERROR] {resp.status_code} {resp.text}")
        return 1

    body = resp.json()
    rtok = body.get("refresh_token", "")
    print("\n=== STEP 3. Issued ===\n")
    print(f"  access_token  : {len(body.get('access_token',''))} chars")
    print(f"  refresh_token : {len(rtok)} chars (saved to .env)")
    print(f"  expires_in    : {body.get('expires_in')} sec")
    print(f"  refresh_expires_in: {body.get('refresh_token_expires_in')} sec")
    print(f"  scope         : {body.get('scope')}")

    # Auto-update .env
    env_path = ROOT / ".env"
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = False
        for i, ln in enumerate(lines):
            if ln.strip().startswith("KAKAO_REFRESH_TOKEN="):
                lines[i] = f"KAKAO_REFRESH_TOKEN={rtok}"
                updated = True
                break
        if not updated:
            lines.append(f"KAKAO_REFRESH_TOKEN={rtok}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[OK] .env auto-updated (KAKAO_REFRESH_TOKEN)")

    # Test send
    print("\n=== STEP 4. Test send to your KakaoTalk ===")
    at = body["access_token"]
    test_resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {at}"},
        data={
            "template_object": '{"object_type":"text","text":"✅ Daily Order Report 봇 연결 성공!\\n\\n이제 매일 08:30 / 12:30 / 18:00에 주문 리포트를 받으실 수 있습니다.","link":{"web_url":"https://nakedsoul75.github.io/daily-order-report/"}}'
        },
        timeout=15,
    )
    if test_resp.ok:
        print(f"  ✅ Test message sent! Check your KakaoTalk '나와의 채팅'.")
    else:
        print(f"  ⚠️  Test send failed: {test_resp.status_code} {test_resp.text[:300]}")
        print(f"  → 동의항목에서 'talk_message' 활성화 확인 필요")

    return 0


if __name__ == "__main__":
    sys.exit(main())
