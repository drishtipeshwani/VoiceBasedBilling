#!/usr/bin/env python3
"""Build the supervised fine-tuning dataset for the action-array agent.

Mixes invoice, customer-ledger, and stock-item rows. Each task uses its own
system prompt; splits are built per task so invoice membership stays stable.

Generates raw + chat-formatted JSONL files:
    train.jsonl / val.jsonl / test.jsonl
    train.chat.jsonl / val.chat.jsonl / test.chat.jsonl

Usage:
    python3 finetune_actions/generate_dataset.py --seed 20260817 --total 7300
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
import intents_customer  # noqa: E402
import intents_stock  # noqa: E402
import pools  # noqa: E402
from noise import apply_noise  # noqa: E402
from schema import dumps, make_action, make_response, remembered_item_name  # noqa: E402

Row = Dict[str, Any]
Actions = List[Dict[str, Any]]

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
SYSTEM_PROMPT_PATHS = {
    "invoice": os.path.join(HERE, "system_prompt.txt"),
    "customer": os.path.join(HERE, "system_prompt_customer.txt"),
    "stock": os.path.join(HERE, "system_prompt_stock.txt"),
}


def _load_system_prompts() -> Dict[str, str]:
    prompts: Dict[str, str] = {}
    for task, path in SYSTEM_PROMPT_PATHS.items():
        with open(path, encoding="utf-8") as handle:
            prompts[task] = handle.read().rstrip("\n")
    return prompts


def _load_system_prompt(task: str = "invoice") -> str:
    return _load_system_prompts()[task]


def _to_chat(
    row: Row, system_prompt: Optional[str] = None, prompts: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Convert a raw row into the chat message format used for training."""
    task = row.get("meta", {}).get("task", "invoice")
    if system_prompt is None:
        if prompts is None:
            prompts = _load_system_prompts()
        system_prompt = prompts[task]
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if row.get("lastModified"):
        messages.append({"role": "assistant", "content": dumps(row["lastModified"])})
    messages.append({"role": "user", "content": row["userInput"]})
    messages.append({"role": "assistant", "content": dumps(row["agentOutput"])})
    return {"messages": messages}


def _row(
    last_modified: Optional[Actions],
    user_input: str,
    agent_output: Actions,
    conversation_id: str,
    turn_index: int,
    tags: List[str],
    task: str = "invoice",
) -> Row:
    return {
        "lastModified": last_modified,
        "userInput": user_input,
        "agentOutput": agent_output,
        "meta": {
            "conversationId": conversation_id,
            "turnIndex": turn_index,
            "tags": tags,
            "task": task,
        },
    }


# --------------------------------------------------------------------------
# Single-turn rows: no prior context, so the utterance must stand alone.
# --------------------------------------------------------------------------

SINGLE_TURN_WEIGHTS = [
    ("company", 10),
    ("customer", 10),
    ("add_item", 18),
    ("price", 11),
    ("quantity", 9),
    ("item_discount_percent", 6),
    ("item_discount_amount", 5),
    ("rename", 4),
    ("remove", 5),
    ("bill_discount_percent", 4),
    ("bill_discount_amount", 3),
    ("date", 12),
    ("clear", 3),
    ("save", 5),
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
    elif kind == "save":
        utterance, response = intents.build_save(rng)
    else:
        utterance, response = intents.build_clear(rng)

    noisy = apply_noise(
        utterance, rng, intensity=0.55, protect_ordinals=protect_ordinals
    )
    return _row(None, noisy, response, f"single-{index}", 0, [kind, "single"])


def build_combo_turn(rng: random.Random, index: int) -> Row:
    tag, utterance, response = intents.build_combo(rng)
    noisy = apply_noise(utterance, rng, intensity=0.45)
    return _row(None, noisy, response, f"combo-{index}", 0, [tag, "combo", "single"])


# --------------------------------------------------------------------------
# Conversations: lastModified is the previous successfully applied actions array.
# --------------------------------------------------------------------------


def _pronoun_turn(rng: random.Random, remembered: str) -> tuple:
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
    last: Optional[Actions] = None
    turn = 0

    def emit(
        utterance: str,
        response: Actions,
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
            last = response

    def resolvable_item() -> Optional[str]:
        return remembered_item_name(last)

    if rng.random() < 0.75:
        utterance, response = intents.build_company(rng)
        emit(utterance, response, ["company", "multi"])

    if rng.random() < 0.75:
        utterance, response = intents.build_customer(rng)
        emit(utterance, response, ["customer", "multi"])

    if last is not None and rng.random() < 0.18:
        _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
        emit(
            utterance,
            make_response(make_action("INCOMPLETE")),
            ["orphan_ellipsis_no_item", "multi", "hard_negative"],
            updates_context=False,
        )

    for _ in range(rng.randint(1, 3)):
        if rng.random() < 0.22:
            tag, utterance, response = intents.build_combo(rng)
            emit(utterance, response, [tag, "combo", "multi"])
        else:
            utterance, response = intents.build_add_item(rng)
            emit(utterance, response, ["add_item", "multi"])

        for _ in range(rng.randint(1, 3)):
            remembered = resolvable_item()
            roll = rng.random()

            if remembered is None:
                if roll < 0.4:
                    _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
                    emit(
                        utterance,
                        make_response(make_action("INCOMPLETE")),
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
                other = pools.pick_other_item(remembered, rng)
                tag, utterance, response = _named_turn(rng, other)
                emit(utterance, response, [tag, "multi", "context_mismatch"])
            elif roll < 0.92:
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

        remembered = resolvable_item()
        if remembered is not None and rng.random() < 0.28:
            tag, utterance, response = _pronoun_turn(rng, remembered)
            emit(utterance, response, [tag, "multi"])

        removable = resolvable_item()
        if removable is not None and rng.random() < 0.22:
            utterance, response = intents.build_remove_pronoun(rng, removable)
            emit(utterance, response, ["remove_pronoun", "multi"])

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

    if rng.random() < 0.1:
        utterance, response = intents.build_save(rng)
        emit(utterance, response, ["save", "multi"])

    if rng.random() < 0.12:
        utterance, response = intents.build_clear(rng)
        emit(utterance, response, ["clear", "multi"])

        if rng.random() < 0.5:
            _, utterance, _ = _pronoun_turn(rng, pools.pick_item(rng))
            emit(
                utterance,
                make_response(make_action("INCOMPLETE")),
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


def _random_context(rng: random.Random) -> Actions:
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
        make_response(make_action("INCOMPLETE")),
        f"orphan-{index}",
        0,
        [tag, "single", "hard_negative"],
    )


# --------------------------------------------------------------------------
# Customer ledger
# --------------------------------------------------------------------------

CUSTOMER_SINGLE_WEIGHTS = [
    ("name", 28),
    ("change_name", 6),
    ("balance", 22),
    ("change_balance", 6),
    ("settled", 12),
    ("clear", 6),
    ("save", 10),
]


def _customer_row(
    last_modified: Optional[Actions],
    user_input: str,
    agent_output: Actions,
    conversation_id: str,
    turn_index: int,
    tags: List[str],
) -> Row:
    return _row(
        last_modified,
        user_input,
        agent_output,
        conversation_id,
        turn_index,
        tags,
        task="customer",
    )


def _customer_context(rng: random.Random) -> Actions:
    builders = [
        intents_customer.build_name,
        intents_customer.build_balance,
        intents_customer.build_name_balance,
        intents_customer.build_settled,
    ]
    _, response = rng.choice(builders)(rng)
    return response


def build_customer_single_turn(rng: random.Random, index: int) -> Row:
    kind = _pick_weighted(rng, CUSTOMER_SINGLE_WEIGHTS)
    builders = {
        "name": intents_customer.build_name,
        "change_name": intents_customer.build_change_name,
        "balance": intents_customer.build_balance,
        "change_balance": intents_customer.build_change_balance,
        "settled": intents_customer.build_settled,
        "clear": intents_customer.build_clear,
        "save": intents_customer.build_save,
    }
    utterance, response = builders[kind](rng)
    last = None
    if kind in ("save", "clear", "settled") and rng.random() < 0.7:
        last = _customer_context(rng)
    noisy = apply_noise(utterance, rng, intensity=0.55)
    return _customer_row(last, noisy, response, f"cust-single-{index}", 0, [kind, "single"])


def build_customer_combo_turn(rng: random.Random, index: int) -> Row:
    tag, utterance, response = intents_customer.build_combo(rng)
    noisy = apply_noise(utterance, rng, intensity=0.45)
    return _customer_row(
        None, noisy, response, f"cust-combo-{index}", 0, [tag, "combo", "single"]
    )


def build_customer_conversation(rng: random.Random, index: int) -> List[Row]:
    conversation_id = f"cust-conv-{index}"
    rows: List[Row] = []
    last: Optional[Actions] = None
    turn = 0

    def emit(
        utterance: str,
        response: Actions,
        tags: List[str],
        updates_context: bool = True,
    ) -> None:
        nonlocal last, turn
        noisy = apply_noise(utterance, rng, intensity=0.5)
        rows.append(_customer_row(last, noisy, response, conversation_id, turn, tags))
        turn += 1
        if updates_context:
            last = response

    if rng.random() < 0.72:
        utterance, response = intents_customer.build_name(rng)
        emit(utterance, response, ["name", "multi"])
    elif rng.random() < 0.5:
        tag, utterance, response = intents_customer.build_combo(rng)
        emit(utterance, response, [tag, "combo", "multi"])
    else:
        utterance, response = intents_customer.build_balance(rng)
        emit(utterance, response, ["balance", "multi"])

    for _ in range(rng.randint(1, 3)):
        roll = rng.random()
        if roll < 0.18:
            utterance, response = intents_customer.build_unknown(rng)
            emit(
                utterance,
                response,
                ["unknown", "multi", "context_preserved"],
                updates_context=False,
            )
        elif roll < 0.30:
            utterance, response = intents_customer.build_incomplete(rng)
            emit(
                utterance,
                response,
                ["incomplete", "multi", "context_preserved"],
                updates_context=False,
            )
        elif roll < 0.48:
            utterance, response = intents_customer.build_settled(rng)
            emit(utterance, response, ["settled", "multi"])
        elif roll < 0.66:
            utterance, response = intents_customer.build_change_name(rng)
            emit(utterance, response, ["change_name", "multi"])
        elif roll < 0.84:
            utterance, response = intents_customer.build_change_balance(rng)
            emit(utterance, response, ["change_balance", "multi"])
        else:
            utterance, response = intents_customer.build_balance(rng)
            emit(utterance, response, ["balance", "multi"])

    if rng.random() < 0.38:
        utterance, response = intents_customer.build_save(rng)
        emit(utterance, response, ["save", "multi"])

    if rng.random() < 0.14:
        utterance, response = intents_customer.build_clear(rng)
        emit(utterance, response, ["clear", "multi"])
        if rng.random() < 0.55:
            utterance, response = intents_customer.build_name(rng)
            emit(utterance, response, ["name", "multi", "after_clear"])

    return rows


def build_customer_unknown_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents_customer.build_unknown(rng)
    noisy = apply_noise(utterance, rng, intensity=0.4)
    last = _customer_context(rng) if rng.random() < 0.5 else None
    return _customer_row(
        last, noisy, response, f"cust-unknown-{index}", 0, ["unknown", "single"]
    )


def build_customer_incomplete_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents_customer.build_incomplete(rng)
    noisy = apply_noise(utterance, rng, intensity=0.3)
    last = _customer_context(rng) if rng.random() < 0.5 else None
    return _customer_row(
        last, noisy, response, f"cust-incomplete-{index}", 0, ["incomplete", "single"]
    )


def generate_customer_rows(rng: random.Random, total: int) -> List[Row]:
    n_single = int(total * 0.40)
    n_combo = int(total * 0.18)
    n_multi_target = int(total * 0.22)
    n_unknown = int(total * 0.08)
    n_incomplete = int(total * 0.05)
    n_save = int(total * 0.07)

    rows: List[Row] = [build_customer_single_turn(rng, i) for i in range(n_single)]
    rows.extend(build_customer_combo_turn(rng, i) for i in range(n_combo))
    rows.extend(
        _customer_row(
            _customer_context(rng) if rng.random() < 0.75 else None,
            apply_noise(utt, rng, intensity=0.35),
            resp,
            f"cust-save-{i}",
            0,
            ["save", "single"],
        )
        for i, (utt, resp) in enumerate(
            intents_customer.build_save(rng) for _ in range(n_save)
        )
    )

    conversation_rows: List[Row] = []
    conversation_index = 0
    while len(conversation_rows) < n_multi_target:
        conversation_rows.extend(build_customer_conversation(rng, conversation_index))
        conversation_index += 1
    rows.extend(conversation_rows)
    rows.extend(build_customer_unknown_row(rng, i) for i in range(n_unknown))
    rows.extend(build_customer_incomplete_row(rng, i) for i in range(n_incomplete))
    return rows


# --------------------------------------------------------------------------
# Stock items
# --------------------------------------------------------------------------

STOCK_SINGLE_WEIGHTS = [
    ("name", 22),
    ("quantity", 16),
    ("cost", 16),
    ("selling", 16),
    ("clear", 6),
    ("save", 10),
    ("ambiguous_price", 8),
]


def _stock_row(
    last_modified: Optional[Actions],
    user_input: str,
    agent_output: Actions,
    conversation_id: str,
    turn_index: int,
    tags: List[str],
) -> Row:
    return _row(
        last_modified,
        user_input,
        agent_output,
        conversation_id,
        turn_index,
        tags,
        task="stock",
    )


def _stock_context(rng: random.Random) -> Actions:
    builders = [
        intents_stock.build_name,
        intents_stock.build_quantity,
        intents_stock.build_cost,
        intents_stock.build_selling,
        intents_stock.build_name_quantity,
        intents_stock.build_full,
    ]
    _, response = rng.choice(builders)(rng)
    return response


def build_stock_single_turn(rng: random.Random, index: int) -> Row:
    kind = _pick_weighted(rng, STOCK_SINGLE_WEIGHTS)
    builders = {
        "name": intents_stock.build_name,
        "quantity": intents_stock.build_quantity,
        "cost": intents_stock.build_cost,
        "selling": intents_stock.build_selling,
        "clear": intents_stock.build_clear,
        "save": intents_stock.build_save,
        "ambiguous_price": intents_stock.build_ambiguous_price,
    }
    utterance, response = builders[kind](rng)
    tags = [kind, "single"]
    if kind == "ambiguous_price":
        tags.append("incomplete")
    last = None
    if kind in ("save", "clear", "ambiguous_price") and rng.random() < 0.7:
        last = _stock_context(rng)
    noisy = apply_noise(utterance, rng, intensity=0.55)
    return _stock_row(last, noisy, response, f"stk-single-{index}", 0, tags)


def build_stock_combo_turn(rng: random.Random, index: int) -> Row:
    tag, utterance, response = intents_stock.build_combo(rng)
    noisy = apply_noise(utterance, rng, intensity=0.45)
    return _stock_row(
        None, noisy, response, f"stk-combo-{index}", 0, [tag, "combo", "single"]
    )


def build_stock_conversation(rng: random.Random, index: int) -> List[Row]:
    conversation_id = f"stk-conv-{index}"
    rows: List[Row] = []
    last: Optional[Actions] = None
    turn = 0

    def emit(
        utterance: str,
        response: Actions,
        tags: List[str],
        updates_context: bool = True,
    ) -> None:
        nonlocal last, turn
        noisy = apply_noise(utterance, rng, intensity=0.5)
        rows.append(_stock_row(last, noisy, response, conversation_id, turn, tags))
        turn += 1
        if updates_context:
            last = response

    if rng.random() < 0.62:
        utterance, response = intents_stock.build_name(rng)
        emit(utterance, response, ["name", "multi"])
    else:
        tag, utterance, response = intents_stock.build_combo(rng)
        emit(utterance, response, [tag, "combo", "multi"])

    followups = [
        ("quantity", intents_stock.build_quantity),
        ("cost", intents_stock.build_cost),
        ("selling", intents_stock.build_selling),
        ("name", intents_stock.build_name),
    ]
    rng.shuffle(followups)
    for tag, builder in followups[: rng.randint(1, 3)]:
        roll = rng.random()
        if roll < 0.12:
            utterance, response = intents_stock.build_unknown(rng)
            emit(
                utterance,
                response,
                ["unknown", "multi", "context_preserved"],
                updates_context=False,
            )
        elif roll < 0.22:
            utterance, response = intents_stock.build_incomplete(rng)
            emit(
                utterance,
                response,
                ["incomplete", "multi", "context_preserved"],
                updates_context=False,
            )
        elif roll < 0.32:
            utterance, response = intents_stock.build_ambiguous_price(rng)
            emit(
                utterance,
                response,
                ["ambiguous_price", "multi", "incomplete"],
                updates_context=False,
            )
        else:
            utterance, response = builder(rng)
            emit(utterance, response, [tag, "multi"])

    if rng.random() < 0.36:
        utterance, response = intents_stock.build_save(rng)
        emit(utterance, response, ["save", "multi"])

    if rng.random() < 0.14:
        utterance, response = intents_stock.build_clear(rng)
        emit(utterance, response, ["clear", "multi"])
        if rng.random() < 0.55:
            utterance, response = intents_stock.build_name(rng)
            emit(utterance, response, ["name", "multi", "after_clear"])

    return rows


def build_stock_unknown_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents_stock.build_unknown(rng)
    noisy = apply_noise(utterance, rng, intensity=0.4)
    last = _stock_context(rng) if rng.random() < 0.5 else None
    return _stock_row(
        last, noisy, response, f"stk-unknown-{index}", 0, ["unknown", "single"]
    )


def build_stock_incomplete_row(rng: random.Random, index: int) -> Row:
    utterance, response = intents_stock.build_incomplete(rng)
    noisy = apply_noise(utterance, rng, intensity=0.3)
    last = _stock_context(rng) if rng.random() < 0.5 else None
    tags = ["incomplete", "single"]
    if response[0]["action"] == "INCOMPLETE" and "price" in utterance.lower():
        tags.append("ambiguous_price")
    return _stock_row(last, noisy, response, f"stk-incomplete-{index}", 0, tags)


def generate_stock_rows(rng: random.Random, total: int) -> List[Row]:
    n_single = int(total * 0.32)
    n_combo = int(total * 0.26)
    n_multi_target = int(total * 0.22)
    n_unknown = int(total * 0.08)
    n_incomplete = int(total * 0.06)
    n_save = int(total * 0.06)

    rows: List[Row] = [build_stock_single_turn(rng, i) for i in range(n_single)]
    rows.extend(build_stock_combo_turn(rng, i) for i in range(n_combo))
    rows.extend(
        _stock_row(
            _stock_context(rng) if rng.random() < 0.75 else None,
            apply_noise(utt, rng, intensity=0.35),
            resp,
            f"stk-save-{i}",
            0,
            ["save", "single"],
        )
        for i, (utt, resp) in enumerate(
            intents_stock.build_save(rng) for _ in range(n_save)
        )
    )

    conversation_rows: List[Row] = []
    conversation_index = 0
    while len(conversation_rows) < n_multi_target:
        conversation_rows.extend(build_stock_conversation(rng, conversation_index))
        conversation_index += 1
    rows.extend(conversation_rows)
    rows.extend(build_stock_unknown_row(rng, i) for i in range(n_unknown))
    rows.extend(build_stock_incomplete_row(rng, i) for i in range(n_incomplete))
    return rows


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def _task_of(row: Row) -> str:
    return row.get("meta", {}).get("task", "invoice")


def _key(row: Row):
    return (_task_of(row), dumps(row["lastModified"]), row["userInput"])


def _holdout_key(row: Row):
    return (
        _task_of(row),
        json.dumps(row["lastModified"], sort_keys=True),
        row["userInput"],
    )


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
    """Split by conversation so no session straddles the boundary."""
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


def write_chat_jsonl(
    path: str, rows: List[Row], prompts: Dict[str, str]
) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            chat = _to_chat(row, prompts=prompts)
            handle.write(json.dumps(chat, ensure_ascii=False) + "\n")


def write_raw_jsonl(path: str, rows: List[Row]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _filter_holdout(rows: List[Row], holdout_path: str) -> List[Row]:
    if not os.path.isfile(holdout_path):
        return rows
    holdout_keys = set()
    with open(holdout_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            holdout_keys.add(_holdout_key(json.loads(line)))
    filtered = [row for row in rows if _holdout_key(row) not in holdout_keys]
    removed = len(rows) - len(filtered)
    if removed:
        print(f"removed {removed} rows that collide with eval_handwritten.jsonl")
    return filtered


def generate_invoice_rows(rng: random.Random, total: int) -> List[Row]:
    n_single = int(total * 0.42)
    n_combo = int(total * 0.15)
    n_multi_target = int(total * 0.25)
    n_unknown = int(total * 0.06)
    n_incomplete = int(total * 0.04)
    n_orphan = int(total * 0.04)
    n_save = int(total * 0.04)

    rows: List[Row] = [build_single_turn(rng, i) for i in range(n_single)]
    rows.extend(build_combo_turn(rng, i) for i in range(n_combo))
    rows.extend(
        _row(
            None,
            apply_noise(utt, rng, intensity=0.35),
            resp,
            f"save-{i}",
            0,
            ["save", "single"],
        )
        for i, (utt, resp) in enumerate(intents.build_save(rng) for _ in range(n_save))
    )

    conversation_rows: List[Row] = []
    conversation_index = 0
    while len(conversation_rows) < n_multi_target:
        conversation_rows.extend(build_conversation(rng, conversation_index))
        conversation_index += 1
    rows.extend(conversation_rows)

    rows.extend(build_unknown_row(rng, i) for i in range(n_unknown))
    rows.extend(build_incomplete_row(rng, i) for i in range(n_incomplete))
    rows.extend(build_orphan_ellipsis_row(rng, i) for i in range(n_orphan))
    print(f"  invoice conversations: {conversation_index}")
    return rows


def _prepare_task_rows(
    rows: List[Row],
    rng: random.Random,
    val_frac: float,
    test_frac: float,
    holdout_path: str,
    label: str,
):
    before = len(rows)
    rows = dedupe(rows)
    rows = _filter_holdout(rows, holdout_path)
    train, val, test = split_rows(rows, rng, val_frac, test_frac)
    print(
        f"  {label}: {before} generated, {len(rows)} after dedupe/holdout "
        f"(train {len(train)} val {len(val)} test {len(test)})"
    )
    return train, val, test


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--total", type=int, default=7300, help="Invoice rows before split")
    parser.add_argument(
        "--customer-total",
        type=int,
        default=3600,
        help="Customer rows before split (~2500 train after dedupe at 8.4/8.4 val/test)",
    )
    parser.add_argument(
        "--stock-total",
        type=int,
        default=3600,
        help="Stock rows before split (~2500 train after dedupe at 8.4/8.4 val/test)",
    )
    parser.add_argument("--val-frac", type=float, default=0.084)
    parser.add_argument("--test-frac", type=float, default=0.084)
    parser.add_argument("--out-dir", default=DATA_DIR)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    prompts = _load_system_prompts()
    holdout_path = os.path.join(args.out_dir, "eval_handwritten.jsonl")

    print("generating invoice rows")
    invoice_train, invoice_val, invoice_test = _prepare_task_rows(
        generate_invoice_rows(rng, args.total),
        rng,
        args.val_frac,
        args.test_frac,
        holdout_path,
        "invoice",
    )

    print("generating customer rows")
    customer_train, customer_val, customer_test = _prepare_task_rows(
        generate_customer_rows(rng, args.customer_total),
        rng,
        args.val_frac,
        args.test_frac,
        holdout_path,
        "customer",
    )

    print("generating stock rows")
    stock_train, stock_val, stock_test = _prepare_task_rows(
        generate_stock_rows(rng, args.stock_total),
        rng,
        args.val_frac,
        args.test_frac,
        holdout_path,
        "stock",
    )

    train = invoice_train + customer_train + stock_train
    val = invoice_val + customer_val + stock_val
    test = invoice_test + customer_test + stock_test

    os.makedirs(args.out_dir, exist_ok=True)
    for name, split in (("train", train), ("val", val), ("test", test)):
        write_raw_jsonl(os.path.join(args.out_dir, f"{name}.jsonl"), split)
        write_chat_jsonl(
            os.path.join(args.out_dir, f"{name}.chat.jsonl"), split, prompts
        )

    print(f"  train: {len(train)}  val: {len(val)}  test: {len(test)}")
    print(f"  written to {args.out_dir}")


if __name__ == "__main__":
    main()
