"""
geoip.py — определение города/страны по IP через локальную базу MaxMind GeoLite2-City.
База лежит в geo/GeoLite2-City.mmdb (не в git, скачивается отдельно).
Ридер кешируется. Если база/библиотека недоступны — молча возвращает пустое.
"""
import os

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "geo", "GeoLite2-City.mmdb")
_reader = None
_tried = False


def _get_reader():
    global _reader, _tried
    if _tried:
        return _reader
    _tried = True
    try:
        import geoip2.database
        if os.path.exists(_DB_PATH):
            _reader = geoip2.database.Reader(_DB_PATH)
            print(f"[GEOIP] База загружена: {_DB_PATH}", flush=True)
        else:
            print(f"[GEOIP] База не найдена: {_DB_PATH}", flush=True)
    except Exception as e:
        print(f"[GEOIP] Недоступно: {e}", flush=True)
        _reader = None
    return _reader


def lookup(ip: str) -> dict:
    """
    Возвращает {'city': str, 'country': str} по IP.
    Пустые строки, если не удалось определить (локальный IP, нет базы и т.п.).
    """
    result = {"city": "", "country": ""}
    if not ip:
        return result
    # Приватные/локальные адреса пропускаем
    if ip.startswith(("127.", "10.", "192.168.", "172.16.", "::1", "fc", "fd")):
        return result
    reader = _get_reader()
    if not reader:
        return result
    try:
        resp = reader.city(ip)
        # Русское название города, если есть, иначе английское
        city = ""
        if resp.city and resp.city.names:
            city = resp.city.names.get("ru") or resp.city.names.get("en") or ""
        country = ""
        if resp.country and resp.country.names:
            country = resp.country.names.get("ru") or resp.country.names.get("en") or ""
        result["city"] = city
        result["country"] = country
    except Exception:
        pass
    return result


# Детект ботов по User-Agent
_BOT_MARKERS = (
    "bot", "crawler", "spider", "slurp", "crawl", "curl", "wget", "python-requests",
    "scrapy", "headless", "phantom", "selenium", "http-client", "go-http", "java/",
    "libwww", "okhttp", "apache-httpclient", "yandex", "google", "bing", "baidu",
    "duckduck", "facebookexternalhit", "telegrambot", "whatsapp", "semrush", "ahrefs",
    "mj12bot", "dotbot", "petalbot", "gptbot", "ccbot", "claudebot", "bytespider",
)


def is_bot(user_agent: str) -> bool:
    """Простой детект бота по User-Agent."""
    if not user_agent:
        return True  # пустой UA — почти всегда бот/скрипт
    ua = user_agent.lower()
    return any(m in ua for m in _BOT_MARKERS)
