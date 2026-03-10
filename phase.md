# 🗺️ QA Auto Test Builder — 로드맵 & Phase 상세 기획

> **문서 유형:** 로드맵 기획서  
> **최종 업데이트:** 2026-03-09  
> **현재 버전:** v7.0 Pro  
> **관련 문서:** [메모장.md](메모장.md) — 프로젝트 기획서

---

## 전체 로드맵 개요

```
 ✅ Phase 1 (v1.0~v4.5)        ✅ Phase 2 (v5.0~v6.0)       ✅ Phase 3 (v7.0)
 ─────────────────────        ─────────────────────       ─────────────────
 코어 엔진 + 기본 GUI          Self-Healing + POM 내보내기    멀티 브라우저, CI/CD
 스캔/실행/DDT                 Smart Wait + 리포터           CLI, 플러그인, YAML
 
      ↓                           ↓                           ↓
 
 ⏳ Phase 4 (v7.1~v7.5)       🔲 Phase 5 (v8.0)            🔲 Phase 6 (v9.0)
 ─────────────────────        ─────────────────────       ─────────────────
 Playwright 장점 흡수           엔진 전환 + API 테스트        AI 자동화 + 배포
 UX 고도화                     Hybrid QA + 메트릭           LLM + .exe 패키징
```

| Phase | 버전 | 테마 | 목표 | 상태 |
|:---:|:---|:---|:---|:---:|
| 1 | v1.0 ~ v4.5 | **Foundation** | 코어 엔진, 기본 GUI, DDT | ✅ 완료 |
| 2 | v5.0 ~ v6.0 | **Stability** | Self-Healing, POM 내보내기, Smart Wait | ✅ 완료 |
| 3 | v7.0 | **Scale** | 멀티 브라우저, CI/CD, CLI, 플러그인 | ✅ 완료 |
| 4 | v7.1 ~ v7.5 | **UX 고도화** | Playwright 장점 흡수, DX 개선 | ✅ 완료 |
| 5 | v8.0 | **Hybrid QA** | 엔진 전환, API 테스트, 품질 메트릭 | 🔲 예정 |
| 6 | v9.0 ~ v10.0 | **AI + 배포** | LLM 자동 생성, .exe 배포 | 🔲 구상 |

---

## ✅ Phase 1. Foundation (v1.0 ~ v4.5) — 완료

> 핵심 엔진 개발 및 기본 사용 가능 버전 완성

### 달성 목표

| 버전 | 주요 기능 | 완료일 |
|:---|:---|:---|
| v1.0 | 모듈화 구조 설계, 기본 스캔/실행 | 2025-11 |
| v2.0 | Smart Wait, Assertion, 텍스트 드래그 스캔 | 2025-11 |
| v2.5 | 단축키(F2), 비밀번호 암호화, 드래그 앤 드롭 | 2025-11 |
| v3.0 | Iframe/Alert 처리, 크롬 보안 팝업 차단 | 2025-11 |
| v3.5 | 보안 패치, Chrome 세션 충돌 해결 | 2025-11 |
| v4.0 | 엑셀 DDT, 코드 생성 안정화 | 2025-11 |
| v4.5 | 키보드/마우스 액션 확장, 엑셀 변수 검증 | 2025-11 |

### 산출물

- `core/scanner.py` — 요소 스캐너 (다중 로케이터, 동적 클래스 필터링, Shadow DOM)
- `core/generator.py` — Pytest 스크립트 생성기
- `core/runner.py` — 테스트 실행기
- `core/browser.py` — 브라우저 매니저
- `gui/qt_app.py` — PySide6 GUI (초기 버전)
- `utils/` — 로깅, 파일 관리, 엑셀 로더, DB

---

## ✅ Phase 2. Stability (v5.0 ~ v6.0) — 완료

> 테스트 안정성 확보 및 코드 생성 고도화

### 달성 목표

| 기능 | 상세 |
|:---|:---|
| **Self-Healing** | 로케이터 실패 시 다중 Fallback 자동 시도 |
| **POM 프로젝트 내보내기** | BasePage → PageObject → TestScript 3계층 자동 생성 |
| **Smart Wait** | 네트워크 유휴 + 요소 가시성 자동 대기 |
| **내장 HTML 리포터** | Allure 없이도 독립 HTML 리포트 생성 |

### 산출물

- `core/pom_generator.py` — POM 3계층 프로젝트 생성기
- `core/html_reporter.py` — 내장 리포터
- Self-Healing 로직 (`scanner.py` 강화)

---

## ✅ Phase 3. Scale (v7.0) — 완료

> 멀티 환경 지원 및 CI/CD 통합

### 달성 목표

| 기능 | 상세 |
|:---|:---|
| **멀티 브라우저** | Chrome/Firefox/Edge/Safari 지원 |
| **CLI 실행기** | `argparse` 기반, 브라우저/데이터/설정 옵션 |
| **CI/CD** | GitHub Actions 워크플로우 자동 생성, Slack 알림 |
| **YAML 설정** | `config.yaml` + 환경변수 계층 설정 |
| **플러그인 시스템** | 확장 가능한 Hook 기반 플러그인 아키텍처 |
| **GUI 고도화** | PySide6 다크 테마, v7.0 Pro UI |

### 산출물

- `core/browser_config.py` — 멀티 브라우저 설정
- `core/ci_generator.py` — GitHub Actions YAML 생성
- `core/plugin_manager.py` — 플러그인 매니저
- `run_tests.py` — CLI 실행기
- `config.py` + `config.yaml` — 통합 설정

---

## ⏳ Phase 4. UX 고도화 (v7.1 ~ v7.5) — 다음 단계

> **목표:** Playwright의 DX(Developer Experience) 장점을 흡수하여 사용성 혁신

### 왜 이 Phase가 필요한가?

현재 AutoTestBuilder는 기능적으로는 충분하지만, Playwright Inspector와 비교했을 때 **UX 측면에서 격차**가 있다. 이 격차를 좁히지 않으면 사용자 확보와 유지가 어렵다.

### v7.1 — 실시간 코드 미리보기

| 항목 | 내용 |
|:---|:---|
| **목표** | 스텝 추가/수정 시 생성될 Pytest 코드를 실시간으로 미리보기 |
| **구현 대상** | GUI에 **Code Preview 탭** 추가 |
| **동작** | `generator.py`의 `generate()` 호출 → 결과를 Syntax Highlighting과 함께 표시 |
| **효과** | 사용자가 "이 스텝이 어떤 코드가 되는지" 즉시 이해 가능 |

```
┌──────────────────────────────────────┐
│ 🎯 Scenario │ ▶ Execution │ 📊 Data │ 💻 Code Preview │
├──────────────────────────────────────┤
│  import pytest                        │
│  from selenium import webdriver       │
│                                       │
│  def test_scenario(driver):           │
│      driver.get("https://...")        │
│      el = driver.find_element(...)  ← │ 현재 선택한 스텝 하이라이트
│      el.click()                       │
│  ...                                  │
└──────────────────────────────────────┘
```

**산출물:**
- [x] GUI에 Code Preview 탭 추가 (`gui/code_tab.py`)
- [x] 실시간 코드 생성 연결 (스텝 변경 → `generate()` → 미리보기 갱신)
- [x] 구문 강조(Syntax Highlighting) 적용 (`gui/syntax_highlighter.py`)

### v7.2 — Step-by-Step 디버깅

| 항목 | 내용 |
|:---|:---|
| **목표** | 한 스텝씩 실행하면서 결과를 확인하는 디버깅 모드 |
| **동작** | [▶ 다음 스텝] 버튼 → 해당 스텝만 실행 → 성공/실패 즉시 표시 |
| **효과** | 어느 스텝에서 문제가 생기는지 즉시 파악 가능 |

```
┌─ Step Debug Mode ────────────────┐
│ Step 1: Click [로그인]     ✅ 성공  │
│ Step 2: Input [아이디]     ✅ 성공  │
│ Step 3: Input [비밀번호]   🔴 실패  │  ← 여기서 멈춤
│ Step 4: Click [제출]       ⏸ 대기  │
│                                   │
│ [◀ 이전] [▶ 다음] [⏩ 전체 실행]   │
└───────────────────────────────────┘
```

**산출물:**
- [x] 디버깅 모드 UI (스텝별 실행 컨트롤) — `gui/execution_tab.py`
- [x] 단일 스텝 실행 엔진 — `core/step_runner.py`
- [x] 스텝별 성공/실패 시각 피드백 + 스크린샷 캐프처

### v7.3 — Trace / Timeline

| 항목 | 내용 |
|:---|:---|
| **목표** | 각 스텝 실행 시 스크린샷 + 소요시간을 타임라인으로 기록/탐색 |
| **효과** | 테스트 실패 원인을 시각적으로 "시간 여행"하며 추적 가능 |

```
┌─ Trace Timeline ─────────────────────────────────┐
│                                                    │
│  0s      2s      4s      6s      8s    10s        │
│  ├───────┼───────┼───────┼───────┼──────┤         │
│  │ Step1 │ Step2 │ Step3 │ Step4 │ Step5│         │
│  │  ✅   │  ✅   │  ✅   │  🔴  │      │         │
│  │       │       │       │       │      │         │
│  └───────┴───────┴───────┴───────┴──────┘         │
│                         ↑                          │
│                   [클릭하면 스크린샷 표시]            │
│                                                    │
│  ┌──────────────────┐                              │
│  │  [Step4 스크린샷] │                              │
│  │  Error: Element   │                              │
│  │  not found       │                              │
│  └──────────────────┘                              │
```

**산출물:**
- [x] 스텝별 스크린샷 자동 캐프처 로직 (`core/step_runner.py`)
- [x] Timeline UI 컨포넌트 (`gui/trace_tab.py`)
- [x] 스크린샷 뷰어 (클릭 시 표시)

### v7.4 — 로그 시각화 개선

| 항목 | 내용 |
|:---|:---|
| **목표** | 로그 뷰의 가독성 대폭 개선 |
| **변경점** | 성공(🟢 초록), 실패(🔴 빨강), 경고(🟡 노랑), 정보(⚪ 회색) 색상 구분 |

**산출물:**
- [x] `QPlainTextEdit` → 커스텀 로그 위젯 교체 (`gui/log_widget.py`)
- [x] 로그 레벨별 색상 매핑
- [ ] 실패 로그 클릭 시 스크린샷 연결

### v7.5 — 호버 스캔 모드

| 항목 | 내용 |
|:---|:---|
| **목표** | F2 키 수동 스캔 대신, 마우스 호버만으로 요소 정보를 실시간 표시 |
| **동작** | 호버 모드 활성화 → 브라우저에서 마우스 움직임 → 요소 하이라이트 + 정보 패널 |
| **효과** | Playwright Inspector의 요소 탐색 UX와 유사한 경험 제공 |

**산출물:**
- [x] 호버 추적 JavaScript 주입 로직 (`core/browser.py` Inspector 모드)
- [x] 요소 정보 실시간 표시 패널 (`gui/scenario_tab.py`)
- [x] 호버 모드 On/Off 토글 버튼

---

## 🔲 Phase 5. Hybrid QA (v8.0) — 예정

> **목표:** UI 테스트를 넘어 API 검증 + 품질 메트릭 + 엔진 현대화

### 5-1. Playwright 백엔드 엔진 도입

| 항목 | 내용 |
|:---|:---|
| **목표** | Selenium 엔진 외에 **Playwright**를 백엔드 옵션으로 추가 |
| **전략** | 기존 Selenium 호환성 유지 + Playwright 선택 가능한 **듀얼 엔진** |
| **이점** | Auto-Wait 네이티브 지원, 속도 2~3배 향상, 네트워크 인터셉트 가능 |

```
┌──────────────────────────────┐
│      GUI / No-Code Layer      │
├──────────────────────────────┤
│    Automation Engine API      │  ← 추상화 레이어 (공통 인터페이스)
├──────────┬───────────────────┤
│ Selenium │    Playwright     │  ← 사용자 선택 (config.yaml)
│ Backend  │    Backend        │
└──────────┴───────────────────┘
```

**산출물:**
- [x] `config.yaml`에 기본 엔진 선택자 추가 (`engine: selenium | playwright`)
- [x] `BrowserEngine` 인터페이스 (Strategy/Abstract Base Class) 정의
- [x] 기존 `BrowserManager`를 `SeleniumEngine`으로 래핑
- [x] `PlaywrightEngine` 골격 구현 및 확장 지원
- [x] `StepRunner`, `PageScanner`, `ScriptGenerator`의 Factory/Proxy 패턴 적용 완료

### 5-2. API 연동 테스트 (Hybrid QA)

| 항목 | 내용 |
|:---|:---|
| **목표** | UI 테스트와 API 테스트를 결합, UI 조작 전후의 서버 상태를 검증 |
| **핵심 라이브러리** | `requests` |
| **시나리오 예시** | UI에서 장바구니 추가 → API로 장바구니 목록 조회 → 상품 존재 검증 |

```
[ UI 테스트 ] → 로그인, 상품 클릭, 구매 버튼 클릭
      ↓
[ API 검증 ] → GET /api/cart → JSON 응답 확인
      ↓
[ 결과 리포트 ] → UI + API 결합 결과를 하나의 리포트에 출력
```

새 액션 타입:

| 액션 | 설명 |
|:---|:---|
| `api_get` | GET 요청 + 응답 검증 |
| `api_post` | POST 요청 + 응답 검증 |
| `api_assert` | 응답 JSON 필드 값 검증 |

**산출물:**
- [x] `core/api_tester.py` — API 테스트 모듈 (REST 호출, 인증, 응답 검증)
- [x] GUI `step_runner.py`에 API 스텝 실행 기능 추가
- [ ] 리포트에 API 검증 결과 포함

### 5-3. 품질 메트릭 대시보드

| 메트릭 | 계산 방식 | 출력 형태 |
|:---|:---|:---|
| **자동화 성공률** | (성공 / 전체) × 100% | `✅ 성공률: 87.5% (7/8)` |
| **평균 실행 시간** | 총 소요시간 / 전체 수 | `⏱️ 평균: 3.2초/테스트` |
| **총 실행 시간** | 시작~종료 시간차 | `🕐 총 소요: 25.6초` |
| **테스트 커버리지** | 자동화 스텝 / 전체 시나리오 | `📊 커버리지: 92%` |
| **실패 분석** | 원인 카테고리 분류 | Timeout / Element / Assert / API 별 건수 |

**산출물:**
- [x] `core/metrics.py` — 메트릭 수집/계산 모듈
- [x] 터미널 품질 요약 리포트
- [ ] HTML 리포트 하단에 메트릭 섹션 추가

### 5-4. 비주얼 리그레션

| 항목 | 내용 |
|:---|:---|
| **목표** | 기준 스크린샷과 현재 스크린샷을 픽셀 비교하여 UI 변경 감지 |
| **라이브러리** | `Pillow` 또는 `pixelmatch` |
| **동작** | 첫 실행 → 기준 이미지 저장 / 이후 실행 → 비교 → 차이 리포트 |

**산출물:**
- [x] `core/visual_compare.py` — 스크린샷 비교 모듈
- [x] 기준 이미지 저장/관리 로직
- [x] 차이 하이라이트 리포트 생성

---

## 🔲 Phase 6. AI 자동화 + 배포 (v9.0 ~ v10.0) — 구상

> **목표:** LLM 기반 자연어 테스트 생성 및 배포 가능한 독립 실행형 제품화

### 6-1. LLM 기반 자연어 테스트 생성기 (Builder)

| 항목 | 내용 |
|:---|:---|
| **목표** | 자연어로 테스트 시나리오를 설명하면, POM 구조의 Pytest 코드 자동 생성 |
| **지원 LLM** | OpenAI API (GPT-4o) 또는 Google Gemini API |
| **입력 예시** | `"네이버에서 '노트북' 검색 후 첫 번째 상품 장바구니 담기"` |
| **출력** | BasePage 상속 PageObject + TestScript Python 코드 |

```
사용자 자연어 입력
    ↓
┌─────────────────────────────┐
│  프롬프트 엔진 (ai_builder)   │
│  ┌───────────────────────┐  │
│  │ 시스템 프롬프트:         │  │
│  │ - BasePage 코드          │  │
│  │ - 지원 액션 목록          │  │
│  │ - POM 구조 규칙          │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
    ↓
LLM API 호출
    ↓
생성 코드 파싱 + 검증
    ↓
POM 프로젝트 파일 출력
```

**프롬프트 설계 원칙:**
1. **컨텍스트 주입** — BasePage 코드를 시스템 프롬프트에 포함 → 호환성 보장
2. **액션 제약** — 지원 액션만 사용하도록 지시
3. **구조 강제** — POM 3계층 출력 (JSON Schema 지정)
4. **즉시 실행 가능** — conftest.py까지 포함

**산출물:**
- [ ] `core/ai_builder.py` — LLM 연동 코드 생성 모듈
- [ ] `core/prompt_templates.py` — 프롬프트 템플릿 관리
- [ ] GUI에 "🤖 AI 생성" 탭/버튼 추가
- [ ] `config.yaml`에 `ai.provider`, `ai.api_key`, `ai.model` 설정
- [ ] 생성 코드 미리보기 + 편집 + POM 내보내기 연동

### 6-2. 제품 배포

| 항목 | 내용 |
|:---|:---|
| **목표** | 설치형 `.exe` 파일로 배포, 비개발자도 즉시 사용 가능 |
| **패키징** | PyInstaller |
| **배포 채널** | GitHub Releases + 자동 업데이트 |

**산출물:**
- [ ] `AutoTestBuilder.spec` 최적화
- [ ] GitHub Releases 자동 빌드 (CI/CD)
- [ ] 자동 업데이트 체크 기능
- [ ] 설치/사용 가이드 문서

---

## 리스크 및 의사결정 포인트

| # | 리스크/결정 사항 | Phase | 설명 | 상태 |
|:-:|:---|:---:|:---|:---:|
| 1 | **Playwright 엔진 전환 시기** | 5 | Selenium 위에 기능을 더 쌓을지, Playwright로 전환할지 | 🟡 검토 필요 |
| 2 | **LLM API 비용** | 6 | GPT-4o API 호출 비용 → 무료 제품과 양립 가능한가? | 🟡 검토 필요 |
| 3 | **PySide6 라이선스** | 전체 | 상업적 배포 시 LGPL 조건 확인 필요 | 🟢 확인 완료 |
| 4 | **크로스 브라우저 실 검증** | 4 | Firefox/Edge/Safari에서 실제 동작 검증 미완 | 🔴 블로커 |
| 5 | **GUI 모듈 분리** | 4 | `qt_app.py` 948줄 → 260줄 + 6개 모듈 분리 완료 | ✅ 해결 |

---

## 마일스톤 요약

| 마일스톤 | 예상 시기 | 핵심 지표 |
|:---|:---|:---|
| **v7.1 — 코드 미리보기** | Phase 4 시작 | 스텝 추가 시 코드 즉시 표시 |
| **v7.3 — Trace 완성** | Phase 4 중반 | 스텝별 스크린샷 타임라인 조회 가능 |
| **v7.5 — Phase 4 완료** | Phase 4 종료 | 호버 스캔, 디버깅, 로그 시각화 모두 구현 |
| **v8.0 — 듀얼 엔진** | Phase 5 시작 | Selenium + Playwright 선택 가능 |
| **v8.0 — Hybrid QA** | Phase 5 중반 | UI + API 통합 테스트 실행 가능 |
| **v9.0 — AI Builder** | Phase 6 시작 | 자연어 → Pytest 코드 자동 생성 |
| **v10.0 — 배포** | Phase 6 종료 | `.exe` 설치 파일 배포 |

---

> 📌 **이 문서의 목적:** 각 Phase별로 "무엇을", "왜", "어떻게" 만들 것인지 상세하게 정의한다. Phase 진행 시 이 문서를 기준으로 산출물을 체크하고, 완료된 항목은 `[x]`로 업데이트한다.
