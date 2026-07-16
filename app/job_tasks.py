"""
app/job_tasks.py — процесс-агностичные задачи парсинга (Блок 9).

Вынесено из build_queue.py, чтобы одну и ту же логику могли выполнять:
  • текущий asyncio-воркер в процессе app (build_queue._worker) — пока так;
  • отдельный процесс worker.py (subprocess) — целевая архитектура.

Здесь НЕ должно быть очереди/диспетчера — только сами задачи и их логирование.
"""

from __future__ import annotations

import importlib
import json as _json
from datetime import datetime, timedelta

from app.models import SessionLocal, Company
from app.parser import (
    slugify, parse_hours, parse_gallery, parse_social_links,
    parse_news, parse_features, parse_menu_items, parse_reviews,
)

TRIAL_DAYS = 7


def _clean_menu_photos(items: list) -> list:
    """
    Фото товаров каталога оставляем как есть.
    Для товарных картинок (get-sprav-products) суффикс _height/_width — рабочий,
    в отличие от галереи. Чистим только пустые/мусорные значения.
    """
    for it in (items or []):
        url = (it.get("image_url") or "").strip()
        if url and ('pin_' in url or url.endswith('.svg')):
            it["image_url"] = ""
    return items


def job_log(company_id: int, message: str):
    """Дописывает строку в build_log компании (+ stdout). Хранит последние ~4 КБ."""
    line = f"[{datetime.utcnow():%H:%M:%S}] {message}"
    print(f"[BUILD #{company_id}] {message}", flush=True)
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.id == company_id).first()
        if c:
            prev = c.build_log or ""
            combined = (prev + line + "\n")[-4000:]
            c.build_log = combined
            db.commit()
    except Exception:
        pass
    finally:
        db.close()


async def build_site(company_id: int):
    """
    Парсит карточку по ссылке компании и заполняет её данными. Запускает триал.
    Идемпотентна: работает по существующему company_id, повторный вызов
    просто перезаполняет данные (дублей сайтов не создаёт).
    """
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return

        company.build_status = "building"
        company.build_attempts = (company.build_attempts or 0) + 1
        attempt = company.build_attempts
        db.commit()
        job_log(company_id, f"▶ Старт сборки (попытка {attempt})")

        target_url = company.yandex_url
        if not target_url:
            company.build_status = "error"
            db.commit()
            job_log(company_id, "✖ Нет ссылки Яндекса")
            return

        ymp = importlib.import_module("yandex_maps_parser")

        class _Args:
            show_browser = False
            slow_mo = 0
            timeout = 90
            width = 1280
            height = 900

        job_log(company_id, "🌐 Открываю карточку, парсю данные…")
        place = await ymp.collect_single_by_url(target_url, _Args())

        if not place or not place.title:
            raise RuntimeError("парсинг не дал результата (пустая карточка/капча?)")

        job_log(company_id, f"✓ Карточка: «{place.title}»")

        base = slugify(place.title)
        if not base:
            base = f"site-{company_id}"
        slug = base
        n = 1
        while db.query(Company).filter(Company.slug == slug, Company.id != company.id).first():
            n += 1
            slug = f"{base}-{n}"

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
        job_log(company_id, f"✓ Данные: фото {_gallery_n}, каталог {_menu_n}, особенности {len(company.features or [])}")

        _ts = getattr(place, 'transit_stop', '')
        if _ts:
            try:
                company.transit_stop = _json.loads(_ts) if isinstance(_ts, str) else _ts
            except Exception:
                pass

        now = datetime.utcnow()
        company.last_parsed_at = now
        company.build_status   = "ready"
        company.is_active      = True
        if company.sub_status == "trial":
            company.trial_ends_at = now + timedelta(days=TRIAL_DAYS)
            db.commit()
            job_log(company_id, f"✅ Готово (триал): {slug}.uqqi.ru до {company.trial_ends_at:%d.%m.%Y}")
        else:
            company.sub_status = "unpaid"
            db.commit()
            job_log(company_id, f"✅ Готово (платный, ждёт оплаты): {slug}.uqqi.ru")
    finally:
        db.close()
