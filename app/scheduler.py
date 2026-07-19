"""
app/scheduler.py — фоновые задачи (asyncio):
  • проверка биллинга (уведомления за 7 и 3 дня)
  • автообновление данных (1 компания в час)
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta

from app.config import settings
from app.models import SessionLocal, Company
from app.mailer import (send_email, billing_reminder_html,
                        welcome_paid_html, monthly_report_html)


def _visitors_count(db, slug: str, days: int) -> int:
    """Уники (по visitor_hash) для сайта за последние N дней — из visits."""
    from sqlalchemy import text as _sql
    cut = (datetime.utcnow().date() - timedelta(days=days)).strftime("%Y-%m-%d")
    row = db.execute(_sql(
        "SELECT COUNT(DISTINCT visitor_hash) FROM visits WHERE target = :t AND day >= :d"
    ), {"t": slug, "d": cut}).scalar()
    return int(row or 0)


_RUNNING = False

# Heartbeat планировщика: обновляется в _loop_monitor, читается /health.
_HEARTBEAT_TS: float = 0.0


def heartbeat_age() -> float | None:
    """Секунд с последнего обновления heartbeat, либо None если ни разу."""
    if not _HEARTBEAT_TS:
        return None
    return time.time() - _HEARTBEAT_TS


async def _billing_check():
    """Раз в сутки: проверяет даты оплаты, шлёт письма за 7 и 3 дня. Чистит старые визиты."""
    db = SessionLocal()
    try:
        # Чистка визитов старше 90 дней
        try:
            from sqlalchemy import text as _sql
            from datetime import timedelta as _td2
            cutoff = (datetime.utcnow().date() - _td2(days=90)).strftime("%Y-%m-%d")
            db.execute(_sql("DELETE FROM visits WHERE day < :c"), {"c": cutoff})
            db.commit()
        except Exception as e:
            print(f"[VISITS] Ошибка чистки: {e}", flush=True)

        # Чистка неподтверждённых регистраций старше 7 дней
        try:
            from app.models import User
            from datetime import timedelta as _td3
            stale = datetime.utcnow() - _td3(days=7)
            n = db.query(User).filter(
                User.email_verified == False,  # noqa: E712
                User.created_at < stale,
            ).delete()
            db.commit()
            if n:
                print(f"[USERS] Удалено неподтверждённых регистраций: {n}", flush=True)
        except Exception as e:
            print(f"[USERS] Ошибка чистки регистраций: {e}", flush=True)

        now = datetime.utcnow()
        companies = db.query(Company).filter(
            Company.next_payment_date.isnot(None),
            Company.client_email != "",
            Company.is_active == True,  # noqa: E712
        ).all()

        for c in companies:
            if not c.next_payment_date:
                continue
            days_left = (c.next_payment_date.date() - now.date()).days

            # за 7 дней
            if days_left == 7 and not c.notified_7d:
                ok = send_email(
                    c.client_email,
                    f"Напоминание: оплата сайта {c.title} через 7 дней",
                    billing_reminder_html(c.title, 7, c.next_payment_date.strftime("%d.%m.%Y")),
                )
                if ok:
                    c.notified_7d = True
                    db.commit()
                    print(f"[BILLING] Уведомление 7д отправлено: {c.client_email}", flush=True)

            # за 3 дня
            elif days_left == 3 and not c.notified_3d:
                ok = send_email(
                    c.client_email,
                    f"Напоминание: оплата сайта {c.title} через 3 дня",
                    billing_reminder_html(c.title, 3, c.next_payment_date.strftime("%d.%m.%Y")),
                )
                if ok:
                    c.notified_3d = True
                    db.commit()
                    print(f"[BILLING] Уведомление 3д отправлено: {c.client_email}", flush=True)

        # ── Клиентские подписки (кабинет): напоминания по paid_until и trial_ends_at ──
        from app.models import User
        client_sites = db.query(Company).filter(
            Company.user_id.isnot(None),
            Company.is_active == True,  # noqa: E712
        ).all()

        for c in client_sites:
            # email владельца
            owner = db.query(User).filter(User.id == c.user_id).first()
            if not owner or not owner.email:
                continue
            email = owner.email

            # ── ОПЛАЧЕННЫЕ Pro: welcome, продление 7/3 дня, ежемесячный отчёт ──
            # (Триал-письма day3/day6 убраны: в freemium триал — это Pro-триал без
            #  таймера подписки; sub_status "trial" больше не выставляется.)
            if c.sub_status == "active" and c.paid_until:
                # Приветственное письмо после первой оплаты («что дальше»).
                # Заодно стартуем отсчёт ежемесячного отчёта, чтобы он не ушёл сразу.
                if not c.welcome_sent:
                    if send_email(email, f"Сайт «{c.title}» оплачен — что дальше",
                                  welcome_paid_html(c.title, c.slug)):
                        c.welcome_sent = True
                        c.last_report_at = now
                        db.commit()

                days_left = (c.paid_until.date() - now.date()).days
                if days_left == 7 and not c.notified_7d:
                    if send_email(email, f"Сайт {c.title}: продление через 7 дней",
                                  billing_reminder_html(c.title, 7, c.paid_until.strftime("%d.%m.%Y"))):
                        c.notified_7d = True
                        db.commit()
                elif days_left == 3 and not c.notified_3d:
                    if send_email(email, f"Сайт {c.title}: продление через 3 дня",
                                  billing_reminder_html(c.title, 3, c.paid_until.strftime("%d.%m.%Y"))):
                        c.notified_3d = True
                        db.commit()

                # Ежемесячный отчёт активному клиенту (не чаще раза в 30 дней)
                if c.welcome_sent and (c.last_report_at is None
                                       or (now - c.last_report_at) >= timedelta(days=30)):
                    v = _visitors_count(db, c.slug, 30)
                    if send_email(email, f"Отчёт за месяц по сайту «{c.title}»",
                                  monthly_report_html(c.title, v, c.slug)):
                        c.last_report_at = now
                        db.commit()
    except Exception as e:
        print(f"[BILLING] Ошибка проверки: {e}", flush=True)
    finally:
        db.close()


async def _auto_refresh_one():
    """Раз в час: обновляет одну самую давно не обновлённую компанию."""
    if not settings.AUTO_REFRESH_ENABLED:
        return

    db = SessionLocal()
    try:
        # Берём активную компанию с картой, не помеченную недоступной,
        # самую давнюю по last_parsed_at (NULL — первыми)
        company = db.query(Company).filter(
            Company.is_active == True,            # noqa: E712
            Company.yandex_unavailable == False,  # noqa: E712
            Company.yandex_url != "",
        ).order_by(Company.last_parsed_at.asc().nullsfirst()).first()

        if not company:
            return

        # Не обновляем если парсили < 20 часов назад
        if company.last_parsed_at and (datetime.utcnow() - company.last_parsed_at) < timedelta(hours=20):
            return

        print(f"[AUTO-REFRESH] Обновляю: {company.title}", flush=True)
        # Ленивый импорт чтобы избежать циклической зависимости
        from app.owner import _refresh_single_company
        result = await _refresh_single_company(company, db)
        print(f"[AUTO-REFRESH] {company.title}: {result.get('message', result)}", flush=True)
    except Exception as e:
        print(f"[AUTO-REFRESH] Ошибка: {e}", flush=True)
    finally:
        db.close()


async def _loop_billing():
    """Цикл биллинга — раз в 24 часа."""
    # первая проверка через 60 сек после старта
    await asyncio.sleep(60)
    while True:
        await _billing_check()
        await asyncio.sleep(24 * 3600)


async def _loop_refresh():
    """Цикл автообновления — раз в час."""
    # первый запуск через 5 минут после старта
    await asyncio.sleep(300)
    while True:
        await _auto_refresh_one()
        await asyncio.sleep(3600)


async def _watchdog_stuck_builds():
    """
    Сторож зависших сборок: сайты в 'building' дольше N минут считаем зависшими.
    Передаём в обработчик неудачи (авто-ретрай или error). Раз в минуту.
    """
    from datetime import datetime, timedelta
    STUCK_MINUTES = 5
    await asyncio.sleep(120)  # первый прогон через 2 мин после старта
    while True:
        try:
            from app.models import SessionLocal, Company
            from app.build_queue import _handle_failure, _log
            db = SessionLocal()
            try:
                cutoff = datetime.utcnow() - timedelta(minutes=STUCK_MINUTES)
                stuck = db.query(Company).filter(
                    Company.build_status == "building",
                    Company.last_parsed_at.is_(None) | (Company.last_parsed_at < cutoff),
                ).all()
                # Доп. фильтр по дате создания, если last_parsed_at пуст
                ids = []
                for c in stuck:
                    ref = c.last_parsed_at or c.created_at
                    if ref and ref < cutoff:
                        ids.append(c.id)
                    elif not ref:
                        ids.append(c.id)
            finally:
                db.close()
            for cid in ids:
                _log(cid, f"🔧 Watchdog: сборка зависла (>{STUCK_MINUTES} мин), перезапускаю")
                _handle_failure(cid)
        except Exception as e:
            print(f"[WATCHDOG] Ошибка: {e}", flush=True)
        await asyncio.sleep(60)


def _recover_orphaned_builds():
    """
    При старте приложения: сайты, застрявшие в building/queued после рестарта сервиса,
    возвращаем в очередь (сервис мог упасть посреди сборки).
    """
    try:
        from app.models import SessionLocal, Company
        from app.build_queue import enqueue, _log
        db = SessionLocal()
        try:
            orphans = db.query(Company).filter(
                Company.build_status.in_(["building", "queued"])
            ).all()
            ids = [c.id for c in orphans]
        finally:
            db.close()
        for cid in ids:
            _log(cid, "♻ Восстановление после рестарта — возвращаю в очередь")
            enqueue(cid)
        if ids:
            print(f"[RECOVER] Возвращено в очередь после старта: {ids}", flush=True)
    except Exception as e:
        print(f"[RECOVER] Ошибка: {e}", flush=True)


async def _loop_watchdog():
    await _watchdog_stuck_builds()


async def _cleanup_old_visit_logs():
    """Удаляет visit_logs старше 90 дней (ретенция IP) + чистит rate-бакеты и ротирует access.log."""
    from datetime import datetime as _dt, timedelta as _td
    from sqlalchemy import text as _sql
    from app.models import SessionLocal
    db = SessionLocal()
    try:
        cut = _dt.utcnow() - _td(days=90)
        res = db.execute(_sql("DELETE FROM visit_logs WHERE created_at < :c"), {"c": cut})
        db.commit()
        if res.rowcount:
            print(f"[CLEANUP] Удалено visit_logs старше 90 дней: {res.rowcount}", flush=True)
    except Exception as e:
        print(f"[CLEANUP] Ошибка: {e}", flush=True)
    finally:
        db.close()
    # Чистка rate-limit бакетов
    try:
        from app.security import cleanup_buckets
        cleanup_buckets()
    except Exception:
        pass
    # Ротация access.log: если больше 50 МБ — оставляем последние ~10 МБ
    try:
        import os
        from app.security import ACCESS_LOG_PATH
        if os.path.exists(ACCESS_LOG_PATH) and os.path.getsize(ACCESS_LOG_PATH) > 50 * 1024 * 1024:
            with open(ACCESS_LOG_PATH, "rb") as f:
                f.seek(-10 * 1024 * 1024, os.SEEK_END)
                tail = f.read()
            with open(ACCESS_LOG_PATH, "wb") as f:
                f.write("# (лог обрезан при ротации)\n".encode("utf-8") + tail)
            print("[CLEANUP] access.log обрезан (ротация)", flush=True)
    except Exception:
        pass


async def _loop_cleanup():
    """Раз в сутки чистит старые логи визитов."""
    while True:
        await _cleanup_old_visit_logs()
        await asyncio.sleep(86400)  # раз в сутки


# ── Мониторинг ────────────────────────────────────────────────────────────────

DISK_ALERT_PCT = 85       # порог заполнения диска для алерта
BUILD_FAIL_ALERT = 3      # столько ошибок сборки за час → алерт


def _check_disk():
    """Диск заполнен > DISK_ALERT_PCT % → алерт в Telegram (троттл 6 ч)."""
    try:
        import shutil
        from app.notifier import send_telegram
        total, used, free = shutil.disk_usage("/")
        pct = used * 100 // total
        if pct >= DISK_ALERT_PCT:
            free_gb = free / (1024 ** 3)
            send_telegram(
                f"🟠 uqqi: диск заполнен на {pct}% (свободно {free_gb:.1f} ГБ). "
                f"Почисти логи/бэкапы/кеши.",
                key="disk", throttle_sec=6 * 3600,
            )
    except Exception as e:
        print(f"[MONITOR] disk check: {e}", flush=True)


def _check_build_failures():
    """За последний час BUILD_FAIL_ALERT+ сайтов в 'error' → алерт (троттл 1 ч)."""
    try:
        from app.notifier import send_telegram
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=1)
            # last_parsed_at обновляется при попытке; для error берём created_at как запас
            q = db.query(Company).filter(Company.build_status == "error")
            recent = [c for c in q.all()
                      if (c.last_parsed_at or c.created_at or datetime.min) >= cutoff]
            n = len(recent)
        finally:
            db.close()
        if n >= BUILD_FAIL_ALERT:
            send_telegram(
                f"🟠 uqqi: за последний час сборок в ошибке: {n}. "
                f"Проверь journalctl -u uqqi (капча/парсер/память?).",
                key="build_fail", throttle_sec=3600,
            )
    except Exception as e:
        print(f"[MONITOR] build check: {e}", flush=True)


async def _loop_monitor():
    """
    Раз в 60с обновляет heartbeat (его читает /health).
    Раз в ~5 мин — проверки диска и ошибок сборки с алертами в Telegram.
    """
    global _HEARTBEAT_TS
    tick = 0
    while True:
        _HEARTBEAT_TS = time.time()
        if tick % 5 == 0:  # каждые ~5 минут
            _check_disk()
            _check_build_failures()
        tick += 1
        await asyncio.sleep(60)


# ── Реконсиляция платежей (safety net к webhook) ──────────────────────────────

async def _reconcile_pending_payments():
    """
    Сами перепроверяем pending-платежи у ЮKassa: webhook мог не дойти, или
    проверка в момент webhook временно упала (fail-closed оставил pending).
    Применяем только через _verify_and_apply_payment (статус + сумма).
    Берём платежи за последние 48ч, чтобы не дёргать API по древним.
    """
    if not settings.YUKASSA_SHOP_ID:
        return
    db = SessionLocal()
    try:
        from app.models import Payment
        from app.cabinet import _verify_and_apply_payment
        cutoff = datetime.utcnow() - timedelta(hours=48)
        pending = db.query(Payment).filter(
            Payment.status == "pending",
            Payment.created_at >= cutoff,
        ).all()
        for p in pending:
            try:
                applied, note = _verify_and_apply_payment(p.payment_id, db)
                if applied:
                    print(f"[RECONCILE] {p.payment_id}: {note}", flush=True)
            except Exception as e:
                print(f"[RECONCILE] {p.payment_id}: {e}", flush=True)
    except Exception as e:
        print(f"[RECONCILE] Ошибка: {e}", flush=True)
    finally:
        db.close()


async def _loop_reconcile():
    """Реконсиляция платежей — раз в 10 мин, первый прогон через 3 мин после старта."""
    await asyncio.sleep(180)
    while True:
        await _reconcile_pending_payments()
        await asyncio.sleep(600)


# ── Telegram: чат с сайтов (Pro) ──────────────────────────────────────────────
# Приём апдейтов бота long-poll'ом getUpdates (без вебхука). Обрабатываем:
#  • /start <token> — привязка Telegram владельца (deep-link из ЛК);
#  • Reply на пересланное сообщение — ответ владельца посетителю.

from pathlib import Path as _Path
_TG_OFFSET_PATH = _Path(__file__).resolve().parent.parent / "logs" / "tg_offset"
_tg_offset = 0


def _tg_load_offset():
    global _tg_offset
    try:
        _tg_offset = int(_TG_OFFSET_PATH.read_text().strip())
    except Exception:
        _tg_offset = 0


def _tg_save_offset(n: int):
    try:
        _TG_OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TG_OFFSET_PATH.write_text(str(n))
    except Exception:
        pass


def _handle_tg_update(up: dict):
    from app.models import SessionLocal, User, Company, ChatMessage
    from app.telegram_bot import tg_send_message

    msg = up.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip()
    update_id = up.get("update_id")
    if not chat_id or not text:
        return

    # /start <token> — привязка владельца по одноразовому токену из ЛК
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        token = parts[1].strip() if len(parts) > 1 else ""
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.tg_link_token == token).first() if token else None
            if u:
                u.tg_chat_id = str(chat_id)
                u.tg_link_token = ""
                db.commit()
                tg_send_message(str(chat_id),
                    "✅ Telegram подключён. Сюда будут приходить сообщения с вашего сайта. "
                    "Отвечайте на них через «Ответить» (Reply).")
            else:
                tg_send_message(str(chat_id),
                    "Чтобы подключить уведомления, откройте «Подключить Telegram» в личном кабинете uqqi.ru.")
        finally:
            db.close()
        return

    # Ответ владельца: Reply на пересланное сообщение посетителя
    reply = msg.get("reply_to_message") or {}
    reply_mid = reply.get("message_id")
    db = SessionLocal()
    try:
        # дедуп по update_id (переобработка после рестарта)
        if update_id and db.query(ChatMessage).filter(ChatMessage.tg_update_id == update_id).first():
            return
        src = None
        if reply_mid:
            src = db.query(ChatMessage).filter(
                ChatMessage.notify_msg_id == reply_mid,
                ChatMessage.direction == "in",
            ).first()
        if not src:
            tg_send_message(str(chat_id),
                "Чтобы ответить посетителю, используйте «Ответить» (Reply) на его сообщение с сайта.")
            return
        c = db.query(Company).filter(Company.id == src.company_id).first()
        owner = db.query(User).filter(User.id == c.user_id).first() if c else None
        if not owner or str(owner.tg_chat_id) != str(chat_id):
            return  # отвечает не владелец этого сайта
        out = ChatMessage(company_id=src.company_id, visitor_id=src.visitor_id,
                          direction="out", text=text[:2000], tg_update_id=update_id)
        db.add(out)
        db.commit()
    finally:
        db.close()


def _tg_poll_once() -> int:
    """Один цикл getUpdates + обработка (блокирующий, крутится в потоке)."""
    from app.telegram_bot import tg_get_updates
    global _tg_offset
    updates = tg_get_updates(_tg_offset, 20)
    for up in updates:
        _tg_offset = max(_tg_offset, (up.get("update_id") or 0) + 1)
        try:
            _handle_tg_update(up)
        except Exception as e:
            print(f"[TG] handle error: {e}", flush=True)
    if updates:
        _tg_save_offset(_tg_offset)
    return len(updates)


async def _loop_telegram():
    """Long-poll апдейтов бота (чат с сайтов). Блокирующие вызовы — в отдельном потоке."""
    if not (settings.TELEGRAM_BOT_TOKEN or "").strip():
        print("[TG] бот не настроен — чат-поллинг выключен", flush=True)
        return
    _tg_load_offset()
    await asyncio.sleep(5)
    while True:
        try:
            n = await asyncio.to_thread(_tg_poll_once)
            if n == 0:
                await asyncio.sleep(2)
        except Exception as e:
            print(f"[TG] poll error: {e}", flush=True)
            await asyncio.sleep(10)


def start_scheduler():
    """Запускает фоновые задачи. Вызывается из main при старте."""
    global _RUNNING
    if _RUNNING:
        return
    _RUNNING = True
    loop = asyncio.get_event_loop()
    loop.create_task(_loop_billing())
    loop.create_task(_loop_refresh())
    loop.create_task(_loop_watchdog())
    loop.create_task(_loop_cleanup())
    loop.create_task(_loop_monitor())
    loop.create_task(_loop_reconcile())
    loop.create_task(_loop_telegram())
    print("[SCHEDULER] Фоновые задачи запущены (биллинг + автообновление + watchdog + очистка логов + мониторинг + реконсиляция платежей + telegram-чат)", flush=True)
