import json
import os
import stat
from cryptography.fernet import Fernet
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 키 파일 경로 (사용자 홈 디렉토리의 숨김 폴더에 저장)
_KEY_DIR = os.path.join(os.path.expanduser("~"), ".qa_autotest")
KEY_FILE = os.path.join(_KEY_DIR, "secret.key")


def _secure_key_file(filepath):
    """
    키 파일에 보안 권한 설정 (소유자만 읽기/쓰기)

    Args:
        filepath: 키 파일 경로
    """
    try:
        if not os.path.exists(filepath):
            logger.error(f"권한 설정 대상 파일이 없습니다: {filepath}")
            return

        if os.name == 'nt':  # Windows
            import subprocess
            # 1. 상속 제거 (/inheritance:d) 및 기존 권한 복사
            # 2. 현재 사용자에게 모든 권한 부여
            # 3. 다른 사용자 접근 차단 (사실상 상속 제거로 달성됨)
            
            # 현재 사용자 이름 가져오기
            user = os.getlogin()
            
            # ACL 초기화 및 사용자 권한 부여
            cmd = ['icacls', filepath, '/inheritance:r', '/grant:r', f'{user}:F']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"icacls 권한 설정 실패: {result.stderr}")
            else:
                logger.debug(f"키 파일 권한 보안 설정 완료: {filepath}")
                
        else:  # Unix/Linux/Mac
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)  # 600 권한
            logger.debug(f"키 파일 권한 설정 완료 (0600): {filepath}")
            
    except Exception as e:
        logger.warning(f"키 파일 권한 설정 중 오류 (수동 설정 권장): {e}")


def _get_cipher():
    """
    암호화 키 로드 또는 생성

    우선순위:
    1. 환경 변수 ENCRYPTION_KEY (프로덕션 권장)
    2. 보안 폴더의 secret.key 파일
    3. 새로 생성 (보안 폴더에 저장)

    Returns:
        Fernet: 암호화/복호화 객체
    """
    # 1. 환경 변수에서 키 가져오기 (프로덕션 권장)
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key:
        try:
            logger.info("환경 변수에서 암호화 키 로드")
            return Fernet(env_key.encode())
        except Exception as e:
            logger.warning(f"환경 변수 키가 유효하지 않음: {e}")

    # 2. 보안 디렉토리 생성
    if not os.path.exists(_KEY_DIR):
        try:
            os.makedirs(_KEY_DIR, mode=0o700)  # 소유자만 접근 가능
            logger.info(f"키 저장 디렉토리 생성: {_KEY_DIR}")
        except Exception as e:
            logger.error(f"키 디렉토리 생성 실패: {e}")
            raise

    # 3. 파일에서 키 로드 또는 생성
    if not os.path.exists(KEY_FILE):
        logger.warning("암호화 키 파일이 없어 새로 생성합니다.")
        logger.warning("프로덕션 환경에서는 환경 변수 ENCRYPTION_KEY 사용을 권장합니다.")
        key = Fernet.generate_key()
        try:
            # 파일 생성 시 권한 제한
            fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as key_file:
                key_file.write(key)
            _secure_key_file(KEY_FILE)
            logger.info(f"암호화 키 파일 생성: {KEY_FILE}")
        except Exception as e:
            logger.error(f"키 파일 생성 실패: {e}")
            raise

    # 4. 키 읽기
    try:
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
        logger.debug(f"암호화 키 파일 로드 완료")
        return Fernet(key)
    except Exception as e:
        logger.error(f"키 파일 읽기 실패: {e}")
        raise

def save_to_json(filepath, url, steps):
    """
    데이터 저장 (비밀번호는 암호화)

    Args:
        filepath: 저장할 JSON 파일 경로
        url: 테스트 URL
        steps: 테스트 스텝 리스트

    Returns:
        bool: 저장 성공 여부
    """
    try:
        cipher = _get_cipher()
        steps_to_save = []

        # 깊은 복사 대신 리스트 컴프리헨션으로 처리
        for step in steps:
            new_step = step.copy()
            # 비밀번호 타입인 경우 암호화 수행
            if new_step['action'] == 'input_password' and new_step['value']:
                encrypted_val = cipher.encrypt(new_step['value'].encode()).decode()
                new_step['value'] = f"ENC:{encrypted_val}"
            steps_to_save.append(new_step)

        data = {"url": url, "steps": steps_to_save}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"시나리오 저장 완료: {filepath}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"파일 쓰기 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"저장 중 에러 발생: {e}")
        return False

def load_from_json(filepath):
    """
    데이터 로드 (비밀번호 복호화)

    Args:
        filepath: 로드할 JSON 파일 경로

    Returns:
        tuple: (url, steps) 또는 (None, []) on error
    """
    try:
        cipher = _get_cipher()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded_steps = []
        for step in data.get("steps", []):
            # 암호화된 비밀번호 복호화
            if step['action'] == 'input_password' and step['value'].startswith("ENC:"):
                try:
                    enc_val = step['value'].replace("ENC:", "")
                    decrypted_val = cipher.decrypt(enc_val.encode()).decode()
                    step['value'] = decrypted_val
                except Exception as decrypt_error:
                    logger.warning(f"비밀번호 복호화 실패 (키 불일치 가능): {decrypt_error}")
                    step['value'] = ""
            loaded_steps.append(step)

        logger.info(f"시나리오 로드 완료: {filepath} ({len(loaded_steps)}개 스텝)")
        return data.get("url", ""), loaded_steps
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없음: {filepath}")
        return None, []
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        return None, []
    except Exception as e:
        logger.error(f"로드 중 에러 발생: {e}")
        return None, []