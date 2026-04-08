"""도면 검토 시스템 공통 데이터 스키마."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TextEntity:
    """도면 내 텍스트 엔티티."""
    text: str
    x: float
    y: float
    layer: str


@dataclass
class CircleEntity:
    """도면 내 원 엔티티."""
    cx: float
    cy: float
    radius: float
    layer: str


@dataclass
class BlockRef:
    """블록 참조 (INSERT)."""
    name: str
    x: float
    y: float
    layer: str


@dataclass
class PEBarInfo:
    """PE BAR 정보."""
    name: str  # PB01, PB02, ...
    bar_type: str  # MAIN, 1PHASE, DC, AD_SHIELD, 3PHASE
    x: float
    y: float
    pole_count: int
    pe_cables: list = field(default_factory=list)  # [{"pe_id": "PE01", "target": "NF01", "ref": "04-02 3/D"}]


@dataclass
class DrawingData:
    """DXF에서 추출한 도면 전체 데이터."""
    source_file: str
    texts: list = field(default_factory=list)  # List[TextEntity]
    circles: list = field(default_factory=list)  # List[CircleEntity]
    blocks: list = field(default_factory=list)  # List[BlockRef]
    pe_bars: list = field(default_factory=list)  # List[PEBarInfo]

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)


@dataclass
class RuleCheck:
    """규칙 검증 조건."""
    check_type: str  # cross_check_existence, pole_count_match, qty_match
    source: str  # PE BAR drawing
    target: str  # SCHEMATIC, LAYOUT LIST, etc.
    field: str  # pe_cable, pole_count, qty
    operator: str = "eq"  # eq, gte, lte


@dataclass
class Violation:
    """위반 사항."""
    rule_id: str
    severity: str  # critical, major, minor
    message: str
    source_entity: str  # PE01, PB03, etc.
    expected: str
    actual: str
    location: str = ""  # 도면 내 위치 참조


@dataclass
class ReviewReport:
    """검토 리포트."""
    drawing_file: str
    total_rules_checked: int = 0
    violations: list = field(default_factory=list)  # List[Violation]
    passed_checks: list = field(default_factory=list)
    skipped_checks: list = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def major_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "major")

    @property
    def minor_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "minor")
