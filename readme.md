# 🚀 No-Code Test Automation Builder (QA Auto Test Builder)

**No-Code Selenium Test Automation Platform** allows you to create, manage, and execute automated tests without writing code.

## 🚀 주요 기능

- **No-Code 시나리오 작성**: 브라우저에서 요소를 클릭하거나 텍스트를 드래그하여 자동으로 테스트 스텝을 생성합니다.
- **강력한 요소 식별**: ID, XPath, CSS, Text 등 다양한 로케이터를 지원하며, **Shadow DOM** 및 **Self-Healing(자동 복구)** 기능을 제공합니다.
- **데이터 주도 테스트 (DDT)**: 엑셀 파일을 로드하여 변수(`{변수명}`)를 바인딩하고 대량의 데이터를 테스트할 수 있습니다.
- **POM 프로젝트 생성**: 작성한 시나리오를 유지보수가 용이한 **Page Object Model** 구조의 Python 프로젝트로 내보냅니다.
- **자동 대기 (Smart Wait)**: 네트워크 유휴 상태 및 요소 가시성을 자동으로 감지하여 테스트 안정성을 높입니다.

## 📦 설치 방법

Python 3.8 이상이 필요합니다.

```bash
# 의존성 설치
pip install -r requirements.txt
```

> **참고**: Playwright나 별드라이버 설치는 필요 없으며, 실행 시 `webdriver-manager`가 자동으로 드라이버를 관리합니다.

## 🎮 사용 방법

### 1. 프로그램 실행
```bash
python main.py
```

### 2. 기본 워크플로우

1.  **브라우저 열기**:
    - URL과 브라우저(Chrome/Edge 등)를 선택하고 `🌐 브라우저 열기` 버튼을 클릭합니다.
2.  **스텝 작성 (스캔 모드)**:
    - 브라우저에서 테스트할 화면으로 이동합니다.
    - 원하는 요소를 클릭하거나 텍스트를 드래그한 상태에서 **`F2` 키**를 누르거나 프로그램의 `🎯 요소 스캔` 버튼을 누릅니다.
    - 자동으로 적절한 로케이터와 액션(Click, Input 등)이 리스트에 추가됩니다.
3.  **데이터 바인딩 (선택 사항)**:
    - '데이터 관리' 탭에서 엑셀 파일을 로드합니다.
    - 스텝의 `Value` 입력란에 `{아이디}`, `{비밀번호}`와 같이 엑셀 컬럼명을 입력하여 변수화합니다.
4.  **테스트 실행 또는 내보내기**:
    - **실행**: '실행 & 로그' 탭에서 바로 테스트를 실행하여 결과를 확인합니다.
    - **내보내기**: 상단의 `📦 POM 내보내기` 버튼을 눌러 독립적인 파이썬 프로젝트로 저장합니다.

## 💡 주요 팁

- **Shadow DOM**: 복잡한 웹 컴포넌트 내부 요소도 자동으로 감지하고 경로를 추적합니다.
- **검증(Assertion)**: 텍스트를 드래그하고 스캔하면 자동으로 `check_text` 검증 스텝이 생성됩니다.
- **Self-Healing**: 요소의 속성이 변경되어도 다른 로케이터를 자동으로 시도하여 테스트 실패를 방지합니다.

### 🟡 엑셀 데이터 연동하기 (DDT)
1.  **엑셀 준비:** 첫 줄에 변수명(헤더)을 적고 데이터를 채웁니다. (예: `ID`, `PW`, `EXPECTED`)
2.  **[📊 엑셀 데이터 연동]** 버튼을 눌러 파일을 불러옵니다.
3.  시나리오 입력칸에 변수를 중괄호와 함께 적습니다. (예: `{ID}`, `{PW}`)
4.  실행하면 엑셀 데이터 줄 수만큼 테스트가 반복됩니다.

### 🔵 액션(Action) 종류 설명

| 액션명 | 설명 | 비고 |
| :--- | :--- | :--- |
| **click** | 요소를 클릭합니다. | JS 강제 클릭 지원 |
| **input** | 텍스트를 입력합니다. | |
| **input_password** | 비밀번호를 입력합니다. | 화면 마스킹(`***`) 처리 |
| **press_key** | 특수키를 입력합니다. | `ENTER`, `TAB` 등 |
| **check_text** | 화면에 특정 글자가 있는지 검증합니다. | 실패 시 스크린샷 |
| **check_url** | 페이지 URL이 변경되었는지 검증합니다. | |
| **switch_frame** | Iframe 내부로 진입합니다. | |
| **accept_alert** | 브라우저 경고창을 '확인'합니다. | |
| **drag_source** | 드래그할 요소를 잡습니다. | |
| **drop_target** | 잡은 요소를 이곳에 놓습니다. | |

---

## 🗺️ 개발 로드맵 (Roadmap)

- [x] **v1.0 (Core):** 모듈화 구조 설계 및 기본 스캔/실행 기능
- [x] **v2.0 (Smart):** Smart Wait, Assertion(검증), 텍스트 드래그 스캔
- [x] **v2.5 (UX/Security):** 단축키(F2), 비밀번호 암호화, 드래그 앤 드롭
- [x] **v3.0 (Stability):** Iframe/Alert 처리, 크롬 보안 팝업 완벽 차단
- [x] **v4.0 (Data):** 엑셀 기반 데이터 주도 테스트(DDT) 및 변수 치환
- [ ] **v5.0 (AI):** Self-Healing (요소 변경 시 자동 복구) 예정
- [ ] **v6.0 (Dist):** 실행 파일(.exe) 배포 예정

---

## 📄 라이선스 (License)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
