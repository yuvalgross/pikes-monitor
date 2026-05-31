#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL = os.getenv("GMAIL_ADDRESS")
PASSWORD = os.getenv("GMAIL_PASSWORD")
RECIPIENT = os.getenv("NOTIFY_EMAIL")

msg = MIMEMultipart("alternative")
msg["Subject"] = "🎉 Pikes Monitor - Test Email SUCCESS!"
msg["From"] = EMAIL
msg["To"] = RECIPIENT

html = '''<html><body style="font-family: Arial, sans-serif; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
<h2 style="color: #ff6b9d;">✅ Pikes Monitor Test Email</h2>
<p>Your email system is <strong>fully operational</strong>!</p>
<h3>What This Means:</h3>
<ul>
<li>✅ GitHub Actions workflow is running</li>
<li>✅ Email notifications are configured</li>
<li>✅ You'll get alerts when Pikes events change</li>
</ul>
<p><strong>Next automated check:</strong> In 48 hours</p>
<p style="color: #666; font-size: 12px; margin-top: 30px;">
Test sent at 2026-05-31 14:45 UTC<br>
Your Pikes monitor is ready for your June trip! 🎵
</p>
</div></body></html>'''

msg.attach(MIMEText(html, "html"))

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(EMAIL, PASSWORD)
server.sendmail(EMAIL, RECIPIENT, msg.as_string())
server.quit()

print("✅ Test email sent!")
