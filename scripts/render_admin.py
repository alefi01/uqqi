"""Рендер редактора контента (admin_panel.html) для гейтов и просмотра глазами.

Редактор открывается только за сессией клиента, поэтому гейтам его не достать.
Скрипт подставляет карточку-фикстуру и кладёт .design-gate/admin.html.

    python3 scripts/render_admin.py
    node scripts/measure_render.mjs .design-gate/admin.html
"""
import os
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".design-gate")

company = SimpleNamespace(
    title="Шиномонтаж и автосервис «Колесо»", slug="koleso",
    address="Москва, Дмитровское шоссе, 71к1", phone="+7 900 123-45-67",
    description="Меняем резину, правим диски, ремонтируем ходовую.",
    org_name="", org_type="ooo", org_inn="",
    book_url="", booking_mode="slots",
    # график пуст — именно этот случай ломал редактирование времени
    booking={"tz": 3, "duration": 60, "lead_hours": 2, "days_ahead": 14,
             "services": ["Шиномонтаж", "Развал-схождение"], "week": {},
             "multi": True,
             "masters": [{"name": "Иван"},
                         {"name": "Пётр", "week": {"1": [["11:00", "18:00"]]}}]},
    hours=[], gallery_photos=[], menu_items=[], social_links=[],
)

env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")),
                  autoescape=select_autoescape(["html"]))
html = env.get_template("admin_panel.html").render(
    company=company, saved=False, error="", photos=[], items=[],
    hours_rows=[], days=[], can_edit=True,
)
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "admin.html")
open(path, "w", encoding="utf-8").write(html.replace('/static/', f'{ROOT}/static/'))
print("rendered", path)
