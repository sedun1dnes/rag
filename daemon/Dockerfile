FROM python:3.12-slim

WORKDIR /app

COPY daemon/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY shared/ /app/shared
COPY daemon/process_documents.py ./process_documents.py

CMD ["python", "process_documents.py"]