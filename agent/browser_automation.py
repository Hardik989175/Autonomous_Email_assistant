# agent/browser_automation.py
# This file contains the core browser automation logic.
# It uses Playwright to launch a browser, log in to Gmail, and send an email.

# Core Libraries 
# os: Used to interact with the operating system, specifically to create the 'screenshots' directory.
# playwright.sync_api: The main library for browser automation. We use the synchronous API for simplicity in this script.

import os
import re # We'll use the 're' library to create safe folder names from email addresses.
from playwright.sync_api import sync_playwright, Playwright, TimeoutError as PlaywrightTimeoutError
import time

def send_email_with_browser(playwright: Playwright, recipient: str, subject: str, body: str, sender_email: str, sender_password: str):
    """
    The definitive browser automation function. It combines all our best ideas:
    1. A unique, persistent browser profile for EACH sender email, so sessions never conflict.
    2. A trusted browser that doesn't give error.
    3. Automatic filling of credentials for the very first login on a new account: email and password.
    4. Automatic detection of a successful login after the user handles 2FA/CAPTCHA(manual intervention).
    5. Detailed step-by-step screenshots for clear debugging.
    """
    
    # Let's create a unique and safe folder name from the user's email address.
    # This is the key to managing multiple accounts without them interfering with each other.
    # For example, 'user.name@example.com' becomes 'profile_user_name_example_com'.
    # After that it will be accesed for further email automations
    
    safe_email_name = re.sub(r'[^a-zA-Z0-9]', '_', sender_email)
    USER_PROFILE_DIR = f"./profile_{safe_email_name}"
    
    # We'll make sure our screenshots folder is ready to go.
    os.makedirs("screenshots", exist_ok=True)

    # We launch the browser using our special persistent profile directory.
    # This is what makes Google trust the browser and saves our login session like a real browser would.
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=USER_PROFILE_DIR,
        headless=False,
        slow_mo=50
    )
    
    # The browser might already have a page open from a previous run. We'll use it if it's there.
    page = context.pages[0] if context.pages else context.new_page()
    
    try:
        # Gmail page.
        print("Navigating to Gmail...")
        page.goto("https://mail.google.com/", wait_until='load', timeout=60000)
        page.screenshot(path="screenshots/01_login_page.png")

        # Now, let's check if we're already logged in for this account.
        
        is_logged_in = False
        try:
            # We'll know we're in the inbox if we can find the "Compose" button.
            
            page.wait_for_selector('div[gh="cm"]', timeout=7000)  # Timeout is increased for slow connections.
            is_logged_in = True
            print(f"Active session found for {sender_email}. Proceeding automatically.")
        except PlaywrightTimeoutError:
            # If we can't find it, no worries, it just means we need to log in.
            is_logged_in = False

        # This entire block only runs if it's the FIRST time we're using this email address, otherwise if it is already existing no credentials needed, direct login.
        if not is_logged_in:
            print(f"No active session for {sender_email}. Starting one-time login process...")
            
            # The script will do its best to fill in the login details.
            try:
                print("Filling the email...")
                page.get_by_role("textbox", name="Email or phone").fill(sender_email)
                page.get_by_role("button", name="Next").click()
                page.screenshot(path="screenshots/02_email_entered.png")
                
                print("Filling the password...")
                password_input = page.get_by_role("textbox", name="Enter your password")
                password_input.wait_for(timeout=5000)
                password_input.fill(sender_password)
                page.screenshot(path="screenshots/03_password_entered.png")
                
                page.get_by_role("button", name="Next").click()
                print("Autofill successful. Now waiting for you to complete the login(Captch/2FA)...")
            except Exception:
                # If autofill fails for any reason, it's not a problem. You can just log in normally.
                print("Could not complete autofill. Please proceed with login manually.")

            # AUTOMATIC DETECTION
            # We will wait for the inbox to appear.
            print("\n" + "="*60)
            print("WAITING FOR MANUAL LOGIN...")
            print("Please complete the login in the browser (2FA, CAPTCHA, etc.).")
            print("The script will automatically detect when you're done and continue...")
            
            # This command will wait for the "Compose" button to appear.
            # Once it appears, the script knows you're in and will proceed.
            
            compose_button = page.get_by_role("button", name="Compose")
            compose_button.wait_for(timeout=180000) # increased timeout
            print("Login successful! Inbox detected automatically.")
            print("="*60 + "\n")

        # Whether we logged in automatically or with manual help, we are now in the inbox.
        # The persistent context has saved this successful login for all future runs.
        
        print("Login confirmed. Taking screenshot of inbox...")
        page.screenshot(path="screenshots/04_inbox_loaded.png")

        # Now we proceed with sending the email.
        # Email Composition Process

        print("Composing email...")
        page.get_by_role("button", name="Compose").click()
        
        to_field = page.get_by_role("combobox", name="Recipients")
        to_field.wait_for(timeout=15000)
        
        to_field.fill(recipient)
        page.get_by_placeholder("Subject").fill(subject)  # For subject.
        page.get_by_role("textbox", name="Message Body").fill(body)
        page.screenshot(path="screenshots/05_email_composed.png")

        print("Sending email...")
        page.get_by_role("button", name="Send ‪(Ctrl-Enter)‬").click()
        page.get_by_text("Message sent").wait_for(timeout=15000)
        page.screenshot(path="screenshots/06_email_sent.png")
        
        print("Browser automation finished successfully.")

    except Exception as e:
       # If any error occurs, take a final screenshot for debugging.
       
        print(f"An error occurred during the browser automation: {e}")
        page.screenshot(path="screenshots/error.png")
        
        # Re-raise the exception so the UI can catch it and display a detailed error message.
        
        raise e
    finally:
        # This makes sure the browser always closes down neatly.
        print("Closing browser context.")
        time.sleep(2) # A small pause to see the final result.
        context.close()