import os
from pathlib import Path

class Config:
    REPO_ROOT = Path(__file__).resolve().parent.parent
    DOCS_DIR = Path(os.environ.get("RAG_DOCS_DIR", REPO_ROOT / "docs"))
    OLLAMA_HOST = os.environ['OLLAMA_HOST']
    OLLAMA_PORT = os.environ['OLLAMA_PORT']
    QDRANT_HOST = os.environ['QDRANT_HOST']
    QDRANT_PORT = os.environ['QDRANT_PORT']
    QDRANT_COLLECTION = os.environ['QDRANT_COLLECTION']

    