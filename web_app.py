"""
Indian Scam Center - Web Application
Streamlit-based web interface for sponsorship and email search
"""

import streamlit as st
import queue
import threading
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import json
import csv
import io
import os
import time
import base64
import dns.resolver
import smtplib
from urllib.parse import urljoin, urlparse
from database import SponsorDatabase

# Inlined EmailSearcher (previously in main_windows.py) for single-file deployment
class EmailSearcher:
    def __init__(self, max_pages=3, delay=0.5, scraper_api_key=None, use_scraper_for_sites=False):
        self.max_pages = max_pages
        self.delay = delay
        self.scraper_api_key = scraper_api_key
        self.use_scraper_for_sites = use_scraper_for_sites
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session.verify = False  # allow sites with cert issues
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]
        self.contact_pages = [
            '/contact','/contact-us','/contact.html','/contact.php',
            '/about','/about-us','/about.html','/about.php',
            '/team','/staff','/people','/leadership',
            '/support','/help','/customer-service',
            '/legal','/privacy','/terms',
            '/careers','/jobs','/employment'
        ]

    def get_page_content(self, url: str, force_scraper=False):
        try:
            # Only use ScraperAPI if explicitly forced or enabled for sites
            if self.scraper_api_key and (force_scraper or self.use_scraper_for_sites):
                scraper_url = f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={url}"
                resp = requests.get(scraper_url, timeout=30, verify=False)
            else:
                resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return None

    def extract_emails_from_text(self, text: str):
        emails = set()
        for pattern in self.email_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                email = match.group(1) if 'mailto:' in pattern else match.group(0)
                email = email.lower().strip()
                if self.is_valid_email_format(email):
                    emails.add(email)
        return emails

    def is_valid_email_format(self, email: str):
        false_positives = {
            'example@example.com','test@test.com','admin@admin.com',
            'info@info.com','contact@contact.com','support@support.com',
            'noreply@noreply.com','donotreply@donotreply.com'
        }
        if email in false_positives: return False
        if any(ext in email for ext in ['.jpg','.png','.gif','.svg']): return False
        return '@' in email and '.' in email.split('@')[-1]

    def get_all_links(self, base_url: str, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        base_domain = urlparse(base_url).netloc
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith(('mailto:', 'javascript:', '#')):
                continue
            full = urljoin(base_url, href)
            if urlparse(full).netloc == base_domain:
                links.add(full.split('#')[0])
        return links

    def analyze_structure(self, base_url: str):
        content = self.get_page_content(base_url)
        if not content:
            return []
        all_links = self.get_all_links(base_url, content)
        categories = {
            'contact':[], 'about':[], 'team':[], 'support':[], 'other':[]
        }
        for link in all_links:
            L = link.lower()
            if any(k in L for k in ['contact','reach','touch']): categories['contact'].append(link)
            elif any(k in L for k in ['about','company','who','story']): categories['about'].append(link)
            elif any(k in L for k in ['team','staff','people','leadership','management']): categories['team'].append(link)
            elif any(k in L for k in ['support','help','service','customer']): categories['support'].append(link)
            else: categories['other'].append(link)
        ordered = []
        ordered += categories['contact'][:3]
        ordered += categories['about'][:2]
        ordered += categories['team'][:2]
        ordered += categories['support'][:2]
        ordered += categories['other'][:3]
        if base_url not in ordered:
            ordered.insert(0, base_url)
        return ordered

    def search_website_for_emails(self, base_url: str):
        pages = self.analyze_structure(base_url)
        pages = pages[:self.max_pages]
        found = set()
        for i, url in enumerate(pages, 1):
            content = self.get_page_content(url)
            if not content:
                continue
            page_emails = self.extract_emails_from_text(content)
            found.update(page_emails)
            # Early exit if we found 3+ emails to save API calls
            if len(found) >= 3:
                break
            time.sleep(self.delay)
        return found

    def verify_email_domain(self, email: str):
        domain = email.split('@')[-1]
        try:
            mx = dns.resolver.resolve(domain, 'MX')
            return len(mx) > 0
        except Exception:
            return False

# OpenAI API Configuration - Use environment variable for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"

# ScraperAPI Configuration - Use environment variable for security  
# Get your free API key at https://scraperapi.com (1000 requests/month free)
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")

# Debug: Show what keys are loaded (only for local testing - remove in production)
if SCRAPER_API_KEY:
    print(f"✅ ScraperAPI Key loaded: {SCRAPER_API_KEY[:10]}...{SCRAPER_API_KEY[-4:]}")
else:
    print("❌ No ScraperAPI key found in environment")
    
if OPENAI_API_KEY:
    print(f"✅ OpenAI Key loaded: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
else:
    print("❌ No OpenAI key found in environment")

# Page configuration
st.set_page_config(
    page_title="UBCO Aerospace - Sponsor Center",
    page_icon="✈Sheesh",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load logo (optional)
def get_base64_image(image_path: str):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

logo_base64 = get_base64_image("ubco_aerospace_logo.jpg")

# Modern CSS with UBCO branding - v2.0
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global styling - Force override */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1d3a 100%) !important;
    }
    
    /* Sidebar styling - Force visible */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141824 0%, #1e2235 100%) !important;
        border-right: 1px solid rgba(59, 142, 208, 0.2) !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e8eaed !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* Main header with logo */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b8ed0 0%, #5ba3e0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-size: 0.95rem;
        color: #9ca3af;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* Stat boxes with modern cards */
    .stat-box {
        background: linear-gradient(135deg, #1e2235 0%, #252a42 100%);
        padding: 1.25rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(59, 142, 208, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59, 142, 208, 0.3);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b8ed0 0%, #60b0ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Modern button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3b8ed0 0%, #2d7ab8 100%);
        color: white;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        box-shadow: 0 4px 16px rgba(59, 142, 208, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2d7ab8 0%, #1f5c8c 100%);
        box-shadow: 0 6px 24px rgba(59, 142, 208, 0.6);
        transform: translateY(-2px);
    }
    
    /* Text input styling */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        background-color: #1e2235;
        color: #e8eaed;
        border: 2px solid rgba(59, 142, 208, 0.3);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #3b8ed0;
        box-shadow: 0 0 0 3px rgba(59, 142, 208, 0.2);
    }
    
    /* Labels with better contrast */
    label {
        color: #e8eaed !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: rgba(59, 142, 208, 0.1);
        border-left: 4px solid #3b8ed0;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1rem;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
        color: #86efac;
    }
    
    /* Tables */
    .stDataFrame {
        font-size: 1rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1e2235;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #3b8ed0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }
    
    /* Page titles */
    h1, h2, h3 {
        color: #e8eaed !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 2rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-size: 1.2rem !important;
    }
    
    /* Paragraphs */
    p {
        font-size: 0.95rem;
        color: #d1d5db;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)



# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection (cached for performance)."""
    return SponsorDatabase()

db = init_database()

# Initialize session state
if 'found_companies' not in st.session_state:
    st.session_state.found_companies = []
if 'recommended_vendors' not in st.session_state:
    st.session_state.recommended_vendors = []
if 'contact_list' not in st.session_state:
    st.session_state.contact_list = []  # Store companies with emails for email center
if 'saved_email_templates' not in st.session_state:
    st.session_state.saved_email_templates = []  # Store custom templates
if 'drafted_emails' not in st.session_state:
    st.session_state.drafted_emails = []  # Store emails created in session
if 'page_switch' not in st.session_state:
    st.session_state.page_switch = None
if 'vendor_search_results' not in st.session_state:
    st.session_state.vendor_search_results = []  # Persist vendor search results
if 'vendor_search_part' not in st.session_state:
    st.session_state.vendor_search_part = ""  # Remember last search term
if 'email_search_results' not in st.session_state:
    st.session_state.email_search_results = {}  # Persist email search results by URL
if 'openai_client' not in st.session_state:
    try:
        if OPENAI_API_KEY and OPENAI_API_KEY.strip():
            st.session_state.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            st.session_state.openai_enabled = True
        else:
            st.session_state.openai_client = None
            st.session_state.openai_enabled = False
    except Exception:
        st.session_state.openai_client = None
        st.session_state.openai_enabled = False

# Sidebar with UBCO branding
if logo_base64:
    st.sidebar.markdown(f"""
<div style="text-align: center; margin-bottom: 1.5rem; padding: 1rem; border-bottom: 2px solid rgba(59, 142, 208, 0.2);">
    <img src="data:image/jpeg;base64,{logo_base64}" alt="UBCO Aerospace" style="max-width:200px; margin-bottom:0.5rem;" />
</div>
""", unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 1.5rem; padding: 1rem; border-bottom: 2px solid rgba(59, 142, 208, 0.2);">
    <h2 style="color: #3b8ed0; margin: 0; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.1em;">UBCO AEROSPACE</h2>
</div>
""", unsafe_allow_html=True)

# Handle page switching from dashboard
if st.session_state.page_switch:
    page = st.session_state.page_switch
    st.session_state.page_switch = None
else:
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Email Search", "Real Sponsors", 
         "Vendor Search", "Email Center", "Email Templates", "Company Database", "Export Tools"],
        label_visibility="collapsed"
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### Status")
if SCRAPER_API_KEY:
    st.sidebar.success("ScraperAPI: ACTIVE")
else:
    st.sidebar.warning("ScraperAPI: Not Configured")

if st.session_state.openai_enabled:
    st.sidebar.success("AI Assistant: Connected")
else:
    st.sidebar.info("AI Assistant: Optional")

# Get database statistics
db_stats = db.get_statistics()

st.sidebar.markdown("---")
st.sidebar.markdown("### Statistics")
st.sidebar.metric("Total Companies", db_stats['total_companies'])
st.sidebar.metric("Sponsors", db_stats['total_sponsors'])
st.sidebar.metric("Vendors", db_stats['total_vendors'])
st.sidebar.metric("Contacts", db_stats['total_contacts'])
st.sidebar.metric("Drafted Emails", db_stats['drafted_emails'])

# Add ScraperAPI test button
if SCRAPER_API_KEY:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ScraperAPI Test")
    if st.sidebar.button("🧪 Test ScraperAPI", help="Test if ScraperAPI is working"):
        with st.sidebar.status("Testing ScraperAPI...", expanded=True) as status:
            try:
                import requests
                import urllib.parse
                
                st.write("🔍 Testing Google search...")
                test_url = "https://www.google.com/search?q=test"
                api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(test_url)}"
                
                response = requests.get(api_url, timeout=15)
                
                if response.status_code == 200:
                    st.write("✅ Status: 200 OK")
                    st.write(f"📦 Response size: {len(response.content)} bytes")
                    
                    # Check if it's actual Google HTML
                    content = response.text.lower()
                    if 'google' in content or 'search' in content:
                        st.write("✅ Google HTML detected")
                        status.update(label="✅ ScraperAPI Working!", state="complete", expanded=False)
                        st.sidebar.success("ScraperAPI is working correctly!")
                    else:
                        st.write("⚠️ Unexpected response content")
                        status.update(label="⚠️ Check Response", state="error", expanded=True)
                elif response.status_code == 401:
                    st.write("❌ Invalid API Key")
                    status.update(label="❌ Invalid Key", state="error", expanded=True)
                elif response.status_code == 403:
                    st.write("❌ Forbidden - Check account")
                    status.update(label="❌ Forbidden", state="error", expanded=True)
                else:
                    st.write(f"❌ Status: {response.status_code}")
                    status.update(label=f"❌ Error {response.status_code}", state="error", expanded=True)
                    
            except requests.exceptions.Timeout:
                st.write("❌ Request timeout (15s)")
                status.update(label="❌ Timeout", state="error", expanded=True)
            except Exception as e:
                st.write(f"❌ Error: {str(e)}")
                status.update(label="❌ Test Failed", state="error", expanded=True)

# Main Content
if page == "Dashboard":
    st.markdown('<h1 style="text-align: center; font-size: 1.8rem; margin-bottom: 1.5rem; font-weight: 700; color: #e8eaed;">SPONSOR DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Key stats - only show the 3 most important metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{db_stats['total_companies']}</div>
            <div class="stat-label">Total Companies</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{db_stats['total_contacts']}</div>
            <div class="stat-label">Contact Emails</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        reply_rate = f"{int((db_stats['replied_emails'] / db_stats['sent_emails'] * 100)) if db_stats['sent_emails'] > 0 else 0}%"
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{reply_rate}</div>
            <div class="stat-label">Reply Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Email Search", use_container_width=True, key="dash_email"):
            st.session_state.page_switch = "Email Search"
            st.rerun()
        if st.button("View Database", use_container_width=True, key="dash_db"):
            st.session_state.page_switch = "Company Database"
            st.rerun()
    with col2:
        if st.button("Find Vendors", use_container_width=True, key="dash_vendors"):
            st.session_state.page_switch = "Vendor Search"
            st.rerun()
        if st.button("Email Center", use_container_width=True, key="dash_email_center"):
            st.session_state.page_switch = "Email Center"
            st.rerun()

elif page == "Email Search":
    st.markdown('<p class="main-header">Company Email Search</p>', unsafe_allow_html=True)
    
    # Input section in a frame
    with st.container():
        st.markdown("### Website URL")
        url = st.text_input("Enter website URL", placeholder="https://example.com", label_visibility="collapsed")
        
        st.markdown("### Search Settings")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Max Pages**")
            max_pages = st.slider("Max Pages to search", 1, 10, 3, label_visibility="collapsed")
            st.caption(f"Pages: {max_pages} (fewer = faster & cheaper)")
        with col2:
            st.markdown("**Delay (seconds)**")
            delay = st.slider("Delay between requests", 0.3, 2.0, 0.5, 0.1, label_visibility="collapsed")
            st.caption(f"Delay: {delay}s")
        with col3:
            st.markdown("**Options**")
            use_scraper = st.checkbox("Use ScraperAPI", value=False, help="Use only if direct access fails")
            verify = st.checkbox("Verify Emails", value=False, help="Slower but more accurate")
    
    # Control buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_btn = st.button("Start Search", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("Clear Results", use_container_width=True)
    with col3:
        pass
    
    st.markdown("---")
    
    # Results section
    if clear_btn:
        if 'search_results' in st.session_state:
            del st.session_state.search_results
        st.success("Results cleared!")
    
    if search_btn:
        if not url:
            st.error("Please enter a website URL")
        else:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            st.warning("Search in progress - DO NOT switch pages or the search will be cancelled!")
            with st.spinner(f"Searching {url} for email addresses..."):
                try:
                    # Only use ScraperAPI if explicitly requested
                    api_key = SCRAPER_API_KEY if use_scraper else None
                    searcher = EmailSearcher(
                        max_pages=max_pages, 
                        delay=delay, 
                        scraper_api_key=api_key,
                        use_scraper_for_sites=use_scraper
                    )
                    
                    if use_scraper and SCRAPER_API_KEY:
                        st.info("🔧 Using ScraperAPI (costs 1-5 credits per page)")
                    elif use_scraper and not SCRAPER_API_KEY:
                        st.warning("⚠️ ScraperAPI enabled but no API key found")
                    
                    emails = searcher.search_website_for_emails(url)
                    
                    if emails:
                        st.success(f"Found {len(emails)} email addresses!")
                        
                        # Store in session state with URL for persistence
                        st.session_state.search_results = emails
                        st.session_state.email_search_results[url] = {
                            'emails': list(emails),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        for email in emails:
                            if email not in st.session_state.found_companies:
                                st.session_state.found_companies.append(email)
                        
                        # Display results in text area
                        st.markdown("### Search Results")
                        result_text = f"EMAIL SEARCH RESULTS - {url}\n{'=' * 60}\n\n"
                        result_text += f"Found {len(emails)} email addresses:\n\n"
                        for i, email in enumerate(sorted(emails), 1):
                            result_text += f"{i:2d}. {email}\n"
                        result_text += f"\n{'=' * 60}\n"
                        result_text += f"Search completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        st.text_area("Results", result_text, height=400, label_visibility="collapsed")
                        
                        # Download button
                        csv_data = "\n".join(sorted(emails))
                        st.download_button(
                            label="Download Emails as CSV",
                            data=csv_data,
                            file_name=f"emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("No emails found on this website")
                        st.info("""
**Possible reasons:**
• Website blocking automated requests
• Emails loaded with JavaScript  
• No contact information available
• Try a different page (e.g., /contact or /about)
                        """)
                        
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
    
    # Display previous results if they exist
    if st.session_state.email_search_results:
        st.markdown("---")
        st.markdown("### Previous Email Searches")
        
        for url, data in st.session_state.email_search_results.items():
            with st.expander(f"{url} - {len(data['emails'])} emails found ({data['timestamp']})"):
                result_text = f"Found {len(data['emails'])} email addresses:\n\n"
                for i, email in enumerate(sorted(data['emails']), 1):
                    result_text += f"{i:2d}. {email}\n"
                st.text_area("", result_text, height=200, label_visibility="collapsed", key=f"email_result_{url}")
                
                csv_data = "\n".join(sorted(data['emails']))
                st.download_button(
                    label="Download",
                    data=csv_data,
                    file_name=f"emails_{url.replace('https://', '').replace('http://', '').split('/')[0]}.csv",
                    mime="text/csv",
                    key=f"download_{url}"
                )

elif page == "Real Sponsors":
    st.markdown('<p class="main-header">Real Sponsor Finder</p>', unsafe_allow_html=True)
    
    # Input section
    project = st.text_area("What project or part needs sponsorship?", 
                          placeholder="e.g., Flight Computer, Rocket Motors, 3D Printer Filament")
    
    col1, col2 = st.columns(2)
    with col1:
        industry = st.text_input("Industry/Category (optional)", 
                                placeholder="e.g., Avionics, Propulsion, Recovery systems")
    with col2:
        canadian_only = st.checkbox("Canadian companies only", value=True)
        include_contact = st.checkbox("Extract contact emails", value=True)
    
    if st.button("Find Real Sponsors", type="primary", use_container_width=True):
        if not project:
            st.error("Please describe your project or part")
        else:
            st.warning("⚠️ Search in progress - DO NOT switch pages or the search will be cancelled!")
            with st.spinner("Searching for real sponsors with actual contact info..."):
                try:
                    # Build search query
                    location = "Canada" if canadian_only else "North America"
                    industry_part = f"{industry} " if industry else ""
                    
                    # Build multiple search URLs for better results
                    base_queries = [
                        f"{project} {industry_part}companies {location}",
                        f"{project} {industry_part}manufacturers {location}",
                        f"{project} {industry_part}suppliers {location}"
                    ]
                    
                    st.info(f"Searching for: {project} {industry_part}in {location}")
                    
                    # Show ScraperAPI status
                    if SCRAPER_API_KEY:
                        st.success("🔧 Using ScraperAPI to bypass blocking")
                    else:
                        st.warning("⚠️ No ScraperAPI - may get blocked by search engines")
                    
                    # Initialize searcher with faster settings
                    searcher = EmailSearcher(max_pages=2, delay=0.5, scraper_api_key=SCRAPER_API_KEY)
                    
                    all_company_urls = set()
                    
                    # Create progress indicators
                    progress_text = st.empty()
                    search_status = st.empty()
                    
                    # Try multiple search engines with ScraperAPI
                    search_engines = [
                        ("Google", f"https://www.google.com/search?q={{}}&num=20"),
                        ("Bing", f"https://www.bing.com/search?q={{}}"),
                        ("DuckDuckGo", f"https://html.duckduckgo.com/html/?q={{}}")
                    ]
                    
                    for engine_name, engine_url_template in search_engines:
                        progress_text.info(f"Searching {engine_name}...")
                        
                        for query in base_queries[:2]:  # Use first 2 queries
                            search_url = engine_url_template.format(query.replace(' ', '+'))
                            
                            search_status.text(f"Query: {query}")
                            
                            # ALWAYS use ScraperAPI for Google and Bing (they block direct requests)
                            if SCRAPER_API_KEY:
                                import urllib.parse
                                import requests
                                
                                # Encode URL properly for ScraperAPI
                                encoded_url = urllib.parse.quote(search_url, safe='')
                                
                                # Add render=false for faster results (HTML only, no JS rendering)
                                scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={encoded_url}"
                                
                                try:
                                    search_status.text(f"Requesting {engine_name} via ScraperAPI...")
                                    st.caption(f"Target: {search_url[:80]}...")
                                    
                                    response = requests.get(scraper_url, timeout=30)
                                    
                                    if response.status_code == 200:
                                        search_content = response.text
                                        search_status.success(f"SUCCESS: Got {len(search_content):,} bytes from {engine_name}")
                                    else:
                                        error_msg = f"Status {response.status_code}"
                                        if response.text:
                                            error_msg += f": {response.text[:100]}"
                                        search_status.error(f"ERROR: {engine_name} - {error_msg}")
                                        st.warning(f"ScraperAPI returned error. Check your API key and credits.")
                                        search_content = None
                                        
                                except requests.exceptions.Timeout:
                                    search_status.error(f"TIMEOUT: {engine_name} (>30s)")
                                    search_content = None
                                except Exception as e:
                                    search_status.error(f"ERROR: {engine_name} - {str(e)[:80]}")
                                    st.error(f"Request failed: {type(e).__name__}: {str(e)}")
                                    search_content = None
                            else:
                                # No ScraperAPI - Google and Bing will be blocked
                                search_status.warning(f"SKIPPED: {engine_name} (requires ScraperAPI)")
                                search_content = None
                        
                            if search_content:
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(search_content, 'html.parser')
                                
                                search_status.text(f"🔍 Parsing {engine_name} results...")
                                
                                # Debug: Show snippet of received HTML
                                with st.expander(f"Debug: {engine_name} HTML preview"):
                                    st.code(search_content[:1000], language="html")
                                
                                # Extract URLs based on search engine
                                skip_domains = ['duckduckgo', 'google', 'bing', 'yahoo', 'facebook', 'twitter', 
                                               'linkedin', 'youtube', 'wikipedia', 'reddit', 'amazon', 'instagram']
                                
                                found_in_iteration = 0
                                
                                # DuckDuckGo Lite results - much simpler structure
                                # Look for all links in result-link class
                                for link in soup.find_all('a', class_='result-link'):
                                    url = link.get('href', '')
                                    if url.startswith('http'):
                                        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                                        if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                            all_company_urls.add(f"https://{domain}")
                                            found_in_iteration += 1
                                
                                # Alternative: look for span.link-text parent links
                                if found_in_iteration == 0:
                                    for span in soup.find_all('span', class_='link-text'):
                                        parent_link = span.find_parent('a')
                                        if parent_link:
                                            url = parent_link.get('href', '')
                                            if url.startswith('http'):
                                                domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                                                if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                                    all_company_urls.add(f"https://{domain}")
                                                    found_in_iteration += 1
                                
                                # Aggressive fallback
                                for link in soup.find_all('a', href=True):
                                    href = link['href']
                                    if href.startswith('http'):
                                        domain = href.replace('https://', '').replace('http://', '').replace('www.', '').split('?')[0].split('/')[0]
                                        if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                            all_company_urls.add(f"https://{domain}")
                                            found_in_iteration += 1
                                
                                if found_in_iteration > 0:
                                    search_status.success(f"FOUND: {found_in_iteration} companies from {engine_name} (Total: {len(all_company_urls)})")
                                else:
                                    st.warning(f"No results parsed from {engine_name} - check if page structure changed")
                                    search_status.warning(f"NO RESULTS from {engine_name}")
                                
                                # Break if we found enough results
                                if len(all_company_urls) >= 10:
                                    progress_text.success(f"✅ Found {len(all_company_urls)} companies! Stopping search.")
                                    break
                            else:
                                search_status.warning(f"⚠️ No response from {engine_name}")
                        
                        # Break outer loop if we have enough
                        if len(all_company_urls) >= 10:
                            break
                    
                    progress_text.empty()
                    search_status.empty()
                    
                    # If still no results, show clear message
                    if not all_company_urls:
                        st.error("Unable to find companies through search engines.")
                        st.info("""
**Try these options:**
1. Add your ScraperAPI key in the code (SCRAPER_API_KEY)
2. Be more specific with project/industry names
3. Use the Email Search tab to search specific company websites directly
4. Contact companies you already know about
                        """)
                    
                    # Remove duplicates, clean URLs, and limit
                    # Deduplicate by domain to avoid showing same site multiple times
                    seen_domains = set()
                    unique_company_urls = []
                    
                    for url in all_company_urls:
                        # Extract domain for deduplication
                        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                        
                        if domain not in seen_domains:
                            seen_domains.add(domain)
                            unique_company_urls.append(url)
                    
                    company_urls = unique_company_urls[:8]
                    
                    if not company_urls:
                        st.error("No company websites found. Try:")
                        st.markdown("""
                        - Be more specific with your project description
                        - Try different industry keywords
                        - Use the Email Search tab to search specific company websites manually
                        """)
                    else:
                        st.success(f"Found {len(company_urls)} potential sponsor websites")
                        
                        # Store results in structured format
                        company_results = []
                        
                        # Process each company URL with progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, url in enumerate(company_urls, 1):
                            progress_bar.progress(i / len(company_urls))
                            status_text.text(f"Processing {i}/{len(company_urls)}: {url}")
                            
                            company_data = {
                                'url': url,
                                'name': url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0],
                                'emails': [],
                                'relevance_score': 0
                            }
                            
                            # Calculate relevance score based on URL content
                            url_lower = url.lower()
                            if industry:
                                industry_words = industry.lower().split()
                                company_data['relevance_score'] += sum(1 for word in industry_words if word in url_lower) * 2
                            
                            project_words = project.lower().split()[:3]
                            company_data['relevance_score'] += sum(1 for word in project_words if word in url_lower)
                            
                            if include_contact:
                                try:
                                    emails = searcher.search_website_for_emails(url)
                                    if emails:
                                        company_data['emails'] = list(emails)
                                        # Boost score for companies with contact info
                                        company_data['relevance_score'] += 5
                                except:
                                    pass
                            
                            company_results.append(company_data)
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Sort by relevance score (highest first)
                        company_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                        
                        # Store results in session state so buttons work
                        st.session_state.last_sponsor_search = company_results
                        
                        # Display results in compact format
                        st.markdown("---")
                        st.markdown("### Search Results Summary")
                        st.markdown(f"**Project:** {project} | **Location:** {location} | **Found:** {len(company_urls)} companies")
                        
                        # Display results in a table
                        st.markdown("### Company Results")
                        
                        # Create columns for table header
                        col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
                        with col1:
                            st.markdown("**#**")
                        with col2:
                            st.markdown("**Company**")
                        with col3:
                            st.markdown("**Emails Found**")
                        with col4:
                            st.markdown("**Action**")
                        
                        st.markdown("---")
                        
                        # Display each company in compact row
                        for i, company in enumerate(company_results, 1):
                            col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
                            
                            with col1:
                                st.text(f"{i}")
                            
                            with col2:
                                st.markdown(f"[{company['name']}]({company['url']})")
                            
                            with col3:
                                if company['emails']:
                                    emails_display = ', '.join(company['emails'][:2])
                                    if len(company['emails']) > 2:
                                        emails_display += f" +{len(company['emails'])-2} more"
                                    st.text(emails_display)
                                else:
                                    st.text("No emails")
                            
                            with col4:
                                if st.button("+", key=f"add_sponsor_{i}", help="Add to database"):
                                    # Save to database
                                    company_id = db.add_company(
                                        name=company['name'],
                                        url=company['url'],
                                        company_type='sponsor',
                                        industry=industry if industry else None,
                                        project_part=project,
                                        relevance_score=company.get('relevance_score', 0)
                                    )
                                    
                                    # Add contacts
                                    if company['emails']:
                                        for email in company['emails']:
                                            db.add_contact(company_id, email)
                                    
                                    # Also add to session state for compatibility
                                    contact_entry = {
                                        'name': company['name'],
                                        'url': company['url'],
                                        'emails': company['emails'],
                                        'type': 'sponsor',
                                        'project': project
                                    }
                                    
                                    if not any(c['url'] == company['url'] for c in st.session_state.contact_list):
                                        st.session_state.contact_list.append(contact_entry)
                                    
                                    st.success(f"Added {company['name']} to database!")
                                    time.sleep(0.5)
                                    st.rerun()
                        
                        # Detailed results in expander
                        with st.expander("View Detailed Text Results"):
                            results_text = f"### SPONSOR SEARCH RESULTS\n"
                            results_text += f"**Project:** {project}\n"
                            results_text += f"**Industry:** {industry if industry else 'General'}\n"
                            results_text += f"**Location:** {location}\n\n"
                            
                            for i, company in enumerate(company_results, 1):
                                results_text += f"{i}. {company['url']}\n"
                                if company['emails']:
                                    results_text += f"   Emails: {', '.join(company['emails'])}\n"
                                results_text += "\n"
                            
                            st.text_area("Results", results_text, height=300)
                            
                            st.download_button(
                                label="Download Results",
                                data=results_text,
                                file_name=f"sponsors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        
                        # Store in session state
                        st.session_state.recommended_vendors.append({
                            'type': 'sponsor',
                            'project': project,
                            'results': results_text,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        # Download option
                        st.download_button(
                            label="Download Results",
                            data=results_text,
                            file_name=f"sponsors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
                    st.info("Try using the Email Search tab to search specific company websites directly.")
    
    # Display previous sponsor search results if available
    if 'last_sponsor_search' in st.session_state and st.session_state.last_sponsor_search:
        st.markdown("---")
        st.markdown("### Previous Sponsor Results")
        
        company_results = st.session_state.last_sponsor_search
        
        col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
        with col1:
            st.markdown("**#**")
        with col2:
            st.markdown("**Company**")
        with col3:
            st.markdown("**Emails Found**")
        with col4:
            st.markdown("**Action**")
        
        st.markdown("---")
        
        for i, company in enumerate(company_results, 1):
            col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
            
            with col1:
                st.text(f"{i}")
            
            with col2:
                st.markdown(f"[{company['name']}]({company['url']})")
            
            with col3:
                if company['emails']:
                    emails_display = ', '.join(company['emails'][:2])
                    if len(company['emails']) > 2:
                        emails_display += f" +{len(company['emails'])-2} more"
                    st.text(emails_display)
                else:
                    st.text("No emails")
            
            with col4:
                if st.button("+", key=f"add_prev_sponsor_{i}", help="Add to contact list"):
                    contact_entry = {
                        'name': company['name'],
                        'url': company['url'],
                        'emails': company['emails'],
                        'type': 'sponsor',
                        'project': company.get('project', 'N/A')
                    }
                    
                    if not any(c['url'] == company['url'] for c in st.session_state.contact_list):
                        st.session_state.contact_list.append(contact_entry)
                        st.success(f"Added {company['name']} to Email Center!")
                        time.sleep(1)  # Show message briefly

elif page == "Vendor Search":
    st.markdown('<p class="main-header">Specific Vendor & Parts Search</p>', unsafe_allow_html=True)
    
    # Show if there are saved results
    if st.session_state.vendor_search_results:
        st.info(f"💾 Previous search results for '{st.session_state.vendor_search_part}' are shown below. Run a new search to update.")
    
    # Input section
    part_name = st.text_input("Specific Part or Product Name", 
                             placeholder="e.g., TD3 recovery system, Arduino Uno, Carbon fiber sheets")
    
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox("Country/Region", ["Canada", "USA", "North America", "Global"])
    with col2:
        price_range = st.selectbox("Price Range", ["Any", "Under $100", "$100-$500", "$500-$1000", "Over $1000"])
    
    find_contact = st.checkbox("Extract supplier contact emails", value=True)
    
    if st.button("Search Vendors", type="primary", use_container_width=True):
        if not part_name:
            st.error("Please enter a specific part or product name")
        else:
            st.warning("⚠️ Search in progress - DO NOT switch pages or the search will be cancelled!")
            with st.spinner(f"Searching for real '{part_name}' vendors..."):
                try:
                    # Build search queries - use only the 2 most effective
                    location = country
                    base_queries = [
                        f"{part_name} supplier {location}",
                        f"{part_name} distributor {location}"
                    ]
                    
                    st.info(f"Searching for: {part_name} vendors in {location}")
                    
                    # Show ScraperAPI status
                    if SCRAPER_API_KEY:
                        st.success("🔧 Using DuckDuckGo (free) + Google via ScraperAPI for best results")
                    else:
                        st.info("🆓 Using DuckDuckGo only (free) - add ScraperAPI key for Google results too")
                    
                    # Initialize searcher - don't use ScraperAPI for individual sites
                    searcher = EmailSearcher(max_pages=2, delay=0.3, scraper_api_key=None, use_scraper_for_sites=False)
                    
                    # Track URLs with their source (DuckDuckGo or ScraperAPI)
                    all_vendor_urls = {}  # {url: source_engine}
                    
                    # Use DuckDuckGo + ScraperAPI Google concurrently for best results
                    search_engines = [
                        ("DuckDuckGo", f"https://lite.duckduckgo.com/lite/?q={{}}", False),  # Direct, free
                        ("Google", f"https://www.google.com/search?q={{}}&num=20", True)     # Via ScraperAPI
                    ]
                    
                    progress_text = st.empty()
                    search_status = st.empty()
                    
                    # Prepare all search requests
                    all_results = []
                    
                    for engine_name, engine_url_template, use_scraper in search_engines:
                        progress_text.info(f"🔍 Searching {engine_name}...")
                        
                        for query in base_queries:  # Use both queries
                            search_url = engine_url_template.format(query.replace(' ', '+'))
                            
                            search_status.text(f"Query: {query}")
                            
                            # Execute based on engine type
                            if use_scraper and SCRAPER_API_KEY:
                                # Use ScraperAPI for Google
                                import urllib.parse
                                import requests
                                
                                encoded_url = urllib.parse.quote(search_url, safe='')
                                scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={encoded_url}"
                                
                                try:
                                    search_status.text(f"🔧 {engine_name} via ScraperAPI...")
                                    response = requests.get(scraper_url, timeout=30)
                                    
                                    if response.status_code == 200:
                                        search_content = response.text
                                        search_status.success(f"✅ {engine_name}: {len(search_content):,} bytes")
                                    else:
                                        search_status.warning(f"⚠️ {engine_name} failed: {response.status_code}")
                                        search_content = None
                                except Exception as e:
                                    search_status.warning(f"⚠️ {engine_name} error: {str(e)[:50]}")
                                    search_content = None
                            elif not use_scraper:
                                # Direct access (DuckDuckGo)
                                try:
                                    search_status.text(f"🆓 {engine_name} direct...")
                                    response = requests.get(search_url, timeout=15)
                                    if response.status_code == 200:
                                        search_content = response.text
                                        search_status.success(f"✅ {engine_name}: {len(search_content):,} bytes (FREE)")
                                    else:
                                        search_content = None
                                except Exception:
                                    search_content = None
                            else:
                                search_status.info(f"⏭️ Skipping {engine_name} (no API key)")
                                search_content = None
                            
                            if search_content:
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(search_content, 'html.parser')
                                
                                search_status.text(f"🔍 Parsing {engine_name} results...")
                                
                                # Store debug info for later display
                                if 'debug_panels' not in locals():
                                    debug_panels = []
                                debug_panels.append({
                                    'engine': engine_name,
                                    'content': search_content[:1000]
                                })
                                
                                skip_domains = ['duckduckgo', 'google', 'bing', 'yahoo', 'facebook', 'twitter', 
                                               'linkedin', 'youtube', 'wikipedia', 'reddit', 'amazon', 'ebay', 'instagram']
                                
                                found_in_iteration = 0
                                
                                # Parse based on search engine type
                                if engine_name == "DuckDuckGo":
                                    # DuckDuckGo Lite results
                                    for link in soup.find_all('a', class_='result-link'):
                                        url = link.get('href', '')
                                        if url.startswith('http'):
                                            domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                                            if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                                vendor_url = f"https://{domain}"
                                                all_vendor_urls[vendor_url] = 'DuckDuckGo'
                                                found_in_iteration += 1
                                    
                                    # Alternative: span.link-text parent links
                                    if found_in_iteration == 0:
                                        for span in soup.find_all('span', class_='link-text'):
                                            parent_link = span.find_parent('a')
                                            if parent_link:
                                                url = parent_link.get('href', '')
                                                if url.startswith('http'):
                                                    domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                                                    if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                                        vendor_url = f"https://{domain}"
                                                        all_vendor_urls[vendor_url] = 'DuckDuckGo'
                                                        found_in_iteration += 1
                                
                                elif engine_name == "Google":
                                    # Google search results
                                    for div in soup.find_all('div', class_=['g', 'yuRUbf']):
                                        a_tag = div.find('a', href=True)
                                        if a_tag:
                                            url = a_tag['href']
                                            if url.startswith('http'):
                                                domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                                                if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                                    vendor_url = f"https://{domain}"
                                                    all_vendor_urls[vendor_url] = 'ScraperAPI'
                                                    found_in_iteration += 1
                                
                                # Aggressive fallback
                                for link in soup.find_all('a', href=True):
                                    href = link['href']
                                    if href.startswith('http'):
                                        domain = href.replace('https://', '').replace('http://', '').replace('www.', '').split('?')[0].split('/')[0]
                                        if not any(skip in domain.lower() for skip in skip_domains) and '.' in domain:
                                            vendor_url = f"https://{domain}"
                                            if vendor_url not in all_vendor_urls:  # Don't overwrite existing source
                                                all_vendor_urls[vendor_url] = engine_name
                                            found_in_iteration += 1
                                
                                if found_in_iteration > 0:
                                    search_status.success(f"✅ Found {found_in_iteration} companies from {engine_name}")
                                else:
                                    st.warning(f"⚠️ No results parsed from {engine_name} - check if page structure changed")
                                
                                if len(all_vendor_urls) >= 15:
                                    progress_text.success(f"🎉 Collected {len(all_vendor_urls)} vendors!")
                                    break
                        
                        if len(all_vendor_urls) >= 15:
                            break
                    
                    progress_text.empty()
                    search_status.empty()
                    
                    # If still no results after trying all engines
                    if not all_vendor_urls:
                        st.error("Unable to find vendors through search engines.")
                        st.info("""
**Try these options:**
1. Add your ScraperAPI key (get free at scraperapi.com)
2. Be more specific with part name and model number
3. Use Email Search tab to search specific vendor websites
4. Check the industry-specific distributors below
                        """)
                    
                    # Add well-known distributors based on category
                    common_distributors = {
                        "electronics": [
                            "https://www.digikey.com", "https://www.mouser.com", "https://www.newark.com",
                            "https://www.digikey.ca", "https://www.adafruit.com", "https://www.sparkfun.com"
                        ],
                        "industrial": [
                            "https://www.mcmaster.com", "https://www.grainger.com", "https://www.fastenal.com",
                            "https://www.mscdirect.com", "https://www.zoro.com"
                        ],
                        "aerospace": [
                            "https://www.aviall.com", "https://www.wencor.com", "https://www.flyingcolours.com"
                        ],
                        "robotics": [
                            "https://www.robotshop.com", "https://www.pololu.com", "https://www.servocity.com",
                            "https://www.trossenrobotics.com"
                        ],
                        "3d printing": [
                            "https://www.matterhackers.com", "https://www.prusa3d.com", "https://www.ultimaker.com",
                            "https://www.filaments.ca"
                        ],
                        "rocketry": [
                            "https://www.apogeerockets.com", "https://www.estesrockets.com", "https://www.madcowrocketry.com",
                            "https://www.wildmanrocketry.com"
                        ],
                        "composites": [
                            "https://www.cstsales.com", "https://www.fibreglast.com", "https://www.carbonfibergear.com"
                        ]
                    }
                    
                    # Smart category matching
                    part_lower = part_name.lower()
                    matched_categories = []
                    
                    # Electronics keywords
                    if any(word in part_lower for word in ["arduino", "sensor", "raspberry", "chip", "electronic", "circuit", 
                                                            "pcb", "microcontroller", "transistor", "resistor", "capacitor"]):
                        matched_categories.append("electronics")
                    
                    # Industrial/hardware keywords
                    if any(word in part_lower for word in ["bolt", "screw", "nut", "tool", "industrial", "fastener",
                                                            "bearing", "spring", "gear", "shaft"]):
                        matched_categories.append("industrial")
                    
                    # Aerospace keywords
                    if any(word in part_lower for word in ["aviation", "aerospace", "flight", "aircraft", "avionics"]):
                        matched_categories.append("aerospace")
                    
                    # Robotics keywords
                    if any(word in part_lower for word in ["robot", "servo", "motor", "stepper", "actuator", "gripper"]):
                        matched_categories.append("robotics")
                    
                    # 3D printing keywords
                    if any(word in part_lower for word in ["3d", "filament", "printer", "pla", "abs", "petg", "nozzle", "hotend"]):
                        matched_categories.append("3d printing")
                    
                    # Rocketry keywords
                    if any(word in part_lower for word in ["rocket", "motor", "propulsion", "recovery", "parachute", "ejection"]):
                        matched_categories.append("rocketry")
                    
                    # Composites keywords
                    if any(word in part_lower for word in ["carbon fiber", "fiberglass", "composite", "epoxy", "resin", "laminate"]):
                        matched_categories.append("composites")
                    
                    # Add distributors from matched categories
                    for category in matched_categories:
                        if category in common_distributors:
                            for dist_url in common_distributors[category][:3]:  # Top 3 per category
                                if dist_url not in all_vendor_urls:
                                    all_vendor_urls[dist_url] = 'Common'
                    
                    # Remove duplicates by domain and limit
                    seen_domains = set()
                    unique_vendor_data = []  # [(url, source), ...]
                    
                    for url, source in all_vendor_urls.items():
                        # Extract domain for deduplication
                        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                        
                        if domain not in seen_domains:
                            seen_domains.add(domain)
                            unique_vendor_data.append((url, source))
                    
                    vendor_data_list = unique_vendor_data[:10]
                    
                    if not vendor_data_list:
                        st.error("No vendor websites found. Try:")
                        st.markdown("""
                        - Be more specific with part name/model number
                        - Include manufacturer name if known
                        - Use Email Search tab to search specific vendor websites
                        """)
                    else:
                        st.success(f"Found {len(vendor_data_list)} potential vendor websites")
                        
                        # Store results in structured format
                        vendor_results = []
                        
                        # Process vendors with progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, (url, source) in enumerate(vendor_data_list, 1):
                            progress_bar.progress(i / len(vendor_data_list))
                            status_text.text(f"Processing {i}/{len(vendor_data_list)}: {url}")
                            
                            vendor_data = {
                                'url': url,
                                'name': url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0],
                                'emails': [],
                                'relevance_score': 0,
                                'source': source  # Track where this vendor was found
                            }
                            
                            # Calculate relevance score
                            url_lower = url.lower()
                            part_words = part_name.lower().split()[:3]
                            vendor_data['relevance_score'] += sum(1 for word in part_words if word in url_lower)
                            
                            # Boost common distributors
                            if any(dist in url_lower for dist in ['supply', 'distributor', 'direct', 'shop']):
                                vendor_data['relevance_score'] += 2
                            
                            if find_contact:
                                try:
                                    emails = searcher.search_website_for_emails(url)
                                    if emails:
                                        vendor_data['emails'] = list(emails)
                                        # Boost score for vendors with contact info
                                        vendor_data['relevance_score'] += 5
                                except:
                                    pass
                            
                            vendor_results.append(vendor_data)
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Sort by relevance score (highest first)
                        vendor_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                        
                        # Store results in session state so they persist across page switches
                        st.session_state.vendor_search_results = vendor_results
                        st.session_state.vendor_search_part = part_name
                        st.session_state.last_vendor_search = vendor_results  # Keep for compatibility
                        
                        # Display compact summary
                        st.markdown("---")
                        st.markdown("### Vendor Search Summary")
                        st.markdown(f"**Part:** {part_name} | **Region:** {location} | **Found:** {len(vendor_results)} vendors")
                        
                        # Create side-by-side layout for debug and results
                        col_debug, col_results = st.columns([1, 2])
                        
                        with col_debug:
                            st.markdown("#### Debug Info")
                            if 'debug_panels' in locals():
                                for panel in debug_panels:
                                    with st.expander(f"{panel['engine']} HTML"):
                                        st.code(panel['content'], language="html")
                            else:
                                st.info("No debug info available")
                        
                        with col_results:
                            st.markdown("#### Vendor Results")
                            
                            # Display results in compact table
                            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
                            with col1:
                                st.markdown("**#**")
                            with col2:
                                st.markdown("**Vendor**")
                            with col3:
                                st.markdown("**Contact**")
                            with col4:
                                st.markdown("**Source**")
                            with col5:
                                st.markdown("**Action**")
                            
                            st.markdown("---")
                            
                            for i, vendor in enumerate(vendor_results, 1):
                                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
                                
                                with col1:
                                    st.text(f"{i}")
                                
                                with col2:
                                    st.markdown(f"[{vendor['name']}]({vendor['url']})")
                                
                                with col3:
                                    if vendor['emails']:
                                        emails_display = ', '.join(vendor['emails'][:2])
                                        if len(vendor['emails']) > 2:
                                            emails_display += f" +{len(vendor['emails'])-2}"
                                        st.text(emails_display)
                                    else:
                                        st.text("Visit site")
                                
                                with col4:
                                    # Display source badge
                                    source = vendor.get('source', 'Unknown')
                                    if source == 'ScraperAPI':
                                        st.markdown("🔧 `ScraperAPI`")
                                    elif source == 'DuckDuckGo':
                                        st.markdown("🦆 `DuckDuckGo`")
                                    elif source == 'Common':
                                        st.markdown("📋 `Common`")
                                    else:
                                        st.text(source)
                                
                                with col5:
                                    if st.button("+", key=f"add_vendor_{i}", help="Add to database"):
                                        # Save to database
                                        company_id = db.add_company(
                                            name=vendor['name'],
                                            url=vendor['url'],
                                            company_type='vendor',
                                            project_part=part_name,
                                            relevance_score=vendor.get('relevance_score', 0)
                                        )
                                        
                                        # Add contacts
                                        if vendor['emails']:
                                            for email in vendor['emails']:
                                                db.add_contact(company_id, email)
                                        
                                        # Also add to session state for compatibility
                                        contact_entry = {
                                            'name': vendor['name'],
                                            'url': vendor['url'],
                                            'emails': vendor['emails'],
                                            'type': 'vendor',
                                            'part': part_name
                                        }
                                        
                                        if not any(c['url'] == vendor['url'] for c in st.session_state.contact_list):
                                            st.session_state.contact_list.append(contact_entry)
                                        
                                        st.success(f"Added {vendor['name']} to database!")
                                        time.sleep(0.5)
                                        st.rerun()
                        
                        # Detailed results in expander
                        with st.expander("View Detailed Results & Next Steps"):
                            results_text = f"### VENDOR SEARCH RESULTS\n"
                            results_text += f"**Part:** {part_name}\n"
                            results_text += f"**Region:** {location}\n\n"
                            
                            for i, vendor in enumerate(vendor_results, 1):
                                results_text += f"{i}. {vendor['url']}\n"
                                if vendor['emails']:
                                    results_text += f"   Contact: {', '.join(vendor['emails'])}\n"
                                results_text += "\n"
                            
                            results_text += "\nNEXT STEPS:\n"
                            results_text += "1. Visit vendor websites\n"
                            results_text += "2. Request quotes from multiple vendors\n"
                            results_text += "3. Compare prices and specifications\n"
                            
                            st.text_area("Results", results_text, height=300)
                            
                            st.download_button(
                                label="Download Vendor List",
                                data=results_text,
                                file_name=f"vendors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        
                        # Store in session state
                        st.session_state.recommended_vendors.append({
                            'type': 'vendor',
                            'part': part_name,
                            'results': results_text,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        # Download option
                        st.download_button(
                            label="Download Vendor List",
                            data=results_text,
                            file_name=f"vendors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
                    st.info("Try using Email Search tab to search specific vendor websites directly.")
    
    # Display previous vendor search results if available
    if 'last_vendor_search' in st.session_state and st.session_state.last_vendor_search:
        st.markdown("---")
        st.markdown("### Previous Vendor Results")
        
        vendor_results = st.session_state.last_vendor_search
        
        col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
        with col1:
            st.markdown("**#**")
        with col2:
            st.markdown("**Vendor**")
        with col3:
            st.markdown("**Contact**")
        with col4:
            st.markdown("**Action**")
        
        st.markdown("---")
        
        for i, vendor in enumerate(vendor_results, 1):
            col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
            
            with col1:
                st.text(f"{i}")
            
            with col2:
                st.markdown(f"[{vendor['name']}]({vendor['url']})")
            
            with col3:
                if vendor['emails']:
                    emails_display = ', '.join(vendor['emails'][:2])
                    if len(vendor['emails']) > 2:
                        emails_display += f" +{len(vendor['emails'])-2}"
                    st.text(emails_display)
                else:
                    st.text("Visit site")
            
            with col4:
                if st.button("+", key=f"add_prev_vendor_{i}", help="Add to contact list"):
                    contact_entry = {
                        'name': vendor['name'],
                        'url': vendor['url'],
                        'emails': vendor['emails'],
                        'type': 'vendor',
                        'part': vendor.get('part', 'N/A')
                    }
                    
                    if not any(c['url'] == vendor['url'] for c in st.session_state.contact_list):
                        st.session_state.contact_list.append(contact_entry)
                        st.success(f"Added {vendor['name']} to Email Center!")
                        time.sleep(1)  # Show message briefly

elif page == "Email Center":
    st.markdown('<p class="main-header">Email Center</p>', unsafe_allow_html=True)
    
    if not st.session_state.contact_list:
        st.info("No contacts in your list yet. Add companies from Real Sponsors or Vendor Search.")
    else:
        st.success(f"You have {len(st.session_state.contact_list)} contacts in your list")
        
        # Display contact list
        st.markdown("### Your Contact List")
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_type = st.selectbox("Filter by type", ["All", "Sponsors", "Vendors"])
        with col2:
            if st.button("Clear Contact List", use_container_width=True):
                st.session_state.contact_list.clear()
                st.rerun()
        
        # Filter contacts
        filtered_contacts = st.session_state.contact_list
        if filter_type == "Sponsors":
            filtered_contacts = [c for c in st.session_state.contact_list if c['type'] == 'sponsor']
        elif filter_type == "Vendors":
            filtered_contacts = [c for c in st.session_state.contact_list if c['type'] == 'vendor']
        
        st.markdown("---")
        
        # Display contacts and create emails
        for i, contact in enumerate(filtered_contacts):
            with st.expander(f"{contact['name']} ({contact['type'].title()}) - {len(contact['emails'])} email(s)"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Website:** {contact['url']}")
                    if contact['emails']:
                        st.markdown(f"**Emails:** {', '.join(contact['emails'])}")
                    else:
                        st.warning("No emails found for this contact")
                    
                    if contact['type'] == 'sponsor':
                        st.markdown(f"**Project:** {contact.get('project', 'N/A')}")
                    else:
                        st.markdown(f"**Part:** {contact.get('part', 'N/A')}")
                
                with col2:
                    if st.button("Create Email", key=f"create_email_{i}"):
                        st.session_state.selected_contact = contact
                        st.session_state.show_email_composer = True
                        st.rerun()
                    
                    if st.button("Remove", key=f"remove_contact_{i}"):
                        st.session_state.contact_list.remove(contact)
                        st.rerun()
        
        # Email composer
        if 'show_email_composer' in st.session_state and st.session_state.show_email_composer:
            st.markdown("---")
            st.markdown("### Compose Email")
            
            contact = st.session_state.selected_contact
            
            # Initialize show_action_buttons
            show_action_buttons = False
            
            # Email generation mode selection
            generation_mode = st.radio(
                "Email Generation Method",
                ["AI Generate (ChatGPT)", "Use Template"],
                horizontal=True
            )
            
            # Email details (common for both modes)
            col1, col2 = st.columns(2)
            with col1:
                recipient = st.selectbox("Recipient Email", contact['emails'] if contact['emails'] else ["No emails available"])
                your_name = st.text_input("Your Name", placeholder="Your name/organization")
            with col2:
                subject_custom = st.text_input("Custom Subject (optional)", placeholder="Leave blank for AI/template default")
                project_name = st.text_input("Project/Part Name", 
                                            value=contact.get('project', contact.get('part', '')))
            
            amount = st.text_input("Amount/Details", placeholder="$5,000 or specific requirements")
            
            # AI Generation Mode
            if generation_mode == "AI Generate (ChatGPT)":
                st.markdown("#### AI Email Generation")
                
                if not st.session_state.openai_enabled:
                    st.error("OpenAI API key not configured. Please add it to use AI generation.")
                    generation_mode = "Use Template"  # Fall back to template
                else:
                    # AI-specific options
                    col1, col2 = st.columns(2)
                    with col1:
                        tone = st.selectbox("Email Tone", ["Professional", "Friendly", "Formal", "Casual", "Persuasive"])
                        length = st.selectbox("Email Length", ["Short", "Medium", "Long"])
                    with col2:
                        use_template_as_reference = st.checkbox("Reference saved template in AI prompt", value=False)
                        reference_template = None
                        if use_template_as_reference and st.session_state.saved_email_templates:
                            template_names = [t['name'] for t in st.session_state.saved_email_templates]
                            selected_template_name = st.selectbox("Select Template to Reference", template_names)
                            reference_template = next((t for t in st.session_state.saved_email_templates if t['name'] == selected_template_name), None)
                    
                    additional_notes = st.text_area("Additional Instructions for AI", 
                                                   placeholder="e.g., Emphasize our team's experience, mention previous successful projects, etc.")
                    
                    if st.button("Generate Email with AI", type="primary"):
                        with st.spinner("AI is crafting your email..."):
                            try:
                                # Build AI prompt
                                contact_type = "sponsor" if contact['type'] == 'sponsor' else "vendor"
                                
                                prompt = f"""Write a {tone.lower()} {length.lower()} business email to {contact['name']}.

CONTEXT:
- Purpose: {"Request sponsorship for" if contact['type'] == 'sponsor' else "Inquire about purchasing"} {project_name}
- Recipient: {contact['name']} ({contact_type})
- Sender: {your_name}
- Amount/Budget: {amount}
- Additional context: {additional_notes}

REQUIREMENTS:
- Tone: {tone}
- Length: {length}
- Include a clear call-to-action
- Professional formatting with proper greeting and signature
"""
                                
                                if reference_template:
                                    prompt += f"""\n\nIMPORTANT - Use this template as your base structure and style guide:

TEMPLATE TO FOLLOW:
Subject: {reference_template['subject']}

{reference_template['body']}

Adapt this template's structure, style, and tone to fit the current context. Replace placeholders with actual details about {contact['name']} and {project_name}."""
                                
                                if contact['type'] == 'sponsor':
                                    prompt += "\n\nKey points to emphasize:\n- Mutual benefits and ROI\n- Exposure opportunities\n- Brand alignment and values\n- Specific deliverables"
                                else:
                                    prompt += "\n\nKey points to emphasize:\n- Specific product requirements\n- Timeline and delivery needs\n- Budget constraints\n- Request for quotes and technical specs"
                                
                                prompt += "\n\nReturn ONLY the email body, no subject line, no metadata."
                                
                                response = st.session_state.openai_client.chat.completions.create(
                                    model=OPENAI_MODEL,
                                    messages=[
                                        {"role": "system", "content": "You are a professional business email writer. Write clear, compelling emails that get responses."},
                                        {"role": "user", "content": prompt}
                                    ],
                                    max_tokens=800,
                                    temperature=0.7
                                )
                                
                                ai_email_body = response.choices[0].message.content
                                
                                # Generate subject if not provided
                                if not subject_custom:
                                    subject_prompt = f"Write a compelling email subject line for: {contact_type} email to {contact['name']} about {project_name}. Return ONLY the subject line, no quotes or extra text."
                                    subject_response = st.session_state.openai_client.chat.completions.create(
                                        model=OPENAI_MODEL,
                                        messages=[
                                            {"role": "system", "content": "You write compelling email subject lines."},
                                            {"role": "user", "content": subject_prompt}
                                        ],
                                        max_tokens=50,
                                        temperature=0.7
                                    )
                                    ai_subject = subject_response.choices[0].message.content.strip().strip('"').strip("'")
                                else:
                                    ai_subject = subject_custom
                                
                                # Store AI-generated content
                                st.session_state.ai_generated_subject = ai_subject
                                st.session_state.ai_generated_body = ai_email_body
                                st.success("AI email generated!")
                                
                            except Exception as e:
                                st.error(f"AI generation failed: {str(e)}")
                                if "quota" in str(e).lower() or "billing" in str(e).lower():
                                    st.warning("Tip: Add credits to your OpenAI account at https://platform.openai.com/account/billing")
                    
                    # Display AI-generated email if available
                    if 'ai_generated_subject' in st.session_state and 'ai_generated_body' in st.session_state:
                        st.markdown("### AI Generated Email")
                        st.text_input("To:", value=recipient, disabled=True)
                        final_subject = st.text_input("Subject:", value=st.session_state.ai_generated_subject, key="ai_subject")
                        final_body = st.text_area("Body:", value=st.session_state.ai_generated_body, height=400, key="ai_body")
                        
                        show_action_buttons = True
                    else:
                        show_action_buttons = False
            
            # Template Mode
            else:  # "Use Template"
                # Email template selection
                template_type = st.selectbox(
                    "Select Template",
                    ["Sponsorship Request", "Vendor Inquiry", "Partnership Proposal", 
                     "Follow-up Email", "Thank You Email"] + 
                    [f"Custom: {t['name']}" for t in st.session_state.saved_email_templates]
                )
                
                additional_notes = st.text_area("Additional Notes (optional)", 
                                              placeholder="Any custom details to include")
                
                # Generate email based on template
                if contact['type'] == 'sponsor':
                    default_subject = f"Sponsorship Partnership Opportunity - {project_name}"
                    default_body = f"""Dear {contact['name']} Team,

I hope this email finds you well. My name is {your_name}, and I'm reaching out regarding an exciting sponsorship opportunity that aligns perfectly with {contact['name']}'s commitment to innovation and community.

ABOUT OUR PROJECT:
{project_name} is an innovative initiative that we believe would provide {contact['name']} with valuable exposure to our target audience.

SPONSORSHIP DETAILS:
• Investment Level: {amount}
• Expected Reach: Significant market exposure
• Deliverables: Brand visibility and engagement

MUTUAL BENEFITS:
• Brand exposure to target market
• Association with innovation and excellence
• Community engagement opportunities

{additional_notes}

We would love to discuss this opportunity further and provide additional details about how {contact['name']} can be involved.

Thank you for considering our proposal. I look forward to hearing from you.

Best regards,
{your_name}"""
                else:  # vendor
                    default_subject = f"Product Inquiry - {project_name}"
                    default_body = f"""Dear {contact['name']} Sales Team,

I hope this message finds you well. I'm {your_name}, and I'm interested in learning more about your products/services for {project_name}.

PROJECT REQUIREMENTS:
• Product needed: {project_name}
• Budget range: {amount}
• Timeline: As soon as possible

QUESTIONS:
• Do you have {project_name} currently in stock?
• What are your current pricing and lead times?
• Do you offer bulk/volume discounts?
• Can you provide technical specifications?

{additional_notes}

We're evaluating several suppliers and would appreciate receiving product information and pricing details.

Thank you for your time. I look forward to your response.

Best regards,
{your_name}"""
                
                subject_line = subject_custom if subject_custom else default_subject
                email_body = default_body
                
                # Display email preview
                st.markdown("### Email Preview")
                st.text_input("To:", value=recipient, disabled=True)
                final_subject = st.text_input("Subject:", value=subject_line, key="template_subject")
                final_body = st.text_area("Body:", value=email_body, height=400, key="template_body")
                
                show_action_buttons = True
            
            # Action buttons (only show if email is ready)
            if show_action_buttons:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Add to Drafted Emails", type="primary", use_container_width=True):
                        drafted_email = {
                            'to': recipient,
                            'subject': final_subject,
                            'body': final_body,
                            'company': contact['name'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.drafted_emails.append(drafted_email)
                        
                        # Clear AI generation cache
                        if 'ai_generated_subject' in st.session_state:
                            del st.session_state.ai_generated_subject
                        if 'ai_generated_body' in st.session_state:
                            del st.session_state.ai_generated_body
                        
                        st.success(f"Email added to drafted emails! ({len(st.session_state.drafted_emails)} total)")
                
                with col2:
                    if st.button("Save as Template", use_container_width=True):
                        st.session_state.show_save_template = True
                
                with col3:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_email_composer = False
                        if 'selected_contact' in st.session_state:
                            del st.session_state.selected_contact
                        if 'ai_generated_subject' in st.session_state:
                            del st.session_state.ai_generated_subject
                        if 'ai_generated_body' in st.session_state:
                            del st.session_state.ai_generated_body
                        st.rerun()
            
            # Save template dialog
            if 'show_save_template' in st.session_state and st.session_state.show_save_template:
                template_name = st.text_input("Template Name", placeholder="e.g., My Custom Sponsorship Email")
                if st.button("Save Template"):
                    new_template = {
                        'name': template_name,
                        'subject': final_subject,
                        'body': final_body
                    }
                    st.session_state.saved_email_templates.append(new_template)
                    st.session_state.show_save_template = False
                    st.success("Template saved!")
                    st.rerun()
    
    # Show drafted emails section
    if st.session_state.drafted_emails:
        st.markdown("---")
        st.markdown(f"### Drafted Emails ({len(st.session_state.drafted_emails)})")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("These are all the emails you've created in this session")
        with col2:
            if st.button("Clear Drafted Emails", use_container_width=True):
                st.session_state.drafted_emails.clear()
                st.rerun()
        
        # Display drafted emails
        for i, email in enumerate(st.session_state.drafted_emails):
            with st.expander(f"Email {i+1}: {email['company']} - {email['timestamp']}"):
                st.markdown(f"**To:** {email['to']}")
                st.markdown(f"**Subject:** {email['subject']}")
                st.text_area("Body:", value=email['body'], height=200, key=f"drafted_{i}", disabled=True)
        
        # Export all drafted emails
        all_emails_text = ""
        for i, email in enumerate(st.session_state.drafted_emails, 1):
            all_emails_text += f"{'='*60}\n"
            all_emails_text += f"EMAIL {i} - {email['company']}\n"
            all_emails_text += f"{'='*60}\n"
            all_emails_text += f"To: {email['to']}\n"
            all_emails_text += f"Subject: {email['subject']}\n"
            all_emails_text += f"Created: {email['timestamp']}\n\n"
            all_emails_text += f"{email['body']}\n\n"
        
        st.download_button(
            label="Download All Drafted Emails as TXT",
            data=all_emails_text,
            file_name=f"drafted_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

elif page == "Email Templates":
    st.markdown('<p class="main-header">Email Template Manager</p>', unsafe_allow_html=True)
    
    # Show saved custom templates
    st.markdown("### Your Saved Templates")
    
    if not st.session_state.saved_email_templates:
        st.info("No custom templates saved yet. Create emails in Email Center and save them as templates!")
    else:
        st.success(f"You have {len(st.session_state.saved_email_templates)} saved template(s)")
        
        for i, template in enumerate(st.session_state.saved_email_templates):
            with st.expander(f"{template['name']}"):
                st.markdown(f"**Subject:** {template['subject']}")
                st.text_area("Body:", value=template['body'], height=300, key=f"template_view_{i}", disabled=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    # Download this template
                    template_text = f"Subject: {template['subject']}\n\n{template['body']}"
                    st.download_button(
                        label="Download Template",
                        data=template_text,
                        file_name=f"{template['name']}.txt",
                        mime="text/plain",
                        key=f"download_template_{i}"
                    )
                with col2:
                    if st.button("Delete Template", key=f"delete_template_{i}"):
                        st.session_state.saved_email_templates.pop(i)
                        st.rerun()
    
    st.markdown("---")
    st.markdown("### Create New Template")
    
    # Template creation form
    new_template_name = st.text_input("Template Name", placeholder="e.g., My Custom Sponsorship Request")
    new_template_subject = st.text_input("Email Subject", placeholder="Subject line template")
    new_template_body = st.text_area("Email Body", height=300, 
                                    placeholder="You can use placeholders like {COMPANY_NAME}, {YOUR_NAME}, {PROJECT_NAME}, {AMOUNT}")
    
    if st.button("Save New Template", type="primary"):
        if new_template_name and new_template_subject and new_template_body:
            new_template = {
                'name': new_template_name,
                'subject': new_template_subject,
                'body': new_template_body
            }
            st.session_state.saved_email_templates.append(new_template)
            st.success(f"Template '{new_template_name}' saved!")
            st.rerun()
        else:
            st.error("Please fill in all fields")
    
    st.markdown("---")
    st.markdown("### Default Templates")
    st.info("These are built-in templates you can use as starting points")
    
    default_templates = {
        "Sponsorship Request": """Dear {COMPANY_NAME} Team,

I hope this email finds you well. My name is {YOUR_NAME}, and I'm reaching out regarding an exciting sponsorship opportunity.

ABOUT OUR PROJECT:
{PROJECT_NAME} is an innovative initiative that we believe would provide {COMPANY_NAME} with valuable exposure.

SPONSORSHIP DETAILS:
• Investment Level: {AMOUNT}
• Expected Reach: Significant market exposure
• Deliverables: Brand visibility and engagement

We would love to discuss this opportunity further.

Best regards,
{YOUR_NAME}""",
        
        "Vendor Inquiry": """Dear {COMPANY_NAME} Sales Team,

I'm {YOUR_NAME}, and I'm interested in your products/services for {PROJECT_NAME}.

PROJECT REQUIREMENTS:
• Product needed: {PROJECT_NAME}
• Budget range: {AMOUNT}
• Timeline: As soon as possible

Please provide pricing and availability information.

Thank you,
{YOUR_NAME}""",
        
        "Partnership Proposal": """Dear {COMPANY_NAME} Team,

I'm reaching out to explore a potential partnership between {YOUR_NAME} and {COMPANY_NAME}.

PARTNERSHIP OPPORTUNITY:
{PROJECT_NAME} represents a unique opportunity for collaboration.

I'd welcome the chance to discuss how we can work together.

Best regards,
{YOUR_NAME}"""
    }
    
    for name, body in default_templates.items():
        with st.expander(f"{name}"):
            st.text_area("Template:", value=body, height=250, key=f"default_{name}", disabled=True)

elif page == "Company Database":
    st.markdown('<p class="main-header">Company Database</p>', unsafe_allow_html=True)
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Search companies", placeholder="Search by name, URL, or project...")
    with col2:
        filter_type = st.selectbox("Filter by type", ["All", "Sponsors", "Vendors"])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Get companies from database
    if search_term:
        companies = db.search_companies(search_term)
    else:
        company_type_filter = None
        if filter_type == "Sponsors":
            company_type_filter = "sponsor"
        elif filter_type == "Vendors":
            company_type_filter = "vendor"
        companies = db.get_all_companies(company_type=company_type_filter)
    
    if not companies:
        st.info("No companies in database yet. Add companies from Real Sponsors or Vendor Search pages.")
    else:
        st.success(f"Found {len(companies)} companies in database")
        
        # Display companies in a nice table format
        for company in companies:
            with st.expander(f"🏢 {company['name']} ({company['type'].title()})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Website:** [{company['url']}]({company['url']})")
                    
                    if company['type'] == 'sponsor':
                        st.markdown(f"**Project:** {company.get('project_part', 'N/A')}")
                    else:
                        st.markdown(f"**Part/Product:** {company.get('project_part', 'N/A')}")
                    
                    if company['industry']:
                        st.markdown(f"**Industry:** {company['industry']}")
                    
                    st.markdown(f"**Relevance Score:** {company['relevance_score']}")
                    st.markdown(f"**Added:** {company['date_added']}")
                    
                    if company['notes']:
                        st.markdown(f"**Notes:** {company['notes']}")
                
                with col2:
                    # Get contacts for this company
                    contacts = db.get_company_contacts(company['id'])
                    
                    if contacts:
                        st.markdown(f"**Contacts:** ({len(contacts)})")
                        for contact in contacts:
                            verified = " ✓" if contact['is_verified'] else ""
                            primary = " [Primary]" if contact['is_primary'] else ""
                            st.text(f"• {contact['email']}{verified}{primary}")
                    else:
                        st.warning("No contacts")
                    
                    # Get emails sent to this company
                    emails = db.get_company_emails(company['id'])
                    if emails:
                        st.markdown(f"**Emails:** {len(emails)} drafted/sent")
                    
                    # Action buttons
                    st.markdown("---")
                    if st.button("View Details", key=f"view_{company['id']}", use_container_width=True):
                        st.session_state.selected_company_id = company['id']
                        st.session_state.show_company_details = True
                    
                    if st.button("Delete", key=f"delete_{company['id']}", use_container_width=True):
                        if db.delete_company(company['id']):
                            st.success(f"Deleted {company['name']}")
                            st.rerun()
        
        st.markdown("---")
        
        # Export database
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Export All to CSV", use_container_width=True):
                # Create CSV
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                csv_writer.writerow(["Name", "URL", "Type", "Industry", "Project/Part", "Relevance", "Added", "Notes"])
                
                for company in companies:
                    csv_writer.writerow([
                        company['name'],
                        company['url'],
                        company['type'],
                        company.get('industry', ''),
                        company.get('project_part', ''),
                        company['relevance_score'],
                        company['date_added'],
                        company.get('notes', '')
                    ])
                
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("Export with Contacts", use_container_width=True):
                companies_with_contacts = db.get_companies_with_contacts()
                json_data = json.dumps(companies_with_contacts, indent=2)
                
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"companies_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col3:
            if st.button("Clear All Data", type="secondary", use_container_width=True):
                st.warning("This will delete ALL companies and related data!")
                if st.button("Confirm Delete All", type="primary"):
                    for company in companies:
                        db.delete_company(company['id'])
                    st.success("All data cleared!")
                    st.rerun()

elif page == "Export Tools":
    st.markdown('<p class="main-header">Export & Reporting Tools</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Email Search Data")
        if st.session_state.found_companies:
            # CSV export
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow(["Email"])
            for email in st.session_state.found_companies:
                csv_writer.writerow([email])
            
            st.download_button(
                label="Export Emails to CSV",
                data=csv_buffer.getvalue(),
                file_name=f"emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # JSON export
            json_data = json.dumps(st.session_state.found_companies, indent=2)
            st.download_button(
                label="Export Emails to JSON",
                data=json_data,
                file_name=f"emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info("No email data to export")
    
    with col2:
        st.markdown("### Vendor Recommendations")
        if st.session_state.recommended_vendors:
            # JSON export
            json_data = json.dumps(st.session_state.recommended_vendors, indent=2)
            st.download_button(
                label="Export Vendors to JSON",
                data=json_data,
                file_name=f"vendors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info("No vendor data to export")
    
    st.markdown("---")
    st.markdown("### Complete Database Export")
    
    if st.session_state.found_companies or st.session_state.recommended_vendors:
        complete_data = {
            "export_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "emails": st.session_state.found_companies,
            "vendors": st.session_state.recommended_vendors,
            "stats": {
                "total_emails": len(st.session_state.found_companies),
                "total_vendors": len(st.session_state.recommended_vendors)
            }
        }
        
        json_data = json.dumps(complete_data, indent=2)
        st.download_button(
            label="Export Complete Database",
            data=json_data,
            file_name=f"complete_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("No data to export")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Integrated Sponsor Center - Web Version | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
