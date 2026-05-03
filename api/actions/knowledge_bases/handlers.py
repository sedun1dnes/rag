import uuid
from pathlib import Path
from flask import request, jsonify
from sqlalchemy import select, func
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from shared.db.db import SessionLocal
from shared.db.entities.knowledge_base import KnowledgeBase
from shared.db.entities.document import Document
from shared.config import Config as SharedConfig
from api.config import Config


def _qdrant_client() -> QdrantClient:
    return QdrantClient(host=SharedConfig.QDRANT_HOST, port=int(SharedConfig.QDRANT_PORT))


def _create_qdrant_collection(collection_name: str) -> None:
    client = _qdrant_client()
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=SharedConfig.EMBEDDING_DIMS, distance=Distance.COSINE),
        )


def _allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in Config.ALLOWED_EXTS


def list_knowledge_bases():
    with SessionLocal() as db:
        rows = db.execute(
            select(KnowledgeBase, func.count(Document.id).label("doc_count"))
            .outerjoin(Document, Document.knowledge_base_id == KnowledgeBase.id)
            .where(KnowledgeBase.removed == False)
            .group_by(KnowledgeBase.id)
            .order_by(KnowledgeBase.created_at.desc())
        ).all()

        return jsonify([
            {
                "id": str(kb.id),
                "name": kb.name,
                "description": kb.description,
                "document_count": doc_count,
                "created_at": kb.created_at.isoformat() if kb.created_at else None,
            }
            for kb, doc_count in rows
        ])


def create_knowledge_base():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    kb = KnowledgeBase(name=data["name"], description=data.get("description"))

    with SessionLocal() as db:
        db.add(kb)
        db.flush()
        kb_id = str(kb.id)

        try:
            _create_qdrant_collection(kb_id)
        except Exception as e:
            db.rollback()
            return jsonify({"error": f"Qdrant недоступен: {e}"}), 500

        db.commit()
        db.refresh(kb)
        return jsonify({
            "id": kb_id,
            "name": kb.name,
            "description": kb.description,
            "document_count": 0,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
        }), 201


def get_knowledge_base(kb_id: str):
    with SessionLocal() as db:
        kb = db.get(KnowledgeBase, uuid.UUID(kb_id))
        if not kb or kb.removed:
            return jsonify({"error": "Not found"}), 404

        docs = db.execute(
            select(Document)
            .where(Document.knowledge_base_id == kb.id)
            .order_by(Document.downloaded_at.desc())
        ).scalars().all()

        return jsonify({
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "documents": [
                {
                    "id": str(d.id),
                    "filename": d.filename,
                    "status": d.status,
                    "downloaded_at": d.downloaded_at.isoformat(),
                }
                for d in docs
            ],
        })


def delete_knowledge_base(kb_id: str):
    with SessionLocal() as db:
        kb = db.get(KnowledgeBase, uuid.UUID(kb_id))
        if not kb:
            return jsonify({"error": "Not found"}), 404
        kb.removed = True
        db.commit()

    try:
        _qdrant_client().delete_collection(kb_id)
    except Exception:
        pass

    return jsonify({}), 200


def upload_documents_to_kb(kb_id: str):
    with SessionLocal() as db:
        kb = db.get(KnowledgeBase, uuid.UUID(kb_id))
        if not kb or kb.removed:
            return jsonify({"error": "Knowledge base not found"}), 404

    incoming = []
    if "files" in request.files:
        incoming = request.files.getlist("files")
    elif "file" in request.files:
        incoming = [request.files["file"]]

    if not incoming:
        return jsonify({"error": "No files provided"}), 400

    saved = []
    rejected = []

    with SessionLocal() as db:
        for f in incoming:
            if not f or not f.filename:
                rejected.append({"filename": None, "reason": "empty filename"})
                continue

            ext = Path(f.filename).suffix
            if ext.lower() not in Config.ALLOWED_EXTS:
                rejected.append({"filename": f.filename, "reason": "unsupported extension"})
                continue

            stored_name = f"{uuid.uuid4().hex}{ext}"
            target = Config.DOCS_DIR / stored_name

            i = 1
            while target.exists():
                stem = target.stem
                target = Config.DOCS_DIR / f"{stem}_{i}{ext}"
                i += 1

            f.save(target)

            doc = Document(
                path=str(target),
                filename=f.filename,
                status="uploaded",
                knowledge_base_id=uuid.UUID(kb_id),
            )
            db.add(doc)
            db.flush()

            saved.append({
                "id": str(doc.id),
                "filename": f.filename,
                "downloaded_at": doc.downloaded_at.isoformat(),
                "status": "uploaded",
            })

        db.commit()

    return jsonify({"saved": saved, "rejected": rejected}), 200 if saved else 400
