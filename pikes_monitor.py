#!/usr/bin/env python3
"""
Pikes Ibiza Event Monitor - Fixed for actual Pikes HTML structure
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
import re

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

YOUR_DATES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

PIKES_URL = "https://www.pikesibiza.com/whats-on/"
SNAPSHOT_FILE = "pikes_snapshot.json"
EMAIL_RECIPIENT = os.getenv("NOTIFY_EMAIL", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")

print("\n" + "="*70)
print("🎵 PIKES IBIZA MONITOR")
print("="*70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Monitoring: June 8-24, 2026 (17 days)")
print("="*70)

def fetch_pikes_selenium():
    """Fetch using Selenium"""
    print("\n🌐 Fetching (Selenium)...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(PIKES_URL)
        
        # Wait for content
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), 'June')]")) > 0
        )
        
        # Close cookies
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]").click()
        except:
            pass
        
        time.sleep(3)
        html = driver.page_source
        driver.quit()
        
        print(f"   ✅ Fetched {len(html)} chars")
        return html
    except Exception as e:
        print(f"   ⚠️  Failed: {str(e)[:60]}")
        return None

def fetch_pikes_requests():
    """Fetch static HTML"""
    print("\n🌐 Fetching (Static)...")
    try:
        response = requests.get(PIKES_URL, headers={
            'User-Agent': 'Mozilla/5.0'
        }, timeout=10)
        print(f"   ✅ Fetched {len(response.text)} chars")
        return response.text
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def extract_events(html_content):
    """Extract events - match actual HTML structure"""
    print(f"\n🔍 Extracting events...")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    all_text = soup.get_text()
    
    events = {}
    found_count = 0
    
    # Look for "June 8", "June 9", etc in the text
    # The actual HTML shows: "Monday, June 8 - 21:00" format
    
    for day_num in YOUR_DATES:
        # Multiple patterns to match
        patterns = [
            f"June {day_num}",      # "June 8"
            f"june {day_num}",      # case insensitive
            f", {day_num} ",        # ", 8 " (sometimes dates appear this way)
        ]
        
        found = False
        details = ""
        
        for pattern in patterns:
            if pattern in all_text or pattern.lower() in all_text.lower():
                found = True
                found_count += 1
                
                # Get context around the match
                idx = all_text.lower().find(pattern.lower())
                if idx >= 0:
                    details = all_text[max(0, idx-100):idx+300].strip()
                break
        
        events[f"Jun {day_num}"] = {
            "found": found,
            "details": details
        }
    
    print(f"   ✅ Found on {found_count}/{len(YOUR_DATES)} days")
    
    if found_count == 0:
        print(f"\n   ⚠️  No events detected!")
        # Debug: check what we actually found
        if "June" in all_text:
            idx = all_text.lower().find("june")
            print(f"\n   Found 'June' at position {idx}")
            print(f"   Context: {all_text[max(0, idx-50):idx+500]}")
    else:
        print(f"\n   ✅ SUCCESS! Found {found_count} days with events")
        # Show which days
        found_days = [e.split()[-1] for e, d in events.items() if d["found"]]
        print(f"   Days: {', '.join(found_days)}")
    
    return events

def load_snapshot():
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                print("✅ Loaded snapshot")
                return json.load(f)
        except:
            return None
    print("📝 First run")
    return None

def save_snapshot(events):
    try:
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        print("💾 Saved snapshot")
    except Exception as e:
        print(f"❌ Save error: {e}")

def detect_changes(old, new):
    if not old:
        return {"new_check": True, "changes": []}
    changes = []
    for date, new_data in new.items():
        old_data = old.get(date, {})
        if old_data.get("found") != new_data.get("found"):
            msg = f"{'🆕' if new_data['found'] else '❌'} {date}"
            changes.append({"message": msg})
    return {"new_check": False, "changes": changes}

def send_email(changes):
    print(f"\n📧 Sending email...")
    if not EMAIL_RECIPIENT or not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        print(f"   ⏭️  Not configured")
        return False
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎉 Pikes Events Update"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = EMAIL_RECIPIENT
        
        html = "<html><body><h2>🎵 Pikes Update</h2><ul>"
        for c in changes:
            html += f"<li>{c['message']}</li>"
        html += "</ul></body></html>"
        
        msg.attach(MIMEText(html, "html"))
        server.sendmail(GMAIL_ADDRESS, EMAIL_RECIPIENT, msg.as_string())
        server.quit()
        
        print(f"   ✅ Sent!")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    try:
        html = None
        if SELENIUM_AVAILABLE:
            html = fetch_pikes_selenium()
        if not html:
            html = fetch_pikes_requests()
        if not html:
            print("\n❌ Could not fetch")
            return False
        
        events = extract_events(html)
        previous = load_snapshot()
        result = detect_changes(previous, events)
        save_snapshot(events)
        
        print("\n" + "="*70)
        if result["new_check"]:
            print("✅ Baseline established")
            found = sum(1 for e in events.values() if e["found"])
            print(f"   {found}/{len(YOUR_DATES)} days have events")
        elif result["changes"]:
            print(f"⚠️ Changes detected:")
            for c in result["changes"]:
                print(f"  {c['message']}")
            send_email(result["changes"])
        else:
            print("✅ No changes")
            found = sum(1 for e in events.values() if e["found"])
            print(f"   {found}/{len(YOUR_DATES)} days have events")
        
        print("="*70)
        return True
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
