import hashlib
from typing import List

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings
from ollama import Client

from ..chunker import chunk_document
from ...config import Config


class RagPipeline:
    def __init__(self, collection_name=Config.QDRANT_COLLECTION):
        self.qdrant_client = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)

        self.embedder = OllamaEmbeddings(
            model="embeddinggemma",
            base_url=f"http://{Config.OLLAMA_HOST}:{Config.OLLAMA_PORT}"
        )

        self.vectorstore = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
            embedding=self.embedder
        )

    def _generate_ids(self, chunks):
        """Дедупликация через hash"""
        ids = []
        for doc in chunks:
            text = doc.page_content
            hash_id = hashlib.md5(text.encode()).hexdigest()
            ids.append(hash_id)
        return ids

    def ingest_record(self, path: str, doc_id: str):
        chunks = chunk_document(path)

        if not chunks:
            return {"status": "error", "reason": "empty document"}

        for doc in chunks:
            doc.metadata.update({"doc_id": doc_id})

        ids = self._generate_ids(chunks)

        self.vectorstore.add_documents(chunks, ids=ids)