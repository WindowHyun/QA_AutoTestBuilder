"""
브라우저 설정 모듈

브라우저별 옵션과 드라이버 설정을 중앙화하여 코드 중복을 제거합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class BrowserConfig:
    """브라우저 설정 관리 클래스"""

    # 지원하는 브라우저 목록
    SUPPORTED_BROWSERS = ["chrome", "firefox", "edge"]

    # 공통 Chrome 옵션
    CHROME_COMMON_OPTIONS = [
        "--incognito",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-notifications",
    ]

    CHROME_COMMON_PREFS = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }

    CHROME_EXPERIMENTAL_OPTIONS = {
        "excludeSwitches": ["enable-automation"],
        "useAutomationExtension": False,
    }

    # Firefox 옵션
    FIREFOX_COMMON_OPTIONS = ["-private"]
    FIREFOX_PREFERENCES = {
        "dom.webnotifications.enabled": False,
    }

    # Edge 옵션
    EDGE_COMMON_OPTIONS = [
        "inprivate",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]

    @classmethod
    def get_chrome_options(cls, headless=False, maximize=True):
        """
        Chrome 옵션 객체 생성

        Args:
            headless: 헤드리스 모드 여부
            maximize: 창 최대화 여부

        Returns:
            webdriver.ChromeOptions: 설정된 옵션 객체
        """
        options = webdriver.ChromeOptions()

        for opt in cls.CHROME_COMMON_OPTIONS:
            options.add_argument(opt)

        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        elif maximize:
            options.add_argument("--start-maximized")

        options.add_experimental_option("prefs", cls.CHROME_COMMON_PREFS)
        for key, value in cls.CHROME_EXPERIMENTAL_OPTIONS.items():
            options.add_experimental_option(key, value)

        return options

    @classmethod
    def get_firefox_options(cls, headless=False):
        """
        Firefox 옵션 객체 생성

        Args:
            headless: 헤드리스 모드 여부

        Returns:
            webdriver.FirefoxOptions: 설정된 옵션 객체
        """
        options = webdriver.FirefoxOptions()

        for opt in cls.FIREFOX_COMMON_OPTIONS:
            options.add_argument(opt)

        if headless:
            options.add_argument("--headless")

        for key, value in cls.FIREFOX_PREFERENCES.items():
            options.set_preference(key, value)

        return options

    @classmethod
    def get_edge_options(cls, headless=False, maximize=True):
        """
        Edge 옵션 객체 생성

        Args:
            headless: 헤드리스 모드 여부
            maximize: 창 최대화 여부

        Returns:
            webdriver.EdgeOptions: 설정된 옵션 객체
        """
        options = webdriver.EdgeOptions()

        for opt in cls.EDGE_COMMON_OPTIONS:
            options.add_argument(opt)

        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        elif maximize:
            options.add_argument("--start-maximized")

        return options

    @classmethod
    def create_driver(cls, browser_type="chrome", headless=False):
        """
        브라우저 드라이버 인스턴스 생성

        Args:
            browser_type: 브라우저 종류 (chrome, firefox, edge)
            headless: 헤드리스 모드 여부

        Returns:
            WebDriver: 생성된 드라이버 인스턴스

        Raises:
            ValueError: 지원하지 않는 브라우저
        """
        browser_type = browser_type.lower()

        if browser_type == "chrome":
            service = ChromeService(ChromeDriverManager().install())
            options = cls.get_chrome_options(headless=headless)
            return webdriver.Chrome(service=service, options=options)

        elif browser_type == "firefox":
            service = FirefoxService(GeckoDriverManager().install())
            options = cls.get_firefox_options(headless=headless)
            return webdriver.Firefox(service=service, options=options)

        elif browser_type == "edge":
            service = EdgeService(EdgeChromiumDriverManager().install())
            options = cls.get_edge_options(headless=headless)
            return webdriver.Edge(service=service, options=options)

        else:
            raise ValueError(f"지원하지 않는 브라우저: {browser_type}. "
                           f"지원 목록: {cls.SUPPORTED_BROWSERS}")

    @classmethod
    def generate_driver_code(cls, browser_type="chrome", headless=False):
        """
        테스트 스크립트용 드라이버 생성 코드 반환

        Args:
            browser_type: 브라우저 종류
            headless: 헤드리스 모드 여부

        Returns:
            dict: import문, 초기화 코드, 드라이버 생성 코드를 담은 딕셔너리
        """
        browser_type = browser_type.lower()

        if browser_type == "chrome":
            return cls._chrome_code_template(headless)
        elif browser_type == "firefox":
            return cls._firefox_code_template(headless)
        elif browser_type == "edge":
            return cls._edge_code_template(headless)
        else:
            # 기본값: Chrome
            return cls._chrome_code_template(headless)

    @classmethod
    def _chrome_code_template(cls, headless=False):
        """Chrome 드라이버 코드 템플릿"""
        imports = """from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager"""

        init_code = """service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()"""

        # Generate options code dynamically
        options_lines = []
        for opt in cls.CHROME_COMMON_OPTIONS:
            options_lines.append(f'    options.add_argument("{opt}")')
            
        # Prefs
        prefs_str = ", ".join([f'"{k}": {v}' for k, v in cls.CHROME_COMMON_PREFS.items()])
        options_lines.append(f'    prefs = {{{prefs_str}}}')
        options_lines.append('    options.add_experimental_option("prefs", prefs)')
        
        # Experimental
        for k, v in cls.CHROME_EXPERIMENTAL_OPTIONS.items():
            val_str = f'"{v}"' if isinstance(v, str) else str(v)
            options_lines.append(f'    options.add_experimental_option("{k}", {val_str})')

        options_code = "\n".join(options_lines)

        if headless:
            headless_code = """    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")"""
        else:
            headless_code = '    options.add_argument("--start-maximized")'


        driver_code = "driver = webdriver.Chrome(service=service, options=options)"

        return {
            "imports": imports,
            "init": init_code,
            "headless": headless_code,
            "options": options_code,
            "driver": driver_code,
        }

    @classmethod
    def _firefox_code_template(cls, headless=False):
        """Firefox 드라이버 코드 템플릿"""
        imports = """from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager"""

        init_code = """service = FirefoxService(GeckoDriverManager().install())
    options = webdriver.FirefoxOptions()"""

        options_lines = []
        for opt in cls.FIREFOX_COMMON_OPTIONS:
            options_lines.append(f'    options.add_argument("{opt}")')
            
        for k, v in cls.FIREFOX_PREFERENCES.items():
            val_str = f'"{v}"' if isinstance(v, str) else str(v)
            options_lines.append(f'    options.set_preference("{k}", {val_str})')
            
        options_code = "\n".join(options_lines)

        if headless:
            headless_code = '    options.add_argument("--headless")'
        else:
            headless_code = ""

        driver_code = "driver = webdriver.Firefox(service=service, options=options)"

        return {
            "imports": imports,
            "init": init_code,
            "headless": headless_code,
            "options": options_code,
            "driver": driver_code,
        }

    @classmethod
    def _edge_code_template(cls, headless=False):
        """Edge 드라이버 코드 템플릿"""
        imports = """from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager"""

        init_code = """service = EdgeService(EdgeChromiumDriverManager().install())
    options = webdriver.EdgeOptions()"""

        options_lines = []
        for opt in cls.EDGE_COMMON_OPTIONS:
            options_lines.append(f'    options.add_argument("{opt}")')
            
        options_code = "\n".join(options_lines)

        if headless:
            headless_code = """    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")"""
        else:
            headless_code = '    options.add_argument("--start-maximized")'

        driver_code = "driver = webdriver.Edge(service=service, options=options)"

        return {
            "imports": imports,
            "init": init_code,
            "headless": headless_code,
            "options": options_code,
            "driver": driver_code,
        }
