"""
Job application functionality for the LinkedIn Automation package.
"""
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from linkedin_automation.config.constants import (
    JOB_APPLY_BUTTON_XPATH, JOB_SUBMIT_BUTTON_XPATH, JOB_SUCCESS_MESSAGE_XPATH,
    JOB_SEARCH_KEYWORD_XPATH, JOB_SEARCH_LOCATION_XPATH, JOB_SEARCH_BUTTON_XPATH,
    NEXT_BUTTON_XPATH
)
from linkedin_automation.config.settings import PAGE_LOAD_WAIT_RANGE
from linkedin_automation.utils.decorators import safe_operation, retry
from linkedin_automation.utils.helpers import sleep
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

class JobApplicationManager:
    """Manage LinkedIn job applications."""
    
    def __init__(self, browser):
        """
        Initialize the JobApplicationManager.
        
        Args:
            browser: Browser instance to use for automation
        """
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait
        self.application_count = 0
        self.viewed_jobs_count = 0
        from linkedin_automation.config.settings import MAX_APPLICATIONS
        self.max_applications = MAX_APPLICATIONS  # Will be updated in run_job_campaign
        
    @safe_operation
    def search_jobs(self, keywords, location, filters=None):
        """
        Search for jobs using keywords and location.
        
        Args:
            keywords (str): Job keywords
            location (str): Job location
            filters (dict, optional): Additional search filters
            
        Returns:
            bool: True if search was successful
        """
        try:
            logger.info(f"Searching jobs with keywords: '{keywords}' in '{location}'")
            
            # Navigate to LinkedIn Jobs page
            self.driver.get("https://www.linkedin.com/jobs/")
            sleep(PAGE_LOAD_WAIT_RANGE)
            
            # Enter keywords
            keyword_input = self.wait.until(ec.element_to_be_clickable(
                (By.XPATH, JOB_SEARCH_KEYWORD_XPATH)
            ))
            keyword_input.clear()
            keyword_input.send_keys(keywords)
            
            # Enter location
            location_input = self.wait.until(ec.element_to_be_clickable(
                (By.XPATH, JOB_SEARCH_LOCATION_XPATH)
            ))
            location_input.clear()
            location_input.send_keys(location)
            
            # Click search button
            search_button = self.wait.until(ec.element_to_be_clickable(
                (By.XPATH, JOB_SEARCH_BUTTON_XPATH)
            ))
            search_button.click()
            sleep(PAGE_LOAD_WAIT_RANGE)
            
            logger.info("Job search completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during job search: {e}")
            return False
    
    @safe_operation
    def find_job_listings(self):
        """
        Find job listings on the current page.
        
        Returns:
            list: List of WebElement objects representing job listings
        """
        try:
            logger.debug("Finding job listings on current page")
            # Job cards are typically in a list with specific class names
            job_cards = self.driver.find_elements(
                By.XPATH, "//div[@class='scaffold-layout__list ']"
            )
            logger.debug(f"Found {len(job_cards)} job listings")
            return job_cards
        except Exception as e:
            logger.error(f"Error finding job listings: {e}")
            return []
    
    @retry(max_attempts=2)
    def apply_to_job(self, job_card=None):
        """
        Apply to a job posting.
        
        Args:
            job_card: WebElement representing the job card (optional)
            
        Returns:
            bool: True if application was successful
        """
        try:
            if job_card:
                # Click on the job card to view details
                job_card.click()
                sleep()
                self.viewed_jobs_count += 1
                
            # Find and click the "Easy Apply" button
            apply_button = self.wait.until(ec.element_to_be_clickable(
                (By.XPATH, JOB_APPLY_BUTTON_XPATH)
            ))
            apply_button.click()
            logger.debug("Clicked 'Easy Apply' button")
            sleep()
            
            # Handle application form (simplified)
            self._fill_application_form()
            
            # Submit application
            submit_button = self.wait.until(ec.element_to_be_clickable(
                (By.XPATH, JOB_SUBMIT_BUTTON_XPATH)
            ))
            submit_button.click()
            logger.debug("Clicked 'Submit application' button")
            
            # Verify submission
            success_message = self.wait.until(ec.presence_of_element_located(
                (By.XPATH, JOB_SUCCESS_MESSAGE_XPATH)
            ))
            
            if success_message:
                self.application_count += 1
                logger.info(f"Job application #{self.application_count} submitted successfully")
                return True
            return False
            
        except TimeoutException as e:
            logger.error(f"Timeout during job application: {e}")
            return False
        except NoSuchElementException as e:
            logger.error(f"Element not found during job application: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during job application: {e}")
            return False
            
    def _fill_application_form(self):
        """
        Fill out the job application form using profile data from config.
        
        Returns:
            bool: True if form filling was successful
        """
        from linkedin_automation.config.settings import CONFIG
        
        # Get profile data from config
        profile_data = CONFIG.get("profile", {})
        logger.debug("Filling out application form with profile data")
        
        try:
            # Process each form step
            form_step = 1
            while True:
                logger.debug(f"Processing form step {form_step}")
                sleep()
                
                # Find all input fields in the current form step
                self._fill_form_inputs(profile_data)
                
                # Find all select/dropdown fields
                self._fill_form_dropdowns(profile_data)
                
                # Find all textarea fields
                self._fill_form_textareas(profile_data)
                
                # Find all radio button groups
                self._fill_form_radio_buttons(profile_data)
                
                # Find all checkbox fields
                self._fill_form_checkboxes(profile_data)
                
                # Try to move to the next step
                try:
                    # Look for Next, Continue, or Review buttons
                    for button_text in ["Continue to next step", "Review your application", "Next", "Review"]:
                        try:
                            next_button = self.driver.find_element(
                                By.XPATH, f"//button[contains(@aria-label, '{button_text}') or contains(text(), '{button_text}')]"
                            )
                            next_button.click()
                            sleep()
                            form_step += 1
                            break
                        except NoSuchElementException:
                            continue
                    else:
                        # If we get here, no next button was found
                        logger.debug("No more form steps found")
                        break
                except Exception as e:
                    logger.error(f"Error navigating form: {e}")
                    break
            
            logger.debug("Application form completed")
            return True
            
        except Exception as e:
            logger.error(f"Error filling application form: {e}", exc_info=True)
            return False
            
    def _fill_form_inputs(self, profile_data):
        """
        Fill text input fields in the form using profile data.
        
        Args:
            profile_data (dict): Profile data from config
        """
        # Common field mappings (form field label -> profile data key)
        field_mappings = {
            "name": "full_name",
            "first name": "full_name",
            "last name": "full_name",
            "phone": "phone",
            "email": "email",
            "address": "location",
            "city": "location",
            "years of experience": "years_of_experience",
            "linkedin": "linkedin_profile",
            "website": "linkedin_profile",
            "salary": "expected_salary",
            "notice period": "notice_period",
            "university": "school",
            "college": "school",
            "institution": "school",
            "gpa": "gpa",
            "graduation date": "graduation_date",
            "company": "current_company",
            "job title": "current_job_title",
            "years": "total_years_experience"
        }
        
        try:
            # Find all input fields with labels
            input_fields = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='tel' or @type='email' or @type='url']")
            
            for input_field in input_fields:
                try:
                    # Try to get the field's label from aria-label, placeholder, or associated label
                    field_label = (
                        input_field.get_attribute("aria-label") or 
                        input_field.get_attribute("placeholder") or 
                        self._get_label_for_field(input_field)
                    )
                    
                    if not field_label:
                        continue
                        
                    field_label = field_label.lower()
                    
                    # Find the matching profile data key
                    matched_key = None
                    for label_pattern, profile_key in field_mappings.items():
                        if label_pattern in field_label and profile_data.get(profile_key):
                            matched_key = profile_key
                            break
                    
                    # If no match found in mappings but field label is a direct match with a profile key
                    if not matched_key:
                        for profile_key in profile_data:
                            if profile_key.replace("_", " ") in field_label and profile_data.get(profile_key):
                                matched_key = profile_key
                                break
                    
                    # Fill the field if we found a match
                    if matched_key and profile_data.get(matched_key):
                        input_field.clear()
                        input_field.send_keys(profile_data[matched_key])
                        logger.debug(f"Filled field '{field_label}' with value from '{matched_key}'")
                    else:
                        # Field not found in profile data
                        logger.debug(f"No data found for field: {field_label}")
                        
                        # Add this field to the config.toml if not already present
                        self._add_missing_field_to_config(field_label)
                        
                except Exception as e:
                    logger.warning(f"Error filling input field: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in _fill_form_inputs: {e}")
            
    def _fill_form_dropdowns(self, profile_data):
        """
        Fill select/dropdown fields in the form using profile data.
        
        Args:
            profile_data (dict): Profile data from config
        """
        # Common dropdown field mappings
        dropdown_mappings = {
            "education": "education_level",
            "degree": "education_level",
            "field of study": "field_of_study",
            "major": "field_of_study",
            "authorization": "work_authorization",
            "sponsorship": "require_sponsorship",
            "relocate": "willing_to_relocate",
            "work location": "remote_preference",
            "remote": "remote_preference",
            "language": "languages"
        }
        
        try:
            # Find all select elements
            select_elements = self.driver.find_elements(By.XPATH, "//select")
            
            for select_element in select_elements:
                try:
                    # Get the field's label
                    field_label = (
                        select_element.get_attribute("aria-label") or 
                        self._get_label_for_field(select_element)
                    )
                    
                    if not field_label:
                        continue
                        
                    field_label = field_label.lower()
                    
                    # Find the matching profile data key
                    matched_key = None
                    for label_pattern, profile_key in dropdown_mappings.items():
                        if label_pattern in field_label and profile_data.get(profile_key):
                            matched_key = profile_key
                            break
                    
                    # If no match found in mappings but field label is a direct match with a profile key
                    if not matched_key:
                        for profile_key in profile_data:
                            if profile_key.replace("_", " ") in field_label and profile_data.get(profile_key):
                                matched_key = profile_key
                                break
                    
                    # Fill the dropdown if we found a match
                    if matched_key and profile_data.get(matched_key):
                        # Find the option closest to our value
                        options = select_element.find_elements(By.XPATH, ".//option")
                        user_value = profile_data[matched_key].lower()
                        
                        best_match = None
                        for option in options:
                            option_text = option.text.lower()
                            if option_text in user_value or user_value in option_text:
                                best_match = option
                                break
                        
                        if best_match:
                            best_match.click()
                            logger.debug(f"Selected option for '{field_label}' with value from '{matched_key}'")
                        else:
                            logger.debug(f"No matching option found for '{field_label}'")
                    else:
                        # Field not found in profile data
                        logger.debug(f"No data found for dropdown: {field_label}")
                        
                        # Add this field to the config.toml if not already present
                        self._add_missing_field_to_config(field_label)
                        
                except Exception as e:
                    logger.warning(f"Error filling dropdown: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in _fill_form_dropdowns: {e}")
            
    def _fill_form_textareas(self, profile_data):
        """
        Fill textarea fields in the form using profile data.
        
        Args:
            profile_data (dict): Profile data from config
        """
        # Common textarea field mappings
        textarea_mappings = {
            "reason": "reason_for_leaving",
            "leaving": "reason_for_leaving",
            "skills": "technical_skills",
            "technical": "technical_skills",
            "soft skills": "soft_skills",
            "experience": "total_years_experience",
            "additional information": "additional_information"
        }
        
        try:
            # Find all textarea elements
            textarea_elements = self.driver.find_elements(By.XPATH, "//textarea")
            
            for textarea in textarea_elements:
                try:
                    # Get the field's label
                    field_label = (
                        textarea.get_attribute("aria-label") or 
                        textarea.get_attribute("placeholder") or 
                        self._get_label_for_field(textarea)
                    )
                    
                    if not field_label:
                        continue
                        
                    field_label = field_label.lower()
                    
                    # Find the matching profile data key
                    matched_key = None
                    for label_pattern, profile_key in textarea_mappings.items():
                        if label_pattern in field_label and profile_data.get(profile_key):
                            matched_key = profile_key
                            break
                    
                    # If no match found in mappings but field label is a direct match with a profile key
                    if not matched_key:
                        for profile_key in profile_data:
                            if profile_key.replace("_", " ") in field_label and profile_data.get(profile_key):
                                matched_key = profile_key
                                break
                    
                    # Fill the textarea if we found a match
                    if matched_key and profile_data.get(matched_key):
                        textarea.clear()
                        textarea.send_keys(profile_data[matched_key])
                        logger.debug(f"Filled textarea '{field_label}' with value from '{matched_key}'")
                    else:
                        # Field not found in profile data
                        logger.debug(f"No data found for textarea: {field_label}")
                        
                        # Add this field to the config.toml if not already present
                        self._add_missing_field_to_config(field_label)
                        
                except Exception as e:
                    logger.warning(f"Error filling textarea: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in _fill_form_textareas: {e}")
            
    def _fill_form_radio_buttons(self, profile_data):
        """
        Fill radio button groups in the form using profile data.
        
        Args:
            profile_data (dict): Profile data from config
        """
        # Common radio button field mappings
        radio_mappings = {
            "relocate": "willing_to_relocate",
            "work remotely": "remote_preference",
            "authorized": "work_authorization",
            "sponsorship": "require_sponsorship"
        }
        
        try:
            # Find all radio button groups
            radio_groups = self.driver.find_elements(By.XPATH, "//fieldset")
            
            for group in radio_groups:
                try:
                    # Get the group's legend/label
                    legend = group.find_element(By.XPATH, "./legend")
                    field_label = legend.text.lower()
                    
                    # Find the matching profile data key
                    matched_key = None
                    for label_pattern, profile_key in radio_mappings.items():
                        if label_pattern in field_label and profile_data.get(profile_key):
                            matched_key = profile_key
                            break
                    
                    # If no match found in mappings but field label is a direct match with a profile key
                    if not matched_key:
                        for profile_key in profile_data:
                            if profile_key.replace("_", " ") in field_label and profile_data.get(profile_key):
                                matched_key = profile_key
                                break
                    
                    # Select the radio button if we found a match
                    if matched_key and profile_data.get(matched_key):
                        # Get all radio buttons in the group
                        radio_buttons = group.find_elements(By.XPATH, ".//input[@type='radio']")
                        labels = group.find_elements(By.XPATH, ".//label")
                        
                        user_value = profile_data[matched_key].lower()
                        
                        # Find the label that best matches our value
                        selected = False
                        for label in labels:
                            label_text = label.text.lower()
                            if user_value in label_text or (
                                ("yes" in user_value and "yes" in label_text) or
                                ("no" in user_value and "no" in label_text)
                            ):
                                # Click the label to select the corresponding radio button
                                label.click()
                                selected = True
                                logger.debug(f"Selected radio option '{label_text}' for '{field_label}'")
                                break
                        
                        if not selected:
                            logger.debug(f"No matching radio option found for '{field_label}'")
                    else:
                        # Field not found in profile data
                        logger.debug(f"No data found for radio group: {field_label}")
                        
                        # Add this field to the config.toml if not already present
                        self._add_missing_field_to_config(field_label)
                        
                except NoSuchElementException:
                    # This fieldset might not have a legend
                    continue
                except Exception as e:
                    logger.warning(f"Error filling radio buttons: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in _fill_form_radio_buttons: {e}")
            
    def _fill_form_checkboxes(self, profile_data):
        """
        Fill checkbox fields in the form using profile data.
        
        Args:
            profile_data (dict): Profile data from config
        """
        try:
            # Find all checkbox elements
            checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            
            for checkbox in checkboxes:
                try:
                    # Get the checkbox's label
                    field_label = self._get_label_for_field(checkbox)
                    
                    if not field_label:
                        continue
                        
                    field_label = field_label.lower()
                    field_key = field_label.replace(" ", "_")
                    
                    # Check if there's a matching key in profile data
                    if field_key in profile_data and profile_data[field_key]:
                        # Determine whether to check the box based on the value
                        value = profile_data[field_key].lower()
                        should_check = value in ["yes", "true", "1", "checked"]
                        
                        # Check or uncheck based on the value
                        is_checked = checkbox.is_selected()
                        if should_check and not is_checked:
                            checkbox.click()
                            logger.debug(f"Checked checkbox: {field_label}")
                        elif not should_check and is_checked:
                            checkbox.click()
                            logger.debug(f"Unchecked checkbox: {field_label}")
                    else:
                        # Field not found in profile data
                        logger.debug(f"No data found for checkbox: {field_label}")
                        
                        # Add this field to the config.toml if not already present
                        self._add_missing_field_to_config(field_label)
                        
                except Exception as e:
                    logger.warning(f"Error handling checkbox: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in _fill_form_checkboxes: {e}")
            
    def _get_label_for_field(self, field_element):
        """
        Get the associated label text for a form field.
        
        Args:
            field_element: WebElement representing the form field
            
        Returns:
            str: Label text or None if not found
        """
        try:
            # Try to get by id-for relationship
            field_id = field_element.get_attribute("id")
            if field_id:
                try:
                    label = self.driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                    return label.text
                except NoSuchElementException:
                    pass
            
            # Try to get by parent-label relationship
            try:
                label = field_element.find_element(By.XPATH, "./ancestor::label")
                return label.text
            except NoSuchElementException:
                pass
                
            # Try to get label from siblings/nearby elements
            try:
                parent = field_element.find_element(By.XPATH, "./parent::div")
                labels = parent.find_elements(By.XPATH, ".//label | .//div[contains(@class, 'label')]")
                if labels:
                    return labels[0].text
            except NoSuchElementException:
                pass
                
            return None
        except Exception:
            return None
            
    def _add_missing_field_to_config(self, field_label):
        """
        Add a missing field to the config.toml file.
        
        Args:
            field_label (str): The field label found in the form
        """
        from pathlib import Path
        import toml
        from linkedin_automation.config.settings import CONFIG_FILE, CONFIG
        
        try:
            # Only process if we have a valid field label
            if not field_label or len(field_label) < 3:
                return
                
            # Clean and normalize the field name
            field_key = field_label.lower().strip()
            field_key = field_key.replace(" ", "_").replace("-", "_")
            
            # Remove any special characters
            import re
            field_key = re.sub(r'[^a-z0-9_]', '', field_key)
            
            # Check if this field already exists in the profile section
            if "profile" in CONFIG and field_key in CONFIG["profile"]:
                return
                
            # Add the field to the CONFIG in memory
            if "profile" not in CONFIG:
                CONFIG["profile"] = {}
                
            CONFIG["profile"][field_key] = ""
            
            # Update the config file
            config_path = Path(CONFIG_FILE)
            if config_path.exists():
                try:
                    # Read existing file
                    current_config = toml.load(config_path)
                    
                    # Add or update the profile section
                    if "profile" not in current_config:
                        current_config["profile"] = {}
                        
                    current_config["profile"][field_key] = ""
                    
                    # Write back to the file
                    with open(config_path, "w") as f:
                        toml.dump(current_config, f)
                        
                    logger.debug(f"Added missing field '{field_key}' to config.toml")
                except Exception as e:
                    logger.error(f"Error updating config.toml: {e}")
        except Exception as e:
            logger.error(f"Error adding missing field to config: {e}")
    
    @retry(max_attempts=2)
    def go_to_next_page(self):
        """
        Navigate to the next page of job results.
        
        Returns:
            bool: True if navigation to next page was successful, False otherwise
        """
        try:
            logger.info("Navigating to next page of job listings")
            sleep(PAGE_LOAD_WAIT_RANGE)
            next_button = self.driver.find_element(By.XPATH, NEXT_BUTTON_XPATH)
            next_button.click()
            logger.info("Successfully navigated to next page")
            sleep(PAGE_LOAD_WAIT_RANGE)
            return True
            
        except NoSuchElementException:
            logger.warning("'Next' button not found")
            return False
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def run_job_campaign(self, search_url=None, keywords=None, location=None, max_applications=10):
        """
        Run a job application campaign.
        
        Args:
            search_url (str, optional): LinkedIn job search URL
            keywords (str, optional): Job search keywords (used if search_url not provided)
            location (str, optional): Job location (used if search_url not provided)
            max_applications (int, optional): Maximum number of applications to submit.
                Use 0 for unlimited applications.
            
        Returns:
            dict: Job application statistics
        """
        from linkedin_automation.config.settings import MAX_APPLICATIONS
        
        self.max_applications = max_applications if max_applications is not None else MAX_APPLICATIONS
        
        # If max_applications is 0, log that applications are unlimited
        if self.max_applications == 0:
            logger.info("Running with UNLIMITED job applications")
        else:
            logger.info(f"Maximum applications set to: {self.max_applications}")
        
        # Navigate to the starting point
        if search_url:
            logger.info(f"Starting job campaign from URL: {search_url}")
            self.driver.get(search_url)
        elif keywords and location:
            logger.info(f"Starting job campaign with search: {keywords} in {location}")
            self.search_jobs(keywords, location)
        else:
            logger.error("No search URL or keywords/location provided")
            return {
                "successful_applications": 0,
                "viewed_jobs": 0,
                "max_applications": self.max_applications
            }
        
        sleep(PAGE_LOAD_WAIT_RANGE)
        
        try:
            # Main processing loop
            while True:
                # Check if we've reached the maximum applications limit (unless unlimited)
                if self.max_applications > 0 and self.application_count >= self.max_applications:
                    logger.info(f"Maximum applications limit reached ({self.max_applications})")
                    break
                
                # Find job listings on the current page
                job_cards = self.find_job_listings()
                
                if not job_cards:
                    logger.warning("No job listings found on this page")
                    if not self.go_to_next_page():
                        logger.info("No more pages. Exiting...")
                        break
                    continue
                
                # Process job listings
                for job_card in job_cards:
                    # Check if we've reached the maximum applications limit (unless unlimited)
                    if self.max_applications > 0 and self.application_count >= self.max_applications:
                        logger.info(f"Maximum applications limit reached ({self.max_applications})")
                        break
                        
                    try:
                        self.apply_to_job(job_card)
                    except Exception as e:
                        logger.error(f"Error applying to job: {e}")
                
                # Move to the next page
                logger.info("Moving to the next page...")
                if not self.go_to_next_page():
                    logger.info("No more pages. Exiting...")
                    break
                
        except KeyboardInterrupt:
            logger.info("Operation interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in job campaign: {e}", exc_info=True)
        
        logger.info(f"Job campaign completed. Applications submitted: {self.application_count}")
        
        return {
            "successful_applications": self.application_count,
            "viewed_jobs": self.viewed_jobs_count,
            "max_applications": self.max_applications
        }