#!/usr/bin/env python3
"""
Command-line interface for the LinkedIn Automation package.
"""
import argparse
import sys
import atexit

from linkedin_automation.core.browser import Browser
from linkedin_automation.core.auth import LinkedInAuth
from linkedin_automation.features.connections import ConnectionManager
from linkedin_automation.features.jobs import JobApplicationManager
from linkedin_automation.config.settings import (
    CONFIG, LINKEDIN_USERNAME, LINKEDIN_PASSWORD,
    MAX_TABS, MAX_APPLICATIONS
)
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='LinkedIn Automation Tool')
    
    # Common arguments
    parser.add_argument('--username', type=str, help='LinkedIn username (overrides config.toml)')
    parser.add_argument('--password', type=str, help='LinkedIn password (overrides config.toml)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (overrides config.toml)')
    
    # Create subparsers for different features
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Connections command
    connections_parser = subparsers.add_parser('connections', help='Send connection requests')
    connections_parser.add_argument('--url', type=str, help='LinkedIn search URL (overrides config.toml)')
    connections_parser.add_argument('--max-tabs', type=int, help='Maximum number of side tabs (overrides config.toml)')
    connections_parser.add_argument('--max-connections', type=int, help='Maximum number of connections to send (overrides config.toml, use 0 for unlimited)')
    
    # Jobs command (if enabled)
    jobs_parser = subparsers.add_parser('jobs', help='Apply for jobs')
    jobs_parser.add_argument('--url', type=str, help='LinkedIn job search URL (overrides config.toml)')
    jobs_parser.add_argument('--keywords', type=str, help='Job search keywords')
    jobs_parser.add_argument('--location', type=str, help='Job location')
    jobs_parser.add_argument('--max-applications', type=int, help='Maximum number of applications (overrides config.toml, use 0 for unlimited)')
    
    return parser.parse_args()


def cleanup(browser):
    """Close browser and perform cleanup when exiting."""
    logger.info("Performing cleanup...")
    if browser:
        browser.cleanup()


def prompt_for_input(args):
    """
    Prompt user for any missing required inputs.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        dict: Updated arguments with user input
    """
    # Create a copy of args as a dictionary
    args_dict = vars(args).copy()
    
    # Command prompt if not provided
    if not args_dict.get('command'):
        print("1. connections - Send connection requests")
        print("2. jobs - Apply for jobs")

        choice = input("Select a command:")
        if choice == '1':
            args_dict['command'] = 'connections'
        elif choice == '2':
            args_dict['command'] = 'jobs'
        else:
            args_dict['command'] = None
    
    # Common arguments - use config file values if not provided via CLI
    if not args_dict.get('username') and not LINKEDIN_USERNAME:
        args_dict['username'] = input("Enter your LinkedIn username/email: ")
    else:
        args_dict['username'] = args_dict.get('username') or LINKEDIN_USERNAME
    
    if not args_dict.get('password') and not LINKEDIN_PASSWORD:
        args_dict['password'] = input("Enter your LinkedIn password: ")
    else:
        args_dict['password'] = args_dict.get('password') or LINKEDIN_PASSWORD
    
    # Command-specific arguments
    if args_dict['command'] == 'connections':
        # Use config value if not provided in CLI
        config_url = CONFIG["connection"]["search_url"]
        
        if not args_dict.get('url') and not config_url:
            args_dict['url'] = input("Enter LinkedIn search URL: ")
        else:
            args_dict['url'] = args_dict.get('url') or config_url
        
        # Max tabs - use config value if not provided in CLI
        if not args_dict.get('max_tabs'):
            args_dict['max_tabs'] = MAX_TABS
            
        # Max connections - use config value if not provided in CLI
        if not args_dict.get('max_connections'):
            # Ask if user wants unlimited connections
            unlimited = input("Do you want to send unlimited connection requests? (y/n, default: n): ")
            if unlimited.lower() == 'y':
                args_dict['max_connections'] = 0  # 0 means unlimited
            else:
                args_dict['max_connections'] = CONFIG["connection"]["max_connections_per_day"]
    
    elif args_dict['command'] == 'jobs':
        config_url = CONFIG["job_application"]["search_url"]
        config_keywords = CONFIG["job_application"]["keywords"]
        config_location = CONFIG["job_application"]["location"]
        
        if not args_dict.get('url') and not config_url and not (args_dict.get('keywords') or args_dict.get('location') or config_keywords or config_location):
            url_choice = input("Do you have a LinkedIn job search URL? (y/n): ")
            if url_choice.lower() == 'y':
                args_dict['url'] = input("Enter LinkedIn job search URL: ")
            else:
                args_dict['keywords'] = input("Enter job search keywords: ")
                args_dict['location'] = input("Enter job location: ")
        else:
            args_dict['url'] = args_dict.get('url') or config_url
            args_dict['keywords'] = args_dict.get('keywords') or config_keywords
            args_dict['location'] = args_dict.get('location') or config_location
        
        # Max applications - use config value if not provided in CLI
        if not args_dict.get('max_applications'):
            # Ask if user wants unlimited applications
            unlimited = input("Do you want to submit unlimited job applications? (y/n, default: n): ")
            if unlimited.lower() == 'y':
                args_dict['max_applications'] = 0  # 0 means unlimited
            else:
                args_dict['max_applications'] = MAX_APPLICATIONS

    return args_dict


def main():
    """Main CLI entry point."""
    args = parse_arguments()
    browser = None
    
    # If command is missing or required args are missing, prompt for input
    if not args.command or (args.command == 'connections' and not (args.url or CONFIG["connection"]["search_url"])):
        args_dict = prompt_for_input(args)
    else:
        args_dict = vars(args)
    
    try:
        # Initialize browser - use CLI args first, then config
        headless = args_dict.get('headless') if args_dict.get('headless') is not None else CONFIG["general"]["headless"]
        browser = Browser(headless=headless)
        
        # Register cleanup function to run at exit
        atexit.register(cleanup, browser)
        
        # Initialize authentication
        auth = LinkedInAuth(browser)
        
        # Login to LinkedIn
        login_success = auth.login(
            args_dict.get('username'), 
            args_dict.get('password')
        )
        
        if not login_success:
            logger.error("Login failed. Exiting.")
            sys.exit(1)
        
        # Execute the requested command
        if args_dict['command'] == 'connections':
            # Get URL from CLI args or config
            url = args_dict['url'] 
            
            # Get max_tabs from CLI args or config
            max_tabs = args_dict.get('max_tabs') or MAX_TABS
            
            # Get max_connections from CLI args or config (0 means unlimited)
            max_connections = args_dict.get('max_connections')
            if max_connections is None:
                max_connections = CONFIG["connection"]["max_connections_per_day"]
            
            # Run connection request feature
            connection_manager = ConnectionManager(browser)
            stats = connection_manager.run_connection_campaign(url, max_tabs, max_connections)
            
            print(f"\nConnection campaign completed!")
            print(f"Successfully sent: {stats['successful_connections']} connection requests")
            
            if stats['max_connections'] == 0:
                print("No maximum limit was applied")
            else:
                print(f"Maximum allowed: {stats['max_connections']} connection requests")
            
        elif args_dict['command'] == 'jobs':
            # Get values from CLI args or config
            url = args_dict.get('url')
            keywords = args_dict.get('keywords')
            location = args_dict.get('location')
            
            # Get max_applications from CLI args or config (0 means unlimited)
            max_applications = args_dict.get('max_applications')
            if max_applications is None:
                max_applications = MAX_APPLICATIONS
            
            # Run job application feature
            job_manager = JobApplicationManager(browser)
            stats = job_manager.run_job_campaign(
                url, keywords, location, max_applications
            )
            
            print(f"\nJob application campaign completed!")
            print(f"Applications submitted: {stats['successful_applications']}")
            print(f"Jobs viewed: {stats['viewed_jobs']}")
            
            if stats['max_applications'] == 0:
                print("No maximum limit was applied")
            else:
                print(f"Maximum allowed: {stats['max_applications']} applications")
            
        else:
            logger.error("Invalid command or feature not enabled")
            sys.exit(1)
            
        print("\nOperation completed successfully!")
        input("Press Enter to exit...")
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nAn error occurred: {e}")
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()