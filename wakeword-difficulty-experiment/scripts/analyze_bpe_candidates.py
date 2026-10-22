#!/usr/bin/env python3
"""Show how the bundle's SentencePiece model segments wake phrases."""
import argparse
import json
from pathlib import Path

import sentencepiece as spm


def read_tokens(path):
    by_id = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").rsplit(maxsplit=1)
            if len(parts) == 2:
                by_id[int(parts[1])] = parts[0]
    return by_id


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, type=Path, help="lang_bpe_500/bpe.model")
    ap.add_argument("--tokens", required=True, type=Path, help="lang_bpe_500/tokens.txt")
    ap.add_argument("--phrases", nargs="+", required=True, help="phrases to inspect")
    ap.add_argument("--case", choices=("upper", "lower", "preserve"), default="upper",
                    help="match the text normalization used by the ASR recipe")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    processor = spm.SentencePieceProcessor(model_file=str(args.model))
    tokens = read_tokens(args.tokens)
    results = []
    for phrase in args.phrases:
        normalized = phrase.upper() if args.case == "upper" else phrase.lower() if args.case == "lower" else phrase
        ids = processor.encode(normalized, out_type=int)
        pieces = processor.encode(normalized, out_type=str)
        results.append({"phrase": phrase, "normalized": normalized, "pieces": pieces,
                        "piece_ids": ids, "piece_count": len(ids),
                        "token_file_match": [tokens.get(i) for i in ids],
                        "has_unk": processor.unk_id() in ids})
    output = json.dumps({"model": str(args.model), "normalization": args.case,
                         "results": results}, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

