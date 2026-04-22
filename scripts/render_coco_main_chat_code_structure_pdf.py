from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs"
PDF_PATH = OUT_DIR / "coco_main_chat_code_structure.pdf"


SECTIONS: list[tuple[str, list[str]]] = [
    (
        "1. 목적",
        [
            "이 문서는 코코앱 메인챗을 실제 코드 단위로 어떻게 분리할지 정의하기 위한 구조 설계 문서다.",
            "목표는 app.py에 몰려 있는 메인챗 관련 책임을 줄이고, 상태 관리와 메인챗 응답, 화면 렌더를 분리하기 쉬운 구조를 만드는 것이다.",
        ],
    ),
    (
        "2. 분리 원칙",
        [
            "처음부터 너무 많은 파일로 쪼개기보다, 현재 복잡도가 가장 높은 부분부터 먼저 분리한다.",
            "첫 단계에서 우선 고정할 축은 contracts, state, main_engine, ui 네 개다.",
            "그리고 메인챗 응답이 조금 더 살아나기 시작하는 시점에는 router, composer, handoff, grounding, followup을 바로 붙인다.",
        ],
    ),
    (
        "3. 권장 패키지 구조",
        [
            "app/chat/__init__.py",
            "app/chat/contracts.py",
            "app/chat/state.py",
            "app/chat/router.py",
            "app/chat/main_engine.py",
            "app/chat/composer.py",
            "app/chat/handoff.py",
            "app/chat/grounding.py",
            "app/chat/followup.py",
            "app/chat/ui.py",
        ],
    ),
    (
        "4. 파일별 책임",
        [
            "contracts.py: 메시지 타입, 문서 요약 타입, 앱 상태 타입 정의.",
            "state.py: 기본 상태 생성, 상태 마이그레이션, 상태 로드/저장, 문서 로드/저장/삭제, 최근 타겟 복원, 메시지 append, 문서 승격.",
            "router.py: 스몰톡, 앱 사용 질문, 수학 질문, 일반 질문으로 입력 의도를 분류.",
            "main_engine.py: 메인챗 응답 오케스트레이션 진입점으로 router, composer, handoff를 연결.",
            "composer.py: 스몰톡, 앱 안내, 일반 질문, 불확실성 표현을 자연스럽게 조립.",
            "handoff.py: 수학 질문을 학습리스트 흐름으로 넘기는 문장을 관리.",
            "grounding.py: 현재 활성 채팅 모드, 저장된 학습리스트 개수, 최근 선택된 학습리스트 이름처럼 메인챗이 내부적으로 참고할 로컬 근거를 만든다.",
            "followup.py: 직전 assistant 질문과 현재 짧은 사용자 답을 연결해, 꼬리질문과 역질문 뒤 흐름을 자연스럽게 이어간다.",
            "ui.py: 프롬프트 제출 큐잉, 대화 HTML 렌더, 최근 메시지 스크롤, 빈 상태 렌더 기준.",
        ],
    ),
    (
        "5. app.py에 남길 책임",
        [
            "Streamlit 페이지 설정",
            "업로드 이벤트 처리",
            "사이드바 화면 구성",
            "체크패널 렌더링",
            "수학 풀이 파이프라인 호출",
            "전체 화면 CSS 주입",
        ],
    ),
    (
        "6. 호출 흐름",
        [
            "app.py가 상태를 불러온다.",
            "상태 관련 처리는 app.chat.state가 담당한다.",
            "메인챗 입력이 들어오면 app.chat.main_engine이 진입점이 된다.",
            "main_engine은 router로 의도를 나눈다.",
            "main_engine은 필요할 때 grounding으로 앱 상태와 학습리스트 상태를 읽는다.",
            "직전 assistant 질문과 현재 짧은 답이 연결될 때는 followup이 먼저 흐름을 이어받는다.",
            "일반 응답은 composer, 수학 전환 문장은 handoff가 만든다.",
            "대화 렌더링과 스크롤 보정은 app.chat.ui가 담당한다.",
            "app.py는 최종 결과를 화면에 조립한다.",
        ],
    ),
    (
        "7. 다음 확장 구조",
        [
            "다음 단계에서는 grounding을 지금의 로컬 근거 수준에서 더 확장한다.",
            "내부 검색 후보 정리, 검증 규칙 추가, 이후 외부 검색 연계 전 준비와 followup·grounding 문맥 확장을 담당한다.",
        ],
    ),
    (
        "8. 구현 순서",
        [
            "1단계: contracts.py, state.py, main_engine.py, ui.py 추가.",
            "2단계: app.py에서 해당 함수들을 새 모듈로 이동하고 import 연결 정리.",
            "3단계: router.py, composer.py, handoff.py를 추가하고 메인챗 응답을 라우팅 구조로 연결.",
            "4단계: grounding.py를 로컬 근거 레이어에서 검색·검증 레이어로 확장하고, followup.py로 꼬리질문과 짧은 응답의 문맥 연결을 강화.",
        ],
    ),
    (
        "9. 핵심 원칙",
        [
            "현재 단계의 핵심은 기능을 많이 넣는 것이 아니라 기능이 들어갈 자리를 먼저 만드는 것이다.",
            "상태는 state.py, 메인챗 오케스트레이션은 main_engine.py, 메인챗 말투는 composer.py, 수학 전환 문장은 handoff.py, 로컬 근거는 grounding.py, 꼬리질문 연결은 followup.py, 화면 보조는 ui.py, 자료 구조는 contracts.py, 입력 분류는 router.py로 고정한다.",
        ],
    ),
]


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="코코 메인챗 코드 구조 설계",
        author="Codex",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "KTitle",
        parent=styles["Title"],
        fontName="HYGothic-Medium",
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#172033"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "KSubtitle",
        parent=styles["Normal"],
        fontName="HYSMyeongJo-Medium",
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor("#5b6475"),
        alignment=TA_LEFT,
        spaceAfter=16,
        wordWrap="CJK",
    )
    heading_style = ParagraphStyle(
        "KHeading",
        parent=styles["Heading2"],
        fontName="HYGothic-Medium",
        fontSize=14,
        leading=19,
        textColor=colors.HexColor("#172033"),
        spaceBefore=6,
        spaceAfter=6,
        wordWrap="CJK",
    )
    body_style = ParagraphStyle(
        "KBody",
        parent=styles["BodyText"],
        fontName="HYSMyeongJo-Medium",
        fontSize=10.5,
        leading=17,
        textColor=colors.HexColor("#243041"),
        spaceAfter=6,
        wordWrap="CJK",
    )
    bullet_style = ParagraphStyle(
        "KBullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-10,
        bulletIndent=0,
        spaceAfter=5,
    )

    story = [
        Paragraph("코코 메인챗 코드 구조 설계", title_style),
        Paragraph(
            "메인챗 1차 리팩터링에서 어떤 파일 단위로 책임을 나누고, app.py를 어떤 방향으로 단순화할지 정리한 내부 설계 문서",
            subtitle_style,
        ),
    ]

    for heading, bullets in SECTIONS:
        story.append(Paragraph(heading, heading_style))
        for bullet in bullets:
            story.append(Paragraph(bullet, bullet_style, bulletText="•"))
        story.append(Spacer(1, 5))

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
