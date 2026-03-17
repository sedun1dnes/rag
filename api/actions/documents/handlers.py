from flask import request, jsonify
from werkzeug.utils import secure_filename
from uuid import uuid4
from pathlib import Path
from sqlalchemy import select

from shared.db.db import SessionLocal
from shared.db.entities.document import Document
from api.config import Config

def _allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in Config.ALLOWED_EXTS

def upload_documents():
    batch_id = uuid4().hex
    db = SessionLocal()

    incoming = []
    if "files" in request.files:
        incoming = request.files.getlist("files")
    elif "file" in request.files:
        incoming = [request.files["file"]]

    if not incoming:
        return jsonify({"error": "No files provided"}), 400

    saved = []
    rejected = []

    for f in incoming:
        if not f or not f.filename:
            rejected.append({"filename": None, "reason": "empty filename"})
            continue

        filename = secure_filename(f.filename)

        if not filename or not _allowed(filename):
            rejected.append({"filename": f.filename, "reason": "unsupported extension"})
            continue

        target = Config.DOCS_DIR / filename

        # avoid overwrite
        if target.exists():
            stem = target.stem
            suffix = target.suffix
            i = 1
            while True:
                candidate = Config.DOCS_DIR / f"{stem}_{i}{suffix}"
                if not candidate.exists():
                    target = candidate
                    break
                i += 1

        f.save(target)

        doc = Document(
            filename=target.name,
            path=str(target),
            original_name=f.filename,
            status="uploaded",
            batch_id=batch_id,
        )

        db.add(doc)

        saved.append({
            "id": str(doc.id),
            "original_name": f.filename,
            "created_at": doc.created_at,
            "status": "uploaded",
        })

    db.commit()

    return jsonify({
        "batch_id": batch_id,
        "saved": saved,
        "rejected": rejected,
    }), 200 if saved else 400

def get_documents():
    limit = int(request.args.get("limit", "200"))
    search = request.args.get("search", "").strip()

    with SessionLocal() as db:
        query = select(Document).order_by(Document.created_at.desc())

        if search:
            query = query.where(Document.original_name.ilike(f"%{search}%"))

        query = query.limit(limit)

        result = db.execute(query).scalars().all()

        documents = [
            {
                "id": str(doc.id),
                "original_name": doc.original_name,
                "status": doc.status,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in result
        ]

    return jsonify({"documents": documents, "limit": limit})