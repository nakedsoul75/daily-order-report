# -*- coding: utf-8 -*-
"""dispatch 아웃박스 reader.
미발송(sent=false) 메시지를 꺼내 화면에 출력하고 sent=true 로 표시한다.
Claude 예약작업이 이 스크립트를 실행 → 출력에 'MSG'가 있으면 각각 PushNotification 으로 전달.
출력 없으면(전부 발송됨) 'NONE'.

  python dispatch_reader.py          # 미발송 출력 + sent 표시
  python dispatch_reader.py --peek   # 출력만(표시 안 함, 디버그)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "dispatch_outbox" / "queue.jsonl"


def main() -> int:
    peek = "--peek" in sys.argv
    if not QUEUE.exists():
        print("NONE")
        return 0
    recs = []
    for ln in QUEUE.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            recs.append(json.loads(ln))
        except Exception:
            pass
    pending = [r for r in recs if not r.get("sent")]
    if not pending:
        print("NONE")
        return 0
    for i, r in enumerate(pending, 1):
        print(f"--- MSG {i} ({r.get('ts','')}) ---")
        print(r.get("text", ""))
        if r.get("link_url"):
            print(f"[URL] {r['link_url']}")
        if not peek:
            r["sent"] = True
            r["sent_at"] = datetime.now().isoformat(timespec="seconds")
    if not peek:
        with open(QUEUE, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"--- {len(pending)}건 {'(peek)' if peek else 'sent 표시 완료'} ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
