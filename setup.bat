@echo off
REM Pikes Monitor - Auto Setup Script for Windows
REM Just run this and it does everything

echo.
echo 🚀 Setting up Pikes Monitor GitHub repo...
echo.

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Git not found. Please install Git first from https://git-scm.com/
    pause
    exit /b 1
)

REM Check if this is already a git repo
if exist ".git" (
    echo ✅ Git repo already initialized
) else (
    echo 📝 Initializing git repo...
    git init
    git config user.name "Pikes Monitor"
    git config user.email "pikes@monitor.local"
)

REM Add GitHub remote if not exists
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 🔗 Adding GitHub remote...
    set /p REPO_URL="Enter your GitHub repo URL (e.g., https://github.com/yuvalgross/pikes-monitor.git): "
    git remote add origin %REPO_URL%
) else (
    echo ✅ GitHub remote already configured
)

REM Add all files
echo.
echo 📦 Adding files...
git add .

REM Commit
echo 💾 Committing changes...
git commit -m "Add Pikes Monitor - Automated Ibiza event tracking"

REM Push to GitHub
echo.
echo 🚀 Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS! Files pushed to GitHub
    echo.
    echo 📋 NEXT STEP: Add GitHub Secrets
    echo.
    echo Go to: https://github.com/yuvalgross/pikes-monitor/settings/secrets/actions
    echo.
    echo Add these 4 secrets:
    echo   1. NOTIFY_EMAIL = your-email@gmail.com
    echo   2. GMAIL_ADDRESS = your-email@gmail.com
    echo   3. GMAIL_PASSWORD = (16-char from https://myaccount.google.com/apppasswords)
    echo   4. DISCORD_WEBHOOK = (optional)
    echo.
    echo 🧪 Then test it:
    echo   Go to Actions tab ^> Run workflow ^> Check email in 30 seconds
    echo.
    echo 🎉 Done! Automatic checking every 48 hours
) else (
    echo.
    echo ❌ Push failed. Common issues:
    echo   - Check your GitHub repo URL
    echo   - Make sure you have push permissions
    echo   - Try: git push -u origin main (with GitHub authentication)
)

pause
