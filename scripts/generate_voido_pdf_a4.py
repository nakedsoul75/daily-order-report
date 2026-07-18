"""Voido 비즈니스 모델 보고서 - A4 인쇄용 PDF (v4 / 대표님 보고용)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

# 인쇄용 고대비 컬러 팔레트
C_NAVY = "#1E3A5F"        # 진한 네이비 (메인)
C_NAVY_DARK = "#0F2547"   # 더 진한 네이비
C_ORANGE = "#EA580C"      # 진한 오렌지 (액션/강조)
C_GREEN = "#047857"       # 진한 그린 (긍정)
C_RED = "#B91C1C"         # 진한 레드 (경고)
C_BLUE = "#1D4ED8"        # 진한 블루
C_PURPLE = "#6D28D9"      # 진한 퍼플
C_AMBER = "#B45309"       # 진한 앰버
C_TEXT = "#111827"        # 본문 텍스트
C_GRAY = "#4B5563"        # 보조 텍스트
C_BORDER = "#D1D5DB"
C_BG = "#F9FAFB"          # 매우 연한 배경

# A4 portrait: 8.27 x 11.69 inch
A4_W, A4_H = 8.27, 11.69

def new_page():
    """A4 portrait 페이지 생성. xlim 0-100, ylim 0-141."""
    fig = plt.figure(figsize=(A4_W, A4_H), facecolor='white')
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 141)
    ax.axis('off')
    fig.patch.set_facecolor('white')
    return fig, ax

def box(ax, x, y, w, h, color, alpha=1.0, radius=1.5):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.3,rounding_size={radius}",
                       facecolor=color, edgecolor='none', alpha=alpha,
                       linewidth=0)
    ax.add_patch(p)

def rect(ax, x, y, w, h, fc, ec=None, lw=0.5):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc,
                           edgecolor=ec or C_BORDER, linewidth=lw))

def t(ax, x, y, s, size=14, color=C_TEXT, weight='normal',
      ha='center', va='center', style='normal'):
    ax.text(x, y, s, fontsize=size, color=color, weight=weight,
            ha=ha, va=va, style=style)

def page_header(ax, page_num, total_pages, title):
    """페이지 상단 헤더."""
    rect(ax, 0, 135, 100, 6, C_NAVY, ec='none')
    t(ax, 3, 138, "Voido 신규 비즈니스 모델",
      size=11, color='white', weight='bold', ha='left')
    t(ax, 97, 138, f"PAGE {page_num} / {total_pages}",
      size=10, color='#9CA3AF', ha='right')
    t(ax, 50, 130, title, size=24, color=C_NAVY, weight='bold')
    # 구분선
    ax.plot([10, 90], [126, 126], color=C_NAVY, lw=1.5)

def page_footer(ax, page_num):
    """페이지 하단 푸터."""
    ax.plot([10, 90], [6, 6], color=C_BORDER, lw=0.5)
    t(ax, 10, 3, "디엘나인  |  Voido 사업기획팀",
      size=9, color=C_GRAY, ha='left')
    t(ax, 90, 3, f"- {page_num} -", size=9, color=C_GRAY, ha='right')

# ============================================================
# PDF 생성 시작
# ============================================================
TOTAL_PAGES = 5
pdf_path = '/home/user/daily-order-report/docs/voido-report-A4.pdf'

with PdfPages(pdf_path) as pdf:
    # ============================================================
    # PAGE 1: COVER + EXECUTIVE SUMMARY
    # ============================================================
    fig, ax = new_page()

    # 메인 타이틀 영역
    rect(ax, 0, 110, 100, 31, C_NAVY, ec='none')
    t(ax, 50, 130, "Voido 신규 비즈니스 모델",
      size=30, color='white', weight='bold')
    t(ax, 50, 122, "대표님 보고 자료",
      size=16, color='#A7C3E0')
    t(ax, 50, 116,
      "강제성 없는 어필리에이트 + 자체 제조 원가 우위 + 협상력 플라이휠",
      size=12, color='#CBD5E1', style='italic')
    t(ax, 50, 112, "2026.05.19  |  디엘나인 사업기획팀",
      size=10, color='#94A3B8')

    # 한 줄 정의
    t(ax, 50, 103, "■ 한 줄 정의", size=18, color=C_TEXT, weight='bold')
    box(ax, 8, 90, 84, 9, C_ORANGE, radius=2)
    t(ax, 50, 95,
      '"인테리어 미끼상품 + 인프라 수수료 + 협력사 영업 외주화"',
      size=15, color='white', weight='bold')

    # 3-Way Win
    t(ax, 50, 82, "■ 핵심 가치 제안 (3-Way Win)",
      size=18, color=C_TEXT, weight='bold')

    boxes_3way = [
        (5, "고객 (점주)",
         ["인테리어 30% 할인",
          "토털 패키지 원스톱",
          "(인테리어+주방+테이블)"], C_GREEN),
        (35, "협력사",
         ["최선단 점주 접점",
          "영업 성공율 상승",
          "영업 비용 절감"], C_BLUE),
        (65, "디엘나인",
         ["영업 약점 회피",
          "인프라 수수료 누적",
          "지속 마진 확보"], C_PURPLE),
    ]
    for x, title, descs, color in boxes_3way:
        box(ax, x, 56, 30, 22, color, alpha=0.95, radius=2)
        t(ax, x + 15, 73, title, size=15, color='white', weight='bold')
        for i, d in enumerate(descs):
            t(ax, x + 15, 67 - i * 3, d, size=11, color='white')

    # 핵심 의사결정 사항
    t(ax, 50, 48, "■ 핵심 의사결정 사항", size=18, color=C_TEXT, weight='bold')

    decisions = [
        "1.  Phase 1 (대구·경북) 파일럿 추진 여부",
        "2.  변호사 자문(가맹사업법) 진행 승인",
        "3.  DL Nine 팩토리 공급 제품 마진 변경 (100% → 70%) 승인",
        "4.  전체 마진 구조 분석 시트 작성",
        "      · 4.1  팩토리 공급 부분: 30% 마진 (주방·집기·간판 포함)",
        "      · 4.2  시공 마진: 유지",
        "      · 4.3  자재 부분: 마진 유지",
    ]
    for i, d in enumerate(decisions):
        size = 13 if not d.startswith("      ") else 11
        color = C_TEXT if not d.startswith("      ") else C_GRAY
        weight = 'bold' if not d.startswith("      ") else 'normal'
        t(ax, 10, 41 - i * 3.8, d, size=size, color=color,
          weight=weight, ha='left')

    page_footer(ax, 1)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 2: 진입 전략 + 마진 구조 재설계
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 2, TOTAL_PAGES, "진입 전략 + 마진 구조 재설계")

    # 진입 전략 (Trojan Horse)
    t(ax, 50, 118, "▶ 진입 전략 : 인테리어 = 미끼상품 (Trojan Horse)",
      size=17, color=C_NAVY, weight='bold')

    # 가격 비교
    rect(ax, 7, 95, 40, 18, C_BG)
    t(ax, 27, 109, "타사 인테리어", size=14, color=C_TEXT, weight='bold')
    t(ax, 27, 101, "1,000만원", size=32, color=C_TEXT, weight='bold')

    box(ax, 53, 95, 40, 18, C_ORANGE, radius=2)
    t(ax, 73, 109, "Voido 인테리어", size=14, color='white', weight='bold')
    t(ax, 73, 101, "700만원", size=32, color='white', weight='bold')

    # 화살표
    ax.annotate("", xy=(53, 104), xytext=(47, 104),
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=3))
    t(ax, 50, 91, "30% 할인", size=14, color=C_RED, weight='bold')
    t(ax, 50, 87, '"최소 공장 마진까지 빼고 판다 + 풀 패키지라 가능한 구조"',
      size=11, color=C_GRAY, style='italic')

    # 마진 구조 재설계
    t(ax, 50, 78, "▶ 마진 구조 재설계", size=17, color=C_NAVY, weight='bold')

    # 표 헤더
    rect(ax, 7, 67, 86, 7, C_NAVY, ec='none')
    t(ax, 27, 70.5, "사업 라인", size=13, color='white', weight='bold')
    t(ax, 55, 70.5, "기존 마진", size=13, color='white', weight='bold')
    t(ax, 80, 70.5, "신규 마진", size=13, color='white', weight='bold')

    # 표 행
    margin_rows = [
        ("팩토리나인 (자체 제조)", "정상", "이익 보존", C_GREEN),
        ("DL Nine (판매)", "100%", "30%만", C_ORANGE),
        ("인프라 수수료", "0%", "0.5~1% 누적", C_BLUE),
        ("인프라 초기 계약 수수료", "0%", "300만원/건", C_BLUE),
    ]
    for i, (col1, col2, col3, c3color) in enumerate(margin_rows):
        y = 60 - i * 7
        bg = C_BG if i % 2 == 0 else 'white'
        rect(ax, 7, y, 86, 7, bg)
        t(ax, 27, y + 3.5, col1, size=12, color=C_TEXT, weight='bold')
        t(ax, 55, y + 3.5, col2, size=12, color=C_TEXT)
        t(ax, 80, y + 3.5, col3, size=13, color=c3color, weight='bold')

    # 핵심 논리
    box(ax, 7, 18, 86, 10, C_BG, radius=2)
    t(ax, 50, 25, "▶ 핵심 논리", size=13, color=C_NAVY, weight='bold')
    t(ax, 50, 21,
      "인테리어 시장의 거품(40~50% 마진)을 회수해 점주 혜택 + 파이 확대로 전환",
      size=11, color=C_TEXT)

    page_footer(ax, 2)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 3: 인프라 수익원
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 3, TOTAL_PAGES, "인프라 수익원 (점주 1명당)")

    t(ax, 50, 118,
      "* 실 현업 영업 담당자와 숫자 확인 필요",
      size=11, color=C_GRAY, style='italic')

    # 표 헤더
    rect(ax, 7, 108, 86, 7, C_NAVY, ec='none')
    t(ax, 22, 111.5, "항목", size=13, color='white', weight='bold')
    t(ax, 55, 111.5, "수익 구조", size=13, color='white', weight='bold')
    t(ax, 82, 111.5, "월 예상 수익", size=13, color='white', weight='bold')

    # 행
    rev_rows = [
        ("카드 단말기", "거래액 0.0X% × 수년", "2~5만원"),
        ("인터넷 구독", "계약 수수료 + 리베이트", "1~2만원"),
        ("정수기 렌탈", "렌탈료 0.5%", "0.1~0.3만원"),
        ("테이블오더", "설치비 + 월 사용료", "3~10만원"),
        ("배민 광고/깃발", "광고비 0.5%", "2~5만원"),
    ]
    for i, (name, struct, amt) in enumerate(rev_rows):
        y = 101 - i * 8
        bg = C_BG if i % 2 == 0 else 'white'
        rect(ax, 7, y, 86, 8, bg)
        t(ax, 22, y + 4, name, size=12, color=C_TEXT, weight='bold')
        t(ax, 55, y + 4, struct, size=11, color=C_GRAY)
        t(ax, 82, y + 4, "월 " + amt, size=13, color=C_ORANGE, weight='bold')

    # 합계
    box(ax, 7, 53, 86, 8, C_NAVY, radius=2)
    t(ax, 22, 57, "월 합계", size=14, color='white', weight='bold')
    t(ax, 82, 57, "월 6~16만원", size=16, color='white', weight='bold')

    # 일회성
    box(ax, 7, 43, 86, 8, C_PURPLE, radius=2)
    t(ax, 22, 47, "일회성 수수료", size=14, color='white', weight='bold')
    t(ax, 82, 47, "300~500만원", size=16, color='white', weight='bold')

    # 누적 회수 시뮬레이션
    t(ax, 50, 35, "▶ 누적 회수 시뮬레이션",
      size=17, color=C_NAVY, weight='bold')
    box(ax, 7, 18, 86, 13, C_GREEN, alpha=0.95, radius=2)
    t(ax, 50, 27, "연 환산 70~190만원 + 일회성 300~500만원",
      size=14, color='white', weight='bold')
    t(ax, 50, 22.5, "→ 인테리어 적자 회수 가능 (상위 매출 점포 집중 시)",
      size=12, color='white')

    page_footer(ax, 3)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 4: 영업 외주화 + 플라이휠
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 4, TOTAL_PAGES, "영업 조직 외주화 + 플라이휠")

    # 영업 외주화
    t(ax, 50, 118, "▶ 영업 조직 외주화 (핵심 혁신)",
      size=17, color=C_NAVY, weight='bold')
    t(ax, 50, 114,
      "디엘나인은 접점 큐레이션만 담당, 영업은 외부 파트너가 수행",
      size=11, color=C_GRAY, style='italic')

    # 상단 2개 박스
    box(ax, 7, 99, 40, 11, C_BLUE, alpha=0.95, radius=2)
    t(ax, 27, 106, "협력사 영업조직 (자발 합류)",
      size=13, color='white', weight='bold')
    t(ax, 27, 103, "배민 · 정수기 · POS·테이블오더",
      size=9.5, color='white')
    t(ax, 27, 100.5, "카드사 · 인터넷",
      size=9.5, color='white')

    box(ax, 53, 99, 40, 11, C_PURPLE, alpha=0.95, radius=2)
    t(ax, 73, 106, "지역 영업맨 네트워크",
      size=13, color='white', weight='bold')
    t(ax, 73, 103, "광역시별 1~2명",
      size=9.5, color='white')
    t(ax, 73, 100.5, "수수료 룰 분배",
      size=9.5, color='white')

    # 수렴 화살표
    ax.annotate("", xy=(45, 92), xytext=(27, 99),
                arrowprops=dict(arrowstyle="->", color=C_TEXT, lw=2))
    ax.annotate("", xy=(55, 92), xytext=(73, 99),
                arrowprops=dict(arrowstyle="->", color=C_TEXT, lw=2))

    # 디엘나인 hub
    box(ax, 20, 82, 60, 10, C_NAVY, radius=2)
    t(ax, 50, 88, "디엘나인", size=18, color='white', weight='bold')
    t(ax, 50, 84, "접점 큐레이션 + 패키지 매칭",
      size=12, color='#A7C3E0')

    # 다운 화살표
    ax.annotate("", xy=(50, 76), xytext=(50, 82),
                arrowprops=dict(arrowstyle="->", color=C_TEXT, lw=3))

    # 점주 박스
    box(ax, 20, 67, 60, 8, C_ORANGE, radius=2)
    t(ax, 50, 71, "신규 점주 확보 + 토털 패키지 제공",
      size=14, color='white', weight='bold')

    # 플라이휠
    t(ax, 50, 58, "▶ 플라이휠 : 점주 풀 → 협상력 → 인바운드",
      size=17, color=C_NAVY, weight='bold')

    phases = [
        (7, "초기", "점주 1~30명", "수수료 0.5%", C_AMBER),
        (37, "중기", "점주 30~100명", "수수료 0.7%", C_BLUE),
        (67, "장기", "점주 100명+", "수수료 1%+\n역인바운드", C_GREEN),
    ]
    for x, label, count, sub, color in phases:
        box(ax, x, 28, 26, 22, color, alpha=0.95, radius=2)
        t(ax, x + 13, 45, label, size=16, color='white', weight='bold')
        t(ax, x + 13, 40, count, size=11, color='white')
        t(ax, x + 13, 33, sub, size=11, color='white', weight='bold')

    for x in [33, 63]:
        ax.annotate("", xy=(x + 4, 39), xytext=(x, 39),
                    arrowprops=dict(arrowstyle="->", color=C_TEXT, lw=2.5))

    box(ax, 7, 14, 86, 8, C_BG, radius=2)
    t(ax, 50, 18.5,
      "임계점 돌파 시 협력사 협상력 비약 상승 + 대기업 직접 코드 발급",
      size=12, color=C_NAVY, weight='bold')

    page_footer(ax, 4)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 5: 신뢰 구축 + 차별화 + 결론
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 5, TOTAL_PAGES, "신뢰 구축 + 차별화 + 결론")

    # 신뢰 구축 메커니즘
    t(ax, 50, 118, "▶ 신뢰 구축 메커니즘",
      size=17, color=C_NAVY, weight='bold')

    trust = [
        (7, "영천 공장+사옥",
         ["라인 투어 + 쇼룸", "실체 있는 회사 증명"], C_RED),
        (37, "강제성 제거",
         ["옵션 선택 보장", "가맹사업법 회피"], C_ORANGE),
        (67, "시장가 동일",
         ["추가 마진 없음", "수수료는 협력사 부담"], C_PURPLE),
    ]
    for x, title, descs, color in trust:
        box(ax, x, 96, 26, 18, color, alpha=0.95, radius=2)
        t(ax, x + 13, 109, title, size=13, color='white', weight='bold')
        for i, d in enumerate(descs):
            t(ax, x + 13, 104 - i * 3.5, d, size=10, color='white')

    # 차별화 3대 카드
    t(ax, 50, 88, "▶ 디엘나인만의 차별화 3대 카드",
      size=17, color=C_NAVY, weight='bold')

    cards = [
        (7, "1", "자체 제조 원가 우위",
         ["팩토리나인", "경쟁사 모방 불가"], C_RED),
        (37, "2", "공장+쇼룸 라인 투어",
         ["신뢰성 상승", "의심 차단"], C_ORANGE),
        (67, "3", "지역(영남권) 선점",
         ["거점 확보", "확장 베이스"], C_PURPLE),
    ]
    for x, num, title, descs, color in cards:
        box(ax, x, 66, 26, 18, color, alpha=0.95, radius=2)
        ax.add_patch(Circle((x + 13, 80), 2.3, facecolor='white'))
        t(ax, x + 13, 80, num, size=15, color=color, weight='bold')
        t(ax, x + 13, 74.5, title, size=11.5, color='white', weight='bold')
        for i, d in enumerate(descs):
            t(ax, x + 13, 70.5 - i * 2.5, d, size=10, color='white')

    # 시장 벤치마크
    t(ax, 50, 58, "▶ 시장 벤치마크 (한국 유사 모델)",
      size=17, color=C_NAVY, weight='bold')

    rect(ax, 7, 49, 86, 6, C_BG)
    t(ax, 22, 52, "이디야·메가커피", size=12, color=C_TEXT,
      weight='bold', ha='left')
    t(ax, 70, 52, "동일 구조 / 단 강제성 있음 (가맹)",
      size=11, color=C_GRAY, ha='left')

    rect(ax, 7, 42, 86, 6, 'white')
    t(ax, 22, 45, "더본코리아", size=12, color=C_TEXT,
      weight='bold', ha='left')
    t(ax, 70, 45, "동일 구조 / 가맹본부 형태",
      size=11, color=C_GRAY, ha='left')

    # 결론
    box(ax, 7, 14, 86, 22, C_NAVY, radius=2)
    t(ax, 50, 31, "■ 한 줄 결론", size=13, color='#A7C3E0', weight='bold',
      style='italic')
    t(ax, 50, 26, "검증된 패턴 + 자체 제조 원가 우위 + 강제성 제거",
      size=15, color='white', weight='bold')
    t(ax, 50, 22, "= 작동 가능한 모델",
      size=15, color='white', weight='bold')
    t(ax, 50, 17,
      "한국 시장 맞춤형 변형으로 틈새 공략 가능",
      size=11, color='#CBD5E1')

    page_footer(ax, 5)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

print(f"Saved: {pdf_path}")
