# GitHub 레포 + Pages + Secrets + Actions 셋업

## 1. 레포 생성 (Private)

```bash
cd "C:/Users/naked/Documents/agent/daily-order-report"
git init
git add .
git commit -m "Initial commit"

# GitHub CLI 인증 (최초 1회)
gh auth login

# Private 레포로 생성 + push
gh repo create daily-order-report --private --source=. --remote=origin --push
```

또는 GitHub 웹에서 빈 레포 생성 후:
```bash
git remote add origin https://github.com/{username}/daily-order-report.git
git branch -M main
git push -u origin main
```

> **반드시 Private**으로 생성 (Secrets는 안전하지만 코드/설정 노출 방지).

## 2. GitHub Pages 활성화 ⚠️ 카페24 App URL 요건

**중요**: GitHub Pages는 Private 레포의 경우 **GitHub Pro / Team / Enterprise** 플랜에서만 사용 가능.
무료 플랜이면 다음 중 선택:

### 옵션 A. 레포만 Public으로 전환 (가장 간단)
코드 자체는 비밀 정보 없음 (.env는 gitignore, Secrets는 별도 저장).
- 레포 Settings → Danger Zone → **Change visibility → Public**

### 옵션 B. 별도 Public 레포 생성 (정적 사이트 전용)
- 새 Public 레포 `daily-order-report-site` 생성
- `docs/site/` 내용만 push
- 이 레포로 Pages 활성화

### 옵션 C. GitHub Pro 가입 ($4/월) — Private 유지
- Private 레포에서 Pages 활성화 가능

→ **추천: 옵션 A**. 코드에 민감 정보가 없으니 Public 무방.

## 3. Pages 활성화 절차

1. 레포 페이지 → **Settings → Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / Folder: `/docs`
4. **Save**
5. 1~2분 대기 후 URL 확인:
   ```
   https://{username}.github.io/daily-order-report/
   ```
6. 브라우저 열어서 정상 표시되는지 확인 (index.html / callback.html)

> 이 URL을 [setup-cafe24.md](setup-cafe24.md) 에서 App URL / Redirect URI로 사용합니다.

## 4. GitHub Secrets 등록

레포 페이지 → **Settings → Secrets and variables → Actions → New repository secret**

다음 8개 모두 등록:

| Secret 이름 | 출처 |
|---|---|
| `CAFE24_MALL_ID` | 본인 쇼핑몰 ID |
| `CAFE24_CLIENT_ID` | [setup-cafe24.md](setup-cafe24.md) Step 3 |
| `CAFE24_CLIENT_SECRET` | 동일 |
| `CAFE24_REFRESH_TOKEN` | [setup-cafe24.md](setup-cafe24.md) Step 5 |
| `NAVER_COMMERCE_CLIENT_ID` | [setup-smartstore.md](setup-smartstore.md) Step 3 |
| `NAVER_COMMERCE_CLIENT_SECRET` | 동일 |
| `KAKAO_REST_API_KEY` | [setup-kakao.md](setup-kakao.md) Step 2 |
| `KAKAO_REFRESH_TOKEN` | [setup-kakao.md](setup-kakao.md) Step 6 |

CLI로도 가능:
```bash
gh secret set CAFE24_MALL_ID -b "myshop"
gh secret set CAFE24_CLIENT_ID -b "xxxx"
# ... 8개 모두
```

## 5. 수동 실행으로 테스트

레포 페이지 → **Actions** → **Daily Order Report** → **Run workflow**
- slot: `test` 선택 → 실행 → 카톡 도착 확인

## 6. 자동 실행 시각 (KST)

- **08:30** — 전일 마감 요약
- **12:30** — 오전 누적
- **18:00** — 일일 마감

> GitHub Actions cron은 ±15분 지연 가능 (무료 플랜의 정상 동작).
> 정확한 정시가 필요하면 사무실 PC의 Windows 작업 스케줄러를 백업으로 추가 등록 가능.

## 7. 로그 확인

레포 → **Actions** 탭 → 각 실행 클릭 → 로그 확인
- 발송 성공: `[SEND] Kakao response: {'result_code': 0}`
- 실패: 카카오톡으로 에러 메시지 자동 발송됨

## 8. 토큰 만료 시

| 토큰 | 만료 주기 | 대응 |
|---|---|---|
| 카페24 refresh_token | 2주 (자동 갱신) | 2주 이상 미실행 시 [setup-cafe24.md](setup-cafe24.md) Step 5 재실행 |
| 카카오 refresh_token | 60일 | [setup-kakao.md](setup-kakao.md) Step 6 재실행 |

재발급 후 Secrets 업데이트:
```bash
gh secret set CAFE24_REFRESH_TOKEN -b "새_토큰값"
gh secret set KAKAO_REFRESH_TOKEN -b "새_토큰값"
```
