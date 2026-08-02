"""
app/dispatcher.py — диспетчер задач парсинга (Блок 9, шаг 3).

Единственный экземпляр в процессе app. Цикл:
  • забирает pending-задачи из `jobs` (не больше MAX_WORKERS одновременно);
  • на каждую спавнит отдельный процесс `worker.py --job <id>` (subprocess);
  • реапит завершившиеся, убивает превысивших таймаут (жёсткая изоляция:
    зависший Chromium умирает вместе со своим процессом, app цел);
  • упавших/убитых без пометки — через jobq.retry_or_fail.

Так Playwright больше НЕ живёт в процессе FastAPI: утечки/зависания и
параллельность=1 уходят. Очередь персистентна (таблица `jobs`).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

from app import jobq

# 4 ГБ RAM, один Chromium 400-700 МБ → безопасный старт с 2 параллельными.
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "2"))
KILL_GRACE = 30            # сек сверх timeout_sec задачи, прежде чем SIGKILL
POLL_SEC = 2              # период опроса очереди

_REPO_ROOT = Path(__file__).resolve().parent.parent
_WORKER_PY = _REPO_ROOT / "worker.py"
_LOG_DIR = _REPO_ROOT / "logs"

# job_id -> (process, start_ts, timeout_sec, logfile)
_procs: dict[int, tuple] = {}


async def _spawn(job_id: int, timeout: int):
    """Спавнит worker.py под задачу. stdout/stderr → logs/worker-<id>.log."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        logf = open(_LOG_DIR / f"worker-{job_id}.log", "wb")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(_WORKER_PY), "--job", str(job_id),
            cwd=str(_REPO_ROOT), stdout=logf, stderr=asyncio.subprocess.STDOUT,
        )
        _procs[job_id] = (proc, time.time(), timeout, logf)
        print(f"[DISPATCH] job #{job_id} → worker pid={proc.pid} (timeout {timeout}с)", flush=True)
    except Exception as e:
        print(f"[DISPATCH] не удалось спавнить job #{job_id}: {e}", flush=True)
        jobq.retry_or_fail(job_id, error=f"spawn failed: {e}")


async def _reap():
    """Проверяет запущенные процессы: завершились / превысили таймаут."""
    for jid, (proc, ts, timeout, logf) in list(_procs.items()):
        if proc.returncode is not None:
            # Завершился сам
            _procs.pop(jid, None)
            try:
                logf.close()
            except Exception:
                pass
            _finalize(jid, proc.returncode)
        elif time.time() - ts > timeout + KILL_GRACE:
            # Завис — убиваем процесс целиком (изоляция от зависшего браузера)
            print(f"[DISPATCH] job #{jid} превысил таймаут — kill pid={proc.pid}", flush=True)
            try:
                proc.kill()
            except Exception:
                pass
            _procs.pop(jid, None)
            try:
                logf.close()
            except Exception:
                pass
            jobq.retry_or_fail(jid, error=f"таймаут диспетчера {timeout}+{KILL_GRACE}с — процесс убит")


def _finalize(job_id: int, returncode: int):
    """Процесс воркера завершился. Если он не пометил job — считаем неудачей."""
    from app.models import SessionLocal, Job
    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.id == job_id).first()
        status = j.status if j else None
    finally:
        db.close()
    # Воркер сам ставит done / failed / (retry→pending). Если остался 'running' —
    # процесс умер, не записав результат: обрабатываем как неудачу.
    if status == "running":
        jobq.retry_or_fail(job_id, error=f"процесс воркера завершился (code {returncode}) без пометки")


async def _tick():
    await _reap()
    free = MAX_WORKERS - len(_procs)
    if free > 0:
        for job_id, timeout in jobq.claim_pending(free):
            await _spawn(job_id, timeout)


async def run_dispatcher():
    """Точка входа: восстановление осиротевших + бесконечный цикл диспетчеризации."""
    if not _WORKER_PY.exists():
        print(f"[DISPATCH] нет {_WORKER_PY} — диспетчер не запущен", flush=True)
        return
    try:
        jobq.recover_orphans()
    except Exception as e:
        print(f"[DISPATCH] recover_orphans: {e}", flush=True)
    print(f"[DISPATCH] Диспетчер запущен (MAX_WORKERS={MAX_WORKERS})", flush=True)
    while True:
        try:
            await _tick()
        except Exception as e:
            print(f"[DISPATCH] tick error: {e}", flush=True)
        await asyncio.sleep(POLL_SEC)
