"""기준 PDF에서 페이지별 텍스트 + 도면 타이틀 추출.

Usage:
    python scripts/preprocess/extract_pdf.py --input data/standards-pdfs/WSOLVENT.pdf --output data/cache/pdf_sections.json
"""

import json
import re
import sys
from pathlib import Path

import click
import fitz  # pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def extract_drawing_title(text: str) -> str:
    """페이지 텍스트에서 도면 타이틀 추출."""
    lines = text.split("\n")
    # 도면 타이틀은 보통 DRAWING TITLE 키워드 근처
    # 또는 특정 패턴: SCHEMATIC DIAGRAM, LAYOUT, PROTECTIVE EARTH BAR 등
    title_keywords = [
        "SCHEMATIC DIAGRAM", "LAYOUT LIST", "LAYOUT",
        "PROTECTIVE EARTH BAR", "TERMINAL BLOCK",
        "FLOW METER", "TOUCH SCREEN", "GENERAL NOTES",
        "DOOR SENSOR", "ELECTRIC ZONE", "CONTROL PANEL",
        "INVERTER PANEL", "EQUIPMENT",
    ]
    for line in lines:
        stripped = line.strip()
        for kw in title_keywords:
            if kw in stripped.upper():
                return stripped
    return ""


def extract_page(page, page_num: int) -> dict:
    """단일 페이지에서 텍스트와 메타데이터 추출."""
    text = page.get_text()
    title = extract_drawing_title(text)

    # PE, PB 참조 추출
    pe_refs = sorted(set(re.findall(r"PE\d+", text)))
    pb_refs = sorted(set(re.findall(r"PB\d+", text)))

    # 파츠 명칭 추출
    part_patterns = [
        r"(?:SO|NF|PS|TR|PC|TS|FC|PD|BLB|LIT|IVM|SV|MF|SS)\d+[A-Za-z0-9_-]*"
    ]
    parts = set()
    for pat in part_patterns:
        parts.update(re.findall(pat, text))
    parts = sorted(parts)

    # DWG NO 추출
    dwg_no = ""
    m = re.search(r"(\d{2}-\d{2})\s*\n?\s*DWG NO", text)
    if m:
        dwg_no = m.group(1)

    return {
        "page": page_num,
        "title": title,
        "dwg_no": dwg_no,
        "pe_refs": pe_refs,
        "pb_refs": pb_refs,
        "parts": parts,
        "text_length": len(text),
        "text": text[:2000],  # 저장 용량 제한
    }


@click.command()
@click.option("--input", "input_path", required=True, help="PDF file path")
@click.option("--output", "output_path", required=True, help="Output JSON path")
@click.option("--full-text", is_flag=True, help="Include full page text (large output)")
def main(input_path: str, output_path: str, full_text: bool):
    """기준 PDF에서 페이지별 구조 추출."""
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(input_file))
    click.echo(f"PDF: {input_file.name} ({doc.page_count} pages)")

    pages = []
    title_index = {}  # title -> [page_nums]
    pe_index = {}  # PE## -> [page_nums]

    for i in range(doc.page_count):
        page_data = extract_page(doc[i], i + 1)
        if not full_text:
            page_data.pop("text", None)
        pages.append(page_data)

        if page_data["title"]:
            title_index.setdefault(page_data["title"], []).append(i + 1)
        for pe in page_data["pe_refs"]:
            pe_index.setdefault(pe, []).append(i + 1)

    result = {
        "source_file": str(input_file),
        "total_pages": doc.page_count,
        "title_index": title_index,
        "pe_index": pe_index,
        "pages": pages,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    click.echo(f"Extracted {len(pages)} pages")
    click.echo(f"Unique titles: {len(title_index)}")
    click.echo(f"PE references: {len(pe_index)}")
    click.echo(f"Output: {output_file}")


if __name__ == "__main__":
    main()
