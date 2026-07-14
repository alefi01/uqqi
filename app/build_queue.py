"""
app/build_queue.py — фоновая очередь создания сайтов из ссылки Яндекса.
Лимит: 1 парсинг одновременно. Триал 7 дней с момента готовности.
"""

from __future__ import annotations

import asyncio
import importlib
import json as _json
from datetime import datetime, timedelta

from app.models import SessionLocal, Company
from app.parser import (
    slugify, slug_to_punycode, parse_hours, parse_gallery, parse_social_links,
    parse_news, parse_features, parse_menu_items, parse_reviews,
)

TRIAL_DAYS = 7
BUILD_TIMEOUT = 180        # общий таймаут на одну сборку, сек (3 минуты)
MAX_ATTEMPTS = 3           # всего попыток: 1 основная + 2 авто-ретрая


def _clean_menu_photos(items: list) -> list:
    """
    Фото товаров каталога оставляем как есть.
    Для товарных картинок (get-sprav-products) суффикс _height/_width — рабочий,
    в отличие от галереи. Чистим только пустые/мусорные значения.
    """
    for it in (items or []):
        url = (it.get("image_url") or "").strip()
        # Отсекаем только явный мусор: пины карты и svg
        if url and ('pin_' in url or url.endswith('.svg')):
            it["image_url"] = ""
    return items


def _log(company_id: int, message: str):
    """Дописывает строку в build_log компании (+ journalctl). Хранит последние ~4 КБ."""
    line = f"[{datetime.utcnow():%H:%M:%S}] {message}"
    print(f"[BUILD #{company_id}] {message}", flush=True)
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if c:
            prev = c.build_log or ""
            combined = (prev + line + "\n")[-4000:]  # не растим бесконечно
            c.build_log = combined
            db.commit()
    except Exception:
        pass
    finally:
        db.close()


# Очередь company_id на парсинг и единственный воркер
_queue: asyncio.Queue[int] = asyncio.Queue()
_worker_started = False


def ensure_worker():
    """Запускает воркер очереди один раз."""
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    asyncio.create_task(_worker())
    print("[BUILD] Воркер очереди парсинга запущен", flush=True)


def enqueue(company_id: int):
    """Ставит сайт в очередь на сборку."""
    ensure_worker()
    _queue.put_nowait(company_id)


async def _worker():
    """Обрабатывает очередь по одному сайту с общим таймаутом и авто-ретраем."""
    while True:
        company_id = await _queue.get()
        try:
            # Общий таймаут на всю сборку
            await asyncio.wait_for(_build_one(company_id), timeout=BUILD_TIMEOUT)
        except asyncio.TimeoutError:
            _log(company_id, f"⏱ Превышен таймаут {BUILD_TIMEOUT}с — сборка прервана")
            _handle_failure(company_id)
        except Exception as e:
            _log(company_id, f"✖ Ошибка сборки: {type(e).__name__}: {e}")
            _handle_failure(company_id)
        finally:
            _queue.task_done()


def _handle_failure(company_id: int):
    """
    Обрабатывает неудачу: если попыток меньше MAX_ATTEMPTS — авто-ретрай,
    иначе помечает error (пользователь жмёт «Попробовать снова»).
    """
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if not c:
            return
        attempts = (c.build_attempts or 0)
        if attempts < MAX_ATTEMPTS:
            c.build_status = "queued"  # вернём в очередь
            db.commit()
            db.close()
            _log(company_id, f"↻ Авто-повтор (попытка {attempts + 1} из {MAX_ATTEMPTS})")
            enqueue(company_id)
            return
        else:
            c.build_status = "error"
            db.commit()
            _log(company_id, "✖ Исчерпаны попытки — статус error")
    finally:
        try:
            db.close()
        except Exception:
            pass


def _mark_error(company_id: int):
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if c:
            c.build_status = "error"
            db.commit()
    finally:
        db.close()


async def _build_one(company_id: int):
    """Парсит карточку по ссылке и заполняет компанию. Запускает триал."""
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return

        company.build_status = "building"
        company.build_attempts = (company.build_attempts or 0) + 1
        attempt = company.build_attempts
        db.commit()
        _log(company_id, f"▶ Старт сборки (попытка {attempt})")

        target_url = company.yandex_url
        if not target_url:
            company.build_status = "error"
            db.commit()
            _log(company_id, "✖ Нет ссылки Яндекса")
            return

        ymp = importlib.import_module("yandex_maps_parser")

        class _Args:
            show_browser = False
            slow_mo = 0
            timeout = 90
            width = 1280
            height = 900

        _log(company_id, "🌐 Открываю карточку, парсю данные…")
        place = await ymp.collect_single_by_url(target_url, _Args())

        if not place or not place.title:
            # Не помечаем error напрямую — пусть _handle_failure решит про ретрай
            raise RuntimeError("парсинг не дал результата (пустая карточка/капча?)")

        _log(company_id, f"✓ Карточка: «{place.title}»")

        # Генерируем уникальный slug
        base = slugify(place.title)
        if not base:
            base = f"site-{company_id}"
        slug = base
        n = 1
        while db.query(Company).filter(Company.slug == slug, Company.id != company.id).first():
            n += 1
            slug = f"{base}-{n}"

        # Заполняем данными
        company.slug         = slug
        company.title        = place.title
        company.address      = place.address or ""
        company.phone        = place.phone or ""
        company.rating       = place.rating or ""
        company.category     = place.categories or "Организация"
        company.coordinates  = place.coordinates or ""
        company.yandex_url   = place.url or target_url
        company.template_variant = "A"
        company.hours        = parse_hours(place.hours)
        company.gallery_photos = parse_gallery(place.gallery_photos)[:12]
        company.social_links = parse_social_links(place.social_links)
        company.logo_url     = getattr(place, 'logo_url', '')
        company.book_url     = getattr(place, 'book_url', '')
        company.reviews_count = getattr(place, 'reviews_count', '')
        company.catalog_title = getattr(place, 'catalog_title', 'Товары и услуги')
        company.about_text   = getattr(place, 'about_text', '')
        company.avg_bill     = getattr(place, 'avg_bill', '')
        company.features     = parse_features(getattr(place, 'features', ''))
        company.menu_items   = _clean_menu_photos(parse_menu_items(getattr(place, 'menu_items', '')))
        company.reviews      = parse_reviews(getattr(place, 'reviews', ''))

        _gallery_n = len(company.gallery_photos or [])
        _menu_n = len(company.menu_items or [])
        _log(company_id, f"✓ Данные: фото {_gallery_n}, каталог {_menu_n}, особенности {len(company.features or [])}")

        _ts = getattr(place, 'transit_stop', '')
        if _ts:
            try:
                company.transit_stop = _json.loads(_ts) if isinstance(_ts, str) else _ts
            except Exception:
                pass

        # Готово. Если триал — запускаем 7 дней; если платный — сразу требует оплаты.
        now = datetime.utcnow()
        company.last_parsed_at = now
        company.build_status   = "ready"
        company.is_active      = True
        if company.sub_status == "trial":
            company.trial_ends_at = now + timedelta(days=TRIAL_DAYS)
            db.commit()
            _log(company_id, f"✅ Готово (триал): {slug}.uqqi.ru до {company.trial_ends_at:%d.%m.%Y}")
        else:
            company.sub_status = "unpaid"
            db.commit()
            _log(company_id, f"✅ Готово (платный, ждёт оплаты): {slug}.uqqi.ru")

        # Скриншот больше НЕ снимается автоматически — только по кнопке в owner-панели.

    finally:
        db.close()
