#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NLM 인증 갱신: Playwright 자동 로그인 (2FA TOTP) → nlm auth.json 저장

Usage:
    python refresh_auth.py
    python refresh_auth.py --visible   # 브라우저 표시
"""
import asyncio
import json
import os
import sys
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv("D:/Projects/notebooklm-automation/.env.local")

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL", "")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD", "")
TOTP_SECRET = os.getenv("GOOGLE_2FA_SECRET", "")

NLM_AUTH_PATH = os.path.expanduser("~/.notebooklm-mcp-cli/auth.json")
NLM_PROFILE_DIR = os.path.expanduser("~/.notebooklm-mcp-cli/profiles/default")
BROWSER_PROFILE = os.path.expanduser("~/.notebooklm-auto-v3")


def get_totp_code() -> str:
    """TOTP 코드 생성"""
    import pyotp
    totp = pyotp.TOTP(TOTP_SECRET.upper())
    return totp.now()


async def auto_login_and_save(headless: bool = True) -> bool:
    """Playwright 자동 로그인 후 nlm auth.json에 저장"""
    from playwright.async_api import async_playwright

    print("=" * 50)
    print("NLM 인증 갱신 (Playwright + 2FA TOTP)")
    print("=" * 50)

    async with async_playwright() as p:
        print(f"\n[1/5] 브라우저 시작 (headless={headless})...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_PROFILE,
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-first-run',
            ],
            ignore_default_args=['--enable-automation'],
            viewport={'width': 1280, 'height': 800},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # NotebookLM 접속
        print("[2/5] NotebookLM 접속...")
        try:
            await page.goto("https://notebooklm.google.com", wait_until='domcontentloaded', timeout=30000)
        except Exception as e:
            print(f"  페이지 로드: {str(e)[:60]}")

        await asyncio.sleep(3)
        url = page.url

        # Google 로그인이 필요한 경우
        if 'accounts.google.com' in url:
            print("[3/5] Google 로그인...")

            # 이메일 입력
            try:
                email_input = await page.wait_for_selector('input[type="email"]', timeout=10000)
                if email_input:
                    await email_input.fill(GOOGLE_EMAIL)
                    await asyncio.sleep(0.5)
                    await page.click('#identifierNext, button[type="button"]:has-text("Next"), button:has-text("다음")')
                    await asyncio.sleep(3)
                    print(f"  이메일 입력: {GOOGLE_EMAIL[:5]}...")
            except Exception as e:
                print(f"  이메일 단계 건너뜀: {str(e)[:40]}")

            # 비밀번호 입력
            try:
                pw_input = await page.wait_for_selector('input[type="password"]', timeout=10000)
                if pw_input:
                    await pw_input.fill(GOOGLE_PASSWORD)
                    await asyncio.sleep(0.5)
                    await page.click('#passwordNext, button:has-text("Next"), button:has-text("다음")')
                    await asyncio.sleep(3)
                    print("  비밀번호 입력 완료")
            except Exception as e:
                print(f"  비밀번호 단계 건너뜀: {str(e)[:40]}")

            # 2FA TOTP
            try:
                # TOTP 필드 찾기
                totp_input = await page.query_selector(
                    'input[name="totpPin"], input[type="tel"][autocomplete="one-time-code"], input[id="totpPin"]'
                )

                # 없으면 "다른 방법 시도" 클릭
                if not totp_input:
                    for selector in [
                        'button:has-text("다른 방법")',
                        'button:has-text("Try another way")',
                        'a:has-text("다른 방법")',
                    ]:
                        try:
                            btn = await page.query_selector(selector)
                            if btn:
                                await btn.click()
                                await asyncio.sleep(2)
                                break
                        except Exception:
                            continue

                    # Google OTP / Authenticator 선택
                    for selector in [
                        '[data-challengetype="6"]',
                        'div:has-text("Google OTP")',
                        'div:has-text("Google Authenticator")',
                        'div:has-text("인증 앱")',
                    ]:
                        try:
                            opt = await page.query_selector(selector)
                            if opt:
                                await opt.click()
                                await asyncio.sleep(2)
                                break
                        except Exception:
                            continue

                    # 다시 TOTP 필드 찾기
                    try:
                        totp_input = await page.wait_for_selector(
                            'input[name="totpPin"], input[type="tel"], input[id="totpPin"]',
                            timeout=10000
                        )
                    except Exception:
                        pass

                if totp_input:
                    code = get_totp_code()
                    await totp_input.fill(code)
                    await asyncio.sleep(0.5)
                    await page.click('button:has-text("Next"), button:has-text("다음"), #totpNext')
                    await asyncio.sleep(3)
                    print(f"  2FA 코드 입력: {code}")
                else:
                    print("  2FA 필드를 찾을 수 없음")
            except Exception as e:
                print(f"  2FA 단계: {str(e)[:60]}")
        else:
            print("[3/5] 이미 로그인 상태")

        # 로그인 완료 대기
        print("[4/5] 로그인 확인 대기...")
        logged_in = False
        for i in range(30):
            url = page.url
            if 'notebooklm.google.com' in url and 'accounts.google' not in url:
                cookies = await context.cookies()
                google_cookies = [c for c in cookies if 'google.com' in c.get('domain', '')]
                cookie_names = {c['name'] for c in google_cookies}
                if 'SID' in cookie_names and ('__Secure-1PSID' in cookie_names or '__Secure-3PSID' in cookie_names):
                    logged_in = True
                    print(f"  로그인 확인 (쿠키 {len(google_cookies)}개)")
                    break
            await asyncio.sleep(2)
            if i % 5 == 4:
                print(f"  대기 중... {(i+1)*2}초")

        if not logged_in:
            print("  로그인 실패")
            await context.close()
            return False

        # 쿠키 추출 → nlm auth.json + 통합 프로필 저장
        print("[5/5] nlm 인증 저장...")
        cookies = await context.cookies()

        # Google 쿠키만 필터
        google_cookies = [c for c in cookies if 'google.com' in c.get('domain', '')]
        cookies_dict = {c['name']: c['value'] for c in google_cookies}

        sapisid = cookies_dict.get('SAPISID', cookies_dict.get('__Secure-3PAPISID', ''))
        csrf_token = f"{sapisid[:16]}:{int(time.time() * 1000)}" if sapisid else ""

        # 1) 레거시 auth.json (dict 형식)
        auth_data = {
            "cookies": cookies_dict,
            "csrf_token": csrf_token,
            "session_id": "",
            "extracted_at": time.time(),
            "auto_login": True,
        }
        os.makedirs(os.path.dirname(NLM_AUTH_PATH), exist_ok=True)
        with open(NLM_AUTH_PATH, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2)
        print(f"  레거시 auth.json 저장 ({len(cookies_dict)}개 쿠키)")

        # 2) 통합 프로필 cookies.json (list 형식 - Playwright 쿠키 그대로)
        os.makedirs(NLM_PROFILE_DIR, exist_ok=True)
        cookies_path = os.path.join(NLM_PROFILE_DIR, "cookies.json")
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(google_cookies, f, indent=2)

        # 3) 통합 프로필 metadata.json (csrf_token은 빈값 → 클라이언트가 자동 추출)
        from datetime import datetime as dt
        metadata = {
            "csrf_token": "",
            "session_id": "",
            "last_validated": dt.utcnow().isoformat() + "Z",
            "login_method": "auto_login",
        }
        meta_path = os.path.join(NLM_PROFILE_DIR, "metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"  통합 프로필 저장: {NLM_PROFILE_DIR}")
        print(f"  쿠키: {len(google_cookies)}개")

        await context.close()

    print("\n" + "=" * 50)
    print("인증 갱신 완료!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    visible = "--visible" in sys.argv
    result = asyncio.run(auto_login_and_save(headless=not visible))
    sys.exit(0 if result else 1)
