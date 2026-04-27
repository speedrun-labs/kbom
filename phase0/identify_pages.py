"""Identify the unit-type variant on each PDF page by parsing title-block text."""
import pdfplumber
import re

PDF = "/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf"

# Unit-type patterns to look for
PATTERNS = [
    (r"26㎡\s*A1형", "26A1 주거약자형 (accessible)"),
    (r"26㎡\s*A형",  "26A 일반형"),
    (r"26m²\s*A1형", "26A1 주거약자형 (accessible)"),
    (r"26m²\s*A형",  "26A 일반형"),
    (r"단면도", "section view"),
    (r"평면도", "plan view"),
    (r"입면도", "elevation"),
    (r"마감사양", "finish spec"),
]

with pdfplumber.open(PDF) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")
    for page_num, page in enumerate(pdf.pages, start=1):
        words = page.extract_words() or []
        text = " ".join(w["text"] for w in words)
        n_words = len(words)

        # Find which unit-type this page references
        variants = set()
        views = set()
        for pat, label in PATTERNS:
            if re.search(pat, text):
                if "주거" in label or "일반" in label:
                    variants.add(label)
                else:
                    views.add(label)

        # Also find explicit unit labels like "26㎡ A형" in a cleaner way
        # Korean text may be split into individual chars; join adjacent chars by x proximity
        variant_tags = []
        for m in re.finditer(r"26[㎡m²]\s*A1?형", text):
            variant_tags.append(m.group(0))

        variant_str = " | ".join(sorted(set(variant_tags))) if variant_tags else " | ".join(variants) if variants else "(none detected)"
        views_str = ", ".join(sorted(views)) if views else ""

        tag = "DETAIL" if n_words > 100 else "TITLE" if n_words < 20 else "MIXED"
        print(f"  page {page_num:2d} [{tag:6}] words={n_words:3d}  variant: {variant_str}  views: {views_str}")
