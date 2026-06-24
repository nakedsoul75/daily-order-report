# 핸드오프: daily-order-report → 신규 OS 이식 가이드

> 생성: 2026-06-24 · 출처 세션: SmartStore 매출누락·카카오 KOE010 복구
> 받는 세션은 이 문서만 읽고도 코드·교훈·함정·미해결을 파악해 신규 OS에 적용할 수 있다.
> 원본 repo: https://github.com/nakedsoul75/daily-order-report (로컬: `C:\Users\naked\Documents\agent\daily-order-report`)

---

## 0. 한 줄 요약
카페24 + 네이버 스마트스토어 매출을 매일 1회(08:40 KST) 카카오로 보고하는 봇.
이번 세션에서 **스마트스토어 매출 누락(96.5%)·429**와 **카카오 토큰(KOE010/KOE322)**을 해결하고,
**발송 폴백 + 테스트 18건**을 추가했다. 신규 OS에는 "외부몰 매출 수집 + 알림" 모듈로 이식한다.

---

## 1. 이번 세션에서 해결한 것

| # | 문제 | 원인 | 해결 | 커밋 |
|---|---|---|---|---|
| 1 | 스마트스토어 매출 96.5% 누락 + 429 | `last-changed-statuses`(status 변경분만) + chunk 사이 sleep 없음 | `product-orders` + `rangeType=PAYED_DATETIME`(결제일 기준) 재구현, 24h 청크 + hasNext 페이지네이션 + 429 백오프/sleep | (smartstore) |
| 2 | 카카오 KOE010(보안 에러) | ① `get_kakao_token.py`가 토큰 교환 시 client_secret 누락 ② `kakao_client`가 회전된 refresh_token을 .env에 저장 안 함 → KOE322 | client_secret 포함 + 회전 토큰 영속화(`_default_persist`) + 재발급 | `9de478f` 외 |
| 3 | 발송 빈도 | 하루 4회(morning/midday/evening/alert) | **하루 1회 08:40, 전일(00:00~24:00) 매출**로 축소. alert(출하지연/재고) 폐지 | `9de478f` |
| 4 | 카카오 끊기면 알림 유실 | 단일 채널 | `FallbackNotifier`: 카카오 우선 + 실패 시 dispatch 큐 폴백 | `c9cefee` |
| 5 | 스마트스토어 재연결 실패(다음날) | **네이버 커머스 IP 화이트리스트** — 공인 IP 변경(`GW.IP_NOT_ALLOWED`) | 미해결 — 사용자가 네이버 API센터에 현재 IP 등록 대기 | — |

---

## 2. 이식 대상 모듈 (재사용 코드)

### 2.1 스마트스토어(네이버 커머스) 매출 수집 — `src/smartstore_client.py`
- **인증**: `client_credentials` + bcrypt 서명. access_token 3h, **매번 새로 발급(refresh 아님)** → 토큰 만료 걱정 없음. 단 **호출 IP가 화이트리스트에 있어야 함**.
- **주문 조회 (핵심 교훈)**: `GET /v1/pay-order/seller/product-orders`
  - `rangeType=PAYED_DATETIME`(결제일 기준), `from`/`to`(**최대 24h**), `pageSize=100`, `page`
  - 응답: `data.contents[].content.{order, productOrder}`, 페이지네이션 `data.pagination.{page,size,hasNext}`
  - ⚠️ `last-changed-statuses`는 "기간 내 status가 *변경된* 주문"만 → **매출 집계에 부적합**(대량 누락). 반드시 `PAYED_DATETIME`.
- **rate limit**: 청크/페이지 사이 `sleep`(기본 0.3s) + 429 시 `Retry-After`/지수백오프.
- 금액 = `productOrder.totalPaymentAmount`, 상태 = `productOrder.productOrderStatus`(STATUS_KR 매핑). 결제일 기준이라 **취소(CANCELED)도 포함** → status로 구분.

### 2.2 카카오 알림 + 토큰 관리 — `src/kakao_client.py`
- **client_secret 필수**: 앱에 시크릿 '사용함(필수)'이면 **모든 토큰 요청**(refresh + authorization_code 교환)에 `client_secret` 포함해야 함. 누락 시 **KOE010**.
- **refresh_token 회전 영속화(핵심)**: 카카오는 잔여 1개월 미만일 때 갱신 응답에 새 refresh_token을 준다. 이를 **.env에 즉시 저장**하지 않으면 다음 실행에서 **KOE322(만료/무효)**. → cafe24와 동일한 `persist_refresh` 콜백으로 `.env` 갱신.
```python
new_rtok = body.get("refresh_token")
if new_rtok and new_rtok != self.refresh_token:
    self.refresh_token = new_rtok
    self.persist_refresh(new_rtok)   # .env의 KAKAO_REFRESH_TOKEN 갱신
```
- 토큰 재발급: `scripts/get_kakao_token.py --redirect-uri ... [--code <code>]` (브라우저 로그인 1회, `--code`로 비대화형 가능).

### 2.3 발송 폴백 — `src/notify.py` `FallbackNotifier`
- `send_text(text, link_url)` 인터페이스 통일(kakao/dispatch 드롭인 호환).
- 1차(카카오) 예외 → 2차(dispatch 큐)로 폴백 + 본문에 실패 표시 → **유실 방지**.
- `NOTIFY_CHANNEL`: `kakao`(우선+폴백) / `kakao_only`(폴백X) / `dispatch`(로컬 큐).

### 2.4 토큰 영속화 패턴 (공통) — `cafe24_client._default_persist` / `kakao_client._default_persist`
- 회전형 refresh_token을 쓰는 모든 외부 API는 **새 토큰을 secret store(.env)에 즉시 저장**. 안 하면 다음 실행 실패. 신규 OS에서는 .env 대신 OS의 secret store에 저장하도록 콜백만 교체.

---

## 3. 반드시 알아야 할 함정 (교훈 체크리스트)
- [ ] **네이버 IP 화이트리스트**: 필수, 최대 3개, 전체허용 불가. 유동 IP면 변경 시마다 `GW.IP_NOT_ALLOWED` 재발 → **고정 IP 권장**. 진단: `python scripts/diagnose_naver_token.py`(현재 IP·403 body 출력).
- [ ] **네이버 주문조회**: `PAYED_DATETIME` 사용(= 매출). `last-changed-statuses`는 변경분만 → 누락.
- [ ] **네이버 24h 제한**: from~to ≤ 24h, 초과 시 code 4000 → 24h 청크 분할.
- [ ] **카카오 client_secret**: refresh + code 교환 양쪽 모두 포함(KOE010).
- [ ] **카카오 refresh_token 회전**: .env 저장 필수(KOE322). 60일 만료 + 회전 미저장 둘 다 끊김 원인.
- [ ] **graceful degradation**: 채널별 try/except로 한 채널 실패해도 나머지 발송.
- [ ] **.env 인코딩**: PowerShell `Set-Content -Encoding UTF8`은 BOM 추가 → 첫 키 깨짐. append는 `[System.IO.File]::AppendAllText(path, line, UTF8Encoding($false))`.
- [ ] **카카오 4000자 제한**: 본문 트림(현재 short_kakao + URL).

---

## 4. 환경변수 (신규 OS로 이전 — 값은 기존 .env에서, 키만 기재)
```
CAFE24_MALL_ID / CAFE24_CLIENT_ID / CAFE24_CLIENT_SECRET / CAFE24_REFRESH_TOKEN(회전) / CAFE24_SHOPS
NAVER_COMMERCE_CLIENT_ID / NAVER_COMMERCE_CLIENT_SECRET / NAVER_COMMERCE_STORE_NAME
KAKAO_REST_API_KEY / KAKAO_CLIENT_SECRET / KAKAO_REFRESH_TOKEN(회전)
NOTIFY_CHANNEL=kakao
```
> ⚠️ 시크릿은 절대 git/문서에 평문 노출 금지. .env(gitignore) 또는 OS secret store.

---

## 5. 미해결 / 즉시 후속
1. **네이버 IP 등록 (최우선)**: 현재 공인 IP `115.137.251.37`을 [네이버 커머스 API센터](https://apicenter.commerce.naver.com) → 내 스토어 애플리케이션 → [수정] → API호출 IP에 추가·저장. 등록 후 `python scripts/diagnose_naver_token.py`로 200 확인 → 누락분 재수집.
2. **라벨 표시버그**: 리포트 제목의 "08:30"은 `main.py SLOTS["morning"]` 하드코딩 텍스트. 실제 트리거는 08:40. 라벨만 정정 필요(사소).

---

## 6. 코드 위치 / 테스트
- 핵심: `src/smartstore_client.py`, `src/kakao_client.py`, `src/notify.py`, `src/main.py`(`_notifier_factory`, `slot_period`), `src/report_builder.py`
- 스크립트: `scripts/get_kakao_token.py`, `scripts/diagnose_smartstore_payed.py`, `scripts/diagnose_naver_token.py`, `scripts/register_scheduler.ps1`(08:40 1회)
- 테스트: `tests/test_smartstore.py`(11) · `tests/test_kakao.py`(5) · `tests/test_notify.py`(2) — 게이트 `run_tests.bat` (**18건 PASS**)

---

## 7. 신규 OS 적용 체크리스트
1. 위 4개 모듈(2.1~2.4) 이식 — `requests`+`bcrypt`+`python-dotenv` 의존.
2. 시크릿을 OS secret store로 이전, 토큰 영속화 콜백을 OS 저장소에 맞게 교체.
3. **신규 OS 실행 환경의 공인 IP를 네이버에 등록**(클라우드면 고정 egress IP 필요 — GitHub Actions 등 유동 IP 러너는 부적합).
4. 알림: OS 내 알림 채널이 있으면 `FallbackNotifier`의 primary/fallback만 교체.
5. 스케줄: 08:40 1회(전일 매출). 시각/주기는 OS 스케줄러로.
6. 테스트 18건 함께 이식 → 회귀 가드.

---

## 8. 새 세션 시작 프롬프트 (복붙용)
```
daily-order-report 프로젝트의 HANDOFF-매출봇.md (C:\Users\naked\Documents\agent\daily-order-report\)를 읽고,
[신규 OS 이름/경로]에 "외부몰(카페24+네이버 스마트스토어) 매출 수집 + 카카오 알림" 모듈을 이식해줘.
특히 §2 재사용 모듈과 §3 함정(네이버 IP 화이트리스트, 토큰 영속화, PAYED_DATETIME)을 반드시 반영.
시크릿은 노출 금지, 테스트(§6) 함께 이식.
```

---

## 9. BK's OS 전용 이식 구체안 (대상 확정: bks-os)

### 9.1 BK's OS 컨텍스트 (메모리 bks-os 기준)
- **정본 레포** `github.com/nakedsoul75/bks-os` — ⚠️ **전용레포 직접수정만**(vault 동기화 금지, 과거 stale 덮어쓰기 사고 이력). 로컬 `C:/Users/naked/Documents/bks-os/`.
- 스택: **Next.js PWA + Supabase(ref `fyrigwjcczlexpdzubag`) + Vercel**(main push → ~90s 자동배포). PWA 안드로이드 설치됨.
- 제약(불변): RLS 전테이블(`auth.uid() is not null`)·물리삭제 금지(`is_archived`)·3브랜드 격리·시크릿 push 금지·자동 결제/발신 금지.
- 게이트: `npm run build`(tsc) 통과 후 배포. 테스트: **순수로직 분리 + vitest**(`lib/*.test.ts` 패턴).
- **다음 후보에 "홈 대시보드 통계/차트(홈만 수정·마이그 불필요)"** 존재 → 매출 카드가 여기에 안착.

### 9.2 핵심 결정: 봇은 수집 유지, BK's OS는 표시만
Python 봇을 TS로 포팅하지 말 것. 봇(카페24+네이버 → 매출 적재)은 그대로 두고 BK's OS는 **요약을 읽어 표시**만 한다.

⚠️ **DB 분리 주의**: 매출 `orders`는 daily-order-report `.env SUPABASE_URL`(= commanine-inventory와 동일 DB로 추정)에 적재된다. 이는 **BK's OS Supabase(`fyrigwjcczlexpdzubag`)와 다른 프로젝트**이며, **commanine-inventory는 무료한도로 Pause됐을 수 있음**(메모리). → 통합 전 매출 DB 활성 여부 확인 필수.

### 9.3 권장 방식 — B2 (단방향 요약 동기화)
- **매출봇이 매일 1회**(08:40 발송 직후) **일일 매출 요약을 BK's OS Supabase 신규 테이블 `daily_sales`에 upsert**.
  - 봇에 BK's OS Supabase 자격(별도 env) + `daily_sales` 마이그레이션 추가.
  - BK's OS는 **자기 DB만** read → commanine-inventory Pause 무관·RLS 일관·무료 활성2개 한도 부합.
- 대안 **B1**(BK's OS가 매출 DB 직접 read): 2-DB 연결·`service_role` 노출 위험·Pause 영향 → **비권장**.

`daily_sales` 제안 스키마(요약 단위, line-item 아님):
```sql
create table daily_sales (
  sale_date date primary key,            -- 전일(KST)
  total_count int, total_amount bigint, total_cash bigint,
  new_buyer_count int,
  by_channel jsonb,                      -- [{sub_channel, count, amount}]
  top_products jsonb,                    -- [[name, qty], ...]
  updated_at timestamptz default now()
);
-- RLS: auth.uid() is not null (BK's OS 표준)
```
봇 측: `report_builder.aggregate()` 결과(이미 total_count/total_amount/by_subchannel/top_products 보유)를 위 형태로 매핑해 upsert(`main.py` 발송 직후 1회).

### 9.4 UI (BK's OS)
- **홈 매출 요약 카드**: 어제 총매출·건수·채널별·신규 — 기존 `QuickPanel`/`BriefingCard` 패턴 재사용, server component에서 `daily_sales` 최신 row read.
- 주간 추이 차트는 "홈 대시보드 통계/차트" 후보와 합류(`daily_sales` 최근 7행).
- AI 아침 브리핑에 "어제 매출 N건/₩X" 한 줄 — `lib/ai/prompts.ts` briefing 컨텍스트에 `daily_sales` 추가 (bks-os 세션8 교훈: **프롬프트 라인에 안 넣으면 모델이 못 봄**).

### 9.5 BK's OS 세션 시작 프롬프트 (복붙)
```
bks-os 전용레포(C:/Users/naked/Documents/bks-os/)에서 작업. vault 동기화 금지·직접수정만.
daily-order-report의 HANDOFF-매출봇.md §9를 읽고, 홈에 "어제 매출 요약 카드"를 추가:
- 방식 B2: 매출봇이 BK's OS Supabase 신규 테이블 daily_sales에 일일 요약 upsert → BK's OS는 자기 DB만 read.
- 마이그 supabase/migrations 신규 파일(daily_sales, RLS auth.uid) + 사용자 SQL 실행 안내.
- 홈 카드는 QuickPanel/BriefingCard 패턴, 순수로직은 lib/*.test.ts(vitest) 분리.
- 게이트 npm run build(tsc). 시크릿(service_role) 클라 노출 금지.
먼저 매출 DB(commanine-inventory) 활성 여부와 동기화 지점(매출봇 main.py 발송 직후)을 사용자와 확정할 것.
```
