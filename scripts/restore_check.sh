#!/usr/bin/env bash
# ============================================================
# restore_check.sh — проверка, что бэкап реально разворачивается и БД цела.
# Прод НЕ трогает: распаковывает во временную папку, проверяет, удаляет.
#
# Использование:
#   scripts/restore_check.sh backups/uqqi_20260715_040000.db.gz
#   scripts/restore_check.sh            # без аргумента — берёт самый свежий из backups/
# ============================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${UQQI_BACKUP_DIR:-$APP_DIR/backups}"

GZ="${1:-}"
if [ -z "$GZ" ]; then
    GZ="$(ls -1t "$BACKUP_DIR"/uqqi_*.db.gz 2>/dev/null | head -1 || true)"
    [ -n "$GZ" ] || { echo "Нет бэкапов в $BACKUP_DIR"; exit 1; }
    echo "Проверяю самый свежий: $GZ"
fi
[ -f "$GZ" ] || { echo "Файл не найден: $GZ"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

gunzip -c "$GZ" > "$TMP/restored.db" || { echo "✖ gunzip не удался"; exit 1; }

if [ "$(sqlite3 "$TMP/restored.db" 'PRAGMA integrity_check;' | head -1)" = "ok" ]; then
    echo "✓ integrity_check: ok"
else
    echo "✖ integrity_check: БД ПОВРЕЖДЕНА"
    exit 1
fi

echo "Счётчики ключевых таблиц:"
for t in companies users payments leads visit_logs parse_candidates; do
    n="$(sqlite3 "$TMP/restored.db" "SELECT count(*) FROM $t;" 2>/dev/null || echo '— нет таблицы')"
    printf '  %-18s %s\n' "$t" "$n"
done

echo "✓ Восстановление успешно. Тестовая копия удалена."
