# Pikes Ibiza Event Monitor - Setup Guide

## What It Does
- ✅ Checks Pikes Ibiza events every 48 hours
- ✅ Monitors your 4 key dates (Jun 8, 10, 11, 13)
- ✅ Detects lineup changes and event updates
- ✅ Sends email or Discord notifications when changes occur
- ✅ Runs automatically (no manual checks needed)

---

## Option A: GitHub Actions (Recommended - Free & Automated)

### Step 1: Create GitHub Repository
```bash
git clone https://github.com/yourusername/pikes-monitor.git
cd pikes-monitor
git init
```

### Step 2: Create GitHub Actions Workflow
Create file: `.github/workflows/check-pikes.yml`

```yaml
name: Check Pikes Events

on:
  schedule:
    # Runs every 48 hours at 10 AM UTC
    - cron: '0 10 */2 * *'
  workflow_dispatch:  # Manual trigger

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run monitor
        env:
          NOTIFY_EMAIL: ${{ secrets.NOTIFY_EMAIL }}
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_PASSWORD: ${{ secrets.GMAIL_PASSWORD }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
        run: python pikes_monitor.py
      
      - name: Commit snapshot
        run: |
          git config user.name "Bot"
          git config user.email "bot@github.com"
          git add pikes_snapshot.json
          git commit -m "Update Pikes snapshot" || true
          git push
```

### Step 3: Add GitHub Secrets

Go to: **Settings → Secrets and Variables → Actions**

Add these secrets:

#### For Email Notifications:
1. `NOTIFY_EMAIL` → your-email@gmail.com
2. `GMAIL_ADDRESS` → your-email@gmail.com
3. `GMAIL_PASSWORD` → [Gmail App Password - see below]

**Get Gmail App Password:**
- Go to https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer"
- Copy the 16-character password
- Paste as `GMAIL_PASSWORD` secret

#### For Discord Notifications (Optional):
1. `DISCORD_WEBHOOK` → [Your Discord Webhook URL]

**Get Discord Webhook:**
- Right-click Discord channel → Edit Channel
- Webhooks → New Webhook → Copy Webhook URL

### Step 4: Deploy
```bash
git add .
git commit -m "Add Pikes monitor"
git push
```

Done! It will now check every 48 hours automatically.

---

## Option B: Run Locally (Manual)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
```bash
export NOTIFY_EMAIL="your-email@gmail.com"
export GMAIL_ADDRESS="your-email@gmail.com"
export GMAIL_PASSWORD="your-gmail-app-password"
```

### Step 3: Run Script
```bash
python pikes_monitor.py
```

### Step 4: Schedule with Cron (Mac/Linux)
```bash
crontab -e
```

Add line (runs every 48 hours at 10 AM):
```
0 10 */2 * * cd /path/to/pikes-monitor && python pikes_monitor.py >> pikes_monitor.log 2>&1
```

### Step 5: Schedule with Task Scheduler (Windows)
- Open Task Scheduler
- Create Basic Task
- Set trigger: Every 2 days at 10:00 AM
- Action: `python C:\path\to\pikes_monitor.py`

---

## Testing

### Test Email:
```bash
export NOTIFY_EMAIL="test@gmail.com"
python pikes_monitor.py
```

### Test Discord:
```bash
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
python pikes_monitor.py
```

### Manual GitHub Trigger:
- Go to GitHub repo
- Actions tab
- Click "Check Pikes Events"
- Click "Run workflow"

---

## Files Structure
```
pikes-monitor/
├── pikes_monitor.py          # Main script
├── requirements.txt           # Dependencies
├── pikes_snapshot.json       # Stores current state (auto-generated)
├── README.md                 # This file
└── .github/workflows/
    └── check-pikes.yml       # GitHub Actions config
```

---

## What It Monitors

| Date | Event | Status |
|------|-------|--------|
| Jun 8 | Mondays @ Pikes (Arrival) | ✅ SECRET DJS |
| Jun 10 | Pikes Sessions | 🔄 TBA |
| Jun 11 | Flash x Homoelectric | ✅ Confirmed lineup |
| Jun 13 | Pikes House Party (Birthday) | 🔄 TBA |

---

## Notifications You'll Get

**Email Example:**
```
Subject: 🎉 Pikes Ibiza Event Update

Jun 11 - Flash x Homoelectric Pride
🔄 Event updated: Flash x Homoelectric

View Full Schedule →
```

**Discord Example:**
```
🎉 Pikes Ibiza Event Update
Jun 11 - Flash x Homoelectric Pride
🔄 Event updated: Flash x Homoelectric
```

---

## Troubleshooting

**Emails not arriving?**
- Check Gmail app password is correct (16 chars, not your regular password)
- Check NOTIFY_EMAIL is valid
- Try Gmail's Less Secure Apps setting

**Discord not notifying?**
- Verify webhook URL is correct
- Check Discord bot permissions
- Try webhook in Postman first

**Script not running in GitHub?**
- Check "Actions" tab for error logs
- Verify all secrets are set
- Click "Run workflow" manually to test

---

## Support

Questions? Check the logs:
- **GitHub:** Actions → Workflow run → Logs
- **Local:** `pikes_monitor.log` (if redirected)

Happy monitoring! 🎵
