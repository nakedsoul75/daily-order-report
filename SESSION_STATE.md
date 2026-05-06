# Daily Order Report — Session State

> 이 파일은 새 Claude 세션에서 작업 이어갈 때 컨텍스트 빠르게 파악하기 위한 메모입니다.
> 새 세션 시작 시 Claude에게 "이 프로젝트 SESSION_STATE.md 읽고 시작해줘"라고 말씀하세요.

## 프로젝트 개요

- **목적**: 카페24 + 네이버 스마트스토어 주문 데이터를 매일 3회(08:30/12:30/18:00 KST) 카카오톡으로 자동 보고
- **위치**: `C:\Users\naked\Documents\agent\daily-order-report`
- **GitHub**: https://github.com/nakedsoul75/daily-order-report (Public)
- **Pages**: https://nakedsoul75.github.io/daily-order-report/
- **리포트 인덱스**: https://nakedsoul75.github.io/daily-order-report/reports/

## 운영 상태 (2026-05-02 기준)

✅ **운영 중** — Windows 작업 스케줄러로 매일 자동 실행
- DailyOrderReport-Morning (08:30)
- DailyOrderReport-Midday (12:30)
- DailyOrderReport-Evening (18:00)

## 기술 스택

- **언어**: Python 3.13
- **데이터 소스**: 카페24 Admin API (v2026-03-01) + 네이버 커머스 API (SELF type)
- **알림**: 카카오 메시지 API (나에게 보내기)
- **호스팅**: GitHub Pages (HTML 리포트)
- **스케줄러**: Windows 작업 스케줄러 (PowerShell로 등록)

## 핵심 파일

```
src/
├── main.py                # 진입점, slot별 분기, HTML+Kakao 발송
├── cafe24_client.py       # 카페24 API + 다중 shop 지원
├── smartstore_client.py   # 네이버 커머스 API
├── kakao_client.py        # 카카오 메시지 (with Client Secret)
└── report_builder.py      # 텍스트/HTML 리포트 + 짧은 카톡 메시지
scripts/
├── get_cafe24_token.py    # 카페24 OAuth 1회 인증 헬퍼
├── get_kakao_token.py     # 카카오 OAuth 1회 인증 헬퍼
├── diagnose_cafe24.py     # 카페24 API 진단
├── diagnose_smartstore.py # 스마트스토어 API 진단
├── register_scheduler.ps1 # Windows 작업 스케줄러 등록
└── unregister_scheduler.ps1
docs/                      # GitHub Pages 콘텐츠
├── index.html
├── callback.html          # OAuth callback 페이지
└── reports/               # 자동 생성된 HTML 리포트들
.env                       # 시크릿 (gitignore)
.env.example
```

## 환경 변수 (.env)

```
# 카페24 (다중 shop 지원: shop_no:이름 형식)
CAFE24_MALL_ID=commanine
CAFE24_CLIENT_ID=...
CAFE24_CLIENT_SECRET=...
CAFE24_REFRESH_TOKEN=...   # 22자, 매 호출마다 자동 회전+저장
CAFE24_SHOPS=1:한국어몰,2:사업자몰

# 네이버 커머스 (콤마캠핑 스토어 연결)
NAVER_COMMERCE_CLIENT_ID=...
NAVER_COMMERCE_CLIENT_SECRET=...
NAVER_COMMERCE_STORE_NAME=콤마캠핑

# 카카오 (Client Secret 필수 — 카카오 앱에서 활성화됨)
KAKAO_REST_API_KEY=...
KAKAO_CLIENT_SECRET=...
KAKAO_REFRESH_TOKEN=...
```

## 토큰 만료 일정

| 토큰 | 만료 | 갱신 방식 |
|---|---|---|
| 카페24 refresh_token | 2주 (사용 시 재연장) | 자동 — 14일 이상 PC 꺼두지 마세요 |
| 카카오 refresh_token | 60일 | 만료 시 `python scripts/get_kakao_token.py --redirect-uri "https://nakedsoul75.github.io/daily-order-report/callback.html"` 재실행 |

## 카페24 다중 쇼핑몰 (운영자 본인 정보)

| shop_no | 이름 | 비고 |
|---|---|---|
| 1 | 한국어몰 | 메인 매출 |
| 2 | 사업자몰 | 거의 사용 안 함 |

## 네이버 스마트스토어

| 스토어 | 통합매니저 ID | API 연결 |
|---|---|---|
| **콤마캠핑** | dlnine211207@naver.com | ✅ 연결됨 |
| 나인사인 | 동일 | 미연결 (사용 안 함) |

> 둘 다 같은 네이버 ID의 통합매니저. 콤마캠핑이 실제 매출 스토어. 처음에 잘못 나인사인으로 API 발급했다가 콤마캠핑 시크릿으로 교체함.

## 리포트 형식 (현재)

### 카톡 메시지 (짧은 요약 + URL)
```
📦 2026-05-02 18:00 일일 리포트
⏱ 기간
💰 총 N건 / ₩X
  • 카페24 (한국어몰) ...
  • 스마트스토어 (콤마캠핑) ...
📄 상세 리포트:
https://nakedsoul75.github.io/daily-order-report/reports/2026-05-02-evening.html
```

### HTML 리포트 (풀 콘텐츠)
- KPI 카드 (총 매출 + 총 주문)
- 채널별 매출 막대 차트
- 상태/CS 요약
- 상품 TOP 5
- 전체 주문 테이블 (시간/채널/주문/고객/상태/매출/상품)
- 신규 고객 강조 (노란 배경)
- 모바일 반응형

## 주요 비즈니스 로직 결정사항

1. **매출 = `actual_order_amount.order_price_amount`** (실 상품 주문가)
   - `payment_amount` (실 카드결제)는 별도 표시
   - 적립금/할인 사용 시 두 값이 크게 다를 수 있음 (#188 케이스)

2. **고객명 마스킹**: `홍길동 → 홍**`, `김철 → 김*`, `이수민철 → 이**철`

3. **신규 vs 기존**: 카페24 `first_order=T` 필드로 구분, ⭐신규 표시

4. **같은 고객/시각 묶음**: (channel, shop, buyer, HH:MM) 동일 시 한 줄로 합쳐 표시

5. **카페24 status 매핑** (v2026-03-01에는 직접 status 필드 없음 → derive):
   - canceled='T' or cancel_date → 취소
   - paid='F' → 결제대기
   - paid='T' + shipping_status='F' → 결제완료
   - shipping_status='A/B/C/D' → 배송준비/중/완료/지연

6. **스마트스토어 시간 범위 24h 제한**: 코드에서 자동 chunk 처리

## 알려진 이슈/제약

- **GitHub Pages는 Public 레포 필수** (Pro 없으면). 시크릿은 .env(gitignore) + GitHub Secrets에 보관해서 안전.
- **카페24 사업자몰(shop_no=2)**: 거의 사용 안 함 (0건 표시 정상)
- **카카오 메시지 4000자 제한**: format_report에 자동 분할 로직 있지만, 현재 short_kakao 사용 중이라 거의 사용되지 않음
- **로그 인코딩**: PowerShell `chcp 65001`로 UTF-8 처리

## 사용자 선호 사항 (관찰)

- 한국어로 응답 선호
- 단계별 자세한 가이드 + 캡처 확인 후 진행
- 시크릿 값 노출 절대 금지 (길이만 표시)
- "옵션 A/B/C/D" 형식 선택지 제공 받기 선호
- COMMANINE 캠핑가구 브랜드 운영 (Factory Nine 자회사)

## 향후 개선 아이디어

- [ ] PDF 리포트 추가 (현재는 HTML만)
- [ ] 텔레그램 봇 보조 채널 (카톡 만료 백업용)
- [ ] 일별/주별/월별 비교 차트
- [ ] 환불·취소 즉시 알림 (5분 polling)
- [ ] 재고 부족 알림
- [ ] 일본어몰 추가 (확장 시)

## 자주 쓰는 명령어

```powershell
# 즉시 한 번 실행
Start-ScheduledTask -TaskName "DailyOrderReport-Evening"

# 로그 보기
Get-Content "logs\evening.log" -Tail 30 -Encoding UTF8

# 작업 상태 확인
Get-ScheduledTask -TaskName "DailyOrderReport-*" | Select TaskName, State, LastRunTime

# 수동 실행 (no Kakao send)
python src/main.py --slot=test --no-send

# 카카오 토큰 재발급 (60일마다)
python scripts/get_kakao_token.py --redirect-uri "https://nakedsoul75.github.io/daily-order-report/callback.html"

# 카페24 토큰 재발급 (2주 이상 미실행 시)
python scripts/get_cafe24_token.py --redirect-uri "https://nakedsoul75.github.io/daily-order-report/callback.html"

# 스케줄러 재등록 (코드 변경 후)
powershell -ExecutionPolicy Bypass -File scripts\register_scheduler.ps1
```

## 최근 commit 히스토리 (최신순)

- `00e3e63` 직구 (배대지) 감지 — Sheet2 461행 학습 + 카톡/HTML/Streamlit 통합
- `de32f2a` Graceful per-channel error handling
- `4a7d2d4` HTML report + short Kakao msg with link
- (중간 생략) ...
- `af493f2` Initial commit

## 🔥 진행 중 — 다음 세션에서 즉시 이어갈 작업 (2026-05-06 기준)

### ⚠️ 결정 대기 중 — SmartStore 데이터 누락 이슈

**문제**: 지난주매출 카톡에 SmartStore "스토어 3건"으로 나옴 → 실제 86건 (96.5% 누락).
- 원인: `lastChangedType=PAYED` 필터가 너무 좁음. 그 기간 내 "결제완료로 변경된" 주문만 잡힘.
- 그 기간 내 활동 status 분포: PURCHASE_DECIDED 45건, DISPATCHED 23건, CLAIM_COMPLETED 15건, **PAYED 3건만**
- 추가: 지난달매출(30일치)에서 SmartStore API 429 Too Many Requests (rate limit)

**진단 결과 (이미 수행)**:
- `last-changed-statuses` API는 본질적으로 "기간 내 status 변경된 주문" 용도 → 매출 집계 부적합
- moreSequence 페이지네이션은 OK (각 chunk 100건 미만, 누락 X)
- chunk 사이 sleep 없어서 30+ chunk 호출 시 429 발생

**제시한 옵션 (사용자 결정 대기)**:
- **[A] paymentDate 기준 재구현 (1시간) ⭐ 추천** — `/v1/pay-order/seller/product-orders` + `rangeType=PAYED_DATETIME`
- [B] lastChangedType 제거 + dedup (10분)
- [C] 옵션 B + status별 분류 표시 (30분)
- [D] Rate limit sleep만 추가 (5분, 데이터 누락은 그대로)

**다음 세션 첫 작업**: 사용자 결정 받고 → A/B/C/D 중 진행.

### ✅ 직구 감지 시스템 (2026-05-06 완료, 라이브 운영 중)

- `data/forwarder_dict.json`: Sheet2 461행에서 학습 — 95 names + 102 addresses + 63 keywords
- `src/forwarder.py`: 4-tier 감지 (allowlist → addr fp → keywords → pattern)
- 한국 일반인 false positive 방지 (한글 성씨 + 키워드만 매칭은 무시)
- 카톡: "🌏 직구 N건 / ₩X" 한 줄 추가
- HTML: 주문 행에 [🌏직구] 보라 태그
- Supabase orders.is_overseas_proxy 자동 저장 (SQL 마이그레이션 02 완료됨)
- Streamlit: 직구 필터 + 대시보드 카운트 + "직구" 컬럼

### ✅ 바탕화면 .bat 파일 5종 (2026-05-06 완료)

`C:\Users\naked\Desktop\` 에 cp949 인코딩으로 저장:
- `오늘매출.bat` → `--slot=today`
- `어제매출.bat` → `--slot=morning`
- `지난주매출.bat` → `--slot=last_week` (월~일 7일)
- `이번달매출.bat` → `--slot=this_month` (1일~지금)
- `지난달매출.bat` → `--slot=last_month` (지난달 전체)

### main.py 신규 slot (2026-05-06 추가)

- `today` — 오늘 00:00 ~ 지금
- `last_week` — 지난주 월~일
- `this_month` — 이번달 1일 ~ 지금
- `last_month` — 지난달 1일 ~ 말일
- 기존: morning / midday / evening / test / alert

### 현재 운영 상태 (2026-05-06)

- **카톡 자동 발송**: 08:30 / 09:00 / 12:30 / 18:00 정상 동작
- **Supabase orders**: 209+ 건 적재 중 (스마트스토어 적재율 낮음 — 위 이슈)
- **commanine-inventory.streamlit.app**: 외부 인터넷 접근 가능
- **GitHub 토큰 무효화**: ⚠️ 아직 처리 안 됨 (5/2 노출분) — 별도 처리 필요

---

**다음 세션 시작 가이드**:
1. Claude Code를 이 폴더에서 열기 (`C:\Users\naked\Documents\agent\daily-order-report`)
2. "SESSION_STATE.md 읽고 현재 상태 파악해줘" 라고 요청
3. 작업할 내용 알려주기
