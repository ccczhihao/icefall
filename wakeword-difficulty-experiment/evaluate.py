#!/usr/bin/env python3
"""Dev-threshold selection and held-out wake-word evaluation. Python standard library only."""
import argparse, csv, json, math, random
from collections import defaultdict
from pathlib import Path

REQUIRED = {"candidate", "utterance_id", "speaker_id", "split", "label", "score", "duration_seconds"}

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        rows = []
        for line, x in enumerate(reader, 2):
            label = x["label"].strip().lower()
            if label not in {"1", "0", "positive", "negative", "wake", "nonwake"}:
                raise ValueError(f"Line {line}: label must be positive/1 or negative/0")
            x["y"] = int(label in {"1", "positive", "wake"})
            x["score_value"] = float(x["score"])
            x["seconds"] = float(x["duration_seconds"])
            if x["seconds"] < 0:
                raise ValueError(f"Line {line}: negative duration")
            rows.append(x)
    if not rows:
        raise ValueError("CSV has no rows")
    return rows

def measure(rows, threshold):
    pos = [r for r in rows if r["y"] == 1]
    neg = [r for r in rows if r["y"] == 0]
    if not pos or not neg:
        raise ValueError("Every candidate/split requires positive and negative rows")
    tp = sum(r["score_value"] >= threshold for r in pos)
    fp = sum(r["score_value"] >= threshold for r in neg)
    hours = sum(r["seconds"] for r in neg) / 3600
    if hours <= 0:
        raise ValueError("Negative duration must be positive")
    return {"threshold": threshold, "positive_n": len(pos), "negative_n": len(neg),
            "negative_hours": hours, "tp": tp, "fn": len(pos)-tp,
            "fp": fp, "tn": len(neg)-fp, "recall": tp/len(pos),
            "frr": (len(pos)-tp)/len(pos), "clip_far": fp/len(neg),
            "false_alarms_per_hour": fp/hours}

def wilson(k, n):
    if n == 0: return [None, None]
    z = 1.959963984540054
    p = k/n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    r = z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return [max(0, c-r), min(1, c+r)]

def bootstrap_speakers(rows, threshold, iterations, seed):
    by = defaultdict(list)
    for r in rows: by[r["speaker_id"]].append(r)
    ids = list(by)
    rng = random.Random(seed)
    frrs, fahs = [], []
    for _ in range(iterations):
        sample = [r for sid in rng.choices(ids, k=len(ids)) for r in by[sid]]
        pos = [r for r in sample if r["y"] == 1]
        neg = [r for r in sample if r["y"] == 0]
        hours = sum(r["seconds"] for r in neg)/3600
        if not pos or not neg or hours <= 0: continue
        frrs.append(sum(r["score_value"] < threshold for r in pos)/len(pos))
        fahs.append(sum(r["score_value"] >= threshold for r in neg)/hours)
    def ci(v):
        if not v: return [None, None]
        v.sort()
        return [v[int(.025*(len(v)-1))], v[int(.975*(len(v)-1))]]
    return {"speaker_bootstrap_frr_95ci": ci(frrs),
            "speaker_bootstrap_fa_per_hour_95ci": ci(fahs),
            "valid_replicates": len(frrs), "bootstrap_unit": "speaker_id"}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--target-fa-per-hour", type=float, default=.1)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=Path("results"))
    a = ap.parse_args()
    if a.target_fa_per_hour < 0: ap.error("target FA/hour must be non-negative")
    rows = read_csv(a.csv_path)
    output, curve = [], []
    for candidate in sorted({r["candidate"] for r in rows}):
        subset = [r for r in rows if r["candidate"] == candidate]
        dev = [r for r in subset if r["split"].lower() == "dev"]
        test = [r for r in subset if r["split"].lower() == "test"]
        if not dev or not test: raise ValueError(f"{candidate}: both dev and test required")
        values = sorted({r["score_value"] for r in dev})
        thresholds = [math.nextafter(values[-1], math.inf)] + values
        feasible = [measure(dev, t) for t in thresholds]
        feasible = [m for m in feasible if m["false_alarms_per_hour"] <= a.target_fa_per_hour]
        chosen = max(feasible, key=lambda m:(m["recall"], -m["false_alarms_per_hour"], m["threshold"]))
        m = measure(test, chosen["threshold"])
        m.update({"candidate": candidate, "target_fa_per_hour": a.target_fa_per_hour,
                  "dev_recall_at_threshold": chosen["recall"],
                  "dev_fa_per_hour_at_threshold": chosen["false_alarms_per_hour"],
                  "frr_wilson_95ci": wilson(m["fn"], m["positive_n"]),
                  "clip_far_wilson_95ci": wilson(m["fp"], m["negative_n"])})
        m.update(bootstrap_speakers(test, chosen["threshold"], a.bootstrap, a.seed+len(output)))
        output.append(m)
        for t in values:
            p = measure(dev, t)
            curve.append({"candidate":candidate, "threshold":t, "recall":p["recall"],
                          "frr":p["frr"], "clip_far":p["clip_far"],
                          "false_alarms_per_hour":p["false_alarms_per_hour"], "split":"dev"})
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/"summary.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    with (a.out/"threshold_curve_dev.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(curve[0])); w.writeheader(); w.writerows(curve)
    print(f"Results written to {a.out}")
    print("candidate | threshold | test FRR | test FA/hour | positive N | negative hours")
    for m in output:
        print(f"{m['candidate']} | {m['threshold']:.6g} | {m['frr']:.4f} | "
              f"{m['false_alarms_per_hour']:.4f} | {m['positive_n']} | {m['negative_hours']:.2f}")

if __name__ == "__main__":
    main()


