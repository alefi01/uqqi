"""
app/designs.py — реестр оформлений витрин (единый источник истины).

Бесплатные: A, B (templates/site_a.html / site_b.html).
Премиум (Pro) — десять оформлений под реальные ниши наших клиентов, живут в
templates/designs/<key>.html. Ключ хранится в Company.template_variant.

Каждый премиум — Jinja2 на том же контексте, что site_a (см.
main._build_site_context), и обязан подключать слоты _seo_meta / _claim_disclaimer
/ _chat_widget и общий скрипт _design_js.

Поэтапный выкат: у премиума enabled=False, пока он не готов — template_for
вернёт None, и рендер упадёт на бесплатный A, а пикер его не покажет.

self_mobile=True у ВСЕХ двенадцати: у каждого оформления своя мобильная
вёрстка, подмены шаблона по User-Agent больше нет (один адрес — один HTML).

Проверка всех оформлений на тестовых данных: python3 scripts/render_designs.py
"""

from __future__ import annotations

from pathlib import Path

_TPL_DIR = Path(__file__).resolve().parent.parent / "templates"

# key → метаданные. fit — для кого; vibe — как выглядит (показываются в пикере ЛК).
DESIGNS: dict[str, dict] = {
    "A": {"name": "Базовый",  "template": "site_a.html", "tier": "free",
          "self_mobile": True, "enabled": True,
          "vibe": "Светлый универсальный", "fit": "подходит любому делу"},
    "B": {"name": "Базовый+", "template": "site_b.html", "tier": "free",
          "self_mobile": True, "enabled": True,
          "vibe": "Светлый с крупным фото", "fit": "подходит любому делу"},

    # ── Премиум (Pro). Десять направлений под наши основные ниши. ──
    "garage": {"name": "Garage", "template": "designs/garage.html",
               "tier": "pro", "self_mobile": True, "enabled": True,
               "vibe": "Тёмный технический, крупный прайс",
               "fit": "автосервисы, шиномонтажи, автомойки"},
    "craft": {"name": "Craft", "template": "designs/craft.html",
              "tier": "pro", "self_mobile": True, "enabled": True,
              "vibe": "Деловой светлый, синий акцент",
              "fit": "бригады, мастер на час, окна, отделка"},
    "atelier": {"name": "Atelier", "template": "designs/atelier.html",
                "tier": "pro", "self_mobile": True, "enabled": True,
                "vibe": "Светлая мастерская, нумерованный прайс",
                "fit": "ремонт обуви, ключи, ателье, химчистки"},
    "barber": {"name": "Barber", "template": "designs/barber.html",
               "tier": "pro", "self_mobile": True, "enabled": True,
               "vibe": "Тёмный кинематографичный, латунь",
               "fit": "барбершопы, парикмахерские, тату"},
    "bloom": {"name": "Bloom", "template": "designs/bloom.html",
              "tier": "pro", "self_mobile": True, "enabled": True,
              "vibe": "Мягкий светлый, скруглённые карточки",
              "fit": "маникюр, косметологи, массаж, студии"},
    "bouquet": {"name": "Bouquet", "template": "designs/bouquet.html",
                "tier": "pro", "self_mobile": True, "enabled": True,
                "vibe": "Журнальный, крупные фото и антиква",
                "fit": "цветочные, декор, подарки"},
    "market": {"name": "Market", "template": "designs/market.html",
               "tier": "pro", "self_mobile": True, "enabled": True,
               "vibe": "Свежий светлый, товары с ценниками",
               "fit": "продукты, фермерское, зоомагазины"},
    "patisserie": {"name": "Patisserie", "template": "designs/patisserie.html",
                   "tier": "pro", "self_mobile": True, "enabled": True,
                   "vibe": "Тёплый кремовый, меню в две колонки",
                   "fit": "кондитерские, пекарни, десерты"},
    "roast": {"name": "Roast", "template": "designs/roast.html",
              "tier": "pro", "self_mobile": True, "enabled": True,
              "vibe": "Тёмный эспрессо, фото на весь экран",
              "fit": "кофейни, чайные, кофе навынос"},
    "streetfood": {"name": "Streetfood", "template": "designs/streetfood.html",
                   "tier": "pro", "self_mobile": True, "enabled": True,
                   "vibe": "Контрастный уличный, крупные цены",
                   "fit": "шаурма, бургеры, стрит-фуд, пивные"},
}

# Оформления первого набора (2026-07), заменённые новыми в 2026-09.
# У части клиентов ключ уже записан в БД, поэтому не роняем их в базовый A,
# а показываем ближайшее по духу новое оформление.
LEGACY_ALIASES: dict[str, str] = {
    "noir": "barber",
    "editorial": "bouquet",
    "clarity": "craft",
    "hearth": "patisserie",
    "forge": "garage",
    # «C» — бывшая отдельная мобильная витрина. Оформлений двенадцать, и у
    # каждого свой адаптив, так что отдельной мобильной версии нет; ключ
    # остаётся только ради тех, у кого он ещё записан в template_variant.
    "C": "A",
}

FREE_DEFAULT = "A"


def resolve(key: str | None) -> str:
    """Ключ с учётом переименований старого набора."""
    k = (key or "").strip()
    return LEGACY_ALIASES.get(k, k)


def get(key: str | None) -> dict | None:
    return DESIGNS.get(resolve(key))


def exists(key: str | None) -> bool:
    return resolve(key) in DESIGNS


def is_pro(key: str | None) -> bool:
    d = get(key)
    return bool(d and d.get("tier") == "pro")


def self_mobile(key: str | None) -> bool:
    d = get(key)
    return bool(d and d.get("self_mobile"))


def template_for(key: str | None) -> str | None:
    """
    Файл шаблона по ключу — только если оформление включено И файл существует.
    Иначе None (вызывающий делает фолбэк на бесплатный). Защищает от выбора
    ещё не адаптированного премиума и от ключей удалённых оформлений.
    """
    d = get(key)
    if not d or not d.get("enabled"):
        return None
    tpl = d.get("template") or ""
    if not tpl or not (_TPL_DIR / tpl).exists():
        return None
    return tpl


def public_list(include_free: bool = True) -> list[dict]:
    """Для API/пикера: только включённые оформления (шаблоны наружу не отдаём).

    preview/poster остались для совместимости с фронтом: карточка сначала пробует
    живой предпросмотр сайта клиента, а эти файлы — необязательный запасной
    вариант, если владелец их запишет.
    """
    out = []
    for key, d in DESIGNS.items():
        if not d.get("enabled"):
            continue
        if d["tier"] == "free" and not include_free:
            continue
        out.append({
            "key":     key,
            "name":    d["name"],
            "tier":    d["tier"],
            "vibe":    d.get("vibe", ""),
            "fit":     d.get("fit", ""),
            "preview": f"/static/designs/{key}.mp4" if d["tier"] == "pro" else "",
            "poster":  f"/static/designs/{key}.jpg" if d["tier"] == "pro" else "",
        })
    return out
