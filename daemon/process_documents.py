import time
from datetime import datetime
from sqlalchemy import select

from shared.db import create_tables
from shared.db.db import SessionLocal
from shared.db.entities.document import Document
from shared.rag.pipeline import RagPipeline

CHECK_INTERVAL = 5


def process_document(doc: Document, db, rag: RagPipeline):
    print(f"[Daemon] Processing document: {doc.path}")
    try:
        rag.ingest_record(doc.path, str(doc.id), collection_name=str(doc.knowledge_base_id))
        doc.status = "processed"
        doc.processed_at = datetime.utcnow()
        db.commit()
        print(f"[Daemon] Document processed: {doc.path}")
    except Exception as e:
        doc.status = "error"
        db.commit()
        print(f"[Daemon] Error processing {doc.path}: {e}")


def run_daemon():
    create_tables()
    print("[Daemon] Started...")

    rag = RagPipeline()
    while True:
        try:
            with SessionLocal() as db:
                docs = db.execute(
                    select(Document).where(Document.status == "uploaded")
                ).scalars().all()

                for doc in docs:
                    doc.status = "processing"
                    db.commit()
                    process_document(doc, db, rag)

        except Exception as e:
            print(f"[Daemon] Error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_daemon()
