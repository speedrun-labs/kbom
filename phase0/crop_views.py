"""Crop the key views from page 2 at higher fidelity for vision analysis.

Page 2 layout (1-indexed views from the drawing sheet):
  view 1 (top-left):     26A plan view
  view 2 (top-right):    finish-spec table
  view 3 (bottom-left):  26A elevation A
  view 4 (bottom-mid):   26A interior elevation
  view 5 (bottom-right): section
"""
from PIL import Image
import pathlib

IN = "/Users/d/Desktop/NEFS Kitchen/phase0/pages/page_02.png"
OUT_DIR = pathlib.Path("/Users/d/Desktop/NEFS Kitchen/phase0/crops")
OUT_DIR.mkdir(exist_ok=True)

img = Image.open(IN)
W, H = img.size
print(f"Page dimensions: {W}x{H}")

# Approximate regions based on a standard LH sheet layout (3 columns, 2 rows)
# Top row: plan (left), spec table (right)
# Bottom row: elevation A (left), interior elev (middle), section (right)
# Borders give ~3% margins
mx = int(W * 0.01)
my = int(H * 0.02)

# Row splits: top ~55%, bottom ~45%
row_split = int(H * 0.48)

crops = {
    "01_plan_view":       (mx,                   my,                   int(W * 0.50),     row_split),
    "02_spec_table":      (int(W * 0.45),        my,                   int(W * 0.95),     row_split),
    "03_elevation_A":     (mx,                   row_split,            int(W * 0.35),     H - my),
    "04_interior_elev":   (int(W * 0.30),        row_split,            int(W * 0.70),     H - my),
    "05_section":         (int(W * 0.65),        row_split,            int(W * 0.95),     H - my),
}

for name, box in crops.items():
    cropped = img.crop(box)
    out_path = OUT_DIR / f"{name}.png"
    cropped.save(out_path)
    print(f"  {name}: {cropped.size}  →  {out_path}")
