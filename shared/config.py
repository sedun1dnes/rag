import os
from pathlib import Path

class Config:
    REPO_ROOT = Path(__file__).resolve().parent.parent
    DOCS_DIR = Path(os.environ.get("RAG_DOCS_DIR", REPO_ROOT / "docs"))
    EMBEDDING_HOST = os.environ['EMBEDDING_HOST']
    EMBEDDING_PORT = os.environ['EMBEDDING_PORT']
    EMBEDDING_MODEL = os.environ['EMBEDDING_MODEL']
    EMBEDDING_DIMS = int(os.environ.get('EMBEDDING_DIMS', '1024'))
    
    GENERATION_HOST = os.environ['GENERATION_HOST']
    GENERATION_PORT = os.environ['GENERATION_PORT']
    GENERATION_MODEL = os.environ['GENERATION_MODEL']
    
    QDRANT_HOST = os.environ['QDRANT_HOST']
    QDRANT_PORT = os.environ['QDRANT_PORT']
    QDRANT_COLLECTION = os.environ['QDRANT_COLLECTION']

    