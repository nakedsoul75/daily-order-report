"""Voido 신규 비즈니스 모델 인포그래픽 생성 스크립트."""
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

# 모바일 친화 세로형 (9:16 비율, 큰 사이즈)
fig = plt.figure(figsize=(10, 22), facecolor='white')
fig.patch.set_facecolor('white')

# 전체 캔버스를 그리드로 나눔 (y=100을 최상단)
ax = fig.add_subplot(111)
ax.set_xlim(0, 100)
ax.set_ylim(0, 220)
ax.axis('off')

def box(x, y, w, h, color, alpha=1.0, radius=2):
    """라운드 박스."""
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.5,rounding_size={radius}",
                       facecolor=color, edgecolor='none', alpha=alpha,
                       linewidth=0)
    ax.add_patch(p)

def text(x, y, s, size=11, color='black', weight='normal', ha='center', va='center'):
    ax.text(x, y, s, fontsize=size, color=color, weight=weight,
            ha=ha, va=va)

# ============================================================
# 1. 헤더 (220 ~ 200)
# ============================================================
box(0, 200, 100, 20, COLOR_PRIMARY, radius=0)
text(50, 213, "Voido 신규 비즈니스 모델", size=24, color='white', weight='bold')
text(50, 207, "강제성 없는 어필리에이트 + 자체 제조 원가 우위 + 협상력 플라이휠",
     size=11, color='#E5E7EB')
text(50, 202.5, "대표님 보고 자료  |  2026.05.19  |  콤마나인", size=9, color='#9CA3AF')

# ============================================================
# 2. 한 줄 정의 (200 ~ 190)
# ============================================================
box(5, 192, 90, 6, COLOR_ACCENT, radius=2)
text(50, 195, '"인테리어 미끼상품 + 인프라 수수료 + 협력사 영업 외주화"',
     size=13, color='white', weight='bold')

# ============================================================
# 3. 핵심 가치 제안 3개 (190 ~ 175)
# ============================================================
text(50, 187, "■ 핵심 가치 제안 (3-Way Win)", size=14, color=COLOR_DARK, weight='bold')

# 3 박스
box_y = 176
boxes = [
    (5, "고객 (점주)", "인테리어 30~40% 할인\n토털 패키지 원스톱", COLOR_SUCCESS),
    (37, "협력사", "점주 접점 제공\n영업 비용 절감", COLOR_BLUE),
    (69, "콤마나인", "영업조직 없이\n인프라 수수료 누적", COLOR_PURPLE),
]
for x, title, desc, color in boxes:
    box(x, box_y, 26, 8, color, alpha=0.9, radius=2)
    text(x + 13, box_y + 6, title, size=11, color='white', weight='bold')
    text(x + 13, box_y + 2.5, desc, size=8.5, color='white')

# ============================================================
# 4. 진입 전략 (170 ~ 155)
# ============================================================
text(50, 171, "■ 진입 전략: 인테리어 = 미끼상품", size=14, color=COLOR_DARK, weight='bold')

# 비교 박스
box(5, 158, 42, 10, COLOR_LIGHT, radius=2)
text(26, 165.5, "타사 인테리어", size=10, color=COLOR_DARK, weight='bold')
text(26, 161, "1,000만원", size=18, color=COLOR_DARK, weight='bold')

box(53, 158, 42, 10, COLOR_ACCENT, radius=2)
text(74, 165.5, "Voido 인테리어", size=10, color='white', weight='bold')
text(74, 161, "600~700만원", size=18, color='white', weight='bold')

# 화살표
ax.annotate("", xy=(53, 163), xytext=(47, 163),
            arrowprops=dict(arrowstyle="->", color=COLOR_DANGER, lw=2.5))
text(50, 156, "30~40% 할인", size=9, color=COLOR_DANGER, weight='bold')

# ============================================================
# 5. 마진 구조 재설계 (155 ~ 138)
# ============================================================
text(50, 153, "■ 마진 구조 재설계", size=14, color=COLOR_DARK, weight='bold')

# 표 헤더
box(5, 144, 90, 6, COLOR_PRIMARY, radius=1)
text(20, 147, "사업 라인", size=10, color='white', weight='bold')
text(50, 147, "기존 마진", size=10, color='white', weight='bold')
text(80, 147, "신규 마진", size=10, color='white', weight='bold')

# 행 1: 팩토리나인
box(5, 138, 90, 5, '#FFFFFF', radius=1)
ax.add_patch(Rectangle((5, 138), 90, 5, facecolor='#F9FAFB', edgecolor='#E5E7EB'))
text(20, 140.5, "팩토리나인 (제조)", size=9.5, color=COLOR_DARK)
text(50, 140.5, "정상", size=9.5, color=COLOR_DARK)
text(80, 140.5, "이익 보존", size=9.5, color=COLOR_SUCCESS, weight='bold')

# 행 2: DL 라인
ax.add_patch(Rectangle((5, 133), 90, 5, facecolor='#FFFFFF', edgecolor='#E5E7EB'))
text(20, 135.5, "DL 라인 (판매)", size=9.5, color=COLOR_DARK)
text(50, 135.5, "100%", size=9.5, color=COLOR_DARK)
text(80, 135.5, "20~30%만", size=9.5, color=COLOR_ACCENT, weight='bold')

# 행 3: 인프라
ax.add_patch(Rectangle((5, 128), 90, 5, facecolor='#F9FAFB', edgecolor='#E5E7EB'))
text(20, 130.5, "인프라 수수료", size=9.5, color=COLOR_DARK)
text(50, 130.5, "0%", size=9.5, color=COLOR_DARK)
text(80, 130.5, "0.5~1% 누적", size=9.5, color=COLOR_BLUE, weight='bold')

# ============================================================
# 6. 인프라 수익원 (128 ~ 105)
# ============================================================
text(50, 125, "■ 인프라 수익원 (점주 1명당 월 추정)", size=14, color=COLOR_DARK, weight='bold')

revenues = [
    ("카드 단말기", "거래액 0.0X% × 수년", "2~5만원"),
    ("인터넷 구독", "계약수수료 + 리베이트", "1~2만원"),
    ("정수기 렌탈", "렌탈료 0.5%", "0.1~0.3만원"),
    ("테이블오더", "설치비 + 월 사용료", "1~3만원"),
    ("배민 광고/깃발", "광고비 %", "2~5만원"),
]

rev_y = 119
for i, (name, struct, amt) in enumerate(revenues):
    y = rev_y - i * 3
    bg = '#F9FAFB' if i % 2 == 0 else '#FFFFFF'
    ax.add_patch(Rectangle((5, y), 90, 3, facecolor=bg, edgecolor='#E5E7EB'))
    text(8, y + 1.5, name, size=9, color=COLOR_DARK, ha='left', weight='bold')
    text(45, y + 1.5, struct, size=8.5, color='#6B7280')
    text(88, y + 1.5, amt, size=9, color=COLOR_ACCENT, weight='bold', ha='right')

# 합계
box(5, 100.5, 90, 3.5, COLOR_PRIMARY, radius=1)
text(8, 102, "합계 (월)", size=10, color='white', ha='left', weight='bold')
text(88, 102, "월 6~16만원", size=11, color='white', ha='right', weight='bold')

text(50, 97.5, "→ 연 70~190만원 × 3~5년 = 누적 210~950만원 (인테리어 적자 회수 가능)",
     size=9.5, color=COLOR_SUCCESS, weight='bold')

# ============================================================
# 7. 영업 외주화 (95 ~ 80)
# ============================================================
text(50, 93, "■ 영업 조직 외주화 (핵심 혁신)", size=14, color=COLOR_DARK, weight='bold')

# 중앙 콤마나인
ax.add_patch(Circle((50, 86), 6, facecolor=COLOR_PRIMARY, edgecolor='none'))
text(50, 87.5, "콤마나인", size=10, color='white', weight='bold')
text(50, 85, "접점 큐레이션", size=8, color='white')

# 외곽 협력사들
partners = [
    (15, 87, "배민\n영업조직"),
    (15, 81, "정수기\n영업조직"),
    (50, 76, "지역\n영업맨"),
    (85, 87, "POS·테이블\n오더 업체"),
    (85, 81, "카드사·\n인터넷"),
]
for x, y, name in partners:
    ax.add_patch(Circle((x, y), 4.5, facecolor=COLOR_BLUE, alpha=0.85, edgecolor='none'))
    text(x, y, name, size=7, color='white', weight='bold')
    # 화살표 - 콤마나인에서 외곽으로
    ax.annotate("", xy=(x, y), xytext=(50, 86),
                arrowprops=dict(arrowstyle="<->", color='#94A3B8', lw=1, alpha=0.6))

# ============================================================
# 8. 플라이휠 (78 ~ 60)
# ============================================================
text(50, 75, "■ 플라이휠: 점주 풀 → 협상력 → 인바운드", size=14, color=COLOR_DARK, weight='bold')

# 3단계
phases = [
    (5, 65, "초기\n점주 1~30명", "수수료 0.5%", COLOR_WARNING),
    (37, 65, "중기\n점주 30~100명", "수수료 0.7%", COLOR_BLUE),
    (69, 65, "장기\n점주 100명+", "수수료 1%+\n역인바운드", COLOR_SUCCESS),
]
for x, y, title, sub, color in phases:
    box(x, y, 26, 6, color, alpha=0.9, radius=2)
    text(x + 13, y + 4, title, size=9, color='white', weight='bold')
    text(x + 13, y + 1.5, sub, size=8, color='white')

# 화살표
for x in [31, 63]:
    ax.annotate("", xy=(x + 4, 68), xytext=(x, 68),
                arrowprops=dict(arrowstyle="->", color=COLOR_DARK, lw=2))

text(50, 61, "임계점 돌파 시 협력사 협상력 비약 상승 + 대기업 직접 코드 발급",
     size=9, color=COLOR_DARK, weight='bold', va='top')

# ============================================================
# 9. 단계별 로드맵 (60 ~ 45)
# ============================================================
text(50, 58, "■ 단계별 성장 로드맵", size=14, color=COLOR_DARK, weight='bold')

# 타임라인
phases_road = [
    ("Phase 1", "0~12개월", "대구·경북", "점주 1~30명", "지역 검증", COLOR_WARNING),
    ("Phase 2", "12~24개월", "광역 확장", "점주 30~100명", "수수료 0.7%", COLOR_BLUE),
    ("Phase 3", "24개월+", "전국", "점주 100+", "프랜차이즈 전문점", COLOR_SUCCESS),
]

for i, (ph, dur, area, count, action, color) in enumerate(phases_road):
    y_top = 54 - i * 4
    box(5, y_top, 90, 3.5, color, alpha=0.9, radius=1)
    text(10, y_top + 1.7, ph, size=10, color='white', weight='bold', ha='left')
    text(25, y_top + 1.7, dur, size=8.5, color='white', ha='left')
    text(45, y_top + 1.7, area, size=8.5, color='white', ha='left')
    text(63, y_top + 1.7, count, size=8.5, color='white', ha='left')
    text(82, y_top + 1.7, action, size=8.5, color='white', weight='bold', ha='left')

# ============================================================
# 10. 차별화 3대 카드 (42 ~ 32)
# ============================================================
text(50, 41, "■ 콤마나인만의 차별화 3대 카드", size=14, color=COLOR_DARK, weight='bold')

cards = [
    (5, "1\n자체 제조\n원가 우위", "팩토리나인\n경쟁사 모방 불가", COLOR_DANGER),
    (37, "2\n영천 실물\n쇼룸", "사옥 투어\n신뢰 구축", COLOR_ACCENT),
    (69, "3\n지역(영남권)\n선점", "거점 확보\n확장 베이스", COLOR_PURPLE),
]
for x, num_title, desc, color in cards:
    box(x, 32, 26, 7, color, alpha=0.9, radius=2)
    text(x + 13, 36.5, num_title, size=10, color='white', weight='bold')
    text(x + 13, 33.5, desc, size=8, color='white')

# ============================================================
# 11. 리스크 & 대응 (32 ~ 22)
# ============================================================
text(50, 30, "■ 핵심 리스크 & 대응", size=14, color=COLOR_DARK, weight='bold')

risks = [
    ("F&B 3년 폐업률 50~60%", "생존율 높은 업종 우선 (편의점·무인매장·카페)"),
    ("가맹사업법 회색지대", "변호사 자문 + 옵션 명시 + SOP"),
    ("Death Valley (~100명)", "초기 자본 확보 + 적자 감수 2~3년"),
    ("협력사 의존", "복수 협력사 확보 + 대기업 직접 코드 전환"),
]

for i, (risk, response) in enumerate(risks):
    y = 27 - i * 1.8
    text(7, y, "⚠", size=10, color=COLOR_DANGER, ha='left', weight='bold')
    text(11, y, risk, size=9, color=COLOR_DARK, ha='left', weight='bold')
    text(50, y, "→", size=9, color='#6B7280', ha='left')
    text(54, y, response, size=8.5, color=COLOR_SUCCESS, ha='left')

# ============================================================
# 12. 의사결정 요청 (20 ~ 10)
# ============================================================
box(0, 10, 100, 10, COLOR_PRIMARY, radius=0)
text(50, 17.5, "■ 대표님께 의사결정 요청", size=13, color='white', weight='bold')

decisions = [
    "① Phase 1 (대구·경북) 파일럿 추진 승인",
    "② 가맹사업법 변호사 자문 진행 (50~100만원)",
    "③ DL 라인 마진 정책 변경 (100% → 20~30%)",
    "④ 초기 자본 계획 (Death Valley 2~3년 적자)",
]
for i, d in enumerate(decisions):
    text(50, 15 - i * 1.3, d, size=9.5, color='white', weight='bold')

# ============================================================
# 13. 푸터 (10 ~ 0)
# ============================================================
box(0, 0, 100, 8, '#111827', radius=0)
text(50, 5, "콤마나인  |  Voido 사업기획팀  |  내부 보고용",
     size=9, color='#9CA3AF')
text(50, 2, "한 줄 결론: 검증된 패턴 + 자체 제조 원가 우위 + 강제성 제거 = 작동 가능한 모델",
     size=9, color=COLOR_ACCENT, weight='bold')

plt.tight_layout(pad=0)
plt.savefig('/home/user/daily-order-report/docs/voido-infographic.png',
            dpi=160, bbox_inches='tight', facecolor='white',
            pad_inches=0.1)
print("Saved: /home/user/daily-order-report/docs/voido-infographic.png")
