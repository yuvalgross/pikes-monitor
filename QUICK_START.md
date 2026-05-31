# Pikes Monitor - Quick GitHub Setup

## Copy-Paste These Commands

```bash
# 1. Clone your repo
git clone https://github.com/yuvalgross/pikes-monitor.git
cd pikes-monitor

# 2. Copy all files from here (they're ready to go)
# Files already present:
# - pikes_monitor.py
# - requirements.txt
# - SETUP_INSTRUCTIONS.md
# - .env.example
# - .github/workflows/check-pikes.yml
# - .gitignore
# - README.md

# 3. Push to GitHub
git add .
git commit -m "Add Pikes monitor automation"
git push

# 4. Add GitHub Secrets (via web browser)
# Go to: Settings → Secrets and variables → Actions
# Add:
#   NOTIFY_EMAIL = your-email@gmail.com
#   GMAIL_ADDRESS = your-email@gmail.com
#   GMAIL_PASSWORD = 16-char app password from Google
#   DISCORD_WEBHOOK = (optional)
```

## Then You're Done! ✅

- Runs automatically every 48 hours
- Email alerts on changes
- Manual trigger available in Actions tab

---

## Get Your Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" + "Windows Computer" (or Mac)
3. Copy the 16-character password
4. Paste as GMAIL_PASSWORD secret in GitHub

---

## Verify It Works

1. Go to Actions tab
2. Click "Run workflow"
3. Should complete in ~30 seconds
4. Check your email for test notification
