"""
Sends emails via Yahoo SMTP using an app password.
Requires env vars: YAHOO_EMAIL, YAHOO_APP_PASSWORD
"""
import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.mail.yahoo.com"
SMTP_PORT = 587


def send_email(to_email: str, subject: str, body: str, from_name: str, from_email: str):
    password = os.environ["YAHOO_APP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, [to_email], msg.as_string())
