# 🚀 START HERE - Pikes Monitor Setup (3 MINUTES)

## What You Do:

### **1. Download & Unzip**
- Download `pikes-monitor.zip` 
- Unzip it to a folder on your computer
- Open that folder

### **2. Run ONE of These Commands:**

#### **Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

#### **Windows:**
```
Double-click setup.bat
```

That's it! The script does everything:
- ✅ Sets up git
- ✅ Adds your GitHub repo
- ✅ Pushes all files
- ✅ Tells you the next step

### **3. Add GitHub Secrets (5 min)**

When the script finishes, it will show you a link like:
```
https://github.com/yuvalgross/pikes-monitor/settings/secrets/actions
```

Go there and add 4 secrets:

| Secret Name | Value |
|-------------|-------|
| `NOTIFY_EMAIL` | your-email@gmail.com |
| `GMAIL_ADDRESS` | your-email@gmail.com |
| `GMAIL_PASSWORD` | [16-char from Google](https://myaccount.google.com/apppasswords) |
| `DISCORD_WEBHOOK` | (optional - leave blank) |

### **4. Test It (30 seconds)**

In GitHub:
1. Go to **Actions** tab
2. Click **Check Pikes Events**
3. Click **Run workflow**
4. Check your email in 30 seconds

**You should see:**
```
✅ First check - baseline established

Events monitored:
  Jun 8: Monday - Arrival (Mondays) - ✅ Found
  Jun 10: Wednesday - Pikes Sessions - ❌ Not found
  Jun 11: Thursday - Flash x Homoelectric - ✅ Found
  Jun 13: Saturday - Birthday (Pikes House Party) - ✅ Found
```

---

## 🎉 You're Done!

Your Pikes monitor is now live:
- ✅ Runs automatically every 48 hours
- ✅ Emails you when lineups change
- ✅ Can be triggered manually anytime

---

## 🐛 Troubleshooting

**Setup script says "git not found"?**
- Download Git from https://git-scm.com/
- Restart your computer
- Try again

**Script asks for "GitHub repo URL"?**
- Copy this: `https://github.com/yuvalgross/pikes-monitor.git`
- Paste it in
- Press Enter

**No email after test?**
- Check Gmail app password (16 chars, NOT your regular password)
- From: https://myaccount.google.com/apppasswords
- Make sure `NOTIFY_EMAIL` secret matches your Gmail

**Still stuck?**
- See `SETUP_INSTRUCTIONS.md` for detailed help
- Or share the error from the setup script

---

**That's all you need!** The rest is automatic. 🎵
