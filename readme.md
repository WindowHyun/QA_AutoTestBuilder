# 📝 QA Auto Test Builder - 프로젝트 메모장

> **최종 업데이트:** 2026-03-05  
> **버전:** v7.0 Pro  
> **저장소:** [OHTARU/QA_AutoTestBuilder](https://github.com/OHTARU/QA_AutoTestBuilder)

---

## 1. 왜 이걸 만들었는가? (프로젝트 목적)

### 🎯 핵심 문제
QA 테스트 자동화를 위해 Selenium 스크립트를 작성하려면 **Python + Selenium + XPath/CSS 셀렉터** 등 개발 지식이 필수적이다. 이로 인해:

- **비개발자 QA 담당자**가 테스트 자동화에 접근하기 어렵다
- 수동으로 셀렉터를 찾고 코드를 작성하는 것은 **시간 소모가 크다**
- 웹 요소가 변경되면 테스트가 깨지고, **유지보수 비용이 높다**
- 반복적인 데이터 테스트(예: 여러 계정 로그인)를 자동화하려면 별도 프레임워크가 필요하다

### 💡 해결책: No-Code 테스트 자동화
**코드를 한 줄도 작성하지 않고** 브라우저에서 클릭/입력만으로 테스트 시나리오를 만들고, 이를 완전한 Python 테스트 프로젝트로 내보내는 도구.

| 문제 | QA Auto Test Builder 해결 방식 |
| :--- | :--- |
| 셀렉터 모름 | 브라우저 요소 클릭 → 자동으로 최적 로케이터 분석 |
| 코드 작성 불가 | GUI에서 스텝 추가 → Pytest 코드 자동 생성 |
| 데이터 반복 테스트 | 엑셀 파일 연동 → DDT 자동화 |
| 요소 변경 시 깨짐 | Self-Healing + 다중 Fallback 로케이터 |
| 리포트 필요 | Allure / HTML 리포트 자동 생성 |

---

## 2. 개발 과정 (Git 로그 기반)

### 📊 커밋 히스토리

| 날짜 | 커밋 해시 | 설명 | 단계 |
| :--- | :--- | :--- | :--- |
| 2025-11-27 | `8089f89` | Level 2.5 Complete | 🟢 코어 완성 |
| 2025-11-27 | `4ced8fc` | Make readme.md | 📄 문서화 |
| 2025-11-27 | `ad97705` | Level 3 기능 구현 및 크롬 보안 팝업 이슈 해결 | 🔧 안정화 |
| 2025-11-27 | `376a0ad` | Level 3.5 보안 패치 | 🔒 보안 |
| 2025-11-27 | `c531d1e` | [Fix] 크롬 보안 팝업 충돌 해결 및 동적 요소 스캔 로직 개선 | 🐛 버그 수정 |
| 2025-11-27 | `d844718` | [Feat/Fix] Level 3.5 기능 구현 및 Chrome 세션 충돌 해결 | 🔧 안정화 |
| 2025-11-28 | `11b0b9e` | [Feat] Level 4 엑셀 데이터 연동(DDT) 및 코드 생성 로직 안정화 | 📊 DDT |
| 2025-11-30 | `e6f0f43` | [Feat] Level 4.5 기능 확장: 키보드/마우스 액션 및 엑셀 변수 검증 추가 | ⌨️ 기능 확장 |
| 2026-02-17 | `adfa8c5` | clear pc commit | 🧹 정리 |
| 2026-02-17 | `89b2e6e` | docs: resolve merge conflict in readme.md | 📄 정리 |

### 🔄 개발 단계별 요약

```
Level 2.5 (2025-11) ──→ 기본 스캔/실행/저장 기능, 단축키(F2), 비밀번호 암호화
    ↓
Level 3.0 (2025-11) ──→ Iframe/Alert 처리, 크롬 보안 팝업 완벽 차단
    ↓
Level 3.5 (2025-11) ──→ 보안 패치, Chrome 세션 충돌 해결, 동적 요소 스캔 개선
    ↓
Level 4.0 (2025-11) ──→ 엑셀 기반 DDT(Data Driven Testing), 코드 생성 안정화
    ↓
Level 4.5 (2025-11) ──→ 키보드/마우스 액션 확장, 엑셀 변수 검증
    ↓
v5.0~v7.0 (2026-02~03) ──→ Self-Healing, POM 프로젝트 내보내기, 멀티 브라우저,
                            CI/CD GitHub Actions, CLI 실행기, YAML 설정 관리,
                            내장 HTML 리포터, 플러그인 시스템
```

---

## 3. 다른 프로그램과의 차별점

### 📌 경쟁 도구 비교

| 기능 | QA Auto Test Builder | Selenium IDE | Katalon Studio | Testim |
| :--- | :---: | :---: | :---: | :---: |
| **No-Code 시나리오 작성** | ✅ | ✅ | ✅ | ✅ |
| **Pytest 코드 자동 생성** | ✅ | ❌ (자체 포맷) | ❌ (Groovy) | ❌ |
| **POM 프로젝트 내보내기** | ✅ | ❌ | ❌ | ❌ |
| **Shadow DOM 자동 감지** | ✅ | ❌ | △ | △ |
| **Self-Healing (자동 복구)** | ✅ | ❌ | ✅ (유료) | ✅ (유료) |
| **엑셀 DDT** | ✅ | ❌ | ✅ | △ |
| **동적 클래스 자동 필터링** | ✅ | ❌ | ❌ | ❌ |
| **멀티 브라우저 (CLI)** | ✅ | ✅ | ✅ | ✅ |
| **CI/CD 연동** | ✅ (GitHub Actions) | ❌ | ✅ | ✅ |
| **Allure + HTML 리포트** | ✅ 둘 다 지원 | ❌ | 자체 리포트 | 자체 리포트 |
| **오픈소스 & 무료** | ✅ | ✅ | △ (유료 기능) | ❌ (유료) |
| **GUI 기반 데이터 편집** | ✅ | ❌ | △ | ❌ |
| **YAML 설정 관리** | ✅ | ❌ | ❌ | ❌ |

### 🏆 핵심 차별점

1. **Pytest 코드 생성**: 녹화한 시나리오를 표준 Pytest 스크립트로 변환 → 어떤 CI/CD에서든 바로 실행 가능
2. **POM 구조 내보내기**: BasePage → PageObject → TestScript 3계층 구조로 유지보수성 극대화
3. **지능형 로케이터 엔진**: `data-testid > id > aria-label > title > CSS > XPath` 우선순위, 동적 클래스/ID 자동 필터링
4. **완전 무료 오픈소스**: Katalon, Testim 등의 유료 기능(Self-Healing, 리포트)을 무료로 제공
5. **데스크톱 GUI (PySide6)**: 브라우저 확장 프로그램이 아닌 독립 실행형 데스크톱 앱

---

## 4. 프로그램 사용 방법

### 🛠️ 설치

```bash
# Python 3.8 이상 필요
pip install -r requirements.txt
```

### ▶️ 실행 방법

#### 방법 1: GUI 모드 (기본)
```bash
python main.py
```

#### 방법 2: CLI 모드 (CI/CD용)
```bash
# 기본 실행
python run_tests.py --test-file first.json

# 브라우저 지정 + 헤드리스
python run_tests.py --browser firefox --headless --test-file first.json

# DDT 데이터 지정
python run_tests.py --test-file first.json --data-path data.xlsx

# 커스텀 설정 파일 사용
python run_tests.py --config my_config.yaml --test-file first.json

# 지원 브라우저 목록 확인
python run_tests.py --list-browsers
```

### 📋 GUI 사용 워크플로우

```
┌──────────────────────────────────────────────────┐
│  1️⃣  브라우저 열기                                 │
│    → URL 입력 + 브라우저 선택 (Chrome/Firefox/Edge) │
│    → [🌐 브라우저 열기] 클릭                        │
├──────────────────────────────────────────────────┤
│  2️⃣  테스트 스텝 작성                              │
│    → 웹 페이지에서 요소 클릭/텍스트 드래그           │
│    → F2 키 또는 [🎯 요소 스캔] 버튼 클릭            │
│    → 자동으로 로케이터+액션이 스텝 리스트에 추가      │
├──────────────────────────────────────────────────┤
│  3️⃣  데이터 바인딩 (선택)                          │
│    → 데이터 관리 탭에서 엑셀 파일 로드               │
│    → Value에 {아이디}, {비밀번호} 같은 변수 입력     │
├──────────────────────────────────────────────────┤
│  4️⃣  실행 또는 내보내기                            │
│    → [▶ 실행] → 즉시 테스트 실행 + 결과 확인         │
│    → [📦 POM 내보내기] → 독립 프로젝트로 저장        │
└──────────────────────────────────────────────────┘
```

### 🔵 지원 액션 목록

| 액션 | 설명 | 비고 |
| :--- | :--- | :--- |
| `click` | 요소 클릭 | JS 강제 클릭 지원 |
| `input` | 텍스트 입력 | |
| `input_password` | 비밀번호 입력 | 화면 마스킹(`***`) |
| `press_key` | 특수키 입력 | ENTER, TAB 등 |
| `check_text` | 텍스트 검증 | 실패 시 스크린샷 |
| `check_url` | URL 변경 검증 | |
| `switch_frame` | Iframe 진입 | |
| `accept_alert` | 경고창 확인 | |
| `drag_source` | 드래그 시작 | |
| `drop_target` | 드롭 위치 | |

### ⚙️ 설정 관리 (config.yaml)

설정 우선순위: **환경변수(`QA_ATB_*`)** > **config.yaml** > **기본값**

```yaml
# 브라우저 설정
browsers:
  default: chrome       # chrome | firefox | edge | safari
  headless: false       # CI/CD 환경에서는 true 권장

# 테스트 실행 설정
test:
  parallel_workers: 1   # 병렬 워커 수
  retry_count: 1        # 실패 시 재시도
  timeout: 30           # 대기 타임아웃(초)

# 리포트 설정
report:
  type: allure          # allure | html
  screenshot_on_failure: true
```

---

## 5. 현재 진행 상황 및 남은 과정

### ✅ 완료된 기능

| 구분 | 기능 | 상세 | 상태 |
| :--- | :--- | :--- | :---: |
| **코어** | 요소 스캐너 | `scanner.py` - 다중 로케이터 Fallback, 동적 클래스 필터링, Shadow DOM | ✅ |
| **코어** | 스크립트 생성기 | `generator.py` - Pytest + Allure 코드 자동 생성 | ✅ |
| **코어** | POM 생성기 | `pom_generator.py` - BasePage/PageObject/TestScript 3계층 구조 | ✅ |
| **코어** | 테스트 실행기 | `runner.py` - Pytest 실행, Allure 리포트 열기, 강제 종료 | ✅ |
| **코어** | 브라우저 설정 | `browser_config.py` - Chrome/Firefox/Edge/Safari 멀티 브라우저 | ✅ |
| **코어** | 데이터 로더 | `data_loader.py` - JSON/CSV/Excel DDT 데이터 로드 | ✅ |
| **코어** | HTML 리포터 | `html_reporter.py` - Allure 없이 독립 HTML 리포트 생성 | ✅ |
| **코어** | CI 생성기 | `ci_generator.py` - GitHub Actions YAML 자동 생성 | ✅ |
| **코어** | 플러그인 매니저 | `plugin_manager.py` - 확장 플러그인 시스템 | ✅ |
| **GUI** | Qt 애플리케이션 | `qt_app.py` - PySide6 다크 테마 GUI (v7.0 Pro) | ✅ |
| **GUI** | 커스텀 컴포넌트 | `qt_components.py` - 테이블 모델, 액션 위임, 스타일 버튼 | ✅ |
| **GUI** | 데이터 모델 | `data_model.py` - DataFrame 기반 데이터 관리 | ✅ |
| **인프라** | 설정 관리 | `config.py` + `config.yaml` - 환경변수/YAML 통합 설정 | ✅ |
| **인프라** | CLI 실행기 | `run_tests.py` - argparse 기반 CLI | ✅ |
| **인프라** | CI/CD | `.github/workflows/main.yml` - GitHub Actions + Slack 알림 | ✅ |
| **인프라** | 로깅 | `utils/logger.py` - 로테이팅 파일 로깅 | ✅ |
| **인프라** | 보안 | `utils/file_manager.py` - 비밀번호 암호화 (cryptography) | ✅ |
| **데이터** | 엑셀 DDT | 엑셀 변수 바인딩 `{변수명}` + 다중 행 반복 실행 | ✅ |
| **안정성** | Smart Wait | 네트워크 유휴 + 요소 가시성 자동 대기 | ✅ |
| **안정성** | Self-Healing | 로케이터 실패 시 Fallback 자동 시도 | ✅ |

### 🔄 현재 진행 중 / 개선 필요 사항

| 구분 | 항목 | 상세 | 우선순위 |
| :--- | :--- | :--- | :---: |
| **리팩토링** | POM 패턴 확대 적용 | 기존 코어 모듈에도 POM 패턴 일관 적용 필요 | 🟡 중 |
| **테스트** | 유닛 테스트 보강 | 각 코어 모듈에 대한 자동화된 유닛 테스트 작성 필요 | 🟡 중 |
| **안정성** | CI/CD 파이프라인 실테스트 | 실제 GitHub Actions에서 정상 동작 검증 필요 | 🔴 높음 |
| **안정성** | 크로스 브라우저 테스트 | Firefox/Edge/Safari에서 실제 실행 검증 필요 | 🟡 중 |

### 📋 남은 로드맵 (TODO)

| 버전 | 목표 | 상세 내용 | 상태 |
| :--- | :--- | :--- | :---: |
| **v7.1** | 안정화 | CI/CD 실환경 테스트, 크로스 브라우저 검증, 에러 핸들링 보강 | ⏳ 예정 |
| **v8.0** | 검증 고도화 | **Phase 4** - Hybrid QA (API 연동) + 품질 메트릭 대시보드 | 🔲 미착수 |
| **v9.0** | AI 자동화 | **Phase 5** - LLM 기반 자연어 → 테스트 코드 자동 생성 | � 미착수 |
| **v10.0** | 배포 | PyInstaller `.exe` 패키징, 설치 프로그램 제작, 자동 업데이트 | � 구상 |

---

### 🔷 Phase 4. 검증 고도화: Hybrid QA 및 메트릭 (과제 9, 10)

> UI를 넘어 API까지 검증하고 품질 지표를 산출하는 단계

#### 과제 9: API 연동 테스트 (Hybrid QA)

**목표**: UI 테스트와 API 테스트를 결합하여, UI 조작 전후의 서버/DB 상태를 자동 검증

| 항목 | 내용 |
| :--- | :--- |
| **핵심 라이브러리** | `requests` |
| **구현 대상** | `core/api_tester.py` (신규 모듈) |
| **기능** | REST API 호출 (GET/POST/PUT/DELETE), 응답 상태코드/JSON 바디 검증 |
| **시나리오 예시** | ① UI에서 상품 장바구니 담기 → ② API로 장바구니 목록 조회 → ③ 해당 상품이 존재하는지 검증 |
| **연동 방식** | 기존 스텝 액션에 `api_get`, `api_post`, `api_assert` 등 새 액션 타입 추가 |
| **인증 지원** | Bearer Token, Basic Auth, Cookie 기반 인증 헤더 자동 설정 |

```
[ UI 테스트 ] ──→ 로그인, 상품 클릭, 구매 버튼 클릭
      ↓
[ API 검증 ] ──→ GET /api/cart → 상품이 담겼는지 JSON 응답 확인
      ↓
[ 결과 리포트 ] ──→ UI + API 결합 결과를 하나의 리포트에 출력
```

#### 과제 10: 품질 메트릭 대시보드

**목표**: 테스트 실행 결과를 정량적 품질 지표로 산출하여 리포트 하단에 출력

| 메트릭 | 계산 방식 | 출력 형태 |
| :--- | :--- | :--- |
| **자동화 성공률** | `(성공 테스트 / 전체 테스트) × 100%` | `✅ 성공률: 87.5% (7/8)` |
| **평균 실행 시간** | `총 소요시간 / 전체 테스트 수` | `⏱️ 평균: 3.2초/테스트` |
| **총 실행 시간** | 시작~종료 시간차 | `🕐 총 소요: 25.6초` |
| **테스트 커버리지** | `(자동화 스텝 / 전체 시나리오 스텝) × 100%` | `📊 커버리지: 92%` |
| **실패 분석** | 실패 원인 카테고리 분류 (Timeout/Element/Assert/API) | 카테고리별 실패 건수 |

**산출물:**
- [ ] `core/metrics.py` — 메트릭 수집/계산 모듈
- [ ] `core/api_tester.py` — API 통합 테스트 모듈
- [ ] 터미널 품질 요약 리포트 출력
- [ ] HTML 리포트 하단에 품질 메트릭 섹션 추가

---

### 🔮 Phase 5. 미래 기술: AI 기반 자동화 (과제 7)

> 프로젝트 이름 "AutoTestBuilder"에 걸맞은 LLM 연동 자동 생성 단계

#### 과제 7: LLM 기반 자연어 테스트 생성기 (Builder)

**목표**: 사용자가 자연어로 테스트 시나리오를 설명하면, POM 구조에 맞는 Pytest 코드 초안을 자동 생성

| 항목 | 내용 |
| :--- | :--- |
| **지원 LLM** | OpenAI API (GPT-4o) 또는 Google Gemini API |
| **구현 대상** | `core/ai_builder.py` (신규 모듈) |
| **입력 예시** | `"네이버에서 '노트북' 검색 후 첫 번째 상품 장바구니 담기"` |
| **출력** | BasePage를 상속받는 PageObject + TestScript Python 코드 |
| **프롬프트 설계** | 기존 BasePage/PageObject 코드를 컨텍스트로 주입하여 호환성 보장 |

**동작 흐름:**
```
사용자 입력 (자연어)
    ↓
┌─────────────────────────────────────┐
│  프롬프트 엔진 (ai_builder.py)       │
│  ┌───────────────────────────────┐  │
│  │ 시스템 프롬프트:               │  │
│  │ - BasePage 클래스 코드         │  │
│  │ - 지원 액션 목록               │  │
│  │ - POM 구조 규칙               │  │
│  │ - 출력 포맷 지정 (Python)      │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 유저 프롬프트:                 │  │
│  │ "네이버에서 상품 검색 후        │  │
│  │  장바구니 담기"                │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
LLM API 호출 (GPT-4o / Gemini)
    ↓
생성된 코드 파싱 + 검증
    ↓
┌─────────────────────────────────────┐
│ 출력: POM 프로젝트 파일             │
│  ├── pages/naver_page.py           │
│  └── tests/test_naver_cart.py      │
└─────────────────────────────────────┘
```

**프롬프트 템플릿 핵심 설계:**
1. **컨텍스트 주입** — 기존 `BasePage` 코드를 시스템 프롬프트에 포함 → 생성 코드가 `BasePage`를 상속
2. **액션 제약** — 지원되는 액션(`click`, `input`, `check_text` 등)만 사용하도록 지시
3. **구조 강제** — POM 3계층(BasePage → PageObject → TestScript) 형태로 출력되도록 JSON Schema 지정
4. **즉시 실행 가능** — `conftest.py` 드라이버 설정까지 포함하여 `pytest`로 바로 실행 가능

**산출물:**
- [ ] `core/ai_builder.py` — LLM 연동 코드 생성 모듈
- [ ] `core/prompt_templates.py` — 프롬프트 템플릿 관리
- [ ] GUI에 "🤖 AI 생성" 탭 또는 버튼 추가
- [ ] `config.yaml`에 `ai.provider`, `ai.api_key`, `ai.model` 설정 추가
- [ ] 생성 코드 미리보기 + 편집 + POM 프로젝트 내보내기 연동

### 📁 현재 프로젝트 구조

```
QA_AutoTestBuilder/
├── main.py                    # GUI 진입점
├── run_tests.py               # CLI 실행기
├── config.py                  # 설정 모듈 (환경변수 + YAML)
├── config.yaml                # YAML 설정 파일
├── requirements.txt           # 의존성 목록
│
├── core/                      # 핵심 엔진
│   ├── scanner.py             # 웹 요소 스캐너 (로케이터 분석)
│   ├── generator.py           # Pytest 스크립트 생성기
│   ├── pom_generator.py       # POM 프로젝트 생성기
│   ├── runner.py              # 테스트 실행기
│   ├── browser.py             # 브라우저 매니저
│   ├── browser_config.py      # 멀티 브라우저 설정
│   ├── data_loader.py         # DDT 데이터 로더
│   ├── html_reporter.py       # 내장 HTML 리포터
│   ├── reporter.py            # Allure 리포터
│   ├── ci_generator.py        # CI/CD 설정 생성기
│   ├── plugin_manager.py      # 플러그인 매니저
│   └── pytest_html_plugin.py  # Pytest HTML 플러그인
│
├── gui/                       # GUI 레이어
│   ├── qt_app.py              # PySide6 메인 윈도우 (v7.0 Pro)
│   ├── qt_components.py       # 커스텀 위젯/모델
│   └── data_model.py          # DataFrame 데이터 모델
│
├── utils/                     # 유틸리티
│   ├── logger.py              # 로깅 시스템
│   ├── database.py            # SQLite DB 관리
│   ├── file_manager.py        # 파일/암호화 관리
│   ├── excel_loader.py        # 엑셀 로더
│   └── locator_utils.py       # 로케이터 헬퍼
│
├── scripts/                   # 검증 스크립트
│   ├── verify_all.py          # 전체 검증
│   ├── verify_phase2.py       # Phase 2 검증
│   ├── verify_phase3.py       # Phase 3 검증
│   └── verify_pom.py          # POM 검증
│
├── plugins/                   # 확장 플러그인
├── data/                      # 테스트 데이터
├── .github/workflows/         # CI/CD
│   └── main.yml               # GitHub Actions 워크플로우
│
└── 메모장.md                   # 이 문서
```

---

> 📌 **요약**: QA Auto Test Builder는 No-Code로 웹 테스트를 자동화하는 데스크톱 도구로, 브라우저에서 요소를 클릭하는 것만으로 Pytest + POM 구조의 완전한 테스트 프로젝트를 생성할 수 있다. 현재 핵심 기능은 모두 완성되었으며, CI/CD 실환경 검증과 `.exe` 배포가 다음 목표이다.
