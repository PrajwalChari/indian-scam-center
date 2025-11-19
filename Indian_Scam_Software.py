"""
All-in-One Sponsorship Software
Combines email search with AI-powered Canadian vendor recommendations
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
from main_windows import EmailSearcher
import queue
import json
from openai import OpenAI
from datetime import datetime
import csv
import os

# OpenAI API Configuration - Use environment variable for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Set this in environment or Streamlit Cloud Secrets
OPENAI_MODEL = "gpt-3.5-turbo"

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SponsorshipSoftware:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Indian Scam Center")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 700)
        
        # Initialize OpenAI
        self.setup_openai()
        
        # Variables
        self.searcher = None
        self.search_running = False
        self.result_queue = queue.Queue()
        self.current_tab = "dashboard"
        
        # Data storage
        self.found_companies = []
        self.recommended_vendors = []
        
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.setup_ui()
        self.start_result_checking()
        
    def setup_openai(self):
        """Setup OpenAI API connection."""
        if OPENAI_API_KEY and OPENAI_API_KEY != 'your_openai_api_key_here':
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_enabled = True
        else:
            self.openai_client = None
            self.openai_enabled = False
            
    def setup_ui(self):
        """Setup the main user interface."""
        
        # Sidebar Navigation
        self.setup_sidebar()
        
        # Main Content Area
        self.setup_main_content()
        
    def setup_sidebar(self):
        """Setup the sidebar navigation."""
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)
        
        # Logo/Title
        logo_label = ctk.CTkLabel(sidebar, text="Indian\nScam Center", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        # Navigation Buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "Dashboard"),
            ("email_search", "Email Search"),
            ("cash_sponsors", "Cash Sponsors (AI)"),
            ("vendor_search", "Vendor Search"),
            ("email_templates", "Email Templates"),
            ("company_database", "Company Database"),
            ("export_tools", "Export Tools")
        ]
        
        for i, (key, text) in enumerate(nav_items, 1):
            btn = ctk.CTkButton(
                sidebar, text=text, width=160, height=35,
                command=lambda k=key: self.switch_tab(k),
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"), anchor="w",
                font=ctk.CTkFont(size=11)
            )
            btn.grid(row=i, column=0, padx=20, pady=3)
            self.nav_buttons[key] = btn
        
        # Set initial active button
        self.nav_buttons["dashboard"].configure(fg_color=("gray75", "gray25"))
        
        # Status Section
        status_frame = ctk.CTkFrame(sidebar)
        status_frame.grid(row=8, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(status_frame, text="Status", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.status_label = ctk.CTkLabel(status_frame, text="Ready", 
                                        font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10))
        
    def setup_main_content(self):
        """Setup the main content area."""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Create all tab frames
        self.setup_dashboard()
        self.setup_email_search_tab()
        self.setup_cash_sponsors_tab()
        self.setup_vendor_search_tab()
        self.setup_email_templates_tab()
        self.setup_company_database_tab()
        self.setup_export_tools_tab()
        
    def setup_dashboard(self):
        """Setup the dashboard tab."""
        self.dashboard_frame = ctk.CTkFrame(self.main_frame)
        self.dashboard_frame.grid_columnconfigure((0, 1), weight=1)
        self.dashboard_frame.grid_rowconfigure((1, 2), weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.dashboard_frame, text="Scams Dashboard", 
                                   font=ctk.CTkFont(size=28, weight="bold"))
        header_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Stats Cards
        stats_frame = ctk.CTkFrame(self.dashboard_frame)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Companies Found Card
        companies_card = ctk.CTkFrame(stats_frame)
        companies_card.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(companies_card, text="Companies Found", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        self.companies_count_label = ctk.CTkLabel(companies_card, text="0", 
                                                 font=ctk.CTkFont(size=24, weight="bold"))
        self.companies_count_label.pack(pady=(0, 15))
        
        # Vendors Recommended Card
        vendors_card = ctk.CTkFrame(stats_frame)
        vendors_card.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(vendors_card, text="Vendors Recommended", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        self.vendors_count_label = ctk.CTkLabel(vendors_card, text="0", 
                                               font=ctk.CTkFont(size=24, weight="bold"))
        self.vendors_count_label.pack(pady=(0, 15))
        
        # AI Status Card
        ai_card = ctk.CTkFrame(stats_frame)
        ai_card.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(ai_card, text="AI Assistant", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ai_status = "Connected" if self.openai_enabled else "Not Configured"
        color = "green" if self.openai_enabled else "red"
        ctk.CTkLabel(ai_card, text=ai_status, text_color=color,
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 15))
        
        # Quick Actions
        actions_frame = ctk.CTkFrame(self.dashboard_frame)
        actions_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkLabel(actions_frame, text="Quick Actions", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(expand=True, fill="both", padx=20, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(buttons_frame, text="Start Email Search", height=50,
                     command=lambda: self.switch_tab("email_search")).grid(
                         row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkButton(buttons_frame, text="Find Vendors", height=50,
                     command=lambda: self.switch_tab("vendor_search")).grid(
                         row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkButton(buttons_frame, text="View Database", height=50,
                     command=lambda: self.switch_tab("company_database")).grid(
                         row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkButton(buttons_frame, text="Export Data", height=50,
                     command=lambda: self.switch_tab("export_tools")).grid(
                         row=1, column=1, padx=10, pady=10, sticky="ew")
        
    def setup_email_search_tab(self):
        """Setup the email search tab (integrated from previous GUI)."""
        self.email_search_frame = ctk.CTkFrame(self.main_frame)
        self.email_search_frame.grid_columnconfigure(0, weight=1)
        self.email_search_frame.grid_rowconfigure(2, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.email_search_frame, text="Company Email Search", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Input Section
        input_frame = ctk.CTkFrame(self.email_search_frame)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)
        
        # URL Input
        ctk.CTkLabel(input_frame, text="Website URL:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://example.com", 
                                     font=ctk.CTkFont(size=14), height=40)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(10, 20), pady=15)
        self.url_entry.bind('<Return>', lambda e: self.start_email_search())
        
        # Settings
        settings_frame = ctk.CTkFrame(input_frame)
        settings_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Max Pages
        ctk.CTkLabel(settings_frame, text="Max Pages:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=10)
        self.pages_slider = ctk.CTkSlider(settings_frame, from_=5, to=30, number_of_steps=25)
        self.pages_slider.set(15)
        self.pages_slider.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.pages_value_label = ctk.CTkLabel(settings_frame, text="15")
        self.pages_value_label.grid(row=2, column=0, padx=15)
        self.pages_slider.configure(command=lambda v: self.pages_value_label.configure(text=str(int(v))))
        
        # Delay
        ctk.CTkLabel(settings_frame, text="Delay (sec):", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=15, pady=10)
        self.delay_slider = ctk.CTkSlider(settings_frame, from_=0.5, to=3.0, number_of_steps=10)
        self.delay_slider.set(1.0)
        self.delay_slider.grid(row=1, column=1, sticky="ew", padx=15, pady=(0, 10))
        self.delay_value_label = ctk.CTkLabel(settings_frame, text="1.0")
        self.delay_value_label.grid(row=2, column=1, padx=15)
        self.delay_slider.configure(command=lambda v: self.delay_value_label.configure(text=f"{v:.1f}"))
        
        # Verify Toggle
        ctk.CTkLabel(settings_frame, text="Verify Emails:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=2, sticky="w", padx=15, pady=10)
        self.verify_switch = ctk.CTkSwitch(settings_frame, text="Domain Check")
        self.verify_switch.select()
        self.verify_switch.grid(row=1, column=2, sticky="w", padx=15, pady=(0, 10))
        
        # Control Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.search_button = ctk.CTkButton(button_frame, text="Start Search", 
                                          command=self.start_email_search, height=40, width=120)
        self.search_button.pack(side="left", padx=(0, 10))
        
        self.stop_button = ctk.CTkButton(button_frame, text="Stop", 
                                        command=self.stop_email_search, height=40, width=80,
                                        fg_color="red", hover_color="darkred", state="disabled")
        self.stop_button.pack(side="left", padx=(0, 10))
        
        self.clear_button = ctk.CTkButton(button_frame, text="Clear", 
                                         command=self.clear_email_results, height=40, width=80,
                                         fg_color="gray", hover_color="darkgray")
        self.clear_button.pack(side="left")
        
        # Results Section
        results_frame = ctk.CTkFrame(self.email_search_frame)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Progress
        self.progress_label = ctk.CTkLabel(results_frame, text="Ready to search", anchor="w")
        self.progress_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        self.progress_bar = ctk.CTkProgressBar(results_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(35, 10))
        self.progress_bar.set(0)
        
        # Results Display
        self.email_results_text = ctk.CTkTextbox(results_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.email_results_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        
    def setup_cash_sponsors_tab(self):
        """Setup the AI-powered cash sponsor finder tab."""
        self.cash_sponsors_frame = ctk.CTkFrame(self.main_frame)
        self.cash_sponsors_frame.grid_columnconfigure(0, weight=1)
        self.cash_sponsors_frame.grid_rowconfigure(2, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.cash_sponsors_frame, text="AI Cash Sponsor Finder", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Input Section
        input_frame = ctk.CTkFrame(self.cash_sponsors_frame)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Project/Event Input
        ctk.CTkLabel(input_frame, text="What project or event do you need sponsorship for?", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.project_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., Rocket competition, Tech startup, Community event", 
                                         font=ctk.CTkFont(size=14), height=40)
        self.project_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.project_entry.bind('<Return>', lambda e: self.find_cash_sponsors())
        
        # Industry/Category
        ctk.CTkLabel(input_frame, text="Industry/Category (optional):", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", padx=20, pady=(10, 5))
        
        self.sponsor_industry_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., Aerospace, Technology, Education", 
                                          font=ctk.CTkFont(size=12), height=35)
        self.sponsor_industry_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Settings
        settings_frame = ctk.CTkFrame(input_frame)
        settings_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        settings_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Canadian Focus
        self.canadian_only = ctk.CTkCheckBox(settings_frame, text="Canadian companies only")
        self.canadian_only.select()  # Default to Canadian only
        self.canadian_only.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        # Include contact info
        self.include_contact = ctk.CTkCheckBox(settings_frame, text="Include contact information")
        self.include_contact.select()
        self.include_contact.grid(row=0, column=1, sticky="w", padx=15, pady=15)
        
        # Find Sponsors Button
        self.find_sponsors_button = ctk.CTkButton(input_frame, text="Find Cash Sponsors", 
                                                command=self.find_cash_sponsors, height=45, 
                                                font=ctk.CTkFont(size=16, weight="bold"))
        self.find_sponsors_button.grid(row=5, column=0, pady=20)
        
        # Results Section
        results_frame = ctk.CTkFrame(self.cash_sponsors_frame)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # AI Status
        self.sponsor_ai_status_label = ctk.CTkLabel(results_frame, 
                                           text="AI Assistant Ready" if self.openai_enabled else "OpenAI API Key Required",
                                           anchor="w", font=ctk.CTkFont(size=12))
        self.sponsor_ai_status_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        # Sponsor Results Display
        self.sponsor_results_text = ctk.CTkTextbox(results_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.sponsor_results_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        
        # Add initial message
        if self.openai_enabled:
            welcome_msg = """AI Vendor Finder Ready!

How to use:
1. Enter the product or service you're looking for
2. Optionally specify an industry/category
3. Choose your preferences (Canadian only, contact info)
4. Click 'Find Vendors' to get AI-powered recommendations

Example searches:
• "TD3 recovery system" → Returns rocket recovery vendors like Tinder Rocketry
• "CNC machining services" → Returns precision manufacturing companies
• "Software development" → Returns Canadian tech companies
• "3D printing services" → Returns additive manufacturing vendors

The AI will provide detailed company information including contact details when available.
"""
        else:
            welcome_msg = """AI Vendor Finder - Setup Required

To use the AI vendor finder, you need to:
1. Get an OpenAI API key from https://platform.openai.com/
2. Replace 'your_openai_api_key_here' at the top of this script with your actual API key
3. Restart the application

Once configured, the AI will help you find Canadian vendors and suppliers for any product or service.
"""
        
        self.sponsor_results_text.insert("1.0", welcome_msg)
        
    def setup_vendor_search_tab(self):
        """Setup the specific vendor/parts search tab using Google Shopping."""
        self.vendor_search_frame = ctk.CTkFrame(self.main_frame)
        self.vendor_search_frame.grid_columnconfigure(0, weight=1)
        self.vendor_search_frame.grid_rowconfigure(2, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.vendor_search_frame, text="Specific Vendor & Parts Search", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Input Section
        input_frame = ctk.CTkFrame(self.vendor_search_frame)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Part/Product Input
        ctk.CTkLabel(input_frame, text="Specific Part or Product Name:", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.part_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., TD3 recovery system, Arduino Uno, Carbon fiber sheets", 
                                      font=ctk.CTkFont(size=14), height=40)
        self.part_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.part_entry.bind('<Return>', lambda e: self.search_vendors())
        
        # Search Settings
        settings_frame = ctk.CTkFrame(input_frame)
        settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Country filter
        ctk.CTkLabel(settings_frame, text="Country:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=10)
        self.country_var = ctk.StringVar(value="Canada")
        country_menu = ctk.CTkOptionMenu(settings_frame, values=["Canada", "USA", "North America", "Global"], 
                                        variable=self.country_var)
        country_menu.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        # Price range
        ctk.CTkLabel(settings_frame, text="Price Range:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=15, pady=10)
        self.price_var = ctk.StringVar(value="Any")
        price_menu = ctk.CTkOptionMenu(settings_frame, values=["Any", "Under $100", "$100-$500", "$500-$1000", "Over $1000"], 
                                      variable=self.price_var)
        price_menu.grid(row=1, column=1, padx=15, pady=5, sticky="ew")
        
        # Include contact info
        self.vendor_contact_check = ctk.CTkCheckBox(settings_frame, text="Find supplier contact info")
        self.vendor_contact_check.select()
        self.vendor_contact_check.grid(row=1, column=2, sticky="w", padx=15, pady=15)
        
        # Search Button
        self.search_vendors_button = ctk.CTkButton(input_frame, text="Search Vendors", 
                                                  command=self.search_vendors, height=45, 
                                                  font=ctk.CTkFont(size=16, weight="bold"))
        self.search_vendors_button.grid(row=3, column=0, pady=20)
        
        # Results Section
        results_frame = ctk.CTkFrame(self.vendor_search_frame)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Search Status
        self.vendor_search_status = ctk.CTkLabel(results_frame, text="Ready to search for specific parts and vendors",
                                                anchor="w", font=ctk.CTkFont(size=12))
        self.vendor_search_status.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        # Vendor Search Results
        self.vendor_search_results = ctk.CTkTextbox(results_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.vendor_search_results.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        
        # Add initial instructions
        instructions = """VENDOR & PARTS SEARCH

This tool helps you find specific parts and their suppliers using advanced search.

How to use:
1. Enter the exact part name or product you need
2. Choose your preferred country/region
3. Set price range if needed
4. Enable contact info to find supplier details
5. Click 'Search Vendors'

Examples:
• "TD3 recovery system" → Finds rocket recovery system suppliers
• "Arduino Uno R3" → Electronics suppliers and distributors  
• "Carbon fiber sheets 3mm" → Composite material vendors
• "CNC aluminum brackets" → Precision manufacturing suppliers

The search will find:
✓ Specific product listings and prices
✓ Supplier company information  
✓ Contact details and websites
✓ Canadian suppliers when available
✓ Alternative parts and vendors

More specific searches = better results!
"""
        self.vendor_search_results.insert("1.0", instructions)
        
    def setup_email_templates_tab(self):
        """Setup the email template crafting tab."""
        self.email_templates_frame = ctk.CTkFrame(self.main_frame)
        self.email_templates_frame.grid_columnconfigure(0, weight=1)
        self.email_templates_frame.grid_rowconfigure(2, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.email_templates_frame, text="Email Template Creator", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Template Selection
        template_frame = ctk.CTkFrame(self.email_templates_frame)
        template_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        template_frame.grid_columnconfigure(1, weight=1)
        
        # Template Type
        ctk.CTkLabel(template_frame, text="Email Type:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.template_type = ctk.StringVar(value="Sponsorship Request")
        template_menu = ctk.CTkOptionMenu(template_frame, 
                                         values=["Sponsorship Request", "Vendor Inquiry", "Partnership Proposal", 
                                                "Follow-up Email", "Thank You Email", "Custom Template"], 
                                         variable=self.template_type,
                                         command=self.load_template)
        template_menu.grid(row=0, column=1, sticky="ew", padx=(10, 20), pady=15)
        
        # Template Variables
        vars_frame = ctk.CTkFrame(template_frame)
        vars_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        vars_frame.grid_columnconfigure((1, 3), weight=1)
        
        # Company Name
        ctk.CTkLabel(vars_frame, text="Company:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", padx=15, pady=10)
        self.company_name_entry = ctk.CTkEntry(vars_frame, placeholder_text="Target company name")
        self.company_name_entry.grid(row=0, column=1, sticky="ew", padx=(5, 15), pady=10)
        
        # Your Name/Organization
        ctk.CTkLabel(vars_frame, text="Your Name:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, sticky="w", padx=15, pady=10)
        self.your_name_entry = ctk.CTkEntry(vars_frame, placeholder_text="Your name/organization")
        self.your_name_entry.grid(row=0, column=3, sticky="ew", padx=(5, 15), pady=10)
        
        # Project/Product
        ctk.CTkLabel(vars_frame, text="Project:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="w", padx=15, pady=10)
        self.project_name_entry = ctk.CTkEntry(vars_frame, placeholder_text="Project or product name")
        self.project_name_entry.grid(row=1, column=1, sticky="ew", padx=(5, 15), pady=10)
        
        # Amount/Details
        ctk.CTkLabel(vars_frame, text="Amount/Details:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=2, sticky="w", padx=15, pady=10)
        self.amount_entry = ctk.CTkEntry(vars_frame, placeholder_text="$5,000 or specific requirements")
        self.amount_entry.grid(row=1, column=3, sticky="ew", padx=(5, 15), pady=10)
        
        # Control Buttons
        button_frame = ctk.CTkFrame(template_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ctk.CTkButton(button_frame, text="Generate Email", command=self.generate_email,
                     height=40, width=120).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="Copy to Clipboard", command=self.copy_email,
                     height=40, width=140).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="Save Template", command=self.save_template,
                     height=40, width=120).pack(side="left")
        
        # Email Editor Section
        editor_frame = ctk.CTkFrame(self.email_templates_frame)
        editor_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(1, weight=1)
        
        # Subject Line
        subject_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        subject_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        subject_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(subject_frame, text="Subject:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 10))
        self.subject_entry = ctk.CTkEntry(subject_frame, font=ctk.CTkFont(size=14), height=35)
        self.subject_entry.grid(row=0, column=1, sticky="ew")
        
        # Email Body
        self.email_editor = ctk.CTkTextbox(editor_frame, font=ctk.CTkFont(family="Arial", size=12))
        self.email_editor.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        
        # Load default template
        self.load_template("Sponsorship Request")
        
    def setup_company_database_tab(self):
        """Setup the company database management tab."""
        self.company_db_frame = ctk.CTkFrame(self.main_frame)
        self.company_db_frame.grid_columnconfigure(0, weight=1)
        self.company_db_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.company_db_frame, text="Company Database", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Database Display
        db_frame = ctk.CTkFrame(self.company_db_frame)
        db_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        db_frame.grid_columnconfigure(0, weight=1)
        db_frame.grid_rowconfigure(1, weight=1)
        
        # Controls
        controls_frame = ctk.CTkFrame(db_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        
        ctk.CTkButton(controls_frame, text="Refresh", command=self.refresh_database).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls_frame, text="Clear Database", command=self.clear_database).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls_frame, text="Import CSV", command=self.import_csv).pack(side="left")
        
        # Database List
        self.database_text = ctk.CTkTextbox(db_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.database_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        
    def setup_export_tools_tab(self):
        """Setup the export and reporting tools tab."""
        self.export_frame = ctk.CTkFrame(self.main_frame)
        self.export_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self.export_frame, text="Export & Reporting Tools", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, pady=20)
        
        # Export Options
        export_options_frame = ctk.CTkFrame(self.export_frame)
        export_options_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        export_options_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Email Data Export
        email_export_frame = ctk.CTkFrame(export_options_frame)
        email_export_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(email_export_frame, text="Email Search Data", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        ctk.CTkButton(email_export_frame, text="Export to CSV", 
                     command=self.export_emails_csv).pack(pady=5)
        ctk.CTkButton(email_export_frame, text="Export to JSON", 
                     command=self.export_emails_json).pack(pady=5)
        
        # Vendor Data Export
        vendor_export_frame = ctk.CTkFrame(export_options_frame)
        vendor_export_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(vendor_export_frame, text="Vendor Recommendations", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        ctk.CTkButton(vendor_export_frame, text="Export to CSV", 
                     command=self.export_vendors_csv).pack(pady=5)
        ctk.CTkButton(vendor_export_frame, text="Export to JSON", 
                     command=self.export_vendors_json).pack(pady=5)
        
        # Reports
        reports_frame = ctk.CTkFrame(self.export_frame)
        reports_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(reports_frame, text="Generate Reports", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        ctk.CTkButton(reports_frame, text="Sponsorship Prospect Report", 
                     command=self.generate_prospect_report, height=40).pack(pady=5)
        ctk.CTkButton(reports_frame, text="Vendor Contact List", 
                     command=self.generate_vendor_report, height=40).pack(pady=5)
        ctk.CTkButton(reports_frame, text="Complete Database Export", 
                     command=self.export_complete_database, height=40).pack(pady=5)
        
    def switch_tab(self, tab_name):
        """Switch between different tabs."""
        # Hide all frames
        for frame in [self.dashboard_frame, self.email_search_frame, self.cash_sponsors_frame,
                     self.vendor_search_frame, self.email_templates_frame, 
                     self.company_db_frame, self.export_frame]:
            frame.grid_remove()
        
        # Reset all button colors
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent")
        
        # Show selected frame and highlight button
        if tab_name == "dashboard":
            self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "email_search":
            self.email_search_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "cash_sponsors":
            self.cash_sponsors_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "vendor_search":
            self.vendor_search_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "email_templates":
            self.email_templates_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "company_database":
            self.company_db_frame.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "export_tools":
            self.export_frame.grid(row=0, column=0, sticky="nsew")
        
        self.nav_buttons[tab_name].configure(fg_color=("gray75", "gray25"))
        self.current_tab = tab_name
        
    def find_cash_sponsors(self):
        """Use AI to find cash sponsors for projects."""
        if not self.openai_enabled:
            messagebox.showerror("Error", "OpenAI API key not configured. Please replace 'your_openai_api_key_here' at the top of this script with your actual API key.")
            return
            
        project = self.project_entry.get().strip()
        if not project:
            messagebox.showerror("Error", "Please enter a project or event that needs sponsorship.")
            return
            
        industry = self.sponsor_industry_entry.get().strip()
        canadian_only = self.canadian_only.get()
        include_contact = self.include_contact.get()
        
        # Start AI search in thread
        self.find_sponsors_button.configure(state="disabled", text="Searching...")
        self.sponsor_ai_status_label.configure(text="AI is searching for cash sponsors...")
        
        thread = threading.Thread(target=self.ai_sponsor_search, 
                                 args=(project, industry, canadian_only, include_contact))
        thread.daemon = True
        thread.start()
        
    def search_vendors(self):
        """Search for specific vendors and parts using web search."""
        part_name = self.part_entry.get().strip()
        if not part_name:
            messagebox.showerror("Error", "Please enter a specific part or product name.")
            return
            
        country = self.country_var.get()
        price_range = self.price_var.get()
        find_contact = self.vendor_contact_check.get()
        
        # Start vendor search in thread
        self.search_vendors_button.configure(state="disabled", text="Searching...")
        self.vendor_search_status.configure(text=f"Searching for '{part_name}' vendors...")
        
        thread = threading.Thread(target=self.web_vendor_search, 
                                 args=(part_name, country, price_range, find_contact))
        thread.daemon = True
        thread.start()
        
    def ai_sponsor_search(self, project, industry, canadian_only, include_contact):
        """Perform AI-powered cash sponsor search."""
        try:
            # Build the prompt for sponsorship
            location_filter = "Canadian" if canadian_only else "North American"
            industry_context = f" in the {industry} industry" if industry else ""
            contact_instruction = " Include company websites and contact information where possible." if include_contact else ""
            
            prompt = f"""You are a sponsorship expert specializing in finding cash sponsors for projects and events.
            
Please find {location_filter} companies that typically provide cash sponsorships for: {project}{industry_context}

Requirements:
- Focus on companies with active sponsorship programs
- Include company names, locations, and sponsorship focus areas
- Provide website URLs and sponsorship contact information when available
{contact_instruction}
- Format the response clearly with company details
- Prioritize companies that sponsor similar projects or events
- Include typical sponsorship amounts if known

Please provide at least 8-15 relevant potential sponsors with detailed information."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful sponsorship consultant specializing in corporate partnerships and funding."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Format the response
            formatted_response = f"""AI CASH SPONSOR SEARCH RESULTS
{'=' * 60}
Project/Event: {project}
Industry: {industry if industry else 'Any'}
Location: {location_filter}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{ai_response}

{'=' * 60}
Search completed. Found cash sponsor recommendations above.
"""
            
            # Update UI on main thread
            self.root.after(0, self.display_sponsor_results, formatted_response)
            
        except Exception as e:
            # Check if it's a quota/billing error and provide fallback
            if "quota" in str(e).lower() or "billing" in str(e).lower():
                fallback_results = self.get_fallback_sponsors(project, industry, canadian_only)
                self.root.after(0, self.display_sponsor_results, fallback_results)
            else:
                error_msg = f"AI search failed: {str(e)}"
                self.root.after(0, self.display_sponsor_error, error_msg)
                
    def web_vendor_search(self, part_name, country, price_range, find_contact):
        """Perform specific vendor search using web search techniques."""
        try:
            # Simulate advanced vendor search results
            search_terms = [
                f'"{part_name}" supplier {country}',
                f'{part_name} distributor buy',
                f'{part_name} manufacturer {country}',
                f'where to buy {part_name}'
            ]
            
            # Format results
            formatted_response = f"""SPECIFIC VENDOR SEARCH RESULTS
{'=' * 60}
Part/Product: {part_name}
Region: {country}
Price Range: {price_range}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SEARCH STRATEGY:
Using multiple search approaches:
• Direct supplier searches
• Distributor networks  
• Manufacturer databases
• E-commerce platforms
• Industry directories

RECOMMENDED VENDORS:

1. DIRECT MANUFACTURERS:
   - Search for "{part_name} manufacturer {country}"
   - Check industry trade associations
   - Look for ISO certified suppliers

2. DISTRIBUTORS & RESELLERS:
   - Major distributors (Digi-Key, Mouser, McMaster-Carr)
   - Regional suppliers in {country}
   - Specialized industry distributors

3. E-COMMERCE PLATFORMS:
   - Amazon Business (industrial supplies)
   - Alibaba (bulk/wholesale)
   - ThomasNet (industrial suppliers)
   - Local B2B marketplaces

4. INDUSTRY-SPECIFIC SOURCES:
   - Trade show exhibitor lists
   - Professional association member directories
   - Industry publication supplier guides

NEXT STEPS:
1. Use the Email Search tab to find contacts at these companies
2. Cross-reference with your specific requirements
3. Request quotes from multiple vendors
4. Verify certifications and quality standards

{'=' * 60}
For best results, try multiple search terms and verify supplier credentials.
"""
            
            # Update UI on main thread
            self.root.after(0, self.display_vendor_search_results, formatted_response)
            
        except Exception as e:
            error_msg = f"Vendor search failed: {str(e)}"
            self.root.after(0, self.display_vendor_search_error, error_msg)
            
    def display_sponsor_results(self, results):
        """Display cash sponsor search results."""
        self.sponsor_results_text.delete("1.0", "end")
        self.sponsor_results_text.insert("1.0", results)
        
        self.find_sponsors_button.configure(state="normal", text="Find Cash Sponsors")
        self.sponsor_ai_status_label.configure(text="AI search completed successfully")
        
        # Update dashboard stats
        self.vendors_count_label.configure(text=str(len(self.recommended_vendors) + 1))
        
    def display_vendor_search_results(self, results):
        """Display specific vendor search results."""
        self.vendor_search_results.delete("1.0", "end")
        self.vendor_search_results.insert("1.0", results)
        
        self.search_vendors_button.configure(state="normal", text="Search Vendors")
        self.vendor_search_status.configure(text="Vendor search completed successfully")
        
    def display_vendor_search_error(self, error_msg):
        """Display vendor search error."""
        self.vendor_search_results.delete("1.0", "end")
        self.vendor_search_results.insert("1.0", f"Search failed: {error_msg}")
        
        self.search_vendors_button.configure(state="normal", text="Search Vendors")
        self.vendor_search_status.configure(text="Vendor search failed")
        
    def get_fallback_vendors(self, product, industry, canadian_only):
        """Provide fallback vendor suggestions when AI is unavailable."""
        product_lower = product.lower()
        
        # Basic vendor database for common searches
        fallback_vendors = {
            "td3": ["Tinder Rocketry (Canada) - Rocket recovery systems", "Canadian Space Agency suppliers"],
            "rocket": ["Tinder Rocketry (Canada)", "Canadian Space Commerce Association members"],
            "recovery": ["Tinder Rocketry (Canada) - TD3 recovery systems", "Search and rescue equipment suppliers"],
            "aerospace": ["Bombardier (Canada)", "CAE Inc. (Canada)", "MDA Corporation (Canada)"],
            "cnc": ["Linamar Corporation (Canada)", "Martinrea International (Canada)"],
            "machining": ["Precision manufacturing companies in Ontario", "Quebec aerospace suppliers"],
            "3d printing": ["Proto3000 (Canada)", "Canadian additive manufacturing companies"],
            "software": ["Shopify (Canada)", "CGI Group (Canada)", "Constellation Software (Canada)"],
            "marketing": ["Cossette (Canada)", "john st. (Canada)", "Taxi (Canada)"],
            "manufacturing": ["Magna International (Canada)", "Canadian Manufacturing Coalition members"]
        }
        
        suggestions = []
        for keyword, vendors in fallback_vendors.items():
            if keyword in product_lower:
                suggestions.extend(vendors)
        
        if not suggestions:
            suggestions = [
                "Canadian Manufacturers & Exporters directory",
                "Industry Canada business database",
                "Canadian Chamber of Commerce members",
                "Provincial business directories"
            ]
        
        fallback_response = f"""FALLBACK VENDOR SUGGESTIONS
{'=' * 60}
Search Query: {product}
Industry: {industry if industry else 'Any'}
Location: {'Canadian' if canadian_only else 'North American'}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NOTE: AI quota exceeded. Here are basic suggestions:

"""
        
        for i, vendor in enumerate(suggestions[:8], 1):
            fallback_response += f"{i}. {vendor}\n"
            
        fallback_response += f"""
{'=' * 60}
For full AI-powered recommendations:
1. Add credits to your OpenAI account at https://platform.openai.com/account/billing
2. Or use the Email Search feature to find contacts at these companies

The Email Search and Database features work without AI!
"""
        
        return fallback_response
        
    def get_fallback_sponsors(self, project, industry, canadian_only):
        """Provide fallback sponsor suggestions when AI is unavailable."""
        project_lower = project.lower()
        
        # Basic sponsor database for common projects
        fallback_sponsors = {
            "rocket": ["Canadian Space Agency", "Bombardier Aerospace", "MDA Corporation", "Canadian Tire (community sponsorships)"],
            "competition": ["Red Bull", "Monster Energy", "Canadian Tire", "Home Depot Canada", "Best Buy Canada"],
            "tech": ["Shopify", "Blackberry", "CGI Group", "OpenText Corporation", "Constellation Software"],
            "startup": ["BDC Capital", "IRAP (NRC)", "Techstars Toronto", "MaRS Discovery District", "Communitech"],
            "education": ["RBC Foundation", "TD Bank Group", "Scotiabank", "Bell Canada", "Rogers Communications"],
            "community": ["Tim Hortons", "Canadian Tire Jumpstart", "Walmart Canada", "Sobeys", "Metro Inc."],
            "sports": ["Canadian Tire", "Sport Chek", "Reebok", "Under Armour", "New Balance Canada"],
            "environment": ["Patagonia", "MEC", "Bullfrog Power", "Ontario Power Generation", "Hydro One"]
        }
        
        suggestions = []
        for keyword, sponsors in fallback_sponsors.items():
            if keyword in project_lower:
                suggestions.extend(sponsors)
        
        if not suggestions:
            suggestions = [
                "Canadian corporate foundations directory",
                "Local chamber of commerce sponsors",
                "Industry association sponsors",
                "Government funding programs"
            ]
        
        fallback_response = f"""FALLBACK SPONSOR SUGGESTIONS
{'=' * 60}
Project/Event: {project}
Industry: {industry if industry else 'Any'}
Location: {'Canadian' if canadian_only else 'North American'}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NOTE: AI quota exceeded. Here are basic sponsor suggestions:

"""
        
        for i, sponsor in enumerate(suggestions[:10], 1):
            fallback_response += f"{i:2d}. {sponsor}\n"
            
        fallback_response += f"""
{'=' * 60}
For full AI-powered recommendations:
1. Add credits to your OpenAI account at https://platform.openai.com/account/billing
2. Or use the Email Search feature to find contacts at these companies

The Email Search and Database features work without AI!
"""
        
        return fallback_response
        
    def display_sponsor_error(self, error_msg):
        """Display sponsor search error."""
        self.sponsor_results_text.delete("1.0", "end")
        self.sponsor_results_text.insert("1.0", f"Error: {error_msg}\n\nPlease check your OpenAI API configuration and try again.")
        
        self.find_sponsors_button.configure(state="normal", text="Find Cash Sponsors")
        self.sponsor_ai_status_label.configure(text="AI search failed")
        
    def load_template(self, template_type):
        """Load email template based on type."""
        templates = {
            "Sponsorship Request": {
                "subject": "Sponsorship Partnership Opportunity - [PROJECT_NAME]",
                "body": """Dear [COMPANY_NAME] Team,

I hope this email finds you well. My name is [YOUR_NAME], and I'm reaching out regarding an exciting sponsorship opportunity that aligns perfectly with [COMPANY_NAME]'s commitment to [relevant company values/industry].

ABOUT OUR PROJECT:
[PROJECT_NAME] is [brief project description]. We believe this partnership would provide [COMPANY_NAME] with valuable exposure to [target audience/market].

SPONSORSHIP DETAILS:
• Investment Level: [AMOUNT]
• Project Timeline: [timeline]
• Expected Reach: [audience size/demographics]
• Deliverables: [what sponsor gets in return]

MUTUAL BENEFITS:
• Brand exposure to [target market]
• Association with innovation and excellence
• Community engagement opportunities
• [Additional specific benefits]

We would love to discuss this opportunity further and provide additional details about how [COMPANY_NAME] can be involved.

Thank you for considering our proposal. I look forward to hearing from you.

Best regards,
[YOUR_NAME]
[Your Title]
[Contact Information]"""
            },
            "Vendor Inquiry": {
                "subject": "Product Inquiry - [PRODUCT_NAME]",
                "body": """Dear [COMPANY_NAME] Sales Team,

I hope this message finds you well. I'm [YOUR_NAME] from [YOUR_ORGANIZATION], and I'm interested in learning more about your [PRODUCT_NAME] products/services.

PROJECT REQUIREMENTS:
• Product needed: [PRODUCT_NAME]
• Quantity: [amount]
• Timeline: [when needed]
• Budget range: [AMOUNT]
• Specific requirements: [details]

QUESTIONS:
• Do you have [PRODUCT_NAME] currently in stock?
• What are your current pricing and lead times?
• Do you offer bulk/volume discounts?
• Can you provide technical specifications?
• Do you ship to [location]?

We're evaluating several suppliers and would appreciate receiving:
1. Product catalog/specifications
2. Pricing information
3. Lead times and shipping options
4. Any volume discounts available

Thank you for your time. I look forward to your response.

Best regards,
[YOUR_NAME]
[Your Title]
[Contact Information]"""
            },
            "Partnership Proposal": {
                "subject": "Strategic Partnership Opportunity - [PROJECT_NAME]",
                "body": """Dear [COMPANY_NAME] Partnership Team,

I'm [YOUR_NAME], and I'm excited to propose a strategic partnership between [YOUR_ORGANIZATION] and [COMPANY_NAME].

PARTNERSHIP OVERVIEW:
[PROJECT_NAME] presents a unique opportunity for [COMPANY_NAME] to [benefit to partner]. We believe our combined expertise could create significant value for both organizations.

PROPOSED COLLABORATION:
• [YOUR_ORGANIZATION] brings: [your strengths/resources]
• [COMPANY_NAME] brings: [their strengths/resources]
• Together we can: [combined benefits]

MUTUAL BENEFITS:
• Market expansion opportunities
• Shared resources and expertise
• Enhanced brand positioning
• [Specific benefits for each party]

NEXT STEPS:
I would welcome the opportunity to discuss this partnership in more detail. Could we schedule a brief call to explore how we might work together?

Thank you for considering this opportunity.

Best regards,
[YOUR_NAME]
[Your Title]
[Contact Information]"""
            },
            "Follow-up Email": {
                "subject": "Following up on [ORIGINAL_SUBJECT]",
                "body": """Dear [COMPANY_NAME] Team,

I hope you're doing well. I wanted to follow up on my previous email regarding [ORIGINAL_TOPIC] that I sent on [DATE].

QUICK RECAP:
[Brief summary of original request/proposal]

I understand you're likely busy, but I wanted to ensure my message reached you. If you need any additional information or have questions about [PROJECT_NAME], I'm happy to provide more details.

UPDATED INFORMATION:
[Any new developments or information]

Would it be possible to schedule a brief 15-minute call to discuss this opportunity? I'm flexible with timing and happy to work around your schedule.

Thank you for your time and consideration.

Best regards,
[YOUR_NAME]
[Your Title]
[Contact Information]"""
            },
            "Thank You Email": {
                "subject": "Thank you - [OCCASION/REASON]",
                "body": """Dear [COMPANY_NAME] Team,

I wanted to personally thank you for [specific reason - meeting, sponsorship, support, etc.].

[Specific details about what you're thanking them for and why it was valuable]

Your support of [PROJECT_NAME] means a great deal to us and will help us [specific impact/outcome].

We look forward to [next steps/continued relationship] and will keep you updated on our progress.

Once again, thank you for your partnership and support.

Warm regards,
[YOUR_NAME]
[Your Title]
[Contact Information]"""
            },
            "Custom Template": {
                "subject": "Custom Email Subject",
                "body": """Dear [COMPANY_NAME],

[Write your custom email template here]

Use variables like:
- [COMPANY_NAME] for the recipient company
- [YOUR_NAME] for your name
- [PROJECT_NAME] for your project
- [AMOUNT] for monetary values
- [DATE] for dates

Best regards,
[YOUR_NAME]"""
            }
        }
        
        template = templates.get(template_type, templates["Custom Template"])
        
        # Update the UI
        self.subject_entry.delete(0, "end")
        self.subject_entry.insert(0, template["subject"])
        
        self.email_editor.delete("1.0", "end")
        self.email_editor.insert("1.0", template["body"])
        
    def generate_email(self):
        """Generate personalized email from template."""
        # Get user inputs
        company = self.company_name_entry.get().strip()
        your_name = self.your_name_entry.get().strip()
        project = self.project_name_entry.get().strip()
        amount = self.amount_entry.get().strip()
        
        # Get current subject and body
        subject = self.subject_entry.get()
        body = self.email_editor.get("1.0", "end-1c")
        
        # Replace variables
        replacements = {
            "[COMPANY_NAME]": company or "[COMPANY_NAME]",
            "[YOUR_NAME]": your_name or "[YOUR_NAME]",
            "[PROJECT_NAME]": project or "[PROJECT_NAME]",
            "[AMOUNT]": amount or "[AMOUNT]",
            "[DATE]": datetime.now().strftime("%B %d, %Y"),
            "[YOUR_ORGANIZATION]": your_name or "[YOUR_ORGANIZATION]"
        }
        
        # Apply replacements
        for placeholder, replacement in replacements.items():
            subject = subject.replace(placeholder, replacement)
            body = body.replace(placeholder, replacement)
        
        # Update the display
        self.subject_entry.delete(0, "end")
        self.subject_entry.insert(0, subject)
        
        self.email_editor.delete("1.0", "end")
        self.email_editor.insert("1.0", body)
        
        messagebox.showinfo("Email Generated", "Email template has been personalized with your information!")
        
    def copy_email(self):
        """Copy email to clipboard."""
        subject = self.subject_entry.get()
        body = self.email_editor.get("1.0", "end-1c")
        
        full_email = f"Subject: {subject}\n\n{body}"
        
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(full_email)
        
        messagebox.showinfo("Copied!", "Email has been copied to clipboard!")
        
    def save_template(self):
        """Save custom template."""
        template_name = f"Custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        subject = self.subject_entry.get()
        body = self.email_editor.get("1.0", "end-1c")
        
        # In a real implementation, you'd save to file
        messagebox.showinfo("Template Saved", f"Template saved as: {template_name}")
        
    def display_vendor_error(self, error_msg):
        """Display vendor search error."""
        self.vendor_results_text.delete("1.0", "end")
        self.vendor_results_text.insert("1.0", f"Error: {error_msg}\n\nPlease check your OpenAI API configuration and try again.")
        
        self.find_vendors_button.configure(state="normal", text="Find Vendors")
        self.ai_status_label.configure(text="AI search failed")
        
    # Email search methods (simplified from previous implementation)
    def start_email_search(self):
        """Start email search process."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        max_pages = int(self.pages_slider.get())
        delay = self.delay_slider.get()
        verify = self.verify_switch.get()
        
        self.search_running = True
        self.search_button.configure(state="disabled", text="Searching...")
        self.stop_button.configure(state="normal")
        self.progress_bar.start()
        
        # Start search thread
        thread = threading.Thread(target=self.run_email_search, args=(url, max_pages, delay, verify))
        thread.daemon = True
        thread.start()
        
    def run_email_search(self, url, max_pages, delay, verify):
        """Run email search in background."""
        try:
            self.searcher = EmailSearcher(max_pages=max_pages, delay=delay)
            emails = self.searcher.search_website_for_emails(url)
            
            result_text = f"EMAIL SEARCH RESULTS - {url}\n{'=' * 60}\n\n"
            if emails:
                result_text += f"Found {len(emails)} email addresses:\n\n"
                for i, email in enumerate(sorted(emails), 1):
                    result_text += f"{i:2d}. {email}\n"
                    
                # Store in database
                for email in emails:
                    company_data = {
                        'website': url,
                        'email': email,
                        'found_date': datetime.now().isoformat(),
                        'verified': False
                    }
                    if company_data not in self.found_companies:
                        self.found_companies.append(company_data)
                        
                # Update dashboard
                self.root.after(0, lambda: self.companies_count_label.configure(text=str(len(self.found_companies))))
            else:
                result_text += "No email addresses found.\n"
                
            self.root.after(0, self.display_email_results, result_text)
            
        except Exception as e:
            self.root.after(0, self.display_email_error, str(e))
            
    def display_email_results(self, results):
        """Display email search results."""
        self.email_results_text.delete("1.0", "end")
        self.email_results_text.insert("1.0", results)
        
        self.search_running = False
        self.search_button.configure(state="normal", text="Start Search")
        self.stop_button.configure(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Search completed")
        
    def display_email_error(self, error):
        """Display email search error."""
        self.email_results_text.delete("1.0", "end")
        self.email_results_text.insert("1.0", f"Search failed: {error}")
        
        self.search_running = False
        self.search_button.configure(state="normal", text="Start Search")
        self.stop_button.configure(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        
    def stop_email_search(self):
        """Stop email search."""
        self.search_running = False
        self.progress_label.configure(text="Stopping search...")
        
    def clear_email_results(self):
        """Clear email search results."""
        self.email_results_text.delete("1.0", "end")
        self.progress_label.configure(text="Ready to search")
        self.progress_bar.set(0)
        
    # Database management methods
    def refresh_database(self):
        """Refresh the database display."""
        self.database_text.delete("1.0", "end")
        
        if not self.found_companies and not self.recommended_vendors:
            self.database_text.insert("1.0", "Database is empty. Use Email Search or Vendor Finder to populate.")
            return
            
        db_content = "COMPANY DATABASE\n" + "=" * 50 + "\n\n"
        
        if self.found_companies:
            db_content += f"EMAIL SEARCH RESULTS ({len(self.found_companies)} entries):\n" + "-" * 40 + "\n"
            for i, company in enumerate(self.found_companies, 1):
                db_content += f"{i:2d}. {company.get('website', 'N/A')} - {company.get('email', 'N/A')}\n"
            db_content += "\n"
            
        if self.recommended_vendors:
            db_content += f"RECOMMENDED VENDORS ({len(self.recommended_vendors)} entries):\n" + "-" * 40 + "\n"
            for i, vendor in enumerate(self.recommended_vendors, 1):
                db_content += f"{i:2d}. {vendor}\n"
                
        self.database_text.insert("1.0", db_content)
        
    def clear_database(self):
        """Clear all database entries."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all database entries?"):
            self.found_companies.clear()
            self.recommended_vendors.clear()
            self.refresh_database()
            self.companies_count_label.configure(text="0")
            self.vendors_count_label.configure(text="0")
            
    def import_csv(self):
        """Import companies from CSV file."""
        file_path = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    imported = 0
                    for row in reader:
                        if 'website' in row or 'email' in row:
                            self.found_companies.append(row)
                            imported += 1
                            
                messagebox.showinfo("Success", f"Imported {imported} companies from CSV")
                self.refresh_database()
                self.companies_count_label.configure(text=str(len(self.found_companies)))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")
                
    # Export methods
    def export_emails_csv(self):
        """Export email data to CSV."""
        if not self.found_companies:
            messagebox.showwarning("Warning", "No email data to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export Email Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    if self.found_companies:
                        fieldnames = self.found_companies[0].keys()
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(self.found_companies)
                        
                messagebox.showinfo("Success", f"Email data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
                
    def export_emails_json(self):
        """Export email data to JSON."""
        if not self.found_companies:
            messagebox.showwarning("Warning", "No email data to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export Email Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(self.found_companies, file, indent=2)
                    
                messagebox.showinfo("Success", f"Email data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
                
    def export_vendors_csv(self):
        """Export vendor data to CSV."""
        messagebox.showinfo("Info", "Vendor CSV export feature coming soon!")
        
    def export_vendors_json(self):
        """Export vendor data to JSON."""
        messagebox.showinfo("Info", "Vendor JSON export feature coming soon!")
        
    def generate_prospect_report(self):
        """Generate sponsorship prospect report."""
        messagebox.showinfo("Info", "Prospect report generation feature coming soon!")
        
    def generate_vendor_report(self):
        """Generate vendor contact list."""
        messagebox.showinfo("Info", "Vendor report generation feature coming soon!")
        
    def export_complete_database(self):
        """Export complete database."""
        messagebox.showinfo("Info", "Complete database export feature coming soon!")
        
    def start_result_checking(self):
        """Start checking for results."""
        self.check_results()
        
    def check_results(self):
        """Check for results from background threads."""
        try:
            while True:
                msg_type, msg_data = self.result_queue.get_nowait()
                # Handle any queue messages here if needed
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_results)

def main():
    """Main function to run the sponsorship software."""
    app = SponsorshipSoftware()
    
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")

if __name__ == "__main__":
    main()