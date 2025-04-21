"""
Authentication functionality for the LinkedIn Automation package.
"""
import time
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from linkedin_automation.config.constants import (
    USERNAME_FIELD_XPATH, PASSWORD_FIELD_XPATH, LOGIN_BUTTON_XPATH,
    LOGIN_NAV_CHECK_SELECTORS
)
from linkedin_automation.config.settings import (
    LINKEDIN_USERNAME, LINKEDIN_PASSWORD, USE_COOKIES,
    save_cookies, load_cookies
)
from linkedin_automation.utils.decorators import retry
from linkedin_automation.utils.helpers import sleep
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

class LinkedInAuth:
    """LinkedIn authentication manager."""
    
    def __init__(self, browser):
        """
        Initialize the LinkedInAuth.
        
        Args:
            browser: Browser instance to use for authentication
        """
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait
        
    @retry(max_attempts=3, delay_seconds=2)
    def login(self, username=None, password=None, url=None):
        """
        Log in to LinkedIn with the provided credentials.
        
        Args:
            username (str, optional): LinkedIn username or email. Defaults to config value.
            password (str, optional): LinkedIn password. Defaults to config value.
            url (str, optional): URL to navigate to after login.
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        # Use provided credentials or fall back to config
        username = username or LINKEDIN_USERNAME
        password = password or LINKEDIN_PASSWORD
        
        if not username:
            logger.error("LinkedIn username not provided")
            return False
            
        # Try to use cookies first if enabled
        if USE_COOKIES:
            logger.info("Attempting to log in using cookies")
            if self._login_with_cookies(username, url):
                logger.info("Successfully logged in using cookies")
                return True
                
        # Fall back to password login if cookies failed or are disabled
        if not password:
            logger.error("LinkedIn password not provided and cookie login failed")
            return False
            
        return self._login_with_password(username, password, url)
    
    def _login_with_cookies(self, username, url=None):
        """
        Attempt to log in using saved cookies.
        
        Args:
            username (str): LinkedIn username for loading the correct cookies
            url (str, optional): URL to navigate to after login
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        cookies = load_cookies(username)
        if not cookies:
            logger.debug("No saved cookies found")
            return False
            
        try:
            # Navigate to LinkedIn homepage first
            self.driver.get("https://www.linkedin.com/")
            sleep()
            
            # Add the cookies to the session
            for cookie in cookies:
                # Some cookies can cause issues, so we handle them individually
                try:
                    # Domain is required for cookies, so skip any without it
                    if 'domain' not in cookie:
                        continue
                        
                    # Some cookie attributes might cause issues
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                        
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Couldn't add cookie: {e}")
                    
            # Refresh to apply cookies
            self.driver.refresh()
            sleep()
            
            # Navigate to the requested URL or feed
            target_url = url or "https://www.linkedin.com/feed/"
            self.driver.get(target_url)
            sleep()
            
            # Check if we're logged in by trying multiple selectors that could indicate successful login
            for selector in LOGIN_NAV_CHECK_SELECTORS:
                try:
                    logged_in = self.wait.until(ec.presence_of_element_located(
                        (By.CSS_SELECTOR, selector)
                    ))
                    logger.info(f"Login confirmed with selector: {selector}")
                    return True
                except:
                    continue
                    
            logger.info("Cookie login failed, will try password login")
            return False
                
        except Exception as e:
            logger.warning(f"Error during cookie login: {e}")
            return False
            
    def _login_with_password(self, username, password, url=None):
        """
        Log in to LinkedIn using username and password.
        
        Args:
            username (str): LinkedIn username or email
            password (str): LinkedIn password
            url (str, optional): URL to navigate to after login
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            logger.info("Logging in with username and password")
            
            # Navigate to LinkedIn login page - try the main page first which may be less prone to bot detection
            login_urls = [
                "https://www.linkedin.com/",  # Try main page first
                "https://www.linkedin.com/login", # Then specific login page
            ]
            
            # Try URL from args first, then our login URL array
            if url:
                self.driver.get(url)
            else:
                # Pick the first URL from our list
                self.driver.get(login_urls[0])
                
            # Wait a bit longer to ensure page loads
            sleep(3, 5)
            
            # Try to find the login form elements with more robust error handling
            try:
                # First check if we're already on a login page, if not try to find a sign-in button
                try:
                    # Check if we're already on the login page
                    self.wait.until(ec.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Sign in')]")))
                except:
                    # If not, try to find and click the sign-in button on homepage
                    try:
                        sign_in_button = self.wait.until(ec.element_to_be_clickable(
                            (By.XPATH, "//a[contains(@href, '/login') or contains(text(), 'Sign in')]")
                        ))
                        sign_in_button.click()
                        sleep(2, 3)  # Wait for login page to load
                    except:
                        # If no sign-in button, directly navigate to login page
                        self.driver.get("https://www.linkedin.com/login")
                        sleep(2, 3)
                        
                # Input username with explicit wait
                username_field = self.wait.until(ec.element_to_be_clickable((By.XPATH, USERNAME_FIELD_XPATH)))
                username_field.clear()
                sleep(0.5, 1)
                username_field.send_keys(username)
                logger.debug("Username entered")
                sleep(1, 2)
                
                # Input password with explicit wait
                password_field = self.wait.until(ec.element_to_be_clickable((By.XPATH, PASSWORD_FIELD_XPATH)))
                password_field.clear()
                sleep(0.5, 1)
                password_field.send_keys(password)
                logger.debug("Password entered")
                sleep(1, 2)
                
                # Click login button
                login_button = self.wait.until(ec.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
                login_button.click()
                logger.info("Login form submitted")
                
            except Exception as e:
                logger.warning(f"Error in login process: {e}")
                # Take screenshot for debugging
                try:
                    screenshot_path = f"/Users/eduardocorrea/git/linkedu/logs/login_error_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Login error screenshot saved to {screenshot_path}")
                except:
                    pass
                
                # Try one more time with alternate login URL
                self.driver.get("https://www.linkedin.com/checkpoint/lg/login")
                sleep(3, 5)
                
                # Input username
                username_field = self.driver.find_element(By.ID, "username")
                username_field.clear()
                username_field.send_keys(username)
                
                # Input password
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                logger.info("Login form submitted (fallback method)")
            
            # Wait for page to load
            sleep()
            
            # Check if login was successful by trying multiple selectors
            for selector in LOGIN_NAV_CHECK_SELECTORS:
                try:
                    nav_element = self.wait.until(ec.presence_of_element_located(
                        (By.CSS_SELECTOR, selector)
                    ))
                    
                    # Save cookies for future logins
                    cookies = self.driver.get_cookies()
                    save_cookies(cookies, username)
                    logger.info(f"Login successful with selector: {selector}")
                    logger.debug("Cookies saved for future sessions")
                    
                    return True
                except:
                    continue
                    
            # Check for challenge page or other verification screens
            try:
                if "challenge" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                    logger.warning("LinkedIn security verification detected. Manual intervention required.")
                else:
                    logger.warning("Login failed - could not find navigation bar or verification element")
                return False
            except:
                logger.warning("Login failed - could not determine login status")
                return False
                
        except TimeoutException as e:
            logger.error(f"Timeout during login: {e}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error during login: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            return False