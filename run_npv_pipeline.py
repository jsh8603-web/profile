#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPV 슬라이드 전체 파이프라인
Step 1: NotebookLM 자동화 (노트북 생성 → 소스 추가 → 슬라이드 생성 → PDF 다운로드)
Step 2: PDF 분석 (텍스트, 제목, 키워드 추출)
Step 3: Admin 폼 자동화 (Playwright로 직접 입력 + PDF 첨부 + Publish)
"""
import asyncio
import base64
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / '.env.local'
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

# ─── 설정 ───────────────────────────────────────────
POST_TITLE = "ROI Method: NPV - 순현재가치 분석"
POST_SLUG = "roi-method-npv"
POST_EXCERPT = "NPV(순현재가치)를 활용한 투자 의사결정 분석 방법을 알기 쉽게 정리한 슬라이드입니다."
POST_CATEGORY = "finance"
POST_TAGS = ["NPV", "ROI", "투자분석", "순현재가치", "재무분석", "현금흐름"]

NLM_TITLE = "ROI method : NPV"
NLM_SOURCE_URL = "https://ko.wikipedia.org/wiki/%EC%88%9C%ED%98%84%EC%9E%AC%EA%B0%80%EC%B9%98"
DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm_automation")
BROWSER_PROFILE = Path.home() / '.notebooklm-auto-v3'

ADMIN_URL = "https://profile-blue-pi.vercel.app"


# ─── PDF 분석 ────────────────────────────────────────

class PDFAnalyzer:
    def __init__(self, pdf_path: Path):
        import fitz
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(self.pdf_path))
        self.page_count = len(self.doc)

    def close(self):
        self.doc.close()

    def extract_all_text(self) -> List[str]:
        texts = []
        for page in self.doc:
            texts.append(page.get_text())
        total = sum(len(t.strip()) for t in texts)
        if total < 100:
            ocr = self._ocr_with_vision()
            if ocr:
                return ocr
        return texts

    def _ocr_with_vision(self) -> Optional[List[str]]:
        import fitz, requests
        api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY') or os.getenv('GOOGLE_VISION_API_KEY')
        if not api_key:
            return None
        texts = []
        for i, page in enumerate(self.doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            b64 = base64.b64encode(pix.tobytes("png")).decode()
            try:
                r = requests.post(
                    f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
                    json={"requests": [{"image": {"content": b64}, "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]}]},
                    timeout=60,
                )
                texts.append(r.json().get('responses', [{}])[0].get('fullTextAnnotation', {}).get('text', ''))
            except:
                texts.append("")
        return texts if sum(len(t) for t in texts) > 0 else None

    def extract_titles(self) -> List[str]:
        titles = []
        for page in self.doc:
            blocks = page.get_text("dict", flags=0)
            best, best_sz = "", 0
            for b in blocks.get("blocks", []):
                if b.get("type") != 0: continue
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
        parts = []
        for i, text in enumerate(texts):
            clean = re.sub(r'\s+', ' ', text).strip()
            if not clean: continue
            title = titles[i] if i < len(titles) else f"슬라이드 {i+1}"
            parts.append(f"### {title}\n\n{clean}")
        return "\n\n---\n\n".join(parts)

    def extract_keywords(self, top_n=10) -> List[str]:
        full = " ".join(t for t in self.extract_all_text() if t.strip())
        stop = {"그리고","하지만","또한","그래서","때문에","위해","통해","경우","등의","대한","있는","없는","하는","되는"}
        words = {}
        for w in full.split():
            c = "".join(ch for ch in w if '\uac00' <= ch <= '\ud7a3' or ch.isascii() and ch.isalpha())
            if len(c) >= 2 and c.lower() not in stop:
                words[c] = words.get(c, 0) + 1
        return [w for w, _ in sorted(words.items(), key=lambda x: -x[1])[:top_n]]

    def analyze(self) -> Dict[str, Any]:
        print(f"  PDF 분석: {self.pdf_path.name} ({self.page_count}페이지)")
        titles = self.extract_titles()
        keywords = self.extract_keywords()
        content = self.build_markdown()
        excerpt = POST_EXCERPT
        if titles:
            excerpt = f"{POST_TITLE} - " + ", ".join(titles[:5])
        print(f"  제목들: {titles[:5]}")
        print(f"  키워드: {keywords[:8]}")
        return {"page_count": self.page_count, "titles": titles,
                "keywords": keywords, "content": content, "excerpt": excerpt[:200]}


# ─── Step 1: NotebookLM 자동화 (전부 인라인) ───────────

async def run_notebooklm() -> Optional[Path]:
    """NotebookLM에서 NPV 슬라이드 생성 후 PDF 다운로드"""
    from playwright.async_api import async_playwright
    from noterang.auto_login import full_auto_login, BROWSER_PROFILE as AUTH_PROFILE
    from noterang.prompts import SlidePrompts

    prompts = SlidePrompts()
    design_prompt = prompts.get_prompt("사이언스 랩") or ""
    focus = f"""{design_prompt}

[추가 요청사항]
- 반드시 한글로 작성
- 영어는 전문용어만 괄호 안에
- 슬라이드 10장
- 핵심 주제: ROI method - NPV (순현재가치)
- 구성: NPV 정의 → 계산공식 → 할인율 → 현금흐름 추정 → 의사결정 기준 → 실무 사례 → IRR 비교 → 한계점 → 요약"""

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1] NotebookLM 브라우저 자동화")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(AUTH_PROFILE),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            downloads_path=str(DOWNLOAD_DIR),
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # ── 로그인 ──
        print("  1) 로그인 확인...")
        await page.goto('https://notebooklm.google.com/', timeout=60000)
        await asyncio.sleep(3)

        if 'accounts.google.com' in page.url:
            print("  로그인 필요 → full_auto_login 실행")
            await ctx.close()
            success = await full_auto_login(headless=False)
            if not success:
                print("  ❌ 로그인 실패")
                return None
            # 다시 열기
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(AUTH_PROFILE), headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True, downloads_path=str(DOWNLOAD_DIR),
            )
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(5)

        print(f"  ✓ 로그인 완료: {page.url}")

        # ── 노트북 생성 ──
        print("  2) 노트북 생성...")
        btn = await page.query_selector('[aria-label="새 노트 만들기"]')
        if btn:
            await btn.click()
            await asyncio.sleep(5)

        url = page.url
        if '/notebook/' not in url:
            print(f"  ❌ 노트북 생성 실패: {url}")
            await ctx.close()
            return None

        notebook_id = url.split('/notebook/')[-1].split('/')[0].split('?')[0]
        print(f"  ✓ 노트북: {notebook_id}")

        # ── 소스 추가 다이얼로그에서 "웹사이트" 탭으로 URL 입력 ──
        print(f"  3) 소스 추가: {NLM_SOURCE_URL[:50]}...")

        # 다이얼로그가 자동으로 열려있음 (?addSource=true)
        await asyncio.sleep(2)

        # 다이얼로그 내부를 스크린샷으로 확인
        await page.screenshot(path=str(DOWNLOAD_DIR / "debug_source_dialog.png"))

        # 방법 1: 다이얼로그 내 "웹사이트" 클릭 → URL 입력
        source_added = False

        # "웹사이트" 버튼 클릭 (JS로 오버레이 내부 접근)
        clicked_website = await page.evaluate('''() => {
            const pane = document.querySelector('.cdk-overlay-pane');
            if (!pane) return false;
            const btns = pane.querySelectorAll('button, [role="tab"], [role="button"]');
            for (const b of btns) {
                if (b.textContent.includes('웹사이트') || b.textContent.includes('Website')) {
                    b.click();
                    return true;
                }
            }
            return false;
        }''')
        print(f"  웹사이트 버튼 클릭: {clicked_website}")
        await asyncio.sleep(2)

        # URL 입력 필드 찾기 + 입력 (오버레이 내부)
        await page.screenshot(path=str(DOWNLOAD_DIR / "debug_after_website_click.png"))

        url_entered = await page.evaluate('''(url) => {
            // 오버레이 패널 내 모든 input 탐색
            const pane = document.querySelector('.cdk-overlay-pane');
            const root = pane || document;
            const inputs = root.querySelectorAll('input, textarea');
            for (const inp of inputs) {
                const ph = (inp.placeholder || '').toLowerCase();
                const t = inp.type || '';
                // URL 관련 입력 필드 또는 검색바
                if (ph.includes('url') || ph.includes('http') || ph.includes('붙여넣') ||
                    ph.includes('paste') || ph.includes('웹사이트') ||
                    t === 'url' || t === 'text' || t === 'search') {
                    if (inp.offsetParent !== null) {
                        // Angular의 NgModel을 위해 nativeInputValueSetter 사용
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value').set;
                        nativeSetter.call(inp, url);
                        inp.dispatchEvent(new Event('input', {bubbles: true}));
                        inp.dispatchEvent(new Event('change', {bubbles: true}));
                        return 'input:' + inp.placeholder;
                    }
                }
            }
            // 폴백: 첫 번째 visible input
            for (const inp of inputs) {
                if (inp.offsetParent !== null && inp.type !== 'hidden' && inp.type !== 'checkbox') {
                    const nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeSetter.call(inp, url);
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                    return 'fallback:' + inp.placeholder;
                }
            }
            return '';
        }''', NLM_SOURCE_URL)
        print(f"  URL 입력 결과: {url_entered}")

        if url_entered:
            await asyncio.sleep(1)

            # 삽입/제출 버튼 클릭
            submitted = await page.evaluate('''() => {
                const pane = document.querySelector('.cdk-overlay-pane');
                const root = pane || document;
                const btns = root.querySelectorAll('button');
                for (const b of btns) {
                    const t = (b.textContent || '').trim();
                    const label = b.getAttribute('aria-label') || '';
                    if (t.includes('삽입') || t.includes('Insert') || t.includes('추가') ||
                        label.includes('제출') || label.includes('submit')) {
                        if (b.offsetParent !== null && !b.disabled) {
                            b.click();
                            return t || label;
                        }
                    }
                }
                return '';
            }''')
            print(f"  제출 버튼: {submitted}")

            if not submitted:
                # Enter 키로 제출 시도
                await page.keyboard.press('Enter')
                print("  Enter 키로 제출")

            await asyncio.sleep(15)
            source_added = True
            print("  ✓ 소스 추가 완료")
        else:
            print("  ⚠️ URL 입력 실패")
            # 다이얼로그 닫기
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)

        # ── 소스 처리 대기 ──
        if source_added:
            print("  소스 처리 대기 (30초)...")
            await asyncio.sleep(30)
        else:
            print("  ⚠️ 소스 없이 진행 (슬라이드 생성 안 될 수 있음)")
            await asyncio.sleep(5)

        # ── 슬라이드 생성 ──
        print("  4) 슬라이드 생성 요청...")

        # "슬라이드 자료 맞춤설정" 버튼 클릭 → 프롬프트 입력
        # 버튼이 enabled 될 때까지 대기 (소스 처리 완료 필요)
        slide_edit = None
        for wait_i in range(6):  # 최대 30초 추가 대기
            slide_edit = await page.query_selector('[aria-label="슬라이드 자료 맞춤설정"]')
            if slide_edit:
                is_disabled = await slide_edit.get_attribute('disabled')
                aria_disabled = await slide_edit.get_attribute('aria-disabled')
                if not is_disabled and aria_disabled != 'true':
                    break
                print(f"  슬라이드 버튼 아직 비활성 → 대기 {(wait_i+1)*5}초...")
            await asyncio.sleep(5)

        if slide_edit:
            await slide_edit.click(force=True)
            await asyncio.sleep(3)
            print("  ✓ 슬라이드 맞춤설정 열림")

            # 프롬프트 입력 (다이얼로그/패널 내 textarea 또는 input)
            prompt_entered = await page.evaluate('''(prompt) => {
                // 오버레이 패널 또는 메인 페이지의 textarea
                const areas = document.querySelectorAll('textarea, [contenteditable="true"]');
                for (const a of areas) {
                    if (a.offsetParent !== null) {
                        a.focus();
                        a.value = prompt;
                        a.textContent = prompt;
                        a.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                }
                return false;
            }''', focus)

            if prompt_entered:
                print("  ✓ 디자인 프롬프트 입력 완료")
            await asyncio.sleep(1)

            # 생성/저장 버튼 클릭
            await page.evaluate('''() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const t = b.textContent.trim();
                    if (t.includes('생성') || t.includes('만들기') || t.includes('Generate') || t.includes('저장')) {
                        if (b.offsetParent !== null) { b.click(); return; }
                    }
                }
            }''')
            await asyncio.sleep(5)
        else:
            print("  '슬라이드 자료 맞춤설정' 버튼 없음 → 직접 클릭 시도")
            # 스튜디오 패널에서 "슬라이드 자료" 타일 직접 클릭
            await page.evaluate('''() => {
                const all = document.querySelectorAll('button, [role="button"], div[class*="studio"]');
                for (const el of all) {
                    if (el.textContent.includes('슬라이드 자료') && !el.textContent.includes('맞춤설정')) {
                        el.click(); return;
                    }
                }
            }''')
            await asyncio.sleep(5)

        # ── 슬라이드 생성 대기 (최대 10분) ──
        print("  5) 슬라이드 생성 대기... (최대 10분)")
        start = time.time()
        while time.time() - start < 600:
            # 다운로드 버튼이나 슬라이드 미리보기 확인
            ready = await page.evaluate('''() => {
                const body = document.body.innerText;
                // "다운로드" 버튼 또는 완료 표시 확인
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const label = b.getAttribute('aria-label') || '';
                    const text = b.textContent || '';
                    if (label.includes('다운로드') || label.includes('Download') ||
                        text.includes('다운로드') || text.includes('Download')) {
                        if (b.offsetParent !== null) return 'ready';
                    }
                }
                // 로딩 중인지 확인
                if (body.includes('생성 중') || body.includes('generating')) return 'loading';
                return 'unknown';
            }''')

            if ready == 'ready':
                print(f"\n  ✓ 슬라이드 생성 완료!")
                break

            elapsed = int(time.time() - start)
            print(f"\r  생성 중... {elapsed}초 ({ready})", end="", flush=True)
            await asyncio.sleep(10)
        else:
            print("\n  ⏰ 타임아웃")
            await page.screenshot(path=str(DOWNLOAD_DIR / "debug_timeout.png"))

        # ── PDF 다운로드 ──
        print("  6) PDF 다운로드...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = DOWNLOAD_DIR / f"NPV_slides_{timestamp}.pdf"

        # 더보기 메뉴 → 다운로드 시도
        downloaded = False
        try:
            # 메뉴 버튼들 시도
            menu_btns = await page.query_selector_all('[aria-haspopup="menu"], [aria-label*="더보기"], [aria-label*="more"]')
            for mb in menu_btns[-5:]:
                try:
                    await mb.click(force=True)
                    await asyncio.sleep(1)
                    dl_item = await page.query_selector(
                        '[role="menuitem"]:has-text("다운로드"), [role="menuitem"]:has-text("Download")'
                    )
                    if dl_item:
                        async with page.expect_download(timeout=60000) as dl_info:
                            await dl_item.click()
                        download = await dl_info.value
                        await download.save_as(str(save_path))
                        downloaded = True
                        print(f"  ✓ 다운로드 완료: {save_path}")
                        break
                    await page.keyboard.press('Escape')
                except:
                    try: await page.keyboard.press('Escape')
                    except: pass

            # 직접 다운로드 버튼
            if not downloaded:
                dl_btn = await page.query_selector(
                    'button:has-text("다운로드"), button:has-text("Download"), '
                    '[aria-label*="다운로드"], [aria-label*="Download"]'
                )
                if dl_btn:
                    try:
                        async with page.expect_download(timeout=60000) as dl_info:
                            await dl_btn.click(force=True)
                        download = await dl_info.value
                        await download.save_as(str(save_path))
                        downloaded = True
                        print(f"  ✓ 다운로드 완료: {save_path}")
                    except Exception as e:
                        print(f"  다운로드 실패: {e}")

        except Exception as e:
            print(f"  다운로드 오류: {e}")

        if not downloaded:
            print("  ⚠️ PDF 다운로드 실패")
            await page.screenshot(path=str(DOWNLOAD_DIR / "debug_download_fail.png"))

        await ctx.close()
        return save_path if downloaded and save_path.exists() else None


# ─── Step 3: Admin 폼 자동화 (Playwright) ──────────────

async def post_to_admin(pdf_path: Path, analysis: Dict[str, Any]):
    """Playwright로 admin/posts/new 폼에 직접 입력 + PDF 첨부 + Publish"""
    from playwright.async_api import async_playwright
    from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE

    content = analysis.get("content", f"# {POST_TITLE}\n\nNPV 순현재가치 분석 슬라이드")
    excerpt = analysis.get("excerpt", POST_EXCERPT)
    tags = list(POST_TAGS)
    for kw in analysis.get("keywords", []):
        if kw not in tags and len(kw) >= 2:
            tags.append(kw)
    tags = tags[:15]

    print("\n[Step 3] Admin 폼에 포스트 입력...")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(AUTH_PROFILE),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # Admin 페이지 이동
        await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
        await asyncio.sleep(3)

        # 로그인 필요시 Google 로그인 (이미 Google 세션 있음)
        if '/auth/signin' in page.url or '/auth' in page.url:
            print("  Admin 로그인 필요...")
            # Google Sign-In 버튼 클릭
            google_btn = await page.query_selector('button:has-text("Google"), button:has-text("Sign in")')
            if google_btn:
                async with ctx.expect_page() as popup_info:
                    await google_btn.click()
                popup = await popup_info.value
                await popup.wait_for_load_state()
                # Google 계정 선택 (이미 로그인된 계정)
                account = await popup.query_selector(f'[data-email="jsh8603@gmail.com"], div:has-text("jsh8603")')
                if account:
                    await account.click()
                    await asyncio.sleep(5)
            await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
            await asyncio.sleep(3)

        print(f"  URL: {page.url}")

        # ── Title ──
        title_input = await page.query_selector('#title, input[placeholder*="title"]')
        if title_input:
            await title_input.fill(POST_TITLE)
            await asyncio.sleep(0.5)
        print(f"  Title: {POST_TITLE}")

        # ── Slug ──
        slug_input = await page.query_selector('#slug, input[placeholder*="slug"]')
        if slug_input:
            await slug_input.fill('')
            await slug_input.fill(POST_SLUG)
            await asyncio.sleep(0.5)
        print(f"  Slug: {POST_SLUG}")

        # ── Excerpt ──
        excerpt_area = await page.query_selector('textarea[placeholder*="Brief"], textarea[placeholder*="description"]')
        if excerpt_area:
            await excerpt_area.fill(excerpt[:200])
        print(f"  Excerpt: {excerpt[:50]}...")

        # ── Category: Finance ──
        fin_btn = await page.query_selector('button:has-text("Finance")')
        if fin_btn:
            await fin_btn.click()
            await asyncio.sleep(0.3)
        print(f"  Category: Finance")

        # ── Tags ──
        tag_input = await page.query_selector('input[placeholder*="tag"]')
        if tag_input:
            for tag in tags:
                await tag_input.fill(tag)
                # Add 버튼 클릭
                add_btn = await page.query_selector('button:has-text("Add")')
                if add_btn:
                    await add_btn.click()
                    await asyncio.sleep(0.3)
        print(f"  Tags: {tags}")

        # ── PDF Attachment ──
        pdf_input = await page.query_selector('input[type="file"][accept=".pdf"]')
        if pdf_input:
            await pdf_input.set_input_files(str(pdf_path))
            await asyncio.sleep(3)
            print(f"  PDF 첨부: {pdf_path.name}")
        else:
            print("  ⚠️ PDF 첨부 input 없음 (PDF Attachment 기능이 배포되지 않았을 수 있음)")

        # ── Content (Markdown) ──
        content_area = await page.query_selector('textarea[placeholder*="Markdown"], textarea[placeholder*="Write"]')
        if content_area:
            await content_area.fill(content[:8000])
        print(f"  Content: {len(content)}자")

        # ── 스크린샷 (확인용) ──
        await page.screenshot(path=str(DOWNLOAD_DIR / "admin_form_filled.png"))
        print(f"  스크린샷 저장: admin_form_filled.png")

        # ── Publish 클릭 ──
        publish_btn = await page.query_selector('button:has-text("Publish")')
        if publish_btn:
            await publish_btn.click()
            await asyncio.sleep(5)
            print(f"  ✓ Publish 클릭 완료")
            print(f"  현재 URL: {page.url}")
        else:
            print("  ⚠️ Publish 버튼 없음")

        await page.screenshot(path=str(DOWNLOAD_DIR / "admin_after_publish.png"))
        await asyncio.sleep(3)
        await ctx.close()

    print(f"  ✓ 포스트 등록 완료: {ADMIN_URL}/blog/{POST_SLUG}")


# ─── 메인 ────────────────────────────────────────────

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="NPV 슬라이드 파이프라인")
    parser.add_argument("--pdf", "-p", help="기존 PDF 사용 (NotebookLM 건너뛰기)")
    args = parser.parse_args()

    start_time = time.time()
    print("\n" + "=" * 60)
    print("  NPV 슬라이드 전체 파이프라인")
    print("=" * 60)
    print(f"  포스트: {POST_TITLE}")
    print(f"  Admin:  {ADMIN_URL}/admin/posts/new")
    print("=" * 60)

    # ── Step 1: NotebookLM ──
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"  ❌ PDF 없음: {pdf_path}")
            return 1
        print(f"\n  기존 PDF 사용: {pdf_path}")
    else:
        pdf_path = await run_notebooklm()

    if not pdf_path or not pdf_path.exists():
        print("\n  ❌ PDF 확보 실패")
        return 1

    # ── Step 2: PDF 분석 ──
    print(f"\n[Step 2] PDF 분석: {pdf_path}")
    analyzer = PDFAnalyzer(pdf_path)
    try:
        analysis = analyzer.analyze()
    finally:
        analyzer.close()

    # ── Step 3: Admin 폼 입력 ──
    await post_to_admin(pdf_path, analysis)

    elapsed = int(time.time() - start_time)
    print("\n" + "=" * 60)
    print("  파이프라인 완료!")
    print("=" * 60)
    print(f"  PDF: {pdf_path}")
    print(f"  슬라이드: {analysis['page_count']}장")
    print(f"  URL: {ADMIN_URL}/blog/{POST_SLUG}")
    print(f"  소요시간: {elapsed}초")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
