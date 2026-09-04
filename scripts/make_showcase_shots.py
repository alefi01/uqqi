#!/usr/bin/env python3
"""
make_showcase_shots.py — кадры клиентских сайтов для ленты «Работы» на главной.

Живые iframe в ленте не годятся: шесть чужих origin на первом же экране
тормозят страницу, а контейнерный Chromium их вообще не рисует — проверить
глазами нельзя. Поэтому снимаем статические кадры заранее и кладём манифест,
который читает app.main._landing_works().

Фильтр тот же, что у /api/showcase-site: собран, включён, легитимный, с фото.
Обезличенные claim-сайты в витрину не попадают — это чужой бизнес без его
ведома.

    python3 scripts/make_showcase_shots.py            # до 8 случайных сайтов
    python3 scripts/make_showcase_shots.py --limit 12
    python3 scripts/make_showcase_shots.py --slugs boroda,motor
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func                                  # noqa: E402
from app.config import settings                              # noqa: E402
from app.designs import DESIGNS                              # noqa: E402
from app.main import is_legit                                # noqa: E402
from app.models import Company, SessionLocal                 # noqa: E402

OUT_DIR = "static/showcase"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
SHOT_W, SHOT_H = 1280, 800
# Три кадра: первый экран, середина (каталог), низ (отзывы и контакты).
SCROLL_POINTS = (0.0, 0.42, 0.78)


def _city(address: str) -> str:
    return (address or "").split(",")[-1].strip()


def _design_name(key: str) -> str:
    d = DESIGNS.get((key or "").strip())
    return d.get("name", "") if isinstance(d, dict) else ""


def pick(limit: int, slugs: list[str]) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(Company).filter(
            Company.is_active.is_(True),
            Company.build_status == "ready",
        )
        if slugs:
            q = q.filter(Company.slug.in_(slugs))
        else:
            q = q.order_by(func.random())
        out = []
        for c in q.limit(max(limit * 4, limit)).all():
            if not is_legit(c) or not c.gallery_photos:
                continue
            out.append({
                "slug": c.slug,
                "title": c.title or c.slug,
                "city": _city(c.address),
                "design_name": _design_name(c.template_variant),
                "year": (c.created_at or datetime.utcnow()).strftime("%Y"),
            })
            if len(out) >= limit:
                break
        return out
    finally:
        db.close()


async def shoot(items: list[dict]) -> list[dict]:
    from playwright.async_api import async_playwright

    os.makedirs(OUT_DIR, exist_ok=True)
    done = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": SHOT_W, "height": SHOT_H},
                                      device_scale_factor=1)
        for it in items:
            url = f"https://{it['slug']}.{settings.BASE_DOMAIN}/"
            shots = []
            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
                for i, frac in enumerate(SCROLL_POINTS, start=1):
                    await page.evaluate(
                        "f => scrollTo(0, (document.body.scrollHeight - innerHeight) * f)", frac)
                    await page.wait_for_timeout(700)
                    rel = f"{it['slug']}-{i}.jpg"
                    await page.screenshot(path=os.path.join(OUT_DIR, rel),
                                          type="jpeg", quality=82)
                    shots.append(f"/{OUT_DIR}/{rel}")
            except Exception as e:                       # сайт мог не ответить
                print(f"[skip] {it['slug']}: {type(e).__name__}: {e}")
                continue
            it["shots"] = shots
            done.append(it)
            print(f"[ok] {it['slug']} — {len(shots)} кадра")
        await browser.close()
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--slugs", default="")
    args = ap.parse_args()

    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    items = pick(args.limit, slugs)
    if not items:
        print("Подходящих сайтов нет: нужен собранный, включённый, легитимный "
              "сайт с фотографиями. Манифест не тронут.")
        return 1

    done = asyncio.run(shoot(items))
    if not done:
        print("Ни один сайт не сняли, манифест не тронут.")
        return 1

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(done, fh, ensure_ascii=False, indent=2)
    print(f"Готово: {len(done)} работ → {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
