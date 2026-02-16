#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 풀 파이프라인: NotebookLM → PDF 슬라이드 분석 → 자료실 등록

NotebookLM이 생성한 PDF 슬라이드를 그대로 분석하여 병원 자료실에 등록합니다.
(PPTX 변환 없이 PDF 원본 사용)

Usage:
    # 기본: NotebookLM에서 슬라이드 생성 → PDF 분석 → 자료실 등록
    python run_pipeline.py --title "회전근개 파열"

    # 커스텀 검색 쿼리
    python run_pipeline.py --title "무릎 반월상연골" --queries "반월상연골 손상,반월상연골 수술"

    # 이미 다운로드된 PDF를 바로 분석 → 자료실 등록
    python run_pipeline.py --pdf "G:/내 드라이브/notebooklm/slides.pdf" --title "오십견"

    # 자료실 등록 없이 슬라이드만 생성
    python run_pipeline.py --title "척추 협착증" --no-register

    # 비공개 등록 (관리자 검토 후 공개)
    python run_pipeline.py --title "족저근막염" --hidden
"""
import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# .env.local 로드 (Vision API 키 등)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / '.env.local'
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        # notebooklm-automation 쪽 .env.local 폴백
        _env_path2 = Path("D:/Projects/notebooklm-automation/.env.local")
        if _env_path2.exists():
            load_dotenv(_env_path2)
except ImportError:
    pass

# noterang 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from noterang import Noterang, WorkflowResult
from noterang.config import get_config
from noterang.prompts import SlidePrompts

# ─── 설정 ───────────────────────────────────────────
WEBAPP_DIR = Path(__file__).parent.parent.parent
UPLOADS_DIR = WEBAPP_DIR / "public" / "uploads"
FIREBASE_PROJECT_ID = "miryangosweb"
STORAGE_BUCKET = "miryangosweb.firebasestorage.app"

# 부위별 키워드 (body-parts.ts 와 동일)
BODY_PARTS = [
    {"id": "shoulder", "label": "어깨 (견관절)",
     "keywords": ["어깨", "견관절", "회전근개", "오십견", "석회성건염", "유착성피막염"]},
    {"id": "elbow", "label": "팔꿈치 (주관절)",
     "keywords": ["팔꿈치", "주관절", "테니스엘보", "골퍼엘보", "상과염"]},
    {"id": "hand_wrist", "label": "손/손목",
     "keywords": ["손목", "손가락", "수근관", "방아쇠", "건초염", "터널증후군"]},
    {"id": "hip", "label": "고관절",
     "keywords": ["고관절", "대퇴골두", "무혈성괴사", "대퇴골"]},
    {"id": "knee", "label": "무릎 (슬관절)",
     "keywords": ["무릎", "슬관절", "십자인대", "반월상", "연골"]},
    {"id": "foot_ankle", "label": "발/발목",
     "keywords": ["발목", "족저근막", "아킬레스", "발바닥", "발뒤꿈치", "족부", "족주상골", "부골", "부주상골", "무지외반"]},
    {"id": "spine", "label": "척추",
     "keywords": ["척추", "허리", "목", "디스크", "협착", "측만", "경추", "요추"]},
]


def match_body_part(tags: List[str], title: str) -> str:
    """태그와 제목으로 부위 판별 (최다 매칭)"""
    search_text = " ".join(tags + [title]).lower()
    best_id = "etc"
    best_count = 0
    for part in BODY_PARTS:
        count = sum(1 for kw in part["keywords"] if kw in search_text)
        if count > best_count:
            best_count = count
            best_id = part["id"]
    return best_id


# ─── PDF 분석 ────────────────────────────────────────

class PDFAnalyzer:
    """PDF 슬라이드 분석기 (PyMuPDF 사용)"""

    def __init__(self, pdf_path: Path):
        import fitz
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(self.pdf_path))
        self.page_count = len(self.doc)

    def close(self):
        self.doc.close()

    def extract_all_text(self) -> List[str]:
        """페이지별 텍스트 추출 (PyMuPDF → Vision OCR 폴백)"""
        texts = []
        for page in self.doc:
            texts.append(page.get_text())

        # PyMuPDF 텍스트가 빈약하면 Vision OCR 폴백
        total_chars = sum(len(t.strip()) for t in texts)
        if total_chars < 100:
            print(f"  PyMuPDF 텍스트 부족 ({total_chars}자) → Vision OCR 시도...")
            ocr_texts = self._ocr_with_vision()
            if ocr_texts:
                return ocr_texts

        return texts

    def _ocr_with_vision(self) -> Optional[List[str]]:
        """Google Cloud Vision API로 OCR 폴백"""
        import fitz
        import requests

        api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY') or os.getenv('GOOGLE_VISION_API_KEY')
        if not api_key:
            print("  Vision API 키 없음 (GOOGLE_CLOUD_VISION_API_KEY). OCR 건너뜀.")
            return None

        api_url = "https://vision.googleapis.com/v1/images:annotate"
        texts = []

        for i, page in enumerate(self.doc):
            # 페이지 → PNG 이미지 변환
            mat = fitz.Matrix(2.0, 2.0)  # 2x 해상도
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            payload = {
                "requests": [{
                    "image": {"content": img_b64},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                }]
            }

            try:
                resp = requests.post(
                    f"{api_url}?key={api_key}",
                    json=payload,
                    timeout=60,
                )
                result = resp.json()

                if 'error' in result:
                    print(f"  Vision API 오류 (페이지 {i+1}): {result['error']}")
                    texts.append("")
                    continue

                responses = result.get('responses', [{}])
                full_text = responses[0].get('fullTextAnnotation', {}).get('text', '')
                texts.append(full_text)
                print(f"  OCR 페이지 {i+1}/{self.page_count}: {len(full_text)}자")
            except Exception as e:
                print(f"  Vision OCR 실패 (페이지 {i+1}): {e}")
                texts.append("")

        total = sum(len(t.strip()) for t in texts)
        print(f"  Vision OCR 완료: 총 {total}자")
        return texts if total > 0 else None

    def extract_slide_titles(self) -> List[str]:
        """각 슬라이드의 제목(큰 글씨) 추출"""
        titles = []
        for page in self.doc:
            blocks = page.get_text("dict", flags=0)
            best_text = ""
            best_size = 0
            for block in blocks.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        size = span.get("size", 0)
                        if text and size > best_size and len(text) > 1:
                            best_size = size
                            best_text = text
            if best_text:
                titles.append(best_text)
        return titles

    def generate_thumbnail(self, page_num: int = 0, scale: float = 1.5) -> bytes:
        """특정 페이지의 썸네일 이미지 (PNG) 생성"""
        import fitz
        page = self.doc[page_num]
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def build_summary(self) -> str:
        """PDF 전체 내용 요약 생성"""
        titles = self.extract_slide_titles()
        if not titles:
            return ""

        lines = []
        for i, title in enumerate(titles, 1):
            lines.append(f"{i}. {title}")
        return "\n".join(lines)

    @staticmethod
    def clean_slide_text(text: str) -> str:
        """슬라이드 텍스트에서 NotebookLM 언급, OCR 아티팩트 등 제거"""
        # NotebookLM / Notebook LM 언급 제거 (대소문자 무시, 앞뒤 공백/마침표 포함)
        text = re.sub(r'[,.]?\s*A?\s*Notebook\s*LM\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[,.]?\s*노트북\s*LM\.?', '', text, flags=re.IGNORECASE)
        # 반복 ·E 패턴 제거 (OCR 아티팩트: ·E·E·E·E...)
        text = re.sub(r'(?:[·.]\s*E\s*){3,}', '', text)
        # ·가 3개 이상 반복되는 패턴 제거
        text = re.sub(r'(?:·\s*){3,}', '', text)
        # 0이 6개 이상 연속 → 빈 문자열 (OCR 실패한 숫자)
        text = re.sub(r'0{6,}', '', text)
        # 연속 공백 정리
        text = re.sub(r' {2,}', ' ', text)
        # 빈 줄이 3개 이상이면 2개로
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def build_content(self) -> str:
        """자료실 등록용 전체 텍스트 컨텐츠 생성 (슬라이드 간 간격 포함)"""
        texts = self.extract_all_text()
        parts = []
        for i, text in enumerate(texts, 1):
            clean = self.clean_slide_text(text)
            if clean:
                parts.append(f"[슬라이드 {i}]\n{clean}")
        # 슬라이드 끼리 간격을 넉넉하게
        return "\n\n\n".join(parts)

    def analyze(self) -> Dict[str, Any]:
        """PDF 전체 분석"""
        print(f"  PDF 분석: {self.pdf_path.name} ({self.page_count}페이지)")

        titles = self.extract_slide_titles()
        all_text = self.extract_all_text()
        full_text = " ".join(t.strip() for t in all_text if t.strip())

        # 키워드 추출 (자주 등장하는 2글자 이상 단어)
        keywords = self._extract_keywords(full_text)

        result = {
            "page_count": self.page_count,
            "titles": titles,
            "summary": self.build_summary(),
            "content": self.build_content(),
            "keywords": keywords,
            "total_chars": len(full_text),
        }

        print(f"  슬라이드: {self.page_count}장")
        print(f"  제목들: {titles[:5]}{'...' if len(titles) > 5 else ''}")
        print(f"  키워드: {keywords[:8]}")

        return result

    def _extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """텍스트에서 주요 키워드 추출"""
        # 불용어
        stopwords = {
            "그리고", "하지만", "또한", "그래서", "때문에", "위해", "통해",
            "경우", "등의", "대한", "있는", "없는", "하는", "되는", "이는",
            "것이", "수술", "치료", "진단",  # 너무 일반적인 의료 용어는 제외
        }

        words = {}
        for word in text.split():
            # 2~6글자 한글 단어만
            clean = "".join(c for c in word if '\uac00' <= c <= '\ud7a3')
            if 2 <= len(clean) <= 6 and clean not in stopwords:
                words[clean] = words.get(clean, 0) + 1

        sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]


# ─── 파이프라인 ──────────────────────────────────────

class NoterangPipeline:
    """전체 파이프라인: NotebookLM → PDF 슬라이드 분석 → 자료실 등록"""

    def __init__(
        self,
        title: str,
        queries: List[str] = None,
        pdf_path: str = None,
        register: bool = True,
        visible: bool = True,
        article_type: str = "disease",
        design: str = "인포그래픽",
        slide_count: int = 15,
        config_override=None,
    ):
        self.title = title
        self.queries = queries
        self.pdf_path = Path(pdf_path) if pdf_path else None
        self.register = register
        self.visible = visible
        self.article_type = article_type
        self.design = design
        self.slide_count = slide_count
        self.config = config_override or get_config()

    # ─── 연구 쿼리 생성 ────────────────────────────────
    def get_research_queries(self) -> List[str]:
        """한의학 제외, 정형외과 관점 검색 쿼리 생성"""
        if self.queries:
            return [f"{q} -한의학 -한방 -침 -뜸 -한의원" for q in self.queries]

        topic = self.title
        return [
            f"{topic} 정형외과 원인 증상 치료 -한의학 -한방 -침 -뜸 -한의원",
            f"{topic} 최신 치료법 수술 비수술 재활 -한의학 -한방치료",
            f"{topic} 진단 검사 예방 운동 -한의학 -한방",
        ]

    # ─── 디자인 포커스 프롬프트 ──────────────────────────
    def get_focus_prompt(self) -> str:
        """디자인 스타일 + 한글 + 쉬운 설명 프롬프트"""
        prompts = SlidePrompts()
        design_prompt = prompts.get_prompt(self.design) or ""

        return f"""{design_prompt}

[추가 요청사항]
- 반드시 한글로 작성해주세요
- 영어는 의학 전문용어만 괄호 안에 최소한으로 병기
- 환자도 이해할 수 있는 쉽고 친근한 표현 사용
- 한의학/한방/침/뜸 관련 내용 완전히 제외
- 정형외과 관점에서만 설명
- 슬라이드 {self.slide_count}장으로 구성
- 인포그래픽 플랫 디자인: 깔끔한 아이콘, 도표, 플로우차트 활용
- 각 슬라이드마다 핵심 포인트를 시각적으로 전달
- 핵심 주제: {self.title}
- 구성 예시: 정의 → 원인/분류 → 증상 → 진단 → 치료법 → 예방/재활"""

    # ─── 태그 자동 생성 ─────────────────────────────────
    def generate_tags(self, pdf_keywords: List[str] = None) -> List[str]:
        """제목 + PDF 분석 키워드로 태그 생성"""
        design_tag = self.design.replace(" ", "")
        tags = ["자동생성", "노트랑", design_tag]

        # 부위 감지
        all_text = self.title + " " + " ".join(pdf_keywords or [])
        body_part = match_body_part(pdf_keywords or [], self.title)
        if body_part != "etc":
            part_info = next((p for p in BODY_PARTS if p["id"] == body_part), None)
            if part_info:
                tags.append(part_info["label"])

        # 제목 키워드
        for word in self.title.split():
            if len(word) >= 2 and word not in tags:
                tags.append(word)

        # PDF에서 추출한 키워드 (상위 5개)
        if pdf_keywords:
            for kw in pdf_keywords[:5]:
                if kw not in tags and len(kw) >= 2:
                    tags.append(kw)

        return tags

    # ─── Step 1: 노트랑 실행 (PDF 생성) ──────────────────
    async def run_noterang(self) -> WorkflowResult:
        """NotebookLM 자동화 (PPTX 변환 건너뛰기, PDF만 다운로드)"""
        noterang = Noterang(config=self.config)
        return await noterang.run(
            title=self.title,
            research_queries=self.get_research_queries(),
            focus=self.get_focus_prompt(),
            language="ko",
            skip_convert=True,  # PPTX 변환 안 함!
        )

    # ─── Step 2: PDF 분석 ────────────────────────────────
    def analyze_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """PDF 슬라이드 분석 (텍스트, 제목, 키워드, 썸네일 추출)"""
        analyzer = PDFAnalyzer(pdf_path)
        try:
            result = analyzer.analyze()
            # 첫 페이지 썸네일 생성
            result["thumbnail"] = analyzer.generate_thumbnail(0)
            return result
        finally:
            analyzer.close()

    # ─── Step 3: PDF + 썸네일을 웹앱에 복사 ────────────────
    async def upload_to_firebase(self, pdf_path: Path, thumbnail: bytes = None) -> Tuple[str, Optional[str]]:
        """PDF 파일과 썸네일을 Firebase Storage에 직접 업로드"""
        try:
            import firebase_admin
            from firebase_admin import storage
        except ImportError:
            print("  firebase-admin 미설치. pip install firebase-admin")
            return self.copy_to_webapp(pdf_path, thumbnail)

        # Firebase Admin 초기화
        if not firebase_admin._apps:
            try:
                # 1. 환경 변수에서 경로 가져오기
                # 2. Downloads 폴더 (사용자 이름 동적 처리)
                # 3. 프로젝트 루트
                service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
                if service_account_path:
                    service_account_path = Path(service_account_path)
                
                if not service_account_path or not service_account_path.exists():
                    # 사용자 홈 디렉토리 기준으로 Downloads 폴더 시도
                    service_account_path = Path.home() / "Downloads" / "miryangosweb-firebase-adminsdk-fbsvc-e139abbe14.json"
                
                if not service_account_path.exists():
                    # 프로젝트 루트 시도
                    service_account_path = WEBAPP_DIR / "firebase-service-account.json"

                if service_account_path.exists():
                    print(f"  서비스 계정 사용: {service_account_path}")
                    cred = firebase_admin.credentials.Certificate(str(service_account_path))
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': STORAGE_BUCKET
                    })
                else:
                    print("  ⚠️ 서비스 계정 파일을 찾을 수 없습니다. ADC(Application Default Credentials)를 시도합니다.")
                    firebase_admin.initialize_app(options={
                        'projectId': FIREBASE_PROJECT_ID,
                        'storageBucket': STORAGE_BUCKET
                    })
                print("  Firebase Storage 초기화 완료")
            except Exception as e:
                print(f"  Firebase 초기화 실패: {e}")
                return self.copy_to_webapp(pdf_path, thumbnail)

        bucket = storage.bucket()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        safe_title = self.title.replace(" ", "_").replace("/", "-")

        # PDF 업로드
        pdf_name = f"articles/{timestamp}_{unique_id}_{safe_title}.pdf"
        blob = bucket.blob(pdf_name)
        blob.upload_from_filename(str(pdf_path))
        
        # Public URL (Firebase Storage Download URL format)
        # gsutil/admin SDK에서는 get_download_url이 없으므로 직접 구성하거나 make_public 사용
        # 여기서는 클라이언트 사이드에서 처리하기 쉽도록 public access 부여 (보안 규칙에 따라 다름)
        # blob.make_public()
        # pdf_url = blob.public_url
        
        # 대신, 프로젝트 내부에서 사용하는 URL 패턴 (Storage 관점)
        # 웹앱에서 getDownloadURL로 가져올 수 있도록 경로만 반환하거나 
        # https://firebasestorage.googleapis.com/... 형식을 사용
        # firebase-admin-python에서는 아래와 같이 서명된 URL을 생성하거나 public_url을 사용할 수 있음
        pdf_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{pdf_name.replace('/', '%2F')}?alt=media"
        print(f"  PDF 업로드 성공: {pdf_url}")

        # 썸네일 업로드
        thumb_url = None
        if thumbnail:
            thumb_name = f"articles/{timestamp}_{unique_id}_{safe_title}_thumb.png"
            thumb_blob = bucket.blob(thumb_name)
            thumb_blob.upload_from_string(thumbnail, content_type='image/png')
            thumb_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{thumb_name.replace('/', '%2F')}?alt=media"
            print(f"  썸네일 업로드 성공: {thumb_url}")

        return pdf_url, thumb_url

    def copy_to_webapp(self, pdf_path: Path, thumbnail: bytes = None) -> Tuple[str, Optional[str]]:
        """[Fallback] PDF 파일과 썸네일을 public/uploads 에 복사"""
        import uuid
        
        # 절대 경로로 확실하게 수정
        ACTUAL_UPLOADS_DIR = Path("d:/Entertainments/DevEnvironment/miryangosweb/public/uploads")
        ACTUAL_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_title = self.title.replace(" ", "_").replace("/", "-")

        # PDF 복사
        pdf_name = f"noterang_{timestamp}_{unique_id}_{safe_title}.pdf"
        pdf_dest = ACTUAL_UPLOADS_DIR / pdf_name
        shutil.copy2(str(pdf_path), str(pdf_dest))
        pdf_url = f"/uploads/{pdf_name}"
        print(f"  [Fallback] PDF 복사: {pdf_dest}")

        # 썸네일 저장
        thumb_url = None
        if thumbnail:
            thumb_name = f"noterang_{timestamp}_{unique_id}_{safe_title}_thumb.png"
            thumb_dest = ACTUAL_UPLOADS_DIR / thumb_name
            thumb_dest.write_bytes(thumbnail)
            thumb_url = f"/uploads/{thumb_name}"
            print(f"  [Fallback] 썸네일 저장: {thumb_dest}")

        return pdf_url, thumb_url

    # ─── Step 4: 자료실 등록 (Firestore) ─────────────────
    def register_to_firestore(
        self,
        pdf_url: str,
        thumb_url: str,
        analysis: Dict[str, Any],
        notebook_id: str = None,
    ) -> Optional[str]:
        """Firestore articles 컬렉션에 문서 등록"""
        try:
            import firebase_admin
            from firebase_admin import firestore as fs_admin
        except ImportError:
            print("  firebase-admin 미설치. pip install firebase-admin")
            return None

        # STORAGE_BUCKET 사용을 위해 초기화 로직 수정
        if not firebase_admin._apps:
            try:
                service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
                if service_account_path:
                    service_account_path = Path(service_account_path)
                
                if not service_account_path or not service_account_path.exists():
                    service_account_path = Path.home() / "Downloads" / "miryangosweb-firebase-adminsdk-fbsvc-e139abbe14.json"
                
                if not service_account_path.exists():
                    service_account_path = WEBAPP_DIR / "firebase-service-account.json"

                if service_account_path.exists():
                    cred = firebase_admin.credentials.Certificate(str(service_account_path))
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': STORAGE_BUCKET
                    })
                else:
                    firebase_admin.initialize_app(options={
                        'projectId': FIREBASE_PROJECT_ID,
                        'storageBucket': STORAGE_BUCKET
                    })
            except Exception as e:
                print(f"  Firebase 초기화 실패: {e}")
                return None

        db = fs_admin.client()
        tags = self.generate_tags(analysis.get("keywords", []))
        page_count = analysis.get("page_count", 0)
        summary_text = analysis.get("summary", "")

        # 슬라이드 제목들로 요약 구성
        titles = analysis.get("titles", [])
        if titles:
            title_summary = " / ".join(titles[:6])
            summary = f"{self.title} - {title_summary}"
            if len(titles) > 6:
                summary += f" 외 {len(titles) - 6}장"
        else:
            summary = f"{self.title}에 대해 알기 쉽게 정리한 슬라이드 자료입니다."

        # 본문: 첫 페이지 이미지 + 슬라이드 목차 + 전체 텍스트
        content_parts = []

        # 첫 페이지 이미지를 content 최상단에 markdown으로 삽입
        if thumb_url:
            content_parts.append(f"![{self.title}]({thumb_url})\n")

        if summary_text:
            content_parts.append(f"\n[슬라이드 목차]\n{summary_text}\n")

        # 전체 텍스트 (너무 길면 잘라서)
        full_content = analysis.get("content", "")
        if full_content:
            # Firestore 문서 크기 제한 고려 (~1MB), 적당히 자르기
            if len(full_content) > 8000:
                full_content = full_content[:8000] + "\n\n... (이하 생략)"
            content_parts.append(f"\n[전체 내용]\n{full_content}")

        # images 배열에서 thumb_url 제거 (content에 이미 포함되므로 중복 방지)
        doc_data = {
            'title': self.title,
            'type': self.article_type,
            'tags': tags,
            'summary': summary[:200],  # 요약은 200자 제한
            'content': "\n".join(content_parts),
            'attachmentUrl': pdf_url,
            'attachmentName': Path(pdf_url).name,
            'images': [],
            'isVisible': self.visible,
            'createdAt': fs_admin.SERVER_TIMESTAMP,
        }

        try:
            _, doc_ref = db.collection('articles').add(doc_data)
            doc_id = doc_ref.id
            print(f"  자료실 등록 완료: {doc_id}")
            print(f"  공개: {'예' if self.visible else '아니오 (관리자 검토 필요)'}")
            return doc_id
        except Exception as e:
            print(f"  Firestore 등록 실패: {e}")
            return None

    # ─── 전체 파이프라인 ─────────────────────────────────
    async def run(self) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        start_time = time.time()

        print("\n" + "=" * 60)
        print(f"  노트랑 PDF 파이프라인")
        print(f"  제목: {self.title}")
        print(f"  디자인: {self.design}")
        print(f"  자료실 등록: {'예' if self.register else '아니오'}")
        if self.pdf_path:
            print(f"  기존 PDF: {self.pdf_path}")
        print("=" * 60)

        notebook_id = None
        pdf_path = self.pdf_path

        # Step 1: NotebookLM으로 PDF 생성 (기존 PDF가 없을 때만)
        if not pdf_path:
            print("\n[1/4] NotebookLM 슬라이드 생성...")
            result = await self.run_noterang()

            if not result.success or not result.pdf_path:
                elapsed = int(time.time() - start_time)
                print(f"\n  파이프라인 실패: {result.error} ({elapsed}초)")
                return {"success": False, "error": result.error}

            pdf_path = Path(result.pdf_path)
            notebook_id = result.notebook_id
            print(f"  PDF 생성 완료: {pdf_path}")
        else:
            print("\n[1/4] 기존 PDF 사용")
            if not pdf_path.exists():
                return {"success": False, "error": f"PDF 파일 없음: {pdf_path}"}

        # Step 2: PDF 분석
        print("\n[2/4] PDF 슬라이드 분석...")
        analysis = self.analyze_pdf(pdf_path)

        # Step 3: 파일 업로드 (Firebase Storage)
        print("\n[3/4] Firebase Storage에 파일 업로드...")
        pdf_url, thumb_url = await self.upload_to_firebase(
            pdf_path, analysis.get("thumbnail")
        )

        # Step 4: 자료실 등록
        doc_id = None
        if self.register:
            print("\n[4/4] 자료실 등록...")
            doc_id = self.register_to_firestore(
                pdf_url, thumb_url, analysis, notebook_id
            )
        else:
            print("\n[4/4] 자료실 등록 건너뜀 (--no-register)")

        elapsed = int(time.time() - start_time)

        # 결과 요약
        print("\n" + "=" * 60)
        print("  파이프라인 완료")
        print("=" * 60)
        print(f"  제목: {self.title}")
        print(f"  PDF: {pdf_path}")
        print(f"  슬라이드: {analysis['page_count']}장")
        print(f"  URL: {pdf_url}")
        if thumb_url:
            print(f"  썸네일: {thumb_url}")
        if doc_id:
            print(f"  자료 ID: {doc_id}")
        print(f"  소요시간: {elapsed}초")
        print("=" * 60)

        return {
            "success": True,
            "title": self.title,
            "notebook_id": notebook_id,
            "pdf_path": str(pdf_path),
            "pdf_url": pdf_url,
            "thumb_url": thumb_url,
            "doc_id": doc_id,
            "page_count": analysis["page_count"],
            "duration": elapsed,
        }


async def main():
    parser = argparse.ArgumentParser(
        description="노트랑 PDF 파이프라인: NotebookLM → PDF 분석 → 자료실 등록"
    )
    parser.add_argument(
        "--title", "-t", required=True,
        help="슬라이드 제목 (예: 회전근개 파열)"
    )
    parser.add_argument(
        "--pdf", "-p",
        help="기존 PDF 파일 경로 (미입력시 NotebookLM에서 새로 생성)"
    )
    parser.add_argument(
        "--queries", "-q",
        help="검색 쿼리 (쉼표 구분, 미입력시 자동 생성)"
    )
    parser.add_argument(
        "--type", default="disease",
        choices=["disease", "guide", "news"],
        help="자료 유형 (기본: disease)"
    )
    parser.add_argument(
        "--no-register", action="store_true",
        help="자료실 등록 안 함 (슬라이드만 생성)"
    )
    parser.add_argument(
        "--hidden", action="store_true",
        help="비공개 등록 (관리자 검토 후 공개)"
    )
    parser.add_argument(
        "--design", "-d", default="인포그래픽",
        help="슬라이드 디자인 스타일 (기본: 인포그래픽)"
    )
    parser.add_argument(
        "--slides", "-s", type=int, default=15,
        help="슬라이드 장수 (기본: 15)"
    )
    parser.add_argument(
        "--batch", "-b",
        help="배치 실행: 쉼표 구분 제목들 (예: '골다공증,측만증,거북목')"
    )
    parser.add_argument(
        "--max-workers", type=int, default=3,
        help="최대 동시 실행 수 (기본: 3, --batch 모드 전용)"
    )
    parser.add_argument(
        "--worker-id", "-w", type=int, default=None,
        help="워커 ID (병렬 실행시 독립 브라우저 프로필 사용, 예: 0, 1, 2)"
    )

    args = parser.parse_args()

    # 배치 모드
    if args.batch:
        from batch_pipeline import BatchPipeline
        titles = [t.strip() for t in args.batch.split(",") if t.strip()]
        batch = BatchPipeline(
            titles=titles,
            design=args.design,
            max_workers=args.max_workers,
            register=not args.no_register,
            visible=not args.hidden,
            article_type=args.type,
            slide_count=args.slides,
        )
        results = await batch.run()
        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.get("success"))
        print(f"\n배치 완료: {success_count}/{len(titles)} 성공")
        return 0 if success_count == len(titles) else 1

    # 단일 실행 모드
    queries = args.queries.split(",") if args.queries else None

    # worker_id 설정 (병렬 실행시 독립 브라우저 프로필)
    config_override = None
    if args.worker_id is not None:
        from noterang.config import NoterangConfig, set_config
        config = NoterangConfig.load()
        config.worker_id = args.worker_id
        config.ensure_dirs()
        set_config(config)
        config_override = config

    pipeline = NoterangPipeline(
        title=args.title,
        pdf_path=args.pdf,
        queries=queries,
        register=not args.no_register,
        visible=not args.hidden,
        article_type=args.type,
        design=args.design,
        slide_count=args.slides,
        config_override=config_override,
    )

    result = await pipeline.run()
    print(f"\nRESULT:{json.dumps(result, ensure_ascii=False)}")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
