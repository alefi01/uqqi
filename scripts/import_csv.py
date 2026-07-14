#!/usr/bin/env python3
"""
scripts/import_csv.py — импорт компаний из CSV в базу данных

Использование:
    python scripts/import_csv.py out.txt
    python scripts/import_csv.py out.txt --force   # перезаписать существующие
"""

from __future__ import annotations

import argparse
import csv
import secrets
import string
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt as _bcrypt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Company, SessionLocal, create_tables
from app.parser import (
    parse_gallery, parse_hours, parse_news,
    parse_social_links, parse_status, slugify,
)


ALPHABET = string.ascii_letters + string.digits


def generate_password(length: int = 12) -> str:
    """Генерирует читаемый случайный пароль."""
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))


def make_unique_slug(base: str, db: Session) -> str:
    """Если slug занят — добавляет числовой суффикс."""
    candidate = base
    counter = 2
    while db.query(Company).filter(Company.slug == candidate).first():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def import_row(row: dict, db: Session, force: bool) -> tuple[str, str, str]:
    """
    Импортирует одну строку CSV.
    Возвращает (slug, password, action) где action: 'created' | 'updated' | 'skipped'
    """
    title   = row.get("title", "").strip()
    website = row.get("website", "").strip()

    if not title:
        return ("", "", "skipped")

    # Пропускаем компании с собственным сайтом
    if website:
        return ("", "", "skipped")

    base_slug = slugify(title)
    existing  = db.query(Company).filter(Company.slug == base_slug).first()

    if existing and not force:
        return (existing.slug, "", "skipped")

    password      = generate_password()
    password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

    hours_raw  = row.get("hours", "")
    hours_data = parse_hours(hours_raw)
    status     = parse_status(hours_raw)

    gallery    = parse_gallery(row.get("gallery_photos", ""))
    socials    = parse_social_links(row.get("social_links", ""))
    news       = parse_news(row.get("latest_news", ""))

    if existing and force:
        # Обновляем данные, пересоздаём пароль
        existing.title           = title
        existing.address         = row.get("address", "").strip()
        existing.phone           = row.get("phone", "").strip()
        existing.rating          = row.get("rating", "").strip()
        existing.category        = row.get("categories", "Организация").strip() or "Организация"
        existing.coordinates     = row.get("coordinates", "").strip()
        existing.yandex_url      = row.get("url", "").strip()
        existing.hours           = hours_data
        existing.gallery_photos  = gallery
        existing.social_links    = socials
        existing.latest_news     = news
        existing.admin_password_hash = password_hash
        db.commit()
        return (existing.slug, password, "updated")

    # Создаём новую компанию
    slug = make_unique_slug(base_slug, db)
    company = Company(
        slug                = slug,
        title               = title,
        address             = row.get("address", "").strip(),
        phone               = row.get("phone", "").strip(),
        rating              = row.get("rating", "").strip(),
        category            = row.get("categories", "Организация").strip() or "Организация",
        coordinates         = row.get("coordinates", "").strip(),
        yandex_url          = row.get("url", "").strip(),
        admin_password_hash = password_hash,
    )
    company.hours          = hours_data
    company.gallery_photos = gallery
    company.social_links   = socials
    company.latest_news    = news

    db.add(company)
    db.commit()
    return (slug, password, "created")


def main():
    parser = argparse.ArgumentParser(
        description="Импорт компаний из CSV Яндекс Карт в базу данных"
    )
    parser.add_argument("csv_file", help="Путь к CSV-файлу")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Перезаписать данные и пароли для существующих компаний"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"[ERROR] Файл не найден: {csv_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Импорт CSV → база данных uqqi.ru")
    print(f"{'='*60}")
    print(f"  Файл    : {csv_path.resolve()}")
    print(f"  Домен   : {settings.BASE_DOMAIN}")
    print(f"  Режим   : {'перезапись' if args.force else 'только новые'}")
    print(f"{'='*60}\n")

    # Инициализируем БД
    create_tables()

    rows: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"[INFO] Строк в CSV: {len(rows)}")

    db = SessionLocal()
    created, updated, skipped = [], [], []

    try:
        for i, row in enumerate(rows, 1):
            title   = row.get("title", "").strip() or f"row_{i}"
            website = row.get("website", "").strip()

            print(f"[{i:02d}/{len(rows):02d}] {title}")

            if website:
                print(f"         ├ сайт уже есть: {website[:60]}")
                print(f"         └ [SKIP] пропускаем\n")
                skipped.append(title)
                continue

            slug, password, action = import_row(row, db, args.force)

            if action == "skipped":
                print(f"         └ [SKIP] уже в БД (используйте --force)\n")
                skipped.append(title)
                continue

            subdomain = f"https://{slug}.{settings.BASE_DOMAIN}"
            admin_url = f"{subdomain}/admin"

            print(f"         ├ адрес   : {row.get('address','—')[:55]}")
            print(f"         ├ телефон : {row.get('phone','—')}")
            print(f"         ├ фото    : {len(parse_gallery(row.get('gallery_photos','')))} шт.")
            print(f"         ├ соцсети : {len(parse_social_links(row.get('social_links','')))} шт.")
            print(f"         ├ сайт    : {subdomain}")
            print(f"         ├ панель  : {admin_url}")

            if action == "created":
                print(f"         ├ пароль  : {password}   ← сохраните!")
                print(f"         └ [СОЗДАН]\n")
                created.append((title, slug, password, subdomain))
            else:
                print(f"         ├ пароль  : {password}   ← НОВЫЙ, старый не работает")
                print(f"         └ [ОБНОВЛЁН]\n")
                updated.append((title, slug, password, subdomain))

    finally:
        db.close()

    # ── Итог ────────────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"  ИТОГ")
    print(f"{'='*60}")
    print(f"  ✔  Создано    : {len(created)}")
    print(f"  ↺  Обновлено  : {len(updated)}")
    print(f"  ⊘  Пропущено  : {len(skipped)}")

    all_active = created + updated
    if all_active:
        print(f"\n  {'─'*56}")
        print(f"  {'КОМПАНИЯ':<28} {'ПАРОЛЬ':<14} САЙТ")
        print(f"  {'─'*56}")
        for title, slug, password, subdomain in all_active:
            short_title = title[:26] + ".." if len(title) > 26 else title
            print(f"  {short_title:<28} {password:<14} {subdomain}")
        print(f"  {'─'*56}")
        print(f"\n  Панель редактирования: <сайт>/admin")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
