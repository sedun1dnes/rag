from preprocess import (
    ChunkingConfig,
    annotate_token_counts,
    load_directory,
    load_pdf,
    load_txt,
    preprocess_documents,
    split_documents,
)


def main() -> None:
    # 1) Load
    # Вариант A: один TXT
    # documents = load_txt("example.txt", encoding="utf-8")

    # Вариант B: один PDF
    # documents = load_pdf("docs/sample.pdf")

    # Вариант C: папка с документами (.txt + .pdf)
    documents = load_directory("docs", encoding="utf-8")

    # 2) Preprocess (clean/normalize)
    documents = preprocess_documents(documents)

    # 3) Chunking
    chunks = split_documents(
        documents,
        config=ChunkingConfig(chunk_size=900, chunk_overlap=150),
    )

    # 4) Tokenization (count tokens for each chunk)
    chunks = annotate_token_counts(chunks, backend="tiktoken", encoding_name="cl100k_base")

    print(f"chunks: {len(chunks)}")
    print(f"first chunk tokens: {chunks[0].metadata.get('token_count')}")
    print("---")
    print(chunks[0].page_content[:800])


if __name__ == "__main__":
    main()