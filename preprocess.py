from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 150
    separators: tuple[str, ...] = ("\n\n", "\n", " ", "")
    add_start_index: bool = True


def normalize_text(text: str) -> str:
    """
    Базовая очистка корпоративных текстов:
    - Unicode normalization (NFKC)
    - удаление NUL
    - нормализация переводов строк
    - схлопывание лишних пробелов/пустых строк
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # убираем "висячие" пробелы в конце строк
    text = re.sub(r"[ \t]+\n", "\n", text)
    # схлопываем 3+ переводов строк в 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # схлопываем множественные пробелы/табы
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def preprocess_documents(
    docs: Iterable[Document],
    *,
    text_transform: Callable[[str], str] = normalize_text,
) -> list[Document]:
    out: list[Document] = []
    for d in docs:
        out.append(
            Document(
                page_content=text_transform(d.page_content),
                metadata=dict(d.metadata or {}),
            )
        )
    return out


def split_documents(
    docs: Iterable[Document],
    *,
    config: ChunkingConfig = ChunkingConfig(),
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=list(config.separators),
        add_start_index=config.add_start_index,
    )
    chunks = splitter.split_documents(list(docs))

    # Проставляем удобный идентификатор чанка
    for i, c in enumerate(chunks):
        c.metadata = dict(c.metadata or {})
        c.metadata.setdefault("chunk_id", i)
        # start_index добавляется сплиттером, если add_start_index=True
        # но оставляем совместимость, если кто-то выключит
        c.metadata.setdefault("start_index", c.metadata.get("start_index"))
    return chunks


TokenizerBackend = Literal["tiktoken", "transformers"]


def _get_tiktoken_encoder(encoding_name: str = "cl100k_base"):
    import tiktoken  # type: ignore

    return tiktoken.get_encoding(encoding_name)


def _get_hf_tokenizer(model_name: str = "intfloat/multilingual-e5-base"):
    from transformers import AutoTokenizer  # type: ignore

    return AutoTokenizer.from_pretrained(model_name, use_fast=True)


def count_tokens(
    text: str,
    *,
    backend: TokenizerBackend = "tiktoken",
    encoding_name: str = "cl100k_base",
    hf_model_name: str = "intfloat/multilingual-e5-base",
) -> int:
    """
    Подсчёт токенов для контроля размера чанков.
    - tiktoken: быстро, полезно если дальше LLM/OpenAI-совместимые токены
    - transformers: полезно если эмбеддинги на HF модели
    """
    if not text:
        return 0

    if backend == "tiktoken":
        enc = _get_tiktoken_encoder(encoding_name)
        return len(enc.encode(text))
    if backend == "transformers":
        tok = _get_hf_tokenizer(hf_model_name)
        return len(tok.encode(text, add_special_tokens=False))
    raise ValueError(f"Unknown backend: {backend}")


def annotate_token_counts(
    chunks: Iterable[Document],
    *,
    backend: TokenizerBackend = "tiktoken",
    encoding_name: str = "cl100k_base",
    hf_model_name: str = "intfloat/multilingual-e5-base",
    metadata_key: str = "token_count",
) -> list[Document]:
    out: list[Document] = []
    for c in chunks:
        md = dict(c.metadata or {})
        md[metadata_key] = count_tokens(
            c.page_content,
            backend=backend,
            encoding_name=encoding_name,
            hf_model_name=hf_model_name,
        )
        out.append(Document(page_content=c.page_content, metadata=md))
    return out


def load_txt(path: str | Path, *, encoding: str = "utf-8") -> list[Document]:
    from langchain_community.document_loaders import TextLoader

    loader = TextLoader(str(path), encoding=encoding)
    return loader.load()


def load_pdf(path: str | Path) -> list[Document]:
    """
    PDF -> Documents (обычно 1 Document = 1 страница).
    Требует пакет `pypdf`.
    """
    from langchain_community.document_loaders import PyPDFLoader

    loader = PyPDFLoader(str(path))
    return loader.load()


def load_directory_txt(
    directory: str | Path,
    *,
    encoding: str = "utf-8",
) -> list[Document]:
    """
    Простая загрузка всех .txt из папки.
    (Для PDF/DOCX лучше подключить отдельные loaders позже.)
    """
    directory = Path(directory)
    docs: list[Document] = []
    for p in sorted(directory.rglob("*.txt")):
        docs.extend(load_txt(p, encoding=encoding))
    return docs


def load_directory(
    directory: str | Path,
    *,
    encoding: str = "utf-8",
    include_exts: tuple[str, ...] = (".txt", ".pdf"),
) -> list[Document]:
    """
    Загрузка документов из папки (рекурсивно) по расширениям.

    - `.txt`: TextLoader
    - `.pdf`: PyPDFLoader (pypdf)
    """
    directory = Path(directory)
    docs: list[Document] = []
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in include_exts}

    for p in sorted(directory.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue

        if p.suffix.lower() == ".txt":
            docs.extend(load_txt(p, encoding=encoding))
        elif p.suffix.lower() == ".pdf":
            docs.extend(load_pdf(p))
        else:
            continue

    return docs

