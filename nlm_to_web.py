#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nlm_to_web - NotebookLM PDF → 웹 자료실 등록 스킬

이미 다운로드된 PDF를 바로 분석하여 자료실에 등록합니다.
브라우저 불필요, 수초 내 완료.

Usage:
    # PDF 경로 지정
    python nlm_to_web.py --pdf "G:/내 드라이브/notebooklm/족주상골_부골증.pdf" --title "족주상골부골증"

    # 최신 PDF 자동 선택
    python nlm_to_web.py --latest --title "족주상골부골증"

    # 옵션
    python nlm_to_web.py --pdf "path.pdf" --title "제목" --type disease --hidden
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# .env.local 로드
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / '.env.local'
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        _env_path2 = Path("D:/Projects/notebooklm-automation/.env.local")
        if _env_path2.exists():
            load_dotenv(_env_path2)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from run_pipeline import NoterangPipeline

DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")


def find_latest_pdf(directory: Path = DOWNLOAD_DIR) -> Path | None:
    """다운로드 폴더에서 최신 PDF 파일 찾기"""
    if not directory.exists():
        return None
    pdfs = sorted(directory.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pdfs[0] if pdfs else None


async def main():
    parser = argparse.ArgumentParser(
        description="nlm_to_web: NotebookLM PDF → 웹 자료실 등록"
    )
    parser.add_argument(
        "--title", "-t", required=True,
        help="자료 제목 (예: 족주상골부골증)"
    )
    parser.add_argument(
        "--pdf", "-p",
        help="PDF 파일 경로"
    )
    parser.add_argument(
        "--latest", "-l", action="store_true",
        help=f"최신 PDF 자동 선택 ({DOWNLOAD_DIR})"
    )
    parser.add_argument(
        "--type", default="disease",
        choices=["disease", "guide", "news"],
        help="자료 유형 (기본: disease)"
    )
    parser.add_argument(
        "--hidden", action="store_true",
        help="비공개 등록"
    )
    parser.add_argument(
        "--design", "-d", default="인포그래픽",
        help="디자인 스타일 (기본: 인포그래픽)"
    )

    args = parser.parse_args()

    # PDF 경로 결정
    pdf_path = None
    if args.pdf:
        pdf_path = args.pdf
    elif args.latest:
        latest = find_latest_pdf()
        if not latest:
            print(f"오류: {DOWNLOAD_DIR} 에서 PDF를 찾을 수 없습니다.")
            return 1
        pdf_path = str(latest)
        print(f"최신 PDF 선택: {pdf_path}")
    else:
        print("오류: --pdf 또는 --latest 중 하나를 지정하세요.")
        return 1

    pipeline = NoterangPipeline(
        title=args.title,
        pdf_path=pdf_path,
        register=True,
        visible=not args.hidden,
        article_type=args.type,
        design=args.design,
    )

    result = await pipeline.run()
    print(f"\nRESULT:{json.dumps(result, ensure_ascii=False)}")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
