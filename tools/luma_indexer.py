"""Build a lightweight searchable index for LUMA project documents.

This script is intentionally dependency-light. It indexes metadata for all
supported file types and extracts text from plain text, CSV, DOCX, and PPTX
files using only Python's standard library. PDF text extraction can be added
later with a package such as pypdf.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Iterable, Optional
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".csv", ".txt", ".md"}
TEXT_EXTENSIONS = {".csv", ".txt", ".md"}
DEFAULT_OUTPUT_DIR = Path("local") / "luma-index"

PROJECT_OVERRIDES = {
    "jobos_solar": "Salinas and Jobos",
    "jobos_bess": "Salinas and Jobos",
}


@dataclass
class IndexRecord:
    file_path: str
    project: str
    facility: str
    service_type: str
    doc_type: str
    source_level: str
    modified_date: str
    extension: str
    title: str
    searchable_text: str
    snippet: str
    tags: list[str]


def normalize_input_path(raw_path: str) -> Path:
    """Accept both Windows paths and Git Bash paths like /x/LUMA."""
    match = re.match(r"^/([a-zA-Z])(?:/(.*))?$", raw_path)
    if match:
        drive = match.group(1).upper()
        rest = (match.group(2) or "").replace("/", "\\")
        return Path(f"{drive}:\\{rest}")
    return Path(raw_path)


def path_text(path: Path) -> str:
    return str(path).replace("/", "\\")


def lower_parts(path: Path) -> list[str]:
    return [part.lower() for part in path.parts]


def friendly_title(path: Path) -> str:
    title = path.stem
    title = re.sub(r"^\d+[_ -]*", "", title)
    title = title.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title or path.name


def infer_source_level(path: Path) -> str:
    parts = lower_parts(path)
    if "contracts" in parts:
        return "Legal"
    if any(part.endswith("invoicing") or part == "xtera_invocing" for part in parts):
        return "Operational"
    if path.name.lower() == "dim_facilities.csv":
        return "Reference"
    return "Reference"


def infer_service_type(path: Path) -> str:
    parts = lower_parts(path)
    if "ppoa" in parts:
        return "PPOA"
    if "bess" in parts:
        return "BESS"
    joined = " ".join(parts)
    if "solar" in joined:
        return "PPOA"
    return ""


def infer_project(path: Path) -> str:
    parts = list(path.parts)
    lowered = [part.lower() for part in parts]

    for key, project in PROJECT_OVERRIDES.items():
        if key in lowered:
            return project

    for part in parts:
        normalized = part.lower()
        if normalized.endswith(" invoicing"):
            return part[: -len(" Invoicing")]

    if "contracts" in lowered:
        idx = lowered.index("contracts")
        if idx + 1 < len(parts):
            raw_project = parts[idx + 1]
            return raw_project.replace("_", " ").title()

    return "Unknown"


def infer_facility(path: Path) -> str:
    text = path_text(path).lower()
    facilities = []
    if "salinas" in text:
        facilities.append("Salinas")
    if "jobos" in text:
        facilities.append("Jobos")
    if "ciro" in text:
        facilities.append("Ciro One")
    return ", ".join(facilities)


def infer_doc_type(path: Path) -> str:
    text = path_text(path).lower()
    name = path.name.lower()
    extension = path.suffix.lower()

    if "sample input" in text or "sample_input" in text:
        return "sample_input"
    if "required_data" in name or "required data" in name:
        return "required_data"
    if "performance_guarantee" in name or "performance guarantee" in name:
        return "performance_guarantee"
    if "monthly_payment_calculation" in name or "monthly payment calculation" in name:
        return "calculation_doc"
    if "compensation_calculation" in name or "compensation calculation" in name:
        return "calculation_doc"
    if "contracts" in lower_parts(path):
        if "amend" in name:
            return "amendment"
        return "contract"
    if extension == ".pptx":
        return "presentation"
    if extension == ".csv":
        if path.name.lower() == "dim_facilities.csv":
            return "reference_data"
        return "sample_input"
    if extension == ".pdf":
        return "report"
    return "reference"


def extract_plain_text(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def extract_docx_text(path: Path, max_chars: int) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (KeyError, OSError, zipfile.BadZipFile):
        return ""
    return extract_xml_text(xml_bytes, max_chars)


def extract_pptx_text(path: Path, max_chars: int) -> str:
    chunks = []
    try:
        with zipfile.ZipFile(path) as archive:
            slide_names = sorted(
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            for slide_name in slide_names:
                chunks.append(extract_xml_text(archive.read(slide_name), max_chars))
                if len(" ".join(chunks)) >= max_chars:
                    break
    except (OSError, zipfile.BadZipFile):
        return ""
    return " ".join(chunks)[:max_chars]


def extract_xml_text(xml_bytes: bytes, max_chars: int) -> str:
    try:
        root = ElementTree.fromstring(xml_bytes)
        text = " ".join(node.text or "" for node in root.iter())
    except ElementTree.ParseError:
        text = re.sub(r"<[^>]+>", " ", xml_bytes.decode("utf-8", errors="ignore"))
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def extract_searchable_text(path: Path, max_chars: int) -> str:
    extension = path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        return extract_plain_text(path, max_chars)
    if extension == ".docx":
        return extract_docx_text(path, max_chars)
    if extension == ".pptx":
        return extract_pptx_text(path, max_chars)
    return ""


def make_snippet(text: str, length: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[: length - 3].rstrip() + "..."


def infer_tags(record: IndexRecord) -> list[str]:
    raw_tags = [
        record.project,
        record.facility,
        record.service_type,
        record.doc_type,
        record.source_level,
    ]
    tags: list[str] = []
    for value in raw_tags:
        for part in value.split(","):
            tag = part.strip().lower().replace(" ", "-")
            if tag and tag not in tags:
                tags.append(tag)
    return tags


def build_record(path: Path, max_chars: int) -> IndexRecord:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    searchable_text = extract_searchable_text(path, max_chars)

    record = IndexRecord(
        file_path=path_text(path.resolve()),
        project=infer_project(path),
        facility=infer_facility(path),
        service_type=infer_service_type(path),
        doc_type=infer_doc_type(path),
        source_level=infer_source_level(path),
        modified_date=modified,
        extension=path.suffix.lower(),
        title=friendly_title(path),
        searchable_text=searchable_text,
        snippet=make_snippet(searchable_text),
        tags=[],
    )
    record.tags = infer_tags(record)
    return record


def iter_supported_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield root
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("~$"):
                continue
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield path


def write_jsonl(records: list[IndexRecord], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as file:
        for record in records:
            file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def write_csv(records: list[IndexRecord], output_path: Path) -> None:
    fieldnames = list(asdict(records[0]).keys()) if records else list(IndexRecord.__dataclass_fields__)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["tags"] = ";".join(record.tags)
            writer.writerow(row)


def write_summary(records: list[IndexRecord], output_path: Path) -> None:
    by_project: dict[str, dict[str, object]] = {}
    grouped: dict[str, list[IndexRecord]] = defaultdict(list)
    for record in records:
        grouped[record.project].append(record)

    for project, project_records in sorted(grouped.items()):
        by_project[project] = {
            "file_count": len(project_records),
            "doc_types": dict(Counter(record.doc_type for record in project_records)),
            "service_types": dict(Counter(record.service_type or "Unknown" for record in project_records)),
            "source_levels": dict(Counter(record.source_level for record in project_records)),
        }

    output = {
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "file_count": len(records),
        "projects": by_project,
    }
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index LUMA project documents.")
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        default=[],
        help="Root file or directory to scan. Can be passed multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=20000,
        help="Maximum extracted text stored per file.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    raw_roots = args.roots or [r"X:\LUMA"]
    roots = [normalize_input_path(raw_root) for raw_root in raw_roots]
    missing_roots = [root for root in roots if not root.exists()]

    if missing_roots:
        print("Missing root paths:", file=sys.stderr)
        for root in missing_roots:
            print(f"  {root}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = [
        build_record(path, args.max_text_chars)
        for path in sorted(set(iter_supported_files(roots)), key=lambda item: path_text(item).lower())
    ]

    write_jsonl(records, output_dir / "index.jsonl")
    write_csv(records, output_dir / "index.csv")
    write_summary(records, output_dir / "projects_summary.json")

    print(f"Indexed {len(records)} files")
    print(f"Wrote {output_dir / 'index.jsonl'}")
    print(f"Wrote {output_dir / 'index.csv'}")
    print(f"Wrote {output_dir / 'projects_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
