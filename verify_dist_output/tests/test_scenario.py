
import pytest
import allure
from pages.auto_page import AutoPage


import pandas as pd
import sys
import os

class SafeData(dict):
    def __missing__(self, key): 
        print(f"[WARN] 엑셀에 변수 '{key}'가 없습니다. 빈 값으로 처리합니다.")
        return ""

def get_excel_data():
    file_path = r"test.xlsx"
    print(f"\n[INFO] 엑셀 로드 중: {file_path}")
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일 없음: {file_path}")
        return []
    try:
        df = pd.read_excel(file_path, engine='openpyxl').fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        data = df.to_dict(orient='records')
        if not data: print("[WARN] 데이터 없음")
        return data
    except Exception as e:
        print(f"\n[FATAL] 엑셀 읽기 실패: {e}")
        return []


@pytest.mark.parametrize("row_data", get_excel_data())
def test_workflow(driver, row_data):
    page = AutoPage(driver)
    page.open("https://example.com")
    
    with allure.step("Run POM Scenario"):
        page.step_1_click()
        page.step_2_input('{USER_ID}'.format_map(SafeData(row_data)))
        page.step_3_click()

