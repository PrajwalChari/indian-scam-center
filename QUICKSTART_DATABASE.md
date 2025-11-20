# Quick Start Guide - SQL Database

## Getting Started

### 1. Run the Web App
```bash
streamlit run web_app.py
```

### 2. Search for Companies
- Go to **"Real Sponsors"** or **"Vendor Search"** pages
- Enter your search criteria
- Click **Search**

### 3. Save Companies to Database
- Click the **"+"** button next to any company in the results
- The company is automatically saved with all contact emails
- Check the **Company Database** page to see saved companies

### 4. View Your Database
- Go to **"Company Database"** page
- Search, filter, and browse all saved companies
- View contact information and interaction history

### 5. Export Your Data
- Click **"Export All to CSV"** for spreadsheet format
- Click **"Export with Contacts"** for JSON with full details

## Common Tasks

### Add a Company Manually
```python
from database import SponsorDatabase

db = SponsorDatabase()

company_id = db.add_company(
    name="Company Name",
    url="https://example.com",
    company_type="sponsor",  # or "vendor"
    project_part="Your Project Name"
)

db.add_contact(company_id, "contact@example.com", is_primary=True)
db.close()
```

### Search Companies
```python
from database import SponsorDatabase

db = SponsorDatabase()

# Search by keyword
results = db.search_companies("rocket")

# Get all sponsors
sponsors = db.get_all_companies(company_type="sponsor")

# Get statistics
stats = db.get_statistics()
print(f"Total companies: {stats['total_companies']}")

db.close()
```

### Track Email Communication
```python
from database import SponsorDatabase

db = SponsorDatabase()

# Add a drafted email
email_id = db.add_email(
    company_id=1,
    subject="Partnership Opportunity",
    body="Dear Team..."
)

# Update when sent
db.update_email_status(email_id, "sent")

# Update when replied
db.update_email_status(email_id, "replied")

db.close()
```

## Database File Location

The database is stored in:
```
sponsor_center.db
```

**To backup:** Simply copy this file
**To reset:** Delete this file (a new one will be created)
**To view:** Use any SQLite browser (e.g., DB Browser for SQLite)

## Web App Pages

### Dashboard
- Live statistics from database
- Total companies, contacts, emails
- Reply rate tracking
- Quick action buttons

### Company Database
- View all saved companies
- Search and filter
- Export to CSV/JSON
- Delete companies

### Real Sponsors / Vendor Search
- Find companies online
- Click "+" to save to database
- Automatically stores contacts and relevance scores

### Email Center
- Draft emails to saved companies
- Emails automatically saved to database
- Track send status

## Tips

✅ **Save as you search** - Click "+" immediately when you find good companies
✅ **Add notes** - Use the notes field to remember important details
✅ **Track interactions** - Record calls, meetings, and outcomes
✅ **Export regularly** - Backup your data by exporting to CSV/JSON
✅ **Use search** - Find companies quickly with the search feature

## Troubleshooting

**Q: Where is my data stored?**
A: In `sponsor_center.db` in the same folder as web_app.py

**Q: Can I access the database from outside the web app?**
A: Yes! Use `from database import SponsorDatabase` in any Python script

**Q: How do I reset everything?**
A: Delete `sponsor_center.db` and restart the app

**Q: Can I edit the database directly?**
A: Yes, use DB Browser for SQLite or any SQLite tool

## Next Steps

1. Start searching for companies
2. Save 10-20 companies to your database
3. Draft some emails in Email Center
4. Track your communications
5. Export your data for reports

Enjoy your new persistent sponsor/vendor database! 🚀
