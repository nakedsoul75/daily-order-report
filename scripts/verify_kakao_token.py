"""카카오 토큰 유효성 검증 — refresh_token으로 access_token 발급을 시도한다.

KOE010(client_secret 누락/오류) 해소 여부를 확인하기 위한 진단.
- 성공: .env의 client_secret/refresh_token 유효 → 카카오 발송 복귀 가능
- KOE010: client_secret 값 오류 → 카카오 콘솔에서 시크릿 재확인 필요
- invalid_grant: refresh_token 만료 → get_kakao_token.py 재발급 필요

성공 시 refresh_token이 회전되면 .env에 자동 저장(메시지는 보내지 않음).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import requests  # noqa: E402

from src.kakao_client import from_env  # noqa: E402


def _save_refresh_token(new_token: str) -> None:
    env = ROOT / ".env"
    lines = env.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("KAKAO_REFRESH_TOKEN="):
            lines[i] = f"KAKAO_REFRESH_TOKEN={new_token}"
            break
    else:
        lines.append(f"KAKAO_REFRESH_TOKEN={new_token}")
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    kc = from_env()
    print(f"client_secret : {('있음 ' + str(len(kc.client_secret)) + '자') if kc.client_secret else '없음 (KOE010 원인)'}")
    print(f"refresh_token : {len(kc.refresh_token)}자")
    print("--- refresh_token → access_token 발급 시도 ---")
    try:
        kc._refresh_access_token()
    except requests.HTTPError as e:
        body = e.response.text[:400]
        print(f"[FAIL] HTTP {e.response.status_code}")
        print(f"  body: {body}")
        if "KOE010" in body:
            print("  → client_secret 값 오류. 카카오 콘솔 > 보안 > Client Secret 재확인 필요.")
        elif "invalid_grant" in body or "KOE" in body:
            print("  → refresh_token 만료/무효. get_kakao_token.py 재발급 필요.")
        return 1
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1

    print(f"[OK] access_token 발급 성공 ({len(kc.access_token)}자) — KOE010 해소 확인")
    if kc.new_refresh_token:
        _save_refresh_token(kc.new_refresh_token)
        print(f"[OK] refresh_token 회전됨 → .env 저장 ({len(kc.new_refresh_token)}자)")
    else:
        print("[OK] refresh_token 회전 없음 (아직 충분히 유효)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
