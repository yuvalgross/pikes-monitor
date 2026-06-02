#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Dynamic Web Scraping
Scrapes the Pikes website in real-time for all Jun 8-24 events
"""

import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

PIKES_URL = "https://www.pikesibiza.com/whats-on/"

def scrape_pikes_events():
    """Dynamically scrape Pikes website for all June 8-24 events"""
    try:
        response = requests.get(PIKES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = {}
        
        # Find all event cards
        event_cards = soup.find_all('div', class_='tribe-events-calendar-list__event')
        
        for card in event_cards:
            # Extract date
            date_elem = card.find('span', class_='tribe-event-date-start')
            if not date_elem:
                continue
            
            date_text = date_elem.get_text(strip=True)
            # Parse "June 8" from date text
            match = re.search(r'(\w+)\s+(\d+)', date_text)
            if not match:
                continue
            
            month, day = match.groups()
            date_key = f"{month} {day}"
            
            # Only process Jun 8-24
            day_int = int(day)
            if day_int < 8 or day_int > 24:
                continue
            
            # Extract event name
            name_elem = card.find('h3', class_='tribe-events-list-event-title')
            event_name = name_elem.get_text(strip=True) if name_elem else "Unknown"
            
            # Extract time
            time_elem = card.find('span', class_='tribe-event-time')
            event_time = time_elem.get_text(strip=True) if time_elem else "TBD"
            
            # Extract artists/lineup
            desc_elem = card.find('div', class_='tribe-events-list-event-description')
            artists = desc_elem.get_text(strip=True) if desc_elem else "COMING SOON…"
            
            # Extract event URL/slug
            link_elem = card.find('a', class_='tribe-events-list-event-title-link')
            event_url = link_elem.get('href') if link_elem else None
            
            # Extract slug from URL
            slug = None
            if event_url:
                # URL format: https://www.pikesibiza.com/event/{slug}/
                slug_match = re.search(r'/event/([^/]+)/', event_url)
                slug = slug_match.group(1) if slug_match else None
            
            if date_key not in events:
                events[date_key] = {
                    "time": event_time,
                    "name": event_name,
                    "artists": artists,
                    "slug": slug,
                    "url": event_url
                }
        
        return events if events else None
    
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return None

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
    """Compare current and previous snapshots"""
    changes = {}
    for day in range(8, 25):
        date_key = f"June {day}"
        if date_key not in current:
            continue
        
        current_val = current[date_key]
        previous_val = previous.get(date_key, {})
        
        # Compare as JSON strings
        current_str = json.dumps(current_val, sort_keys=True)
        previous_str = json.dumps(previous_val, sort_keys=True)
        
        if current_str != previous_str:
            changes[date_key] = {
                "day": f"Jun {day}",
                "before": previous_val if previous_val else "(New event)",
                "after": current_val
            }
    
    return changes

def send_email(current_program, changes):
    """Send notification email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    EMAIL = os.getenv("GMAIL_ADDRESS")
    PASSWORD = os.getenv("GMAIL_PASSWORD")
    RECIPIENT = os.getenv("NOTIFY_EMAIL")
    
    if not all([EMAIL, PASSWORD, RECIPIENT]):
        print("⚠️  Missing email credentials")
        return
    
    # Build changelog
    changelog = ""
    if changes:
        changelog = '<div style="background: #fef3c7; border: 1px solid #fcd34d; padding: 16px; border-radius: 8px; margin-bottom: 24px;">'
        changelog += '<p style="margin: 0 0 10px 0; font-weight: 600; color: #b45309; font-size: 13px;">🔄 ' + str(len(changes)) + ' CHANGES DETECTED</p>'
        changelog += '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
        for date in sorted(changes.keys()):
            day = changes[date].get("day", date)
            changelog += f'<div style="background: white; border: 0.5px solid #fcd34d; border-radius: 4px; padding: 6px 12px; font-size: 12px; color: #78350f; font-weight: 500;">{day}</div>'
        changelog += '</div></div>'
    
    current_html = '<div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto; max-width: 600px; margin: 0 auto;">'
    
    # Header
    current_html += '<div style="background: linear-gradient(135deg, #d946a6 0%, #ec4899 100%); color: white; padding: 40px 24px; text-align: center; border-radius: 12px 12px 0 0;">'
    current_html += '<h1 style="margin: 0; font-size: 28px; font-weight: 600;">🎵 Pikes Ibiza</h1>'
    current_html += '<p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.9;">Lineup Updates • June 2026</p>'
    current_html += '</div>'
    
    current_html += '<div style="padding: 24px;">'
    current_html += changelog
    
    # Events
    for day in range(8, 25):
        date = f"June {day}"
        if date not in current_program:
            continue
        
        event = current_program[date]
        
        time_str = event.get('time', '')
        name = event.get('name', '')
        artists = event.get('artists', '')
        slug = event.get('slug', '')
        event_url = f"https://www.pikesibiza.com/event/{slug}/" if slug else None
        
        has_change = date in changes
        bg_color = "#fff5f9" if has_change else "var(--color-background-primary)"
        border_color = "#ec4899" if has_change else "var(--color-border-tertiary)"
        
        event_link = f' <a href="{event_url}" style="color: #ec4899; text-decoration: none; font-size: 12px; font-weight: 500;">🔗 Open event</a>' if event_url else ''
        
        current_html += f'<div style="border: 0.5px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: {bg_color};">'
        current_html += f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">'
        current_html += f'<div><div style="font-weight: 600; font-size: 14px; color: #333;">{date} @ {time_str}</div>{event_link}</div></div>'
        current_html += f'<div style="font-weight: 600; font-size: 15px; color: #333; margin-bottom: 8px;">{name}</div>'
        current_html += f'<div style="font-size: 13px; color: #666;">{artists}</div>'
        
        if has_change:
            change = changes[date]
            before_val = change.get('before', {})
            after_val = change.get('after', {})
            
            if isinstance(before_val, dict) and isinstance(after_val, dict):
                before_artists = before_val.get('artists', '')
                after_artists = after_val.get('artists', '')
                
                if before_artists and after_artists and before_artists != after_artists:
                    current_html += '<div style="background: white; border: 0.5px solid #fecdd3; border-radius: 4px; padding: 10px; margin-top: 12px; font-size: 12px;">'
                    current_html += '<div style="color: #831843; font-weight: 600; margin-bottom: 4px;">🔄 LINEUP UPDATED</div>'
                    current_html += f'<div style="color: #999; margin-bottom: 4px; text-decoration: line-through;">Before: {before_artists}</div>'
                    current_html += f'<div style="color: #ec4899; font-weight: 500;">After: {after_artists}</div>'
                    current_html += '</div>'
        
        current_html += '</div>'
    
    current_html += '</div>'
    
    # Footer
    current_html += '<div style="border-top: 0.5px solid #e0e0e0; padding: 16px 24px; text-align: center; font-size: 12px; color: #999;">'
    current_html += '<p style="margin: 0;">Monitor running every 48 hours through June 25</p>'
    current_html += '<a href="https://www.pikesibiza.com/whats-on/" style="color: #ec4899; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 12px;">View all events →</a>'
    current_html += '</div>'
    current_html += '</div>'
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎵 Pikes Ibiza Lineup Updates"
    msg["From"] = EMAIL
    msg["To"] = RECIPIENT
    
    html_part = MIMEText(current_html, "html")
    msg.attach(html_part)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, RECIPIENT, msg.as_string())
        print("✅ Email sent successfully")
    except Exception as e:
        print(f"❌ Email error: {e}")

def main():
    print("=" * 70)
    print("🎵 PIKES IBIZA MONITOR (Web Scraping)")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    # Scrape website
    print("🌐 Scraping Pikes website...")
    current_program = scrape_pikes_events()
    
    if not current_program:
        print("❌ Failed to scrape website, using fallback...")
        # Fallback to hardcoded baseline if scraping fails
        current_program = load_snapshot()
    else:
        print(f"✅ Found {len(current_program)} events")
    
    # Load previous snapshot
    previous_program = load_snapshot()
    print(f"💾 Previous snapshot: {len(previous_program)} events")
    
    # Detect changes
    changes = detect_changes(current_program, previous_program)
    
    print(f"\n{'='*70}")
    if changes:
        print(f"🔄 CHANGES DETECTED ({len(changes)} dates)")
        for day in sorted(changes.keys()):
            print(f"  ✓ {day}")
    else:
        print("✅ No changes detected")
    print(f"{'='*70}\n")
    
    # Save snapshot
    save_snapshot(current_program)
    
    # Send email if there are changes or if this is the first run
    if not previous_program or changes:
        send_email(current_program, changes)
    else:
        print("✅ Silent check - no email (no changes)")

if __name__ == "__main__":
    main()
