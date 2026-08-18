"""Canonical shape of the action-array agent response.

Mirrors AgentActionResponseSchema in types/agentActionResponse.ts.
Actions are sparse: only `action` plus the invoice fields that utterance set.
Key order is fixed so every target serialises identically.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

TASKS = ("invoice", "customer", "stock")

INVOICE_ACTIONS = (
    "ADD_ITEM",
    "DELETE_ITEM",
    "SET_PRICE",
    "SET_QUANTITY",
    "RENAME_ITEM",
    "SET_ITEM_DISCOUNT",
    "SET_INVOICE_DISCOUNT",
    "SET_DATE",
    "SET_CUSTOMER",
    "SET_COMPANY",
    "CLEAR_INVOICE",
    "SAVE_INVOICE",
    "UNKNOWN",
    "INCOMPLETE",
)

CUSTOMER_ACTIONS = (
    "SET_NAME",
    "SET_BALANCE",
    "CLEAR",
    "SAVE",
    "UNKNOWN",
    "INCOMPLETE",
)

STOCK_ACTIONS = (
    "SET_NAME",
    "SET_QUANTITY",
    "SET_COST",
    "SET_SELLING",
    "CLEAR",
    "SAVE",
    "UNKNOWN",
    "INCOMPLETE",
)

ACTIONS = tuple(dict.fromkeys(INVOICE_ACTIONS + CUSTOMER_ACTIONS + STOCK_ACTIONS))

TASK_ACTIONS = {
    "invoice": set(INVOICE_ACTIONS),
    "customer": set(CUSTOMER_ACTIONS),
    "stock": set(STOCK_ACTIONS),
}

ITEM_ACTIONS = {
    "ADD_ITEM",
    "SET_PRICE",
    "SET_QUANTITY",
    "RENAME_ITEM",
    "SET_ITEM_DISCOUNT",
}

BARE_ACTIONS = {
    "CLEAR_INVOICE",
    "SAVE_INVOICE",
    "CLEAR",
    "SAVE",
    "UNKNOWN",
    "INCOMPLETE",
}

FIELD_ORDER = (
    "action",
    "name",
    "updatedItemName",
    "quantity",
    "pricePerItem",
    "discountPercent",
    "discountAmount",
    "companyName",
    "customerName",
    "invoiceDate",
    "invoiceDiscountPercent",
    "invoiceDiscountAmount",
    "balanceAmount",
    "costPrice",
    "sellingPrice",
)

REQUIRED_FIELDS = {
    "ADD_ITEM": ("name",),
    "DELETE_ITEM": ("name",),
    "SET_PRICE": ("name", "pricePerItem"),
    "SET_QUANTITY": ("quantity",),
    "RENAME_ITEM": ("name", "updatedItemName"),
    "SET_ITEM_DISCOUNT": ("name",),
    "SET_INVOICE_DISCOUNT": (),
    "SET_DATE": ("invoiceDate",),
    "SET_CUSTOMER": ("customerName",),
    "SET_COMPANY": ("companyName",),
    "CLEAR_INVOICE": (),
    "SAVE_INVOICE": (),
    "SET_NAME": ("name",),
    "SET_BALANCE": ("balanceAmount",),
    "SET_COST": ("costPrice",),
    "SET_SELLING": ("sellingPrice",),
    "CLEAR": (),
    "SAVE": (),
    "UNKNOWN": (),
    "INCOMPLETE": (),
}

REQUIRED_FIELDS_BY_TASK = {
    "invoice": {
        **REQUIRED_FIELDS,
        "SET_QUANTITY": ("name", "quantity"),
    },
    "customer": {action: REQUIRED_FIELDS[action] for action in CUSTOMER_ACTIONS},
    "stock": {action: REQUIRED_FIELDS[action] for action in STOCK_ACTIONS},
}

OPTIONAL_FIELDS = {
    "ADD_ITEM": ("quantity", "pricePerItem", "discountPercent", "discountAmount"),
    "SET_ITEM_DISCOUNT": ("discountPercent", "discountAmount"),
    "SET_INVOICE_DISCOUNT": ("invoiceDiscountPercent", "invoiceDiscountAmount"),
}


def make_action(action: str, **fields: Any) -> Dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    payload: Dict[str, Any] = {"action": action}
    for key, value in fields.items():
        if value is None:
            continue
        if key not in FIELD_ORDER:
            raise ValueError(f"unknown field {key!r} for action {action}")
        payload[key] = value
    return {key: payload[key] for key in FIELD_ORDER if key in payload}


def make_response(*actions: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not actions:
        raise ValueError("response must contain at least one action")
    return list(actions)


def dumps(value: Any) -> str:
    """Compact JSON with no spaces, matching what the model must emit."""

    def order_action(action: Dict[str, Any]) -> Dict[str, Any]:
        return {key: action[key] for key in FIELD_ORDER if key in action}

    if isinstance(value, list):
        return json.dumps(
            [order_action(action) for action in value],
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def remembered_item_name(last_modified: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """The item a pronoun may attach to, read from the previous actions array."""
    if not last_modified:
        return None
    for action in reversed(last_modified):
        kind = action.get("action")
        if kind in ("DELETE_ITEM", "CLEAR_INVOICE"):
            return None
        if kind == "RENAME_ITEM":
            return action.get("updatedItemName") or action.get("name")
        if kind in ITEM_ACTIONS:
            return action.get("name")
    return None
