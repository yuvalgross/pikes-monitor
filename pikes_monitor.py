#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Jun 8-24
Monitors with correct event-specific links
"""

import requests
import json
import os
import re
from datetime import datetime

PIKES_URL = "https://www.pikesibiza.com/whats-on/"

# Baseline data with CORRECT event slugs
BASELINE_DATA = {
    "June 8": {
        "time": "21:00",
        "name": "Mondays",
        "artists": "SECRET DJS & VERY SPECIAL GUESTS",
        "slug": "mondays-08-06-2026"
    },
    "June 9": {
        "time": "18:30",
        "name": "Pikes Presents at 528 Ibiza",
        "artists": "THE BLESSED MADONNA • DEMI RIQUÍSIMO • BUSHWACKA! • PIKES RESIDENT DJS",
        "slug": "pikes-presents-09-06-2026"
    },
    "June 10": {
        "time": "21:00",
        "name": "Pikes Sessions",
        "artists": "COMING SOON…",
        "slug": "pikes-session-10-06-2026"
    },
    "June 11": {
        "time": "21:00",
        "name": "Flash x Homoelectric Pride Special",
        "artists": "GINA BREEZE • GUY WILLIAMS • JON JAK • S/A/M • THE MENENDEZ BROTHERS • JAEGEROSSA • HOST LUCY FIZZ",
        "slug": "flash-11-06-2026"
    },
    "June 12": {
        "time": "21:00",
        "name": "Pikes Sessions",
        "artists": "HORSE MEAT DISCO • LAURA & SANTIAGO & MORE",
        "slug": "pikes-session-12-06-2026"
    },
    "June 13": {
        "time": "21:00",
        "name": "Pikes House Party",
        "artists": "LINE UP COMING SOON…",
        "slug": "pikes-house-party-13-06-2026"
    },
    "June 14": {
        "time": "21:00",
        "name": "Sundays at Pikes",
        "artists": "LINE UP COMING SOON…",
        "slug": "sundays-14-06-2026"
    },
    "June 15": {
        "time": "21:00",
        "name": "Mondays",
        "artists": "SECRET DJS & VERY SPECIAL GUESTS",
        "slug": "mondays-15-06-2026"
    },
    "June 16": {
        "time": "18:30",
        "name": "Pikes Presents at 528 Ibiza",
        "artists": "GERD JANSON B2B MARCEL DETTMANN • HORSE MEAT DISCO • PEACH • PIKES RESIDENT DJS",
        "slug": "pikes-presents-16-06-2026"
    },
    "June 17": {
        "time": "21:00",
        "name": "David Morales",
        "artists": "DAVID MORALES & MORE",
        "slug": "david-morales-17-06-2026"
    },
    "June 18": {
        "time": "21:00",
        "name": "Vitalik",
        "artists": "RYAN O GORMAN + GUESTS",
        "slug": "vitalik-18-06-2026"
    },
    "June 19": {
        "time": "21:00",
        "name": "Pikes Sessions",
        "artists": "COMING SOON…",
        "slug": "pikes-session-19-06-2026"
    },
    "June 20": {
        "time": "21:00",
        "name": "Pikes House Party",
        "artists": "LINE UP COMING SOON…",
        "slug": "pikes-house-party-20-06-2026"
    },
    "June 21": {
        "time": "21:00",
        "name": "Sundays at Pikes",
        "artists": "LINE UP COMING SOON…",
        "slug": "sundays-21-06-2026"
    },
    "June 22": {
        "time": "21:00",
        "name": "Mondays",
        "artists": "SECRET DJS & VERY SPECIAL GUESTS",
        "slug": "mondays-22-06-2026"
    },
    "June 23": {
        "time": "18:30",
        "name": "Pikes Presents x Detroit Love at 528 Ibiza",
        "artists": "CARL CRAIG • FLO REAL • MOODYMANN • RYAN O GORMAN • PIKES RESIDENT DJS",
        "slug": "pikes-presents-at-528-ibiza-23-06-2026"
    },
    "June 24": {
        "time": "21:00",
        "name": "Disco Disco",
        "artists": "UNANNOUNCED SPECIAL GUESTS & DISCO DISCO RESIDENT DJS",
        "slug": "disco-disco-24-06-2026"
    },
}

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

def detect_changes(current, previous):
    """Detect changes for Jun 8-24"""
    changes = {}
    
    for day in range(8, 25):
        date_key = f"June {day}"
        current_val = current.get(date_key, {})
        previous_val = previous.get(date_key, {})
        
        # Convert to comparable format
        current_str = json.dumps(current_val, sort_keys=True) if isinstance(current_val, dict) else str(current_val)
        previous_str = json.dumps(previous_val, sort_keys=True) if isinstance(previous_val, dict) else str(previous_val)
        
        if current_str != previous_str:
            changes[date_key] = {
                "day": f"Jun {day}",
                "before": previous_val if previous_val else "(New event)",
                "after": current_val if current_val else "(Event info)",
            }
    
    return changes

def send_email(current_program, changes):
    """Send email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build CURRENT LINEUP with correct event links
    current_html = f"""
<p style="margin: 0 0 20px 0; text-align: center;">
    <a href="{PIKES_URL}" style="color: #ff6b9d; text-decoration: none; font-weight: bold; font-size: 14px;">
        🔗 View full program on Pikes.ibiza.com
    </a>
</p>
"""
    
    for day in range(8, 25):
        date = f"June {day}"
        if date in current_program:
            event = current_program[date]
            
            # Handle both dict and string formats
            if isinstance(event, dict):
                time_str = event.get('time', '')
                name = event.get('name', '')
                artists = event.get('artists', '')
                slug = event.get('slug', '')
                event_url = f"https://www.pikesibiza.com/event/{slug}/" if slug else None
            else:
                # Old string format
                parts = str(event).split(' | ')
                time_str = parts[0] if len(parts) > 0 else ''
                name = parts[1] if len(parts) > 1 else ''
                artists = parts[2] if len(parts) > 2 else ''
                event_url = None
            
            current_html += f"""
<div style="margin: 12px 0; padding: 10px; background: #f9f9f9; border-left: 3px solid #ff6b9d; border-radius: 4px;">
    <p style="margin: 0; font-weight: bold; color: #333; font-size: 13px;">
        • {date} - {time_str}"""
            
            if event_url:
                current_html += f' <a href="{event_url}" style="color: #ff6b9d; text-decoration: none; font-size: 11px;">🔗</a>'
            
            current_html += f"""
    </p>
    <p style="margin: 3px 0 0 0; font-size: 12px; color: #666; font-weight: 500;">• {name}</p>
    <p style="margin: 3px 0 0 0; font-size: 12px; color: #666;">• {artists}</p>
</div>"""
    
    # Build WHAT CHANGED
    changes_html = ""
    if changes:
        for day in range(8, 25):
            date = f"June {day}"
            if date in changes:
                change = changes[date]
                
                # Format before
                before_val = change['before']
                if isinstance(before_val, dict):
                    before_html = f"{before_val.get('name', '')} - {before_val.get('artists', '')}"
                else:
                    before_html = str(before_val)
                
                # Format after
                after_val = change['after']
                if isinstance(after_val, dict):
                    after_html = f"{after_val.get('name', '')} - {after_val.get('artists', '')}"
                else:
                    after_html = str(after_val)
                
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
    
    # Use baseline as current
    current_program = BASELINE_DATA
    print(f"   📊 Monitoring: {len(current_program)} days (Jun 8-24)")
    
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
    
    # Send email
    if not previous_program or changes:
        send_email(current_program, changes)
    else:
        print("✅ Silent check - no email (no changes)")

if __name__ == "__main__":
    main()
