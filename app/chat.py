"""
app/chat.py — публичный чат на витринах (Pro-фича).

POST /api/chat/{slug}/send  — посетитель шлёт сообщение → сохраняем + пересылаем
                              владельцу в Telegram (маршрутизация ответа по reply).
GET  /api/chat/{slug}/poll  — посетитель забирает ответы владельца (direction='out').

Гейт: только сайты с активным Pro и подключённым Telegram владельца.
Антиспам: лёгкий in-memory лимит по (slug, visitor, ip). Тела в access-лог НЕ пишем.
"""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.models import SessionLocal, Company, User, ChatMessage
from app.telegram_bot import tg_send_message

router = APIRouter(prefix="/api/chat")

MAX_LEN = 2000
_rate: dict[str, list[float]] = {}


def _rate_ok(key: str, limit: int = 8, window: int = 300) -> bool:
    now = time.time()
    arr = [t for t in _rate.get(key, []) if now - t < window]
    if len(arr) >= limit:
        _rate[key] = arr
        return False
    arr.append(now)
    _rate[key] = arr
    return True


def _pro_active(c) -> bool:
    return bool(c and c.pro_until and c.pro_until > datetime.utcnow())


class SendPayload(BaseModel):
    visitor_id: str
    text: str


@router.post("/{slug}/send")
async def chat_send(slug: str, payload: SendPayload, request: Request):
    text = (payload.text or "").strip()[:MAX_LEN]
    vid = (payload.visitor_id or "").strip()[:40]
    if not text or not vid:
        raise HTTPException(status_code=422, detail="empty")

    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.slug == slug).first()
        if not c or not c.user_id or not _pro_active(c):
            raise HTTPException(status_code=404, detail="chat unavailable")
        owner = db.query(User).filter(User.id == c.user_id).first()
        if not owner or not owner.tg_chat_id:
            raise HTTPException(status_code=409, detail="chat not connected")

        ip = request.client.host if request.client else "?"
        if not _rate_ok(f"{slug}:{vid}:{ip}"):
            raise HTTPException(status_code=429, detail="too many messages")

        msg = ChatMessage(company_id=c.id, visitor_id=vid, direction="in", text=text)
        db.add(msg)
        db.commit()

        short = vid[-6:]
        notif = (
            f"💬 Сообщение с сайта «{c.title}» ({slug}.uqqi.ru)\n"
            f"Посетитель #{short}:\n\n{text}\n\n"
            f"↩️ Ответьте на это сообщение (Reply), чтобы написать посетителю."
        )
        mid = tg_send_message(owner.tg_chat_id, notif)
        if mid:
            msg.notify_msg_id = mid
            db.commit()
        return {"ok": True, "id": msg.id}
    finally:
        db.close()


@router.get("/{slug}/poll")
async def chat_poll(slug: str, visitor_id: str, after: int = 0):
    vid = (visitor_id or "").strip()[:40]
    if not vid:
        return {"messages": []}
    db = SessionLocal()
    try:
        c = db.query(Company).filter(Company.slug == slug).first()
        if not c:
            raise HTTPException(status_code=404)
        rows = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.company_id == c.id,
                ChatMessage.visitor_id == vid,
                ChatMessage.direction == "out",
                ChatMessage.id > after,
            )
            .order_by(ChatMessage.id.asc())
            .limit(50)
            .all()
        )
        return {
            "messages": [
                {"id": r.id, "text": r.text,
                 "at": r.created_at.strftime("%H:%M") if r.created_at else ""}
                for r in rows
            ]
        }
    finally:
        db.close()
