# Indian Scam Center - Web Deployment Guide

## 🚀 Quick Start (Run Locally)

```bash
streamlit run web_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🌐 Deploy Online (Share with Anyone)

### Option 1: Streamlit Cloud (FREE & EASIEST)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/indian-scam-center.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select `web_app.py` as the main file
   - Click "Deploy"
   - Get your shareable link: `https://YOUR_APP.streamlit.app`

3. **Share the link with anyone!**

---

### Option 2: Heroku (Free Tier Available)

1. **Create `Procfile`:**
   ```
   web: streamlit run web_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Deploy:**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. **Access at:** `https://your-app-name.herokuapp.com`

---

### Option 3: Railway.app (Modern Alternative)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Streamlit
5. Get your shareable link

---

### Option 4: Hugging Face Spaces (FREE)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Create new Space → Select "Streamlit"
3. Upload your files or connect GitHub
4. Get shareable link: `https://huggingface.co/spaces/YOUR_USERNAME/indian-scam-center`

---

## 🔐 Security Note

**⚠️ IMPORTANT:** Before deploying publicly, remove your OpenAI API key from the code!

### Use Environment Variables Instead:

1. **Update `web_app.py`:**
   ```python
   import os
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
   ```

2. **Set in Streamlit Cloud:**
   - Go to App settings → Secrets
   - Add:
     ```toml
     OPENAI_API_KEY = "your-key-here"
     ```

3. **Set in Heroku:**
   ```bash
   heroku config:set OPENAI_API_KEY=your-key-here
   ```

---

## 📦 What Gets Deployed

- `web_app.py` - Main Streamlit application
- `main_windows.py` - Email searcher backend
- `requirements.txt` - Python dependencies

---

## 🧪 Test Before Deployment

```bash
# Run locally first
streamlit run web_app.py

# Check all features work:
# ✓ Email search
# ✓ AI sponsor finder
# ✓ Vendor search
# ✓ Email templates
# ✓ Export tools
```

---

## 🎯 Recommended: Streamlit Cloud

**Why?**
- ✅ Free forever
- ✅ Automatic HTTPS
- ✅ Easy updates (push to GitHub)
- ✅ No credit card required
- ✅ Custom domain support
- ✅ Built-in secrets management

**Your app will be accessible at:**
`https://YOUR-USERNAME-indian-scam-center.streamlit.app`

**Anyone with the link can use it - no installation required!**

---

## 📧 Sharing Your App

Once deployed, share the URL:
- Email: "Check out my app at https://your-app.streamlit.app"
- Social: Post the link directly
- Embed: Use iframe on your website

---

## 🔧 Updating Your App

**Streamlit Cloud (auto-updates):**
```bash
git add .
git commit -m "Updated features"
git push
# App updates automatically!
```

**Heroku:**
```bash
git push heroku main
```

---

## 💡 Tips

1. **Custom Domain:** Most platforms support custom domains (e.g., scamcenter.yoursite.com)
2. **Analytics:** Add Google Analytics to track usage
3. **Authentication:** Add login if you want to restrict access
4. **Rate Limiting:** Consider adding limits for API calls

---

## 🆘 Troubleshooting

**App won't start?**
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility (3.8+)

**SSL Errors?**
- Already handled in `main_windows.py` with `verify=False`

**Slow performance?**
- Free tiers have limited resources
- Consider caching with `@st.cache_data`

---

## 🎉 You're Ready!

Your app is now a website that anyone can access with just a link - no installation required!
