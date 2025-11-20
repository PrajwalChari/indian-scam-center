# Database Feature - Integrated Sponsor Center

## Overview

The Integrated Sponsor Center now includes a persistent SQL database to store:
- **Companies** (sponsors and vendors)
- **Contact information** (emails)
- **Drafted and sent emails**
- **Email templates**
- **Interaction history**
- **Search history**

## Database Schema

### Tables

1. **companies** - All companies (sponsors/vendors) found
   - id, name, url, type, industry, project_part, relevance_score, date_added, notes

2. **contacts** - Email addresses for companies
   - id, company_id, email, contact_type, is_verified, is_primary

3. **emails** - Drafted and sent emails
   - id, company_id, contact_id, subject, body, status, created_at, sent_at

4. **templates** - Email templates
   - id, name, subject, body, category, times_used

5. **interactions** - Interaction tracking
   - id, company_id, interaction_type, description, outcome, created_at

6. **search_history** - Search history
   - id, search_type, query, results_count, search_date

## Usage

### Running the Web App

```bash
streamlit run web_app.py
```

The database file `sponsor_center.db` will be created automatically in the same directory.

### Testing the Database

```bash
python test_database.py
```

This creates a test database with sample data to verify everything works.

### Direct Database Access

```python
from database import SponsorDatabase

# Initialize database
db = SponsorDatabase()

# Add a company
company_id = db.add_company(
    name="Example Corp",
    url="https://example.com",
    company_type="sponsor",
    project_part="Flight Computer"
)

# Add contact
db.add_contact(company_id, "contact@example.com", is_primary=True)

# Get all companies
companies = db.get_all_companies()

# Search companies
results = db.search_companies("flight")

# Get statistics
stats = db.get_statistics()

# Close connection
db.close()
```

## Features

### Automatic Storage
- When you click the "+" button on search results, companies are automatically saved to the database
- Contact emails are stored and associated with each company
- Relevance scores are calculated and saved

### Company Database Page
- View all companies in a searchable, filterable interface
- See contact information and interaction history
- Export data to CSV or JSON
- Delete individual companies or clear entire database

### Dashboard Statistics
- Live statistics from the database
- Total companies, contacts, emails
- Sponsors vs vendors breakdown
- Email reply rate tracking

### Data Persistence
- All data persists between sessions
- No need to re-search or re-add companies
- Build your contact list over time
- Track interactions and outcomes

## Database File

- **Location**: `sponsor_center.db` (same directory as web_app.py)
- **Format**: SQLite (single file, no server required)
- **Backup**: Simply copy the .db file to backup your data
- **Size**: Small and efficient (typically < 1 MB for hundreds of companies)

## API Reference

See `database.py` for full documentation of all available functions:

- Company operations: `add_company()`, `get_company()`, `update_company()`, `delete_company()`, `search_companies()`
- Contact operations: `add_contact()`, `get_company_contacts()`, `update_contact()`
- Email operations: `add_email()`, `get_email()`, `update_email_status()`
- Template operations: `add_template()`, `get_all_templates()`
- Statistics: `get_statistics()`, `get_companies_with_contacts()`

## Migration from Session State

The app still supports session state for backwards compatibility, but all new data is stored in both:
1. Session state (temporary, for current session)
2. Database (permanent, persists between sessions)

## Benefits

✅ **Persistent Storage** - Data survives app restarts
✅ **Searchable** - Find companies by name, URL, or keywords
✅ **Organized** - Structured data with relationships
✅ **Scalable** - Handle thousands of companies efficiently
✅ **Trackable** - Monitor interactions and outcomes
✅ **Exportable** - Easy data export to CSV/JSON
✅ **Professional** - Track reply rates and communication history

## Troubleshooting

### Database locked error
If you get a "database locked" error, close other instances of the app.

### Resetting the database
Delete `sponsor_center.db` file to start fresh. A new database will be created automatically.

### Viewing the database
Use any SQLite browser tool (e.g., DB Browser for SQLite) to view `sponsor_center.db` directly.

## Future Enhancements

Potential additions:
- Email scheduling and automation
- Reminder notifications
- Analytics dashboard
- Company tagging system
- Document attachments
- Multi-user support with authentication
