"""Render selected PDF pages to PNG so the vision model can read them.

Page 2 is the main 26A 일반형 plan + elevation + section, per earlier exploration.
We'll also render page 4 (first 26A1 주거약자형 page) for context.
"""
import fitz  # pymupdf
import pathlib

PDF = "/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf"
OUT_DIR = pathlib.Path("/Users/d/Desktop/NEFS Kitchen/phase0/pages")
OUT_DIR.mkdir(exist_ok=True)

doc = fitz.open(PDF)
print(f"PDF has {len(doc)} pages")

# Pages with actual detail drawings (high word counts from test 1):
# pages 2, 4, 5, 7, 9, 10, 12, 14, 15, 17, 19, 20, 21 (1-indexed)
# The page containing 주방가구 + 26A main details is page 2
TARGETS = [2, 4, 5]

for page_num in TARGETS:
    page = doc.load_page(page_num - 1)  # 0-indexed
    # 200 DPI — enough detail for dimension labels
    mat = fitz.Matrix(200 / 72, 200 / 72)
    pix = page.get_pixmap(matrix=mat)
    out_path = OUT_DIR / f"page_{page_num:02d}.png"
    pix.save(str(out_path))
    print(f"  page {page_num}: {pix.width}x{pix.height}  →  {out_path}")

doc.close()
print("\nDone.")
