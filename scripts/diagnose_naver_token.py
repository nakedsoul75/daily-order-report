"""네이버 커머스 토큰 발급 403 원인 진단 — 응답 body 확인.

raise_for_status 이전에 status/body를 그대로 출력해 403의 정확한 사유
(권한 회수 / 일시 차단 / 서명 오류 등)를 파악한다. 1회성 진단.
"""
import base64
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import bcrypt  # noqa: E402
import requests  # noqa: E402

cid = os.environ["NAVER_COMMERCE_CLIENT_ID"]
csec = os.environ["NAVER_COMMERCE_CLIENT_SECRET"]
store = os.getenv("NAVER_COMMERCE_STORE_NAME", "")
print(f"store={store} / client_id len={len(cid)} / secret len={len(csec)}")
print(f"client_id prefix={cid[:6]}... (식별용 앞 6자만)")

ts = int(time.time() * 1000)
sign = base64.standard_b64encode(
    bcrypt.hashpw(f"{cid}_{ts}".encode(), csec.encode())
).decode()

r = requests.post(
    "https://api.commerce.naver.com/external/v1/oauth2/token",
    data={
        "client_id": cid,
        "timestamp": ts,
        "client_secret_sign": sign,
        "grant_type": "client_credentials",
        "type": "SELF",
    },
    timeout=15,
)
print(f"\nstatus: {r.status_code}")
hint = {k: v for k, v in r.headers.items()
        if k.lower() in ("server", "date", "x-request-id", "content-type", "retry-after")}
print(f"headers: {hint}")
print("body:")
print(r.text[:1200])
