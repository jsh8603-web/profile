#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 완전 자동 로그인 모듈
- Google 2FA TOTP 자동 생성
- 브라우저 자동화로 NotebookLM 로그인
"""
import asyncio
import os
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import pyotp
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# .env.local 파일 로드
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

# 인증 정보 (환경 변수에서 로드)
EMAIL = os.getenv('GOOGLE_EMAIL', '')
PASSWORD = os.getenv('GOOGLE_PASSWORD', '')
TOTP_SECRET = os.getenv('GOOGLE_2FA_SECRET', '')
APP_PASSWORD = os.getenv('NOTEBOOKLM_APP_PASSWORD', '')
APIFY_API_KEY = os.getenv('APIFY_API_KEY', '')

# 브라우저 프로필 경로
BROWSER_PROFILE = Path.home() / '.notebooklm-auto-v3'


def get_totp_code() -> str:
    """현재 TOTP 코드 생성"""
    totp = pyotp.TOTP(TOTP_SECRET.upper())
    return totp.now()


async def _try_select_otp(page):
    """OTP/Authenticator 옵션을 찾아 클릭하고 TOTP 입력 필드를 반환"""
    # 1. data-challengetype="6" (TOTP) 직접 탐색
    otp_selectors = [
        '[data-challengetype="6"]',
        'li:has-text("Google Authenticator")',
        'li:has-text("Google OTP")',
        'li:has-text("인증 앱")',
        'li:has-text("Authenticator")',
        'div[role="link"]:has-text("Authenticator")',
        'div[role="link"]:has-text("OTP")',
    ]

    for selector in otp_selectors:
        try:
            elem = await page.query_selector(selector)
            if elem:
                text = (await elem.inner_text()).strip()
                # 전화/SMS 옵션은 건너뛰기
                if any(skip in text for skip in ['전화', 'phone', 'SMS', '문자']):
                    continue
                await elem.click()
                print(f"  ✓ OTP 선택 (selector): {text[:50]}")
                await asyncio.sleep(4)
                break
        except:
            continue
    else:
        # 2. 텍스트 매칭으로 시도
        for kw in ['Google Authenticator', 'Google OTP', '인증 앱', 'Authenticator']:
            try:
                await page.click(f'text={kw}', timeout=2000)
                print(f"  ✓ OTP 선택 (text): {kw}")
                await asyncio.sleep(4)
                break
            except:
                continue

    # TOTP 입력 필드 대기
    try:
        totp_input = await page.wait_for_selector(
            'input[name="totpPin"], input[id="totpPin"], input[type="tel"], input[autocomplete="one-time-code"]',
            timeout=10000
        )
        return totp_input
    except:
        return None


async def full_auto_login(headless: bool = False) -> bool:
    """
    완전 자동 로그인

    Args:
        headless: True면 백그라운드 실행

    Returns:
        로그인 성공 여부
    """
    print("=" * 50)
    print("NotebookLM 완전 자동 로그인")
    print("=" * 50)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
            viewport={'width': 1280, 'height': 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # 1. NotebookLM 접속
        print("\n[1/4] NotebookLM 접속...")
        await page.goto('https://notebooklm.google.com/', timeout=60000)
        await asyncio.sleep(3)

        # 이미 로그인된 경우
        if 'notebooklm.google.com' in page.url and 'accounts' not in page.url:
            print("  ✓ 이미 로그인되어 있습니다.")
            await context.close()
            return True

        # 2. 이메일 입력
        if 'accounts.google.com' in page.url:
            print("[2/4] 이메일 입력...")
            try:
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.fill('input[type="email"]', EMAIL)
                await page.click('#identifierNext')
                await asyncio.sleep(4)
                print("  ✓ 이메일 입력 완료")
            except Exception as e:
                print(f"  ❌ 이메일 입력 실패: {e}")
                await context.close()
                return False

        # 3. 비밀번호 입력
        print("[3/4] 비밀번호 입력...")
        try:
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('#passwordNext')
            await asyncio.sleep(4)
            print("  ✓ 비밀번호 입력 완료")
        except Exception as e:
            print(f"  ❌ 비밀번호 입력 실패: {e}")
            await context.close()
            return False

        # 4. 2FA - TOTP만 사용 (전화번호 절대 사용 안 함)
        print("[4/4] 2FA 코드 입력 (TOTP only)...")
        try:
            await asyncio.sleep(3)

            totp_input = None

            # ── Phase A: TOTP 입력 필드가 바로 있는지 확인 ──
            totp_input = await page.query_selector(
                'input[name="totpPin"], input[id="totpPin"], input[autocomplete="one-time-code"]'
            )

            if totp_input:
                print("  TOTP 입력 필드 바로 발견!")
            else:
                # ── Phase B: 첫 번째 "다른 방법 시도" 클릭 ──
                # (push알림/전화 기본 챌린지 → 방법 선택 페이지)
                print("  TOTP 필드 없음 → '다른 방법 시도' 클릭 (1차)...")
                for try_text in ['다른 방법 시도', 'Try another way']:
                    try:
                        await page.click(f'text={try_text}', timeout=5000)
                        print(f"  ✓ '{try_text}' 클릭 완료")
                        await asyncio.sleep(4)
                        break
                    except:
                        continue

                # 현재 페이지 상태 확인
                page_text = await page.inner_text('body')
                print(f"  1차 후 페이지: {page_text[:200]}...")

                # OTP 옵션이 바로 보이면 선택
                totp_input = await _try_select_otp(page)

                # ── Phase C: 아직 TOTP 없으면 "다른 방법 시도" 한 번 더 ──
                if not totp_input:
                    # 전화번호 선택 페이지에서 "다른 방법 시도" 옵션 클릭
                    print("  OTP 미발견 → '다른 방법 시도' 클릭 (2차)...")
                    for try_text in ['다른 방법 시도', 'Try another way']:
                        try:
                            await page.click(f'text={try_text}', timeout=5000)
                            print(f"  ✓ '{try_text}' 클릭 완료")
                            await asyncio.sleep(4)
                            break
                        except:
                            continue

                    page_text = await page.inner_text('body')
                    print(f"  2차 후 페이지: {page_text[:200]}...")

                    # OTP 옵션 선택 시도
                    totp_input = await _try_select_otp(page)

            # ── TOTP 코드 입력 ──
            if totp_input:
                code = get_totp_code()
                print(f"  TOTP 코드 생성: {code}")

                await totp_input.fill(code)
                await asyncio.sleep(1)

                next_btn = await page.query_selector(
                    '#totpNext, button:has-text("다음"), button:has-text("Next")'
                )
                if next_btn:
                    await next_btn.click()
                else:
                    await totp_input.press('Enter')
                await asyncio.sleep(5)
                print("  ✓ TOTP 코드 입력 완료")
            else:
                print("  ⚠️ TOTP 입력 필드를 찾지 못함")
                await page.screenshot(path='debug_2fa_final.png')

        except Exception as e:
            print(f"  2FA 처리 중 오류: {e}")
            try:
                await page.screenshot(path='debug_2fa_error.png')
            except:
                pass

        # 로그인 결과 확인
        print("\n로그인 결과 확인...")
        for i in range(10):
            await asyncio.sleep(2)
            if 'notebooklm.google.com' in page.url and 'accounts' not in page.url:
                print("✓ 로그인 성공!")
                await context.close()
                return True
            print(f"  대기 중... {(i+1)*2}초")

        print("❌ 로그인 실패")
        await page.screenshot(path='login_failed.png')
        await context.close()
        return False


async def login_and_get_context():
    """
    로그인 후 브라우저 컨텍스트 반환 (다른 작업용)
    """
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto('https://notebooklm.google.com/', timeout=60000)
        await asyncio.sleep(3)

        # 로그인 필요시
        if 'accounts.google.com' in page.url:
            success = await full_auto_login(headless=False)
            if not success:
                await context.close()
                return None, None

            # 다시 컨텍스트 열기
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                viewport={'width': 1280, 'height': 900},
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(3)

        return context, page


# CLI 실행
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='NotebookLM 자동 로그인')
    parser.add_argument('--headless', action='store_true', help='백그라운드 실행')
    parser.add_argument('--test-totp', action='store_true', help='TOTP 코드만 테스트')
    args = parser.parse_args()

    if args.test_totp:
        print(f"현재 TOTP 코드: {get_totp_code()}")
    else:
        result = asyncio.run(full_auto_login(headless=args.headless))
        print(f"\n결과: {'성공' if result else '실패'}")
