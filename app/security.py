"""
security.py — access-лог активности и rate limiting.
Access-лог: метод, путь, IP, статус, время, User-Agent — БЕЗ тел запросов
(чтобы не писать пароли/токены). Для отслеживания атак и активности.
Rate limiter: ограничивает частоту запросов к чувствительным endpoint'ам (вход, регистрация).
"""
import time
import os
from collections import defaultdict, deque
from datetime import datetime

# ── ACCESS-ЛОГ ────────────────────────────────────────────────────────────────
ACCESS_LOG_PATH = "logs/access.log"
_log_ready = False


def _ensure_log_dir():
    global _log_ready
    if not _log_ready:
        os.makedirs(os.path.dirname(ACCESS_LOG_PATH), exist_ok=True)
        _log_ready = True


def log_access(ip: str, method: str, path: str, status: int, ua: str, ms: float):
    """Пишет строку access-лога. Без тел запросов — только метаданные."""
    try:
        _ensure_log_dir()
        ts = datetime.utcnow().isoformat()
        # таб-разделённый формат, легко парсить и грепать
        line = f"{ts}\t{ip}\t{method}\t{path}\t{status}\t{ms:.0f}ms\t{ua[:200]}\n"
        with open(ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # логирование не должно ломать запрос


def client_ip(request) -> str:
    """Достаёт реальный IP за nginx (X-Forwarded-For)."""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


# ── RATE LIMITER ──────────────────────────────────────────────────────────────
# Скользящее окно в памяти: {key: deque[timestamps]}.
# Простое, без внешних зависимостей. При рестарте сбрасывается (это ок).
_buckets: dict = defaultdict(deque)

# Правила: путь (по префиксу) → (макс. запросов, окно в секундах)
RATE_RULES = [
    ("/lk/api/register",      (5, 300)),    # 5 регистраций / 5 мин с IP
    ("/lk/api/login",         (10, 300)),   # 10 попыток входа / 5 мин
    ("/lk/api/resend-verify", (5, 600)),    # 5 переотправок / 10 мин
    ("/lk/api/reset",         (5, 600)),    # сброс пароля
    ("/lk/api/forgot",        (5, 600)),
    ("/api/yukassa/webhook",  (120, 60)),   # webhook — щедро, но от флуда
]
# Дефолтный общий лимит на чувствительные пути панели (брутфорс входа в панель)
PANEL_LOGIN_RULE = (15, 300)  # 15 попыток / 5 мин


def _match_rule(path: str):
    for prefix, rule in RATE_RULES:
        if path.startswith(prefix):
            return prefix, rule
    return None, None


def check_rate_limit(ip: str, path: str) -> bool:
    """
    True — запрос разрешён, False — превышен лимит.
    Ограничиваем только чувствительные endpoint'ы (не всё подряд).
    """
    key_prefix, rule = _match_rule(path)
    # Вход в панель (путь панели + /login)
    if rule is None and path.endswith("/login") and "/api/" not in path:
        key_prefix, rule = "panel-login", PANEL_LOGIN_RULE
    if rule is None:
        return True  # путь не лимитируется

    max_req, window = rule
    now = time.time()
    key = f"{ip}:{key_prefix}"
    bucket = _buckets[key]
    # выкидываем устаревшие метки
    while bucket and bucket[0] < now - window:
        bucket.popleft()
    if len(bucket) >= max_req:
        return False
    bucket.append(now)
    return True


def cleanup_buckets():
    """Периодическая чистка пустых бакетов (вызывать из scheduler)."""
    now = time.time()
    empty = []
    for key, bucket in _buckets.items():
        while bucket and bucket[0] < now - 3600:
            bucket.popleft()
        if not bucket:
            empty.append(key)
    for key in empty:
        _buckets.pop(key, None)
