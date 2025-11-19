"""
Example usage of the Email Search Algorithm

This script demonstrates how to use the EmailSearcher class
to find and verify company emails from websites.
"""

from main import EmailSearcher

def quick_search_example():
    """Quick example of searching for emails on a website."""
    
    # Example websites to test (you can replace with any company website)
    test_websites = [
        "https://www.microsoft.com",
        "https://www.github.com", 
        "https://www.stackoverflow.com"
    ]
    
    print("🤖 Email Search Algorithm Demo")
    print("=" * 50)
    
    # Choose a website or enter custom one
    print("Available test websites:")
    for i, site in enumerate(test_websites, 1):
        print(f"  {i}. {site}")
    
    choice = input(f"\nEnter number (1-{len(test_websites)}) or paste a custom URL: ").strip()
    
    try:
        if choice.isdigit() and 1 <= int(choice) <= len(test_websites):
            website = test_websites[int(choice) - 1]
        elif choice.startswith(('http://', 'https://')):
            website = choice
        else:
            website = 'https://' + choice
        
        # Initialize searcher with moderate settings
        searcher = EmailSearcher(max_pages=8, delay=1.5)
        
        print(f"\n🔍 Searching {website} for email addresses...")
        
        # Search for emails
        emails_found = searcher.search_website_for_emails(website)
        
        if emails_found:
            print(f"\n✅ Found {len(emails_found)} email addresses:")
            for email in sorted(emails_found):
                print(f"   📧 {email}")
            
            # Quick domain verification only (faster than full SMTP)
            print(f"\n🔬 Performing domain verification...")
            valid_domains = []
            invalid_domains = []
            
            for email in emails_found:
                if searcher.verify_email_domain(email):
                    valid_domains.append(email)
                else:
                    invalid_domains.append(email)
            
            print(f"\n📊 Domain Verification Results:")
            print(f"   ✅ Valid domains: {len(valid_domains)}")
            print(f"   ❌ Invalid domains: {len(invalid_domains)}")
            
            if valid_domains:
                print(f"\n🎯 Emails with valid domains:")
                for email in valid_domains:
                    print(f"   • {email}")
        else:
            print(f"\n❌ No email addresses found on {website}")
            print("   💡 Try a different website or check if the site blocks web scraping")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

def batch_search_example():
    """Example of searching multiple websites in batch."""
    
    websites = [
        "https://www.python.org",
        "https://www.django-project.com", 
        "https://flask.palletsprojects.com"
    ]
    
    print("🔄 Batch Email Search Example")
    print("=" * 40)
    
    searcher = EmailSearcher(max_pages=5, delay=2)
    all_results = {}
    
    for website in websites:
        print(f"\n🔍 Searching: {website}")
        try:
            emails = searcher.search_website_for_emails(website)
            all_results[website] = emails
            print(f"   Found: {len(emails)} emails")
        except Exception as e:
            print(f"   Error: {e}")
            all_results[website] = set()
    
    # Summary
    print(f"\n📊 Batch Search Summary:")
    print("-" * 50)
    
    total_emails = 0
    for site, emails in all_results.items():
        total_emails += len(emails)
        print(f"{site}: {len(emails)} emails")
        for email in sorted(emails):
            print(f"   • {email}")
    
    print(f"\nTotal unique emails found: {total_emails}")

if __name__ == "__main__":
    print("Choose an example:")
    print("1. Quick single website search")
    print("2. Batch multiple website search") 
    print("3. Run full interactive search (from main.py)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        quick_search_example()
    elif choice == "2":
        batch_search_example()
    elif choice == "3":
        from main import main
        main()
    else:
        print("Invalid choice. Running quick search example...")
        quick_search_example()