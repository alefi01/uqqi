# uqqi.ru — деплой с нуля на Debian

SaaS: автоматическая генерация сайтов для малого бизнеса из карточек Яндекс.Карт.
Стек: FastAPI + SQLite + Jinja2 + Playwright, фронт кабинета на React (CDN + Babel).

---

## 0. Что понадобится

- VPS с Debian 11/12, root-доступ
- Домен (пример: `uqqi.ru`) с **wildcard**-записью `*.uqqi.ru` → IP сервера
- SMTP-доступ для писем (у нас — почта Beget)
- Аккаунт ЮKassa (shop_id + секретный ключ)
- База GeoLite2-City.mmdb (для гео в метрике) — скачивается отдельно

---

## 1. Системные пакеты

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx sqlite3 git curl \
               certbot python3-certbot-nginx
```

Node (нужен только если будешь пересобирать бандл кабинета; в архиве уже собран):

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs
```

---

## 2. Код проекта

```bash
mkdir -p /var/www/uqqi
cd /var/www/uqqi
# распаковать архив проекта сюда (uqqi/* → /var/www/uqqi/)
```

Структура после распаковки:

```
/var/www/uqqi/
├── app/                 # backend (main, owner, cabinet, parser, security, geoip, ...)
├── templates/           # витрины сайтов, лендинг, панель, ЛК, юр-страницы
├── static/              # lk/ (React-кабинет), js/, requisites.png, screenshots/
├── yandex_maps_parser.py
├── migrate.py
├── requirements.txt
└── uqqi.service, uqqi.nginx.conf   # примеры конфигов
```

---

## 3. Python-окружение

```bash
cd /var/www/uqqi
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

Playwright (браузер для парсинга и скриншотов):

```bash
venv/bin/playwright install --with-deps chromium
```

Если ставишь под root, браузер ляжет в `/root/.cache/ms-playwright` — приложение это учитывает.

---

## 4. Конфигурация (.env)

Создай `/var/www/uqqi/.env`:

```ini
# Секретный путь к owner-панели (любая случайная строка)
PANEL_PATH=<случайная_строка>
PANEL_USER=<логин>
PANEL_PASSWORD=<СЛОЖНЫЙ_пароль>

BASE_DOMAIN=uqqi.ru

# SMTP (пример для Beget)
SMTP_HOST=smtp.beget.com
SMTP_PORT=465
SMTP_USER=support@uqqi.ru
SMTP_PASSWORD=<пароль_почты>
SMTP_FROM=support@uqqi.ru

# ЮKassa
YUKASSA_SHOP_ID=<shop_id>
YUKASSA_SECRET_KEY=<secret_key>
SUBSCRIPTION_PRICE=990.00
```

Права:

```bash
chmod 600 /var/www/uqqi/.env
```

---

## 5. GeoIP-база (для метрики: города посетителей)

```bash
mkdir -p /var/www/uqqi/geo
# положить скачанный файл сюда:
#   /var/www/uqqi/geo/GeoLite2-City.mmdb
```

Без базы всё работает — просто города в метрике будут пустыми.

---

## 6. Папки для рантайма

```bash
cd /var/www/uqqi
mkdir -p logs static/screenshots
```

- `logs/access.log` — access-лог (кто, куда, статус; без тел запросов)
- `static/screenshots/` — скриншоты сайтов для материалов клиенту

---

## 7. База данных

```bash
cd /var/www/uqqi
venv/bin/python migrate.py
```

Создаст/обновит таблицы: `companies`, `users`, `sessions`, `leads`,
`support_messages`, `visits`, `visit_logs`, `payments`, `parse_candidates`.

Миграция идемпотентна — можно запускать повторно после обновлений.

---

## 8. systemd-сервис

`/etc/systemd/system/uqqi.service`:

```ini
[Unit]
Description=uqqi.ru FastAPI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/uqqi
EnvironmentFile=/var/www/uqqi/.env
ExecStart=/var/www/uqqi/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now uqqi
systemctl status uqqi
```

---

## 9. Nginx

`/etc/nginx/sites-available/uqqi`:

```nginx
server {
    listen 80;
    server_name uqqi.ru www.uqqi.ru *.uqqi.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name uqqi.ru www.uqqi.ru *.uqqi.ru;

    ssl_certificate     /etc/letsencrypt/live/uqqi.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/uqqi.ru/privkey.pem;

    client_max_body_size 20m;

    location /static/ {
        alias /var/www/uqqi/static/;
        expires 7d;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/uqqi /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

**Важно:** `X-Forwarded-For` обязателен — по нему определяются IP в метрике и работает rate limiting.

---

## 10. SSL (wildcard)

Поддомены сайтов (`slug.uqqi.ru`) требуют **wildcard**-сертификат, а он выдаётся
только через DNS-01:

```bash
certbot certonly --manual --preferred-challenges dns \
  -d uqqi.ru -d '*.uqqi.ru'
```

Certbot попросит добавить TXT-запись `_acme-challenge.uqqi.ru` в DNS.
После выпуска — `systemctl reload nginx`.

Продление: `certbot renew` (для wildcard/manual удобнее использовать DNS-плагин
своего регистратора, иначе продлевать вручную раз в 90 дней).

---

## 11. DNS

| Тип | Имя | Значение |
|-----|-----|----------|
| A   | `@` | IP сервера |
| A   | `*` | IP сервера |
| A   | `lk` | IP сервера |

Плюс для почты — SPF/DKIM/DMARC от твоего почтового провайдера
(иначе письма подтверждения будут улетать в спам).

---

## 12. ЮKassa

В личном кабинете ЮKassa → HTTP-уведомления:

```
https://lk.uqqi.ru/api/yukassa/webhook
```

События: `payment.succeeded`, `payment.canceled`.

---

## 13. Проверка после запуска

```bash
journalctl -u uqqi -f
```

Что должно быть в логах при старте:

- `[SCHEDULER] Фоновые задачи запущены (биллинг + автообновление + watchdog + очистка логов)`
- `[GEOIP] База загружена: /var/www/uqqi/geo/GeoLite2-City.mmdb` (если положил базу)

Проверить руками:

1. `https://uqqi.ru` — лендинг
2. `https://uqqi.ru/<PANEL_PATH>` — owner-панель (логин/пароль из .env)
3. `https://lk.uqqi.ru` — кабинет клиента
4. В панели → «Поиск клиентов» → найти организации без сайта → «Создать сайт»
5. `https://<slug>.uqqi.ru/` — сгенерированный сайт
6. `https://<slug>.uqqi.ru/demo` — он же + окошко «Приобрести»

---

## Как всё работает (кратко)

**Двухфазный парсинг.** Фаза 1: поиск организаций **без сайта** (лёгкий парсинг,
только проверка наличия сайта) → список кандидатов в БД (переживает рестарт).
Фаза 2: кнопка «Создать сайт» у кандидата → глубокий парсинг (меню, фото,
отзывы) → готовый сайт с claim-кодом.

**Claim-продажа.** Готовый сайт живёт на `slug.uqqi.ru` (закрыт от индексации).
Клиенту отправляется ссылка `slug.uqqi.ru/demo` — там сайт + окошко «Приобрести».
Клиент регистрируется → после подтверждения email сайт привязывается к его
аккаунту + триал 7 дней. Дальше 990₽/мес за сайт.

Материалы для продажи — кнопка «📦 Клиенту» в панели: скриншот (по кнопке),
готовый текст предложения, claim-ссылка.

**Автообновление.** Раз в сутки данные сайтов обновляются с Яндекс.Карт по
**прямому URL** карточки с проверкой `org_id` — если ссылка ведёт на другую
организацию, данные не перезаписываются (защита от подмены).

**Метрика.** Уники/просмотры по периодам, таблицы IP с городами (GeoIP),
разделение боты/люди, экспорт логов. IP хранятся 90 дней, потом удаляются.

**Безопасность.** Access-лог (без тел запросов — пароли не пишутся),
rate limiting на вход/регистрацию, secure-куки, секретный путь панели.

---

## Обновление кода

```bash
cd /var/www/uqqi
# залить новые файлы поверх (.env, uqqi.db, geo/ — НЕ трогать)
venv/bin/python migrate.py
systemctl restart uqqi
```

Панель после обновления открывать с **Ctrl+Shift+R** (сброс кеша).

---

## Что осталось сделать (известные пробелы)

- 🔴 **Бэкапы БД** — не настроены. Обязательно до реальных клиентов.
- 🔴 **Проверка подписи webhook ЮKassa** — сейчас статус платежа
  перепроверяется через API ЮKassa, но при сбое проверки код доверяет
  запросу (fail-open). Стоит добавить HMAC-проверку подписи.
- 🟠 Мониторинг/алерты при падении сервиса и ошибках сборки.
- 🟠 Юридические документы (оферта/политика) — не проверены юристом.
- 🟡 SQLite при росте нагрузки — узкое место, миграция на PostgreSQL.
