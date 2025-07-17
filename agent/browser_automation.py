# agent/browser_automation.py
# This file contains the core browser automation logic.
# It uses Playwright to launch a browser, log in to Gmail, and send an email.

# Core Libraries 
# os: Used to interact with the operating system, specifically to create the 'screenshots' directory.
# playwright.sync_api: The main library for browser automation. We use the synchronous API for simplicity in this script.
# dotenv: A library to load environment variables from a .env file, which is a best practice for managing sensitive data like passwords.
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This command finds the .env file in your project and loads the variables
# (like GMAIL_ADDRESS and GMAIL_PASSWORD) into the environment.
load_dotenv()

# Main Function
def send_email_with_playwright(recipient: str, subject: str, body: str):
    """
    The definitive browser automation function. It logs into Gmail, sends an email,
    and captures screenshots at each step. This version includes robust error handling.

    Args:
        recipient (str): The email address of the person receiving the email.
        subject (str): The subject line of the email.
        body (str): The main content of the email.
    """
    # Retrieve credentials from the environment variables. This keeps them secure.
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

    # Ensure the screenshots directory exists before trying to save files into it.
    # The 'exist_ok=True' argument prevents an error if the folder already exists.
    os.makedirs("screenshots", exist_ok=True)
    
    # The 'with' statement ensures that Playwright resources are properly managed and closed.
    with sync_playwright() as p:
        # We launch a visible browser (headless=False) so the user can see the automation in real-time.
        # 'slow_mo' adds a small delay between actions, making the automation more stable.
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        # The 'try...finally' block ensures that the browser is always closed,
        # even if an error occurs during the automation process.
        try:
            print("▶️ Browser automation process started...")
            # Navigate to the Gmail login page.
            page.goto("https://mail.google.com/")
            page.screenshot(path="screenshots/01_login_page.png")

            #Login Process
            print("   - Filling email...")
            page.get_by_role("textbox", name="Email or phone").fill(GMAIL_ADDRESS)
            page.get_by_role("button", name="Next").click()
            page.screenshot(path="screenshots/02_email_entered.png")
            
            print("   - Filling password...")
            password_input = page.get_by_role("textbox", name="Enter your password")
            password_input.wait_for(timeout=15000) 
            password_input.fill(GMAIL_PASSWORD)
            page.screenshot(path="screenshots/03_password_entered.png")
            
            page.get_by_role("button", name="Next").click()

            print("   - Waiting for inbox to load...")
            compose_button = page.get_by_role("button", name="Compose")
            # Increased timeout for slower connections
            compose_button.wait_for(timeout=90000) 
            page.screenshot(path="screenshots/04_inbox_loaded.png")
            
            # Email Composition Process
            print("   - Composing email...")
            compose_button.click()

            to_field = page.get_by_role("combobox", name="Recipients")
            to_field.wait_for(timeout=15000)
            
            to_field.fill(recipient)
            page.get_by_placeholder("Subject").fill(subject)
            page.get_by_role("textbox", name="Message Body").fill(body)
            page.screenshot(path="screenshots/05_email_composed.png")

            print("   - Sending email...")
            page.get_by_role("button", name="Send ‪(Ctrl-Enter)‬").click()
            page.get_by_text("Message sent").wait_for(timeout=15000)
            page.screenshot(path="screenshots/06_email_sent.png")
            
            print("Browser automation finished successfully.")
            
        except Exception as e:
            # If any error occurs, take a final screenshot for debugging.
            print(f"An error occurred in the browser automation: {e}")
            page.screenshot(path="screenshots/error.png")
            # Re-raise the exception so the UI can catch it and display a detailed error message.
            raise e
        finally:
            # This 'finally' block is crucial. It guarantees that the browser
            # will be closed, preventing leftover processes.
            print("Closing browser.")
            browser.close()
