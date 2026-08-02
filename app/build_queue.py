"""
app/build_queue.py — постановка сборки сайта в очередь (Блок 9).

Очередь теперь персистентна: `enqueue` пишет задачу `build_site` в таблицу `jobs`,
а исполняет её ОТДЕЛЬНЫЙ процесс `worker.py`, которым управляет диспетчер
(`app/dispatcher.py`). Прежний in-memory asyncio-воркор удалён (шаг 5) — Playwright
больше не живёт в процессе FastAPI.

Логика самой сборки — в `app/job_tasks.py`; реэкспорт ниже для обратной
совместимости старых импортов.
"""

from __future__ import annotations

from app import jobq
from app.job_tasks import (
    build_site,          # noqa: F401 — сама сборка (используется worker.py)
    job_log as _log,     # noqa: F401 — реэкспорт для старых импортов
    _clean_menu_photos,  # noqa: F401
    TRIAL_DAYS,          # noqa: F401
)


def enqueue(company_id: int):
    """Ставит сайт в очередь на сборку — создаёт задачу build_site в таблице `jobs`."""
    jobq.enqueue_build(company_id)
