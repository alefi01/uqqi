#!/usr/bin/env python3
"""Рендер витрин на тестовых данных — вход для дизайн-гейтов.

Шаблоны витрин (templates/site_a|b|c.html и templates/designs/*.html) — Jinja2
на контексте из app.main._build_site_context. Чтобы прогонять по ним гейты кита
(measure_render, verify_states, verify_responsive, taste_audit…), нужен готовый
HTML. Скрипт подставляет фикстуру и складывает результат в отдельную папку.

  python3 scripts/render_designs.py                 # все включённые дизайны
  python3 scripts/render_designs.py noir garage     # только эти ключи
  python3 scripts/render_designs.py --out /tmp/x    # другая папка
  python3 scripts/render_designs.py --empty         # фикстура «пустая карточка»
                                                    # (нет фото, меню, отзывов)

Фикстура намеренно кривая: длинное название, позиции без фото и без цены,
отзыв без автора — краевые случаи должны схлопываться красиво, а не ломать вёрстку.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class Obj(dict):
    """Словарь с доступом через точку — заменяет ORM-объект в шаблоне."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None


# Локальная картинка-заглушка: гейты не должны зависеть от сети.
PHOTO = ("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='900'%3E"
         "%3Crect width='1200' height='900' fill='%23555a5f'/%3E%3C/svg%3E")


def fixture(empty: bool = False) -> Obj:
    if empty:
        return Obj(
            title="Мастерская «Ключи и обувь» на Большой Академической",
            category="Ремонт обуви", slug="demo", about_text=None, catalog_title=None,
            address="Москва, Большая Академическая ул., 77к2", phone="+7 (900) 000-00-00",
            book_url=None, avg_bill=None, rating=None, reviews_count=0, logo_url=None,
            coordinates="55.75,37.61", yandex_url="https://yandex.ru/maps/org/12345/",
            gallery_photos=[], menu_items=[], reviews=[], hours=[], features=[],
            social_links=[], transit_stop=None,
        )
    return Obj(
        title="Шиномонтаж и автосервис «Колесо»",
        category="Шиномонтаж, автосервис",
        slug="demo",
        about_text=("Работаем с 2012 года. Балансировка, ремонт проколов, сезонное "
                    "хранение резины. Записываться не нужно: приезжайте, очередь видно на месте."),
        catalog_title="Услуги и цены",
        address="Москва, Дмитровское шоссе, 71к1",
        phone="+7 (900) 123-45-67",
        book_url="https://example.com/book",
        avg_bill="от 1 500 ₽",
        rating=4.8,
        reviews_count=214,
        logo_url=PHOTO,
        coordinates="55.75,37.61",
        yandex_url="https://yandex.ru/maps/org/12345/",
        gallery_photos=[PHOTO] * 7,
        menu_items=[
            Obj(name="Шиномонтаж R13-R16", description="Снятие, монтаж, балансировка, четыре колеса",
                price="2 400 ₽", image_url=PHOTO),
            Obj(name="Ремонт прокола жгутом", description=None, price="600 ₽", image_url=None),
            Obj(name="Сезонное хранение комплекта резины",
                description="Отапливаемый склад, страховка включена", price="3 900 ₽ за сезон", image_url=PHOTO),
            Obj(name="Замена масла и фильтра", description="Масло клиента или наше", price="от 1 200 ₽", image_url=PHOTO),
            Obj(name="Диагностика подвески", description=None, price=None, image_url=None),
            Obj(name="Правка литых дисков", description="Прокатка на станке", price="от 2 000 ₽", image_url=PHOTO),
            Obj(name="Мойка колёс перед хранением", description=None, price="400 ₽", image_url=None),
            Obj(name="Установка датчиков давления", description="TPMS, программирование",
                price="1 800 ₽", image_url=PHOTO),
        ],
        reviews=[
            Obj(rating=5, text="Приехал без записи, сделали за сорок минут. Цену назвали сразу и не поменяли.",
                author="Игорь", date="12 августа"),
            Obj(rating=5, text="Храню резину третий сезон. Привозят к подъезду, это удобно.",
                author=None, date="3 июля"),
            Obj(rating=4, text="Очередь была, но предупредили честно, что ждать сорок минут.",
                author="Марина", date="28 июня"),
            Obj(rating=5, text="Единственные в районе, кто взялся править литой диск.",
                author="Сергей", date="14 июня"),
        ],
        hours=[
            Obj(day="Mo", day_ru="Понедельник", closed=False, time="09:00 – 21:00"),
            Obj(day="Tu", day_ru="Вторник", closed=False, time="09:00 – 21:00"),
            Obj(day="We", day_ru="Среда", closed=False, time="09:00 – 21:00"),
            Obj(day="Th", day_ru="Четверг", closed=False, time="09:00 – 21:00"),
            Obj(day="Fr", day_ru="Пятница", closed=False, time="09:00 – 21:00"),
            Obj(day="Sa", day_ru="Суббота", closed=False, time="10:00 – 18:00"),
            Obj(day="Su", day_ru="Воскресенье", closed=True, time=""),
        ],
        features=["Оплата картой", "Своя парковка", "Кофе, пока ждёте", "Гарантия на работы"],
        social_links=[Obj(platform="telegram", url="https://t.me/example"),
                      Obj(platform="vk", url="https://vk.com/example")],
        transit_stop=Obj(name="Дмитровская", distance="700 м"),
    )


def build_context(company: Obj) -> dict:
    return {
        "request": None,
        "company": company,
        "status": "Открыто до 21:00",
        "status_short": "Открыто",
        "yandex_map_url": "https://yandex.ru/map-widget/v1/org/12345/?z=16",
        "route_url": "https://yandex.ru/maps/?mode=routes",
        "feat_icon": lambda name: "check",
        "site_url": "https://demo.uqqi.ru/",
        "seo_noindex": True,
        "is_claim_site": False,
        "chat_enabled": False,
        "unpaid_overlay": False,
        # Виджет записи должен попадать под гейты, поэтому в фикстуре режим
        # «наши слоты». У пустой карточки записи нет — проверяем и этот случай.
        "book_mode": "off" if not company.book_url else "slots",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*", help="ключи дизайнов (по умолчанию — все включённые)")
    ap.add_argument("--out", default=str(ROOT / ".design-gate"), help="куда складывать HTML")
    ap.add_argument("--empty", action="store_true", help="фикстура «пустая карточка»")
    args = ap.parse_args(argv)

    from app import designs as design_registry

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                      autoescape=select_autoescape(["html"]))
    company = fixture(empty=args.empty)
    ctx = build_context(company)

    keys = args.keys or [d["key"] for d in design_registry.public_list()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for key in keys:
        tpl_name = design_registry.template_for(key)
        if not tpl_name:
            print(f"SKIP {key}: шаблона нет или дизайн выключен")
            continue
        try:
            html = env.get_template(tpl_name).render(**ctx)
        except Exception as exc:                      # noqa: BLE001 — отчёт, не падение
            print(f"FAIL {key}: {type(exc).__name__}: {exc}")
            failed.append(key)
            continue
        path = out_dir / f"{key}.html"
        path.write_text(html, encoding="utf-8")
        print(f"OK   {key} -> {path} ({len(html) // 1024} КБ)")

    if failed:
        print(f"\n{len(failed)} шаблон(ов) не отрендерились: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
