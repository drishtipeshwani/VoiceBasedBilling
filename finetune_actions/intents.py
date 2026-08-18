"""Intent builders: one spoken utterance plus the actions array it must produce.

Each builder returns (utterance, actions). Builders that can be phrased
without naming the item take an `item_name` of None to mean "say it with a
pronoun", which is only legal when the caller has a remembered item.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

import pools
from schema import make_action, make_response

Actions = List[Dict[str, Any]]
Built = Tuple[str, Actions]

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
    return utterance, make_response(make_action("SET_COMPANY", companyName=name))


def build_customer(rng: random.Random) -> Built:
    name = rng.choice(pools.CUSTOMER_NAMES)
    utterance = rng.choice(_CUSTOMER_TEMPLATES).format(name=name)
    return utterance, make_response(make_action("SET_CUSTOMER", customerName=name))


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
        return utterance, make_response(make_action("ADD_ITEM", name=item))

    if roll < 0.55:
        quantity = rng.choice(pools.QUANTITY_VALUES)
        utterance = rng.choice(_ADD_QTY_TEMPLATES).format(
            item=spoken, qty=pools.render_quantity(quantity, rng)
        )
        return utterance, make_response(
            make_action("ADD_ITEM", name=item, quantity=quantity)
        )

    if roll < 0.7:
        price = rng.choice(pools.PRICE_VALUES)
        utterance = rng.choice(_ADD_PRICE_TEMPLATES).format(
            item=spoken, price=pools.render_price(price, rng)
        )
        return utterance, make_response(
            make_action("ADD_ITEM", name=item, pricePerItem=price)
        )

    quantity = rng.choice(pools.QUANTITY_VALUES)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_ADD_FULL_TEMPLATES).format(
        item=spoken,
        qty=pools.render_quantity(quantity, rng),
        price=pools.render_price(price, rng),
    )
    return utterance, make_response(
        make_action("ADD_ITEM", name=item, quantity=quantity, pricePerItem=price)
    )


# --------------------------------------------------------------------------
# Updating an existing item
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
        make_action("SET_PRICE", name=item_name, pricePerItem=price)
    )


def build_price_pronoun(rng: random.Random, remembered: str) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_PRICE_PRONOUN_TEMPLATES).format(
        price=pools.render_price(price, rng)
    )
    return utterance, make_response(
        make_action("SET_PRICE", name=remembered, pricePerItem=price)
    )


def build_quantity(rng: random.Random, item_name: str) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    utterance = rng.choice(_QTY_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        qty=pools.render_quantity(quantity, rng),
    )
    return utterance, make_response(
        make_action("SET_QUANTITY", name=item_name, quantity=quantity)
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
        utterance = rng.choice(_QTY_BARE_TEMPLATES).format(
            qty=pools.render_number(quantity, rng)
        )
    else:
        utterance = rng.choice(_QTY_PRONOUN_TEMPLATES).format(
            qty=pools.render_quantity(quantity, rng)
        )
    return utterance, make_response(
        make_action("SET_QUANTITY", name=remembered, quantity=quantity)
    )


def build_item_discount_percent(rng: random.Random, item_name: str) -> Built:
    value = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    utterance = rng.choice(_ITEM_PERCENT_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        disc=pools.render_discount_percent(value, rng),
    )
    return utterance, make_response(
        make_action("SET_ITEM_DISCOUNT", name=item_name, discountPercent=value)
    )


def build_item_discount_percent_pronoun(rng: random.Random, remembered: str) -> Built:
    value = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    utterance = rng.choice(_ITEM_PERCENT_PRONOUN_TEMPLATES).format(
        disc=pools.render_discount_percent(value, rng)
    )
    return utterance, make_response(
        make_action("SET_ITEM_DISCOUNT", name=remembered, discountPercent=value)
    )


def build_item_discount_amount(rng: random.Random, item_name: str) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_ITEM_AMOUNT_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng),
        disc=pools.render_discount_amount(value, rng),
    )
    return utterance, make_response(
        make_action("SET_ITEM_DISCOUNT", name=item_name, discountAmount=value)
    )


def build_item_discount_amount_pronoun(rng: random.Random, remembered: str) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_ITEM_AMOUNT_PRONOUN_TEMPLATES).format(
        disc=pools.render_discount_amount(value, rng)
    )
    return utterance, make_response(
        make_action("SET_ITEM_DISCOUNT", name=remembered, discountAmount=value)
    )


def build_rename(rng: random.Random, item_name: str) -> Built:
    new_name = pools.rename_target(item_name, rng)
    utterance = rng.choice(_RENAME_NAMED_TEMPLATES).format(
        old=pools.render_item(item_name, rng),
        new=pools.render_item(new_name, rng),
    )
    return utterance, make_response(
        make_action("RENAME_ITEM", name=item_name, updatedItemName=new_name)
    )


def build_rename_pronoun(rng: random.Random, remembered: str) -> Built:
    new_name = pools.rename_target(remembered, rng)
    utterance = rng.choice(_RENAME_PRONOUN_TEMPLATES).format(
        new=pools.render_item(new_name, rng)
    )
    return utterance, make_response(
        make_action("RENAME_ITEM", name=remembered, updatedItemName=new_name)
    )


def build_remove(rng: random.Random, item_name: str) -> Built:
    utterance = rng.choice(_REMOVE_NAMED_TEMPLATES).format(
        item=pools.render_item(item_name, rng)
    )
    return utterance, make_response(make_action("DELETE_ITEM", name=item_name))


def build_remove_pronoun(rng: random.Random, remembered: str) -> Built:
    utterance = rng.choice(_REMOVE_PRONOUN_TEMPLATES)
    return utterance, make_response(make_action("DELETE_ITEM", name=remembered))


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
    return utterance, make_response(
        make_action("SET_INVOICE_DISCOUNT", invoiceDiscountPercent=value)
    )


def build_bill_discount_amount(rng: random.Random) -> Built:
    value = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    utterance = rng.choice(_BILL_AMOUNT_TEMPLATES).format(
        disc=pools.render_discount_amount(value, rng)
    )
    return utterance, make_response(
        make_action("SET_INVOICE_DISCOUNT", invoiceDiscountAmount=value)
    )


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
    return utterance, make_response(make_action("SET_DATE", invoiceDate=target))


# --------------------------------------------------------------------------
# Clear, save, unknown, incomplete
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

_SAVE_TEMPLATES = [
    "save invoice",
    "save the invoice",
    "save the bill",
    "save it",
    "save this bill",
    "please save",
    "save this invoice",
    "store the invoice",
    "save bill",
    "okay save it",
]


def build_clear(rng: random.Random) -> Built:
    return rng.choice(_CLEAR_TEMPLATES), make_response(make_action("CLEAR_INVOICE"))


def build_save(rng: random.Random) -> Built:
    return rng.choice(_SAVE_TEMPLATES), make_response(make_action("SAVE_INVOICE"))


def build_unknown(rng: random.Random) -> Built:
    return rng.choice(pools.UNKNOWN_UTTERANCES), make_response(make_action("UNKNOWN"))


def build_incomplete(rng: random.Random) -> Built:
    return rng.choice(pools.INCOMPLETE_UTTERANCES), make_response(
        make_action("INCOMPLETE")
    )


# --------------------------------------------------------------------------
# Combinations: more than one action in a single utterance
# --------------------------------------------------------------------------

_TWO_ADD_TEMPLATES = [
    "add {a} add {b}",
    "add {a} and {b}",
    "add item {a} and add {b}",
    "put {a} and {b} in the bill",
    "add {a} also add {b}",
    "next {a} and {b}",
]

_QTY_PRICE_TEMPLATES = [
    "{item} quantity {qty} price {price}",
    "make {item} quantity {qty} rate {price}",
    "set {item} to {qty} at {price}",
    "{item} {qty} at {price}",
    "change {item} quantity {qty} price {price}",
]

_TWO_ITEM_DISCOUNT_TEMPLATES = [
    "give {disc_a} off on {a} and {disc_b} off on {b}",
    "{a} discount {disc_a} and {b} discount {disc_b}",
    "apply {disc_a} on {a} and {disc_b} on {b}",
    "give {disc_a} discount on {a} and {disc_b} on {b}",
]

_CUSTOMER_ADD_TEMPLATES = [
    "customer {customer} add {item}",
    "bill to {customer} add item {item}",
    "customer name {customer} put {item} in the bill",
    "this bill is for {customer} add {item}",
]


def build_combo_two_add(rng: random.Random) -> Built:
    first = pools.pick_item(rng)
    second = pools.pick_other_item(first, rng)
    utterance = rng.choice(_TWO_ADD_TEMPLATES).format(
        a=pools.render_item(first, rng),
        b=pools.render_item(second, rng),
    )
    return utterance, make_response(
        make_action("ADD_ITEM", name=first),
        make_action("ADD_ITEM", name=second),
    )


def build_combo_qty_price(rng: random.Random) -> Built:
    item = pools.pick_item(rng)
    quantity = rng.choice(pools.QUANTITY_VALUES)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_QTY_PRICE_TEMPLATES).format(
        item=pools.render_item(item, rng),
        qty=pools.render_quantity(quantity, rng),
        price=pools.render_price(price, rng),
    )
    return utterance, make_response(
        make_action("SET_QUANTITY", name=item, quantity=quantity),
        make_action("SET_PRICE", name=item, pricePerItem=price),
    )


def build_combo_two_item_discounts(rng: random.Random) -> Built:
    first = pools.pick_item(rng)
    second = pools.pick_other_item(first, rng)
    percent = rng.choice(pools.DISCOUNT_PERCENT_VALUES)
    amount = rng.choice(pools.DISCOUNT_AMOUNT_VALUES)
    if rng.random() < 0.5:
        utterance = rng.choice(_TWO_ITEM_DISCOUNT_TEMPLATES).format(
            a=pools.render_item(first, rng),
            b=pools.render_item(second, rng),
            disc_a=pools.render_discount_percent(percent, rng),
            disc_b=pools.render_discount_amount(amount, rng),
        )
        return utterance, make_response(
            make_action("SET_ITEM_DISCOUNT", name=first, discountPercent=percent),
            make_action("SET_ITEM_DISCOUNT", name=second, discountAmount=amount),
        )
    utterance = rng.choice(_TWO_ITEM_DISCOUNT_TEMPLATES).format(
        a=pools.render_item(first, rng),
        b=pools.render_item(second, rng),
        disc_a=pools.render_discount_amount(amount, rng),
        disc_b=pools.render_discount_percent(percent, rng),
    )
    return utterance, make_response(
        make_action("SET_ITEM_DISCOUNT", name=first, discountAmount=amount),
        make_action("SET_ITEM_DISCOUNT", name=second, discountPercent=percent),
    )


def build_combo_customer_add(rng: random.Random) -> Built:
    customer = rng.choice(pools.CUSTOMER_NAMES)
    item = pools.pick_item(rng)
    utterance = rng.choice(_CUSTOMER_ADD_TEMPLATES).format(
        customer=customer,
        item=pools.render_item(item, rng),
    )
    return utterance, make_response(
        make_action("SET_CUSTOMER", customerName=customer),
        make_action("ADD_ITEM", name=item),
    )


COMBO_BUILDERS = (
    ("combo_two_add", build_combo_two_add),
    ("combo_qty_price", build_combo_qty_price),
    ("combo_two_item_discounts", build_combo_two_item_discounts),
    ("combo_customer_add", build_combo_customer_add),
)


def build_combo(rng: random.Random) -> Tuple[str, str, Actions]:
    tag, builder = rng.choice(COMBO_BUILDERS)
    utterance, response = builder(rng)
    return tag, utterance, response
