#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor
Clean event extraction with readable before/after tracking (Jun 8-24)
"""

import requests
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
    """Extract clean event data for Jun 8-24 only"""
    events = {}
    
    # Only June 8-24
    for day in range(8, 25):
        date_str = f"June {day}"
        
        if date_str in html_content:
            idx = html_content.find(date_str)
            if idx >= 0:
                # Get context around date
                start = max(0, idx - 100)
                end = min(len(html_content), idx + 1200)
                snippet = html_content[start:end]
                
                # Extract readable text (not HTML)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(snippet, 'html.parser')
                text = soup.get_text(separator=" | ", strip=True)
                
                # Clean up
                lines = [l.strip() for l in text.split('|') if l.strip() and len(l.strip()) > 3]
                
                # Get key lines (time, event name, artists)
                event_text = " | ".join(lines[:4])
                
                if event_text and len(event_text) > 10:
                    events[date_str] = event_text
    
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

def format_event(text):
    """Format event text nicely"""
    if not text:
        return "(No event listed)"
    
    # Clean up formatting
    text = text.replace(" | ", "\n")
    return text

def detect_changes(current, previous):
    """Detect changes (Jun 8-24 only)"""
    changes = {}
    
    # Get all June 8-24 dates in order
    dates_to_check = [f"June {day}" for day in range(8, 25)]
    
    for date in dates_to_check:
        current_val = current.get(date, "")
        previous_val = previous.get(date, "")
        
        if current_val != previous_val:
            match = re.search(r"(\d+)", date)
            day = match.group(1) if match else "?"
            
            changes[date] = {
                "day": f"Jun {day}",
                "before": format_event(previous_val) if previous_val else "(New event)",
                "after": format_event(current_val) if current_val else "(Event removed)",
            }
    
    return changes

def send_email(current_events, changes):
    """Send email with current lineup + before/after changes"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build CURRENT LINEUP (Jun 8-24 only, in order)
    current_html = ""
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
    
    # Build WHAT CHANGED (only Jun 8-24)
    changes_html = ""
    if changes:
        for day in range(8, 25):
            date = f"June {day}"
            if date in changes:
                change = changes[date]
                before_lines = change['before'].split("\n")
                after_lines = change['after'].split("\n")
                
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
    
    # Detect changes
    changes = detect_changes(current_program, previous_program)
    
    print(f"\n{'='*70}")
    if changes:
        print(f"🔄 CHANGES DETECTED ({len(changes)} dates)")
        for date in sorted(changes.keys()):
            match = re.search(r"(\d+)", date)
            day = match.group(1) if match else "?"
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
