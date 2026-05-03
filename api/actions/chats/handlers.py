import uuid
import json
from datetime import datetime
from flask import request, jsonify, Response, stream_with_context
from sqlalchemy import select

from shared.db.db import SessionLocal
from shared.db.entities.chat import Chat
from shared.db.entities.message import Message
from shared.rag.pipeline import RagPipeline


def list_chats():
    session_id = request.args.get("session_id")
    with SessionLocal() as db:
        query = (
            select(Chat)
            .where(Chat.removed == False)
            .order_by(Chat.updated_at.desc())
        )
        if session_id:
            query = query.where(Chat.session_id == uuid.UUID(session_id))
        chats = db.execute(query).scalars().all()
        return jsonify([
            {
                "id": str(c.id),
                "title": c.title,
                "session_id": str(c.session_id),
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in chats
        ])


def create_chat():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    chat = Chat(
        title=data.get("title", "Новый диалог"),
        session_id=uuid.UUID(session_id),
    )
    with SessionLocal() as db:
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return jsonify({
            "id": str(chat.id),
            "title": chat.title,
            "session_id": str(chat.session_id),
            "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
        }), 201


def delete_chat(chat_id: str):
    with SessionLocal() as db:
        chat = db.get(Chat, uuid.UUID(chat_id))
        if not chat:
            return jsonify({"error": "Not found"}), 404
        chat.removed = True
        db.commit()
        return jsonify({}), 200


def get_messages(chat_id: str):
    with SessionLocal() as db:
        msgs = db.execute(
            select(Message)
            .where(Message.chat_id == uuid.UUID(chat_id))
            .order_by(Message.created_at.asc())
        ).scalars().all()
        return jsonify([
            {
                "id": str(m.id),
                "text": m.text,
                "type": m.type,
                "created_at": m.created_at.isoformat(),
                "knowledge_base_id": str(m.knowledge_base_id) if m.knowledge_base_id else None,
            }
            for m in msgs
        ])


def send_message(chat_id: str):
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({"error": "text is required"}), 400

    kb_id = data.get("knowledge_base_id")
    if not kb_id:
        return jsonify({"error": "knowledge_base_id is required"}), 400

    text = data["text"]

    with SessionLocal() as db:
        chat = db.get(Chat, uuid.UUID(chat_id))
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        last_msg = db.execute(
            select(Message)
            .where(Message.chat_id == uuid.UUID(chat_id))
            .order_by(Message.created_at.desc())
        ).scalars().first()

        user_msg = Message(
            text=text,
            type="user",
            chat_id=uuid.UUID(chat_id),
            previous_id=last_msg.id if last_msg else None,
            knowledge_base_id=uuid.UUID(kb_id),
        )
        db.add(user_msg)
        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user_msg)
        user_msg_id = str(user_msg.id)
        user_msg_data = {
            "id": user_msg_id,
            "text": text,
            "type": "user",
            "created_at": user_msg.created_at.isoformat(),
            "knowledge_base_id": kb_id,
        }

    def generate():
        yield f"data: {json.dumps({'type': 'user_message', 'message': user_msg_data})}\n\n"

        full_text = ""
        try:
            rag = RagPipeline()
            for token in rag.stream_response(text, collection_name=kb_id):
                if token:
                    full_text += token
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as e:
            full_text = f"Ошибка при генерации ответа: {e}"
            yield f"data: {json.dumps({'type': 'token', 'token': full_text})}\n\n"

        with SessionLocal() as db:
            assistant_msg = Message(
                text=full_text,
                type="assistant",
                chat_id=uuid.UUID(chat_id),
                previous_id=uuid.UUID(user_msg_id),
                knowledge_base_id=uuid.UUID(kb_id),
            )
            db.add(assistant_msg)
            chat = db.get(Chat, uuid.UUID(chat_id))
            if chat:
                chat.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(assistant_msg)
            yield f"data: {json.dumps({'type': 'done', 'message': {'id': str(assistant_msg.id), 'text': full_text, 'type': 'assistant', 'created_at': assistant_msg.created_at.isoformat(), 'knowledge_base_id': kb_id}})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )
