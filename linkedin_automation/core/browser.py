"""
Browser management for the LinkedIn Automation package.
"""
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from linkedin_automation.config.settings import BROWSER_CONFIG
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

class Browser:
    """Singleton browser class to manage Selenium WebDriver instance."""
    _instance = None
    driver = None
    wait = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Browser, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, headless=None):
        if self._initialized:
            return
            
        self._initialized = True
        self.start_browser(headless)
        
    def start_browser(self, headless=None):
        """
        Initialize and configure the browser instance.
        
        Args:
            headless (bool, optional): Run browser in headless mode. 
                If None, uses value from config.
        """
        browser_type = BROWSER_CONFIG.get("browser", "chrome").lower()
        logger.info(f"Starting {browser_type} browser...")
        
        # Use provided headless value or fall back to config
        use_headless = headless if headless is not None else BROWSER_CONFIG.get("headless", False)
        
        if browser_type == "chrome":
            self._start_chrome(use_headless)
        elif browser_type == "firefox":
            self._start_firefox(use_headless)
        elif browser_type == "edge":
            self._start_edge(use_headless)
        else:
            logger.warning(f"Unsupported browser type: {browser_type}. Falling back to Chrome.")
            self._start_chrome(use_headless)
        
        # Configure wait with randomized timing for a more human-like behavior
        timeout = BROWSER_CONFIG.get("timeout", 30)
        self.wait = WebDriverWait(self.driver, timeout)
        
        self.driver.maximize_window()
        
        # Apply CDP commands to help avoid detection
        if browser_type == "chrome":
            try:
                # Execute CDP commands to avoid bot detection
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    """
                })
                
                # Hide that we're using automation
                self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.96 Safari/537.36"
                })
            except Exception as e:
                logger.debug(f"CDP commands failed: {e}")
                
        logger.info("Browser started successfully")
    
    def _start_chrome(self, headless):
        """Initialize Chrome browser."""
        options = ChromeOptions()
        
        if headless:
            options.add_argument("--headless=new")  # Use newer headless mode
            
        # Apply additional browser configurations
        for key, value in BROWSER_CONFIG.items():
            if key not in ["browser", "headless", "timeout"] and isinstance(value, bool) and value:
                options.add_argument(f"--{key.replace('_', '-')}")
        
        # Performance optimizations
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Reduced aggressive options that might trigger anti-automation detection
        # options.add_argument("--disable-gpu")
        # options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        # options.add_argument("--disable-site-isolation-trials")
        # options.add_argument("--disable-web-security")
        # options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        # Keep images enabled to avoid detection
        # options.add_argument("--blink-settings=imagesEnabled=false")
        
        # Removed problematic memory optimization settings that might be causing instability
        # options.add_argument("--disable-features=NetworkService")
        # options.add_argument("--disable-features=VizDisplayCompositor")
        # options.add_argument("--renderer-process-limit=1")
        # options.add_argument("--single-process")
        
        # Add JS flags if specified
        if "js_flags" in BROWSER_CONFIG:
            options.add_argument(f"--js-flags={BROWSER_CONFIG['js_flags']}")
        
        # Use a more recent user agent to avoid detection
        options.add_argument(f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.96 Safari/537.36")
        
        # Add anti-detection preferences
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Add additional preferences to avoid detection
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "download_restrictions": 3
        }
        options.add_experimental_option("prefs", prefs)
        
        # Initialize Chrome WebDriver with better error handling
        try:
            service = ChromeService(executable_path=ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Chrome browser: {e}")
            # Try again with minimal fallback options
            options = ChromeOptions()
            options.add_argument("--headless") if headless else None
            options.add_argument("--disable-extensions")
            options.add_argument("--no-sandbox")
            
            # Add modern user agent
            options.add_argument(f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.96 Safari/537.36")
            
            # Add some essential preferences
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            })
            
            service = ChromeService(executable_path=ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome browser initialized with fallback options")
    
    def _start_firefox(self, headless):
        """Initialize Firefox browser."""
        options = FirefoxOptions()
        
        if headless:
            options.add_argument("--headless")
            
        # Performance optimizations for Firefox
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("media.volume_scale", "0.0")
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
        
        # Disable images for faster loading
        options.set_preference("permissions.default.image", 2)
        
        # Memory optimizations
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", True)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)
        
        # Custom user agent
        options.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0")
        
        try:
            service = FirefoxService(executable_path=GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            logger.info("Firefox browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firefox browser: {e}")
            # Try again with minimal options
            options = FirefoxOptions()
            options.add_argument("--headless") if headless else None
            service = FirefoxService(executable_path=GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            logger.info("Firefox browser initialized with fallback options")
    
    def _start_edge(self, headless):
        """Initialize Edge browser."""
        options = EdgeOptions()
        
        if headless:
            options.add_argument("--headless=new")
            
        # Performance optimizations (Edge uses Chromium, so many Chrome options work)
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
        
        # Custom user agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58")
        
        try:
            service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            logger.info("Edge browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Edge browser: {e}")
            # Try again with minimal options
            options = EdgeOptions()
            options.add_argument("--headless") if headless else None
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            logger.info("Edge browser initialized with fallback options")
        
    def cleanup(self):
        """Close the browser and perform cleanup."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
                self._initialized = False