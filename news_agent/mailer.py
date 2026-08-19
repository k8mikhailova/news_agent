"""
Sends the rendered HTML report as an email via Gmail's SMTP server.

Requires a Gmail APP PASSWORD, not your normal Gmail password --
Gmail blocks plain password login for SMTP. Setup:
1. Turn on 2-Step Verification on your Google account (required first)
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail" -> copy the 16-character code

If you'd rather not deal with Gmail app passwords, a transactional
email API (Resend, SendGrid) is a drop-in alternative -- ask if you'd
rather swap to one of those.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(html_body: str, subject: str = "Your Daily Briefing") -> None:
    sender = os.environ.get("EMAIL_FROM")
    app_password = os.environ.get("EMAIL_APP_PASSWORD")
    recipient = os.environ.get("EMAIL_TO", sender)

    if not sender or not app_password:
        raise SystemExit(
            "Set EMAIL_FROM and EMAIL_APP_PASSWORD environment variables first.\n"
            "See README.md for how to create a Gmail app password."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, recipient, msg.as_string())
