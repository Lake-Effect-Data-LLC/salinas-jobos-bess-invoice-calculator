from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


DOCS_DIR = Path("docs")
TEXT_DIR = DOCS_DIR / "text"


def main():
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    extracted = []
    failed = []

    for path in sorted(DOCS_DIR.rglob("*")):
        if not path.is_file() or TEXT_DIR in path.parents:
            continue

        if path.suffix.lower() == ".pdf":
            try:
                text = extract_pdf_text(path)
            except Exception as exc:
                failed.append((path, str(exc)))
                continue
        elif path.suffix.lower() == ".docx":
            try:
                text = extract_docx_text(path)
            except Exception as exc:
                failed.append((path, str(exc)))
                continue
        else:
            continue

        output_path = text_output_path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        extracted.append((path, output_path, len(text)))

    write_manifest(extracted, failed)
    print(f"Extracted {len(extracted)} document(s).")
    if failed:
        print(f"Failed to extract {len(failed)} document(s); see docs/text/manifest.md.")


def extract_pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is not installed") from exc

    reader = PdfReader(str(path))
    page_text = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_text.append(f"\n\n--- Page {index} ---\n{text}")

    return "".join(page_text).strip()


def extract_docx_text(path):
    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")

    root = ET.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        text_parts = [
            text_node.text or ""
            for text_node in paragraph.findall(".//w:t", namespace)
        ]
        text = "".join(text_parts).strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def text_output_path(path):
    relative_path = path.relative_to(DOCS_DIR)
    return TEXT_DIR / relative_path.with_suffix(".txt")


def write_manifest(extracted, failed):
    lines = ["# Extracted Document Text", ""]

    if extracted:
        lines.extend(["## Extracted", ""])
        for source, output, character_count in extracted:
            lines.append(
                f"- `{source}` -> `{output}` ({character_count:,} characters)"
            )
        lines.append("")

    if failed:
        lines.extend(["## Failed", ""])
        for source, error in failed:
            lines.append(f"- `{source}`: {error}")
        lines.append("")

    (TEXT_DIR / "manifest.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
