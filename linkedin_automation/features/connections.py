"""
Connection management functionality for the LinkedIn Automation package.
"""
from selenium.common.exceptions import (
    ElementNotInteractableException, 
    NoSuchElementException, 
    StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from linkedin_automation.config.constants import (
    CONNECT_BUTTON_XPATH, SEND_WITHOUT_NOTE_XPATH, 
    SEND_BUTTON_XPATH, DISMISS_BUTTON_XPATH, NEXT_BUTTON_XPATH,
    GOT_IT_BUTTON_XPATH, PROFILE_MORE_BUTTON_XPATH, PROFILE_CONNECT_BUTTON_XPATH
)
from linkedin_automation.config.settings import MAX_CONNECTIONS, PAGE_LOAD_WAIT_RANGE
from linkedin_automation.utils.decorators import safe_operation, retry
from linkedin_automation.utils.helpers import sleep
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """Manage LinkedIn connection requests."""
    
    def __init__(self, browser):
        """
        Initialize the ConnectionManager.
        
        Args:
            browser: Browser instance to use for automation
        """
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait
        self.connection_count = 0
        self.main_window = None
        self.max_connections = MAX_CONNECTIONS  # Will be updated in run_connection_campaign
        
    @safe_operation
    def find_connection_buttons(self):
        """
        Find both 'Connect' and 'Follow' buttons on the current page.
        
        Returns:
            list: List of WebElement objects representing connect/follow buttons
        """
        logger.debug("Searching for Connect/Follow buttons")
        sleep()
        buttons = self.driver.find_elements(By.XPATH, CONNECT_BUTTON_XPATH)
        logger.debug(f"Found {len(buttons)} Connect/Follow buttons")
        return buttons
    
    @retry(max_attempts=2)
    def wait_to_click(self, element):
        """
        Wait until the element is clickable and then click it.
        
        Args:
            element: WebElement to click
            
        Returns:
            bool: True if click was successful, False otherwise
        """
        try:
            self.wait.until(ec.element_to_be_clickable(element)).click()
            return True
        except StaleElementReferenceException:
            logger.warning("Element became stale, retrying...")
            raise  # Let the retry decorator handle it
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            raise
            
    @safe_operation
    def send_connection_request(self):
        """
        Click the 'Send without a note' button or the 'Send' button.
        
        Returns:
            bool: True if send was successful, False otherwise
        """
        try:
            logger.debug("Attempting to click 'Send without a note' button")
            send_button = self.driver.find_element(By.XPATH, SEND_WITHOUT_NOTE_XPATH)
            self.wait_to_click(send_button)
            logger.debug("Successfully clicked 'Send without a note' button")
            return True
        except NoSuchElementException:
            try:
                logger.debug("'Send without a note' button not found, trying regular 'Send' button")
                send_button = self.driver.find_element(By.XPATH, SEND_BUTTON_XPATH)
                self.wait_to_click(send_button)
                logger.debug("Successfully clicked 'Send' button")
                return True
            except NoSuchElementException:
                logger.warning("'Send' button not found")
                return False
        except Exception as e:
            logger.error(f"Error clicking the 'Send' button: {e}")
            try:
                logger.debug("Attempting to dismiss modal")
                close_button = self.driver.find_element(By.XPATH, DISMISS_BUTTON_XPATH)
                self.wait_to_click(close_button)
                logger.debug("Modal dismissed")
            except NoSuchElementException:
                logger.warning("'Dismiss' button not found")
            except Exception as close_exception:
                logger.error(f"Error closing the modal: {close_exception}")
            return False
            
    @safe_operation
    def process_connection_buttons(self, button_list):
        """
        Process connection buttons from the provided list.
        
        Args:
            button_list: List of WebElement objects representing buttons
            
        Returns:
            bool: True if processing should continue, False if max connections reached
        """
        if not button_list:
            logger.warning("No buttons to process")
            return True
            
        logger.info(f"Processing {len(button_list)} buttons")
        
        # Store the main window handle if not already set
        if not self.main_window:
            self.main_window = self.driver.current_window_handle
        
        for button in button_list:
            # Check if we've reached the maximum connections limit
            # If max_connections is 0, it means unlimited
            if 0 < self.max_connections <= self.connection_count:
                logger.info(f"Maximum connections limit reached ({self.max_connections})")
                return False
                
            try:
                if button.text == "Follow":
                    self._open_profile_in_new_tab(button)
                elif button.text == "Connect":
                    button.click()
                    sleep()
                    if self.send_connection_request():
                        self.connection_count += 1
                        logger.info(f"Connection request #{self.connection_count} sent successfully")
            except StaleElementReferenceException:
                logger.warning("Button element is stale - skipping")
                continue
            except Exception as e:
                logger.error(f"Error processing button: {e}")
                continue
        
        return True
        
    def _open_profile_in_new_tab(self, button):
        """
        Open a LinkedIn profile in a new tab to the side.
        
        Args:
            button: WebElement representing the Follow button
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        logger.debug("Processing 'Follow' button - opening profile in new tab")
        try:
            # Go to the common ancestor
            common_ancestor = button.find_element(By.XPATH, './ancestor::li')
            
            # From the common ancestor, find the profile link
            profile_link = common_ancestor.find_element(
                By.XPATH, './/div/div/div[2]/div[1]/div[1]/div/span[1]/span/a'
            )
            
            # Get the href attribute
            profile_url = profile_link.get_attribute('href')
            
            # Open the profile in a new tab in the background
            # Use JavaScript to open in a new tab and explicitly keep focus on current tab
            current_tab = self.driver.current_window_handle
            self.driver.execute_script(f"window.open('{profile_url}', '_blank');")
            self.driver.switch_to.window(current_tab)  # Switch back to maintain focus on current tab
            
            logger.debug("Profile opened in new tab in the background")
            return True
        except Exception as e:
            logger.error(f"Error opening profile in new tab: {e}")
            return False
    
    @retry(max_attempts=2)
    def connect_in_profile_tab(self):
        """
        Connect with a profile in the current tab using the 'More' dropdown.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            logger.info("Attempting to connect with profile in current tab")
            
            # Look for 'More' button
            logger.debug("Looking for 'More' button")
            more_button = self.driver.find_element(By.XPATH, PROFILE_MORE_BUTTON_XPATH)
            sleep()
            self.wait_to_click(more_button)
            logger.debug("Clicked 'More' button")
            
            # Look for 'Connect' button in dropdown
            logger.debug("Looking for 'Connect' button in dropdown")
            connect_button = self.driver.find_element(By.XPATH, PROFILE_CONNECT_BUTTON_XPATH)
            sleep()
            self.wait_to_click(connect_button)
            logger.debug("Clicked 'Connect' button")
            
            # Send connection request
            if self.send_connection_request():
                self.connection_count += 1
                logger.info(f"Connection request #{self.connection_count} sent successfully")
                return True
            else:
                logger.warning("Failed to send connection request")
                return False
                
        except NoSuchElementException as e:
            logger.warning(f"'Connect' button not found: {e}")
            return False
        except StaleElementReferenceException as e:
            logger.warning(f"Element became stale: {e}")
            raise  # Let the retry decorator handle it
        except Exception as e:
            logger.error(f"Error connecting with profile: {e}", exc_info=True)
            return False
    
    @safe_operation
    def process_opened_tabs(self, tabs=None):
        """
        Process all opened tabs, attempting to connect with profiles in each tab.
        
        Args:
            tabs (list, optional): List of tab handles to process. If None, uses
                all currently open tabs except the main window.
                
        Returns:
            int: Number of successful connections made during processing
        """
        initial_count = self.connection_count
        try:
            # Make sure main window is set
            if not self.main_window:
                self.main_window = self.driver.current_window_handle
                
            # Get all open tabs
            all_tabs = self.driver.window_handles
            
            # Find tabs to process (all except main window)
            tabs_to_process = [tab for tab in all_tabs if tab != self.main_window]
            
            logger.info(f"Found {len(tabs_to_process)} tabs to process")
            
            # Process all tabs except the main window
            for i, tab in enumerate(tabs_to_process, 1):
                try:
                    logger.debug(f"Switching to tab {i}")
                    self.driver.switch_to.window(tab)
                    
                    # Wait for tab content to load
                    sleep()
                    
                    # Attempt to connect
                    success = self.connect_in_profile_tab()
                    
                    # Close the tab
                    self.driver.close()
                    
                except Exception as e:
                    logger.error(f"Error processing tab {i}: {e}")
                    try:
                        self.driver.close()  # Try to close the tab even if there was an error
                    except Exception:
                        pass  # Ignore any errors during close
                
            # Switch back to the main window
            logger.debug("Switching back to main window")
            self.driver.switch_to.window(self.main_window)
            
            connections_made = self.connection_count - initial_count
            logger.info(f"Tab processing complete. Connections made: {connections_made}")
            
            return connections_made
            
        except Exception as e:
            logger.error(f"Error processing tabs: {e}", exc_info=True)
            # Attempt to return to main window in case of error
            try:
                if self.main_window:
                    self.driver.switch_to.window(self.main_window)
            except Exception:
                pass
            
            return self.connection_count - initial_count
    
    @retry(max_attempts=2)
    def go_to_next_page(self):
        """
        Navigate to the next page of search results.
        
        Returns:
            bool: True if navigation to next page was successful, False otherwise
        """
        try:
            logger.info("Navigating to next page")
            sleep(PAGE_LOAD_WAIT_RANGE)
            next_button = self.driver.find_element(By.XPATH, NEXT_BUTTON_XPATH)
            self.wait_to_click(next_button)
            logger.info("Successfully navigated to next page")
            return True
            
        except NoSuchElementException:
            logger.warning("'Next' button not found")
            return False
            
        except ElementNotInteractableException:
            logger.debug("'Got it' dialog intercepting, handling it")
            sleep(PAGE_LOAD_WAIT_RANGE)
            
            try:
                got_it_button = self.driver.find_element(By.XPATH, GOT_IT_BUTTON_XPATH)
                self.wait_to_click(got_it_button)
                logger.debug("Clicked 'Got it' button")
                
                next_button = self.driver.find_element(By.XPATH, NEXT_BUTTON_XPATH)
                self.wait_to_click(next_button)
                logger.info("Successfully navigated to next page after handling dialog")
                return True
                
            except Exception as e:
                logger.error(f"Error handling 'Got it' dialog: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def find_and_process_buttons(self):
        """
        Find and process Connect/Follow buttons on the current page.
        
        Returns:
            bool: True if processing should continue, False otherwise
        """
        logger.info("Finding and processing buttons on current page")
        sleep()
        buttons = self.find_connection_buttons()
        
        if not buttons:
            logger.warning("No buttons found, retrying after longer wait")
            sleep(PAGE_LOAD_WAIT_RANGE)
            buttons = self.find_connection_buttons()
            if not buttons:
                logger.warning("No buttons found again, moving to next page")
                return self.go_to_next_page()
        
        logger.info(f"Found {len(buttons)} buttons")
        sleep()
        return self.process_connection_buttons(buttons)
    
    def run_connection_campaign(self, search_url, max_tabs=None, max_connections=None):
        """
        Run a connection campaign from a search URL.
        
        Args:
            search_url (str): LinkedIn search URL with the profiles to connect with
            max_tabs (int, optional): Maximum number of side tabs to open.
                Defaults to MAX_TABS from settings.
            max_connections (int, optional): Maximum number of connections to send.
                Defaults to MAX_CONNECTIONS from settings. Use 0 for unlimited.
                
        Returns:
            dict: Connection statistics
        """
        from linkedin_automation.config.settings import MAX_TABS, MAX_CONNECTIONS
        
        max_tabs = max_tabs or MAX_TABS
        self.max_connections = max_connections if max_connections is not None else MAX_CONNECTIONS
        
        # If max_connections is 0, log that connections are unlimited
        if self.max_connections == 0:
            logger.info("Running with UNLIMITED connections")
        else:
            logger.info(f"Maximum connections set to: {self.max_connections}")
        
        # Store the main window handle
        self.main_window = self.driver.current_window_handle
        
        # Navigate to the search URL
        logger.info(f"Starting connection campaign from URL: {search_url}")
        self.driver.get(search_url)
        sleep(PAGE_LOAD_WAIT_RANGE)
        
        try:
            # Main processing loop
            while True:
                # Find and process buttons on the current page
                if not self.find_and_process_buttons():
                    logger.info("No more buttons to process. Exiting...")
                    break
                
                # Process tabs if we've reached the maximum
                tab_count = len(self.driver.window_handles) - 1  # Subtract 1 for main window
                if tab_count >= max_tabs:
                    logger.info(f"Maximum number of tabs reached ({max_tabs}). Processing...")
                    self.process_opened_tabs()
                
                # Move to the next page
                logger.info("Moving to the next page...")
                if not self.go_to_next_page():
                    logger.info("No more pages. Exiting...")
                    break
                
        except KeyboardInterrupt:
            logger.info("Operation interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in connection campaign: {e}", exc_info=True)
        finally:
            # Process any remaining open tabs
            logger.info("Processing any remaining open tabs...")
            self.process_opened_tabs()
            
            # Make sure we're back on the main window
            if self.main_window:
                try:
                    self.driver.switch_to.window(self.main_window)
                except Exception:
                    pass
        
        logger.info(f"Connection campaign completed. Total connections sent: {self.connection_count}")
        
        return {
            "successful_connections": self.connection_count,
            "max_connections": self.max_connections
        }