# All-in-One Sponsorship Software Setup Guide

## 🚀 Quick Start

### Option 1: Run Complete Suite (Recommended)
```bash
python sponsorship_software.py
```

### Option 2: Use Launcher to Choose
```bash
python launcher.py
```

## 🔑 AI Vendor Finder Setup

To enable the AI-powered Canadian vendor recommendations:

### 1. Get OpenAI API Key
1. Go to https://platform.openai.com/
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 2. Configure API Key
1. Open the `.env` file in this folder
2. Replace `your_openai_api_key_here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```
3. Save the file
4. Restart the application

### 3. Test the Integration
1. Open the Sponsorship Software
2. Go to "Vendor Finder" tab
3. Try searching for "TD3 recovery system"
4. Should return Tinder Rocketry and other Canadian vendors

## 📋 Features Overview

### 1. Dashboard
- Overview of found companies and vendors
- Quick action buttons
- System status indicators

### 2. Email Search
- Intelligent website crawling
- Real email extraction from HTML
- Domain verification
- Progress tracking with terminal logs

### 3. AI Vendor Finder
- Natural language product/service queries
- Canadian company focus
- Contact information included
- Powered by ChatGPT

### 4. Company Database
- Stores all found companies and emails
- Import/export capabilities
- Data management tools

### 5. Export Tools
- CSV and JSON export options
- Report generation
- Complete database backup

## 🎯 Example AI Queries

Try these searches in the Vendor Finder:

- **"TD3 recovery system"** → Returns Tinder Rocketry and rocket recovery specialists
- **"CNC machining services"** → Canadian precision manufacturing companies
- **"Software development"** → Tech companies for software partnerships
- **"3D printing services"** → Additive manufacturing vendors
- **"Aerospace components"** → Aviation and space industry suppliers
- **"Marketing agencies"** → Canadian marketing and advertising firms

## 🔧 Troubleshooting

### AI Not Working?
- Check if your API key is correctly set in `.env`
- Ensure you have OpenAI API credits
- Restart the application after setting the key

### Email Search Issues?
- Some websites block automated requests
- Try adjusting the delay settings
- Check your internet connection

### Database Not Saving?
- Check file permissions in the application folder
- Ensure you have write access to the directory

## 💡 Tips for Best Results

### Email Search:
- Use full website URLs (https://company.com)
- Adjust max pages based on website size
- Enable domain verification for quality results

### AI Vendor Search:
- Be specific about what you're looking for
- Include industry context when helpful
- Use the Canadian-only filter for local companies
- Try different phrasings if initial results aren't perfect

## 🆘 Support

If you encounter issues:
1. Check the terminal/console for error messages
2. Ensure all dependencies are installed
3. Verify your OpenAI API key is valid
4. Try restarting the application

## 🔄 Updates

The software includes:
- Real-time progress tracking
- Comprehensive logging
- Data persistence
- Export capabilities
- Professional reporting tools

Your all-in-one sponsorship solution is ready to help you find Canadian companies and their contact information!