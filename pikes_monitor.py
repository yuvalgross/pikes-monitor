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


def format_current_events(events):
    """Format current events for email"""
    html = ""
    for day in sorted(events.keys(), key=lambda x: int(x.split()[-1])):
        day_events = events[day].get("events", [])
        if day_events:
            html += f'<p style="margin: 10px 0; color: #666;"><strong>{day}</strong></p>'
            for event in day_events[:3]:
                html += f'<p style="margin: 5px 0 5px 20px; color: #666; font-size: 13px;">• {event}</p>'
            if len(day_events) > 3:
                html += f'<p style="margin: 5px 0 5px 20px; color: #999; font-size: 12px;">... and {len(day_events)-3} more</p>'
    return html if html else '<p style="color: #666;">No changes yet</p>'

def format_changes(changes):
    """Format changes for email"""
    if not changes:
        return '<p style="color: #666;">✅ No changes detected</p>'
    html = ""
    for day, change_list in changes.items():
        html += f'<p style="margin: 10px 0; color: #92400e;"><strong>🆕 {day}</strong></p>'
        for change in change_list:
            html += f'<p style="margin: 5px 0 5px 20px; color: #666; font-size: 13px;">• {change}</p>'
    return html


def send_email(changes, current_events=None, previous_events=None):
    """Send comprehensive email with CURRENT + CHANGES"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    from datetime import datetime
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build HTML email
    html = """<html><body style="font-family: Arial, sans-serif; color: #333; background: #f5f5f5; padding: 20px;">
<div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">

<h1 style="color: #ff6b9d; text-align: center; margin: 0 0 10px 0;">🎵 Pikes Ibiza</h1>
<h2 style="text-align: center; color: #666; font-size: 16px; margin: 0 0 30px 0;">June 8-24 Lineup</h2>

<!-- CURRENT EVENTS SECTION -->
<div style="background: #f0f9ff; padding: 25px; border-radius: 10px; margin-bottom: 30px; border-left: 5px solid #ff6b9d;">
<h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 18px;">📅 CURRENT LINEUP</h3>

""" + get_current_events_html(current_events) + """

</div>

<!-- CHANGES SECTION -->
<div style="background: #fef3c7; padding: 25px; border-radius: 10px; border-left: 5px solid #f59e0b;">
<h3 style="margin: 0 0 20px 0; color: #92400e; font-size: 18px;">🔄 WHAT CHANGED</h3>

""" + get_changes_html(changes) + """

</div>

<div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-top: 30px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee;">
<p style="margin: 5px 0;">Email sent: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
<p style="margin: 5px 0;">Monitor checks every 48 hours • Next update: June 2-3</p>
</div>

</div>
</body></html>"""
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎵 Pikes Ibiza - Current Lineup & Updates"
    msg["From"] = EMAIL
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html, "html"))
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, RECIPIENT, msg.as_string())
        server.quit()
        print("✅ Email sent!")
    except Exception as e:
        print(f"Email error: {e}")


def get_current_events_html(events):
    """Format current events for HTML"""
    if not events:
        return "<p style='color: #666;'>Loading events...</p>"
    
    html = ""
    for day_num in range(8, 25):
        day_str = f"June {day_num}"
        if day_str in events:
            day_events = events[day_str].get("events", [])
            if day_events:
                days = {8:"Mon",9:"Tue",10:"Wed",11:"Thu",12:"Fri",13:"Sat",14:"Sun",15:"Mon",16:"Tue",17:"Wed",18:"Thu",19:"Fri",20:"Sat",21:"Sun",22:"Mon",23:"Tue",24:"Wed"}
                day_name = days.get(day_num, "")
                
                html += f'<div style="margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px;">'
                html += f'<h4 style="margin: 0 0 10px 0; color: #1f2937;">📅 {day_str} ({day_name})</h4>'
                
                for event in day_events:
                    html += f'<p style="margin: 5px 0; color: #555; font-size: 13px; line-height: 1.5;">• {event}</p>'
                
                html += '</div>'
    
    return html if html else "<p style='color: #666;'>No events scheduled</p>"


def get_changes_html(changes):
    """Format changes for HTML"""
    if not changes:
        return "<p style='color: #666;'>✅ No changes detected</p>"
    
    html = ""
    for day, items in changes.items():
        html += f'<div style="margin-bottom: 15px; padding: 12px; background: white; border-radius: 8px;">'
        html += f'<h4 style="margin: 0 0 8px 0; color: #92400e;">🆕 {day}</h4>'
        
        for item in items:
            html += f'<p style="margin: 5px 0; color: #856404; font-size: 13px;">✓ {item}</p>'
        
        html += '</div>'
    
    return html

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
            send_email(result["changes"], events, previous)
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
