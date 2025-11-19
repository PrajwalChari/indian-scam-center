"""
GUI Frontend for Company Email Search System
A simple, user-friendly interface for searching and verifying company emails.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from main_windows import EmailSearcher
import queue

class EmailSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Company Email Search & Verification System")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.searcher = None
        self.search_running = False
        self.result_queue = queue.Queue()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Company Email Search System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL Input
        ttk.Label(main_frame, text="Company Website URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="https://")
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Search Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # Max Pages
        ttk.Label(settings_frame, text="Max Pages:").grid(row=0, column=0, sticky=tk.W)
        self.max_pages_var = tk.StringVar(value="10")
        max_pages_spinbox = ttk.Spinbox(settings_frame, from_=1, to=50, width=10, 
                                       textvariable=self.max_pages_var)
        max_pages_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        # Delay
        ttk.Label(settings_frame, text="Delay (seconds):").grid(row=0, column=2, sticky=tk.W)
        self.delay_var = tk.StringVar(value="1.0")
        delay_spinbox = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1, 
                                   width=10, textvariable=self.delay_var)
        delay_spinbox.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # Verify emails checkbox
        self.verify_var = tk.BooleanVar(value=True)
        verify_check = ttk.Checkbutton(settings_frame, text="Verify email domains", 
                                      variable=self.verify_var)
        verify_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.search_button = ttk.Button(button_frame, text="Search for Emails", 
                                       command=self.start_search, style="Accent.TButton")
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Search", 
                                     command=self.stop_search, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Results", 
                                      command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress Bar
        self.progress_var = tk.StringVar(value="Ready to search...")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=4, column=0, columnspan=3, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Results Area
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results Text Area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Bind Enter key to start search
        self.url_entry.bind('<Return>', lambda e: self.start_search())
        
        # Start checking for results
        self.check_results()
        
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
            
        url = self.validate_url(self.url_var.get())
        if not url:
            messagebox.showerror("Error", "Please enter a valid website URL")
            return
            
        try:
            max_pages = int(self.max_pages_var.get())
            delay = float(self.delay_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for max pages and delay")
            return
            
        # Update UI
        self.search_running = True
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set(f"Starting search for {url}...")
        self.status_var.set("Searching...")
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Start search thread
        self.search_thread = threading.Thread(target=self.run_search, 
                                             args=(url, max_pages, delay))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def run_search(self, url, max_pages, delay):
        """Run the email search in background thread."""
        try:
            # Initialize searcher
            self.searcher = EmailSearcher(max_pages=max_pages, delay=delay)
            
            # Update progress
            self.result_queue.put(("progress", f"Searching {url}..."))
            
            # Search for emails
            emails = self.searcher.search_website_for_emails(url)
            
            # Update progress
            self.result_queue.put(("progress", f"Found {len(emails)} emails. Processing results..."))
            
            if emails:
                # Display found emails
                result_text = f"SEARCH RESULTS for {url}\n"
                result_text += "=" * 60 + "\n\n"
                result_text += f"Found {len(emails)} email addresses:\n\n"
                
                for i, email in enumerate(sorted(emails), 1):
                    result_text += f"{i:2d}. {email}\n"
                
                self.result_queue.put(("results", result_text))
                
                # Verify emails if requested
                if self.verify_var.get() and self.search_running:
                    self.result_queue.put(("progress", "Verifying email domains..."))
                    
                    verification_results = []
                    for i, email in enumerate(sorted(emails), 1):
                        if not self.search_running:
                            break
                            
                        self.result_queue.put(("progress", f"Verifying {i}/{len(emails)}: {email}"))
                        
                        try:
                            domain_valid = self.searcher.verify_email_domain(email)
                            verification_results.append({
                                'email': email,
                                'domain_valid': domain_valid,
                                'status': 'Valid' if domain_valid else 'Invalid Domain'
                            })
                        except Exception as e:
                            verification_results.append({
                                'email': email,
                                'domain_valid': False,
                                'status': f'Error: {str(e)[:30]}...'
                            })
                    
                    if self.search_running:
                        # Display verification results
                        verify_text = "\n\nEMAIL VERIFICATION RESULTS:\n"
                        verify_text += "-" * 60 + "\n"
                        verify_text += f"{'Email':<35} {'Status':<20}\n"
                        verify_text += "-" * 60 + "\n"
                        
                        valid_count = 0
                        for result in verification_results:
                            status_symbol = "✓" if result['domain_valid'] else "✗"
                            verify_text += f"{result['email']:<35} {status_symbol} {result['status']}\n"
                            if result['domain_valid']:
                                valid_count += 1
                        
                        verify_text += f"\nSUMMARY:\n"
                        verify_text += f"Total emails found: {len(emails)}\n"
                        verify_text += f"Valid domains: {valid_count}\n"
                        verify_text += f"Invalid/Error: {len(emails) - valid_count}\n"
                        
                        if valid_count > 0:
                            verify_text += f"\nRECOMMENDED EMAILS TO CONTACT:\n"
                            for result in verification_results:
                                if result['domain_valid']:
                                    verify_text += f"  • {result['email']}\n"
                        
                        self.result_queue.put(("append", verify_text))
            else:
                result_text = f"SEARCH RESULTS for {url}\n"
                result_text += "=" * 60 + "\n\n"
                result_text += "No email addresses found.\n\n"
                result_text += "This could be due to:\n"
                result_text += "  • Website blocking automated requests\n"
                result_text += "  • Emails loaded dynamically with JavaScript\n"
                result_text += "  • No contact information on accessible pages\n"
                result_text += "  • Email addresses are images or obfuscated\n"
                
                self.result_queue.put(("results", result_text))
            
            if self.search_running:
                self.result_queue.put(("complete", "Search completed successfully!"))
            else:
                self.result_queue.put(("complete", "Search stopped by user."))
                
        except Exception as e:
            self.result_queue.put(("error", f"Search failed: {str(e)}"))
        
    def stop_search(self):
        """Stop the current search."""
        self.search_running = False
        self.progress_var.set("Stopping search...")
        
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Results cleared")
        
    def check_results(self):
        """Check for results from the search thread."""
        try:
            while True:
                msg_type, msg_data = self.result_queue.get_nowait()
                
                if msg_type == "progress":
                    self.progress_var.set(msg_data)
                elif msg_type == "results":
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, msg_data)
                elif msg_type == "append":
                    self.results_text.insert(tk.END, msg_data)
                elif msg_type == "complete":
                    self.search_running = False
                    self.search_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.progress_bar.stop()
                    self.progress_var.set(msg_data)
                    self.status_var.set("Search complete")
                elif msg_type == "error":
                    self.search_running = False
                    self.search_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.progress_bar.stop()
                    self.progress_var.set("Search failed")
                    self.status_var.set("Error")
                    messagebox.showerror("Search Error", msg_data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_results)

def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('winnative')
    
    app = EmailSearchGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")

if __name__ == "__main__":
    main()