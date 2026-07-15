#!/usr/bin/env bash
# ============================================================
# backup_db.sh — ежедневный бэкап SQLite с вывозом в Telegram.
#
# Что делает:
#   1. Проверяет целостность живой БД (PRAGMA integrity_check)
#   2. Горячий консистентный снимок через `sqlite3 .backup` (НЕ cp —
#      cp во время записи даёт битый файл)
#   3. Проверяет целостность снимка
#   4. gzip
#   5. ВЫВОЗ копии в Telegram (бэкап на том же диске бесполезен при смерти VPS)
#   6. Ротация: удаляет архивы старше RETENTION_DAYS
#   При любой ошибке — алерт в Telegram и выход с кодом 1.
#
# Требует в .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
# Крон (пример, ежедневно в 04:00):
#   0 4 * * * /var/www/uqqi/scripts/backup_db.sh >> /var/www/uqqi/logs/backup.log 2>&1
# ============================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB="${UQQI_DB:-$APP_DIR/uqqi.db}"
BACKUP_DIR="${UQQI_BACKUP_DIR:-$APP_DIR/backups}"
ENV_FILE="${UQQI_ENV:-$APP_DIR/.env}"
RETENTION_DAYS="${UQQI_BACKUP_RETENTION:-14}"

# Читаем ТОЛЬКО нужные ключи из .env (не source — там могут быть спецсимволы)
read_env() {
    [ -f "$ENV_FILE" ] || return 0
    grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}
TG_TOKEN="$(read_env TELEGRAM_BOT_TOKEN)"
TG_CHAT="$(read_env TELEGRAM_CHAT_ID)"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

notify() {  # best-effort текстовый алерт
    [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ] || return 0
    curl -sS --max-time 30 "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -d chat_id="$TG_CHAT" --data-urlencode text="$1" >/dev/null 2>&1 || true
}

fail() {
    echo "[$(ts)] [BACKUP] ✖ ОШИБКА: $1" >&2
    notify "🔴 uqqi backup FAILED: $1"
    exit 1
}

integrity_ok() {  # $1 = путь к .db, возвращает 0 если ok
    [ "$(sqlite3 "$1" 'PRAGMA integrity_check;' 2>/dev/null | head -1)" = "ok" ]
}

command -v sqlite3 >/dev/null || fail "sqlite3 не установлен"
command -v curl    >/dev/null || fail "curl не установлен"
mkdir -p "$BACKUP_DIR"
[ -f "$DB" ] || fail "БД не найдена: $DB"

STAMP="$(date +%Y%m%d_%H%M%S)"
RAW="$BACKUP_DIR/uqqi_${STAMP}.db"
GZ="${RAW}.gz"

echo "[$(ts)] [BACKUP] Старт: $DB"

# 1. Целостность живой БД
integrity_ok "$DB" || fail "integrity_check живой БД не 'ok' — БД повреждена, бэкап отменён"

# 2. Горячий снимок (.backup держит консистентность даже при записи в БД)
sqlite3 "$DB" ".backup '$RAW'" || fail "sqlite3 .backup не удался"
[ -s "$RAW" ] || fail "снимок пустой: $RAW"

# 3. Целостность снимка
integrity_ok "$RAW" || { rm -f "$RAW"; fail "снимок повреждён (integrity_check)"; }

# 4. Сжатие
gzip -f "$RAW" || fail "gzip не удался"
SIZE="$(du -h "$GZ" | cut -f1)"

# 5. Вывоз в Telegram (обязателен — иначе копия только на том же диске)
if [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
    RESP="$(curl -sS --max-time 180 \
        -F document=@"$GZ" \
        -F chat_id="$TG_CHAT" \
        -F caption="🗄 uqqi.db бэкап ${STAMP} (${SIZE})" \
        "https://api.telegram.org/bot${TG_TOKEN}/sendDocument" 2>&1)" || fail "curl к Telegram упал"
    echo "$RESP" | grep -q '"ok":true' || fail "Telegram отклонил файл: ${RESP:0:200}"
    echo "[$(ts)] [BACKUP] Вывезен в Telegram"
else
    echo "[$(ts)] [BACKUP] ⚠ TELEGRAM_BOT_TOKEN/CHAT_ID не заданы — вывоз ПРОПУЩЕН (копия только локально!)" >&2
fi

# 6. Ротация
DELETED="$(find "$BACKUP_DIR" -maxdepth 1 -name 'uqqi_*.db.gz' -mtime +"$RETENTION_DAYS" -print -delete | wc -l)"

echo "[$(ts)] [BACKUP] ✓ Готово: $GZ ($SIZE); удалено старых: $DELETED; ретенция ${RETENTION_DAYS} дн."
