"""
전체 파이프라인 오케스트레이터

NotebookLM 노트북 생성 → 소스 추가 → 슬라이드 생성 → PDF 다운로드 → (선택) 웹 포스팅
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .cdk_utils import (
    coord_click,
    dump_elements,
    overlay_click_insert,
    overlay_find_and_click,
    print_els,
    ss,
)
from .poster import AdminPoster, PostConfig

# ── dotenv ──
try:
    from dotenv import load_dotenv

    _env = Path(__file__).parents[1] / ".env.local"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass


# ═══════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════


@dataclass
class PipelineConfig:
    """파이프라인 실행에 필요한 모든 파라미터."""

    title: str  # 노트북 제목
    sources: list[str] = field(default_factory=list)  # URL 소스 목록
    design_prompt: str = ""  # 슬라이드 디자인 프롬프트 (빈 문자열이면 기본)
    slide_count: int = 10
    post: PostConfig | None = None  # None이면 포스팅 스킵
    download_dir: Path = field(default_factory=lambda: Path("G:/내 드라이브/notebooklm_automation"))

    @property
    def debug_dir(self) -> Path:
        return self.download_dir / "debug_screenshots"


@dataclass
class PipelineResult:
    """파이프라인 실행 결과."""

    success: bool
    pdf_path: Path | None = None
    analysis: dict[str, Any] | None = None
    post_result: dict[str, Any] | None = None
    elapsed_seconds: int = 0


# ═══════════════════════════════════════════════════
# PDFAnalyzer (private)
# ═══════════════════════════════════════════════════


class _PDFAnalyzer:
    """PDF 텍스트/키워드 추출. (PyMuPDF + 선택적 Vision OCR)"""

    def __init__(self, pdf_path: Path):
        import fitz

        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(self.pdf_path))
        self.page_count = len(self.doc)

    def close(self):
        self.doc.close()

    def extract_all_text(self) -> list[str]:
        texts = []
        for page in self.doc:
            texts.append(page.get_text())
        total = sum(len(t.strip()) for t in texts)
        if total < 100:
            ocr = self._ocr_with_vision()
            if ocr:
                return ocr
        return texts

    def _ocr_with_vision(self) -> list[str] | None:
        import fitz
        import requests

        api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY") or os.getenv("GOOGLE_VISION_API_KEY")
        if not api_key:
            return None
        texts: list[str] = []
        for page in self.doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            b64 = base64.b64encode(pix.tobytes("png")).decode()
            try:
                r = requests.post(
                    f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
                    json={"requests": [{"image": {"content": b64}, "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]}]},
                    timeout=60,
                )
                texts.append(r.json().get("responses", [{}])[0].get("fullTextAnnotation", {}).get("text", ""))
            except Exception:
                texts.append("")
        return texts if sum(len(t) for t in texts) > 0 else None

    def extract_titles(self) -> list[str]:
        titles: list[str] = []
        for page in self.doc:
            blocks = page.get_text("dict", flags=0)
            best, best_sz = "", 0.0
            for b in blocks.get("blocks", []):
                if b.get("type") != 0:
                    continue
                for ln in b.get("lines", []):
                    for sp in ln.get("spans", []):
                        t, sz = sp.get("text", "").strip(), sp.get("size", 0)
                        if t and sz > best_sz and len(t) > 1:
                            best, best_sz = t, sz
            if best:
                titles.append(best)
        return titles

    def build_markdown(self) -> str:
        texts = self.extract_all_text()
        titles = self.extract_titles()
        parts: list[str] = []
        for i, text in enumerate(texts):
            clean = re.sub(r"\s+", " ", text).strip()
            if not clean:
                continue
            title = titles[i] if i < len(titles) else f"슬라이드 {i+1}"
            parts.append(f"### {title}\n\n{clean}")
        return "\n\n---\n\n".join(parts)

    def extract_keywords(self, top_n: int = 10) -> list[str]:
        full = " ".join(t for t in self.extract_all_text() if t.strip())
        stop = {"그리고", "하지만", "또한", "그래서", "때문에", "위해", "통해", "경우", "등의", "대한", "있는", "없는", "하는", "되는"}
        words: dict[str, int] = {}
        for w in full.split():
            c = "".join(ch for ch in w if "\uac00" <= ch <= "\ud7a3" or ch.isascii() and ch.isalpha())
            if len(c) >= 2 and c.lower() not in stop:
                words[c] = words.get(c, 0) + 1
        return [w for w, _ in sorted(words.items(), key=lambda x: -x[1])[:top_n]]

    def analyze(self) -> dict[str, Any]:
        print(f"  PDF 분석: {self.pdf_path.name} ({self.page_count}페이지)")
        titles = self.extract_titles()
        keywords = self.extract_keywords()
        content = self.build_markdown()
        print(f"  제목들: {titles[:5]}")
        print(f"  키워드: {keywords[:8]}")
        return {
            "page_count": self.page_count,
            "titles": titles,
            "keywords": keywords,
            "content": content,
        }


# ═══════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════


class Pipeline:
    """전체 파이프라인 오케스트레이터."""

    def __init__(self, config: PipelineConfig):
        self.cfg = config

    async def run(self, existing_pdf: Path | str | None = None) -> PipelineResult:
        """파이프라인 실행.

        *existing_pdf* 를 넘기면 NotebookLM 단계를 건너뛰고 포스팅만 수행합니다.
        """
        start_time = time.time()

        print("\n" + "=" * 60)
        print(f"  파이프라인: {self.cfg.title}")
        print("=" * 60)

        # ── NotebookLM → PDF ──
        if existing_pdf:
            pdf_path = Path(existing_pdf)
            if not pdf_path.exists():
                print(f"  ❌ PDF 없음: {pdf_path}")
                return PipelineResult(success=False, elapsed_seconds=int(time.time() - start_time))
            print(f"  기존 PDF: {pdf_path}")
        else:
            pdf_path = await self.run_notebooklm()

        if not pdf_path or not pdf_path.exists():
            print("\n  ❌ PDF 없음 - 포스팅 건너뜀")
            return PipelineResult(success=False, elapsed_seconds=int(time.time() - start_time))

        # ── PDF 분석 ──
        analysis = self.analyze_pdf(pdf_path)

        # ── 웹 포스팅 (선택) ──
        post_result = None
        if self.cfg.post:
            post_result = await self.post_to_web(pdf_path, analysis)

        elapsed = int(time.time() - start_time)
        print("\n" + "=" * 60)
        print("  파이프라인 완료!")
        print("=" * 60)
        print(f"  PDF:      {pdf_path}")
        print(f"  슬라이드: {analysis['page_count']}장")
        if self.cfg.post:
            print(f"  포스트:   {self.cfg.post.admin_url}/blog/{self.cfg.post.slug}")
        print(f"  소요시간: {elapsed}초")
        print("=" * 60)

        return PipelineResult(
            success=True,
            pdf_path=pdf_path,
            analysis=analysis,
            post_result=post_result,
            elapsed_seconds=elapsed,
        )

    # ── NotebookLM 자동화 ──────────────────────────

    async def run_notebooklm(self) -> Path | None:
        """NotebookLM 자동화: 노트북 → 소스 → 슬라이드 → PDF 다운로드."""
        from playwright.async_api import async_playwright
        from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE, full_auto_login

        self.cfg.download_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.debug_dir.mkdir(parents=True, exist_ok=True)
        debug_dir = self.cfg.debug_dir

        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(AUTH_PROFILE),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1920, "height": 1080},
                accept_downloads=True,
                downloads_path=str(self.cfg.download_dir),
            )
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            save_path: Path | None = None
            downloaded = False

            try:
                # ── 1. 로그인 ──
                print("\n[1/6] 로그인 확인...")
                await page.goto("https://notebooklm.google.com/", timeout=60000)
                await asyncio.sleep(3)
                await ss(page, "01_login", debug_dir)

                if "accounts.google.com" in page.url:
                    print("  로그인 필요 → auto_login")
                    await ctx.close()
                    success = await full_auto_login(headless=False)
                    if not success:
                        print("  ❌ 로그인 실패")
                        return None
                    ctx = await p.chromium.launch_persistent_context(
                        user_data_dir=str(AUTH_PROFILE),
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled"],
                        viewport={"width": 1920, "height": 1080},
                        accept_downloads=True,
                        downloads_path=str(self.cfg.download_dir),
                    )
                    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
                    await page.goto("https://notebooklm.google.com/", timeout=60000)
                    await asyncio.sleep(5)

                print("  ✓ 로그인 완료")

                # ── 2. 노트북 생성 ──
                print("\n[2/6] 노트북 생성...")
                btn = await page.query_selector('[aria-label="새 노트 만들기"]')
                if btn:
                    await coord_click(page, btn, "새 노트 만들기")
                await asyncio.sleep(5)
                await ss(page, "02_notebook", debug_dir)

                if "/notebook/" not in page.url:
                    print(f"  ❌ 노트북 생성 실패: {page.url}")
                    await ctx.close()
                    return None

                notebook_id = page.url.split("/notebook/")[-1].split("/")[0].split("?")[0]
                print(f"  ✓ 노트북: {notebook_id}")

                # ── 3. 소스 추가 ──
                print("\n[3/6] 소스 추가...")
                await asyncio.sleep(3)
                await ss(page, "03_source_dialog", debug_dir)

                source_count = 0
                for ui, src_url in enumerate(self.cfg.sources):
                    print(f"\n  소스 {ui+1}/{len(self.cfg.sources)}: {src_url[:50]}...")

                    if ui > 0:
                        add_btn = await page.query_selector('[aria-label="출처 추가"]')
                        if add_btn:
                            await coord_click(page, add_btn, "출처 추가")
                            await asyncio.sleep(3)

                    # "웹사이트" 탭
                    ws_tab = await page.evaluate(
                        """() => {
                        const pane = document.querySelector('.cdk-overlay-pane');
                        if (!pane) return null;
                        const tabs = pane.querySelectorAll('[role="tab"], button');
                        for (const t of tabs) {
                            const txt = (t.textContent || '').trim();
                            if (txt.includes('웹사이트') && t.offsetParent !== null) {
                                const rect = t.getBoundingClientRect();
                                if (rect.width > 20 && rect.width < 300)
                                    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: txt.substring(0, 20)};
                            }
                        }
                        return null;
                    }"""
                    )
                    if ws_tab:
                        await coord_click(page, ws_tab, f"웹사이트 탭: '{ws_tab['text']}'")
                    else:
                        print("  ⚠️ '웹사이트' 탭 없음 → overlay_find_and_click 시도")
                        await overlay_find_and_click(page, "웹사이트", "웹사이트 탭")
                    await asyncio.sleep(2)
                    await ss(page, f"03_website_tab_{ui}", debug_dir)

                    # URL 입력
                    url_field = await page.evaluate(
                        """() => {
                        const pane = document.querySelector('.cdk-overlay-pane');
                        if (!pane) return null;
                        const areas = pane.querySelectorAll('textarea, input[type="text"], input[type="url"], input:not([type])');
                        for (const a of areas) {
                            const ph = (a.placeholder || '').toLowerCase();
                            if ((ph.includes('링크') || ph.includes('붙여넣') || ph.includes('url') || ph.includes('http')) &&
                                a.offsetParent !== null) {
                                const rect = a.getBoundingClientRect();
                                return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, ph: a.placeholder};
                            }
                        }
                        for (const a of areas) {
                            if (a.offsetParent === null) continue;
                            const ph = (a.placeholder || '');
                            if (ph.includes('검색') || ph.includes('search')) continue;
                            const rect = a.getBoundingClientRect();
                            if (rect.width > 100)
                                return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, ph: ph};
                        }
                        return null;
                    }"""
                    )

                    if url_field:
                        await coord_click(page, url_field, f"URL 입력필드 (ph={url_field['ph'][:25]})")
                        await asyncio.sleep(0.3)
                        await page.keyboard.press("Control+A")
                        await page.keyboard.type(src_url, delay=15)
                        await asyncio.sleep(1)
                        await ss(page, f"03_url_typed_{ui}", debug_dir)

                        await page.keyboard.press("Enter")
                        await asyncio.sleep(3)

                        if await overlay_click_insert(page):
                            source_count += 1
                            await asyncio.sleep(10)
                            await ss(page, f"03_inserted_{ui}", debug_dir)
                            print(f"  ✓ 소스 {ui+1} 추가 완료")
                        else:
                            await asyncio.sleep(5)
                            await ss(page, f"03_auto_inserted_{ui}", debug_dir)
                            print("  ⚠️ 삽입 버튼 없음 → 자동 처리 확인 필요")
                    else:
                        print("  ⚠️ URL 입력필드 없음")
                        await ss(page, f"03_no_url_field_{ui}", debug_dir)

                # 다이얼로그 닫기
                await page.keyboard.press("Escape")
                await asyncio.sleep(2)

                # 실제 소스 수 확인
                actual_sources = await page.evaluate(
                    """() => {
                    const items = document.querySelectorAll('[class*="source-item"], [class*="sourceItem"], [data-source-id], .source-list-item');
                    if (items.length > 0) return items.length;
                    const listItems = document.querySelectorAll('[role="listitem"], [role="option"]');
                    let count = 0;
                    for (const li of listItems) {
                        const rect = li.getBoundingClientRect();
                        if (rect.x < 400 && rect.width > 50 && rect.height > 20 && li.offsetParent !== null) count++;
                    }
                    return count;
                }"""
                )
                if actual_sources > 0:
                    source_count = actual_sources
                print(f"\n  총 {source_count}개 소스 추가됨 (UI 확인: {actual_sources}개)")

                # 제목 설정
                title_el = await page.query_selector('[contenteditable="true"]')
                if title_el:
                    await coord_click(page, title_el, "제목 입력")
                    await asyncio.sleep(0.5)
                    await page.keyboard.press("Control+A")
                    await page.keyboard.type(self.cfg.title, delay=30)
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(1)
                    print(f"  ✓ 제목: {self.cfg.title}")

                # 소스 처리 대기
                print("  소스 처리 대기 (20초)...")
                await asyncio.sleep(20)
                await ss(page, "03_sources_done", debug_dir)

                # ── 4. 슬라이드 생성 ──
                print("\n[4/6] 슬라이드 생성 요청...")
                await ss(page, "04_before_slide", debug_dir)
                await print_els(page, "body", "슬라이드 생성 전")

                slide_edit = None
                for attempt in range(12):
                    slide_edit = await page.query_selector('[aria-label="슬라이드 자료 맞춤설정"]')
                    if slide_edit:
                        is_disabled = await slide_edit.get_attribute("disabled")
                        aria_disabled = await slide_edit.get_attribute("aria-disabled")
                        if not is_disabled and aria_disabled != "true":
                            break
                        print(f"  슬라이드 버튼 비활성 → 대기 {(attempt+1)*5}초...")
                        slide_edit = None
                    await asyncio.sleep(5)

                if slide_edit:
                    await coord_click(page, slide_edit, "슬라이드 자료 맞춤설정")
                    await asyncio.sleep(3)
                    await ss(page, "04_slide_edit_open", debug_dir)
                    await print_els(page, "body", "맞춤설정 열림")

                    # 프롬프트 입력 (오늘 날짜 자동 주입)
                    design_prompt = self.cfg.design_prompt
                    if design_prompt:
                        today = datetime.now().strftime("%Y.%m.%d")
                        today_kr = datetime.now().strftime("%Y년 %m월 %d일")
                        date_instruction = f"\n\n[날짜]\n- 슬라이드에 표시할 날짜: {today} ({today_kr})\n- 반드시 위 날짜를 사용할 것 (다른 날짜 사용 금지)"
                        design_prompt = design_prompt + date_instruction
                        print(f"  날짜 주입: {today}")

                        prompt_box = await page.evaluate(
                            """() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return null;
                            const areas = pane.querySelectorAll('textarea');
                            for (const a of areas) {
                                if (a.offsetParent !== null) {
                                    const rect = a.getBoundingClientRect();
                                    if (rect.width > 100 && rect.height > 20)
                                        return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, tag: a.tagName,
                                                ph: (a.placeholder || '').substring(0, 40)};
                                }
                            }
                            return null;
                        }"""
                        )
                        if prompt_box:
                            await coord_click(page, prompt_box, f"오버레이 textarea (ph={prompt_box.get('ph', '')})")
                            await asyncio.sleep(0.3)
                            await page.keyboard.press("Control+A")
                            await asyncio.sleep(0.1)
                            await page.keyboard.type(design_prompt, delay=5)
                            await asyncio.sleep(1)
                            print(f"  ✓ 디자인 프롬프트 입력 ({len(self.cfg.design_prompt)}자)")
                        else:
                            print("  ⚠️ 프롬프트 textarea 없음 (기본 디자인)")

                    await ss(page, "04_prompt_entered", debug_dir)
                    await asyncio.sleep(1)

                    # 생성 버튼
                    gen_box = await page.evaluate(
                        """() => {
                        const pane = document.querySelector('.cdk-overlay-pane');
                        if (!pane) return null;
                        const btns = pane.querySelectorAll('button');
                        for (const b of btns) {
                            const t = b.textContent.trim();
                            if ((t.includes('생성') || t.includes('만들기') || t.includes('Generate')) &&
                                b.offsetParent !== null && !b.disabled) {
                                const rect = b.getBoundingClientRect();
                                if (rect.width > 30 && rect.height > 20)
                                    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t.substring(0, 30)};
                            }
                        }
                        return null;
                    }"""
                    )
                    if gen_box:
                        await coord_click(page, gen_box, f"생성: '{gen_box['text']}'")
                    else:
                        await page.keyboard.press("Enter")
                        print("  Enter 키로 생성 요청")

                    await asyncio.sleep(5)
                    await ss(page, "04_slide_generate", debug_dir)
                else:
                    print("  '맞춤설정' 버튼 없음 → 슬라이드 자료 타일 직접 클릭")
                    tile_box = await page.evaluate(
                        """() => {
                        const all = document.querySelectorAll('button, [role="button"], div[class*="studio"], div[class*="artifact"]');
                        for (const el of all) {
                            const t = (el.textContent || '').trim();
                            if (t.includes('슬라이드') && !t.includes('맞춤설정') && el.offsetParent !== null) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 50) return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t.substring(0, 30)};
                            }
                        }
                        return null;
                    }"""
                    )
                    if tile_box:
                        await coord_click(page, tile_box, f"슬라이드 타일: '{tile_box['text']}'")
                    await asyncio.sleep(5)

                # ── 5. 슬라이드 생성 완료 대기 ──
                print("\n[5/6] 슬라이드 생성 대기... (최소 30초 후 감지 시작)")
                await asyncio.sleep(30)
                print("  30초 대기 완료, 감지 시작...")
                start_wait = time.time()
                while time.time() - start_wait < 570:
                    elapsed_s = int(time.time() - start_wait)
                    if elapsed_s % 60 < 15:
                        await ss(page, f"05_check_{elapsed_s}", debug_dir)
                    ready = await page.evaluate(
                        """() => {
                        const btns = document.querySelectorAll('button');
                        for (const b of btns) {
                            const label = b.getAttribute('aria-label') || '';
                            const text = b.textContent || '';
                            if ((label.includes('다운로드') || label.includes('Download') ||
                                 text.includes('다운로드') || text.includes('Download')) &&
                                b.offsetParent !== null) return 'ready';
                        }
                        const iframes = document.querySelectorAll('iframe, embed');
                        for (const f of iframes) {
                            if (f.offsetParent !== null) {
                                const rect = f.getBoundingClientRect();
                                if (rect.width > 300 && rect.height > 200) return 'ready';
                            }
                        }
                        for (const b of btns) {
                            const label = b.getAttribute('aria-label') || '';
                            if (label.includes('더보기') && b.offsetParent !== null) {
                                const rect = b.getBoundingClientRect();
                                if (rect.x > 1400) return 'ready';
                            }
                        }
                        const links = document.querySelectorAll('a');
                        for (const a of links) {
                            if ((a.textContent || '').includes('프레젠테이션') || (a.href || '').includes('docs.google.com/presentation'))
                                return 'ready';
                        }
                        const body = document.body.innerText;
                        if (body.includes('생성 중') || body.includes('generating') || body.includes('Creating')) return 'loading';
                        if (body.includes('생성할 수 없') || body.includes('오류')) return 'error';
                        return 'unknown';
                    }"""
                    )
                    if ready == "ready":
                        print(f"\n  ✓ 슬라이드 생성 완료!")
                        break
                    if ready == "error":
                        print(f"\n  ❌ 슬라이드 생성 오류")
                        break
                    elapsed = int(time.time() - start_wait)
                    print(f"\r  생성 중... {elapsed}초 ({ready})", end="", flush=True)
                    await asyncio.sleep(10)
                else:
                    print("\n  ⏰ 타임아웃 - 현재 상태로 다운로드 시도")

                await ss(page, "05_slides_ready", debug_dir)
                await print_els(page, "body", "슬라이드 완료 후")

                # ── 6. PDF 다운로드 ──
                print("\n[6/6] PDF 다운로드...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.cfg.download_dir / f"{self.cfg.title}_{timestamp}.pdf"

                # 방법 1: 더보기 메뉴 → 다운로드
                all_els = await dump_elements(page, "body")
                menu_candidates = [
                    el
                    for el in all_els
                    if el["tag"] == "button"
                    and ("더보기" in el["label"] or "more" in el["label"].lower() or el["text"] == "more_vert")
                    and el["x"] > 800
                ]

                for mc in reversed(menu_candidates):
                    try:
                        await coord_click(page, mc, f"더보기 메뉴 ({mc['x']},{mc['y']})")
                        await asyncio.sleep(1)
                        await ss(page, "06_menu_open", debug_dir)

                        dl_item = await page.query_selector('[role="menuitem"]:has-text("다운로드"), [role="menuitem"]:has-text("Download")')
                        if dl_item:
                            dl_box = await dl_item.bounding_box()
                            if dl_box:
                                async with page.expect_download(timeout=60000) as dl_info:
                                    await page.mouse.click(dl_box["x"] + dl_box["width"] / 2, dl_box["y"] + dl_box["height"] / 2)
                                download = await dl_info.value
                                await download.save_as(str(save_path))
                                downloaded = True
                                print(f"  ✓ 다운로드 완료: {save_path}")
                                break
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"  메뉴 시도 실패: {e}")
                        try:
                            await page.keyboard.press("Escape")
                        except Exception:
                            pass

                # 방법 2: 다운로드 버튼 직접
                if not downloaded:
                    dl_candidates = [
                        el
                        for el in all_els
                        if el["tag"] == "button"
                        and ("다운로드" in el["text"] or "Download" in el["text"] or "다운로드" in el["label"] or "Download" in el["label"])
                    ]
                    for dc in dl_candidates:
                        try:
                            async with page.expect_download(timeout=60000) as dl_info:
                                await coord_click(page, dc, f"다운로드: '{dc['text'][:20]}'")
                            download = await dl_info.value
                            await download.save_as(str(save_path))
                            downloaded = True
                            print(f"  ✓ 다운로드 완료: {save_path}")
                            break
                        except Exception:
                            pass

                if not downloaded:
                    print("  ⚠️ PDF 다운로드 실패")
                    await ss(page, "06_download_fail", debug_dir)

                await ss(page, "06_final", debug_dir)

            except Exception as e:
                print(f"\n  ❌ 오류: {e}")
                import traceback

                traceback.print_exc()
                await ss(page, "error", debug_dir)
                save_path = None
                downloaded = False

            finally:
                await ctx.close()

        return save_path if downloaded and save_path and save_path.exists() else None

    # ── PDF 분석 ────────────────────────────────────

    def analyze_pdf(self, pdf_path: Path) -> dict[str, Any]:
        """PDF 텍스트/키워드 추출."""
        print(f"\n[PDF 분석] {pdf_path}")
        analyzer = _PDFAnalyzer(pdf_path)
        try:
            return analyzer.analyze()
        finally:
            analyzer.close()

    # ── 웹 포스팅 ───────────────────────────────────

    async def post_to_web(self, pdf_path: Path, analysis: dict[str, Any]) -> dict[str, Any]:
        """AdminPoster 를 통해 웹에 포스팅."""
        if not self.cfg.post:
            return {}
        content = analysis.get("content", f"# {self.cfg.post.title}\n\n슬라이드 분석")
        extra_tags = analysis.get("keywords", [])
        poster = AdminPoster(self.cfg.post)
        return await poster.post(pdf_path, content, extra_tags)


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════


async def _async_main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Noterang 전체 파이프라인")
    parser.add_argument("--title", "-t", required=True, help="노트북/슬라이드 제목")
    parser.add_argument("--sources", "-s", default="", help="쉼표 구분 URL 목록")
    parser.add_argument("--design", "-d", default="", help="디자인 프롬프트 (또는 파일 경로)")
    parser.add_argument("--pdf", "-p", default="", help="기존 PDF 경로 (NotebookLM 건너뛰기)")
    parser.add_argument("--skip-post", action="store_true", help="포스팅 스킵")
    parser.add_argument("--post-title", default="", help="포스트 제목 (기본: --title 과 동일)")
    parser.add_argument("--slug", default="", help="포스트 URL slug")
    parser.add_argument("--excerpt", default="", help="포스트 요약")
    parser.add_argument("--category", default="finance", help="포스트 카테고리")
    parser.add_argument("--tags", default="", help="쉼표 구분 태그")
    parser.add_argument("--download-dir", default="", help="다운로드 디렉터리")
    args = parser.parse_args()

    sources = [u.strip() for u in args.sources.split(",") if u.strip()] if args.sources else []

    # 디자인 프롬프트: 파일 경로면 읽기
    design_prompt = args.design
    if design_prompt and Path(design_prompt).is_file():
        design_prompt = Path(design_prompt).read_text(encoding="utf-8")

    # PostConfig
    post_cfg: PostConfig | None = None
    if not args.skip_post and (args.post_title or args.slug):
        slug = args.slug or re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
        post_cfg = PostConfig(
            title=args.post_title or args.title,
            slug=slug,
            excerpt=args.excerpt or f"{args.title} 슬라이드 분석",
            category=args.category,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else [],
        )

    download_dir = Path(args.download_dir) if args.download_dir else Path("G:/내 드라이브/notebooklm_automation")

    config = PipelineConfig(
        title=args.title,
        sources=sources,
        design_prompt=design_prompt,
        post=post_cfg,
        download_dir=download_dir,
    )

    result = await Pipeline(config).run(existing_pdf=args.pdf or None)
    return 0 if result.success else 1


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    return asyncio.run(_async_main())


if __name__ == "__main__":
    sys.exit(main())
