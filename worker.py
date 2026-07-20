#!/usr/bin/env python3
"""
worker.py — автономный процесс-исполнитель одной задачи из таблицы `jobs` (Блок 9).

Целевая архитектура изоляции парсинга: диспетчер в app спавнит этот скрипт как
subprocess под конкретный job, процесс отрабатывает ОДНУ задачу и умирает
(поднялся → выполнил → записал результат → вышел). Так зависший/утёкший Chromium
не тянет за собой процесс FastAPI.

Запуск (обычно спавнит диспетчер app/dispatcher.py, но можно и вручную):
    venv/bin/python worker.py --job <JOB_ID>

Неудача/таймаут отдаются в jobq.retry_or_fail (авто-ретрай пока attempts <
max_attempts, иначе failed) — та же семантика, что была у старого build_queue.

Типы задач:
    • build_site      — payload {"company_id": N} → app.job_tasks.build_site
    • (остальные типы — collect_candidates/create_site/refresh_company/screenshot —
       перенос на jobs отдельной задачей; сейчас дают NotImplementedError)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime


def _load_job(db, job_id: int):
    from app.models import Job
    return db.query(Job).filter(Job.id == job_id).first()


def _finish(db, job, status: str, *, error: str = "", result: str = "", progress: str = ""):
    job.status = status
    job.finished_at = datetime.utcnow()
    if error:
        job.error = error[-4000:]
    if result:
        job.result = result[-4000:]
    if progress:
        job.progress = progress[:255]
    db.commit()


async def _dispatch(job) -> str:
    """Выполняет задачу по её типу. Возвращает строку-результат (или бросает)."""
    try:
        payload = json.loads(job.payload or "{}")
    except Exception:
        payload = {}

    jtype = (job.type or "").strip()

    if jtype == "build_site":
        company_id = payload.get("company_id")
        if not company_id:
            raise ValueError("build_site: в payload нет company_id")
        from app.job_tasks import build_site
        await build_site(int(company_id))
        return f"build_site company_id={company_id} ok"

    # Прочие типы появятся на Step 4 (перенос Фаз 1/2, автообновления, скриншота).
    raise NotImplementedError(f"тип задачи '{jtype}' пока не поддержан в worker.py")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="uqqi job worker (Блок 9)")
    parser.add_argument("--job", type=int, required=True, help="ID задачи из таблицы jobs")
    args = parser.parse_args(argv)

    # Импорт моделей внутри main, чтобы --help не тянул за собой БД/движок.
    from app.models import SessionLocal
    from app import jobq

    db = SessionLocal()
    try:
        job = _load_job(db, args.job)
        if not job:
            print(f"[WORKER] job #{args.job} не найден", flush=True)
            return 2

        if job.status in ("done",):
            print(f"[WORKER] job #{job.id} уже done — пропускаю", flush=True)
            return 0

        # Помечаем running
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.worker_pid = os.getpid()
        job.attempts = (job.attempts or 0) + 1
        db.commit()
        print(f"[WORKER] job #{job.id} type={job.type} pid={os.getpid()} — старт", flush=True)

        timeout = int(job.timeout_sec or 180)
        job_id = job.id
        try:
            result = asyncio.run(asyncio.wait_for(_dispatch(job), timeout=timeout))
            _finish(db, job, "done", result=str(result), progress="готово")
            print(f"[WORKER] job #{job_id} — done", flush=True)
            return 0
        except asyncio.TimeoutError:
            db.close()  # отдаём ретрай/фейл через отдельную сессию jobq
            jobq.retry_or_fail(job_id, error=f"таймаут воркера {timeout}с")
            print(f"[WORKER] job #{job_id} — таймаут {timeout}с", flush=True)
            return 1
        except BaseException as e:
            # BaseException, а не Exception: парсер при отсутствии Playwright и т.п.
            # делает raise SystemExit(2) — его тоже надо пометить, а не оставить 'running'.
            db.close()
            jobq.retry_or_fail(job_id, error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
            print(f"[WORKER] job #{job_id} — ошибка: {type(e).__name__}: {e}", flush=True)
            return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
