#!/bin/bash
# Pikes Monitor - Auto Setup Script
# Just run this and it does everything

echo "🚀 Setting up Pikes Monitor GitHub repo..."
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git first."
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)

# Check if this is already a git repo
if [ -d ".git" ]; then
    echo "✅ Git repo already initialized"
else
    echo "📝 Initializing git repo..."
    git init
    git config user.name "Pikes Monitor"
    git config user.email "pikes@monitor.local"
fi

# Add GitHub remote if not exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "🔗 Adding GitHub remote..."
    echo "Enter your GitHub repo URL (e.g., https://github.com/yuvalgross/pikes-monitor.git):"
    read REPO_URL
    git remote add origin "$REPO_URL"
else
    echo "✅ GitHub remote already configured"
fi

# Add all files
echo ""
echo "📦 Adding files..."
git add .

# Commit
echo "💾 Committing changes..."
git commit -m "🎵 Add Pikes Monitor - Automated Ibiza event tracking

- Monitors Jun 8, 10, 11, 13 events
- Automated checks every 48 hours
- Email alerts on lineup changes
- GitHub Actions integration ready"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo ""
    echo "🔄 Renaming branch to 'main'..."
    git branch -M main
fi

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Files pushed to GitHub"
    echo ""
    echo "📋 NEXT STEP: Add GitHub Secrets"
    echo ""
    echo "Go to: https://github.com/yuvalgross/pikes-monitor/settings/secrets/actions"
    echo ""
    echo "Add these 4 secrets:"
    echo "  1. NOTIFY_EMAIL = your-email@gmail.com"
    echo "  2. GMAIL_ADDRESS = your-email@gmail.com"
    echo "  3. GMAIL_PASSWORD = (16-char from https://myaccount.google.com/apppasswords)"
    echo "  4. DISCORD_WEBHOOK = (optional - leave blank if not using)"
    echo ""
    echo "🧪 Then test it:"
    echo "  Go to Actions tab → Run workflow → Check for email in 30 seconds"
    echo ""
    echo "🎉 Done! It will now check Pikes automatically every 48 hours"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "  - Check your GitHub repo URL"
    echo "  - Make sure you have push permissions"
    echo "  - Try: git push -u origin main (with authentication)"
fi
