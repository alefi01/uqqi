"""
app/telegram_bot.py — минимальный клиент Telegram Bot API для чата с сайтов (Pro).

Тот же бот, что у алертов/бэкапов (TELEGRAM_BOT_TOKEN). Через stdlib urllib,
без новых зависимостей. Приём апдейтов — long-poll getUpdates (в scheduler),
без вебхука: не нужен публичный URL/секрет.

Опциональный HTTP(S)-прокси через settings.TELEGRAM_PROXY (на случай блокировки;
SOCKS5 потребовал бы PySocks — пока не добавляем, доступ прямой).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from app.config import settings


def _opener():
    proxy = (settings.TELEGRAM_PROXY or "").strip()
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    return urllib.request.build_opener()


def tg_call(method: str, params: dict | None = None, timeout: int = 30) -> dict | None:
    """Вызывает метод Bot API. Возвращает dict result или None при ошибке."""
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not token:
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with _opener().open(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode() or "{}")
        if not body.get("ok"):
            print(f"[TG] {method} not ok: {body.get('description')}", flush=True)
            return None
        return body.get("result")
    except Exception as e:
        print(f"[TG] {method} failed: {e}", flush=True)
        return None


def tg_send_message(chat_id: str, text: str) -> int | None:
    """Шлёт сообщение. Возвращает message_id отправленного сообщения или None."""
    res = tg_call("sendMessage", {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"})
    if isinstance(res, dict):
        return res.get("message_id")
    return None


def tg_get_updates(offset: int = 0, timeout: int = 20) -> list:
    """Long-poll апдейтов. timeout — сколько сервер держит соединение (сек)."""
    # HTTP-таймаут даём чуть больше, чем long-poll timeout, иначе рвём раньше времени.
    res = tg_call("getUpdates", {"offset": offset, "timeout": timeout}, timeout=timeout + 10)
    return res if isinstance(res, list) else []
