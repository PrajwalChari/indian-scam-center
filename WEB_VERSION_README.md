# 🚀 Indian Scam Center - Web Version

**A web-based sponsorship and email search platform that you can share with anyone via a link!**

---

## ✨ What's New?

Your desktop app is now a **web application** that:
- ✅ Runs in any web browser
- ✅ Can be shared via a simple link
- ✅ No installation required for users
- ✅ Works on any device (desktop, tablet, mobile)
- ✅ Can be deployed online for free

---

## 🏃 Quick Start (Local Testing)

### Windows:
Double-click `run_web_app.bat`

### Or use command line:
```bash
python -m streamlit run web_app.py
```

The app will open automatically at: **http://localhost:8501**

---

## 🌐 Deploy Online (Share with Anyone)

### **Recommended: Streamlit Cloud (100% FREE)**

1. **Create GitHub account** (if you don't have one): https://github.com

2. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/indian-scam-center.git
   git push -u origin main
   ```

3. **Deploy on Streamlit Cloud:**
   - Go to: https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Main file: `web_app.py`
   - Click "Deploy"

4. **Get your shareable link:**
   ```
   https://YOUR-APP-NAME.streamlit.app
   ```

5. **Share with anyone!** They can use your app instantly - no setup required.

---

## 🔐 Important: Protect Your API Key

Before deploying publicly, **remove your OpenAI API key from the code!**

### Steps:

1. **Edit `web_app.py`** - Replace line 13-14 with:
   ```python
   import os
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
   ```

2. **In Streamlit Cloud:**
   - Go to App settings → Secrets
   - Add your key:
     ```toml
     OPENAI_API_KEY = "sk-your-actual-key-here"
     ```

This keeps your key secure and private!

---

## 📱 Features Available in Web Version

### 🏠 Dashboard
- View statistics and quick actions
- See companies and vendors found

### 📧 Email Search
- Search any website for email addresses
- Download results as CSV
- Smart contact page detection

### 💰 Cash Sponsors (AI)
- AI-powered sponsor recommendations
- Canadian company focus
- Industry-specific searches

### 🛒 Vendor Search
- Find suppliers for specific parts
- Regional filtering
- Price range selection

### ✉️ Email Templates
- Pre-built professional templates
- Auto-fill with your details
- Download ready-to-send emails

### 📊 Database
- View all found companies
- Track sponsor recommendations
- Clear or refresh data

### 📤 Export Tools
- Export to CSV or JSON
- Complete database backup
- Ready for spreadsheets

---

## 🎯 How to Share Your Deployed App

Once deployed on Streamlit Cloud:

1. **Get your URL:** `https://your-app.streamlit.app`

2. **Share it:**
   - Email: "Try my sponsorship tool: [link]"
   - Social media: Post the link
   - WhatsApp/Slack: Send directly
   - Website: Embed as iframe

3. **Anyone can use it** - they just click the link!

---

## 🔄 Updating Your Deployed App

After deploying to Streamlit Cloud:

```bash
# Make changes to your code
git add .
git commit -m "Updated features"
git push
```

**Your app updates automatically!** No need to redeploy.

---

## 💡 Deployment Options Comparison

| Platform | Cost | Setup | Custom Domain | Best For |
|----------|------|-------|---------------|----------|
| **Streamlit Cloud** | FREE | Easy | Yes | **Recommended** |
| Heroku | Free tier | Medium | Yes | Apps with databases |
| Railway | Free tier | Easy | Yes | Modern alternative |
| Hugging Face | FREE | Easy | No | AI/ML focused |
| PythonAnywhere | Free tier | Medium | Paid | Python-specific |

---

## 🆘 Troubleshooting

### App won't start locally?
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### SSL errors?
Already fixed in `main_windows.py` - should work fine!

### Deployment fails?
- Check `requirements.txt` includes all packages
- Verify Python version is 3.8+
- Check error logs in deployment platform

### AI features not working?
- Verify OpenAI API key is set correctly
- Check you have credits in your OpenAI account
- Ensure key is in Secrets (not hardcoded)

---

## 📞 Support

Having issues? Check:
1. `DEPLOYMENT_GUIDE.md` for detailed deployment instructions
2. Streamlit docs: https://docs.streamlit.io
3. Test locally first with `run_web_app.bat`

---

## 🎉 You're Ready!

Your sponsorship tool is now a full web application that anyone can access with just a link!

**Next Steps:**
1. Test locally: Run `run_web_app.bat`
2. Deploy to Streamlit Cloud
3. Share your link with the world! 🌍

---

**Built with ❤️ using Streamlit**
