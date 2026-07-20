"""
app/models.py — модели базы данных
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint, create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


# ── Engine & Session ──────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно для SQLite
    echo=settings.DEBUG,
)


# WAL + busy_timeout: несколько процессов (app + воркеры) пишут в одну SQLite.
# WAL разрешает параллельные чтения + одного писателя; busy_timeout ждёт при блокировке.
@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _rec):
    if settings.DATABASE_URL.startswith("sqlite"):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute("PRAGMA synchronous=NORMAL")  # безопасно с WAL, быстрее
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Dependency для FastAPI — открывает сессию и закрывает после запроса."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Company ───────────────────────────────────────────────────────────────────

class User(Base):
    """Аккаунт клиента в личном кабинете lk.uqqi.ru."""

    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    password_hash   = Column(String(255), nullable=False)

    email_verified  = Column(Boolean, default=False)
    verify_token    = Column(String(64), default="", index=True)   # подтверждение email
    verify_sent_at  = Column(DateTime, nullable=True)              # когда выдан verify_token (TTL 24ч)
    reset_token     = Column(String(64), default="", index=True)   # сброс пароля
    reset_expires   = Column(DateTime, nullable=True)

    # Согласие с офертой/политикой (юридическое требование)
    agreed_at       = Column(DateTime, nullable=True)
    agreed_ip       = Column(String(64), default="")

    # Триал использован (один на аккаунт за всю жизнь)
    trial_used      = Column(Boolean, default=False)
    pending_claim_code = Column(String(40), default="")  # claim-код, ожидающий подтверждения email

    # Чат с сайта → Telegram владельца (Pro-фича).
    tg_chat_id      = Column(String(40), default="")   # chat_id владельца (куда шлём сообщения с сайта)
    tg_link_token   = Column(String(64), default="")   # одноразовый токен deep-link подключения

    created_at      = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} verified={self.email_verified}>"


class Company(Base):
    """Одна компания = один сайт на субдомене."""

    __tablename__ = "companies"

    id              = Column(Integer, primary_key=True, index=True)
    slug            = Column(String(120), unique=True, nullable=False, index=True)

    # Владелец (None = демо-сайт или созданный из owner-панели)
    user_id         = Column(Integer, index=True, nullable=True)
    is_demo         = Column(Boolean, default=False)  # витрина для лендинга, без подписки

    # Подписка/триал этого сайта
    sub_status      = Column(String(20), default="free")    # freemium: free / active (Pro). legacy trial/unpaid не используются
    trial_ends_at   = Column(DateTime, nullable=True)        # конец пробного периода (legacy, вестигиально)
    paid_until      = Column(DateTime, nullable=True)        # оплачено до (legacy, вестигиально)

    # Freemium/Pro (редизайн подписки):
    #   pro_until — до когда активен Pro (пишут и Pro-триал, и оплата); активен, если > now.
    #   is_claim  — сайт создан из owner-панели (серый origin); персистентный
    #               (claim_code гасится при привязке, а этот флаг остаётся).
    #   paid_once — была ли хоть одна успешная оплата → легитимизирует claim-сайт навсегда.
    pro_until       = Column(DateTime, nullable=True)
    is_claim        = Column(Boolean, default=False)
    paid_once       = Column(Boolean, default=False)

    build_status    = Column(String(20), default="ready")   # queued / building / ready / error

    # Основные данные
    title           = Column(String(255), nullable=False)
    address         = Column(String(500), default="")
    phone           = Column(String(50),  default="")
    rating          = Column(String(10),  default="")
    category        = Column(String(120), default="Кофейня")
    coordinates     = Column(String(50),  default="")
    yandex_url      = Column(String(500), default="")

    # JSON-поля (хранятся как текст, читаются через свойства)
    _hours          = Column("hours",         Text, default="[]")
    _gallery_photos = Column("gallery_photos", Text, default="[]")
    _social_links   = Column("social_links",   Text, default="[]")
    _latest_news    = Column("latest_news",    Text, default="[]")

    # legacy-колонка: вход в редактирование теперь только через кабинет lk.uqqi.ru.
    # Оставлена для совместимости со схемой БД (в базе NOT NULL). Кодом не используется,
    # всегда пустая строка.
    admin_password_hash = Column(String(255), nullable=False, default="")

    # Логотип
    logo_url        = Column(String(500), default="")
    book_url        = Column(String(500), default="")
    reviews_count   = Column(String(20), default="")
    catalog_title   = Column(String(50), default="Товары и услуги")  # «Меню» для общепита
    about_text      = Column(Text, default="")       # «Коротко о месте»
    build_log       = Column(Text, default="")      # лог последней сборки
    build_attempts  = Column(Integer, default=0)     # сколько раз пытались собрать

    # Дополнительные данные (витрина, отзывы, особенности)
    _menu_items     = Column("menu_items",   Text, default="[]")  # витрина
    _reviews        = Column("reviews",      Text, default="[]")  # отзывы
    _features       = Column("features",     Text, default="[]")  # особенности
    avg_bill        = Column(String(50), default="")              # средний счёт

    # Реквизиты организации (заполняются вручную через /admin)
    org_name        = Column(String(500), default="")  # полное наименование
    org_type        = Column(String(50),  default="")  # ИП / ООО / АО
    org_inn         = Column(String(20),  default="")  # ИНН

    # Ближайшая остановка (JSON: {"name": "...", "distance": "168 м"})
    _transit_stop   = Column("transit_stop", Text, default="{}")

    # Выбор шаблона витрины: A или B (мобильным всегда отдаётся C). По умолчанию B.
    template_variant = Column(String(1), default="A")  # A — единый дефолт (миграция/сборка/рендер); claim-сайты ставят B явно

    # Claim-система (продажа готовых сайтов): для обезличенных сайтов из owner-панели
    claim_code      = Column(String(40), nullable=True, default=None, index=True)  # код привязки; NULL у клиентских
    screenshot      = Column(String(200), default="")   # путь к скриншоту hero (для материалов клиенту)
    demo_until      = Column(DateTime, nullable=True)    # до какого времени снята заглушка («демо 7 дней»)

    # Ручное редактирование галереи
    gallery_manual  = Column(Boolean, default=False)  # True → не перезаписывать при обновлении

    # Флаги автообновления по вкладкам (True = тянуть из Яндекса, поле заблокировано для ручной правки)
    auto_main       = Column(Boolean, default=True)   # название, категория, телефон, адрес
    auto_hours      = Column(Boolean, default=True)   # часы работы
    auto_socials    = Column(Boolean, default=True)   # соцсети
    auto_requisites = Column(Boolean, default=True)   # реквизиты организации

    # Состояние Яндекс-карточки
    yandex_unavailable = Column(Boolean, default=False)  # True → карточка удалена, обновление недоступно
    last_parsed_at  = Column(DateTime, nullable=True)    # время последнего успешного парсинга

    # Биллинг
    next_payment_date = Column(DateTime, nullable=True)  # дата следующей оплаты
    client_email      = Column(String(255), default="")  # email клиента для уведомлений
    notified_7d       = Column(Boolean, default=False)   # напоминание о продлении за 7 дней (оплаченные)
    notified_3d       = Column(Boolean, default=False)   # напоминание о продлении за 3 дня (оплаченные)
    # Цепочка писем триала/удержания (идемпотентность — одноразовые флаги)
    notified_trial_d3 = Column(Boolean, default=False)   # письмо «3 дня триала: метрики»
    notified_trial_d6 = Column(Boolean, default=False)   # письмо «триал кончается завтра»
    welcome_sent      = Column(Boolean, default=False)   # письмо «что дальше» после первой оплаты
    last_report_at    = Column(DateTime, nullable=True)  # когда слали последний ежемесячный отчёт

    # Флаги
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── JSON helpers ─────────────────────────────────────────────────────────

    def _get_json(self, col: str) -> Any:
        val = getattr(self, col)
        if not val:
            return []
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []

    def _set_json(self, col: str, value: Any) -> None:
        setattr(self, col, json.dumps(value, ensure_ascii=False))

    @property
    def hours(self) -> list[dict]:
        return self._get_json("_hours")

    @hours.setter
    def hours(self, value: list[dict]) -> None:
        self._set_json("_hours", value)

    @property
    def gallery_photos(self) -> list[str]:
        return self._get_json("_gallery_photos")

    @gallery_photos.setter
    def gallery_photos(self, value: list[str]) -> None:
        self._set_json("_gallery_photos", value)

    @property
    def social_links(self) -> list[dict]:
        """[{"platform": "telegram", "url": "https://t.me/..."}, ...]"""
        return self._get_json("_social_links")

    @social_links.setter
    def social_links(self, value: list[dict]) -> None:
        self._set_json("_social_links", value)

    @property
    def latest_news(self) -> list[dict]:
        """[{"date": "...", "text": "...", "image_url": "..."}, ...]"""
        return self._get_json("_latest_news")

    @latest_news.setter
    def latest_news(self, value: list[dict]) -> None:
        self._set_json("_latest_news", value)

    @property
    def menu_items(self) -> list[dict]:
        """[{"name": "...", "price": "...", "image_url": "..."}, ...]"""
        return self._get_json("_menu_items")

    @menu_items.setter
    def menu_items(self, value: list[dict]) -> None:
        self._set_json("_menu_items", value)

    @property
    def reviews(self) -> list[dict]:
        """[{"author": "...", "text": "...", "rating": 5, "date": "..."}, ...]"""
        return self._get_json("_reviews")

    @reviews.setter
    def reviews(self, value: list[dict]) -> None:
        self._set_json("_reviews", value)

    @property
    def features(self) -> list[str]:
        """["Wi-Fi", "Доставка", ...]"""
        return self._get_json("_features")

    @features.setter
    def features(self, value: list[str]) -> None:
        self._set_json("_features", value)

    @property
    def transit_stop(self) -> dict:
        """{"name": "ост. ПМК", "distance": "168 м"}"""
        val = self._get_json("_transit_stop")
        return val if isinstance(val, dict) else {}

    @transit_stop.setter
    def transit_stop(self, value: dict) -> None:
        setattr(self, "_transit_stop", json.dumps(value or {}, ensure_ascii=False))

    def __repr__(self) -> str:
        return f"<Company id={self.id} slug={self.slug!r} title={self.title!r}>"



# ── Session ───────────────────────────────────────────────────────────────────

class Session(Base):
    """Сессии авторизации (и владельца и клиентов)."""

    __tablename__ = "sessions"

    token      = Column(String(64), primary_key=True, index=True)
    identity   = Column(String(255), nullable=False)  # slug компании или "owner"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    def is_valid(self) -> bool:
        return datetime.utcnow() < self.expires_at

# ── Lead ─────────────────────────────────────────────────────────────────────

class Lead(Base):
    """Заявка с лендинга."""

    __tablename__ = "leads"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), default="")
    email      = Column(String(255), default="")
    url        = Column(String(500), default="")
    comment    = Column(String(1000), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Lead id={self.id} name={self.name!r}>"


# ── SupportMessage ────────────────────────────────────────────────────────────

class SupportMessage(Base):
    """Обращение в поддержку из клиентской панели."""

    __tablename__ = "support_messages"

    id            = Column(Integer, primary_key=True, index=True)
    company_slug  = Column(String(120), default="")   # с какого сайта пришло
    company_title = Column(String(255), default="")
    reply_email   = Column(String(255), default="")   # куда отвечать
    message       = Column(Text, default="")
    is_read       = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SupportMessage id={self.id} from={self.reply_email!r}>"


# ── Visit (метрика посещений) ─────────────────────────────────────────────────

class Visit(Base):
    """Уникальный визит за сутки. target = slug сайта или '__landing__'."""

    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("target", "day", "visitor_hash", name="uq_visit_unique"),
    )

    id           = Column(Integer, primary_key=True, index=True)
    target       = Column(String(120), index=True, default="")   # slug или '__landing__'
    day          = Column(String(10), index=True, default="")     # YYYY-MM-DD
    visitor_hash = Column(String(64), default="")                  # hash(IP+UA)
    created_at   = Column(DateTime, default=datetime.utcnow)


class VisitLog(Base):
    """Сырой лог визитов для детальной метрики (IP, гео, бот). Ретенция 90 дней."""

    __tablename__ = "visit_logs"

    id           = Column(Integer, primary_key=True, index=True)
    target       = Column(String(120), index=True, default="")   # slug или '__landing__'
    ip           = Column(String(45), index=True, default="")     # IPv4/IPv6
    city         = Column(String(120), default="")                # город из GeoIP
    country      = Column(String(80), default="")                 # страна
    user_agent   = Column(String(400), default="")
    is_bot       = Column(Boolean, default=False, index=True)
    visitor_hash = Column(String(64), default="")                  # для подсчёта уников
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<Visit target={self.target!r} day={self.day!r}>"


class ParseCandidate(Base):
    """Кандидат для создания сайта — организация без сайта (Фаза 1 двухфазного парсинга)."""

    __tablename__ = "parse_candidates"

    id          = Column(Integer, primary_key=True, index=True)
    org_id      = Column(String(40), index=True, default="")      # ключ дедупликации
    title       = Column(String(200), default="")
    address     = Column(String(400), default="")
    yandex_url  = Column(String(500), default="")
    query       = Column(String(200), index=True, default="")     # запрос поиска (фильтр)
    status      = Column(String(20), default="new")               # new / site_created
    company_id  = Column(Integer, nullable=True)                  # созданный сайт
    created_at  = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Платёж ЮKassa за подписку сайта."""

    __tablename__ = "payments"

    id            = Column(Integer, primary_key=True, index=True)
    payment_id    = Column(String(64), unique=True, index=True)  # id от ЮKassa (идемпотентность)
    user_id       = Column(Integer, index=True)
    company_id    = Column(Integer, index=True)
    company_slug  = Column(String(120), default="")
    amount        = Column(String(20), default="1990.00")
    days          = Column(Integer, default=30)             # срок продления из тарифа (30/90/365)
    status        = Column(String(20), default="pending")  # pending / succeeded / canceled
    processed     = Column(Boolean, default=False)          # webhook уже применён (защита от дублей)
    created_at    = Column(DateTime, default=datetime.utcnow)
    paid_at       = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Payment {self.payment_id} {self.status} {self.amount}>"


# ── Job (очередь фоновых Playwright-задач; Блок 9) ────────────────────────────

class Job(Base):
    """
    Фоновая задача парсинга/скриншота. Выполняется отдельным процессом worker.py.
    Очередь персистентна (переживает рестарт), диспетчер в app раздаёт воркерам.
    """

    __tablename__ = "jobs"

    id          = Column(Integer, primary_key=True, index=True)
    type        = Column(String(30), index=True)   # build_site|collect_candidates|create_site|refresh_company|screenshot
    payload     = Column(Text, default="{}")       # JSON-параметры задачи
    status      = Column(String(20), default="pending", index=True)  # pending|running|done|failed
    attempts    = Column(Integer, default=0)        # сделано попыток
    max_attempts = Column(Integer, default=3)
    timeout_sec = Column(Integer, default=180)      # индивидуальный таймаут
    progress    = Column(String(255), default="")   # шаг/процент для панели
    result      = Column(Text, default="")          # JSON итог (по желанию)
    error       = Column(Text, default="")          # текст последней ошибки
    worker_pid  = Column(Integer, nullable=True)     # pid держащего процесса
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)
    started_at  = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Job {self.id} {self.type} {self.status}>"


class ChatMessage(Base):
    """
    Сообщение чата на сайте (Pro-фича). Двусторонний:
      direction='in'  — от посетителя сайта → пересылаем владельцу в Telegram;
      direction='out' — ответ владельца из Telegram → посетитель забирает поллингом.
    Переписка одного посетителя связывается через visitor_id (генерит виджет).
    """

    __tablename__ = "chat_messages"

    id            = Column(Integer, primary_key=True, index=True)
    company_id    = Column(Integer, index=True)
    visitor_id    = Column(String(40), index=True)      # id посетителя (localStorage виджета)
    direction     = Column(String(3))                    # 'in' | 'out'
    text          = Column(Text, default="")
    notify_msg_id = Column(Integer, nullable=True)        # message_id пересылки владельцу (для маршрутизации ответа reply-to)
    tg_update_id  = Column(Integer, nullable=True, index=True)  # update_id ответа владельца (дедуп поллинга)
    created_at    = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} c{self.company_id} {self.direction}>"


# ── Init ──────────────────────────────────────────────────────────────────────

def create_tables() -> None:
    """Создаёт все таблицы если их нет."""
    Base.metadata.create_all(bind=engine)
    print("[DB] Таблицы созданы (или уже существуют)")
