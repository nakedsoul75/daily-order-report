# 카카오톡 "나에게 보내기" 셋업 가이드

본인 카카오톡으로 리포트를 받기 위한 카카오 디벨로퍼스 앱 등록 + Refresh Token 획득.

## 1. 카카오 디벨로퍼스 가입

1. https://developers.kakao.com 접속
2. 본인 카카오 계정으로 로그인
3. **내 애플리케이션** → **애플리케이션 추가하기**
4. 입력:
   - **앱 이름**: `daily-order-report`
   - **사업자명**: 본인 또는 사업자명
5. 저장

## 2. 앱 키 확인

- 좌측 **앱 키** → **REST API 키** 메모
  ```
  KAKAO_REST_API_KEY = xxxxxxxxxxxxxxxxxxxx
  ```

## 3. 플랫폼 등록

- 좌측 **플랫폼** → **Web 플랫폼 등록**
- 사이트 도메인: `https://localhost`

## 4. 카카오 로그인 활성화

- 좌측 **카카오 로그인** → **활성화 ON**
- **Redirect URI** 등록: `https://localhost/callback`

## 5. 동의 항목 설정 ⚠️ 핵심

- 좌측 **카카오 로그인** → **동의항목**
- **`카카오톡 메시지 전송 (talk_message)`** → **선택 동의**로 설정
- (기본 정보는 동의 불필요)

## 6. Refresh Token 획득 (1회만)

### 6-1. 인가 코드 받기
브라우저 주소창에 (값 1개 치환):
```
https://kauth.kakao.com/oauth/authorize?
response_type=code&
client_id={REST_API_KEY}&
redirect_uri=https://localhost/callback&
scope=talk_message
```

→ 카카오 로그인 → 동의 → 리다이렉트된 URL에서 `code=XXXX` 복사

### 6-2. Code → Token 교환
터미널 (값 2개 치환):
```bash
curl -X POST "https://kauth.kakao.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id={REST_API_KEY}" \
  -d "redirect_uri=https://localhost/callback" \
  -d "code={CODE}"
```

응답:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "refresh_token": "AbCdEf...",          ← 이 값 저장 (60일 유효)
  "expires_in": 21599,
  "refresh_token_expires_in": 5183999,
  "scope": "talk_message"
}
```

## 7. .env / GitHub Secrets에 저장할 값

```
KAKAO_REST_API_KEY=xxxxxxxxxxxxxxx
KAKAO_REFRESH_TOKEN=xxxxxxxxxxxxxxx
```

## 8. 동작 확인 (선택)

```bash
# Access Token 재발급
curl -X POST "https://kauth.kakao.com/oauth/token" \
  -d "grant_type=refresh_token" \
  -d "client_id={REST_API_KEY}" \
  -d "refresh_token={REFRESH_TOKEN}"

# 나에게 메시지 발송
curl -X POST "https://kapi.kakao.com/v2/api/talk/memo/default/send" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -d 'template_object={"object_type":"text","text":"테스트","link":{"web_url":"https://example.com"}}'
```

본인 카톡 "나와의 채팅"에 메시지가 도착하면 성공.

## 토큰 갱신 정책 (자동화 됨)

| 토큰 | 유효기간 | 갱신 |
|---|---|---|
| Access Token | 6시간 | 매 호출 시 refresh_token으로 자동 발급 |
| Refresh Token | **60일** | 1개월 미만 남았을 때 자동 갱신 + GitHub Secrets 자동 업데이트 (선택) |

> 60일에 1번만 수동 재발급해도 됨. 자동 갱신은 GitHub Actions에서 `gh secret set` 명령으로 가능 (선택 사항).

## 참고
- 공식 문서: https://developers.kakao.com/docs/latest/ko/message/rest-api
- "나에게 보내기"는 본인 카카오톡 "나와의 채팅"으로만 발송 가능 (다른 사람 발송 불가)
