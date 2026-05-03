import hashlib
from typing import List

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from ollama import Client

from ..chunker import chunk_document
from ...config import Config
from ...db.db import SessionLocal
from ...db.entities.document import Document

class RagPipeline:
    def __init__(self, collection_name=Config.QDRANT_COLLECTION):
        self.qdrant_client = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)

        self.embedder = OllamaEmbeddings(
            model=Config.EMBEDDING_MODEL,
            base_url=f"http://{Config.EMBEDDING_HOST}:{Config.EMBEDDING_PORT}"
        )

        self.llm = ChatOllama(
            model=Config.GENERATION_MODEL,
            validate_model_on_init=True,
            temperature=0,
            base_url=f"http://{Config.GENERATION_HOST}:{Config.GENERATION_PORT}"
        )

        self.vectorstore = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
            embedding=self.embedder
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 3,
                "fetch_k": 5,
                "lambda_mult": 0.5,
                "score_threshold": 0.5
            },
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

    def retrieve_and_generate(self, query: str):
        docs = self.retriever.invoke(query)
        docs_data = []

        with SessionLocal() as db:
            for doc in docs:
                doc_id = doc.metadata['doc_id']
                document = db.query(Document).get(doc_id)
                
                data = f"Документ <{document.original_name}>: {doc.page_content}"
                docs_data.append(data)
            

        message = f"""
            Ты — умный ассистент. Твоя задача — ответить на вопрос пользователя максимально подробно, 
            используя предоставленные ниже документы. Если информация в документах недостаточна, 
            можешь добавить свои знания, но всегда уточняй, что это не из документов.

            === Документы ===
            {docs_data}

            === Вопрос пользователя ===
            {query}

            === Инструкция для ответа ===
            1. Сначала дай краткий и понятный ответ.
            2. Затем можешь привести детали из документов, если они релевантны.
            3. Обязательно укажи источники (они указаны в <> перед текстом документа) и процитируй, если используешь конкретные фрагменты.
            4. Если документы не дают точного ответа, честно скажи, что информации недостаточно.
            5. Используй ясный, дружелюбный и профессиональный стиль.
        """

        messages = [
            (
                "system",
                message,
            )
        ]

        ai_msg = self.llm.invoke(messages)

        return ai_msg.content
