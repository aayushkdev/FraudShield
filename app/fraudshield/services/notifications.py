import json
import os
import smtplib
from email.message import EmailMessage
from urllib.request import Request, urlopen


def notify_high_risk(transaction: dict) -> None:
    if int(transaction.get("RISK_SCORE", 0)) <= 60:
        return

    message = {
        "text": (
            f"FraudShield alert: {transaction['STATUS']} risk={transaction['RISK_SCORE']} "
            f"txn={transaction['TXN_ID']} user={transaction['USER_ID']} "
            f"reasons={transaction.get('ALERT_REASONS', '')}"
        )
    }
    urls = [os.getenv("ALERT_WEBHOOK_URL"), os.getenv("SLACK_WEBHOOK_URL")]
    for url in filter(None, urls):
        try:
            request = Request(
                url,
                data=json.dumps(message, default=str).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5):
                pass
        except Exception as error:
            print(f"Notification failed: {error}", flush=True)

    smtp_host = os.getenv("SMTP_HOST")
    recipient = os.getenv("ALERT_EMAIL_TO")
    if not smtp_host or not recipient:
        return
    try:
        email = EmailMessage()
        email["Subject"] = f"FraudShield alert: {transaction['STATUS']}"
        email["From"] = os.getenv("SMTP_FROM", "fraudshield@localhost")
        email["To"] = recipient
        email.set_content(message["text"])
        with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587")), timeout=5) as client:
            if os.getenv("SMTP_TLS", "true").lower() == "true":
                client.starttls()
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                client.login(smtp_user, smtp_password)
            client.send_message(email)
    except Exception as error:
        print(f"Email notification failed: {error}", flush=True)
