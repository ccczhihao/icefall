#!/usr/bin/env python3
"""Compare KWS decisions on byte-identical WAVs before and after fine-tuning.

Each root must contain wake/<candidate>/*.wav and no_wake/<candidate>/*.wav.
Files are paired by candidate and relative file path within candidate folder.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_phase(root):
    if not root.is_dir():
        raise SystemExit(f"Missing results root: {root}")
    found = {}
    for folder, hit in (("wake", 1), ("no_wake", 0)):
        base = root / folder
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() != ".wav":
                continue
            rel = path.relative_to(base)
            if len(rel.parts) < 2:
                raise SystemExit(f"WAV needs a candidate subfolder: {path}")
            candidate = rel.parts[0].replace("_", " ").casefold()
            key = (candidate, Path(*rel.parts[1:]).as_posix().casefold())
            if key in found:
                raise SystemExit(f"Duplicate candidate/file identity: {found[key]['path']} and {path}")
            found[key] = {"hit": hit, "path": path}
    if not found:
        raise SystemExit(f"No candidate WAV files under {root}")
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before", type=Path, help="original-model results root")
    ap.add_argument("after", type=Path, help="fine-tuned-model results root")
    ap.add_argument("--out", type=Path, default=Path("kws_transitions.json"))
    args = ap.parse_args()
    before, after = read_phase(args.before), read_phase(args.after)
    all_keys = set(before) | set(after)
    report = {
        "meaning": "same-WAV Icefall KWS trigger transitions; 0=not triggered, 1=triggered",
        "candidates": {},
    }
    by_candidate = defaultdict(lambda: {"before_only": 0, "after_only": 0,
                                        "content_mismatch": 0, "00": 0, "01": 0, "10": 0, "11": 0})
    for key in sorted(all_keys):
        candidate = key[0]
        row = by_candidate[candidate]
        if key not in before:
            row["after_only"] += 1
        elif key not in after:
            row["before_only"] += 1
        elif digest(before[key]["path"]) != digest(after[key]["path"]):
            row["content_mismatch"] += 1
        else:
            transition = f"{before[key]['hit']}{after[key]['hit']}"
            row[transition] += 1
    for candidate, counts in sorted(by_candidate.items()):
        n = sum(counts[k] for k in ("00", "01", "10", "11"))
        old_misses = counts["00"] + counts["01"]
        report["candidates"][candidate] = {
            **counts,
            "matched_identical_wavs": n,
            "before_hit_rate_on_matched": (counts["10"] + counts["11"]) / n if n else None,
            "after_hit_rate_on_matched": (counts["01"] + counts["11"]) / n if n else None,
            "net_gain_pp": 100 * (counts["01"] - counts["10"]) / n if n else None,
            "actual_rescue_fraction_of_old_misses": counts["01"] / old_misses if old_misses else None,
        }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()

