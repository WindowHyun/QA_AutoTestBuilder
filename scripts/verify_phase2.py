
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from core.generator import ScriptGenerator
from core.pom_generator import POMGenerator
from core.data_loader import DataLoader

def check(condition, message):
    if condition:
        print(f"✅ [PASS] {message}")
        return True
    else:
        print(f"❌ [FAIL] {message}")
        return False

def verify_phase2():
    print("="*60)
    print("🚀 Phase 2 Verification: DDT + Allure Report")
    print("="*60)

    passed = 0
    failed = 0

    def track(result):
        nonlocal passed, failed
        if result:
            passed += 1
        else:
            failed += 1

    # ---------------------------------------------------------
    # 1. DataLoader 모듈 검증
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 2] DataLoader 모듈 검증")
    print("="*60)

    loader = DataLoader()

    # 1-1. 포맷 감지
    track(check(loader.detect_format("test.json") == "json", "detect_format: JSON 감지"))
    track(check(loader.detect_format("test.csv") == "csv", "detect_format: CSV 감지"))
    track(check(loader.detect_format("test.xlsx") == "excel", "detect_format: Excel 감지"))
    track(check(loader.detect_format("test.xls") == "excel", "detect_format: XLS 감지"))

    # 1-2. 지원하지 않는 포맷
    try:
        loader.detect_format("test.txt")
        track(check(False, "detect_format: 미지원 포맷 에러"))
    except ValueError:
        track(check(True, "detect_format: 미지원 포맷 ValueError 발생"))

    # 1-3. JSON 파일 로드
    json_path = os.path.join("data", "test_cases.json")
    if os.path.exists(json_path):
        json_data = loader.load(json_path)
        track(check(len(json_data) > 0, f"JSON 로드: {len(json_data)}행"))
        track(check(isinstance(json_data[0], dict), "JSON 로드: Dict 반환"))
        track(check("ID" in json_data[0], "JSON 로드: 'ID' 키 존재"))
        track(check("PW" in json_data[0], "JSON 로드: 'PW' 키 존재"))
    else:
        track(check(False, f"JSON 파일 없음: {json_path}"))

    # 1-4. CSV 파일 로드
    csv_path = os.path.join("data", "test_cases.csv")
    if os.path.exists(csv_path):
        csv_data = loader.load(csv_path)
        track(check(len(csv_data) > 0, f"CSV 로드: {len(csv_data)}행"))
        track(check(isinstance(csv_data[0], dict), "CSV 로드: Dict 반환"))
        track(check("ID" in csv_data[0], "CSV 로드: 'ID' 키 존재"))
    else:
        track(check(False, f"CSV 파일 없음: {csv_path}"))

    # 1-5. Excel 파일 로드 (기존 data.xlsx)
    excel_path = "data.xlsx"
    if os.path.exists(excel_path):
        excel_data = loader.load(excel_path)
        track(check(isinstance(excel_data, list), f"Excel 로드: List 반환"))
        track(check(len(excel_data) >= 0, f"Excel 로드: {len(excel_data)}행"))
    else:
        print(f"   [SKIP] Excel 파일 없음 (data.xlsx) - 기존 호환성 테스트 생략")

    # 1-6. 코드 생성 검증
    json_code = loader.generate_loader_code(json_path)
    track(check("def get_test_data():" in json_code, "코드 생성(JSON): get_test_data 함수"))
    track(check("json.load" in json_code, "코드 생성(JSON): json.load 사용"))

    csv_code = loader.generate_loader_code(csv_path)
    track(check("def get_test_data():" in csv_code, "코드 생성(CSV): get_test_data 함수"))
    track(check("csv.DictReader" in csv_code, "코드 생성(CSV): csv.DictReader 사용"))

    excel_code = loader.generate_loader_code("test.xlsx")
    track(check("def get_test_data():" in excel_code, "코드 생성(Excel): get_test_data 함수"))
    track(check("openpyxl" in excel_code, "코드 생성(Excel): openpyxl 사용"))

    # ---------------------------------------------------------
    # 2. Standard Script Generator DDT 검증
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 2] Standard Script Generator DDT 검증")
    print("="*60)

    mock_steps = [
        {
            "name": "Login Button",
            "type": "ID",
            "locator": "login-btn",
            "action": "click",
            "value": "",
        },
        {
            "name": "Username",
            "type": "NAME",
            "locator": "username",
            "action": "input",
            "value": "{ID}",
        },
        {
            "name": "Password",
            "type": "NAME",
            "locator": "password",
            "action": "input_password",
            "value": "{PW}",
        },
    ]

    gen = ScriptGenerator()

    # 2-1. JSON DDT
    json_script = gen.generate("https://example.com", mock_steps, data_path=json_path)
    track(check("get_test_data" in json_script, "Generator(JSON): get_test_data 함수 포함"))
    track(check("json.load" in json_script, "Generator(JSON): json.load 코드 포함"))
    track(check('@pytest.mark.parametrize("row_data", get_test_data())' in json_script,
                "Generator(JSON): parametrize 데코레이터"))
    track(check("format_map(SafeData(row_data))" in json_script,
                "Generator(JSON): Safe 변수 바인딩"))
    track(check("allure.title" in json_script, "Generator(JSON): allure.title 데코레이터"))

    # 2-2. CSV DDT
    csv_script = gen.generate("https://example.com", mock_steps, data_path=csv_path)
    track(check("get_test_data" in csv_script, "Generator(CSV): get_test_data 함수 포함"))
    track(check("csv.DictReader" in csv_script, "Generator(CSV): csv.DictReader 코드 포함"))

    # 2-3. Excel DDT (하위호환: excel_path 파라미터)
    excel_script = gen.generate("https://example.com", mock_steps, excel_path="test.xlsx")
    track(check("get_test_data" in excel_script, "Generator(Excel 하위호환): get_test_data 함수 포함"))
    track(check("openpyxl" in excel_script, "Generator(Excel 하위호환): openpyxl 코드 포함"))

    # 2-4. DDT 없는 경우 (data_path=None)
    no_ddt_script = gen.generate("https://example.com", mock_steps)
    track(check("get_test_data" not in no_ddt_script, "Generator(No DDT): 로더 코드 없음"))
    track(check("parametrize" not in no_ddt_script, "Generator(No DDT): parametrize 없음"))

    # ---------------------------------------------------------
    # 3. POM Generator DDT + Allure 검증
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 2] POM Generator DDT + Allure 검증")
    print("="*60)

    pom_gen = POMGenerator()
    output_dir = "verify_phase2_output"

    # 3-1. JSON DDT로 POM 프로젝트 생성
    success, msg = pom_gen.generate_project(
        output_dir,
        "https://example.com",
        mock_steps,
        data_path=json_path,
        browser_type="chrome"
    )

    if check(success, f"POM 프로젝트 생성 성공 ({msg})"):
        passed += 1

        # conftest.py 검증
        conftest_path = os.path.join(output_dir, "tests", "conftest.py")
        with open(conftest_path, "r", encoding="utf-8") as f:
            conftest = f.read()
            track(check("import allure" in conftest, "conftest: import allure 포함"))
            track(check("allure.attach" in conftest, "conftest: allure.attach 스크린샷 첨부"))
            track(check("get_screenshot_as_png" in conftest, "conftest: PNG 스크린샷 캡처"))
            track(check("attachment_type=allure.attachment_type.PNG" in conftest,
                        "conftest: PNG 첨부 타입"))

        # test_scenario.py 검증
        test_path = os.path.join(output_dir, "tests", "test_scenario.py")
        with open(test_path, "r", encoding="utf-8") as f:
            test = f.read()
            track(check("get_test_data" in test, "test_scenario: get_test_data 포함"))
            track(check("json.load" in test, "test_scenario(JSON): json.load 코드 포함"))
            track(check('@pytest.mark.parametrize("row_data", get_test_data())' in test,
                        "test_scenario: parametrize 데코레이터"))
            track(check("allure.step" in test, "test_scenario: allure.step 단계별 설명"))
            track(check("allure.feature" in test, "test_scenario: allure.feature 데코레이터"))
            track(check("allure.title" in test, "test_scenario: allure.title 데코레이터"))
            track(check("SafeData" in test, "test_scenario: SafeData 클래스"))
    else:
        failed += 1

    # 3-2. Excel DDT로 POM 프로젝트 생성 (하위호환)
    output_dir2 = "verify_phase2_output_excel"
    success2, _ = pom_gen.generate_project(
        output_dir2,
        "https://example.com",
        mock_steps,
        excel_path="test.xlsx",
        browser_type="chrome"
    )
    if check(success2, "POM 프로젝트 생성 (Excel 하위호환) 성공"):
        passed += 1
        with open(os.path.join(output_dir2, "tests", "test_scenario.py"), "r", encoding="utf-8") as f:
            test2 = f.read()
            track(check("openpyxl" in test2, "test_scenario(Excel): openpyxl 코드 포함"))
    else:
        failed += 1

    # ---------------------------------------------------------
    # 4. Config 검증
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 2] Config 설정 검증")
    print("="*60)

    import config
    track(check(hasattr(config, "DATA_DIR"), "config: DATA_DIR 존재"))
    track(check(hasattr(config, "DEFAULT_DATA_FORMAT"), "config: DEFAULT_DATA_FORMAT 존재"))
    track(check(config.DEFAULT_DATA_FORMAT in ("json", "csv", "excel"),
                f"config: DEFAULT_DATA_FORMAT = {config.DEFAULT_DATA_FORMAT}"))
    track(check("data" in config.DATA_DIR.lower(), f"config: DATA_DIR 경로 설정"))

    # ---------------------------------------------------------
    # 5. 샘플 데이터 파일 검증
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 2] 샘플 데이터 파일 검증")
    print("="*60)

    track(check(os.path.exists("data/test_cases.json"), "샘플 파일: data/test_cases.json 존재"))
    track(check(os.path.exists("data/test_cases.csv"), "샘플 파일: data/test_cases.csv 존재"))

    # JSON/CSV 데이터 일치성 확인
    json_data = loader.load("data/test_cases.json")
    csv_data = loader.load("data/test_cases.csv")
    track(check(len(json_data) == len(csv_data),
                f"JSON/CSV 데이터 행 수 일치: {len(json_data)} == {len(csv_data)}"))

    # Cleanup
    for d in ["verify_phase2_output", "verify_phase2_output_excel"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"   [CLEANUP] {d} 삭제")

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    print("\n" + "="*60)
    total = passed + failed
    print(f"📊 결과: {passed}/{total} PASSED, {failed}/{total} FAILED")
    if failed == 0:
        print("🎉 Phase 2 모든 검증 통과!")
    else:
        print(f"⚠️  {failed}개 항목 실패!")
    print("="*60)

    return failed == 0

if __name__ == "__main__":
    verify_phase2()
