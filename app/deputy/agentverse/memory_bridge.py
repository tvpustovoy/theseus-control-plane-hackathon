"""Owner-authorized read-only access to RecPlace. Never exposes a Mongo credential."""
import hmac
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / "database" / "private"
TOKEN = (PRIVATE / "deputy-bridge-key").read_text().strip()
CLIENT = MongoClient((PRIVATE / "mongodb-uri").read_text().strip(),
                     serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                     socketTimeoutMS=8000, maxPoolSize=4)
DB = CLIENT["theseus_recplace"]
COLLECTIONS = {"raw_records", "sources", "claims", "source_chunks", "fact_refs",
               "decisions", "model_versions", "extraction_runs", "review_signals",
               "simulation_runs", "simulation_events", "crm_deals_demo", "import_runs",
               "deputy_public_state"}
FILTERS = {"source_type", "source_table", "source_id", "claim_id", "record_id", "period",
           "arm", "status", "actor_type", "kind", "organization_id", "day"}


def now():
    return datetime.now(timezone.utc).isoformat()


def bounded(row, query=""):
    """Return a bounded excerpt with explicit truncation; never a silent full-source claim."""
    result = {}
    truncated = []
    for key, value in row.items():
        if isinstance(value, str) and len(value) > 2400:
            pos = value.lower().find(query.lower()) if query else 0
            start = max(0, pos - 500)
            result[key] = value[start:start + 2400]
            truncated.append({"field": key, "start": start, "end": start + len(result[key]), "original_chars": len(value)})
        else:
            result[key] = value
    if truncated:
        result["excerpt_boundaries"] = truncated
    return result


def query_memory(args):
    collection = args.get("collection", "sources")
    if collection not in COLLECTIONS:
        raise ValueError("Collection not allowed")
    operation = args.get("operation", "search")
    query = str(args.get("query", ""))[:160]
    limit = max(1, min(int(args.get("limit", 5)), 8))
    filters = args.get("filters") or {}
    if not isinstance(filters, dict) or any(k not in FILTERS or not isinstance(v, (str, int, float, bool)) for k,v in filters.items()):
        raise ValueError("Only approved scalar equality filters are allowed")
    match = dict(filters)
    if query:
        fields = ["text", "statement", "summary", "v_json", "claim_id", "source_id", "record_id", "justification_text"]
        match["$or"] = [{field: {"$regex": re.escape(query), "$options": "i"}} for field in fields]
    if operation == "count":
        return {"collection": collection, "count": DB[collection].count_documents(match, maxTimeMS=5000), "read_at_utc": now()}
    if operation == "read":
        rid = str(args.get("record_id", ""))[:200]
        if not rid:
            raise ValueError("record_id is required")
        match = {"$or": [{key: rid} for key in ["_id", "source_id", "claim_id", "record_id"]]}
    elif operation != "search":
        raise ValueError("Unknown operation")
    rows = list(DB[collection].find(match).limit(limit).max_time_ms(5000))
    records = [bounded(row, query) for row in rows]
    payload = {"collection": collection, "read_at_utc": now(), "records": records,
               "returned": len(records), "limit": limit, "exhaustive": False,
               "note": "Bounded search results; no match is not proof of absence. Text excerpts carry boundaries."}
    if len(json.dumps(payload, default=str)) > 45000:
        raise ValueError("Result too large; narrow the query")
    return payload


def memory_context():
    inventory = {}
    for name in sorted(COLLECTIONS):
        inventory[name] = DB[name].count_documents({}, maxTimeMS=5000)
    curated = list(CLIENT["theseus_deputy_demo"]["memory"].find({"public_safe": True}, {"_id": 0}).limit(40))
    state = [bounded(row) for row in DB["deputy_public_state"].find(
        {"_id": "deputy_mirror:recplace:current"}).limit(1)]
    return {"connected": True, "transport": "authenticated_https_to_mongodb", "read_at_utc": now(),
            "scope": "Owner-authorized RecPlace database; source corpus is historical, simulation rows are synthetic",
            "collection_counts": inventory, "records": curated, "current_state_records": state,
            "note": "Counts are fresh. Raw and sources represent overlapping layers, not unique-document totals. Zero claims means no claims persisted in this collection, not no local extraction artifacts."}


class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        return hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN)

    def respond(self, payload):
        body = json.dumps(payload, default=str).encode()
        if len(body) > 100000:
            raise ValueError("Response too large")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authorized():
            self.send_error(401); return
        if self.path != "/memory":
            self.send_error(404); return
        try:
            self.respond(memory_context())
            print("memory_context ok", flush=True)
        except Exception as error:
            print("memory_context error=" + type(error).__name__, flush=True)
            self.send_error(503, "Memory unavailable")

    def do_POST(self):
        if not self.authorized():
            self.send_error(401); return
        if self.path != "/query":
            self.send_error(404); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid request size")
            args = json.loads(self.rfile.read(length))
            if not isinstance(args, dict):
                raise ValueError("Object required")
            self.respond(query_memory(args))
            print("memory_query ok collection=" + str(args.get("collection")), flush=True)
        except Exception as error:
            self.respond({"error": "Query unavailable or outside the permitted read contract", "error_type": type(error).__name__})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Memory bridge listening on 127.0.0.1:18765", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 18765), Handler).serve_forever()
