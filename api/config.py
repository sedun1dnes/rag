import os
from pathlib import Path

class Config:
    # Flask
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    PORT = int(os.environ.get("PORT", 5000))
    MAX_CONTENT_LENGTH = int(os.environ.get("RAG_MAX_UPLOAD_MB", "50")) * 1024 * 1024

    # Директории
    REPO_ROOT = Path(__file__).resolve().parent.parent
    DOCS_DIR = Path(os.environ.get("RAG_DOCS_DIR", REPO_ROOT / "docs"))
    UPLOADS_DIR = Path(os.environ.get("RAG_UPLOADS_DIR", REPO_ROOT / "uploads"))
    DB_PATH = Path(os.environ.get("RAG_DB_PATH", REPO_ROOT / "db/documents.json"))

    # Files
    ALLOWED_EXTS = {'.pdf', '.txt'}