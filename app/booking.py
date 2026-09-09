"""
app/booking.py — онлайн-запись на витринах (Pro-фича).

Публичное API витрины:
  GET  /api/booking/{slug}/days    — ближайшие дни со свободными слотами
  GET  /api/booking/{slug}/slots   — свободные слоты на дату (?date=YYYY-MM-DD)
  POST /api/booking/{slug}/create  — посетитель записывается

Гейт жёсткий: запись работает ТОЛЬКО если у сайта активен Pro И владелец сам
настроил график (booking_mode='slots' + хотя бы один рабочий день). Пока график
не заполнен, режим слотов включить нельзя — кнопка ведёт на внешний сервис или
её нет вовсе. Это осознанно: пустой календарь хуже отсутствия кнопки.

Время. В базе всё в UTC (naive), как в остальном проекте. У бизнеса свой пояс
(`booking.tz`, смещение от UTC в часах) — расписание владелец задаёт в местном
времени, наружу отдаём местное, внутрь пишем UTC.
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.models import SessionLocal, Company, User, Booking

router = APIRouter(prefix="/api/booking")

# Значения по умолчанию: их же показывает редактор, когда владелец открывает
# настройку впервые.
DEFAULTS = {
    "tz": 3,               # UTC+3, Москва
    "duration": 60,        # длительность слота, минут
    "step": 0,             # шаг сетки; 0 = равен длительности
    "lead_hours": 2,       # ближайшая запись не раньше чем через N часов
    "days_ahead": 14,      # горизонт записи
    "services": [],        # список услуг (необязательно)
    "week": {},            # {"1": [["10:00","20:00"]], ...}, 1=понедельник
    "multi": False,        # режим «Мульти»: несколько мастеров со своими графиками
    "masters": [],         # [{"name": "Иван", "week": {...}}] — только при multi
}

MAX_DAYS_AHEAD = 60
_rate: dict[str, list[float]] = {}


# ── Настройки и гейты ────────────────────────────────────────────────────────

def _num(value, default: int, lo: int, hi: int) -> int:
    """Число из настроек с зажимом в диапазон. Мусор → значение по умолчанию.

    Настройки приходят из редактора числами, но JSON правится и руками, а
    settings_of вызывается на ПУБЛИЧНОЙ витрине — исключение здесь уронило бы
    страницу целиком.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def settings_of(company) -> dict:
    """Настройки записи с подставленными значениями по умолчанию."""
    cfg = dict(DEFAULTS)
    raw = company.booking if isinstance(company.booking, dict) else {}
    cfg.update({k: v for k, v in raw.items() if v is not None})
    cfg["tz"] = _num(cfg.get("tz"), 3, -12, 14)
    cfg["duration"] = _num(cfg.get("duration"), 60, 5, 600)
    step = _num(cfg.get("step"), 0, 0, 600)
    cfg["step"] = cfg["duration"] if step <= 0 else max(5, step)
    cfg["lead_hours"] = _num(cfg.get("lead_hours"), 0, 0, 720)
    cfg["days_ahead"] = _num(cfg.get("days_ahead"), 14, 1, MAX_DAYS_AHEAD)
    week = cfg.get("week")
    cfg["week"] = week if isinstance(week, dict) else {}
    services = cfg.get("services")
    cfg["services"] = [s for s in services if s] if isinstance(services, list) else []
    cfg["masters"] = _masters(cfg.get("masters"), cfg["week"])
    # «Мульти» без единого мастера с графиком — это обычный режим одного мастера.
    cfg["multi"] = bool(cfg.get("multi")) and bool(cfg["masters"])
    return cfg


def _masters(raw, fallback_week: dict) -> list[dict]:
    """
    Мастера режима «Мульти», приведённые к виду [{'name':…, 'week':{…}}].

    Как и всё в settings_of, вызывается на ПУБЛИЧНОЙ витрине: любой мусор в
    JSON превращается в пустой список, а не в исключение. Мастер без своего
    графика работает по общему — так владельцу не нужно заполнять одно и то же
    семь раз, если мастера работают в одну смену.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for item in raw[:20]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()[:120]
        if not name or name.lower() in seen:
            continue
        week = item.get("week")
        week = week if isinstance(week, dict) else {}
        out.append({"name": name, "week": week or dict(fallback_week)})
        seen.add(name.lower())
    return out


def has_schedule(company) -> bool:
    """
    Есть ли хотя бы один РАБОЧИЙ интервал. Без него слоты включать нельзя.

    Проверяем ровно тем же разбором, что и расчёт слотов: «10:00–13:00» — да,
    а «25:00–x» или «19:00–10:00» — нет. Иначе режим включился бы на битом
    графике и витрина показала бы пустой календарь.
    """
    cfg = settings_of(company)
    weeks = [cfg["week"]] + [m["week"] for m in cfg["masters"]]
    for week in weeks:
        for ranges in week.values():
            if not isinstance(ranges, list):
                continue
            for r in ranges:
                if not (isinstance(r, (list, tuple)) and len(r) == 2):
                    continue
                a, b = _parse_hhmm(r[0]), _parse_hhmm(r[1])
                if a is not None and b is not None and b > a:
                    return True
    return False


def _pro_active(company) -> bool:
    return bool(company.pro_until and company.pro_until > datetime.utcnow())


def slots_active(company) -> bool:
    """Работает ли наша запись со слотами на этой витрине."""
    return bool(
        company
        and company.is_active
        and company.booking_mode == "slots"
        and _pro_active(company)
        and has_schedule(company)
    )


def button_mode(company) -> str:
    """
    Что делает кнопка «Записаться» на витрине: 'slots' | 'external' | 'off'.
    Бесплатные оформления вызывают это же — им доступен только 'external'.
    """
    if slots_active(company):
        return "slots"
    if (company.book_url or "").strip():
        return "external"
    return "off"


# ── Расчёт слотов ────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    """Почта клиента или пустая строка. Она необязательна и ничего не гейтит."""
    v = (value or "").strip().lower()[:160]
    return v if _EMAIL_RE.match(v) else ""


def _parse_hhmm(value: str) -> int | None:
    """'09:30' → минуты от полуночи. Мусор → None."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", str(value or ""))
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 24 or mi > 59:
        return None
    return h * 60 + mi


def _day_ranges(cfg: dict, local_day: datetime, week: dict | None = None) -> list[tuple[int, int]]:
    """Рабочие интервалы дня в минутах от полуночи (местное время).

    `week` позволяет посчитать день по графику конкретного мастера; без него
    берётся общий график заведения.
    """
    key = str(local_day.isoweekday())          # 1 = понедельник
    src = week if isinstance(week, dict) else cfg["week"]
    out = []
    for r in src.get(key) or []:
        if not (isinstance(r, (list, tuple)) and len(r) == 2):
            continue
        a, b = _parse_hhmm(r[0]), _parse_hhmm(r[1])
        if a is None or b is None or b <= a:
            continue
        out.append((a, b))
    return sorted(out)


def _taken(db, company_id: int, since_utc: datetime, until_utc: datetime,
           exclude_id: int | None = None) -> dict[datetime, set[str]]:
    """
    Занятые начала слотов → множество мастеров, у которых это время занято.

    В режиме одного мастера имя пустое, и множество вырождается в {''} — слот
    занят целиком. В режиме «Мульти» слот свободен, пока свободен хоть один
    мастер. `exclude_id` нужен, когда владелец переносит существующую запись:
    её собственное время не должно считаться занятым ею же.
    """
    q = db.query(Booking.slot_start, Booking.master).filter(
        Booking.company_id == company_id,
        Booking.slot_start >= since_utc,
        Booking.slot_start < until_utc,
        Booking.status != "canceled",
    )
    if exclude_id:
        q = q.filter(Booking.id != exclude_id)
    out: dict[datetime, set[str]] = {}
    for start, master in q.all():
        if start:
            out.setdefault(start, set()).add((master or "").strip())
    return out


def free_slots(db, company, day: str, *, owner: bool = False,
               exclude_id: int | None = None) -> list[dict]:
    """
    Свободные слоты на дату 'YYYY-MM-DD' (дата местная для бизнеса).

    Возвращает [{'time': '10:00', 'start': '2026-09-08T10:00', 'masters': [...]}]
    в местном времени. `masters` пуст в обычном режиме и содержит свободных
    мастеров в режиме «Мульти».

    `owner=True` снимает ограничение «не раньше чем через N часов»: правило
    защищает от записи впритык с улицы, а владелец в мини-приложении заводит
    записи и на ближайший час. `exclude_id` не считает занятой ту запись,
    которую сейчас переносят.
    """
    cfg = settings_of(company)
    try:
        local_day = datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        return []

    tz = timedelta(hours=cfg["tz"])
    now_local = datetime.utcnow() + tz
    earliest_local = now_local if owner else now_local + timedelta(hours=cfg["lead_hours"])
    horizon_local = (now_local + timedelta(days=cfg["days_ahead"])).replace(
        hour=23, minute=59, second=59, microsecond=0)
    if not owner and local_day.date() > horizon_local.date():
        return []

    # Кто на смене: в режиме «Мульти» — каждый мастер со своим графиком,
    # иначе один безымянный «мастер» по общему графику заведения.
    if cfg["multi"]:
        crew = [(m["name"], _day_ranges(cfg, local_day, m["week"])) for m in cfg["masters"]]
        crew = [(name, ranges) for name, ranges in crew if ranges]
    else:
        crew = [("", _day_ranges(cfg, local_day))]
        crew = [c for c in crew if c[1]]
    if not crew:
        return []

    taken = _taken(db, company.id,
                   local_day - tz - timedelta(hours=1),
                   local_day - tz + timedelta(days=1, hours=1),
                   exclude_id=exclude_id)

    # Слот → свободные на нём мастера. Порядок держим по времени начала.
    found: dict[int, list[str]] = {}
    for name, ranges in crew:
        for start_min, end_min in ranges:
            t = start_min
            # Слот целиком должен помещаться в интервал: полуслотов не предлагаем.
            while t + cfg["duration"] <= end_min:
                start_local = local_day + timedelta(minutes=t)
                busy = taken.get(start_local - tz, set())
                if start_local >= earliest_local and name not in busy:
                    found.setdefault(t, []).append(name)
                t += cfg["step"]

    out: list[dict] = []
    for t in sorted(found):
        start_local = local_day + timedelta(minutes=t)
        out.append({
            "time":    f"{t // 60:02d}:{t % 60:02d}",
            "start":   start_local.strftime("%Y-%m-%dT%H:%M"),
            "masters": [n for n in found[t] if n],
        })
    return out


def open_days(db, company, limit: int = 14) -> list[dict]:
    """Ближайшие дни горизонта с числом свободных слотов (для календаря виджета)."""
    cfg = settings_of(company)
    now_local = datetime.utcnow() + timedelta(hours=cfg["tz"])
    days = []
    for i in range(cfg["days_ahead"] + 1):
        d = (now_local + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        key = d.strftime("%Y-%m-%d")
        n = len(free_slots(db, company, key))
        if n:
            days.append({"date": key, "slots": n,
                         "weekday": d.isoweekday(), "day": d.day, "month": d.month})
        if len(days) >= limit:
            break
    return days


# ── Публичные эндпоинты ──────────────────────────────────────────────────────

def _company(db, slug: str):
    c = db.query(Company).filter(Company.slug == slug).first()
    if not c or not slots_active(c):
        raise HTTPException(status_code=404, detail="Запись недоступна")
    return c


def _rate_ok(key: str, limit: int, window: int) -> bool:
    now = time.time()
    arr = [t for t in _rate.get(key, []) if now - t < window]
    if len(arr) >= limit:
        _rate[key] = arr
        return False
    arr.append(now)
    _rate[key] = arr
    return True


@router.get("/{slug}/days")
async def api_days(slug: str):
    db = SessionLocal()
    try:
        c = _company(db, slug)
        cfg = settings_of(c)
        return {"ok": True, "days": open_days(db, c),
                "services": cfg["services"], "duration": cfg["duration"],
                "masters": [m["name"] for m in cfg["masters"]] if cfg["multi"] else []}
    finally:
        db.close()


@router.get("/{slug}/slots")
async def api_slots(slug: str, date: str = ""):
    db = SessionLocal()
    try:
        c = _company(db, slug)
        return {"ok": True, "date": date, "slots": free_slots(db, c, date)}
    finally:
        db.close()


class BookPayload(BaseModel):
    start:   str = ""     # '2026-09-08T10:00' — местное время бизнеса
    name:    str = ""
    phone:   str = ""
    service: str = ""
    comment: str = ""
    master:  str = ""     # режим «Мульти»: кого выбрали; пусто = любой свободный
    email:   str = ""     # необязательно, единственный канал напоминания клиенту


@router.post("/{slug}/create")
async def api_create(slug: str, payload: BookPayload, request: Request):
    db = SessionLocal()
    try:
        c = _company(db, slug)
        cfg = settings_of(c)

        name = (payload.name or "").strip()[:120]
        phone = (payload.phone or "").strip()[:40]
        if len(name) < 2:
            raise HTTPException(status_code=422, detail="Укажите имя")
        if len(re.sub(r"\D", "", phone)) < 10:
            raise HTTPException(status_code=422, detail="Укажите телефон полностью")

        try:
            start_local = datetime.strptime(payload.start, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise HTTPException(status_code=422, detail="Выберите время")

        # Слот проверяем заново по расписанию: клиент мог прислать что угодно.
        day_key = start_local.strftime("%Y-%m-%d")
        slot = next((s for s in free_slots(db, c, day_key) if s["start"] == payload.start), None)
        if not slot:
            raise HTTPException(status_code=409, detail="Это время уже заняли. Выберите другое.")

        # Мастера выбирает клиент или мы сами берём первого свободного.
        master = ""
        if cfg["multi"]:
            want = (payload.master or "").strip()
            if want and want not in slot["masters"]:
                raise HTTPException(status_code=409,
                                    detail="Этот мастер уже занят. Выберите другое время.")
            master = want or (slot["masters"][0] if slot["masters"] else "")
            if not master:
                raise HTTPException(status_code=409, detail="Это время уже заняли. Выберите другое.")

        ip = (request.client.host if request.client else "") or ""
        vhash = hashlib.sha256(f"{slug}|{ip}|{phone}".encode()).hexdigest()[:64]
        if not _rate_ok(f"{slug}|{ip}", limit=5, window=3600):
            raise HTTPException(status_code=429, detail="Слишком много записей подряд. Позвоните нам.")

        start_utc = start_local - timedelta(hours=cfg["tz"])
        # Финальная защита от гонки: два человека могли выбрать один слот
        # одновременно — перед вставкой смотрим ещё раз.
        if db.query(Booking).filter(
            Booking.company_id == c.id,
            Booking.slot_start == start_utc,
            Booking.master == master,
            Booking.status != "canceled",
        ).first():
            raise HTTPException(status_code=409, detail="Это время уже заняли. Выберите другое.")

        b = Booking(
            company_id=c.id, slot_start=start_utc, duration_min=cfg["duration"],
            service=(payload.service or "").strip()[:200], name=name, phone=phone,
            comment=(payload.comment or "").strip()[:500],
            status="new", source="site", visitor_hash=vhash,
            master=master, created_by="client",
            client_email=_clean_email(payload.email),
        )
        db.add(b)
        db.commit()
        db.refresh(b)

        _notify_owner(db, c, b, start_local)
        return {"ok": True, "id": b.id,
                "when": start_local.strftime("%d.%m.%Y в %H:%M")}
    finally:
        db.close()


# ── Уведомление владельца ────────────────────────────────────────────────────

def _notify_owner(db, company, booking, start_local: datetime) -> None:
    """
    Шлёт владельцу карточку записи с кнопками «Подтвердить» / «Отменить».
    Ошибка Telegram не должна ронять запись — она уже сохранена.
    """
    try:
        from app.telegram_bot import tg_send_message, booking_keyboard
        owner = db.query(User).filter(User.id == company.user_id).first() if company.user_id else None
        if not owner or not owner.tg_chat_id:
            return
        lines = [
            "Новая запись",
            f"{company.title}",
            "",
            f"Когда: {start_local:%d.%m.%Y} в {start_local:%H:%M}",
            f"Кто: {booking.name}",
            f"Телефон: {booking.phone}",
        ]
        if booking.service:
            lines.append(f"Услуга: {booking.service}")
        if booking.comment:
            lines.append(f"Комментарий: {booking.comment}")
        mid = tg_send_message(str(owner.tg_chat_id), "\n".join(lines),
                              reply_markup=booking_keyboard(booking.id))
        if mid:
            booking.notify_msg_id = mid
            db.commit()
    except Exception as e:                                   # noqa: BLE001
        print(f"[BOOKING] уведомление не ушло: {e}", flush=True)
