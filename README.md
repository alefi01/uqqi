# uqqi.ru — сервис сайтов для малого бизнеса

Система автоматически создаёт одностраничные сайты для компаний
у которых нет сайта. Данные берутся из Яндекс Карт, сайты
публикуются на субдоменах `название.uqqi.ru`.

---

## Структура проекта

```
uqqi/
├── app/
│   ├── __init__.py
│   ├── config.py          # настройки из .env
│   ├── main.py            # FastAPI: публичные сайты + API клиента
│   ├── models.py          # БД: Company, Lead
│   ├── owner.py           # панель владельца: парсер, управление сайтами
│   └── parser.py          # парсинг полей CSV в структуры для БД
├── scripts/
│   ├── __init__.py
│   └── import_csv.py      # импорт компаний из CSV вручную
├── static/
│   └── uploads/           # фото клиентов (создаётся автоматически)
├── templates/
│   ├── landing.html       # лендинг uqqi.ru
│   ├── site.html          # публичный сайт компании
│   ├── admin_login.html   # вход в панель клиента
│   ├── admin_panel.html   # панель редактирования клиента
│   ├── owner_login.html   # вход в панель владельца
│   └── owner_panel.html   # панель владельца (парсер, сайты, заявки)
├── yandex_maps_parser.py  # парсер Яндекс Карт (Playwright)
├── .env.example
├── requirements.txt
├── uqqi.nginx.conf
└── uqqi.service
```

---

## Деплой на сервер (Debian 12)

### 1. Системные пакеты

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot
```

### 2. Файлы проекта

Скопируйте содержимое архива на сервер:

```bash
mkdir -p /var/www/uqqi
# с локальной машины:
scp -r ./uqqi/* root@ВАШ_IP:/var/www/uqqi/
```

### 3. Виртуальное окружение

```bash
cd /var/www/uqqi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Для парсера дополнительно:
pip install playwright
playwright install chromium
playwright install-deps chromium
```

### 4. Файл .env

```bash
cp .env.example .env
nano .env
```

Обязательно замените `SECRET_KEY` на случайную строку:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Итоговый `.env`:

```
BASE_DOMAIN=uqqi.ru
SECRET_KEY=ваша-случайная-строка
DATABASE_URL=sqlite:///./uqqi.db
UPLOAD_DIR=./static/uploads
DEBUG=False

PANEL_PATH=BcJf69nkkikxqBj8
PANEL_USER=admin
PANEL_PASSWORD=qsc123zx
```

### 5. DNS

В панели управления доменом добавьте две A-записи:

| Тип | Имя | Значение      |
|-----|-----|---------------|
| A   | @   | IP вашего VPS |
| A   | *   | IP вашего VPS |

Запись `*` — wildcard, направляет все субдомены на ваш сервер.

### 6. SSL (wildcard-сертификат)

Wildcard требует подтверждения через DNS TXT-запись:

```bash
certbot certonly --manual --preferred-challenges dns \
    -d uqqi.ru -d *.uqqi.ru
```

Certbot попросит добавить TXT-запись `_acme-challenge.uqqi.ru` —
добавьте в DNS, подождите 1–2 минуты, нажмите Enter.

Проверить что запись появилась:

```bash
dig TXT _acme-challenge.uqqi.ru +short
```

### 7. Nginx

```bash
cp /var/www/uqqi/uqqi.nginx.conf /etc/nginx/sites-available/uqqi.ru
ln -s /etc/nginx/sites-available/uqqi.ru /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 8. Systemd-сервис

```bash
cp /var/www/uqqi/uqqi.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable uqqi
systemctl start uqqi
```

Проверить статус:

```bash
systemctl status uqqi
journalctl -u uqqi -f     # логи в реальном времени
```

---

## Адреса после запуска

| Адрес | Что |
|-------|-----|
| `https://uqqi.ru` | Лендинг — продажа услуги |
| `https://uqqi.ru/BcJf69nkkikxqBj8` | Панель владельца |
| `https://название.uqqi.ru` | Публичный сайт компании |
| `https://название.uqqi.ru/admin` | Панель клиента |

---

## Панель владельца

**Логин:** `admin`  
**Пароль:** `qsc123zx`

Три вкладки:

**Сайты** — список всех компаний. Для каждой можно:
- сгенерировать новый пароль (старый перестаёт работать)
- включить / выключить сайт
- удалить сайт

**Заявки** — список заявок с лендинга (имя, телефон, ссылка, комментарий).

**Парсер** — запуск Яндекс Карт прямо из браузера:
1. Введите запрос и город
2. Нажмите «Запустить парсер»
3. Следите за логом в реальном времени
4. После завершения нажмите «Импортировать и создать сайты»
5. Скопируйте пароли из лога и отправьте клиентам

---

## Импорт из CSV вручную

Если предпочитаете запускать парсер в терминале:

```bash
cd /var/www/uqqi
source venv/bin/activate

# Запустить парсер
python yandex_maps_parser.py "кофейни" --city "Москва" --limit 30 \
    --only-without-website --output out.csv

# Импортировать результат в БД
python scripts/import_csv.py out.csv
```

Скрипт выведет таблицу со slug и паролями:

```
  КОМПАНИЯ              ПАРОЛЬ         САЙТ
  Дело в кофе           Xk9mLpQ2nR4s   https://delo-v-kofe.uqqi.ru
  Гёг                   Wm3jTzA8bC6q   https://gyog.uqqi.ru
```

Флаги импорта:

```bash
python scripts/import_csv.py out.csv           # только новые
python scripts/import_csv.py out.csv --force   # перезаписать + новый пароль
```

---

## Панель клиента

Клиент получает от вас:
- ссылку на сайт: `https://название.uqqi.ru`
- ссылку на панель: `https://название.uqqi.ru/admin`
- пароль из терминала

В панели клиент может сам менять:
- название, адрес, телефон, рейтинг, категорию
- часы работы с выходными по дням
- фотографии (drag & drop, до 5 штук, до 5 МБ каждая)
- ссылки на соцсети (Telegram, ВКонтакте, WhatsApp, Viber, Instagram, YouTube)

---

## Обновление приложения

```bash
cd /var/www/uqqi
# скопируйте новые файлы
source venv/bin/activate
pip install -r requirements.txt
systemctl restart uqqi
```

---

## Локальная разработка

```bash
cp .env.example .env
# установите DEBUG=True в .env

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt pydantic-settings
uvicorn app.main:app --reload
```

В режиме `DEBUG=True` субдомены не нужны —
компания определяется по query-параметру `?slug=`:

```
http://localhost:8000/?slug=delo-v-kofe
http://localhost:8000/admin?slug=delo-v-kofe
http://localhost:8000/BcJf69nkkikxqBj8/panel   ← панель владельца
```
