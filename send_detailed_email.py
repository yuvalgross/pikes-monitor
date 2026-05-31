#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from datetime import datetime

EMAIL = os.getenv("GMAIL_ADDRESS", "gross.yuval@gmail.com")
PASSWORD = os.getenv("GMAIL_PASSWORD")
RECIPIENT = os.getenv("NOTIFY_EMAIL", "gross.yuval@gmail.com")

# Current snapshot data
current_events = {"June 8": {"events": ["Monday, June 8 - 21:00", "Mondays", "SECRET DJS & VERY SPECIAL GUESTS"]}, "June 9": {"events": ["Tuesday, June 9 - 18:30", "Pikes Presents at 528 Ibiza", "THE BLESSED MADONNA \u2022 DEMI RIQU\u00cdSIMO \u2022 BUSHWACKA! \u2022 PIKES RESIDENT DJS", "Tuesday, June 9 - 21:00", "Bathtub Club", "PIKES RESIDENT DJS"]}, "June 10": {"events": ["Wednesday, June 10 - 21:00", "Pikes Sessions", "COMING SOON\u2026"]}, "June 11": {"events": ["Thursday, June 11 - 21:00", "Flash x Homoelectric Pride Special", "GINA BREEZE \u2022 GUY WILLIAMS \u2022 JON JAK \u2022 S/A/M \u2022 THE MENENDEZ BROTHERS \u2022 JAEGEROSSA \u2022 HOST LUCY FIZZ"]}, "June 12": {"events": ["Friday, June 12 - 21:00", "Pikes Sessions", "HORSE MEAT DISCO \u2022 LAURA & SANTIAGO & MORE"]}, "June 13": {"events": ["Saturday, June 13 - 21:00", "Pikes House Party", "LINE UP COMING SOON\u2026"]}, "June 14": {"events": ["Sunday, June 14 - 21:00", "Sundays at Pikes", "LINE UP COMING SOON\u2026"]}, "June 15": {"events": ["Monday, June 15 - 21:00", "Mondays", "SECRET DJS & VERY SPECIAL GUESTS"]}, "June 16": {"events": ["Tuesday, June 16 - 18:30", "Pikes Presents at 528 Ibiza", "GERD JANSON B2B MARCEL DETTMANN \u2022 HORSE MEAT DISCO \u2022 PEACH \u2022 PIKES RESIDENT DJS", "Tuesday, June 16 - 21:00", "Bathtub Club", "PIKES RESIDENT DJS"]}, "June 17": {"events": ["Wednesday, June 17 - 21:00", "David Morales", "DAVID MORALES & MORE"]}, "June 18": {"events": ["Thursday, June 18 - 21:00", "Vitalik", "RYAN O GORMAN + GUESTS"]}, "June 19": {"events": ["Friday, June 19 - 21:00", "Pikes Sessions", "COMING SOON\u2026"]}, "June 20": {"events": ["Saturday, June 20 - 21:00", "Pikes House Party", "LINE UP COMING SOON\u2026"]}, "June 21": {"events": ["Sunday, June 21 - 21:00", "Sundays at Pikes", "LINE UP COMING SOON\u2026"]}, "June 22": {"events": ["Monday, June 22 - 21:00", "Mondays", "SECRET DJS & VERY SPECIAL GUESTS"]}, "June 23": {"events": ["Tuesday, June 23 - 18:30", "Pikes Presents x Detroit Love at 528 Ibiza", "CARL CRAIG \u2022 FLO REAL \u2022 MOODYMANN \u2022 RYAN O GORMAN \u2022 PIKES RESIDENT DJS", "Tuesday, June 23 - 21:00", "Bathtub Club", "PIKES RESIDENT DJS"]}, "June 24": {"events": ["Wednesday, June 24 - 21:00", "Disco Disco", "UNANNOUNCED SPECIAL GUESTS & DISCO DISCO RESIDENT DJS"]}}

print("📧 Sending comprehensive Pikes update email...")

# Build email with current events
msg = MIMEMultipart("alternative")
msg["Subject"] = "🎵 Pikes Ibiza - Current Lineup (Jun 8-24)"
msg["From"] = EMAIL
msg["To"] = RECIPIENT

# Build HTML email
html_parts = []

html_parts.append("""<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1f2937; background: #f9fafb; padding: 20px;">
<div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

<div style="background: linear-gradient(135deg, #ff6b9d 0%, #ff8fab 100%); padding: 40px 20px; text-align: center;">
<h1 style="margin: 0; color: white; font-size: 32px;">🎵 Pikes Ibiza</h1>
<p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">June 8-24 Lineup</p>
</div>

<div style="padding: 30px;">
<h2 style="color: #1f2937; margin: 0 0 20px 0; font-size: 20px;">📅 Current Events</h2>
""")

# Add all current events
days_dict = {8: "Mon", 9: "Tue", 10: "Wed", 11: "Thu", 12: "Fri", 13: "Sat", 
            14: "Sun", 15: "Mon", 16: "Tue", 17: "Wed", 18: "Thu", 19: "Fri",
            20: "Sat", 21: "Sun", 22: "Mon", 23: "Tue", 24: "Wed"}

for day_num in range(8, 25):
    day_str = f"June {day_num}"
    day_name = days_dict.get(day_num, "")
    
    if day_str in current_events:
        events = current_events[day_str].get("events", [])
        if events:
            html_parts.append(f'<div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ff6b9d;">')
            html_parts.append(f'<h3 style="margin: 0 0 10px 0; color: #1f2937; font-size: 14px;"><strong>{day_str} ({day_name})</strong></h3>')
            
            for event in events:
                clean_event = event.strip()
                html_parts.append(f'<p style="margin: 5px 0; color: #666; font-size: 13px;">• {clean_event}</p>')
            
            html_parts.append('</div>')

html_parts.append("""
<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 8px; margin: 25px 0;">
<h3 style="margin: 0 0 8px 0; color: #92400e; font-weight: 600;">⏱️ How Monitoring Works</h3>
<ul style="margin: 0; padding-left: 20px; color: #78350f; font-size: 13px; line-height: 1.8;">
<li>📊 This email shows <strong>current baseline</strong></li>
<li>🔄 Next check compares website to this snapshot</li>
<li>🔔 Email sent ONLY if changes detected</li>
<li>🆕 New artists, cancellations, time changes → Alert</li>
<li>✅ No changes → Silent check (no email)</li>
</ul>
</div>

</div>

<div style="background: #f9fafb; border-top: 1px solid #e5e7eb; padding: 20px 30px; text-align: center; font-size: 12px; color: #999;">
<p style="margin: 0;">Email sent: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
<p style="margin: 5px 0 0 0;">Monitor active • Next check: ~48 hours</p>
</div>

</div>
</body></html>""")

html = "".join(html_parts)

msg.attach(MIMEText(html, "html"))

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, RECIPIENT, msg.as_string())
    server.quit()
    print("✅ Comprehensive email sent!")
except Exception as e:
    print(f"Error: {e}")
