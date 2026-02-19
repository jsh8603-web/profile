"""
Firebase REST API 웹 포스팅 모듈

Google OAuth (Playwright) → ID Token 추출 → Firebase Storage/Firestore REST API 로 포스트를 생성합니다.
UI 자동화 폴백도 포함.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .cdk_utils import ss


@dataclass
class PostConfig:
    """포스트 설정."""

    title: str
    slug: str
    excerpt: str
    category: str = "finance"
    tags: list[str] = field(default_factory=list)
    admin_url: str = "https://profile-blue-pi.vercel.app"
    project_id: str = "profile-28714"
    storage_bucket: str = "profile-28714.firebasestorage.app"
    author_name: str = "Sehoon Jang"


class AdminPoster:
    """Firebase REST API 기반 Admin 포스팅."""

    def __init__(self, config: PostConfig):
        self.cfg = config

    # ── public ──────────────────────────────────────

    async def post(
        self,
        pdf_path: Path | None,
        content: str,
        extra_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """REST API 로 포스트 생성. 실패 시 UI 폴백."""
        tags = list(self.cfg.tags)
        for kw in extra_tags or []:
            if kw not in tags and len(kw) >= 2:
                tags.append(kw)
        tags = tags[:15]

        print("\n[Admin] Google OAuth 로그인 → REST API 포스트 생성...")

        id_token = await self._get_id_token()
        if not id_token:
            print("  ❌ ID Token 없음 → UI 자동화 폴백")
            await self._post_via_ui(pdf_path, content, tags)
            return {"method": "ui_fallback"}

        attachment_url, attachment_name = await self._upload_pdf(id_token, pdf_path)
        result = await self._create_post(id_token, content, tags, attachment_url, attachment_name)
        return result

    # ── ID Token ────────────────────────────────────

    async def _get_id_token(self) -> str | None:
        from playwright.async_api import async_playwright
        from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE

        print("  1) Google OAuth 로그인...")
        id_token = None

        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(AUTH_PROFILE),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 900},
            )
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            await page.goto(f"{self.cfg.admin_url}/admin/posts/new", timeout=30000)
            await asyncio.sleep(3)

            if "/auth" in page.url or "signin" in page.url:
                google_btn = await page.query_selector('button:has-text("Google")')
                if google_btn:
                    try:
                        async with ctx.expect_page(timeout=15000) as popup_info:
                            await google_btn.click()
                        await popup_info.value
                        await asyncio.sleep(8)
                    except Exception:
                        await asyncio.sleep(5)

                if "/admin" not in page.url:
                    await page.goto(f"{self.cfg.admin_url}/admin/posts/new", timeout=30000)
                    await asyncio.sleep(3)

            if "/admin" in page.url:
                id_token = await page.evaluate(
                    """async () => {
                    // localStorage
                    try {
                        const keys = Object.keys(localStorage);
                        for (const key of keys) {
                            if (key.startsWith('firebase:authUser:')) {
                                const data = JSON.parse(localStorage.getItem(key));
                                if (data && data.stsTokenManager && data.stsTokenManager.accessToken)
                                    return data.stsTokenManager.accessToken;
                            }
                        }
                    } catch {}
                    // IndexedDB - firebaseLocalStorageDb
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
                                            resolve(val.stsTokenManager.accessToken); return;
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
                    // 모든 IndexedDB 탐색
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
                                                        resolve(val.stsTokenManager.accessToken); return;
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
                }"""
                )
                if id_token:
                    print(f"  ✓ ID Token 획득 ({len(id_token)}자)")
                else:
                    print("  ⚠️ ID Token 추출 실패")

            await ctx.close()

        return id_token

    # ── PDF 업로드 ──────────────────────────────────

    async def _upload_pdf(
        self, id_token: str, pdf_path: Path | None
    ) -> tuple[str, str]:
        import requests

        if not pdf_path or not pdf_path.exists():
            return "", ""

        print(f"  2) PDF 업로드: {pdf_path.name}...")
        storage_path = f"posts/{self.cfg.slug}/{pdf_path.name}"
        upload_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{self.cfg.storage_bucket}"
            f"/o/{requests.utils.quote(storage_path, safe='')}?uploadType=media"
        )

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        upload_resp = requests.post(
            upload_url,
            data=pdf_data,
            headers={
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/pdf",
            },
            timeout=120,
        )

        if upload_resp.status_code == 200:
            storage_name = upload_resp.json().get("name", storage_path)
            attachment_url = (
                f"https://firebasestorage.googleapis.com/v0/b/{self.cfg.storage_bucket}"
                f"/o/{requests.utils.quote(storage_name, safe='')}?alt=media"
            )
            print(f"  ✓ PDF 업로드 완료: {pdf_path.name}")
            return attachment_url, pdf_path.name
        else:
            print(f"  ⚠️ PDF 업로드 실패: {upload_resp.status_code} {upload_resp.text[:200]}")
            return "", ""

    # ── Firestore: slug 중복 확인 ───────────────────

    def _find_existing_post(self, id_token: str) -> str | None:
        """동일 slug를 가진 기존 포스트의 document path를 반환. 없으면 None."""
        import requests

        query_url = (
            f"https://firestore.googleapis.com/v1/projects/{self.cfg.project_id}"
            f"/databases/(default)/documents:runQuery"
        )
        body = {
            "structuredQuery": {
                "from": [{"collectionId": "posts"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "slug"},
                        "op": "EQUAL",
                        "value": {"stringValue": self.cfg.slug},
                    }
                },
                "limit": 1,
            }
        }
        try:
            resp = requests.post(
                query_url,
                json=body,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                results = resp.json()
                for r in results:
                    doc = r.get("document")
                    if doc and doc.get("name"):
                        return doc["name"]  # full path
        except Exception as e:
            print(f"  ⚠️ 기존 포스트 조회 실패: {e}")
        return None

    # ── Firestore 문서 생성/업데이트 ─────────────────

    async def _create_post(
        self,
        id_token: str,
        content: str,
        tags: list[str],
        attachment_url: str = "",
        attachment_name: str = "",
    ) -> dict[str, Any]:
        import requests

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        base_url = (
            f"https://firestore.googleapis.com/v1/projects/{self.cfg.project_id}"
            f"/databases/(default)/documents/posts"
        )

        def str_val(s):
            return {"stringValue": str(s)}

        def int_val(n):
            return {"integerValue": str(n)}

        def bool_val(b):
            return {"booleanValue": b}

        def ts_val(t):
            return {"timestampValue": t}

        def arr_val(items):
            return {"arrayValue": {"values": items}}

        # 동일 slug 기존 포스트 확인
        existing_doc_path = self._find_existing_post(id_token)

        if existing_doc_path:
            # ── 기존 포스트 업데이트 ──
            doc_id = existing_doc_path.split("/")[-1]
            print(f"  3) 기존 포스트 업데이트 (ID: {doc_id})...")

            update_fields: dict[str, Any] = {
                "title": str_val(self.cfg.title),
                "excerpt": str_val(self.cfg.excerpt),
                "content": str_val(content[:15000]),
                "category": str_val(self.cfg.category),
                "tags": arr_val([str_val(t) for t in tags]),
                "published": bool_val(True),
                "publishedAt": ts_val(now),
                "updatedAt": ts_val(now),
                "authorName": str_val(self.cfg.author_name),
            }
            if attachment_url:
                update_fields["attachmentUrl"] = str_val(attachment_url)
                update_fields["attachmentName"] = str_val(attachment_name)

            update_url = f"https://firestore.googleapis.com/v1/{existing_doc_path}"
            mask_params = "&".join(f"updateMask.fieldPaths={k}" for k in update_fields)
            update_url = f"{update_url}?{mask_params}"

            fs_resp = requests.patch(
                update_url,
                json={"fields": update_fields},
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )

            if fs_resp.status_code == 200:
                print(f"  ✓ 포스트 업데이트 완료! (ID: {doc_id})")
                print(f"  ✓ URL: {self.cfg.admin_url}/blog/{self.cfg.slug}")
                return {"method": "rest_api_update", "doc_id": doc_id, "slug": self.cfg.slug}
            else:
                print(f"  ❌ 업데이트 실패: {fs_resp.status_code}")
                print(f"  응답: {fs_resp.text[:300]}")
                # 업데이트 실패 시 새로 생성 시도
                print("  → 새 포스트 생성으로 폴백...")

        # ── 새 포스트 생성 ──
        print("  3) Firestore 포스트 생성...")

        doc_fields: dict[str, Any] = {
            "title": str_val(self.cfg.title),
            "slug": str_val(self.cfg.slug),
            "excerpt": str_val(self.cfg.excerpt),
            "content": str_val(content[:15000]),
            "category": str_val(self.cfg.category),
            "tags": arr_val([str_val(t) for t in tags]),
            "coverImageUrl": str_val(""),
            "published": bool_val(True),
            "publishedAt": ts_val(now),
            "createdAt": ts_val(now),
            "updatedAt": ts_val(now),
            "authorName": str_val(self.cfg.author_name),
            "commentCount": int_val(0),
            "viewCount": int_val(0),
        }
        if attachment_url:
            doc_fields["attachmentUrl"] = str_val(attachment_url)
            doc_fields["attachmentName"] = str_val(attachment_name)

        fs_resp = requests.post(
            base_url,
            json={"fields": doc_fields},
            headers={
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

        if fs_resp.status_code == 200:
            doc_name = fs_resp.json().get("name", "")
            doc_id = doc_name.split("/")[-1] if doc_name else "unknown"
            print(f"  ✓ 포스트 생성 완료! (ID: {doc_id})")
            print(f"  ✓ URL: {self.cfg.admin_url}/blog/{self.cfg.slug}")
            return {"method": "rest_api", "doc_id": doc_id, "slug": self.cfg.slug}
        else:
            print(f"  ❌ 포스트 생성 실패: {fs_resp.status_code}")
            print(f"  응답: {fs_resp.text[:300]}")
            await self._post_via_ui(None, content, tags)
            return {"method": "ui_fallback"}

    # ── UI 폴백 ─────────────────────────────────────

    async def _post_via_ui(
        self,
        pdf_path: Path | None,
        content: str,
        tags: list[str],
    ) -> None:
        from playwright.async_api import async_playwright
        from noterang.auto_login import BROWSER_PROFILE as AUTH_PROFILE

        print("\n[Admin UI 폴백] Playwright로 포스트 입력...")
        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(AUTH_PROFILE),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 900},
            )
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            await page.goto(f"{self.cfg.admin_url}/admin/posts/new", timeout=30000)
            await asyncio.sleep(3)

            if "/auth" in page.url or "signin" in page.url:
                google_btn = await page.query_selector('button:has-text("Google")')
                if google_btn:
                    try:
                        async with ctx.expect_page(timeout=15000) as popup_info:
                            await google_btn.click()
                        await popup_info.value
                        await asyncio.sleep(8)
                    except Exception:
                        await asyncio.sleep(5)
                if "/admin" not in page.url:
                    await page.goto(f"{self.cfg.admin_url}/admin/posts/new", timeout=30000)
                    await asyncio.sleep(3)

            if "/admin" not in page.url:
                print("  ❌ Admin 로그인 실패")
                await ctx.close()
                return

            page.on("dialog", lambda d: d.dismiss())

            await page.fill('input[placeholder*="Post title"]', self.cfg.title)
            await asyncio.sleep(0.5)

            slug_input = await page.query_selector('input[placeholder*="url-slug"], input[placeholder*="slug"]')
            if slug_input:
                await slug_input.fill("")
                await slug_input.fill(self.cfg.slug)

            excerpt_area = await page.query_selector('textarea[placeholder*="Brief"]')
            if excerpt_area:
                await excerpt_area.fill(self.cfg.excerpt)

            cat_btn = await page.query_selector(f'button:has-text("{self.cfg.category.title()}")')
            if cat_btn:
                await cat_btn.click()

            tag_input = await page.query_selector('input[placeholder*="Add tag"]')
            if tag_input:
                for tag in tags:
                    await tag_input.fill(tag)
                    await tag_input.press("Enter")
                    await asyncio.sleep(0.2)

            content_area = await page.query_selector('textarea[placeholder*="Markdown"], textarea[placeholder*="Write"]')
            if content_area:
                await content_area.fill(content[:8000])

            await ss(page, "admin_03_filled")

            console_logs: list[str] = []
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))

            result = await page.evaluate(
                """async () => {
                const logs = [];
                try {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Publish');
                    const form = document.querySelector('form');
                    if (!btn || !form) return {ok: false, err: 'no btn/form'};
                    logs.push('btn found: ' + btn.type + ', form found');
                    let submitBlocked = false;
                    const blocker = (e) => { e.preventDefault(); e.stopImmediatePropagation(); submitBlocked = true; };
                    form.addEventListener('submit', blocker, {capture: true, once: true});
                    btn.click();
                    logs.push('clicked, submitBlocked=' + submitBlocked);
                    await new Promise(r => setTimeout(r, 500));
                    logs.push('waited 500ms');
                    btn.click();
                    logs.push('second click done');
                    await new Promise(r => setTimeout(r, 3000));
                    logs.push('final URL: ' + window.location.href);
                    return {ok: true, logs: logs};
                } catch (e) {
                    return {ok: false, err: e.message, logs: logs};
                }
            }"""
            )
            print(f"  Publish 결과: {result}")
            await asyncio.sleep(8)
            print(f"  현재 URL: {page.url}")

            if console_logs:
                print(f"  콘솔 로그 ({len(console_logs)}개):")
                for log in console_logs[-10:]:
                    print(f"    {log[:100]}")

            await ss(page, "admin_04_published")
            await ctx.close()

        print(f"  ✓ 포스트: {self.cfg.admin_url}/blog/{self.cfg.slug}")
