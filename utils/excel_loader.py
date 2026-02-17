import pandas as pd
import os
from utils.logger import setup_logger

logger = setup_logger(__name__)

def get_excel_columns(filepath):
    """
    엑셀 파일의 컬럼(헤더) 목록만 가져오기

    Args:
        filepath: 엑셀 파일 경로

    Returns:
        list: 컬럼명 리스트
    """
    try:
        if not os.path.exists(filepath):
            logger.warning(f"엑셀 파일이 존재하지 않음: {filepath}")
            return []
        df = pd.read_excel(filepath, nrows=0)
        columns = list(df.columns)
        logger.info(f"엑셀 컬럼 로드 완료: {columns}")
        return columns
    except Exception as e:
        logger.error(f"엑셀 컬럼 읽기 실패: {e}")
        return []

def load_excel_data(filepath):
    """
    엑셀 데이터를 리스트(Dictionary List) 형태로 반환

    Args:
        filepath: 엑셀 파일 경로

    Returns:
        list: 각 행이 딕셔너리인 리스트
    """
    try:
        df = pd.read_excel(filepath).fillna("")
        data = df.to_dict(orient='records')
        logger.info(f"엑셀 데이터 로드 완료: {len(data)}행")
        return data
    except FileNotFoundError:
        logger.error(f"엑셀 파일을 찾을 수 없음: {filepath}")
        return []
    except Exception as e:
        logger.error(f"엑셀 데이터 로드 실패: {e}")
        return []