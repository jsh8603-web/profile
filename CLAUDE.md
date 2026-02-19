# Noterang - NotebookLM 슬라이드 자동화 파이프라인

Python 3.12+ / Playwright 기반. NotebookLM에서 슬라이드 PDF를 자동 생성하고 블로그에 포스팅.

## Auto Trigger
키워드 감지 시 자동 실행: `노트랑`, `noterang`, `notebooklm`, `슬라이드 만들어`, `ppt 만들어`

## Commands
```bash
python run_noterang.py                                   # 전체 파이프라인
python run_provision_pipeline.py                         # 로그인→노트북→소스→슬라이드→PDF→포스팅
python run_provision_pipeline.py --pdf path/to/file.pdf  # 기존 PDF로 포스팅만
python -m noterang login --show                          # 로그인 (먼저!)
```

## Project Map
```
noterang/
  browser.py      # Playwright 직접 제어 (핵심)
  artifacts.py    # 슬라이드/인포그래픽 생성
  pipeline.py     # 파이프라인 오케스트레이션
  poster.py       # Admin 블로그 포스팅
  auth.py         # 자동 로그인 (2FA TOTP)
  download.py     # 브라우저 다운로드
  convert.py      # PDF → PPTX (JPDF)
run_noterang.py / run_provision_pipeline.py  # 실행 스크립트
```

## Critical Rules (실수 방지)
- NotebookLM = Angular CDK overlay → 일반 `.click()` 안됨. 반드시 `bounding_box()` → `page.mouse.click(x, y)` 좌표 클릭
- 텍스트 입력: coord_click 후 `keyboard.type()` (Angular 변경감지 호환)
- 슬라이드 언어: 반드시 `language="ko"` 한글
- nlm CLI 버그 있음 → `run_browser()` 메서드 사용
- 다운로드 403 → Playwright 브라우저 세션으로만 다운로드
- 슬라이드 생성 시 반드시 디자인 스타일 물어볼 것 (상세: `.claude/rules/slide-styles.md`)

## Paths
- 다운로드: `G:/내 드라이브/notebooklm_automation/`
- 브라우저 프로필: `~/.notebooklm-auto-v3/`
- 인증: `.env.local` (GOOGLE_EMAIL, GOOGLE_PASSWORD, GOOGLE_2FA_SECRET)
- 디자인 프롬프트: `gallery/prompts_100.json`
- Firebase: project=`profile-28714`, bucket=`profile-28714.firebasestorage.app`
