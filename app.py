# app.py
# This is the main application file for the Autonomous Email Assistant.
# It creates a modern, conversational desktop user interface (UI) where users can
# interact with an AI to draft and send emails automatically.

# Core Libraries 
# customtkinter: A modern Python UI library used to build the beautiful, themed chat window.
import customtkinter as ctk
# threading: Essential for running time-consuming tasks (like AI generation and browser automation) in the background, which ensures the user interface never freezes or lags.

import threading
# tkinter (messagebox, simpledialog): The standard Python library for creating simple pop-up dialog boxes for errors, successes, and user feedback.
from tkinter import messagebox, simpledialog
# playwright.sync_api: The main library for browser automation. We need to import this here to pass the playwright instance to our browser function.

from playwright.sync_api import sync_playwright
# These imports connect our UI to the "brain" and "hands" of our assistant.
from agent.email_generator import analyze_prompt_for_followup, generate_email_content
from agent.browser_automation import send_email_with_browser

# We structure the entire application inside a class. This is a best practice for GUI apps
# as it keeps all the UI elements and their related functions organized and self-contained.
class ChatApp(ctk.CTk):
    # The __init__ method is the constructor for our app. It runs once when the app starts.
    # Everything to set up the initial state and appearance of the app goes here.
    def __init__(self):
        # This line calls the constructor of the parent class (CTk), which is necessary
        # to properly initialize the window.
        super().__init__()

        # This dictionary will hold all the information we gather during the conversation, like the recipient's email, the user's name, and the core email prompt.
        self.conversation_data = {}
        # This variable will store the AI-generated email draft (a dictionary with 'subject' and 'body').
        self.generated_email = None
        # It's a "state machine" that tracks what question the bot should ask next. This makes the conversation flow logical and easy to manage.
        self.conversation_state = "asking_recipient"

        # Window a title and set its initial size.
        self.title("Autonomous Email Assistant")
        self.geometry("800x850")
        # We'll use a sleek dark theme with a green accent color for a modern look.
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # Main UI Layout
        # We use a grid layout to structure the window into three main parts.
        # The 'weight' tells the grid how to distribute extra space if the window is resized.
        self.grid_rowconfigure(0, weight=4) # Chat history area (takes up the most space).
        self.grid_rowconfigure(1, weight=3) # Action panel for the draft.
        self.grid_rowconfigure(2, weight=0) # Input bar at the bottom (fixed size).
        self.grid_columnconfigure(0, weight=1) # A single column that expands horizontally.

        # Chat History Display
        # This is the main textbox where the conversation appears.
        self.chat_history = ctk.CTkTextbox(self, state="disabled", wrap="word", font=("Segoe UI", 14), border_spacing=10)
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        # We define "tags" to style the bot's and user's messages differently, giving it that classic chat application look.
        self.chat_history.tag_config("bot", foreground="#4ADEDE", justify="left")
        self.chat_history.tag_config("user", foreground="#FFFFFF", justify="right")

        # The Action Panel (for displaying the draft)
        # This dedicated panel is where the user will review the AI-generated draft.
        # It's created once at the start but kept hidden until a draft is ready.
        self.action_panel = ctk.CTkFrame(self, fg_color="#2A2D2E", corner_radius=10)
        self.action_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.action_panel.grid_remove() # We start with the panel hidden.

        # We configure the grid inside the action panel itself.
        self.action_panel.grid_columnconfigure(0, weight=1)
        self.action_panel.grid_rowconfigure(1, weight=1) # The body text should expand.

        # The widgets inside the action panel.
        self.subject_label = ctk.CTkLabel(self.action_panel, text="Subject:", font=ctk.CTkFont(weight="bold"))
        self.subject_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))
        
        self.body_text = ctk.CTkTextbox(self.action_panel, wrap="word", font=("Segoe UI", 12), state="disabled")
        self.body_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        # A frame to hold the "Yes" and "No" buttons side-by-side.
        self.button_frame = ctk.CTkFrame(self.action_panel, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        self.button_frame.grid_columnconfigure((0, 1), weight=1) # Make both buttons expand equally.

        # The final decision buttons for the user.
        self.yes_button = ctk.CTkButton(self.button_frame, text="Yes, Send It", command=self.handle_sending)
        self.no_button = ctk.CTkButton(self.button_frame, text=" No, I need changes", fg_color="#D32F2F", hover_color="#B71C1C", command=self.handle_rejection)
        self.yes_button.grid(row=0, column=0, padx=(0, 5), ipady=5, sticky="ew")
        self.no_button.grid(row=0, column=1, padx=(5, 0), ipady=5, sticky="ew")
        
        # User Input Frame
        # This frame at the bottom holds the text entry box and the send button.
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your response here...", height=40, font=("Segoe UI", 12))
        self.input_entry.grid(row=0, column=0, sticky="ew")
        
        # This is a great usability feature: it allows the user to press the Enter key to send their message.
        self.input_entry.bind("<Return>", self.handle_user_input)
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80, height=40, font=ctk.CTkFont(weight="bold"), command=self.handle_user_input)
        self.send_button.grid(row=0, column=1, padx=(10, 0))
        
        # After setting up all the UI elements, we kick off the conversation.
        self.start_conversation()

    # UI Helper Functions
    def add_message(self, speaker, text):
        """A helper function to add a new message bubble to the chat history."""
        # We have to temporarily enable the textbox to add text, then disable it again
        # to prevent the user from typing directly into the history.
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"{text}\n\n", speaker)
        self.chat_history.configure(state="disabled")
        # This ensures the chat window always scrolls down to show the latest message.
        self.chat_history.see("end")

    # Core Application Logic
    def start_conversation(self):
        """Initiates the conversation by asking the first question."""
        self.add_message("bot", "Hello! I'm your Autonomous Email Assistant.\nWho should this email be sent to (recipient email id)?")

    def handle_user_input(self, event=None):
        """This function is the central controller for the conversation. It runs every time the user sends a message."""
        user_text = self.input_entry.get().strip()
        # We'll ignore if any empty messages.
        if not user_text: return
        
        # Add the user's message to the history and clear the input box.
        self.add_message("user", user_text)
        self.input_entry.delete(0, "end")
        # We immediately disable the input field so the user can't send another message while the bot is thinking.
        self.toggle_input(False)

        # This is our State Machine in action. It checks the current state of the conversation and decides what to do with the user's input.
        
        if self.conversation_state == "asking_recipient":
            self.conversation_data["recipient"] = user_text
            self.conversation_state = "asking_name" # Move to the next state.
            self.add_message("bot", "Got it. What is your name for the signature?")
            self.toggle_input(True) # Re-enable input for the user's next answer.
        elif self.conversation_state == "asking_name":
            self.conversation_data["user_name"] = user_text
            self.conversation_state = "asking_prompt"
            self.add_message("bot", "Perfect! Now, what should the email be about?")
            self.toggle_input(True)
        elif self.conversation_state == "asking_prompt":
            self.conversation_data["prompt"] = user_text
            self.conversation_state = "analyzing"
            self.add_message("bot", "Analyzing your request...")
            # Here, we start the AI analysis in a background thread to keep the UI responsive.
            threading.Thread(target=self.analyze_logic, daemon=True).start()
        elif self.conversation_state == "asking_followup":
            # The user has provided the answer to the AI's follow-up question.
            # We'll append it to the original prompt.
            self.conversation_data["prompt"] += f". Additional details: {user_text}"
            self.conversation_state = "generating"
            self.add_message("bot", "Thank you. I'm writing the draft now...")
            threading.Thread(target=self.generate_logic, daemon=True).start()

    def analyze_logic(self):
        """Calls the AI to analyze if a follow-up question is needed. Runs in a background thread."""
        follow_up_question = analyze_prompt_for_followup(self.conversation_data["prompt"])
        # This is the safe way to send the result back to the main UI thread.
        self.after(0, self.update_ui_after_analysis, follow_up_question)

    def update_ui_after_analysis(self, follow_up_question):
        """Decides whether to ask a follow-up or generate the draft. Runs on the main UI thread."""
        if follow_up_question:
            # If the AI returned a question, we ask it.
            self.conversation_state = "asking_followup"
            self.add_message("bot", f"One quick question: {follow_up_question}")
            self.toggle_input(True)
        else:
            # If no question is needed, we proceed directly to generating the email.
            self.conversation_state = "generating"
            self.add_message("bot", "Understood. I'm writing the draft now...")
            threading.Thread(target=self.generate_logic, daemon=True).start()

    def generate_logic(self):
        """Calls the AI to generate the email content. Runs in a background thread."""
        self.generated_email = generate_email_content(self.conversation_data["user_name"], self.conversation_data["prompt"])
        self.after(0, self.update_ui_after_generation)

    def update_ui_after_generation(self):
        """Updates the UI after the AI has finished generating. Runs on the main UI thread."""
        self.toggle_input(False) # Keep input disabled while the user reviews the draft.
        if self.generated_email:
            self.add_message("bot", "Here is the draft I've prepared for your review:")
            
            # We populate the dedicated action panel with the draft's subject and body.
            
            self.subject_label.configure(text=f"Subject: {self.generated_email['subject']}")
            self.body_text.configure(state="normal")
            self.body_text.delete("1.0", "end")
            self.body_text.insert("1.0", self.generated_email["body"])
            self.body_text.configure(state="disabled")
            # The panel visible to the user.
            self.action_panel.grid()
            
            self.conversation_state = "awaiting_decision"
        else:
            # If something went wrong during generation, we inform the user and reset.
            self.add_message("bot", "I'm sorry, I couldn't generate an email. Please check the terminal for error details.")
            self.add_message("bot", "Let's try again. What should the email be about?")
            self.conversation_state = "asking_prompt"
            self.toggle_input(True)

    def handle_rejection(self):
        """Handles the 'No, I need changes' button click."""
        self.action_panel.grid_remove() # Hide the draft panel.
        # We use a simple pop-up dialog to ask for feedback.
         
        feedback = simpledialog.askstring("Provide Feedback", "Of course. Please tell me what you'd like to change.", parent=self)
        if feedback:
            # We update the original prompt with the user's feedback and re-run the generation process.
            self.conversation_data["prompt"] = f"Original topic: {self.conversation_data['prompt']}. Revision feedback: {feedback}"
            self.conversation_state = "generating"
            self.add_message("user", f"(Feedback provided: {feedback})")
            self.add_message("bot", "Thank you. I'm writing a new version now...")
            self.toggle_input(False)
            threading.Thread(target=self.generate_logic, daemon=True).start()
        else:
            # If the user cancels the feedback dialog, we just show the draft panel again.
            self.action_panel.grid()
            self.toggle_input(False)

    def handle_sending(self):
        """Handles the 'Yes, Send It' button click."""
        self.action_panel.grid_remove()

        # We will always ask for the sender's credentials. This is the key to our smart,
        # multi-account system. The app uses the provided email to find the correct browser profile.
        sender_email = simpledialog.askstring("Sender Credentials", "Please enter YOUR email address:", parent=self)
        if not sender_email: return # Do nothing if the user cancels.

        sender_password = simpledialog.askstring("Sender Credentials", f"Please enter the password for {sender_email}:", parent=self, show='*')
        if not sender_password: return

        self.add_message("bot", "Perfect! Starting the browser. Please watch the window and terminal for instructions...")
        self.toggle_input(False)

        # We start the final browser automation task in a background thread.
        thread = threading.Thread(
            target=self.run_browser_and_update_gui,
            args=(sender_email, sender_password),
            daemon=True
        )
        thread.start()

    def run_browser_and_update_gui(self, sender_email, sender_password):
        """Calls the browser automation function and handles the result. Runs in a background thread."""
        try:
            # The 'with' statement ensures Playwright resources are managed cleanly.
            with sync_playwright() as playwright:
                # We pass the playwright instance and all necessary data to our browser function.
                send_email_with_browser(
                    playwright,
                    self.conversation_data["recipient"],
                    self.generated_email["subject"],
                    self.generated_email["body"],
                    sender_email,
                    sender_password
                )
            # If the browser automation succeeds, we schedule a success pop-up on the main thread.
            self.after(0, lambda: messagebox.showinfo("Success", "Email sent successfully!"))
        except Exception as e:
            # If any error occurs in the browser, we catch it and show a detailed error pop-up.
            # This lambda trick is crucial to correctly capture the error message 'e'.
            self.after(0, lambda exc=e: messagebox.showerror("Browser Error", f"An error occurred during automation:\n{exc}"))
        finally:
            # We always reset the conversation so the user can start over.
            self.after(0, self.reset_conversation)

    def reset_conversation(self):
        """Resets the application state to make it ready for a new email task."""
        self.add_message("bot", "I'm ready to help with another email. Who is the next recipient?")
        self.conversation_state = "asking_recipient"
        self.toggle_input(True)

    def toggle_input(self, enabled=True):
        """A small helper function to enable or disable the user input fields."""
        self.input_entry.configure(state="normal" if enabled else "disabled")
        self.send_button.configure(state="normal" if enabled else "disabled")
        # This automatically puts the cursor back in the input box for the user.
        if enabled: self.input_entry.focus()

# This is the standard entry point for a Python application. The code inside this block will only run when the script is executed directly.

if __name__ == "__main__":
    # We create an instance of our application class
    app = ChatApp()
    # start the main event loop, which makes the window appear and wait for user interaction.
    
    app.mainloop()
