#!/usr/bin/env python3
"""
QA Auto Test Builder - CLI 실행기

argparse 기반 CLI에서 브라우저 지정, 헤드리스 모드, DDT 데이터 파일 등을
지정하여 테스트를 실행합니다.

사용법:
    python run_tests.py                                    # config.yaml 기본 설정
    python run_tests.py --browser firefox                  # 브라우저 지정
    python run_tests.py --browser chrome --headless        # 헤드리스 모드
    python run_tests.py --data data/test_cases.json        # DDT 데이터 경로
    python run_tests.py --parallel 4                       # 병렬 실행
    python run_tests.py --config my_config.yaml            # 커스텀 설정 파일
    python run_tests.py --test-file first.json             # 테스트 시나리오 파일
    python run_tests.py --list-browsers                    # 지원 브라우저 목록
"""

import argparse
import sys
import os
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def parse_args():
    """CLI 인자 파서"""
    parser = argparse.ArgumentParser(
        prog="run_tests",
        description="QA Auto Test Builder - CLI 테스트 실행기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --browser firefox --headless
  %(prog)s --data data/test_cases.json --parallel 4
  %(prog)s --config custom_config.yaml --browser edge
  %(prog)s --test-file first.json --browser chrome --headless
        """,
    )

    # 브라우저 설정
    browser_group = parser.add_argument_group("Browser Options")
    browser_group.add_argument(
        "-b", "--browser",
        choices=["chrome", "firefox", "edge", "safari"],
        default=None,
        help="브라우저 지정 (default: config.yaml의 browsers.default)",
    )
    browser_group.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="헤드리스 모드 실행 (GUI 없이)",
    )
    browser_group.add_argument(
        "--no-headless",
        action="store_true",
        default=False,
        help="헤드리스 모드 비활성화 (config.yaml 오버라이드)",
    )
    browser_group.add_argument(
        "--list-browsers",
        action="store_true",
        help="지원하는 브라우저 목록 출력 후 종료",
    )

    # 테스트 설정
    test_group = parser.add_argument_group("Test Options")
    test_group.add_argument(
        "-t", "--test-file",
        default=None,
        help="테스트 시나리오 JSON 파일 경로",
    )
    test_group.add_argument(
        "-d", "--data",
        default=None,
        help="DDT 데이터 파일 경로 (JSON/CSV/Excel)",
    )
    test_group.add_argument(
        "-u", "--url",
        default=None,
        help="테스트 URL (시나리오 파일 내 URL 오버라이드)",
    )
    test_group.add_argument(
        "-p", "--parallel",
        type=int,
        default=None,
        help="병렬 워커 수 (default: 1)",
    )
    test_group.add_argument(
        "--retry",
        type=int,
        default=None,
        help="실패 시 재시도 횟수",
    )

    # 설정 파일
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "-c", "--config",
        default=None,
        help="YAML 설정 파일 경로 (default: config.yaml)",
    )

    # 리포트
    report_group = parser.add_argument_group("Report Options")
    report_group.add_argument(
        "--report",
        choices=["allure", "html"],
        default=None,
        help="리포트 형식 (default: allure)",
    )
    report_group.add_argument(
        "--open-report",
        action="store_true",
        help="테스트 완료 후 리포트 자동 열기",
    )

    return parser.parse_args()


def list_browsers():
    """지원 브라우저 목록 출력"""
    from core.browser_config import BrowserConfig

    print("\n🌐 지원 브라우저 목록:")
    print("=" * 40)
    for browser in BrowserConfig.SUPPORTED_BROWSERS:
        note = " (macOS only)" if browser == "safari" else ""
        default_marker = " ← default" if browser == config.DEFAULT_BROWSER else ""
        print(f"  • {browser}{note}{default_marker}")
    print()
    print(f"현재 설정: browser={config.DEFAULT_BROWSER}, headless={config.DEFAULT_HEADLESS}")
    print()


def run(args):
    """테스트 실행"""
    from core.generator import ScriptGenerator
    from core.runner import TestRunner

    # 1. YAML 설정 로드
    yaml_cfg = config.load_yaml_config(args.config)

    # 2. CLI 인자로 오버라이드
    browser = args.browser or config.DEFAULT_BROWSER
    headless = config.DEFAULT_HEADLESS
    if args.headless:
        headless = True
    elif args.no_headless:
        headless = False

    data_path = args.data
    if data_path is None and yaml_cfg:
        test_cfg = yaml_cfg.get("test", {})
        data_path = test_cfg.get("data_path")

    parallel = args.parallel or config.DEFAULT_PARALLEL_WORKERS
    retry = args.retry
    if retry is not None:
        config.RETRY_COUNT = retry

    # 리포트 설정
    if args.report == "html":
        config.USE_BUILTIN_REPORTER = True
    elif args.report == "allure":
        config.USE_BUILTIN_REPORTER = False

    # 3. 테스트 시나리오 파일 결정
    test_file = args.test_file
    if test_file is None and yaml_cfg:
        test_file = yaml_cfg.get("test", {}).get("test_file")

    if test_file is None:
        # 기본 시나리오 파일 검색
        for candidate in ["first.json", "test_scenario.json"]:
            if os.path.exists(candidate):
                test_file = candidate
                break

    if test_file is None:
        print("\n❌ 테스트 시나리오 파일을 찾을 수 없습니다.")
        print("   --test-file 옵션 또는 config.yaml의 test.test_file을 설정하세요.")
        sys.exit(1)

    # 4. 시나리오 파일 로드
    print(f"\n{'='*60}")
    print(f"🚀 QA Auto Test Builder - CLI Runner")
    print(f"{'='*60}")
    print(f"  Browser:  {browser}")
    print(f"  Headless: {headless}")
    print(f"  Scenario: {test_file}")
    print(f"  Data:     {data_path or '(none)'}")
    print(f"  Parallel: {parallel}")
    print(f"  Report:   {'HTML' if config.USE_BUILTIN_REPORTER else 'Allure'}")
    print(f"{'='*60}\n")

    try:
        with open(test_file, "r", encoding="utf-8") as f:
            scenario = json.load(f)
    except Exception as e:
        print(f"\n❌ 시나리오 파일 로드 실패: {e}")
        sys.exit(1)

    # URL 결정
    url = args.url
    if url is None and yaml_cfg:
        url = yaml_cfg.get("test", {}).get("url")
    if url is None:
        url = scenario.get("url", config.DEFAULT_URL)

    steps = scenario.get("steps", [])
    if not steps:
        print("\n❌ 테스트 스텝이 없습니다.")
        sys.exit(1)

    # 5. 스크립트 생성
    generator = ScriptGenerator()
    script = generator.generate(
        url=url,
        steps=steps,
        is_headless=headless,
        data_path=data_path,
        browser_type=browser,
    )

    output_file = config.TEMP_TEST_FILE
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"✅ 테스트 스크립트 생성: {output_file}")

    # 6. 테스트 실행
    runner = TestRunner()
    print(f"\n🏃 테스트 실행 중...\n")
    process = runner.run_pytest(parallel_workers=parallel)

    # 실행 결과 대기 및 출력
    if hasattr(process, "stdout") and process.stdout:
        for line in process.stdout:
            print(line, end="")
        process.wait()
        rc = process.returncode
    else:
        # MockProcess (frozen 환경)
        import time
        while not hasattr(process, "_returncode") or process._returncode is None:
            time.sleep(0.5)
        rc = process._returncode

    # 7. 결과 출력
    print(f"\n{'='*60}")
    if rc == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️  테스트 실패 (exit code: {rc})")
    print(f"{'='*60}\n")

    # 8. 리포트 자동 열기
    if args.open_report:
        print("📊 리포트 열기...")
        runner.open_report()

    return rc


def main():
    args = parse_args()

    # 브라우저 목록 출력 후 종료
    if args.list_browsers:
        # YAML 설정 먼저 로드
        config.load_yaml_config(args.config)
        list_browsers()
        sys.exit(0)

    rc = run(args)
    sys.exit(rc)


if __name__ == "__main__":
    main()
