#!/usr/bin/env python3
"""Convert raw dataset JSONL into the chat window used for training.

Usage:
    python3 finetune_actions/to_chat.py finetune_actions/data/eval_handwritten.jsonl \\
        -o finetune_actions/data/eval_handwritten.chat.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_dataset import _load_system_prompts, _to_chat  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("-o", "--out", required=True)
    args = parser.parse_args()

    prompts = _load_system_prompts()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    count = 0
    with open(args.source, encoding="utf-8") as src, open(
        args.out, "w", encoding="utf-8"
    ) as dest:
        for line in src:
            line = line.strip()
            if not line:
                continue
            dest.write(
                json.dumps(_to_chat(json.loads(line), prompts=prompts), ensure_ascii=False)
                + "\n"
            )
            count += 1
    print(f"wrote {count} chat rows to {args.out}")


if __name__ == "__main__":
    main()
