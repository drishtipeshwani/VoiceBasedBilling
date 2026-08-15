#!/usr/bin/env python3
"""Score a trained LoRA adapter on the hand-written holdout set.

Runs every row in data/eval_handwritten.chat.jsonl by default and prints
exact-match accuracy (overall, plus single-turn vs multi-turn).

Usage:
    python3 finetune/eval_llm.py
    python3 finetune/eval_llm.py --adapter finetune/output/final
    python3 finetune/eval_llm.py --data finetune/data/test.chat.jsonl
    python3 finetune/eval_llm.py --n 20          # quick sample instead of full set
    python3 finetune/eval_llm.py --verbose       # print each example
"""

from __future__ import annotations

import argparse
import json
import os
import random

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
HANDWRITTEN_CHAT_PATH = os.path.join(HERE, "data", "eval_handwritten.chat.jsonl")
DEFAULT_ADAPTER = os.path.join(HERE, "output", "final")
MODEL_ID = "LiquidAI/LFM2.5-350M-Base"
MAX_NEW_TOKENS = 512


def format_prompt(tokenizer, messages: list[dict]) -> str:
    try:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        parts = [f"<|{m['role']}|>\n{m['content']}" for m in messages]
        parts.append("<|assistant|>")
        return "\n".join(parts)


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def resolve_data_path(path: str) -> str:
    """Accept paths relative to cwd, repo root, or the finetune/ folder."""
    candidates = [
        path,
        os.path.abspath(path),
        os.path.join(HERE, path),
        os.path.join(HERE, "data", os.path.basename(path)),
    ]
    # Common mistake: `finetune/data/...` while cwd is already finetune/
    if path.startswith("finetune" + os.sep) or path.startswith("finetune/"):
        candidates.append(os.path.join(HERE, path[len("finetune") + 1 :]))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        f"No such data file: {path}\n  tried: " + "\n  ".join(candidates)
    )

def is_multi_turn(row: dict) -> bool:
    return len(row["messages"]) > 3


def parse_generated_json(generated_text: str):
    text = generated_text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end < start:
        raise ValueError("no JSON object found")
    return json.loads(text[start : end + 1])


def run_example(
    model,
    tokenizer,
    device,
    row: dict,
    idx: int,
    total: int,
    *,
    verbose: bool,
) -> bool:
    messages = row["messages"]
    expected = messages[-1]["content"]
    prompt_messages = messages[:-1]

    user_turn = next(
        (m["content"] for m in reversed(prompt_messages) if m["role"] == "user"),
        "",
    )
    context_turn = next(
        (m["content"] for m in prompt_messages if m["role"] == "assistant"),
        None,
    )
    has_context = context_turn is not None
    kind = "multi-turn" if has_context else "single-turn"

    prompt = format_prompt(tokenizer, prompt_messages)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[1] :]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    try:
        exp_obj = json.loads(expected)
        gen_obj = parse_generated_json(generated_text)
        match = exp_obj == gen_obj
    except (json.JSONDecodeError, ValueError):
        match = False

    if verbose:
        print(f"\n{'─'*60}")
        print(f"  [{idx}/{total}] ({kind})")
        if has_context:
            print(f"  Context: {context_turn}")
        print(f"  User:    {user_turn}")
        print(f"{'─'*60}")
        print(f"\n  Expected:\n    {expected}")
        print(f"\n  Generated:\n    {generated_text}")
        print(f"\n  Exact match: {'YES' if match else 'NO'}")
    else:
        status = "OK" if match else "FAIL"
        print(f"  [{idx}/{total}] {status}  ({kind})  {user_turn[:80]}")
        if not match:
            print(f"    Expected:  {expected}")
            print(f"    Generated: {generated_text}")

    return match


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", default=DEFAULT_ADAPTER)
    parser.add_argument(
        "--data",
        default=HANDWRITTEN_CHAT_PATH,
        help="Chat JSONL to score (default: data/eval_handwritten.chat.jsonl)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="If set, score only N randomly sampled rows instead of the full set",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--multi-only",
        action="store_true",
        help="Only score multi-turn (lastModified) examples",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full expected/generated output for each example",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Loading base model {MODEL_ID} …")
    base_model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading adapter from {args.adapter} …")
    model = PeftModel.from_pretrained(base_model, args.adapter)
    model.eval()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model.to(device)

    rows = load_jsonl(resolve_data_path(args.data))
    if args.multi_only:
        rows = [r for r in rows if is_multi_turn(r)]
    if args.n is not None:
        rows = random.sample(rows, min(args.n, len(rows)))

    total = len(rows)
    n_multi = sum(1 for r in rows if is_multi_turn(r))
    n_single = total - n_multi
    print(f"\nScoring {total} examples from {args.data}")
    print(f"  ({n_single} single-turn, {n_multi} multi-turn)\n")

    correct = 0
    correct_single = 0
    correct_multi = 0
    single_total = 0
    multi_total = 0

    for i, row in enumerate(rows, 1):
        multi = is_multi_turn(row)
        if multi:
            multi_total += 1
        else:
            single_total += 1

        matched = run_example(
            model,
            tokenizer,
            device,
            row,
            i,
            total,
            verbose=args.verbose,
        )
        if matched:
            correct += 1
            if multi:
                correct_multi += 1
            else:
                correct_single += 1

    def pct(num: int, den: int) -> str:
        return f"{(100.0 * num / den):.1f}%" if den else "n/a"

    print(f"\n{'='*60}")
    print("  HANDWRITTEN SCORE")
    print(f"{'='*60}")
    print(f"  Single-turn: {correct_single}/{single_total} ({pct(correct_single, single_total)})")
    print(f"  Multi-turn:  {correct_multi}/{multi_total} ({pct(correct_multi, multi_total)})")
    print(f"  OVERALL:     {correct}/{total} ({pct(correct, total)})")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
