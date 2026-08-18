"""Stock-item draft intents: name, quantity, cost, selling, clear, save."""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Tuple

import pools
from schema import make_action, make_response

Actions = List[Dict[str, Any]]
Built = Tuple[str, Actions]
TaggedBuilt = Tuple[str, str, Actions]

_NAME_TEMPLATES = [
    "add item {item}",
    "add {item}",
    "item name {item}",
    "item name is {item}",
    "new item {item}",
    "stock {item}",
    "add stock {item}",
    "put {item} in stock",
    "name is {item}",
    "next item {item}",
    "add item {item} please",
    "stock item {item}",
    "new stock {item}",
    "put {item}",
    "item is {item}",
    "add to stock {item}",
    "inventory {item}",
]

_QTY_TEMPLATES = [
    "quantity {qty}",
    "quantity is {qty}",
    "set quantity to {qty}",
    "make quantity {qty}",
    "{qty} in stock",
    "stock quantity {qty}",
    "we have {qty}",
    "units {qty}",
    "make stock {qty}",
    "qty {qty}",
    "opening stock {qty}",
    "available {qty}",
]

_COST_TEMPLATES = [
    "cost price {price}",
    "cost {price}",
    "cost is {price}",
    "set cost to {price}",
    "purchase price {price}",
    "bought at {price}",
    "cost price is {price}",
    "make cost {price}",
    "kharid {price}",
    "purchase {price}",
    "buying price {price}",
    "we bought at {price}",
]

_SELLING_TEMPLATES = [
    "selling price {price}",
    "selling {price}",
    "selling price is {price}",
    "set selling to {price}",
    "sell at {price}",
    "sale price {price}",
    "mrp {price}",
    "make selling price {price}",
    "bech {price}",
    "selling rate {price}",
    "we sell at {price}",
    "mark selling {price}",
]

_NAME_QTY_TEMPLATES = [
    "add {item} quantity {qty}",
    "add item {item} {qty}",
    "{qty} {item}",
    "put {qty} {item} in stock",
    "add {qty} {item}",
    "stock {item} quantity {qty}",
]

_NAME_COST_TEMPLATES = [
    "add {item} cost {price}",
    "item {item} cost price {price}",
    "add item {item} cost {price}",
    "add {item} bought at {price}",
]

_NAME_SELLING_TEMPLATES = [
    "add {item} selling {price}",
    "item {item} selling price {price}",
    "add {item} sell at {price}",
    "add {item} mrp {price}",
]

_QTY_COST_TEMPLATES = [
    "quantity {qty} cost {price}",
    "quantity {qty} cost price {price}",
    "{qty} in stock cost {price}",
]

_QTY_SELLING_TEMPLATES = [
    "quantity {qty} selling {price}",
    "quantity {qty} selling price {price}",
    "{qty} sell at {price}",
]

_COST_SELLING_TEMPLATES = [
    "cost {cost} selling {selling}",
    "cost price {cost} selling price {selling}",
    "bought at {cost} sell at {selling}",
    "kharid {cost} bech {selling}",
    "purchase {cost} mrp {selling}",
]

_NAME_COST_SELLING_TEMPLATES = [
    "add {item} cost {cost} selling {selling}",
    "item {item} cost price {cost} selling price {selling}",
    "add {item} bought at {cost} sell at {selling}",
]

_NAME_QTY_COST_TEMPLATES = [
    "add {item} quantity {qty} cost {cost}",
    "add {qty} {item} cost price {cost}",
    "stock {item} {qty} cost {cost}",
]

_NAME_QTY_SELLING_TEMPLATES = [
    "add {item} quantity {qty} selling {selling}",
    "add {qty} {item} sell at {selling}",
    "stock {item} {qty} mrp {selling}",
]

_QTY_COST_SELLING_TEMPLATES = [
    "quantity {qty} cost {cost} selling {selling}",
    "{qty} in stock cost {cost} selling {selling}",
]

_FULL_TEMPLATES = [
    "add {item} quantity {qty} cost {cost} selling {selling}",
    "add item {item} quantity {qty} cost price {cost} selling price {selling}",
    "add {qty} {item} cost {cost} selling {selling}",
    "stock {item} {qty} cost {cost} selling {selling}",
    "add {item} {qty} bought at {cost} sell at {selling}",
]

_AMBIGUOUS_PRICE_TEMPLATES = [
    "price {price}",
    "rate {price}",
    "make price {price}",
    "at {price}",
    "price is {price}",
    "make the price {price}",
    "set price to {price}",
    "rate is {price}",
]

_CLEAR_TEMPLATES = [
    "clear",
    "reset",
    "clear draft",
    "start again",
    "reset item",
    "clear the item",
    "wipe the draft",
    "clear this",
    "start over",
]

_SAVE_TEMPLATES = [
    "save",
    "save it",
    "save item",
    "save the item",
    "save stock",
    "okay save",
    "please save",
    "store the item",
    "save this item",
    "ok save it",
    "save to stock",
    "haan save kar do",
    "save this stock",
    "please save this now",
    "done save",
    "save item please",
    "store this in inventory",
    "keep this item",
    "save inventory",
]

INCOMPLETE_UTTERANCES = [
    "add item",
    "item name",
    "item name is",
    "cost price",
    "selling price",
    "quantity",
    "add uh",
    "add stock",
    "set cost",
    "set selling",
    "put the",
    "new item",
    "stock item",
    "bought at",
    "sell at",
    "mrp",
]

DOMAIN_UNKNOWN = [
    "add customer Rahul",
    "opening balance 500",
    "settled",
    "no dues",
    "paid",
    "all paid",
    "mark paid",
    "party name Ramesh",
    "bill to customer Priya",
    "customer is Amit",
    "give 10 percent discount on pens",
    "save the bill",
    "save invoice",
    "clear invoice",
    "bill date 25th June",
    "shop name is Mehta Electricals",
    "cut 50 rupees from the total",
    "give five percent off on the whole bill",
    "customer name Priya Sharma",
    "they owe 1200",
    "add paneer to the bill",
    "remove the pens",
    "udhaar 200",
]


def _pick_item(rng: random.Random) -> Tuple[str, str]:
    item = pools.pick_item(rng)
    return item, pools.render_item(item, rng)


def build_name(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    utterance = rng.choice(_NAME_TEMPLATES).format(item=spoken)
    return utterance, make_response(make_action("SET_NAME", name=item))


def build_quantity(rng: random.Random) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    utterance = rng.choice(_QTY_TEMPLATES).format(
        qty=pools.render_quantity(quantity, rng)
    )
    return utterance, make_response(make_action("SET_QUANTITY", quantity=quantity))


def build_cost(rng: random.Random) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_COST_TEMPLATES).format(price=pools.render_price(price, rng))
    return utterance, make_response(make_action("SET_COST", costPrice=price))


def build_selling(rng: random.Random) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_SELLING_TEMPLATES).format(
        price=pools.render_price(price, rng)
    )
    return utterance, make_response(make_action("SET_SELLING", sellingPrice=price))


def build_name_quantity(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    quantity = rng.choice(pools.QUANTITY_VALUES)
    utterance = rng.choice(_NAME_QTY_TEMPLATES).format(
        item=spoken, qty=pools.render_quantity(quantity, rng)
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_QUANTITY", quantity=quantity),
    )


def build_name_cost(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_COST_TEMPLATES).format(
        item=spoken, price=pools.render_price(price, rng)
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_COST", costPrice=price),
    )


def build_name_selling(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_SELLING_TEMPLATES).format(
        item=spoken, price=pools.render_price(price, rng)
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_SELLING", sellingPrice=price),
    )


def build_quantity_cost(rng: random.Random) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_QTY_COST_TEMPLATES).format(
        qty=pools.render_quantity(quantity, rng),
        price=pools.render_price(price, rng),
    )
    return utterance, make_response(
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_COST", costPrice=price),
    )


def build_quantity_selling(rng: random.Random) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_QTY_SELLING_TEMPLATES).format(
        qty=pools.render_quantity(quantity, rng),
        price=pools.render_price(price, rng),
    )
    return utterance, make_response(
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_SELLING", sellingPrice=price),
    )


def build_cost_selling(rng: random.Random) -> Built:
    cost = rng.choice(pools.PRICE_VALUES)
    selling = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_COST_SELLING_TEMPLATES).format(
        cost=pools.render_price(cost, rng),
        selling=pools.render_price(selling, rng),
    )
    return utterance, make_response(
        make_action("SET_COST", costPrice=cost),
        make_action("SET_SELLING", sellingPrice=selling),
    )


def build_name_cost_selling(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    cost = rng.choice(pools.PRICE_VALUES)
    selling = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_COST_SELLING_TEMPLATES).format(
        item=spoken,
        cost=pools.render_price(cost, rng),
        selling=pools.render_price(selling, rng),
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_COST", costPrice=cost),
        make_action("SET_SELLING", sellingPrice=selling),
    )


def build_name_quantity_cost(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    quantity = rng.choice(pools.QUANTITY_VALUES)
    cost = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_QTY_COST_TEMPLATES).format(
        item=spoken,
        qty=pools.render_quantity(quantity, rng),
        cost=pools.render_price(cost, rng),
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_COST", costPrice=cost),
    )


def build_name_quantity_selling(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    quantity = rng.choice(pools.QUANTITY_VALUES)
    selling = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_NAME_QTY_SELLING_TEMPLATES).format(
        item=spoken,
        qty=pools.render_quantity(quantity, rng),
        selling=pools.render_price(selling, rng),
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_SELLING", sellingPrice=selling),
    )


def build_quantity_cost_selling(rng: random.Random) -> Built:
    quantity = rng.choice(pools.QUANTITY_VALUES)
    cost = rng.choice(pools.PRICE_VALUES)
    selling = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_QTY_COST_SELLING_TEMPLATES).format(
        qty=pools.render_quantity(quantity, rng),
        cost=pools.render_price(cost, rng),
        selling=pools.render_price(selling, rng),
    )
    return utterance, make_response(
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_COST", costPrice=cost),
        make_action("SET_SELLING", sellingPrice=selling),
    )


def build_full(rng: random.Random) -> Built:
    item, spoken = _pick_item(rng)
    quantity = rng.choice(pools.QUANTITY_VALUES)
    cost = rng.choice(pools.PRICE_VALUES)
    selling = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_FULL_TEMPLATES).format(
        item=spoken,
        qty=pools.render_quantity(quantity, rng),
        cost=pools.render_price(cost, rng),
        selling=pools.render_price(selling, rng),
    )
    return utterance, make_response(
        make_action("SET_NAME", name=item),
        make_action("SET_QUANTITY", quantity=quantity),
        make_action("SET_COST", costPrice=cost),
        make_action("SET_SELLING", sellingPrice=selling),
    )


def build_ambiguous_price(rng: random.Random) -> Built:
    price = rng.choice(pools.PRICE_VALUES)
    utterance = rng.choice(_AMBIGUOUS_PRICE_TEMPLATES).format(
        price=pools.render_price(price, rng)
    )
    return utterance, make_response(make_action("INCOMPLETE"))


def build_clear(rng: random.Random) -> Built:
    return rng.choice(_CLEAR_TEMPLATES), make_response(make_action("CLEAR"))


def build_save(rng: random.Random) -> Built:
    return rng.choice(_SAVE_TEMPLATES), make_response(make_action("SAVE"))


def build_unknown(rng: random.Random) -> Built:
    pool = DOMAIN_UNKNOWN if rng.random() < 0.45 else pools.UNKNOWN_UTTERANCES
    return rng.choice(pool), make_response(make_action("UNKNOWN"))


def build_incomplete(rng: random.Random) -> Built:
    if rng.random() < 0.35:
        return build_ambiguous_price(rng)
    return rng.choice(INCOMPLETE_UTTERANCES), make_response(make_action("INCOMPLETE"))


_COMBO_BUILDERS: List[Tuple[str, Callable[[random.Random], Built]]] = [
    ("combo_name_qty", build_name_quantity),
    ("combo_name_cost", build_name_cost),
    ("combo_name_selling", build_name_selling),
    ("combo_qty_cost", build_quantity_cost),
    ("combo_qty_selling", build_quantity_selling),
    ("combo_cost_selling", build_cost_selling),
    ("combo_name_cost_selling", build_name_cost_selling),
    ("combo_name_qty_cost", build_name_quantity_cost),
    ("combo_name_qty_selling", build_name_quantity_selling),
    ("combo_qty_cost_selling", build_quantity_cost_selling),
    ("combo_full", build_full),
]


def build_combo(rng: random.Random) -> TaggedBuilt:
    tag, builder = rng.choice(_COMBO_BUILDERS)
    utterance, response = builder(rng)
    return tag, utterance, response


STOCK_FOLLOWUPS: List[Tuple[str, Callable[[random.Random], Built]]] = [
    ("name", build_name),
    ("quantity", build_quantity),
    ("cost", build_cost),
    ("selling", build_selling),
]
