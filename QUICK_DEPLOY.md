# 🚀 Quick Deployment Guide

## The Fastest Path to Deploy Your App

### 1️⃣ Push to GitHub (2 minutes)
```powershell
git init
git add .
git commit -m "Ready to deploy"
git remote add origin https://github.com/YOUR_USERNAME/indian-scam-center.git
git push -u origin main
```

### 2️⃣ Deploy on Streamlit Cloud (3 minutes)
1. Go to: **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo: `YOUR_USERNAME/indian-scam-center`
5. Main file: `web_app.py`
6. Click **"Deploy"**

### 3️⃣ Add API Key Secret (1 minute)
1. Go to **App Settings** → **Secrets**
2. Add:
   ```toml
   OPENAI_API_KEY = "your-actual-key-here"
   ```
3. Click **Save**

### ✅ Done!
Your app is live at:
```
https://your-app.streamlit.app
```

---

## 🔄 Update Your App Later
```powershell
git add .
git commit -m "Updated"
git push
```
Auto-deploys in ~1 minute!

---

## 📖 Full Guide
See `DEPLOYMENT_STEPS.md` for detailed instructions.

---

## 💡 Quick Tips

- **Test locally first:** `.\run_web_app.bat`
- **No credit card needed:** Streamlit Cloud is 100% free
- **Share instantly:** Just send the link
- **Works everywhere:** Desktop, mobile, tablet
- **Auto HTTPS:** Secure by default

---

## 🆘 Common Issues

**"Port in use" locally?**
```powershell
.\restart_web_app.bat
```

**Deployment fails?**
- Check `requirements.txt` is complete
- Verify all files are pushed to GitHub
- Check logs in Streamlit Cloud dashboard

**API not working?**
- Make sure secret is set in Streamlit Cloud
- Copy key exactly (no extra spaces)
- Verify key is valid on OpenAI dashboard

---

Your web app is ready to go live! 🌍
