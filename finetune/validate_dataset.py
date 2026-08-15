#!/usr/bin/env python3
"""Validate dataset rows and report coverage.

The important check is the last one: an item name in the target must either be
audible in the transcript or be inherited from lastModified. Anything else is a
row that teaches the model to invent an item, which is the exact failure the
app's logs already show.

Usage:
    python3 finetune/validate_dataset.py finetune/data/*.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import ITEM_KEYS, RESPONSE_KEYS, remembered_item_name  # noqa: E402
from pools import (  # noqa: E402
    MONTH_ABBREVIATIONS,
    _LETTER_SOUNDS,
    canonicalize_invoice_date,
)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


_SOUND_TO_LETTER = {sound: letter.lower() for letter, sound in _LETTER_SOUNDS.items()}
# Multi-word sounds first so "double you" collapses before "you".
_SOUND_PATTERN = re.compile(
    r"\b("
    + "|".join(
        re.escape(sound)
        for sound in sorted(_SOUND_TO_LETTER, key=len, reverse=True)
    )
    + r")\b",
    re.IGNORECASE,
)


def _squash_with_letter_sounds(text: str) -> str:
    """Like _squash, but 'em ex 96' becomes 'mx96' so spelled codes match."""

    def repl(match: re.Match[str]) -> str:
        return _SOUND_TO_LETTER[match.group(0).lower()]

    return _squash(_SOUND_PATTERN.sub(repl, text))


def check_row(row: Dict[str, Any], index: int, source: str) -> List[str]:
    where = f"{source}:{index}"
    problems: List[str] = []

    for key in ("lastModified", "userInput", "agentOutput"):
        if key not in row:
            problems.append(f"{where} missing key {key}")
    if problems:
        return problems

    output = row["agentOutput"]
    if tuple(output.keys()) != RESPONSE_KEYS:
        problems.append(f"{where} response keys wrong or out of order")

    if not isinstance(row["userInput"], str) or not row["userInput"].strip():
        problems.append(f"{where} empty userInput")

    percent = output.get("invoiceDiscountPercent")
    if percent is not None and not (0 <= percent <= 100):
        problems.append(f"{where} invoiceDiscountPercent out of range: {percent}")
    if percent is not None and output.get("invoiceDiscountAmount") is not None:
        problems.append(f"{where} both invoice discount kinds set")

    date = output.get("invoiceDate")
    if date is not None and (not isinstance(date, str) or not date.strip()):
        problems.append(f"{where} invoiceDate is empty")
    if isinstance(date, str):
        abbrevs = {
            a.lower()
            for names in MONTH_ABBREVIATIONS.values()
            for a in names
        }
        for token in re.findall(r"[A-Za-z]+", date):
            if token.lower() in abbrevs:
                problems.append(
                    f"{where} invoiceDate uses abbreviated month {token!r}; "
                    f"expected full name (e.g. {canonicalize_invoice_date(date)!r})"
                )
                break

    flags = [
        output.get("clearInvoice"),
        output.get("unknownInput"),
        output.get("incompleteInput"),
    ]
    if sum(1 for flag in flags if flag) > 1:
        problems.append(f"{where} more than one of clear/unknown/incomplete")

    if output.get("unknownInput") or output.get("incompleteInput"):
        payload_keys = [
            "modifiedCompanyName",
            "modifiedCustomerName",
            "modifiedItems",
            "invoiceDiscountPercent",
            "invoiceDiscountAmount",
            "invoiceDate",
        ]
        if any(output.get(key) is not None for key in payload_keys):
            problems.append(f"{where} unknown/incomplete row also carries a payload")

    item = output.get("modifiedItems")
    if item is not None:
        if tuple(item.keys()) != ITEM_KEYS:
            problems.append(f"{where} item keys wrong or out of order")

        item_percent = item.get("discountPercent")
        if item_percent is not None and not (0 <= item_percent <= 100):
            problems.append(f"{where} discountPercent out of range: {item_percent}")
        if item_percent is not None and item.get("discountAmount") is not None:
            problems.append(f"{where} both item discount kinds set")

        if item.get("removeItem") and not item.get("name"):
            problems.append(f"{where} removeItem without a name")
        if item.get("updatedItemName") and not item.get("name"):
            problems.append(f"{where} updatedItemName without a name")

        if not any(item.get(key) is not None for key in ITEM_KEYS[:-1]) and not item.get(
            "removeItem"
        ):
            problems.append(f"{where} modifiedItems set but entirely empty")

        name = item.get("name")
        if name:
            heard = set(_tokens(row["userInput"]))
            name_tokens = [t for t in _tokens(name) if len(t) > 2]
            audible = any(token in heard for token in name_tokens) if name_tokens else False
            if not audible:
                # Model codes survive as "ad212" with no space, so compare with
                # separators stripped before deciding the name was invented.
                # Also map spelled letters ("em ex 96") onto "mx96".
                audible = _squash(name) in _squash_with_letter_sounds(
                    row["userInput"]
                )
            inherited = remembered_item_name(row["lastModified"])
            if not audible and name != inherited:
                problems.append(
                    f"{where} item {name!r} is neither in the transcript nor in context"
                    f" (context item: {inherited!r})"
                )

    return problems


def coverage(rows: List[Dict[str, Any]]) -> None:
    fields = Counter()
    tags = Counter()
    date_shapes = Counter()
    context = Counter()

    for row in rows:
        output = row["agentOutput"]
        for key in RESPONSE_KEYS:
            value = output.get(key)
            if value not in (None, False):
                fields[key] += 1

        item = output.get("modifiedItems")
        if item:
            for key in ITEM_KEYS:
                value = item.get(key)
                if value not in (None, False):
                    fields[f"modifiedItems.{key}"] += 1

        for tag in row.get("meta", {}).get("tags", []):
            tags[tag] += 1

        date = output.get("invoiceDate")
        if date:
            if re.fullmatch(r"\d{1,2}(st|nd|rd|th)", date):
                date_shapes["bare day"] += 1
            elif re.search(r"\d{2,4}$", date):
                date_shapes["day month year"] += 1
            elif re.search(r"[A-Za-z]", date) and re.search(r"\d", date):
                date_shapes["day month"] += 1
            else:
                date_shapes["relative"] += 1

        context["with context" if row["lastModified"] else "cold start"] += 1

    print(f"\nrows: {len(rows)}")
    print("\nfield coverage")
    for key, count in sorted(fields.items(), key=lambda kv: -kv[1]):
        print(f"  {key:<34} {count:>5}  {count / len(rows):>6.1%}")

    print("\ndate shapes")
    total_dates = sum(date_shapes.values()) or 1
    for key, count in date_shapes.most_common():
        print(f"  {key:<34} {count:>5}  {count / total_dates:>6.1%} of dated rows")

    print("\ncontext")
    for key, count in context.most_common():
        print(f"  {key:<34} {count:>5}  {count / len(rows):>6.1%}")

    print("\ntags")
    for key, count in tags.most_common():
        print(f"  {key:<34} {count:>5}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument(
        "--holdout",
        help="File whose (lastModified, userInput) pairs must not appear in paths",
    )
    args = parser.parse_args()

    expanded: List[str] = []
    for path in args.paths:
        expanded.extend(sorted(glob.glob(path)) or [path])

    all_rows: List[Dict[str, Any]] = []
    problems: List[str] = []

    for path in expanded:
        with open(path, encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                all_rows.append(row)
                problems.extend(check_row(row, index, os.path.basename(path)))

    seen = Counter()
    for row in all_rows:
        seen[(json.dumps(row["lastModified"], sort_keys=True), row["userInput"])] += 1
    duplicates = sum(count - 1 for count in seen.values() if count > 1)
    if duplicates:
        problems.append(f"{duplicates} duplicate (lastModified, userInput) pairs")

    if args.holdout:
        with open(args.holdout, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = (
                    json.dumps(row["lastModified"], sort_keys=True),
                    row["userInput"],
                )
                if key in seen:
                    problems.append(f"holdout row leaked into training: {row['userInput']!r}")

    coverage(all_rows)

    print()
    if problems:
        print(f"FAILED: {len(problems)} problems")
        for problem in problems[:40]:
            print(f"  {problem}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        sys.exit(1)

    print(f"OK: {len(all_rows)} rows valid")


if __name__ == "__main__":
    main()
