#!/usr/bin/env python3
"""
🎵 Pikes Ibiza Monitor - Hybrid Scraping
Scrapes BOTH individual event pages + what's-on listing page
Gets data from whichever source has the most recent info
"""

import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

PIKES_URL = "https://www.pikesibiza.com/whats-on/"
PIKES_EVENT_BASE = "https://www.pikesibiza.com/event/"

def scrape_individual_event_pages():
    """Scrape individual event pages (Jun 8-24)"""
    events = {}
    
    # Known event slugs for Jun 8-24
    slugs = [
        "mondays-08-06-2026",
        "pikes-presents-at-528-ibiza-09-06-2026",
        "pikes-sessions-10-06-2026",
        "flash-11-06-2026",
        "pikes-sessions-12-06-2026",
        "pikes-house-party-13-06-2026",
        "sundays-at-pikes-14-06-2026",
        "mondays-15-06-2026",
        "pikes-presents-at-528-ibiza-16-06-2026",
        "david-morales-17-06-2026",
        "vitalik-18-06-2026",
        "pikes-session-19-06-2026",
        "pikes-house-party-20-06-2026",
        "sundays-at-pikes-21-06-2026",
        "mondays-22-06-2026",
        "pikes-presents-at-528-ibiza-23-06-2026",
        "disco-disco-24-06-2026",
    ]
    
    for slug in slugs:
        try:
            url = f"{PIKES_EVENT_BASE}{slug}/"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract date from page
            title = soup.find('h1')
            if not title:
                continue
            
            title_text = title.get_text(strip=True)
            
            # Extract date like "Wednesday 10 June 2026"
            date_match = re.search(r'(\w+day),?\s+(\w+)\s+(\d+)', title_text)
            if not date_match:
                continue
            
            month, day = date_match.group(2), date_match.group(3)
            day_int = int(day)
            if day_int < 8 or day_int > 24 or month.lower() != 'june':
                continue
            
            date_key = f"June {day}"
            
            # Extract event name and time from title
            event_name = title_text.split("|")[0].strip()
            
            # Look for time in the page
            time_text = "TBD"
            time_match = re.search(r'(\d{1,2}:\d{2})', response.text)
            if time_match:
                time_text = time_match.group(1)
            
            # Extract lineup from the page
            lineup_text = "Coming Soon…"
            
            # Look for "LINE UP" heading or similar
            lineup_sections = soup.find_all(['h2', 'h3'], string=lambda x: x and 'LINE UP' in x.upper())
            
            if lineup_sections:
                # Get text after the LINE UP heading
                for section in lineup_sections:
                    next_elem = section.find_next('p')
                    if next_elem:
                        potential_lineup = next_elem.get_text(strip=True)
                        if potential_lineup and potential_lineup.lower() != 'coming soon':
                            lineup_text = potential_lineup
                            break
            
            # Fallback: search for artist names pattern
            if lineup_text == "Coming Soon…":
                text_content = soup.get_text()
                # Look for patterns with • (bullet points indicating artists)
                lineup_match = re.search(r'([A-Z][A-Z\s•&]+?)(?:\n|\.|View|Book|Get|Call)', text_content)
                if lineup_match:
                    potential = lineup_match.group(1).strip()
                    if '•' in potential and len(potential) > 5:
                        lineup_text = potential
            
            events[date_key] = {
                "time": time_text,
                "name": event_name,
                "artists": lineup_text,
                "slug": slug,
                "source": "individual_page"
            }
        
        except Exception as e:
            continue
    
    return events

def scrape_listing_page():
    """Try to scrape what's-on listing page (may be incomplete due to JS)"""
    try:
        response = requests.get(PIKES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = {}
        event_links = soup.find_all('a', href=re.compile(r'/event/[^/]+/'))
        
        for link in event_links:
            try:
                event_url = link.get('href')
                slug_match = re.search(r'/event/([^/]+)/', event_url)
                if not slug_match:
                    continue
                
                slug = slug_match.group(1)
                
                # Find date info from parent
                parent = link.find_parent()
                date_text = None
                
                for ancestor in link.parents:
                    text = ancestor.get_text(strip=True)
                    date_match = re.search(r'(\w+day),\s+(\w+)\s+(\d+)', text)
                    if date_match:
                        month, day = date_match.group(2), date_match.group(3)
                        if 8 <= int(day) <= 24 and month.lower() == 'june':
                            date_text = f"June {day}"
                            break
                
                if not date_text:
                    continue
                
                event_name = link.get_text(strip=True)
                
                # Extract time
                time_match = re.search(r'(\d{1,2}:\d{2})', event_name)
                time_text = time_match.group(1) if time_match else "TBD"
                
                # Get artists from card
                card = link.find_parent('article') or link.find_parent('div')
                artists = "Coming Soon…"
                
                if card:
                    text_parts = card.get_text('|', strip=True).split('|')
                    for i, part in enumerate(text_parts):
                        if part.strip() and '•' in part:
                            artists = part.strip()
                            break
                
                events[date_text] = {
                    "time": time_text,
                    "name": event_name,
                    "artists": artists,
                    "slug": slug,
                    "source": "listing_page"
                }
            except:
                continue
        
        return events
    except:
        return {}

def merge_events(individual_events, listing_events):
    """Merge data from both sources (prefer listing if available and non-empty)"""
    merged = {}
    
    # Start with individual events (reliable)
    merged.update(individual_events)
    
    # Overlay with listing data (prefer if it has better info)
    for date, listing_data in listing_events.items():
        if date in merged:
            # Prefer listing data if it has more detailed artist info
            if listing_data.get('artists') != "Coming Soon…" and listing_data.get('artists') != "LINE UP COMING SOON…":
                merged[date]['artists'] = listing_data['artists']
                merged[date]['source'] = "listing_page (primary)"
        else:
            merged[date] = listing_data
    
    return merged

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
        if date_key not in current:
            continue
        
        current_val = current[date_key]
        previous_val = previous.get(date_key, {})
        
        current_str = json.dumps({k: v for k, v in current_val.items() if k != 'source'}, sort_keys=True)
        previous_str = json.dumps(previous_val, sort_keys=True)
        
        if current_str != previous_str:
            changes[date_key] = {
                "day": f"Jun {day}",
                "before": previous_val if previous_val else "(New event)",
                "after": current_val
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
        return
    
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
    current_html += '<div style="background: linear-gradient(135deg, #d946a6 0%, #ec4899 100%); color: white; padding: 40px 24px; text-align: center; border-radius: 12px 12px 0 0;">'
    current_html += '<h1 style="margin: 0; font-size: 28px; font-weight: 600;">🎵 Pikes Ibiza</h1>'
    current_html += '<p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.9;">Lineup Updates • June 2026</p>'
    current_html += '</div>'
    current_html += '<div style="padding: 24px;">'
    current_html += changelog
    
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
        
        event_link = f' <a href="{event_url}" style="color: #ec4899; text-decoration: none; font-size: 12px; font-weight: 500;">🔗</a>' if event_url else ''
        
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
                    current_html += f'<div style="color: #999; margin-bottom: 4px; text-decoration: line-through;">Before: {before_artists[:70]}</div>'
                    current_html += f'<div style="color: #ec4899; font-weight: 500;">After: {after_artists[:70]}</div>'
                    current_html += '</div>'
        
        current_html += '</div>'
    
    current_html += '</div><div style="border-top: 0.5px solid #e0e0e0; padding: 16px 24px; text-align: center; font-size: 12px; color: #999;">'
    current_html += '<p style="margin: 0;">Dual-source monitoring (pages + listing) every 48h</p>'
    current_html += '</div></div>'
    
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
    print("🎵 PIKES IBIZA MONITOR (Hybrid: Individual Pages + Listing)")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    print("🔗 Scraping individual event pages (Jun 8-24)...")
    individual_events = scrape_individual_event_pages()
    print(f"✅ Found {len(individual_events)} from individual pages")
    
    print("📄 Scraping what's-on listing page...")
    listing_events = scrape_listing_page()
    print(f"✅ Found {len(listing_events)} from listing page")
    
    # Merge both sources
    current_program = merge_events(individual_events, listing_events)
    print(f"✅ Merged: {len(current_program)} total events")
    
    # Load previous and detect changes
    previous_program = load_snapshot()
    print(f"💾 Previous: {len(previous_program)} events")
    
    changes = detect_changes(current_program, previous_program)
    
    print(f"\n{'='*70}")
    if changes:
        print(f"🔄 CHANGES DETECTED ({len(changes)} dates)")
        for day in sorted(changes.keys()):
            print(f"  ✓ {day}")
    else:
        print("✅ No changes detected")
    print(f"{'='*70}\n")
    
    # Clean data for snapshot (remove source field)
    clean_program = {}
    for date, data in current_program.items():
        clean_program[date] = {k: v for k, v in data.items() if k != 'source'}
    
    save_snapshot(clean_program)
    
    if not previous_program or changes:
        send_email(clean_program, changes)
    else:
        print("✅ Silent check - no email (no changes)")

if __name__ == "__main__":
    main()
