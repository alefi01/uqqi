"""
app/mailer.py — отправка email через SMTP Beget
"""

from __future__ import annotations

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from app.config import settings


def send_email(to: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Отправляет письмо. Возвращает True при успехе."""
    if not to or "@" not in to:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("uqqi", settings.SMTP_FROM))
    msg["To"] = to
    msg["Reply-To"] = settings.SUPPORT_EMAIL

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=20) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        return True
    except Exception as e:
        print(f"[MAIL] Ошибка отправки на {to}: {e}", flush=True)
        return False


def billing_reminder_html(company_title: str, days_left: int, pay_date: str) -> str:
    """HTML-шаблон письма-напоминания об оплате."""
    word = "дней"
    if days_left == 1:
        word = "день"
    elif days_left in (2, 3, 4):
        word = "дня"

    return f"""\
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#faf8f4;font-family:Arial,Helvetica,sans-serif;color:#1a1a1a">
  <div style="max-width:520px;margin:0 auto;padding:2rem 1.5rem">
    <div style="background:#fff;border:1px solid #e8e4dc;border-radius:18px;padding:2.5rem 2rem;text-align:center">
      <div style="width:64px;height:64px;margin:0 auto 1.5rem">
        <img src="https://uqqi.ru/static/logo-seal.png" alt="uqqi" style="width:100%;height:100%;object-fit:contain">
      </div>
      <h1 style="font-size:1.3rem;margin:0 0 .75rem">Подходит срок оплаты сайта</h1>
      <p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">
        Здравствуйте! Напоминаем, что срок размещения сайта
        <strong>{company_title}</strong> истекает через <strong>{days_left} {word}</strong> — {pay_date}.
      </p>
      <p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1.5rem">
        Чтобы сайт продолжил работать без перерыва, продлите размещение.
        Реквизиты и детали пришлём в ответном письме.
      </p>
      <a href="mailto:{settings.SUPPORT_EMAIL}?subject=Продление сайта {company_title}"
         style="display:inline-block;background:#1a1a1a;color:#fff;text-decoration:none;font-weight:600;padding:.8rem 1.8rem;border-radius:12px;font-size:.9rem">
        Продлить сайт
      </a>
      <p style="font-size:.78rem;color:#999;margin:1.5rem 0 0">
        {settings.SUPPORT_EMAIL} · платформа uqqi.ru
      </p>
    </div>
  </div>
</body>
</html>"""
