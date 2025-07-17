# app.py
# This is the main application file for the AI Email Assistant.
# It creates a modern, conversational desktop user interface (UI) where users can
# interact with an AI to draft and send emails automatically.

# Core Libraries
# customtkinter: A modern Python UI library used to build the beautiful, themed chat window.
# threading: Essential for running time-consuming tasks (like AI generation and browser automation)
#            in the background, which ensures the user interface never freezes or lags.
# tkinter (messagebox, simpledialog): The standard Python library for creating simple pop-up dialog
#                                     boxes for errors, successes, and user feedback.
import customtkinter as ctk
import threading
from tkinter import messagebox, simpledialog

# Custom Agent Modules
# These imports connect our UI to the "brain" and "hands" of our assistant.
# We now import both functions from the email_generator.
from agent.email_generator import analyze_prompt_for_followup, generate_email_content
from agent.browser_automation import send_email_with_playwright

# Main Application Class
# We structure the entire application inside a class to keep all the UI elements
# and their related functions organized and self-contained.
class ChatApp(ctk.CTk):
    # The __init__ method is the constructor for our app. It runs once when the app starts.
    def __init__(self):
        super().__init__()

        # State and Data Management
        # This dictionary holds all the information gathered during the conversation.
        self.conversation_data = {}
        # This variable stores the AI-generated email draft.
        self.generated_email = None
        # This is the heart of our conversational logic. It's a "state machine" that
        # tracks what question the bot should ask next.
        self.conversation_state = "asking_recipient"

        # Window and Theme Configuration
        self.title(" Autonomous Email Assistant (Definitive Version)")
        self.geometry("800x850") # Set the window size
        ctk.set_appearance_mode("dark")  # Use a sleek dark theme
        ctk.set_default_color_theme("green") # Set the accent color

        # Main UI Layout
        # We use a grid layout to structure the window into three main parts.
        self.grid_rowconfigure(0, weight=4) # Chat history area (takes most space)
        self.grid_rowconfigure(1, weight=3) # Action panel for the draft
        self.grid_rowconfigure(2, weight=0) # Input bar at the bottom
        self.grid_columnconfigure(0, weight=1)

        # Chat History Display
        # This is the main textbox where the conversation appears.
        self.chat_history = ctk.CTkTextbox(self, state="disabled", wrap="word", font=("Segoe UI", 14), border_spacing=10)
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        # We define "tags" to style the bot's and user's messages differently.
        self.chat_history.tag_config("bot", foreground="#4ADEDE", justify="left")
        self.chat_history.tag_config("user", foreground="#FFFFFF", justify="right")

        # The Action Panel (for displaying the draft)
        # This dedicated panel is the robust solution to our previous UI-freezing bugs.
        # It's created once but kept hidden until a draft is ready.
        self.action_panel = ctk.CTkFrame(self, fg_color="#2A2D2E", corner_radius=10)
        self.action_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.action_panel.grid_remove() # Start with the panel hidden

        self.action_panel.grid_columnconfigure(0, weight=1)
        self.action_panel.grid_rowconfigure(1, weight=1)

        self.subject_label = ctk.CTkLabel(self.action_panel, text="Subject:", font=ctk.CTkFont(weight="bold"))
        self.subject_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))
        
        self.body_text = ctk.CTkTextbox(self.action_panel, wrap="word", font=("Segoe UI", 12), state="disabled")
        self.body_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        self.button_frame = ctk.CTkFrame(self.action_panel, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.yes_button = ctk.CTkButton(self.button_frame, text="Yes, Send It", command=self.handle_sending)
        self.no_button = ctk.CTkButton(self.button_frame, text=" No, I need changes", fg_color="#D32F2F", hover_color="#B71C1C", command=self.handle_rejection)
        self.yes_button.grid(row=0, column=0, padx=(0, 5), ipady=5, sticky="ew")
        self.no_button.grid(row=0, column=1, padx=(5, 0), ipady=5, sticky="ew")
        
        # User Input Frame
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your response here...", height=40, font=("Segoe UI", 12))
        self.input_entry.grid(row=0, column=0, sticky="ew")
        self.input_entry.bind("<Return>", self.handle_user_input) # Allow pressing Enter to send
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80, height=40, font=ctk.CTkFont(weight="bold"), command=self.handle_user_input)
        self.send_button.grid(row=0, column=1, padx=(10, 0))
        
        # Start the Conversation
        self.start_conversation()

    # UI Helper Functions
    def add_message(self, speaker, text):
        """A helper function to add a new message bubble to the chat history."""
        self.chat_history.configure(state="normal") # Enable writing to the box
        self.chat_history.insert("end", f"{text}\n\n", speaker)
        self.chat_history.configure(state="disabled") # Disable writing to prevent user typing
        self.chat_history.see("end") # Auto-scroll to the latest message

    # Core Application Logic
    def start_conversation(self):
        """Initiates the conversation with the first question."""
        self.add_message("bot", "Hello! I'm your AI Email Assistant.\nWho should this email be sent to?")

    def handle_user_input(self, event=None):
        """This function is the central controller for the conversation."""
        user_text = self.input_entry.get().strip()
        if not user_text: return # Ignore empty input
        
        self.add_message("user", user_text)
        self.input_entry.delete(0, "end")
        self.toggle_input(False) # Disable input while the bot is "thinking"

        # This is our State Machine logic. It checks the current state of the
        # conversation and decides what to do next.
        if self.conversation_state == "asking_recipient":
            self.conversation_data["recipient"] = user_text
            self.conversation_state = "asking_name"
            self.add_message("bot", "Got it. And what is your name for the signature?")
            self.toggle_input(True)
        elif self.conversation_state == "asking_name":
            self.conversation_data["user_name"] = user_text
            self.conversation_state = "asking_prompt"
            self.add_message("bot", "Perfect! Now, what should the email be about?")
            self.toggle_input(True)
        elif self.conversation_state == "asking_prompt":
            self.conversation_data["prompt"] = user_text
            self.conversation_state = "analyzing" # NEW STATE
            self.add_message("bot", "Analyzing your request...")
            # Start the analysis in a background thread
            threading.Thread(target=self.analyze_logic, daemon=True).start()
            
        elif self.conversation_state == "asking_followup": # NEW STATE
            
            # The user has provided the answer to the follow-up question
            
            self.conversation_data["prompt"] += f". Additional details: {user_text}"
            self.conversation_state = "generating"
            self.add_message("bot", "Thank you. I'm writing the draft now...")
            threading.Thread(target=self.generate_logic, daemon=True).start()

    def analyze_logic(self):
        """Calls the AI to analyze if a follow-up question is needed."""
        follow_up_question = analyze_prompt_for_followup(self.conversation_data["prompt"])
        # Schedule the UI update on the main thread
        self.after(0, self.update_ui_after_analysis, follow_up_question)

    def update_ui_after_analysis(self, follow_up_question):
        """Decides whether to ask a follow-up or generate the draft."""
        if follow_up_question:
            # If a question is returned, ask it.
            self.conversation_state = "asking_followup"
            self.add_message("bot", f"Just one quick question: {follow_up_question}")
            self.toggle_input(True)
        else:
            # If no question is needed, proceed directly to generation.
            self.conversation_state = "generating"
            self.add_message("bot", "Understood. I'm writing the draft now...")
            threading.Thread(target=self.generate_logic, daemon=True).start()

    def generate_logic(self):
        """Calls the AI to generate the email content."""
        self.generated_email = generate_email_content(self.conversation_data["user_name"], self.conversation_data["prompt"])
        self.after(0, self.update_ui_after_generation)

    def update_ui_after_generation(self):
        """Updates the UI after the AI has finished generating."""
        self.toggle_input(False) # Keep input disabled while showing the draft
        if self.generated_email:
            self.add_message("bot", "Here is the draft I've prepared for your review:")
            
            # Populate and show the dedicated action panel with the draft
            self.subject_label.configure(text=f"Subject: {self.generated_email['subject']}")
            self.body_text.configure(state="normal")
            self.body_text.delete("1.0", "end")
            self.body_text.insert("1.0", self.generated_email["body"])
            self.body_text.configure(state="disabled")
            self.action_panel.grid() # Make the panel visible
            
            self.conversation_state = "awaiting_decision"
        else:
            self.add_message("bot", "I'm sorry, I couldn't generate an email. Please check the terminal for error details.")
            self.add_message("bot", "Let's try again. What should the email be about?")
            self.conversation_state = "asking_prompt"
            self.toggle_input(True)

    def handle_rejection(self):
        """Handles the 'No, I need changes' button click."""
        self.action_panel.grid_remove() # Hide the draft panel
        feedback = simpledialog.askstring("Provide Feedback", "Of course. Please tell me what you'd like to change.", parent=self)
        if feedback:
            # Update the prompt with the new feedback for the AI
            self.conversation_data["prompt"] = f"Original topic: {self.conversation_data['prompt']}. Revision feedback: {feedback}"
            self.conversation_state = "generating"
            self.add_message("user", f"(Feedback provided: {feedback})")
            self.add_message("bot", "Thank you. I'm writing a new version now...")
            self.toggle_input(False)
            threading.Thread(target=self.generate_logic, daemon=True).start()
        else:
            # If the user cancels the feedback dialog, show the draft panel again
            self.action_panel.grid()
            self.toggle_input(False)

    def handle_sending(self):
        """Handles the 'Yes, Send It' button click."""
        self.action_panel.grid_remove() # Hide the draft panel
        self.add_message("bot", "Perfect! Sending the email now. Please watch for the browser window to open...")
        self.toggle_input(False)
        threading.Thread(target=self.run_browser_and_update_gui, daemon=True).start()

    def run_browser_and_update_gui(self):
        """Calls the browser automation function and handles the result."""
        try:
            send_email_with_playwright(self.conversation_data["recipient"], self.generated_email["subject"], self.generated_email["body"])
            self.after(0, lambda: messagebox.showinfo("Success", "Email sent successfully!"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Browser Error", f"An error occurred during automation:\n{e}"))
        finally:
            self.after(0, self.reset_conversation)

    def reset_conversation(self):
        """Resets the application state to start a new conversation."""
        self.add_message("bot", "I'm ready to help with another email. Who is the next recipient?")
        self.conversation_state = "asking_recipient"
        self.toggle_input(True)

    def toggle_input(self, enabled=True):
        """A helper function to enable or disable the user input fields."""
        self.input_entry.configure(state="normal" if enabled else "disabled")
        self.send_button.configure(state="normal" if enabled else "disabled")
        if enabled: self.input_entry.focus()

# This is the standard entry point for a Python application.

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
