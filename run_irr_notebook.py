#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IRR 노트북 생성 파이프라인
- 스크린샷으로 UI 상태 확인
- bounding_box 좌표 + mouse.click() 다이렉트 클릭 (CDK overlay 우회)
- JS focus + keyboard.type() 텍스트 입력
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime

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

# IRR 관련 검색 소스
IRR_SOURCES = [
    "https://ko.wikipedia.org/wiki/%EB%82%B4%EB%B6%80%EC%88%98%EC%9D%B5%EB%A5%A0",
    "https://en.wikipedia.org/wiki/Internal_rate_of_return",
]

IRR_SEARCH_QUERIES = [
    "IRR 내부수익률 투자분석 계산방법",
    "Internal Rate of Return NPV 비교",
]


async def screenshot(page, name: str) -> str:
    """스크린샷 저장 + 경로 반환"""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%H%M%S')
    path = str(DEBUG_DIR / f"{ts}_{name}.png")
    await page.screenshot(path=path)
    print(f"  📸 {name}")
    return path


async def direct_click(page, selector: str, description: str = "") -> bool:
    """
    bounding_box 좌표 기반 다이렉트 마우스 클릭
    CDK overlay를 우회하여 정확한 좌표에 클릭
    """
    el = await page.query_selector(selector)
    if not el:
        print(f"  ✗ 요소 없음: {description or selector}")
        return False

    box = await el.bounding_box()
    if not box:
        print(f"  ✗ bounding_box 없음: {description or selector}")
        return False

    cx = box['x'] + box['width'] / 2
    cy = box['y'] + box['height'] / 2
    await page.mouse.click(cx, cy)
    print(f"  ✓ 클릭: {description or selector} ({cx:.0f}, {cy:.0f})")
    return True


async def direct_click_text(page, text: str, tag: str = "*") -> bool:
    """
    텍스트를 포함하는 요소를 JS로 찾고, bounding_box로 다이렉트 클릭
    """
    box = await page.evaluate(f'''(text) => {{
        const els = document.querySelectorAll('{tag}');
        for (const el of els) {{
            if (el.offsetParent === null) continue;
            const t = (el.textContent || '').trim();
            if (t.includes(text) && t.length < text.length + 30) {{
                const rect = el.getBoundingClientRect();
                return {{x: rect.x, y: rect.y, width: rect.width, height: rect.height}};
            }}
        }}
        return null;
    }}''', text)

    if not box:
        print(f"  ✗ 텍스트 없음: '{text}'")
        return False

    cx = box['x'] + box['width'] / 2
    cy = box['y'] + box['height'] / 2
    await page.mouse.click(cx, cy)
    print(f"  ✓ 클릭: '{text}' ({cx:.0f}, {cy:.0f})")
    return True


async def focus_and_type(page, selector_or_js: str, text: str, use_js: bool = False) -> bool:
    """
    JS로 요소에 focus → keyboard.type()로 입력
    CDK overlay 내 input에도 동작
    """
    if use_js:
        # JS로 focus
        focused = await page.evaluate(f'''() => {{
            {selector_or_js}
        }}''')
        if not focused:
            print(f"  ✗ JS focus 실패")
            return False
    else:
        el = await page.query_selector(selector_or_js)
        if not el:
            print(f"  ✗ 요소 없음: {selector_or_js}")
            return False
        # bounding_box 클릭으로 focus (overlay 우회)
        box = await el.bounding_box()
        if box:
            await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        else:
            await page.evaluate('(el) => el.focus()', el)

    await asyncio.sleep(0.3)
    # 기존 텍스트 삭제
    await page.keyboard.press('Control+A')
    await asyncio.sleep(0.1)
    await page.keyboard.type(text, delay=30)
    print(f"  ✓ 입력: '{text[:50]}...' " if len(text) > 50 else f"  ✓ 입력: '{text}'")
    return True


async def dump_page_elements(page, scope: str = "body") -> list:
    """
    현재 페이지의 클릭 가능한 요소들을 덤프 (디버깅용)
    """
    elements = await page.evaluate(f'''(scope) => {{
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
                idx: i,
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                text: (el.textContent || '').trim().substring(0, 60),
                label: el.getAttribute('aria-label') || '',
                placeholder: el.placeholder || '',
                disabled: el.disabled || false,
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                w: Math.round(rect.width),
                h: Math.round(rect.height),
            }});
        }}
        return result;
    }}''', scope)

    return elements


async def print_elements(page, scope: str = "body", label: str = ""):
    """요소 목록 출력"""
    els = await dump_page_elements(page, scope)
    print(f"\n  --- {label or scope} 요소 ({len(els)}개) ---")
    for el in els:
        icon = "🔘" if el['tag'] == 'button' else "📝" if el['tag'] == 'input' else "📋" if el['tag'] == 'textarea' else "🔗"
        disabled = " [DISABLED]" if el['disabled'] else ""
        print(f"  {icon} [{el['idx']}] {el['tag']}"
              f" text='{el['text'][:40]}'"
              f" label='{el['label'][:30]}'"
              f" ph='{el['placeholder'][:30]}'"
              f" ({el['x']},{el['y']} {el['w']}x{el['h']}){disabled}")
    print(f"  --- end ---\n")
    return els


async def click_element_by_index(page, elements: list, idx: int, description: str = "") -> bool:
    """dump된 요소 목록에서 인덱스로 다이렉트 클릭"""
    el = None
    for e in elements:
        if e['idx'] == idx:
            el = e
            break
    if not el:
        print(f"  ✗ 인덱스 {idx} 없음")
        return False

    cx = el['x'] + el['w'] / 2
    cy = el['y'] + el['h'] / 2
    await page.mouse.click(cx, cy)
    print(f"  ✓ 클릭 [{idx}]: {description or el['text'][:30]} ({cx:.0f}, {cy:.0f})")
    return True


# ─── 메인 파이프라인 ───

async def create_irr_notebook():
    """NotebookLM에서 IRR 노트북 생성 + 소스 추가"""
    from playwright.async_api import async_playwright
    from noterang.auto_login import full_auto_login, BROWSER_PROFILE as AUTH_PROFILE

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  IRR 노트북 생성 파이프라인")
    print("  (스크린샷 확인 + 다이렉트 클릭)")
    print("=" * 60)

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
            # ══════════════════════════════════════════
            # STEP 1: 로그인
            # ══════════════════════════════════════════
            print("\n[STEP 1] 로그인 확인...")
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(3)
            await screenshot(page, "01_initial")

            if 'accounts.google.com' in page.url:
                print("  로그인 필요 → full_auto_login 실행")
                await ctx.close()
                success = await full_auto_login(headless=False)
                if not success:
                    print("  ❌ 로그인 실패")
                    return False
                # 재연결
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
            await screenshot(page, "02_logged_in")

            # ══════════════════════════════════════════
            # STEP 2: 노트북 생성
            # ══════════════════════════════════════════
            print("\n[STEP 2] 새 노트북 생성...")

            # 메인 페이지 요소 확인
            await print_elements(page, "body", "메인 페이지")

            created = await direct_click(page, '[aria-label="새 노트 만들기"]', "새 노트 만들기")
            if not created:
                created = await direct_click_text(page, "새로 만들기", "button")
            if not created:
                created = await direct_click_text(page, "New notebook", "button")

            await asyncio.sleep(5)
            await screenshot(page, "03_after_create")

            url = page.url
            if '/notebook/' not in url:
                print(f"  ❌ 노트북 생성 실패: {url}")
                await ctx.close()
                return False

            notebook_id = url.split('/notebook/')[-1].split('/')[0].split('?')[0]
            print(f"  ✓ 노트북 생성 완료: {notebook_id}")

            # ══════════════════════════════════════════
            # STEP 3: 소스 추가 (다이얼로그)
            # ══════════════════════════════════════════
            print("\n[STEP 3] 소스 추가...")
            await asyncio.sleep(3)

            # 다이얼로그가 자동으로 열림 (?addSource=true)
            await screenshot(page, "04_source_dialog")

            # 오버레이 내부 요소 확인
            overlay_els = await print_elements(page, "overlay", "소스 추가 다이얼로그")

            # ── 3a: 검색바로 IRR 소스 검색 ──
            source_count = 0

            # 검색바 찾기: 오버레이 내 input 또는 textarea 중 visible한 것
            search_input_info = None
            for el in overlay_els:
                if el['tag'] in ('input', 'textarea') and not el['disabled'] and el['w'] > 100:
                    search_input_info = el
                    break

            if search_input_info:
                print(f"\n  검색바 발견: placeholder='{search_input_info['placeholder']}' ({search_input_info['x']},{search_input_info['y']})")

                for qi, query in enumerate(IRR_SEARCH_QUERIES):
                    print(f"\n  --- 검색 {qi+1}: '{query}' ---")

                    # 검색바 클릭 (좌표 다이렉트)
                    cx = search_input_info['x'] + search_input_info['w'] / 2
                    cy = search_input_info['y'] + search_input_info['h'] / 2
                    await page.mouse.click(cx, cy)
                    await asyncio.sleep(0.5)

                    # 기존 텍스트 삭제 + 새 검색어 입력
                    await page.keyboard.press('Control+A')
                    await asyncio.sleep(0.1)
                    await page.keyboard.type(query, delay=30)
                    await asyncio.sleep(0.5)
                    await screenshot(page, f"05_search_typed_{qi}")

                    # Enter로 검색 실행
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(8)
                    await screenshot(page, f"06_search_results_{qi}")

                    # 검색 결과 확인
                    result_els = await print_elements(page, "overlay", f"검색 결과 {qi+1}")

                    # 체크박스/결과 항목 선택 (좌표 클릭)
                    selected = 0
                    for el in result_els:
                        # 체크박스 또는 선택 가능한 결과 항목
                        if (el['tag'] == 'input' and el['type'] == 'checkbox') or \
                           (el['label'] and ('선택' in el['label'] or 'select' in el['label'].lower())):
                            rcx = el['x'] + el['w'] / 2
                            rcy = el['y'] + el['h'] / 2
                            await page.mouse.click(rcx, rcy)
                            selected += 1
                            print(f"  ✓ 결과 선택 [{el['idx']}]: {el['text'][:40]} ({rcx:.0f},{rcy:.0f})")
                            await asyncio.sleep(0.5)
                            if selected >= 3:
                                break

                    # mat-checkbox 시도 (Angular Material)
                    if selected == 0:
                        checkbox_boxes = await page.evaluate('''() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return [];
                            const cbs = pane.querySelectorAll('mat-checkbox, .mat-checkbox, [role="checkbox"], .mdc-checkbox');
                            const result = [];
                            for (const cb of cbs) {
                                if (cb.offsetParent === null) continue;
                                const rect = cb.getBoundingClientRect();
                                result.push({x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: cb.textContent.trim().substring(0, 50)});
                            }
                            return result;
                        }''')
                        print(f"  mat-checkbox 발견: {len(checkbox_boxes)}개")
                        for cb in checkbox_boxes[:3]:
                            cbx = cb['x'] + cb['w'] / 2
                            cby = cb['y'] + cb['h'] / 2
                            await page.mouse.click(cbx, cby)
                            selected += 1
                            print(f"  ✓ 체크박스 클릭: {cb['text'][:40]} ({cbx:.0f},{cby:.0f})")
                            await asyncio.sleep(0.5)

                    # 결과 카드/리스트 아이템 클릭 시도
                    if selected == 0:
                        card_boxes = await page.evaluate('''() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return [];
                            const items = pane.querySelectorAll('[class*="result"], [class*="source"], [class*="item"], [class*="card"], li');
                            const result = [];
                            for (const item of items) {
                                if (item.offsetParent === null) continue;
                                const rect = item.getBoundingClientRect();
                                if (rect.height > 20 && rect.width > 100) {
                                    result.push({x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: item.textContent.trim().substring(0, 60)});
                                }
                            }
                            return result;
                        }''')
                        print(f"  결과 카드 발견: {len(card_boxes)}개")
                        for card in card_boxes[:3]:
                            cardx = card['x'] + card['w'] / 2
                            cardy = card['y'] + card['h'] / 2
                            await page.mouse.click(cardx, cardy)
                            selected += 1
                            print(f"  ✓ 카드 클릭: {card['text'][:40]} ({cardx:.0f},{cardy:.0f})")
                            await asyncio.sleep(0.5)

                    if selected > 0:
                        await screenshot(page, f"07_selected_{qi}")
                        await asyncio.sleep(1)

                        # "삽입" / "추가" 버튼 클릭 (좌표)
                        insert_els = await dump_page_elements(page, "overlay")
                        for el in insert_els:
                            if el['tag'] == 'button' and not el['disabled']:
                                t = el['text'].lower()
                                l = el['label'].lower()
                                if '삽입' in t or 'insert' in t or '추가' in el['text'] or \
                                   '제출' in l or 'submit' in l:
                                    ibx = el['x'] + el['w'] / 2
                                    iby = el['y'] + el['h'] / 2
                                    await page.mouse.click(ibx, iby)
                                    print(f"  ✓ 삽입 클릭: '{el['text'][:30]}' ({ibx:.0f},{iby:.0f})")
                                    source_count += selected
                                    await asyncio.sleep(10)
                                    break

                        await screenshot(page, f"08_after_insert_{qi}")

                    if source_count >= 3:
                        break

                    # 다음 검색을 위해 검색바로 돌아가기
                    if qi < len(IRR_SEARCH_QUERIES) - 1 and source_count == 0:
                        await asyncio.sleep(2)

            # ── 3b: 검색 실패 시 URL 직접 입력 시도 ──
            if source_count == 0:
                print("\n  검색 방식 실패 → URL 직접 입력 시도...")
                await screenshot(page, "09_before_url")

                # 오버레이 요소 다시 확인
                overlay_els = await print_elements(page, "overlay", "URL 입력 전")

                # "웹사이트" 탭 찾기 + 좌표 클릭
                website_box = await page.evaluate('''() => {
                    const pane = document.querySelector('.cdk-overlay-pane');
                    if (!pane) return null;
                    const els = pane.querySelectorAll('button, [role="tab"], span, div');
                    for (const el of els) {
                        const t = (el.textContent || '').trim();
                        if ((t === '웹사이트' || t === 'Website') && el.offsetParent !== null) {
                            const rect = el.getBoundingClientRect();
                            return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
                        }
                    }
                    return null;
                }''')

                if website_box:
                    wx = website_box['x'] + website_box['w'] / 2
                    wy = website_box['y'] + website_box['h'] / 2
                    await page.mouse.click(wx, wy)
                    print(f"  ✓ '웹사이트' 탭 클릭 ({wx:.0f},{wy:.0f})")
                    await asyncio.sleep(2)
                    await screenshot(page, "10_website_tab")

                    # URL 입력 필드 확인
                    overlay_els = await print_elements(page, "overlay", "웹사이트 탭")

                for ui, irr_url in enumerate(IRR_SOURCES):
                    print(f"\n  URL {ui+1}/{len(IRR_SOURCES)}: {irr_url[:60]}...")

                    # 두 번째 URL부터: 소스 추가 다이얼로그 다시 열기
                    if ui > 0:
                        # "소스 추가" 버튼 클릭
                        add_src = await page.query_selector('[aria-label="출처 추가"], [aria-label*="소스 추가"], [aria-label*="Add source"]')
                        if add_src:
                            box = await add_src.bounding_box()
                            if box:
                                await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                                await asyncio.sleep(3)
                        # "웹사이트" 탭 다시 클릭
                        website_box2 = await page.evaluate('''() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return null;
                            const els = pane.querySelectorAll('button, [role="tab"], span, div');
                            for (const el of els) {
                                const t = (el.textContent || '').trim();
                                if ((t === '웹사이트' || t === 'Website' || t.includes('웹사이트')) && el.offsetParent !== null) {
                                    const rect = el.getBoundingClientRect();
                                    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
                                }
                            }
                            return null;
                        }''')
                        if website_box2:
                            await page.mouse.click(website_box2['x'] + website_box2['w'] / 2, website_box2['y'] + website_box2['h'] / 2)
                            await asyncio.sleep(2)

                    # 오버레이 내 모든 visible input/textarea 좌표 가져오기
                    input_boxes = await page.evaluate('''() => {
                        const pane = document.querySelector('.cdk-overlay-pane');
                        if (!pane) return [];
                        const inputs = pane.querySelectorAll('input, textarea');
                        const result = [];
                        for (const inp of inputs) {
                            if (inp.offsetParent === null) continue;
                            if (inp.type === 'hidden' || inp.type === 'checkbox' || inp.type === 'radio') continue;
                            const rect = inp.getBoundingClientRect();
                            result.push({
                                x: rect.x, y: rect.y, w: rect.width, h: rect.height,
                                placeholder: inp.placeholder || '', type: inp.type || 'text'
                            });
                        }
                        return result;
                    }''')

                    print(f"  visible input 수: {len(input_boxes)}")
                    for ib in input_boxes:
                        print(f"    input: type={ib['type']} ph='{ib['placeholder'][:40]}' ({ib['x']},{ib['y']} {ib['w']}x{ib['h']})")

                    if input_boxes:
                        # 첫 번째 visible input에 좌표 클릭 → 타이핑
                        ib = input_boxes[0]
                        ix = ib['x'] + ib['w'] / 2
                        iy = ib['y'] + ib['h'] / 2
                        await page.mouse.click(ix, iy)
                        await asyncio.sleep(0.3)
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type(irr_url, delay=15)
                        print(f"  ✓ URL 타이핑 완료")
                        await asyncio.sleep(1)
                        await screenshot(page, f"11_url_typed_{ui}")

                        # Enter 또는 삽입 버튼
                        await page.keyboard.press('Enter')
                        await asyncio.sleep(3)

                        # 삽입 버튼 좌표 클릭
                        insert_box = await page.evaluate('''() => {
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

                        if insert_box:
                            ibx = insert_box['x'] + insert_box['w'] / 2
                            iby = insert_box['y'] + insert_box['h'] / 2
                            await page.mouse.click(ibx, iby)
                            print(f"  ✓ 삽입 버튼: '{insert_box['text'][:20]}' ({ibx:.0f},{iby:.0f})")
                            source_count += 1
                            await asyncio.sleep(10)
                            await screenshot(page, f"12_url_inserted_{ui}")
                        else:
                            print("  삽입 버튼 없음")
                            await screenshot(page, f"12_no_insert_btn_{ui}")

            # ── 3c: 최후수단 - "복사된 텍스트" 탭으로 직접 텍스트 붙여넣기 ──
            if source_count == 0:
                print("\n  URL 입력도 실패 → '복사된 텍스트'로 직접 텍스트 소스 추가...")

                paste_box = await page.evaluate('''() => {
                    const pane = document.querySelector('.cdk-overlay-pane');
                    if (!pane) return null;
                    const els = pane.querySelectorAll('button, [role="tab"], span, div');
                    for (const el of els) {
                        const t = (el.textContent || '').trim();
                        if ((t === '복사된 텍스트' || t === 'Copied text' || t.includes('Paste')) && el.offsetParent !== null) {
                            const rect = el.getBoundingClientRect();
                            return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
                        }
                    }
                    return null;
                }''')

                if paste_box:
                    px = paste_box['x'] + paste_box['w'] / 2
                    py = paste_box['y'] + paste_box['h'] / 2
                    await page.mouse.click(px, py)
                    print(f"  ✓ '복사된 텍스트' 탭 클릭 ({px:.0f},{py:.0f})")
                    await asyncio.sleep(2)
                    await screenshot(page, "13_paste_tab")

                    # textarea 찾기
                    textarea_boxes = await page.evaluate('''() => {
                        const pane = document.querySelector('.cdk-overlay-pane');
                        if (!pane) return [];
                        const areas = pane.querySelectorAll('textarea, [contenteditable="true"]');
                        const result = [];
                        for (const a of areas) {
                            if (a.offsetParent === null) continue;
                            const rect = a.getBoundingClientRect();
                            result.push({x: rect.x, y: rect.y, w: rect.width, h: rect.height});
                        }
                        return result;
                    }''')

                    irr_text = """IRR (Internal Rate of Return, 내부수익률)

내부수익률(IRR)은 투자 프로젝트의 순현재가치(NPV)를 0으로 만드는 할인율을 말합니다. 투자의 수익성을 평가하는 핵심 재무지표입니다.

## IRR의 정의
IRR은 투자로부터 발생하는 현금흐름의 현재가치 합이 초기 투자비용과 같아지는 할인율입니다.
수식: NPV = Σ(CFt / (1+IRR)^t) - C0 = 0

## IRR의 특징
1. NPV = 0이 되는 할인율
2. 프로젝트의 기대수익률을 나타냄
3. 자본비용(WACC)과 비교하여 투자 의사결정
4. IRR > WACC → 투자 채택
5. IRR < WACC → 투자 기각

## IRR vs NPV 비교
- NPV: 절대적 가치(금액) 제공, 프로젝트 규모 반영
- IRR: 상대적 수익률(%) 제공, 직관적 이해 용이
- 상호배타적 프로젝트에서는 NPV 우선 사용 권장

## IRR의 계산 방법
1. 시행착오법 (Trial and Error)
2. 보간법 (Interpolation)
3. Excel IRR() 함수
4. 뉴턴-랩슨 방법 (Newton-Raphson Method)

## IRR의 한계점
1. 비정상적 현금흐름 시 복수의 IRR 존재 가능
2. 상호배타적 프로젝트 비교에 부적합
3. 재투자 가정의 비현실성 (Modified IRR로 보완)
4. 프로젝트 규모 차이 무시

## 수정내부수익률 (MIRR)
기존 IRR의 재투자율 가정 문제를 해결한 지표입니다.
자금조달비용으로 음의 현금흐름을, 재투자수익률로 양의 현금흐름을 계산합니다.

## 실무 활용
- 부동산 투자 분석
- 기업 자본예산 편성
- 벤처 캐피탈 투자 평가
- 채권 수익률(YTM) 계산
"""

                    if textarea_boxes:
                        ta = textarea_boxes[0]
                        tax = ta['x'] + ta['w'] / 2
                        tay = ta['y'] + ta['h'] / 2
                        await page.mouse.click(tax, tay)
                        await asyncio.sleep(0.3)
                        await page.keyboard.type(irr_text, delay=5)
                        print(f"  ✓ IRR 텍스트 입력 완료 ({len(irr_text)}자)")
                        await asyncio.sleep(1)
                        await screenshot(page, "14_text_pasted")

                        # 소스 이름 입력 (있으면)
                        name_inputs = await page.evaluate('''() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return [];
                            const inputs = pane.querySelectorAll('input[type="text"], input:not([type])');
                            const result = [];
                            for (const inp of inputs) {
                                if (inp.offsetParent === null) continue;
                                const rect = inp.getBoundingClientRect();
                                result.push({x: rect.x, y: rect.y, w: rect.width, h: rect.height, ph: inp.placeholder || ''});
                            }
                            return result;
                        }''')

                        for ni in name_inputs:
                            if 'source' in ni['ph'].lower() or '소스' in ni['ph'] or '이름' in ni['ph'] or 'name' in ni['ph'].lower():
                                nix = ni['x'] + ni['w'] / 2
                                niy = ni['y'] + ni['h'] / 2
                                await page.mouse.click(nix, niy)
                                await asyncio.sleep(0.2)
                                await page.keyboard.type("IRR 내부수익률 분석", delay=30)
                                break

                        # 삽입 버튼 클릭
                        insert_box = await page.evaluate('''() => {
                            const pane = document.querySelector('.cdk-overlay-pane');
                            if (!pane) return null;
                            const btns = pane.querySelectorAll('button');
                            for (const b of btns) {
                                const t = (b.textContent || '').trim();
                                const l = b.getAttribute('aria-label') || '';
                                if ((t.includes('삽입') || t.includes('Insert') || l.includes('제출')) &&
                                    b.offsetParent !== null && !b.disabled) {
                                    const rect = b.getBoundingClientRect();
                                    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height, text: t};
                                }
                            }
                            return null;
                        }''')

                        if insert_box:
                            ibx = insert_box['x'] + insert_box['w'] / 2
                            iby = insert_box['y'] + insert_box['h'] / 2
                            await page.mouse.click(ibx, iby)
                            print(f"  ✓ 삽입: '{insert_box['text'][:20]}' ({ibx:.0f},{iby:.0f})")
                            source_count += 1
                            await asyncio.sleep(10)
                            await screenshot(page, "15_text_inserted")

            # ══════════════════════════════════════════
            # STEP 4: 제목 설정 + 소스 처리 대기
            # ══════════════════════════════════════════
            print(f"\n[STEP 4] 마무리 (소스 {source_count}개 추가됨)")

            # 다이얼로그 닫기
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)

            # 노트북 제목 변경
            title_el = await page.query_selector('[contenteditable="true"]')
            if title_el:
                box = await title_el.bounding_box()
                if box:
                    await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    await asyncio.sleep(0.5)
                    await page.keyboard.press('Control+A')
                    await page.keyboard.type("IRR - 내부수익률 분석", delay=30)
                    await page.keyboard.press('Tab')
                    await asyncio.sleep(1)
                    print("  ✓ 제목: IRR - 내부수익률 분석")

            if source_count > 0:
                print("  소스 처리 대기 (30초)...")
                await asyncio.sleep(30)

            await screenshot(page, "16_final")

            # ══════════════════════════════════════════
            # 결과
            # ══════════════════════════════════════════
            print("\n" + "=" * 60)
            if source_count > 0:
                print(f"  ✓ IRR 노트북 생성 완료! (소스 {source_count}개)")
            else:
                print("  ⚠️ 노트북 생성됨, 소스 추가는 수동 필요")
            print(f"  ID:  {notebook_id}")
            print(f"  URL: https://notebooklm.google.com/notebook/{notebook_id}")
            print(f"  스크린샷: {DEBUG_DIR}")
            print("=" * 60)

        except Exception as e:
            print(f"\n  ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
            await screenshot(page, "error")

        finally:
            await ctx.close()

    return source_count > 0


if __name__ == "__main__":
    result = asyncio.run(create_irr_notebook())
    sys.exit(0 if result else 1)
