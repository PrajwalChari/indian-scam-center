"""
Indian Scam Center - Web Application
Streamlit-based web interface for sponsorship and email search
"""

import streamlit as st
import queue
import threading
from main_windows import EmailSearcher
from openai import OpenAI
from datetime import datetime
import json
import csv
import io
import os

# OpenAI API Configuration - Use environment variable for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"

# Page configuration
st.set_page_config(
    page_title="Integrated Sponsor Center",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Matches desktop dark theme
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Sidebar styling to match desktop */
    [data-testid="stSidebar"] {
        background-color: #2b2b2b;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e0e0;
    }
    
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #3b8ed0;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Stat boxes matching desktop cards */
    .stat-box {
        background-color: #2b2b2b;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #404040;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #3b8ed0;
    }
    
    .stat-label {
        font-size: 1rem;
        color: #b0b0b0;
        margin-top: 0.5rem;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: #3b8ed0;
        color: white;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2d6da8;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Text input styling */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: #2b2b2b;
        color: #e0e0e0;
        border: 1px solid #404040;
        border-radius: 8px;
    }
    
    /* Results text boxes */
    .stTextArea textarea {
        font-family: 'Consolas', 'Monaco', monospace;
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    
    /* Cards and frames */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #2b2b2b;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #404040;
    }
    
    /* Section headers */
    h3 {
        color: #3b8ed0;
        font-weight: 600;
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background-color: #3b8ed0;
    }
    
    /* Success/Warning/Error boxes */
    .success-box {
        background-color: #1e3a1e;
        border: 1px solid #2d5a2d;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #90ee90;
    }
    
    .warning-box {
        background-color: #3a3a1e;
        border: 1px solid #5a5a2d;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffeb3b;
    }
    
    .error-box {
        background-color: #3a1e1e;
        border: 1px solid #5a2d2d;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ff6b6b;
    }
    
    /* Code blocks */
    code {
        background-color: #1a1a1a;
        color: #3b8ed0;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2b2b2b;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #b0b0b0;
    }
    
    .stTabs [aria-selected="true"] {
        color: #3b8ed0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'found_companies' not in st.session_state:
    st.session_state.found_companies = []
if 'recommended_vendors' not in st.session_state:
    st.session_state.recommended_vendors = []
if 'page_switch' not in st.session_state:
    st.session_state.page_switch = None
if 'openai_client' not in st.session_state:
    if OPENAI_API_KEY and OPENAI_API_KEY != 'your_openai_api_key_here':
        st.session_state.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        st.session_state.openai_enabled = True
    else:
        st.session_state.openai_client = None
        st.session_state.openai_enabled = False

# Sidebar Navigation
st.sidebar.markdown("# Integrated Sponsor Center")
st.sidebar.markdown("### Sponsorship & Search Platform")
st.sidebar.markdown("---")

# Handle page switching from dashboard
if st.session_state.page_switch:
    page = st.session_state.page_switch
    st.session_state.page_switch = None
else:
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Email Search", "Cash Sponsors (AI)", 
         "Vendor Search", "Email Templates", "Company Database", "Export Tools"],
        label_visibility="collapsed"
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### Status")
if st.session_state.openai_enabled:
    st.sidebar.success("AI Assistant: Connected")
else:
    st.sidebar.error("AI Assistant: Not Configured")

st.sidebar.markdown("---")
st.sidebar.markdown("### Statistics")
st.sidebar.metric("Companies Found", len(st.session_state.found_companies))
st.sidebar.metric("Vendors Found", len(st.session_state.recommended_vendors))

# Main Content
if page == "Dashboard":
    st.markdown('<p class="main-header">Scams Dashboard</p>', unsafe_allow_html=True)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(st.session_state.found_companies)}</div>
            <div class="stat-label">Companies Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(st.session_state.recommended_vendors)}</div>
            <div class="stat-label">Vendors Recommended</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        ai_status = "Connected" if st.session_state.openai_enabled else "Not Configured"
        ai_color = "#28a745" if st.session_state.openai_enabled else "#dc3545"
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color: {ai_color};">{"✓" if st.session_state.openai_enabled else "✗"}</div>
            <div class="stat-label">AI Assistant {ai_status}</div>
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
        if st.button("Export Data", use_container_width=True, key="dash_export"):
            st.session_state.page_switch = "Export Tools"
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
            max_pages = st.slider("Max Pages to search", 5, 30, 15, label_visibility="collapsed")
            st.caption(f"Pages: {max_pages}")
        with col2:
            st.markdown("**Delay (seconds)**")
            delay = st.slider("Delay between requests", 0.5, 3.0, 1.0, 0.1, label_visibility="collapsed")
            st.caption(f"Delay: {delay}s")
        with col3:
            st.markdown("**Options**")
            verify = st.checkbox("Verify Emails", value=True)
            st.caption("Domain verification")
    
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
            
            with st.spinner(f"Searching {url} for email addresses..."):
                try:
                    searcher = EmailSearcher(max_pages=max_pages, delay=delay)
                    emails = searcher.search_website_for_emails(url)
                    
                    if emails:
                        st.success(f"Found {len(emails)} email addresses!")
                        
                        # Store in session state
                        st.session_state.search_results = emails
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
    elif 'search_results' in st.session_state:
        st.markdown("### Previous Search Results")
        emails = st.session_state.search_results
        result_text = f"Found {len(emails)} email addresses:\n\n"
        for i, email in enumerate(sorted(emails), 1):
            result_text += f"{i:2d}. {email}\n"
        st.text_area("Results", result_text, height=300, label_visibility="collapsed")

elif page == "Cash Sponsors (AI)":
    st.markdown('<p class="main-header">AI Cash Sponsor Finder</p>', unsafe_allow_html=True)
    
    if not st.session_state.openai_enabled:
        st.error("OpenAI API key not configured. Please add it in Streamlit Cloud Secrets.")
    else:
        # Input section
        project = st.text_area("What project or event needs sponsorship?", 
                              placeholder="e.g., Rocket competition, Tech startup, Community event")
        
        col1, col2 = st.columns(2)
        with col1:
            industry = st.text_input("Industry/Category (optional)", 
                                    placeholder="e.g., Aerospace, Technology, Education")
        with col2:
            canadian_only = st.checkbox("Canadian companies only", value=True)
            include_contact = st.checkbox("Include contact information", value=True)
        
        if st.button("Find Cash Sponsors", type="primary", use_container_width=True):
            if not project:
                st.error("Please describe your project or event")
            else:
                with st.spinner("AI is searching for cash sponsors..."):
                    try:
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

                        response = st.session_state.openai_client.chat.completions.create(
                            model=OPENAI_MODEL,
                            messages=[
                                {"role": "system", "content": "You are a helpful sponsorship consultant specializing in corporate partnerships and funding."},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=2000,
                            temperature=0.7
                        )
                        
                        ai_response = response.choices[0].message.content
                        
                        st.success("AI Search Complete!")
                        st.markdown("### Recommended Cash Sponsors:")
                        st.markdown(ai_response)
                        
                        # Store in session state
                        st.session_state.recommended_vendors.append({
                            'type': 'sponsor',
                            'project': project,
                            'results': ai_response,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                    except Exception as e:
                        st.error(f"AI search failed: {str(e)}")
                        if "quota" in str(e).lower() or "billing" in str(e).lower():
                            st.warning("Tip: Add credits to your OpenAI account at https://platform.openai.com/account/billing")

elif page == "Vendor Search":
    st.markdown('<p class="main-header">Specific Vendor & Parts Search</p>', unsafe_allow_html=True)
    
    # Input section
    part_name = st.text_input("Specific Part or Product Name", 
                             placeholder="e.g., TD3 recovery system, Arduino Uno, Carbon fiber sheets")
    
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox("Country/Region", ["Canada", "USA", "North America", "Global"])
    with col2:
        price_range = st.selectbox("Price Range", ["Any", "Under $100", "$100-$500", "$500-$1000", "Over $1000"])
    
    find_contact = st.checkbox("Find supplier contact info", value=True)
    
    if st.button("Search Vendors", type="primary", use_container_width=True):
        if not part_name:
            st.error("Please enter a specific part or product name")
        else:
            with st.spinner(f"Searching for '{part_name}' vendors..."):
                # Provide search strategy and recommendations
                st.success("Search Strategy Generated!")
                
                st.markdown(f"""
### VENDOR SEARCH RESULTS
**Part/Product:** {part_name}  
**Region:** {country}  
**Price Range:** {price_range}

#### SEARCH STRATEGY:
Using multiple search approaches:
- Direct supplier searches
- Distributor networks
- Manufacturer databases
- E-commerce platforms
- Industry directories

#### RECOMMENDED VENDORS:

**1. DIRECT MANUFACTURERS:**
- Search for "{part_name} manufacturer {country}"
- Check industry trade associations
- Look for ISO certified suppliers

**2. DISTRIBUTORS & RESELLERS:**
- Major distributors (Digi-Key, Mouser, McMaster-Carr)
- Regional suppliers in {country}
- Specialized industry distributors

**3. E-COMMERCE PLATFORMS:**
- Amazon Business (industrial supplies)
- Alibaba (bulk/wholesale)
- ThomasNet (industrial suppliers)
- Local B2B marketplaces

**4. INDUSTRY-SPECIFIC SOURCES:**
- Trade show exhibitor lists
- Professional association member directories
- Industry publication supplier guides

#### NEXT STEPS:
1. Use the Email Search tab to find contacts at these companies
2. Cross-reference with your specific requirements
3. Request quotes from multiple vendors
4. Verify certifications and quality standards
""")

elif page == "Email Templates":
    st.markdown('<p class="main-header">Email Template Creator</p>', unsafe_allow_html=True)
    
    # Template selection
    template_type = st.selectbox(
        "Email Type",
        ["Sponsorship Request", "Vendor Inquiry", "Partnership Proposal", 
         "Follow-up Email", "Thank You Email", "Custom Template"]
    )
    
    # Template variables
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", placeholder="Target company name")
        project_name = st.text_input("Project Name", placeholder="Your project or product")
    with col2:
        your_name = st.text_input("Your Name", placeholder="Your name/organization")
        amount = st.text_input("Amount/Details", placeholder="$5,000 or specific requirements")
    
    # Template content
    templates = {
        "Sponsorship Request": {
            "subject": "Sponsorship Partnership Opportunity - [PROJECT_NAME]",
            "body": """Dear [COMPANY_NAME] Team,

I hope this email finds you well. My name is [YOUR_NAME], and I'm reaching out regarding an exciting sponsorship opportunity that aligns perfectly with [COMPANY_NAME]'s commitment to innovation and community.

ABOUT OUR PROJECT:
[PROJECT_NAME] is an innovative initiative that we believe would provide [COMPANY_NAME] with valuable exposure to our target audience.

SPONSORSHIP DETAILS:
• Investment Level: [AMOUNT]
• Expected Reach: Significant market exposure
• Deliverables: Brand visibility and engagement

MUTUAL BENEFITS:
• Brand exposure to target market
• Association with innovation and excellence
• Community engagement opportunities

We would love to discuss this opportunity further and provide additional details about how [COMPANY_NAME] can be involved.

Thank you for considering our proposal. I look forward to hearing from you.

Best regards,
[YOUR_NAME]"""
        },
        "Vendor Inquiry": {
            "subject": "Product Inquiry - [PROJECT_NAME]",
            "body": """Dear [COMPANY_NAME] Sales Team,

I hope this message finds you well. I'm [YOUR_NAME], and I'm interested in learning more about your products/services for [PROJECT_NAME].

PROJECT REQUIREMENTS:
• Product needed: [PROJECT_NAME]
• Budget range: [AMOUNT]
• Timeline: As soon as possible

QUESTIONS:
• Do you have [PROJECT_NAME] currently in stock?
• What are your current pricing and lead times?
• Do you offer bulk/volume discounts?
• Can you provide technical specifications?

We're evaluating several suppliers and would appreciate receiving product information and pricing details.

Thank you for your time. I look forward to your response.

Best regards,
[YOUR_NAME]"""
        }
    }
    
    template = templates.get(template_type, templates["Sponsorship Request"])
    
    # Replace variables
    subject = template["subject"]
    body = template["body"]
    
    if company_name:
        subject = subject.replace("[COMPANY_NAME]", company_name)
        body = body.replace("[COMPANY_NAME]", company_name)
    if your_name:
        subject = subject.replace("[YOUR_NAME]", your_name)
        body = body.replace("[YOUR_NAME]", your_name)
    if project_name:
        subject = subject.replace("[PROJECT_NAME]", project_name)
        body = body.replace("[PROJECT_NAME]", project_name)
    if amount:
        body = body.replace("[AMOUNT]", amount)
    
    body = body.replace("[DATE]", datetime.now().strftime("%B %d, %Y"))
    
    # Display template
    st.markdown("### Email Preview:")
    st.text_input("Subject:", value=subject, key="subject_preview")
    st.text_area("Body:", value=body, height=400, key="body_preview")
    
    # Copy button
    full_email = f"Subject: {subject}\n\n{body}"
    st.download_button(
        label="Download Email",
        data=full_email,
        file_name=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

elif page == "Company Database":
    st.markdown('<p class="main-header">Company Database</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Refresh Database", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Clear Database", use_container_width=True):
            st.session_state.found_companies.clear()
            st.session_state.recommended_vendors.clear()
            st.success("Database cleared!")
            st.rerun()
    
    st.markdown("---")
    
    # Display companies
    if st.session_state.found_companies:
        st.markdown(f"### Email Search Results ({len(st.session_state.found_companies)} entries)")
        for i, email in enumerate(st.session_state.found_companies, 1):
            st.code(f"{i}. {email}")
    else:
        st.info("No companies in database. Use Email Search to add entries.")
    
    st.markdown("---")
    
    # Display vendors
    if st.session_state.recommended_vendors:
        st.markdown(f"### Recommended Vendors ({len(st.session_state.recommended_vendors)} entries)")
        for i, vendor in enumerate(st.session_state.recommended_vendors, 1):
            with st.expander(f"Entry {i} - {vendor.get('type', 'Unknown')} - {vendor.get('timestamp', 'N/A')}"):
                st.markdown(vendor.get('results', 'No details available'))
    else:
        st.info("No vendors in database. Use Vendor Search or Cash Sponsors to add entries.")

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
