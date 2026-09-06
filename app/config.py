"""
app/config.py — настройки приложения из .env
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DOMAIN:    str  = "uqqi.ru"
    SECRET_KEY:     str  = "dev-secret-key-change-in-production"
    DATABASE_URL:   str  = "sqlite:///./uqqi.db"
    UPLOAD_DIR:     str  = "./static/uploads"
    DEBUG:          bool = False

    # Панель владельца
    PANEL_PATH:     str  = "BcJf69nkkikxqBj8"   # секретный URL-путь
    PANEL_USER:     str  = "admin"
    PANEL_PASSWORD: str  = "qsc123zx"

    # SMTP для биллинг-уведомлений (Beget)
    SMTP_HOST:      str  = "smtp.beget.com"
    SMTP_PORT:      int  = 465
    SMTP_USER:      str  = "clients@uqqi.ru"
    SMTP_PASSWORD:  str  = "di5knwkDCt9*"
    SMTP_FROM:      str  = "clients@uqqi.ru"
    SUPPORT_EMAIL:  str  = "support@uqqi.ru"

    # Подтверждение прав в Яндекс.Вебмастере и Google Search Console.
    # Пустые по умолчанию — мета-тег не выводится, пока код не задан в .env.
    YANDEX_VERIFICATION: str = ""
    GOOGLE_VERIFICATION: str = ""

    # Автообновление данных
    AUTO_REFRESH_ENABLED: bool = True

    # ЮKassa (приём платежей)
    YUKASSA_SHOP_ID:    str = ""   # идентификатор магазина
    YUKASSA_SECRET_KEY: str = ""   # секретный ключ API
    SUBSCRIPTION_DAYS:  int = 30        # fallback срока продления (реальный — Payment.days из тарифа PLANS в cabinet.py)

    # Telegram-бот: вывоз бэкапов БД + алерты мониторинга + чат с сайтов (Pro).
    # Пустые дефолты — реальные значения только в .env (не коммитить).
    TELEGRAM_BOT_TOKEN: str = ""   # токен от @BotFather
    TELEGRAM_CHAT_ID:   str = ""   # ID чата/канала для алертов/бэкапов
    TELEGRAM_BOT_USERNAME: str = ""  # username бота без @ (для deep-link t.me/<bot>?start=)
    TELEGRAM_PROXY:     str = ""   # опц. SOCKS5/HTTPS-прокси для Bot API (если заблокирован)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
