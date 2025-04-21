import os
import sys
# from bs4 import BeautifulSoup # No longer needed
from linkedin_automation.job_data_extractor import JobDataExtractor
# Selenium import for type hinting
from selenium.webdriver.remote.webdriver import WebDriver


class LinkedInJobDataManager:
    """
    Main class to manage LinkedIn job data extraction and CSV export using Selenium.
    """

    def __init__(self, data_dir):
        """
        Initialize the manager with the data directory.

        Args:
            data_dir (str): Path to the data directory where 'jobs.csv' will be stored.
        """
        self.data_dir = data_dir
        # Keep the output directory structure as before (e.g., data/jobs/)
        self.jobs_dir = os.path.join(data_dir, 'jobs')
        self.job_extractor = JobDataExtractor(self.jobs_dir)

        # Ensure jobs directory exists
        os.makedirs(self.jobs_dir, exist_ok=True)

    def process_job_search_page(self, driver: WebDriver, scroll_limit: int = 5):
        """
        Process the current LinkedIn job search page using Selenium WebDriver
        to extract job data and save it to CSV.

        Args:
            driver (WebDriver): The Selenium WebDriver instance on the job search page.
            scroll_limit (int): Max number of scrolls to load more jobs.
        """
        print(f"Starting job extraction from the current page...")
        job_data_list = self.job_extractor.extract_job_data_from_page(driver, scroll_limit)
        if job_data_list:
            print(f"Saving {len(job_data_list)} extracted jobs to CSV...")
            self.job_extractor.save_job_data_to_csv(job_data_list)
        else:
            print("No job data extracted from this page.")
        # Return the list for potential further use
        return job_data_list

    def update_job_status(self, job_url, status):
        """
        Update the status of a job in the CSV file.

        Args:
            job_url (str): URL of the job to update (should be the clean URL)
            status (str): New status value (Submitted, Skipped, Error, Pending)
        """
        self.job_extractor.update_job_status(job_url, status)

    def get_csv_path(self):
        """
        Get the path to the CSV file.

        Returns:
            str: Path to the CSV file (e.g., data/jobs/linkedin_jobs.csv)
        """
        return self.job_extractor.csv_path