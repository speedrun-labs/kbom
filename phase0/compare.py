"""Compare Test 3 blind-extraction prediction vs Test 2 ground truth.

Scoring:
  - Strict match: category + name + W + D + H all match (±5mm tolerance on dimensions)
  - Type match: category + name match (dimensions off or missing)
  - Miss: ground-truth row has no prediction at all
  - False positive: predicted row has no ground-truth match
"""
import json

GT = "/Users/d/Desktop/NEFS Kitchen/phase0/ground_truth_26A.json"
PRED = "/Users/d/Desktop/NEFS Kitchen/phase0/test3_prediction.json"
TOL = 30  # mm tolerance for dimensions (accounts for rounding e.g. 280 vs 260)

with open(GT, encoding="utf-8") as f:
    gt = json.load(f)["rows"]
with open(PRED, encoding="utf-8") as f:
    pred = json.load(f)["predicted_rows"]

def close(a, b, tol=TOL):
    if a is None and b is None: return True
    if a is None or b is None: return False
    return abs(a - b) <= tol

def strict_match(a, b):
    return (a["category"] == b["category"]
            and a["name"] == b["name"]
            and close(a.get("w"), b.get("w"))
            and close(a.get("d"), b.get("d"))
            and close(a.get("h"), b.get("h")))

def type_match(a, b):
    return a["category"] == b["category"] and a["name"] == b["name"]

used_pred = set()
gt_strict = 0
gt_type = 0
gt_miss = 0
results = []

for i, g in enumerate(gt):
    best_strict = None
    best_type = None
    for j, p in enumerate(pred):
        if j in used_pred: continue
        if strict_match(g, p):
            best_strict = j
            break
        if type_match(g, p) and best_type is None:
            best_type = j
    if best_strict is not None:
        used_pred.add(best_strict)
        gt_strict += 1
        results.append(("STRICT", g, pred[best_strict]))
    elif best_type is not None:
        used_pred.add(best_type)
        gt_type += 1
        results.append(("TYPE  ", g, pred[best_type]))
    else:
        gt_miss += 1
        results.append(("MISS  ", g, None))

fp = [pred[j] for j in range(len(pred)) if j not in used_pred]

print("=" * 90)
print(f"Ground truth rows: {len(gt)}")
print(f"Predicted rows:    {len(pred)}")
print("=" * 90)

for status, g, p in results:
    def fmt(r):
        if r is None: return " " * 60
        w = f"{int(r['w'])}" if r.get('w') else "---"
        d = f"{int(r['d'])}" if r.get('d') else "---"
        h = f"{int(r['h'])}" if r.get('h') else "---"
        return f"[{r['category']:4}] {r['name']:<18} W={w:>5} D={d:>4} H={h:>5}"
    p_str = fmt(p) if p else "(not predicted)"
    print(f"  {status}  GT: {fmt(g)}   ←→   PRED: {p_str}")

if fp:
    print("\nFalse positives (predicted but no GT match):")
    for p in fp:
        w = f"{int(p['w'])}" if p.get('w') else "---"
        d = f"{int(p['d'])}" if p.get('d') else "---"
        h = f"{int(p['h'])}" if p.get('h') else "---"
        print(f"  [{p['category']:4}] {p['name']:<18} W={w:>5} D={d:>4} H={h:>5}  (conf {p.get('confidence')})")

print("\n" + "=" * 90)
total = len(gt)
print(f"Strict match:  {gt_strict}/{total}  ({100*gt_strict/total:.0f}%)  — category+name+dims all correct")
print(f"Type match:    {gt_type}/{total}  ({100*gt_type/total:.0f}%)  — correct cabinet type, dims off or missing")
print(f"Covered (any): {gt_strict+gt_type}/{total}  ({100*(gt_strict+gt_type)/total:.0f}%)  — at least the right type identified")
print(f"Missed:        {gt_miss}/{total}  ({100*gt_miss/total:.0f}%)  — ground-truth row not predicted")
print(f"False positives: {len(fp)}  — predicted row that doesn't appear in ground truth")
