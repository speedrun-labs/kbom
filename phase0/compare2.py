"""Comparison with flexible prediction-file path. Used to score the augmented
prediction (after domain rules) against the same ground truth."""
import json, sys

GT = "/Users/d/Desktop/NEFS Kitchen/phase0/ground_truth_26A.json"
PRED = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/d/Desktop/NEFS Kitchen/phase0/test3_prediction_augmented.json"
TOL = 30

with open(GT, encoding="utf-8") as f:
    gt = json.load(f)["rows"]
with open(PRED, encoding="utf-8") as f:
    pred = json.load(f)["predicted_rows"]

def close(a, b):
    if a is None and b is None: return True
    if a is None or b is None: return False
    return abs(a - b) <= TOL

def strict_match(a, b):
    return (a["category"] == b["category"] and a["name"] == b["name"]
            and close(a.get("w"), b.get("w")) and close(a.get("d"), b.get("d"))
            and close(a.get("h"), b.get("h")))

def type_match(a, b):
    return a["category"] == b["category"] and a["name"] == b["name"]

used = set()
s, t, m = 0, 0, 0
rows_out = []
for g in gt:
    best_s = best_t = None
    for j, p in enumerate(pred):
        if j in used: continue
        if strict_match(g, p):
            best_s = j; break
        if type_match(g, p) and best_t is None:
            best_t = j
    if best_s is not None:
        used.add(best_s); s += 1; rows_out.append(("STRICT", g, pred[best_s]))
    elif best_t is not None:
        used.add(best_t); t += 1; rows_out.append(("TYPE  ", g, pred[best_t]))
    else:
        m += 1; rows_out.append(("MISS  ", g, None))

fp = [pred[j] for j in range(len(pred)) if j not in used]
n = len(gt)

print(f"Prediction file: {PRED}")
print("=" * 90)
for status, g, p in rows_out:
    def fmt(r):
        if r is None: return " " * 55
        w = f"{int(r['w'])}" if r.get('w') else "---"
        d = f"{int(r['d'])}" if r.get('d') else "---"
        h = f"{int(r['h'])}" if r.get('h') else "---"
        return f"[{r['category']:4}] {r['name']:<18} W={w:>5} D={d:>4} H={h:>5}"
    p_str = fmt(p) if p else "(not matched)"
    print(f"  {status}  {fmt(g)}   ←→   {p_str}")

if fp:
    print("\nFalse positives:")
    for p in fp:
        def fmt2(r):
            w = f"{int(r['w'])}" if r.get('w') else "---"
            d = f"{int(r['d'])}" if r.get('d') else "---"
            h = f"{int(r['h'])}" if r.get('h') else "---"
            return f"[{r['category']:4}] {r['name']:<18} W={w:>5} D={d:>4} H={h:>5}"
        print(f"  {fmt2(p)}")

print(f"\n  Strict:   {s}/{n}  ({100*s/n:.0f}%)")
print(f"  Type:     {t}/{n}  ({100*t/n:.0f}%)")
print(f"  Covered:  {s+t}/{n}  ({100*(s+t)/n:.0f}%)")
print(f"  Missed:   {m}/{n}  ({100*m/n:.0f}%)")
print(f"  False +:  {len(fp)}")
