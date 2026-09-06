"""
app/main.py — FastAPI-приложение
"""

from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import bcrypt as _bcrypt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from datetime import datetime, timedelta

from app.models import Company, Session as DbSession, SessionLocal, create_tables, get_db
from app.parser import parse_status
from app.owner import router as owner_router

# ── Инициализация ─────────────────────────────────────────────────────────────

app = FastAPI(title="uqqi.ru", docs_url=None, redoc_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Заголовки безопасности + rate limiting + access-лог активности."""
    import time as _t
    from app.security import (log_access, client_ip as _cip,
                              check_rate_limit as _rl)
    from fastapi.responses import JSONResponse as _JSON

    ip = _cip(request)
    path = request.url.path
    method = request.method
    ua = request.headers.get("user-agent", "")

    # Rate limiting чувствительных endpoint'ов (вход, регистрация и т.п.)
    if method == "POST" and not _rl(ip, path):
        log_access(ip, method, path, 429, ua, 0)
        return _JSON(status_code=429,
                     content={"detail": "Слишком много попыток. Подождите пару минут."})

    start = _t.time()
    response = await call_next(request)
    elapsed_ms = (_t.time() - start) * 1000

    response.headers["X-Content-Type-Options"] = "nosniff"
    # Предпросмотр дизайна в ЛК встраивает витрину (slug.uqqi.ru) в iframe на
    # lk.uqqi.ru — это другой origin, SAMEORIGIN его бы запретил. Такие ответы
    # помечаются заголовком X-Uqqi-Embeddable и получают CSP frame-ancestors,
    # разрешающий вложение только внутрь нашего домена.
    # У starlette.MutableHeaders нет .pop() — только get/__delitem__.
    if response.headers.get("X-Uqqi-Embeddable") == "1":
        del response.headers["X-Uqqi-Embeddable"]
        response.headers["Content-Security-Policy"] = (
            "frame-ancestors 'self' https://uqqi.ru https://*.uqqi.ru"
        )
    else:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # Витрина отдаёт мобильный шаблон по User-Agent на том же адресе
    # (dynamic serving). Без Vary поисковики и кеши считают ответ одним и тем
    # же для всех устройств и могут показать десктопную версию на телефоне.
    response.headers["Vary"] = "User-Agent"

    # Access-лог: только метаданные, без тел запросов (не пишем пароли/токены)
    log_access(ip, method, path, response.status_code, ua, elapsed_ms)
    return response


templates  = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем панель владельца
app.include_router(owner_router)
from app.cabinet import router as cabinet_router
app.include_router(cabinet_router)
from app.chat import router as chat_router
app.include_router(chat_router)

SESSION_COOKIE = "admin_session"
SESSION_TTL    = timedelta(days=7)


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    create_tables()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    print(f"[APP] Запущено. Домен: {settings.BASE_DOMAIN}")
    print(f"[APP] Панель владельца: /{settings.PANEL_PATH}")
    # Запуск фоновых задач (биллинг + автообновление + watchdog)
    try:
        from app.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[APP] Планировщик не запущен: {e}")
    # Восстановление застрявших сборок после рестарта (отложенно — нужен running loop)
    try:
        import asyncio as _asyncio
        from app.scheduler import _recover_orphaned_builds
        async def _deferred_recover():
            await _asyncio.sleep(3)
            _recover_orphaned_builds()
        _asyncio.get_event_loop().create_task(_deferred_recover())
    except Exception as e:
        print(f"[APP] Восстановление сборок не запущено: {e}")


# ── Health-check (для UptimeRobot и алертов) ──────────────────────────────────

@app.get("/health")
async def health():
    """
    Проверка живости: БД отвечает, планировщик крутится, очередь не залипла.
    200 если всё ок, иначе 503 (внешний пинг увидит 'down').
    Доступен на любом хосте без авторизации.
    """
    from sqlalchemy import text as _sql
    checks: dict[str, str] = {}

    # 1. БД отвечает
    try:
        db = SessionLocal()
        try:
            db.execute(_sql("SELECT 1"))
        finally:
            db.close()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"fail: {type(e).__name__}"

    # 2. Планировщик жив (heartbeat обновлялся < 3 мин назад)
    try:
        from app.scheduler import heartbeat_age
        age = heartbeat_age()
        if age is None:
            checks["scheduler"] = "starting"  # ещё не было первого тика
        elif age < 180:
            checks["scheduler"] = "ok"
        else:
            checks["scheduler"] = f"stale ({int(age)}s)"
    except Exception as e:
        checks["scheduler"] = f"fail: {type(e).__name__}"

    # 3. Очередь не залипла: нет сборок в 'building' дольше 10 мин
    try:
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=10)
            stuck = db.query(Company).filter(
                Company.build_status == "building",
                Company.last_parsed_at.is_(None) | (Company.last_parsed_at < cutoff),
            ).count()
        finally:
            db.close()
        checks["queue"] = "ok" if stuck == 0 else f"stuck: {stuck}"
    except Exception as e:
        checks["queue"] = f"fail: {type(e).__name__}"

    healthy = all(v in ("ok", "starting") for v in checks.values())
    return JSONResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status_code=200 if healthy else 503,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

RESERVED_LABELS = {"lk", "www", "api", "admin", "static", "mail"}


def is_cabinet_host(request: Request) -> bool:
    host = request.headers.get("host", "").split(":")[0].lower()
    return host == f"lk.{settings.BASE_DOMAIN}"


def get_company_by_request(request: Request, db: Session) -> Company | None:
    host = request.headers.get("host", "").split(":")[0].lower()
    base = settings.BASE_DOMAIN

    if host == base or host == f"www.{base}":
        return None

    if host.endswith(f".{base}"):
        label = host[:-(len(base) + 1)]

        # Зарезервированные поддомены (lk, www, api...) — не компании
        if label in RESERVED_LABELS:
            return None

        # Кандидаты слага: исходный + декодированный из punycode
        candidates = [label]
        if label.startswith("xn--"):
            try:
                decoded = label.encode("ascii").decode("idna")
                if decoded and decoded != label:
                    candidates.append(decoded)
            except Exception:
                pass
        else:
            # на случай если в БД хранится punycode, а пришла кириллица
            try:
                encoded = label.encode("idna").decode("ascii")
                if encoded != label:
                    candidates.append(encoded)
            except Exception:
                pass

        return db.query(Company).filter(
            Company.slug.in_(candidates),
            Company.is_active == True,
        ).first()

    if settings.DEBUG:
        slug = request.query_params.get("slug")
        if slug:
            return db.query(Company).filter(Company.slug == slug).first()

    return None


def get_session_slug(admin_session: str | None = Cookie(default=None),
                     db: Session = Depends(get_db)) -> str | None:
    if not admin_session:
        return None
    s = db.query(DbSession).filter(DbSession.token == admin_session).first()
    if s and s.is_valid():
        return s.identity
    return None


def get_cabinet_user_id(uqqi_user_session: str | None = Cookie(default=None),
                         db: Session = Depends(get_db)) -> int | None:
    """ID юзера кабинета по куке uqqi_user_session."""
    if not uqqi_user_session:
        return None
    s = db.query(DbSession).filter(DbSession.token == uqqi_user_session).first()
    if s and s.is_valid() and s.identity.startswith("user:"):
        try:
            return int(s.identity.split(":", 1)[1])
        except ValueError:
            return None
    return None


def user_owns_site(slug: str, user_id: int | None, db: Session) -> bool:
    """True если сайт принадлежит юзеру кабинета."""
    if not user_id:
        return False
    c = db.query(Company).filter(Company.slug == slug).first()
    return bool(c and c.user_id == user_id)


def _can_edit_site(company) -> bool:
    """
    Редактирование контента — Pro-функция (наряду с премиум-оформлениями и
    чатом). Гейт тот же, что у остальных Pro: активный `pro_until`, включая
    Pro-триал. Старые sub_status/paid_until вестигиальны и здесь не участвуют.
    Гейт живёт на бэкенде — на скрытие кнопки в кабинете не полагаемся.
    """
    return pro_active(company)


def _require_editable(slug: str, user_id: int | None, db: Session):
    """Проверка владельца + существования + оплаты. Возвращает Company или 4xx."""
    if not user_owns_site(slug, user_id, db):
        raise HTTPException(status_code=403)
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company:
        raise HTTPException(status_code=404)
    if not _can_edit_site(company):
        raise HTTPException(
            status_code=403,
            detail="Редактирование контента входит в Pro.",
        )
    return company



# ── Иконки особенностей ───────────────────────────────────────────────────────

def _feat_icon(text: str) -> str:
    """Возвращает имя lucide-иконки по ключевым словам особенности."""
    t = text.lower()
    if any(w in t for w in ['карт', 'оплат', 'безнал', 'visa', 'master']): return 'credit-card'
    if any(w in t for w in ['наличн']): return 'banknote'
    if any(w in t for w in ['парковк', 'стоянк']): return 'square-parking'
    if any(w in t for w in ['wi-fi', 'wifi', 'вай-фай', 'интернет']): return 'wifi'
    if any(w in t for w in ['доставк', 'курьер']): return 'truck'
    if any(w in t for w in ['самовывоз', 'навынос']): return 'shopping-bag'
    if any(w in t for w in ['животн', 'собак', 'кошк', 'питомц']): return 'dog'
    if any(w in t for w in ['туалет', 'санузел']): return 'toilet'
    if any(w in t for w in ['инвалид', 'коляск', 'доступн']): return 'accessibility'
    if any(w in t for w in ['открытк', 'подарк', 'сувенир', 'сертификат']): return 'gift'
    if any(w in t for w in ['кофе', 'чай', 'напитк']): return 'coffee'
    if any(w in t for w in ['бар', 'алкогол', 'вин', 'пив']): return 'wine'
    if any(w in t for w in ['запис', 'бронир', 'резерв']): return 'calendar-check'
    if any(w in t for w in ['акци', 'скидк', 'спецпредл', 'лояльн']): return 'badge-percent'
    if any(w in t for w in ['детск', 'ребён', 'дети']): return 'baby'
    if any(w in t for w in ['терраса', 'веранд', 'летн']): return 'sun'
    if any(w in t for w in ['кальян']): return 'cloud'
    if any(w in t for w in ['музык', 'концерт']): return 'music'
    if any(w in t for w in ['полировк', 'детейлинг', 'мойк', 'чистк']): return 'sparkles'
    if any(w in t for w in ['ремонт', 'сервис']): return 'wrench'
    if any(w in t for w in ['покрас', 'малярн']): return 'paintbrush'
    return 'check'


# ── ПУБЛИЧНЫЙ САЙТ ────────────────────────────────────────────────────────────

def _is_mobile(request: Request) -> bool:
    """Определяет мобильное устройство по User-Agent."""
    ua = request.headers.get("user-agent", "").lower()
    markers = ["mobile", "android", "iphone", "ipod", "ipad", "windows phone", "opera mini"]
    return any(m in ua for m in markers)


def _city_from_address(address: str) -> str:
    """Пытается извлечь город из адреса (обычно предпоследний/последний компонент)."""
    if not address:
        return ""
    import re as _re
    # Ищем известные города или берём компонент после запятой, похожий на город
    parts = [p.strip() for p in address.split(",") if p.strip()]
    # Частый формат: «улица, дом, Город» — город часто последний или предпоследний
    for p in reversed(parts):
        # пропускаем дома/этажи/индексы
        if _re.search(r'\d', p) and len(p) < 12:
            continue
        # первое «словесное» — вероятно город
        if _re.match(r'^[А-ЯЁ][а-яё-]+', p):
            return p
    return parts[-1] if parts else ""


def _extract_org_id(url: str) -> str | None:
    """
    Достаёт числовой org_id из ссылки Яндекс.Карт обоих форматов:
    - org:      /maps/org/slug/12345  или  /maps/org/12345
    - mapframe: ...?poi[uri]=ymapsbm1://org?oid=12345  (в т.ч. url-encoded)
    """
    if not url:
        return None
    import re as _re
    # org-формат: /org/slug/ID или /org/ID
    m = _re.search(r'/org/(?:[^/]+/)?(\d+)', url)
    if m:
        return m.group(1)
    # mapframe: oid=ID (encoded oid%3DID) или org?oid=ID
    m = (_re.search(r'oid%3D(\d+)', url, _re.I)
         or _re.search(r'[?&]oid=(\d+)', url)
         or _re.search(r'org%3Foid%3D(\d+)', url, _re.I)
         or _re.search(r'org\?oid=(\d+)', url, _re.I))
    if m:
        return m.group(1)
    return None


def _compute_status(company) -> str:
    """
    Определяет статус по расписанию и текущему времени (МСК).
    Возвращает 'Открыто до HH:MM', 'Закрыто', 'Откроется в HH:MM' или ''.
    """
    from datetime import datetime, timedelta, timezone
    hours = company.hours or []
    if not hours:
        return ""
    # Москва UTC+3
    now = datetime.now(timezone(timedelta(hours=3)))
    wd = now.weekday()  # 0=Mon
    daymap = {0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa", 6: "Su"}
    today_key = daymap[wd]
    cur_min = now.hour * 60 + now.minute

    def parse_ranges(time_str):
        """'09:00–22:00' или '09:00-22:00, ...' → [(start_min, end_min)]"""
        import re
        out = []
        for m in re.finditer(r'(\d{1,2}):(\d{2})\s*[–\-]\s*(\d{1,2}):(\d{2})', time_str or ""):
            s = int(m.group(1)) * 60 + int(m.group(2))
            e = int(m.group(3)) * 60 + int(m.group(4))
            out.append((s, e))
        return out

    today = next((e for e in hours if e.get("day") == today_key), None)
    if today and not today.get("closed") and today.get("time"):
        for s, e in parse_ranges(today["time"]):
            end_disp = f"{e // 60:02d}:{e % 60:02d}"
            if s <= cur_min < e:
                return f"Открыто до {end_disp}"
            # ещё не открылось сегодня
            if cur_min < s:
                return f"Откроется в {s // 60:02d}:{s % 60:02d}"
    return "Закрыто"


def _build_site_context(request: Request, company) -> dict:
    """Собирает контекст для рендеринга витрины."""
    status_text = _compute_status(company)
    # Короткий статус для варианта B: только «Открыто»/«Закрыто»
    if status_text.startswith("Открыто"):
        status_short = "Открыто"
    elif status_text.startswith(("Закрыто", "Откроется")):
        status_short = "Закрыто"
    else:
        status_short = status_text

    import re as _re
    yandex_map_url = ""
    if company.yandex_url:
        org_id = _extract_org_id(company.yandex_url)
        if org_id:
            coords = company.coordinates or ""
            if coords and ',' in coords:
                lat, lon = coords.split(',')
                yandex_map_url = f"https://yandex.ru/map-widget/v1/org/{org_id}/?ll={lon.strip()}%2C{lat.strip()}&z=16"
            else:
                yandex_map_url = f"https://yandex.ru/map-widget/v1/org/{org_id}/?z=16"

    # Маршрут по координатам
    route_url = ""
    if company.coordinates and ',' in company.coordinates:
        lat, lon = [c.strip() for c in company.coordinates.split(',')]
        route_url = f"https://yandex.ru/maps/?ll={lon}%2C{lat}&mode=routes&rtext=~{lat}%2C{lon}"

    site_url = f"https://{company.slug}.{settings.BASE_DOMAIN}/"
    # Индексируем только легитимные (свои) сайты; серые непроплаченные и демо — noindex.
    seo_noindex = not _indexable(company)

    # Юр-дисклеймер в подвале — пока сайт не легитимизирован (серый и ещё не оплачен).
    is_claim_site = not is_legit(company)

    return {
        "request":        request,
        "company":        company,
        "status":         status_text,
        "status_short":   status_short,
        "yandex_map_url": yandex_map_url,
        "route_url":      route_url,
        "feat_icon":      _feat_icon,
        "site_url":       site_url,
        "seo_noindex":    seo_noindex,
        "is_claim_site":  is_claim_site,
    }


def _variant_template(request: Request, company) -> str:
    """
    Файл витрины по ключу дизайна (реестр app/designs.py).
    - Премиум (tier=pro) отдаётся ТОЛЬКО при активном Pro и готовом шаблоне;
      иначе фолбэк на бесплатный. У премиума свой адаптив — мобильный НЕ форсим C.
    - Бесплатные A/B: мобильный всегда → site_c.html.
    """
    from app import designs
    key = (company.template_variant or "A").strip()
    d = designs.get(key)

    if d and d.get("tier") == "pro":
        if pro_active(company):
            tpl = designs.template_for(key)
            if tpl:
                return tpl   # премиум responsive — он же и на мобильном
        # Pro не активен или шаблон ещё не готов → бесплатный
        return "site_c.html" if _is_mobile(request) else "site_a.html"

    # Бесплатные A/B
    if _is_mobile(request):
        return "site_c.html"
    return "site_b.html" if key == "B" else "site_a.html"


def _track_visit(request: Request, target: str, db: Session) -> None:
    """Записывает визит: уник за сутки (visits) + сырой лог с IP/гео/ботом (visit_logs)."""
    try:
        import hashlib
        from datetime import datetime as _dt
        from sqlalchemy import text as _sql

        # IP: учитываем X-Forwarded-For за nginx
        xff = request.headers.get("x-forwarded-for", "")
        ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "")
        ua = (request.headers.get("user-agent", "") or "")[:400]
        now = _dt.utcnow()
        day = now.strftime("%Y-%m-%d")
        vhash = hashlib.sha256(f"{ip}|{ua}|{day}".encode()).hexdigest()[:64]

        # 1) Уник за сутки (как раньше)
        db.execute(_sql(
            "INSERT OR IGNORE INTO visits (target, day, visitor_hash, created_at) "
            "VALUES (:t, :d, :h, :c)"
        ), {"t": target, "d": day, "h": vhash, "c": now})

        # 2) Сырой лог для детальной метрики (каждый визит = просмотр)
        try:
            from app.geoip import lookup as _geo, is_bot as _isbot
            geo = _geo(ip)
            bot = _isbot(ua)
            db.execute(_sql(
                "INSERT INTO visit_logs (target, ip, city, country, user_agent, is_bot, visitor_hash, created_at) "
                "VALUES (:t, :ip, :city, :country, :ua, :bot, :h, :c)"
            ), {"t": target, "ip": ip, "city": geo["city"], "country": geo["country"],
                "ua": ua, "bot": 1 if bot else 0, "h": vhash, "c": now})
        except Exception as _e:
            print(f"[VISIT] лог-деталь пропущена: {_e}", flush=True)

        db.commit()
    except Exception as e:
        print(f"[VISIT] Ошибка трекинга: {e}", flush=True)


@app.post("/api/yukassa/webhook")
async def yukassa_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook от ЮKassa. Идемпотентен: повторный payment.succeeded не продлевает дважды.
    Проверяем статус напрямую у ЮKassa (не доверяем телу слепо).
    """
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}  # некорректное тело — отвечаем 200 чтобы ЮKassa не ретраила вечно

    event = body.get("event", "")
    obj = body.get("object", {}) or {}
    payment_id = obj.get("id", "")

    if not payment_id:
        return {"ok": True}

    # Обрабатываем только успешную оплату.
    # Fail-CLOSED: применяем ТОЛЬКО если сами подтвердили статус+сумму у ЮKassa.
    # Телу webhook не доверяем (его можно подделать); при сбое проверки платёж
    # остаётся pending и его подхватит реконсиляция в scheduler.
    if event == "payment.succeeded":
        from app.cabinet import _verify_and_apply_payment
        applied, note = _verify_and_apply_payment(payment_id, db)
        print(f"[YUKASSA] webhook {payment_id}: {note}", flush=True)

    elif event == "payment.canceled":
        from app.models import Payment
        pay = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if pay and not pay.processed:
            pay.status = "canceled"
            pay.processed = True
            db.commit()

    return {"ok": True}


@app.api_route("/oferta", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def oferta_page(request: Request):
    resp = templates.TemplateResponse("oferta.html", {"request": request})
    resp.headers["Cache-Control"] = "public, max-age=3600"
    resp.headers["Last-Modified"] = "Sat, 28 Jun 2026 00:00:00 GMT"
    return resp


@app.api_route("/privacy", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def privacy_page(request: Request):
    resp = templates.TemplateResponse("privacy.html", {"request": request})
    resp.headers["Cache-Control"] = "public, max-age=3600"
    resp.headers["Last-Modified"] = "Sat, 28 Jun 2026 00:00:00 GMT"
    return resp


@app.api_route("/contacts", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def contacts_page(request: Request):
    resp = templates.TemplateResponse("contacts.html", {"request": request})
    resp.headers["Cache-Control"] = "public, max-age=3600"
    resp.headers["Last-Modified"] = "Sat, 28 Jun 2026 00:00:00 GMT"
    return resp


@app.get("/verify", response_class=HTMLResponse)
async def lk_verify_page(request: Request):
    """Страница подтверждения email (открывается по ссылке из письма)."""
    if is_cabinet_host(request):
        return templates.TemplateResponse("lk.html", {"request": request})
    raise HTTPException(status_code=404)


@app.get("/reset", response_class=HTMLResponse)
async def lk_reset_page(request: Request):
    """Страница сброса пароля (открывается по ссылке из письма)."""
    if is_cabinet_host(request):
        return templates.TemplateResponse("lk.html", {"request": request})
    raise HTTPException(status_code=404)


@app.get("/claim/{code}", response_class=HTMLResponse)
async def lk_claim_page(request: Request, code: str):
    """Страница привязки claim-сайта (переход по кнопке «Приобрести»). Отдаёт кабинет-SPA."""
    if is_cabinet_host(request):
        return templates.TemplateResponse("lk.html", {"request": request})
    raise HTTPException(status_code=404)


def pro_active(company) -> bool:
    """True, если активна Pro-подписка (Pro-триал ИЛИ оплата) — pro_until в будущем."""
    from datetime import datetime as _dt
    return bool(company and company.pro_until and company.pro_until > _dt.utcnow())


def is_legit(company) -> bool:
    """
    «Сайт свой» (легитимизирован): self-service — всегда; серый claim-сайт из
    owner-панели — только после первой оплаты (paid_once). Демо-витрины лендинга
    легитимны формально, но из индексации отсекаются отдельно (is_demo).
    """
    return bool(
        company
        and (not getattr(company, "is_claim", False) or getattr(company, "paid_once", False))
    )


def _indexable(company) -> bool:
    """Участвует в индексации/sitemap/robots: легитимный клиентский сайт, не демо."""
    return bool(is_legit(company) and not getattr(company, "is_demo", False))


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(request: Request, db: Session = Depends(get_db)):
    """robots.txt: разрешаем индексацию, указываем sitemap."""
    host = request.headers.get("host", settings.BASE_DOMAIN).split(":")[0]
    # Поддомен клиентского сайта
    if host != settings.BASE_DOMAIN and host != f"www.{settings.BASE_DOMAIN}" and not is_cabinet_host(request):
        company = get_company_by_request(request, db)
        # Нелегитимный (серый непроплаченный) или демо — запрещаем индексацию
        if company and not _indexable(company):
            return "User-agent: *\nDisallow: /\n"
        # Clean-param — директива Яндекса: параметры предпросмотра не создают
        # дублей карточки в индексе (Google их и так игнорирует по noindex).
        return (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /api/\n"
            "Clean-param: variant&preview\n"
            f"Sitemap: https://{host}/sitemap.xml\n"
        )
    # Кабинет — не индексируем
    if is_cabinet_host(request):
        return "User-agent: *\nDisallow: /\n"
    # Главный домен
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /health\n"
        f"Sitemap: https://{settings.BASE_DOMAIN}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, db: Session = Depends(get_db)):
    """sitemap.xml. На главном домене — список всех активных сайтов; на поддомене — сам сайт."""
    host = request.headers.get("host", settings.BASE_DOMAIN).split(":")[0]
    # (url, lastmod|None, priority)
    urls: list[tuple[str, object, str]] = []
    if host == settings.BASE_DOMAIN or host == f"www.{settings.BASE_DOMAIN}":
        base = f"https://{settings.BASE_DOMAIN}"
        urls.append((f"{base}/", None, "1.0"))
        # Юр-страницы: для поисковиков это сигнал доверия у сервиса, который
        # принимает платежи, — раньше они в карту сайта не попадали.
        for path in ("/oferta", "/privacy", "/contacts"):
            urls.append((f"{base}{path}", None, "0.3"))
        companies = db.query(Company).filter(
            Company.is_active == True,  # noqa: E712
            Company.build_status == "ready",
        ).all()
        for c in companies:
            # Только легитимные клиентские сайты (self-service или оплаченный claim).
            # Серые непроплаченные и демо-витрины НЕ индексируем.
            # ⚠️ Это чужие хосты (поддомены). Вебмастер их из карты главного
            # домена не возьмёт, но ссылка помогает обходу; свою карту каждый
            # поддомен отдаёт сам (ветка ниже).
            if _indexable(c):
                urls.append((f"https://{c.slug}.{settings.BASE_DOMAIN}/",
                             c.last_parsed_at or c.created_at, "0.8"))
    elif not is_cabinet_host(request):
        company = get_company_by_request(request, db)
        if company and _indexable(company):
            urls.append((f"https://{company.slug}.{settings.BASE_DOMAIN}/",
                         company.last_parsed_at or company.created_at, "1.0"))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority in urls:
        row = f"  <url><loc>{loc}</loc>"
        if lastmod is not None:
            try:
                row += f"<lastmod>{lastmod.date().isoformat()}</lastmod>"
            except AttributeError:
                pass
        row += f"<priority>{priority}</priority></url>"
        xml.append(row)
    xml.append("</urlset>")
    return Response(content="\n".join(xml), media_type="application/xml")


# ── Данные для главной ───────────────────────────────────────────────────────
# Числа на главной — настоящие, из базы: выдуманных цифр на лендинге нет.
# Запрос не бесплатный, поэтому держим результат 5 минут в памяти процесса.

_LANDING_STATS: dict = {"at": 0.0, "data": {}}
_LANDING_STATS_TTL = 300          # секунд


def _landing_stats(db: Session) -> dict:
    """Сколько сайтов собрано, в скольких городах, за сколько минут в среднем."""
    import time as _time
    now = _time.time()
    if _LANDING_STATS["data"] and now - _LANDING_STATS["at"] < _LANDING_STATS_TTL:
        return _LANDING_STATS["data"]

    rows = db.query(Company.address, Company.created_at, Company.last_parsed_at).filter(
        Company.build_status == "ready",
    ).all()

    cities, minutes = set(), []
    for address, created_at, parsed_at in rows:
        city = _city_from_address(address or "")
        if city:
            cities.add(city.lower())
        if created_at and parsed_at and parsed_at > created_at:
            delta = (parsed_at - created_at).total_seconds() / 60
            if 0 < delta < 30:        # длинные хвосты — это ретраи, не сборка
                minutes.append(delta)

    avg = round(sum(minutes) / len(minutes), 1) if minutes else 4.0
    data = {
        "sites":  len(rows),
        "cities": len(cities),
        "minutes": (f"{avg:.1f}".rstrip("0").rstrip(".")).replace(".", ","),
    }
    _LANDING_STATS.update(at=now, data=data)
    return data


_LANDING_JSON: dict = {}          # путь -> (mtime, распарсенные данные)


def _read_json_file(path: str, default):
    """Читает JSON-файл с кешем по mtime. Нет файла или битый — default."""
    import json as _json
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return default
    cached = _LANDING_JSON.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        with open(path, encoding="utf-8") as fh:
            data = _json.load(fh)
    except (OSError, ValueError):
        return default
    _LANDING_JSON[path] = (mtime, data)
    return data


def _landing_works() -> list:
    """
    Работы для ленты на главной. Манифест готовит scripts/make_showcase_shots.py
    (он же следит, чтобы туда попадали только легитимные сайты с фотографиями).
    Нет манифеста — секция на главной не рендерится.
    """
    data = _read_json_file("static/showcase/manifest.json", [])
    return data if isinstance(data, list) else []


def _landing_reviews() -> list:
    """Отзывы владельцев. Только реальные — файл ведём руками."""
    data = _read_json_file("content/reviews.json", [])
    return data if isinstance(data, list) else []


def _landing_context(request: Request, db: Session) -> dict:
    from app.cabinet import PLANS
    return {
        "request": request,
        "stats":   _landing_stats(db),
        "works":   _landing_works(),
        "reviews": _landing_reviews(),
        "plans":   PLANS,
        # Коды из .env. Пустые — мета-тег не выводится вовсе.
        "yandex_verification": settings.YANDEX_VERIFICATION,
        "google_verification": settings.GOOGLE_VERIFICATION,
    }


@app.get("/demo")
async def demo_view(request: Request):
    """
    Устарело: /demo больше не нужен — окно «Приобрести» показывается на обычном
    адресе (slug.uqqi.ru/) у обезличенного claim-сайта. Оставлен редиректом,
    чтобы уже разосланные клиентам ссылки на /demo не ломались.
    """
    return RedirectResponse(url="/", status_code=302)


@app.get("/", response_class=HTMLResponse)
async def site_index(request: Request, db: Session = Depends(get_db)):
    # Поддомен lk.uqqi.ru — личный кабинет
    if is_cabinet_host(request):
        return templates.TemplateResponse("lk.html", {"request": request})

    company = get_company_by_request(request, db)

    if not company:
        _track_visit(request, "__landing__", db)
        return templates.TemplateResponse("landing.html", _landing_context(request, db))

    # Деактивированный вручную сайт — дружелюбная заглушка
    if not company.is_active:
        return templates.TemplateResponse("site_inactive.html", {
            "request": request,
            "company": company,
        }, status_code=200)

    # Сайт ещё строится — заглушка "готовится"
    if company.build_status in ("queued", "building"):
        return templates.TemplateResponse("site_inactive.html", {
            "request": request, "company": company, "building": True,
        }, status_code=200)

    # Freemium: сайт бесплатен и всегда виден (кроме ручной деактивации и сборки выше).
    # Серые непроплаченные claim-сайты показываются, но noindex + дисклеймер (см. контекст).

    # Превью конкретного дизайна (?variant=A|B|C|<premium-key>) из пикера/ЛК —
    # рендерим напрямую, в ОБХОД Pro-гейта и БЕЗ учёта визита (клиент смотрит,
    # как выглядел бы его сайт в этом дизайне).
    preview = request.query_params.get("variant", "").strip()
    if preview:
        from app import designs
        up = preview.upper()
        if up in ("A", "B", "C"):
            ptpl = {"A": "site_a.html", "B": "site_b.html", "C": "site_c.html"}[up]
        else:
            ptpl = designs.template_for(preview)   # премиум, если включён и готов
        if ptpl:
            pctx = _build_site_context(request, company)
            pctx["unpaid_overlay"] = False
            pctx["chat_enabled"] = False
            pctx["seo_noindex"] = True     # превью не должно попадать в выдачу
            presp = templates.TemplateResponse(ptpl, pctx)
            presp.headers["Cache-Control"] = "no-store"
            # Разрешаем встроить превью в iframe кабинета (см. middleware выше):
            # клиент листает дизайны на СВОИХ данных, не открывая новую вкладку.
            presp.headers["X-Uqqi-Embeddable"] = "1"
            return presp

    tpl = _variant_template(request, company)
    _track_visit(request, company.slug, db)

    ctx = _build_site_context(request, company)
    ctx["unpaid_overlay"] = False  # overlay-напоминание в freemium не используется
    # Чат-виджет (Pro): показываем, только если Pro активен И владелец подключил Telegram.
    ctx["chat_enabled"] = False
    if pro_active(company) and company.user_id:
        from app.models import User as _User
        _owner = db.query(_User).filter(_User.id == company.user_id).first()
        ctx["chat_enabled"] = bool(_owner and _owner.tg_chat_id)
    # Claim-окошко «Приобрести» — на ОБЫЧНОМ адресе у обезличенного claim-сайта.
    # Клиенту отправляем реальную ссылку slug.uqqi.ru/ — там сразу и сайт, и
    # предложение приобрести. Отдельная страница /demo больше не нужна.
    if company.claim_code and not company.user_id:
        ctx["claim_offer"] = {
            "title": company.title,
            "city":  _city_from_address(company.address),
            "url":   f"https://lk.{settings.BASE_DOMAIN}/claim/{company.claim_code}",
        }
    resp = templates.TemplateResponse(tpl, ctx)
    # Короткий кеш (5 мин) — баланс скорости и свежести при смене дизайна
    resp.headers["Cache-Control"] = "public, max-age=300, must-revalidate"
    return resp


# ── ЗАЯВКИ С ЛЕНДИНГА ────────────────────────────────────────────────────────

@app.get("/api/showcase-site")
async def public_showcase_site(db: Session = Depends(get_db)):
    """
    Сайт для витрины на главной («вот что получается»). Главная показывает
    живой сайт в iframe, поэтому отдаём только такой, который не стыдно
    показать всем: собран, включён, с фотографиями и легитимный —
    обезличенные claim-сайты сюда не попадают, это чужой бизнес без его ведома.

    Адрес отдаём с ?variant=<его дизайн>: этот режим рендерит витрину без учёта
    визита, без чата и с заголовком X-Uqqi-Embeddable — иначе встроить в iframe
    не выйдет (X-Frame-Options). Ничего подходящего нет → пустой ответ, блок на
    главной прячется.
    """
    from sqlalchemy import func as _func
    rows = db.query(Company).filter(
        Company.is_active == True,  # noqa: E712
        Company.build_status == "ready",
    ).order_by(_func.random()).limit(25).all()
    for c in rows:
        if is_legit(c) and c.gallery_photos:
            variant = (c.template_variant or "A").strip() or "A"
            base = f"https://{c.slug}.{settings.BASE_DOMAIN}/"
            return {"url": base, "embed": f"{base}?variant={variant}",
                    "title": c.title, "slug": c.slug}
    return {"url": "", "embed": "", "title": "", "slug": ""}


@app.get("/api/random-site")
async def public_random_site(db: Session = Depends(get_db)):
    """Случайный активный сайт для кнопки 'Показать готовый сайт' на лендинге."""
    from sqlalchemy import func as _func
    company = db.query(Company).filter(
        Company.is_active == True,  # noqa: E712
    ).order_by(_func.random()).first()
    if not company:
        return {"url": "", "title": ""}
    return {
        "url":   f"https://{company.slug}.{settings.BASE_DOMAIN}/",
        "title": company.title,
    }


class LeadPayload(BaseModel):
    name:    str
    email:   str = ""
    url:     str = ""
    comment: str = ""


@app.post("/api/lead")
async def submit_lead(payload: LeadPayload, db: Session = Depends(get_db)):
    """Сохраняет заявку с лендинга."""
    import re as _re
    from app.models import Lead

    # Базовая серверная валидация
    name = payload.name.strip()[:255]
    email = payload.email.strip()[:255]
    url = payload.url.strip()[:500]
    comment = payload.comment.strip()[:1000]

    if not name:
        raise HTTPException(status_code=422, detail="Укажите название")
    if email and not _re.match(r'^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$', email):
        raise HTTPException(status_code=422, detail="Некорректный email")
    if url and "yandex.ru" not in url:
        raise HTTPException(status_code=422, detail="Ссылка должна быть с yandex.ru")

    # Санитизация — убираем опасные символы
    for val in [name, email, url, comment]:
        if any(c in val for c in ['<', '>', '"', "'"]):
            raise HTTPException(status_code=422, detail="Недопустимые символы")

    lead = Lead(
        name    = name,
        email   = email,
        url     = url,
        comment = comment,
    )
    db.add(lead)
    db.commit()
    return {"ok": True}


# ── АВТОРИЗАЦИЯ КЛИЕНТА ───────────────────────────────────────────────────────

@app.get("/admin")
async def admin_redirect_to_cabinet(request: Request):
    """Старый вход в админку убран — весь доступ через кабинет lk.uqqi.ru."""
    return RedirectResponse(f"https://lk.{settings.BASE_DOMAIN}/", status_code=302)


@app.get("/site/{slug}/edit", response_class=HTMLResponse)
async def cabinet_site_editor(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Редактор контента сайта, открывается из кабинета lk.uqqi.ru."""
    if not is_cabinet_host(request):
        raise HTTPException(status_code=404)
    if not user_id:
        return RedirectResponse(f"https://lk.{settings.BASE_DOMAIN}/", status_code=302)
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company or company.user_id != user_id:
        return RedirectResponse(f"https://lk.{settings.BASE_DOMAIN}/", status_code=302)
    # Редактор — Pro-функция (гейт _can_edit_site → pro_active).
    # Бэкенд-эндпоинты сохранения защищены отдельно (_require_editable).
    if not _can_edit_site(company):
        return RedirectResponse(
            f"https://lk.{settings.BASE_DOMAIN}/?edit_locked={slug}", status_code=302)
    return templates.TemplateResponse("admin_panel.html", {
        "request": request, "company": company, "from_cabinet": True,
    })


# ── API КЛИЕНТА: СОХРАНЕНИЕ ───────────────────────────────────────────────────

class SavePayload(BaseModel):
    title:          str = ""
    address:        str = ""
    phone:          str = ""
    category:       str = ""
    hours:          list[dict] = []
    social_links:   list[dict] = []
    org_name:       str = ""
    org_type:       str = ""
    org_inn:        str = ""


@app.post("/admin/save/{slug}")
async def admin_save(
    slug: str,
    payload: SavePayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    company = _require_editable(slug, user_id, db)

    # Сохраняем только разблокированные вкладки (флаг auto_* = False).
    # Рейтинг и галерея здесь не трогаются (только авто / отдельные эндпоинты).
    if not company.auto_main:
        company.title    = payload.title[:255]
        company.address  = payload.address[:500]
        company.phone    = payload.phone[:50]
        company.category = payload.category[:120]
    if not company.auto_hours:
        company.hours    = payload.hours
    if not company.auto_socials:
        company.social_links = payload.social_links
    # Реквизиты — всегда вручную (галочка автообновления убрана из панели)
    company.org_name = payload.org_name[:500]
    company.org_type = payload.org_type[:50]
    company.org_inn  = payload.org_inn[:20]
    db.commit()
    return {"ok": True}


# ── API КЛИЕНТА: ФЛАГИ И ДИЗАЙН ───────────────────────────────────────────────

class FlagPayload(BaseModel):
    flag:  str
    value: bool


@app.post("/admin/flag/{slug}")
async def admin_set_flag(
    slug: str,
    payload: FlagPayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Переключает флаг автообновления вкладки."""
    company = _require_editable(slug, user_id, db)
    if payload.flag not in ("auto_main", "auto_hours", "auto_socials", "auto_requisites"):
        raise HTTPException(status_code=422, detail="Неизвестный флаг")
    setattr(company, payload.flag, bool(payload.value))
    db.commit()
    return {"ok": True, "flag": payload.flag, "value": bool(payload.value)}


class DesignPayload(BaseModel):
    variant: str


@app.post("/admin/design/{slug}")
async def admin_set_design(
    slug: str,
    payload: DesignPayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Клиент выбирает дизайн A или B."""
    company = _require_editable(slug, user_id, db)
    v = payload.variant.upper()
    if v not in ("A", "B"):
        raise HTTPException(status_code=422, detail="variant must be A or B")
    company.template_variant = v
    db.commit()
    return {"ok": True, "variant": v}


# ── API КЛИЕНТА: ФОТО ГАЛЕРЕИ ─────────────────────────────────────────────────

ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_SIZE = 8 * 1024 * 1024
MAX_GALLERY    = 12


@app.post("/admin/gallery/toggle-manual/{slug}")
async def gallery_toggle_manual(
    slug: str,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Включает/выключает ручной режим галереи."""
    company = _require_editable(slug, user_id, db)

    company.gallery_manual = not company.gallery_manual
    db.commit()
    return {"ok": True, "manual": company.gallery_manual}


@app.post("/admin/gallery/upload/{slug}")
async def gallery_upload(
    slug: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Загружает фото в галерею с ресайзом/сжатием. Включает ручной режим."""
    company = _require_editable(slug, user_id, db)

    photos = company.gallery_photos
    if len(photos) >= MAX_GALLERY:
        raise HTTPException(status_code=400, detail=f"Максимум {MAX_GALLERY} фотографий")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Только JPG, PNG, WebP")

    contents = await file.read()
    if len(contents) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=400, detail="Файл больше 8 МБ")

    # Ресайз и сжатие через Pillow
    from PIL import Image
    import io as _io
    try:
        img = Image.open(_io.BytesIO(contents))
        img = img.convert("RGB")
        # Ограничиваем макс. сторону 1600px
        img.thumbnail((1600, 1600), Image.LANCZOS)
    except Exception:
        raise HTTPException(status_code=400, detail="Не удалось обработать изображение")

    company_dir = settings.upload_path / slug
    company_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    out_path = company_dir / filename
    img.save(out_path, "JPEG", quality=82, optimize=True)

    url = f"/static/uploads/{slug}/{filename}"
    photos.append(url)
    company.gallery_photos = photos
    # Первая ручная загрузка → замораживаем галерею
    company.gallery_manual = True
    db.commit()

    return {"ok": True, "url": url, "count": len(photos), "manual": True}


class GalleryDeletePayload(BaseModel):
    url: str


@app.post("/admin/gallery/delete/{slug}")
async def gallery_delete(
    slug: str,
    payload: GalleryDeletePayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Удаляет фото из галереи."""
    company = _require_editable(slug, user_id, db)

    photos = [p for p in company.gallery_photos if p != payload.url]
    company.gallery_photos = photos
    company.gallery_manual = True

    # Удаляем локальный файл если он наш
    if payload.url.startswith(f"/static/uploads/{slug}/"):
        fname = payload.url.split("/")[-1]
        fpath = settings.upload_path / slug / fname
        try:
            if fpath.exists():
                fpath.unlink()
        except Exception:
            pass

    db.commit()
    return {"ok": True, "count": len(photos)}


class GalleryReorderPayload(BaseModel):
    order: list[str]


@app.post("/admin/gallery/reorder/{slug}")
async def gallery_reorder(
    slug: str,
    payload: GalleryReorderPayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Сохраняет новый порядок фото (drag&drop)."""
    company = _require_editable(slug, user_id, db)

    current = set(company.gallery_photos)
    new_order = [u for u in payload.order if u in current]
    # добавляем потерянные в конец
    for u in company.gallery_photos:
        if u not in new_order:
            new_order.append(u)
    company.gallery_photos = new_order[:MAX_GALLERY]
    company.gallery_manual = True
    db.commit()
    return {"ok": True}


# ── API КЛИЕНТА: ПОДДЕРЖКА ────────────────────────────────────────────────────

class SupportPayload(BaseModel):
    message: str
    email:   str


@app.post("/admin/support/{slug}")
async def support_submit(
    slug: str,
    payload: SupportPayload,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_cabinet_user_id),
):
    """Клиент пишет в поддержку из своей панели."""
    if not user_owns_site(slug, user_id, db):
        raise HTTPException(status_code=403)
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company:
        raise HTTPException(status_code=404)

    import re as _re
    msg = payload.message.strip()[:5000]
    email = payload.email.strip()[:255]
    if len(msg) < 5:
        raise HTTPException(status_code=422, detail="Сообщение слишком короткое")
    if not _re.match(r'^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$', email):
        raise HTTPException(status_code=422, detail="Некорректный email")

    from app.models import SupportMessage
    sm = SupportMessage(
        company_slug  = slug,
        company_title = company.title,
        reply_email   = email,
        message       = msg,
    )
    db.add(sm)
    db.commit()
    return {"ok": True}
