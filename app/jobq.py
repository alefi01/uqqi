"""
app/jobq.py — состояние очереди задач в таблице `jobs` (Блок 9, шаг 3).

Чистая DB-логика (без asyncio и subprocess) — используется и диспетчером в app,
и процессом worker.py. Одна задача = одна строка `jobs`.

Статусы: pending → running → done | failed. Ретраи: пока attempts < max_attempts
задача возвращается в pending; иначе — failed. Для build_site заодно двигаем
Company.build_status (queued/building/ready/error) для UI.
"""

from __future__ import annotations

import json
from datetime import datetime

from app.models import SessionLocal, Job, Company


def _job_company_id(job) -> int | None:
    try:
        return json.loads(job.payload or "{}").get("company_id")
    except Exception:
        return None


def _set_company_build_status(db, company_id, status: str):
    if not company_id:
        return
    c = db.query(Company).filter(Company.id == company_id).first()
    if c:
        c.build_status = status


def has_active_build(db, company_id: int) -> bool:
    """Есть ли уже незавершённая (pending/running) задача сборки для этой компании."""
    for j in db.query(Job).filter(
        Job.type == "build_site", Job.status.in_(("pending", "running"))
    ).all():
        if _job_company_id(j) == company_id:
            return True
    return False


def enqueue_build(company_id: int) -> int | None:
    """Ставит задачу сборки сайта в очередь (dedup по company_id). Возвращает job_id."""
    db = SessionLocal()
    try:
        if has_active_build(db, company_id):
            return None  # уже в очереди/собирается — не дублируем
        job = Job(
            type="build_site",
            payload=json.dumps({"company_id": company_id}),
            status="pending",
            max_attempts=3,
            timeout_sec=180,
        )
        db.add(job)
        _set_company_build_status(db, company_id, "queued")
        db.commit()
        return job.id
    finally:
        db.close()


def claim_pending(n: int) -> list[tuple[int, int]]:
    """
    Забирает до n задач из pending в running (единственный диспетчер — гонок нет).
    Возвращает список (job_id, timeout_sec).
    """
    if n <= 0:
        return []
    db = SessionLocal()
    try:
        rows = (
            db.query(Job)
            .filter(Job.status == "pending")
            .order_by(Job.created_at.asc())
            .limit(n)
            .all()
        )
        out = []
        for r in rows:
            r.status = "running"
            r.started_at = datetime.utcnow()
            out.append((r.id, int(r.timeout_sec or 180)))
        db.commit()
        return out
    finally:
        db.close()


def retry_or_fail(job_id: int, error: str = ""):
    """
    Неудача задачи: пока попыток меньше лимита — обратно в pending (авто-ретрай),
    иначе — failed. Для build_site двигает Company.build_status (queued/error).
    """
    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.id == job_id).first()
        if not j:
            return
        cid = _job_company_id(j)
        if (j.attempts or 0) < (j.max_attempts or 3):
            j.status = "pending"
            j.worker_pid = None
            j.error = (error or "")[-4000:]
            if j.type == "build_site":
                _set_company_build_status(db, cid, "queued")
        else:
            j.status = "failed"
            j.finished_at = datetime.utcnow()
            j.error = (error or "")[-4000:]
            if j.type == "build_site":
                _set_company_build_status(db, cid, "error")
        db.commit()
    finally:
        db.close()


def recover_orphans():
    """
    При старте app: задачи, застрявшие в 'running' (их worker умер вместе со старым
    процессом), возвращаем через retry_or_fail. Плюс компании в building/queued без
    активной задачи — доставляем заново.
    """
    db = SessionLocal()
    try:
        running_ids = [j.id for j in db.query(Job).filter(Job.status == "running").all()]
        stuck_companies = [
            c.id for c in db.query(Company).filter(
                Company.build_status.in_(["building", "queued"])
            ).all()
        ]
    finally:
        db.close()

    for jid in running_ids:
        retry_or_fail(jid, error="осиротела после рестарта app")

    # Компании, зависшие в building/queued без активной задачи — переenqueue.
    for cid in stuck_companies:
        db = SessionLocal()
        try:
            active = has_active_build(db, cid)
        finally:
            db.close()
        if not active:
            enqueue_build(cid)

    if running_ids or stuck_companies:
        print(f"[RECOVER] jobs running→retry: {running_ids}; компаний проверено: {len(stuck_companies)}", flush=True)
