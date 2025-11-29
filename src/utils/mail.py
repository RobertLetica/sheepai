import os
import smtplib
import ssl
import logging
from pathlib import Path
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

# Load environment variables
load_dotenv()

# Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")

def render_template(template_path: str, context: dict) -> str:
    """Render an HTML template with Jinja2 variables."""
    # Adjust path to be relative to src/ if needed, or absolute
    base_dir = Path(__file__).parent.parent
    full_path = base_dir / template_path

    if not full_path.exists():
        # Fallback to checking from current working directory
        full_path = Path(template_path)
    
    if not full_path.exists():
        raise FileNotFoundError(f"Template not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(context)

def send_email(to_email: str, subject: str, html_path: str, context: dict):
    """
    Sends an email using standard SMTP (e.g., Gmail).
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logging.error("SMTP credentials not set in .env")
        return False

    try:
        # Render HTML
        html_content = render_template(html_path, context)

        # Create message container
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"SheepAI <{SENDER_EMAIL}>"
        msg["To"] = to_email

        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))

        # Create secure connection with server and send email
        context_ssl = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context_ssl) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        
        return True

    except Exception as e:
        logging.error(f"Failed to send email via SMTP: {e}")
        return False

def send_otp_email(to_email: str, code: str):
    """
    Specific function to send an OTP email.
    """
    return send_email(
        to_email=to_email,
        subject="Your OTP Code - SheepAI",
        html_path="templates/otp_email.html",
        context={"code": code},
    )