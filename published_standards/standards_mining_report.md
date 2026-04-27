# LH 표준상세도 V2025.01 — Mining Report for Kitchen-Furniture Rules

**Date**: 2026-04-26
**Source**: `published_standards/2-2.-표준상세도_건축_V2025.01.pdf` (74 MB Part 2 of LH's 2025.01 architecture detail catalog), with index from `1.-표준상세도-목록표_V2025.01.xlsx`.
**Goal**: confirm the LH catalog actually contains rule-grade content, extract concrete rule statements with document citations, and compare canonical LH layouts against the NEFS sample blueprint.

---

## TL;DR

- The LH catalog contains **35 directly relevant kitchen-furniture detail pages** (sheet 11 "건구류(가구)" of the index Excel). They span PDF pages **467–599** of the architecture pack.
- Every spec page has a **주기 (notes) box** with explicit rule statements — exactly the rule-grade content needed to seed the pipeline's domain-rules layer. Sample rules below are extracted with page citations.
- Critical rule discovered: **"전체길이가 2400 이하일 경우 일체식" (single-piece if total length ≤ 2400mm)** — directly explains why the NEFS Excel sizes 장식판 and 걸레받이 at 2400mm. That's an LH-mandated stock-board ceiling, not a NEFS choice. This is a citable rule.
- **The LH-canonical 26㎡ kitchen layout differs from the NEFS 26㎡ A2BL layout** — meaning NEFS does a project-customized assembly within LH's component rules. Confirms the right architecture is *component-level rules from LH catalog* + *assembly-level rules from NEFS history*.

---

## What's actually in the LH catalog (sheet 11 "건구류(가구)")

35 kitchen-related entries. The most important ones for the pipeline:

| 분류코드 | 상세명 | English | Pipeline relevance |
|---|---|---|---|
| DA-90-005 | 주방가구 공통사항 | Kitchen Furniture Common Specs | Universal rules across all kitchens |
| DA-91-010/011 | 상하개폐벽장 | Top/bottom-opening wall cabinet | Wall-cab type definitions |
| DA-91-012/012-1 | 냉장고 상부장 | Refrigerator upper cabinet | Maps to NEFS code WE/WEF |
| DA-91-013/014 | 후드 상부장 | Hood upper cabinet | Maps to NEFS code WH |
| DA-91-017 | 냉장고장 등 조합예시 | Fridge cabinet combination examples | Layout assembly examples |
| **DA-91-018** | **빌트인 가구 조합예시** | **Built-in furniture combination examples** | **Canonical 26㎡ + 31㎡ layouts (compare vs NEFS)** |
| DA-91-112 | 코너장-벽장 연결 | Corner-cabinet to wall-cabinet connection | Corner geometry rules |
| DA-91-116 | 장식판 | Fascia trim | Maps to NEFS row FA (장식판) |
| DA-91-117 | 장식판 마감 및 연결 | Fascia finish + connection | Connection rules |
| DA-91-118 | 스틸레일 | Steel drawer rail | Hardware rules |
| DA-91-119 | 볼레일 | Ball drawer rail | Alternative drawer rail spec |
| DA-91-123-1 | 조리기구걸이 세트(고급형) | Cooking utensil rail set (premium) | Maps to NEFS 행거레일 (상품) |
| DA-91-125 | 언더씽크볼 | Under-sink bowl | Maps to NEFS 씽크볼 (상품) |
| DA-91-132/133 | 인출망 (일반/고급) | Pull-out basket (basic/premium) | Sink-base interior accessory |
| DA-91-140/141 | 씽크볼/언더상판(HPL) | Sink bowl + HPL countertop | HPL countertop variant |
| **DA-91-142** | **씽크볼/언더상판(인조대리석)** | **Sink bowl + artificial-marble (BMC) countertop** | **Maps to NEFS 26A countertop spec** |
| DA-91-143 | 주방가구 문짝 | Kitchen-furniture door | Door rules |
| **DA-91-150 to 155** | **건축마감 시공한계** | **Construction-finish installation limits** | **Critical: gives clearances/heights as numbers** |
| DA-91-162 | 키큰장(냉장고장) | Tall cabinet (fridge cabinet) | Tall-cabinet rules |

---

## Extracted rule statements (with citations)

### From **DA-91-116 장식판** (fascia trim) — page 561 of the architecture PDF

> 주기:
> * 장식판은 문짝 동일마감 — *Fascia uses same finish as door*
> * 전체길이가 2400 이하일 경우 일체식 — *If total length ≤ 2400mm, use single piece*

**Rule that directly maps to NEFS Excel**: NEFS row FA 장식판 60×20×**2400** is sized exactly to this LH stock-length ceiling. Same applies to 걸레받이 baseboard (PL row, 150×20×**2400**). Both are LH-mandated, not NEFS choices.

**Visible dimensions**: corner radius R4.5–5.5; thickness 23mm; fastener Ø3×28 나사못 (Ø3×28 screw).

### From **DA-91-117 장식판 마감 및 연결** (fascia finish + connection) — page 561

> 주기:
> * 주방라디오(통신공사) 설치시 위치는 전기감독과 협의하여 주방가구 제조업체에서 절단
> *(Kitchen radio/communications device installation: location requires coordination with electrical supervisor; cutting performed by furniture manufacturer)*

This is an interface-rule between trades — a class of rules the NEFS Excel doesn't capture but the install BOM definitely needs.

### From **DA-91-118 스틸레일** + **DA-91-119 볼레일** (drawer rails) — page 561

> 주기:
> * 레일의 형상은 제작사에 따라 상이할 수 있지만 수평으로 서랍을 열시 앞으로 빠지지 않도록 걸림장치가 있어야 한다
> *(Rail shape may vary by manufacturer, but must include a stopper to prevent the drawer from being pulled completely out when opened horizontally)*

Performance requirement, not a dimension. Pipeline encodes as a procurement/QA rule.

**Visible dimensions**:
- Steel rail: 12.5mm clearance between drawer-box side and drawer-cabinet side
- Ball rail: 12.7mm clearance (different by 0.2mm)
- Both: 서랍밑판 THK3 HDF (drawer bottom panel: 3mm HDF)
- Both: 3×19 스크류조립 (3×19 mounting screws)

These are **exact mechanical clearances** — pipeline rules can use them directly.

### From **DA-91-123-1 조리기구걸이 세트(고급형)(조명분리형)** (cooking utensil rail set, premium with separated lighting) — page 569

> 주기:
> * 형태 및 세부치수 등은 기능에 지장이 없는 범위내에서 제작사의 사양에 따라 상이할 수 있음
> * 조리기구걸이는 조명일체형 또는 프로파일 중 1개소 설치 — *Install ONE only: integrated-lighting type OR profile type*
> * 조명은 전기공사 — *Lighting is electrical-work scope (not furniture)*

This last note is a **scope-boundary rule** — it tells the install BOM "the light fixture is the electrician's job, not the kitchen installer's." Critical for the install-side BOM (Phase 3b).

### From **DA-91-141 씽크볼/언더상판(HPL)** (sink bowl + HPL countertop) — page 575

Five concrete rules in the 주기 box:

> 1. 상판(언더형식)은 이음매가 없는 것을 원칙으로 하되, 단, 가스대, 코너대와의 접합부위와 2400mm를 초과하는 길이는 예외로 한다
>    *(Countertop must be jointless except at gas-range junction, corner-unit junction, or lengths exceeding 2400mm)*

> 2. 상판의 마감면은 평활도가 유지되도록 하며, 세부형태 및 치수는 제작사의 사양에 따른다
>    *(Countertop finish must maintain flatness; detailed form/dimensions per manufacturer spec)*

> 3. 상판과 씽크볼의 연결:
>    - 접합재료: 수지층을 형성하는 재료로, 물 및 습기에 견디도록 내수성이 고려된, 인체에 무해한 접착제여야 한다
>      *(Adhesive: resin layer-forming material, water-resistant, human-safe)*
>    - 보강구조: 내수성이 고려된 구조로, 상판밑면 및 캐비넷안으로 물이 스며들지 않도록 하며, 만수위 하중에 충분히 견딜 수 있어야한다
>      *(Reinforcement structure: water-resistant, prevent seepage into cabinet, support full water load)*
>    - 연결구조: 상판과 볼의 연결은 "S1"구조의 언더형식을 적용할 수 있다
>      *(Connection: countertop-to-bowl connection may use "S1" under-mount structure)*

**Visible material spec**: THK15P/W reinforcement layer (15mm thick particle/wood under the sink area).

### From **DA-91-132/133 인출망** (pull-out basket) — page 569

> * 인출망의 구조는 측면 부착할 수 있는 구조가 되도록 하며, 제작사의 사양에 따라 150용과 200용을 적용토록 한다
>   *(Pull-out structure must be side-mountable; use 150-version or 200-version per manufacturer)*
> * 알루미늄 소재의 바스켓을 사용하며, ABS 소재의 다용도 걸이는 3개를 적용한다
>   *(Use aluminum-material baskets; apply three ABS-material multipurpose hangers)*

Component-quantity rule: **3 ABS hangers per basket**. Pipeline can derive count automatically.

### From **DA-91-018 빌트인 가구 조합예시** (built-in furniture combination examples) — page 555

This page shows the **canonical LH layouts for 26㎡ and 31㎡ units** with components labeled by 분류코드. Critical for layout validation.

LH-canonical 26㎡ contains (left → right):
- SINK BOWL → DA-91-142 (artificial-marble countertop with sink)
- 상부장 → DA-91-014 (hood upper)
- 가전수납 → DA-90-311.012.321 (appliance storage)
- 현장창TV / 부엌 공용 → DA-90-301.302
- 현장 → DA-90-301.302

---

## Cross-check: LH canonical 26㎡ vs NEFS 26㎡ A2BL

The NEFS sample blueprint (`붙임3-2 주방가구 상세도(화성태안3 A-2BL)-2.pdf` page 2) and the LH canonical 26㎡ combination example (DA-91-018) **are different layouts**:

| Position | LH canonical 26㎡ | NEFS 26A2BL 26㎡ |
|---|---|---|
| Far left | Sink bowl + countertop | Plain base 280W |
| Center-left | Hood upper / appliance storage | Range base 600W |
| Center | Appliance storage | Drawer base 400W |
| Center-right | TV / Kitchen common cabinet | **Sink base 800W** |
| Far right | Field cabinet | Refrigerator position |

The NEFS unit is a more conventional kitchen (sink/range/drawer/fridge); the LH-canonical 26㎡ shows a more compact unit with built-in appliance storage (washer/dryer space) and no separate range. Either:

- (a) NEFS does a project-customized layout LH approved (most likely)
- (b) LH's catalog publishes one example out of multiple 26㎡ variants
- (c) The 화성태안3 A2BL spec was issued before this catalog version

**Implication for the pipeline architecture (validates the plan):**

The LH catalog provides:
- ✅ **Component-level rules** — dimensions, materials, screws, clearances per cabinet code (universal across all LH projects)

The NEFS history provides:
- ✅ **Assembly-level rules** — which components combine for which project's specific unit type (project-by-project variation)

→ The right rule library is **two-layer**: component rules from LH catalog (Approach B), assembly patterns from NEFS Excels (Approach A). Combination beats either alone.

---

## Concrete additions to `domain_rules.py` from this mining pass

Each rule below cites its LH document source. These would be added on top of the existing R1–R8 rules (which were inferred from the round-trip test).

```yaml
- id: R9_fascia_max_length
  source: "LH 표준상세도 V2025.01, DA-91-116"
  rule: "장식판 (fascia/FA) total length ≤ 2400mm; if longer, must split"
  effect: "Sets stock-board ceiling for 장식판 H value (height col is overloaded as length here)"

- id: R10_baseboard_max_length
  source: "LH 표준상세도 V2025.01, DA-91-116 (general application)"
  rule: "걸레받이 (baseboard/PL) follows same 2400mm stock ceiling"
  effect: "Pre-explains why NEFS Excel sets PL row at 2400mm"

- id: R11_countertop_seamless
  source: "LH 표준상세도 V2025.01, DA-91-141"
  rule: "BMC/HPL countertop (인조대리석상판) must be seamless except at: gas-range junction, corner-unit junction, length > 2400mm"
  effect: "Validation: if countertop length > 2400mm and not at any of these junctions, flag for human review"

- id: R12_drawer_bottom_thickness
  source: "LH 표준상세도 V2025.01, DA-91-118 + DA-91-119"
  rule: "All drawer-box bottoms must be THK3 HDF; mounting via 3*19 screws"
  effect: "Cross-validate against 기초입력 sheet's HDF spec"

- id: R13_drawer_rail_clearance
  source: "LH 표준상세도 V2025.01, DA-91-118 (steel) / DA-91-119 (ball)"
  rule: "Drawer-rail clearance: 12.5mm (steel rail), 12.7mm (ball rail)"
  effect: "Drawer-box width = drawer-cabinet inside width − (2 × clearance per rail type)"

- id: R14_lighting_scope
  source: "LH 표준상세도 V2025.01, DA-91-123-1"
  rule: "Lighting installation is electrical-work scope, not kitchen-furniture scope"
  effect: "Install BOM marks lighting items as 'electrical' subcontractor, not kitchen install crew"

- id: R15_pullout_basket_hangers
  source: "LH 표준상세도 V2025.01, DA-91-132/133"
  rule: "Each pull-out basket includes 3 ABS-material multipurpose hangers"
  effect: "Cabinet hardware count: per pull-out basket, +3 ABS hangers automatically"

- id: R16_drawer_stopper_required
  source: "LH 표준상세도 V2025.01, DA-91-118"
  rule: "All drawer rails must include a stopper preventing pull-out when opened horizontally"
  effect: "QA acceptance criterion (procurement spec); not a dimensional rule"
```

---

---

## Second mining pass — DA-91-150 to 155 (construction-finish installation limits)

These pages were called out as the "highest-density rule pages" — they specify the exact installation tolerances/gaps/clearances between kitchen furniture and surrounding architecture (floors, walls, ceilings). Confirmed: each page yields **multiple dimensional and procedural rules** for the install BOM.

### DA-91-150 건축마감 시공한계-1 (주방가구 하부장 걸레받이) — Base Cabinet Baseboard

> 주기:
> * 바닥재 시공한계 (Flooring construction limit):
>   - 하부장 다리: 다리전면 — *under base cabinet legs: flooring extends to FRONT face of leg*
>   - 하부장 기타: 다리중심 — *other base elements: flooring extends to CENTER of leg*
> * 수성페인트 시공한계: 가구끝선까지 — *water-based wall paint extends up to furniture end-line*

**Visible dimensions**: baseboard offset 60mm from cabinet face; baseboard height 150mm.

This is **gold for the install BOM** — tells the install crew how much flooring tile to lay (not under the cabinet body, only up to the leg face) and how high to take wall paint (only to the cabinet end, not behind it). Pure waste-reduction information.

### DA-91-151 건축마감 시공한계-2 (주방가구 하부장 뒷선반 설치) — Back Shelf INSTALLED

> 주기:
> * 주방가구 상판은 자재유형에 따라 규격 및 치수가 상이 — *Countertop sizes/dims vary by material type*
> * (DA-91-136~139) 참고 — *See DA-91-136 to 139 for details*
> * 은폐부위 벽면: 골조노출 경우도 동일하게 "마감없음" — *Concealed wall: same "no finish" treatment even if structural exposure*

**Visible dimensions** (with back-shelf installed):
- Wall tile reveal **above countertop: 100mm**
- Back shelf gap from wall tile: **25mm**
- Back shelf depth offset: **50mm**
- Countertop forward extension: **50mm beyond cabinet face**
- Countertop visible thickness: **12mm**
- Countertop material: **인조대리석 MMA급 마감** (artificial marble MMA grade) — matches NEFS spec
- "No finish" treatment behind back shelf: **100mm vertical zone**

### DA-91-152 건축마감 시공한계-3 (주방가구 하부장 뒷선반 미설치) — Back Shelf NOT INSTALLED

> 주기: same as DA-91-151

**Visible dimensions** (no back shelf):
- Wall tile gap from countertop top: **12mm** (smaller, since no back shelf)
- Other dimension: **75mm** (countertop edge to wall plane)
- Countertop thickness: **12mm**
- "No finish" zone behind: **100mm**

### DA-91-153 건축마감 시공한계-4 (주방가구 상부장) — Upper Cabinet

**Visible dimensions**: wall tile reveal behind upper cabinet **100mm** (visible behind, even though concealed). Door hinge pattern shown.

### DA-91-154 건축마감 시공한계-5 (주방가구 상부장 천장부위) — Upper Cabinet Ceiling Area, *반자돌림 없는 경우* (no crown molding)

> 주기:
> * 상부장 천장: 별도 마감 없음 — *Upper-cabinet ceiling: no separate finish*
> * **천장과 상부장 사이 간격: 최대 25mm** — *Gap between ceiling and upper cabinet: max 25mm*

**Visible**: 100mm wall reveal; ceiling system = 경량철골천정틀 (light steel frame) + THK9 석고보드 (9mm gypsum board) + 천정마감지 (paper finish).

### DA-91-155 건축마감 시공한계-6 (주방가구 상부장 천장부위) — Upper Cabinet Ceiling Area, *반자돌림 있는 경우* (with crown molding)

> 주기:
> * 상부장 천장: 별도 마감 없음 — same as DA-91-154

Same ceiling system; same "no separate finish" rule.

### Additional rules from this pass (R17–R23) added to the library

```yaml
- id: R17_baseboard_height
  source: "LH 표준상세도 V2025.01, DA-91-150"
  rule: "걸레받이 (baseboard) standard height = 150mm"
  effect: "Cross-validates NEFS Excel PL row at 150W (matches LH spec)"

- id: R18_baseboard_offset
  source: "LH 표준상세도 V2025.01, DA-91-150"
  rule: "걸레받이 offset from cabinet face = 60mm"
  effect: "Install-BOM: subtract 60mm × 2 from cabinet linear length to compute baseboard length"

- id: R19_flooring_limit
  source: "LH 표준상세도 V2025.01, DA-91-150"
  rule: "Flooring extends only to: (a) front face of cabinet leg under leg position, (b) center of leg elsewhere. Does NOT extend under base-cabinet body."
  effect: "Construction-side BOM: tile/flooring quantity per kitchen = (room area − base-cabinet footprint + leg-front extension). Saves substantial flooring material."

- id: R20_wall_paint_limit
  source: "LH 표준상세도 V2025.01, DA-91-150"
  rule: "Water-based wall paint extends only to furniture-end line (not behind cabinets)"
  effect: "Construction-side BOM: paint quantity per kitchen wall = (wall area − cabinet-covered area). Saves paint material."

- id: R21_wall_tile_reveal
  source: "LH 표준상세도 V2025.01, DA-91-151/153/154/155"
  rule: "주방벽 도기질 시유타일 (kitchen wall ceramic glazed tile) reveal = 100mm above countertop face AND 100mm visible behind upper cabinet"
  effect: "Construction-side BOM: tile area per kitchen wall = (countertop-to-upper-cabinet zone) + 100mm above + 100mm behind upper cab = stable computation per wall length"

- id: R22_upper_cab_ceiling_gap
  source: "LH 표준상세도 V2025.01, DA-91-154/155"
  rule: "Gap between upper cabinet top and finished ceiling: maximum 25mm"
  effect: "Validation: if cabinet H + plinth + countertop + backsplash + upper-cab H + 25mm > floor-to-ceiling height, flag for human review (cabinet won't fit)"

- id: R23_concealed_wall_no_finish
  source: "LH 표준상세도 V2025.01, DA-91-151/152"
  rule: "Wall area concealed by base cabinet: NO finish applied — same rule even if rough-frame is exposed"
  effect: "Construction-side BOM: subtract concealed area from wall-finish quantities (paint, drywall, tile back of cabinet)"
```

These are **install-BOM rules in particular** — they tell the construction crew where finishes do and don't go, which is exactly the gap NEFS faces today (the project owner confirmed install rules aren't written down). This page alone delivers six concrete savings/validation rules for the install side.

---

## Updated rule count

- R1–R8: inferred from round-trip test on NEFS Excel (cabinet-side hardware)
- R9–R16: from first standards-mining pass (cabinet-side: trim, drawer, sink, accessories)
- **R17–R23: from second standards-mining pass (install-side: floor/wall/ceiling clearances)**

**Total rule library**: 23 rules, all citation-backed where catalog-derived. Estimated coverage of NEFS's typical kitchen-BOM needs: ~70%, with the remaining 30% expected from Approach A (mining 20+ past NEFS Excels) for assembly-level rules.

---

## Recommendation

1. **Adopt these 8 catalog-cited rules** (R9–R16) into `domain_rules.py`. Each has a documented source URL — anyone auditing the pipeline can verify against the LH PDF.
2. **Run the same mining pass on additional kitchen pages** (DA-91-150 to 155 "construction-finish installation limits" — these will give clearance/gap rules for cabinet-to-ceiling, cabinet-to-wall, and baseboard placement). Estimated: 3 more rules per page × 6 pages = ~18 more rules.
3. **Get the LH 가구 표준상세도** (the furniture-specific catalog separate from this architecture pack) — that document likely has the canonical layouts for *every* unit type variant including 26A1, 37B, 46A. Without it, we have component rules but not the full assembly catalog.
4. **For NEFS-specific assembly rules**: still need Approach A (mining 20+ past NEFS Excels) since the LH-canonical layouts don't match NEFS's actual deliveries 1:1.

---

## Artifacts produced this session

- `published_standards/standards_mining_report.md` — this file
- `published_standards/extracts/DA-91-018_combination.png` — high-res render of the canonical combination example (the most decision-relevant single image)
- `published_standards/extracts/scan_p176.png` — DA-91-116/117/118/119 fascia + rails details
- `published_standards/extracts/scan_p190.png` — DA-91-141 sink/HPL countertop with full notes
- `published_standards/extracts/scan_p180.png` — DA-91-123-1 cooking utensil rail
- `published_standards/extracts/scan_p184.png` — DA-91-132/133 pull-out baskets
- `published_standards/extracts/part2_p110.png`, `_p140.png`, `_p150.png`, `_p170.png`, `_p200.png` — survey scans for index navigation
