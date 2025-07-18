# agent/email_generator.py
# This file serves as the "creative brain" of the AI assistant. It now has two functions:
# 1. analyze_prompt_for_followup: To intelligently decide if a critical detail is missing.
# 2. generate_email_content: To write the complete, professional email draft.

import os
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_prompt_for_followup(prompt: str) -> str | None:
    """
    Analyzes the user's prompt with expert human-like judgment to see if a
    critical detail is missing, returning a follow-up question or None.

    Args:
        prompt (str): The user's raw request for the email.

    Returns:
        str | None: A single, non-irritating follow-up question if needed, otherwise None.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # This prompt trains the AI to act as a minimalist assistant.
    analysis_prompt = f"""
    You are an AI assistant's brain. Your job is to analyze a user's request for an email and decide if a single, absolutely critical piece of information is missing.

    **Your Core Principles:**
    1.  **Be Minimalist:** Only ask a question if the email would be fundamentally incomplete or nonsensical without the answer.
    2.  **Infer Gracefully:** If a detail isn't absolutely critical (like the specific name of an interviewer for a thank you note), do not ask. Write a great, general email instead.
    3.  **Do NOT Ask for Attachments:** Never ask for resumes, portfolios, or files.

    **Analyze the user's request:** "{prompt}"

    **Task:**
    - If a follow-up for a critical missing detail (like a date for a leave request, name, anything that truly needs as according to user input, but not any documents.) is essential, provide the single, short question.
    - Otherwise, respond with the exact text `NO_FOLLOWUP_NEEDED`.
    - If something incomplete given by user and that information needs to be put into mail necessarily for the receptient to understand, then ask it as a follow up question, but if it is very necessary, something actually missing.

    **Examples of Your Judgment:**
    - User Request: "sick leave email to my manager" -> Your Response: For what dates will you be on leave?
    - User Request: "sick leave for tomorrow and the day after" -> Your Response: NO_FOLLOWUP_NEEDED
    - User Request: "thank you note to the hiring team" -> Your Response: NO_FOLLOWUP_NEEDED
    - User Request: "Write something for some student let's say" -> Your Response: Name and Student_ID of the student?
    """
    try:
        print("Analyzing prompt for follow-up...")
        response = model.generate_content(analysis_prompt)
        result_text = response.text.strip()

        if result_text == "NO_FOLLOWUP_NEEDED":
            print("Analysis complete. No follow-up needed.")
            return None
        else:
            print(f"Analysis complete. Follow-up needed: {result_text}")
            return result_text  # This is the follow-up question
    except Exception as e:
        print(f"ERROR during follow-up analysis: {e}")
        return None # If analysis fails, proceed without a follow-up

def generate_email_content(user_name: str, prompt: str) -> dict | None:
    """
    Generates a 100% complete, high-quality email draft using the (now complete) prompt.

    Args:
        user_name (str): The name of the user for the signature.
        prompt (str): The user's request, now including any follow-up answers.

    Returns:
        dict | None: A dictionary with the email 'subject' and 'body', or None on failure.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')  # gemini model used
    
    full_prompt = f"""
    You are an expert AI assistant. Your function is to write a perfect, 100% ready-to-send email based on a user's request.

    **YOUR #1 UNBREAKABLE RULE: YOU ARE FORBIDDEN FROM USING BRACKETS `[]` OR PARENTHESES `()` TO SUGGEST USER INPUT.**
    Your output must be a final product. If a minor detail is missing, you MUST invent a plausible, professional-sounding detail.

    **CRITICAL RULE ON PERSONAL DETAILS:** You are STRICTLY FORBIDDEN from inventing personal names or contact information. Instead, you must use a general phrase like "my team is briefed" or "I am available to connect."

    **YOUR TASK:**
    - User's Name (for signature): "{user_name}"
    - User's Request (now including any necessary details): "{prompt}"
    - Now, write the complete email. The output format MUST be ONLY a valid JSON string:
    {{"subject": "A creative and professional subject line", "body": "The full, well-written email body."}}
    """
    
    try:
        print("Generating final draft...")
        response = model.generate_content(full_prompt)
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON object found in the AI's response.")
            
        json_str = json_match.group(0)
        draft = json.loads(json_str)
        
        if not draft.get("subject") or not draft.get("body"):
            raise ValueError("Generated JSON is missing 'subject' or 'body'.")
            
        print("Draft generation successful.")
        return draft
        
    except Exception as e:
        print(f"FATAL ERROR during email generation: {e}")
        return None
