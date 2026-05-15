FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY eval/requirements.txt /app/eval/requirements.txt
RUN pip install --no-cache-dir -r /app/eval/requirements.txt

COPY eval/ /app/eval
COPY shared/ /app/shared
