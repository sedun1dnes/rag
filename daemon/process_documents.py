import time
from sqlalchemy import select, update
from shared.db.db import SessionLocal
from shared.db.entities.document import Document
from shared.rag.pipeline import RagPipeline

CHECK_INTERVAL = 5  # секунд между проверками

def process_document(doc: Document, db, rag):
    print(f"[Daemon] Processing document: {doc.path}")

    try:
        rag.ingest_record(doc.path, doc.id)
        doc.status = "processed"
        db.commit()
        print(f"[Daemon] Document processed: {doc.path}")

    except Exception as e:
        doc.status = "error"
        db.commit()
        print(f"[Daemon] Error processing {doc.path}: {e}")

def run_daemon():
    print("[Daemon] Started...")
    while True:
        try:
            rag = RagPipeline()
            with SessionLocal() as db:
                query = select(Document).where(Document.status != "processed")
                docs = db.execute(query).scalars().all()

                for doc in docs:
                    doc.status = 'processing'
                    db.commit()
                    process_document(doc, db, rag)

        except Exception as e:
            print(f"[Daemon] Error reading DB: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_daemon()