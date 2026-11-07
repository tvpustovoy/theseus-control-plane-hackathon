"""Reproducible bounded batch runner (preparation; sends nothing by default).

Reads the private batch manifest (source IDs + hashes) and the local staging
store, validates every item, and prints the exact state. A real extraction
run additionally requires the owner-approved batch flag in the environment;
without it the runner stops before any source text is sent to a model.

Usage:
    python3 -m app.extraction.run_batch            # dry-run validation only
    OWNER_BATCH_APPROVED=1 MODEL_API_KEY=... \\
        python3 -m app.extraction.run_batch --run  # only after owner approval
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "database/private/a05-next-batch.json"
STORE = ROOT / "database/private/recplace_live_staging_store.json"
OUT_DIR = ROOT / "database/private/batch-out"


def load_items() -> tuple[dict, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    store = json.loads(STORE.read_text(encoding="utf-8"))
    by_id = {s["_id"]: s for s in store["collections"]["sources"]}
    return manifest, by_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    manifest, by_id = load_items()
    errors = []
    for item in manifest["items"]:
        source = by_id.get(item["source_id"])
        if not source:
            errors.append(f"missing:{item['source_id']}")
        elif source["text_sha256"] != item["text_sha256"]:
            errors.append(f"hash:{item['source_id']}")
    print(f"batch={manifest['batch']} items={len(manifest['items'])} errors={errors}")
    print(f"rule={manifest['selection_rule']}")
    if not args.run:
        print("dry-run: no model calls; real run needs OWNER_BATCH_APPROVED=1")
        return 0
    if os.environ.get("OWNER_BATCH_APPROVED") != "1":
        print("refused: OWNER_BATCH_APPROVED is not set; owner approval required")
        return 2
    print("owner approval flag present; extraction would write to", OUT_DIR)
    print("model calls are intentionally not wired until the approval is confirmed in-session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
