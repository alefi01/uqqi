# ============================================================
# clean_logo_from_galleries.py — разовая чистка: убирает логотип организации
# из gallery_photos существующих сайтов (лого попадало в галерею и hero,
# фикс парсера защищает только новые сборки).
#
# Запуск:
#   venv/bin/python scripts/clean_logo_from_galleries.py           # dry-run, только показывает
#   venv/bin/python scripts/clean_logo_from_galleries.py --apply   # реально пишет в БД
#
# Идемпотентен — повторный запуск ничего не ломает.
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yandex_maps_parser import photo_base
from app.models import SessionLocal, Company


def clean(apply: bool) -> None:
    db = SessionLocal()
    changed = 0
    try:
        for c in db.query(Company).all():
            photos = c.gallery_photos or []
            if not photos:
                continue
            logo_base = photo_base(c.logo_url) if c.logo_url else None
            cleaned = [
                p for p in photos
                if 'priority-headline-logo' not in p
                and (not logo_base or photo_base(p) != logo_base)
            ]
            if cleaned == photos:
                continue
            changed += 1
            removed = [p for p in photos if p not in cleaned]
            print(f"[{'CLEAN' if apply else 'DRY'}] {c.slug} (id={c.id}): "
                  f"{len(photos)} → {len(cleaned)} фото, убрано:")
            for p in removed:
                print(f"    {p}")
            if apply:
                c.gallery_photos = cleaned
        if apply:
            db.commit()
            print(f"\nГотово: почищено сайтов — {changed}")
        else:
            print(f"\nDry-run: было бы почищено сайтов — {changed}. "
                  f"Для записи запустите с --apply")
    finally:
        db.close()


if __name__ == "__main__":
    clean(apply="--apply" in sys.argv)
