#!/usr/bin/env python3
"""
Pikes Ibiza Event Monitor
Checks for changes in your Ibiza trip events (Jun 8-24)
Uses Selenium for JavaScript-rendered content
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

# Try to import selenium, fall back to requests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    import requests
    from bs4 import BeautifulSoup

# Configuration
PIKES_URL = "https://www.pikesibiza.com/whats-on/"
YOUR_DATES = [
    "Jun 8", "Jun 9", "Jun 10", "Jun 11", "Jun 12", "Jun 13", "Jun 14",
    "Jun 15", "Jun 16", "Jun 17", "Jun 18", "Jun 19", "Jun 20", "Jun 21",
    "Jun 22", "Jun 23", "Jun 24"
]

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
print(f"Method: {'Selenium (JavaScript-enabled)' if SELENIUM_AVAILABLE else 'Requests (Static HTML)'}")
print("\n📋 ENVIRONMENT VARIABLES:")
print(f"  NOTIFY_EMAIL: {'✅ SET' if EMAIL_RECIPIENT else '❌ NOT SET'}")
print(f"  GMAIL_ADDRESS: {'✅ SET' if GMAIL_ADDRESS else '❌ NOT SET'}")
print(f"  GMAIL_PASSWORD: {'✅ SET' if GMAIL_PASSWORD else '❌ NOT SET'}")
print(f"  DISCORD_WEBHOOK: {'✅ SET' if DISCORD_WEBHOOK else '⏭️ OPTIONAL'}")
print("="*70)

def fetch_pikes_events_selenium():
    """Fetch Pikes events using Selenium (handles JavaScript)"""
    print("\n🌐 Fetching Pikes website (Selenium - JavaScript enabled)...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        driver.get(PIKES_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
        )
        
        # Wait a bit for JavaScript to render
        time.sleep(3)
        
        html = driver.page_source
        driver.quit()
        
        print(f"   ✅ Fetched {len(html)} characters")
        return html
    
    except Exception as e:
        print(f"   ⚠️  Selenium failed: {e}")
        print(f"   Falling back to static HTML...")
        return None

def fetch_pikes_events_requests():
    """Fetch Pikes events using requests (static HTML only)"""
    print("\n🌐 Fetching Pikes website (Static HTML)...")
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
    """Extract events from HTML content"""
    print(f"\n🔍 Extracting events for {len(YOUR_DATES)} days...")
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    events = {}
    found_count = 0
    
    # Get all text content
    all_text = soup.get_text().lower()
    
    for date_str in YOUR_DATES:
        event_data = {
            "date": date_str,
            "found": date_str.lower() in all_text,
            "details": ""
        }
        
        if event_data["found"]:
            found_count += 1
            # Try to find context around the date
            for element in soup.find_all(['div', 'section', 'article']):
                if date_str.lower() in element.get_text().lower():
                    details = element.get_text(strip=True)[:250]
                    event_data["details"] = details
                    break
        
        events[date_str] = event_data
    
    print(f"   ✅ Found events on {found_count}/{len(YOUR_DATES)} days")
    
    if found_count == 0:
        print(f"   ⚠️  WARNING: No dates found. Website might use different format.")
    
    return events

def load_snapshot():
    """Load previous snapshot"""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded previous snapshot")
                return data
        except Exception as e:
            print(f"⚠️  Could not load snapshot: {e}")
            return None
    else:
        print("📝 No previous snapshot found (first run)")
    return None

def save_snapshot(events):
    """Save snapshot"""
    try:
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"💾 Saved snapshot")
    except Exception as e:
        print(f"❌ Error saving snapshot: {e}")

def detect_changes(old_events, new_events):
    """Detect changes"""
    if not old_events:
        return {"new_check": True, "changes": []}
    
    changes = []
    for date, new_data in new_events.items():
        old_data = old_events.get(date, {})
        if old_data.get("found") != new_data.get("found"):
            changes.append({
                "date": date,
                "message": f"{'🆕 New' if new_data.get('found') else '⚠️ Removed'}: {date}"
            })
    
    return {"new_check": False, "changes": changes}

def send_email_notification(changes):
    """Send email"""
    print(f"\n📧 Sending email notification...")
    
    if not EMAIL_RECIPIENT or not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        print(f"   ⏭️ Credentials not configured")
        return False
    
    try:
        print(f"   Connecting to Gmail SMTP...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "🎉 Pikes Events - Your Trip (Jun 8-24)"
        message["From"] = GMAIL_ADDRESS
        message["To"] = EMAIL_RECIPIENT
        
        body = f"<html><body><h2>🎵 Pikes Update</h2><ul>"
        for change in changes:
            body += f"<li>{change['message']}</li>"
        body += f"</ul></body></html>"
        
        message.attach(MIMEText(body, "html"))
        server.sendmail(GMAIL_ADDRESS, EMAIL_RECIPIENT, message.as_string())
        server.quit()
        
        print(f"   ✅ Email sent!")
        return True
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    try:
        # Try Selenium first if available
        html = None
        if SELENIUM_AVAILABLE:
            html = fetch_pikes_events_selenium()
        
        # Fall back to requests
        if not html:
            html = fetch_pikes_events_requests()
        
        if not html:
            print("\n❌ Could not fetch website")
            return False
        
        current_events = extract_events(html)
        previous_events = load_snapshot()
        result = detect_changes(previous_events, current_events)
        save_snapshot(current_events)
        
        print("\n" + "="*70)
        print("📊 RESULTS:")
        print("="*70)
        
        if result["new_check"]:
            print("✅ First check - baseline established")
            found = sum(1 for e in current_events.values() if e["found"])
            print(f"   {found}/{len(YOUR_DATES)} days have events")
        elif result["changes"]:
            print(f"⚠️ Changes detected!")
            for change in result["changes"]:
                print(f"  {change['message']}")
            send_email_notification(result["changes"])
        else:
            print("✅ No changes")
            found = sum(1 for e in current_events.values() if e["found"])
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
