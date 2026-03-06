"""
QA Auto Test Builder 설정 모듈

환경변수로 설정을 오버라이드할 수 있습니다.
환경변수명: QA_ATB_{설정명}
"""

import os
from pathlib import Path


def _get_env(key: str, default, cast_type=str):
    """
    환경변수에서 설정값 가져오기

    Args:
        key: 환경변수 키 (QA_ATB_ 접두사 자동 추가)
        default: 기본값
        cast_type: 타입 변환 함수

    Returns:
        설정값
    """
    env_key = f"QA_ATB_{key}"
    value = os.getenv(env_key)
    if value is None:
        return default
    try:
        if cast_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        return cast_type(value)
    except (ValueError, TypeError):
        return default


# ============================================================
# 기본 설정
# ============================================================

# 기본 테스트 URL
DEFAULT_URL = _get_env("DEFAULT_URL", "https://www.saucedemo.com/")

# 기본 브라우저 (chrome, firefox, edge)
DEFAULT_BROWSER = _get_env("DEFAULT_BROWSER", "chrome")


# ============================================================
# 타임아웃 설정
# ============================================================

# 명시적 대기 시간 (초)
EXPLICIT_WAIT = _get_env("EXPLICIT_WAIT", 30, int)

# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = _get_env("PAGE_LOAD_TIMEOUT", 60, int)

# 스크립트 실행 타임아웃 (초)
SCRIPT_TIMEOUT = _get_env("SCRIPT_TIMEOUT", 30, int)


# ============================================================
# UI 설정
# ============================================================

# 하이라이트 색상
HIGHLIGHT_COLOR = _get_env("HIGHLIGHT_COLOR", "red")

# 하이라이트 테두리 두께
HIGHLIGHT_BORDER = _get_env("HIGHLIGHT_BORDER", "5px")


# ============================================================
# 파일 경로 설정
# ============================================================

import sys

# 프로젝트 루트 디렉토리
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller로 패키징된 경우 임시 디렉토리 사용
    PROJECT_ROOT = Path(sys._MEIPASS).resolve()
    # 실행 파일이 있는 위치 (DB 저장용)
    EXEC_DIR = Path(sys.executable).parent.resolve()
else:
    # 일반 스크립트 실행
    PROJECT_ROOT = Path(__file__).parent.resolve()
    EXEC_DIR = PROJECT_ROOT

# 임시 테스트 파일 경로
TEMP_TEST_FILE = _get_env("TEMP_TEST_FILE", str(EXEC_DIR / "temp_test.py"))

# Allure 결과 디렉토리
ALLURE_RESULTS_DIR = _get_env("ALLURE_RESULTS_DIR", str(EXEC_DIR / "allure_results"))

# 로그 디렉토리
LOG_DIR = _get_env("LOG_DIR", str(EXEC_DIR / "logs"))

# 데이터베이스 파일 경로
DB_PATH = _get_env("DB_PATH", str(EXEC_DIR / "testcases.db"))

# DDT 데이터 디렉토리
DATA_DIR = _get_env("DATA_DIR", str(EXEC_DIR / "data"))

# 기본 데이터 포맷 (json, csv, excel)
DEFAULT_DATA_FORMAT = _get_env("DEFAULT_DATA_FORMAT", "json")


# ============================================================
# 로깅 설정
# ============================================================

# 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = _get_env("LOG_LEVEL", "INFO")

# 파일 로깅 활성화
LOG_TO_FILE = _get_env("LOG_TO_FILE", True, bool)

# 로그 파일 최대 크기 (MB)
LOG_MAX_SIZE_MB = _get_env("LOG_MAX_SIZE_MB", 10, int)

# 로그 파일 백업 개수
LOG_BACKUP_COUNT = _get_env("LOG_BACKUP_COUNT", 5, int)


# ============================================================
# 테스트 실행 설정
# ============================================================

# 기본 병렬 워커 수 (0 = 자동)
DEFAULT_PARALLEL_WORKERS = _get_env("DEFAULT_PARALLEL_WORKERS", 1, int)

# 헤드리스 모드 기본값
DEFAULT_HEADLESS = _get_env("DEFAULT_HEADLESS", False, bool)

# 테스트 실패 시 스크린샷 자동 저장
SCREENSHOT_ON_FAILURE = _get_env("SCREENSHOT_ON_FAILURE", True, bool)

# 테스트 실패 시 자동 재시도 횟수 (Self-Healing)
RETRY_COUNT = _get_env("RETRY_COUNT", 1, int)

# 스크린샷 저장 디렉토리
SCREENSHOT_DIR = _get_env("SCREENSHOT_DIR", str(EXEC_DIR / "screenshots"))


# ============================================================
# 리포트 설정
# ============================================================

# 내장 HTML 리포터 사용 여부 (False=Allure 사용)
USE_BUILTIN_REPORTER = _get_env("USE_BUILTIN_REPORTER", False, bool)

# HTML 리포트 저장 디렉토리
HTML_REPORT_DIR = _get_env("HTML_REPORT_DIR", str(PROJECT_ROOT / "reports"))


# ============================================================
# 보안 설정
# ============================================================

# 암호화 키 환경변수 이름 (file_manager.py에서 사용)
ENCRYPTION_KEY_ENV = "ENCRYPTION_KEY"


# ============================================================
# 디렉토리 자동 생성
# ============================================================

def ensure_directories():
    """필요한 디렉토리 생성"""
    dirs = [LOG_DIR, ALLURE_RESULTS_DIR, SCREENSHOT_DIR]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


# 모듈 로드 시 디렉토리 생성
ensure_directories()


# ============================================================
# YAML 설정 파일 지원
# ============================================================

# 기본 YAML 설정 파일 경로
YAML_CONFIG_PATH = str(EXEC_DIR / "config.yaml")


def load_yaml_config(yaml_path=None):
    """
    config.yaml에서 설정을 읽어 모듈 변수를 오버라이드합니다.

    우선순위: 환경변수 > YAML > 기본값
    (환경변수가 설정된 항목은 YAML보다 우선합니다)

    Args:
        yaml_path: YAML 파일 경로 (None이면 기본 경로 사용)

    Returns:
        dict: 로드된 YAML 설정 (파일 없으면 빈 딕셔너리)
    """
    import yaml

    path = yaml_path or YAML_CONFIG_PATH
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        return {}

    g = globals()

    # browsers 섹션
    browsers = cfg.get("browsers", {})
    if browsers:
        if "default" in browsers and not os.getenv("QA_ATB_DEFAULT_BROWSER"):
            g["DEFAULT_BROWSER"] = browsers["default"]
        if "headless" in browsers and not os.getenv("QA_ATB_DEFAULT_HEADLESS"):
            g["DEFAULT_HEADLESS"] = bool(browsers["headless"])

    # test 섹션
    test = cfg.get("test", {})
    if test:
        if "parallel_workers" in test and not os.getenv("QA_ATB_DEFAULT_PARALLEL_WORKERS"):
            g["DEFAULT_PARALLEL_WORKERS"] = int(test["parallel_workers"])
        if "retry_count" in test and not os.getenv("QA_ATB_RETRY_COUNT"):
            g["RETRY_COUNT"] = int(test["retry_count"])
        if "timeout" in test and not os.getenv("QA_ATB_EXPLICIT_WAIT"):
            g["EXPLICIT_WAIT"] = int(test["timeout"])

    # report 섹션
    report = cfg.get("report", {})
    if report:
        if "type" in report and not os.getenv("QA_ATB_USE_BUILTIN_REPORTER"):
            g["USE_BUILTIN_REPORTER"] = (report["type"] == "html")
        if "allure_results_dir" in report and not os.getenv("QA_ATB_ALLURE_RESULTS_DIR"):
            g["ALLURE_RESULTS_DIR"] = str(EXEC_DIR / report["allure_results_dir"])
        if "screenshot_dir" in report and not os.getenv("QA_ATB_SCREENSHOT_DIR"):
            g["SCREENSHOT_DIR"] = str(EXEC_DIR / report["screenshot_dir"])
        if "screenshot_on_failure" in report and not os.getenv("QA_ATB_SCREENSHOT_ON_FAILURE"):
            g["SCREENSHOT_ON_FAILURE"] = bool(report["screenshot_on_failure"])

    return cfg
