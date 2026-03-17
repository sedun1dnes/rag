import time
from pathlib import Path
from kv_db import KVDb, KVDbConfig

db_path = Path("/app/db/documents.json").resolve()
kv = KVDb(KVDbConfig(db_path=db_path))

CHECK_INTERVAL = 5

def process_document(doc_path: str):
    """
    Вставь сюда свою функцию обработки документа.
    После успешной обработки вызываем:
        kv.mark_processed(doc_path, processed=True)
    """
    print(f"[Daemon] Processing document: {doc_path}")
    # === ВАША ФУНКЦИЯ ===
    # Пример:
    # with open(doc_path, "r", encoding="utf-8") as f:
    #     data = f.read()
    #     do_something(data)
    kv.mark_processed(doc_path, processed=True)
    print(f"[Daemon] Document processed: {doc_path}")

def run_daemon():
    print("[Daemon] Started...")
    while True:
        try:
            for doc in kv.list_documents(limit=1000):
                if not doc.get("processed", False):
                    try:
                        process_document(doc["path"])
                    except Exception as e:
                        print(f"[Daemon] Error processing {doc['path']}: {e}")
        except Exception as e:
            print(f"[Daemon] Error reading DB: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_daemon()
