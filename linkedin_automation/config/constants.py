"""
Constants for the LinkedIn Automation package.
"""

# XPath selectors for connection buttons
CONNECT_BUTTON_XPATH = "//button/span[text()='Connect' or text()='Follow']"
SEND_WITHOUT_NOTE_XPATH = '//button/span[text()="Send without a note"]'
SEND_BUTTON_XPATH = "//button//span[@class='artdeco-button__text' and .//text()='Send']"
DISMISS_BUTTON_XPATH = "//button[@aria-label='Dismiss']"
NEXT_BUTTON_XPATH = "//button/span[text()='Next']"
GOT_IT_BUTTON_XPATH = "//button/span[text()='Got it']"

# XPath selectors for profile page
PROFILE_MORE_BUTTON_XPATH = "(//button[contains(@id, 'profile-overflow-action') and contains(@aria-label, 'More actions')])[2]"
PROFILE_CONNECT_BUTTON_XPATH = "//div[2]/div/div/ul/li[3]/div/span[text() = 'Connect']"

# XPath selectors for login page - with fallbacks for different LinkedIn login page versions
USERNAME_FIELD_XPATH = '//*[@id="username" or @id="session_key" or @name="session_key"]'
PASSWORD_FIELD_XPATH = '//*[@id="password" or @id="session_password" or @name="session_password"]'
LOGIN_BUTTON_XPATH = '//button[@data-litms-control-urn="login-submit" or @aria-label="Sign in" or @type="submit"]'
LOGIN_NAV_CHECK_SELECTORS = [
    "nav.global-nav", 
    "div.global-nav__me", 
    ".feed-identity-module",
    "#global-nav"
]

# XPath selectors for job applications
JOB_APPLY_BUTTON_XPATH = "//button/span[text()='Easy Apply']"
JOB_SUBMIT_BUTTON_XPATH = "//button/span[text()='Submit application']"
JOB_SUCCESS_MESSAGE_XPATH = "//h2[contains(text(), 'Application submitted')]"
JOB_SEARCH_KEYWORD_XPATH = "//input[contains(@id, 'jobs-search-box-keyword')]"
JOB_SEARCH_LOCATION_XPATH = "//input[contains(@id, 'jobs-search-box-location')]"
JOB_SEARCH_BUTTON_XPATH = "//button[contains(@class, 'jobs-search-box__submit')]"