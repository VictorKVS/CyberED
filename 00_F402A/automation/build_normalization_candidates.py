from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
QUEUE = DATA / "source_normalization_queue.local.json"
NORMALIZED = DATA / "documents.json"
OUT = DATA / "normalization_candidates.local.json"

AUTHORITY_LABELS = {
    "fstec": "ФСТЭК России",
    "fsb": "ФСБ России",
    "rkn": "Роскомнадзор",
    "rospotreb": "Роспотребнадзор",
    "mincom": "Минкомсвязь России",
    "mindigital": "Минцифры России",
    "cbr": "Банк России",
    "fz": "Федеральное законодательство",
    "president": "Президент Российской Федерации",
    "government": "Правительство Российской Федерации",
    "gost": "Росстандарт / стандарты",
    "other": "Требуется определить",
}

PREFIXES = {
    "fstec": "ФСТЭК",
    "fsb": "ФСБ",
    "rkn": "РКН",
    "rospotreb": "РПН",
    "mincom": "Минкомсвязь",
    "mindigital": "Минцифры",
    "cbr": "БР",
    "president": "УП",
    "government": "ПП",
}

SECTION_TAGS = {
    "Персональные данные": ["ПДн"],
    "Критическая информационная инфраструктура": ["КИИ"],
    "Криптографическая защита информации": ["СКЗИ", "криптография"],
    "Государственные информационные системы": ["ГИС"],
    "Видеонаблюдение": ["ИТСО", "видеонаблюдение"],
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean_title(item: dict) -> str:
    title = (item.get("short_title") or item.get("raw_title") or "").strip()
    return title.strip("«»„“\" ")


def proposed_code(item: dict) -> str:
    family = item.get("authority_family") or "other"
    number = item.get("act_number")

    if family == "fz" and number:
        return number
    if family == "gost":
        raw = item.get("raw_title") or ""
        match = re.search(r"(ГОСТ(?:\s+Р)?\s+[0-9][0-9A-Za-z.\-–—/]*)", raw, re.I)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).upper()
    if number and family in PREFIXES:
        return f"{PREFIXES[family]}-{number}"
    if number:
        return number
    return item.get("source_id") or "SOURCE-UNKNOWN"


def infer_tags(item: dict) -> list[str]:
    tags = []
    hay = " ".join(
        [
            item.get("section") or "",
            item.get("raw_title") or "",
            item.get("kind") or "",
        ]
    ).lower()

    rules = [
        (("персональн", "пдн"), "ПДн"),
        (("кии", "критическ"), "КИИ"),
        (("гис", "государственн информацион"), "ГИС"),
        (("фстэк",), "ФСТЭК"),
        (("фсб",), "ФСБ"),
        (("крипт", "скзи"), "СКЗИ"),
        (("гост", "iso"), "стандарт"),
        (("искусственн интеллект", "ai", "нейросет"), "AI"),
        (("облач", "cloud"), "Cloud"),
        (("видеонаблю", "скуд", "охран"), "ИТСО"),
        (("аудит", "контрол"), "Audit"),
        (("инцидент", "госсопка"), "Incident Response"),
    ]
    for needles, tag in rules:
        if any(token in hay for token in needles) and tag not in tags:
            tags.append(tag)
    return tags


def risk_flags(item: dict, normalized_codes: set[str]) -> list[str]:
    flags = []
    code = proposed_code(item)
    if code in normalized_codes:
        flags.append("PROPOSED_CODE_COLLISION")
    if not item.get("act_number"):
        flags.append("NUMBER_NOT_PARSED")
    if not item.get("act_date"):
        flags.append("DATE_NOT_PARSED")
    if (item.get("authority_family") or "other") == "other":
        flags.append("AUTHORITY_NOT_PARSED")
    if not item.get("short_title"):
        flags.append("SHORT_TITLE_NOT_PARSED")
    return flags


def main() -> int:
    if not QUEUE.exists():
        print("Normalization queue not found. Run link_source_catalog.py first.")
        return 2

    queue = load(QUEUE)
    normalized = load(NORMALIZED)
    normalized_codes = {doc.get("code", "") for doc in normalized.get("documents", [])}

    candidates = []
    reviews = []

    for item in queue.get("items", []):
        if item.get("queue_status") == "REVIEW_REQUIRED":
            reviews.append(
                {
                    "source_id": item.get("source_id"),
                    "action": "REVIEW_LINK",
                    "title": clean_title(item),
                    "source": item,
                    "candidates": item.get("candidates", []),
                    "decision": None,
                    "decision_evidence": [],
                }
            )
            continue

        code = proposed_code(item)
        flags = risk_flags(item, normalized_codes)
        candidate = {
            "candidate_id": f"CAND-{item.get('source_id', 'UNKNOWN')}",
            "action": "CREATE_NORMALIZED_DOCUMENT",
            "state": "CANDIDATE",
            "source_id": item.get("source_id"),
            "proposed_document": {
                "id": None,
                "code": code,
                "title": clean_title(item),
                "kind": item.get("kind") or "other",
                "authority": AUTHORITY_LABELS.get(
                    item.get("authority_family") or "other",
                    "Требуется определить",
                ),
                "status": "CANDIDATE",
                "edition": item.get("act_date") or "требуется определить",
                "scope": item.get("section") or "требуется определить",
                "summary": (
                    "Автоматически созданная карточка-кандидат из полного SOURCE-каталога. "
                    "До проверки актуальности, реквизитов и применимости не переводить в VERIFIED."
                ),
                "source_url": None,
                "tags": infer_tags(item),
                "requirements": [],
            },
            "source_trace": {
                "source_line": item.get("source_line"),
                "raw_title": item.get("raw_title"),
                "authority_family": item.get("authority_family"),
                "act_number": item.get("act_number"),
                "act_date": item.get("act_date"),
                "section": item.get("section"),
            },
            "risk_flags": flags,
            "ready_for_review": len(flags) <= 1,
            "decision": None,
            "decision_evidence": [],
        }
        candidates.append(candidate)

    ready = sum(1 for x in candidates if x["ready_for_review"])
    flagged = len(candidates) - ready
    payload = {
        "schema": "father.normalization_candidates.v1",
        "rule": (
            "CANDIDATE is not VERIFIED. Promotion to the canonical documents.json "
            "requires duplicate check, current-version verification and reviewer evidence."
        ),
        "stats": {
            "create_candidates": len(candidates),
            "review_links": len(reviews),
            "ready_for_review": ready,
            "flagged": flagged,
        },
        "create_candidates": candidates,
        "review_links": reviews,
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Normalization candidates: {len(candidates)} create / "
        f"{len(reviews)} link review / {ready} ready / {flagged} flagged"
    )
    print(f"Output: {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
