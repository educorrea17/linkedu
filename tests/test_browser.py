"""
Tests for the browser module.
"""
import unittest
from unittest.mock import patch, MagicMock

from linkedin_automation.core.browser import Browser


class TestBrowser(unittest.TestCase):
    """Tests for the Browser class."""
    
    @patch('linkedin_automation.core.browser.Service')
    @patch('linkedin_automation.core.browser.ChromeDriverManager')
    @patch('linkedin_automation.core.browser.webdriver.Chrome')
    @patch('linkedin_automation.core.browser.WebDriverWait')
    def test_singleton_pattern(self, mock_wait, mock_chrome, mock_driver_manager, mock_service):
        """Test that Browser follows the singleton pattern."""
        # Setup mocks
        mock_driver_manager.return_value.install.return_value = 'path/to/chromedriver'
        mock_chrome.return_value = MagicMock()
        
        # Create first instance
        browser1 = Browser()
        
        # Create second instance
        browser2 = Browser()
        
        # Assert they are the same instance
        self.assertIs(browser1, browser2)
        
        # Assert Chrome was only initialized once
        mock_chrome.assert_called_once()
        
    @patch('linkedin_automation.core.browser.Service')
    @patch('linkedin_automation.core.browser.ChromeDriverManager')
    @patch('linkedin_automation.core.browser.webdriver.Chrome')
    @patch('linkedin_automation.core.browser.WebDriverWait')
    def test_cleanup(self, mock_wait, mock_chrome, mock_driver_manager, mock_service):
        """Test the cleanup method."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Create instance
        browser = Browser()
        
        # Call cleanup
        browser.cleanup()
        
        # Assert driver was quit
        mock_driver.quit.assert_called_once()
        
        # Assert driver was reset
        self.assertIsNone(browser.driver)
        self.assertIsNone(browser.wait)
        self.assertFalse(browser._initialized)


if __name__ == '__main__':
    unittest.main()