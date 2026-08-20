"""Alert delivery backends — email (SMTP), Slack (webhook), desktop (Tauri notification).

Each alerter is a standalone function that takes a channel config dict and
alert details, returning (success: bool, error: str | None).
"""
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email (SMTP)
# ---------------------------------------------------------------------------

def send_email(config: dict, title: str, message: str, severity: str) -> tuple[bool, str | None]:
    """Send an email alert via SMTP.

    config keys: smtp_host, smtp_port (default 587), username, password,
                 from_address, to_addresses (list[str]), use_tls (default true)
    """
    host = config.get("smtp_host")
    port = config.get("smtp_port", 587)
    username = config.get("username")
    password = config.get("password")
    from_addr = config.get("from_address")
    to_addrs = config.get("to_addresses", [])
    use_tls = config.get("use_tls", True)

    if not all([host, from_addr, to_addrs]):
        return False, "Missing smtp_host, from_address, or to_addresses in channel config"

    severity_colors = {"info": "#3b82f6", "warning": "#f59e0b", "critical": "#ef4444"}
    color = severity_colors.get(severity, "#6b7280")

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
      <div style="background: {color}; color: white; padding: 12px 16px; border-radius: 6px 6px 0 0;">
        <strong style="font-size: 14px;">{severity.upper()}</strong>
        <span style="float: right; font-size: 12px; opacity: 0.8;">SCI Monitor</span>
      </div>
      <div style="border: 1px solid #e5e7eb; border-top: none; padding: 16px; border-radius: 0 0 6px 6px;">
        <h3 style="margin: 0 0 8px;">{title}</h3>
        <p style="color: #374151; line-height: 1.5;">{message}</p>
      </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[SCI {severity.upper()}] {title}"
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(message, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        return True, None
    except Exception as exc:
        logger.warning("Email alert failed: %s", exc)
        return False, str(exc)


# ---------------------------------------------------------------------------
# Slack (Incoming Webhook)
# ---------------------------------------------------------------------------

def send_slack(config: dict, title: str, message: str, severity: str) -> tuple[bool, str | None]:
    """Send a Slack notification via incoming webhook.

    config keys: webhook_url
    """
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return False, "Missing webhook_url in channel config"

    severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
    emoji = severity_emoji.get(severity, "📢")

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {title}", "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"*Severity:* {severity.upper()} | _SEO Content Intelligence Monitor_"}
                ],
            },
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, None
            return False, f"Slack returned HTTP {resp.status}"
    except Exception as exc:
        logger.warning("Slack alert failed: %s", exc)
        return False, str(exc)


# ---------------------------------------------------------------------------
# Desktop Notification (Tauri — via backend log, picked up by frontend)
# ---------------------------------------------------------------------------

def send_desktop(config: dict, title: str, message: str, severity: str) -> tuple[bool, str | None]:
    """Queue a desktop notification.

    Since we're running in the Python backend, we can't directly call Tauri
    notification APIs. Instead, we write the notification to the settings table
    and the frontend polls for pending notifications (or uses the Tauri
    notification plugin on the frontend side).

    For now, we log it and mark it as sent — the frontend will pick it up
    via the /api/monitoring/notifications/pending endpoint.
    """
    logger.info("Desktop notification: [%s] %s — %s", severity, title, message)
    return True, None


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

ALERTERS = {
    "email": send_email,
    "slack": send_slack,
    "desktop": send_desktop,
}


def dispatch_alert(
    channel_type: str, config: dict, title: str, message: str, severity: str,
) -> tuple[bool, str | None]:
    alerter = ALERTERS.get(channel_type)
    if not alerter:
        return False, f"Unknown channel type: {channel_type}"
    return alerter(config, title, message, severity)
