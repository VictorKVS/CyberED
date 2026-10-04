from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
SOURCE = DATA / "documents_source_full.json"
NORMALIZED = DATA / "documents.json"
REPORT = DATA / "source_normalization_report.json"

BRACKET_TAGS = re.compile(r"\s*\[[^\]]+\]\s*$")
NONWORD = re.compile(r"[^0-9a-zа-яё]+", re.I)
SPACES = re.compile(r"\s+")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = BRACKET_TAGS.sub("", value or "")
    value = value.lower().replace("ё", "е")
    value = NONWORD.sub(" ", value)
    return SPACES.sub(" ", value).strip()


def title_score(source_title: str, normalized_title: str) -> float:
    a = normalize(source_title)
    b = normalize(normalized_title)
    if not a or not b:
        return 0.0
    if b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def code_tokens(code: str) -> list[str]:
    code = (code or "").upper().replace("Ё", "Е")
    return [x for x in re.findall(r"\d+[А-ЯA-Z-]*", code) if len(x) >= 2]


def code_score(source_title: str, code: str) -> float:
    upper = (source_title or "").upper().replace("Ё", "Е")
    tokens = code_tokens(code)
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in upper)
    if hits == len(tokens):
        return 1.0
    if hits:
        return 0.65
    return 0.0


def candidate_score(source_doc: dict, normalized_doc: dict) -> float:
    ts = title_score(source_doc.get("title", ""), normalized_doc.get("title", ""))
    cs = code_score(source_doc.get("title", ""), normalized_doc.get("code", ""))

    if ts >= 0.97:
        return 1.0
    if cs == 1.0 and ts >= 0.72:
        return max(0.96, ts)
    if ts >= 0.91:
        return ts
    if cs == 1.0 and ts >= 0.58:
        return 0.90
    return max(ts * 0.82, cs * 0.60)


def main() -> int:
    if not SOURCE.exists():
        print("SOURCE catalog not found; nothing to link.")
        return 0

    source = load(SOURCE)
    normalized = load(NORMALIZED)
    norm_docs = normalized.get("documents", [])

    linked = 0
    ambiguous = 0
    unmatched = 0
    review = []

    for item in source.get("documents", []):
        scored = []
        for doc in norm_docs:
            score = candidate_score(item, doc)
            if score >= 0.78:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        item["normalized_id"] = None
        item["match_method"] = None
        item["match_score"] = None
        item["match_status"] = "UNMATCHED"

        if not scored:
            unmatched += 1
            continue

        best_score, best_doc = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        margin = best_score - second_score

        if best_score >= 0.94 and margin >= 0.035:
            item["normalized_id"] = best_doc["id"]
            item["match_method"] = "AUTO_HIGH_CONFIDENCE"
            item["match_score"] = round(best_score, 4)
            item["match_status"] = "LINKED"
            linked += 1
        elif best_score >= 0.86:
            item["match_method"] = "REVIEW_REQUIRED"
            item["match_score"] = round(best_score, 4)
            item["match_status"] = "AMBIGUOUS"
            item["candidate_normalized_ids"] = [
                {"id": doc["id"], "score": round(score, 4)}
                for score, doc in scored[:3]
            ]
            ambiguous += 1
            review.append({
                "source_id": item["source_id"],
                "title": item["title"],
                "candidates": item["candidate_normalized_ids"],
            })
        else:
            unmatched += 1

    total = len(source.get("documents", []))
    coverage = round((linked / total * 100.0), 2) if total else 0.0
    source["normalization"] = {
        "linked": linked,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "coverage_percent": coverage,
        "rule": "AUTO link only for high-confidence matches; ambiguous records require review.",
    }

    SOURCE.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "schema": "father.source_normalization_report.v1",
        "source_documents": total,
        "normalized_documents": len(norm_docs),
        "linked": linked,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "coverage_percent": coverage,
        "review_queue": review,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"SOURCE -> NORMALIZED: {linked}/{total} linked "
        f"({coverage}%), {ambiguous} review, {unmatched} unmatched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
