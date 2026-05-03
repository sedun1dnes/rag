from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama

from ..chunker import chunk_document
from ...config import Config
from ...db.db import SessionLocal
from ...db.entities.document import Document


class RagPipeline:
    def __init__(self):
        self._qdrant_url = f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}"

        self.embedder = OllamaEmbeddings(
            model=Config.EMBEDDING_MODEL,
            base_url=f"http://{Config.EMBEDDING_HOST}:{Config.EMBEDDING_PORT}"
        )

        self.llm = ChatOllama(
            model=Config.GENERATION_MODEL,
            temperature=0,
            base_url=f"http://{Config.GENERATION_HOST}:{Config.GENERATION_PORT}"
        )

    def ingest_record(self, path: str, doc_id: str, collection_name: str):
        chunks = chunk_document(path)
        if not chunks:
            return

        for doc in chunks:
            doc.metadata["doc_id"] = doc_id

        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=self.embedder,
            collection_name=collection_name,
            url=self._qdrant_url,
        )

    def stream_response(self, query: str, collection_name: str):
        vs = QdrantVectorStore.from_existing_collection(
            embedding=self.embedder,
            collection_name=collection_name,
            url=self._qdrant_url,
        )
        docs = vs.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 5, "lambda_mult": 0.5},
        ).invoke(query)

        docs_data = []
        with SessionLocal() as db:
            for doc in docs:
                doc_id = doc.metadata.get("doc_id")
                document = db.get(Document, doc_id) if doc_id else None
                name = document.filename if document else "Неизвестный документ"
                docs_data.append(f"Документ <{name}>: {doc.page_content}")

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

        for chunk in self.llm.stream([("system", message)]):
            yield chunk.content

    def retrieve_and_generate(self, query: str, collection_name: str):
        vs = QdrantVectorStore.from_existing_collection(
            embedding=self.embedder,
            collection_name=collection_name,
            url=self._qdrant_url,
        )
        docs = vs.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 5, "lambda_mult": 0.5},
        ).invoke(query)

        docs_data = []
        with SessionLocal() as db:
            for doc in docs:
                doc_id = doc.metadata.get("doc_id")
                document = db.get(Document, doc_id) if doc_id else None
                name = document.filename if document else "Неизвестный документ"
                docs_data.append(f"Документ <{name}>: {doc.page_content}")

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

        ai_msg = self.llm.invoke([("system", message)])
        return ai_msg.content
