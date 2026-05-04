# MRCS Revision Tool — Deployment Guide

## Quick Start (Local)

```bash
cd /Users/joerundle/Desktop/mrcs_revision
export ANTHROPIC_API_KEY="your-api-key-here"
streamlit run Home.py --server.port 8501
```

Visit `http://localhost:8501` in your browser.

---

## Deploy to Streamlit Cloud (Easiest & Free)

Streamlit Cloud is the **fastest way** to get your app online for your friend to test.

### Step 1: Push to GitHub
```bash
cd /Users/joerundle/Desktop/mrcs_revision
git init
git add .
git commit -m "Initial MRCS revision tool"
```

Create a repository on GitHub (https://github.com/new) and push:
```bash
git remote add origin https://github.com/YOUR-USERNAME/mrcs-revision.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository, main branch, and `Home.py`
4. Click "Deploy"

### Step 3: Add Your API Key Securely
1. In the Streamlit Cloud app dashboard, click the three dots (⋮) → Settings
2. Go to "Secrets"
3. Add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. App redeploys automatically

**Your app is now live!** Share the URL with your friend.

---

## Alternative: Deploy on GoDaddy Hosting

GoDaddy shared hosting runs PHP/cPanel, **not** Python. You'd need:

### Option A: GoDaddy VPS/Dedicated Server
- Rent a VPS ($10-20/month)
- SSH in, install Python, pip, dependencies
- Run the Streamlit app or use Gunicorn

### Option B: PaaS Services (Recommended over GoDaddy)
- **Streamlit Cloud**: Free tier, easiest ✅
- **Render**: Free tier for simple apps (https://render.com)
- **Railway**: $5 credit/month free (https://railway.app)
- **Heroku**: Paid only now ($7/month minimum)

---

## Environment Variables

### Local Development
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Streamlit Cloud Secrets
Add in the app dashboard (Settings → Secrets):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

### Python reads it (both methods):
```python
import os
key = os.environ.get("ANTHROPIC_API_KEY")
```

---

## Troubleshooting Deployments

### "ModuleNotFoundError: No module named 'streamlit'"
→ Ensure `requirements.txt` is in the root directory. Streamlit Cloud will run `pip install -r requirements.txt` automatically.

### "ANTHROPIC_API_KEY not found"
→ Check Streamlit Cloud Secrets (Settings → Secrets). Restart the app.

### "AttributeError: module 'whisper' has no attribute..."
→ Whisper adds ~500MB to the build. Streamlit Cloud has a 1GB app limit. If close, consider removing Whisper or deferring to browser Speech API.

### App is slow/timing out
→ Streamlit Cloud free tier has CPU limits. For heavy usage, upgrade or use a paid PaaS.

---

## What's Different Online?

| Feature | Local | Streamlit Cloud |
|---------|-------|-----------------|
| File access | ✅ Full | ❌ Read-only (ephemeral) |
| Environment vars | ✅ `.env` or export | ✅ Secrets UI |
| Session state | ✅ Persistent | ❌ Lost on refresh |
| WebSocket/live | ✅ Works | ✅ Works |
| Microphone | ✅ Works | ✅ Works (HTTPS required) |

**Note:** Your app uses browser speech recognition, which requires HTTPS on Streamlit Cloud. It's automatically enabled, so no action needed.

---

## Quick Comparison: Where to Deploy?

| Platform | Cost | Setup | Best For |
|----------|------|-------|----------|
| **Streamlit Cloud** | Free (with limits) | 5 min | Fast prototyping, friend testing |
| **Render** | Free tier available | 10 min | Small apps, more flexibility |
| **Railway** | $5 credit/month free | 10 min | Simple Python apps |
| **GoDaddy Shared** | $3-5/mo | Not suitable | Not Python-friendly |
| **GoDaddy VPS** | $10-20/mo | 30+ min | Full control, if needed |

**Recommendation:** Use Streamlit Cloud for your friend's testing. If you scale up or need a custom domain, upgrade to Render or Railway.

---

## Next Steps

1. **Push to GitHub** (if using Streamlit Cloud)
2. **Deploy to Streamlit Cloud** (5 min)
3. **Share URL with your friend**
4. **Gather feedback**
5. **Extract Salah's Notes PDF** into `utils/knowledge_base.json` to personalize questions

---

## Customizing Knowledge Base

The knowledge base is stored in `utils/knowledge_base.json` with sample data. To add more content from Salah's Notes:

1. Extract key facts from the PDF
2. Add to `knowledge_base.json` under the relevant topic/concept
3. The tutor automatically uses these facts in questions
4. Commit and push → Streamlit Cloud updates within seconds

Example structure:
```json
{
  "anatomy": {
    "Applied Surgical Anatomy": [
      {
        "concept": "Spinal cord compression",
        "key_facts": ["...", "...", "..."],
        "clinical_scenarios": ["...", "..."],
        "exam_pitfalls": ["...", "..."]
      }
    ]
  }
}
```

---

Questions? Check `.streamlit/config.toml` for app settings or see Streamlit docs: https://docs.streamlit.io
