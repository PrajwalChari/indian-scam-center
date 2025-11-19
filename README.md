# Company Email Search & Verification System

This project provides a comprehensive solution for automatically discovering and verifying company email addresses from their websites. The system performs real web scraping, extracts emails from HTML content, and verifies their validity.

## 🚀 Features

- **Intelligent Web Crawling**: Automatically discovers and searches multiple pages on a website
- **Real Email Extraction**: Uses advanced regex patterns to find email addresses in HTML content
- **Smart Page Discovery**: Automatically checks common contact pages (/contact, /about, /team, etc.)
- **Email Verification**: 
  - Format validation using industry-standard libraries
  - DNS/MX record verification
  - SMTP server verification (optional)
- **Respectful Scraping**: Includes delays and rate limiting to be respectful to websites
- **Comprehensive Results**: Detailed reporting of found emails and their verification status

## 📋 Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:
- `requests` - For HTTP requests and web scraping
- `beautifulsoup4` - For HTML parsing and content extraction
- `dnspython` - For DNS/MX record verification
- `email-validator` - For email format validation
- `lxml` - For faster HTML parsing

## 🔧 Usage

### Easy Start - Choose Your Interface

Run the launcher to choose between GUI and command line:

```bash
python launcher.py
```

### GUI Interface (Recommended)

Run the graphical user interface:

```bash
python email_search_gui.py
```

Features:
- Easy-to-use graphical interface
- Real-time progress updates
- Configurable search settings
- Built-in email verification
- Clear results display

### Command Line Interface

Run the command line version:

```bash
python main_windows.py
```

This will:
1. Ask for a company website URL
2. Ask for search settings (max pages)
3. Automatically search through multiple pages
4. Extract all email addresses found
5. Optionally verify the emails for validity

### Programmatic Usage

```python
from main_windows import EmailSearcher

# Initialize the searcher
searcher = EmailSearcher(max_pages=10, delay=1)

# Search for emails
emails = searcher.search_website_for_emails("https://example.com")

# Verify the emails
results = searcher.verify_emails(emails)

# Display results
for result in results:
    print(f"{result['email']}: {result['overall_status']}")
```

## 🔍 How It Works

### 1. Website Crawling
- Starts with the provided base URL
- Automatically discovers internal links
- Prioritizes common contact pages (/contact, /about, /team, etc.)
- Respects robots.txt and includes delays between requests

### 2. Email Extraction
- Uses multiple regex patterns to find email addresses
- Extracts emails from:
  - Plain text content
  - mailto: links
  - Contact forms
  - Hidden content
- Filters out common false positives

### 3. Email Verification

#### Format Validation
- Uses `email-validator` library for RFC-compliant validation
- Filters out test/example emails
- Removes obvious false positives

#### Domain Verification
- Checks DNS MX records to verify the domain can receive emails
- Confirms the email domain is properly configured

#### SMTP Verification (Optional)
- Connects to the mail server
- Performs RCPT TO command to check if the email exists
- **Note**: This can be blocked by some mail servers and should be used carefully

## ⚙️ Configuration

### EmailSearcher Parameters

```python
EmailSearcher(
    max_pages=10,    # Maximum pages to crawl per website
    delay=1          # Delay in seconds between requests
)
```

### Common Contact Pages Searched
- `/contact`, `/contact-us`
- `/about`, `/about-us`
- `/team`, `/staff`, `/people`
- `/support`, `/help`
- `/legal`, `/privacy`
- `/careers`, `/jobs`

## 📊 Output Format

The system provides detailed results for each email found:

```
Email                           Format  Domain  SMTP    Status
---------------------------------------------------------------
contact@company.com            ✓       ✓       ✓       Valid
info@company.com               ✓       ✓       ✗       Questionable
old@company.com                ✓       ✗       ✗       Invalid Domain
```

## 🛡️ Ethical Considerations

- **Respect robots.txt**: Always check if the website allows scraping
- **Rate limiting**: Built-in delays to avoid overwhelming servers
- **Legal compliance**: Ensure your use complies with local laws and website terms of service
- **Privacy**: Handle discovered emails responsibly and in compliance with privacy laws

## 🔧 Troubleshooting

### Common Issues

1. **No emails found**
   - Website might block web scraping
   - Emails might be loaded dynamically with JavaScript
   - Try different delay settings

2. **SMTP verification fails**
   - Some mail servers block verification attempts
   - Use domain verification as a more reliable alternative

3. **SSL/Certificate errors**
   - Some websites have certificate issues
   - The system includes error handling for these cases

### Debug Mode

Enable detailed logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Example Output

```
🔍 Searching for emails on: https://example.com
============================================================

📧 Found 3 email addresses:
  • contact@example.com
  • support@example.com
  • info@example.com

🔬 Verifying emails...
============================================================

📊 Verification Results:
--------------------------------------------------------------------------------
Email                           Format  Domain  SMTP    Status         
--------------------------------------------------------------------------------
contact@example.com            ✓       ✓       ✓       Valid          
info@example.com               ✓       ✓       ✗       Questionable   
support@example.com            ✓       ✓       ✓       Valid          

📈 Summary:
  ✅ Valid emails: 2
  ⚠️  Questionable emails: 1
  ❌ Invalid emails: 0

🎯 Recommended emails to contact:
  • contact@example.com
  • support@example.com
```

## 🤝 Contributing

Feel free to improve the email detection patterns, add new verification methods, or enhance the crawling algorithm. Some areas for improvement:

- JavaScript rendering for dynamic content
- Better handling of email obfuscation techniques
- Integration with email deliverability APIs
- Support for additional contact form patterns

## ⚠️ Disclaimer

This tool is for legitimate business purposes only. Always respect website terms of service, privacy policies, and applicable laws. The authors are not responsible for misuse of this software.