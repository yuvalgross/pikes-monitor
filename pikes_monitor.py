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
EMAIL_RECIPIENT = os.getenv("NOTIFY_EMAIL", "your-email@gmail.com")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

def fetch_pikes_events():
    """Fetch current Pikes events"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PIKES_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error fetching Pikes: {e}")
        return None

def extract_events(html_content):
    """Extract events for your trip dates from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = {}
    
    for date_str in YOUR_DATES:
        event_data = {
            "date": date_str,
            "found": False,
            "details": ""
        }
        
        # Look for event headers containing the date
        for element in soup.find_all(['h2', 'h3', 'div']):
            text = element.get_text(strip=True)
            if date_str in text:
                event_data["found"] = True
                # Get surrounding context
                parent = element.find_parent(['div', 'article', 'section'])
                if parent:
                    details = parent.get_text(strip=True)[:250]
                    event_data["details"] = details
                break
        
        events[date_str] = event_data
    
    return events

def load_snapshot():
    """Load previous snapshot if exists"""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_snapshot(events):
    """Save current events as snapshot"""
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def detect_changes(old_events, new_events):
    """Compare old and new events, return changes"""
    if not old_events:
        return {"new_check": True, "changes": []}
    
    changes = []
    
    for date, new_data in new_events.items():
        old_data = old_events.get(date, {})
        
        # Check if event was found before but not now
        if old_data.get("found") and not new_data.get("found"):
            changes.append({
                "type": "removed",
                "date": date,
                "message": f"⚠️ Event removed on {date}"
            })
        
        # Check if event is now found but wasn't before
        if not old_data.get("found") and new_data.get("found"):
            changes.append({
                "type": "new",
                "date": date,
                "message": f"🆕 New event found on {date}"
            })
        
        # Check if details changed
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
    if not EMAIL_RECIPIENT or EMAIL_RECIPIENT == "your-email@gmail.com":
        print("⏭️ Email not configured. Set NOTIFY_EMAIL env var")
        return
    
    try:
        smtp_server = "smtp.gmail.com"
        sender_email = os.getenv("GMAIL_ADDRESS")
        sender_password = os.getenv("GMAIL_PASSWORD")
        
        if not sender_email or not sender_password:
            print("⏭️ Gmail credentials not set")
            return
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "🎉 Pikes Ibiza Events - Your Trip (Jun 8-24)"
        message["From"] = sender_email
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
        
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, EMAIL_RECIPIENT, message.as_string())
        
        print(f"✉️ Email sent to {EMAIL_RECIPIENT}")
    
    except Exception as e:
        print(f"❌ Email error: {e}")

def send_discord_notification(changes):
    """Send Discord webhook notification"""
    if not DISCORD_WEBHOOK:
        return
    
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
        print("✅ Discord notification sent")
    
    except Exception as e:
        print(f"❌ Discord error: {e}")

def main():
    """Main monitoring function"""
    print(f"\n🔍 Checking Pikes Ibiza (Jun 8-24)... {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Fetch current events
    html = fetch_pikes_events()
    if not html:
        return
    
    # Extract events for your trip dates
    current_events = extract_events(html)
    
    # Load previous snapshot
    previous_events = load_snapshot()
    
    # Detect changes
    result = detect_changes(previous_events, current_events)
    
    # Save current snapshot
    save_snapshot(current_events)
    
    # Report status
    if result["new_check"]:
        print("✅ First check - baseline established")
        print(f"\n📅 Monitoring {len(YOUR_DATES)} days of your trip:")
        found_count = sum(1 for e in current_events.values() if e["found"])
        print(f"   {found_count}/{len(YOUR_DATES)} days have events listed")
    
    elif result["changes"]:
        print(f"\n⚠️ {len(result['changes'])} change(s) detected!\n")
        for change in result["changes"]:
            print(f"  {change['message']}")
        
        # Send notifications
        send_email_notification(result["changes"])
        send_discord_notification(result["changes"])
    
    else:
        print("✅ No changes detected")
        found_count = sum(1 for e in current_events.values() if e["found"])
        print(f"   {found_count}/{len(YOUR_DATES)} days have events")

if __name__ == "__main__":
    main()
