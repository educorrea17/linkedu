"""
Configuration settings for the LinkedIn Automation package.
"""
import os
import json
import toml
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
COOKIES_DIR = DATA_DIR / "cookies"
CONFIG_FILE = BASE_DIR / "config.toml"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
COOKIES_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_CONFIG = {
    "general": {
        "browser": "chrome",
        "headless": False,
        "timeout": 30,
        "retry_attempts": 3,
        "data_storage": "csv",
        "log_level": "INFO"
    },
    "linkedin": {
        "username": "",
        "password": "",
        "use_cookies": True
    },
    "connection": {
        "max_connections_per_day": 60,  # Set to 0 for unlimited connections
        "max_tabs": 3,
        "connection_message_template": "Hi {name}, I'd like to connect with you on LinkedIn.",
        "search_url": ""
    },
    "job_application": {
        "enabled": False,
        "search_url": "",
        "keywords": "",
        "location": "",
        "max_applications_per_day": 10,  # Set to 0 for unlimited applications
        "easy_apply_only": True
    },
    "profile": {
        # Personal information
        "full_name": "",
        "phone": "",
        "email": "",
        "location": "",
        "years_of_experience": "",
        
        # Work authorization
        "work_authorization": "",
        "require_sponsorship": "",
        
        # Education
        "education_level": "",
        "graduation_date": "",
        "field_of_study": "",
        "school": "",
        "gpa": "",
        
        # Experience
        "current_job_title": "",
        "current_company": "",
        "years_at_current_company": "",
        "total_years_experience": "",
        
        # Skills
        "technical_skills": "",
        "soft_skills": "",
        "languages": "",
        
        # Questionnaire responses
        "willing_to_relocate": "",
        "remote_preference": "",
        "expected_salary": "",
        "reason_for_leaving": "",
        "notice_period": "",
        "linkedin_profile": ""
    }
}


def load_config():
    """
    Load configuration from the config.toml file or create one if it doesn't exist.
    
    Returns:
        dict: Configuration dictionary
    """
    if not CONFIG_FILE.exists():
        # Create a default config file if it doesn't exist
        with open(CONFIG_FILE, 'w') as f:
            toml.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = toml.load(f)
        
        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        for section in config:
            if section in merged_config:
                merged_config[section].update(config[section])
            else:
                merged_config[section] = config[section]
                
        return merged_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG


# Load configuration
CONFIG = load_config()
LOG_LEVEL = CONFIG["general"]["log_level"]

# Browser settings
BROWSER_CONFIG = {
    "browser": CONFIG["general"]["browser"],
    "headless": CONFIG["general"]["headless"],
    "timeout": CONFIG["general"]["timeout"],
    "disable_extensions": True,
    "disable_gpu": True,
    "disable_dev_shm_usage": True,
    "no_sandbox": True,
    "disable_notifications": True,
    "disable_popup_blocking": True,
    "js_flags": "--expose-gc",
    "enable_precise_memory_info": True
}

# Connection settings
MAX_CONNECTIONS = CONFIG["connection"]["max_connections_per_day"]
DEFAULT_WAIT_RANGE = (1, 3)
PAGE_LOAD_WAIT_RANGE = (3, 6)
MAX_TABS = CONFIG["connection"]["max_tabs"]
CONNECTION_MESSAGE_TEMPLATE = CONFIG["connection"]["connection_message_template"]

# Profile settings
PROFILE_CONFIG = CONFIG.get("profile", {})

# Authentication
LINKEDIN_USERNAME = CONFIG["linkedin"]["username"]
LINKEDIN_PASSWORD = CONFIG["linkedin"]["password"]

# Feature flags
ENABLE_JOB_APPLICATIONS = CONFIG["job_application"]["enabled"]
MAX_APPLICATIONS = CONFIG["job_application"]["max_applications_per_day"]
EASY_APPLY_ONLY = CONFIG["job_application"]["easy_apply_only"]

# Cookie settings
USE_COOKIES = CONFIG["linkedin"]["use_cookies"]
COOKIES_PATH = COOKIES_DIR / "linkedin_cookies.json"

def save_cookies(cookies, username=None):
    """
    Save cookies to a file.
    
    Args:
        cookies (list): List of cookie dictionaries
        username (str, optional): Username to include in filename
    """
    if not cookies:
        return
        
    # Use username-specific cookie file if provided
    cookie_path = COOKIES_PATH
    if username:
        cookie_path = COOKIES_DIR / f"linkedin_cookies_{username.split('@')[0]}.json"
        
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f)


def load_cookies(username=None):
    """
    Load cookies from a file.
    
    Args:
        username (str, optional): Username to include in filename
        
    Returns:
        list: List of cookie dictionaries or None if file doesn't exist
    """
    # Use username-specific cookie file if provided
    cookie_path = COOKIES_PATH
    if username:
        cookie_path = COOKIES_DIR / f"linkedin_cookies_{username.split('@')[0]}.json"
        
    if not cookie_path.exists():
        return None
        
    try:
        with open(cookie_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None