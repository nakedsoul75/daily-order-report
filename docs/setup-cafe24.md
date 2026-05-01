# 카페24 Open API 셋업 가이드

> 출처: 카페24 공식 [신규 앱 제작 가이드](https://developers.cafe24.com/app/front/common/concepts/sellapp/newbuildapp)
>
> 본인 쇼핑몰 1개에서만 사용하는 **자가 사용 봇**이므로 **Step 06 검수 / Step 07 앱스토어 등록은 불필요**합니다.

## 0. 사전 준비 — App URL 확보 (HTTPS 필수)

카페24는 앱 등록 시 **HTTPS App URL과 Redirect URI**를 요구합니다. GitHub Pages로 무료 해결합니다.

→ [setup-github.md](setup-github.md) 의 "GitHub Pages 활성화" 절차를 먼저 완료하세요.

획득할 URL 두 개:
- **App URL**: `https://{username}.github.io/daily-order-report/`
- **Redirect URI**: `https://{username}.github.io/daily-order-report/callback.html`

## 1. 카페24 개발자 센터 가입

1. https://developers.cafe24.com 접속
2. 본인 카페24 계정으로 로그인 (24EC 통합 ID 사용 가능)
3. 약관 동의 → 가입 완료

## 2. 앱 생성

1. 좌측 **App** → **ADD Product**
2. 앱 정보 입력:
   - **앱 이름**: `daily-order-report` (자유)
   - **앱 카테고리**: 주문 관리
3. **App URL**, **Redirect URI(s)** 등록:
   ```
   App URL       : https://{username}.github.io/daily-order-report/
   Redirect URI  : https://{username}.github.io/daily-order-report/callback.html
   ```
4. **권한(Scope)** 설정 — 다음 3개만 체크:
   - `mall.read_application`
   - `mall.read_order`
   - `mall.read_product`
5. 저장

## 3. Client ID / Secret 확인

생성된 앱 → **앱 정보** 탭에서 메모:
```
CAFE24_MALL_ID       = (본인 쇼핑몰 ID, 예: myshop)
CAFE24_CLIENT_ID     = ...
CAFE24_CLIENT_SECRET = ...
```

> `.env` 파일에 저장. `.env`는 `.gitignore`에 의해 git에 올라가지 않음.

## 4. 본인 쇼핑몰에 "테스트 모드"로 설치

카페24 공식 가이드 Step 04 절차:

1. **개발자센터 → Apps → 내 앱 → STEP 01 (테스트)** 메뉴 진입
2. **테스트** 버튼 클릭
3. 본인 쇼핑몰 ID 입력 → 다음
4. 권한 동의 화면 → 승인
5. 앱 실행 → App URL 페이지(=GitHub Pages 메인)가 열림

→ 이 시점에 카페24가 본인 쇼핑몰에 앱을 설치한 상태가 됩니다. **검수 불필요, 앱스토어 등록 불필요.**

## 5. OAuth Refresh Token 획득 (1회만)

`scripts/get_cafe24_token.py` 헬퍼 스크립트 사용:

```bash
cd daily-order-report
pip install -r requirements.txt

# .env 에 CAFE24_MALL_ID, CAFE24_CLIENT_ID, CAFE24_CLIENT_SECRET 저장 후:
python scripts/get_cafe24_token.py \
  --redirect-uri "https://{username}.github.io/daily-order-report/callback.html"
```

스크립트 동작:
1. 인증 URL 출력 → 브라우저에서 열어 동의
2. 콜백 페이지(`callback.html`)에 표시되는 `code` 값을 복사 → 터미널에 붙여넣기
3. 토큰 교환 자동 수행
4. **`refresh_token`** 출력됨 → `.env` / GitHub Secrets에 저장

응답 예:
```
mall_id          : myshop
access_token     : XYz...
refresh_token    : AbCdEf123...           ← 이 값 저장
expires_at       : 2026-05-01T22:00:00.000
refresh_expires  : 2026-05-15T22:00:00.000
```

## 6. .env / GitHub Secrets 최종 값

| Key | Value |
|---|---|
| `CAFE24_MALL_ID` | 본인 쇼핑몰 ID |
| `CAFE24_CLIENT_ID` | Step 3에서 발급 |
| `CAFE24_CLIENT_SECRET` | Step 3에서 발급 |
| `CAFE24_REFRESH_TOKEN` | Step 5에서 발급 |

## 7. 동작 확인

```bash
python src/main.py --slot=test --no-send
```

콘솔에 카페24 주문이 정상 조회되면 OK. 카톡 발송은 Kakao 셋업 후 따로 검증.

## 토큰 만료 정책

| 토큰 | 유효기간 | 갱신 방식 |
|---|---|---|
| `access_token` | 2시간 | 매 호출 시 `refresh_token`으로 자동 발급 |
| `refresh_token` | **2주** | 사용할 때마다 자동 갱신 (rotating) |

→ GitHub Actions가 1일 3회 호출 → refresh_token이 항상 신선하게 유지됨.
→ **2주 이상 미실행 시** Refresh Token 만료 → Step 5 재실행 필요.

## API 호출 제한

- 버킷 방식: 초당 2회 보충
- 초과 시 HTTP 429 (Too Many Requests)
- 응답 헤더 `X-Cafe24-Call-Usage`로 사용률 확인
- → 일일 3회 호출 시 전혀 영향 없음

## 참고 링크

- 신규 앱 제작 가이드: https://developers.cafe24.com/app/front/common/concepts/sellapp/newbuildapp
- 앱 제작 FAQ: https://developers.cafe24.com/app/front/common/concepts/appservicefaq
- Admin API 문서: https://developers.cafe24.com/docs/api/admin/
- 동영상 가이드: https://youtu.be/8XIHe1Wtikc
