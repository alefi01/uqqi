"""
app/yukassa.py — интеграция с ЮKassa (создание платежа, проверка webhook).
Без автосписания: разовый платёж по ссылке. Чеки — на стороне ЮKassa.
"""

from __future__ import annotations

import base64
import json
import secrets
import urllib.request
import urllib.error

from app.config import settings

API_URL = "https://api.yookassa.ru/v3/payments"


def _auth_header() -> str:
    raw = f"{settings.YUKASSA_SHOP_ID}:{settings.YUKASSA_SECRET_KEY}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def create_payment(amount: str, description: str, return_url: str,
                   metadata: dict | None = None) -> dict:
    """
    Создаёт платёж в ЮKassa. Возвращает dict с id и confirmation_url.
    Бросает RuntimeError при ошибке.
    """
    if not settings.YUKASSA_SHOP_ID or not settings.YUKASSA_SECRET_KEY:
        raise RuntimeError("ЮKassa не настроена (нет SHOP_ID/SECRET_KEY)")

    body = {
        "amount": {"value": amount, "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
        "metadata": metadata or {},
    }
    data = json.dumps(body).encode()

    req = urllib.request.Request(API_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", _auth_header())
    # Idempotence-Key защищает от дублей при ретраях
    req.add_header("Idempotence-Key", secrets.token_hex(16))

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"ЮKassa HTTP {e.code}: {detail}")
    except Exception as e:
        raise RuntimeError(f"ЮKassa недоступна: {e}")

    confirmation = result.get("confirmation", {})
    return {
        "id": result.get("id", ""),
        "status": result.get("status", ""),
        "confirmation_url": confirmation.get("confirmation_url", ""),
    }


def get_payment(payment_id: str) -> dict:
    """Запрашивает статус платежа у ЮKassa."""
    if not settings.YUKASSA_SHOP_ID:
        raise RuntimeError("ЮKassa не настроена")
    req = urllib.request.Request(f"{API_URL}/{payment_id}", method="GET")
    req.add_header("Authorization", _auth_header())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"ЮKassa: не удалось получить платёж: {e}")
