# ============================================================
# yandex_links.py — разбор ссылок Яндекс.Карт, вставленных клиентом в ЛК.
#
# Принимаем только форматы, которые ведут на карточку организации:
#   - короткий:  https://yandex.ru/maps/-/CDe4bU8
#   - org:       https://yandex.ru/maps/org/<slug>/<org_id>[/<вкладка>/][?si=...]
#   - mapframe:  .../maps/...?...oid=<org_id>... (в т.ч. urlencoded в poi[uri])
# Ссылки «просто на карту» (город, маршрут) отклоняем: парсер не найдёт карточку,
# сборка упадёт, а триал у клиента уже будет помечен использованным.
#
# ВАЖНО: та же логика продублирована на фронте — validYandex() в
# static/lk/dashboard.jsx, app.bundle.jsx и app.bundle.js. Менять синхронно.
#
# Модуль без зависимостей от FastAPI/SQLAlchemy — его импортирует
# scripts/test_yandex_links.py без поднятия приложения.
# ============================================================

import re

# Домены Яндекс.Карт: «Поделиться» даёт .ru/.com, у соседей — .by/.kz/.uz
_HOST = r'(?:maps\.)?yandex\.(?:ru|com|by|kz|uz)'

# Любая ссылка Яндекс.Карт внутри вставленного текста
# (с телефона копируется блок: название + адрес + ссылка)
YANDEX_URL_IN_TEXT = re.compile(rf'https?://{_HOST}/maps/[^\s]+')

# Короткий формат «Поделиться»: /maps/-/CDe4bU8
SHORT_RE = re.compile(rf'^https?://{_HOST}/maps/-/[A-Za-z0-9_~-]+/?$')

# Org-формат: /maps/org/<slug>/<org_id>; slug может отсутствовать
ORG_ID_IN_PATH_RE = re.compile(r'/maps/org/(?:[^/]+/)?(\d+)')

# Mapframe/poi: org_id в query как oid= (в т.ч. urlencoded внутри poi[uri])
OID_RE = re.compile(r'(?:[?&]oid=|oid%3D)(\d+)', re.I)

ERR_NO_LINK = "Вставьте ссылку на Яндекс.Карты (можно вместе с названием и адресом)."
ERR_NOT_ORG = ("Ссылка ведёт не на карточку организации. Откройте карточку вашей "
               "компании в Яндекс.Картах, нажмите «Поделиться» и скопируйте ссылку.")


def extract_org_id(url: str) -> str | None:
    """Извлекает числовой org_id из ссылки (org-формат или mapframe oid=)."""
    if not url:
        return None
    m = ORG_ID_IN_PATH_RE.search(url)
    if m:
        return m.group(1)
    m = OID_RE.search(url)
    if m:
        return m.group(1)
    return None


def extract_yandex_url(raw: str) -> tuple[str | None, str | None]:
    """
    Достаёт ссылку Яндекс.Карт из вставленного текста и проверяет,
    что она ведёт на карточку организации.
    Возвращает (url, None) при успехе или (None, текст_ошибки) при отказе.
    """
    if not raw or not raw.strip():
        return None, ERR_NO_LINK
    m = YANDEX_URL_IN_TEXT.search(raw.strip())
    if not m:
        return None, ERR_NO_LINK
    url = m.group(0).rstrip('.,;)')

    without_fragment = url.split('#', 1)[0]
    without_query = without_fragment.split('?', 1)[0]

    # Короткая и org-ссылки самодостаточны — query (?si=...) отбрасываем
    if SHORT_RE.match(without_query):
        return without_query, None
    if ORG_ID_IN_PATH_RE.search(without_query):
        return without_query, None
    # Mapframe: org_id живёт в query (oid=/poi[uri]=...), срезать нельзя
    if OID_RE.search(without_fragment):
        return without_fragment, None
    return None, ERR_NOT_ORG
