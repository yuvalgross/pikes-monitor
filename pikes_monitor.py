#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Enhanced
Tracks DJ lineups and sends email alerts with detailed change information
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

def fetch_pikes_program():
    """Fetch Pikes Ibiza program"""
    print("🌐 Fetching Pikes program...")
    
    url = "https://www.pikesibiza.com/en/program/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Fetched {len(response.text):,} characters")
            return extract_events(response.text)
        else:
            print(f"   ❌ Status {response.status_code}")
            return {}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {}

def extract_events(html_content):
    """Extract events from HTML with more granularity"""
    events = {}
    
    # Look for June dates
    for day in range(1, 32):
        patterns = [
            f"June {day}",
            f"Jun {day}",
            f"{day:02d}",
        ]
        
        for pattern in patterns:
            if pattern in html_content:
                # Find the event block for this date
                idx = html_content.find(pattern)
                if idx > 0:
                    # Extract surrounding context (next 500 chars)
                    snippet = html_content[idx:idx+800]
                    
                    # Clean up
                    snippet = snippet.replace('<', '\n<').replace('>', '>\n')
                    lines = [l.strip() for l in snippet.split('\n') if l.strip() and '<' not in l]
                    
                    # Get relevant lines
                    event_info = []
                    for line in lines[:15]:
                        if line and len(line) > 3 and not line.startswith(('http', 'www', 'href')):
                            event_info.append(line)
                    
                    if event_info:
                        date_key = f"June {day}"
                        events[date_key] = " | ".join(event_info[:3])
                        break
    
    return events

def load_snapshot(filename="pikes_snapshot.json"):
    """Load previous snapshot"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_snapshot(data, filename="pikes_snapshot.json"):
    """Save current snapshot"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def detect_detailed_changes(current, previous):
    """Detect detailed changes for each date"""
    changes = {}
    
    all_dates = set(list(current.keys()) + list(previous.keys()))
    
    for date in sorted(all_dates):
        current_val = current.get(date, "")
        previous_val = previous.get(date, "")
        
        if current_val != previous_val:
            # Extract date number
            match = re.search(r"(\d+)", date)
            day = match.group(1) if match else "?"
            
            changes[date] = {
                "day": f"Jun {day}",
                "old": previous_val,
                "new": current_val,
                "status": "Updated" if previous_val else "Added"
            }
    
    return changes

def send_email(current_events, changes):
    """Send email with detailed changes"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build current lineup HTML
    current_html = ""
    for date in sorted(current_events.keys()):
        current_html += f"""
<div style="margin: 15px 0; padding: 12px; background: #f9f9f9; border-left: 3px solid #ff6b9d; border-radius: 4px;">
    <p style="margin: 0; font-weight: bold; color: #333;">{date}</p>
    <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">{current_events[date][:150]}</p>
</div>"""
    
    # Build changes HTML with inline details
    changes_html = ""
    if changes:
        for date in sorted(changes.keys()):
            change = changes[date]
            changes_html += f"""
<div style="margin: 15px 0; padding: 12px; background: #fef3c7; border-left: 3px solid #fbbf24; border-radius: 4px;">
    <p style="margin: 0; font-weight: bold; color: #333;">{change['day']}</p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
        <span style="background: #fff3cd; padding: 2px 6px; border-radius: 3px;">✓ {change['status']}</span>
    </p>
    <p style="margin: 8px 0 0 0; font-size: 12px; color: #555; padding: 8px; background: white; border-radius: 3px;">
        {change['new'][:200]}
    </p>
</div>"""
    else:
        changes_html = '<p style="color: #666;">No changes detected</p>'
    
    html = f"""<html><body style="font-family: Arial; color: #333; background: #f5f5f5; padding: 20px;">
<div style="max-width: 900px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">

<h1 style="color: #ff6b9d; text-align: center; margin: 0 0 10px 0;">🎵 Pikes Ibiza</h1>
<h2 style="text-align: center; color: #666; font-size: 14px; margin: 0 0 30px 0;">June 8-24 Lineup Monitor</h2>

<h3 style="color: #333; border-bottom: 2px solid #ff6b9d; padding-bottom: 10px;">📅 CURRENT LINEUP</h3>
{current_html}

<h3 style="color: #333; border-bottom: 2px solid #fbbf24; padding-bottom: 10px; margin-top: 30px;">🔄 WHAT CHANGED</h3>
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
    
    # Load previous snapshot
    previous_program = load_snapshot()
    
    # Detect detailed changes
    changes = detect_detailed_changes(current_program, previous_program)
    
    print(f"\n{'='*70}")
    if changes:
        print(f"🔄 CHANGES DETECTED ({len(changes)} dates updated)")
        for date in list(changes.keys())[:5]:
            print(f"  ✓ {date}")
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
