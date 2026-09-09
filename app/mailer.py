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


# ── Цепочка писем триала / удержания ──────────────────────────────────────────

def _lk_url() -> str:
    return f"https://lk.{settings.BASE_DOMAIN}/"


def _mail_wrap(heading: str, body_html: str, cta_label: str = "", cta_url: str = "") -> str:
    """Общая обёртка письма (шапка с печатью, карточка, опциональная кнопка)."""
    cta = ""
    if cta_label and cta_url:
        cta = (f'<a href="{cta_url}" style="display:inline-block;background:#1a1a1a;color:#fff;'
               f'text-decoration:none;font-weight:600;padding:.8rem 1.8rem;border-radius:12px;'
               f'font-size:.9rem;margin-top:.6rem">{cta_label}</a>')
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
      <h1 style="font-size:1.3rem;margin:0 0 .9rem">{heading}</h1>
      {body_html}
      {cta}
      <p style="font-size:.78rem;color:#999;margin:1.6rem 0 0">{settings.SUPPORT_EMAIL} · платформа uqqi.ru</p>
    </div>
  </div>
</body>
</html>"""


def trial_day3_html(title: str, visitors: int, slug: str) -> str:
    """День 3 триала: сколько людей уже посмотрели сайт."""
    body = (
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
        f'За первые дни ваш сайт <strong>{title}</strong> уже посмотрели '
        f'<strong>{visitors} чел.</strong> — это реальные посетители с адреса '
        f'{slug}.uqqi.ru.</p>'
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1.2rem">'
        f'Сайт индексируется поисковиками и работает на вас круглосуточно. '
        f'Загляните в кабинет — можно обновить фото, часы и контакты.</p>'
    )
    return _mail_wrap("Ваш сайт уже смотрят 👀", body, "Открыть кабинет", _lk_url())


def trial_day6_html(title: str, visitors: int, slug: str) -> str:
    """День 6 триала: заканчивается завтра + метрики + оплата."""
    body = (
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
        f'Пробный период сайта <strong>{title}</strong> заканчивается завтра. '
        f'За это время его посмотрели <strong>{visitors} чел.</strong></p>'
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1.2rem">'
        f'Чтобы сайт продолжил работать без перерыва, оформите подписку в кабинете — '
        f'тарифы от 1990 ₽. Не продлите — сайт скроется, но все данные сохранятся.</p>'
    )
    return _mail_wrap("Триал заканчивается завтра", body, "Продлить сайт", _lk_url())


def welcome_paid_html(title: str, slug: str) -> str:
    """После первой оплаты: что делать дальше."""
    body = (
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
        f'Спасибо за оплату! Сайт <strong>{title}</strong> активен на адресе '
        f'<strong>{slug}.uqqi.ru</strong>.</p>'
        f'<p style="font-size:.92rem;color:#555;line-height:1.6;margin:0 0 .5rem;text-align:left">'
        f'Что стоит сделать дальше:</p>'
        f'<ul style="text-align:left;font-size:.92rem;color:#555;line-height:1.7;margin:0 0 1.2rem;padding-left:1.2rem">'
        f'<li>Проверьте контакты и часы работы в кабинете</li>'
        f'<li>Добавьте свои фото в галерею</li>'
        f'<li>Поделитесь ссылкой в соцсетях и в карточке Яндекс.Карт</li></ul>'
    )
    return _mail_wrap("Сайт оплачен и работает 🎉", body, "Перейти в кабинет", _lk_url())


def monthly_report_html(title: str, visitors: int, slug: str) -> str:
    """Ежемесячный отчёт активному клиенту."""
    body = (
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
        f'За последний месяц сайт <strong>{title}</strong> ({slug}.uqqi.ru) посмотрели '
        f'<strong>{visitors} чел.</strong></p>'
        f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1.2rem">'
        f'Спасибо, что остаётесь с нами. Обновляйте контент в кабинете, чтобы клиенты '
        f'видели актуальную информацию.</p>'
    )
    return _mail_wrap("Отчёт за месяц", body, "Открыть кабинет", _lk_url())


# ── Письма клиенту записи (Pro, онлайн-запись) ───────────────────────────────
# Почта у клиента необязательная: он оставляет её в виджете сам. Если её нет —
# уведомить его нечем, и вызывающий код просто ничего не отправляет.

def booking_changed_html(title: str, when: str, was: str = "", master: str = "") -> str:
    """Владелец перенёс запись клиента."""
    lines = [f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
             f'Ваша запись в <strong>{title}</strong> перенесена.</p>']
    if was:
        lines.append(f'<p style="font-size:.95rem;color:#999;margin:0 0 .3rem">'
                     f'Было: <s>{was}</s></p>')
    lines.append(f'<p style="font-size:1.05rem;font-weight:600;margin:0 0 1rem">Стало: {when}</p>')
    if master:
        lines.append(f'<p style="font-size:.9rem;color:#555;margin:0 0 1rem">Мастер: {master}</p>')
    lines.append('<p style="font-size:.88rem;color:#555;line-height:1.6;margin:0">'
                 'Если время не подходит, свяжитесь с заведением.</p>')
    return _mail_wrap("Запись перенесена", "".join(lines))


def booking_canceled_html(title: str, when: str) -> str:
    """Владелец отменил запись клиента."""
    body = (f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
            f'Ваша запись в <strong>{title}</strong> на {when} отменена заведением.</p>'
            f'<p style="font-size:.88rem;color:#555;line-height:1.6;margin:0">'
            f'Если это ошибка, свяжитесь с заведением — вас запишут заново.</p>')
    return _mail_wrap("Запись отменена", body)


def booking_reminder_html(title: str, when: str, address: str = "", phone: str = "") -> str:
    """Напоминание клиенту за час до визита."""
    rows = [f'<p style="font-size:1.05rem;font-weight:600;margin:0 0 1rem">{when}</p>']
    if address:
        rows.append(f'<p style="font-size:.9rem;color:#555;margin:0 0 .3rem">{address}</p>')
    if phone:
        rows.append(f'<p style="font-size:.9rem;color:#555;margin:0 0 1rem">{phone}</p>')
    body = (f'<p style="font-size:.95rem;color:#555;line-height:1.6;margin:0 0 1rem">'
            f'Напоминаем: сегодня вас ждут в <strong>{title}</strong>.</p>' + "".join(rows))
    return _mail_wrap("Через час вас ждут", body)
