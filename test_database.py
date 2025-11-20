"""
Test script for the Sponsor Center database
Run this to test database functionality
"""

from database import SponsorDatabase
from datetime import datetime

def test_database():
    print("="*60)
    print("Testing Sponsor Center Database")
    print("="*60)
    
    # Initialize database
    db = SponsorDatabase("test_sponsor_center.db")
    print("✓ Database initialized")
    
    # Test 1: Add a sponsor company
    print("\n--- Test 1: Adding Sponsor Company ---")
    company_id = db.add_company(
        name="SpaceX",
        url="https://www.spacex.com",
        company_type="sponsor",
        industry="Aerospace",
        project_part="Rocket Propulsion System",
        relevance_score=10,
        notes="Major aerospace company"
    )
    print(f"✓ Added company with ID: {company_id}")
    
    # Test 2: Add contacts
    print("\n--- Test 2: Adding Contacts ---")
    contact_id1 = db.add_contact(company_id, "partnerships@spacex.com", contact_type="sales", is_primary=True)
    contact_id2 = db.add_contact(company_id, "info@spacex.com", contact_type="general")
    print(f"✓ Added contacts: {contact_id1}, {contact_id2}")
    
    # Test 3: Add a vendor company
    print("\n--- Test 3: Adding Vendor Company ---")
    vendor_id = db.add_company(
        name="DigiKey",
        url="https://www.digikey.com",
        company_type="vendor",
        project_part="Arduino Uno R3",
        relevance_score=8
    )
    db.add_contact(vendor_id, "sales@digikey.com", contact_type="sales", is_primary=True)
    print(f"✓ Added vendor with ID: {vendor_id}")
    
    # Test 4: Create draft email
    print("\n--- Test 4: Creating Draft Email ---")
    email_id = db.add_email(
        company_id=company_id,
        contact_id=contact_id1,
        subject="Partnership Opportunity - Rocket Project",
        body="Dear SpaceX team,\n\nWe would like to discuss...",
        template_used="Sponsorship Request"
    )
    print(f"✓ Created draft email with ID: {email_id}")
    
    # Test 5: Add interaction
    print("\n--- Test 5: Adding Interaction ---")
    interaction_id = db.add_interaction(
        company_id=company_id,
        interaction_type="email_sent",
        description="Sent initial sponsorship request",
        outcome="pending"
    )
    print(f"✓ Added interaction with ID: {interaction_id}")
    
    # Test 6: Add template
    print("\n--- Test 6: Adding Email Template ---")
    template_id = db.add_template(
        name="My Custom Sponsorship Template",
        subject="Partnership Opportunity - {PROJECT_NAME}",
        body="Dear {COMPANY_NAME},\n\nWe are excited to propose...",
        category="sponsorship"
    )
    print(f"✓ Added template with ID: {template_id}")
    
    # Test 7: Get statistics
    print("\n--- Test 7: Database Statistics ---")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test 8: Search companies
    print("\n--- Test 8: Searching Companies ---")
    results = db.search_companies("rocket")
    print(f"✓ Found {len(results)} companies matching 'rocket'")
    for company in results:
        print(f"  - {company['name']} ({company['type']})")
    
    # Test 9: Get company with contacts
    print("\n--- Test 9: Getting Company Details ---")
    company = db.get_company(company_id)
    contacts = db.get_company_contacts(company_id)
    print(f"✓ Company: {company['name']}")
    print(f"  Contacts: {len(contacts)}")
    for contact in contacts:
        print(f"    - {contact['email']} ({contact['contact_type']})")
    
    # Test 10: Get all companies with contacts
    print("\n--- Test 10: Getting All Companies with Contacts ---")
    companies_with_contacts = db.get_companies_with_contacts()
    print(f"✓ Retrieved {len(companies_with_contacts)} companies")
    for company in companies_with_contacts:
        print(f"  - {company['name']}: {company['emails'] if company['emails'] else 'No emails'}")
    
    # Test 11: Update email status
    print("\n--- Test 11: Updating Email Status ---")
    db.update_email_status(email_id, "sent")
    email = db.get_email(email_id)
    print(f"✓ Email status updated to: {email['status']}")
    print(f"  Sent at: {email['sent_at']}")
    
    # Test 12: Get all emails
    print("\n--- Test 12: Getting All Emails ---")
    all_emails = db.get_all_emails()
    print(f"✓ Found {len(all_emails)} emails")
    for email in all_emails:
        print(f"  - To: (Company ID {email['company_id']}) | Subject: {email['subject'][:30]}... | Status: {email['status']}")
    
    print("\n" + "="*60)
    print("All tests completed successfully! ✓")
    print("="*60)
    print(f"\nTest database created: test_sponsor_center.db")
    print("You can delete this file after testing.")
    
    # Close database
    db.close()

if __name__ == "__main__":
    test_database()
