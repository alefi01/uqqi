"""
app/parser.py — разбор полей из CSV Яндекс Карт в структуры для БД
"""

from __future__ import annotations

import re
import unicodedata


DAY_RU = {
    "Mo": "Пн", "Tu": "Вт", "We": "Ср",
    "Th": "Чт", "Fr": "Пт", "Sa": "Сб", "Su": "Вс",
}

SOCIAL_PLATFORMS = {
    "t.me":      "telegram",
    "vk.com":    "vk",
    "wa.me":     "whatsapp",
    "viber":     "viber",
    "instagram": "instagram",
    "youtube":   "youtube",
    "max.ru":    "max",
}

SOCIAL_LABELS = {
    "telegram":  "Telegram",
    "vk":        "ВКонтакте",
    "whatsapp":  "WhatsApp",
    "viber":     "Viber",
    "instagram": "Instagram",
    "youtube":   "YouTube",
    "max":       "Max",
}


_TRANSLIT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
    'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
}


def slugify(name: str) -> str:
    """
    Латинский slug для домена (транслитерация кириллицы).
    На iPhone/Safari кириллица в поддоменах не работает, поэтому только латиница.
    Примеры: «Кафе Пушкинъ» → 'kafe-pushkin', «Форсаж 24» → 'forsazh-24',
             «Winx» → 'winx', «Бритва & Co» → 'britva-i-co'.
    """
    s = name.lower().strip()
    s = s.replace('&', ' и ')
    # Транслитерация кириллицы
    out = []
    for ch in s:
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        else:
            out.append(ch)
    s = ''.join(out)
    # Оставляем только латиницу, цифры, пробел, дефис
    s = re.sub(r'[^a-z0-9\s\-]+', '', s)
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or "company"


def slug_to_punycode(slug: str) -> str:
    """Slug теперь всегда латинский — punycode не нужен, возвращаем как есть."""
    return slug


def parse_pipe(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    return [v.strip() for v in value.split('|') if v.strip()]


def parse_hours(hours_str: str) -> list[dict]:
    """
    'Открыто до 23:00 | Mo 08:00-23:00 | Tu 08:00-23:00 | ...'
    → [{"day": "Mo", "day_ru": "Пн", "time": "08:00-23:00", "closed": False}, ...]
    """
    parts = parse_pipe(hours_str)
    result = []
    for part in parts:
        m = re.match(r'^(Mo|Tu|We|Th|Fr|Sa|Su)\s+(.+)$', part)
        if m:
            result.append({
                "day":     m.group(1),
                "day_ru":  DAY_RU.get(m.group(1), m.group(1)),
                "time":    m.group(2),
                "closed":  False,
            })
    # Если расписание не найдено — возвращаем пустой шаблон на все дни
    if not result:
        return [
            {"day": d, "day_ru": DAY_RU[d], "time": "", "closed": True}
            for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        ]
    return result


def parse_status(hours_str: str) -> str:
    """Извлекает текст статуса ('Открыто до 23:00') из строки часов."""
    parts = parse_pipe(hours_str)
    for part in parts:
        if not re.match(r'^(Mo|Tu|We|Th|Fr|Sa|Su)\s', part):
            return part
    return ""


def parse_gallery(photos_str: str) -> list[str]:
    return parse_pipe(photos_str)[:15]  # до 15 фото


def parse_social_links(social_str: str) -> list[dict]:
    """
    'https://t.me/foo | https://vk.com/bar | ...'
    → [{"platform": "telegram", "label": "Telegram", "url": "..."}, ...]
    """
    urls = parse_pipe(social_str)
    result = []
    seen_platforms = set()

    for url in urls:
        # Пропускаем слишком длинные (UTM-ссылки WhatsApp/Viber с мусором)
        if len(url) > 250:
            continue
        platform = "other"
        for key, name in SOCIAL_PLATFORMS.items():
            if key in url:
                platform = name
                break
        # Не дублируем платформы
        if platform in seen_platforms:
            continue
        seen_platforms.add(platform)
        result.append({
            "platform": platform,
            "label":    SOCIAL_LABELS.get(platform, platform.capitalize()),
            "url":      url,
        })
    return result


def parse_news(news_str: str) -> list[dict]:
    """
    '10 ИЮНЯ, 05:55 - Текст... - https://img.url'
    → [{"date": "...", "text": "...", "image_url": "..."}, ...]
    """
    items = parse_pipe(news_str)
    result = []
    for item in items:
        m = re.match(r'^(.+?)\s*-\s*(.+?)\s*-\s*(https?://\S+)$', item.strip(), re.DOTALL)
        if m:
            result.append({
                "date":      m.group(1).strip(),
                "text":      m.group(2).strip(),
                "image_url": m.group(3).strip(),
            })
    return result


def parse_features(features_str: str) -> list[str]:
    """'Wi-Fi | Доставка | ...' → ['Wi-Fi', 'Доставка', ...]"""
    return parse_pipe(features_str)


def parse_menu_items(menu_str: str) -> list[dict]:
    """JSON-строка или пустая строка → список."""
    if not menu_str or not menu_str.strip():
        return []
    try:
        import json
        data = json.loads(menu_str)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _shorten_author(name: str) -> str:
    """
    Сокращает имя автора отзыва для приватности (152-ФЗ):
    «Александр Петров» → «Александр П.», «Иван» → «Иван».
    """
    name = (name or "").strip()
    if not name:
        return "Гость"
    parts = name.split()
    if len(parts) >= 2 and parts[1]:
        return f"{parts[0]} {parts[1][0].upper()}."
    return parts[0]


def parse_reviews(reviews_str: str) -> list[dict]:
    """JSON-строка → список отзывов. Имена авторов сокращаются для приватности."""
    if not reviews_str or not reviews_str.strip():
        return []
    try:
        import json
        data = json.loads(reviews_str)
        if isinstance(data, list):
            for r in data:
                if isinstance(r, dict):
                    r["author"] = _shorten_author(r.get("author", ""))
                    # Аватар убираем — это тоже персональные данные
                    r["avatar"] = ""
            return data
    except Exception:
        pass
    return []
