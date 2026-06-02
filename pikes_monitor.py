#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Dynamic Web Scraping (What's-On Listing)
Scrapes the Pikes what's-on listing page for all Jun 8-24 events
"""

import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

PIKES_URL = "https://www.pikesibiza.com/whats-on/"

def scrape_pikes_events():
    """Dynamically scrape Pikes what's-on listing page for all June 8-24 events"""
    try:
        response = requests.get(PIKES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = {}
        
        # Find all event containers - looking for the event list items
        # The what's-on page uses various class structures, so we look for date + event info
        event_sections = soup.find_all(['article', 'div'], class_=lambda x: x and 'event' in x.lower() if x else False)
        
        if not event_sections:
            # Alternative: find by heading + content patterns
            event_sections = soup.find_all('div', class_='tribe-events-list-event-title')
        
        # More robust: find all links that point to /event/ URLs
        event_links = soup.find_all('a', href=re.compile(r'/event/[^/]+/'))
        
        for link in event_links:
            try:
                # Get the event URL and extract slug
                event_url = link.get('href')
                if not event_url:
                    continue
                
                slug_match = re.search(r'/event/([^/]+)/', event_url)
                if not slug_match:
                    continue
                
                slug = slug_match.group(1)
                event_name = link.get_text(strip=True)
                
                # Find the nearest date info (look in parent elements)
                parent = link.find_parent()
                date_text = None
                time_text = None
                artists_text = None
                
                # Traverse up to find date and artist info
                for ancestor in link.parents:
                    # Look for date patterns like "Wednesday, June 10"
                    text_content = ancestor.get_text(strip=True)
                    date_match = re.search(r'(\w+day),\s+(\w+)\s+(\d+)', text_content)
                    if date_match:
                        month, day = date_match.group(2), date_match.group(3)
                        # Only process Jun 8-24
                        day_int = int(day)
                        if day_int >= 8 and day_int <= 24 and month.lower() == 'june':
                            date_text = f"{month} {day}"
                        break
                
                if not date_text:
                    continue
                
                # Extract time (look for time pattern like "21:00" or "18:30")
                time_match = re.search(r'(\d{1,2}:\d{2})', event_name)
                if time_match:
                    time_text = time_match.group(1)
                    event_name = event_name.replace(time_text, '').strip()
                
                # Find artists/lineup in the article/container
                article = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'event' in x.lower() if x else False)
                if article:
                    # Get all text after event name that looks like artists
                    all_text = article.get_text('|', strip=True)
                    parts = [p.strip() for p in all_text.split('|')]
                    
                    # Find the part that contains artist names (usually after title)
                    for i, part in enumerate(parts):
                        if event_name in part and i + 1 < len(parts):
                            artists_text = parts[i + 1]
                            break
                
                if not artists_text:
                    artists_text = "Coming Soon…"
                
                if not time_text:
                    time_text = "TBD"
                
                # Store the event
                if date_text not in events:
                    events[date_text] = {
                        "time": time_text,
                        "name": event_name,
                        "artists": artists_text,
                        "slug": slug,
                        "url": event_url
                    }
            
            except Exception as e:
                continue
        
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
    print("🎵 PIKES IBIZA MONITOR (What's-On Listing Scraper)")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    # Scrape website
    print("🌐 Scraping Pikes what's-on listing...")
    current_program = scrape_pikes_events()
    
    if not current_program:
        print("❌ Failed to scrape website, using fallback...")
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
