#!/usr/bin/env python3
"""
Pikes Ibiza Event Monitor
Checks for changes in your Ibiza trip events (Jun 8-24)
Sends notifications via email or Discord
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import traceback

# Configuration
PIKES_URL = "https://www.pikesibiza.com/whats-on/"
TRIP_START = "Jun 8"
TRIP_END = "Jun 24"
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
print(f"Monitoring dates: {TRIP_START} to {TRIP_END}")
print("\n📋 ENVIRONMENT VARIABLES:")
print(f"  NOTIFY_EMAIL: {EMAIL_RECIPIENT if EMAIL_RECIPIENT else '❌ NOT SET'}")
print(f"  GMAIL_ADDRESS: {GMAIL_ADDRESS if GMAIL_ADDRESS else '❌ NOT SET'}")
print(f"  GMAIL_PASSWORD: {'✅ SET' if GMAIL_PASSWORD else '❌ NOT SET'}")
print(f"  DISCORD_WEBHOOK: {'✅ SET' if DISCORD_WEBHOOK else '⏭️ OPTIONAL'}")
print("="*70)

def fetch_pikes_events():
    """Fetch current Pikes events"""
    print("\n🌐 Fetching Pikes website...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PIKES_URL, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"   ✅ Fetched {len(response.text)} characters")
        return response.text
    except Exception as e:
        print(f"   ❌ Error fetching Pikes: {e}")
        traceback.print_exc()
        return None

def extract_events(html_content):
    """Extract events for your trip dates from HTML"""
    print(f"\n🔍 Extracting events for {len(YOUR_DATES)} days...")
    soup = BeautifulSoup(html_content, 'html.parser')
    events = {}
    
    for date_str in YOUR_DATES:
        event_data = {
            "date": date_str,
            "found": False,
            "details": ""
        }
        
        for element in soup.find_all(['h2', 'h3', 'div']):
            text = element.get_text(strip=True)
            if date_str in text:
                event_data["found"] = True
                parent = element.find_parent(['div', 'article', 'section'])
                if parent:
                    details = parent.get_text(strip=True)[:250]
                    event_data["details"] = details
                break
        
        events[date_str] = event_data
    
    found_count = sum(1 for e in events.values() if e["found"])
    print(f"   ✅ Found events on {found_count}/{len(YOUR_DATES)} days")
    return events

def load_snapshot():
    """Load previous snapshot if exists"""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded previous snapshot ({len(data)} dates)")
                return data
        except Exception as e:
            print(f"⚠️ Could not load snapshot: {e}")
            return None
    else:
        print("📝 No previous snapshot found (first run)")
    return None

def save_snapshot(events):
    """Save current events as snapshot"""
    try:
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"💾 Saved snapshot ({len(events)} dates)")
    except Exception as e:
        print(f"❌ Error saving snapshot: {e}")

def detect_changes(old_events, new_events):
    """Compare old and new events, return changes"""
    if not old_events:
        return {"new_check": True, "changes": []}
    
    changes = []
    
    for date, new_data in new_events.items():
        old_data = old_events.get(date, {})
        
        if old_data.get("found") and not new_data.get("found"):
            changes.append({
                "type": "removed",
                "date": date,
                "message": f"⚠️ Event removed on {date}"
            })
        
        if not old_data.get("found") and new_data.get("found"):
            changes.append({
                "type": "new",
                "date": date,
                "message": f"🆕 New event found on {date}"
            })
        
        if old_data.get("details") != new_data.get("details"):
            if new_data.get("details") and old_data.get("details"):
                changes.append({
                    "type": "updated",
                    "date": date,
                    "message": f"🔄 Event updated on {date}"
                })
    
    return {"new_check": False, "changes": changes}

def send_email_notification(changes):
    """Send email notification of changes"""
    print(f"\n📧 Sending email notification...")
    
    if not EMAIL_RECIPIENT or EMAIL_RECIPIENT == "your-email@gmail.com":
        print(f"   ⏭️ NOTIFY_EMAIL not configured")
        return False
    
    if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        print(f"   ❌ Gmail credentials missing")
        print(f"      GMAIL_ADDRESS: {GMAIL_ADDRESS if GMAIL_ADDRESS else '❌ NOT SET'}")
        print(f"      GMAIL_PASSWORD: {'✅ SET' if GMAIL_PASSWORD else '❌ NOT SET'}")
        return False
    
    try:
        print(f"   Connecting to smtp.gmail.com:465...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        print(f"   ✅ Connected")
        
        print(f"   Logging in as {GMAIL_ADDRESS}...")
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        print(f"   ✅ Authenticated")
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "🎉 Pikes Ibiza Events - Your Trip (Jun 8-24)"
        message["From"] = GMAIL_ADDRESS
        message["To"] = EMAIL_RECIPIENT
        
        body = f"""
        <html>
          <body>
            <h2>🎵 Pikes Ibiza Events Update</h2>
            <p><strong>Your Trip:</strong> Jun 8-24, 2026</p>
            <p><strong>Check Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <h3>Changes Detected:</h3>
            <ul>
        """
        
        for change in changes:
            body += f"<li>{change['message']}</li>"
        
        body += """
            </ul>
            <p><a href="https://www.pikesibiza.com/whats-on/">View Full Schedule →</a></p>
            <hr>
            <p style="font-size: 12px; color: #666;">
              Monitoring Pikes events for your entire Ibiza trip (Jun 8-24)
            </p>
          </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        print(f"   Sending to {EMAIL_RECIPIENT}...")
        server.sendmail(GMAIL_ADDRESS, EMAIL_RECIPIENT, message.as_string())
        server.quit()
        
        print(f"   ✅ Email sent successfully!")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print(f"      Check Gmail app password")
        return False
    except Exception as e:
        print(f"   ❌ Email error: {e}")
        traceback.print_exc()
        return False

def send_discord_notification(changes):
    """Send Discord webhook notification"""
    if not DISCORD_WEBHOOK:
        return False
    
    try:
        embed = {
            "title": "🎵 Pikes Ibiza Events Update",
            "description": f"Your trip: Jun 8-24, 2026",
            "color": 16711680,
            "timestamp": datetime.now().isoformat(),
            "fields": []
        }
        
        for change in changes:
            embed["fields"].append({
                "name": change['date'],
                "value": change['message'],
                "inline": False
            })
        
        payload = {"embeds": [embed]}
        requests.post(DISCORD_WEBHOOK, json=payload)
        print(f"   ✅ Discord notification sent")
        return True
    
    except Exception as e:
        print(f"   ❌ Discord error: {e}")
        return False

def main():
    """Main monitoring function"""
    try:
        # Fetch current events
        html = fetch_pikes_events()
        if not html:
            print("\n❌ FAILED: Could not fetch Pikes website")
            return False
        
        # Extract events for your trip dates
        current_events = extract_events(html)
        
        # Load previous snapshot
        previous_events = load_snapshot()
        
        # Detect changes
        result = detect_changes(previous_events, current_events)
        
        # Save current snapshot
        save_snapshot(current_events)
        
        # Report status
        print("\n" + "="*70)
        print("📊 RESULTS:")
        print("="*70)
        
        if result["new_check"]:
            print("✅ First check - baseline established")
            found_count = sum(1 for e in current_events.values() if e["found"])
            print(f"   {found_count}/{len(YOUR_DATES)} days have events")
        
        elif result["changes"]:
            print(f"⚠️ {len(result['changes'])} change(s) detected!\n")
            for change in result["changes"]:
                print(f"  {change['message']}")
            
            # Send notifications
            send_email_notification(result["changes"])
            send_discord_notification(result["changes"])
        
        else:
            print("✅ No changes detected")
            found_count = sum(1 for e in current_events.values() if e["found"])
            print(f"   {found_count}/{len(YOUR_DATES)} days have events")
        
        print("="*70)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("="*70 + "\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
