FROM python:3.12-slim

WORKDIR /app

COPY api/kv_db.py ./kv_db.py

COPY daemon/process_documents.py ./process_documents.py

CMD ["python", "process_documents.py"]