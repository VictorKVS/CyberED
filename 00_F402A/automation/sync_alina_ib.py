"""CyberED bridge to the local Alina knowledge worker.

Reads Alina's localhost-only HTTP API and produces a sanitized static JSON snapshot
for the CyberED course site. Original documents and absolute filesystem paths are
never copied into the repository by this script.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import quote
from urllib.request import urlopen


DEFAULT_BASE = "http://127.0.0.1:8768"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "site" / "data" / "alina_ib_index.json"

QUERIES = [
    {"id": "fstec", "label": "ФСТЭК", "q": "ФСТЭК"},
    {"id": "fsb", "label": "ФСБ", "q": "ФСБ"},
    {"id": "rkn", "label": "Роскомнадзор", "q": "Роскомнадзор"},
    {"id": "gost", "label": "ГОСТ", "q": "ГОСТ"},
    {"id": "pdn", "label": "152-ФЗ / ПДн", "q": "152-ФЗ"},
    {"id": "kii", "label": "187-ФЗ / КИИ", "q": "187-ФЗ"},
    {"id": "pp1119", "label": "ПП РФ 1119", "q": "1119"},
    {"id": "fstec117", "label": "ФСТЭК 117", "q": "117"},
    {"id": "fstec21", "label": "ФСТЭК 21", "q": "21"},
    {"id": "fstec239", "label": "ФСТЭК 239", "q": "239"},
    {"id": "fsb378", "label": "ФСБ 378", "q": "378"},
]


def get_json(url: str, timeout: float = 5.0):
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


def source_ref(path: str) -> dict:
    p = Path(path)
    digest = hashlib.sha256(path.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return {
        "source_id": digest,
        "filename": p.name,
        "suffix": p.suffix.lower(),
    }


def sanitize_book(book: dict) -> dict:
    ref = source_ref(book.get("path", ""))
    return {
        **ref,
        "status": book.get("status"),
        "chunks": book.get("chunks", 0),
        "error": book.get("error") or "",
        "notes": [
            {
                "locator": note.get("locator", ""),
                "excerpt": note.get("excerpt", ""),
            }
            for note in (book.get("notes") or [])
        ],
    }


def sanitize_hit(hit: dict, query_id: str, query_label: str) -> dict:
    ref = source_ref(hit.get("path", ""))
    return {
        **ref,
        "query_id": query_id,
        "query_label": query_label,
        "locator": hit.get("locator", ""),
        "excerpt": hit.get("excerpt", ""),
    }


def build_snapshot(base: str) -> dict:
    status = get_json(f"{base}/api/status")
    security = get_json(f"{base}/api/books?domain=security")

    hits = []
    query_stats = []
    seen = set()

    for item in QUERIES:
        rows = get_json(f"{base}/api/search?q={quote(item['q'])}")
        accepted = 0
        for row in rows:
            clean = sanitize_hit(row, item["id"], item["label"])
            key = (
                clean["source_id"],
                clean["locator"],
                clean["query_id"],
                clean["excerpt"][:160],
            )
            if key in seen:
                continue
            seen.add(key)
            hits.append(clean)
            accepted += 1
        query_stats.append(
            {
                "id": item["id"],
                "label": item["label"],
                "query": item["q"],
                "matches": accepted,
            }
        )

    tracks = []
    for track in status.get("study", {}).get("tracks", []):
        if track.get("id") == "security":
            tracks.append(
                {
                    "id": track.get("id"),
                    "title": track.get("title"),
                    "books": track.get("books", 0),
                    "ready": track.get("ready", 0),
                    "pending": track.get("pending", 0),
                    "attention": track.get("attention", 0),
                    "references": track.get("references", 0),
                    "chunks": track.get("chunks", 0),
                    "notes": track.get("notes", 0),
                    "progress": track.get("progress", 0),
                }
            )

    return {
        "schema": "cybered.alina.ib.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "alina": {
            "online": True,
            "mode": status.get("mode"),
            "phase": status.get("live", {}).get("phase"),
            "paused": status.get("paused", False),
            "processed": status.get("processed", 0),
            "chunks_total": status.get("chunks", 0),
            "errors_total": status.get("errors_total", 0),
            "security_tracks": tracks,
        },
        "security_library": {
            "books": [sanitize_book(b) for b in security.get("books", [])],
            "unsupported_count": len(security.get("unsupported") or []),
        },
        "regulatory_search": {
            "queries": query_stats,
            "hits": hits,
        },
        "safety": {
            "original_documents_copied": False,
            "absolute_paths_exported": False,
            "note": "Выдержки — поисковые фрагменты источников, а не подтвержденные требования.",
        },
    }


def write_snapshot(base: str, output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = build_snapshot(base)
    except Exception as exc:
        payload = {
            "schema": "cybered.alina.ib.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "alina": {
                "online": False,
                "error": str(exc),
            },
            "security_library": {"books": [], "unsupported_count": 0},
            "regulatory_search": {"queries": [], "hits": []},
            "safety": {
                "original_documents_copied": False,
                "absolute_paths_exported": False,
            },
        }

    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(output)

    print(
        f"[CyberED] Alina IB snapshot: online={payload['alina'].get('online')} "
        f"hits={len(payload['regulatory_search']['hits'])} -> {output}"
    )
    return 0 if payload["alina"].get("online") else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()

    if not args.watch:
        return write_snapshot(args.base.rstrip("/"), args.output)

    while True:
        write_snapshot(args.base.rstrip("/"), args.output)
        time.sleep(max(args.seconds, 15))


if __name__ == "__main__":
    raise SystemExit(main())
