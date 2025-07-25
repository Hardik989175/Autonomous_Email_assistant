# Autonomous Email Assistant

A smart desktop application that provides a conversational chat interface for users to generate and automatically send professional emails using AI and browser automation.

## Project Overview & Key Features

This project brings together cutting-edge AI and automation to create a truly helpful email assistant. Instead of filling out forms, you can interact with the agent through a natural, conversational chat interface. The agent is designed to understand your intent, ask for the absolute minimum information required, and then take over the entire process of writing and sending the email.

* **Natural Conversation Flow:** The agent doesn't use forms. It engages in a flowing conversation, asking for one piece of information at a time (like the recipient or topic) to feel like you're talking to a real assistant.
* **Intelligent AI Content Generation:** Powered by the Google Gemini API, the agent doesn't just fill in templates. It understands the intent behind your request and generates a complete, professional, and context-aware email draft from scratch. It is explicitly programmed to never use placeholders.
* **Live Visual Feedback:** The agent shows you what it's doing. When it's time to send the email, it launches a visible browser window, allowing you to watch the entire process in real-time as it logs in, composes the message, and clicks send.
* **Intelligent Hybrid Authentication:** The agent features a sophisticated, multi-account authentication system. It automatically uses saved, trusted browser sessions for known accounts for lightning-fast, zero-touch logins. For new accounts, it initiates a secure, user-assisted workflow to reliably handle any 2FA and CAPTCHA challenges(manually).
* **Step-by-Step Screenshotting:** For a complete audit trail, the agent automatically captures and saves screenshots at every critical step of the browser automation process, from the login page to the final "message sent" confirmation.

---

* [Architecture Overview](#️-architecture-overview)
* [Technology Stack & Justification](#-technology-stack--justification)
* [Setup and Running Instructions](#-setup-and-running-instructions)
* [Challenges Faced & Solutions Implemented](#-challenges-faced--solutions-implemented)

---

## Architecture Overview

The application is built on a decoupled, three-part architecture to ensure stability and responsiveness. The **User Interface (UI)** is completely separate from the **AI "brain"** and the **browser "hands,"** which prevents the application from freezing during complex operations.

### Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph "User Interface (app.py)"
        A[Start Conversation] --> B{Ask for Recipient}
        B -->|User Input| C{Ask for Name}
        C -->|User Input| D{Ask for Topic}
        D -->|User Input| E[Generate Draft]
        E --> F{Display Draft & Ask for Approval}
        F -->|User Clicks 'No'| G[Get Feedback for Changes]
        G --> E
        F -->|User Clicks 'Yes'| H[Initiate Sending]
        I[Show Success/Error] --> A
    end
    subgraph "Execution Layers (agent/)"
        E --> J(email_generator.py)
        J -->|AI Draft| F
        
        H --> K_Check{Check for Saved Profile?}
        K_Check -- No --> K_Autofill[Autofill Credentials]
        K_Autofill --> K_Manual_Pause{Wait for Human 2FA/CAPTCHA}
        K_Manual_Pause --> K_Save[Save New Session]
        K_Save --> K_Send[Compose & Send Email]
        
        K_Check -- Yes --> K_Auto[Automatic Login]
        K_Auto --> K_Send

        K_Send -->|Status| I
    end

    subgraph "External Systems & Outputs"
        J <-->|API Call| L((Google Gemini AI))
        K_Send -->|Control| M((Gmail via Browser))
        M --> N([screenshots/ folder])
    end



    style A fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style B fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style C fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style D fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style E fill:#ffffff,stroke:#5C5,stroke-width:2px
    style F fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style G fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style H fill:#ffffff,stroke:#5C5,stroke-width:2px
    style I fill:#ffffff,stroke:#4ADEDE,stroke-width:2px
    style J fill:#ffffff,stroke:#5C5,stroke-width:2px
    style K fill:#ffffff,stroke:#5C5,stroke-width:2px
    style L fill:#ffffff,stroke:#f9f,stroke-width:2px
    style M fill:#ffffff,stroke:#f9f,stroke-width:2px
    style N fill:#ffffff,stroke:#fff,stroke-width:2px,stroke-dasharray: 5 5
```

(continued in the next cell for character limit)

---

## Detailed File Explanation

### `app.py` - The Application Core & UI

- **Role**: This is the main entry point and the user-facing part of the application. It creates the modern, attractive chat window using the CustomTkinter library.
- **Conversational Flow**: It manages a precise **State Machine (self.conversation_state)** that guarantees a minimal, non-irritating conversation. It asks for the recipient, then the user's name, and finally the email topic.
- **Responsiveness**: To prevent the UI from ever freezing, all heavy operations are run in the background using Python's threading module. When the AI is thinking or the browser is running, the main UI thread remains completely responsive.
- **The Feedback Loop**: This is a critical feature managed by app.py. After a draft is generated and displayed in a dedicated panel, **the user is presented with "Yes, Send It" and "No, I need changes" buttons.** If the user clicks **"No," a pop-up dialog appears to collect feedback.** This feedback is then used to re-run the generation process, ensuring the user has final control over the content.

### `agent/email_generator.py` - The AI Brain

- **Role**: This module's sole responsibility is to generate a complete, professional, and ready-to-send email draft. It acts as the creative core of the assistant.
- **AI Model**: It interfaces with the **Google Gemini API**, specifically using the** gemini-1.5-flash-latest model.** This model was chosen for its optimal balance of speed and reasoning power, allowing for quick draft generation without sacrificing quality.
- **Intent-Based Generation**: The core of this file is the advanced prompt sent to the AI. This prompt contains a strict set of rules that command the AI to **"get the intent"** of the user's request and write a full email. It is explicitly forbidden from using placeholders or inventing fake personal details.
- **Output**: It returns a clean JSON object ({"subject": "...", "body": "..."}) that the main app.py can easily parse and display.
- 
### `agent/browser_automation.py` - The Automation Hands

- **Role**: This module contains the agent's most sophisticated logic: a multi-account, persistent authentication system designed to robustly handle real-world web security.
- **Multi-Account Persistent Context:**: For each unique sender email, the agent creates a separate, isolated browser profile folder. This crucial step prevents account session conflicts and makes the automated browser appear "trusted" to Google over time, solving the common "browser not secure" error.
- **Hybrid Authentication Flow**:
  1. **Smart Detection**: When initiated, the agent first checks if a trusted profile for the given email already exists. If so, it launches directly into the inbox for a fully automated       experience i.e. it will not require only email id and password to match after that no login/2FA/Captcha handling is required, direct mail is sent.
  2. If the email is new, the agent performs a "best-effort" autofill of the credentials on the Gmail login page. It then intelligently pauses and waits for the user to **manually complete any 2FA or CAPTCHA challenge.** 
  3. The agent actively monitors the page and, **upon detecting a successful login, automatically resumes its work.** This one-time assisted login is then saved to the **profile**, making all future runs for that account **fully automatic.**
- **Real-Time View**:  It uses the **Playwright(Browser-Use Library. It is perfecas it is built specifically for LLM-powered browser automation)** framework to launch a visible browser by setting headless=False. This provides the **"real-time see"** feature, allowing the user to watch the entire automation process live.
- **Screenshot Feature**: At every key step of the automation, a page.screenshot() command is executed. This saves a numbered image to the screenshots/ folder, creating a valuable visual log of the agent's actions.
- **Robust Element Selection**: This module solves the critical challenge of the agent getting confused on the Gmail page. By using Playwright's modern selectors like page.get_by_role("textbox", name="Enter your password"), it can reliably distinguish between similar-looking elements.

---

## Technology Stack & Justification
Each technology in this project was chosen for a specific reason to maximize performance, stability, and user experience.

- **Python**: The core programming language, chosen for its simplicity, extensive libraries, and strong support for AI and automation. It's the industry standard for this type of work.
- **CustomTkinter**:Used for the graphical user interface (GUI). It was chosen over standard Tkinter for its modern, attractive appearance and over web frameworks like Flask/Streamlit to create a stable, single-process desktop application. This was a critical decision that completely eliminated the complex NotImplementedError we encountered with web-based solutions.
- **Google Generative AI (google-generativeai)**:
  - **Role**: This is the official Python library from Google that acts as the bridge to the Gemini family of AI models. It handles authenticating with your API key and sending our carefully crafted prompts to Google's servers.
  - **Justification**: We use this library to access the gemini-1.5-flash-latest model. It uses **GEMINI_API_KEY** for composing and generating email and uses its API Key. It uses Gemini latest model. "Flash" was specifically chosen for its excellent balance of high speed and powerful reasoning. This is crucial for a responsive chat application where users expect quick replies.
- **Playwright(Browser-use Library)**: The **browser automation framework**. It was chosen over alternatives like Selenium for its modern, robust API that is better at handling dynamic, complex web applications like Gmail. Its get_by_role and get_by_placeholder selectors proved essential for reliably finding elements on the page, which was a major challenge.
- **Regular Expressions (`re`)**:
  - **Role**: This standard Python library is a powerful tool for pattern matching in text.
  - **Justification**: The Gemini AI, while instructed to return clean JSON, would sometimes add extra text or formatting. The re.search(r'\{.*\}', ...) command in email_generator.py is a bulletproof solution that finds the JSON object ({...}) within the AI's response, no matter what extra text surrounds it.
- **Dotenv**:
  - Used for securely managing the GEMINI_API_KEY, keeping sensitive credentials out of the source code.

---

## Setup and Running Instructions(I have done this in Visual Studio Code)

### Prerequisites

- Python 3.8+
- Terminal or Command Line Access

### Step 1: Clone or Download the Project

Ensure the following structure:

```
Email-assistant/
│
├── agent/
│   ├── __init__.py
│   ├── browser_automation.py
│   └── email_generator.py
├── screenshots/
│   ├── 01_login_page.png
│   ├── 02_email_entered.png
│   ├── 03_password_entered.png
│   ├── 04_inbox_loaded.png
│   ├── 05_email_composed.png
│   └── 06_email_sent.png
├── app.py
├── profile_raj5528yadav_gmail_com  # This is an example of the profile folder to be created for the given email id for the first time.
├── .env
└── requirements.txt
```

### Step 2: Set Up a Virtual Environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install customtkinter google-generativeai playwright python-dotenv
```

### Step 4: Install Playwright Browsers

```bash
playwright install
```

### Step 5: Configure Your Credentials

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

> **Use a test Gmail account** to avoid any personal security issues.

### Step 6: Run the Application

```bash
python app.py
```

A chat-based desktop window will appear and is ready to use.

---

## Challenges Faced & Solutions Implemented

### Challenge 1: UI Instability and Freezing

- **Problem**: Initial attempts using both web frameworks (Flask/Streamlit) and early desktop versions caused the application to either crash with a NotImplementedError or freeze completely during long-running tasks.
- **Solution**: We adopted a two-part solution. First, we committed to a native desktop application using CustomTkinter to eliminate the event-loop conflicts. Second, we implemented Python's threading module to run all heavy tasks in a background thread, ensuring the UI remains active and responsive at all times.

### Challenge 2: AI Generating Incomplete Content or unhelpful content

- **Problem**: The AI model would often return drafts with placeholders like [add your details here] or invent unrealistic personal information (like fake colleague names), defeating the purpose of the automation.
- **Solution**: This was solved through advanced prompt engineering. The final prompt in agent/email_generator.py gives the AI a strict set of unbreakable rules: it is forbidden from using placeholders and forbidden from inventing personal information, but it must invent plausible, non-personal details to make the email complete.

### Challenge 3: Unreliable Browser Automation

- **Problem**: The automation was highly unreliable. The script would frequently fail because it couldn't find the correct element to interact with. Specific issues included:
  - **Password Field**: The script would find two password fields (one hidden, one visible) and crash due to ambiguity.
  - **"To" and "Send" Buttons**: The script would get confused between the main "Send" button and the dropdown arrow for "schedule send."
- **Solution**: We abandoned simple selectors and adopted Playwright's modern "accessible role" locators. Instead of looking for a generic input[type="password"], the final code looks for page.get_by_role("textbox", name="Enter your password"). This is far more specific and reliable and stabilized the automation completely.
  
### Challenge 4: Handling Google's Advanced Security & Login(Captcha/2FA)

- **Problem**: Simple automated logins were consistently blocked by Google's "browser not secure" error or got stuck at 2FA/CAPTCHA prompts, especially when switching accounts.
- **Solution**: Google being a billion dollar company invested highly in security and we can not handle **2FA/Captcha automatically, also it violates platform rules.** So, smart manual intervention is required. First, the agent launches the dedicated browser for the account you provided. To make the process as smooth as possible, it then performs a *best-effort attempt to automatically fill in the email and password fields* for you. This is the initial 'automated' part of our flow, designed to assist and speed up the process. At this point, the agent's logic recognizes that it has reached a critical security checkpoint: a **CAPTCHA or a 2-Factor Authentication prompt**. Our agent does not attempt to programmatically guess or bypass these security measures. **Attempting to do so is fundamentally insecure, unreliable, and violates the terms of service of the platform.**
Instead, the agent intelligently pauses its own execution and **securely hands control over to you, the human user**. Our terminal will clearly state that it is now waiting for you to complete the login. This is the **explicit manual intervention** part of our flow. It ensures that your sensitive 2FA codes and security gestures are handled in the most secure way possible by you. The agent patiently and actively **waits in the background, watching the browser for a successful login**. The moment it detects that the Gmail inbox has loaded, it knows you've succeeded.
It then automatically resumes its task, seamlessly taking back control to compose and send the email. In that same instant, the successful login session is **permanently saved** to that user's unique profile folder. This entire **manual handshake** is a one-time event for this account on this machine. The next time you need to send an email using that same email address, the agent will find the existing, trusted profile folder. It will launch the browser and go **directly to the inbox**, **completely bypassing the login, CAPTCHA, and 2FA steps.**
**So, to be perfectly explicit: our agent uses a partially automated** flow for the **very first login on any new account**, which then enables a **fully automated** flow for all subsequent uses. This hybrid approach provides the best possible balance of security, reliability, and long-term convenience."


