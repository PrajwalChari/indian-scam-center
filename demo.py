"""
Quick Start Guide for Company Email Search System

This script provides examples and demonstrations of how to use
the email search system effectively.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_email_extraction():
    """Demonstrate email extraction from sample text."""
    print("=" * 60)
    print("Demo 1: Email Extraction from Text")
    print("=" * 60)
    
    from main_windows import EmailSearcher
    
    searcher = EmailSearcher()
    
    # Sample HTML-like content that might be found on a website
    sample_content = """
    <div class="contact-info">
        <h2>Contact Information</h2>
        <p>For general inquiries, please contact us at <a href="mailto:info@company.com">info@company.com</a></p>
        <p>Sales team: sales@company.com</p>
        <p>Support: <a href="mailto:support@company.com">Click here to email support</a></p>
        <p>HR Department: careers@company.com</p>
        <p>Press inquiries: press@company.com</p>
    </div>
    
    <footer>
        <p>Legal questions? Contact legal@company.com</p>
        <p>Partnership opportunities: partnerships@company.com</p>
    </footer>
    """
    
    emails = searcher.extract_emails_from_text(sample_content)
    
    print(f"Sample content processed...")
    print(f"Found {len(emails)} email addresses:")
    for email in sorted(emails):
        print(f"  • {email}")
    
    print("\nThis demonstrates how the system extracts emails from HTML content.")

def demo_domain_verification():
    """Demonstrate domain verification for sample emails."""
    print("\n" + "=" * 60)
    print("Demo 2: Domain Verification")
    print("=" * 60)
    
    from main_windows import EmailSearcher
    
    searcher = EmailSearcher()
    
    # Sample emails for testing (mix of valid and invalid domains)
    test_emails = [
        "info@microsoft.com",      # Should be valid
        "contact@github.com",      # Should be valid  
        "test@nonexistentdomain12345.com",  # Should be invalid
        "support@google.com"       # Should be valid
    ]
    
    print("Testing domain verification for sample emails:")
    print("-" * 50)
    
    for email in test_emails:
        try:
            is_valid = searcher.verify_email_domain(email)
            status = "VALID" if is_valid else "INVALID"
            print(f"{email:<35} {status}")
        except Exception as e:
            print(f"{email:<35} ERROR: {e}")
    
    print("\nThis shows how the system verifies email domains using DNS/MX records.")

def demo_website_search():
    """Demonstrate searching a real website for emails."""
    print("\n" + "=" * 60)
    print("Demo 3: Live Website Search")
    print("=" * 60)
    
    from main_windows import EmailSearcher
    
    # Use a website that's likely to have contact information
    test_websites = [
        "https://www.djangoproject.com",
        "https://flask.palletsprojects.com", 
        "https://www.github.com"
    ]
    
    print("Available websites for testing:")
    for i, site in enumerate(test_websites, 1):
        print(f"  {i}. {site}")
    
    try:
        choice = input("\nEnter number (1-3) or press Enter for automated demo: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_websites):
            selected_site = test_websites[int(choice) - 1]
        else:
            selected_site = test_websites[0]  # Default to first site
        
        print(f"\nSearching {selected_site} for email addresses...")
        print("(Limited to 3 pages for demo)")
        
        searcher = EmailSearcher(max_pages=3, delay=1)
        emails = searcher.search_website_for_emails(selected_site)
        
        if emails:
            print(f"\nFound {len(emails)} email addresses:")
            for email in sorted(emails):
                print(f"  • {email}")
                
            # Quick domain verification
            print(f"\nQuick domain verification:")
            for email in sorted(emails):
                try:
                    is_valid = searcher.verify_email_domain(email)
                    status = "✓" if is_valid else "✗"
                    print(f"  {status} {email}")
                except:
                    print(f"  ? {email} (verification failed)")
        else:
            print(f"\nNo email addresses found on {selected_site}")
            print("This might be due to:")
            print("  • Website blocking automated requests")
            print("  • Emails loaded dynamically with JavaScript")
            print("  • No contact information on the searched pages")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError during website search: {e}")

def interactive_search():
    """Run an interactive email search session."""
    print("\n" + "=" * 60)
    print("Interactive Email Search")
    print("=" * 60)
    
    website = input("Enter a company website URL: ").strip()
    
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    try:
        from main_windows import EmailSearcher
        
        # Get user preferences
        try:
            max_pages = int(input("Maximum pages to search (default 10): ").strip() or "10")
        except ValueError:
            max_pages = 10
        
        try:
            delay = float(input("Delay between requests in seconds (default 1.5): ").strip() or "1.5")
        except ValueError:
            delay = 1.5
        
        print(f"\nStarting search of {website}")
        print(f"Settings: max_pages={max_pages}, delay={delay}s")
        print("-" * 50)
        
        searcher = EmailSearcher(max_pages=max_pages, delay=delay)
        emails = searcher.search_website_for_emails(website)
        
        if emails:
            print(f"\n✓ Found {len(emails)} email addresses:")
            for email in sorted(emails):
                print(f"    {email}")
            
            verify = input(f"\nVerify these emails? (y/n): ").strip().lower()
            if verify in ['y', 'yes']:
                print("\nVerifying emails (this may take a while)...")
                
                for email in sorted(emails):
                    try:
                        domain_valid = searcher.verify_email_domain(email)
                        print(f"  {email}: {'Domain OK' if domain_valid else 'Domain Invalid'}")
                    except Exception as e:
                        print(f"  {email}: Verification error")
        else:
            print(f"\n✗ No emails found on {website}")
    
    except Exception as e:
        print(f"\nError: {e}")

def main_menu():
    """Display main menu and handle user choices."""
    while True:
        print("\n" + "=" * 60)
        print("Company Email Search & Verification System")
        print("=" * 60)
        print("Choose an option:")
        print("1. Demo: Email extraction from text")
        print("2. Demo: Domain verification")
        print("3. Demo: Live website search")
        print("4. Interactive email search")
        print("5. Run full system (main_windows.py)")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        try:
            if choice == "1":
                demo_email_extraction()
            elif choice == "2":
                demo_domain_verification()
            elif choice == "3":
                demo_website_search()
            elif choice == "4":
                interactive_search()
            elif choice == "5":
                from main_windows import main
                main()
            elif choice == "0":
                print("Thank you for using the Email Search System!")
                break
            else:
                print("Invalid choice. Please enter 0-5.")
                
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user.")
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or contact support.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nFatal error: {e}")
        print("Please check your installation and try again.")