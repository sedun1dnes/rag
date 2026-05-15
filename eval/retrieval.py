"""
Retrieval evaluation — uses RagPipeline directly, no HTTP.

Dataset: ai-forever/hist-rag-bench-private-qa
  columns: id, text_ids, text, url, question, answer, type

Each document is identified by a deterministic UUID derived from its text
(uuid5 of the MD5 hash). That same UUID is stored as doc_id in Qdrant, so
matching retrieved chunks back to the ground-truth document requires no DB
and no extra mapping.

Output files (written next to this script):
  retrieval_results.jsonl   one entry per question (detailed)
  retrieval_results.csv     one row per retrieved chunk (flat, for spreadsheets)
  retrieval_scores.json     aggregate hit@k and MRR

Usage (from the repo root):
  python rag/eval/retrieval.py [--limit N] [--skip-upload] [--k 3]

"""

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parent.parent

from datasets import load_dataset

sys.path.insert(0, str(RAG_ROOT))
from shared.rag.pipeline import RagPipeline  # noqa: E402

COLLECTION = "eval"
HERE = Path(__file__).parent
RESULTS_JSONL = HERE / "retrieval_results.jsonl"
RESULTS_CSV = HERE / "retrieval_results.csv"
SCORES_FILE = HERE / "retrieval_scores.json"

CSV_HEADER = [
    "question",
    "doc_true",
    "doc_retrieved",
    "chunk",
    "hit"
]


def text_to_doc_id(text: str) -> str:
    """Deterministic UUID stored as doc_id in Qdrant for each unique text."""
    h = hashlib.md5(text.encode()).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, h))


def ingest_all(pipeline: RagPipeline, unique_texts: dict[str, str]) -> None:
    total = len(unique_texts)
    print(f"[ingest] ingesting {total} unique documents...")
    for i, (doc_id, text) in enumerate(unique_texts.items(), start=1):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            tmp_path = f.name
        try:
            pipeline.ingest_record(tmp_path, doc_id, COLLECTION)
        finally:
            os.unlink(tmp_path)
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total}", end="\r")
    print(f"\n[ingest] done")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="evaluate only the first N questions")
    parser.add_argument("--skip-upload", action="store_true",
                        help="skip ingestion (collection already populated)")
    parser.add_argument("--k", type=int, default=3,
                        help="number of chunks to retrieve per question")
    args = parser.parse_args()

    print("[data] loading dataset...")
    ds = load_dataset("ai-forever/hist-rag-bench-private-qa", split="train")
    rows = list(ds)
    if args.limit:
        rows = rows[: args.limit]
    print(f"[data] {len(rows)} questions")

    # Build maps over the full dataset regardless of --limit
    unique_texts: dict[str, str] = {}   # doc_id -> text
    doc_id_to_row: dict[str, dict] = {} # doc_id -> row (for reference)
    for row in ds:
        did = text_to_doc_id(row["text"])
        if did not in unique_texts:
            unique_texts[did] = row["text"]
            doc_id_to_row[did] = row
    print(f"[data] {len(unique_texts)} unique documents")

    pipeline = RagPipeline()

    if not args.skip_upload:
        ingest_all(pipeline, unique_texts)
    else:
        print("[ingest] skipped")

    # Resume support via already-written JSONL
    completed_ids: set = set()
    if RESULTS_JSONL.exists():
        with open(RESULTS_JSONL, encoding="utf-8") as f:
            for line in f:
                try:
                    completed_ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        print(f"[eval] resuming — {len(completed_ids)} questions already done")

    pending = [r for r in rows if r["id"] not in completed_ids]
    print(f"[eval] {len(pending)} questions remaining\n")

    csv_write_header = not RESULTS_CSV.exists()
    with (
        open(RESULTS_JSONL, "a", encoding="utf-8") as jout,
        open(RESULTS_CSV, "a", encoding="utf-8", newline="") as cout,
    ):
        writer = csv.writer(cout, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        if csv_write_header:
            writer.writerow(CSV_HEADER)

        for i, row in enumerate(pending):
            q_id = row["id"]
            question = row["question"]
            true_doc_id = text_to_doc_id(row["text"])

            print(f"[{i + 1}/{len(pending)}] id={q_id} | {question[:80]}")

            try:
                retrieved = pipeline.retrieve(question, COLLECTION, k=args.k)
            except Exception as e:
                print(f"  ERROR: {e}")
                retrieved = []

            print(retrieved[0]["doc_id"])
            hit = any(c["doc_id"] == true_doc_id for c in retrieved)
            annotated = []

            for rank, chunk in enumerate(retrieved, start=1):
                is_correct = chunk["doc_id"] == true_doc_id
                annotated.append({
                    "rank": rank,
                    "doc_id": chunk["doc_id"],
                    "is_correct_doc": is_correct,
                    "chunk": chunk["chunk"],
                    "page": chunk["page"],
                })
                writer.writerow([
                    question,
                    true_doc_id,
                    chunk["doc_id"],
                    chunk["chunk"][:300].replace("\n", " "),
                    hit,
                ])

            print(f"  {'HIT' if hit else 'MISS'}  retrieved={len(retrieved)}")

            jout.write(json.dumps({
                "id": q_id,
                "question": question,
                "true_doc_id": true_doc_id,
                "retrieved": annotated,
                "hit": hit,
            }, ensure_ascii=False) + "\n")
            jout.flush()
            cout.flush()

    # Aggregate scores
    print("\n[score] computing metrics...")
    all_results = []
    with open(RESULTS_JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                all_results.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    n = len(all_results)
    hit_at_k = sum(1 for r in all_results if r["hit"]) / n if n else 0.0

    mrr_sum = 0.0
    for r in all_results:
        for chunk in r["retrieved"]:
            if chunk["is_correct_doc"]:
                mrr_sum += 1.0 / chunk["rank"]
                break

    summary = {
        "n": n,
        "k": args.k,
        f"hit@{args.k}": round(hit_at_k, 4),
        "mrr": round(mrr_sum / n, 4) if n else 0.0,
    }
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"Retrieval results ({n} questions, k={args.k}):")
    print(f"  hit@{args.k} : {hit_at_k:.4f}")
    print(f"  MRR      : {summary['mrr']:.4f}")


if __name__ == "__main__":
    main()
