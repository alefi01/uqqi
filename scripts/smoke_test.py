#!/usr/bin/env python3
"""
scripts/smoke_test.py — smoke-тесты ключевых потоков (логика, без Chromium/HTTP).

Покрывает деньги/модель: freemium-показ, применение оплаты + идемпотентность,
привязка claim, TTL verify_token, конечный автомат очереди сборки.

ИЗОЛИРОВАН: создаёт временную БД и работает с ней — прод uqqi.db НЕ трогает.
Запуск:  venv/bin/python scripts/smoke_test.py   (код возврата 1 при падении)
"""
import os
import sys
import asyncio
import tempfile
from datetime import datetime, timedelta
from types import SimpleNamespace

# Временная БД ДО импорта app.* (движок читает DATABASE_URL при импорте).
_TMP = tempfile.mkdtemp(prefix="uqqi_smoke_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/smoke.db"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException  # noqa: E402
from app.models import create_tables, SessionLocal, Company, User, Payment, Job  # noqa: E402
from app import main as M  # noqa: E402
from app import jobq  # noqa: E402
from app.cabinet import (  # noqa: E402
    _apply_successful_payment, _bind_claim_to_user, verify_email, VERIFY_TTL,
)

create_tables()

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓ {name}")
    else:
        _FAIL += 1
        print(f"  ✗ {name}")


def ns(**kw):
    d = dict(is_claim=False, paid_once=False, is_demo=False, pro_until=None)
    d.update(kw)
    return SimpleNamespace(**d)


# ── 1. Freemium: показ/индексация ────────────────────────────────────────────
print("1) freemium: pro_active / is_legit / _indexable")
fut = datetime.utcnow() + timedelta(days=3)
past = datetime.utcnow() - timedelta(days=1)
check("self-service — свой и индексируется", M.is_legit(ns()) and M._indexable(ns()))
check("claim не оплачен — не свой, не индексируется",
      not M.is_legit(ns(is_claim=True)) and not M._indexable(ns(is_claim=True)))
check("claim оплачен — свой и индексируется",
      M.is_legit(ns(is_claim=True, paid_once=True)) and M._indexable(ns(is_claim=True, paid_once=True)))
check("demo — легитим, но НЕ индексируется",
      M.is_legit(ns(is_demo=True)) and not M._indexable(ns(is_demo=True)))
check("pro_active по будущему pro_until",
      M.pro_active(ns(pro_until=fut)) and not M.pro_active(ns(pro_until=past)) and not M.pro_active(ns()))


# ── 2. Оплата: pro_until + paid_once + идемпотентность ────────────────────────
print("2) оплата: продление Pro + легитимизация + идемпотентность")
db = SessionLocal()
c = Company(slug="pay", title="Pay", is_claim=True, paid_once=False, build_status="ready", admin_password_hash="")
db.add(c); db.commit(); cid = c.id
db.add(Payment(payment_id="pay-1", user_id=1, company_id=cid, company_slug="pay",
               amount="990.00", days=30, status="pending"))
db.commit()
ok1 = _apply_successful_payment("pay-1", db)
db.refresh(c)
check("платёж применён", ok1 is True)
check("paid_once=True (легитимизирует claim)", c.paid_once is True)
check("pro_until в будущем", bool(c.pro_until and c.pro_until > datetime.utcnow()))
check("paid_until синхронизирован с pro_until", c.paid_until == c.pro_until)
check("sub_status=active", c.sub_status == "active")
pu1 = c.pro_until
ok2 = _apply_successful_payment("pay-1", db)  # повтор того же платежа
db.refresh(c)
check("идемпотентность: повтор не продлевает", ok2 is False and c.pro_until == pu1)
db.close()


# ── 3. Claim: привязка оставляет обезличенным до оплаты ───────────────────────
print("3) claim: забрал → в ЛК, но обезличен; Pro-триал выдан")
db = SessionLocal()
u = User(email="claim@x.ru", password_hash="x")
db.add(u); db.commit(); uid = u.id
c = Company(slug="cl", title="Cl", is_claim=True, paid_once=False, claim_code="CODE1",
            build_status="ready", admin_password_hash="")
db.add(c); db.commit()
res = _bind_claim_to_user("CODE1", u, db)
db.refresh(c)
check("привязан к юзеру (в ЛК)", c.user_id == uid and res is not None)
check("claim_code погашен", not c.claim_code)
check("остаётся обезличенным (is_claim, не оплачен)", c.is_claim is True and not c.paid_once)
check("Pro-триал выдан (~7 дней)", bool(c.pro_until and c.pro_until > datetime.utcnow()))
db.close()


# ── 4. verify_token: TTL 24 часа ──────────────────────────────────────────────
print("4) verify_token: TTL 24ч (защита от отложенного подтверждения)")
db = SessionLocal()
db.add(User(email="v@x.ru", password_hash="x", verify_token="TOK_FRESH",
            verify_sent_at=datetime.utcnow()))
db.add(User(email="v2@x.ru", password_hash="x", verify_token="TOK_OLD",
            verify_sent_at=datetime.utcnow() - timedelta(hours=25)))
db.commit(); db.close()

db = SessionLocal()
expired_rejected = False
try:
    asyncio.run(verify_email("TOK_OLD", db))
except HTTPException as e:
    expired_rejected = (e.status_code == 400)
db.close()
check("просроченная (>24ч) ссылка отклонена", expired_rejected)

db = SessionLocal()
verified = False
try:
    asyncio.run(verify_email("TOK_FRESH", db))
    db2 = SessionLocal()
    verified = bool(db2.query(User).filter(User.email == "v@x.ru").first().email_verified)
    db2.close()
except Exception as e:  # noqa: BLE001
    print(f"   (fresh verify исключение: {e})")
db.close()
check("свежая (<24ч) ссылка активирует аккаунт", verified)


# ── 5. Очередь сборки (jobs) ──────────────────────────────────────────────────
print("5) очередь jobs: enqueue / dedup / claim / retry")
db = SessionLocal()
c = Company(slug="jb", title="Jb", build_status="queued", admin_password_hash="")
db.add(c); db.commit(); jc = c.id
db.close()
jid = jobq.enqueue_build(jc)
check("enqueue создал задачу", bool(jid))
check("dedup: повторный enqueue не дублирует", jobq.enqueue_build(jc) is None)
claimed = jobq.claim_pending(5)
check("claim_pending → running", any(x[0] == jid for x in claimed))
jobq.retry_or_fail(jid, "boom")
db = SessionLocal()
st = db.query(Job).filter(Job.id == jid).first().status
db.close()
check("retry (attempts<max) → pending", st == "pending")


# ── Итог ──────────────────────────────────────────────────────────────────────
print(f"\nИтого: {_PASS} ok, {_FAIL} fail")
# Уборка временной БД
try:
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)
except Exception:
    pass
sys.exit(1 if _FAIL else 0)
