#!/usr/bin/env python3
"""
migrate.py — безопасная миграция БД uqqi.
Добавляет недостающие колонки в companies и создаёт support_messages.
Идемпотентно: можно запускать сколько угодно раз.

Запуск на сервере:
    cd /var/www/uqqi
    venv/bin/python migrate.py
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "uqqi.db"

# Колонка → SQL-тип с дефолтом
COMPANY_COLUMNS = {
    "user_id":            "INTEGER",
    "is_demo":            "BOOLEAN DEFAULT 0",
    "sub_status":         "VARCHAR(20) DEFAULT 'trial'",
    "trial_ends_at":      "DATETIME",
    "paid_until":         "DATETIME",
    "build_status":       "VARCHAR(20) DEFAULT 'ready'",
    "book_url":           "VARCHAR(500) DEFAULT ''",
    "reviews_count":      "VARCHAR(20) DEFAULT ''",
    "catalog_title":      "VARCHAR(50) DEFAULT 'Товары и услуги'",
    "about_text":         "TEXT DEFAULT ''",
    "build_log":          "TEXT DEFAULT ''",
    "build_attempts":     "INTEGER DEFAULT 0",
    "transit_stop":       "TEXT DEFAULT '{}'",
    "template_variant":   "VARCHAR(1) DEFAULT 'A'",
    "claim_code":         "VARCHAR(40)",
    "screenshot":         "VARCHAR(200) DEFAULT ''",
    "demo_until":         "DATETIME",
    "gallery_manual":     "BOOLEAN DEFAULT 0",
    "auto_main":          "BOOLEAN DEFAULT 1",
    "auto_hours":         "BOOLEAN DEFAULT 1",
    "auto_socials":       "BOOLEAN DEFAULT 1",
    "auto_requisites":    "BOOLEAN DEFAULT 1",
    "yandex_unavailable": "BOOLEAN DEFAULT 0",
    "last_parsed_at":     "DATETIME",
    "next_payment_date":  "DATETIME",
    "client_email":       "VARCHAR(255) DEFAULT ''",
    "notified_7d":        "BOOLEAN DEFAULT 0",
    "notified_3d":        "BOOLEAN DEFAULT 0",
    "notified_trial_d3":  "BOOLEAN DEFAULT 0",
    "notified_trial_d6":  "BOOLEAN DEFAULT 0",
    "welcome_sent":       "BOOLEAN DEFAULT 0",
    "last_report_at":     "DATETIME",
    # на случай свежей БД без ранних полей
    "logo_url":           "VARCHAR(500) DEFAULT ''",
    "menu_items":         "TEXT DEFAULT '[]'",
    "reviews":            "TEXT DEFAULT '[]'",
    "features":           "TEXT DEFAULT '[]'",
    "avg_bill":           "VARCHAR(50) DEFAULT ''",
    "org_name":           "VARCHAR(500) DEFAULT ''",
    "org_type":           "VARCHAR(50) DEFAULT ''",
    "org_inn":            "VARCHAR(20) DEFAULT ''",
}


def existing_columns(cur, table):
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def table_exists(cur, table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def main():
    if not DB_PATH.exists():
        print(f"[migrate] БД не найдена: {DB_PATH}")
        print("[migrate] Она создастся автоматически при первом запуске приложения.")
        sys.exit(0)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    if not table_exists(cur, "companies"):
        print("[migrate] Таблицы companies нет — создастся приложением. Пропуск.")
        conn.close()
        sys.exit(0)

    cols = existing_columns(cur, "companies")
    added = 0
    for name, ddl in COMPANY_COLUMNS.items():
        if name not in cols:
            cur.execute(f"ALTER TABLE companies ADD COLUMN {name} {ddl}")
            print(f"[migrate] + companies.{name}")
            added += 1

    # support_messages
    if not table_exists(cur, "support_messages"):
        cur.execute("""
            CREATE TABLE support_messages (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                company_slug  VARCHAR(120) DEFAULT '',
                company_title VARCHAR(255) DEFAULT '',
                reply_email   VARCHAR(255) DEFAULT '',
                message       TEXT DEFAULT '',
                is_read       BOOLEAN DEFAULT 0,
                created_at    DATETIME
            )
        """)
        print("[migrate] + таблица support_messages")
        added += 1

    # visits (метрика)
    if not table_exists(cur, "visits"):
        cur.execute("""
            CREATE TABLE visits (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                target       VARCHAR(120) DEFAULT '',
                day          VARCHAR(10) DEFAULT '',
                visitor_hash VARCHAR(64) DEFAULT '',
                created_at   DATETIME
            )
        """)
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_visit_unique "
            "ON visits (target, day, visitor_hash)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_visits_target ON visits (target)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_visits_day ON visits (day)")
        print("[migrate] + таблица visits")
        added += 1

    # visit_logs (детальная метрика: IP, гео, боты; ретенция 90 дней)
    if not table_exists(cur, "visit_logs"):
        cur.execute("""
            CREATE TABLE visit_logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                target       VARCHAR(120) DEFAULT '',
                ip           VARCHAR(45) DEFAULT '',
                city         VARCHAR(120) DEFAULT '',
                country      VARCHAR(80) DEFAULT '',
                user_agent   VARCHAR(400) DEFAULT '',
                is_bot       BOOLEAN DEFAULT 0,
                visitor_hash VARCHAR(64) DEFAULT '',
                created_at   DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vlogs_target ON visit_logs (target)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vlogs_ip ON visit_logs (ip)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vlogs_created ON visit_logs (created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vlogs_bot ON visit_logs (is_bot)")
        print("[migrate] + таблица visit_logs")
        added += 1

    # users (аккаунты кабинета)
    if not table_exists(cur, "users"):
        cur.execute("""
            CREATE TABLE users (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                email          VARCHAR(255) UNIQUE NOT NULL,
                password_hash  VARCHAR(255) NOT NULL,
                email_verified BOOLEAN DEFAULT 0,
                verify_token   VARCHAR(64) DEFAULT '',
                reset_token    VARCHAR(64) DEFAULT '',
                reset_expires  DATETIME,
                agreed_at      DATETIME,
                agreed_ip      VARCHAR(64) DEFAULT '',
                trial_used     BOOLEAN DEFAULT 0,
                created_at     DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_users_verify ON users (verify_token)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_users_reset ON users (reset_token)")
        print("[migrate] + таблица users")
        added += 1
    else:
        # users уже есть — добавим trial_used если нет
        ucols = existing_columns(cur, "users")
        if "trial_used" not in ucols:
            cur.execute("ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT 0")
            print("[migrate] + users.trial_used")
            added += 1
        if "pending_claim_code" not in ucols:
            cur.execute("ALTER TABLE users ADD COLUMN pending_claim_code VARCHAR(40) DEFAULT ''")
            print("[migrate] + users.pending_claim_code")
            added += 1

    # parse_candidates (двухфазный парсинг: кандидаты без сайта)
    if not table_exists(cur, "parse_candidates"):
        cur.execute("""
            CREATE TABLE parse_candidates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id      VARCHAR(40) DEFAULT '',
                title       VARCHAR(200) DEFAULT '',
                address     VARCHAR(400) DEFAULT '',
                yandex_url  VARCHAR(500) DEFAULT '',
                query       VARCHAR(200) DEFAULT '',
                status      VARCHAR(20) DEFAULT 'new',
                company_id  INTEGER,
                created_at  DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cand_org ON parse_candidates (org_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_cand_query ON parse_candidates (query)")
        print("[migrate] + таблица parse_candidates")
        added += 1

    # payments (платежи ЮKassa)
    if not table_exists(cur, "payments"):
        cur.execute("""
            CREATE TABLE payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id   VARCHAR(64) UNIQUE,
                user_id      INTEGER,
                company_id   INTEGER,
                company_slug VARCHAR(120) DEFAULT '',
                amount       VARCHAR(20) DEFAULT '1990.00',
                days         INTEGER DEFAULT 30,
                status       VARCHAR(20) DEFAULT 'pending',
                processed    BOOLEAN DEFAULT 0,
                created_at   DATETIME,
                paid_at      DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_payments_pid ON payments (payment_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_payments_user ON payments (user_id)")
        print("[migrate] + таблица payments")
        added += 1
    else:
        # Добавляем недостающие колонки в существующую payments (тарифы)
        pay_cols = existing_columns(cur, "payments")
        if "days" not in pay_cols:
            cur.execute("ALTER TABLE payments ADD COLUMN days INTEGER DEFAULT 30")
            print("[migrate] + payments.days")
            added += 1

    # Пометить существующие сайты как демо (без владельца) — разово при первой миграции.
    # Только если колонка user_id только что добавлена (все user_id пустые).
    try:
        total = cur.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        with_user = cur.execute(
            "SELECT COUNT(*) FROM companies WHERE user_id IS NOT NULL"
        ).fetchone()[0]
        # Если ни у одного сайта нет владельца — это старые сайты, метим их демо
        if total > 0 and with_user == 0:
            n = cur.execute("UPDATE companies SET is_demo = 1 WHERE user_id IS NULL").rowcount
            if n:
                print(f"[migrate] помечено демо-сайтов: {n}")
    except Exception as e:
        print(f"[migrate] пометка демо пропущена: {e}")

    conn.commit()
    conn.close()
    print(f"[migrate] Готово. Изменений: {added}")


if __name__ == "__main__":
    main()
