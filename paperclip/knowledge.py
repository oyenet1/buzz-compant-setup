"""Local, citation-preserving lexical RAG. No third-party packages or API keys."""
import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "paperclip-knowledge.sqlite3"


def build():
    DB.parent.mkdir(parents=True, exist_ok=True)
    files = [ROOT / "SOUL.md", *sorted((ROOT / "marketing").rglob("*.md")),
             *sorted((ROOT / "departments").glob("*.json"))]
    # Optional product truth sheets are deliberately separate from book frameworks.
    files += sorted((ROOT / "products").rglob("*.md"))
    with sqlite3.connect(DB) as db:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(source UNINDEXED, line UNINDEXED, body)")
        db.execute("DELETE FROM chunks")
        count = 0
        for path in files:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
            for start in range(0, len(lines), 32):
                body = "\n".join(lines[start:start + 40])
                if body.strip():
                    db.execute("INSERT INTO chunks VALUES (?, ?, ?)",
                               (path.relative_to(ROOT).as_posix(), start + 1, body))
                    count += 1
    return {"files": len(files), "chunks": count}


def search(query, limit=5):
    if not DB.exists():
        raise SystemExit("Index missing: run python3 paperclip/knowledge.py index")
    terms = re.findall(r"\w+", query, re.UNICODE)
    if not terms:
        return []
    match = " OR ".join('"' + term + '"' for term in terms[:40])
    with sqlite3.connect(DB) as db:
        rows = db.execute(
            "SELECT source, line, body FROM chunks WHERE chunks MATCH ? ORDER BY bm25(chunks) LIMIT ?",
            (match, max(1, min(limit, 20)))).fetchall()
    return [{"citation": f"{source}:{line}", "text": body} for source, line, body in rows]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["index", "search"])
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(build() if args.command == "index" else search(args.query, args.limit),
                     ensure_ascii=True, indent=2))
