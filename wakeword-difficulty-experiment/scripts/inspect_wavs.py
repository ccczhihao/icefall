#!/usr/bin/env python3
"""Create a WAV metadata/level manifest (stdlib only; does not assess wake quality)."""
import argparse
import csv
import math
import wave
from pathlib import Path


def inspect(path):
    with wave.open(str(path), "rb") as w:
        channels, width = w.getnchannels(), w.getsampwidth()
        rate, frames = w.getframerate(), w.getnframes()
        if width not in (1, 2, 3, 4):
            raise ValueError(f"unsupported PCM width: {width}")
        raw = w.readframes(frames)
    # Decode integer PCM samples for basic peak/RMS/clipping checks.
    if width == 1:
        vals = [b - 128 for b in raw]
    elif width == 2:
        vals = [int.from_bytes(raw[i:i+2], "little", signed=True) for i in range(0, len(raw), 2)]
    elif width == 3:
        vals = []
        for i in range(0, len(raw), 3):
            v = int.from_bytes(raw[i:i+3], "little", signed=False)
            vals.append(v - (1 << 24) if v & (1 << 23) else v)
    else:
        vals = [int.from_bytes(raw[i:i+4], "little", signed=True) for i in range(0, len(raw), 4)]
    peak = max((abs(x) for x in vals), default=0)
    rms = math.sqrt(sum(x*x for x in vals) / len(vals)) if vals else 0
    full_scale = (1 << (8*width - 1)) - 1 if width > 1 else 127
    return {"file": str(path), "sample_rate_hz": rate, "channels": channels,
            "sample_width_bits": width*8, "frames": frames,
            "duration_s": frames/rate if rate else 0,
            "peak_dbfs": 20*math.log10(peak/full_scale) if peak else "-inf",
            "rms_dbfs": 20*math.log10(rms/full_scale) if rms else "-inf",
            "clipped_sample_fraction": sum(abs(x) >= full_scale for x in vals)/len(vals) if vals else 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wav_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("wav_manifest.csv"))
    args = ap.parse_args()
    files = sorted(args.wav_dir.rglob("*.wav"))
    if not files:
        raise SystemExit(f"No .wav files found under {args.wav_dir}")
    rows, errors = [], []
    for p in files:
        try:
            rows.append(inspect(p))
        except (wave.Error, OSError, ValueError) as e:
            errors.append({"file": str(p), "error": str(e)})
    fields = ["file", "sample_rate_hz", "channels", "sample_width_bits", "frames", "duration_s", "peak_dbfs", "rms_dbfs", "clipped_sample_fraction"]
    with args.out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"WAV files: {len(files)}; inspected: {len(rows)}; errors: {len(errors)}; manifest: {args.out}")
    for e in errors:
        print(f"ERROR {e['file']}: {e['error']}")
    print("Metadata/levels are QC only; this report does not measure pronunciation or wake-word suitability.")


if __name__ == "__main__":
    main()

