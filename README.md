
# Autonomous Email Assistant

A smart desktop application that provides a conversational chat interface for users to generate and automatically send professional emails using AI and browser automation.

---

## Table of Contents
- Architecture Overview
- Technology Stack & Justification
- Setup and Running Instructions
- Challenges Faced & Solutions Implemented

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

    subgraph "Agent Logic (agent/)"
        E --> J(email_generator.py)
        J -->|AI Draft| F
        H --> K(browser_automation.py)
        K -->|Status| I
    end

    subgraph "External Systems & Outputs"
        J <-->|API Call| L((Google Gemini AI))
        K -->|Control| M((Gmail via Browser))
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
- **Conversational Flow**: Manages a precise State Machine (`self.conversation_state`) that ensures a minimal, non-irritating conversation. It asks for the recipient, then the user's name, and finally the email topic. No other questions are asked unless changes are requested.
- **Responsiveness**: All heavy operations are run in the background using Python's threading module to keep the UI responsive.
- **The Feedback Loop**: After generating a draft, users can approve or request changes. Clicking "No" opens a pop-up for feedback which is used to regenerate the email.

### `agent/email_generator.py` - The AI Brain

- **Role**: Generates a complete, professional, ready-to-send email draft.
- **AI Model**: Uses Google Gemini's `gemini-1.5-flash-latest` model via the official API.
- **Intent-Based Generation**: Prompts enforce strict rules to avoid placeholders and fake personal info, but generate plausible details.
- **Output**: Returns clean JSON like `{"subject": "...", "body": "..."}`.

### `agent/browser_automation.py` - The Automation Hands

- **Role**: Sends the final email.
- **Real-Time View**: Uses Playwright with `headless=False` for live browser view.
- **Screenshot Feature**: Takes screenshots at every step saved in `screenshots/` for logs.
- **Robust Element Selection**: Uses modern Playwright selectors like `get_by_role` for accurate targeting.
- **Captcha Handling**: Manages hidden fields and Captcha challenges with a visible browser and App Passwords.

---

## Technology Stack & Justification

- **Python**: Chosen for simplicity, rapid development, and integration.
- **CustomTkinter**: Modern GUI without async conflicts faced in web frameworks.
- **Google Generative AI (google-generativeai)**:
  - Official library to interface with Gemini.
  - **Model Used**: `gemini-1.5-flash-latest`.
- **Playwright**:
  - Chosen over Selenium for dynamic web handling.
  - Uses role-based selectors for reliability.
- **Regular Expressions (`re`)**:
  - Bulletproof method to extract JSON from AI output.
- **Dotenv**:
  - Keeps sensitive data like `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_PASSWORD` in `.env`.

---

## Setup and Running Instructions

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
GMAIL_ADDRESS="your-test-email@gmail.com"
GMAIL_PASSWORD="your-test-email-password"
```

> ✅ **Use a test Gmail account** to avoid any personal security issues.

### Step 6: Run the Application

```bash
python app.py
```

A chat-based desktop window will appear and is ready to use.

---

## Challenges Faced & Solutions Implemented

### Challenge 1: UI Instability and Freezing

- **Problem**: UI would crash or freeze during heavy operations.
- **Solution**:
  - Switched to CustomTkinter desktop app.
  - Used Python `threading` to offload heavy tasks.

### Challenge 2: AI Generating Incomplete Content

- **Problem**: AI returned drafts with `[add your details here]` or fake info.
- **Solution**: Used strict prompt engineering to forbid placeholders and personal info, while allowing plausible generic details.

### Challenge 3: Unreliable Browser Automation

- **Problem**:
  - Multiple password fields confused the agent.
  - Incorrectly selected "Send" or "To" buttons.
- **Solution**: Switched to Playwright's `get_by_role` selectors for reliable element selection.

### Challenge 4: Handling Google Security

- **Problem**: Google triggered Captcha and blocked automation.
- **Solution**:
  - Used `headless=False` to manually bypass Captcha.
  - Recommended using **Google App Passwords** for automation.

