"""
Beautiful Modern GUI for Company Email Search System
Using CustomTkinter for a sleek, modern interface
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from main_windows import EmailSearcher
import queue
import webbrowser
from PIL import Image
import os

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ModernEmailSearchGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Company Email Search & Verification")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.searcher = None
        self.search_running = False
        self.result_queue = queue.Queue()
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.setup_ui()
        self.start_result_checking()
        
    def setup_ui(self):
        """Setup the modern user interface."""
        
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # Header Section
        self.setup_header(main_frame)
        
        # Input Section
        self.setup_input_section(main_frame)
        
        # Results Section
        self.setup_results_section(main_frame)
        
        # Footer Section
        self.setup_footer(main_frame)
        
    def setup_header(self, parent):
        """Setup the header section."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Company Email Search & Verification",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f538d", "#4da6ff")
        )
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automatically discover and verify company email addresses from websites",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        subtitle_label.grid(row=1, column=0)
        
    def setup_input_section(self, parent):
        """Setup the input and controls section."""
        input_frame = ctk.CTkFrame(parent)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)
        
        # URL Input
        url_label = ctk.CTkLabel(input_frame, text="Website URL:", font=ctk.CTkFont(size=14, weight="bold"))
        url_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=(20, 5))
        
        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="https://example.com",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(20, 5))
        self.url_entry.bind('<Return>', lambda e: self.start_search())
        
        # Settings Frame
        settings_frame = ctk.CTkFrame(input_frame)
        settings_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20))
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Max Pages Setting
        pages_label = ctk.CTkLabel(settings_frame, text="Max Pages:", font=ctk.CTkFont(size=12, weight="bold"))
        pages_label.grid(row=0, column=0, sticky="w", padx=(15, 5), pady=(15, 5))
        
        self.max_pages_var = tk.StringVar(value="15")
        self.pages_slider = ctk.CTkSlider(
            settings_frame,
            from_=5,
            to=50,
            number_of_steps=45,
            command=self.update_pages_label
        )
        self.pages_slider.set(15)
        self.pages_slider.grid(row=1, column=0, sticky="ew", padx=(15, 5), pady=(0, 15))
        
        self.pages_value_label = ctk.CTkLabel(settings_frame, text="15", font=ctk.CTkFont(size=12))
        self.pages_value_label.grid(row=2, column=0, padx=(15, 5))
        
        # Delay Setting
        delay_label = ctk.CTkLabel(settings_frame, text="Delay (sec):", font=ctk.CTkFont(size=12, weight="bold"))
        delay_label.grid(row=0, column=1, sticky="w", padx=(15, 5), pady=(15, 5))
        
        self.delay_slider = ctk.CTkSlider(
            settings_frame,
            from_=0.5,
            to=5.0,
            number_of_steps=18,
            command=self.update_delay_label
        )
        self.delay_slider.set(1.0)
        self.delay_slider.grid(row=1, column=1, sticky="ew", padx=(15, 5), pady=(0, 15))
        
        self.delay_value_label = ctk.CTkLabel(settings_frame, text="1.0", font=ctk.CTkFont(size=12))
        self.delay_value_label.grid(row=2, column=1, padx=(15, 5))
        
        # Verification Toggle
        verify_label = ctk.CTkLabel(settings_frame, text="Verify Emails:", font=ctk.CTkFont(size=12, weight="bold"))
        verify_label.grid(row=0, column=2, sticky="w", padx=(15, 5), pady=(15, 5))
        
        self.verify_switch = ctk.CTkSwitch(
            settings_frame,
            text="Domain Verification",
            font=ctk.CTkFont(size=12)
        )
        self.verify_switch.select()  # Default to on
        self.verify_switch.grid(row=1, column=2, sticky="w", padx=(15, 5), pady=(5, 15))
        
        # Control Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        self.search_button = ctk.CTkButton(
            button_frame,
            text="Start Search",
            command=self.start_search,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=150
        )
        self.search_button.pack(side="left", padx=(0, 10))
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_search,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=100,
            fg_color=("#d32f2f", "#f44336"),
            hover_color=("#b71c1c", "#d32f2f"),
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=(0, 10))
        
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self.clear_results,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=100,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray30")
        )
        self.clear_button.pack(side="left")
        
    def setup_results_section(self, parent):
        """Setup the results display section."""
        results_frame = ctk.CTkFrame(parent)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Progress Section
        progress_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to search! Enter a website URL above.",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=8)
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.progress_bar.set(0)
        
        # Results Display with tabs
        results_display_frame = ctk.CTkFrame(results_frame)
        results_display_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        results_display_frame.grid_columnconfigure(0, weight=1)
        results_display_frame.grid_rowconfigure(1, weight=1)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(results_display_frame, fg_color="transparent")
        tab_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.results_tab_button = ctk.CTkButton(
            tab_frame, text="Results", width=80, height=30,
            command=lambda: self.switch_tab("results")
        )
        self.results_tab_button.pack(side="left", padx=(0, 5))
        
        self.terminal_tab_button = ctk.CTkButton(
            tab_frame, text="Terminal Log", width=100, height=30,
            command=lambda: self.switch_tab("terminal"),
            fg_color="gray40", hover_color="gray30"
        )
        self.terminal_tab_button.pack(side="left")
        
        # Results Text Area
        self.results_text = ctk.CTkTextbox(
            results_display_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Terminal Log Text Area (initially hidden)
        self.terminal_text = ctk.CTkTextbox(
            results_display_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        
        # Track current tab
        self.current_tab = "results"
        
        # Initial welcome message
        welcome_text = """Welcome to the Company Email Search System!

How to use:
1. Enter a company website URL (e.g., https://microsoft.com)
2. Adjust search settings if needed
3. Click 'Start Search' to begin
4. View results and verification status below

Features:
• Intelligent website analysis
• Real email extraction from HTML
• Domain verification
• Professional results display

Ready to find some emails? Enter a URL above!
        """
        self.results_text.insert("1.0", welcome_text)
        
    def setup_footer(self, parent):
        """Setup the footer section."""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 20))
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Stats
        self.stats_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.stats_label.grid(row=0, column=0, sticky="w")
        
        # Version info
        version_label = ctk.CTkLabel(
            footer_frame,
            text="v2.0 • Modern Email Search System",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        version_label.grid(row=0, column=2, sticky="e")
        
    def update_pages_label(self, value):
        """Update the pages slider label."""
        self.pages_value_label.configure(text=str(int(value)))
        
    def update_delay_label(self, value):
        """Update the delay slider label."""
        self.delay_value_label.configure(text=f"{value:.1f}")
        
    def validate_url(self, url):
        """Validate and format the URL."""
        url = url.strip()
        if not url:
            return None
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
        
    def start_search(self):
        """Start the email search in a separate thread."""
        if self.search_running:
            return
            
        url = self.validate_url(self.url_entry.get())
        if not url:
            messagebox.showerror("❌ Error", "Please enter a valid website URL")
            return
            
        max_pages = int(self.pages_slider.get())
        delay = self.delay_slider.get()
        verify_emails = self.verify_switch.get()
        
        # Update UI
        self.search_running = True
        self.search_button.configure(state="disabled", text="Searching...")
        self.stop_button.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        # Clear previous results
        self.results_text.delete("1.0", "end")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.insert("1.0", f"Starting search for: {url}\n" + "="*60 + "\n")
        
        # Start search thread
        self.search_thread = threading.Thread(
            target=self.run_search, 
            args=(url, max_pages, delay, verify_emails)
        )
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def search_with_logging(self, url, max_pages, delay):
        """Search for emails with detailed terminal logging."""
        all_emails = set()
        
        # Analyze website structure first
        self.result_queue.put(("terminal", f"[ANALYSIS] Fetching homepage: {url}\n"))
        structure = self.searcher.analyze_website_structure(url)
        
        if "error" in structure:
            self.result_queue.put(("terminal", f"[ERROR] Could not analyze website: {structure['error']}\n"))
            return all_emails
        
        # Log discovered pages
        total_pages = sum(len(pages) for pages in structure.values() if isinstance(pages, list))
        self.result_queue.put(("terminal", f"[ANALYSIS] Discovered {total_pages} relevant pages on website\n"))
        
        for page_type, pages in structure.items():
            if pages and isinstance(pages, list):
                self.result_queue.put(("terminal", f"[ANALYSIS] - {page_type.replace('_', ' ').title()}: {len(pages)} pages\n"))
        
        # Build prioritized list
        priority_pages = []
        priority_pages.extend(structure.get("contact_pages", [])[:3])
        priority_pages.extend(structure.get("about_pages", [])[:2])
        priority_pages.extend(structure.get("team_pages", [])[:2])
        priority_pages.extend(structure.get("support_pages", [])[:2])
        priority_pages.extend(structure.get("other_pages", [])[:3])
        
        if url not in priority_pages:
            priority_pages.insert(0, url)
        
        pages_to_search = priority_pages[:max_pages]
        self.result_queue.put(("terminal", f"[SEARCH] Will search {len(pages_to_search)} most relevant pages\n"))
        self.result_queue.put(("terminal", "-" * 60 + "\n"))
        
        # Search each page
        for i, page_url in enumerate(pages_to_search, 1):
            if not self.search_running:
                break
                
            self.result_queue.put(("terminal", f"[PAGE {i}/{len(pages_to_search)}] Checking: {page_url}\n"))
            
            # Get page content
            content = self.searcher.get_page_content(page_url)
            if not content:
                self.result_queue.put(("terminal", f"[PAGE {i}/{len(pages_to_search)}] Failed to fetch page\n"))
                continue
            
            # Extract emails
            page_emails = self.searcher.extract_emails_from_text(content)
            all_emails.update(page_emails)
            
            if page_emails:
                self.result_queue.put(("terminal", f"[PAGE {i}/{len(pages_to_search)}] Found {len(page_emails)} emails: {', '.join(sorted(page_emails))}\n"))
            else:
                self.result_queue.put(("terminal", f"[PAGE {i}/{len(pages_to_search)}] No emails found\n"))
            
            # Update progress
            progress = 0.1 + (0.5 * i / len(pages_to_search))
            self.result_queue.put(("progress", progress))
            
            time.sleep(delay)
        
        return all_emails
        
    def run_search(self, url, max_pages, delay, verify_emails):
        """Run the email search in background thread."""
        try:
            # Initialize searcher
            self.searcher = EmailSearcher(max_pages=max_pages, delay=delay)
            
            # Update progress
            self.result_queue.put(("status", f"Analyzing website structure: {url}"))
            self.result_queue.put(("terminal", f"[ANALYSIS] Starting website structure analysis...\n"))
            self.result_queue.put(("progress", 0.1))
            
            # Search for emails with detailed logging
            emails = self.search_with_logging(url, max_pages, delay)
            
            self.result_queue.put(("progress", 0.6))
            self.result_queue.put(("status", f"Found {len(emails)} emails. Preparing results..."))
            self.result_queue.put(("terminal", f"[COMPLETE] Email discovery finished. Found {len(emails)} unique emails.\n"))
            
            if emails:
                # Display found emails
                result_text = f"""SEARCH RESULTS for {url}
{'=' * 80}

DISCOVERED EMAIL ADDRESSES ({len(emails)} found):
{'-' * 50}
"""
                
                for i, email in enumerate(sorted(emails), 1):
                    result_text += f"{i:2d}. {email}\n"
                
                result_text += f"\nEmail discovery completed successfully!\n"
                
                self.result_queue.put(("results", result_text))
                self.result_queue.put(("progress", 0.7))
                
                # Verify emails if requested
                if verify_emails and self.search_running:
                    self.result_queue.put(("status", "Verifying email domains..."))
                    self.result_queue.put(("terminal", f"\n[VERIFICATION] Starting domain verification for {len(emails)} emails\n"))
                    
                    verification_results = []
                    total_emails = len(emails)
                    
                    for i, email in enumerate(sorted(emails), 1):
                        if not self.search_running:
                            break
                            
                        self.result_queue.put(("status", f"Verifying {i}/{total_emails}: {email}"))
                        self.result_queue.put(("terminal", f"[VERIFY {i}/{total_emails}] Checking domain for: {email}\n"))
                        progress = 0.7 + (0.25 * i / total_emails)
                        self.result_queue.put(("progress", progress))
                        
                        try:
                            domain_valid = self.searcher.verify_email_domain(email)
                            status = 'Valid Domain' if domain_valid else 'Invalid Domain'
                            verification_results.append({
                                'email': email,
                                'domain_valid': domain_valid,
                                'status': status
                            })
                            self.result_queue.put(("terminal", f"[VERIFY {i}/{total_emails}] Result: {status}\n"))
                        except Exception as e:
                            error_msg = f'Error: {str(e)[:30]}...'
                            verification_results.append({
                                'email': email,
                                'domain_valid': False,
                                'status': error_msg
                            })
                            self.result_queue.put(("terminal", f"[VERIFY {i}/{total_emails}] {error_msg}\n"))
                    
                    if self.search_running:
                        # Display verification results
                        verify_text = f"""
EMAIL VERIFICATION RESULTS:
{'-' * 80}
{'Email':<35} {'Status':<25}
{'-' * 80}
"""
                        
                        valid_count = 0
                        for result in verification_results:
                            status_display = f"[✓] {result['status']}" if result['domain_valid'] else f"[✗] {result['status']}"
                            verify_text += f"{result['email']:<35} {status_display}\n"
                            if result['domain_valid']:
                                valid_count += 1
                        
                        verify_text += f"""
VERIFICATION SUMMARY:
{'-' * 50}
Total emails found: {len(emails)}
Valid domains: {valid_count}
Invalid/Error: {len(emails) - valid_count}
Success rate: {(valid_count/len(emails)*100):.1f}%
"""
                        
                        if valid_count > 0:
                            verify_text += f"""
RECOMMENDED EMAILS TO CONTACT:
{'-' * 50}
"""
                            for result in verification_results:
                                if result['domain_valid']:
                                    verify_text += f"• {result['email']}\n"
                        
                        self.result_queue.put(("append", verify_text))
                        self.result_queue.put(("terminal", f"[VERIFICATION] Complete. {valid_count}/{len(emails)} emails have valid domains\n"))
            else:
                result_text = f"""SEARCH RESULTS for {url}
{'=' * 80}

NO EMAIL ADDRESSES FOUND

This could be due to:
• Website blocking automated requests
• Emails loaded dynamically with JavaScript  
• No contact information on accessible pages
• Email addresses are images or obfuscated
• Website uses contact forms instead of direct emails

Suggestions:
• Try manually checking their contact page
• Look for social media links with contact info
• Check if they have a different contact method
• Some companies intentionally hide email addresses
"""
                
                self.result_queue.put(("results", result_text))
            
            if self.search_running:
                self.result_queue.put(("complete", "Search completed successfully!"))
                self.result_queue.put(("stats", f"Searched up to {max_pages} pages • Found {len(emails)} emails"))
            else:
                self.result_queue.put(("complete", "Search stopped by user"))
                
        except Exception as e:
            self.result_queue.put(("error", f"Search failed: {str(e)}"))
        
    def stop_search(self):
        """Stop the current search."""
        self.search_running = False
        self.result_queue.put(("status", "Stopping search..."))
        self.result_queue.put(("terminal", "\n[STOP] Search stopped by user\n"))
        
    def switch_tab(self, tab_name):
        """Switch between results and terminal tabs."""
        if tab_name == "results":
            self.terminal_text.grid_remove()
            self.results_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.results_tab_button.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.terminal_tab_button.configure(fg_color="gray40", hover_color="gray30")
            self.current_tab = "results"
        elif tab_name == "terminal":
            self.results_text.grid_remove()
            self.terminal_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.terminal_tab_button.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.results_tab_button.configure(fg_color="gray40", hover_color="gray30")
            self.current_tab = "terminal"
    
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete("1.0", "end")
        self.terminal_text.delete("1.0", "end")
        welcome_text = """Results cleared! Ready for a new search.

Enter a website URL above and click 'Start Search' to begin discovering emails!
        """
        self.results_text.insert("1.0", welcome_text)
        self.terminal_text.insert("1.0", "Terminal log cleared. Ready for new search.\n")
        self.stats_label.configure(text="Ready")
        
    def start_result_checking(self):
        """Start checking for results from the search thread."""
        self.check_results()
        
    def check_results(self):
        """Check for results from the search thread."""
        try:
            while True:
                msg_type, msg_data = self.result_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_label.configure(text=msg_data)
                elif msg_type == "progress":
                    self.progress_bar.set(msg_data)
                elif msg_type == "terminal":
                    self.terminal_text.insert("end", msg_data)
                    self.terminal_text.see("end")  # Auto-scroll to bottom
                elif msg_type == "results":
                    self.results_text.delete("1.0", "end")
                    self.results_text.insert("1.0", msg_data)
                elif msg_type == "append":
                    self.results_text.insert("end", msg_data)
                elif msg_type == "stats":
                    self.stats_label.configure(text=msg_data)
                elif msg_type == "complete":
                    self.search_running = False
                    self.search_button.configure(state="normal", text="Start Search")
                    self.stop_button.configure(state="disabled")
                    self.progress_bar.stop()
                    self.progress_bar.set(1.0)
                    self.status_label.configure(text=msg_data)
                elif msg_type == "error":
                    self.search_running = False
                    self.search_button.configure(state="normal", text="Start Search")
                    self.stop_button.configure(state="disabled")
                    self.progress_bar.stop()
                    self.progress_bar.set(0)
                    self.status_label.configure(text="Search failed")
                    messagebox.showerror("Search Error", msg_data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_results)

def main():
    """Main function to run the modern GUI application."""
    app = ModernEmailSearchGUI()
    
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")

if __name__ == "__main__":
    main()