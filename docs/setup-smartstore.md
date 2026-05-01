# 네이버 커머스 API (스마트스토어) 셋업 가이드

본인 스마트스토어 주문 데이터를 조회하기 위한 애플리케이션을 등록합니다.

## 사전 조건 ⚠️

- 본인 ID가 스마트스토어 **"통합매니저"** 권한을 보유해야 합니다.
- 확인 방법: 스마트스토어센터 → 판매자정보 → 매니저 관리 → 본인 ID 권한 확인
- 통상 본인 명의 스토어 운영자는 자동으로 통합매니저입니다.

## 1. 커머스 API 센터 가입

1. https://apicenter.commerce.naver.com 접속
2. **통합매니저 ID로 로그인** (일반 ID 아님 주의)
3. 우측 상단 **계정생성**
4. 입력:
   - **개발업체 계정명**: 본인 사업자명 또는 자유
   - **장애대응 연락처**: 본인 연락처
5. 약관 동의 → 가입 완료

## 2. 애플리케이션 등록

1. **애플리케이션 등록** 클릭
2. 입력:
   - **애플리케이션 이름**: `daily-order-report`
   - **사용 환경**: 서버
   - **API 호출 IP**:
     - GitHub Actions 사용 시 — IP가 가변이므로 **`0.0.0.0/0`** 또는 IP 제한 해제 (보안 검토 필요)
     - 또는 고정 IP가 있는 사무실 PC 사용 시 해당 IP 등록
3. **API 그룹** 5개 모두 추가:
   - 상품
   - 주문/배송
   - 정산
   - 문의/리뷰
   - 회원/스토어
   (주문 조회만 쓸 거라면 "주문/배송"만 있어도 되지만, 향후 확장 위해 5개 권장)
4. 등록

## 3. Application ID / Secret 확인

- 등록된 애플리케이션 → 상세 → **Application ID**, **Application Secret** 메모

## 4. .env / GitHub Secrets에 저장할 값

```
NAVER_COMMERCE_CLIENT_ID=xxxxxxxxxxxxxxx
NAVER_COMMERCE_CLIENT_SECRET=xxxxxxxxxxxxxxx
```

> 카페24와 달리 OAuth Redirect 단계가 없습니다. **client_credentials** 방식으로 매 호출마다 access_token을 발급받습니다.

## 5. 동작 확인 (선택)

```bash
# 1) Access Token 발급
TIMESTAMP=$(($(date +%s) * 1000))
SIGNATURE=...  # HMAC-SHA256 서명 필요 (코드에서 자동 처리)

curl -X POST "https://api.commerce.naver.com/external/v1/oauth2/token" \
  -d "client_id={CLIENT_ID}" \
  -d "timestamp=${TIMESTAMP}" \
  -d "client_secret_sign={SIGNATURE}" \
  -d "grant_type=client_credentials" \
  -d "type=SELF"
```

→ 코드(`smartstore_client.py`)가 서명 생성과 토큰 발급을 자동 처리하므로 수동으로 할 필요는 없습니다. 발급 시 IP 제한 에러가 안 나오면 OK.

## 6. 호출 제한

- **초당 2회** (`2/s`)
- 일일 알림 용도라면 여유롭게 처리됨

## 참고
- 공식 GitHub (기술지원): https://github.com/commerce-api-naver/commerce-api
- 인증 방식: `client_credentials` (HMAC-SHA256 서명 + 타임스탬프)
- Access Token 유효기간: 3시간 (자동 재발급)
