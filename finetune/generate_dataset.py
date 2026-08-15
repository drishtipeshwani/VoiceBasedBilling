#!/usr/bin/env python3
"""Build the supervised fine-tuning dataset for the invoice voice agent.

Generates raw + chat-formatted JSONL files:
    train.jsonl / val.jsonl / test.jsonl
    train.chat.jsonl / val.chat.jsonl / test.chat.jsonl

Usage:
    python3 finetune/generate_dataset.py --seed 20260726 --total 4000
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import intents  # noqa: E402
import pools  # noqa: E402
from noise import apply_noise  # noqa: E402
from schema import dumps, make_response, remembered_item_name  # noqa: E402

Row = Dict[str, Any]

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
SYSTEM_PROMPT_PATH = os.path.join(HERE, "system_prompt.txt")


def _load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as handle:
        return handle.read().rstrip("\n")


def _to_chat(row: Row, system_prompt: str) -> Dict[str, Any]:
    """Convert a raw row into the chat message format used for training."""
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if row.get("lastModified"):
        messages.append({"role": "assistant", "content": dumps(row["lastModified"])})
    messages.append({"role": "user", "content": row["userInput"]})
    messages.append({"role": "assistant", "content": dumps(row["agentOutput"])})
    return {"messages": messages}


def _row(
    last_modified: Optional[Dict[str, Any]],
    user_input: str,
    agent_output: Dict[str, Any],
    conversation_id: str,
    turn_index: int,
    tags: List[str],
) -> Row:
    return {
        "lastModified": last_modified,
        "userInput": user_input,
        "agentOutput": agent_output,
        "meta": {
            "conversationId": conversation_id,
            "turnIndex": turn_index,
            "tags": tags,
        },
    }


# --------------------------------------------------------------------------
# Single-turn rows: no prior context, so the utterance must stand alone.
# --------------------------------------------------------------------------

SINGLE_TURN_WEIGHTS = [
    ("company", 10),
    ("customer", 10),
    ("add_item", 20),
    ("price", 12),
    ("quantity", 9),
    ("item_discount_percent", 7),
    ("item_discount_amount", 6),
    ("rename", 4),
    ("remove", 5),
    ("bill_discount_percent", 4),
    ("bill_discount_amount", 3),
    ("date", 16),
    ("clear", 3),
]


def _pick_weighted(rng: random.Random, weights) -> str:
    total = sum(weight for _, weight in weights)
    roll = rng.uniform(0, total)
    upto = 0.0
    for name, weight in weights:
        upto += weight
        if roll <= upto:
            return name
    return weights[-1][0]


def build_single_turn(rng: random.Random, index: int) -> Row:
    kind = _pick_weighted(rng, SINGLE_TURN_WEIGHTS)
    item = pools.pick_item(rng)
    protect_ordinals = False

    if kind == "company":
        utterance, response = intents.build_company(rng)
    elif kind == "customer":
        utterance, response = intents.build_customer(rng)
    elif kind == "add_item":
        utterance, response = intents.build_add_item(rng)
    elif kind == "price":
        utterance, response = intents.build_price(rng, item)
    elif kind == "quantity":
        utterance, response = intents.build_quantity(rng, item)
    elif kind == "item_discount_percent":
        utterance, response = intents.build_item_discount_percent(rng, item)
    elif kind == "item_discount_amount":
        utterance, response = intents.build_item_discount_amount(rng, item)
    elif kind == "rename":
        utterance, response = intents.build_rename(rng, item)
    elif kind == "remove":
        utterance, response = intents.build_remove(rng, item)
    elif kind == "bill_discount_percent":
        utterance, response = intents.build_bill_discount_percent(rng)
    elif kind == "bill_discount_amount":
        utterance, response = intents.build_bill_discount_amount(rng)
    elif kind == "date":
        utterance, response = intents.build_date(rng)
        protect_ordinals = True
    else:
        utterance, response = intents.build_clear(rng)

    noisy = apply_noise(
        utterance, rng, intensity=0.55, protect_ordinals=protect_ordinals
    )
    return _row(None, noisy, response, f"single-{index}", 0, [kind, "single"])


# --------------------------------------------------------------------------
# Conversations: lastModified is the previous successfully applied response,
# exactly as HomeScreen keeps it.
# --------------------------------------------------------------------------


def _pronoun_turn(
    rng: random.Random, remembered: str
) -> Optional[tuple]:
    """An update phrased without naming the item."""
    choices = [
        ("price_pronoun", intents.build_price_pronoun),
        ("quantity_pronoun", intents.build_quantity_pronoun),
        ("item_discount_percent_pronoun", intents.build_item_discount_percent_pronoun),
        ("item_discount_amount_pronoun", intents.build_item_discount_amount_pronoun),
        ("rename_pronoun", intents.build_rename_pronoun),
    ]
    tag, builder = rng.choice(choices)
    utterance, response = builder(rng, remembered)
    return tag, utterance, response


def _named_turn(rng: random.Random, item: str) -> tuple:
    choices = [
        ("price", intents.build_price),
        ("quantity", intents.build_quantity),
        ("item_discount_percent", intents.build_item_discount_percent),
        ("item_discount_amount", intents.build_item_discount_amount),
    ]
    tag, builder = rng.choice(choices)
    utterance, response = builder(rng, item)
    return tag, utterance, response


def build_conversation(rng: random.Random, index: int) -> List[Row]:
    conversation_id = f"conv-{index}"
    rows: List[Row] = []
    last: Optional[Dict[str, Any]] = None
    turn = 0

    def emit(
        utterance: str,
        response: Dict[str, Any],
        tags: List[str],
        updates_context: bool = True,
        protect_ordinals: bool = False,
    ) -> None:
        nonlocal last, turn
        noisy = apply_noise(
            utterance, rng, intensity=0.5, protect_ordinals=protect_ordinals
        )
        rows.append(_row(last, noisy, response, conversation_id, turn, tags))
        turn += 1
        if updates_context:
            # HomeScreen only remembers responses it could actually apply.
            last = response

    def resolvable_item() -> Optional[str]:
        """The item a pronoun may attach to, read from the context the model
        will actually see. A removal is excluded: the item is gone, so
        referring back to it is not something to teach."""
        item = (last or {}).get("modifiedItems")
        if not item or item.get("removeItem"):
            return None
        return remembered_item_name(last)

    if rng.random() < 0.75:
        utterance, response = intents.build_company(rng)
        emit(utterance, response, ["company", "multi"])

    if rng.random() < 0.75:
        utterance, response = intents.build_customer(rng)
        emit(utterance, response, ["customer", "multi"])

    # An ellipsis turn here is unresolvable: the last response carries no item.
    if last is not None and rng.random() < 0.18:
        _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
        emit(
            utterance,
            make_response(incomplete_input=True),
            ["orphan_ellipsis_no_item", "multi", "hard_negative"],
            updates_context=False,
        )

    for _ in range(rng.randint(1, 3)):
        utterance, response = intents.build_add_item(rng)
        emit(utterance, response, ["add_item", "multi"])

        for _ in range(rng.randint(1, 3)):
            remembered = resolvable_item()
            roll = rng.random()

            if remembered is None:
                # Context lost its item, usually because a date or discount
                # turn came in between. A pronoun now resolves to nothing.
                if roll < 0.4:
                    _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
                    emit(
                        utterance,
                        make_response(incomplete_input=True),
                        ["orphan_ellipsis_no_item", "multi", "hard_negative"],
                        updates_context=False,
                    )
                else:
                    tag, utterance, response = _named_turn(rng, pools.pick_item(rng))
                    emit(utterance, response, [tag, "multi", "context_recovered"])
                continue

            if roll < 0.72:
                tag, utterance, response = _pronoun_turn(rng, remembered)
                emit(utterance, response, [tag, "multi"])
            elif roll < 0.84:
                # Names a different item than the one in context, so the
                # remembered name must lose to the spoken one.
                other = pools.pick_other_item(remembered, rng)
                tag, utterance, response = _named_turn(rng, other)
                emit(utterance, response, [tag, "multi", "context_mismatch"])
            elif roll < 0.92:
                # Bare day right after item talk: still a date, not a quantity.
                utterance, response = intents.build_date(rng, allow_bare=True)
                emit(
                    utterance,
                    response,
                    ["date", "multi", "date_after_item"],
                    protect_ordinals=True,
                )
            else:
                utterance, response = intents.build_quantity_pronoun(
                    rng, remembered, bare=True
                )
                emit(
                    utterance,
                    response,
                    ["quantity_pronoun", "multi", "qty_vs_date"],
                    protect_ordinals=True,
                )

        # Extra context-resolution turn: update the last item without naming it.
        remembered = resolvable_item()
        if remembered is not None and rng.random() < 0.28:
            tag, utterance, response = _pronoun_turn(rng, remembered)
            emit(utterance, response, [tag, "multi"])

        removable = resolvable_item()
        if removable is not None and rng.random() < 0.22:
            utterance, response = intents.build_remove_pronoun(rng, removable)
            emit(utterance, response, ["remove_pronoun", "multi"])

        # Background speech does not update what the app remembers, so the next
        # turn still resolves against the response before it.
        if rng.random() < 0.22:
            if rng.random() < 0.5:
                utterance, response = intents.build_unknown(rng)
                tags = ["unknown", "multi", "context_preserved"]
            else:
                utterance, response = intents.build_incomplete(rng)
                tags = ["incomplete", "multi", "context_preserved"]
            emit(utterance, response, tags, updates_context=False)

    if rng.random() < 0.3:
        if rng.random() < 0.6:
            utterance, response = intents.build_bill_discount_percent(rng)
            emit(utterance, response, ["bill_discount_percent", "multi"])
        else:
            utterance, response = intents.build_bill_discount_amount(rng)
            emit(utterance, response, ["bill_discount_amount", "multi"])

    if rng.random() < 0.45:
        utterance, response = intents.build_date(rng)
        emit(utterance, response, ["date", "multi"], protect_ordinals=True)

    if rng.random() < 0.12:
        utterance, response = intents.build_clear(rng)
        emit(utterance, response, ["clear", "multi"])

        # After a clear there is nothing to refer back to.
        if rng.random() < 0.5:
            _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
            emit(
                utterance,
                make_response(incomplete_input=True),
                ["orphan_ellipsis_after_clear", "multi", "hard_negative"],
                updates_context=False,
            )

    return rows


# --------------------------------------------------------------------------
# Standalone negatives
# --------------------------------------------------------------------------


def build_unknown_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents.build_unknown(rng)
    noisy = apply_noise(utterance, rng, intensity=0.4)
    last = _random_context(rng) if rng.random() < 0.5 else None
    return _row(last, noisy, response, f"unknown-{index}", 0, ["unknown", "single"])


def build_incomplete_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents.build_incomplete(rng)
    noisy = apply_noise(utterance, rng, intensity=0.3)
    last = _random_context(rng) if rng.random() < 0.5 else None
    return _row(
        last, noisy, response, f"incomplete-{index}", 0, ["incomplete", "single"]
    )


def _random_context(rng: random.Random) -> Dict[str, Any]:
    """A plausible previous response, for rows where context exists but is
    irrelevant to the utterance."""
    roll = rng.random()
    if roll < 0.3:
        _, response = intents.build_add_item(rng)
    elif roll < 0.5:
        _, response = intents.build_company(rng)
    elif roll < 0.7:
        _, response = intents.build_customer(rng)
    elif roll < 0.85:
        _, response = intents.build_date(rng)
    else:
        _, response = intents.build_bill_discount_percent(rng)
    return response


def build_orphan_ellipsis_row(rng: random.Random, index: int) -> Row:
    """A pronoun update with nothing to resolve against."""
    remembered = pools.pick_item(rng)
    _, utterance, _ = _pronoun_turn(rng, remembered)
    noisy = apply_noise(utterance, rng, intensity=0.45)

    roll = rng.random()
    if roll < 0.5:
        last = None
        tag = "orphan_ellipsis_cold_start"
    else:
        # Context exists but holds no item to attach the update to.
        choice = rng.random()
        if choice < 0.35:
            _, last = intents.build_company(rng)
        elif choice < 0.7:
            _, last = intents.build_customer(rng)
        elif choice < 0.85:
            _, last = intents.build_date(rng)
        else:
            _, last = intents.build_clear(rng)
        tag = "orphan_ellipsis_no_item"

    return _row(
        last,
        noisy,
        make_response(incomplete_input=True),
        f"orphan-{index}",
        0,
        [tag, "single", "hard_negative"],
    )


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def _key(row: Row):
    return (dumps(row["lastModified"]), row["userInput"])


def dedupe(rows: List[Row]) -> List[Row]:
    seen = set()
    kept: List[Row] = []
    for row in rows:
        key = _key(row)
        if key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept


def split_rows(
    rows: List[Row],
    rng: random.Random,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
):
    """Split by conversation so no session straddles the boundary.

    Conversations vary in length, so the row counts land near the requested
    fractions rather than exactly on them.
    """
    groups: Dict[str, List[Row]] = {}
    for row in rows:
        groups.setdefault(row["meta"]["conversationId"], []).append(row)

    keys = sorted(groups)
    rng.shuffle(keys)

    total_rows = len(rows)
    val_budget = total_rows * val_frac
    test_budget = total_rows * test_frac

    val_keys: List[str] = []
    test_keys: List[str] = []
    train_keys: List[str] = []
    val_size = test_size = 0

    for key in keys:
        size = len(groups[key])
        if val_size < val_budget:
            val_keys.append(key)
            val_size += size
        elif test_size < test_budget:
            test_keys.append(key)
            test_size += size
        else:
            train_keys.append(key)

    def collect(subset):
        out: List[Row] = []
        for key in subset:
            out.extend(groups[key])
        return out

    return collect(train_keys), collect(val_keys), collect(test_keys)


def write_chat_jsonl(path: str, rows: List[Row], system_prompt: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            chat = _to_chat(row, system_prompt)
            handle.write(json.dumps(chat, ensure_ascii=False) + "\n")


def write_raw_jsonl(path: str, rows: List[Row]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument("--total", type=int, default=6000)
    parser.add_argument("--val-frac", type=float, default=0.084)
    parser.add_argument("--test-frac", type=float, default=0.084)
    parser.add_argument("--out-dir", default=DATA_DIR)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    system_prompt = _load_system_prompt()

    n_single = int(args.total * 0.55)
    n_multi_target = int(args.total * 0.30)
    n_unknown = int(args.total * 0.08)
    n_incomplete = int(args.total * 0.04)
    n_orphan = int(args.total * 0.04)

    rows: List[Row] = [build_single_turn(rng, i) for i in range(n_single)]

    conversation_rows: List[Row] = []
    conversation_index = 0
    while len(conversation_rows) < n_multi_target:
        conversation_rows.extend(build_conversation(rng, conversation_index))
        conversation_index += 1
    rows.extend(conversation_rows)

    rows.extend(build_unknown_row(rng, i) for i in range(n_unknown))
    rows.extend(build_incomplete_row(rng, i) for i in range(n_incomplete))
    rows.extend(build_orphan_ellipsis_row(rng, i) for i in range(n_orphan))

    before = len(rows)
    rows = dedupe(rows)

    holdout_path = os.path.join(args.out_dir, "eval_handwritten.jsonl")
    if os.path.isfile(holdout_path):
        holdout_keys = set()
        with open(holdout_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                holdout_keys.add(
                    (json.dumps(row["lastModified"], sort_keys=True), row["userInput"])
                )
        filtered = [
            row
            for row in rows
            if (json.dumps(row["lastModified"], sort_keys=True), row["userInput"])
            not in holdout_keys
        ]
        removed = len(rows) - len(filtered)
        if removed:
            print(f"removed {removed} rows that collide with eval_handwritten.jsonl")
        rows = filtered

    train, val, test = split_rows(rows, rng, args.val_frac, args.test_frac)

    os.makedirs(args.out_dir, exist_ok=True)
    for name, split in (("train", train), ("val", val), ("test", test)):
        write_raw_jsonl(os.path.join(args.out_dir, f"{name}.jsonl"), split)
        write_chat_jsonl(
            os.path.join(args.out_dir, f"{name}.chat.jsonl"), split, system_prompt
        )

    print(f"generated {before} rows, {len(rows)} after dedupe")
    print(f"  conversations: {conversation_index}")
    print(f"  train: {len(train)}  val: {len(val)}  test: {len(test)}")
    print(f"  written to {args.out_dir}")


if __name__ == "__main__":
    main()
