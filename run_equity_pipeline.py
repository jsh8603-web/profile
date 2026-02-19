#!/usr/bin/env python3
"""지분법과 연결회계 파이프라인 실행"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from noterang.pipeline import Pipeline, PipelineConfig
from noterang.poster import PostConfig

FINANCE_DESIGN_PROMPT = """[NotebookLM 슬라이드 디자인 요청]

■ 역할: 전문 프레젠테이션 디자이너
■ 스타일: 파이낸스
■ 카테고리: 비즈니스

━━━━━━━━━━━━━━━━━━━━━━

[컬러 시스템]
• 배경: #064e3b (다크 그린)
• 텍스트: #ecfdf5 (밝은 민트)
• 강조: #34d399 (에메랄드)
• 폰트: Lato

[무드 & 레퍼런스]
Bloomberg Terminal, 금융 리포트, 전문 재무 보고서

[디자인 특성]
• 깔끔한 데이터 표현
• 숫자/차트 중심 레이아웃
• 전문적이고 신뢰감 있는 톤
• 금융기관 보고서 느낌

[레이아웃 가이드]
헤더 + 본문 + 데이터 영역 3단 구성, 깔끔한 표와 차트

━━━━━━━━━━━━━━━━━━━━━━

위 가이드를 바탕으로 고품질 슬라이드를 생성해주세요.

[추가 요청사항]
- 반드시 한글로 작성
- 영어는 전문용어만 괄호 안에
- 슬라이드 10장
- 핵심 주제: 지분법과 연결회계 (Equity Method & Consolidated Accounting)
- 구성: 정의 → 지분법 적용범위(K-IFRS 1028) → 유의적 영향력 판단 → 지분법 회계처리 → 연결재무제표 개요(K-IFRS 1110) → 연결 vs 지분법 비교 → 내부거래 제거 → 실무 사례 → 공시요구사항 → 요약"""

config = PipelineConfig(
    title="지분법과 연결회계",
    sources=[
        "https://en.wikipedia.org/wiki/Equity_method",
        "https://www.kifrs.com/s/8/91ZhYx",
    ],
    design_prompt=FINANCE_DESIGN_PROMPT,
    slide_count=10,
    post=PostConfig(
        title="지분법과 연결회계 - K-IFRS 회계처리 완벽 가이드",
        slug="equity-method-consolidated-accounting",
        excerpt="지분법의 정의, K-IFRS 적용범위, 유의적 영향력 판단, 연결재무제표 작성방법, 내부거래 제거까지 지분법과 연결회계를 체계적으로 정리한 슬라이드입니다.",
        category="finance",
        tags=["지분법", "연결회계", "K-IFRS", "연결재무제표", "관계기업", "종속기업", "유의적영향력", "재무회계"],
    ),
    download_dir=Path("G:/내 드라이브/notebooklm_automation"),
)

async def main():
    result = await Pipeline(config).run()
    if result.success:
        print(f"\n✅ 성공! PDF: {result.pdf_path}")
    else:
        print(f"\n❌ 실패")
    return 0 if result.success else 1

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main()))
