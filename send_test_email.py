#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

EMAIL = os.getenv("GMAIL_ADDRESS", "gross.yuval@gmail.com")
PASSWORD = os.getenv("GMAIL_PASSWORD")
RECIPIENT = os.getenv("NOTIFY_EMAIL", "gross.yuval@gmail.com")

print("📧 Sending test email...")

msg = MIMEMultipart("alternative")
msg["Subject"] = "✅ Pikes Monitor - Test Email"
msg["From"] = EMAIL
msg["To"] = RECIPIENT

html = """<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1f2937; background: #f9fafb; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

<div style="background: linear-gradient(135deg, #ff6b9d 0%, #ff8fab 100%); padding: 40px 20px; text-align: center;">
<h1 style="margin: 0; color: white; font-size: 32px;">🎵 Pikes Ibiza</h1>
<p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">Event Monitor Test Email</p>
</div>

<div style="padding: 40px 30px;">

<h2 style="color: #1f2937; margin: 0 0 20px 0;">✅ System Test Successful!</h2>

<p style="color: #666; font-size: 15px; line-height: 1.6;">
Your Pikes monitor is now <strong>fully configured</strong> with the real baseline from June 8-24.
</p>

<div style="background: #f0f9ff; border-left: 4px solid #ff6b9d; padding: 20px; border-radius: 8px; margin: 25px 0;">
<h3 style="margin: 0 0 12px 0; color: #1f2937;">📊 Current Baseline</h3>
<ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 1.8;">
<li>17 days being monitored (Jun 8-24)</li>
<li>60 event entries tracked</li>
<li>Artists, times, and lineups locked in</li>
<li>Ready to detect ANY changes</li>
</ul>
</div>

<h3 style="color: #1f2937; margin: 30px 0 12px 0; font-size: 15px;">🔔 You'll Get Email Alerts When:</h3>
<ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 1.8;">
<li>🆕 "COMING SOON" lineups get announced</li>
<li>🎤 Artists change or are added</li>
<li>❌ Events are cancelled</li>
<li>⏰ Times are updated</li>
<li>🔄 Anything changes on Pikes website</li>
</ul>

<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 8px; margin: 25px 0;">
<h3 style="margin: 0 0 8px 0; color: #92400e; font-weight: 600;">⏱️ Next Check</h3>
<p style="margin: 0; color: #78350f; font-size: 13px;">Automatic in ~48 hours, or trigger manually on GitHub</p>
</div>

</div>

<div style="background: #f9fafb; border-top: 1px solid #e5e7eb; padding: 20px 30px; text-align: center; font-size: 12px; color: #999;">
<p style="margin: 0;">Test sent: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
<p style="margin: 5px 0 0 0;">Your Pikes monitor is LIVE and ready for your June 8-24 trip! 🎊</p>
</div>

</div>
</body></html>"""

msg.attach(MIMEText(html, "html"))

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, RECIPIENT, msg.as_string())
    server.quit()
    print("✅ Email sent!")
except Exception as e:
    print(f"Error: {e}")
