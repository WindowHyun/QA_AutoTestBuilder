"""
Phase 3 검증: 멀티 브라우저, config.yaml, CLI, GitHub Actions
"""

import sys
import os

sys.path.append(os.getcwd())

import config
from core.browser_config import BrowserConfig
from core.ci_generator import CIGenerator


def check(condition, message):
    if condition:
        print(f"  [PASS] {message}")
        return True
    else:
        print(f"  [FAIL] {message}")
        return False


def verify_phase3():
    print("=" * 60)
    print("Phase 3 Verification: Multi-Browser + CI/CD")
    print("=" * 60)

    passed = 0
    failed = 0

    def track(result):
        nonlocal passed, failed
        if result:
            passed += 1
        else:
            failed += 1

    # ─── 1. config.yaml ─────────────────────────────
    print("\n[1] config.yaml 검증")
    print("-" * 40)

    track(check(os.path.exists("config.yaml"), "config.yaml 파일 존재"))

    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    track(check("browsers" in cfg, "browsers 섹션 존재"))
    track(check("test" in cfg, "test 섹션 존재"))
    track(check("report" in cfg, "report 섹션 존재"))
    track(check("ci" in cfg, "ci 섹션 존재"))

    browsers = cfg["browsers"]
    track(check(browsers["default"] in ["chrome", "firefox", "edge", "safari"],
                f"기본 브라우저: {browsers['default']}"))
    track(check("headless" in browsers, "headless 설정 존재"))
    track(check("chrome" in browsers, "Chrome 옵션 존재"))
    track(check("firefox" in browsers, "Firefox 옵션 존재"))
    track(check("safari" in browsers, "Safari 옵션 존재"))
    track(check("edge" in browsers, "Edge 옵션 존재"))
    track(check("slack_webhook_url" in cfg["ci"], "Slack webhook 설정 존재"))

    # ─── 2. YAML 로더 ─────────────────────────────
    print("\n[2] config.py YAML 로더 검증")
    print("-" * 40)

    track(check(hasattr(config, "load_yaml_config"), "load_yaml_config 함수 존재"))
    track(check(hasattr(config, "YAML_CONFIG_PATH"), "YAML_CONFIG_PATH 상수 존재"))

    yaml_cfg = config.load_yaml_config("config.yaml")
    track(check(isinstance(yaml_cfg, dict), "YAML 로드 결과: dict"))
    track(check("browsers" in yaml_cfg, "YAML 로드: browsers 섹션"))
    track(check(config.DEFAULT_BROWSER in ["chrome", "firefox", "edge", "safari"],
                f"YAML -> DEFAULT_BROWSER = {config.DEFAULT_BROWSER}"))

    # 존재하지 않는 파일
    empty = config.load_yaml_config("nonexistent.yaml")
    track(check(empty == {}, "미존재 YAML: 빈 딕셔너리 반환"))

    # ─── 3. CLI argparse ─────────────────────────────
    print("\n[3] CLI 실행기 (run_tests.py) 검증")
    print("-" * 40)

    track(check(os.path.exists("run_tests.py"), "run_tests.py 파일 존재"))

    with open("run_tests.py", "r", encoding="utf-8") as f:
        cli_code = f.read()

    track(check("argparse" in cli_code, "argparse 임포트"))
    track(check("--browser" in cli_code, "--browser 옵션"))
    track(check("--headless" in cli_code, "--headless 옵션"))
    track(check("--data" in cli_code, "--data 옵션"))
    track(check("--parallel" in cli_code, "--parallel 옵션"))
    track(check("--config" in cli_code, "--config 옵션"))
    track(check("--test-file" in cli_code, "--test-file 옵션"))
    track(check("--open-report" in cli_code, "--open-report 옵션"))
    track(check("--list-browsers" in cli_code, "--list-browsers 옵션"))
    track(check("safari" in cli_code, "Safari 옵션 포함"))
    track(check("load_yaml_config" in cli_code, "YAML 로드 호출"))

    # argparse 파싱 테스트
    sys.argv = ["run_tests.py", "--browser", "firefox", "--headless"]
    from run_tests import parse_args
    args = parse_args()
    track(check(args.browser == "firefox", "argparse: --browser firefox"))
    track(check(args.headless == True, "argparse: --headless"))
    sys.argv = ["run_tests.py"]  # reset

    # ─── 4. Safari 지원 ─────────────────────────────
    print("\n[4] Safari 지원 검증 (browser_config.py)")
    print("-" * 40)

    track(check("safari" in BrowserConfig.SUPPORTED_BROWSERS, "SUPPORTED_BROWSERS에 safari 포함"))
    track(check(hasattr(BrowserConfig, "get_safari_options"), "get_safari_options 메서드"))
    track(check(hasattr(BrowserConfig, "_safari_code_template"), "_safari_code_template 메서드"))

    safari_code = BrowserConfig.generate_driver_code("safari", headless=False)
    track(check("Safari" in safari_code["driver"], "Safari 드라이버 코드 생성"))
    track(check("SafariOptions" in safari_code["init"], "SafariOptions 초기화 코드"))

    # 기존 브라우저 호환성
    for br in ["chrome", "firefox", "edge"]:
        code = BrowserConfig.generate_driver_code(br, headless=True)
        track(check("driver" in code, f"{br} 드라이버 코드 생성 유지"))

    # ─── 5. GitHub Actions ─────────────────────────────
    print("\n[5] GitHub Actions 워크플로우 검증")
    print("-" * 40)

    workflow_path = os.path.join(".github", "workflows", "main.yml")
    track(check(os.path.exists(workflow_path), "main.yml 파일 존재"))

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = f.read()

    track(check("matrix:" in workflow, "매트릭스 전략 포함"))
    track(check("chrome" in workflow and "firefox" in workflow, "Chrome/Firefox 매트릭스"))
    track(check("--headless" in workflow, "헤드리스 실행"))
    track(check("SLACK_WEBHOOK_URL" in workflow, "Slack webhook 참조"))
    track(check("slack-github-action" in workflow, "Slack action 사용"))
    track(check("upload-artifact" in workflow, "아티팩트 업로드"))
    track(check("allure-results" in workflow, "Allure 결과 업로드"))
    track(check("screenshots" in workflow, "스크린샷 업로드"))
    track(check("workflow_dispatch" in workflow, "수동 실행 트리거"))
    track(check("run_tests.py" in workflow, "CLI 실행기 사용"))

    # ─── 6. CI Generator ─────────────────────────────
    print("\n[6] CI Generator 업데이트 검증")
    print("-" * 40)

    ci_gen = CIGenerator()

    # Slack 없이
    basic = ci_gen.generate_github_actions("chrome", slack_webhook=False)
    track(check("matrix:" in basic, "CI Gen 기본: 매트릭스 포함"))
    track(check("SLACK" not in basic, "CI Gen 기본: Slack 없음"))

    # Slack 있이
    with_slack = ci_gen.generate_github_actions("firefox", slack_webhook=True)
    track(check("matrix:" in with_slack, "CI Gen Slack: 매트릭스 포함"))
    track(check("Slack" in with_slack, "CI Gen Slack: Slack job 포함"))

    # Jenkins
    jenkins = ci_gen.generate_jenkinsfile()
    track(check("pipeline" in jenkins, "Jenkins: pipeline 키워드"))
    track(check("BROWSER" in jenkins, "Jenkins: BROWSER 파라미터"))

    # ─── Summary ─────────────────────────────
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Result: {passed}/{total} PASSED, {failed}/{total} FAILED")
    if failed == 0:
        print("Phase 3 ALL VERIFICATIONS PASSED!")
    else:
        print(f"WARNING: {failed} items failed!")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    verify_phase3()
