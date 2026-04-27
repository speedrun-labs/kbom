"""Test 2 — Extract ground-truth BOM from Excel sheet 원가산출표 cols B-G.

This is the canonical cabinet list we're trying to match with Test 3.
Emits JSON so Test 3 can diff against it programmatically.
"""
import json
import xlrd

XLS = "/Users/d/Downloads/1. LH 화성태안3 A2BL-26A.xls"
OUT = "/Users/d/Desktop/NEFS Kitchen/phase0/ground_truth_26A.json"

wb = xlrd.open_workbook(XLS, formatting_info=False)
sheet = wb.sheet_by_name("원가산출표")

print(f"원가산출표: {sheet.nrows} rows")
print("=" * 80)

rows = []
for row_idx in range(sheet.nrows):
    full_row = sheet.row_values(row_idx)
    # cols B-G = indices 1-6
    category = str(full_row[1]).strip()
    name = str(full_row[2]).strip()
    w = full_row[3]
    d = full_row[4]
    h = full_row[5]
    type_ = str(full_row[6]).strip()

    # Only keep rows with real content
    if category in ("목대", "상품") and name:
        rows.append({
            "row_index": row_idx,
            "category": category,
            "name": name,
            "w": w if isinstance(w, (int, float)) and w else None,
            "d": d if isinstance(d, (int, float)) and d else None,
            "h": h if isinstance(h, (int, float)) and h else None,
            "type": type_ or None,
        })

for r in rows:
    w = f"{int(r['w'])}" if r["w"] else "---"
    d = f"{int(r['d'])}" if r["d"] else "---"
    h = f"{int(r['h'])}" if r["h"] else "---"
    print(f"  [{r['category']:4}] {r['name']:20} W={w:>6}  D={d:>6}  H={h:>6}  TYPE={r['type']}")

print(f"\nTotal rows: {len(rows)}")
print(f"  목대 (custom frame): {sum(1 for r in rows if r['category'] == '목대')}")
print(f"  상품 (products):     {sum(1 for r in rows if r['category'] == '상품')}")

# Filter to just 26A (ignore any other TYPE variants that may appear)
rows_26A = [r for r in rows if r["type"] == "26A"]
print(f"\n26A only: {len(rows_26A)} rows")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"source_sheet": "원가산출표", "unit_type": "26A",
               "rows": rows_26A, "all_rows": rows}, f, ensure_ascii=False, indent=2)
print(f"\nSaved → {OUT}")
