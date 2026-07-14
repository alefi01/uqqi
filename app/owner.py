"""
app/owner.py — роутер владельца (скрытая панель управления)

Маршруты:
    GET  /{PANEL_PATH}           — страница входа
    POST /{PANEL_PATH}           — авторизация
    GET  /{PANEL_PATH}/panel     — дашборд
    GET  /{PANEL_PATH}/logout    — выход

    POST /{PANEL_PATH}/api/parser/start          — запустить парсер
    GET  /{PANEL_PATH}/api/parser/status/{id}    — статус задачи + лог
    POST /{PANEL_PATH}/api/parser/stop/{id}      — остановить
    POST /{PANEL_PATH}/api/parser/import/{id}    — импортировать результаты в БД

    POST /{PANEL_PATH}/api/company/{id}/toggle
    DELETE /{PANEL_PATH}/api/company/{id}
"""

from __future__ import annotations

import asyncio
import os
import secrets
import string
import sys

# Выставляем путь к браузерам до любых импортов Playwright
if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    for _candidate in ["/root/.cache/ms-playwright", "/home/www-data/.cache/ms-playwright"]:
        if os.path.isdir(_candidate):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _candidate
            break
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt as _bcrypt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from datetime import timedelta

import io
import zipfile

from app.config import settings
from app.models import Company, Session as DbSession, SessionLocal, get_db
from app.parser import (
    parse_features, parse_gallery, parse_hours, parse_menu_items,
    parse_news, parse_reviews, parse_social_links, parse_status, slugify,
)

# ── Настройки ─────────────────────────────────────────────────────────────────

PANEL_PATH     = settings.PANEL_PATH          # секретный URL
PANEL_USER     = settings.PANEL_USER
PANEL_PASSWORD = settings.PANEL_PASSWORD

templates  = Jinja2Templates(directory="templates")
router     = APIRouter(prefix=f"/{PANEL_PATH}")

OWNER_SESSION_COOKIE = "owner_session"
OWNER_SESSION_TTL = timedelta(days=7)

ALPHABET = string.ascii_letters + string.digits


def _city_from_address_owner(address: str) -> str:
    """Извлекает город из адреса для текста предложения."""
    if not address:
        return ""
    import re as _re
    parts = [p.strip() for p in address.split(",") if p.strip()]
    for p in reversed(parts):
        if _re.search(r'\d', p) and len(p) < 12:
            continue
        if _re.match(r'^[А-ЯЁ][а-яё-]+', p):
            return p
    return parts[-1] if parts else ""


# ── Задачи парсера ────────────────────────────────────────────────────────────

class ParserTask:
    def __init__(self, task_id: str):
        self.task_id  = task_id
        self.status   = "running"   # running | done | stopped | error
        self.log: list[str] = []
        self.found    = 0
        self.no_site  = 0
        self.error    = ""
        self.places: list[Any] = []
        self._stop    = False
        self._task: asyncio.Task | None = None

    def append_log(self, line: str):
        self.log.append(line)

    def stop(self):
        self._stop = True
        if self._task:
            self._task.cancel()


_tasks: dict[str, ParserTask] = {}


# ── Auth helpers ──────────────────────────────────────────────────────────────

def is_owner(owner_session: str | None = Cookie(default=None),
             db: Session = Depends(get_db)) -> bool:
    if not owner_session:
        return False
    s = db.query(DbSession).filter(
        DbSession.token == owner_session,
        DbSession.identity == "owner"
    ).first()
    return s is not None and s.is_valid()


def require_owner(owner_session: str | None = Cookie(default=None),
                  db: Session = Depends(get_db)):
    if not owner_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    s = db.query(DbSession).filter(
        DbSession.token == owner_session,
        DbSession.identity == "owner"
    ).first()
    if not s or not s.is_valid():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# ── СТРАНИЦЫ ─────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def owner_login_page(request: Request,
                            owner_session: str | None = Cookie(default=None)):
    db: Session = SessionLocal()
    try:
        s = db.query(DbSession).filter(
            DbSession.token == owner_session,
            DbSession.identity == "owner"
        ).first() if owner_session else None
        already_auth = s is not None and s.is_valid()
    finally:
        db.close()
    if already_auth:
        return RedirectResponse(f"/{PANEL_PATH}/panel")
    return templates.TemplateResponse("owner_login.html", {"request": request, "error": None})


@router.post("", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
async def owner_login(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    if username != PANEL_USER or password != PANEL_PASSWORD:
        return templates.TemplateResponse("owner_login.html", {
            "request": request, "error": "Неверный логин или пароль"
        }, status_code=401)

    token = secrets.token_urlsafe(32)
    db2 = SessionLocal()
    try:
        from datetime import datetime
        db_session = DbSession(
            token      = token,
            identity   = "owner",
            expires_at = datetime.utcnow() + OWNER_SESSION_TTL,
        )
        db2.add(db_session)
        db2.commit()
    finally:
        db2.close()
    response = RedirectResponse(f"/{PANEL_PATH}/panel", status_code=303)
    response.set_cookie(OWNER_SESSION_COOKIE, token, max_age=86400 * 7, httponly=True, samesite="lax", secure=True)
    return response


@router.get("/logout")
async def owner_logout(owner_session: str | None = Cookie(default=None)):
    if owner_session:
        db2 = SessionLocal()
        try:
            db2.query(DbSession).filter(DbSession.token == owner_session).delete()
            db2.commit()
        finally:
            db2.close()
    response = RedirectResponse(f"/{PANEL_PATH}")
    response.delete_cookie(OWNER_SESSION_COOKIE)
    return response


@router.get("/panel", response_class=HTMLResponse)
async def owner_panel(request: Request,
                       db: Session = Depends(get_db),
                       _: bool = Depends(require_owner)):
    from app.models import Lead
    companies = db.query(Company).order_by(Company.created_at.desc()).all()
    leads     = db.query(Lead).order_by(Lead.created_at.desc()).limit(50).all()
    return templates.TemplateResponse("owner_panel.html", {
        "request":    request,
        "companies":  companies,
        "leads":      leads,
        "panel_path": PANEL_PATH,
    })


# ── API: УПРАВЛЕНИЕ КОМПАНИЯМИ ────────────────────────────────────────────────


@router.get("/api/company/{company_id}/export")
async def export_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_owner),
):
    """Генерирует ZIP с готовым сайтом для самостоятельного размещения."""
    from fastapi.responses import StreamingResponse
    from jinja2 import Environment, FileSystemLoader

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)

    # Рендерим шаблон сайта
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("site.html")

    hours_raw = " | ".join(
        f"{e['day']} {e['time']}"
        for e in company.hours
        if not e.get("closed") and e.get("time")
    )
    # Простой статус
    import re as _re
    status = ""
    for part in hours_raw.split(" | "):
        if not _re.match(r'^(Mo|Tu|We|Th|Fr|Sa|Su)\s', part):
            status = part
            break

    # feat_icon — имя SVG-иконки (общая логика из main.py)
    from app.main import _feat_icon

    # yandex_map_url — embed для iframe
    yandex_map_url = ""
    if company.yandex_url:
        m = _re.search(r'/org/[^/]+/(\d+)', company.yandex_url)
        if m:
            org_id = m.group(1)
            coords = company.coordinates or ""
            if coords and ',' in coords:
                lat, lon = coords.split(',')
                yandex_map_url = f"https://yandex.ru/map-widget/v1/org/{org_id}/?ll={lon.strip()}%2C{lat.strip()}&z=16"
            else:
                yandex_map_url = f"https://yandex.ru/map-widget/v1/org/{org_id}/?z=16"

    html_content = template.render(
        company=company,
        status=status,
        feat_icon=_feat_icon,
        yandex_map_url=yandex_map_url,
    )

    # README для клиента
    readme = f"""# Сайт «{company.title}» — инструкция по размещению

## Что внутри архива

- index.html  — готовый сайт
- README.md   — эта инструкция

## Как разместить на Beget

### Шаг 1 — Зарегистрируйтесь на Beget
Перейдите на beget.com и создайте аккаунт если его ещё нет.

### Шаг 2 — Привяжите домен
В панели управления Beget перейдите в «Домены» → «Добавить домен» и добавьте ваш домен.

### Шаг 3 — Загрузите файл сайта
1. Перейдите в «Файловый менеджер» → папка вашего домена (обычно public_html или папка с именем домена)
2. Загрузите файл index.html в эту папку
3. Если на домене уже есть файл index.html — замените его

### Шаг 4 — Проверьте сайт
Откройте ваш домен в браузере — сайт должен загрузиться.

### Шаг 5 — Настройте SSL (HTTPS)
В панели Beget перейдите в «SSL» и активируйте бесплатный сертификат Let's Encrypt для вашего домена.

## Важно

- Сайт полностью автономный, не требует сервера с PHP или Python
- Все данные зашиты в HTML-файл
- Для обновления данных (фото, часы, контакты) — отредактируйте файл index.html
  или напишите нам на support@uqqi.ru и мы поможем

## Поддержка

По всем вопросам: support@uqqi.ru
"""

    # Создаём ZIP в памяти
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html_content)
        zf.writestr("README.md", readme)

    buf.seek(0)
    filename = f"site_{company.slug}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/company/{company_id}/screenshot")
async def company_screenshot(company_id: int,
                              db: Session = Depends(get_db),
                              _: bool = Depends(require_owner)):
    """Отдаёт файл скриншота на скачивание."""
    from fastapi.responses import FileResponse
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.screenshot:
        raise HTTPException(status_code=404, detail="Скриншот ещё не готов")
    path = company.screenshot.lstrip("/")
    import os as _os
    if not _os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл скриншота не найден")
    return FileResponse(path, media_type="image/png",
                        filename=f"{company.slug}-preview.png")


# ── CLAIM / ДЕМО / МАТЕРИАЛЫ ДЛЯ ПРОДАЖИ ──────────────────────────────────────

@router.post("/api/company/{company_id}/demo")
async def toggle_demo(company_id: int,
                       db: Session = Depends(get_db),
                       _: bool = Depends(require_owner)):
    """Снять заглушку на 7 дней (показать сайт вживую по обычному адресу). Повтор — продлевает."""
    from datetime import datetime as _dt, timedelta as _td
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    company.demo_until = _dt.utcnow() + _td(days=7)
    db.commit()
    return {"ok": True, "demo_until": company.demo_until.isoformat()}


@router.post("/api/company/{company_id}/demo-off")
async def toggle_demo_off(company_id: int,
                           db: Session = Depends(get_db),
                           _: bool = Depends(require_owner)):
    """Вернуть заглушку досрочно."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    company.demo_until = None
    db.commit()
    return {"ok": True}


@router.post("/api/company/{company_id}/make-screenshot")
async def make_screenshot(company_id: int,
                           db: Session = Depends(get_db),
                           _: bool = Depends(require_owner)):
    """Снимает/пересоздаёт скриншот hero по реальному адресу сайта."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    try:
        from app.screenshot import capture_hero
        shot = await capture_hero(company.slug, settings.BASE_DOMAIN)
        if shot:
            company.screenshot = shot
            db.commit()
            return {"ok": True, "screenshot": shot}
        return {"ok": False, "error": "Не удалось сделать скриншот"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/api/company/{company_id}/materials")
async def company_materials(company_id: int,
                             db: Session = Depends(get_db),
                             _: bool = Depends(require_owner)):
    """Материалы для клиента: готовый текст предложения + ссылки + путь к скриншоту."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)

    base = settings.BASE_DOMAIN
    site_url  = f"https://{company.slug}.{base}/"
    claim_url = f"{site_url}demo" if company.claim_code else ""
    city = _city_from_address_owner(company.address)

    # Дружелюбный текст предложения (реальная молодая команда, не мошенники)
    city_part = f" в {city}" if city else ""
    offer_text = (
        f"Здравствуйте! 👋\n\n"
        f"Мы — небольшая команда разработчиков из России, делаем простые и красивые сайты "
        f"для локального бизнеса. Увидели «{company.title}»{city_part} и сделали для вас готовый сайт — "
        f"бесплатно, просто чтобы показать, как это может выглядеть.\n\n"
        f"Вот он, посмотрите: {claim_url or site_url}\n\n"
        f"Если понравится — заберёте себе за пару минут, первые 7 дней бесплатно, без предоплаты. "
        f"Не понравится — ничего страшного, просто закройте вкладку 🙂\n\n"
        f"С уважением,\nкоманда uqqi.ru"
    )

    return {
        "title":      company.title,
        "site_url":   site_url,
        "claim_url":  claim_url,
        "offer_text": offer_text,
        "screenshot": company.screenshot or "",
        "has_claim":  bool(company.claim_code),
    }


class TogglePayload(BaseModel):
    active: bool


@router.post("/api/company/{company_id}/toggle")
async def toggle_company(company_id: int, payload: TogglePayload,
                          db: Session = Depends(get_db),
                          _: bool = Depends(require_owner)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    company.is_active = payload.active
    db.commit()
    return {"ok": True}


@router.delete("/api/company/{company_id}")
async def delete_company(company_id: int,
                          db: Session = Depends(get_db),
                          _: bool = Depends(require_owner)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    # Удаляем скриншот, если был
    if company.screenshot:
        import os as _os
        p = company.screenshot.lstrip("/")
        try:
            if _os.path.exists(p):
                _os.remove(p)
        except Exception:
            pass
    db.delete(company)
    db.commit()
    return {"ok": True}


# ── API: МЕТРИКА ──────────────────────────────────────────────────────────────

# ── API: МЕТРИКА (старый простой эндпоинт удалён — используется расширенный ниже) ──


@router.get("/api/random-site")
async def random_site_owner(db: Session = Depends(get_db),
                             _: bool = Depends(require_owner)):
    """Дубль для удобства из owner-панели."""
    from sqlalchemy import func as _func
    company = db.query(Company).filter(Company.is_active == True).order_by(_func.random()).first()  # noqa: E712
    if not company:
        return {"url": ""}
    return {"url": f"https://{company.slug}.{settings.BASE_DOMAIN}/", "title": company.title}


@router.get("/api/company/{company_id}/build-log")
async def company_build_log(company_id: int,
                             db: Session = Depends(get_db),
                             _: bool = Depends(require_owner)):
    """Лог последней сборки сайта (для кнопки в панели)."""
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Сайт не найден")
    return {
        "id": c.id,
        "title": c.title,
        "slug": c.slug,
        "build_status": c.build_status,
        "build_attempts": c.build_attempts or 0,
        "build_log": c.build_log or "(лог пуст)",
    }


# ── API: МЕТРИКА ──────────────────────────────────────────────────────────────

@router.get("/api/metrics")
async def metrics(db: Session = Depends(get_db),
                   _: bool = Depends(require_owner)):
    """Сводная метрика: уники/просмотры по периодам, IP-детали, свежесть Я.Карт."""
    from datetime import datetime as _dt, timedelta as _td
    from sqlalchemy import text as _sql

    now = _dt.utcnow()
    periods = {"d1": 1, "d7": 7, "d30": 30, "d90": 90}
    cutoffs = {k: now - _td(days=v) for k, v in periods.items()}

    def uniq_for(target: str) -> dict:
        """Уники (по visitor_hash) для цели по периодам — из visits (только люди-уники)."""
        out = {}
        for k, cut in cutoffs.items():
            day_cut = cut.strftime("%Y-%m-%d")
            row = db.execute(_sql(
                "SELECT COUNT(DISTINCT visitor_hash) FROM visits "
                "WHERE target = :t AND day >= :d"
            ), {"t": target, "d": day_cut}).scalar()
            out[k] = int(row or 0)
        return out

    def views_for(target: str) -> dict:
        """Просмотры (все визиты людей, не боты) по периодам — из visit_logs."""
        out = {}
        for k, cut in cutoffs.items():
            row = db.execute(_sql(
                "SELECT COUNT(*) FROM visit_logs "
                "WHERE target = :t AND is_bot = 0 AND created_at >= :c"
            ), {"t": target, "c": cut}).scalar()
            out[k] = int(row or 0)
        return out

    def ips_for(target: str) -> list:
        """Топ IP за 90 дней: ip, город, кол-во запросов, бот, последний визит."""
        rows = db.execute(_sql(
            "SELECT ip, "
            "  MAX(city) as city, "
            "  COUNT(*) as requests, "
            "  MAX(is_bot) as bot, "
            "  MAX(created_at) as last_seen "
            "FROM visit_logs "
            "WHERE target = :t AND created_at >= :c AND ip != '' "
            "GROUP BY ip "
            "ORDER BY requests DESC "
            "LIMIT 100"
        ), {"t": target, "c": cutoffs["d90"]}).fetchall()
        result = []
        for r in rows:
            result.append({
                "ip": r[0],
                "city": r[1] or "",
                "requests": int(r[2] or 0),
                "bot": bool(r[3]),
                "last_seen": r[4] if isinstance(r[4], str) else (r[4].isoformat() if r[4] else ""),
            })
        return result

    # Лендинг — как сайт, с детализацией IP
    landing = uniq_for("__landing__")
    landing["pageviews"] = views_for("__landing__")
    landing["ips"] = ips_for("__landing__")

    # Сайты
    companies = db.query(Company).all()
    sites = []
    for c in companies:
        entry = {
            "title": c.title,
            "slug": c.slug,
            **uniq_for(c.slug),
            "pageviews": views_for(c.slug),
            "ips": ips_for(c.slug),
        }
        if c.last_parsed_at:
            entry["yandex_refresh"] = c.last_parsed_at.isoformat()
        sites.append(entry)

    return {"landing": landing, "sites": sites}


@router.get("/api/metrics/{slug}/log")
async def metrics_log(slug: str, ip: str = "",
                       db: Session = Depends(get_db),
                       _: bool = Depends(require_owner)):
    """Экспорт .txt лога визитов по сайту (весь или по конкретному IP)."""
    from fastapi.responses import PlainTextResponse
    from sqlalchemy import text as _sql
    from datetime import datetime as _dt, timedelta as _td

    cut = _dt.utcnow() - _td(days=90)
    q = ("SELECT created_at, ip, city, country, is_bot, user_agent FROM visit_logs "
         "WHERE target = :t AND created_at >= :c")
    params = {"t": slug, "c": cut}
    if ip:
        q += " AND ip = :ip"
        params["ip"] = ip
    q += " ORDER BY created_at DESC LIMIT 5000"
    rows = db.execute(_sql(q), params).fetchall()

    lines = [f"# Лог визитов: {slug}" + (f" | IP: {ip}" if ip else " | все IP"),
             f"# Сформировано: {_dt.utcnow().isoformat()} | записей: {len(rows)}",
             "# " + "-" * 70]
    for r in rows:
        ts = r[0] if isinstance(r[0], str) else (r[0].isoformat() if r[0] else "")
        bot = "BOT" if r[4] else "человек"
        geo = ", ".join(x for x in [r[2], r[3]] if x) or "—"
        lines.append(f"{ts}\t{r[1]}\t[{bot}]\t{geo}\t{r[5] or ''}")

    fname = f"log-{slug}" + (f"-{ip}" if ip else "-all") + ".txt"
    return PlainTextResponse(
        "\n".join(lines),
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/api/access-log")
async def access_log_export(lines: int = 500, q: str = "",
                             _: bool = Depends(require_owner)):
    """Отдаёт последние N строк access-лога (активность/атаки). q — фильтр-подстрока."""
    from fastapi.responses import PlainTextResponse
    from app.security import ACCESS_LOG_PATH
    import os
    if not os.path.exists(ACCESS_LOG_PATH):
        return PlainTextResponse("Лог пуст (пока не было запросов).")
    lines = max(10, min(lines, 5000))
    try:
        with open(ACCESS_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except Exception as e:
        return PlainTextResponse(f"Ошибка чтения лога: {e}")
    if q:
        all_lines = [ln for ln in all_lines if q in ln]
    tail = all_lines[-lines:]
    header = ("# time\tip\tmethod\tpath\tstatus\tms\tuser-agent\n"
              "# " + "-" * 70 + "\n")
    return PlainTextResponse(header + "".join(tail))


# ── API: ПОДДЕРЖКА (для владельца) ────────────────────────────────────────────

@router.get("/api/support")
async def support_list(db: Session = Depends(get_db),
                        _: bool = Depends(require_owner)):
    from app.models import SupportMessage
    msgs = db.query(SupportMessage).order_by(SupportMessage.created_at.desc()).limit(200).all()
    return {
        "messages": [
            {
                "id":        m.id,
                "company":   m.company_title,
                "slug":      m.company_slug,
                "email":     m.reply_email,
                "message":   m.message,
                "is_read":   m.is_read,
                "created_at": m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "",
            }
            for m in msgs
        ],
        "unread": sum(1 for m in msgs if not m.is_read),
    }


@router.post("/api/support/{msg_id}/read")
async def support_mark_read(msg_id: int,
                             db: Session = Depends(get_db),
                             _: bool = Depends(require_owner)):
    from app.models import SupportMessage
    m = db.query(SupportMessage).filter(SupportMessage.id == msg_id).first()
    if not m:
        raise HTTPException(status_code=404)
    m.is_read = True
    db.commit()
    return {"ok": True}


@router.delete("/api/support/{msg_id}")
async def support_delete(msg_id: int,
                          db: Session = Depends(get_db),
                          _: bool = Depends(require_owner)):
    from app.models import SupportMessage
    m = db.query(SupportMessage).filter(SupportMessage.id == msg_id).first()
    if m:
        db.delete(m)
        db.commit()
    return {"ok": True}


# ── API: ВЫБОР ВИТРИНЫ ────────────────────────────────────────────────────────

class VariantPayload(BaseModel):
    variant: str  # "A" или "B"


@router.post("/api/company/{company_id}/variant")
async def set_variant(company_id: int, payload: VariantPayload,
                       db: Session = Depends(get_db),
                       _: bool = Depends(require_owner)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)
    v = payload.variant.upper()
    if v not in ("A", "B"):
        raise HTTPException(status_code=422, detail="variant must be A or B")
    company.template_variant = v
    db.commit()
    return {"ok": True, "variant": v}


# ── API: БИЛЛИНГ ──────────────────────────────────────────────────────────────

class BillingPayload(BaseModel):
    next_payment_date: str = ""   # YYYY-MM-DD
    client_email:      str = ""


@router.post("/api/company/{company_id}/billing")
async def set_billing(company_id: int, payload: BillingPayload,
                       db: Session = Depends(get_db),
                       _: bool = Depends(require_owner)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)

    from datetime import datetime as _dt
    if payload.next_payment_date:
        try:
            company.next_payment_date = _dt.strptime(payload.next_payment_date, "%Y-%m-%d")
            # сброс флагов уведомлений при смене даты
            company.notified_7d = False
            company.notified_3d = False
        except ValueError:
            raise HTTPException(status_code=422, detail="Дата в формате ГГГГ-ММ-ДД")
    else:
        company.next_payment_date = None

    company.client_email = payload.client_email.strip()[:255]
    db.commit()
    return {"ok": True}


# ── API: ПАРСЕР ───────────────────────────────────────────────────────────────

class ParserStartPayload(BaseModel):
    query:                str
    city:                 str = ""
    limit:                int = 30
    delay:                int = 900
    only_without_website: bool = True
    open_cards:           bool = True
    mode:                 str = "overwrite"  # overwrite (перезаписать) | append (дополнить)


@router.post("/api/parser/start")
async def parser_start(payload: ParserStartPayload,
                        _: bool = Depends(require_owner)):
    task_id = secrets.token_hex(8)
    task = ParserTask(task_id)
    _tasks[task_id] = task

    # Запускаем парсер в фоне
    task._task = asyncio.create_task(_run_parser(task, payload))
    return {"task_id": task_id}


# ── API: КАНДИДАТЫ (двухфазный парсинг) ───────────────────────────────────────

async def _create_site_from_url(yandex_url: str, fallback_title: str, db):
    """Фаза 2: глубоко парсит карточку по URL и создаёт claim-сайт. Возвращает Company или None."""
    import importlib, json as _jts
    from datetime import datetime as _dt
    from app.parser import (parse_hours, parse_gallery, parse_social_links,
                            parse_news, parse_features, parse_menu_items,
                            parse_reviews, slugify)

    ymp = importlib.import_module("yandex_maps_parser")

    # argparse namespace для одиночного глубокого парсинга
    import argparse
    args = argparse.Namespace(
        query="", city="", limit=1, delay=500, timeout=90,
        only_without_website=False, open_cards=True, require_org_url=False,
        max_empty_scrolls=5, show_browser=False, slow_mo=0,
        width=1280, height=900, candidates_mode=False,
    )

    # Глубокий парсинг по прямому URL
    try:
        place = await ymp.collect_single_by_url(yandex_url, args)
    except Exception as e:
        print(f"[CANDIDATE] Ошибка парсинга {yandex_url}: {e}", flush=True)
        return None
    if not place or not place.title:
        return None

    base_slug = slugify(place.title) or slugify(fallback_title)
    if not base_slug:
        return None
    slug = base_slug
    counter = 2
    while db.query(Company).filter(Company.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    claim_code = secrets.token_urlsafe(9)
    company = Company(
        slug=slug, title=place.title, address=place.address, phone=place.phone,
        rating=place.rating, category=place.categories or "Организация",
        coordinates=place.coordinates, yandex_url=place.url or yandex_url,
        claim_code=claim_code, template_variant="B", admin_password_hash="",
    )
    company.last_parsed_at = _dt.utcnow()
    company.hours          = parse_hours(place.hours)
    company.gallery_photos = parse_gallery(place.gallery_photos)[:15]
    company.social_links   = parse_social_links(place.social_links)
    company.latest_news    = parse_news(place.latest_news)
    company.logo_url       = getattr(place, 'logo_url', '')
    company.book_url       = getattr(place, 'book_url', '')
    company.reviews_count  = getattr(place, 'reviews_count', '')
    _ts = getattr(place, 'transit_stop', '')
    if _ts:
        try: company.transit_stop = _jts.loads(_ts) if isinstance(_ts, str) else _ts
        except Exception: pass
    company.avg_bill    = getattr(place, 'avg_bill', '')
    company.features    = parse_features(getattr(place, 'features', ''))
    company.menu_items  = parse_menu_items(getattr(place, 'menu_items', ''))
    company.reviews     = parse_reviews(getattr(place, 'reviews', ''))

    db.add(company)
    db.commit()

    try:
        from app.build_queue import enqueue
        enqueue(company.id)
    except Exception:
        pass
    return company


@router.get("/api/candidates")
async def candidates_list(query: str = "",
                           db: Session = Depends(get_db),
                           _: bool = Depends(require_owner)):
    """Список кандидатов (организаций без сайта). query — фильтр по запросу поиска."""
    from app.models import ParseCandidate
    q = db.query(ParseCandidate)
    if query:
        q = q.filter(ParseCandidate.query == query)
    cands = q.order_by(ParseCandidate.created_at.desc()).all()
    # уникальные запросы для фильтра
    all_queries = sorted({c.query for c in db.query(ParseCandidate).all() if c.query})
    return {
        "queries": all_queries,
        "candidates": [{
            "id": c.id,
            "title": c.title,
            "address": c.address,
            "yandex_url": c.yandex_url,
            "query": c.query,
            "status": c.status,
            "company_id": c.company_id,
        } for c in cands],
    }


@router.post("/api/candidates/{cand_id}/create-site")
async def candidate_create_site(cand_id: int,
                                 db: Session = Depends(get_db),
                                 _: bool = Depends(require_owner)):
    """Фаза 2: глубокий парсинг кандидата по URL → создание claim-сайта."""
    from app.models import ParseCandidate
    cand = db.query(ParseCandidate).filter(ParseCandidate.id == cand_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Кандидат не найден")
    if cand.status == "site_created":
        raise HTTPException(status_code=400, detail="Сайт для этого кандидата уже создан")
    if not cand.yandex_url:
        raise HTTPException(status_code=400, detail="Нет ссылки на карточку")

    # Глубокий парсинг по прямому URL + создание сайта (та же логика, что была в импорте)
    company = await _create_site_from_url(cand.yandex_url, cand.title, db)
    if not company:
        raise HTTPException(status_code=500, detail="Не удалось создать сайт")

    cand.status = "site_created"
    cand.company_id = company.id
    db.commit()
    return {"ok": True, "company_id": company.id, "slug": company.slug}


@router.delete("/api/candidates/{cand_id}")
async def candidate_delete(cand_id: int,
                            db: Session = Depends(get_db),
                            _: bool = Depends(require_owner)):
    """Удалить кандидата из списка."""
    from app.models import ParseCandidate
    cand = db.query(ParseCandidate).filter(ParseCandidate.id == cand_id).first()
    if cand:
        db.delete(cand)
        db.commit()
    return {"ok": True}


@router.delete("/api/candidates")
async def candidates_clear(query: str = "",
                            db: Session = Depends(get_db),
                            _: bool = Depends(require_owner)):
    """Очистить весь список кандидатов (или по запросу)."""
    from app.models import ParseCandidate
    q = db.query(ParseCandidate)
    if query:
        q = q.filter(ParseCandidate.query == query)
    # не трогаем тех, у кого уже создан сайт (история)
    q = q.filter(ParseCandidate.status == "new")
    n = q.delete()
    db.commit()
    return {"ok": True, "deleted": n}


# ── API: ОБНОВИТЬ ДАННЫЕ КОМПАНИИ ─────────────────────────────────────────────

@router.post("/api/company/{company_id}/refresh")
async def refresh_company(company_id: int,
                           db: Session = Depends(get_db),
                           _: bool = Depends(require_owner)):
    """Повторный парсинг карточки. Не чаще 1 раза в день. Галерею не трогает
    если включён ручной режим. При удалённой карточке ставит yandex_unavailable."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404)

    if company.yandex_unavailable:
        raise HTTPException(status_code=400, detail="Карточка недоступна, обновление отключено")

    if not company.yandex_url:
        raise HTTPException(status_code=400, detail="Нет ссылки на Яндекс Карты")

    # Лимит: не чаще раза в день
    from datetime import datetime as _dt, timedelta as _td
    if company.last_parsed_at and (_dt.utcnow() - company.last_parsed_at) < _td(hours=24):
        nxt = company.last_parsed_at + _td(hours=24)
        raise HTTPException(status_code=429,
            detail=f"Обновлять можно раз в сутки. Следующее обновление после {nxt.strftime('%H:%M %d.%m')}")

    result = await _refresh_single_company(company, db)
    return result


async def _refresh_single_company(company, db) -> dict:
    """Перепарсивает одну компанию ПО ПРЯМОМУ URL (не поиском по названию!).
    Проверяет org_id: если спарсенная карточка — другая организация, данные НЕ трогаются."""
    import importlib, json as _json
    from datetime import datetime as _dt
    from app.parser import (parse_hours, parse_gallery, parse_social_links,
                            parse_features, parse_menu_items, parse_reviews)

    ymp = importlib.import_module("yandex_maps_parser")

    # Без сохранённого URL обновлять нельзя — иначе рискуем притащить чужую компанию
    if not company.yandex_url:
        company.yandex_unavailable = True
        db.commit()
        return {"ok": False, "unavailable": True,
                "message": "Нет сохранённой ссылки на карточку. Обновление отключено."}

    def _org_id(url: str):
        """Извлекает числовой org_id из ссылки (org-формат или mapframe oid=)."""
        import re as _re
        if not url:
            return None
        m = _re.search(r'/org/(?:[^/]+/)?(\d+)', url)
        if m:
            return m.group(1)
        m = (_re.search(r'oid%3D(\d+)', url, _re.I)
             or _re.search(r'[?&]oid=(\d+)', url)
             or _re.search(r'org%3Foid%3D(\d+)', url, _re.I)
             or _re.search(r'org\?oid=(\d+)', url, _re.I))
        return m.group(1) if m else None

    saved_org_id = _org_id(company.yandex_url)

    class _Args:
        query = ""
        city = ""
        limit = 1
        delay = 500
        timeout = 90
        only_without_website = False
        open_cards = True
        require_org_url = False
        max_empty_scrolls = 5
        show_browser = False
        slow_mo = 0
        format = "json"
        output = ""
        width = 1280
        height = 900

    try:
        # Открываем СОХРАНЁННУЮ ссылку напрямую (не ищем по названию!)
        match = await ymp.collect_single_by_url(company.yandex_url, _Args())
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if not match or not match.title:
        company.yandex_unavailable = True
        db.commit()
        return {"ok": False, "unavailable": True,
                "message": "Карточка не найдена на Яндекс Картах. Обновление отключено."}

    # КРИТИЧНАЯ ЗАЩИТА: сверяем org_id. Если карточка ведёт на ДРУГУЮ организацию —
    # не трогаем данные (иначе затрём клиента чужим бизнесом, как было с Алекс Кофе → Etlon).
    parsed_org_id = _org_id(match.url)
    if saved_org_id and parsed_org_id and saved_org_id != parsed_org_id:
        company.yandex_unavailable = True
        db.commit()
        print(f"[AUTO-REFRESH] ⚠️ org_id не совпал для {company.title}: "
              f"сохранён {saved_org_id}, получен {parsed_org_id} ({match.title}). "
              f"Обновление отклонено, данные сохранены.", flush=True)
        return {"ok": False, "unavailable": True, "org_mismatch": True,
                "message": f"Ссылка ведёт на другую организацию ({match.title}). "
                           f"Данные не изменены, обновление отключено."}

    # ── Обновляем поля с учётом флагов автообновления по вкладкам ──
    # Каждый блок обновляется только если его флаг auto_* = True.
    # Непустые значения не затираются пустыми.

    def _upd(field, value):
        """Обновляет поле только если новое значение непустое."""
        if value:
            setattr(company, field, value)

    # Вкладка «Основное»: название, адрес, телефон, категория, координаты
    if company.auto_main:
        _upd("title", match.title)
        _upd("address", match.address)
        _upd("phone", match.phone)
        _upd("category", match.categories)
        _upd("coordinates", match.coordinates)

    # Часы работы
    if company.auto_hours:
        new_hours = parse_hours(match.hours)
        if new_hours:
            company.hours = new_hours

    # Соцсети
    if company.auto_socials:
        new_socials = parse_social_links(match.social_links)
        if new_socials:
            company.social_links = new_socials

    # Реквизиты — Яндекс отдаёт не всегда, пустым не затираем
    if company.auto_requisites:
        _upd("org_name", getattr(match, 'org_name', ''))
        _upd("org_type", getattr(match, 'org_type', ''))
        _upd("org_inn",  getattr(match, 'org_inn', ''))

    # Поля, которые всегда обновляются автоматически (не редактируются вручную):
    # рейтинг, число оценок, логотип, кнопка записи, средний чек, особенности, каталог, отзыслан
    _upd("rating", match.rating)
    _upd("reviews_count", getattr(match, 'reviews_count', ''))
    _upd("logo_url", getattr(match, 'logo_url', ''))
    _upd("book_url", getattr(match, 'book_url', ''))
    _upd("avg_bill", getattr(match, 'avg_bill', ''))
    company.features    = parse_features(getattr(match, 'features', ''))
    company.menu_items  = parse_menu_items(getattr(match, 'menu_items', ''))
    company.reviews     = parse_reviews(getattr(match, 'reviews', ''))

    _ts = getattr(match, 'transit_stop', '')
    if _ts:
        try: company.transit_stop = _json.loads(_ts) if isinstance(_ts, str) else _ts
        except Exception: pass

    # Галерея — обновляется только если НЕ в ручном режиме
    if not company.gallery_manual:
        new_gallery = parse_gallery(match.gallery_photos)[:15]
        if new_gallery:
            company.gallery_photos = new_gallery

    company.last_parsed_at = _dt.utcnow()
    company.yandex_unavailable = False
    db.commit()

    return {"ok": True, "title": company.title,
            "gallery_kept": company.gallery_manual,
            "message": "Данные обновлены" + (" (галерея сохранена — ручной режим)" if company.gallery_manual else "")}


@router.get("/api/parser/status/{task_id}")
async def parser_status(task_id: str, _: bool = Depends(require_owner)):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404)
    return {
        "status":  task.status,
        "log":     task.log,
        "found":   task.found,
        "no_site": task.no_site,
        "error":   task.error,
    }


@router.post("/api/parser/stop/{task_id}")
async def parser_stop(task_id: str, _: bool = Depends(require_owner)):
    task = _tasks.get(task_id)
    if task:
        task.stop()
        task.status = "stopped"
    return {"ok": True}


@router.post("/api/parser/import/{task_id}")
async def parser_import(task_id: str,
                         db: Session = Depends(get_db),
                         _: bool = Depends(require_owner)):
    task = _tasks.get(task_id)
    if not task or not task.places:
        raise HTTPException(status_code=404, detail="Нет данных для импорта")

    created_sites = []

    for place in task.places:
        base_slug = slugify(place.title)
        if not base_slug:
            continue

        # Проверяем дубликаты
        existing = db.query(Company).filter(Company.slug == base_slug).first()
        if existing:
            task.append_log(f"[SKIP] {place.title} — уже существует")
            continue

        # Уникальный slug
        slug = base_slug
        counter = 2
        while db.query(Company).filter(Company.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Claim-код для продажи готового сайта (обезличенный сайт из панели)
        claim_code = secrets.token_urlsafe(9)

        company = Company(
            slug                = slug,
            title               = place.title,
            address             = place.address,
            phone               = place.phone,
            rating              = place.rating,
            category            = place.categories or "Организация",
            coordinates         = place.coordinates,
            yandex_url          = place.url,
            claim_code          = claim_code,
            template_variant    = "B",
            admin_password_hash = "",   # legacy-колонка NOT NULL в БД — кладём пустую строку
        )
        from datetime import datetime as _dt
        company.last_parsed_at = _dt.utcnow()
        company.hours          = parse_hours(place.hours)
        company.gallery_photos = parse_gallery(place.gallery_photos)[:15]
        company.social_links   = parse_social_links(place.social_links)
        company.latest_news    = parse_news(place.latest_news)
        company.logo_url       = getattr(place, 'logo_url', '')
        company.book_url       = getattr(place, 'book_url', '')
        company.reviews_count  = getattr(place, 'reviews_count', '')
        import json as _jts
        _ts = getattr(place, 'transit_stop', '')
        if _ts:
            try: company.transit_stop = _jts.loads(_ts) if isinstance(_ts, str) else _ts
            except Exception: pass
        company.avg_bill       = getattr(place, 'avg_bill', '')
        company.features       = parse_features(getattr(place, 'features', ''))
        company.menu_items     = parse_menu_items(getattr(place, 'menu_items', ''))
        company.reviews        = parse_reviews(getattr(place, 'reviews', ''))

        db.add(company)
        db.commit()

        # Ставим в очередь сборки (догрузит меню/фото/особенности + сделает скриншот)
        try:
            from app.build_queue import enqueue
            enqueue(company.id)
        except Exception:
            pass

        created_sites.append({
            "title":      place.title,
            "slug":       slug,
            "claim_code": claim_code,
            "claim_url":  f"https://{slug}.{settings.BASE_DOMAIN}/demo",
        })

    skipped = sum(1 for p in task.places if slugify(p.title) and
                  db.query(Company).filter(Company.slug == slugify(p.title)).first())

    return {
        "created": len(created_sites),
        "sites":   created_sites,
        "skipped": skipped,
    }


# ── ФОНОВАЯ ЗАДАЧА ПАРСЕРА ────────────────────────────────────────────────────

async def _run_parser(task: ParserTask, payload: ParserStartPayload):
    """Запускает yandex_maps_parser в том же процессе через его API."""
    try:
        # Проверяем наличие playwright
        import importlib.util
        spec = importlib.util.find_spec("playwright")
        if spec is None:
            task.append_log("[ERR] Playwright не установлен.")
            task.append_log("Выполните: pip install playwright && playwright install chromium")
            task.status = "error"
            task.error  = "Playwright не установлен"
            return

        # Добавляем корень проекта в путь для импорта парсера
        project_root = str(Path(__file__).parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from yandex_maps_parser import collect_places, has_real_website
        import argparse

        # Собираем аргументы как namespace
        args = argparse.Namespace(
            query              = payload.query,
            city               = payload.city,
            limit              = payload.limit,
            delay              = payload.delay,
            only_without_website = payload.only_without_website,
            open_cards         = payload.open_cards,
            timeout            = 90,
            max_empty_scrolls  = 5,
            width              = 1366,
            height             = 900,
            slow_mo            = 0,
            require_org_url    = True,
            show_browser       = False,
            candidates_mode    = True,   # Фаза 1: лёгкий парсинг, только организации без сайта
        )

        task.append_log(f"[INFO] Запрос: «{payload.query}{' ' + payload.city if payload.city else ''}»")
        task.append_log(f"[INFO] Лимит: {payload.limit} | задержка: {payload.delay}мс")
        task.append_log(f"[INFO] Только без сайта: {payload.only_without_website}")
        task.append_log("─" * 50)

        # Запускаем парсер напрямую в том же процессе
        # print перехватываем через SimpleQueue — не ломает async
        import queue as _queue
        import builtins as _builtins

        _log_q = _queue.SimpleQueue()
        _orig_print = _builtins.print

        def _capturing(*a, **kw):
            line = ' '.join(str(x) for x in a)
            if line.strip():
                _log_q.put(line)

        _builtins.print = _capturing
        try:
            places = await collect_places(args)
        except SystemExit:
            _builtins.print = _orig_print
            task.status = "error"
            task.error  = "Chromium не запустился"
            task.append_log("[ERR] Не удалось запустить браузер Chromium.")
            task.append_log("[ERR] Выполните на сервере:")
            task.append_log("      playwright install chromium")
            task.append_log("      playwright install-deps chromium")
            return
        except Exception as _e:
            places = []
            task.append_log(f"[ERR] {_e}")
        finally:
            _builtins.print = _orig_print

        # Переносим лог
        while not _log_q.empty():
            try:
                task.append_log(_log_q.get_nowait())
            except Exception:
                break

        if payload.only_without_website:
            places = [p for p in places if not has_real_website(p)]

        task.places  = places
        task.found   = len(places)
        task.no_site = len(places)

        # Сохраняем кандидатов в БД (Фаза 1). mode: overwrite очищает старый список.
        import re as _re
        def _org_id_of(url):
            if not url:
                return ""
            m = _re.search(r'/org/(?:[^/]+/)?(\d+)', url)
            if m:
                return m.group(1)
            m = (_re.search(r'oid%3D(\d+)', url, _re.I) or _re.search(r'[?&]oid=(\d+)', url))
            return m.group(1) if m else ""

        from app.models import ParseCandidate, SessionLocal
        db = SessionLocal()
        added, skipped = 0, 0
        try:
            if payload.mode == "overwrite":
                db.query(ParseCandidate).delete()
                db.commit()
            existing_orgs = {c.org_id for c in db.query(ParseCandidate).all() if c.org_id}
            for p in places:
                oid = _org_id_of(p.url)
                if oid and oid in existing_orgs:
                    skipped += 1
                    continue
                cand = ParseCandidate(
                    org_id=oid, title=p.title or "", address=p.address or "",
                    yandex_url=p.url or "", query=payload.query.strip(),
                    status="new",
                )
                db.add(cand)
                if oid:
                    existing_orgs.add(oid)
                added += 1
            db.commit()
        finally:
            db.close()

        task.append_log("─" * 50)
        task.append_log(f"[OK] Фаза 1 завершена. Без сайта: {len(places)} | "
                        f"добавлено: {added}" + (f" | пропущено дублей: {skipped}" if skipped else ""))
        task.status = "done"

    except asyncio.CancelledError:
        task.status = "stopped"
        task.append_log("[WARN] Задача остановлена.")
    except SystemExit as e:
        task.status = "error"
        task.error  = "SystemExit"
        task.append_log(f"[ERR] Парсер завершился с кодом {e.code}")
    except Exception as exc:
        task.status = "error"
        task.error  = str(exc)
        task.append_log(f"[ERR] {type(exc).__name__}: {exc}")
        import traceback
        for line in traceback.format_exc().splitlines():
            task.append_log(line)
