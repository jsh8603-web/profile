#!/usr/bin/env python3
"""Firebase CLI 로그인 자동화 - Playwright로 Google OAuth 처리"""
import asyncio
import json
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from playwright.async_api import async_playwright

# Firebase CLI OAuth credentials (공개 클라이언트)
CLIENT_ID = "563584335869-fgrhgmd47bqnekij5i8b5pr03ho849e6.apps.googleusercontent.com"
CLIENT_SECRET = "j9iVZfS8kkCEFUPaAeJV0sAi"
SCOPES = [
    "email", "openid",
    "https://www.googleapis.com/auth/cloudplatformprojects.readonly",
    "https://www.googleapis.com/auth/firebase",
    "https://www.googleapis.com/auth/cloud-platform",
]
REDIRECT_PORT = 9005
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

BROWSER_PROFILE = Path.home() / '.notebooklm-auto-v3'
CONFIG_PATH = Path.home() / '.config' / 'configstore' / 'firebase-tools.json'

auth_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<html><body><h2>Firebase Login Success!</h2><p>You can close this window.</p></body></html>')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'No code received')

    def log_message(self, format, *args):
        pass  # Suppress logs


async def main():
    global auth_code

    print("Firebase CLI 로그인 자동화...")

    # 1. 로컬 서버 시작 (OAuth 리다이렉트 수신)
    server = HTTPServer(('localhost', REDIRECT_PORT), OAuthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"  OAuth 서버: http://localhost:{REDIRECT_PORT}")

    # 2. OAuth URL 생성
    oauth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={CLIENT_ID}"
        f"&scope={'+'.join(SCOPES)}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&access_type=offline"
    )

    # 3. Playwright로 브라우저 열기 (기존 Google 세션 활용)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 800, 'height': 600},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        print("  Google OAuth 페이지 열기...")
        await page.goto(oauth_url, timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path="firebase_oauth_01.png")
        print(f"  현재 URL: {page.url[:80]}")

        # 계정 선택 (이미 로그인된 경우)
        email_el = await page.query_selector('[data-email="jsh8603@gmail.com"]')
        if email_el:
            await email_el.click()
            print("  계정 선택: jsh8603@gmail.com")
            await asyncio.sleep(5)
            await page.screenshot(path="firebase_oauth_02.png")
            print(f"  선택 후 URL: {page.url[:80]}")

        # 권한 동의 루프
        for i in range(15):
            if auth_code:
                break

            current_url = page.url
            print(f"  [{i}] URL: {current_url[:80]}")

            # 이미 리다이렉트됨?
            if 'localhost' in current_url and 'code=' in current_url:
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                if 'code' in params:
                    auth_code = params['code'][0]
                    break

            # "Continue" / "허용" / "Allow" 버튼 찾기
            for selector in [
                '#submit_approve_access',
                'button:has-text("Continue")',
                'button:has-text("Allow")',
                'button:has-text("허용")',
                'button:has-text("계속")',
                'input[type="submit"]',
                '[data-idom-class*="nCP5yc"]',
            ]:
                btn = await page.query_selector(selector)
                if btn:
                    visible = await btn.is_visible()
                    if visible:
                        await btn.click()
                        print(f"  클릭: {selector}")
                        await asyncio.sleep(3)
                        break

            if i == 2:
                await page.screenshot(path="firebase_oauth_03.png")

            await asyncio.sleep(2)

        await ctx.close()

    server.shutdown()

    if not auth_code:
        print("  ❌ Authorization code 획득 실패")
        return False

    print(f"  ✓ Auth code 획득 ({len(auth_code)}자)")

    # 4. Code → Refresh Token 교환
    print("  Token 교환...")
    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }, timeout=30)

    if token_resp.status_code != 200:
        print(f"  ❌ Token 교환 실패: {token_resp.text[:200]}")
        return False

    tokens = token_resp.json()
    refresh_token = tokens.get('refresh_token', '')
    access_token = tokens.get('access_token', '')

    if not refresh_token:
        print("  ❌ Refresh token 없음")
        return False

    print(f"  ✓ Refresh token 획득")

    # 5. 사용자 정보 가져오기
    user_resp = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={
        "Authorization": f"Bearer {access_token}"
    }, timeout=30)
    user_info = user_resp.json() if user_resp.status_code == 200 else {}

    # 6. Firebase CLI 설정 파일에 토큰 저장
    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

    config['user'] = {
        'email': user_info.get('email', ''),
        'token': refresh_token,
    }
    config['tokens'] = {
        'refresh_token': refresh_token,
        'access_token': access_token,
    }
    config['activeProjects'] = {
        str(Path.cwd()): 'profile-28714'
    }
    config['usage'] = False
    config['analytics'] = False

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent='\t'), encoding='utf-8')

    print(f"  ✓ Firebase 설정 저장: {CONFIG_PATH}")
    print(f"  ✓ 로그인 완료: {user_info.get('email', 'unknown')}")
    return True


if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
