#!/usr/bin/env python3
"""
Pikes Ibiza Event Monitor - Improved Selenium with better wait strategies
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
print("🎵 PIKES IBIZA MONITOR")
print("="*70)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Monitoring: Jun 8-24, 2026")
print("\n📋 ENVIRONMENT:")
print(f"  Email configured: {'✅' if EMAIL_RECIPIENT else '❌'}")
print(f"  Selenium available: {'✅' if SELENIUM_AVAILABLE else '❌'}")
print("="*70)

def fetch_pikes_selenium():
    """Fetch using Selenium with improved wait strategies"""
    print("\n🌐 Fetching Pikes (Selenium + JavaScript)...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        print("   Starting Chrome browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("   Loading page...")
        driver.get(PIKES_URL)
        
        # Wait for page to load - look for specific indicators
        print("   Waiting for page content...")
        
        # Wait for body to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Close any cookie popups that might block content
        try:
            accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            accept_button.click()
            print("   Closed cookie dialog...")
        except:
            pass
        
        # Try to find event elements
        print("   Waiting for event content...")
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), 'Jun')]")) > 0 or
                     len(d.find_elements(By.XPATH, "//article")) > 0 or
                     len(d.find_elements(By.XPATH, "//div[@class*='event']")) > 0 or
                     len(d.find_elements(By.XPATH, "//div[@class*='date']")) > 0
        )
        
        # Scroll down to trigger lazy loading
        print("   Scrolling to load more content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Wait a bit more for any remaining dynamic content
        time.sleep(3)
        
        html = driver.page_source
        driver.quit()
        
        print(f"   ✅ Fetched {len(html)} characters")
        return html
    
    except Exception as e:
        print(f"   ⚠️  Selenium failed: {str(e)[:80]}")
        try:
            driver.quit()
        except:
            pass
        return None

def fetch_pikes_requests():
    """Fallback to requests"""
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
    """Extract events - look for multiple date formats"""
    print(f"\n🔍 Extracting events...")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    all_text = soup.get_text()
    
    # Try different date formats
    date_formats = {
        "Jun 8": ["Jun 8", "8 Jun", "8 June", "June 8", "08/06"],
        "Jun 9": ["Jun 9", "9 Jun", "9 June", "June 9", "09/06"],
        "Jun 10": ["Jun 10", "10 Jun", "10 June", "June 10", "10/06"],
        # ... etc for other dates
    }
    
    events = {}
    found_count = 0
    
    for date_str in YOUR_DATES:
        found = False
        details = ""
        
        # Check for the date in various formats
        if date_str in all_text:
            found = True
        elif date_str.lower() in all_text.lower():
            found = True
        else:
            # Try other common formats
            day = date_str.split()[-1]
            if f"{day} Jun" in all_text or f"{day} June" in all_text:
                found = True
        
        if found:
            found_count += 1
            # Get context
            for elem in soup.find_all(['div', 'article', 'section']):
                elem_text = elem.get_text().lower()
                if day in elem_text and ('jun' in elem_text or 'june' in elem_text):
                    details = elem.get_text(strip=True)[:200]
                    break
        
        events[date_str] = {"found": found, "details": details}
    
    print(f"   ✅ Found on {found_count}/{len(YOUR_DATES)} days")
    
    if found_count == 0:
        print(f"\n   📊 DEBUGGING INFO:")
        print(f"   HTML size: {len(html_content)} chars")
        print(f"   Looking for: 'Jun', 'June', 'June 8', etc")
        
        # Check what we actually got
        if "June" in all_text or "jun" in all_text.lower():
            print(f"   ✅ Found 'June' in text")
            idx = all_text.lower().find("june")
            print(f"   Context: ...{all_text[max(0, idx-100):idx+200]}...")
        else:
            print(f"   ❌ No 'June' found in page")
            print(f"   First 500 chars: {all_text[:500]}")
    
    return events

def load_snapshot():
    """Load previous snapshot"""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                print("✅ Loaded previous snapshot")
                return json.load(f)
        except:
            return None
    print("📝 First run - no previous snapshot")
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
        print(f"   ⏭️ Credentials not configured")
        return False
    
    try:
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
        
        print(f"   ✅ Email sent to {EMAIL_RECIPIENT}!")
        return True
    except Exception as e:
        print(f"   ❌ Email error: {e}")
        return False

def main():
    try:
        html = None
        
        # Try Selenium first
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
            print(f"⚠️ {len(result['changes'])} change(s)!")
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
    success = main()
    sys.exit(0 if success else 1)
