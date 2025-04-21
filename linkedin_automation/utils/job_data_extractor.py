import os
import csv
import re
from datetime import datetime
import time

# Selenium Imports
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException


class JobDataExtractor:
    """
    Class to extract job data from a live LinkedIn job search page using Selenium
    and save it to a CSV file in the data/jobs directory.
    Handles 'Easy Apply' vs external application jobs.
    """

    def __init__(self, output_dir):
        """
        Initialize the extractor with the output directory.

        Args:
            output_dir (str): Path to the directory where CSV will be saved
        """
        self.output_dir = output_dir
        self.csv_path = os.path.join(output_dir, 'linkedin_jobs.csv')
        self.fieldnames = [
            'Company',
            'Title',
            'URL',
            'Location',
            'PostTime',
            'Status', # Can be 'Pending', 'Skipped (External)', 'Submitted', etc.
        ]

        # Create CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_path):
            self._create_csv_file()

    def _create_csv_file(self):
        """Create a new CSV file with headers."""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()

    def extract_job_data_from_page(self, driver: WebDriver, scroll_limit: int = 5):
        """
        Extracts job data from the currently loaded LinkedIn job search page using Selenium.

        Args:
            driver (WebDriver): The Selenium WebDriver instance navigating the page.
            scroll_limit (int): Maximum number of times to scroll down to load more jobs.

        Returns:
            list: List of dictionaries containing job data extracted from the page.
        """
        job_data_list = []
        processed_job_ids = set()
        wait = WebDriverWait(driver, 10)

        for _ in range(scroll_limit):
            try:
                # Wait for the job list container to be present
                job_list_container = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                )

                # Find all job listing elements within the container that haven't been processed
                job_listings = job_list_container.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

                if not job_listings:
                    print("No job listings found on the page.")
                    break # Exit scroll loop if no listings

                new_listings_found = False
                for listing in job_listings:
                    try:
                        job_id = listing.get_attribute("data-occludable-job-id")
                        if job_id in processed_job_ids:
                            continue # Skip already processed jobs

                        new_listings_found = True
                        processed_job_ids.add(job_id)

                        # --- Extract basic data directly from the listing card ---
                        try:
                            title_element = listing.find_element(By.CSS_SELECTOR, "a.job-card-list__title")
                            title = title_element.text.strip()
                            url = title_element.get_attribute('href').split('?')[0] # Clean URL
                        except NoSuchElementException:
                            title = "Unknown Title"
                            url = "Unknown URL"

                        try:
                            company = listing.find_element(By.CSS_SELECTOR, "span.job-card-container__primary-description").text.strip()
                        except NoSuchElementException:
                            company = "Unknown Company"

                        try:
                            location = listing.find_element(By.CSS_SELECTOR, "li.job-card-container__metadata-item").text.strip()
                        except NoSuchElementException:
                            location = "Unknown Location"

                        try:
                            post_time_element = listing.find_element(By.CSS_SELECTOR, "time.job-card-container__listdate")
                            post_time = post_time_element.text.strip()
                            # Optionally convert relative time (e.g., "2 days ago") to a date
                            # post_time = post_time_element.get_attribute('datetime')
                        except NoSuchElementException:
                             try: # Try alternative selector if the first fails
                                 post_time_element = listing.find_element(By.CSS_SELECTOR, "li.job-card-container__listed-date")
                                 post_time = post_time_element.text.strip()
                             except NoSuchElementException:
                                 post_time = "Unknown Time"


                        # --- Click listing and check details pane for Easy Apply ---
                        status = 'Skipped (External)' # Default to external/skipped
                        try:
                            # Scroll the element into view before clicking
                            driver.execute_script("arguments[0].scrollIntoView(true);", listing)
                            time.sleep(0.5) # Brief pause after scroll
                            listing.click()
                            time.sleep(1) # Wait for detail pane to potentially load

                            # Wait for the apply button area in the details pane
                            apply_section = wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.jobs-apply-button--top-card"))
                                # Alternative: EC.visibility_of_element_located((By.CSS_SELECTOR, "div.jobs-search__job-details--container"))
                            )

                            # Check specifically for the "Easy Apply" button
                            try:
                                easy_apply_button = apply_section.find_element(By.CSS_SELECTOR, "button.jobs-apply-button span:-soup-contains('Easy Apply')")
                                # Note: Using :-soup-contains which might be browser/driver specific or less standard.
                                # A more robust check might look for button text or specific classes/attributes if available.
                                # Example alternative: button[aria-label*='Easy Apply']
                                # Or check button text directly:
                                # easy_apply_buttons = apply_section.find_elements(By.CSS_SELECTOR, "button.jobs-apply-button")
                                # for btn in easy_apply_buttons:
                                #    if 'Easy Apply' in btn.text:
                                #        status = 'Pending'
                                #        break
                                if easy_apply_button: # Check if element was found
                                     status = 'Pending'

                            except NoSuchElementException:
                                # Easy Apply button not found, status remains 'Skipped (External)'
                                pass

                        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as click_err:
                            print(f"Warning: Could not click or process details for job '{title}': {click_err}")
                            # Keep status as 'Skipped (External)' if details couldn't be checked

                        # Append extracted data
                        job_data = {
                            'Company': company,
                            'Title': title,
                            'URL': url,
                            'Location': location,
                            'PostTime': post_time,
                            'Status': status,
                        }
                        if job_data['URL'] != "Unknown URL": # Only add if we have a valid URL
                             job_data_list.append(job_data)

                    except StaleElementReferenceException:
                        print("Warning: Stale element reference encountered for a listing. Re-finding elements.")
                        break # Break inner loop to re-fetch listings
                    except Exception as e:
                        print(f"Error processing a job listing: {e}")
                        continue # Skip to the next listing

                # --- Scroll down to load more jobs ---
                if not new_listings_found and _ > 0: # Avoid breaking on the first pass if few jobs initially
                    print("No new listings found after scrolling. Stopping scroll.")
                    break # Stop scrolling if no new jobs were processed in this pass

                print(f"Scrolling down page (Attempt {_ + 1}/{scroll_limit})...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # Wait for new jobs to load after scroll

            except TimeoutException:
                print("Timed out waiting for job list container or elements.")
                break # Exit scroll loop if main container not found
            except Exception as e:
                print(f"An error occurred during scraping: {e}")
                break # Exit scroll loop on other errors

        print(f"Finished scraping page. Found {len(job_data_list)} potential jobs.")
        return job_data_list

    def save_job_data_to_csv(self, job_data_list):
        """
        Save job data to CSV file, avoiding duplicates based on URL.

        Args:
            job_data_list (list): List of dictionaries containing job data
        """
        if not job_data_list:
            print("No new job data provided to save.")
            return

        existing_urls = set()
        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    # Use sniff to handle potential dialect issues, though DictReader is usually robust
                    # dialect = csv.Sniffer().sniff(csvfile.read(1024))
                    # csvfile.seek(0)
                    # reader = csv.DictReader(csvfile, dialect=dialect)
                    reader = csv.DictReader(csvfile) # Simpler approach
                    if reader.fieldnames and 'URL' in reader.fieldnames:
                        for row in reader:
                            if row.get('URL'): # Check if URL key exists and value is not None/empty
                                existing_urls.add(row['URL'])
                    elif not reader.fieldnames and os.path.getsize(self.csv_path) > 0:
                         print(f"Warning: CSV file {self.csv_path} is not empty but has no header. Recreating.")
                         self._create_csv_file()
                    # else: file is empty or has header but no URL column - handled by DictWriter later
            except (FileNotFoundError, StopIteration):
                 pass # File doesn't exist or is empty, existing_urls remains empty
            except csv.Error as e:
                print(f"Error reading existing CSV: {e}. Recreating file.")
                self._create_csv_file() # Recreate if error occurs
            except Exception as e: # Catch other potential file reading errors
                 print(f"Unexpected error reading CSV {self.csv_path}: {e}. Recreating file.")
                 self._create_csv_file()


        new_jobs_added = 0
        try:
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                # Ensure fieldnames match the current class definition, even if file had different ones
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, extrasaction='ignore')

                # Write header if file is newly created or was empty
                if csvfile.tell() == 0:
                     writer.writeheader()

                for job_data in job_data_list:
                    job_url = job_data.get('URL')
                    # Ensure URL is valid and not already present
                    if job_url and job_url != "Unknown URL" and job_url not in existing_urls:
                        # No need to filter keys if using extrasaction='ignore'
                        # filtered_job_data = {k: v for k, v in job_data.items() if k in self.fieldnames}
                        writer.writerow(job_data)
                        existing_urls.add(job_url) # Add newly added URL to set
                        new_jobs_added += 1
            if new_jobs_added > 0:
                 print(f"Added {new_jobs_added} new unique jobs to {self.csv_path}")
            else:
                 print("No new unique jobs found to add to the CSV.")
        except IOError as e:
            print(f"Error writing to CSV file {self.csv_path}: {e}")
        except csv.Error as e:
             print(f"CSV writing error: {e}")


    def update_job_status(self, job_url, status):
        """
        Update the status of a job in the CSV file.

        Args:
            job_url (str): URL of the job to update (should be the clean URL)
            status (str): New status value (e.g., Submitted, Skipped, Error)
        """
        rows = []
        updated = False
        if not os.path.exists(self.csv_path):
            print(f"CSV file not found: {self.csv_path}. Cannot update status.")
            return

        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Check if required fieldnames exist before proceeding
                if not reader.fieldnames:
                    print(f"CSV file is empty or has no header: {self.csv_path}. Cannot update.")
                    return # Exit if no header
                if 'URL' not in reader.fieldnames or 'Status' not in reader.fieldnames:
                     print(f"CSV file is missing 'URL' or 'Status' column: {self.csv_path}. Cannot update.")
                     return # Exit if crucial columns are missing

                original_fieldnames = reader.fieldnames

                for row in reader:
                     # Ensure row has the URL key before accessing
                    current_url = row.get('URL')
                    if current_url and current_url.split('?')[0] == job_url.split('?')[0]: # Compare cleaned URLs
                        row['Status'] = status
                        updated = True
                    # Ensure all original columns are preserved, even if not in self.fieldnames
                    # Create a new dict to avoid modifying reader's internal dict directly if needed
                    # Although appending the list of dicts read should be fine
                    rows.append(row)

            if updated:
                # Rewrite the entire file using the *current* class fieldnames
                # This ensures consistency if fields were added/removed in the class definition
                temp_file_path = self.csv_path + '.tmp'
                with open(temp_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    # Use current self.fieldnames for writing
                    writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    # Write the updated rows, ignoring extra fields read from old file
                    writer.writerows(rows)

                # Replace the original file with the temporary file
                os.replace(temp_file_path, self.csv_path)
                print(f"Updated status for job {job_url} to '{status}'")
            else:
                print(f"Job with URL {job_url} not found for status update.")

        except FileNotFoundError:
             print(f"Error: Could not find {self.csv_path} during update process.")
        except csv.Error as e:
             print(f"CSV read/write error during update for {job_url}: {e}")
        except Exception as e:
             print(f"Unexpected error updating job status for {job_url}: {e}")