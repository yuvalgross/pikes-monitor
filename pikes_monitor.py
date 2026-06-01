#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor
Tracks DJ lineups with detailed before/after (Jun 8-24)
"""

import requests
import json
import os
import re
from datetime import datetime

PIKES_URL = "https://www.pikesibiza.com/en/program/"

def fetch_pikes_program():
    """Fetch Pikes Ibiza program"""
    print("🌐 Fetching Pikes program...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(PIKES_URL, headers=headers, timeout=15, allow_redirects=True)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Fetched {len(response.text):,} characters")
            return extract_events(response.text)
        else:
            print(f"   ❌ Error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {}

def extract_events(html_content):
    """Extract events for Jun 8-24"""
    from bs4 import BeautifulSoup
    
    events = {}
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # Extract June 8-24 events
    for day in range(8, 25):
        # Look for date patterns
        patterns = [
            f"June {day}",
            f"Jun {day}",
        ]
        
        for pattern in patterns:
            if pattern in text:
                # Find the date
                idx = text.find(pattern)
                
                # Get context (next 800 chars)
                snippet = text[idx:idx+800]
                
                # Get first meaningful lines
                lines = [l.strip() for l in snippet.split('\n') if l.strip() and len(l.strip()) > 3]
                
                # Filter out noise
                event_lines = []
                for line in lines[:12]:
                    # Skip if too long or looks like nav
                    if len(line) < 200 and not any(x in line.lower() for x in ['home', 'privacy', 'accept', 'cookie']):
                        event_lines.append(line)
                
                # Join first 3 meaningful lines
                if event_lines:
                    event_text = " | ".join(event_lines[:3])
                    events[pattern] = event_text
                    break
    
    return events

def load_snapshot(filename="pikes_snapshot.json"):
    """Load previous snapshot"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_snapshot(data, filename="pikes_snapshot.json"):
    """Save current snapshot"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def format_event(value):
    """Format event text - handle both string and dict"""
    if not value:
        return "(No event info)"
    
    # Handle old dict format
    if isinstance(value, dict):
        if 'events' in value and isinstance(value['events'], list):
            return " | ".join(str(e) for e in value['events'][:3])
        return str(value)
    
    # String format
    return str(value).strip()

def detect_changes(current, previous):
    """Detect changes between snapshots"""
    changes = {}
    
    # Check all June 8-24 dates
    for day in range(8, 25):
        date_key = f"June {day}"
        current_val = current.get(date_key, "")
        previous_val = previous.get(date_key, "")
        
        # Compare
        if current_val != previous_val:
            changes[date_key] = {
                "day": f"Jun {day}",
                "before": format_event(previous_val) if previous_val else "(New event)",
                "after": format_event(current_val) if current_val else "(Event info not found)",
            }
    
    return changes

def send_email(current_events, changes):
    """Send email with lineup + changes"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build CURRENT LINEUP (with website link)
    current_html = f"""
<p style="margin: 0 0 20px 0; text-align: center;">
    <a href="{PIKES_URL}" style="color: #ff6b9d; text-decoration: none; font-weight: bold;">
        🔗 View full program on Pikes website
    </a>
</p>
"""
    
    for day in range(8, 25):
        date = f"June {day}"
        if date in current_events:
            event = current_events[date]
            event_lines = event.split(" | ")
            
            current_html += f"""
<div style="margin: 12px 0; padding: 10px; background: #f9f9f9; border-left: 3px solid #ff6b9d; border-radius: 4px;">
    <p style="margin: 0; font-weight: bold; color: #333; font-size: 13px;">• {date}</p>"""
            
            for line in event_lines[:3]:
                current_html += f'<p style="margin: 3px 0 0 0; font-size: 12px; color: #666;">• {line}</p>'
            
            current_html += "</div>"
    
    # Build WHAT CHANGED
    changes_html = ""
    if changes:
        for day in range(8, 25):
            date = f"June {day}"
            if date in changes:
                change = changes[date]
                before_lines = change['before'].split(" | ")
                after_lines = change['after'].split(" | ")
                
                before_html = "<br>".join(before_lines[:3])
                after_html = "<br>".join(after_lines[:3])
                
                changes_html += f"""
<div style="margin: 15px 0; padding: 12px; background: #fef3c7; border-left: 3px solid #fbbf24; border-radius: 4px;">
    <p style="margin: 0; font-weight: bold; color: #d97706; font-size: 13px;">{change['day']} - Changed</p>
    
    <div style="margin: 10px 0 0 0;">
        <p style="margin: 0; font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold;">📍 Was:</p>
        <p style="margin: 5px 0; font-size: 12px; color: #555; padding: 8px; background: #fff5e6; border-radius: 3px; border-left: 2px solid #d97706;">
            {before_html}
        </p>
    </div>
    
    <div style="margin: 10px 0 0 0;">
        <p style="margin: 0; font-size: 10px; color: #059669; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold;">✓ Now:</p>
        <p style="margin: 5px 0; font-size: 12px; color: #065f46; padding: 8px; background: #ecfdf5; border-radius: 3px; border-left: 2px solid #059669;">
            {after_html}
        </p>
    </div>
</div>"""
    else:
        changes_html = '<p style="color: #666; text-align: center; padding: 20px; font-size: 13px;">✅ No changes detected</p>'
    
    html = f"""<html><body style="font-family: Arial; color: #333; background: #f5f5f5; padding: 20px;">
<div style="max-width: 900px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">

<h1 style="color: #ff6b9d; text-align: center; margin: 0 0 5px 0;">🎵 Pikes Ibiza</h1>
<h2 style="text-align: center; color: #666; font-size: 13px; margin: 0 0 30px 0;">June 8-24 Lineup Monitor</h2>

<h3 style="color: #333; border-bottom: 2px solid #ff6b9d; padding-bottom: 10px; margin: 0 0 15px 0; font-size: 14px;">📅 CURRENT LINEUP</h3>
{current_html}

<h3 style="color: #333; border-bottom: 2px solid #fbbf24; padding-bottom: 10px; margin: 30px 0 15px 0; font-size: 14px;">🔄 WHAT CHANGED</h3>
{changes_html}

<div style="text-align: center; padding-top: 20px; border-top: 1px solid #eee; margin-top: 30px; font-size: 11px; color: #999;">
    <p>Email sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>Monitor checks every 48 hours</p>
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

def main():
    """Main monitoring function"""
    print("=" * 70)
    print("🎵 PIKES IBIZA MONITOR")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    # Fetch current program
    current_program = fetch_pikes_program()
    print(f"   📊 Extracted: {len(current_program)} days")
    
    # Load previous snapshot
    previous_program = load_snapshot()
    print(f"   💾 Previous: {len(previous_program)} days")
    
    # Detect changes
    changes = detect_changes(current_program, previous_program)
    
    print(f"\n{'='*70}")
    if changes:
        print(f"🔄 CHANGES DETECTED ({len(changes)} dates)")
        for day in range(8, 25):
            date = f"June {day}"
            if date in changes:
                print(f"  ✓ Jun {day}")
    else:
        print("✅ No changes detected")
    print(f"{'='*70}\n")
    
    # Save snapshot
    save_snapshot(current_program)
    
    # Send email if first run or changes detected
    if not previous_program or changes:
        send_email(current_program, changes)
    else:
        print("✅ Silent check - no email (no changes)")

if __name__ == "__main__":
    main()
