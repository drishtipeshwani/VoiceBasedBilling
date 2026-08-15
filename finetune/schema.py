"""Canonical shape of the agent response.

Mirrors AgentResponseSchema in types/agentResponse.ts. Key order is fixed here
so every target in the dataset serialises identically and the model never
spends loss on formatting variation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

ITEM_KEYS = (
    "name",
    "updatedItemName",
    "quantity",
    "pricePerItem",
    "discountPercent",
    "discountAmount",
    "removeItem",
)

RESPONSE_KEYS = (
    "modifiedCompanyName",
    "modifiedCustomerName",
    "modifiedItems",
    "invoiceDiscountPercent",
    "invoiceDiscountAmount",
    "invoiceDate",
    "clearInvoice",
    "unknownInput",
    "incompleteInput",
)


def make_item(
    name: Optional[str] = None,
    updated_item_name: Optional[str] = None,
    quantity: Optional[float] = None,
    price_per_item: Optional[float] = None,
    discount_percent: Optional[float] = None,
    discount_amount: Optional[float] = None,
    remove_item: bool = False,
) -> Dict[str, Any]:
    return {
        "name": name,
        "updatedItemName": updated_item_name,
        "quantity": quantity,
        "pricePerItem": price_per_item,
        "discountPercent": discount_percent,
        "discountAmount": discount_amount,
        "removeItem": remove_item,
    }


def make_response(
    modified_company_name: Optional[str] = None,
    modified_customer_name: Optional[str] = None,
    modified_items: Optional[Dict[str, Any]] = None,
    invoice_discount_percent: Optional[float] = None,
    invoice_discount_amount: Optional[float] = None,
    invoice_date: Optional[str] = None,
    clear_invoice: bool = False,
    unknown_input: bool = False,
    incomplete_input: bool = False,
) -> Dict[str, Any]:
    return {
        "modifiedCompanyName": modified_company_name,
        "modifiedCustomerName": modified_customer_name,
        "modifiedItems": modified_items,
        "invoiceDiscountPercent": invoice_discount_percent,
        "invoiceDiscountAmount": invoice_discount_amount,
        "invoiceDate": invoice_date,
        "clearInvoice": clear_invoice,
        "unknownInput": unknown_input,
        "incompleteInput": incomplete_input,
    }


def dumps(value: Any) -> str:
    """Compact JSON with no spaces, matching what the model must emit."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def remembered_item_name(last_modified: Optional[Dict[str, Any]]) -> Optional[str]:
    """The item name carried by a previous response, if it has one."""
    if not last_modified:
        return None
    item = last_modified.get("modifiedItems")
    if not item:
        return None
    return item.get("updatedItemName") or item.get("name")
