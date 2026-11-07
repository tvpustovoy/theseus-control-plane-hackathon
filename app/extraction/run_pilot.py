"""Bounded M01 extraction pilot runner.

Loads the private 3-record sample, chunks each record, calls the Meta Model
API per chunk, and passes every returned assert through the local quote gate.
Accepted claims and rejected items (with reasons) are written to the private
output directory only; quotes never leave database/private/.

Usage:
    python3 -m app.extraction.run_pilot --dry-run
    MODEL_API_KEY=... python3 -m app.extraction.run_pilot

Without a credential the runner fails closed before any source text is sent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from app.extraction import meta_adapter
from app.extraction.quote_gate import chunk_text, load_jsonl, run_gate, text_sha256

ROOT = pathlib.Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "database/private/muse-meta-pilot-3.jsonl"
OUT_DIR = ROOT / "database/private"
PROMPT_FILE = ROOT / "app/extraction/prompts/sales-v1.md"
PROMPT_VERSION = "sales-v1"
MODEL = "muse-spark-1.3"


def record_provenance(record: dict) -> dict:
    """Provenance attached to every claim; source field types are preserved
    exactly (for example src_row stays an integer when the source has one)."""
    return {
        "dump_id": record["dump_id"],
        "src_file": record["src_file"],
        "src_row": record["src_row"],
        "table": record["table"],
        "kind": record["kind"],
        "source_id": str(record["source_id"]),
        "text_sha256": record["text_sha256"],
    }


def build_messages(record: dict, chunk: dict, prompt_text: str) -> list[dict]:
    user = (
        f"source_kind: {record['kind']}\n"
        f"table: {record['table']}\n"
        f"chunk {chunk['chunk_index']} chars {chunk['char_start']}-{chunk['char_end']}\n\n"
        f"{chunk['text']}"
    )
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": user},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=str(SAMPLE))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = load_jsonl(args.sample)
    prompt_text = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_hash = text_sha256(prompt_text)
    run_id = uuid.uuid4().hex

    plan = []
    for record in records:
        chunks = chunk_text(record["text"], max_chars=1800)
        plan.append((record, chunks))
        print(
            f"{record['kind']} source={record['source_id']} row={record['src_row']} "
            f"chunks={len(chunks)} text_sha256={record['text_sha256'][:12]}"
        )
    print(f"prompt={PROMPT_VERSION} sha256={prompt_hash[:12]} model={args.model} run={run_id}")

    if args.dry_run:
        print("dry-run: no API calls made")
        return 0

    meta_adapter.require_key()  # fail closed before any text leaves the host

    accepted_all: list[dict] = []
    rejected_all: list[dict] = []
    usage_total: dict = {}

    for record, chunks in plan:
        provenance = record_provenance(record)
        for chunk in chunks:
            response = meta_adapter.chat_completion(
                build_messages(record, chunk, prompt_text), model=args.model
            )
            usage = response.get("usage") or {}
            for key, value in usage.items():
                if isinstance(value, (int, float)):
                    usage_total[key] = usage_total.get(key, 0) + value
            content = response["choices"][0]["message"]["content"]
            parsed = meta_adapter.extract_json_object(content)
            gate = run_gate(parsed.get("asserts", []), chunk["text"])
            for claim in gate.accepted:
                claim["evidence_locator"]["char_start"] += chunk["char_start"]
                claim["evidence_locator"]["char_end"] += chunk["char_start"]
                claim.update(
                    provenance=provenance,
                    chunk_index=chunk["chunk_index"],
                    run_id=run_id,
                    model=args.model,
                    prompt_version=PROMPT_VERSION,
                    prompt_sha256=prompt_hash,
                )
                accepted_all.append(claim)
            for item in gate.rejected:
                rejected_all.append({**item, "provenance": provenance})

    out = pathlib.Path(args.out_dir)
    claims_path = out / "m01-claims.json"
    rejected_path = out / "m01-rejected.json"
    claims_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": args.model,
                "prompt_version": PROMPT_VERSION,
                "prompt_sha256": prompt_hash,
                "usage": usage_total,
                "claims": accepted_all,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    rejected_path.write_text(
        json.dumps({"run_id": run_id, "rejected": rejected_all}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"accepted={len(accepted_all)} rejected={len(rejected_all)} usage={usage_total}")
    print(f"wrote {claims_path} and {rejected_path} (private, not for Git)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
