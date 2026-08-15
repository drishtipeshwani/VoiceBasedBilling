"""Intent builders: one spoken utterance plus the JSON it must produce.

Each builder returns (utterance, response). Builders that can be phrased
without naming the item take an `item_name` of None to mean "say it with a
pronoun", which is only legal when the caller has a remembered item.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional, Tuple

import pools
from schema import make_item, make_response

Built = Tuple[str, Dict[str, Any]]

# --------------------------------------------------------------------------
# Company and customer
# --------------------------------------------------------------------------

_COMPANY_TEMPLATES = [
    "make company name {name}",
    "company name is {name}",
    "set company name to {name}",
    "my company name is {name}",
    "the company is {name}",
    "change company name to {name}",
    "bill from {name}",
    "company {name}",
    "make the company name as {name}",
    "shop name is {name}",
    "firm name {name}",
    "put company name {name}",
]

_CUSTOMER_TEMPLATES = [
    "bill to customer {name}",
    "customer name is {name}",
    "make customer name {name}",
    "set customer to {name}",
    "the customer is {name}",
    "change customer name to {name}",
    "bill it to {name}",
    "customer {name}",
    "party name is {name}",
    "make the bill to customer {name}",
    "buyer name {name}",
    "this bill is for {name}",
]


def build_company(rng: random.Random) -> Built:
    name = rng.choice(pools.COMPANY_NAMES)
    utterance = rng.choice(_COMPANY_TEMPLATES).format(name=name)
    return utterance, make_response(modified_company_name=name)


def build_customer(rng: random.Random) -> Built:
    name = rng.choice(pools.CUSTOMER_NAMES)
    utterance = rng.choice(_CUSTOMER_TEMPLATES).format(name=name)
    return utterance, make_response(modified_customer_name=name)


# --------------------------------------------------------------------------
# Adding items
# --------------------------------------------------------------------------

_ADD_BARE_TEMPLATES = [
    "add item {item}",
    "add {item}",
    "add one {item}",
    "put {item} in the bill",
    "add {item} to the invoice",
    "{item} also add",
    "next item {item}",
    "add item {item} please",
]

_ADD_QTY_TEMPLATES = [
    "add item {item} quantity {qty}",
    "add {qty} {item}",
    "add {item} {qty}",
    "put {qty} {item} in the bill",
    "add item {item} {qty}",
]

_ADD_PRICE_TEMPLATES = [
    "add item {item} price {price}",
    "add {item} at {price}",
    "add {item} for {price}",
    "add item {item} rate {price}",
]

_ADD_FULL_TEMPLATES = [
    "add item {item} quantity {qty} price {price}",
    "add {qty} {item} at {price}",
    "add {item} quantity {qty} rate {price}",
    "put {qty} {item} price {price}",
    "add item {item} {qty} price {price}",
]


def build_add_item(rng: random.Random) -> Built:
    item = pools.pick_item(rng)
    spoken = pools.render_item(item, rng)
    roll = rng.random()

    if roll < 0.35:
        utterance = rng.choice(_ADD_BARE_TEMPLATES).format(item=spoken)
        return utterance, make_response(modified_items=make_item(name=item))

    if roll < 0.55:
        quantity = rng.choice(pools.QUANTITY_VALUES)
        utterance = rng.choice(_ADD_QTY_TEMPLATES).format(
            item=spoken, qty=pools.render_quantity(quantity, rng)
        )
        return utterance, make_response(
            modified_items=make_item(name=item, quantity=quantity)
        )

    if roll < 0.7:
        price = rng.choice(pools.PRICE_VALUES)
        utterance = rng.choice(_ADD_PRICE_TEMPLATES).format(
            item=spoken, price=pools.render_price(price, rng)
        )
        return utterance, make_response(
            modified_items=make_item(name=item, price_per_item=price)
        )

    quantity = rng.choice(pools.QUANTITY_VALUES)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_ADD_FULL_TEMPLATES).format(
        item=spoken,
        qty=pools.render_quantity(quantity, rng),
        price=pools.render_price(price, rng),
    )
    return utterance, make_response(
        modified_items=make_item(name=item, quantity=quantity, price_per_item=price)
    )


# --------------------------------------------------------------------------
# Updating an existing item
#
# Every one of these has a named form and a pronoun form. The pronoun form is
# what makes the previous response load-bearing.
# --------------------------------------------------------------------------

_PRICE_NAMED_TEMPLATES = [
    "make the price of {item} {price}",
    "price of {item} is {price}",
    "set {item} price to {price}",
    "{item} rate is {price}",
    "change the price of {item} to {price}",
    "make {item} {price}",
    "{item} rate as {price}",
    "put price of {item} as {price}",
]

_PRICE_PRONOUN_TEMPLATES = [
    "make its price {price}",
    "price is {price}",
    "make the price {price}",
    "set the price to {price}",
    "rate is {price}",
    "make it {price} rupees",
    "the rate should be {price}",
    "change price to {price}",
]

_QTY_NAMED_TEMPLATES = [
    "make quantity of {item} {qty}",
    "{item} quantity is {qty}",
    "set {item} quantity to {qty}",
    "change quantity of {item} to {qty}",
    "make it {qty} {item}",
    "{item} {qty}",
]

# The unit, if any, comes from render_quantity, so templates never add their
# own: "make it {qty} pieces" would produce "make it nine nos pieces".
_QTY_PRONOUN_TEMPLATES = [
    "make quantity {qty}",
    "change quantity to {qty}",
    "quantity is {qty}",
    "set quantity as {qty}",
    "make it {qty}",
    "need {qty}",
]

_ITEM_PERCENT_NAMED_TEMPLATES = [
    "give {disc} discount on {item}",
    "apply {disc} on {item}",
    "{item} discount {disc}",
    "give {disc} off on {item}",
    "discount of {disc} on {item}",
    "make {item} discount {disc}",
]

_ITEM_PERCENT_PRONOUN_TEMPLATES = [
    "give {disc} discount",
    "apply {disc} discount on it",
    "give it {disc} off",
    "discount of {disc}",
    "add {disc} discount",
    "make the discount {disc}",
]

_ITEM_AMOUNT_NAMED_TEMPLATES = [
    "give {disc} discount on {item}",
    "reduce {disc} on {item}",
    "reduce {item} by {disc}",
    "give {disc} off on {item}",
    "discount of {disc} on {item}",
    "less {disc} on {item}",
]

_ITEM_AMOUNT_PRONOUN_TEMPLATES = [
    "give {disc} discount",
    "reduce {disc} on it",
    "give it {disc} off",
    "discount of {disc}",
    "less {disc}",
    "cut {disc} from it",
]

_RENAME_NAMED_TEMPLATES = [
    "change {old} to {new}",
    "rename {old} as {new}",
    "make {old} into {new}",
    "the {old} is actually {new}",
    "correct {old} to {new}",
]

_RENAME_PRONOUN_TEMPLATES = [
    "call it {new}",
    "rename it to {new}",
    "change the name to {new}",
    "actually it is {new}",
    "make the name {new}",
]

_REMOVE_NAMED_TEMPLATES = [
    "remove {item}",
    "delete {item} from the bill",
    "remove the {item}",
    "take out {item}",
    "cancel {item}",
    "take {item} off the bill",
    "remove {item} from invoice",
]

_REMOVE_PRONOUN_TEMPLATES = [
    "remove it",
    "delete it",
    "remove that one",
    "take it out",
    "cancel that item",
    "take that one off",
]


def build_price(rng: random.Random, item_name: Optional[str]) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    rendered = pools.render_price(price, rng)
    if item_name is None:
        raise ValueError("price intent needs an item name")
    utterance = rng.choice(_PRICE_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng), price=rendered
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, price_per_item=price)
    )


def build_price_pronoun(rng: random.Random, remembered: str) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_PRICE_PRONOUN_TEMPLATES).format(
        price=pools.render_price(price, rng)
    )
    return utterance, make_response(
        modified_items=make_item(name=remembered, price_per_item=price)
    )


def build_quantity(rng: random.Random, item_name: str) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    utterance = rng.choice(_QTY_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        qty=pools.render_quantity(quantity, rng),
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, quantity=quantity)
    )


_QTY_BARE_TEMPLATES = [
    "make it {qty}",
    "make it {qty} pieces",
    "change it to {qty}",
    "{qty} pieces",
]


def build_quantity_pronoun(
    rng: random.Random, remembered: str, bare: bool = False
) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    if bare:
        # "make it 14", the twin of the "make it 14th" date utterance.
        utterance = rng.choice(_QTY_BARE_TEMPLATES).format(
            qty=pools.render_number(quantity, rng)
        )
    else:
        utterance = rng.choice(_QTY_PRONOUN_TEMPLATES).format(
            qty=pools.render_quantity(quantity, rng)
        )
    return utterance, make_response(
        modified_items=make_item(name=remembered, quantity=quantity)
    )


def build_item_discount_percent(rng: random.Random, item_name: str) -> Built:
    value = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    utterance = rng.choice(_ITEM_PERCENT_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        disc=pools.render_discount_percent(value, rng),
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, discount_percent=value)
    )


def build_item_discount_percent_pronoun(rng: random.Random, remembered: str) -> Built:
    value = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    utterance = rng.choice(_ITEM_PERCENT_PRONOUN_TEMPLATES).format(
        disc=pools.render_discount_percent(value, rng)
    )
    return utterance, make_response(
        modified_items=make_item(name=remembered, discount_percent=value)
    )


def build_item_discount_amount(rng: random.Random, item_name: str) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_ITEM_AMOUNT_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        disc=pools.render_discount_amount(value, rng),
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, discount_amount=value)
    )


def build_item_discount_amount_pronoun(rng: random.Random, remembered: str) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_ITEM_AMOUNT_PRONOUN_TEMPLATES).format(
        disc=pools.render_discount_amount(value, rng)
    )
    return utterance, make_response(
        modified_items=make_item(name=remembered, discount_amount=value)
    )


def build_rename(rng: random.Random, item_name: str) -> Built:
    new_name = pools.rename_target(item_name, rng)
    utterance = rng.choice(_RENAME_NAMED_TEMPLATES).format(
        old=pools.render_item(item_name, rng),
        new=pools.render_item(new_name, rng),
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, updated_item_name=new_name)
    )


def build_rename_pronoun(rng: random.Random, remembered: str) -> Built:
    new_name = pools.rename_target(remembered, rng)
    utterance = rng.choice(_RENAME_PRONOUN_TEMPLATES).format(
        new=pools.render_item(new_name, rng)
    )
    return utterance, make_response(
        modified_items=make_item(name=remembered, updated_item_name=new_name)
    )


def build_remove(rng: random.Random, item_name: str) -> Built:
    utterance = rng.choice(_REMOVE_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng)
    )
    return utterance, make_response(
        modified_items=make_item(name=item_name, remove_item=True)
    )


def build_remove_pronoun(rng: random.Random, remembered: str) -> Built:
    utterance = rng.choice(_REMOVE_PRONOUN_TEMPLATES)
    return utterance, make_response(
        modified_items=make_item(name=remembered, remove_item=True)
    )


# --------------------------------------------------------------------------
# Whole-bill discount
# --------------------------------------------------------------------------

_BILL_PERCENT_TEMPLATES = [
    "give {disc} off on the whole bill",
    "apply {disc} discount on the total",
    "total discount {disc}",
    "give {disc} discount on the full bill",
    "overall discount of {disc}",
    "on the whole bill give {disc}",
    "full bill {disc} discount",
    "make the total discount {disc}",
    "give {disc} on the entire invoice",
]

_BILL_AMOUNT_TEMPLATES = [
    "give {disc} off on the whole bill",
    "reduce {disc} from the total",
    "total discount {disc}",
    "overall discount of {disc}",
    "less {disc} from the bill",
    "reduce {disc} from the full bill",
    "make the total discount {disc}",
    "cut {disc} from the total amount",
]


def build_bill_discount_percent(rng: random.Random) -> Built:
    value = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    utterance = rng.choice(_BILL_PERCENT_TEMPLATES).format(
        disc=pools.render_discount_percent(value, rng)
    )
    return utterance, make_response(invoice_discount_percent=value)


def build_bill_discount_amount(rng: random.Random) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_BILL_AMOUNT_TEMPLATES).format(
        disc=pools.render_discount_amount(value, rng)
    )
    return utterance, make_response(invoice_discount_amount=value)


# --------------------------------------------------------------------------
# Date
# --------------------------------------------------------------------------

_DATE_TEMPLATES = [
    "bill date {date}",
    "make the date {date}",
    "invoice date {date}",
    "date should be {date}",
    "set the date as {date}",
    "put date {date}",
    "change the date to {date}",
    "bill date is {date}",
    "date {date}",
    "make bill date {date}",
    "the date is {date}",
    "invoice date should be {date}",
]

# Said only when a date is clearly already the topic, which is why these carry
# no "date" keyword and are used sparingly.
_DATE_BARE_TEMPLATES = [
    "make it {date}",
    "{date}",
    "no make it {date}",
    "change it to {date}",
]


def build_date(rng: random.Random, allow_bare: bool = False) -> Built:
    spoken, target = pools.render_date(rng)
    if allow_bare and rng.random() < 0.5:
        utterance = rng.choice(_DATE_BARE_TEMPLATES).format(date=spoken)
    else:
        utterance = rng.choice(_DATE_TEMPLATES).format(date=spoken)
    return utterance, make_response(invoice_date=target)


# --------------------------------------------------------------------------
# Clear, unknown, incomplete
# --------------------------------------------------------------------------

_CLEAR_TEMPLATES = [
    "clear invoice",
    "reset invoice",
    "clear the invoice",
    "clear the bill",
    "start a new bill",
    "reset the bill",
    "delete everything and start again",
    "clear everything",
    "new invoice",
    "wipe the invoice clean",
]


def build_clear(rng: random.Random) -> Built:
    return rng.choice(_CLEAR_TEMPLATES), make_response(clear_invoice=True)


def build_unknown(rng: random.Random) -> Built:
    return rng.choice(pools.UNKNOWN_UTTERANCES), make_response(unknown_input=True)


def build_incomplete(rng: random.Random) -> Built:
    return rng.choice(pools.INCOMPLETE_UTTERANCES), make_response(
        incomplete_input=True
    )
