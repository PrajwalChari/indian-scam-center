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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailSearcher:
    def __init__(self, max_pages=10, delay=1):
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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
            response = self.session.get(url, timeout=10)
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
        """Extract all internal links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include internal links
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)
        
        return links

    def search_website_for_emails(self, base_url: str) -> Set[str]:
        """Comprehensively search a website for email addresses."""
        logger.info(f"Starting email search for: {base_url}")
        
        all_emails = set()
        visited_urls = set()
        urls_to_visit = {base_url}
        
        # Add common contact pages
        parsed_url = urlparse(base_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        for contact_path in self.contact_pages:
            contact_url = urljoin(base_domain, contact_path)
            urls_to_visit.add(contact_url)
        
        page_count = 0
        
        while urls_to_visit and page_count < self.max_pages:
            current_url = urls_to_visit.pop()
            
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            page_count += 1
            
            logger.info(f"Searching page {page_count}/{self.max_pages}: {current_url}")
            
            # Get page content
            content = self.get_page_content(current_url)
            if not content:
                continue
            
            # Extract emails from this page
            page_emails = self.extract_emails_from_text(content)
            all_emails.update(page_emails)
            
            if page_emails:
                logger.info(f"Found {len(page_emails)} emails on {current_url}: {page_emails}")
            
            # Get more links to search (only if we haven't reached max pages)
            if page_count < self.max_pages:
                new_links = self.get_all_links(base_url, content)
                # Add new links but limit to avoid infinite crawling
                for link in list(new_links)[:5]:  # Limit to 5 new links per page
                    if link not in visited_urls:
                        urls_to_visit.add(link)
            
            # Be respectful with delays
            time.sleep(self.delay)
        
        logger.info(f"Email search completed. Found {len(all_emails)} unique emails.")
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
    
    print("=" * 60)
    print("Company Email Search & Verification System")
    print("=" * 60)
    
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
        
        print(f"\nSearching for emails on: {website_url}")
        print("=" * 60)
        
        # Search for emails
        found_emails = searcher.search_website_for_emails(website_url)
        
        if not found_emails:
            print("No emails found on the website.")
            print("\nThis could be due to:")
            print("  • Website blocking automated requests")
            print("  • Emails loaded dynamically with JavaScript")
            print("  • No contact information on accessible pages")
            return
        
        print(f"\nFound {len(found_emails)} email addresses:")
        for i, email in enumerate(sorted(found_emails), 1):
            print(f"  {i:2d}. {email}")
        
        # Ask user if they want to verify emails
        verify_choice = input(f"\nWould you like to verify these emails? (y/n): ").strip().lower()
        
        if verify_choice in ['y', 'yes']:
            print("\nVerifying emails...")
            print("=" * 60)
            
            verification_results = searcher.verify_emails(found_emails)
            
            # Display results
            print("\nVerification Results:")
            print("-" * 70)
            print(f"{'Email':<35} {'Format':<8} {'Domain':<8} {'SMTP':<8} {'Status':<15}")
            print("-" * 70)
            
            for result in verification_results:
                format_check = "YES" if result['format_valid'] else "NO"
                domain_check = "YES" if result['domain_valid'] else "NO"
                smtp_check = "YES" if result['smtp_valid'] else "NO"
                
                print(f"{result['email']:<35} {format_check:<8} {domain_check:<8} {smtp_check:<8} {result['overall_status']:<15}")
            
            # Summary
            valid_emails = [r for r in verification_results if r['overall_status'] == 'Valid']
            questionable_emails = [r for r in verification_results if r['overall_status'] == 'Questionable']
            invalid_emails = [r for r in verification_results if r['overall_status'] == 'Invalid Domain']
            
            print("\nSummary:")
            print(f"  Valid emails: {len(valid_emails)}")
            print(f"  Questionable emails: {len(questionable_emails)}")
            print(f"  Invalid emails: {len(invalid_emails)}")
            
            if valid_emails:
                print(f"\nRecommended emails to contact:")
                for result in valid_emails:
                    print(f"  • {result['email']}")
        
        print(f"\nEmail search completed for {website_url}")
        
    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        logger.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
