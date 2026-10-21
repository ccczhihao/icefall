#!/usr/bin/env python3
"""Select a threshold from icefall dev metric summaries; evaluate held-out test counts."""
import argparse, csv, json, math
from pathlib import Path

REQ = {"candidate", "split", "threshold", "tp", "fp", "fn", "tn", "negative_hours"}

def wilson(k, n):
    if n <= 0: return [None, None]
    z = 1.959963984540054; p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    r = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / d
    return [max(0, c-r), min(1, c+r)]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--target-fa-per-hour", type=float, default=0.1)
    ap.add_argument("--out", type=Path, default=Path("results/icefall-sweep.json"))
    a = ap.parse_args()
    with a.csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQ - set(reader.fieldnames or [])
        if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
        rows = list(reader)
    result = []
    for name in sorted({r["candidate"] for r in rows}):
        subset = [r for r in rows if r["candidate"] == name]
        dev = [r for r in subset if r["split"].strip().lower() == "dev"]
        test = [r for r in subset if r["split"].strip().lower() == "test"]
        feasible = []
        for r in dev:
            x = {k: float(r[k]) for k in ("threshold", "tp", "fp", "fn", "tn", "negative_hours")}
            pos = x["tp"] + x["fn"]
            if pos and x["negative_hours"] > 0 and x["fp"]/x["negative_hours"] <= a.target_fa_per_hour:
                feasible.append((x["tp"]/pos, -x["fp"]/x["negative_hours"], x["threshold"], x))
        if not feasible: raise ValueError(f"{name}: no dev threshold meets target FA/hour")
        chosen = max(feasible, key=lambda x: x[:3])[3]
        matching = [r for r in test if math.isclose(float(r["threshold"]), chosen["threshold"], rel_tol=0, abs_tol=1e-9)]
        if len(matching) != 1: raise ValueError(f"{name}: need one test row at frozen threshold {chosen['threshold']}")
        x = {k: float(matching[0][k]) for k in ("threshold", "tp", "fp", "fn", "tn", "negative_hours")}
        pos, neg = x["tp"] + x["fn"], x["fp"] + x["tn"]
        result.append({"candidate": name, "dev_selected_threshold": chosen["threshold"],
            "target_fa_per_hour": a.target_fa_per_hour, "dev_recall": chosen["tp"]/(chosen["tp"]+chosen["fn"]),
            "test_tp": int(x["tp"]), "test_fp": int(x["fp"]), "test_fn": int(x["fn"]), "test_tn": int(x["tn"]),
            "test_recall": x["tp"]/pos if pos else None, "test_frr": x["fn"]/pos if pos else None,
            "test_frr_wilson_95ci": wilson(x["fn"], pos),
            "test_clip_far": x["fp"]/neg if neg else None, "test_clip_far_wilson_95ci": wilson(x["fp"], neg),
            "test_false_alarms_per_hour": x["fp"]/x["negative_hours"], "test_negative_hours": x["negative_hours"]})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {a.out}")
    for r in result:
        print(f"{r['candidate']}: threshold={r['dev_selected_threshold']:g}, test FRR={r['test_frr']:.4f}, FA/hour={r['test_false_alarms_per_hour']:.4f}")

if __name__ == "__main__": main()

