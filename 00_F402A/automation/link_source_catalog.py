from __future__ import annotations

import copy
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
SOURCE = DATA / "documents_source_full.json"
NORMALIZED = DATA / "documents.json"
LINKED = DATA / "documents_source_linked.local.json"
REPORT = DATA / "source_normalization_report.local.json"
QUEUE = DATA / "source_normalization_queue.local.json"

BRACKET_TAGS = re.compile(r"\s*\[[^\]]+\]\s*$")
NONWORD = re.compile(r"[^0-9a-zа-яё]+", re.I)
SPACES = re.compile(r"\s+")
DATE_RE = re.compile(r"\bот\s+(\d{2}\.\d{2}\.\d{4})\b", re.I)
NUMBER_RE = re.compile(r"\b(?:N|№)\s*([0-9]+(?:-[А-ЯA-Zа-яa-z0-9]+)?)", re.I)
QUOTE_RE = re.compile(r"[«„\"]([^»“\"]{8,})[»“\"]")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = BRACKET_TAGS.sub("", value or "")
    value = value.lower().replace("ё", "е")
    value = NONWORD.sub(" ", value)
    return SPACES.sub(" ", value).strip()


def semantic(value: str) -> str:
    value = normalize(value)
    for prefix in (
        "об утверждении и введении в действие ",
        "об утверждении ",
        "о введении в действие ",
    ):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def title_variants(value: str) -> list[str]:
    variants = [normalize(value), semantic(value)]
    for match in QUOTE_RE.findall(value or ""):
        variants.extend([normalize(match), semantic(match)])
    return [x for x in dict.fromkeys(variants) if x]


def title_score(source_title: str, normalized_title: str) -> float:
    targets = title_variants(normalized_title)
    sources = title_variants(source_title)
    best = 0.0
    for a in sources:
        for b in targets:
            if not a or not b:
                continue
            if a == b:
                return 1.0
            if b in a or a in b:
                shorter = min(len(a), len(b))
                longer = max(len(a), len(b))
                ratio = shorter / longer if longer else 0.0
                best = max(best, 1.0 if ratio >= 0.72 else 0.94 if ratio >= 0.55 else 0.86)
            best = max(best, SequenceMatcher(None, a, b).ratio())
    return best


def primary_number(value: str) -> str:
    match = NUMBER_RE.search(value or "")
    return match.group(1).upper().replace("Ё", "Е") if match else ""


def normalized_number(code: str) -> str:
    match = re.search(r"(\d+(?:-[А-ЯA-Zа-яa-z0-9]+)?)", code or "", re.I)
    return match.group(1).upper().replace("Ё", "Е") if match else ""


def source_family(value: str) -> str:
    text = (value or "").lower()
    if "фстэк" in text:
        return "fstec"
    if "фсб россии" in text:
        return "fsb"
    if "роскомнадзор" in text:
        return "rkn"
    if "роспотребнадзор" in text:
        return "rospotreb"
    if "минкомсвяз" in text:
        return "mincom"
    if "минцифры" in text:
        return "mindigital"
    if "банк россии" in text:
        return "cbr"
    if text.startswith("федеральный закон"):
        return "fz"
    if text.startswith("указ президента"):
        return "president"
    if text.startswith("постановление правительства"):
        return "government"
    if text.startswith("распоряжение правительства"):
        return "government"
    if text.startswith("гост") or text.startswith("«гост"):
        return "gost"
    return "other"


def normalized_family(doc: dict) -> str:
    joined = " ".join(
        [doc.get("id", ""), doc.get("code", ""), doc.get("authority", "")]
    ).lower()
    if "фстэк" in joined:
        return "fstec"
    if "фсб" in joined:
        return "fsb"
    if "ркн" in joined or "роскомнадзор" in joined:
        return "rkn"
    if "роспотреб" in joined:
        return "rospotreb"
    if "минкомсвяз" in joined:
        return "mincom"
    if "минцифры" in joined:
        return "mindigital"
    if "банк россии" in joined or "цб" in joined:
        return "cbr"

    code = doc.get("code", "")
    if re.match(r"^\d+-ФЗ", code, re.I):
        return "fz"
    if code.startswith("УП-"):
        return "president"
    if code.startswith("ПП-"):
        return "government"
    if doc.get("kind") == "gost":
        return "gost"
    return "other"


def families_compatible(source_doc: dict, normalized_doc: dict) -> bool:
    left = source_family(source_doc.get("title", ""))
    right = normalized_family(normalized_doc)
    return left == "other" or right == "other" or left == right


def code_score(source_doc: dict, normalized_doc: dict) -> float:
    left = primary_number(source_doc.get("title", ""))
    right = normalized_number(normalized_doc.get("code", ""))
    if not left or not right:
        return 0.0
    return 1.0 if left == right else 0.0


def candidate_score(source_doc: dict, normalized_doc: dict) -> float:
    ts = title_score(source_doc.get("title", ""), normalized_doc.get("title", ""))
    cs = code_score(source_doc, normalized_doc)
    compatible = families_compatible(source_doc, normalized_doc)

    if not compatible:
        return min(ts, 0.84)

    if ts >= 0.985:
        return 1.0
    if cs == 1.0 and ts >= 0.78:
        return max(0.97, ts)
    if ts >= 0.94:
        return ts
    if cs == 1.0 and ts >= 0.62:
        return 0.90
    if ts >= 0.88:
        return ts
    return max(ts * 0.82, cs * 0.58)


def parse_source_identity(item: dict) -> dict:
    title = item.get("title", "")
    date_match = DATE_RE.search(title)
    quoted = QUOTE_RE.findall(title)
    return {
        "source_id": item.get("source_id"),
        "source_line": item.get("source_line"),
        "section": item.get("section"),
        "kind": item.get("kind"),
        "authority_family": source_family(title),
        "act_date": date_match.group(1) if date_match else None,
        "act_number": primary_number(title) or None,
        "short_title": quoted[0] if quoted else None,
        "raw_title": title,
    }


def main() -> int:
    if not SOURCE.exists():
        print("SOURCE catalog not found; nothing to link.")
        return 0

    source = copy.deepcopy(load(SOURCE))
    normalized = load(NORMALIZED)
    norm_docs = normalized.get("documents", [])

    linked = 0
    ambiguous = 0
    unmatched = 0
    review = []
    queue = []

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
        item.pop("candidate_normalized_ids", None)

        identity = parse_source_identity(item)

        if not scored:
            unmatched += 1
            queue.append({**identity, "queue_status": "NORMALIZATION_REQUIRED"})
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
            candidates = [
                {"id": doc["id"], "score": round(score, 4)}
                for score, doc in scored[:3]
            ]
            item["match_method"] = "REVIEW_REQUIRED"
            item["match_score"] = round(best_score, 4)
            item["match_status"] = "AMBIGUOUS"
            item["candidate_normalized_ids"] = candidates
            ambiguous += 1
            row = {**identity, "queue_status": "REVIEW_REQUIRED", "candidates": candidates}
            review.append(row)
            queue.append(row)
        else:
            unmatched += 1
            queue.append({**identity, "queue_status": "NORMALIZATION_REQUIRED"})

    total = len(source.get("documents", []))
    coverage = round((linked / total * 100.0), 2) if total else 0.0
    source["normalization"] = {
        "linked": linked,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "coverage_percent": coverage,
        "rule": (
            "AUTO link only for high-confidence semantic matches. "
            "Recognized authority mismatch prevents automatic linking. "
            "SOURCE_FOUND != REQUIREMENT_VERIFIED."
        ),
    }

    LINKED.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "schema": "father.source_normalization_report.v2",
        "source_documents": total,
        "normalized_documents": len(norm_docs),
        "linked": linked,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "coverage_percent": coverage,
        "review_queue": review,
        "output_catalog": LINKED.name,
        "normalization_queue": QUEUE.name,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    queue_payload = {
        "schema": "father.source_normalization_queue.v1",
        "rule": "Queue items are candidates only. They are not VERIFIED requirements or verified current law.",
        "stats": {
            "total": len(queue),
            "review_required": ambiguous,
            "normalization_required": unmatched,
        },
        "items": queue,
    }
    QUEUE.write_text(json.dumps(queue_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"SOURCE -> NORMALIZED: {linked}/{total} linked "
        f"({coverage}%), {ambiguous} review, {unmatched} unmatched"
    )
    print(f"Normalization queue: {len(queue)} items -> {QUEUE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
