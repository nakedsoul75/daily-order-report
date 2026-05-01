"""
카페24 OAuth 1회 인증 헬퍼.

사용 절차:
  1. 카페24 개발자 센터에서 앱 생성 후 Client ID/Secret 확보
  2. .env 또는 환경변수에 CAFE24_MALL_ID, CAFE24_CLIENT_ID, CAFE24_CLIENT_SECRET 설정
  3. python scripts/get_cafe24_token.py
  4. 출력된 URL을 브라우저에서 열어 동의
  5. 리다이렉트된 URL의 ?code=... 부분을 복사해서 프롬프트에 붙여넣기
  6. 발급된 refresh_token을 .env / GitHub Secrets에 저장
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SCOPES = [
    "mall.read_application",
    "mall.read_order",
    "mall.read_product",
]


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--mall-id", default=os.getenv("CAFE24_MALL_ID"))
    parser.add_argument("--client-id", default=os.getenv("CAFE24_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.getenv("CAFE24_CLIENT_SECRET"))
    parser.add_argument(
        "--redirect-uri",
        required=True,
        help="카페24 앱에 등록한 Redirect URI (예: https://username.github.io/daily-order-report/callback.html)",
    )
    parser.add_argument(
        "--scope",
        default=",".join(DEFAULT_SCOPES),
        help="요청할 권한 (콤마 구분)",
    )
    args = parser.parse_args()

    missing = [k for k in ("mall_id", "client_id", "client_secret") if not getattr(args, k)]
    if missing:
        print(f"[ERROR] 누락된 값: {missing}. .env에 설정하거나 --xxx 인자로 전달하세요.")
        return 1

    auth_url = (
        f"https://{args.mall_id}.cafe24api.com/api/v2/oauth/authorize?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": args.client_id,
                "state": "init_install",
                "redirect_uri": args.redirect_uri,
                "scope": args.scope,
            }
        )
    )

    print("\n=== STEP 1. 아래 URL을 브라우저에서 열고 동의를 진행하세요 ===\n")
    print(auth_url)
    print("\n동의 후 리다이렉트된 페이지의 주소창에서 ?code=XXXX 부분을 복사하세요.")
    code = input("\n복사한 code 값을 붙여넣고 Enter: ").strip()
    if not code:
        print("[ERROR] code가 비어있습니다.")
        return 1

    print("\n=== STEP 2. Token 교환 중... ===")
    creds = base64.b64encode(f"{args.client_id}:{args.client_secret}".encode()).decode()
    resp = requests.post(
        f"https://{args.mall_id}.cafe24api.com/api/v2/oauth/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": args.redirect_uri,
        },
        timeout=15,
    )
    if not resp.ok:
        print(f"[ERROR] {resp.status_code} {resp.text}")
        return 1

    body = resp.json()
    print("\n=== STEP 3. 발급 결과 ===\n")
    print(f"  mall_id          : {body.get('mall_id')}")
    print(f"  scopes           : {body.get('scopes')}")
    print(f"  access_token     : {body.get('access_token')[:30]}...")
    print(f"  refresh_token    : {body.get('refresh_token')}")
    print(f"  expires_at       : {body.get('expires_at')}")
    print(f"  refresh_expires  : {body.get('refresh_token_expires_at')}")

    print("\n=== STEP 4. 다음 값을 .env / GitHub Secrets에 저장하세요 ===\n")
    print(f"  CAFE24_REFRESH_TOKEN={body.get('refresh_token')}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
