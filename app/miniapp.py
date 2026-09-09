"""
app/miniapp.py — мини-приложение владельца в Telegram (Pro, 2026-09).

Календарь записей прямо внутри Telegram: посмотреть неделю, подтвердить,
перенести, отменить, добавить запись руками. Открывается кнопкой меню бота,
живёт на хосте кабинета: `https://lk.<домен>/tg/app`.

  GET    /tg/app                    — страница мини-приложения
  POST   /tg/api/bootstrap          — сайты владельца + настройки записи
  POST   /tg/api/bookings           — записи на диапазон дат
  POST   /tg/api/slots              — свободные слоты на дату (для переноса)
  POST   /tg/api/booking/create     — владелец заводит запись сам
  POST   /tg/api/booking/update     — перенос, смена мастера, статуса, данных
  POST   /tg/api/booking/delete     — удаление записи

Почему всё POST, включая чтение: авторизация идёт строкой initData от
Telegram, а её не стоит светить в адресной строке и в access-логе.

Авторизация. Telegram отдаёт странице подписанный initData; подпись
проверяется ключом бота (`_check_init_data`), из неё берётся id пользователя
и сверяется с `users.tg_chat_id`. Ни логина, ни пароля, ни куки — сессия
кабинета сюда не доезжает, это другой контекст.

Гейт: мини-приложение — Pro-функция. В списке только сайты с активным Pro;
любая операция ещё раз проверяет Pro у конкретного сайта.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.booking import free_slots, settings_of, slots_active
from app.config import settings
from app.models import Booking, Company, SessionLocal, User

router = APIRouter(prefix="/tg")
templates = Jinja2Templates(directory="templates")

# Столько живёт подпись initData. Telegram переоткрывает приложение с новой,
# поэтому сутки — запас на «открыл и оставил висеть».
INIT_DATA_TTL = 24 * 3600
MAX_RANGE_DAYS = 62


# ── Авторизация через Telegram ───────────────────────────────────────────────

def _check_init_data(init_data: str) -> dict | None:
    """
    Проверяет подпись initData и возвращает данные пользователя Telegram.

    Схема из документации Bot API: ключ — HMAC('WebAppData', токен бота),
    подписывается строка «ключ=значение», отсортированная по ключу, без поля
    hash. Неверная подпись, просроченная метка времени или отсутствующий
    токен — None, и вызывающий отдаёт 401.
    """
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not token or not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:                                        # noqa: BLE001
        return None

    got = pairs.pop("hash", "")
    if not got:
        return None
    check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    want = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, got):
        return None

    try:
        if abs(int(time_now() - int(pairs.get("auth_date", "0")))) > INIT_DATA_TTL:
            return None
    except (TypeError, ValueError):
        return None

    try:
        return json.loads(pairs.get("user") or "{}")
    except json.JSONDecodeError:
        return None


def time_now() -> int:
    """Вынесено отдельной функцией, чтобы подменять в тестах."""
    import time as _t
    return int(_t.time())


def _owner(db, init_data: str) -> User:
    """Владелец по подписанным данным Telegram или 401."""
    tg = _check_init_data(init_data)
    if not tg or not tg.get("id"):
        raise HTTPException(status_code=401, detail="Откройте приложение из чата с ботом")
    user = db.query(User).filter(User.tg_chat_id == str(tg["id"])).first()
    if not user:
        raise HTTPException(status_code=403,
                            detail="Telegram не привязан. Кабинет → Настройки → Подключить Telegram")
    return user


def _pro_sites(db, user: User) -> list[Company]:
    """Сайты владельца с активным Pro — только они попадают в приложение."""
    now = datetime.utcnow()
    rows = db.query(Company).filter(
        Company.user_id == user.id,
        Company.is_active.is_(True),
        Company.pro_until.isnot(None),
        Company.pro_until > now,
    ).order_by(Company.id).all()
    return rows


def _site(db, user: User, site_id: int) -> Company:
    c = db.query(Company).filter(Company.id == site_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Сайт не найден")
    if not (c.pro_until and c.pro_until > datetime.utcnow()):
        raise HTTPException(status_code=403, detail="Записи доступны на тарифе Pro")
    return c


# ── Представление записи ─────────────────────────────────────────────────────

def _dto(b: Booking, tz_hours: int) -> dict:
    local = b.slot_start + timedelta(hours=tz_hours) if b.slot_start else None
    return {
        "id":        b.id,
        "date":      local.strftime("%Y-%m-%d") if local else "",
        "time":      local.strftime("%H:%M") if local else "",
        "start":     local.strftime("%Y-%m-%dT%H:%M") if local else "",
        "duration":  b.duration_min or 60,
        "name":      b.name or "",
        "phone":     b.phone or "",
        "email":     b.client_email or "",
        "service":   b.service or "",
        "master":    b.master or "",
        "comment":   b.comment or "",
        "status":    b.status or "new",
        "byOwner":   (b.created_by or "client") == "owner",
    }


# ── Схемы запросов ───────────────────────────────────────────────────────────

class Auth(BaseModel):
    initData: str = ""


class RangeReq(Auth):
    site_id: int = 0
    date_from: str = ""
    date_to: str = ""


class SlotsReq(Auth):
    site_id: int = 0
    date: str = ""
    exclude_id: int = 0


class CreateReq(Auth):
    site_id: int = 0
    start: str = ""          # '2026-09-10T14:00', местное время заведения
    name: str = ""
    phone: str = ""
    email: str = ""
    service: str = ""
    master: str = ""
    comment: str = ""


class UpdateReq(Auth):
    id: int = 0
    start: str = ""
    name: str = ""
    phone: str = ""
    email: str = ""
    service: str = ""
    master: str = ""
    comment: str = ""
    status: str = ""
    notify: bool = True      # сообщать ли клиенту (владелец может отключить)


class DeleteReq(Auth):
    id: int = 0
    notify: bool = True


# ── Страница ─────────────────────────────────────────────────────────────────

@router.get("/app", response_class=HTMLResponse)
async def miniapp_page(request: Request):
    """
    Страница приложения. Никакой авторизации здесь нет: initData доступен
    только скрипту на странице, он и ходит в API. Показываем оболочку.

    Заголовок X-Uqqi-Embeddable=tg просит middleware отдать frame-ancestors
    для Telegram: веб-версия Telegram открывает мини-приложения в iframe, и
    X-Frame-Options: SAMEORIGIN её бы сломал.
    """
    # Именованные аргументы: позиционный вызов у свежей Starlette значит
    # уже (request, name), и старый порядок падает.
    resp = templates.TemplateResponse(request=request, name="tg_app.html")
    resp.headers["X-Uqqi-Embeddable"] = "tg"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ── API ──────────────────────────────────────────────────────────────────────

@router.post("/api/bootstrap")
async def api_bootstrap(req: Auth):
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        out = []
        for c in _pro_sites(db, user):
            cfg = settings_of(c)
            out.append({
                "id": c.id, "title": c.title or c.slug, "slug": c.slug,
                "tz": cfg["tz"], "duration": cfg["duration"],
                "multi": cfg["multi"],
                "masters": [m["name"] for m in cfg["masters"]],
                "services": cfg["services"],
                "slotsOn": slots_active(c),
            })
        return {"ok": True, "sites": out}
    finally:
        db.close()


@router.post("/api/bookings")
async def api_bookings(req: RangeReq):
    """Записи сайта за диапазон дат (даты местные для заведения)."""
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        c = _site(db, user, req.site_id)
        cfg = settings_of(c)
        tz = timedelta(hours=cfg["tz"])

        try:
            d_from = datetime.strptime(req.date_from, "%Y-%m-%d")
            d_to = datetime.strptime(req.date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=422, detail="Неверные даты")
        if d_to < d_from:
            d_from, d_to = d_to, d_from
        if (d_to - d_from).days > MAX_RANGE_DAYS:
            d_to = d_from + timedelta(days=MAX_RANGE_DAYS)

        rows = db.query(Booking).filter(
            Booking.company_id == c.id,
            Booking.slot_start >= d_from - tz,
            Booking.slot_start < d_to + timedelta(days=1) - tz,
        ).order_by(Booking.slot_start).all()
        return {"ok": True, "bookings": [_dto(b, cfg["tz"]) for b in rows]}
    finally:
        db.close()


@router.post("/api/slots")
async def api_slots(req: SlotsReq):
    """
    Свободные слоты на дату — для добавления и переноса.

    owner=True: правило «не раньше чем через N часов» здесь не применяется,
    владелец записывает и на ближайший час. exclude_id не считает занятой
    ту запись, которую он же сейчас переносит.
    """
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        c = _site(db, user, req.site_id)
        slots = free_slots(db, c, req.date, owner=True, exclude_id=req.exclude_id or None)
        return {"ok": True, "date": req.date, "slots": slots}
    finally:
        db.close()


def _apply_slot(db, company, start: str, exclude_id: int | None, master: str) -> tuple[datetime, str]:
    """
    Проверяет выбранное время по расписанию и возвращает (UTC-начало, мастер).

    Владелец тоже ходит через расчёт слотов, а не пишет произвольное время:
    иначе появились бы записи вне графика и наложения друг на друга.
    """
    cfg = settings_of(company)
    try:
        start_local = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Выберите время")

    day = start_local.strftime("%Y-%m-%d")
    slot = next((s for s in free_slots(db, company, day, owner=True, exclude_id=exclude_id)
                 if s["start"] == start), None)
    if not slot:
        raise HTTPException(status_code=409, detail="Это время занято или вне графика")

    chosen = (master or "").strip()
    if cfg["multi"]:
        if chosen and chosen not in slot["masters"]:
            raise HTTPException(status_code=409, detail="Этот мастер занят в это время")
        chosen = chosen or (slot["masters"][0] if slot["masters"] else "")
        if not chosen:
            raise HTTPException(status_code=409, detail="Свободных мастеров нет")
    else:
        chosen = ""
    return start_local - timedelta(hours=cfg["tz"]), chosen


@router.post("/api/booking/create")
async def api_create(req: CreateReq):
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        c = _site(db, user, req.site_id)
        cfg = settings_of(c)

        name = (req.name or "").strip()[:120]
        if len(name) < 2:
            raise HTTPException(status_code=422, detail="Укажите имя")

        start_utc, master = _apply_slot(db, c, req.start, None, req.master)
        b = Booking(
            company_id=c.id, slot_start=start_utc, duration_min=cfg["duration"],
            service=(req.service or "").strip()[:200], name=name,
            phone=(req.phone or "").strip()[:40],
            comment=(req.comment or "").strip()[:500],
            status="confirmed", source="owner", visitor_hash="",
            master=master, created_by="owner",
            client_email=_email(req.email),
        )
        db.add(b)
        db.commit()
        db.refresh(b)
        return {"ok": True, "booking": _dto(b, cfg["tz"])}
    finally:
        db.close()


@router.post("/api/booking/update")
async def api_update(req: UpdateReq):
    """
    Правка записи владельцем. Запись, созданную клиентом, не меняем молча:
    если у него оставлена почта, ему уходит письмо о переносе или отмене.
    """
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        b = db.query(Booking).filter(Booking.id == req.id).first()
        if not b:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        c = _site(db, user, b.company_id)
        cfg = settings_of(c)

        was_local = b.slot_start + timedelta(hours=cfg["tz"]) if b.slot_start else None
        was_status = b.status

        if req.start:
            b.slot_start, b.master = _apply_slot(db, c, req.start, b.id, req.master or b.master)
        elif req.master and cfg["multi"]:
            b.slot_start, b.master = _apply_slot(
                db, c, was_local.strftime("%Y-%m-%dT%H:%M"), b.id, req.master)

        if req.name:
            b.name = req.name.strip()[:120]
        if req.phone:
            b.phone = req.phone.strip()[:40]
        if req.email:
            b.client_email = _email(req.email)
        if req.service is not None:
            b.service = (req.service or "").strip()[:200]
        if req.comment is not None:
            b.comment = (req.comment or "").strip()[:500]
        if req.status in ("new", "confirmed", "canceled"):
            b.status = req.status
        db.commit()
        db.refresh(b)

        now_local = b.slot_start + timedelta(hours=cfg["tz"])
        if req.notify and (b.created_by or "client") == "client":
            if b.status == "canceled" and was_status != "canceled":
                _tell_client(c, b, "canceled", now_local, was_local)
            elif was_local and now_local != was_local:
                _tell_client(c, b, "moved", now_local, was_local)
        return {"ok": True, "booking": _dto(b, cfg["tz"])}
    finally:
        db.close()


@router.post("/api/booking/delete")
async def api_delete(req: DeleteReq):
    db = SessionLocal()
    try:
        user = _owner(db, req.initData)
        b = db.query(Booking).filter(Booking.id == req.id).first()
        if not b:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        c = _site(db, user, b.company_id)
        cfg = settings_of(c)
        local = b.slot_start + timedelta(hours=cfg["tz"]) if b.slot_start else None

        # Уже отменённую не «отменяем» второй раз: письмо об этом клиент
        # получил, когда владелец нажал «Отменить».
        if (req.notify and (b.created_by or "client") == "client"
                and local and b.status != "canceled"):
            _tell_client(c, b, "canceled", local, local)
        db.delete(b)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


# ── Уведомление клиента ──────────────────────────────────────────────────────

def _email(value: str) -> str:
    from app.booking import _clean_email
    return _clean_email(value)


def _tell_client(company, booking, what: str, now_local: datetime,
                 was_local: datetime | None) -> None:
    """
    Сообщает клиенту, что его запись перенесли или отменили.

    Единственный канал до клиента — почта, и она необязательная: телефон для
    писем не годится, SMS-провайдера у нас нет. Нет почты — молча выходим,
    владелец видит это в карточке записи. Ошибка отправки не должна ронять
    саму правку, она уже сохранена.
    """
    if not booking.client_email:
        return
    try:
        from app.mailer import booking_canceled_html, booking_changed_html, send_email
        title = company.title or company.slug
        when = f"{now_local:%d.%m.%Y} в {now_local:%H:%M}"
        if what == "canceled":
            send_email(booking.client_email, f"Запись отменена — {title}",
                       booking_canceled_html(title, when))
        else:
            was = f"{was_local:%d.%m.%Y} в {was_local:%H:%M}" if was_local else ""
            send_email(booking.client_email, f"Запись перенесена — {title}",
                       booking_changed_html(title, when, was, booking.master or ""))
    except Exception as e:                                   # noqa: BLE001
        print(f"[MINIAPP] письмо клиенту не ушло: {e}", flush=True)
