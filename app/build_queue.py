"""
app/build_queue.py — фоновая очередь создания сайтов из ссылки Яндекса.
Лимит: 1 парсинг одновременно. Триал 7 дней с момента готовности.

Сами задачи парсинга вынесены в app/job_tasks.py (Блок 9) — этот модуль
оставляет только очередь/воркер/ретраи в процессе app. Целевая архитектура:
диспетчер + worker.py (subprocess) будут использовать те же job_tasks.
"""

from __future__ import annotations

import asyncio

from app.models import SessionLocal, Company
# Логика самой сборки — общий модуль (используется и app-воркером, и worker.py).
from app.job_tasks import (
    build_site as _build_one,
    job_log as _log,
    _clean_menu_photos,  # noqa: F401 — реэкспорт для обратной совместимости импортов
    TRIAL_DAYS,          # noqa: F401 — реэкспорт для обратной совместимости импортов
)

BUILD_TIMEOUT = 180        # общий таймаут на одну сборку, сек (3 минуты)
MAX_ATTEMPTS = 3           # всего попыток: 1 основная + 2 авто-ретрая


# Очередь company_id на парсинг и единственный воркер
_queue: asyncio.Queue[int] = asyncio.Queue()
_worker_started = False


def ensure_worker():
    """Запускает воркер очереди один раз."""
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    asyncio.create_task(_worker())
    print("[BUILD] Воркер очереди парсинга запущен", flush=True)


def enqueue(company_id: int):
    """Ставит сайт в очередь на сборку."""
    ensure_worker()
    _queue.put_nowait(company_id)


async def _worker():
    """Обрабатывает очередь по одному сайту с общим таймаутом и авто-ретраем."""
    while True:
        company_id = await _queue.get()
        try:
            # Общий таймаут на всю сборку
            await asyncio.wait_for(_build_one(company_id), timeout=BUILD_TIMEOUT)
        except asyncio.TimeoutError:
            _log(company_id, f"⏱ Превышен таймаут {BUILD_TIMEOUT}с — сборка прервана")
            _handle_failure(company_id)
        except Exception as e:
            _log(company_id, f"✖ Ошибка сборки: {type(e).__name__}: {e}")
            _handle_failure(company_id)
        finally:
            _queue.task_done()


def _handle_failure(company_id: int):
    """
    Обрабатывает неудачу: если попыток меньше MAX_ATTEMPTS — авто-ретрай,
    иначе помечает error (пользователь жмёт «Попробовать снова»).
    """
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if not c:
            return
        attempts = (c.build_attempts or 0)
        if attempts < MAX_ATTEMPTS:
            c.build_status = "queued"  # вернём в очередь
            db.commit()
            db.close()
            _log(company_id, f"↻ Авто-повтор (попытка {attempts + 1} из {MAX_ATTEMPTS})")
            enqueue(company_id)
            return
        else:
            c.build_status = "error"
            db.commit()
            _log(company_id, "✖ Исчерпаны попытки — статус error")
    finally:
        try:
            db.close()
        except Exception:
            pass


def _mark_error(company_id: int):
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if c:
            c.build_status = "error"
            db.commit()
    finally:
        db.close()
