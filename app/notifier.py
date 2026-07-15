"""
app/notifier.py — алерты в Telegram (мониторинг).

Тот же бот, что и для бэкапов (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID из .env).
Через stdlib urllib — без новых зависимостей. На проде HTTPS идёт напрямую.

Троттлинг по ключу: один и тот же алерт (напр. 'disk') не чаще раза в
throttle_sec — иначе при постоянной проблеме бот зафлудит чат.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from app.config import settings

# key -> unix-время последней отправки
_last_sent: dict[str, float] = {}


def send_telegram(text: str, key: str | None = None, throttle_sec: int = 3600) -> bool:
    """
    Шлёт текстовый алерт в Telegram. Возвращает True при успешной отправке.
    key задаёт троттлинг: повтор по тому же ключу раньше throttle_sec — пропуск.
    """
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    chat = (settings.TELEGRAM_CHAT_ID or "").strip()
    if not token or not chat:
        return False

    if key is not None:
        now = time.time()
        if now - _last_sent.get(key, 0.0) < throttle_sec:
            return False  # ещё рано — троттлинг
        _last_sent[key] = now

    try:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode() or "{}")
            return bool(body.get("ok"))
    except Exception as e:
        print(f"[NOTIFY] Telegram send failed: {e}", flush=True)
        return False
