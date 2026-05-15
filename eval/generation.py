"""
Generation evaluation — uses RagPipeline directly, no HTTP.

Dataset: ai-forever/hist-rag-bench-private-qa
  columns: id, text_ids, text, url, question, answer, type

Documents are ingested once into a shared Qdrant collection "eval".
For each question stream_response() is called directly and the full answer
is collected.

Output files (written next to this script):
  generation_results.jsonl   one entry per question (detailed)
  generation_results.csv     one row per question: вопрос | идеальный ответ | ответ системы
  generation_scores.json     aggregate BERTScore (P, R, F1)

Usage (from the repo root):
  python rag/eval/generation.py [--limit N] [--skip-upload]

Shares the same Qdrant collection "eval" with retrieval.py.
Run retrieval.py first (or pass --skip-upload if already ingested).
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

_env_file = RAG_ROOT / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

from datasets import load_dataset

sys.path.insert(0, str(RAG_ROOT))
from shared.rag.pipeline import RagPipeline  # noqa: E402

COLLECTION = "eval"
HERE = Path(__file__).parent
RESULTS_JSONL = HERE / "generation_results.jsonl"
RESULTS_CSV = HERE / "generation_results.csv"
SCORES_FILE = HERE / "generation_scores.json"

CSV_HEADER = ["question", "target_answer", "system_answer"]

def text_to_doc_id(text: str) -> str:
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


def collect_response(pipeline: RagPipeline, question: str) -> str:
    return "".join(pipeline.stream_response(question, COLLECTION))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="evaluate only the first N questions")
    parser.add_argument("--skip-upload", action="store_true",
                        help="skip ingestion (collection already populated)")
    parser.add_argument("--model", default="xlm-roberta-base",
                        help="BERTScore model (default: xlm-roberta-base)")
    args = parser.parse_args()

    print("[data] loading dataset...")
    ds = load_dataset("ai-forever/hist-rag-bench-private-qa", split="train")
    rows = list(ds)
    if args.limit:
        rows = rows[: args.limit]
    print(f"[data] {len(rows)} questions")

    unique_texts: dict[str, str] = {}
    for row in ds:
        did = text_to_doc_id(row["text"])
        if did not in unique_texts:
            unique_texts[did] = row["text"]
    print(f"[data] {len(unique_texts)} unique documents")

    pipeline = RagPipeline()

    if not args.skip_upload:
        ingest_all(pipeline, unique_texts)
    else:
        print("[ingest] skipped")

    # Resume support
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
            reference = row["answer"]

            print(f"[{i + 1}/{len(pending)}] id={q_id} | {question[:80]}")

            try:
                predicted = collect_response(pipeline, question)
            except Exception as e:
                print(f"  ERROR: {e}")
                predicted = ""

            print(f"  ref : {reference[:80]}")
            print(f"  pred: {predicted[:120].strip()}\n")

            writer.writerow([question, reference, predicted])

            jout.write(json.dumps({
                "id": q_id,
                "type": row.get("type", ""),
                "question": question,
                "reference": reference,
                "predicted": predicted,
            }, ensure_ascii=False) + "\n")
            jout.flush()
            cout.flush()

    # Compute BERTScore over all saved results
    print("[score] loading results for BERTScore...")
    all_results = []
    with open(RESULTS_JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                all_results.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    n = len(all_results)
    predictions = [r["predicted"] for r in all_results]
    references = [r["reference"] for r in all_results]

    print(f"[score] computing BERTScore (model={args.model}, n={n})...")
    from bert_score import score as bert_score
    # bert_score calls tokenizer.build_inputs_with_special_tokens([]) on empty strings,
    # which is missing in newer transformers; replace empties to avoid it.
    predictions = [p if p.strip() else "null" for p in predictions]
    references = [r if r.strip() else "null" for r in references]
    P, R, F1 = bert_score(predictions, references, model_type=args.model, verbose=True)

    avg_p = float(P.mean())
    avg_r = float(R.mean())
    avg_f1 = float(F1.mean())

    by_type: dict[str, list] = {}
    for r, p, rc, f in zip(all_results, P.tolist(), R.tolist(), F1.tolist()):
        r["bertscore_p"] = round(p, 4)
        r["bertscore_r"] = round(rc, 4)
        r["bertscore_f1"] = round(f, 4)
        by_type.setdefault(r.get("type", "unknown"), []).append(r)

    summary = {
        "n": n,
        "model": args.model,
        "bertscore_precision": round(avg_p, 4),
        "bertscore_recall": round(avg_r, 4),
        "bertscore_f1": round(avg_f1, 4),
        "by_type": {
            t: {
                "n": len(rs),
                "bertscore_precision": round(sum(r["bertscore_p"] for r in rs) / len(rs), 4),
                "bertscore_recall": round(sum(r["bertscore_r"] for r in rs) / len(rs), 4),
                "bertscore_f1": round(sum(r["bertscore_f1"] for r in rs) / len(rs), 4),
            }
            for t, rs in by_type.items()
        },
    }
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"Generation results ({n} questions, model={args.model}):")
    print(f"  BERTScore P  : {avg_p:.4f}")
    print(f"  BERTScore R  : {avg_r:.4f}")
    print(f"  BERTScore F1 : {avg_f1:.4f}")
    for t, s in summary["by_type"].items():
        print(f"  [{t}] n={s['n']}  P={s['bertscore_precision']:.3f}  R={s['bertscore_recall']:.3f}  F1={s['bertscore_f1']:.3f}")
    print(f"\nSaved to {RESULTS_JSONL}, {RESULTS_CSV}, {SCORES_FILE}")


if __name__ == "__main__":
    main()
