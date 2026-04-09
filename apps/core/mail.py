"""
Gmail SMTP 발송 — 관리자 이메일 배치 등에서 사용.
env: GMAIL_SENDER, GMAIL_APP_PASSWORD(또는 GOOGLE_API_KEY에 앱 비밀번호)
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    *,
    from_email: str | None = None,
    from_display_name: str | None = None,
    reply_to: str | None = None,
) -> bool:
    sender = (os.getenv("GMAIL_SENDER") or "").strip()
    password = (os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GOOGLE_API_KEY") or "").strip()

    if not sender:
        logger.warning("메일 발송 건너뜀: GMAIL_SENDER가 설정되지 않았습니다.")
        return False
    if not password:
        logger.warning("메일 발송 건너뜀: GMAIL_APP_PASSWORD 또는 GOOGLE_API_KEY가 설정되지 않았습니다.")
        return False
    if password.startswith("AIza"):
        logger.warning(
            "메일 발송 건너뜀: GOOGLE_API_KEY에 Google API 키가 설정되어 있습니다. "
            "Gmail 발송에는 앱 비밀번호가 필요합니다."
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["To"] = to_email

    from_addr = (from_email or "").strip()
    if from_addr:
        if from_display_name and from_display_name.strip():
            msg["From"] = formataddr((from_display_name.strip(), from_addr))
        else:
            msg["From"] = from_addr
        rt = (reply_to or from_addr).strip()
        if rt:
            msg["Reply-To"] = rt
    else:
        msg["From"] = sender

    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        logger.info("메일 발송 성공: to=%s", to_email)
        return True
    except Exception as e:
        logger.exception("메일 발송 실패: to=%s, error=%s", to_email, e)
        return False
