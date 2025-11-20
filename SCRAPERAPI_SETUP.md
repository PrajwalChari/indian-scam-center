# ScraperAPI Setup Instructions

## Why ScraperAPI?
ScraperAPI bypasses anti-bot systems and handles proxy rotation automatically, preventing the "blocking requests" error on Streamlit Cloud.

## Setup Steps

### 1. Get Your Free API Key
1. Go to https://www.scraperapi.com/
2. Sign up for a free account (1000 requests/month)
3. Copy your API key from the dashboard

### 2. Add to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Open your app settings
3. Click "Secrets" in the left sidebar
4. Add this to your secrets:

```toml
SCRAPER_API_KEY = "your_api_key_here"
```

5. Click "Save"

### 3. Deploy
Your app will automatically restart with ScraperAPI enabled. The sidebar will show "ScraperAPI: Connected".

## Usage Limits
- **Free Plan**: 1000 requests/month
- Each search uses ~5-10 requests
- Monitor usage at: https://www.scraperapi.com/dashboard

## Features Enabled
- ✅ Real Sponsors search works on cloud
- ✅ Vendor Search works on cloud  
- ✅ Email extraction from websites
- ✅ No more "blocking requests" errors

## Cost
- Free: 1000 requests/month ($0)
- Hobby: 10,000 requests/month ($29)
- Startup: 100,000 requests/month ($99)

## Testing Locally
Add to your environment variables:
```bash
export SCRAPER_API_KEY="your_api_key_here"
```

Or create a `.env` file (don't commit this!):
```
SCRAPER_API_KEY=your_api_key_here
```
