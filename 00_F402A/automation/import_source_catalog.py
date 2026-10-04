from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "site" / "data" / "documents_source_full.json"

META_RE = re.compile(
    r"^(Комментарий|Примечание|См\.|Источник|Версия справочника|Дата |"
    r"Сведения|Общее количество|Перечень удаленных|В раздел|Из раздела)",
    re.I,
)

DOC_PREFIX_RE = re.compile(
    r"^(Федеральный закон|Закон РФ|Указ Президента РФ|"
    r"Распоряжение Президента РФ|Постановление Правительства РФ|"
    r"Распоряжение Правительства РФ|Приказ |Письмо |<Письмо>|"
    r"Информационное сообщение|ИНФОРМАЦИОННОЕ СООБЩЕНИЕ|"
    r"Методический документ|Методические рекомендации|Рекомендации |"
    r"ГОСТ|«ГОСТ|Положение |Указание Банка России|Положение Банка России|"
    r"Решение |Определение |Постановление |Распоряжение |"
    r"Федеральные нормы|РД |Руководящий документ|СТО БР ИББС|СТО/БР|"
    r"МИ |ISO/IEC|ISO |IEC |«Конституция|«Гражданский кодекс|"
    r"«Трудовой кодекс|«Уголовный кодекс|«Кодекс Российской Федерации)",
    re.I,
)

DATED_DOC_RE = re.compile(
    r"\bот\s+\d{2}\.\d{2}\.\d{4}\b.*(?:\bN\s*[\w/-]+|№\s*[\w/-]+)",
    re.I,
)

NAMED_DOC_RE = re.compile(
    r"^(Доктрина|Стратегия|Концепция|Основы государственной политики|"
    r"Базовая модель угроз|Типовая модель угроз|Положение о|ПЕРЕЧЕНЬ |"
    r"Перечень типовых|Правила |Требования |Инструкция |"
    r"Инструкция Банка России)",
    re.I,
)


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Не удалось определить кодировку: {path}")


def is_document(line: str) -> bool:
    if not line or META_RE.match(line):
        return False
    if DOC_PREFIX_RE.match(line):
        return True
    if DATED_DOC_RE.search(line):
        return True
    return bool(NAMED_DOC_RE.match(line) and len(line) > 35)


def is_heading(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not line or len(line) > 180 or is_document(line) or META_RE.match(line):
        return False
    if index > 0 and lines[index - 1]:
        return False

    seen = 0
    for j in range(index + 1, min(len(lines), index + 12)):
        candidate = lines[j]
        if not candidate or META_RE.match(candidate):
            continue
        seen += 1
        if is_document(candidate):
            return True
        if seen > 4:
            break
    return False


def classify(section: str, title: str) -> str:
    hay = f"{section} {title}".lower()

    rules = (
        (("персональн", "пдн"), "pdn"),
        (("государственные и муниципальные информационные", "гис", "гостех"), "gis"),
        (("критическ", "кии"), "kii"),
        (("фстэк",), "fstec"),
        (("фсб",), "fsb"),
        (("роскомнадзор",), "rkn"),
        (("роспотребнадзор",), "rospotreb"),
        (("крипт", "электронн подпис"), "crypto"),
        (("видеонаблю", "скуд", "охран"), "itso"),
        (("искусственн интеллект", "нейросет", "машинн обуч"), "ai"),
        (("облач", "cloud", "kubernetes"), "cloud"),
        (("гост", "iso/iec", "iso "), "gost"),
    )
    for needles, kind in rules:
        if any(token in hay for token in needles):
            return kind
    return "other"


def parse_catalog(source: Path) -> dict:
    original_lines = read_text(source).splitlines()

    stop = next(
        (
            i
            for i, value in enumerate(original_lines)
            if value.strip() == "Сведения о последнем обновлении"
        ),
        len(original_lines),
    )
    lines = [line.strip() for line in original_lines[:stop]]

    headings: list[tuple[int, str]] = []
    for i in range(len(lines)):
        if is_heading(lines, i):
            headings.append((i + 1, lines[i]))

    def section_for(line_no: int) -> str:
        current = "Без раздела"
        for heading_line, heading in headings:
            if heading_line < line_no:
                current = heading
            else:
                break
        return current

    documents = []
    for i, title in enumerate(lines, start=1):
        if not is_document(title):
            continue
        section = section_for(i)
        documents.append(
            {
                "source_id": f"SRC-{i:04d}",
                "source_line": i,
                "section": section,
                "kind": classify(section, title),
                "title": title,
                "status": "SOURCE_EXACT",
                "normalized_id": None,
            }
        )

    return {
        "schema": "father.document_source_catalog.v1",
        "owner": "FATHER",
        "consumer": "CyberED",
        "source": {
            "filename": source.name,
            "preservation": "Only document titles and section context are imported; article commentary is not copied.",
        },
        "stats": {
            "documents": len(documents),
            "sections": len({item["section"] for item in documents}),
        },
        "sections": sorted({item["section"] for item in documents}),
        "documents": documents,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Импорт полного исходного перечня IT/ИБ документов в FATHER."
    )
    parser.add_argument("source", type=Path, help="Исходный TXT-файл")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Файл не найден: {args.source}")

    payload = parse_catalog(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        "FATHER source catalog: "
        f"{payload['stats']['documents']} documents / "
        f"{payload['stats']['sections']} sections"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
