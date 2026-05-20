"""Voido 배민 영업자 협업 제안 - A4 인쇄용 PDF (v5)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

# 인쇄용 고대비 컬러 (배민 친화 틸 톤)
C_TEAL_DARK = "#0F766E"       # 진한 틸 (메인)
C_TEAL = "#0D9488"            # 미디엄 틸
C_ORANGE = "#EA580C"          # 진한 오렌지
C_GREEN = "#047857"           # 진한 그린
C_RED = "#B91C1C"             # 진한 레드
C_BLUE = "#1D4ED8"            # 진한 블루
C_PURPLE = "#6D28D9"          # 진한 퍼플
C_AMBER = "#B45309"
C_TEXT = "#111827"
C_GRAY = "#4B5563"
C_BORDER = "#D1D5DB"
C_BG = "#F0FDFA"              # 연 틸 배경
C_BG_GRAY = "#F9FAFB"

A4_W, A4_H = 8.27, 11.69

def new_page():
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
    rect(ax, 0, 135, 100, 6, C_TEAL_DARK, ec='none')
    t(ax, 3, 138, "배민 광고 영업 협업 제안",
      size=11, color='white', weight='bold', ha='left')
    t(ax, 97, 138, f"PAGE {page_num} / {total_pages}",
      size=10, color='#A7F3D0', ha='right')
    t(ax, 50, 130, title, size=22, color=C_TEAL_DARK, weight='bold')
    ax.plot([10, 90], [126, 126], color=C_TEAL_DARK, lw=1.5)

def page_footer(ax, page_num):
    ax.plot([10, 90], [6, 6], color=C_BORDER, lw=0.5)
    t(ax, 10, 3, "콤마나인 × 배달의민족  |  내부 영업 교육용",
      size=9, color=C_GRAY, ha='left')
    t(ax, 90, 3, f"- {page_num} -", size=9, color=C_GRAY, ha='right')

TOTAL_PAGES = 5
pdf_path = '/home/user/daily-order-report/docs/voido-baemin-A4.pdf'

with PdfPages(pdf_path) as pdf:
    # ============================================================
    # PAGE 1: COVER + HOOK + PAIN POINTS
    # ============================================================
    fig, ax = new_page()

    # 메인 타이틀
    rect(ax, 0, 110, 100, 31, C_TEAL_DARK, ec='none')
    t(ax, 50, 130, "배민 광고 영업 협업 제안",
      size=28, color='white', weight='bold')
    t(ax, 50, 122, "콤마나인 × 배달의민족 광고 영업",
      size=15, color='#A7F3D0')
    t(ax, 50, 117, "Win-Win 파트너십",
      size=13, color='#6EE7B7', style='italic')
    t(ax, 50, 112,
      "2026.05.19  |  내부 영업 교육·설득용 자료",
      size=10, color='#A7F3D0')

    # 후크 라인
    box(ax, 5, 96, 90, 11, C_ORANGE, radius=2)
    t(ax, 50, 103, "신규 점주, 가장 먼저 만나는",
      size=18, color='white', weight='bold')
    t(ax, 50, 98, "영업자가 이깁니다",
      size=18, color='white', weight='bold')

    # 페인포인트
    t(ax, 50, 88, "■ 지금 영업, 이런 점이 힘들지 않나요?",
      size=17, color=C_TEXT, weight='bold')

    pains = [
        (5, "발굴 비용 ↑",
         ["콜드콜·전단·발품으로", "매일 새 점주 찾기"]),
        (35, "늦은 진입",
         ["오픈 후 접근 시", "이미 다른 광고 계약됨"]),
        (65, "낮은 클로징",
         ["신뢰 형성에 시간 소요", "거절·반려 빈번"]),
    ]
    for x, title, descs in pains:
        box(ax, x, 60, 30, 22, C_RED, alpha=0.92, radius=2)
        t(ax, x + 15, 76, title, size=15, color='white', weight='bold')
        for i, d in enumerate(descs):
            t(ax, x + 15, 70 - i * 3.5, d, size=11, color='white')

    # 핵심 메시지
    box(ax, 5, 30, 90, 22, C_BG, radius=2)
    t(ax, 50, 46, "■ 이 자료의 목적", size=14,
      color=C_TEAL_DARK, weight='bold')
    t(ax, 50, 41,
      "콤마나인과의 협업이 위 3가지 문제를 어떻게 해결하는지",
      size=12, color=C_TEXT)
    t(ax, 50, 37,
      "그리고 당신과 팀에게 어떤 구체적 이득이 있는지를",
      size=12, color=C_TEXT)
    t(ax, 50, 33,
      "5분 안에 명확히 설명드립니다.",
      size=12, color=C_TEXT, weight='bold')

    page_footer(ax, 1)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 2: LIFECYCLE TIMELINE + 5-STEP PROCESS
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 2, TOTAL_PAGES, "콤마나인은 점주를 가장 먼저 만납니다")

    # 타임라인 다이어그램
    t(ax, 50, 118, "▶ 점주 라이프사이클 — 누가 언제 만나는가?",
      size=15, color=C_TEAL_DARK, weight='bold')

    # 타임라인 바
    rect(ax, 8, 102, 84, 2, '#CBD5E1', ec='none')

    # 4단계 마커
    stages = [
        (15, "인테리어\n시작"),
        (38, "인테리어\n완공"),
        (62, "오픈"),
        (85, "영업\n안정화"),
    ]
    for x, label in stages:
        ax.add_patch(Circle((x, 103), 1.8, facecolor=C_TEXT))
        t(ax, x, 96, label, size=11, color=C_TEXT, weight='bold')

    # 콤마나인 진입
    box(ax, 8, 108, 28, 6, C_TEAL, alpha=0.95, radius=2)
    t(ax, 22, 111, "콤마나인 진입", size=12, color='white', weight='bold')
    ax.annotate("", xy=(15, 105), xytext=(22, 108),
                arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=2.5))

    # 기존 배민 영업
    box(ax, 64, 108, 28, 6, C_RED, alpha=0.92, radius=2)
    t(ax, 78, 111, "기존 방식 (늦음)",
      size=12, color='white', weight='bold')
    ax.annotate("", xy=(85, 105), xytext=(78, 108),
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=2.5))

    # 핵심 메시지 박스
    box(ax, 7, 78, 86, 13, C_BG, radius=2)
    t(ax, 50, 87,
      "콤마나인과 협업하면 = 점주가 가게를 만드는 단계에서 연결",
      size=13, color=C_TEAL_DARK, weight='bold')
    t(ax, 50, 82,
      "오픈 후 접근 (X)  →  인테리어 단계 사전 접점 (○)",
      size=11, color=C_GRAY)

    # 5단계 프로세스
    t(ax, 50, 71, "▶ 협업 프로세스 — 단 5단계",
      size=15, color=C_TEAL_DARK, weight='bold')

    steps = [
        ("1", "콤마나인이\n점주와\n인테리어 계약", C_TEAL),
        ("2", "토털 패키지에\n'배민 깃발'\n옵션 포함", C_TEAL_DARK),
        ("3", "점주 관심 표시\n→ 당신에게\n리드 전달", C_ORANGE),
        ("4", "당신이 점주\n방문하여\n클로징", C_GREEN),
        ("5", "광고비 0.5%\n콤마나인 수수료\n당신 커미션 그대로", C_AMBER),
    ]

    step_w = 16.5
    step_gap = 1.4
    start_x = 7

    for i, (num, desc, color) in enumerate(steps):
        x = start_x + i * (step_w + step_gap)
        box(ax, x, 38, step_w, 28, color, alpha=0.95, radius=2)
        ax.add_patch(Circle((x + step_w/2, 60), 2.8, facecolor='white'))
        t(ax, x + step_w/2, 60, num, size=15, color=color, weight='bold')
        t(ax, x + step_w/2, 51, "STEP", size=8.5, color='white', weight='bold')
        t(ax, x + step_w/2, 45, desc, size=9, color='white', weight='bold')
        # 화살표
        if i < 4:
            ax.annotate("", xy=(x + step_w + step_gap - 0.3, 52),
                        xytext=(x + step_w + 0.2, 52),
                        arrowprops=dict(arrowstyle="->",
                                        color=C_TEXT, lw=1.5))

    # 흐름 설명
    box(ax, 7, 18, 86, 14, C_TEAL_DARK, radius=2)
    t(ax, 50, 27,
      "당신은 '이미 관심 표시한 점주'만 방문",
      size=15, color='white', weight='bold')
    t(ax, 50, 22, "콜드콜·발품 = 0", size=14,
      color='#A7F3D0', weight='bold')

    page_footer(ax, 2)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 3: 영업자가 얻는 것 + 수수료 구조
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 3, TOTAL_PAGES, "당신이 얻는 것")

    t(ax, 50, 118, "▶ 영업자가 얻는 4가지 구체적 이득",
      size=15, color=C_TEAL_DARK, weight='bold')

    benefits = [
        ("콜드콜 0건",
         "점주가 이미 관심 표시한",
         "상태에서 시작"),
        ("클로징 성공률 ↑",
         "인테리어 단계에서",
         "신뢰 사전 형성됨"),
        ("영업 시간 절감",
         "발굴 시간 줄어",
         "월 처리 건수 2배"),
        ("커미션 100% 유지",
         "콤마나인 수수료는 별도",
         "당신 수입 그대로"),
    ]
    for i, (title, d1, d2) in enumerate(benefits):
        row = i // 2
        col = i % 2
        x = 7 + col * 44
        y = 85 - row * 28
        box(ax, x, y, 42, 25, C_GREEN, alpha=0.95, radius=2)
        t(ax, x + 21, y + 18, title, size=15, color='white', weight='bold')
        t(ax, x + 21, y + 11, d1, size=11, color='white')
        t(ax, x + 21, y + 7, d2, size=11, color='white')

    # 수수료 구조
    t(ax, 50, 51, "▶ 수수료 구조 — 100% 투명",
      size=15, color=C_TEAL_DARK, weight='bold')

    fee_boxes = [
        (7, "콤마나인이\n받는 것", "광고비의\n0.5%",
         "별도 — 광고사 지급", C_TEAL_DARK),
        (37, "당신이\n받는 것", "기존 커미션\n100%",
         "그대로 — 변동 없음", C_GREEN),
        (67, "점주가\n부담하는 것", "시장가\n동일",
         "추가 비용 0원", C_ORANGE),
    ]
    for x, title, big, sub, color in fee_boxes:
        box(ax, x, 14, 26, 33, color, alpha=0.95, radius=2)
        t(ax, x + 13, 42, title, size=13, color='white', weight='bold')
        t(ax, x + 13, 32, big, size=16, color='white', weight='bold')
        t(ax, x + 13, 22, sub, size=10, color='white')

    page_footer(ax, 3)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 4: 왜 리스크 없나 + 시작하는 법
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 4, TOTAL_PAGES, "리스크 없음 + 시작 방법")

    t(ax, 50, 122, "▶ 왜 리스크가 없나",
      size=15, color=C_TEAL_DARK, weight='bold')

    risks = [
        ("접점만 제공",
         "콤마나인은 영업·클로징·CS에 개입하지 않음"),
        ("점주 DB 당신이 보유",
         "리드 전달 후 점주 관계는 당신의 자산"),
        ("다른 광고사로 빼가지 않음",
         "계약서에 명시 — 한 점주당 한 영업자만 연결"),
        ("강제성 없음",
         "점주가 거절해도 인테리어 가격 동일 → 신뢰 유지"),
    ]
    for i, (title, desc) in enumerate(risks):
        y = 107 - i * 9.5
        rect(ax, 7, y, 86, 8.5, C_BG if i % 2 == 0 else 'white', ec=C_TEAL)
        ax.add_patch(Circle((12, y + 4.3), 2.3, facecolor=C_GREEN))
        t(ax, 12, y + 4.3, "V", size=12, color='white', weight='bold')
        t(ax, 18, y + 5.7, title, size=12.5, color=C_TEXT,
          weight='bold', ha='left')
        t(ax, 18, y + 2.5, desc, size=10.5, color=C_GRAY, ha='left')

    # 시작 방법
    t(ax, 50, 60, "▶ 지금 시작하려면 — 단 3단계",
      size=15, color=C_TEAL_DARK, weight='bold')

    start_steps = [
        ("1", "콤마나인 영천 사옥 방문",
         ["공장 + 쇼룸 라인 투어", "실체 있는 회사 확인"]),
        ("2", "협력 계약 체결",
         ["수수료 룰 합의", "점주 보호 조항 포함"]),
        ("3", "첫 리드 수신 시작",
         ["보통 1주일 내", "월 평균 5~15건 예상"]),
    ]
    for i, (num, title, descs) in enumerate(start_steps):
        x = 7 + i * 30
        box(ax, x, 25, 26, 30, C_TEAL, alpha=0.95, radius=2)
        ax.add_patch(Circle((x + 13, 48), 3.5, facecolor='white'))
        t(ax, x + 13, 48, num, size=20, color=C_TEAL, weight='bold')
        t(ax, x + 13, 39, title, size=12, color='white', weight='bold')
        for j, d in enumerate(descs):
            t(ax, x + 13, 32 - j * 3, d, size=10, color='white')
        # 화살표
        if i < 2:
            ax.annotate("", xy=(x + 30, 40), xytext=(x + 26, 40),
                        arrowprops=dict(arrowstyle="->",
                                        color=C_TEXT, lw=2.5))

    # 마무리
    box(ax, 7, 11, 86, 10, C_ORANGE, radius=2)
    t(ax, 50, 16,
      "■ 영천 사옥 투어는 평일·주말 상시 가능",
      size=12, color='white', weight='bold')

    page_footer(ax, 4)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    # ============================================================
    # PAGE 5: 결론 / 요약
    # ============================================================
    fig, ax = new_page()
    page_header(ax, 5, TOTAL_PAGES, "한 줄 결론 + 요약")

    # 큰 결론 박스
    box(ax, 7, 80, 86, 40, C_TEAL_DARK, radius=3)
    t(ax, 50, 110, "■ 한 줄 결론",
      size=13, color='#A7F3D0', weight='bold', style='italic')
    t(ax, 50, 102, "당신이 영업할 새 점주가",
      size=20, color='white', weight='bold')
    t(ax, 50, 95, "매주 자동으로 들어옵니다",
      size=20, color='white', weight='bold')
    t(ax, 50, 87,
      "콜드콜 시대는 끝났습니다.",
      size=13, color='#A7F3D0')
    t(ax, 50, 83.5,
      "시발점에서 만나는 영업이 이깁니다.",
      size=13, color='#A7F3D0')

    # 핵심 요약 박스
    t(ax, 50, 72, "▶ 핵심 요약 (한 페이지로 다시)",
      size=15, color=C_TEAL_DARK, weight='bold')

    summary_items = [
        ("문제", "콜드콜·발품·늦은 진입·낮은 클로징"),
        ("해결책", "콤마나인이 인테리어 단계에서 점주를 만남"),
        ("프로세스", "5단계 협업 (계약 → 옵션 → 리드 → 방문 → 클로징)"),
        ("당신 이득", "콜드콜 0 / 클로징↑ / 시간↓ / 커미션 100% 유지"),
        ("수수료", "콤마나인 0.5% (별도) / 당신 100% / 점주 시장가"),
        ("리스크", "0 — 접점만 제공, 영업·CS는 당신, 강제성 없음"),
        ("시작", "사옥 방문 → 계약 → 1주일 내 첫 리드"),
    ]
    for i, (key, val) in enumerate(summary_items):
        y = 64 - i * 6.5
        rect(ax, 7, y, 86, 5.5, C_BG if i % 2 == 0 else 'white', ec=C_TEAL)
        t(ax, 12, y + 2.7, key, size=12, color=C_TEAL_DARK,
          weight='bold', ha='left')
        t(ax, 30, y + 2.7, val, size=11, color=C_TEXT, ha='left')

    # 문의처
    box(ax, 7, 11, 86, 6, '#0F172A', radius=2)
    t(ax, 50, 14, "문의 : 콤마나인 사업기획팀  |  영천 사옥 투어 상시 가능",
      size=11, color=C_ORANGE, weight='bold')

    page_footer(ax, 5)
    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

print(f"Saved: {pdf_path}")
