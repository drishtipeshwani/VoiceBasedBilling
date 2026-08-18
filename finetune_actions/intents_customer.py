"""Customer-ledger draft intents: name, balance, clear, save, unknowns."""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Tuple

import pools
from schema import make_action, make_response

Actions = List[Dict[str, Any]]
Built = Tuple[str, Actions]
TaggedBuilt = Tuple[str, str, Actions]

_NAME_TEMPLATES = [
    "add customer {name}",
    "customer name {name}",
    "customer name is {name}",
    "new customer {name}",
    "add party {name}",
    "party name {name}",
    "party name is {name}",
    "customer is {name}",
    "make customer {name}",
    "set customer name to {name}",
    "this customer is {name}",
    "add {name} to ledger",
    "ledger customer {name}",
    "put customer {name}",
    "name is {name}",
    "naam {name}",
    "unka naam {name}",
    "naya customer {name}",
    "add to khata {name}",
    "khata {name}",
    "create customer {name}",
    "next customer {name}",
    "make the name {name}",
    "the name is {name}",
    "customer {name}",
]

_CHANGE_NAME_TEMPLATES = [
    "change name to {name}",
    "no the name is {name}",
    "make the name {name}",
    "customer name should be {name}",
    "change customer to {name}",
    "actually {name}",
    "sorry name is {name}",
    "update name to {name}",
]

_BALANCE_TEMPLATES = [
    "opening balance {amount}",
    "balance {amount}",
    "balance is {amount}",
    "outstanding {amount}",
    "outstanding balance {amount}",
    "they owe {amount}",
    "due {amount}",
    "set balance to {amount}",
    "make balance {amount}",
    "opening {amount}",
    "credit {amount}",
    "pending {amount} rupees",
    "udhaar {amount}",
    "baaki {amount}",
    "pending amount {amount}",
    "make opening balance {amount}",
    "outstanding is {amount}",
    "balance amount {amount}",
    "they have to pay {amount}",
    "dues {amount}",
]

_CHANGE_BALANCE_TEMPLATES = [
    "change balance to {amount}",
    "no make balance {amount}",
    "update balance {amount}",
    "make it {amount} balance",
    "sorry balance is {amount}",
    "actually outstanding {amount}",
]

_NAME_BALANCE_TEMPLATES = [
    "add customer {name} balance {amount}",
    "customer {name} opening balance {amount}",
    "add {name} with balance {amount}",
    "new customer {name} outstanding {amount}",
    "party {name} due {amount}",
    "add customer {name} they owe {amount}",
    "ledger {name} balance {amount}",
    "customer name {name} balance {amount}",
    "add party {name} udhaar {amount}",
    "naya customer {name} baaki {amount}",
    "khata {name} outstanding {amount}",
    "customer is {name} pending {amount}",
    "add {name} opening {amount}",
    "party name {name} dues {amount}",
]

_SETTLED_TEMPLATES = [
    "settled",
    "no dues",
    "balance zero",
    "balance is zero",
    "nothing outstanding",
    "they have paid",
    "clear the dues",
    "no pending balance",
    "mark as settled",
    "zero balance",
    "no udhaar",
    "all paid",
    "nothing pending",
    "balance 0",
    "opening balance zero",
    "paid",
    "mark paid",
    "mark as paid",
    "mark it paid",
    "fully paid",
    "paid in full",
    "already paid",
    "they paid",
    "payment done",
]

_CLEAR_TEMPLATES = [
    "clear",
    "reset",
    "clear draft",
    "start again",
    "reset customer",
    "clear the customer",
    "wipe the draft",
    "clear this",
    "start over",
]

_SAVE_TEMPLATES = [
    "save",
    "save it",
    "save customer",
    "save the customer",
    "save this",
    "okay save",
    "please save",
    "store the customer",
    "save to ledger",
    "save this customer",
    "ok save it",
    "save khata",
    "haan save kar do",
    "save this party",
    "please save this now",
    "done save",
    "save customer please",
    "store this in ledger",
    "keep this customer",
]

INCOMPLETE_UTTERANCES = [
    "add customer",
    "customer name is",
    "customer uh",
    "add party",
    "opening balance",
    "the balance is",
    "make the name",
    "new customer",
    "add uh",
    "party name",
    "outstanding",
    "they owe",
    "set customer",
    "change name to",
    "balance is",
    "naya customer",
    "udhaar",
    "khata",
]

DOMAIN_UNKNOWN = [
    "add paneer",
    "add rice twenty kg",
    "put atta at eighty rupees",
    "add 5 pens rate 10 rupees",
    "give 10 percent off on the whole bill",
    "cut 50 rupees from the total",
    "bill date 25th June",
    "save the bill",
    "save invoice",
    "clear invoice",
    "cost price 50",
    "selling price 80",
    "quantity 10 cost 20",
    "shop name is Mehta Electricals",
    "add sl 253 to the bill",
    "remove the pens",
    "make price of onions forty",
    "total discount 3 percent",
    "add item speaker",
    "stock quantity 12",
]


def build_name(rng: random.Random) -> Built:
    name = rng.choice(pools.CUSTOMER_NAMES)
    utterance = rng.choice(_NAME_TEMPLATES).format(name=name)
    return utterance, make_response(make_action("SET_NAME", name=name))


def build_change_name(rng: random.Random) -> Built:
    name = rng.choice(pools.CUSTOMER_NAMES)
    utterance = rng.choice(_CHANGE_NAME_TEMPLATES).format(name=name)
    return utterance, make_response(make_action("SET_NAME", name=name))


def build_balance(rng: random.Random) -> Built:
    amount = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_BALANCE_TEMPLATES).format(
        amount=pools.render_price(amount, rng)
    )
    return utterance, make_response(make_action("SET_BALANCE", balanceAmount=amount))


def build_change_balance(rng: random.Random) -> Built:
    amount = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_CHANGE_BALANCE_TEMPLATES).format(
        amount=pools.render_price(amount, rng)
    )
    return utterance, make_response(make_action("SET_BALANCE", balanceAmount=amount))


def build_name_balance(rng: random.Random) -> Built:
    name = rng.choice(pools.CUSTOMER_NAMES)
    amount = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_BALANCE_TEMPLATES).format(
        name=name, amount=pools.render_price(amount, rng)
    )
    return utterance, make_response(
        make_action("SET_NAME", name=name),
        make_action("SET_BALANCE", balanceAmount=amount),
    )


def build_settled(rng: random.Random) -> Built:
    return rng.choice(_SETTLED_TEMPLATES), make_response(
        make_action("SET_BALANCE", balanceAmount=0)
    )


def build_clear(rng: random.Random) -> Built:
    return rng.choice(_CLEAR_TEMPLATES), make_response(make_action("CLEAR"))


def build_save(rng: random.Random) -> Built:
    return rng.choice(_SAVE_TEMPLATES), make_response(make_action("SAVE"))


def build_unknown(rng: random.Random) -> Built:
    pool = DOMAIN_UNKNOWN if rng.random() < 0.45 else pools.UNKNOWN_UTTERANCES
    return rng.choice(pool), make_response(make_action("UNKNOWN"))


def build_incomplete(rng: random.Random) -> Built:
    return rng.choice(INCOMPLETE_UTTERANCES), make_response(make_action("INCOMPLETE"))


def build_combo(rng: random.Random) -> TaggedBuilt:
    utterance, response = build_name_balance(rng)
    return "combo_name_balance", utterance, response


CUSTOMER_FOLLOWUPS: List[Tuple[str, Callable[[random.Random], Built]]] = [
    ("name", build_name),
    ("change_name", build_change_name),
    ("balance", build_balance),
    ("change_balance", build_change_balance),
    ("settled", build_settled),
]
