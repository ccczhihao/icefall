#!/usr/bin/env python3
"""Analyze fixed-parameter wake-word trials; never tunes per-candidate thresholds."""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def wilson(successes, n, z=1.96):
    if not n:
        return None
    p = successes / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * ((p * (1-p) / n + z*z / (4*n*n)) ** .5) / d
    return [max(0, center-half), min(1, center+half)]


def bootstrap(values, reps, rng, statistic=lambda x: sum(x)/len(x)):
    if not values:
        return None
    draws = sorted(statistic([rng.choice(values) for _ in values]) for _ in range(reps))
    return [draws[int(.025 * (reps-1))], draws[int(.975 * (reps-1))]]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", type=Path, help="per-utterance CSV")
    ap.add_argument("--control", default="hey google")
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--red-gap", type=float, default=.15, help="pilot-only negative gap rule")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rows = []
    with args.csv.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            hit = row["hit"].strip().lower()
            if hit not in {"0", "1"}:
                raise ValueError(f"hit must be 0 or 1: {row}")
            row["hit"] = int(hit)
            rows.append(row)
    if not rows:
        raise SystemExit("No trial rows found")
    candidates = sorted({r["candidate"].strip().lower() for r in rows})
    by_candidate = defaultdict(list)
    by_speaker = defaultdict(lambda: defaultdict(list))
    by_condition = defaultdict(lambda: defaultdict(list))
    for r in rows:
        c = r["candidate"].strip().lower()
        by_candidate[c].append(r)
        by_speaker[c][r["speaker_id"]].append(r["hit"])
        by_condition[c][r.get("condition", "").strip() or "unspecified"].append(r["hit"])
    if args.control.strip().lower() not in by_candidate:
        raise SystemExit(f"Control {args.control!r} is absent from CSV")
    control = args.control.strip().lower()
    control_means = {s: sum(v)/len(v) for s, v in by_speaker[control].items()}
    out = {"method": "fixed parameters; no per-word threshold tuning", "control": control,
           "pilot_red_gap": args.red_gap, "candidates": {}}
    for c in candidates:
        rs = by_candidate[c]
        hits = sum(r["hit"] for r in rs)
        speakers = {s: sum(v)/len(v) for s, v in by_speaker[c].items()}
        entry = {"trials": len(rs), "hits": hits, "hit_rate": hits/len(rs),
                 "clip_wilson_95": wilson(hits, len(rs)), "speakers": len(speakers),
                 "speaker_mean_hit_rate": sum(speakers.values())/len(speakers),
                 "speaker_cluster_bootstrap_95": bootstrap(list(speakers.values()), args.bootstrap, rng),
                 "conditions": {},
                 "pronunciation_variants": dict(Counter(r.get("pronunciation_variant", "").strip() or "unspecified" for r in rs)),
                 "miss_causes": dict(Counter(r.get("miss_cause", "").strip() or "unspecified" for r in rs if not r["hit"]))}
        for cond, vals in by_condition[c].items():
            entry["conditions"][cond] = {"trials": len(vals), "hits": sum(vals), "hit_rate": sum(vals)/len(vals)}
        if c == control:
            entry["paired_vs_control"] = {"matched_speakers": len(speakers), "mean_difference": 0.0,
                                            "bootstrap_95": [0.0, 0.0], "decision": "reference"}
        else:
            common = sorted(set(speakers) & set(control_means))
            diffs = [speakers[s] - control_means[s] for s in common]
            ci = bootstrap(diffs, args.bootstrap, rng)
            mean_diff = sum(diffs)/len(diffs) if diffs else None
            decision = "insufficient paired speakers"
            if len(common) >= 10:
                if mean_diff <= -args.red_gap and ci[1] < 0:
                    decision = "red: pilot evidence of materially lower hit rate"
                elif ci[0] > -args.red_gap:
                    decision = "green: pilot difference within margin"
                else:
                    decision = "yellow: inconclusive or borderline"
            entry["paired_vs_control"] = {"matched_speakers": len(common), "mean_difference": mean_diff,
                                            "bootstrap_95": ci, "decision": decision}
        out["candidates"][c] = entry
    serialized = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()

