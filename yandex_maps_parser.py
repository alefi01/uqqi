#!/usr/bin/env python3
"""
Yandex Maps terminal parser.

This script uses Playwright to open the regular Yandex Maps website, scroll
search results, open business cards, and export collected data to CSV or JSON.

All source-code strings are intentionally in English to avoid terminal encoding
issues on mixed Windows/Linux environments. Search queries may still be typed in
any language, for example: python yandex_maps_parser.py "coffee Moscow".
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
import sys
import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus, urljoin, urlsplit, urlunsplit


YANDEX_MAPS_URL = "https://yandex.ru/maps/?text={query}"

CARD_SELECTORS = [
    ".search-snippet-view",
    ".business-snippet-view",
    "[class*='search-snippet']",
    "[class*='business-snippet']",
]

TITLE_SELECTORS = [
    ".search-business-snippet-view__title",
    ".search-snippet-view__title",
    ".business-snippet-view__title",
    "[class*='snippet-view__title']",
    "[class*='business-snippet-view__title']",
]

ADDRESS_SELECTORS = [
    ".search-business-snippet-view__address",
    ".search-snippet-view__address",
    ".business-snippet-view__address",
    "[class*='snippet-view__address']",
    "[class*='business-snippet-view__address']",
]

RATING_SELECTORS = [
    ".business-rating-badge-view__rating-text",
    "[class*='rating-badge-view__rating']",
    "[class*='business-rating']",
]

DETAIL_TITLE_SELECTORS = [
    ".business-card-title-view__title",
    "h1",
    "[class*='card-title-view__title']",
]

DETAIL_ADDRESS_SELECTORS = [
    ".business-contacts-view__address",
    ".business-card-summary-view__address",
    "[class*='contacts-view__address']",
    "[class*='summary-view__address']",
]

DETAIL_PHONE_SELECTORS = [
    ".card-phones-view__phone-number",
    ".business-contacts-view__phone",
    "[class*='phone-number']",
    "[class*='contacts-view__phone']",
]

DETAIL_SITE_SELECTORS = [
    ".business-urls-view__text",
    ".business-contacts-view__website",
    ".business-urls-view__link",
    "a[itemprop='url']",
    "a[href^='http']:not([href*='yandex'])",
]

DETAIL_HOURS_SELECTORS = [
    ".business-working-status-view",
    ".business-card-working-status-view",
    "[class*='working-status']",
]

DETAIL_CATEGORY_SELECTORS = [
    ".business-card-title-view__categories",
    ".business-card-title-view__category",
    "[class*='title-view__categor']",
]

DETAIL_SOCIAL_LINK_SELECTORS = [
    ".business-contacts-view__social-links a[itemprop='sameAs']",
    ".business-contacts-view__social-button a[href]",
]

DETAIL_GALLERY_PHOTO_SELECTORS = [
    ".orgpage-media-view__media img[src*='avatars.mds.yandex.net']",
    ".orgpage-media-view img[src*='avatars.mds.yandex.net']",
]

DETAIL_STORY_SELECTORS = [
    ".business-stories-view .story-preview",
    ".story-preview",
]

DETAIL_NEWS_SELECTORS = [
    ".business-post-card-view",
]

DETAIL_AVG_BILL_SELECTORS = [
    ".business-summary-rating-badge-view__rating-count",
    "[class*='average-bill']",
    "[class*='price-category']",
]

DETAIL_FEATURES_SELECTORS = [
    ".business-features-view__feature",
    "[class*='features-view__feature']",
    ".business-features-list-view__item",
]

DETAIL_MENU_SELECTORS = [
    ".business-card-products-view__product",
    "[class*='card-products-view__product']",
]

DETAIL_REVIEW_SELECTORS = [
    ".business-reviews-view__review",
    "[class*='reviews-view__review']",
]

ORG_LINK_SELECTOR = "a[href*='/org/']"

SOCIAL_OR_MESSENGER_HOSTS = [
    "t.me",
    "telegram.me",
    "telegram.org",
    "vk.com",
    "viber.click",
    "wa.me",
    "whatsapp.com",
    "max.ru",
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "facebook.com",
    "ok.ru",
]


def configure_terminal_encoding() -> None:
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


@dataclass
class Place:
    title: str = ""
    address: str = ""
    rating: str = ""
    phone: str = ""
    website: str = ""
    hours: str = ""
    categories: str = ""
    url: str = ""
    coordinates: str = ""
    gallery_photos: str = ""
    stories: str = ""
    latest_news: str = ""
    social_links: str = ""
    avg_bill: str = ""
    features: str = ""
    menu_items: str = ""
    reviews: str = ""
    logo_url: str = ""
    book_url: str = ""
    transit_stop: str = ""
    reviews_count: str = ""
    catalog_title: str = "Товары и услуги"  # «Меню» для общепита
    about_text: str = ""  # текст «Коротко о месте» из story-entry


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_phone(value: str) -> str:
    phones = re.findall(r"(?:\+7|8)\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", value)
    return ", ".join(dict.fromkeys(clean_text(phone) for phone in phones))


def join_values(values: Iterable[str], limit: int | None = None) -> str:
    cleaned = [clean_text(value) for value in values if clean_text(value)]
    unique = list(dict.fromkeys(cleaned))
    if limit is not None:
        unique = unique[:limit]
    return " | ".join(unique)


def normalize_media_url(value: str) -> str:
    value = clean_text(value)
    if value.startswith("//"):
        value = f"https:{value}"
    return value.replace("&amp;", "&")


def normalize_external_url(value: str) -> str:
    value = normalize_media_url(value)
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return value


def url_host(value: str) -> str:
    try:
        return urlsplit(normalize_external_url(value)).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def is_http_url(value: str) -> bool:
    value = normalize_external_url(value)
    return value.startswith("http://") or value.startswith("https://")


def is_social_or_messenger_url(value: str) -> bool:
    host = url_host(value)
    if not host:
        return False
    return any(host == item or host.endswith(f".{item}") for item in SOCIAL_OR_MESSENGER_HOSTS)


def is_real_website_url(value: str) -> bool:
    if not is_http_url(value):
        return False
    host = url_host(value)
    if not host:
        return False
    if "yandex." in host or host in {"ya.ru"}:
        return False
    return not is_social_or_messenger_url(value)


def has_real_website(place: Place) -> bool:
    return is_real_website_url(place.website)


def split_values(value: str) -> list[str]:
    return [clean_text(item) for item in value.split("|") if clean_text(item)]


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def image_alt(place: Place, index: int) -> str:
    title = clean_text(place.title) or "Company"
    return f"{title} photo {index}"


def uniq_key(place: Place) -> str:
    if place.url:
        return place.url.lower()
    return "|".join([place.title.lower(), place.address.lower()])


def normalize_org_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    url = urljoin("https://yandex.ru", raw_url)
    parts = urlsplit(url)

    if "/org/" not in parts.path:
        return ""

    path = parts.path
    path = re.sub(r"/(?:gallery|photos|reviews|features|prices|menu)/?$", "/", path)
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


# Суффиксы размеров фото Яндекса. Нужны для дедупа галереи и для сравнения
# фото с логотипом: одна и та же картинка приходит с разными суффиксами.
PHOTO_SIZE_SUFFIX_RE = re.compile(
    r'/(XXXL|XXL|XL|L|M|orig|'
    r'priority-headline-background|priority-headline-logo-square|'
    r'[0-9]+x[0-9]+|smart_crop_[^/]+)$'
)


def photo_base(url: str) -> str:
    """Базовый путь фото без суффикса размера — для сравнения картинок."""
    return PHOTO_SIZE_SUFFIX_RE.sub('', (url or '').strip().rstrip('/'))


def is_search_echo(title: str, query: str) -> bool:
    return clean_text(title).casefold() == clean_text(query).casefold()


def print_dependency_help() -> None:
    print("Playwright is not installed in this Python environment.", file=sys.stderr)
    print("Create a clean virtual environment and install dependencies:", file=sys.stderr)
    print("  python -m venv .venv", file=sys.stderr)
    print("  source .venv/bin/activate", file=sys.stderr)
    print("  python -m pip install -r requirements.txt", file=sys.stderr)
    print("  python -m playwright install chromium", file=sys.stderr)


def ensure_pip_playwright() -> None:
    spec = importlib.util.find_spec("playwright")
    if spec is None:
        print_dependency_help()
        raise SystemExit(2)

    origin = str(spec.origin or "")
    if "/usr/lib/python3/dist-packages/playwright" in origin:
        print("System Playwright package was detected.", file=sys.stderr)
        print(f"Loaded from: {origin}", file=sys.stderr)
        print("", file=sys.stderr)
        print("This apt/deb package expects /usr/bin/node and often breaks in minimal environments.", file=sys.stderr)
        print("Use the project virtual environment instead:", file=sys.stderr)
        print("  python -m venv .venv", file=sys.stderr)
        print("  source .venv/bin/activate", file=sys.stderr)
        print("  python -m pip install --upgrade pip", file=sys.stderr)
        print("  python -m pip install -r requirements.txt", file=sys.stderr)
        print("  python -m playwright install chromium", file=sys.stderr)
        print("  python yandex_maps_parser.py \"moscow\"", file=sys.stderr)
        raise SystemExit(2)


def print_browser_help(error: Exception) -> None:
    reason = str(error).splitlines()[0] if str(error) else type(error).__name__
    print("Could not start Playwright Chromium.", file=sys.stderr)
    print(f"Reason: {reason}", file=sys.stderr)
    print("Recommended install commands:", file=sys.stderr)
    print("  python -m pip install -r requirements.txt", file=sys.stderr)
    print("  python -m playwright install chromium", file=sys.stderr)
    print("On Linux, if system libraries are missing, also run:", file=sys.stderr)
    print("  python -m playwright install-deps chromium", file=sys.stderr)


async def first_text(locator, selectors: Iterable[str], timeout: int = 1200) -> str:
    for selector in selectors:
        try:
            item = locator.locator(selector).first
            if await item.count():
                text = clean_text(await item.inner_text(timeout=timeout))
                if text:
                    return text
        except Exception:
            continue
    return ""


async def first_attr(locator, selectors: Iterable[str], attr: str, timeout: int = 1200) -> str:
    for selector in selectors:
        try:
            item = locator.locator(selector).first
            if await item.count():
                value = clean_text(await item.get_attribute(attr, timeout=timeout))
                if value:
                    return value
        except Exception:
            continue
    return ""


async def all_attrs(locator, selectors: Iterable[str], attr: str, timeout: int = 1200) -> list[str]:
    values: list[str] = []
    for selector in selectors:
        try:
            items = locator.locator(selector)
            count = await items.count()
            for index in range(count):
                value = clean_text(await items.nth(index).get_attribute(attr, timeout=timeout))
                if value:
                    values.append(value)
            if values:
                return list(dict.fromkeys(values))
        except Exception:
            continue
    return []


async def all_texts(locator, selectors: Iterable[str], timeout: int = 1200) -> list[str]:
    values: list[str] = []
    for selector in selectors:
        try:
            items = locator.locator(selector)
            count = await items.count()
            for index in range(count):
                text = clean_text(await items.nth(index).inner_text(timeout=timeout))
                if text:
                    values.append(text)
            if values:
                return list(dict.fromkeys(values))
        except Exception:
            continue
    return []


async def all_background_image_urls(locator, selectors: Iterable[str], timeout: int = 1200) -> list[str]:
    values: list[str] = []
    pattern = re.compile(r"url\([\"']?(.*?)[\"']?\)")

    for selector in selectors:
        try:
            items = locator.locator(selector)
            count = await items.count()
            for index in range(count):
                style = clean_text(await items.nth(index).get_attribute("style", timeout=timeout))
                match = pattern.search(style)
                if match:
                    values.append(normalize_media_url(match.group(1)))
            if values:
                return list(dict.fromkeys(values))
        except Exception:
            continue
    return []


async def extract_stories(page, limit: int = 3) -> str:
    stories: list[str] = []

    for selector in DETAIL_STORY_SELECTORS:
        try:
            items = page.locator(selector)
            count = await items.count()
            for index in range(min(count, limit)):
                item = items.nth(index)
                title = await first_text(item, [".story-preview__title"])
                images = await all_background_image_urls(item, [".story-cover-preview__inner"])
                parts = [title]
                if images:
                    parts.append(images[0])
                stories.append(" - ".join(part for part in parts if part))
            if stories:
                return join_values(stories, limit)
        except Exception:
            continue

    return ""


async def extract_latest_news(page) -> str:
    for selector in DETAIL_NEWS_SELECTORS:
        try:
            item = page.locator(selector).first
            if not await item.count():
                continue

            text = await first_text(item, [".business-post-card-view__text"])
            date = await first_text(item, [".business-post-card-view__date"])
            images = await all_background_image_urls(item, [".business-post-card-view__photo"])
            parts = [date, text]
            if images:
                parts.append(images[0])
            return " - ".join(part for part in parts if part)
        except Exception:
            continue

    return ""


async def extract_avg_bill(page) -> str:
    """Средний счёт — из блока особенностей valued."""
    try:
        # Ищем через JavaScript — быстрее и надёжнее
        result = await page.evaluate(r"""() => {
            const items = document.querySelectorAll('.business-features-view__valued');
            for (const item of items) {
                const title = item.querySelector('.business-features-view__valued-title');
                const value = item.querySelector('.business-features-view__valued-value');
                if (title && value) {
                    const t = title.textContent.toLowerCase();
                    if (t.includes('средний') || t.includes('чек') || t.includes('счёт') || t.includes('цена')) {
                        return value.textContent.trim();
                    }
                }
            }
            return '';
        }""")
        return result.strip() if result else ""
    except Exception:
        return ""


async def extract_features(page) -> list[str]:
    """Особенности: bool (Wi-Fi, парковка) + valued (оплата, часы)."""
    try:
        result = await page.evaluate(r"""() => {
            const features = [];
            // Bool-особенности (чекбоксы)
            document.querySelectorAll('.business-features-view__bool-item').forEach(item => {
                const text = item.querySelector('.business-features-view__bool-text');
                if (text) {
                    const t = text.textContent.trim();
                    if (t) features.push(t);
                }
            });
            // Valued-особенности (ключ: значение)
            document.querySelectorAll('.business-features-view__valued').forEach(item => {
                const title = item.querySelector('.business-features-view__valued-title');
                const value = item.querySelector('.business-features-view__valued-value');
                if (title && value) {
                    const t = title.textContent.replace(':', '').trim();
                    const v = value.textContent.trim();
                    if (t && v) features.push(t + ': ' + v);
                }
            });
            return features;
        }""")
        return result if result else []
    except Exception:
        return []


async def extract_menu_items(page) -> list[dict]:
    """Каталог: переходим на /prices/, собираем категории, товары с фото и описаниями."""
    try:
        import re as _re

        # Определяем URL страницы с ценами
        current_url = page.url
        # Нормализуем базовый URL организации
        base_url = _re.sub(r'/(?:gallery|photos|reviews|features|prices|menu)/?$', '/', current_url)
        if not base_url.endswith('/'):
            base_url += '/'
        prices_url = base_url + 'prices/'

        # Открываем страницу каталога
        try:
            await page.goto(prices_url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(1500)
        except Exception:
            return []

        # Прокручиваем для загрузки всех товаров
        for _ in range(3):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(700)

        result = await page.evaluate(r"""() => {
            const items = [];
            // Карточки товаров: photo-view (с фото) и list-view (список без фото)
            document.querySelectorAll(
                '.related-item-photo-view, .business-card-item-view, .related-item-list-view'
            ).forEach(item => {
                // Название
                const titleEl = item.querySelector(
                    '.related-item-photo-view__title, .business-card-item-view__title, ' +
                    '.related-item-list-view__title, [class*="item-view__title"]'
                );
                // Цена
                const priceEl = item.querySelector(
                    '.related-product-view__price, .related-item-list-view__price, ' +
                    '[class*="product-view__price"], [class*="item-view__price"]'
                );
                // Описание / объём-вес
                const descEl = item.querySelector(
                    '.related-item-photo-view__description, .related-item-list-view__volume, ' +
                    '[class*="item-view__description"], [class*="item-view__subtitle"], ' +
                    '[class*="item-view__volume"]'
                );
                // Категория — ближайший заголовок секции выше
                let category = '';
                let el = item.closest('[class*="product-group"], [class*="category"]');
                if (!el) {
                    let prev = item.parentElement;
                    while (prev) {
                        const hdr = prev.querySelector('h2, h3, [class*="section-header__title"], [class*="grouped-view__title"]');
                        if (hdr) { category = hdr.textContent.trim(); break; }
                        prev = prev.parentElement;
                        if (!prev || prev === document.body) break;
                    }
                } else {
                    const hdr = el.querySelector('h2, h3, [class*="section-header__title"]');
                    if (hdr) category = hdr.textContent.trim();
                }

                // Фото
                let img = '';
                const imgEl = item.querySelector('img');
                const imgDiv = item.querySelector('.image__content, [class*="photo-view__image"] div');
                if (imgEl && imgEl.src && !imgEl.src.endsWith('svg')) {
                    img = imgEl.src;
                } else if (imgDiv) {
                    const style = imgDiv.getAttribute('style') || '';
                    const m = style.match(/url\(["']?([^"')]+)["']?\)/);
                    if (m) img = m[1];
                }
                if (img) {
                    img = img.replace(':443/', '/');
                }

                const name = titleEl ? titleEl.textContent.trim() : '';
                if (name) {
                    items.push({
                        name:        name,
                        price:       priceEl ? priceEl.textContent.trim() : '',
                        description: descEl  ? descEl.textContent.trim().slice(0, 300) : '',
                        image_url:   img,
                        category:    category
                    });
                }
            });
            return items;
        }""")

        # Возвращаемся на основную страницу
        try:
            await page.go_back(wait_until='domcontentloaded', timeout=10000)
        except Exception:
            pass

        return result if result else []
    except Exception:
        return []


async def extract_reviews(page, limit: int = 30) -> list[dict]:
    """Отзывы через itemprop — с аватарками и прокруткой для загрузки всех."""
    try:
        # Кликаем на вкладку "Отзывы" чтобы загрузить все
        try:
            reviews_tab = page.locator('a[href*="/reviews"], [class*="tabs__tab"]:has-text("Отзывы")')
            if await reviews_tab.count():
                await reviews_tab.first.click(timeout=3000)
                await page.wait_for_timeout(1200)
        except Exception:
            pass

        # Кликаем "Показать ещё" несколько раз чтобы догрузить отзывы
        for _ in range(5):
            try:
                more_btn = page.locator('.business-reviews-card-view__more button, [class*="show-more"], button:has-text("Показать ещё")')
                if await more_btn.count() and await more_btn.first.is_visible(timeout=1000):
                    await more_btn.first.click(timeout=2000)
                    await page.wait_for_timeout(800)
                else:
                    break
            except Exception:
                break

        result = await page.evaluate(r"""(limit) => {
            const reviews = [];
            document.querySelectorAll('[itemprop="review"]').forEach(block => {
                if (reviews.length >= limit) return;

                const author = block.querySelector('[itemprop="name"]');
                const body   = block.querySelector('[itemprop="reviewBody"]');
                const rating = block.querySelector('[itemprop="ratingValue"]');
                const date   = block.querySelector('[itemprop="datePublished"]');

                // Аватарка из meta[itemprop="image"] внутри блока автора
                const avatarMeta = block.querySelector('meta[itemprop="image"]');
                const avatarImg  = block.querySelector('.business-review-view__author-image img, [class*="author-image"] img');
                let avatar = '';
                if (avatarMeta) {
                    avatar = avatarMeta.getAttribute('content') || '';
                } else if (avatarImg) {
                    avatar = avatarImg.src || '';
                }

                // Текст через spoiler или прямо
                let text = '';
                if (body) {
                    const spoiler = body.closest('.business-review-view__body')
                        ?.querySelector('.spoiler-view__text');
                    text = spoiler ? spoiler.textContent.trim() : body.textContent.trim();
                }

                const ratingVal = rating
                    ? parseFloat(rating.getAttribute('content') || '5')
                    : 5;

                if (ratingVal >= 4 && text) {
                    reviews.push({
                        author: author ? author.textContent.trim() : 'Анонимно',
                        avatar: avatar,
                        text:   text.slice(0, 800),
                        rating: Math.round(ratingVal),
                        date:   date ? date.getAttribute('content') || '' : ''
                    });
                }
            });
            return reviews;
        }""", limit)
        # Форматируем дату
        import re as _re
        for r in (result or []):
            if r.get('date'):
                m = _re.match(r'(\d{4})-(\d{2})-(\d{2})', r['date'])
                if m:
                    months = ['','янв','фев','мар','апр','май','июн',
                              'июл','авг','сен','окт','ноя','дек']
                    r['date'] = f"{int(m.group(3))} {months[int(m.group(2))]} {m.group(1)}"
        return result if result else []
    except Exception:
        return []


def _normalize_address(addr: str) -> str:
    """Вставляет запятую+пробел перед слипшимися частями адреса (этаж, корпус и т.п.)."""
    import re as _re
    if not addr:
        return addr
    addr = addr.strip()
    parts = ['этаж', 'корпус', 'корп', 'подъезд', 'строение', 'офис',
             'помещение', 'пом', 'вход', 'секция', 'блок']
    for w in parts:
        addr = _re.sub(rf'(?<=[а-яёА-ЯЁ0-9])({w}\b)', r', \1', addr, flags=_re.IGNORECASE)
    addr = _re.sub(r'\s{2,}', ' ', addr)
    addr = _re.sub(r',\s*,', ',', addr)
    return addr.strip()


def _tab_url(url: str, tab: str) -> str:
    """
    Строит URL вкладки Яндекс.Карт с учётом формата ссылки.
    - org-формат  (/maps/org/.../123/)        → сегмент пути:    /maps/org/.../123/<tab>/
    - mapframe    (?poi[uri]=...&tab=overview) → query-параметр:  ...&tab=<tab>
    tab: gallery|reviews|features|menu|prices
    """
    import re as _re
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    # Сегмент prices у org-формата называется /prices/, у mapframe tab=menu (общий каталог)
    parts = urlsplit(url)
    has_poi = 'poi[' in url or 'poi%5B' in url or 'tab=' in (parts.query or '')

    if has_poi:
        # mapframe: меняем/добавляем tab= в query
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        # Для mapframe каталог — это tab=menu (prices отдельной вкладки нет)
        tab_val = 'menu' if tab in ('menu', 'prices') else tab
        q['tab'] = tab_val
        new_query = urlencode(q, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
    else:
        # org-формат: вкладка — сегмент пути
        base = _re.sub(r'/(?:gallery|photos|reviews|features|prices|menu)/?$', '/', url)
        # убираем query/fragment для чистого пути-сегмента
        base = urlunsplit((parts.scheme, parts.netloc, urlsplit(base).path, '', ''))
        if not base.endswith('/'):
            base += '/'
        return base + tab + '/'


def _catalog_title_for(category: str) -> str:
    """«Меню» для общепита, иначе «Товары и услуги»."""
    cat = (category or "").lower()
    FOOD = ["кафе", "ресторан", "столов", "пекарн", "бар", "паб",
            "кейтеринг", "кофейн", "пиццери", "бистро", "кофе"]
    for word in FOOD:
        if word in cat:
            return "Меню"
    return "Товары и услуги"


def _normalize_gallery_urls(raw_urls: list, limit: int = 15) -> list[str]:
    """
    Отсекает заготовки (_height/_width — незагруженные lazy-плейсхолдеры),
    видео и логотип организации (лого — не фото заведения, ему не место
    в галерее и hero). Берёт уникальные фото по base-пути.
    """
    import re as _re
    # Заготовки — отбрасываем
    BAD_SUFFIX = _re.compile(r'/(?:[A-Z]+_height|[A-Z]+_width)$')
    # Мусор карточки Яндекса — не фото заведения:
    #  - priority-headline-* : рекламные ассеты платного размещения (лого + баннер-шапка)
    #  - pin_* / _pin_search : картографические метки-булавки с карты
    JUNK = _re.compile(r'priority-headline|/pin_|_pin_search|pin_x\d', _re.I)

    seen_bases = set()
    photos = []
    for url in raw_urls:
        url = (url or "").strip().rstrip('/')
        if not url:
            continue
        # Видео / плеер — пропускаем
        if 'yaplayer' in url or '/get-vh/' in url and url.endswith('_height'):
            continue
        # Рекламные ассеты и картографические метки — пропускаем
        if JUNK.search(url):
            continue
        # Битая заготовка — пропускаем
        if BAD_SUFFIX.search(url):
            continue
        # Дедуп по базовому пути без суффикса размера
        base = photo_base(url)
        if base in seen_bases:
            continue
        seen_bases.add(base)
        photos.append(url)
        if len(photos) >= limit:
            break
    return photos


async def extract_gallery_photos(page, limit: int = 15) -> list[str]:
    """Фото галереи: реальные рабочие URL. Отсекаем заготовки (_height/_width) и видео (yaplayer)."""
    try:
        result = await page.evaluate(r"""() => {
            const urls = new Set();
            const HOSTS = ['get-altay', 'get-tycoon', 'get-vh'];
            const sel = HOSTS.map(h => `[style*="${h}"], [src*="${h}"], [data-src*="${h}"]`).join(', ');
            document.querySelectorAll(sel).forEach(el => {
                // Пропускаем элементы внутри видео-плеера и логотипа
                if (el.closest('.yaplayer, [class*="yaplayer"], [class*="video"], [class*="logo"]')) return;
                const style = el.getAttribute('style') || '';
                const src   = el.getAttribute('src') || el.getAttribute('data-src') || '';
                const all   = style + ' ' + src;
                const m = all.match(/https:\/\/avatars\.mds\.yandex\.net\/(?:get-altay|get-tycoon|get-vh)\/[^\s"')]+/g);
                if (m) m.forEach(u => urls.add(u));
            });
            document.querySelectorAll('script').forEach(s => {
                const text = s.textContent || '';
                const m = text.match(/https:\/\/avatars\.mds\.yandex\.net\/(?:get-altay|get-tycoon|get-vh)\/[^\s"'\\,)]+/g);
                if (m) m.forEach(u => urls.add(u));
            });
            return [...urls];
        }""")

        photos = _normalize_gallery_urls(result or [], limit)
        return photos
    except Exception:
        return []


async def safe_inner_text(locator) -> str:
    try:
        return clean_text(await locator.inner_text(timeout=1200))
    except Exception:
        return ""


async def safe_click(locator) -> bool:
    try:
        await locator.click(timeout=2500)
        return True
    except Exception:
        try:
            await locator.scroll_into_view_if_needed(timeout=1500)
            await locator.click(timeout=2500)
            return True
        except Exception:
            return False


async def find_cards(page):
    for selector in CARD_SELECTORS:
        cards = page.locator(selector)
        try:
            if await cards.count():
                return cards
        except Exception:
            continue
    return page.locator(CARD_SELECTORS[0])


async def close_popups(page) -> None:
    candidates = [
        "button:has-text('OK')",
        "button:has-text('Ok')",
        "button:has-text('Accept')",
        "button:has-text('Allow')",
        "button:has-text('Not now')",
        "button:has-text('Got it')",
    ]
    for selector in candidates:
        try:
            button = page.locator(selector).first
            if await button.count():
                await button.click(timeout=700)
                await page.wait_for_timeout(300)
        except Exception:
            pass


async def parse_coordinates_from_url(page) -> str:
    url = page.url

    match = re.search(r"[?&]ll=([0-9.\-]+)%2C([0-9.\-]+)", url)
    if match:
        return f"{match.group(2)},{match.group(1)}"

    match = re.search(r"[?&]ll=([0-9.\-]+),([0-9.\-]+)", url)
    if match:
        return f"{match.group(2)},{match.group(1)}"

    return ""


async def parse_card(card) -> Place:
    place = Place()
    place.title = await first_text(card, TITLE_SELECTORS)
    place.address = await first_text(card, ADDRESS_SELECTORS)
    place.rating = await first_text(card, RATING_SELECTORS)
    place.url = normalize_org_url(await first_attr(card, [ORG_LINK_SELECTOR], "href"))

    if not place.title and place.url:
        link_text = await first_text(card, [ORG_LINK_SELECTOR])
        lines = [clean_text(line) for line in link_text.splitlines() if clean_text(line)]
        if lines:
            place.title = lines[0]

    text = await safe_inner_text(card)
    place.phone = normalize_phone(text)

    return place




async def extract_book_url(page) -> str:
    """Ссылка кнопки 'Записаться онлайн' из блока call-to-action."""
    try:
        result = await page.evaluate(r"""() => {
            // Приоритет: блок призыва к действию на карточке
            const cta = document.querySelector('.business-card-title-view__call-to-action');
            if (cta) {
                const a = cta.querySelector('a[href]');
                if (a && a.href) return a.href;
            }
            // Фолбэк: любая ссылка с текстом записи
            const links = [...document.querySelectorAll('a[href]')];
            for (const a of links) {
                const text = (a.textContent || '').toLowerCase();
                if (text.includes('записаться') || text.includes('онлайн-запись') || text.includes('забронировать')) {
                    if (a.href) return a.href;
                }
            }
            return '';
        }""")
        url = (result or '').strip()
        # Отсекаем ссылки на сам Яндекс (это не запись)
        if url and 'yandex.' in url and '/maps/' in url:
            return ''
        return url
    except Exception:
        return ''


async def extract_rating_and_count(page) -> dict:
    """Рейтинг (5,0 → 5.0) и число оценок (580 оценок → 580)."""
    try:
        result = await page.evaluate(r"""() => {
            const out = { rating: '', count: '' };
            // Рейтинг
            const rt = document.querySelector('.business-rating-badge-view__rating-text');
            if (rt) out.rating = (rt.textContent || '').trim();
            // Число оценок/отзывов
            const ct = document.querySelector('.business-header-rating-view__text');
            if (ct) {
                const m = (ct.textContent || '').match(/\d[\d\s]*/);
                if (m) out.count = m[0].replace(/\s/g, '');
            }
            return out;
        }""")
        rating = (result.get("rating") or "").replace(",", ".").strip()
        count = (result.get("count") or "").strip()
        return {"rating": rating, "count": count}
    except Exception:
        return {"rating": "", "count": ""}


async def extract_transit_stop(page) -> dict:
    """Ближайшая остановка с расстоянием."""
    try:
        result = await page.evaluate(r"""() => {
            const stop = document.querySelector('.masstransit-stops-view__stop');
            if (!stop) return {};
            const nameEl = stop.querySelector('.masstransit-stops-view__stop-name');
            const distEl = stop.querySelector('.masstransit-stops-view__stop-distance-text');
            const name = nameEl ? nameEl.textContent.trim() : '';
            const dist = distEl ? distEl.textContent.replace(/\\u00a0/g, ' ').trim() : '';
            if (!name) return {};
            return { name, distance: dist };
        }""")
        return result or {}
    except Exception:
        return {}


async def extract_about(page) -> str:
    """Текст «Коротко о месте» из story-entry (business-story-entry-view__description)."""
    try:
        result = await page.evaluate(r"""() => {
            const d = document.querySelector(
                '.business-story-entry-view__description, ' +
                '.orgpage-header-view__story-entry .business-story-entry-view__description'
            );
            return d ? (d.textContent || '').trim() : '';
        }""")
        return (result or '').strip()
    except Exception:
        return ''


async def extract_logo(page) -> str:
    """Логотип организации."""
    try:
        result = await page.evaluate(r"""() => {
            const sels = [
                '.orgpage-media-view__logo img',
                '.business-header-logo img',
                '[class*="media-view__logo"] img',
                'img[src*="priority-headline-logo"]',
                'img[alt="Логотип"]',
            ];
            for (const s of sels) {
                const img = document.querySelector(s);
                if (img) {
                    const src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                    if (src && !src.endsWith('svg')) return src;
                }
            }
            return '';
        }""")
        logo = (result or '').strip().replace(':443/', '/')
        # Мелкий размер /S → больший для чёткости (логотип квадратный)
        import re as _re
        logo = _re.sub(r'/S$', '/M', logo)
        return logo
    except Exception:
        return ''


async def extract_features_bool(page) -> list:
    """Только bool-особенности (короткие теги без valued)."""
    try:
        # Ждём появления списка особенностей (на вкладке /features/ грузится не сразу)
        try:
            await page.wait_for_selector('.business-features-view__bool-item', timeout=8000)
        except Exception:
            pass
        result = await page.evaluate(r"""() => {
            const feats = [];
            const seen = new Set();
            // Все bool-item где угодно (карточка обрезает список, вкладка /features/ — полный)
            document.querySelectorAll('.business-features-view__bool-item').forEach(item => {
                const el = item.querySelector('.business-features-view__bool-text');
                const t = (el ? el.textContent : '').trim();
                if (t && !seen.has(t)) { seen.add(t); feats.push(t); }
            });
            return feats;
        }""")
        return result or []
    except Exception:
        return []


async def _fetch_tab(context, url: str, extractor, **kwargs):
    """Открывает новую вкладку на url, запускает extractor, закрывает."""
    tab = await context.new_page()
    try:
        await tab.goto(url, wait_until="domcontentloaded", timeout=30000)
        await tab.wait_for_timeout(1500)
        return await extractor(tab, **kwargs)
    except Exception as e:
        print(f"[WARN] _fetch_tab {url[:50]}: {e}", flush=True)
        return None
    finally:
        try:
            await tab.close()
        except Exception:
            pass


async def scrape_gallery(page, limit: int = 20) -> list:
    """Собирает фото с /gallery/ — ждёт загрузки и берёт из всех источников."""
    try:
        # Ждём появления первых фото
        try:
            await page.wait_for_selector(
                '.media-gallery img[src*="avatars"], .media-wrapper img[src*="avatars"], [class*="media"] img[src*="avatars"]',
                timeout=12000
            )
        except Exception:
            await page.wait_for_timeout(3000)

        # Прокрутка для подгрузки всех фото
        for _ in range(10):
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(600)

        result = await page.evaluate(r"""(limit) => {
            const urls = [];
            const HOSTS = ['get-altay', 'get-tycoon', 'get-vh'];
            const hostOk = (s) => HOSTS.some(h => s.includes(h));

            // Из img элементов (кроме видео и логотипа организации)
            document.querySelectorAll('img').forEach(img => {
                if (img.closest('.yaplayer, [class*="yaplayer"], [class*="video"], [class*="logo"]')) return;
                let src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                if (!src.includes('avatars.mds.yandex.net')) return;
                if (!hostOk(src)) return;
                src = src.replace(':443/', '/');
                urls.push(src);
            });

            // Из CSS background-image
            const sel = HOSTS.map(h => `[style*="${h}"]`).join(', ');
            document.querySelectorAll(sel).forEach(el => {
                if (el.closest('.yaplayer, [class*="yaplayer"], [class*="video"], [class*="logo"]')) return;
                const style = el.getAttribute('style') || '';
                const m = style.match(/url\(["']?(https:\/\/avatars\.mds\.yandex\.net[^"')]+)["']?\)/);
                if (m) urls.push(m[1].replace(':443/', '/'));
            });

            return urls;
        }""", limit)

        # Отсев заготовок и видео через общий нормализатор
        photos = _normalize_gallery_urls(result or [], limit)
        print(f"[INFO] scrape_gallery: {len(result) if result else 0} сырых → {len(photos)} рабочих", flush=True)
        return photos
    except Exception as e:
        print(f"[WARN] scrape_gallery: {e}", flush=True)
        return []


async def scrape_catalog(page) -> list:
    """Собирает каталог с /prices/ — поддерживает grouped и rubricator структуру."""
    try:
        # Ждём любой из вариантов структуры
        try:
            await page.wait_for_selector(
                '.business-full-items-grouped-view__item, .related-item-photo-view, .related-item-list-view',
                timeout=10000
            )
        except Exception:
            pass
        await page.wait_for_timeout(1000)
        # Прокручиваем, пока растёт число товаров И загруженных картинок (lazy load)
        prev_count = -1
        stable = 0
        for _ in range(25):
            cur = await page.evaluate(r"""() => {
                const items = document.querySelectorAll(
                    '.business-full-items-grouped-view__item, .related-item-photo-view, .related-item-list-view'
                ).length;
                const imgs = [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth > 0).length;
                return items * 1000 + imgs;  // комбинированный счётчик
            }""")
            if cur == prev_count:
                stable += 1
                if stable >= 3:  # 3 раза подряд без изменений — дошли до конца
                    break
            else:
                stable = 0
            prev_count = cur
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(700)
        # финальная пауза на догрузку последних картинок
        await page.wait_for_timeout(800)

        result = await page.evaluate(r"""() => {
            const items = [];
            const seen = new Set();

            function pushItem(name, price, desc, img, cat){
                name = (name || '').trim();
                if (!name) return;
                const key = name + '|' + (price || '');
                if (seen.has(key)) return;
                seen.add(key);
                items.push({ name, price: (price||'').trim(),
                    description: (desc||'').trim().slice(0,300),
                    image_url: (img||'').replace(':443/','/'), category: (cat||'').trim() });
            }
            function catFor(item){
                let p = item.closest('[class*="grouped-view__category"], [class*="rubricator__container"]');
                if (p){
                    const h = p.querySelector('[class*="grouped-view__title"], h2, h3, [class*="section-header__title"]');
                    if (h) return h.textContent.trim();
                }
                let prev = item.parentElement, depth = 0;
                while (prev && depth < 6){
                    const h = prev.querySelector && prev.querySelector('[class*="grouped-view__title"], h2, h3, [class*="section-header__title"]');
                    if (h) return h.textContent.trim();
                    prev = prev.parentElement; depth++;
                }
                return '';
            }

            // === Универсальный сбор: все list-view и photo-view где угодно ===
            document.querySelectorAll('.related-item-list-view').forEach(item => {
                const t = item.querySelector('.related-item-list-view__title');
                const pr = item.querySelector('.related-item-list-view__price');
                const sub = item.querySelector('.related-item-list-view__subtitle, .related-item-list-view__volume, .related-item-list-view__description');
                const imgEl = item.querySelector('img');
                pushItem(t ? (t.getAttribute('title') || t.textContent) : '',
                         pr ? pr.textContent : '',
                         sub ? sub.textContent : '',
                         imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '',
                         catFor(item));
            });
            document.querySelectorAll('.related-item-photo-view').forEach(item => {
                const t = item.querySelector('.related-item-photo-view__title');
                const pr = item.querySelector('.related-product-view__price, [class*="product-view__price"]');
                const ds = item.querySelector('.related-item-photo-view__description');
                const imgEl = item.querySelector('img');
                pushItem(t ? (t.getAttribute('title') || t.textContent) : '',
                         pr ? pr.textContent : '',
                         ds ? ds.textContent : '',
                         imgEl ? (imgEl.src || '') : '',
                         catFor(item));
            });
            if (items.length > 0) return items;

            // === Вариант 1: business-full-items-grouped-view (новая структура) ===
            const groupedCats = document.querySelectorAll('.business-full-items-grouped-view__category');
            if (groupedCats.length > 0) {
                groupedCats.forEach(catBlock => {
                    const catTitle = catBlock.querySelector('.business-full-items-grouped-view__title');
                    const category = catTitle ? catTitle.textContent.trim() : '';

                    catBlock.querySelectorAll('.related-item-list-view').forEach(item => {
                        const titleEl    = item.querySelector('.related-item-list-view__title');
                        const subtitleEl = item.querySelector('.related-item-list-view__subtitle, .related-item-list-view__description');
                        const priceEl    = item.querySelector('.related-item-list-view__price');
                        const imgEl      = item.querySelector('img');
                        let img = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '';
                        img = img.replace(/\/(M_height|S|L_height)$/, '/XXL_height').replace(':443/', '/');
                        const name = titleEl ? titleEl.textContent.trim() : '';
                        if (!name) return;
                        items.push({
                            name,
                            description: subtitleEl ? subtitleEl.textContent.trim().slice(0, 300) : '',
                            price:       priceEl ? priceEl.textContent.trim() : '',
                            image_url:   img,
                            category
                        });
                    });

                    catBlock.querySelectorAll('.related-item-photo-view').forEach(item => {
                        const titleEl = item.querySelector('.related-item-photo-view__title');
                        const descEl  = item.querySelector('.related-item-photo-view__description');
                        const priceEl = item.querySelector('.related-product-view__price');
                        const imgEl   = item.querySelector('img');
                        let img = imgEl ? (imgEl.src || '') : '';
                        img = img.replace(/\/(M_height|S|L_height)$/, '/XXL_height').replace(':443/', '/');
                        const name = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent || '').trim() : '';
                        if (!name) return;
                        items.push({
                            name,
                            description: descEl ? descEl.textContent.trim().slice(0, 300) : '',
                            price:       priceEl ? priceEl.textContent.trim() : '',
                            image_url:   img,
                            category
                        });
                    });
                });
                return items;
            }

            // === Вариант 2: rubricator контейнеры (старая структура) ===
            const containers = document.querySelectorAll('.business-related-items-rubricator__container');
            if (containers.length > 0) {
                containers.forEach(container => {
                    const prev = container.previousElementSibling;
                    let cat = '';
                    if (prev) {
                        const h = prev.querySelector('h2, h3, [class*="section-header__title"]');
                        if (h) cat = h.textContent.trim();
                    }
                    container.querySelectorAll('.related-item-photo-view, .related-item-list-view').forEach(item => {
                        const isPhoto = item.classList.contains('related-item-photo-view');
                        const titleEl = item.querySelector(
                            isPhoto ? '.related-item-photo-view__title' : '.related-item-list-view__title'
                        );
                        const priceEl = item.querySelector(
                            isPhoto ? '.related-product-view__price' : '.related-item-list-view__price'
                        );
                        const imgEl = item.querySelector('img');
                        let img = imgEl ? (imgEl.src || '') : '';
                        img = img.replace(/\/(M_height|S|L_height)$/, '/XXL_height').replace(':443/', '/');
                        const name = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent || '').trim() : '';
                        if (!name) return;
                        items.push({ name, description: '', price: priceEl ? priceEl.textContent.trim() : '',
                                      image_url: img, category: cat });
                    });
                });
                return items;
            }

            // === Вариант 3: плоский список ===
            document.querySelectorAll('.related-item-photo-view, .related-item-list-view').forEach(item => {
                const isPhoto = item.classList.contains('related-item-photo-view');
                const titleEl = item.querySelector(
                    isPhoto ? '.related-item-photo-view__title' : '.related-item-list-view__title'
                );
                const priceEl = item.querySelector(
                    isPhoto ? '.related-product-view__price' : '.related-item-list-view__price'
                );
                const name = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent || '').trim() : '';
                if (!name) return;
                items.push({ name, description: '', price: priceEl ? priceEl.textContent.trim() : '',
                              image_url: '', category: '' });
            });
            return items;
        }""")
        return result or []
    except Exception:
        return []


async def scrape_reviews(page, limit: int = 30) -> list:
    """Собирает отзывы с /reviews/."""
    import re as _re2
    try:
        try:
            await page.wait_for_selector('[itemprop="review"]', timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(800)
        for _ in range(6):
            try:
                btn = page.locator('.business-reviews-card-view__more button, button:has-text("Показать ещё")')
                if await btn.count() and await btn.first.is_visible(timeout=1500):
                    await btn.first.click(timeout=2000)
                    await page.wait_for_timeout(700)
                else:
                    break
            except Exception:
                break
        result = await page.evaluate(r"""(limit) => {
            const reviews = [], seen = new Set();
            document.querySelectorAll('[itemprop="review"]').forEach(block => {
                if (reviews.length >= limit) return;
                const authorEl = block.querySelector('[itemprop="name"]');
                const bodyEl   = block.querySelector('[itemprop="reviewBody"]');
                const ratingEl = block.querySelector('[itemprop="ratingValue"]');
                const dateEl   = block.querySelector('[itemprop="datePublished"]');
                const avatarMeta = block.querySelector('meta[itemprop="image"]');
                const avatarImg  = block.querySelector('[class*="author-image"] img');
                let avatar = avatarMeta ? (avatarMeta.getAttribute('content') || '') :
                             (avatarImg ? (avatarImg.src || '') : '');
                let text = '';
                if (bodyEl) {
                    const sp = bodyEl.closest('.business-review-view__body')?.querySelector('.spoiler-view__text');
                    text = (sp || bodyEl).textContent.trim();
                }
                const author = authorEl ? authorEl.textContent.trim() : 'Аноним';
                const dateRaw = dateEl ? (dateEl.getAttribute('content') || '') : '';
                const rating = ratingEl ? parseFloat(ratingEl.getAttribute('content') || '5') : 5;
                if (rating < 4 || !text) return;
                const key = author + '|' + dateRaw + '|' + text.slice(0,40);
                if (seen.has(key)) return;
                seen.add(key);
                reviews.push({ author, avatar, text: text.slice(0,800), rating: Math.round(rating), date: dateRaw });
            });
            return reviews;
        }""", limit)
        months = ['','янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
        for r in (result or []):
            if r.get('date'):
                import re as _re3
                m = _re3.match(r'(\d{4})-(\d{2})-(\d{2})', r['date'])
                if m:
                    r['date'] = f"{int(m.group(3))} {months[int(m.group(2))]} {m.group(1)}"
        return result or []
    except Exception:
        return []


async def parse_detail_page(page, place: Place, context=None) -> Place:
    await page.wait_for_timeout(900 + random.randint(0, 500))
    await close_popups(page)

    title = await first_text(page, DETAIL_TITLE_SELECTORS)
    address = await first_text(page, DETAIL_ADDRESS_SELECTORS)

    if title and not is_search_echo(title, place.title):
        place.title = title
    if address:
        place.address = _normalize_address(address)
    if not place.phone:
        place.phone = await first_text(page, DETAIL_PHONE_SELECTORS)
        if not place.phone:
            place.phone = normalize_phone(await safe_inner_text(page.locator("body")))
    place.phone = normalize_phone(place.phone)

    if not place.website:
        website_candidates = await all_attrs(page, ["a[itemprop='url']", ".business-urls-view__link"], "href")
        real_websites = [normalize_external_url(url) for url in website_candidates if is_real_website_url(url)]
        if real_websites:
            place.website = real_websites[0]
    place.website = normalize_external_url(place.website)
    if not is_real_website_url(place.website):
        place.website = ""

    if not place.hours:
        place.hours = await first_text(page, DETAIL_HOURS_SELECTORS)
    opening_hours = await all_attrs(page, ["meta[itemprop='openingHours']"], "content")
    if opening_hours:
        place.hours = join_values([place.hours, join_values(opening_hours)])

    if not place.categories:
        # Категории из шапки карточки — каждая отдельным элементом (не слитный текст)
        try:
            cats = await page.evaluate(r"""() => {
                const out = [];
                // Каждая категория — отдельная ссылка/span в блоке категорий карточки
                const nodes = document.querySelectorAll(
                    '.business-card-title-view__categories a, ' +
                    '.business-card-title-view__categories span, ' +
                    '.orgpage-categories-info-view__category, ' +
                    '.orgpage-categories-info-view__link, ' +
                    '[class*="categories-info-view__category"]'
                );
                nodes.forEach(n => {
                    const t = (n.getAttribute('title') || n.textContent || '').trim();
                    if (t && !out.includes(t)) out.push(t);
                });
                return out;
            }""")
            if cats:
                # Убираем хвост « в <Город>» из каждой категории
                import re as _rc
                cleaned = [_rc.sub(r'\s+в\s+[А-ЯЁ][а-яё-]+\s*$', '', c).strip() for c in cats]
                cleaned = [c for c in cleaned if c]
                place.categories = ", ".join(cleaned)
        except Exception:
            pass
        # Фолбек: breadcrumbs (последняя крошка)
        if not place.categories:
            try:
                cat_from_crumbs = await page.evaluate(r"""() => {
                    const crumbs = document.querySelectorAll('.breadcrumbs-view__breadcrumb');
                    if (crumbs.length > 0) {
                        const last = crumbs[crumbs.length - 1];
                        return (last.getAttribute('title') || last.textContent || '').trim();
                    }
                    return '';
                }""")
                place.categories = cat_from_crumbs or ""
            except Exception:
                place.categories = ""
        # Фолбек на старые селекторы
        if not place.categories:
            categories = await all_texts(page, DETAIL_CATEGORY_SELECTORS)
            place.categories = ", ".join(categories)

    # Раздел каталога: «Меню» для общепита, иначе «Товары и услуги»
    place.catalog_title = _catalog_title_for(place.categories)

    if not place.coordinates:
        place.coordinates = await parse_coordinates_from_url(page)

    if not place.social_links:
        social_links = await all_attrs(page, DETAIL_SOCIAL_LINK_SELECTORS, "href")
        site_links = await all_attrs(page, ["a[itemprop='url']", ".business-urls-view__link"], "href")
        social_links.extend(link for link in site_links if is_social_or_messenger_url(link))
        place.social_links = join_values([normalize_external_url(link) for link in social_links])

    # Фото галереи берём ТОЛЬКО со вкладки /gallery/ (ниже через scrape_gallery).
    # Сбор по карточке отключён — он тащил мусор (картографические пины pin_x2 и т.п.).

    if not place.stories:
        place.stories = await extract_stories(page, 3)

    if not place.latest_news:
        place.latest_news = await extract_latest_news(page)

    # Новые поля
    import json as _json

    if not place.avg_bill:
        place.avg_bill = await extract_avg_bill(page)

    # Особенности парсятся ниже через extract_features_bool (только bool-item)

    # Старые extract_* заменены на scrape_* через _fetch_tab ниже

    normalized_url = normalize_org_url(page.url)
    if normalized_url:
        place.url = normalized_url

    # ── НОВЫЕ ПОЛЯ ──────────────────────────────────────────────
    import json as _json

    if not place.logo_url:
        place.logo_url = await extract_logo(page)

    if not place.about_text:
        place.about_text = await extract_about(page)

    if not place.book_url:
        place.book_url = await extract_book_url(page)

    if not place.transit_stop:
        import json as _jt
        _stop = await extract_transit_stop(page)
        if _stop:
            place.transit_stop = _jt.dumps(_stop, ensure_ascii=False)

    # Рейтинг и число оценок из шапки карточки
    _rc = await extract_rating_and_count(page)
    if _rc.get("rating"):
        place.rating = _rc["rating"]
    if _rc.get("count"):
        place.reviews_count = _rc["count"]

    # Особенности парсятся ниже со вкладки /features/ (на карточке список обрезан)

    if context and place.url:
        _full_url = place.url

        print(f"[INFO] Загружаем галерею: {_tab_url(_full_url, 'gallery')}", flush=True)
        photos = await _fetch_tab(context, _tab_url(_full_url, 'gallery'), scrape_gallery, limit=20)
        print(f"[INFO] Фото найдено: {len(photos) if photos else 0}", flush=True)
        # Лого может прийти и с обычным суффиксом размера — сверяем базовые пути
        if photos and place.logo_url:
            _logo_base = photo_base(place.logo_url)
            photos = [p for p in photos if photo_base(p) != _logo_base]
        if photos:
            place.gallery_photos = ' | '.join(photos[:20])

        if not place.features:
            print(f"[INFO] Загружаем особенности: {_tab_url(_full_url, 'features')}", flush=True)
            feats = await _fetch_tab(context, _tab_url(_full_url, 'features'), extract_features_bool)
            if not feats:
                feats = await extract_features_bool(page)
            place.features = " | ".join(feats) if feats else ""
            print(f"[INFO] Особенностей найдено: {len(feats) if feats else 0}", flush=True)

        if not place.menu_items:
            # Общепит → сначала menu, остальные → сначала prices. Второй как fallback.
            is_food = _catalog_title_for(place.categories) == "Меню"
            tab_order = ['menu', 'prices'] if is_food else ['prices', 'menu']
            menu = None
            for _tab in tab_order:
                _u = _tab_url(_full_url, _tab)
                print(f"[INFO] Загружаем каталог: {_u}", flush=True)
                menu = await _fetch_tab(context, _u, scrape_catalog)
                if menu:
                    print(f"[INFO] Товаров найдено ({_tab}): {len(menu)}", flush=True)
                    break
                else:
                    print(f"[INFO] Пусто в {_tab}, пробую следующий источник", flush=True)
            if menu:
                place.menu_items = _json.dumps(menu, ensure_ascii=False)
            else:
                print("[INFO] Каталог пуст в обоих источниках", flush=True)

        if not place.reviews:
            print(f"[INFO] Загружаем отзывы: {_tab_url(_full_url, 'reviews')}", flush=True)
            revs = await _fetch_tab(context, _tab_url(_full_url, 'reviews'), scrape_reviews, limit=30)
            print(f"[INFO] Отзывов найдено: {len(revs) if revs else 0}", flush=True)
            if revs:
                place.reviews = _json.dumps(revs, ensure_ascii=False)

    return place


async def parse_detail_light(context, place: Place, args) -> Place:
    """
    Лёгкий парсинг карточки для Фазы 1: только website + базовое (название/адрес/рейтинг/категория).
    НЕ ходит по вкладкам меню/фото/отзывов — быстро, чтобы отсеять организации с сайтом.
    """
    if not place.url:
        return place
    detail_page = await context.new_page()
    try:
        await detail_page.goto(place.url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
        await detail_page.wait_for_timeout(800)
        # Website
        try:
            website_candidates = await all_attrs(
                detail_page, ["a[itemprop='url']", ".business-urls-view__link"], "href"
            )
            real = [normalize_external_url(u) for u in website_candidates if is_real_website_url(u)]
            place.website = real[0] if real else ""
        except Exception:
            place.website = ""
        # Базовое (если ещё не заполнено из карточки списка)
        if not place.rating:
            try:
                place.rating = await first_text(detail_page, RATING_SELECTORS) or ""
            except Exception:
                pass
        # Нормализуем URL карточки (для стабильного org_id)
        try:
            final_url = detail_page.url
            place.url = normalize_org_url(final_url) or place.url
        except Exception:
            pass
        return place
    except Exception as e:
        print(f"[LIGHT] {place.title}: {type(e).__name__}", flush=True)
        return place
    finally:
        try:
            await detail_page.close()
        except Exception:
            pass


async def parse_detail_in_new_page(context, place: Place, args: argparse.Namespace) -> Place:
    if not place.url:
        return place

    for attempt in range(2):  # два попытки
        detail_page = await context.new_page()
        try:
            await detail_page.goto(place.url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
            result = await parse_detail_page(detail_page, place, context)
            return result
        except Exception as e:
            if attempt == 0:
                print(f"[WARN] {place.title}: retry after error: {type(e).__name__}", flush=True)
                await detail_page.close()
                continue
            else:
                print(f"[WARN] {place.title}: failed after 2 attempts: {e}", flush=True)
                return place
        finally:
            try:
                await detail_page.close()
            except Exception:
                pass
    return place


async def scroll_results(page, previous_count: int) -> int:
    cards = await find_cards(page)
    count = await cards.count()

    if count:
        try:
            await cards.nth(count - 1).scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass

    await page.mouse.wheel(0, 2600)
    await page.wait_for_timeout(1100 + random.randint(0, 600))

    cards = await find_cards(page)
    current_count = await cards.count()
    return max(previous_count, current_count)


async def _launch_browser(playwright, args):
    """Запускает Chromium с нужными флагами. Общий код для collect_*."""
    import os, glob
    _chrome_exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "")
    if not _chrome_exe:
        _patterns = [
            "/root/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
            "/var/www/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
            "/home/www-data/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
            os.path.expanduser("~/.cache/ms-playwright/chromium*/chrome-linux64/chrome"),
        ]
        for _pat in _patterns:
            _found = sorted(glob.glob(_pat))
            if _found:
                _chrome_exe = _found[-1]
                break
    _launch_kwargs = {
        "headless": not args.show_browser,
        "slow_mo":  args.slow_mo,
        "args": [
            "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--disable-extensions", "--disable-background-networking",
            "--disable-sync", "--disable-translate", "--hide-scrollbars",
            "--metrics-recording-only", "--mute-audio", "--no-first-run",
            "--safebrowsing-disable-auto-update", "--js-flags=--max-old-space-size=256",
        ],
    }
    if _chrome_exe:
        _launch_kwargs["executable_path"] = _chrome_exe
    return await playwright.chromium.launch(**_launch_kwargs)


async def collect_single_by_url(target_url: str, args: argparse.Namespace):
    """
    Парсит ОДНУ карточку по прямой ссылке (включая короткие yandex.com/maps/-/...).
    Открывает ссылку, ждёт редиректа на карточку организации, парсит детально.
    Возвращает Place или None.
    """
    ensure_pip_playwright()

    # Mapframe/poi-ссылка (org_id в query как oid=) не редиректит на /org/:
    # карточка открывается оверлеем на карте города, вкладки каталога не
    # работают, лого не извлекается. Открываем канонический org-URL напрямую.
    if '/org/' not in urlsplit(target_url).path:
        m_oid = re.search(r'(?:[?&]oid=|oid%3D)(\d+)', target_url, re.I)
        if m_oid:
            target_url = f"https://yandex.ru/maps/org/{m_oid.group(1)}/"
            print(f"[SINGLE] Mapframe-ссылка → канонический org-URL: {target_url}", flush=True)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print_dependency_help()
        raise SystemExit(2)

    async with async_playwright() as playwright:
        browser = await _launch_browser(playwright, args)
        context = await browser.new_context(
            locale="ru-RU",
            viewport={"width": getattr(args, "width", 1280), "height": getattr(args, "height", 900)},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"),
        )
        page = await context.new_page()
        place = Place()
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
            try:
                await page.wait_for_url("**/org/**", timeout=20000)
            except Exception:
                pass
            await page.wait_for_timeout(1500)

            final_url = page.url
            place.url = normalize_org_url(final_url) or final_url

            place = await parse_detail_page(page, place, context)

            if not place.title:
                return None
            return place
        except Exception as e:
            print(f"[SINGLE] Ошибка парсинга {target_url}: {type(e).__name__}: {e}", flush=True)
            return None
        finally:
            try:
                await context.close()
                await browser.close()
            except Exception:
                pass


async def collect_places(args: argparse.Namespace) -> list[Place]:
    ensure_pip_playwright()

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print_dependency_help()
        raise SystemExit(2)

    query = args.query
    if args.city:
        query = f"{query} {args.city}"

    url = YANDEX_MAPS_URL.format(query=quote_plus(query))
    places: list[Place] = []
    seen: set[str] = set()

    async with async_playwright() as playwright:
        try:
            # Определяем путь к исполняемому файлу браузера
            import os, glob
            _chrome_exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "")
            if not _chrome_exe:
                # Ищем любой chrome в кэше Playwright
                _patterns = [
                    "/root/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
                    "/var/www/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
                    "/home/www-data/.cache/ms-playwright/chromium*/chrome-linux64/chrome",
                    os.path.expanduser("~/.cache/ms-playwright/chromium*/chrome-linux64/chrome"),
                ]
                for _pat in _patterns:
                    _found = sorted(glob.glob(_pat))
                    if _found:
                        _chrome_exe = _found[-1]
                        break
            print(f"[DEBUG] Chrome executable: {_chrome_exe or 'NOT FOUND'}", flush=True)

            _launch_kwargs = {
                "headless": not args.show_browser,
                "slow_mo":  args.slow_mo,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--disable-translate",
                    "--hide-scrollbars",
                    "--metrics-recording-only",
                    "--mute-audio",
                    "--no-first-run",
                    "--safebrowsing-disable-auto-update",
                    "--js-flags=--max-old-space-size=256",
                ],
            }
            if _chrome_exe:
                _launch_kwargs["executable_path"] = _chrome_exe

            browser = await playwright.chromium.launch(**_launch_kwargs)
        except Exception as error:
            print_browser_help(error)
            raise SystemExit(2) from error

        context = await browser.new_context(
            locale="ru-RU",
            viewport={"width": getattr(args, "width", 1280), "height": getattr(args, "height", 900)},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
            # Ждём JS-редиректа Яндекса на /search/
            try:
                await page.wait_for_url("**/search/**", timeout=15000)
            except Exception:
                pass
            try:
                await page.wait_for_selector(".search-snippet-view", timeout=10000)
            except Exception:
                pass
            await page.wait_for_timeout(1000)
            await close_popups(page)

            empty_scrolls = 0
            known_count = 0

            while len(places) < args.limit and empty_scrolls < args.max_empty_scrolls:
                cards = await find_cards(page)
                count = await cards.count()
                added_this_round = 0

                for index in range(count):
                    if len(places) >= args.limit:
                        break

                    cards = await find_cards(page)
                    if index >= await cards.count():
                        break

                    card = cards.nth(index)
                    place = await parse_card(card)

                    if not place.title:
                        continue

                    if args.require_org_url and not place.url:
                        continue

                    if is_search_echo(place.title, query) and not place.url:
                        continue

                    key = uniq_key(place)
                    if key in seen:
                        continue

                    # Фаза 1 (кандидаты): лёгкий парсинг — только website + базовое.
                    # Обычный режим: полный глубокий парсинг карточки.
                    _cand_mode = getattr(args, "candidates_mode", False)
                    if _cand_mode:
                        if place.url:
                            place = await parse_detail_light(context, place, args)
                        # В режиме кандидатов берём ТОЛЬКО тех, у кого нет сайта
                        if has_real_website(place):
                            _cb = getattr(args, "progress_cb", None)
                            if _cb:
                                _cb({"checked": True, "has_site": True, "title": place.title})
                            continue
                    else:
                        if args.open_cards and place.url:
                            place = await parse_detail_in_new_page(context, place, args)
                        if args.only_without_website and has_real_website(place):
                            continue

                    if is_search_echo(place.title, query):
                        continue

                    key = uniq_key(place)
                    if key in seen:
                        continue

                    seen.add(key)
                    places.append(place)
                    added_this_round += 1
                    print(f"[{len(places)}/{args.limit}] {place.title} | {place.address}", flush=True)
                    _cb = getattr(args, "progress_cb", None)
                    if _cb:
                        _cb({"checked": True, "has_site": False, "title": place.title,
                             "found": len(places)})

                    await page.wait_for_timeout(args.delay + random.randint(0, 600))

                new_count = await scroll_results(page, known_count)
                if added_this_round == 0 and new_count <= known_count:
                    empty_scrolls += 1
                else:
                    empty_scrolls = 0
                known_count = new_count

        finally:
            await context.close()
            await browser.close()

    return places


def write_csv(path: Path, places: list[Place]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(Place()).keys()))
        writer.writeheader()
        for place in places:
            writer.writerow(asdict(place))


def write_json(path: Path, places: list[Place]) -> None:
    data = []
    for p in places:
        d = asdict(p)
        # menu_items и reviews хранятся как JSON-строки — декодируем
        for field in ("menu_items", "reviews"):
            if d.get(field) and isinstance(d[field], str) and d[field].startswith('['):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    pass
        data.append(d)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def read_places_csv(path: Path) -> list[Place]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        rows = csv.DictReader(file)
        allowed_fields = set(asdict(Place()).keys())
        places = []

        for row in rows:
            data = {key: clean_text(value) for key, value in row.items() if key in allowed_fields}
            places.append(Place(**data))

        return places


def render_company_html(place: Place) -> str:
    title = html.escape(clean_text(place.title) or "Company")
    address = html.escape(clean_text(place.address))
    rating = html.escape(clean_text(place.rating))
    phone = html.escape(clean_text(place.phone))
    hours = html.escape(clean_text(place.hours))
    maps_url = html.escape(clean_text(place.url))
    latest_news = html.escape(clean_text(place.latest_news))

    photos = split_values(place.gallery_photos)[:3]
    stories = split_values(place.stories)[:3]
    social_links = split_values(place.social_links)

    hero_image = html.escape(photos[0]) if photos else ""
    photo_cards = "\n".join(
        f'<img src="{html.escape(photo)}" alt="{html.escape(image_alt(place, index + 1))}">'
        for index, photo in enumerate(photos)
    )
    story_cards = "\n".join(
        f"<li>{html.escape(story)}</li>"
        for story in stories
    )
    social_cards = "\n".join(
        f'<a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(url_host(link) or link)}</a>'
        for link in social_links
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --ink: #202124;
      --muted: #667085;
      --line: #e6e8ec;
      --paper: #fbfaf7;
      --brand: #1f6f5b;
      --brand-dark: #164b3f;
      --card: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background: linear-gradient(180deg, #f7f1e6 0%, var(--paper) 42%, #ffffff 100%);
    }}
    a {{ color: inherit; }}
    .page {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    .hero {{
      min-height: 520px;
      display: grid;
      grid-template-columns: 1.1fr .9fr;
      gap: 28px;
      align-items: stretch;
    }}
    .hero-copy {{
      padding: 56px 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .kicker {{
      color: var(--brand);
      font: 700 13px/1.2 Arial, sans-serif;
      letter-spacing: .12em;
      text-transform: uppercase;
      margin-bottom: 18px;
    }}
    h1 {{
      font-size: clamp(44px, 7vw, 92px);
      line-height: .92;
      margin: 0 0 22px;
      letter-spacing: 0;
    }}
    .lead {{
      max-width: 620px;
      color: #38413d;
      font: 20px/1.55 Arial, sans-serif;
      margin: 0 0 28px;
    }}
    .hero-media {{
      min-height: 420px;
      border-radius: 8px;
      overflow: hidden;
      background: #d9ddd4;
      box-shadow: 0 24px 70px rgba(27, 39, 35, .18);
    }}
    .hero-media img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .hero-media.empty {{ display: grid; place-items: center; color: var(--muted); font: 16px Arial, sans-serif; }}
    .details {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 18px 0 36px;
    }}
    .detail {{
      background: rgba(255,255,255,.72);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      font: 15px/1.45 Arial, sans-serif;
    }}
    .label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 7px;
    }}
    .section {{ padding: 42px 0; border-top: 1px solid var(--line); }}
    .section h2 {{ font-size: 34px; margin: 0 0 20px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .gallery img {{ width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: 8px; }}
    .list {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 10px; font: 16px/1.5 Arial, sans-serif; }}
    .list li, .news, .socials a {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .socials {{ display: flex; flex-wrap: wrap; gap: 10px; font: 15px Arial, sans-serif; }}
    .socials a {{ text-decoration: none; }}
    .cta {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 46px;
      padding: 0 18px;
      border-radius: 6px;
      background: var(--brand);
      color: #fff;
      text-decoration: none;
      font: 700 15px Arial, sans-serif;
    }}
    .cta:hover {{ background: var(--brand-dark); }}
    @media (max-width: 820px) {{
      .page {{ padding: 18px; }}
      .hero {{ grid-template-columns: 1fr; min-height: auto; }}
      .hero-copy {{ padding: 34px 0 0; }}
      .details {{ grid-template-columns: 1fr; }}
      .gallery {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero-copy">
        <div class="kicker">Local business</div>
        <h1>{title}</h1>
        <p class="lead">{address}</p>
        {f'<a class="cta" href="{maps_url}" target="_blank" rel="noopener noreferrer">Open on Yandex Maps</a>' if maps_url else ''}
      </div>
      <div class="hero-media{' empty' if not hero_image else ''}">
        {f'<img src="{hero_image}" alt="{title}">' if hero_image else '<span>No photo available</span>'}
      </div>
    </section>

    <section class="details">
      <div class="detail"><span class="label">Rating</span>{rating or "Not specified"}</div>
      <div class="detail"><span class="label">Phone</span>{phone or "Not specified"}</div>
      <div class="detail"><span class="label">Address</span>{address or "Not specified"}</div>
      <div class="detail"><span class="label">Hours</span>{hours or "Not specified"}</div>
    </section>

    {f'<section class="section"><h2>Gallery</h2><div class="gallery">{photo_cards}</div></section>' if photo_cards else ''}
    {f'<section class="section"><h2>Stories</h2><ul class="list">{story_cards}</ul></section>' if story_cards else ''}
    {f'<section class="section"><h2>Latest News</h2><div class="news">{latest_news}</div></section>' if latest_news else ''}
    {f'<section class="section"><h2>Social Links</h2><div class="socials">{social_cards}</div></section>' if social_cards else ''}
  </main>
</body>
</html>
"""


def write_company_pages(directory: Path, places: list[Place]) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()

    for index, place in enumerate(places, start=1):
        fallback = f"company-{index}"
        base_name = slugify(place.title, fallback)
        file_name = base_name
        suffix = 2

        while file_name in used_names:
            file_name = f"{base_name}-{suffix}"
            suffix += 1

        used_names.add(file_name)
        path = directory / f"{file_name}.html"
        path.write_text(render_company_html(place), encoding="utf-8")

    return len(places)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse Yandex Maps search results.")
    parser.add_argument("query", nargs="?", help="Search phrase, for example: coffee Moscow")
    parser.add_argument(
        "--input-csv",
        default="",
        help="Read existing parser CSV output instead of scraping Yandex Maps",
    )
    parser.add_argument("--city", default="", help="Optional city appended to the query")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of places")
    parser.add_argument("--output", default="yandex_maps_results.csv", help="Output file path")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument(
        "--only-without-website",
        action="store_true",
        help="Keep only companies without a real website",
    )
    parser.add_argument(
        "--generate-html",
        action="store_true",
        help="Generate a simple standalone HTML page for each kept company",
    )
    parser.add_argument("--html-dir", default="generated_sites", help="Directory for generated HTML pages")
    parser.add_argument("--delay", type=int, default=900, help="Delay between card actions in milliseconds")
    parser.add_argument("--timeout", type=int, default=45, help="Page load timeout in seconds")
    parser.add_argument("--max-empty-scrolls", type=int, default=5, help="Stop after this many empty scrolls")
    parser.add_argument("--width", type=int, default=1366, help="Browser viewport width")
    parser.add_argument("--height", type=int, default=900, help="Browser viewport height")
    parser.add_argument("--slow-mo", type=int, default=0, help="Slow down browser actions in milliseconds")
    parser.add_argument(
        "--require-org-url",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip results without a Yandex Maps organization URL",
    )
    parser.add_argument(
        "--open-cards",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Open each card to collect details",
    )
    parser.add_argument("--show-browser", action="store_true", help="Show the browser window")
    return parser


async def main() -> None:
    configure_terminal_encoding()
    args = build_parser().parse_args()
    output = Path(args.output)

    if args.format == "json" and output.suffix.lower() != ".json":
        output = output.with_suffix(".json")
    if args.format == "csv" and output.suffix.lower() != ".csv":
        output = output.with_suffix(".csv")

    if args.input_csv:
        places = read_places_csv(Path(args.input_csv))
    else:
        if not args.query:
            print("Query is required unless --input-csv is provided.", file=sys.stderr)
            raise SystemExit(2)
        places = await collect_places(args)

    if args.only_without_website:
        places = [place for place in places if not has_real_website(place)]

    if args.format == "json":
        write_json(output, places)
    else:
        write_csv(output, places)

    print(f"\nSaved {len(places)} places to: {output.resolve()}")

    if args.generate_html:
        count = write_company_pages(Path(args.html_dir), places)
        print(f"Generated {count} HTML pages in: {Path(args.html_dir).resolve()}")


if __name__ == "__main__":
    try:
        import asyncio

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
