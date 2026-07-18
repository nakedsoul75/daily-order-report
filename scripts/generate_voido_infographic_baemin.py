"""Voido 인포그래픽 v5 - 배민 광고 영업자 시점 (Recruitment Material)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

# 색상 - 배민 친화 틸/민트 톤
COLOR_PRIMARY = "#0F766E"      # 진한 틸
COLOR_BRAND = "#14B8A6"        # 메인 틸 (배민 톤 참조)
COLOR_ACCENT = "#F97316"       # 액션 오렌지
COLOR_SUCCESS = "#10B981"      # 그린
COLOR_DANGER = "#EF4444"       # 페인포인트 레드
COLOR_WARNING = "#F59E0B"      # 앰버
COLOR_LIGHT = "#F0FDFA"        # 연 틸
COLOR_BG_GRAY = "#F3F4F6"
COLOR_DARK = "#0F172A"
COLOR_GRAY = "#6B7280"

fig = plt.figure(figsize=(10, 22), facecolor='white')
fig.patch.set_facecolor('white')

ax = fig.add_subplot(111)
ax.set_xlim(0, 100)
ax.set_ylim(0, 220)
ax.axis('off')

def box(x, y, w, h, color, alpha=1.0, radius=2):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.5,rounding_size={radius}",
                       facecolor=color, edgecolor='none', alpha=alpha,
                       linewidth=0)
    ax.add_patch(p)

def text(x, y, s, size=11, color='black', weight='normal',
         ha='center', va='center', style='normal'):
    ax.text(x, y, s, fontsize=size, color=color, weight=weight,
            ha=ha, va=va, style=style)

# ============================================================
# 1. 헤더 (220 ~ 200)
# ============================================================
box(0, 200, 100, 20, COLOR_PRIMARY, radius=0)
text(50, 213, "배민 광고 영업 협업 제안", size=24, color='white', weight='bold')
text(50, 207, "디엘나인 × 배달의민족 광고 영업 — Win-Win 파트너십",
     size=11, color='#A7F3D0')
text(50, 202.5, "내부 영업 교육·설득용 자료  |  2026.05.19",
     size=9, color='#6EE7B7')

# ============================================================
# 2. 후크 라인 (200 ~ 192)
# ============================================================
box(5, 192, 90, 6, COLOR_ACCENT, radius=2)
text(50, 195,
     '"신규 점주, 가장 먼저 만나는 영업자가 이깁니다"',
     size=14, color='white', weight='bold')

# ============================================================
# 3. 현재 우리의 어려움 (190 ~ 172)
# ============================================================
text(50, 188, "■ 지금 영업, 이런 점이 힘들지 않나요?",
     size=14, color=COLOR_DARK, weight='bold')

pains = [
    (5, "₩↑\n발굴 비용 ↑",
     "콜드콜·전단·발품으로\n매일 새 점주 찾기"),
    (37, "[時]\n늦은 진입",
     "오픈 후 접근 시\n이미 다른 광고 계약됨"),
    (69, "X\n낮은 클로징",
     "신뢰 형성에 시간 소요\n거절·반려 빈번"),
]
for x, title, desc in pains:
    box(x, 174, 26, 12, COLOR_DANGER, alpha=0.85, radius=2)
    text(x + 13, 182.5, title, size=12, color='white', weight='bold')
    text(x + 13, 177, desc, size=8.5, color='white')

# ============================================================
# 4. 해결책: 디엘나인 = 시발점 접점 (170 ~ 145)
# ============================================================
text(50, 170, "■ 디엘나인은 점주를 가장 먼저 만납니다",
     size=14, color=COLOR_DARK, weight='bold')

# 타임라인 다이어그램
# 가로축: 점주 라이프사이클
text(50, 167, "점주 라이프사이클 — 누가 언제 만나는가?",
     size=10, color=COLOR_GRAY, style='italic')

# 타임라인 바
ax.add_patch(Rectangle((5, 158), 90, 1.5, facecolor='#CBD5E1'))

# 4단계 마커
stages = [
    (12.5, "인테리어\n시작"),
    (37.5, "인테리어\n완공"),
    (62.5, "오픈"),
    (87.5, "영업\n안정화"),
]
for x, label in stages:
    ax.add_patch(Circle((x, 158.75), 1.5, facecolor=COLOR_DARK))
    text(x, 155, label, size=8, color=COLOR_DARK, weight='bold')

# 디엘나인 진입 표시 (왼쪽)
box(5, 161, 25, 4, COLOR_BRAND, alpha=0.95, radius=1)
text(17.5, 163, "디엘나인 진입 ✓", size=10, color='white', weight='bold')
ax.annotate("", xy=(12.5, 160), xytext=(17.5, 161),
            arrowprops=dict(arrowstyle="->", color=COLOR_BRAND, lw=2))

# 기존 배민 영업 진입 표시 (오른쪽)
box(70, 161, 25, 4, COLOR_DANGER, alpha=0.85, radius=1)
text(82.5, 163, "기존 방식 (늦음)", size=10, color='white', weight='bold')
ax.annotate("", xy=(87.5, 160), xytext=(82.5, 161),
            arrowprops=dict(arrowstyle="->", color=COLOR_DANGER, lw=2))

# 메시지 박스
box(5, 147, 90, 5, COLOR_LIGHT, radius=2)
text(50, 150.5,
     "디엘나인과 협업하면 = 점주가 가게를 만드는 단계에서 당신과 연결됩니다",
     size=11, color=COLOR_PRIMARY, weight='bold')
text(50, 148.2,
     "오픈 후 접근 (X)  →  인테리어 단계에서 사전 접점 (○)",
     size=9, color=COLOR_GRAY)

# ============================================================
# 5. 어떻게 동작하나 (5단계) (144 ~ 116)
# ============================================================
text(50, 144, "■ 협업 프로세스 — 단 5단계",
     size=14, color=COLOR_DARK, weight='bold')

steps = [
    ("STEP 1", "디엘나인이\n점주와 인테리어 계약", COLOR_BRAND),
    ("STEP 2", "토털 패키지에\n'배민 깃발 영업' 옵션 포함", COLOR_PRIMARY),
    ("STEP 3", "점주 관심 표시 →\n당신에게 리드 전달", COLOR_ACCENT),
    ("STEP 4", "당신이 점주 방문\n→ 클로징", COLOR_SUCCESS),
    ("STEP 5", "광고비 0.5% 디엘나인 수수료\n당신 커미션은 그대로", COLOR_WARNING),
]

step_w = 17
step_gap = 1
step_total = step_w * 5 + step_gap * 4  # 89
start_x = 5

for i, (label, desc, color) in enumerate(steps):
    x = start_x + i * (step_w + step_gap)
    box(x, 120, step_w, 19, color, alpha=0.92, radius=2)
    text(x + step_w/2, 136, label, size=9, color='white', weight='bold')
    # 동그란 번호
    ax.add_patch(Circle((x + step_w/2, 132), 1.8, facecolor='white'))
    text(x + step_w/2, 132, str(i+1), size=11, color=color, weight='bold')
    text(x + step_w/2, 125, desc, size=8, color='white', weight='bold')
    # 화살표
    if i < 4:
        ax.annotate("", xy=(x + step_w + step_gap, 129),
                    xytext=(x + step_w + 0.1, 129),
                    arrowprops=dict(arrowstyle="->", color=COLOR_DARK, lw=1.5))

# 흐름 설명
text(50, 117.5,
     "당신은 '이미 관심 표시한 점주'만 방문 — 콜드콜·발품 0",
     size=10, color=COLOR_DARK, weight='bold')

# ============================================================
# 6. 영업자가 얻는 것 (115 ~ 92)
# ============================================================
text(50, 114, "■ 당신이 얻는 것 (구체적 이득)",
     size=14, color=COLOR_DARK, weight='bold')

benefits = [
    ("☎ → 0", "콜드콜 0건",
     "점주가 이미 관심\n표시한 상태에서 시작"),
    ("↑↑↑", "클로징 성공률 ↑",
     "인테리어 단계 신뢰\n사전 형성됨"),
    ("-50%", "영업 시간 절감",
     "발굴 시간 줄어\n월 처리 건수 2배"),
    ("₩ 100%", "커미션 100% 유지",
     "디엘나인 수수료는 별도\n당신 수입 그대로"),
]
b_w = 21
b_gap = 1
for i, (icon, title, desc) in enumerate(benefits):
    x = 5 + i * (b_w + b_gap)
    box(x, 95, b_w, 17, COLOR_SUCCESS, alpha=0.92, radius=2)
    text(x + b_w/2, 109, icon, size=18, color='white')
    text(x + b_w/2, 104.5, title, size=10, color='white', weight='bold')
    text(x + b_w/2, 99, desc, size=8, color='white')

# ============================================================
# 7. 수수료 구조 - 투명성 (91 ~ 73)
# ============================================================
text(50, 90, "■ 수수료 구조 — 100% 투명",
     size=14, color=COLOR_DARK, weight='bold')

fee_boxes = [
    (5, "디엘나인이 받는 것",
     "광고비의\n0.5%", "별도 — 광고사가 지급", COLOR_PRIMARY),
    (37, "당신이 받는 것",
     "기존 커미션\n100%", "그대로 — 변동 없음", COLOR_SUCCESS),
    (69, "점주가 부담하는 것",
     "시장가\n동일", "추가 비용 0원", COLOR_ACCENT),
]
for x, title, big, sub, color in fee_boxes:
    box(x, 75, 26, 13, color, alpha=0.95, radius=2)
    text(x + 13, 86, title, size=10, color='white', weight='bold')
    text(x + 13, 81.5, big, size=14, color='white', weight='bold')
    text(x + 13, 77, sub, size=8, color='white')

# ============================================================
# 8. 왜 리스크 없나 (72 ~ 50)
# ============================================================
text(50, 72, "■ 왜 리스크가 없나",
     size=14, color=COLOR_DARK, weight='bold')

risks = [
    ("✓", "접점만 제공",
     "디엘나인은 영업·클로징·CS에 개입하지 않음"),
    ("✓", "점주 DB 당신이 보유",
     "리드 전달 후 점주 관계는 당신의 자산"),
    ("✓", "다른 광고사로 빼가지 않음",
     "계약서에 명시 — 디엘나인은 한 점주당 한 영업자만 연결"),
    ("✓", "강제성 없음",
     "점주가 깃발 영업 거절해도 인테리어 가격 동일 — 신뢰 유지"),
]
for i, (mark, title, desc) in enumerate(risks):
    y = 67.5 - i * 4
    ax.add_patch(Rectangle((5, y), 90, 3.5,
                           facecolor='#F0FDFA' if i % 2 == 0 else '#FFFFFF',
                           edgecolor='#A7F3D0'))
    text(8, y + 1.7, mark, size=12, color=COLOR_SUCCESS,
         weight='bold', ha='left')
    text(13, y + 1.7, title, size=10, color=COLOR_DARK,
         weight='bold', ha='left')
    text(40, y + 1.7, desc, size=9, color=COLOR_GRAY, ha='left')

# ============================================================
# 9. 시작하는 법 (49 ~ 28)
# ============================================================
text(50, 49, "■ 지금 시작하려면 — 단 3단계",
     size=14, color=COLOR_DARK, weight='bold')

start_steps = [
    (5, "1", "디엘나인 영천 사옥 방문",
     "공장 + 쇼룸 라인 투어\n실체 있는 회사 확인"),
    (37, "2", "협력 계약 체결",
     "수수료 룰 합의\n점주 보호 조항 포함"),
    (69, "3", "첫 리드 수신 시작",
     "보통 1주일 내\n월 평균 5~15건 예상"),
]
for x, num, title, desc in start_steps:
    box(x, 32, 26, 14, COLOR_BRAND, alpha=0.92, radius=2)
    # 큰 번호 원
    ax.add_patch(Circle((x + 13, 43), 2.5, facecolor='white'))
    text(x + 13, 43, num, size=16, color=COLOR_BRAND, weight='bold')
    text(x + 13, 38.5, title, size=9.5, color='white', weight='bold')
    text(x + 13, 34, desc, size=8, color='white')

# 화살표 사이
for x in [31, 63]:
    ax.annotate("", xy=(x + 4, 39), xytext=(x, 39),
                arrowprops=dict(arrowstyle="->", color=COLOR_DARK, lw=2))

# ============================================================
# 10. 마무리 메시지 (27 ~ 7)
# ============================================================
box(5, 11, 90, 15, COLOR_PRIMARY, radius=2)
text(50, 22, "한 줄 결론",
     size=10, color='#A7F3D0', weight='bold', style='italic')
text(50, 18,
     "당신이 영업할 새 점주가 매주 자동으로 들어옵니다",
     size=13, color='white', weight='bold')
text(50, 14.5,
     "콜드콜 시대는 끝났습니다. 시발점에서 만나는 영업이 이깁니다.",
     size=10, color='#A7F3D0')

# ============================================================
# 11. 푸터 (6 ~ 0)
# ============================================================
box(0, 0, 100, 6, '#0F172A', radius=0)
text(50, 4, "디엘나인  |  배민 광고 영업자 협업 제안서  |  내부 교육용",
     size=8.5, color='#9CA3AF')
text(50, 1.7,
     "문의: 디엘나인 사업기획팀  |  영천 사옥 투어 상시 가능",
     size=8.5, color=COLOR_ACCENT, weight='bold')

plt.tight_layout(pad=0)
plt.savefig('/home/user/daily-order-report/docs/voido-infographic-baemin.png',
            dpi=160, bbox_inches='tight', facecolor='white',
            pad_inches=0.1)
print("Saved: /home/user/daily-order-report/docs/voido-infographic-baemin.png")
