#!/usr/bin/env python3
"""
Pikes Ibiza Event Monitor - Using webdriver-manager for automatic Chrome setup
"""

import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import traceback
import time
import requests
from bs4 import BeautifulSoup

# Try Selenium with webdriver-manager (handles Chrome automatically)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

YOUR_DATES = [
    "Jun 8", "Jun 9", "Jun 10", "Jun 11", "Jun 12", "Jun 13", "Jun 14",
    "Jun 15", "Jun 16", "Jun 17", "Jun 18", "Jun 19", "Jun 20", "Jun 21",
    "Jun 22", "Jun 23", "Jun 24"
]

PIKES_URL = "https://www.pikesibiza.com/whats-on/"
SNAPSHOT_FILE = "pikes_snapshot.json"
EMAIL_RECIPIENT = os.getenv("NOTIFY_EMAIL", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

print("\n" + "="*70)
print("🎵 PIKES IBIZA MONITOR - DEBUG MODE")
print("="*70)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Monitoring: Jun 8-24, 2026")
print(f"Selenium Available: {'✅ YES' if SELENIUM_AVAILABLE else '❌ NO'}")
print("\n📋 ENVIRONMENT VARIABLES:")
print(f"  NOTIFY_EMAIL: {'✅ SET' if EMAIL_RECIPIENT else '❌ NOT SET'}")
print(f"  GMAIL_ADDRESS: {'✅ SET' if GMAIL_ADDRESS else '❌ NOT SET'}")
print(f"  GMAIL_PASSWORD: {'✅ SET' if GMAIL_PASSWORD else '❌ NOT SET'}")
print("="*70)

def fetch_pikes_selenium():
    """Fetch using Selenium with automatic Chrome setup"""
    print("\n🌐 Fetching with Selenium (JavaScript enabled)...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        print("   Setting up Chrome with webdriver-manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("   Loading Pikes website...")
        driver.get(PIKES_URL)
        
        # Wait for content
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(5)  # Wait for JS to render
        html = driver.page_source
        driver.quit()
        
        print(f"   ✅ Fetched {len(html)} characters with Selenium")
        return html
    
    except Exception as e:
        print(f"   ⚠️  Selenium error: {str(e)[:100]}")
        return None

def fetch_pikes_requests():
    """Fallback: fetch static HTML"""
    print("\n🌐 Fetching static HTML...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PIKES_URL, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"   ✅ Fetched {len(response.text)} characters")
        return response.text
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def extract_events(html_content):
    """Extract events from HTML"""
    print(f"\n🔍 Extracting events for {len(YOUR_DATES)} days...")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    all_text = soup.get_text()
    
    events = {}
    found_count = 0
    
    for date_str in YOUR_DATES:
        found = False
        details = ""
        
        # Check if date is in the page
        if date_str in all_text or date_str.lower() in all_text.lower():
            found = True
            found_count += 1
            
            # Get some context
            for elem in soup.find_all(['div', 'section']):
                if date_str.lower() in elem.get_text().lower():
                    details = elem.get_text(strip=True)[:200]
                    break
        
        events[date_str] = {"found": found, "details": details}
    
    print(f"   ✅ Found events on {found_count}/{len(YOUR_DATES)} days")
    
    if found_count == 0:
        print(f"   ⚠️  No dates found - checking raw HTML...")
        # Check first 2000 chars for any date markers
        print(f"   First 1000 chars: {all_text[:1000]}")
    
    return events

def load_snapshot():
    """Load previous snapshot"""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                data = json.load(f)
                print("✅ Loaded previous snapshot")
                return data
        except:
            return None
    print("📝 No previous snapshot (first run)")
    return None

def save_snapshot(events):
    """Save snapshot"""
    try:
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        print("💾 Saved snapshot")
    except Exception as e:
        print(f"❌ Save error: {e}")

def detect_changes(old, new):
    """Detect changes"""
    if not old:
        return {"new_check": True, "changes": []}
    changes = []
    for date, new_data in new.items():
        old_data = old.get(date, {})
        if old_data.get("found") != new_data.get("found"):
            msg = f"{'🆕 NEW' if new_data['found'] else '❌ REMOVED'}: {date}"
            changes.append({"date": date, "message": msg})
    return {"new_check": False, "changes": changes}

def send_email(changes):
    """Send email notification"""
    print(f"\n📧 Sending email...")
    
    if not EMAIL_RECIPIENT or not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        print(f"   ⏭️ Credentials missing")
        return False
    
    try:
        print(f"   Connecting to Gmail...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎉 Pikes Ibiza Events Update"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = EMAIL_RECIPIENT
        
        html = "<html><body><h2>🎵 Pikes Update</h2><ul>"
        for c in changes:
            html += f"<li>{c['message']}</li>"
        html += "</ul></body></html>"
        
        msg.attach(MIMEText(html, "html"))
        server.sendmail(GMAIL_ADDRESS, EMAIL_RECIPIENT, msg.as_string())
        server.quit()
        
        print(f"   ✅ Email sent!")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    try:
        # Try Selenium first
        html = None
        if SELENIUM_AVAILABLE:
            html = fetch_pikes_selenium()
        
        # Fallback to requests
        if not html:
            html = fetch_pikes_requests()
        
        if not html:
            print("\n❌ FAILED: Could not fetch website")
            return False
        
        events = extract_events(html)
        previous = load_snapshot()
        result = detect_changes(previous, events)
        save_snapshot(events)
        
        print("\n" + "="*70)
        print("📊 RESULTS:")
        print("="*70)
        
        if result["new_check"]:
            print("✅ First check - baseline established")
            found = sum(1 for e in events.values() if e["found"])
            print(f"   {found}/{len(YOUR_DATES)} days have events")
        elif result["changes"]:
            print(f"⚠️ {len(result['changes'])} change(s) detected!")
            for c in result["changes"]:
                print(f"  {c['message']}")
            send_email(result["changes"])
        else:
            print("✅ No changes detected")
            found = sum(1 for e in events.values() if e["found"])
            print(f"   {found}/{len(YOUR_DATES)} days have events")
        
        print("="*70)
        return True
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
