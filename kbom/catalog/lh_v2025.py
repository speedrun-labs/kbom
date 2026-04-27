"""LH developer profile (Korea Land & Housing Corporation).

Sourced from LH 표준상세도 V2025.01 (architecture pack) plus the round-trip
test on the supplied 화성태안3 A2BL sample. Citations point at the published
standards we mined in `published_standards/standards_mining_report.md`.
"""
from __future__ import annotations

from dataclasses import dataclass


# -----------------------------------------------------------------------------
# Cabinet vocabulary — codes used in the customer's 장등록 sheet.
# Maps short code → Korean name + typical role.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CabinetType:
    code: str
    name: str
    description_en: str
    is_panel: bool = False  # True for end panels / fillers / trim
    is_drawer: bool = False
    has_recessed_hob: bool = False  # True for range-base — height is 550 not 700


CABINET_TYPES: dict[str, CabinetType] = {
    # --- Wall (upper) cabinets ---
    "WP":  CabinetType("WP",  "벽장판넬",        "Wall-cab end panel", is_panel=True),
    "W":   CabinetType("W",   "일반벽장",        "Standard wall cabinet"),
    "WH":  CabinetType("WH",  "후드벽장",        "Hood wall cabinet"),
    "WE":  CabinetType("WE",  "냉장고벽장",      "Refrigerator wall cabinet"),
    "WC":  CabinetType("WC",  "코너벽장",        "Corner wall cabinet"),
    # --- Base (lower) cabinets ---
    "BI":  CabinetType("BI",  "밑장휠라",        "Base filler", is_panel=True),
    "BP":  CabinetType("BP",  "밑장판넬",        "Base end panel", is_panel=True),
    "B":   CabinetType("B",   "밑장",            "Plain base cabinet"),
    "BR":  CabinetType("BR",  "렌지밑장",        "Range base", has_recessed_hob=True),
    "BS":  CabinetType("BS",  "씽크밑장",        "Sink base"),
    "BD2": CabinetType("BD2", "2단서랍밑장",     "2-drawer base", is_drawer=True),
    "BD3": CabinetType("BD3", "3단서랍밑장",     "3-drawer base", is_drawer=True),
    # --- Channel-mount variants (NEFS-specific suffix to plain codes above) ---
    "C":   CabinetType("C",   "찬넬밑장",        "Channel-mount plain base"),
    "CR":  CabinetType("CR",  "찬넬렌지밑장",    "Channel-mount range base", has_recessed_hob=True),
    "CS":  CabinetType("CS",  "찬넬씽크밑장",    "Channel-mount sink base"),
    "CD2": CabinetType("CD2", "찬넬2단서랍밑장", "Channel-mount 2-drawer base", is_drawer=True),
    "CD3": CabinetType("CD3", "찬넬3단서랍밑장", "Channel-mount 3-drawer base", is_drawer=True),
    # --- Trim ---
    "FA":  CabinetType("FA",  "장식판",          "Fascia trim", is_panel=True),
    "PL":  CabinetType("PL",  "걸레받이",        "Baseboard", is_panel=True),
    # --- Tall ---
    "T":   CabinetType("T",   "키큰장",          "Tall cabinet"),
}


def code_to_name(code: str) -> str:
    """Resolve a cabinet code to its Korean name. Returns the code itself if unknown."""
    ct = CABINET_TYPES.get(code)
    return ct.name if ct else code


def name_to_code(name: str) -> str | None:
    """Reverse lookup: Korean name to cabinet code."""
    for ct in CABINET_TYPES.values():
        if ct.name == name:
            return ct.code
    return None


# -----------------------------------------------------------------------------
# Standard products — always present in any LH kitchen unit.
# These end up as 상품 rows in the customer's 상품등록 sheet.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class StandardProduct:
    name: str
    description_en: str
    sink_size_dependent: bool = False  # e.g. sink bowl varies 630/700 by unit


STANDARD_PRODUCTS: list[StandardProduct] = [
    StandardProduct("행거레일", "Hanger rail (cooking utensil rail)"),
    StandardProduct("2단컵걸이선반", "2-tier cup-holder shelf"),
    StandardProduct("씽크볼(630용) 수세미망 포함", "630mm undermount sink with drain mesh", sink_size_dependent=True),
    StandardProduct("후크배수구", "Hook drain"),
    StandardProduct("칼꽂이", "Knife holder"),
    StandardProduct("BMC상판", "Artificial-marble (BMC) countertop"),
]


# -----------------------------------------------------------------------------
# Standard cabinet dimensions — used as defaults / sanity checks.
# These come from observation of the round-trip test on the 26A sample.
# -----------------------------------------------------------------------------
DEFAULT_DEPTHS_MM = {
    "wall": 290,    # upper cabinets
    "base": 570,    # lower cabinets
    "tall": 290,
    "panel": 20,    # end panels and trim are 20mm thick
}

DEFAULT_HEIGHTS_MM = {
    "wall_standard": 800,
    "wall_outer_panel": 860,    # outer end panels are taller (top cap)
    "wall_inner_panel": 800,
    "base_standard": 700,
    "base_range": 550,          # 찬넬렌지밑장 — recessed hob
    "base_panel": 850,          # base end panels include plinth
    "trim_stock_length": 2400,  # 장식판 + 걸레받이 stock-board length
}
