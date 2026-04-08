"""DWG → DXF → 구조화 JSON 추출 파이프라인.

Usage:
    python scripts/extract/extract_dwg.py --input inbox/sample.dwg --output data/cache/drawing.json
"""

import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import click
import ezdxf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.common.config import DWG2DXF_BIN, POLE_CIRCLE_RADIUS, POLE_GROUP_X_TOLERANCE, PE_BAR_Y_RANGE


def convert_dwg_to_dxf(dwg_path: Path, dxf_path: Path) -> Path:
    """DWG를 DXF로 변환. LibreDWG 또는 ODA File Converter 자동 감지."""
    if DWG2DXF_BIN is None:
        raise FileNotFoundError(
            "DWG→DXF 변환기를 찾을 수 없습니다.\n"
            "다음 중 하나를 설치하세요:\n"
            "  1. LibreDWG: https://github.com/LibreDWG/libredwg\n"
            "  2. ODA File Converter: https://www.opendesign.com/guestfiles\n"
            "  3. 환경변수 DWG2DXF_PATH에 변환기 경로 설정\n"
            "  4. AutoCAD에서 DXF로 내보내기 후 DXF 직접 입력"
        )

    converter = Path(DWG2DXF_BIN)
    converter_name = converter.stem.lower()

    if "odafileconverter" in converter_name:
        # ODA File Converter: 다른 커맨드라인 인터페이스
        # ODAFileConverter "input_dir" "output_dir" version type recursive audit
        input_dir = str(dwg_path.parent)
        output_dir = str(dxf_path.parent)
        result = subprocess.run(
            [str(converter), input_dir, output_dir,
             "ACAD2018", "DXF", "0", "1"],
            capture_output=True, text=True, timeout=120,
        )
        # ODA는 입력 파일명 기준으로 .dxf 생성
        oda_output = dxf_path.parent / dwg_path.with_suffix(".dxf").name
        if oda_output.exists() and oda_output != dxf_path:
            oda_output.rename(dxf_path)
    else:
        # LibreDWG dwg2dxf
        result = subprocess.run(
            [str(converter), "-o", str(dxf_path), str(dwg_path)],
            capture_output=True, text=True, timeout=120,
        )

    if not dxf_path.exists():
        raise RuntimeError(
            f"DWG→DXF conversion failed:\n{result.stderr}"
        )
    return dxf_path


def _clean_text(s: str) -> str:
    """서로게이트 문자 등 비정상 유니코드 제거."""
    return s.encode("utf-8", errors="replace").decode("utf-8")


def extract_texts(msp) -> list:
    """모든 TEXT/MTEXT 엔티티 추출."""
    texts = []
    for entity in msp:
        text = ""
        pos = (0.0, 0.0)

        if entity.dxftype() == "TEXT":
            text = _clean_text(entity.dxf.text or "")
            try:
                p = entity.dxf.insert
                pos = (round(p.x, 2), round(p.y, 2))
            except Exception:
                pass
        elif entity.dxftype() == "MTEXT":
            text = _clean_text(entity.text or "")
            try:
                p = entity.dxf.insert
                pos = (round(p.x, 2), round(p.y, 2))
            except Exception:
                pass

        if text.strip():
            texts.append({
                "text": text.strip(),
                "x": pos[0],
                "y": pos[1],
                "layer": entity.dxf.layer,
            })
    return texts


def extract_circles(msp) -> list:
    """모든 CIRCLE 엔티티 추출."""
    circles = []
    for entity in msp:
        if entity.dxftype() == "CIRCLE":
            c = entity.dxf.center
            circles.append({
                "cx": round(c.x, 2),
                "cy": round(c.y, 2),
                "radius": round(entity.dxf.radius, 2),
                "layer": entity.dxf.layer,
            })
    return circles


def extract_blocks(msp) -> list:
    """모든 INSERT (블록 참조) 추출."""
    blocks = []
    for entity in msp:
        if entity.dxftype() == "INSERT":
            try:
                p = entity.dxf.insert
                blocks.append({
                    "name": entity.dxf.name,
                    "x": round(p.x, 2),
                    "y": round(p.y, 2),
                    "layer": entity.dxf.layer,
                })
            except Exception:
                pass
    return blocks


def _detect_pe_bar_regions(texts):
    """PE BAR 상세 도면 영역을 자동 감지.

    "PROTECTIVE EARTH BAR" 타이틀 + DWG NO "05-XX" 위치를 기준으로
    각 PE BAR 도면의 X/Y 범위를 찾는다.
    """
    # DWG NO 05-00 ~ 05-04 위치로 PE BAR 도면 영역 찾기
    # DWG NO는 도면 하단 타이틀블록에 있으므로 가장 신뢰할 수 있는 기준
    dwg_05 = [
        t for t in texts
        if re.match(r"^05-0[0-4]$", t["text"])
    ]
    if not dwg_05:
        return []

    # Y 값 기준으로 클러스터링 (도면 영역 vs 인덱스 영역 구분)
    # 같은 Y 범위에 여러 DWG NO가 있는 클러스터가 실제 도면 영역
    ys = sorted(set(round(d["y"]) for d in dwg_05))
    # 가장 낮은 Y 클러스터가 실제 도면 (도면은 아래쪽에 배치)
    y_detail = min(ys)

    # 실제 도면 영역의 DWG NO만
    dwg_05_detail = [d for d in dwg_05 if abs(d["y"] - y_detail) < 50]

    regions = []
    for d in sorted(dwg_05_detail, key=lambda t: t["x"]):
        regions.append({
            "dwg_no": d["text"],
            "x_center": d["x"],
            "y_center": d["y"],
        })

    # PE BAR 도면 Y 중심 = DWG NO Y + 약 200 (도면은 위쪽으로 펼쳐짐)
    y_center = y_detail + 150

    return regions, y_center


def find_pe_bars(texts, circles) -> list:
    """PE BAR 정보를 텍스트 + 원 위치에서 추론.

    PE BAR 상세 도면 영역만 필터링하여 중복 제거.
    """
    # PE BAR 도면 영역 감지
    detection = _detect_pe_bar_regions(texts)
    if not detection:
        # fallback: 영역 감지 실패 시 전체 스캔
        pe_bar_y_min, pe_bar_y_max = PE_BAR_Y_RANGE
    else:
        regions, y_center = detection
        pe_bar_y_min = y_center - 250
        pe_bar_y_max = y_center + 100

    # PE BAR 도면 영역 내 PB 텍스트만 수집
    pb_texts = [
        t for t in texts
        if re.match(r"^PB\d+$", t["text"])
        and pe_bar_y_min < t["y"] < pe_bar_y_max
    ]

    # 같은 이름의 PB가 여전히 여러 개면 (BAR-1, BAR-2 쌍) 그대로 유지
    # 하지만 완전히 다른 영역(LAYOUT, TB)의 PB는 이미 제거됨

    # 작은 원 (pole indicator) - PE BAR 영역 내만
    r_min, r_max = POLE_CIRCLE_RADIUS
    pole_circles = [
        c for c in circles
        if r_min < c["radius"] < r_max
        and pe_bar_y_min < c["cy"] < pe_bar_y_max
    ]

    # PE 텍스트 - PE BAR 영역 내만
    pe_texts = [
        t for t in texts
        if re.match(r"^PE\d+", t["text"])
        and pe_bar_y_min < t["y"] < pe_bar_y_max
    ]

    # BAR 타입 텍스트 매핑 - PE BAR 영역 내만
    bar_type_texts = []
    for t in texts:
        if not (pe_bar_y_min - 50 < t["y"] < pe_bar_y_max + 50):
            continue
        txt = t["text"].upper()
        if "MAIN PROTECTIVE EARTH" in txt or "MAIN PE BAR" in txt:
            bar_type_texts.append({**t, "_type": "MAIN"})
        elif "AC PROTECTIVE EARTH" in txt or "1 PHASE PE BAR" in txt:
            bar_type_texts.append({**t, "_type": "1PHASE"})
        elif "DC PROTECTIVE EARTH" in txt:
            bar_type_texts.append({**t, "_type": "DC"})
        elif "AD & SHIELD" in txt or "AD PE BAR" in txt or "SHIELD PE BAR" in txt:
            bar_type_texts.append({**t, "_type": "AD_SHIELD"})
        elif "3 PHASE PROTECTIVE EARTH" in txt or "3 PHASE PE BAR" in txt:
            bar_type_texts.append({**t, "_type": "3PHASE"})

    # PB별 정보 추출
    pe_bars = []
    tol = POLE_GROUP_X_TOLERANCE

    for pb in pb_texts:
        pb_name = pb["text"]
        pb_x, pb_y = pb["x"], pb["y"]

        # 근처 pole 원 카운트 (X 좌표 유사 + Y 범위 내)
        nearby_poles = [
            c for c in pole_circles
            if abs(c["cx"] - pb_x) < tol
        ]
        pole_count = len(nearby_poles)

        # 근처 PE 케이블 (같은 도면 내 - X +-200, Y +-200)
        pe_cables = []
        seen_pe = set()
        for pe in pe_texts:
            if abs(pe["x"] - pb_x) < 200 and abs(pe["y"] - pb_y) < 200:
                if pe["text"] not in seen_pe:
                    pe_cables.append({"pe_id": pe["text"], "x": pe["x"], "y": pe["y"]})
                    seen_pe.add(pe["text"])

        # BAR 타입 추론 (가장 가까운 타입 텍스트)
        bar_type = "UNKNOWN"
        min_dist = float("inf")
        for bt in bar_type_texts:
            dist = abs(bt["x"] - pb_x) + abs(bt["y"] - pb_y)
            if dist < min_dist:
                min_dist = dist
                bar_type = bt["_type"]

        # BAR-1/BAR-2 라벨 찾기 (PB 근처)
        bar_sub = ""
        bar_labels = [
            t for t in texts
            if re.match(r".+ PE BAR-[12]$", t["text"])
            and pe_bar_y_min < t["y"] < pe_bar_y_max
            and abs(t["x"] - pb_x) < 50
        ]
        if bar_labels:
            closest = min(bar_labels, key=lambda t: abs(t["x"] - pb_x) + abs(t["y"] - pb_y))
            bar_sub = "BAR-1" if "BAR-1" in closest["text"] else "BAR-2"

        pe_bars.append({
            "name": pb_name,
            "bar_type": bar_type,
            "bar_sub": bar_sub,
            "x": pb_x,
            "y": pb_y,
            "pole_count": pole_count,
            "pe_cables": pe_cables,
        })

    # BAR 쌍 매칭: 같은 타입 + 같은 Y + 가까운 X → 쌍
    # BAR-1의 pole=0이면 BAR-2의 pole을 공유
    pairs = {}
    for pb in pe_bars:
        key = (pb["bar_type"], round(pb["y"]))
        pairs.setdefault(key, []).append(pb)

    for key, group in pairs.items():
        if len(group) == 2:
            g = sorted(group, key=lambda p: p["x"])
            g[0]["pair"] = g[1]["name"]
            g[1]["pair"] = g[0]["name"]
            # 쌍의 pole 합산
            total_poles = g[0]["pole_count"] + g[1]["pole_count"]
            g[0]["pair_pole_count"] = total_poles
            g[1]["pair_pole_count"] = total_poles

    return pe_bars


def extract_drawing(dxf_path: Path) -> dict:
    """DXF 파일에서 전체 도면 데이터 추출."""
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    texts = extract_texts(msp)
    circles = extract_circles(msp)
    blocks = extract_blocks(msp)
    pe_bars = find_pe_bars(texts, circles)

    return {
        "source_file": str(dxf_path),
        "summary": {
            "total_texts": len(texts),
            "total_circles": len(circles),
            "total_blocks": len(blocks),
            "total_pe_bars": len(pe_bars),
        },
        "pe_bars": pe_bars,
        "texts": texts,
        "circles": circles,
        "blocks": blocks,
    }


@click.command()
@click.option("--input", "input_path", required=True, help="DWG or DXF file path")
@click.option("--output", "output_path", required=True, help="Output JSON path")
@click.option("--keep-dxf", is_flag=True, help="Keep intermediate DXF file")
def main(input_path: str, output_path: str, keep_dxf: bool):
    """DWG/DXF에서 구조화된 도면 데이터를 추출."""
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if input_file.suffix.lower() == ".dwg":
        click.echo(f"Converting DWG → DXF: {input_file.name}")
        if keep_dxf:
            dxf_path = input_file.with_suffix(".dxf")
        else:
            dxf_path = Path(tempfile.mktemp(suffix=".dxf"))
        convert_dwg_to_dxf(input_file, dxf_path)
    elif input_file.suffix.lower() == ".dxf":
        dxf_path = input_file
    else:
        raise click.BadParameter(f"Unsupported file type: {input_file.suffix}")

    click.echo(f"Extracting entities from: {dxf_path.name}")
    data = extract_drawing(dxf_path)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    click.echo(f"Extracted: {data['summary']}")
    click.echo(f"Output: {output_file}")

    if input_file.suffix.lower() == ".dwg" and not keep_dxf:
        dxf_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
