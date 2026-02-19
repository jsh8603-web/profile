#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공사충당부채 전체 파이프라인
1. NotebookLM 노트북 생성 + 소스 추가
2. 파이낸스 디자인 한글 10장 슬라이드 생성
3. PDF 다운로드
4. PDF 분석 (텍스트/키워드 추출)
5. Admin 폼 자동 입력 + PDF 첨부 + Publish
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

# ─── 설정 ───
DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm_automation")
DEBUG_DIR = DOWNLOAD_DIR / "debug_screenshots"
BROWSER_PROFILE = Path.home() / '.notebooklm-auto-v3'

# 포스트 정보
POST_TITLE = "공사충당부채 - 건설업 회계처리 완벽 가이드"
POST_SLUG = "construction-provision-liability"
POST_EXCERPT = "공사충당부채의 정의, K-IFRS 회계기준, 인식조건, 측정방법, 하자보수충당부채까지 건설업 재무회계를 체계적으로 정리한 슬라이드입니다."
POST_CATEGORY = "finance"
POST_TAGS = ["공사충당부채", "충당부채", "K-IFRS", "건설업회계", "하자보수", "재무회계", "IAS37"]
ADMIN_URL = "https://profile-blue-pi.vercel.app"

# NotebookLM 설정
NLM_TITLE = "공사충당부채"
NLM_SOURCES = [
    "https://ko.wikipedia.org/wiki/%EC%B6%A9%EB%8B%B9%EB%B6%80%EC%B1%84",
    "https://en.wikipedia.org/wiki/Provision_(accounting)",
]

# 파이낸스 디자인 프롬프트
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
- 핵심 주제: 공사충당부채 (Construction Provision)
- 구성: 정의 → 회계기준(K-IFRS) → 인식조건 → 측정방법 → 공사계약 적용 → 실무 사례 → 공시요구사항 → 하자보수충당부채 → 세무처리 → 요약"""


# ═══════════════════════════════════════════════════
# 유틸리티 함수 (CDK overlay 우회용)
# ═══════════════════════════════════════════════════

async def ss(page, name: str) -> str:
    """스크린샷 저장"""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%H%M%S')
    path = str(DEBUG_DIR / f"{ts}_{name}.png")
    await page.screenshot(path=path)
    print(f"  📸 {name}")
    return path


async def dump_elements(page, scope: str = "body") -> list:
    """페이지/오버레이 내 클릭 가능한 요소 덤프"""
    return await page.evaluate(f'''(scope) => {{
        const root = scope === 'overlay'
            ? document.querySelector('.cdk-overlay-pane') || document.body
            : document.querySelector(scope) || document.body;
        const els = root.querySelectorAll('button, input, textarea, [role="tab"], [role="button"], [role="menuitem"], a, [contenteditable="true"]');
        const result = [];
        for (let i = 0; i < els.length; i++) {{
            const el = els[i];
            if (el.offsetParent === null && el.type !== 'file') continue;
            const rect = el.getBoundingClientRect();
            result.push({{
                idx: i, tag: el.tagName.toLowerCase(), type: el.type || '',
                text: (el.textContent || '').trim().substring(0, 60),
                label: el.getAttribute('aria-label') || '',
                placeholder: el.placeholder || '',
                disabled: el.disabled || false,
                x: Math.round(rect.x), y: Math.round(rect.y),
                w: Math.round(rect.width), h: Math.round(rect.height),
            }});
        }}
        return result;
    }}''', scope)


async def print_els(page, scope="body", label=""):
    """요소 목록 출력"""
    els = await dump_elements(page, scope)
    print(f"\n  --- {label or scope} ({len(els)}개) ---")
    for el in els:
        d = " [DISABLED]" if el['disabled'] else ""
        print(f"  [{el['idx']}] {el['tag']} text='{el['text'][:35]}' label='{el['label'][:25]}' ph='{el['placeholder'][:25]}' ({el['x']},{el['y']} {el['w']}x{el['h']}){d}")
    print(f"  ---\n")
    return els


async def coord_click(page, box_or_el, description=""):
    """좌표 기반 다이렉트 마우스 클릭 (CDK overlay 우회)"""
    if isinstance(box_or_el, dict):
        cx = box_or_el['x'] + box_or_el['w'] / 2
        cy = box_or_el['y'] + box_or_el['h'] / 2
    else:
        box = await box_or_el.bounding_box()
        if not box:
            print(f"  ✗ bbox 없음: {description}")
            return False
        cx = box['x'] + box['width'] / 2
        cy = box['y'] + box['height'] / 2
    await page.mouse.click(cx, cy)
    print(f"  ✓ 클릭: {description} ({cx:.0f},{cy:.0f})")
    return True


async def overlay_find_and_click(page, text_match: str, description=""):
    """오버레이 내 텍스트로 요소 찾아 좌표 클릭"""
    box = await page.evaluate('''(text) => {
        const pane = document.querySelector('.cdk-overlay-pane');
        if (!pane) return null;
        const els = pane.querySelectorAll('button, [role="tab"], span, div, textarea, input');
        for (const el of els) {
            const t = (el.textContent || '').trim();
            if (t.includes(text) && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 10 && rect.height > 10)
                    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t.substring(0, 50)};
            }
        }
        return null;
    }''', text_match)
    if box:
        await coord_click(page, box, description or text_match)
        return True
    print(f"  ✗ '{text_match}' 없음")
    return False


async def overlay_find_inputs(page):
    """오버레이 내 visible input/textarea 좌표 목록"""
    return await page.evaluate('''() => {
        const pane = document.querySelector('.cdk-overlay-pane');
        if (!pane) return [];
        const inputs = pane.querySelectorAll('input, textarea');
        const result = [];
        for (const inp of inputs) {
            if (inp.offsetParent === null) continue;
            if (inp.type === 'hidden' || inp.type === 'checkbox' || inp.type === 'radio') continue;
            const rect = inp.getBoundingClientRect();
            result.push({x: rect.x, y: rect.y, w: rect.width, h: rect.height,
                         placeholder: inp.placeholder || '', type: inp.type || 'text'});
        }
        return result;
    }''')


async def overlay_click_insert(page):
    """오버레이 내 '삽입' 버튼 좌표 클릭"""
    box = await page.evaluate('''() => {
        const pane = document.querySelector('.cdk-overlay-pane');
        if (!pane) return null;
        const btns = pane.querySelectorAll('button');
        for (const b of btns) {
            const t = (b.textContent || '').trim();
            const l = b.getAttribute('aria-label') || '';
            if ((t.includes('삽입') || t.includes('Insert') || l.includes('제출') || l.includes('submit')) &&
                b.offsetParent !== null && !b.disabled) {
                const rect = b.getBoundingClientRect();
                return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t};
            }
        }
        return null;
    }''')
    if box:
        await coord_click(page, box, f"삽입: '{box['text'][:20]}'")
        return True
    print("  ✗ 삽입 버튼 없음/비활성")
    return False


# ═══════════════════════════════════════════════════
# PDF 분석
# ═══════════════════════════════════════════════════

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
        for page in self.doc:
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
        parts = []
        for i, text in enumerate(texts):
            clean = re.sub(r'\s+', ' ', text).strip()
            if not clean:
                continue
            title = titles[i] if i < len(titles) else f"슬라이드 {i+1}"
            parts.append(f"### {title}\n\n{clean}")
        return "\n\n---\n\n".join(parts)

    def extract_keywords(self, top_n=10) -> List[str]:
        full = " ".join(t for t in self.extract_all_text() if t.strip())
        stop = {"그리고", "하지만", "또한", "그래서", "때문에", "위해", "통해", "경우", "등의", "대한", "있는", "없는", "하는", "되는"}
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
        print(f"  제목들: {titles[:5]}")
        print(f"  키워드: {keywords[:8]}")
        return {
            "page_count": self.page_count,
            "titles": titles,
            "keywords": keywords,
            "content": content,
        }


# ═══════════════════════════════════════════════════
# STEP 1: NotebookLM 노트북 + 소스 + 슬라이드 + PDF
# ═══════════════════════════════════════════════════

async def run_notebooklm() -> Optional[Path]:
    """NotebookLM 자동화: 노트북 → 소스 → 슬라이드 → PDF 다운로드"""
    from playwright.async_api import async_playwright
    from noterang.auto_login import full_auto_login, BROWSER_PROFILE as AUTH_PROFILE

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

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

        try:
            # ── 1. 로그인 ──
            print("\n[1/6] 로그인 확인...")
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(3)
            await ss(page, "01_login")

            if 'accounts.google.com' in page.url:
                print("  로그인 필요 → auto_login")
                await ctx.close()
                success = await full_auto_login(headless=False)
                if not success:
                    print("  ❌ 로그인 실패")
                    return None
                ctx = await p.chromium.launch_persistent_context(
                    user_data_dir=str(AUTH_PROFILE), headless=False,
                    args=['--disable-blink-features=AutomationControlled'],
                    viewport={'width': 1920, 'height': 1080},
                    accept_downloads=True, downloads_path=str(DOWNLOAD_DIR),
                )
                page = ctx.pages[0] if ctx.pages else await ctx.new_page()
                await page.goto('https://notebooklm.google.com/', timeout=60000)
                await asyncio.sleep(5)

            print(f"  ✓ 로그인 완료")

            # ── 2. 노트북 생성 ──
            print("\n[2/6] 노트북 생성...")
            btn = await page.query_selector('[aria-label="새 노트 만들기"]')
            if btn:
                await coord_click(page, btn, "새 노트 만들기")
            await asyncio.sleep(5)
            await ss(page, "02_notebook")

            if '/notebook/' not in page.url:
                print(f"  ❌ 노트북 생성 실패: {page.url}")
                await ctx.close()
                return None

            notebook_id = page.url.split('/notebook/')[-1].split('/')[0].split('?')[0]
            print(f"  ✓ 노트북: {notebook_id}")

            # ── 3. 소스 추가 (URL 방식) ──
            print("\n[3/6] 소스 추가...")
            await asyncio.sleep(3)
            await ss(page, "03_source_dialog")

            source_count = 0
            for ui, src_url in enumerate(NLM_SOURCES):
                print(f"\n  소스 {ui+1}/{len(NLM_SOURCES)}: {src_url[:50]}...")

                # 첫 번째는 다이얼로그 이미 열려있음, 이후는 재열기
                if ui > 0:
                    add_btn = await page.query_selector('[aria-label="출처 추가"]')
                    if add_btn:
                        await coord_click(page, add_btn, "출처 추가")
                        await asyncio.sleep(3)

                # "웹사이트" 탭 찾기 - role="tab" 중 "웹사이트" 텍스트 포함
                ws_tab = await page.evaluate('''() => {
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
                }''')
                if ws_tab:
                    await coord_click(page, ws_tab, f"웹사이트 탭: '{ws_tab['text']}'")
                else:
                    print("  ⚠️ '웹사이트' 탭 없음 → overlay_find_and_click 시도")
                    await overlay_find_and_click(page, "웹사이트", "웹사이트 탭")
                await asyncio.sleep(2)
                await ss(page, f"03_website_tab_{ui}")

                # URL 입력 - "링크를 붙여넣으세요" placeholder를 가진 textarea 찾기
                url_field = await page.evaluate('''() => {
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
                    // 대안: 오버레이 내 visible textarea 중 placeholder가 '검색'이 아닌 것
                    for (const a of areas) {
                        if (a.offsetParent === null) continue;
                        const ph = (a.placeholder || '');
                        if (ph.includes('검색') || ph.includes('search')) continue;
                        const rect = a.getBoundingClientRect();
                        if (rect.width > 100)
                            return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, ph: ph};
                    }
                    return null;
                }''')

                if url_field:
                    await coord_click(page, url_field, f"URL 입력필드 (ph={url_field['ph'][:25]})")
                    await asyncio.sleep(0.3)
                    await page.keyboard.press('Control+A')
                    await page.keyboard.type(src_url, delay=15)
                    await asyncio.sleep(1)
                    await ss(page, f"03_url_typed_{ui}")

                    # Enter 전송
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(3)

                    # 삽입 버튼
                    if await overlay_click_insert(page):
                        source_count += 1
                        await asyncio.sleep(10)
                        await ss(page, f"03_inserted_{ui}")
                        print(f"  ✓ 소스 {ui+1} 추가 완료")
                    else:
                        # 삽입 버튼 없이 자동 처리되었을 수 있음
                        await asyncio.sleep(5)
                        await ss(page, f"03_auto_inserted_{ui}")
                        print(f"  ⚠️ 삽입 버튼 없음 → 자동 처리 확인 필요")
                else:
                    print(f"  ⚠️ URL 입력필드 없음")
                    await ss(page, f"03_no_url_field_{ui}")

            # 다이얼로그 닫기
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)

            # 실제 소스 수 확인 (왼쪽 패널의 소스 아이템 카운트)
            actual_sources = await page.evaluate('''() => {
                // 소스 목록 패널에서 실제 소스 아이템 수를 센다
                const items = document.querySelectorAll('[class*="source-item"], [class*="sourceItem"], [data-source-id], .source-list-item');
                if (items.length > 0) return items.length;
                // 대안: "출처" 섹션 아래 리스트 아이템
                const listItems = document.querySelectorAll('[role="listitem"], [role="option"]');
                let count = 0;
                for (const li of listItems) {
                    const rect = li.getBoundingClientRect();
                    if (rect.x < 400 && rect.width > 50 && rect.height > 20 && li.offsetParent !== null) count++;
                }
                return count;
            }''')
            if actual_sources > 0:
                source_count = actual_sources
            print(f"\n  총 {source_count}개 소스 추가됨 (UI 확인: {actual_sources}개)")

            # 제목 설정
            title_el = await page.query_selector('[contenteditable="true"]')
            if title_el:
                await coord_click(page, title_el, "제목 입력")
                await asyncio.sleep(0.5)
                await page.keyboard.press('Control+A')
                await page.keyboard.type(NLM_TITLE, delay=30)
                await page.keyboard.press('Tab')
                await asyncio.sleep(1)
                print(f"  ✓ 제목: {NLM_TITLE}")

            # 소스 처리 대기
            print("  소스 처리 대기 (20초)...")
            await asyncio.sleep(20)
            await ss(page, "03_sources_done")

            # ── 4. 슬라이드 생성 ──
            print("\n[4/6] 슬라이드 생성 요청...")
            await ss(page, "04_before_slide")
            await print_els(page, "body", "슬라이드 생성 전")

            # "슬라이드 자료 맞춤설정" 버튼 대기 (소스 처리 후 활성화)
            slide_edit = None
            for attempt in range(12):  # 최대 60초 대기
                slide_edit = await page.query_selector('[aria-label="슬라이드 자료 맞춤설정"]')
                if slide_edit:
                    is_disabled = await slide_edit.get_attribute('disabled')
                    aria_disabled = await slide_edit.get_attribute('aria-disabled')
                    if not is_disabled and aria_disabled != 'true':
                        break
                    print(f"  슬라이드 버튼 비활성 → 대기 {(attempt+1)*5}초...")
                    slide_edit = None
                await asyncio.sleep(5)

            if slide_edit:
                # FIX #1: 좌표 클릭으로 맞춤설정 열기
                await coord_click(page, slide_edit, "슬라이드 자료 맞춤설정")
                await asyncio.sleep(3)
                await ss(page, "04_slide_edit_open")
                await print_els(page, "body", "맞춤설정 열림")

                # FIX #2: 프롬프트 입력 - CDK 오버레이 내 textarea만 찾기
                prompt_box = await page.evaluate('''() => {
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
                }''')

                if prompt_box:
                    # 오늘 날짜 자동 주입
                    today = datetime.now().strftime("%Y.%m.%d")
                    today_kr = datetime.now().strftime("%Y년 %m월 %d일")
                    date_instruction = f"\n\n[날짜]\n- 슬라이드에 표시할 날짜: {today} ({today_kr})\n- 반드시 위 날짜를 사용할 것 (다른 날짜 사용 금지)"
                    design_prompt = FINANCE_DESIGN_PROMPT + date_instruction
                    print(f"  날짜 주입: {today}")

                    await coord_click(page, prompt_box, f"오버레이 textarea (ph={prompt_box.get('ph','')})")
                    await asyncio.sleep(0.3)
                    await page.keyboard.press('Control+A')
                    await asyncio.sleep(0.1)
                    await page.keyboard.type(design_prompt, delay=5)
                    await asyncio.sleep(1)
                    print(f"  ✓ 디자인 프롬프트 입력 ({len(design_prompt)}자)")
                else:
                    print("  ⚠️ 프롬프트 textarea 없음 (기본 디자인)")

                await ss(page, "04_prompt_entered")
                await asyncio.sleep(1)

                # FIX #3: 생성 버튼 - CDK 오버레이 내에서만 찾기
                gen_box = await page.evaluate('''() => {
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
                }''')

                if gen_box:
                    await coord_click(page, gen_box, f"생성: '{gen_box['text']}'")
                else:
                    # Enter 키 폴백
                    await page.keyboard.press('Enter')
                    print("  Enter 키로 생성 요청")

                await asyncio.sleep(5)
                await ss(page, "04_slide_generate")
            else:
                # 직접 "슬라이드 자료" 타일 좌표 클릭
                print("  '맞춤설정' 버튼 없음 → 슬라이드 자료 타일 직접 클릭")
                tile_box = await page.evaluate('''() => {
                    const all = document.querySelectorAll('button, [role="button"], div[class*="studio"], div[class*="artifact"]');
                    for (const el of all) {
                        const t = (el.textContent || '').trim();
                        if (t.includes('슬라이드') && !t.includes('맞춤설정') && el.offsetParent !== null) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 50) return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t.substring(0, 30)};
                        }
                    }
                    return null;
                }''')
                if tile_box:
                    await coord_click(page, tile_box, f"슬라이드 타일: '{tile_box['text']}'")
                await asyncio.sleep(5)

            # ── 5. 슬라이드 생성 완료 대기 (최대 10분) ──
            # FIX #4: 최소 30초 대기 후 감지, false positive 제거
            print("\n[5/6] 슬라이드 생성 대기... (최소 30초 후 감지 시작)")
            await asyncio.sleep(30)  # 최소 대기
            print("  30초 대기 완료, 감지 시작...")
            start_wait = time.time()
            while time.time() - start_wait < 570:  # 30+570 = 600초 총 10분
                elapsed_s = int(time.time() - start_wait)
                if elapsed_s % 60 < 15:  # 매 60초마다 스크린샷
                    await ss(page, f"05_check_{elapsed_s}")
                ready = await page.evaluate('''() => {
                    // 1. 다운로드 버튼/메뉴 (가장 확실한 신호)
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const label = b.getAttribute('aria-label') || '';
                        const text = b.textContent || '';
                        if ((label.includes('다운로드') || label.includes('Download') ||
                             text.includes('다운로드') || text.includes('Download')) &&
                            b.offsetParent !== null) return 'ready';
                    }
                    // 2. 슬라이드 미리보기 iframe/embed만 (slide 클래스 제외 - false positive)
                    const iframes = document.querySelectorAll('iframe, embed');
                    for (const f of iframes) {
                        if (f.offsetParent !== null) {
                            const rect = f.getBoundingClientRect();
                            if (rect.width > 300 && rect.height > 200) return 'ready';
                        }
                    }
                    // 3. 스튜디오 패널의 더보기 메뉴 (새 아티팩트 생성 완료 시 나타남)
                    for (const b of btns) {
                        const label = b.getAttribute('aria-label') || '';
                        if (label.includes('더보기') && b.offsetParent !== null) {
                            const rect = b.getBoundingClientRect();
                            if (rect.x > 1400) return 'ready';  // 스튜디오 패널 (x > 1400)
                        }
                    }
                    // 4. "Google 프레젠테이션에서 열기" 링크
                    const links = document.querySelectorAll('a');
                    for (const a of links) {
                        if ((a.textContent || '').includes('프레젠테이션') || (a.href || '').includes('docs.google.com/presentation'))
                            return 'ready';
                    }
                    // 4. 로딩 중
                    const body = document.body.innerText;
                    if (body.includes('생성 중') || body.includes('generating') || body.includes('Creating')) return 'loading';
                    // 5. 에러
                    if (body.includes('생성할 수 없') || body.includes('오류')) return 'error';
                    return 'unknown';
                }''')

                if ready == 'ready':
                    print(f"\n  ✓ 슬라이드 생성 완료!")
                    break
                if ready == 'error':
                    print(f"\n  ❌ 슬라이드 생성 오류")
                    break

                elapsed = int(time.time() - start_wait)
                print(f"\r  생성 중... {elapsed}초 ({ready})", end="", flush=True)
                await asyncio.sleep(10)
            else:
                print("\n  ⏰ 타임아웃 - 현재 상태로 다운로드 시도")

            await ss(page, "05_slides_ready")
            await print_els(page, "body", "슬라이드 완료 후")

            # ── 6. PDF 다운로드 ──
            # FIX #5: 요소 덤프 기반 정확한 메뉴 찾기
            print("\n[6/6] PDF 다운로드...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = DOWNLOAD_DIR / f"provision_{timestamp}.pdf"
            downloaded = False

            # 방법 1: 슬라이드 영역의 더보기(⋮) 메뉴 → 다운로드
            all_els = await dump_elements(page, "body")
            menu_candidates = [el for el in all_els if el['tag'] == 'button' and
                              ('더보기' in el['label'] or 'more' in el['label'].lower() or
                               el['text'] == 'more_vert') and el['x'] > 800]

            for mc in reversed(menu_candidates):
                try:
                    await coord_click(page, mc, f"더보기 메뉴 ({mc['x']},{mc['y']})")
                    await asyncio.sleep(1)
                    await ss(page, "06_menu_open")

                    dl_item = await page.query_selector('[role="menuitem"]:has-text("다운로드"), [role="menuitem"]:has-text("Download")')
                    if dl_item:
                        dl_box = await dl_item.bounding_box()
                        if dl_box:
                            async with page.expect_download(timeout=60000) as dl_info:
                                await page.mouse.click(dl_box['x'] + dl_box['width']/2, dl_box['y'] + dl_box['height']/2)
                            download = await dl_info.value
                            await download.save_as(str(save_path))
                            downloaded = True
                            print(f"  ✓ 다운로드 완료: {save_path}")
                            break
                    await page.keyboard.press('Escape')
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  메뉴 시도 실패: {e}")
                    try: await page.keyboard.press('Escape')
                    except: pass

            # 방법 2: 다운로드 버튼/링크 직접
            if not downloaded:
                dl_candidates = [el for el in all_els if el['tag'] == 'button' and
                                ('다운로드' in el['text'] or 'Download' in el['text'] or
                                 '다운로드' in el['label'] or 'Download' in el['label'])]
                for dc in dl_candidates:
                    try:
                        async with page.expect_download(timeout=60000) as dl_info:
                            await coord_click(page, dc, f"다운로드: '{dc['text'][:20]}'")
                        download = await dl_info.value
                        await download.save_as(str(save_path))
                        downloaded = True
                        print(f"  ✓ 다운로드 완료: {save_path}")
                        break
                    except:
                        pass

            if not downloaded:
                print("  ⚠️ PDF 다운로드 실패")
                await ss(page, "06_download_fail")

            await ss(page, "06_final")

        except Exception as e:
            print(f"\n  ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
            await ss(page, "error")
            save_path = None
            downloaded = False

        finally:
            await ctx.close()

    return save_path if downloaded and save_path.exists() else None


# ═══════════════════════════════════════════════════
# STEP 2: Admin 폼 자동 입력 + PDF 첨부
# ═══════════════════════════════════════════════════

async def post_to_admin(pdf_path: Path, analysis: Dict[str, Any]):
    """Playwright로 Google OAuth 로그인 → Firebase ID Token 추출 → REST API로 포스트 생성"""
    import requests
    from playwright.async_api import async_playwright
    from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE

    project_id = os.getenv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'profile-28714')
    storage_bucket = os.getenv('NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET', 'profile-28714.firebasestorage.app')

    content = analysis.get("content", f"# {POST_TITLE}\n\n공사충당부채 분석 슬라이드")
    tags = list(POST_TAGS)
    for kw in analysis.get("keywords", []):
        if kw not in tags and len(kw) >= 2:
            tags.append(kw)
    tags = tags[:15]

    print("\n[Admin] Google OAuth 로그인 → REST API 포스트 생성...")

    # ── 1. Playwright: Google OAuth 로그인 + ID Token 추출 ──
    print("  1) Google OAuth 로그인...")
    id_token = None
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(AUTH_PROFILE), headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
        await asyncio.sleep(3)

        if '/auth' in page.url or 'signin' in page.url:
            google_btn = await page.query_selector('button:has-text("Google")')
            if google_btn:
                try:
                    async with ctx.expect_page(timeout=15000) as popup_info:
                        await google_btn.click()
                    popup = await popup_info.value
                    await asyncio.sleep(8)
                except:
                    await asyncio.sleep(5)

            if '/admin' not in page.url:
                await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
                await asyncio.sleep(3)

        # Firebase Auth에서 ID Token 추출 (여러 방법 시도)
        if '/admin' in page.url:
            id_token = await page.evaluate('''async () => {
                // 방법 1: localStorage에서 Firebase auth token 찾기
                try {
                    const keys = Object.keys(localStorage);
                    for (const key of keys) {
                        if (key.startsWith('firebase:authUser:')) {
                            const data = JSON.parse(localStorage.getItem(key));
                            if (data && data.stsTokenManager && data.stsTokenManager.accessToken) {
                                return data.stsTokenManager.accessToken;
                            }
                        }
                    }
                } catch {}

                // 방법 2: IndexedDB - firebaseLocalStorageDb
                try {
                    const token = await new Promise((resolve) => {
                        const req = indexedDB.open('firebaseLocalStorageDb');
                        req.onsuccess = (e) => {
                            const db = e.target.result;
                            const names = Array.from(db.objectStoreNames);
                            if (names.length === 0) { resolve(null); return; }
                            const tx = db.transaction(names[0], 'readonly');
                            const store = tx.objectStore(names[0]);
                            const getReq = store.getAll();
                            getReq.onsuccess = () => {
                                for (const item of (getReq.result || [])) {
                                    const val = item.value || item;
                                    if (val && val.stsTokenManager && val.stsTokenManager.accessToken) {
                                        resolve(val.stsTokenManager.accessToken);
                                        return;
                                    }
                                }
                                resolve(null);
                            };
                            getReq.onerror = () => resolve(null);
                        };
                        req.onerror = () => resolve(null);
                        setTimeout(() => resolve(null), 5000);
                    });
                    if (token) return token;
                } catch {}

                // 방법 3: 모든 IndexedDB 탐색
                try {
                    const dbs = await indexedDB.databases();
                    for (const dbInfo of dbs) {
                        if (!dbInfo.name) continue;
                        const token = await new Promise((resolve) => {
                            const req = indexedDB.open(dbInfo.name);
                            req.onsuccess = (e) => {
                                const db = e.target.result;
                                const names = Array.from(db.objectStoreNames);
                                for (const storeName of names) {
                                    try {
                                        const tx = db.transaction(storeName, 'readonly');
                                        const store = tx.objectStore(storeName);
                                        const getReq = store.getAll();
                                        getReq.onsuccess = () => {
                                            for (const item of (getReq.result || [])) {
                                                const val = item.value || item;
                                                if (val && val.stsTokenManager && val.stsTokenManager.accessToken) {
                                                    resolve(val.stsTokenManager.accessToken);
                                                    return;
                                                }
                                            }
                                        };
                                    } catch {}
                                }
                                setTimeout(() => resolve(null), 2000);
                            };
                            req.onerror = () => resolve(null);
                        });
                        if (token) return token;
                    }
                } catch {}

                return null;
            }''')
            if id_token:
                print(f"  ✓ ID Token 획득 ({len(id_token)}자)")
            else:
                print("  ⚠️ ID Token 추출 실패")

        await ctx.close()

    if not id_token:
        print("  ❌ ID Token 없음 → UI 자동화 폴백")
        return await post_to_admin_ui(pdf_path, analysis, content, tags)

    # ── 2. PDF 업로드 (Firebase Storage REST API) ──
    attachment_url = ''
    attachment_name = ''
    if pdf_path and pdf_path.exists():
        print(f"  2) PDF 업로드: {pdf_path.name}...")
        storage_path = f"posts/{POST_SLUG}/{pdf_path.name}"
        upload_url = f"https://firebasestorage.googleapis.com/v0/b/{storage_bucket}/o/{requests.utils.quote(storage_path, safe='')}?uploadType=media"
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        upload_resp = requests.post(upload_url, data=pdf_data, headers={
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/pdf',
        }, timeout=120)
        if upload_resp.status_code == 200:
            storage_name = upload_resp.json().get('name', storage_path)
            attachment_url = f"https://firebasestorage.googleapis.com/v0/b/{storage_bucket}/o/{requests.utils.quote(storage_name, safe='')}?alt=media"
            attachment_name = pdf_path.name
            print(f"  ✓ PDF 업로드 완료: {attachment_name}")
        else:
            print(f"  ⚠️ PDF 업로드 실패: {upload_resp.status_code} {upload_resp.text[:200]}")

    # ── 3. Firestore: 동일 slug 기존 포스트 확인 → 업데이트 또는 생성 ──
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    firestore_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/posts"

    def str_val(s): return {"stringValue": str(s)}
    def int_val(n): return {"integerValue": str(n)}
    def bool_val(b): return {"booleanValue": b}
    def ts_val(t): return {"timestampValue": t}
    def arr_val(items): return {"arrayValue": {"values": items}}

    # 기존 포스트 조회
    existing_doc_path = None
    try:
        query_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"
        q_resp = requests.post(query_url, json={
            "structuredQuery": {
                "from": [{"collectionId": "posts"}],
                "where": {"fieldFilter": {"field": {"fieldPath": "slug"}, "op": "EQUAL", "value": {"stringValue": POST_SLUG}}},
                "limit": 1,
            }
        }, headers={'Authorization': f'Bearer {id_token}', 'Content-Type': 'application/json'}, timeout=30)
        if q_resp.status_code == 200:
            for r in q_resp.json():
                doc = r.get("document")
                if doc and doc.get("name"):
                    existing_doc_path = doc["name"]
    except Exception as e:
        print(f"  ⚠️ 기존 포스트 조회 실패: {e}")

    if existing_doc_path:
        # ── 기존 포스트 업데이트 ──
        existing_doc_id = existing_doc_path.split('/')[-1]
        print(f"  3) 기존 포스트 업데이트 (ID: {existing_doc_id})...")
        update_fields = {
            "title": str_val(POST_TITLE),
            "excerpt": str_val(POST_EXCERPT),
            "content": str_val(content[:15000]),
            "category": str_val(POST_CATEGORY),
            "tags": arr_val([str_val(t) for t in tags]),
            "published": bool_val(True),
            "publishedAt": ts_val(now),
            "updatedAt": ts_val(now),
            "authorName": str_val("Sehoon Jang"),
        }
        if attachment_url:
            update_fields["attachmentUrl"] = str_val(attachment_url)
            update_fields["attachmentName"] = str_val(attachment_name)

        mask = "&".join(f"updateMask.fieldPaths={k}" for k in update_fields)
        patch_url = f"https://firestore.googleapis.com/v1/{existing_doc_path}?{mask}"
        fs_resp = requests.patch(patch_url, json={"fields": update_fields}, headers={
            'Authorization': f'Bearer {id_token}', 'Content-Type': 'application/json',
        }, timeout=60)

        if fs_resp.status_code == 200:
            print(f"  ✓ 포스트 업데이트 완료! (ID: {existing_doc_id})")
            print(f"  ✓ URL: {ADMIN_URL}/blog/{POST_SLUG}")
        else:
            print(f"  ❌ 업데이트 실패: {fs_resp.status_code} → 새로 생성 시도")
            existing_doc_path = None  # 폴백: 새 문서 생성

    if not existing_doc_path:
        # ── 새 포스트 생성 ──
        print("  3) Firestore 포스트 생성...")
        doc_fields = {
            "title": str_val(POST_TITLE),
            "slug": str_val(POST_SLUG),
            "excerpt": str_val(POST_EXCERPT),
            "content": str_val(content[:15000]),
            "category": str_val(POST_CATEGORY),
            "tags": arr_val([str_val(t) for t in tags]),
            "coverImageUrl": str_val(""),
            "published": bool_val(True),
            "publishedAt": ts_val(now),
            "createdAt": ts_val(now),
            "updatedAt": ts_val(now),
            "authorName": str_val("Sehoon Jang"),
            "commentCount": int_val(0),
            "viewCount": int_val(0),
        }
        if attachment_url:
            doc_fields["attachmentUrl"] = str_val(attachment_url)
            doc_fields["attachmentName"] = str_val(attachment_name)

        fs_resp = requests.post(firestore_url, json={"fields": doc_fields}, headers={
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/json',
        }, timeout=60)

    if fs_resp.status_code == 200:
        doc_name = fs_resp.json().get('name', '')
        doc_id = doc_name.split('/')[-1] if doc_name else 'unknown'
        print(f"  ✓ 포스트 생성 완료! (ID: {doc_id})")
        print(f"  ✓ URL: {ADMIN_URL}/blog/{POST_SLUG}")
    else:
        print(f"  ❌ 포스트 생성 실패: {fs_resp.status_code}")
        print(f"  응답: {fs_resp.text[:300]}")
        return await post_to_admin_ui(pdf_path, analysis, content, tags)


async def post_to_admin_ui(pdf_path: Path, analysis: Dict[str, Any], content: str, tags: list):
    """UI 자동화 폴백: Playwright로 Admin 폼 입력"""
    from playwright.async_api import async_playwright
    from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE

    print("\n[Admin UI 폴백] Playwright로 포스트 입력...")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(AUTH_PROFILE), headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # Google OAuth 로그인
        await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
        await asyncio.sleep(3)

        if '/auth' in page.url or 'signin' in page.url:
            google_btn = await page.query_selector('button:has-text("Google")')
            if google_btn:
                try:
                    async with ctx.expect_page(timeout=15000) as popup_info:
                        await google_btn.click()
                    popup = await popup_info.value
                    await asyncio.sleep(8)
                except:
                    await asyncio.sleep(5)

            if '/admin' not in page.url:
                await page.goto(f"{ADMIN_URL}/admin/posts/new", timeout=30000)
                await asyncio.sleep(3)

        if '/admin' not in page.url:
            print("  ❌ Admin 로그인 실패")
            await ctx.close()
            return

        # 다이얼로그 자동 닫기
        page.on('dialog', lambda d: d.dismiss())

        # 폼 입력
        await page.fill('input[placeholder*="Post title"]', POST_TITLE)
        await asyncio.sleep(0.5)
        slug_input = await page.query_selector('input[placeholder*="url-slug"], input[placeholder*="slug"]')
        if slug_input:
            await slug_input.fill('')
            await slug_input.fill(POST_SLUG)

        excerpt_area = await page.query_selector('textarea[placeholder*="Brief"]')
        if excerpt_area:
            await excerpt_area.fill(POST_EXCERPT)

        fin_btn = await page.query_selector('button:has-text("Finance")')
        if fin_btn:
            await fin_btn.click()

        tag_input = await page.query_selector('input[placeholder*="Add tag"]')
        if tag_input:
            for tag in tags:
                await tag_input.fill(tag)
                await tag_input.press('Enter')
                await asyncio.sleep(0.2)

        content_area = await page.query_selector('textarea[placeholder*="Markdown"], textarea[placeholder*="Write"]')
        if content_area:
            await content_area.fill(content[:8000])

        await ss(page, "admin_03_filled")

        # 콘솔 로그 캡처
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on('dialog', lambda d: asyncio.ensure_future(d.dismiss()))

        # Publish: React state 경합 우회 + 디버그
        result = await page.evaluate('''async () => {
            const logs = [];
            try {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Publish');
                const form = document.querySelector('form');
                if (!btn || !form) return {ok: false, err: 'no btn/form'};

                logs.push('btn found: ' + btn.type + ', form found');

                // form submit 이벤트를 한 번 차단 (onClick만 실행되도록)
                let submitBlocked = false;
                const blocker = (e) => { e.preventDefault(); e.stopImmediatePropagation(); submitBlocked = true; };
                form.addEventListener('submit', blocker, {capture: true, once: true});

                // 클릭: onClick → published=true, submit은 차단됨
                btn.click();
                logs.push('clicked, submitBlocked=' + submitBlocked);

                // React state 업데이트 대기 (500ms + microtask)
                await new Promise(r => setTimeout(r, 500));
                logs.push('waited 500ms');

                // Publish 버튼으로 제출 (type=submit이므로 form.submit 트리거)
                btn.click();
                logs.push('second click done');

                // 대기
                await new Promise(r => setTimeout(r, 3000));
                logs.push('final URL: ' + window.location.href);

                return {ok: true, logs: logs};
            } catch (e) {
                return {ok: false, err: e.message, logs: logs};
            }
        }''')
        print(f"  Publish 결과: {result}")
        await asyncio.sleep(8)
        print(f"  현재 URL: {page.url}")

        # 콘솔 로그 출력
        if console_logs:
            print(f"  콘솔 로그 ({len(console_logs)}개):")
            for log in console_logs[-10:]:
                print(f"    {log[:100]}")

        await ss(page, "admin_04_published")
        await ctx.close()
    print(f"  ✓ 포스트: {ADMIN_URL}/blog/{POST_SLUG}")


# ═══════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="공사충당부채 파이프라인")
    parser.add_argument("--pdf", "-p", help="기존 PDF 사용 (NotebookLM 건너뛰기)")
    parser.add_argument("--skip-post", action="store_true", help="Admin 포스팅 건너뛰기")
    args = parser.parse_args()

    start_time = time.time()
    print("\n" + "=" * 60)
    print("  공사충당부채 전체 파이프라인")
    print("=" * 60)
    print(f"  제목:   {POST_TITLE}")
    print(f"  디자인: 파이낸스 (#21)")
    print(f"  Admin:  {ADMIN_URL}/admin/posts/new")
    print("=" * 60)

    # ── NotebookLM → PDF ──
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"  ❌ PDF 없음: {pdf_path}")
            return 1
        print(f"\n  기존 PDF: {pdf_path}")
    else:
        pdf_path = await run_notebooklm()

    if not pdf_path or not pdf_path.exists():
        print("\n  ❌ PDF 없음 - Admin 포스팅 건너뜀")
        return 1

    # ── PDF 분석 ──
    print(f"\n[PDF 분석] {pdf_path}")
    analyzer = PDFAnalyzer(pdf_path)
    try:
        analysis = analyzer.analyze()
    finally:
        analyzer.close()

    # ── Admin 포스트 ──
    if not args.skip_post:
        await post_to_admin(pdf_path, analysis)

    elapsed = int(time.time() - start_time)
    print("\n" + "=" * 60)
    print("  파이프라인 완료!")
    print("=" * 60)
    print(f"  PDF:      {pdf_path}")
    print(f"  슬라이드: {analysis['page_count']}장")
    print(f"  포스트:   {ADMIN_URL}/blog/{POST_SLUG}")
    print(f"  소요시간: {elapsed}초")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
