import os
from pathlib import Path
from dotenv import load_dotenv
import resend
from jinja2 import Template

# Load environment variables
load_dotenv()

# Configure Resend API
resend.api_key = os.getenv("RESEND_API_KEY")
DEFAULT_FROM = os.getenv("FROM_EMAIL", "App <no-reply@example.com>")


def render_template(template_path: str, context: dict) -> str:
    """
    Render an HTML template with Jinja2 variables.
    """
    template_path = Path(template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(context)


def send_email(to_email: str, subject: str, html_path: str, context: dict):
    """
    Generic email sender using Resend + HTML template.
    """
    html_content = render_template(html_path, context)

    return resend.Emails.send(
        {
            "from": DEFAULT_FROM,
            "to": to_email,
            "subject": subject,
            "html": html_content,
        }
    )


def send_otp_email(to_email: str, code: str):
    """
    Specific function to send an OTP email using otp_email.html template.
    """
    return send_email(
        to_email=to_email,
        subject="Your OTP Code",
        html_path="templates/otp_email.html",
        context={"code": code},
    )
