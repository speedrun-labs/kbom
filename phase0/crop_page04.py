"""Crop page 4 (26A1 accessible) into the same 5 views as page 2."""
from PIL import Image
import pathlib

IN = "/Users/d/Desktop/NEFS Kitchen/phase0/pages/page_04.png"
OUT_DIR = pathlib.Path("/Users/d/Desktop/NEFS Kitchen/phase0/crops_p04")
OUT_DIR.mkdir(exist_ok=True)

img = Image.open(IN)
W, H = img.size
mx = int(W * 0.01); my = int(H * 0.02)
row_split = int(H * 0.48)

crops = {
    "01_plan_view":       (mx,              my,          int(W * 0.50), row_split),
    "02_spec_table":      (int(W * 0.45),   my,          int(W * 0.95), row_split),
    "03_elevation_A":     (mx,              row_split,   int(W * 0.35), H - my),
    "04_interior_elev":   (int(W * 0.30),   row_split,   int(W * 0.70), H - my),
    "05_section":         (int(W * 0.65),   row_split,   int(W * 0.95), H - my),
}

for name, box in crops.items():
    cropped = img.crop(box)
    out_path = OUT_DIR / f"{name}.png"
    cropped.save(out_path)
    print(f"  {name}: {cropped.size}  →  {out_path}")
