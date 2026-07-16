"""
app/cabinet.py — личный кабинет lk.uqqi.ru
Фаза А: регистрация, подтверждение email, вход, выход, восстановление пароля.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

import bcrypt as _bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.models import User, Company, Session as DbSession, SessionLocal, get_db
from app.mailer import send_email

router = APIRouter(prefix="/lk/api")

USER_COOKIE = "uqqi_user_session"
USER_TTL    = timedelta(days=30)
VERIFY_TTL  = timedelta(hours=24)


# ── Хелперы ───────────────────────────────────────────────────────────────────

def _hash_pw(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()


def _check_pw(pw: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    return xff.split(",")[0].strip() if xff else (request.client.host if request.client else "")


def _make_session(user_id: int, db: OrmSession) -> str:
    token = secrets.token_urlsafe(32)
    db.add(DbSession(
        token=token,
        identity=f"user:{user_id}",
        expires_at=datetime.utcnow() + USER_TTL,
    ))
    db.commit()
    return token


def current_user(
    uqqi_user_session: str | None = Cookie(default=None),
    db: OrmSession = Depends(get_db),
) -> User | None:
    if not uqqi_user_session:
        return None
    sess = db.query(DbSession).filter(DbSession.token == uqqi_user_session).first()
    if not sess or not sess.is_valid() or not sess.identity.startswith("user:"):
        return None
    uid = int(sess.identity.split(":", 1)[1])
    return db.query(User).filter(User.id == uid).first()


def require_user(user: User | None = Depends(current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Требуется вход")
    return user


# ── Email письма ──────────────────────────────────────────────────────────────

def _send_verify(email: str, token: str):
    link = f"https://lk.{settings.BASE_DOMAIN}/verify?token={token}"
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:2rem;color:#1a1a1a">
  <div style="text-align:center;margin-bottom:1.5rem">
    <img src="https://{settings.BASE_DOMAIN}/static/lk/assets/seal-192.png" width="64" alt="uqqi">
  </div>
  <h1 style="font-size:1.3rem;text-align:center">Подтвердите регистрацию</h1>
  <p style="font-size:.95rem;color:#555;line-height:1.6">
    Вы создали аккаунт на uqqi.ru. Нажмите кнопку, чтобы подтвердить email и войти в кабинет.
    Ссылка действует 24 часа.
  </p>
  <div style="text-align:center;margin:1.5rem 0">
    <a href="{link}" style="display:inline-block;background:#1a1a1a;color:#fff;text-decoration:none;font-weight:600;padding:.8rem 2rem;border-radius:12px">Подтвердить email</a>
  </div>
  <p style="font-size:.78rem;color:#999">Если вы не регистрировались — просто проигнорируйте это письмо.</p>
</div>"""
    send_email(email, "Подтверждение регистрации на uqqi.ru", html)


def _send_reset(email: str, token: str):
    link = f"https://lk.{settings.BASE_DOMAIN}/reset?token={token}"
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:2rem;color:#1a1a1a">
  <div style="text-align:center;margin-bottom:1.5rem">
    <img src="https://{settings.BASE_DOMAIN}/static/lk/assets/seal-192.png" width="64" alt="uqqi">
  </div>
  <h1 style="font-size:1.3rem;text-align:center">Сброс пароля</h1>
  <p style="font-size:.95rem;color:#555;line-height:1.6">
    Вы запросили сброс пароля. Нажмите кнопку, чтобы задать новый. Ссылка действует 1 час.
  </p>
  <div style="text-align:center;margin:1.5rem 0">
    <a href="{link}" style="display:inline-block;background:#1a1a1a;color:#fff;text-decoration:none;font-weight:600;padding:.8rem 2rem;border-radius:12px">Задать новый пароль</a>
  </div>
  <p style="font-size:.78rem;color:#999">Если вы не запрашивали сброс — проигнорируйте письмо, пароль не изменится.</p>
</div>"""
    send_email(email, "Сброс пароля на uqqi.ru", html)


# ── Схемы ───────────────────────────────────────────────────────────────────

class RegisterPayload(BaseModel):
    email: str
    password: str
    agree: bool = False
    claim_code: str = ""  # если регистрация через «Приобрести этот сайт»


class LoginPayload(BaseModel):
    email: str
    password: str


class ForgotPayload(BaseModel):
    email: str


class ResetPayload(BaseModel):
    token: str
    password: str


class ResendPayload(BaseModel):
    email: str


class PasswordPayload(BaseModel):
    current: str
    next: str


# ── Регистрация ───────────────────────────────────────────────────────────────

@router.post("/register")
async def register(payload: RegisterPayload, request: Request, db: OrmSession = Depends(get_db)):
    import re
    email = payload.email.strip().lower()
    if not re.match(r'^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$', email):
        raise HTTPException(status_code=422, detail="Некорректный email")
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Пароль минимум 6 символов")
    if not payload.agree:
        raise HTTPException(status_code=422, detail="Необходимо принять оферту и политику")

    claim_code = (payload.claim_code or "").strip()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.email_verified:
            raise HTTPException(status_code=409, detail="Этот email уже зарегистрирован")
        # неподтверждённый — пересоздаём токен и шлём заново
        existing.verify_token = secrets.token_urlsafe(32)[:64]
        existing.password_hash = _hash_pw(payload.password)
        existing.agreed_at = datetime.utcnow()
        existing.agreed_ip = _client_ip(request)
        if claim_code:
            existing.pending_claim_code = claim_code
        db.commit()
        _send_verify(email, existing.verify_token)
        return {"ok": True, "resent": True}

    user = User(
        email=email,
        password_hash=_hash_pw(payload.password),
        verify_token=secrets.token_urlsafe(32)[:64],
        agreed_at=datetime.utcnow(),
        agreed_ip=_client_ip(request),
        pending_claim_code=claim_code,
    )
    db.add(user)
    db.commit()
    _send_verify(email, user.verify_token)
    return {"ok": True}


@router.post("/resend-verify")
async def resend_verify(payload: ResendPayload, db: OrmSession = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user and not user.email_verified:
        if not user.verify_token:
            user.verify_token = secrets.token_urlsafe(32)[:64]
            db.commit()
        _send_verify(email, user.verify_token)
    return {"ok": True}  # не раскрываем существование email


@router.get("/verify")
async def verify_email(token: str, db: OrmSession = Depends(get_db)):
    """Вызывается со страницы /verify, активирует аккаунт и логинит."""
    user = db.query(User).filter(User.verify_token == token, User.verify_token != "").first()
    if not user:
        raise HTTPException(status_code=400, detail="Ссылка недействительна или устарела")
    user.email_verified = True
    user.verify_token = ""
    db.commit()
    # Если регистрация была через «Приобрести этот сайт» — привязываем claim-сайт
    claimed = None
    if user.pending_claim_code:
        claimed = _bind_claim_to_user(user.pending_claim_code, user, db)
        user.pending_claim_code = ""
        db.commit()
    token_s = _make_session(user.id, db)
    body = '{"ok":true}'
    if claimed:
        import json as _j
        body = _j.dumps({"ok": True, "claimed": claimed})
    resp = Response(content=body, media_type="application/json")
    resp.set_cookie(USER_COOKIE, token_s, max_age=int(USER_TTL.total_seconds()),
                    httponly=True, samesite="lax", secure=True)
    return resp


# ── Вход / выход ────────────────────────────────────────────────────────────

@router.post("/login")
async def login(payload: LoginPayload, db: OrmSession = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not _check_pw(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Подтвердите email — проверьте почту")

    token = _make_session(user.id, db)
    resp = Response(content='{"ok":true}', media_type="application/json")
    resp.set_cookie(USER_COOKIE, token, max_age=int(USER_TTL.total_seconds()),
                    httponly=True, samesite="lax", secure=True)
    return resp


@router.post("/logout")
async def logout(uqqi_user_session: str | None = Cookie(default=None),
                  db: OrmSession = Depends(get_db)):
    if uqqi_user_session:
        db.query(DbSession).filter(DbSession.token == uqqi_user_session).delete()
        db.commit()
    resp = Response(content='{"ok":true}', media_type="application/json")
    resp.delete_cookie(USER_COOKIE)
    return resp


@router.get("/me")
async def me(user: User = Depends(require_user)):
    return {"email": user.email, "id": user.id}


# ── Восстановление пароля ───────────────────────────────────────────────────

@router.post("/forgot")
async def forgot(payload: ForgotPayload, db: OrmSession = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.reset_token = secrets.token_urlsafe(32)[:64]
        user.reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        _send_reset(email, user.reset_token)
    return {"ok": True}  # не раскрываем существование email


@router.post("/reset")
async def reset(payload: ResetPayload, db: OrmSession = Depends(get_db)):
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Пароль минимум 6 символов")
    user = db.query(User).filter(User.reset_token == payload.token, User.reset_token != "").first()
    if not user or not user.reset_expires or datetime.utcnow() > user.reset_expires:
        raise HTTPException(status_code=400, detail="Ссылка недействительна или устарела")
    user.password_hash = _hash_pw(payload.password)
    user.reset_token = ""
    user.reset_expires = None
    # на всякий случай — разлогиниваем все старые сессии юзера
    db.query(DbSession).filter(DbSession.identity == f"user:{user.id}").delete()
    db.commit()
    return {"ok": True}


# ── Настройки аккаунта ──────────────────────────────────────────────────────

@router.post("/account/password")
async def change_password(payload: PasswordPayload,
                           user: User = Depends(require_user),
                           db: OrmSession = Depends(get_db)):
    if not _check_pw(payload.current, user.password_hash):
        raise HTTPException(status_code=403, detail="Текущий пароль неверен")
    if len(payload.next) < 6:
        raise HTTPException(status_code=422, detail="Новый пароль минимум 6 символов")
    user.password_hash = _hash_pw(payload.next)
    db.commit()
    return {"ok": True}


# ── CLAIM: привязка готового сайта из панели к аккаунту ──────────────────────

def _bind_claim_to_user(code: str, user: User, db: OrmSession):
    """
    Привязывает claim-сайт к пользователю, даёт триал 7 дней, гасит claim_code.
    Триал даётся всегда (даже если аккаунтный триал использован) — это подарок-крючок.
    Возвращает dict с инфо о сайте или None, если код невалиден/уже использован.
    """
    from datetime import datetime as _dt, timedelta as _td
    code = (code or "").strip()
    if not code:
        return None
    company = db.query(Company).filter(
        Company.claim_code == code,
        Company.user_id.is_(None),
    ).first()
    if not company:
        return None
    company.user_id       = user.id
    company.claim_code    = None
    company.demo_until    = None
    company.sub_status    = "trial"
    company.trial_ends_at = _dt.utcnow() + _td(days=7)
    company.is_active     = True
    db.commit()
    return {
        "slug":  company.slug,
        "title": company.title,
        "url":   f"https://{company.slug}.{settings.BASE_DOMAIN}/",
    }


@router.get("/claim/{code}/info")
async def claim_info(code: str, db: OrmSession = Depends(get_db)):
    """Инфо о claim-сайте (для страницы привязки в ЛК)."""
    company = db.query(Company).filter(
        Company.claim_code == code,
        Company.user_id.is_(None),
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Ссылка недействительна или сайт уже забрали.")
    return {
        "slug":  company.slug,
        "title": company.title,
        "url":   f"https://{company.slug}.{settings.BASE_DOMAIN}/",
    }


@router.post("/claim/{code}")
async def claim_site(code: str,
                      user: User = Depends(require_user),
                      db: OrmSession = Depends(get_db)):
    """Привязка claim-сайта к текущему (залогиненному, подтверждённому) пользователю."""
    result = _bind_claim_to_user(code, user, db)
    if not result:
        raise HTTPException(status_code=404, detail="Ссылка недействительна или сайт уже забрали.")
    return {"ok": True, **result}


@router.delete("/account")
async def delete_account(user: User = Depends(require_user),
                          db: OrmSession = Depends(get_db)):
    # Отвязываем/удаляем сайты юзера, чистим сессии, удаляем юзера
    db.query(Company).filter(Company.user_id == user.id).delete()
    db.query(DbSession).filter(DbSession.identity == f"user:{user.id}").delete()
    db.delete(user)
    db.commit()
    resp = Response(content='{"ok":true}', media_type="application/json")
    resp.delete_cookie(USER_COOKIE)
    return resp


# ── СAЙТЫ (Фаза Б) ────────────────────────────────────────────────────────────

# Разбор ссылок Яндекс.Карт (короткая /maps/-/CODE, org, mapframe) — app/yandex_links.py.
# Та же валидация продублирована на фронте (validYandex в static/lk/) — менять синхронно.
from app.yandex_links import extract_yandex_url


def _site_dict(c: Company) -> dict:
    """Сериализует компанию для фронта кабинета."""
    from datetime import datetime as _dt

    # Определяем статус для бейджа
    status = "active"
    trial_days = None
    until = None

    if c.build_status in ("queued", "building"):
        status = "building"
    elif c.build_status == "error":
        status = "error"
    elif c.sub_status == "trial":
        status = "trial"
        if c.trial_ends_at:
            delta = (c.trial_ends_at - _dt.utcnow()).days
            trial_days = max(0, delta + 1)
            if c.trial_ends_at < _dt.utcnow():
                status = "unpaid"  # триал истёк
    elif c.sub_status == "active":
        status = "active"
        if c.paid_until:
            until = c.paid_until.strftime("%d.%m.%Y")
            if c.paid_until < _dt.utcnow():
                status = "unpaid"
    elif c.sub_status == "unpaid":
        status = "unpaid"

    # Можно ли удалять: нельзя только активный готовый триал
    can_delete = not (
        c.sub_status == "trial" and c.trial_ends_at and c.trial_ends_at > _dt.utcnow()
        and c.build_status == "ready"
    )

    return {
        "id":        c.id,
        "name":      c.title or "Новый сайт",
        "slug":      c.slug,
        "city":      (c.address or "").split(",")[-1].strip() if c.address else "",
        "status":    status,
        "trialDays": trial_days,
        "until":     until,
        "created":   c.created_at.strftime("%d.%m.%Y") if c.created_at else "",
        "icon":      "store",
        "build_status": c.build_status,
        "canDelete": can_delete,
    }


class AddSitePayload(BaseModel):
    url: str


def _is_unpaid_paid_site(c) -> bool:
    """True если это платный сайт (не триал), который не оплачен."""
    from datetime import datetime as _dt
    if c.build_status in ("queued", "building", "error"):
        return False
    # Платный неоплаченный: sub_status unpaid, или active с истёкшим paid_until
    if c.sub_status == "unpaid":
        return True
    if c.sub_status == "active" and c.paid_until and c.paid_until < _dt.utcnow():
        return True
    return False


def _can_add_site(user, sites) -> tuple[bool, str]:
    """
    Можно ли создать новый сайт.
    Нельзя, пока есть строящийся или неоплаченный платный сайт.
    """
    # Пока что-то строится — нельзя
    if any(c.build_status in ("queued", "building") for c in sites):
        return False, "Дождитесь завершения создания текущего сайта."
    # Есть неоплаченный платный — нельзя
    if any(_is_unpaid_paid_site(c) for c in sites):
        return False, "Сначала оплатите предыдущий сайт."
    return True, ""


@router.get("/sites")
async def list_sites(user: User = Depends(require_user), db: OrmSession = Depends(get_db)):
    sites = db.query(Company).filter(Company.user_id == user.id).order_by(Company.id.desc()).all()
    can_add, reason = _can_add_site(user, sites)
    return {
        "sites": [_site_dict(c) for c in sites],
        "canAdd": can_add,
        "canAddReason": reason,
    }


@router.post("/sites/add")
async def add_site(payload: AddSitePayload,
                    user: User = Depends(require_user),
                    db: OrmSession = Depends(get_db)):
    url, url_err = extract_yandex_url(payload.url)
    if not url:
        raise HTTPException(status_code=422, detail=url_err)

    existing = db.query(Company).filter(Company.user_id == user.id).all()
    can_add, reason = _can_add_site(user, existing)
    if not can_add:
        raise HTTPException(status_code=409, detail=reason)

    # Триал положен только если ещё не использован. Иначе — сразу платный.
    is_trial = not user.trial_used

    import secrets as _s
    tmp_slug = f"building-{_s.token_hex(4)}"
    company = Company(
        slug=tmp_slug,
        title="Создаётся…",
        user_id=user.id,
        is_demo=False,
        yandex_url=url,
        build_status="queued",
        sub_status="trial" if is_trial else "unpaid",
        is_active=False,
        admin_password_hash="",
    )
    db.add(company)
    # Помечаем триал использованным сразу при создании триал-сайта
    if is_trial:
        user.trial_used = True
    db.commit()
    db.refresh(company)

    from app.build_queue import enqueue
    enqueue(company.id)

    return {"ok": True, "id": company.id, "trial": is_trial}


@router.get("/sites/{site_id}/status")
async def site_status(site_id: int,
                       user: User = Depends(require_user),
                       db: OrmSession = Depends(get_db)):
    c = db.query(Company).filter(Company.id == site_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404)
    return _site_dict(c)


@router.delete("/sites/{site_id}")
async def delete_site(site_id: int,
                       user: User = Depends(require_user),
                       db: OrmSession = Depends(get_db)):
    from datetime import datetime as _dt
    c = db.query(Company).filter(Company.id == site_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404)
    # Нельзя удалять активный триал (защита от абуза: удалить+создать заново)
    if c.sub_status == "trial" and c.trial_ends_at and c.trial_ends_at > _dt.utcnow() \
            and c.build_status == "ready":
        raise HTTPException(status_code=403,
            detail="Дождитесь окончания trial-периода.")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.post("/sites/{site_id}/cancel")
async def cancel_subscription(site_id: int,
                               user: User = Depends(require_user),
                               db: OrmSession = Depends(get_db)):
    """Отмена подписки: сайт работает до конца оплаченного периода, дальше не продлевается.
    Автосписания нет, поэтому отмена = больше не напоминаем о продлении."""
    c = db.query(Company).filter(Company.id == site_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404)
    # Отключаем напоминания; сайт остаётся active до paid_until
    c.notified_7d = True
    c.notified_3d = True
    db.commit()
    return {"ok": True, "active_until": c.paid_until.strftime("%d.%m.%Y") if c.paid_until else None}


# ── ПОДДЕРЖКА ─────────────────────────────────────────────────────────────────

class TicketPayload(BaseModel):
    subject: str
    message: str


@router.get("/tickets")
async def list_tickets(user: User = Depends(require_user), db: OrmSession = Depends(get_db)):
    from app.models import SupportMessage
    msgs = db.query(SupportMessage).filter(
        SupportMessage.reply_email == user.email
    ).order_by(SupportMessage.created_at.desc()).limit(100).all()
    return {
        "tickets": [
            {
                "subj":   m.company_title or "Обращение",
                "body":   m.message,
                "status": "answered" if m.is_read else "open",
                "date":   m.created_at.strftime("%d.%m.%Y") if m.created_at else "",
            }
            for m in msgs
        ]
    }


@router.post("/tickets")
async def create_ticket(payload: TicketPayload,
                         user: User = Depends(require_user),
                         db: OrmSession = Depends(get_db)):
    from app.models import SupportMessage
    subj = payload.subject.strip()[:255]
    msg = payload.message.strip()[:5000]
    if len(msg) < 5:
        raise HTTPException(status_code=422, detail="Опишите вопрос подробнее")
    sm = SupportMessage(
        company_slug="",
        company_title=subj,
        reply_email=user.email,
        message=msg,
    )
    db.add(sm)
    db.commit()
    return {"ok": True}


# ── ПЛАТЕЖИ (ЮKassa) ──────────────────────────────────────────────────────────

# Тарифы подписки. amount — строка (сравнивается с ЮKassa через Decimal),
# days — на сколько продлевать paid_until. months — для подачи «X ₽/мес».
# ВАЖНО: дублируется на фронте (billing.jsx/app.bundle.jsx) — менять синхронно.
PLANS = {
    "month":   {"amount": "1990.00",  "days": 30,  "months": 1,  "label": "Месяц"},
    "quarter": {"amount": "4990.00",  "days": 90,  "months": 3,  "label": "3 месяца"},
    "year":    {"amount": "15990.00", "days": 365, "months": 12, "label": "Год"},
}
DEFAULT_PLAN = "quarter"


class PaymentCreatePayload(BaseModel):
    site_id: int
    plan: str = DEFAULT_PLAN


@router.post("/payment/create")
async def payment_create(payload: PaymentCreatePayload,
                          user: User = Depends(require_user),
                          db: OrmSession = Depends(get_db)):
    """Создаёт платёж ЮKassa за подписку сайта. Возвращает confirmation_url."""
    from app.models import Payment
    from app.yukassa import create_payment

    company = db.query(Company).filter(
        Company.id == payload.site_id, Company.user_id == user.id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Сайт не найден")
    if company.build_status not in ("ready",):
        raise HTTPException(status_code=400, detail="Сайт ещё не готов")

    plan = PLANS.get(payload.plan)
    if not plan:
        raise HTTPException(status_code=422, detail="Неизвестный тариф")
    amount = plan["amount"]
    days = plan["days"]
    return_url = f"https://lk.{settings.BASE_DOMAIN}/?paid={company.id}"
    description = f"Подписка uqqi.ru ({plan['label']}) — {company.slug}.{settings.BASE_DOMAIN}"

    try:
        result = create_payment(
            amount=amount,
            description=description,
            return_url=return_url,
            metadata={"company_id": company.id, "user_id": user.id,
                      "slug": company.slug, "plan": payload.plan},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not result.get("id") or not result.get("confirmation_url"):
        raise HTTPException(status_code=502, detail="ЮKassa не вернула ссылку оплаты")

    # Сохраняем платёж в статусе pending
    pay = Payment(
        payment_id=result["id"],
        user_id=user.id,
        company_id=company.id,
        company_slug=company.slug,
        amount=amount,
        days=days,
        status="pending",
    )
    db.add(pay)
    db.commit()

    return {"ok": True, "confirmation_url": result["confirmation_url"], "payment_id": result["id"]}


@router.get("/payment/{payment_id}/status")
async def payment_status(payment_id: str,
                          user: User = Depends(require_user),
                          db: OrmSession = Depends(get_db)):
    """Проверка статуса платежа (для экрана 'оплата обрабатывается')."""
    from app.models import Payment
    pay = db.query(Payment).filter(
        Payment.payment_id == payment_id, Payment.user_id == user.id
    ).first()
    if not pay:
        raise HTTPException(status_code=404)
    return {"status": pay.status, "processed": pay.processed}


@router.get("/payments")
async def list_payments(user: User = Depends(require_user), db: OrmSession = Depends(get_db)):
    """История платежей пользователя."""
    from app.models import Payment
    rows = db.query(Payment).filter(
        Payment.user_id == user.id
    ).order_by(Payment.created_at.desc()).limit(100).all()
    return {
        "payments": [
            {
                "date":   (p.paid_at or p.created_at).strftime("%d.%m.%Y") if (p.paid_at or p.created_at) else "",
                "site":   f"{p.company_slug}.{settings.BASE_DOMAIN}",
                "amount": f"{p.amount} ₽",
                "ok":     p.status == "succeeded",
            }
            for p in rows
        ]
    }


def _apply_successful_payment(payment_id: str, db: OrmSession) -> bool:
    """
    Применяет успешный платёж: продлевает подписку сайта.
    Идемпотентно — повторный вызов с тем же payment_id ничего не делает.
    Возвращает True если применён сейчас.
    """
    from app.models import Payment
    from datetime import datetime as _dt, timedelta as _td

    pay = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not pay:
        return False
    if pay.processed:
        return False  # уже обработан — защита от дублей webhook

    company = db.query(Company).filter(Company.id == pay.company_id).first()
    if not company:
        pay.status = "succeeded"
        pay.processed = True
        db.commit()
        return False

    # Продлеваем: от max(сейчас, текущий paid_until) + срок тарифа
    now = _dt.utcnow()
    base = company.paid_until if (company.paid_until and company.paid_until > now) else now
    company.paid_until    = base + _td(days=(pay.days or settings.SUBSCRIPTION_DAYS))
    company.sub_status    = "active"
    company.is_active     = True
    company.trial_ends_at = None  # триал больше не релевантен

    pay.status    = "succeeded"
    pay.processed = True
    pay.paid_at   = now
    db.commit()
    return True


def _verify_and_apply_payment(payment_id: str, db: OrmSession) -> tuple[bool, str]:
    """
    Проверяет платёж напрямую у ЮKassa и применяет ТОЛЬКО при:
      • payment_id есть в нашей БД,
      • ЮKassa вернула status == succeeded,
      • оплаченная сумма совпадает с ожидаемой (Payment.amount).
    Fail-CLOSED: при любой невозможности проверить (API недоступен, нет ключей,
    сумма не сошлась) — НЕ применяет, оставляет pending (подхватит реконсиляция).
    Возвращает (применён_ли_сейчас, заметка_для_лога).
    """
    from app.models import Payment
    from decimal import Decimal, InvalidOperation

    pay = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not pay:
        return False, "payment_id нет в нашей БД — игнор"
    if pay.processed:
        return False, "уже обработан (идемпотентность)"

    if not settings.YUKASSA_SHOP_ID or not settings.YUKASSA_SECRET_KEY:
        return False, "ЮKassa не настроена — проверка невозможна, оставляю pending"

    # Спрашиваем истину у ЮKassa (телу webhook не доверяем)
    from app.yukassa import get_payment
    try:
        remote = get_payment(payment_id)
    except Exception as e:
        return False, f"проверка статуса не удалась ({e}) — оставляю pending"

    status = remote.get("status", "")
    if status == "canceled":
        pay.status = "canceled"
        pay.processed = True
        db.commit()
        return False, "ЮKassa: canceled"
    if status != "succeeded":
        return False, f"ЮKassa статус={status!r} — не применяю"

    # Сверка суммы: реально оплачено vs ожидали
    remote_amount = (remote.get("amount") or {}).get("value", "")
    try:
        if Decimal(str(remote_amount)) != Decimal(str(pay.amount)):
            from app.notifier import send_telegram
            send_telegram(
                f"🔴 uqqi: платёж {payment_id} succeeded, но сумма НЕ совпала — "
                f"оплачено {remote_amount}, ожидали {pay.amount}. Не применяю.",
                key=f"amount_{payment_id}", throttle_sec=6 * 3600,
            )
            return False, f"сумма не совпала (оплачено {remote_amount}, ждали {pay.amount})"
    except (InvalidOperation, TypeError):
        return False, f"некорректная сумма от ЮKassa: {remote_amount!r}"

    applied = _apply_successful_payment(payment_id, db)
    return applied, "применён" if applied else "не применён (компания не найдена?)"


# ── НАСТРОЙКИ ─────────────────────────────────────────────────────────────────
