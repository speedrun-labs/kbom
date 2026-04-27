"""Test 1 — Verify the sample blueprint PDF is vector-text-extractable.

Pass = dimension labels (2120, 800, 600, 400, 280, 570, 700), finish-spec
values (630, BMC, THK18, etc.), and view titles (평면도, 입면도, 단면도)
come out as selectable strings with coordinates.
"""
import pdfplumber
from collections import Counter

PDF = "/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf"

DIMENSION_TARGETS = ["2,120", "2120", "800", "600", "400", "380", "280", "570", "700", "650", "290", "310", "825"]
SPEC_TARGETS = ["630", "BMC", "THK18", "THK15", "HPL", "LPL", "PB", "HDF", "PVC", "인조대리석", "도기질", "언더싱크", "수세미"]
VIEW_TARGETS = ["평면도", "입면도", "단면도", "마감사양", "주방가구"]
TITLE_TARGETS = ["화성태안", "A2BL", "26㎡", "26m²", "A형", "A1형", "LH"]

def scan(pdf_path):
    found = {k: [] for k in ["dims", "specs", "views", "titles"]}
    page_counts = []
    all_strings = []
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words() or []
            page_counts.append((page_num, len(words)))
            for w in words:
                txt = w["text"]
                all_strings.append((page_num, txt, round(w["x0"], 1), round(w["top"], 1)))
                for t in DIMENSION_TARGETS:
                    if t in txt:
                        found["dims"].append((page_num, txt, t))
                for t in SPEC_TARGETS:
                    if t in txt:
                        found["specs"].append((page_num, txt, t))
                for t in VIEW_TARGETS:
                    if t in txt:
                        found["views"].append((page_num, txt, t))
                for t in TITLE_TARGETS:
                    if t in txt:
                        found["titles"].append((page_num, txt, t))
    return page_counts, all_strings, found

page_counts, all_strings, found = scan(PDF)

print(f"\n--- Word counts per page ---")
for p, c in page_counts:
    print(f"  page {p}: {c} words")

print(f"\nTotal extracted strings: {len(all_strings)}")

print(f"\n--- Target hits ---")
for category, hits in found.items():
    targets_hit = Counter(h[2] for h in hits)
    print(f"  {category}: {len(hits)} hits across {len(targets_hit)} distinct targets")
    for t, n in targets_hit.most_common():
        print(f"    {t!r}: {n}x")

print(f"\n--- Sample strings from page 2 (main 26A plan view) ---")
page2 = [s for s in all_strings if s[0] == 2]
for s in page2[:30]:
    print(f"  {s}")

print(f"\n--- Unique strings containing digits (dimension candidates) from page 2 ---")
import re
digit_strings = set()
for p, txt, x, y in all_strings:
    if p == 2 and re.search(r"\d", txt) and len(txt) < 15:
        digit_strings.add(txt)
print(f"  {len(digit_strings)} unique: {sorted(digit_strings)[:60]}")

print(f"\n--- Korean strings on page 2 ---")
kor_strings = set()
for p, txt, x, y in all_strings:
    if p == 2 and re.search(r"[\uac00-\ud7a3]", txt):
        kor_strings.add(txt)
print(f"  {len(kor_strings)} unique: {sorted(kor_strings)}")

# Pass/fail summary
has_dims = len(found["dims"]) > 0
has_specs = len(found["specs"]) > 0
has_views = len(found["views"]) > 0
has_titles = len(found["titles"]) > 0

print("\n=== TEST 1 VERDICT ===")
print(f"  Dimensions extractable: {'YES' if has_dims else 'NO'}  ({len(found['dims'])} hits)")
print(f"  Finish specs extractable: {'YES' if has_specs else 'NO'}  ({len(found['specs'])} hits)")
print(f"  View titles extractable: {'YES' if has_views else 'NO'}  ({len(found['views'])} hits)")
print(f"  Title-block extractable: {'YES' if has_titles else 'NO'}  ({len(found['titles'])} hits)")

verdict = "PASS" if all([has_dims, has_specs, has_views, has_titles]) else "PARTIAL" if has_dims else "FAIL"
print(f"\n  Overall: {verdict}")
