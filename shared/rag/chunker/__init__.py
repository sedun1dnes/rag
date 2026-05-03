from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document(file_path: str, chunk_size: int = 500, chunk_overlap: int = 200) -> List[Document]:
    """
    Разбивает файл на чанки и возвращает список Document с метаданными
    :param file_path: путь к файлу
    :param chunk_size: размер чанка в символах
    :param chunk_overlap: перекрытие между чанками
    :return: список Document
    """
    path = Path(file_path)
    documents: List[Document] = []

    if path.suffix.lower() in [".txt", ".md"]:
        text = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(file_path),
                    "type": path.suffix
                }
            )
        )

    elif path.suffix.lower() == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                documents.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": str(file_path),
                            "page": i,
                            "type": ".pdf"
                        }
                    )
                )
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)

    return chunks