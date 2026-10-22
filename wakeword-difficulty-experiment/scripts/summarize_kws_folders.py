#!/usr/bin/env python3
"""Summarize Icefall KWS hit/miss WAVs without a hand-edited per-file CSV.

Expected layout (candidate folder names become candidate labels):
  results/wake/hey_google/*.wav
  results/no_wake/hey_google/*.wav
  results/wake/hey_eva/*.wav
  results/no_wake/hey_eva/*.wav

Only the user's existing KWS decision is used as the label. WAV checks are
descriptive acoustic measurements; they do not infer pronunciation or cause.
"""
import argparse
import json
import math
import statistics
import wave
from collections import defaultdict
from pathlib import Path


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z*z/n
    center = (p + z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [max(0.0, center-half), min(1.0, center+half)]


def wav_info(path):
    with wave.open(str(path), "rb") as w:
        channels, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(frames)
    if width == 1:
        samples = [b-128 for b in raw]
    elif width in (2, 4):
        samples = [int.from_bytes(raw[i:i+width], "little", signed=True) for i in range(0, len(raw), width)]
    elif width == 3:
        samples = []
        for i in range(0, len(raw), 3):
            v = int.from_bytes(raw[i:i+3], "little")
            samples.append(v-(1 << 24) if v & (1 << 23) else v)
    else:
        raise ValueError(f"unsupported PCM sample width {width}")
    if not samples:
        raise ValueError("empty audio")
    peak = max(abs(x) for x in samples)
    scale = 127 if width == 1 else (1 << (width*8-1))-1
    rms = math.sqrt(sum(x*x for x in samples)/len(samples))
    zcr = sum((a < 0) != (b < 0) for a, b in zip(samples, samples[1:])) / max(1, len(samples)-1)
    return {"duration_s": frames/rate if rate else 0, "sample_rate_hz": rate,
            "channels": channels, "rms_dbfs": 20*math.log10(rms/scale) if rms else None,
            "peak_dbfs": 20*math.log10(peak/scale) if peak else None,
            "zero_crossing_rate": zcr}


def mean_or_none(values):
    values = [x for x in values if x is not None]
    return statistics.mean(values) if values else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, help="folder containing wake/ and no_wake/")
    ap.add_argument("--control", default="hey_google", help="control candidate folder; default: hey_google")
    ap.add_argument("--out", type=Path, default=Path("kws_folder_summary.json"))
    args = ap.parse_args()
    groups = defaultdict(list)
    errors = []
    for label_dir, hit in (("wake", 1), ("no_wake", 0)):
        base = args.root / label_dir
        if not base.is_dir():
            raise SystemExit(f"Missing folder: {base}")
        for path in sorted(base.rglob("*.wav")):
            # The first directory below wake/no_wake identifies the candidate.
            rel = path.relative_to(base)
            if len(rel.parts) < 2:
                errors.append({"file": str(path), "error": "put WAVs in a candidate subfolder"})
                continue
            candidate = rel.parts[0].replace("_", " ").casefold()
            try:
                groups[candidate].append({"hit": hit, **wav_info(path)})
            except (wave.Error, OSError, ValueError) as e:
                errors.append({"file": str(path), "error": str(e)})
    if not groups:
        raise SystemExit("No readable WAVs found. See expected folder layout in --help.")
    summary = {"metric": "Icefall KWS trigger rate from supplied wake/no_wake folders",
               "model_context": "GigaSpeech ASR-trained model, no KWS fine-tuning (as reported by user)",
               "acoustic_feature_note": "descriptive only; no feature proves a cause",
               "candidates": {}, "errors": errors}
    control = args.control.casefold().replace("_", " ")
    control_rate = None
    if control in groups:
        control_rate = sum(r["hit"] for r in groups[control])/len(groups[control])
    for candidate, rows in sorted(groups.items()):
        n = len(rows)
        hits = sum(r["hit"] for r in rows)
        by_outcome = {}
        for hit, name in ((1, "wake"), (0, "no_wake")):
            part = [r for r in rows if r["hit"] == hit]
            by_outcome[name] = {"count": len(part), "mean_duration_s": mean_or_none([r["duration_s"] for r in part]),
                                "mean_rms_dbfs": mean_or_none([r["rms_dbfs"] for r in part]),
                                "mean_peak_dbfs": mean_or_none([r["peak_dbfs"] for r in part]),
                                "mean_zero_crossing_rate": mean_or_none([r["zero_crossing_rate"] for r in part])}
        rate = hits/n
        summary["candidates"][candidate] = {"trials": n, "hits": hits, "misses": n-hits,
            "kws_hit_rate": rate, "wilson_95": wilson(hits, n),
            "delta_vs_control_pp": (100*(rate-control_rate) if control_rate is not None else None),
            "acoustics_by_kws_outcome": by_outcome}
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()

