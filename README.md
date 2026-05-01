# Daily Order Report

카페24 + 네이버 스마트스토어 주문 내역을 매일 3회(08:30 / 12:30 / 18:00 KST) 카카오톡 "나에게 보내기"로 자동 전송하는 GitHub Actions 봇.

## 구성

| 구성요소 | 역할 | 비용 |
|---|---|---|
| 카페24 Admin API | 카페24 주문 조회 | 무료 |
| 네이버 커머스 API | 스마트스토어 주문 조회 | 무료 |
| 카카오톡 메시지 API | 본인에게 리포트 발송 | 무료 |
| GitHub Actions | cron 스케줄러 | 무료 (월 2,000분) |

## 디렉터리 구조

```
daily-order-report/
├── .github/workflows/daily-report.yml   # cron 3회/일
├── src/
│   ├── main.py                          # 진입점, 시간대별 분기
│   ├── cafe24_client.py                 # 카페24 Admin API
│   ├── smartstore_client.py             # 네이버 커머스 API
│   ├── kakao_client.py                  # 카톡 나에게 보내기
│   └── report_builder.py                # 집계/포맷팅
├── scripts/
│   └── get_cafe24_token.py              # 카페24 OAuth 1회 인증 헬퍼
├── tests/
│   ├── mock_cafe24.json
│   └── mock_smartstore.json
├── docs/
│   ├── site/
│   │   ├── index.html                   # GitHub Pages App URL
│   │   └── callback.html                # OAuth Redirect URI
│   ├── setup-cafe24.md
│   ├── setup-smartstore.md
│   ├── setup-kakao.md
│   └── setup-github.md
├── .env.example
├── .gitignore
└── requirements.txt
```

## 셋업 체크리스트 — 진행 순서

**Step 0** (최우선)
- [ ] **GitHub 레포 생성 + Pages 활성화** → [docs/setup-github.md](docs/setup-github.md) §1~3
  - `https://{username}.github.io/daily-order-report/` URL 확보 (카페24 App URL 요건)

**Step 1** (병렬 진행 가능)
- [ ] **카페24 앱 등록 + 테스트 모드 설치 + Refresh Token 발급** → [docs/setup-cafe24.md](docs/setup-cafe24.md)
- [ ] **네이버 커머스 API 신청** → [docs/setup-smartstore.md](docs/setup-smartstore.md)
- [ ] **카카오 디벨로퍼스 앱 등록 + Refresh Token 발급** → [docs/setup-kakao.md](docs/setup-kakao.md)

**Step 2**
- [ ] **GitHub Secrets 8개 등록** → [docs/setup-github.md](docs/setup-github.md) §4
- [ ] **로컬 테스트** (`python src/main.py --slot=test --no-send`)
- [ ] **GitHub Actions 수동 실행 → 카톡 도착 확인**
- [ ] **자동 cron 활성화 (자동으로 등록됨)**

## 발송 시각 (KST)

| Slot | 시각 | 조회 범위 |
|---|---|---|
| morning | 08:30 | 어제 00:00 ~ 23:59 (전일 마감 요약) |
| midday | 12:30 | 오늘 00:00 ~ 12:30 (오전 누적) |
| evening | 18:00 | 오늘 00:00 ~ 18:00 (일일 마감) |

## 리포트 샘플

```
📦 2026-05-01 18:00 일일 리포트

▣ 누적 (오늘 00:00~18:00)
   카페24       : 12건 / ₩487,000
   스마트스토어 : 8건  / ₩312,000
   ─────────────────────
   합계         : 20건 / ₩799,000

▣ 상태
   신규 5 / 결제완료 8 / 발송완료 7

▣ 상품 TOP3
   1. 상품A — 6건
   2. 상품B — 4건
   3. 상품C — 3건

▣ CS
   취소 1 / 환불요청 0 / 반품 0
```

## 실행

### 로컬 테스트
```bash
pip install -r requirements.txt
cp .env.example .env  # 값 채우기
python src/main.py --slot=morning
```

### GitHub Actions
`.github/workflows/daily-report.yml`이 자동으로 cron 3회 실행.
