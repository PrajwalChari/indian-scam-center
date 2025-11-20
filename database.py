"""
Database Manager for Integrated Sponsor Center
SQLite database for storing companies, contacts, and email history
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

class SponsorDatabase:
    def __init__(self, db_path: str = "sponsor_center.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        
        # Companies table - stores all companies found
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,  -- 'sponsor' or 'vendor'
                industry TEXT,
                project_part TEXT,  -- project name for sponsors, part name for vendors
                relevance_score INTEGER DEFAULT 0,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Contacts table - stores email addresses for companies
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                contact_type TEXT DEFAULT 'general',  -- 'general', 'sales', 'support', 'info'
                is_verified BOOLEAN DEFAULT 0,
                is_primary BOOLEAN DEFAULT 0,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
                UNIQUE(company_id, email)
            )
        ''')
        
        # Emails table - stores drafted and sent emails
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                contact_id INTEGER,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT DEFAULT 'drafted',  -- 'drafted', 'sent', 'replied', 'bounced'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                replied_at TIMESTAMP,
                template_used TEXT,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL
            )
        ''')
        
        # Interactions table - tracks all interactions with companies
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,  -- 'email_sent', 'reply_received', 'phone_call', 'meeting', 'note'
                description TEXT,
                outcome TEXT,  -- 'positive', 'negative', 'neutral', 'pending'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
            )
        ''')
        
        # Templates table - stores email templates
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT,  -- 'sponsorship', 'vendor', 'follow_up', 'thank_you'
                times_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        ''')
        
        # Search history table - tracks searches performed
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_type TEXT NOT NULL,  -- 'email', 'sponsor', 'vendor'
                query TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    # ==================== COMPANY OPERATIONS ====================
    
    def add_company(self, name: str, url: str, company_type: str, 
                   industry: str = None, project_part: str = None,
                   relevance_score: int = 0, notes: str = None) -> int:
        """Add a new company to the database."""
        try:
            self.cursor.execute('''
                INSERT INTO companies (name, url, type, industry, project_part, relevance_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, url, company_type, industry, project_part, relevance_score, notes))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Company already exists, return existing ID
            self.cursor.execute('SELECT id FROM companies WHERE url = ?', (url,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
    
    def get_company(self, company_id: int) -> Optional[Dict]:
        """Get a company by ID."""
        self.cursor.execute('SELECT * FROM companies WHERE id = ?', (company_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_company_by_url(self, url: str) -> Optional[Dict]:
        """Get a company by URL."""
        self.cursor.execute('SELECT * FROM companies WHERE url = ?', (url,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_all_companies(self, company_type: str = None, limit: int = None) -> List[Dict]:
        """Get all companies, optionally filtered by type."""
        if company_type:
            query = 'SELECT * FROM companies WHERE type = ? ORDER BY date_added DESC'
            params = (company_type,)
        else:
            query = 'SELECT * FROM companies ORDER BY date_added DESC'
            params = ()
        
        if limit:
            query += f' LIMIT {limit}'
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_company(self, company_id: int, **kwargs) -> bool:
        """Update company fields."""
        if not kwargs:
            return False
        
        # Add last_updated timestamp
        kwargs['last_updated'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [company_id]
        
        self.cursor.execute(f'''
            UPDATE companies SET {set_clause} WHERE id = ?
        ''', values)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_company(self, company_id: int) -> bool:
        """Delete a company and all related records."""
        self.cursor.execute('DELETE FROM companies WHERE id = ?', (company_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def search_companies(self, search_term: str) -> List[Dict]:
        """Search companies by name, URL, or project/part."""
        search_pattern = f'%{search_term}%'
        self.cursor.execute('''
            SELECT * FROM companies 
            WHERE name LIKE ? OR url LIKE ? OR project_part LIKE ? OR notes LIKE ?
            ORDER BY relevance_score DESC, date_added DESC
        ''', (search_pattern, search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== CONTACT OPERATIONS ====================
    
    def add_contact(self, company_id: int, email: str, contact_type: str = 'general',
                   is_verified: bool = False, is_primary: bool = False) -> int:
        """Add a contact email for a company."""
        try:
            self.cursor.execute('''
                INSERT INTO contacts (company_id, email, contact_type, is_verified, is_primary)
                VALUES (?, ?, ?, ?, ?)
            ''', (company_id, email, contact_type, is_verified, is_primary))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Contact already exists
            return None
    
    def get_company_contacts(self, company_id: int) -> List[Dict]:
        """Get all contacts for a company."""
        self.cursor.execute('''
            SELECT * FROM contacts WHERE company_id = ? ORDER BY is_primary DESC, date_added ASC
        ''', (company_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_contact(self, contact_id: int, **kwargs) -> bool:
        """Update contact fields."""
        if not kwargs:
            return False
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [contact_id]
        
        self.cursor.execute(f'''
            UPDATE contacts SET {set_clause} WHERE id = ?
        ''', values)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact."""
        self.cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # ==================== EMAIL OPERATIONS ====================
    
    def add_email(self, company_id: int, subject: str, body: str,
                 contact_id: int = None, template_used: str = None) -> int:
        """Add a drafted email."""
        self.cursor.execute('''
            INSERT INTO emails (company_id, contact_id, subject, body, template_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (company_id, contact_id, subject, body, template_used))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_email(self, email_id: int) -> Optional[Dict]:
        """Get an email by ID."""
        self.cursor.execute('SELECT * FROM emails WHERE id = ?', (email_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_company_emails(self, company_id: int) -> List[Dict]:
        """Get all emails for a company."""
        self.cursor.execute('''
            SELECT * FROM emails WHERE company_id = ? ORDER BY created_at DESC
        ''', (company_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_all_emails(self, status: str = None) -> List[Dict]:
        """Get all emails, optionally filtered by status."""
        if status:
            query = 'SELECT * FROM emails WHERE status = ? ORDER BY created_at DESC'
            params = (status,)
        else:
            query = 'SELECT * FROM emails ORDER BY created_at DESC'
            params = ()
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_email_status(self, email_id: int, status: str) -> bool:
        """Update email status and set appropriate timestamp."""
        timestamp_field = None
        if status == 'sent':
            timestamp_field = 'sent_at'
        elif status == 'replied':
            timestamp_field = 'replied_at'
        
        if timestamp_field:
            self.cursor.execute(f'''
                UPDATE emails SET status = ?, {timestamp_field} = ? WHERE id = ?
            ''', (status, datetime.now().isoformat(), email_id))
        else:
            self.cursor.execute('UPDATE emails SET status = ? WHERE id = ?', (status, email_id))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_email(self, email_id: int) -> bool:
        """Delete an email."""
        self.cursor.execute('DELETE FROM emails WHERE id = ?', (email_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # ==================== INTERACTION OPERATIONS ====================
    
    def add_interaction(self, company_id: int, interaction_type: str,
                       description: str = None, outcome: str = 'neutral') -> int:
        """Add an interaction record."""
        self.cursor.execute('''
            INSERT INTO interactions (company_id, interaction_type, description, outcome)
            VALUES (?, ?, ?, ?)
        ''', (company_id, interaction_type, description, outcome))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_company_interactions(self, company_id: int) -> List[Dict]:
        """Get all interactions for a company."""
        self.cursor.execute('''
            SELECT * FROM interactions WHERE company_id = ? ORDER BY created_at DESC
        ''', (company_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== TEMPLATE OPERATIONS ====================
    
    def add_template(self, name: str, subject: str, body: str, category: str = None) -> int:
        """Add an email template."""
        try:
            self.cursor.execute('''
                INSERT INTO templates (name, subject, body, category)
                VALUES (?, ?, ?, ?)
            ''', (name, subject, body, category))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_all_templates(self, category: str = None) -> List[Dict]:
        """Get all templates, optionally filtered by category."""
        if category:
            query = 'SELECT * FROM templates WHERE category = ? ORDER BY name'
            params = (category,)
        else:
            query = 'SELECT * FROM templates ORDER BY name'
            params = ()
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get a template by ID."""
        self.cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def update_template_usage(self, template_id: int) -> bool:
        """Increment template usage counter and update last_used timestamp."""
        self.cursor.execute('''
            UPDATE templates 
            SET times_used = times_used + 1, last_used = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), template_id))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a template."""
        self.cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # ==================== SEARCH HISTORY OPERATIONS ====================
    
    def add_search_history(self, search_type: str, query: str, results_count: int = 0) -> int:
        """Add a search history record."""
        self.cursor.execute('''
            INSERT INTO search_history (search_type, query, results_count)
            VALUES (?, ?, ?)
        ''', (search_type, query, results_count))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent searches."""
        self.cursor.execute('''
            SELECT * FROM search_history ORDER BY search_date DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        stats = {}
        
        # Company counts
        self.cursor.execute('SELECT COUNT(*) as total FROM companies')
        stats['total_companies'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM companies WHERE type = "sponsor"')
        stats['total_sponsors'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM companies WHERE type = "vendor"')
        stats['total_vendors'] = self.cursor.fetchone()['total']
        
        # Contact counts
        self.cursor.execute('SELECT COUNT(*) as total FROM contacts')
        stats['total_contacts'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM contacts WHERE is_verified = 1')
        stats['verified_contacts'] = self.cursor.fetchone()['total']
        
        # Email counts
        self.cursor.execute('SELECT COUNT(*) as total FROM emails')
        stats['total_emails'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM emails WHERE status = "drafted"')
        stats['drafted_emails'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM emails WHERE status = "sent"')
        stats['sent_emails'] = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(*) as total FROM emails WHERE status = "replied"')
        stats['replied_emails'] = self.cursor.fetchone()['total']
        
        # Template count
        self.cursor.execute('SELECT COUNT(*) as total FROM templates')
        stats['total_templates'] = self.cursor.fetchone()['total']
        
        # Interaction count
        self.cursor.execute('SELECT COUNT(*) as total FROM interactions')
        stats['total_interactions'] = self.cursor.fetchone()['total']
        
        return stats
    
    def get_companies_with_contacts(self) -> List[Dict]:
        """Get all companies with their contact information."""
        self.cursor.execute('''
            SELECT 
                c.id, c.name, c.url, c.type, c.industry, c.project_part, 
                c.relevance_score, c.date_added, c.notes,
                GROUP_CONCAT(ct.email, ', ') as emails
            FROM companies c
            LEFT JOIN contacts ct ON c.id = ct.company_id
            GROUP BY c.id
            ORDER BY c.date_added DESC
        ''')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick database access
def get_database(db_path: str = "sponsor_center.db") -> SponsorDatabase:
    """Get a database instance."""
    return SponsorDatabase(db_path)


if __name__ == "__main__":
    # Test the database
    db = get_database()
    
    print("Database created successfully!")
    print("\nStatistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    db.close()
