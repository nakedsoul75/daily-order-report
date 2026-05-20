"""Voido 신규 비즈니스 모델 인포그래픽 생성 스크립트 (v2 - 업데이트 반영)."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import matplotlib.font_manager as fm

# 한글 폰트 설정 - Noto Sans CJK JP (Korean glyphs included in same TTC)
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

# 색상 팔레트
COLOR_PRIMARY = "#1E3A5F"      # 진한 네이비
COLOR_ACCENT = "#FF6B35"       # 오렌지
COLOR_SUCCESS = "#10B981"      # 그린
COLOR_WARNING = "#F59E0B"      # 앰버
COLOR_DANGER = "#EF4444"       # 레드
COLOR_LIGHT = "#F3F4F6"        # 연회색
COLOR_DARK = "#111827"         # 다크
COLOR_BLUE = "#3B82F6"         # 블루
COLOR_PURPLE = "#8B5CF6"       # 퍼플

# 모바일 친화 세로형 (확장된 높이)
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

def text(x, y, s, size=11, color='black', weight='normal', ha='center', va='center', style='normal'):
    ax.text(x, y, s, fontsize=size, color=color, weight=weight,
            ha=ha, va=va, style=style)

# ============================================================
# 1. 헤더 (220 ~ 200)
# ============================================================
box(0, 200, 100, 20, COLOR_PRIMARY, radius=0)
text(50, 213, "Voido 신규 비즈니스 모델", size=24, color='white', weight='bold')
text(50, 207, "강제성 없는 어필리에이트 + 자체 제조 원가 우위 + 협상력 플라이휠",
     size=11, color='#E5E7EB')
text(50, 202.5, "대표님 보고용  |  2026.05.19  |  콤마나인 사업기획팀",
     size=9, color='#9CA3AF')

# ============================================================
# 2. 한 줄 정의 (200 ~ 192)
# ============================================================
box(5, 192, 90, 6, COLOR_ACCENT, radius=2)
text(50, 195, '"인테리어 미끼상품 + 인프라 수수료 + 협력사 영업 외주화"',
     size=13, color='white', weight='bold')

# ============================================================
# 3. 핵심 가치 제안 3개 (190 ~ 175)
# ============================================================
text(50, 187, "■ 핵심 가치 제안 (3-Way Win)", size=14, color=COLOR_DARK, weight='bold')

box_y = 176
boxes = [
    (5, "고객 (점주)",
     "인테리어 30% 할인\n토털 패키지 원스톱\n(인테리어+주방+테이블)", COLOR_SUCCESS),
    (37, "협력사",
     "최선단 점주 접점 제공\n영업 성공율 상승\n영업 비용 절감", COLOR_BLUE),
    (69, "콤마나인",
     "영업 약점 회피\n인프라 수수료 누적\n네트워크 + 지속 마진", COLOR_PURPLE),
]
for x, title, desc, color in boxes:
    box(x, box_y, 26, 9, color, alpha=0.9, radius=2)
    text(x + 13, box_y + 7, title, size=11, color='white', weight='bold')
    text(x + 13, box_y + 3, desc, size=8, color='white')

# ============================================================
# 4. 진입 전략 (171 ~ 155)
# ============================================================
text(50, 171, "■ 진입 전략: 인테리어 = 미끼상품 (Trojan Horse)",
     size=14, color=COLOR_DARK, weight='bold')

box(5, 158, 42, 10, COLOR_LIGHT, radius=2)
text(26, 165.5, "타사 인테리어", size=10, color=COLOR_DARK, weight='bold')
text(26, 161, "1,000만원", size=18, color=COLOR_DARK, weight='bold')

box(53, 158, 42, 10, COLOR_ACCENT, radius=2)
text(74, 165.5, "Voido 인테리어", size=10, color='white', weight='bold')
text(74, 161, "700만원", size=18, color='white', weight='bold')

ax.annotate("", xy=(53, 163), xytext=(47, 163),
            arrowprops=dict(arrowstyle="->", color=COLOR_DANGER, lw=2.5))
text(50, 156, "30% 할인", size=9, color=COLOR_DANGER, weight='bold')
text(50, 154, '"최소 공장 마진까지 빼고 판다 + 풀 패키지라 가능한 구조"',
     size=8.5, color='#6B7280', style='italic')

# ============================================================
# 5. 마진 구조 재설계 (152 ~ 132)
# ============================================================
text(50, 150, "■ 마진 구조 재설계", size=14, color=COLOR_DARK, weight='bold')

# 표 헤더
box(5, 141, 90, 6, COLOR_PRIMARY, radius=1)
text(20, 144, "사업 라인", size=10, color='white', weight='bold')
text(50, 144, "기존 마진", size=10, color='white', weight='bold')
text(80, 144, "신규 마진", size=10, color='white', weight='bold')

# 행 1
ax.add_patch(Rectangle((5, 136), 90, 5, facecolor='#F9FAFB', edgecolor='#E5E7EB'))
text(20, 138.5, "팩토리나인 (자체 제조)", size=9, color=COLOR_DARK)
text(50, 138.5, "정상", size=9, color=COLOR_DARK)
text(80, 138.5, "이익 보존", size=9, color=COLOR_SUCCESS, weight='bold')

# 행 2
ax.add_patch(Rectangle((5, 131), 90, 5, facecolor='#FFFFFF', edgecolor='#E5E7EB'))
text(20, 133.5, "DL Nine (판매)", size=9, color=COLOR_DARK)
text(50, 133.5, "100%", size=9, color=COLOR_DARK)
text(80, 133.5, "30%만", size=9, color=COLOR_ACCENT, weight='bold')

# 행 3
ax.add_patch(Rectangle((5, 126), 90, 5, facecolor='#F9FAFB', edgecolor='#E5E7EB'))
text(20, 128.5, "인프라 수수료", size=9, color=COLOR_DARK)
text(50, 128.5, "0%", size=9, color=COLOR_DARK)
text(80, 128.5, "0.5~1% 누적", size=9, color=COLOR_BLUE, weight='bold')

# 행 4 (신규)
ax.add_patch(Rectangle((5, 121), 90, 5, facecolor='#FFFFFF', edgecolor='#E5E7EB'))
text(20, 123.5, "인프라 초기 계약 수수료", size=9, color=COLOR_DARK)
text(50, 123.5, "0%", size=9, color=COLOR_DARK)
text(80, 123.5, "300만원/건", size=9, color=COLOR_BLUE, weight='bold')

# ============================================================
# 6. 인프라 수익원 (118 ~ 95)
# ============================================================
text(50, 118, "■ 인프라 수익원 (점주 1명당 — 실 영업 담당자와 숫자 확인 필요)",
     size=12.5, color=COLOR_DARK, weight='bold')

revenues = [
    ("카드 단말기", "거래액 0.0X% × 수년", "월 2~5만원"),
    ("인터넷 구독", "계약수수료 + 리베이트", "월 1~2만원"),
    ("정수기 렌탈", "렌탈료 0.5%", "월 0.1~0.3만원"),
    ("테이블오더", "설치비 + 월 사용료", "월 3~10만원"),
    ("배민 광고/깃발", "광고비 0.5%", "월 2~5만원"),
]

rev_y = 113
for i, (name, struct, amt) in enumerate(revenues):
    y = rev_y - i * 3
    bg = '#F9FAFB' if i % 2 == 0 else '#FFFFFF'
    ax.add_patch(Rectangle((5, y), 90, 3, facecolor=bg, edgecolor='#E5E7EB'))
    text(8, y + 1.5, name, size=9, color=COLOR_DARK, ha='left', weight='bold')
    text(45, y + 1.5, struct, size=8.5, color='#6B7280')
    text(88, y + 1.5, amt, size=9, color=COLOR_ACCENT, weight='bold', ha='right')

# 합계
box(5, 95, 90, 3.5, COLOR_PRIMARY, radius=1)
text(8, 96.5, "월 합계", size=10, color='white', ha='left', weight='bold')
text(88, 96.5, "월 6~16만원", size=11, color='white', ha='right', weight='bold')

# 일회성
box(5, 91, 90, 3.5, '#7C3AED', radius=1)
text(8, 92.5, "일회성 수수료", size=10, color='white', ha='left', weight='bold')
text(88, 92.5, "300~500만원", size=11, color='white', ha='right', weight='bold')

text(50, 88.5, "→ 연 환산 70~190만원 + 일회성 300~500만원",
     size=9.5, color=COLOR_SUCCESS, weight='bold')

# ============================================================
# 7. 영업 외주화 (86 ~ 70)
# ============================================================
text(50, 86, "■ 영업 조직 외주화 (핵심 혁신)",
     size=14, color=COLOR_DARK, weight='bold')

# 중앙 콤마나인
ax.add_patch(Circle((50, 78), 6, facecolor=COLOR_PRIMARY, edgecolor='none'))
text(50, 79.5, "디엘나인", size=10, color='white', weight='bold')
text(50, 77, "접점 큐레이션", size=8, color='white')

partners = [
    (15, 80, "배민\n영업조직"),
    (15, 74, "정수기\n영업조직"),
    (50, 68, "지역\n영업맨"),
    (85, 80, "POS·테이블\n오더 업체"),
    (85, 74, "카드사·\n인터넷"),
]
for x, y, name in partners:
    ax.add_patch(Circle((x, y), 4.5, facecolor=COLOR_BLUE, alpha=0.85, edgecolor='none'))
    text(x, y, name, size=7, color='white', weight='bold')
    ax.annotate("", xy=(x, y), xytext=(50, 78),
                arrowprops=dict(arrowstyle="<->", color='#94A3B8', lw=1, alpha=0.6))

# ============================================================
# 8. 플라이휠 (68 ~ 54)
# ============================================================
text(50, 66, "■ 플라이휠: 점주 풀 → 협상력 → 인바운드",
     size=14, color=COLOR_DARK, weight='bold')

phases = [
    (5, 57, "초기\n점주 1~30명", "수수료 0.5%", COLOR_WARNING),
    (37, 57, "중기\n점주 30~100명", "수수료 0.7%", COLOR_BLUE),
    (69, 57, "장기\n점주 100명+", "수수료 1%+\n역인바운드", COLOR_SUCCESS),
]
for x, y, title, sub, color in phases:
    box(x, y, 26, 6, color, alpha=0.9, radius=2)
    text(x + 13, y + 4, title, size=9, color='white', weight='bold')
    text(x + 13, y + 1.5, sub, size=8, color='white')

for x in [31, 63]:
    ax.annotate("", xy=(x + 4, 60), xytext=(x, 60),
                arrowprops=dict(arrowstyle="->", color=COLOR_DARK, lw=2))

text(50, 53.5,
     "임계점 돌파 시 협력사 협상력 비약 상승 + 대기업 직접 코드 발급",
     size=9, color=COLOR_DARK, weight='bold')

# ============================================================
# 9. 신뢰 구축 (51 ~ 41)
# ============================================================
text(50, 50, "■ 신뢰 구축 메커니즘", size=14, color=COLOR_DARK, weight='bold')

trust = [
    (5, "영천 공장+사옥",
     "라인 투어 + 쇼룸\n실체 있는 회사 증명", COLOR_DANGER),
    (37, "강제성 제거",
     "옵션 선택 보장\n가맹사업법 회피", COLOR_ACCENT),
    (69, "시장가 동일",
     "추가 마진 없음\n수수료는 협력사 부담", COLOR_PURPLE),
]
for x, title, desc, color in trust:
    box(x, 42, 26, 7, color, alpha=0.9, radius=2)
    text(x + 13, 46.5, title, size=10, color='white', weight='bold')
    text(x + 13, 43.5, desc, size=8, color='white')

# ============================================================
# 10. 차별화 3대 카드 (40 ~ 30)
# ============================================================
text(50, 39, "■ 콤마나인만의 차별화 3대 카드",
     size=14, color=COLOR_DARK, weight='bold')

cards = [
    (5, "1\n자체 제조\n원가 우위",
     "팩토리나인\n경쟁사 모방 불가", COLOR_DANGER),
    (37, "2\n공장+쇼룸\n라인 투어",
     "신뢰성 ↑\n의심 차단", COLOR_ACCENT),
    (69, "3\n지역(영남권)\n선점",
     "거점 확보\n확장 베이스", COLOR_PURPLE),
]
for x, num_title, desc, color in cards:
    box(x, 31, 26, 7, color, alpha=0.9, radius=2)
    text(x + 13, 35.5, num_title, size=10, color='white', weight='bold')
    text(x + 13, 32.5, desc, size=8, color='white')

# ============================================================
# 11. 시장 벤치마크 (28 ~ 18)
# ============================================================
text(50, 28, "■ 시장 벤치마크 (한국 유사 모델)",
     size=14, color=COLOR_DARK, weight='bold')

box(5, 23, 90, 4, COLOR_LIGHT, radius=1)
text(20, 25, "이디야·메가커피", size=10, color=COLOR_DARK, weight='bold', ha='left')
text(75, 25, "동일 구조 / 단 강제성 있음 (가맹)",
     size=9, color='#6B7280', ha='left')

box(5, 18.5, 90, 4, COLOR_LIGHT, radius=1)
text(20, 20.5, "더본코리아", size=10, color=COLOR_DARK, weight='bold', ha='left')
text(75, 20.5, "동일 구조 / 가맹본부 형태",
     size=9, color='#6B7280', ha='left')

text(50, 16,
     "→ 콤마나인 = 자체 제조 + 옵셔널 구조의 한국 맞춤형 변형",
     size=9.5, color=COLOR_SUCCESS, weight='bold')

# ============================================================
# 12. 의사결정 요청 (14 ~ 4)
# ============================================================
box(0, 4, 100, 10, COLOR_PRIMARY, radius=0)
text(50, 12, "■ 대표님께 의사결정 요청", size=13, color='white', weight='bold')

decisions = [
    "① Phase 1 (대구·경북) 파일럿 추진 승인",
    "② 가맹사업법 변호사 자문 진행 승인",
    "③ DL Nine 팩토리 공급 제품 마진 정책 변경 (100% → 70%)",
    "④ 전체 마진 구조 분석 시트 작성 (팩토리 30% / 시공·자재 마진 유지)",
]
for i, d in enumerate(decisions):
    text(50, 10.5 - i * 1.5, d, size=9.5, color='white', weight='bold')

# ============================================================
# 13. 푸터 (4 ~ 0)
# ============================================================
box(0, 0, 100, 4, '#111827', radius=0)
text(50, 2.5, "콤마나인 / 디엘나인  |  Voido 사업기획팀  |  내부 보고용",
     size=8.5, color='#9CA3AF')
text(50, 0.8,
     "검증된 패턴 + 자체 제조 원가 우위 + 강제성 제거 = 작동 가능한 모델",
     size=8.5, color=COLOR_ACCENT, weight='bold')

plt.tight_layout(pad=0)
plt.savefig('/home/user/daily-order-report/docs/voido-infographic.png',
            dpi=160, bbox_inches='tight', facecolor='white',
            pad_inches=0.1)
print("Saved: /home/user/daily-order-report/docs/voido-infographic.png")
