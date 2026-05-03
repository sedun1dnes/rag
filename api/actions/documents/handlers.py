import uuid
from flask import jsonify

from shared.db.db import SessionLocal
from shared.db.entities.document import Document


def delete_document(doc_id: str):
    with SessionLocal() as db:
        doc = db.get(Document, uuid.UUID(doc_id))
        if not doc:
            return jsonify({"error": "Not found"}), 404
        db.delete(doc)
        db.commit()
        return jsonify({}), 200
