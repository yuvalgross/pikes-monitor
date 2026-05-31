# 🎵 Pikes Ibiza Event Monitor

Automatically monitor Pikes Ibiza events and get notified when lineups change.

**Monitors your Ibiza trip dates:**
- Jun 8 (Mon) - Mondays @ Pikes
- Jun 10 (Wed) - Pikes Sessions  
- Jun 11 (Thu) - Flash x Homoelectric
- Jun 13 (Sat) - Pikes House Party (Birthday! 🎂)

## ✨ Features

✅ Checks every 48 hours automatically  
✅ Email alerts when lineups update  
✅ Discord notifications (optional)  
✅ Tracks changes across all your dates  
✅ Manual trigger anytime  

## 🚀 Quick Start

### GitHub Actions (Auto-Running)

```bash
# 1. Clone this repo
git clone https://github.com/yuvalgross/pikes-monitor.git
cd pikes-monitor

# 2. Push to your GitHub
git add .
git commit -m "Add Pikes monitor"
git push
```

Then add GitHub Secrets:
- `NOTIFY_EMAIL` = your email
- `GMAIL_ADDRESS` = your Gmail  
- `GMAIL_PASSWORD` = [16-char app password](https://myaccount.google.com/apppasswords)
- `DISCORD_WEBHOOK` = (optional)

Done! It runs automatically. ✅

### Local Testing

```bash
pip install -r requirements.txt
python pikes_monitor.py
```

## 📋 What's Inside

| File | Purpose |
|------|---------|
| `pikes_monitor.py` | Main monitoring script |
| `requirements.txt` | Python dependencies |
| `.github/workflows/check-pikes.yml` | GitHub Actions automation |
| `SETUP_INSTRUCTIONS.md` | Detailed setup guide |
| `QUICK_START.md` | Fast setup reference |

## 🔔 How It Works

1. **Fetches** current Pikes event data
2. **Compares** against previous snapshot
3. **Detects** lineup changes or updates
4. **Notifies** you via email + Discord
5. **Stores** snapshot for next check

## 📧 Email Setup

Get a Gmail app password (NOT your regular password):
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" → "Windows Computer" (or Mac)
3. Copy 16-character password
4. Add to GitHub Secrets as `GMAIL_PASSWORD`

## 🤖 Discord Setup (Optional)

1. Right-click Discord channel
2. Edit Channel → Integrations → Webhooks
3. New Webhook → Copy Webhook URL
4. Add to GitHub Secrets as `DISCORD_WEBHOOK`

## 🧪 Testing

Go to GitHub repo → **Actions** tab:
1. Click "Check Pikes Events"
2. Click "Run workflow"
3. Should complete in ~30 seconds
4. Check email for test notification

## 📊 Monitoring Schedule

- **Automatic:** Every 48 hours at 10 AM UTC
- **Manual:** Anytime via GitHub Actions → "Run workflow"

## 🐛 Troubleshooting

**No emails?**
- Check Gmail app password (16 chars, NOT regular password)
- Verify NOTIFY_EMAIL secret is correct
- Check GitHub Actions logs for errors

**Workflow not running?**
- Go to Actions tab and check logs
- Manually trigger with "Run workflow"

## 📝 Files Tracked

```
Pikes Events (Jun 8, 10, 11, 13)
└── Monitors:
    ├── Event existence
    ├── Lineup changes
    ├── Event details
    └── Time changes
```

## 🎯 Your Dates

| Date | Event | Status |
|------|-------|--------|
| Jun 8 | Mondays - SECRET DJS | ✅ |
| Jun 10 | Pikes Sessions | 🔄 TBA |
| Jun 11 | Flash x Homoelectric | ✅ LOCKED |
| Jun 13 | House Party (Birthday) | 🔄 TBA |

## 🎧 Stay Updated

Once deployed, you'll automatically know:
- When new artists are announced
- If events are cancelled
- Lineup changes
- Time updates

No more manual checking! 🚀

---

**Questions?** See `SETUP_INSTRUCTIONS.md` for detailed help.
