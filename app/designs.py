"""
app/designs.py — реестр дизайнов витрин (единый источник истины).

Бесплатные: A, B (templates/site_a.html / site_b.html). Премиум (Pro) —
курируемые из загруженных дизайнов, живут в templates/designs/<key>.html.
Ключ дизайна хранится в Company.template_variant.

Поэтапный выкат: у премиума enabled=False, пока он НЕ адаптирован в Jinja —
такой дизайн не показывается в пикере, а рендер падает на бесплатный A
(template_for вернёт None). Как адаптирую дизайн — ставлю enabled=True.

self_mobile=True у премиума → у него свой адаптив, поэтому на мобильном НЕ
форсим site_c.html (в отличие от бесплатных A/B).
"""

from __future__ import annotations

from pathlib import Path

_TPL_DIR = Path(__file__).resolve().parent.parent / "templates"

# key → метаданные. src — исходный загруженный файл (для адаптации), не для рантайма.
DESIGNS: dict[str, dict] = {
    "A": {"name": "Базовый",  "template": "site_a.html", "tier": "free",
          "self_mobile": False, "enabled": True},
    "B": {"name": "Базовый+", "template": "site_b.html", "tier": "free",
          "self_mobile": False, "enabled": True},

    # ── Премиум (Pro) — курируемые. enabled ставится при адаптации в Jinja. ──
    "noir": {"name": "Noir", "src": "design_p2.html", "template": "designs/noir.html",
             "tier": "pro", "self_mobile": True, "enabled": True,
             "vibe": "Тёмный кинематографичный, золотой акцент",
             "fit": "детейлинг, барбершоп, тату, авто, бары, залы"},
    "editorial": {"name": "Editorial", "src": "design_p10.html", "template": "designs/editorial.html",
                  "tier": "pro", "self_mobile": True, "enabled": True,
                  "vibe": "Светлый журнальный, антиква",
                  "fit": "рестораны, кафе, салоны, флористы"},
    "bloom": {"name": "Bloom", "src": "design_p3.html", "template": "designs/bloom.html",
              "tier": "pro", "self_mobile": True, "enabled": True,
              "vibe": "Светлый мягкий, тёплый",
              "fit": "красота, велнес, студии, детское"},
    "clarity": {"name": "Clarity", "src": "design_p11.html", "template": "designs/clarity.html",
                "tier": "pro", "self_mobile": True, "enabled": True,
                "vibe": "Светлый чистый, холодный",
                "fit": "стоматология, оптика, клиники, услуги"},
    "garage": {"name": "Garage", "src": "design_p8.html", "template": "designs/garage.html",
               "tier": "pro", "self_mobile": True, "enabled": True,
               "vibe": "Технический моно",
               "fit": "авто, ремонт, промышленное, IT"},
    "atelier": {"name": "Atelier", "src": "design_p21.html", "template": "designs/atelier.html",
                "tier": "pro", "self_mobile": True, "enabled": True,
                "vibe": "Тёмный артовый",
                "fit": "фото, дизайн, креатив, ивенты"},
    "hearth": {"name": "Hearth", "src": "design_p4.html", "template": "designs/hearth.html",
               "tier": "pro", "self_mobile": True, "enabled": True,
               "vibe": "Тёплый уютный",
               "fit": "пекарни, еда, кафе, магазины"},
    "forge": {"name": "Forge", "src": "design_p14.html", "template": "designs/forge.html",
              "tier": "pro", "self_mobile": True, "enabled": True,
              "vibe": "Тёмный жёсткий",
              "fit": "залы, кроссфит, спорт"},
}

FREE_DEFAULT = "A"


def get(key: str | None) -> dict | None:
    return DESIGNS.get((key or "").strip())


def exists(key: str | None) -> bool:
    return (key or "").strip() in DESIGNS


def is_pro(key: str | None) -> bool:
    d = get(key)
    return bool(d and d.get("tier") == "pro")


def self_mobile(key: str | None) -> bool:
    d = get(key)
    return bool(d and d.get("self_mobile"))


def template_for(key: str | None) -> str | None:
    """
    Файл шаблона по ключу — только если дизайн включён И файл существует.
    Иначе None (вызывающий делает фолбэк на бесплатный). Защищает от выбора
    ещё не адаптированного премиума.
    """
    d = get(key)
    if not d or not d.get("enabled"):
        return None
    tpl = d.get("template") or ""
    if not tpl or not (_TPL_DIR / tpl).exists():
        return None
    return tpl


def public_list(include_free: bool = True) -> list[dict]:
    """Для API/пикера: только включённые дизайны (без src/шаблонов внутрь не отдаём)."""
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
