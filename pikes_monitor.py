#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Jun 8-24
Enhanced graphic design with monitoring end date
"""

import requests
import json
import os
import re
from datetime import datetime

PIKES_URL = "https://www.pikesibiza.com/whats-on/"

# Baseline data with correct event slugs
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
        "slug": "sundays-at-pikes-14-06-2026"
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
        "slug": "sundays-at-pikes-21-06-2026"
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
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_snapshot(data, filename="pikes_snapshot.json"):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def detect_changes(current, previous):
    changes = {}
    for day in range(8, 25):
        date_key = f"June {day}"
        current_val = current.get(date_key, {})
        previous_val = previous.get(date_key, {})
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
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    current_html = f"""
<p style="margin: 0 0 20px 0; text-align: center;">
    <a href="{PIKES_URL}" style="color: white; text-decoration: none; font-weight: bold; font-size: 16px; background: #ff6b9d; padding: 12px 24px; border-radius: 6px; display: inline-block;">
        🔗 View Full Program
    </a>
</p>
"""
    
    for day in range(8, 25):
        date = f"June {day}"
        if date in current_program:
            event = current_program[date]
            
            if isinstance(event, dict):
                time_str = event.get('time', '')
                name = event.get('name', '')
                artists = event.get('artists', '')
                slug = event.get('slug', '')
                event_url = f"https://www.pikesibiza.com/event/{slug}/" if slug else None
            else:
                parts = str(event).split(' | ')
                time_str = parts[0] if len(parts) > 0 else ''
                name = parts[1] if len(parts) > 1 else ''
                artists = parts[2] if len(parts) > 2 else ''
                event_url = None
            
            has_change = date in changes
            bg_color = "#fff5f7" if has_change else "#f9f9f9"
            border_color = "#ff6b9d" if has_change else "#e0e0e0"
            
            current_html += f"""
<div style="margin: 14px 0; padding: 16px; background: {bg_color}; border-left: 4px solid {border_color}; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <p style="margin: 0; font-weight: bold; color: #222; font-size: 15px;">
        📍 {date} @ {time_str}"""
            
            if event_url:
                current_html += f' <a href="{event_url}" style="color: #ff6b9d; text-decoration: none; font-size: 11px; font-weight: bold;">🔗</a>'
            
            current_html += f"""
    </p>
    <p style="margin: 8px 0 0 0; font-size: 14px; color: #333; font-weight: 600;">🎤 {name}</p>
    <p style="margin: 6px 0 0 0; font-size: 13px; color: #666; line-height: 1.4;">👥 {artists}</p>"""
            
            if has_change:
                change = changes[date]
                before_val = change['before']
                after_val = change['after']
                
                if isinstance(before_val, dict):
                    before_text = f"{before_val.get('name', '')} - {before_val.get('artists', '')}"
                else:
                    before_text = str(before_val)
                
                if isinstance(after_val, dict):
                    after_text = f"{after_val.get('name', '')} - {after_val.get('artists', '')}"
                else:
                    after_text = str(after_val)
                
                current_html += f"""
    <div style="margin: 12px 0 0 0; padding: 10px; background: linear-gradient(135deg, #fff9e6 0%, #fffbf0 100%); border-radius: 4px; border-left: 3px solid #fbbf24;">
        <p style="margin: 0; font-size: 11px; color: #d97706; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">🔄 LINEUP UPDATED</p>
        <p style="margin: 6px 0 0 0; font-size: 12px; color: #555;"><strong>Before:</strong> {before_text[:70]}</p>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #059669;"><strong>After:</strong> {after_text[:70]}</p>
    </div>"""
            else:
                current_html += f"""
    <p style="margin: 8px 0 0 0; font-size: 12px; color: #059669; font-weight: 500;">✅ No changes</p>"""
            
            current_html += """
</div>"""
    
    # End of monitoring message
    end_message = """
<div style="margin: 30px 0 0 0; padding: 20px; background: linear-gradient(135deg, #ff6b9d 0%, #ff8ab8 100%); border-radius: 8px; text-align: center; color: white;">
    <p style="margin: 0; font-size: 18px; font-weight: bold;">🎉 Trip Ends June 25</p>
    <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.95;">Monitoring ends June 25 • Enjoy your Ibiza adventure! 🌴</p>
</div>
"""
    
    html = f"""<html><body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%); padding: 20px; margin: 0;">
<div style="max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);">

<div style="background: linear-gradient(135deg, #ff6b9d 0%, #ff8ab8 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
    <p style="margin: 0; font-size: 42px; font-weight: bold;">🎵</p>
    <h1 style="color: white; text-align: center; margin: 10px 0 0 0; font-size: 32px;">Pikes Ibiza</h1>
    <h2 style="text-align: center; color: rgba(255,255,255,0.9); font-size: 16px; margin: 8px 0 0 0; font-weight: 400;">📅 June 8-24 Lineup Monitor</h2>
</div>

<h3 style="color: #333; border-bottom: 3px solid #ff6b9d; padding-bottom: 12px; margin: 0 0 20px 0; font-size: 18px;">📅 CURRENT LINEUP</h3>
{current_html}

{end_message}

<div style="text-align: center; padding-top: 25px; border-top: 1px solid #eee; margin-top: 30px; font-size: 12px; color: #999;">
    <p style="margin: 0;">Email sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p style="margin: 6px 0 0 0;">✨ Next check in 48 hours (until June 25)</p>
</div>

</div>
</body></html>"""
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎵 Pikes Ibiza - Lineup Update"
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
    print("=" * 70)
    print("🎵 PIKES IBIZA MONITOR")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    current_program = BASELINE_DATA
    print(f"   📊 Monitoring: {len(current_program)} days (Jun 8-24)")
    
    previous_program = load_snapshot()
    print(f"   💾 Previous: {len(previous_program)} days")
    
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
    
    save_snapshot(current_program)
    
    if not previous_program or changes:
        send_email(current_program, changes)
    else:
        print("✅ Silent check - no email (no changes)")

if __name__ == "__main__":
    main()
