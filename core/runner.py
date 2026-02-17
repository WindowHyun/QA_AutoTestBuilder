import subprocess
import sys
import os
import shutil
import config
from utils.logger import setup_logger
from core.plugin_manager import PluginManager

logger = setup_logger(__name__)


import threading
import queue
import time
import io

class TestRunner:
    def __init__(self):
        self.process = None
        self.plugin_manager = PluginManager()

    def run_pytest(self, parallel_workers=1):
        """
        Pytest 실행 (Frozen 환경 대응)
        """
        # [Plugin Hook] 테스트 시작 전
        self.plugin_manager.hook("on_test_start", parallel_workers=parallel_workers)

        # 기존 결과 삭제
        if os.path.exists(config.ALLURE_RESULTS_DIR):
            try:
                shutil.rmtree(config.ALLURE_RESULTS_DIR)
                logger.info(f"기존 테스트 결과 삭제: {config.ALLURE_RESULTS_DIR}")
            except Exception as e:
                logger.warning(f"기존 결과 삭제 실패: {e}")

        # 결과 디렉토리 재생성
        os.makedirs(config.ALLURE_RESULTS_DIR, exist_ok=True)
        
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            # [In-Process Execution]
            output_queue = queue.Queue()
            self.process = MockProcess(output_queue)
            
            def run_in_thread():
                import pytest
                
                # Output Capture Wrapper
                class StreamCapturer(io.StringIO):
                    def write(self, msg):
                        output_queue.put(msg)
                        return len(msg)
                        
                capture = StreamCapturer()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = capture
                sys.stderr = capture
                
                try:
                    args = [
                        config.TEMP_TEST_FILE,
                    ]
                    
                    if config.USE_BUILTIN_REPORTER:
                        args.append(f"--html-report-dir={config.HTML_REPORT_DIR}")
                    else:
                        args.append(f"--alluredir={config.ALLURE_RESULTS_DIR}")
                        
                    args.append("-v")

                    if parallel_workers > 1:
                        args.extend(["-n", str(parallel_workers)])
                        
                    logger.info(f"In-Process Pytest 실행: {args}")
                    rc = pytest.main(args)
                    self.process.set_returncode(rc)
                    # [Plugin Hook] 테스트 종료 후
                    self.plugin_manager.hook("on_test_end", return_code=rc)
                except SystemExit as e:
                    self.process.set_returncode(e.code)
                    self.plugin_manager.hook("on_test_end", return_code=e.code)
                except Exception as e:
                    output_queue.put(f"Execution Error: {e}\n")
                    self.process.set_returncode(1)
                    self.plugin_manager.hook("on_test_end", return_code=1, error=str(e))
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
            threading.Thread(target=run_in_thread, daemon=True).start()
            return self.process
            
        else:
            # [Standard Subprocess Execution]
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                config.TEMP_TEST_FILE,
            ]

            if config.USE_BUILTIN_REPORTER:
                cmd.append(f"--html-report-dir={config.HTML_REPORT_DIR}")
            else:
                cmd.append(f"--alluredir={config.ALLURE_RESULTS_DIR}")
                
            cmd.append("-v")

            # 병렬 실행 옵션 추가
            if parallel_workers > 1:
                cmd.extend(["-n", str(parallel_workers)])
                logger.info(f"병렬 실행 모드: {parallel_workers}개 워커")
            else:
                logger.info("순차 실행 모드")

            logger.info(f"Pytest 실행 시작: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1  # Line buffering
            )
            
            # Subprocess의 경우 종료 대기를 위한 별도 모니터링 필요할 수 있으나,
            # 현재 구조에서는 Popen 객체를 그대로 반환함.
            return self.process

    def open_report(self):
        """
        Allure 리포트 열기

        Note:
            allure 명령어가 시스템에 설치되어 있어야 함
        """
        try:
            # 보안: shell=False 사용, 커맨드 인젝션 방지
            # Windows에서는 allure.bat 또는 allure.cmd 찾기
            import shutil
            allure_cmd = shutil.which("allure")
            if not allure_cmd:
                # Windows에서 .bat, .cmd 확장자 확인
                for ext in ["", ".bat", ".cmd"]:
                    allure_cmd = shutil.which(f"allure{ext}")
                    if allure_cmd:
                        break

            if not allure_cmd:
                logger.error("Allure가 설치되지 않았거나 PATH에 없습니다.")
                logger.error("설치: https://docs.qameta.io/allure/#_installing_a_commandline")
                return

            if config.USE_BUILTIN_REPORTER:
                # HTML 리포트 열기
                report_file = os.path.join(config.HTML_REPORT_DIR, "report.html") # TODO: 가장 최근 파일 찾기
                # 가장 최근 생성된 html 파일 찾기
                try:
                    files = [f for f in os.listdir(config.HTML_REPORT_DIR) if f.endswith(".html")]
                    if not files:
                        logger.warning("생성된 HTML 리포트가 없습니다.")
                        return
                    
                    latest_file = max([os.path.join(config.HTML_REPORT_DIR, f) for f in files], key=os.path.getctime)
                    os.startfile(latest_file)
                    logger.info(f"HTML 리포트 열기: {latest_file}")
                except Exception as e:
                    logger.error(f"HTML 리포트 열기 실패: {e}")
                return

            subprocess.Popen(
                [allure_cmd, "serve", config.ALLURE_RESULTS_DIR],
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            logger.info("Allure 리포트 서버 시작")
        except FileNotFoundError:
            logger.error("Allure가 설치되지 않았습니다.")
            logger.error("설치 방법: https://docs.qameta.io/allure/#_installing_a_commandline")
        except Exception as e:
            logger.error(f"리포트 열기 실패: {e}")

    def stop(self):
        """
        테스트 강제 종료 (좀비 프로세스 방지)
        """
        if self.process:
            logger.info("테스트 프로세스 종료 시도")
            try:
                self.process.terminate()
                # 5초 대기
                try:
                    self.process.wait(timeout=5)
                    logger.info("테스트 프로세스 정상 종료")
                except subprocess.TimeoutExpired:
                    # 강제 종료
                    logger.warning("프로세스가 응답하지 않아 강제 종료")
                    self.process.kill()
                    self.process.wait()
                    logger.info("테스트 프로세스 강제 종료 완료")
            except Exception as e:
                logger.error(f"프로세스 종료 중 에러: {e}")
            finally:
                self.process = None