"""
Loads a scoped slice of ai4bharat/MSMARCO-XI.

We do NOT index all 11.5M rows (55.6GB) — that's not a hackathon-scale
decision, it's an infrastructure decision. We pick one language and a
bounded row count, and document that choice in docs/ARCHITECTURE.md.

Schema per row (see HF dataset card):
    query (str), Answer (str), query_id (int), query_type (str)
    Eng_Query (str), Eng_Answer (str)
    passages: {
        is_selected: [0/1, ...],
        English_passages: [...],
        Translated_passages: [...],
    }

NOTE on parquet reading: HuggingFace's `datasets` library reads parquet
via pyarrow's `iter_batches()`, which hits a real pyarrow bug on this
dataset's nested 'passages' struct columns
(ArrowNotImplementedError: Nested data conversions not implemented for
chunked array outputs) — happens both in streaming and non-streaming mode,
since both paths go through iter_batches internally. We sidestep this
entirely by downloading the file ourselves and reading it with plain
pyarrow.parquet.read_table(), which uses a different (non-batched) read
path that handles nested columns correctly.
"""

import argparse
import json
import os

import httpx
# import pyarrow as pa
# import pyarrow.parquet as pq
import polars as pl

DEFAULT_LANG = "hi"
DEFAULT_SPLIT = "train"
DEFAULT_N_ROWS = 8000

LANG_CODE_TO_FILE_PREFIX = {
    "as": "asm", "bn": "ben", "gu": "guj", "hi": "hin", "kn": "kan",
    "ml": "mal", "mr": "mar", "ne": "nep", "or": "ory", "pa": "pan",
    "sa": "san", "ta": "tam", "te": "tel", "ur": "urd",
}

SPLIT_TO_DIR_AND_SUFFIX = {
    "train": ("train", "train"),
    "validation": ("validation", "val"),
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "_parquet_cache")


def _download_file(url: str, dest_path: str, max_retries: int = 5):
    if os.path.exists(dest_path):
        print(f"Already downloaded: {dest_path}")
        return dest_path

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".tmp"

    for attempt in range(max_retries):
        resume_from = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}

        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=60, headers=headers) as resp:
                if resp.status_code not in (200, 206):
                    resp.raise_for_status()

                # total size: for a 206 partial response, content-length is
                # the REMAINING bytes, so add what we've already got
                content_length = int(resp.headers.get("content-length", 0))
                total = resume_from + content_length if resp.status_code == 206 else content_length

                mode = "ab" if resp.status_code == 206 else "wb"
                downloaded = resume_from
                with open(tmp_path, mode) as f:
                    for chunk in resp.iter_bytes(chunk_size=4 * 1024 * 1024):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded / total * 100
                            print(f"\r  {pct:5.1f}%  ({downloaded/1e9:.2f}GB / {total/1e9:.2f}GB)", end="", flush=True)
            print()
            os.rename(tmp_path, dest_path)
            return dest_path

        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as e:
            print(f"\n  Connection dropped ({e}). Retrying with resume ({attempt + 1}/{max_retries})...")
            continue

    raise RuntimeError(f"Failed to download {url} after {max_retries} attempts")


def load_slice(
    lang: str = DEFAULT_LANG,
    split: str = DEFAULT_SPLIT,
    n_rows: int = DEFAULT_N_ROWS,
):
    """
    Downloads the language-specific parquet shard locally, then reads only
    the first n_rows using Polars.

    Polars is used here because MSMARCO-XI contains nested struct/list
    columns inside `passages`, which trigger PyArrow's:

        ArrowNotImplementedError:
        Nested data conversions not implemented for chunked array outputs

    when read through the Parquet row-group/batch APIs.
    """

    prefix = LANG_CODE_TO_FILE_PREFIX.get(lang)
    if prefix is None:
        raise ValueError(
            f"Unknown lang code '{lang}'. "
            f"Supported: {list(LANG_CODE_TO_FILE_PREFIX.keys())}"
        )

    dir_name, suffix = SPLIT_TO_DIR_AND_SUFFIX.get(
        split,
        ("train", "train"),
    )

    file_url = (
        f"https://huggingface.co/datasets/ai4bharat/MSMARCO-XI/resolve/main/"
        f"{dir_name}/{prefix}{suffix}.parquet"
    )

    local_path = os.path.join(
        CACHE_DIR,
        f"{prefix}{suffix}.parquet",
    )

    print(f"Downloading: {file_url}")
    _download_file(file_url, local_path)

    print(f"Reading first {n_rows} rows with Polars...")

    # Only load columns actually required by flatten_to_documents().
    # This avoids unnecessarily materializing the `meta` struct.
    columns = [
        "target_lang",
        "Answer",
        "query_id",
        "query_type",
        "passages",
        "Eng_Query",
        "Eng_Answer",
        "query",
    ]

    df = pl.read_parquet(
        local_path,
        columns=columns,
        n_rows=n_rows,
    )

    print(f"Read {df.height} query rows.")

    # Convert Polars structs/lists into ordinary Python dictionaries/lists.
    rows = df.to_dicts()

    return rows

def flatten_to_documents(rows):
    """
    Turns each MSMARCO-XI row into flat passage-documents ready for chunking.
    We keep BOTH English and translated passage text (metadata-tagged by
    language) so retrieval can work across either, and we preserve
    is_selected as a relevance signal / eval label (not used at query time,
    used to validate retrieval quality during dev).
    """
    documents = []
    for row in rows:
        passages = row.get("passages", {})
        is_selected = passages.get("is_selected", [])
        eng_passages = passages.get("English_passages", [])
        trans_passages = passages.get("Translated_passages", [])

        for idx, (eng_text, trans_text) in enumerate(zip(eng_passages, trans_passages)):
            selected_flag = is_selected[idx] if idx < len(is_selected) else 0

            documents.append({
                "doc_id": f"{row['query_id']}_{idx}_en",
                "text": eng_text,
                "language": "eng_Latn",
                "query_id": row["query_id"],
                "query": row.get("Eng_Query", ""),
                "query_type": row.get("query_type", "UNKNOWN"),
                "is_selected": bool(selected_flag),
                "passage_index": idx,
            })
            documents.append({
                "doc_id": f"{row['query_id']}_{idx}_translated",
                "text": trans_text,
                "language": row.get("target_lang", "unknown"),
                "query_id": row["query_id"],
                "query": row.get("query", ""),
                "query_type": row.get("query_type", "UNKNOWN"),
                "is_selected": bool(selected_flag),
                "passage_index": idx,
            })

    return documents


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default=DEFAULT_LANG)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--n_rows", type=int, default=DEFAULT_N_ROWS)
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Loading {args.n_rows} rows from ai4bharat/MSMARCO-XI [{args.lang}/{args.split}] ...")
    rows = load_slice(args.lang, args.split, args.n_rows)
    print(f"Loaded {len(rows)} query rows.")

    documents = flatten_to_documents(rows)
    print(f"Flattened to {len(documents)} passage-documents.")

    out_path = os.path.join(OUT_DIR, f"documents_{args.lang}_{args.n_rows}.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
