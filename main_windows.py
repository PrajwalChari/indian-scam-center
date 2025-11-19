import requests
from bs4 import BeautifulSoup
import re
import time
import smtplib
import socket
from urllib.parse import urljoin, urlparse
from typing import Set, List, Tuple, Optional
import dns.resolver
import email_validator
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import os
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging with Windows console support
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Windows console compatibility
def safe_print(text):
    """Print text safely on Windows console."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

class EmailSearcher:
    def __init__(self, max_pages=10, delay=1):
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Disable SSL verification to handle self-signed certificates
        self.session.verify = False
        
        # Common email patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]
        
        # Common pages that might contain contact info
        self.contact_pages = [
            '/contact', '/contact-us', '/contact.html', '/contact.php',
            '/about', '/about-us', '/about.html', '/about.php',
            '/team', '/staff', '/people', '/leadership',
            '/support', '/help', '/customer-service',
            '/legal', '/privacy', '/terms',
            '/careers', '/jobs', '/employment'
        ]

    def get_page_content(self, url: str) -> Optional[str]:
        """Fetch and return the content of a web page."""
        try:
            response = self.session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_emails_from_text(self, text: str) -> Set[str]:
        """Extract email addresses from text using regex patterns."""
        emails = set()
        
        for pattern in self.email_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'mailto:' in pattern:
                    email = match.group(1)
                else:
                    email = match.group(0)
                
                # Clean up the email
                email = email.lower().strip()
                
                # Filter out common false positives
                if self.is_valid_email_format(email):
                    emails.add(email)
        
        return emails

    def is_valid_email_format(self, email: str) -> bool:
        """Check if email has valid format and isn't a common false positive."""
        try:
            # Basic format validation
            email_validator.validate_email(email)
            
            # Filter out common false positives
            false_positives = [
                'example@example.com', 'test@test.com', 'admin@admin.com',
                'info@info.com', 'contact@contact.com', 'support@support.com',
                'noreply@noreply.com', 'donotreply@donotreply.com'
            ]
            
            if email in false_positives:
                return False
                
            # Check for image file extensions (sometimes OCR mistakes)
            if any(ext in email for ext in ['.jpg', '.png', '.gif', '.svg']):
                return False
                
            return True
            
        except email_validator.EmailNotValidError:
            return False

    def get_all_links(self, base_url: str, html_content: str) -> Set[str]:
        """Extract all internal links from HTML content with smart filtering."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        base_domain = urlparse(base_url).netloc
        
        # Priority keywords for contact-related pages
        contact_keywords = [
            'contact', 'about', 'team', 'staff', 'people', 'leadership',
            'support', 'help', 'customer', 'service', 'careers', 'jobs',
            'legal', 'privacy', 'terms', 'company', 'organization'
        ]
        
        priority_links = set()
        regular_links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                continue
                
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Only include internal links
            if parsed.netloc == base_domain:
                # Clean the URL
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                
                # Skip common non-content URLs
                skip_patterns = [
                    'login', 'register', 'logout', 'cart', 'checkout',
                    'download', 'pdf', 'image', 'photo', 'gallery',
                    'search', 'filter', 'sort', 'page=', 'tag=',
                    '.jpg', '.png', '.gif', '.pdf', '.doc', '.zip'
                ]
                
                if any(pattern in clean_url.lower() for pattern in skip_patterns):
                    continue
                
                # Prioritize contact-related pages
                if any(keyword in clean_url.lower() or keyword in link.get_text().lower() 
                       for keyword in contact_keywords):
                    priority_links.add(clean_url)
                else:
                    regular_links.add(clean_url)
        
        # Return priority links first, then regular links
        all_links = list(priority_links) + list(regular_links)
        return set(all_links[:20])  # Limit to 20 most relevant links

    def analyze_website_structure(self, base_url: str) -> dict:
        """Analyze website structure to find the best pages to search."""
        logger.info(f"Analyzing website structure: {base_url}")
        
        # Get the homepage first
        content = self.get_page_content(base_url)
        if not content:
            return {"pages": [], "error": "Could not access homepage"}
        
        # Extract all links from homepage
        all_links = self.get_all_links(base_url, content)
        
        # Analyze page types and prioritize
        page_analysis = {
            "contact_pages": [],
            "about_pages": [],
            "team_pages": [],
            "support_pages": [],
            "other_pages": []
        }
        
        for link in all_links:
            link_lower = link.lower()
            if any(word in link_lower for word in ['contact', 'reach', 'touch']):
                page_analysis["contact_pages"].append(link)
            elif any(word in link_lower for word in ['about', 'company', 'who', 'story']):
                page_analysis["about_pages"].append(link)
            elif any(word in link_lower for word in ['team', 'staff', 'people', 'leadership', 'management']):
                page_analysis["team_pages"].append(link)
            elif any(word in link_lower for word in ['support', 'help', 'service', 'customer']):
                page_analysis["support_pages"].append(link)
            else:
                page_analysis["other_pages"].append(link)
        
        return page_analysis
    
    def search_website_for_emails(self, base_url: str) -> Set[str]:
        """Intelligently search a website for email addresses based on actual structure."""
        logger.info(f"Starting intelligent email search for: {base_url}")
        
        all_emails = set()
        visited_urls = set()
        
        # Step 1: Analyze the website structure
        structure = self.analyze_website_structure(base_url)
        
        if "error" in structure:
            logger.error(f"Could not analyze website: {structure['error']}")
            return all_emails
        
        # Step 2: Build prioritized list of pages to search
        priority_pages = []
        
        # Highest priority: Contact pages
        priority_pages.extend(structure.get("contact_pages", [])[:3])
        # High priority: About and team pages
        priority_pages.extend(structure.get("about_pages", [])[:2])
        priority_pages.extend(structure.get("team_pages", [])[:2])
        # Medium priority: Support pages
        priority_pages.extend(structure.get("support_pages", [])[:2])
        # Low priority: Other relevant pages
        priority_pages.extend(structure.get("other_pages", [])[:3])
        
        # Always include the homepage
        if base_url not in priority_pages:
            priority_pages.insert(0, base_url)
        
        # Limit to max_pages
        pages_to_search = priority_pages[:self.max_pages]
        
        logger.info(f"Found {len(pages_to_search)} relevant pages to search")
        
        # Step 3: Search each page
        for i, url in enumerate(pages_to_search, 1):
            if url in visited_urls:
                continue
                
            visited_urls.add(url)
            logger.info(f"Searching page {i}/{len(pages_to_search)}: {url}")
            
            # Get page content
            content = self.get_page_content(url)
            if not content:
                continue
            
            # Extract emails from this page
            page_emails = self.extract_emails_from_text(content)
            all_emails.update(page_emails)
            
            if page_emails:
                logger.info(f"Found {len(page_emails)} emails on {url}: {page_emails}")
            
            # Be respectful with delays
            time.sleep(self.delay)
        
        logger.info(f"Email search completed. Found {len(all_emails)} unique emails from {len(visited_urls)} pages.")
        return all_emails

    def verify_email_domain(self, email: str) -> bool:
        """Verify that the email domain has valid MX records."""
        domain = email.split('@')[1]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            logger.warning(f"No MX records found for domain: {domain}")
            return False

    def verify_email_smtp(self, email: str) -> Tuple[bool, str]:
        """Verify email existence using SMTP (be careful with this - can be blocked)."""
        domain = email.split('@')[1]
        
        try:
            # Get MX record
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(mx_records[0].exchange)
            
            # Connect to mail server
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_record, 25)
            server.helo()
            server.mail('test@test.com')  # Sender
            
            # Check if recipient exists
            code, message = server.rcpt(email)
            server.quit()
            
            # 250 means success, 550 usually means user doesn't exist
            if code == 250:
                return True, "Email appears to be valid"
            else:
                return False, f"SMTP verification failed: {code} {message}"
                
        except Exception as e:
            logger.warning(f"SMTP verification failed for {email}: {e}")
            return False, f"SMTP verification error: {str(e)}"

    def verify_emails(self, emails: Set[str]) -> List[dict]:
        """Verify a set of emails and return detailed results."""
        results = []
        
        for email in emails:
            logger.info(f"Verifying email: {email}")
            
            result = {
                'email': email,
                'format_valid': True,  # Already validated during extraction
                'domain_valid': False,
                'smtp_valid': False,
                'smtp_message': '',
                'overall_status': 'Unknown'
            }
            
            # Verify domain has MX records
            result['domain_valid'] = self.verify_email_domain(email)
            
            if result['domain_valid']:
                # Only try SMTP if domain is valid
                smtp_valid, smtp_message = self.verify_email_smtp(email)
                result['smtp_valid'] = smtp_valid
                result['smtp_message'] = smtp_message
                
                if smtp_valid:
                    result['overall_status'] = 'Valid'
                else:
                    result['overall_status'] = 'Questionable'
            else:
                result['overall_status'] = 'Invalid Domain'
            
            results.append(result)
            
            # Be respectful with verification delays
            time.sleep(2)
        
        return results

def main():
    """Main function for the company email search and verification system."""
    
    safe_print("=" * 60)
    safe_print("Company Email Search & Verification System")
    safe_print("=" * 60)
    
    # Get website URL from user
    website_url = input("Enter the company website URL (e.g., https://example.com): ").strip()
    
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    try:
        # Get search settings
        try:
            max_pages = int(input("Maximum pages to search (default 15): ").strip() or "15")
        except ValueError:
            max_pages = 15
            
        # Initialize the email searcher
        searcher = EmailSearcher(max_pages=max_pages, delay=1)
        
        safe_print(f"\nSearching for emails on: {website_url}")
        safe_print("=" * 60)
        
        # Search for emails
        found_emails = searcher.search_website_for_emails(website_url)
        
        if not found_emails:
            safe_print("No emails found on the website.")
            safe_print("\nThis could be due to:")
            safe_print("  • Website blocking automated requests")
            safe_print("  • Emails loaded dynamically with JavaScript")
            safe_print("  • No contact information on accessible pages")
            return
        
        safe_print(f"\nFound {len(found_emails)} email addresses:")
        for i, email in enumerate(sorted(found_emails), 1):
            safe_print(f"  {i:2d}. {email}")
        
        # Ask user if they want to verify emails
        verify_choice = input(f"\nWould you like to verify these emails? (y/n): ").strip().lower()
        
        if verify_choice in ['y', 'yes']:
            safe_print("\nVerifying emails...")
            safe_print("=" * 60)
            
            verification_results = searcher.verify_emails(found_emails)
            
            # Display results
            safe_print("\nVerification Results:")
            safe_print("-" * 70)
            safe_print(f"{'Email':<35} {'Format':<8} {'Domain':<8} {'SMTP':<8} {'Status':<15}")
            safe_print("-" * 70)
            
            for result in verification_results:
                format_check = "YES" if result['format_valid'] else "NO"
                domain_check = "YES" if result['domain_valid'] else "NO"
                smtp_check = "YES" if result['smtp_valid'] else "NO"
                
                safe_print(f"{result['email']:<35} {format_check:<8} {domain_check:<8} {smtp_check:<8} {result['overall_status']:<15}")
            
            # Summary
            valid_emails = [r for r in verification_results if r['overall_status'] == 'Valid']
            questionable_emails = [r for r in verification_results if r['overall_status'] == 'Questionable']
            invalid_emails = [r for r in verification_results if r['overall_status'] == 'Invalid Domain']
            
            safe_print("\nSummary:")
            safe_print(f"  Valid emails: {len(valid_emails)}")
            safe_print(f"  Questionable emails: {len(questionable_emails)}")
            safe_print(f"  Invalid emails: {len(invalid_emails)}")
            
            if valid_emails:
                safe_print(f"\nRecommended emails to contact:")
                for result in valid_emails:
                    safe_print(f"  • {result['email']}")
        
        safe_print(f"\nEmail search completed for {website_url}")
        
    except KeyboardInterrupt:
        safe_print("\n\nSearch interrupted by user.")
    except Exception as e:
        safe_print(f"\nAn error occurred: {e}")
        logger.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()