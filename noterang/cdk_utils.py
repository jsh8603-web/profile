"""
CDK 오버레이 유틸리티 — NotebookLM (Angular Material) 자동화용

NotebookLM은 Angular Material + CDK overlay를 사용하므로
일반 `.click()`이 차단됩니다.  반드시 bounding_box → mouse.click 좌표 클릭 패턴을 사용해야 합니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

# 기본 디버그 스크린샷 디렉터리 (호출자가 override 가능)
_DEFAULT_DEBUG_DIR = Path("G:/내 드라이브/notebooklm_automation/debug_screenshots")


async def ss(page, name: str, debug_dir: Path | None = None) -> str:
    """타임스탬프 스크린샷 저장."""
    d = debug_dir or _DEFAULT_DEBUG_DIR
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = str(d / f"{ts}_{name}.png")
    await page.screenshot(path=path)
    print(f"  📸 {name}")
    return path


async def dump_elements(page, scope: str = "body") -> list[dict[str, Any]]:
    """페이지/오버레이 내 클릭 가능한 요소 덤프."""
    return await page.evaluate(
        """(scope) => {
        const root = scope === 'overlay'
            ? document.querySelector('.cdk-overlay-pane') || document.body
            : document.querySelector(scope) || document.body;
        const els = root.querySelectorAll('button, input, textarea, [role="tab"], [role="button"], [role="menuitem"], a, [contenteditable="true"]');
        const result = [];
        for (let i = 0; i < els.length; i++) {
            const el = els[i];
            if (el.offsetParent === null && el.type !== 'file') continue;
            const rect = el.getBoundingClientRect();
            result.push({
                idx: i, tag: el.tagName.toLowerCase(), type: el.type || '',
                text: (el.textContent || '').trim().substring(0, 60),
                label: el.getAttribute('aria-label') || '',
                placeholder: el.placeholder || '',
                disabled: el.disabled || false,
                x: Math.round(rect.x), y: Math.round(rect.y),
                w: Math.round(rect.width), h: Math.round(rect.height),
            });
        }
        return result;
    }""",
        scope,
    )


async def print_els(page, scope: str = "body", label: str = "") -> list[dict]:
    """요소 목록 출력."""
    els = await dump_elements(page, scope)
    print(f"\n  --- {label or scope} ({len(els)}개) ---")
    for el in els:
        d = " [DISABLED]" if el["disabled"] else ""
        print(
            f"  [{el['idx']}] {el['tag']} text='{el['text'][:35]}' label='{el['label'][:25]}'"
            f" ph='{el['placeholder'][:25]}' ({el['x']},{el['y']} {el['w']}x{el['h']}){d}"
        )
    print("  ---\n")
    return els


async def coord_click(page, box_or_el, description: str = "") -> bool:
    """좌표 기반 다이렉트 마우스 클릭 (CDK overlay 우회).

    *box_or_el* 은 ``{x, y, w, h}`` dict 또는 Playwright ElementHandle.
    """
    if isinstance(box_or_el, dict):
        cx = box_or_el["x"] + box_or_el["w"] / 2
        cy = box_or_el["y"] + box_or_el["h"] / 2
    else:
        box = await box_or_el.bounding_box()
        if not box:
            print(f"  ✗ bbox 없음: {description}")
            return False
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
    await page.mouse.click(cx, cy)
    print(f"  ✓ 클릭: {description} ({cx:.0f},{cy:.0f})")
    return True


async def overlay_find_and_click(page, text_match: str, description: str = "") -> bool:
    """오버레이 내 텍스트로 요소 찾아 좌표 클릭."""
    box = await page.evaluate(
        """(text) => {
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
    }""",
        text_match,
    )
    if box:
        await coord_click(page, box, description or text_match)
        return True
    print(f"  ✗ '{text_match}' 없음")
    return False


async def overlay_find_inputs(page) -> list[dict]:
    """오버레이 내 visible input/textarea 좌표 목록."""
    return await page.evaluate(
        """() => {
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
    }"""
    )


async def overlay_click_insert(page) -> bool:
    """오버레이 내 '삽입' 버튼 좌표 클릭."""
    box = await page.evaluate(
        """() => {
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
    }"""
    )
    if box:
        await coord_click(page, box, f"삽입: '{box['text'][:20]}'")
        return True
    print("  ✗ 삽입 버튼 없음/비활성")
    return False
