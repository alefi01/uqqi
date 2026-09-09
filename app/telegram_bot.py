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


def tg_send_message(chat_id: str, text: str, reply_markup: dict | None = None) -> int | None:
    """Шлёт сообщение. Возвращает message_id отправленного сообщения или None."""
    params = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if reply_markup:
        params["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    res = tg_call("sendMessage", params)
    if isinstance(res, dict):
        return res.get("message_id")
    return None


def tg_edit_message(chat_id: str, message_id: int, text: str,
                    reply_markup: dict | None = None) -> bool:
    """Переписывает уже отправленное сообщение (карточку записи после решения)."""
    params = {"chat_id": chat_id, "message_id": message_id, "text": text,
              "disable_web_page_preview": "true"}
    # Пустой inline_keyboard убирает кнопки — иначе они остаются кликабельными.
    params["reply_markup"] = json.dumps(reply_markup or {"inline_keyboard": []},
                                        ensure_ascii=False)
    return tg_call("editMessageText", params) is not None


def tg_answer_callback(callback_id: str, text: str = "") -> None:
    """Гасит «часики» на нажатой кнопке. Без этого клиент ждёт до таймаута."""
    tg_call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def booking_keyboard(booking_id: int) -> dict:
    """Кнопки под карточкой записи. callback_data читает scheduler."""
    return {"inline_keyboard": [[
        {"text": "Подтвердить", "callback_data": f"bk:ok:{booking_id}"},
        {"text": "Отменить",    "callback_data": f"bk:no:{booking_id}"},
    ]]}


def miniapp_url() -> str:
    """Адрес мини-приложения владельца. Только https — Telegram другого не примет."""
    return f"https://lk.{settings.BASE_DOMAIN}/tg/app"


def miniapp_keyboard(label: str = "Открыть календарь") -> dict:
    """Инлайн-кнопка, открывающая мини-приложение прямо из сообщения."""
    return {"inline_keyboard": [[{"text": label, "web_app": {"url": miniapp_url()}}]]}


def tg_set_commands() -> None:
    """
    Меню команд бота и кнопка мини-приложения слева от поля ввода.

    setChatMenuButton без chat_id ставит кнопку по умолчанию для всех чатов —
    отдельно каждому владельцу её ставить не нужно.
    """
    cmds = [
        {"command": "app",      "description": "Календарь записей"},
        {"command": "today",    "description": "Записи на сегодня"},
        {"command": "tomorrow", "description": "Записи на завтра"},
        {"command": "week",     "description": "Записи на неделю"},
        {"command": "help",     "description": "Что умеет бот"},
    ]
    tg_call("setMyCommands", {"commands": json.dumps(cmds, ensure_ascii=False)})
    tg_call("setChatMenuButton", {"menu_button": json.dumps(
        {"type": "web_app", "text": "Записи", "web_app": {"url": miniapp_url()}},
        ensure_ascii=False)})


def tg_get_updates(offset: int = 0, timeout: int = 20) -> list:
    """Long-poll апдейтов. timeout — сколько сервер держит соединение (сек)."""
    # HTTP-таймаут даём чуть больше, чем long-poll timeout, иначе рвём раньше времени.
    # allowed_updates нужен явно: без него Telegram НЕ шлёт callback_query,
    # и кнопки под записями молча ничего не делают.
    res = tg_call("getUpdates", {
        "offset": offset,
        "timeout": timeout,
        "allowed_updates": json.dumps(["message", "callback_query"]),
    }, timeout=timeout + 10)
    return res if isinstance(res, list) else []
