#!/usr/bin/env python3
"""Validate action-array dataset rows and report coverage.

An item name in a target action must either be audible in the transcript or
be inherited from lastModified. Anything else teaches the model to invent items.

Usage:
    python3 finetune_actions/validate_dataset.py finetune_actions/data/*.jsonl
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

from schema import (  # noqa: E402
    ACTIONS,
    BARE_ACTIONS,
    FIELD_ORDER,
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS_BY_TASK,
    TASK_ACTIONS,
    remembered_item_name,
)
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
    def repl(match: re.Match[str]) -> str:
        return _SOUND_TO_LETTER[match.group(0).lower()]

    without_dash = re.sub(r"\bdash\b", "", text, flags=re.IGNORECASE)
    return _squash(_SOUND_PATTERN.sub(repl, without_dash))


def _name_is_audible(name: str, transcript: str) -> bool:
    heard = set(_tokens(transcript))
    name_tokens = [token for token in _tokens(name) if len(token) > 2]
    if name_tokens and any(token in heard for token in name_tokens):
        return True
    return _squash(name) in _squash_with_letter_sounds(transcript)


def check_action(
    action: Dict[str, Any], where: str, index: int, task: str = "invoice"
) -> List[str]:
    problems: List[str] = []
    prefix = f"{where} action[{index}]"
    kind = action.get("action")
    allowed_actions = TASK_ACTIONS.get(task, TASK_ACTIONS["invoice"])
    if kind not in ACTIONS:
        problems.append(f"{prefix} unknown action {kind!r}")
        return problems
    if kind not in allowed_actions:
        problems.append(f"{prefix} action {kind!r} is not valid for task {task}")
        return problems

    ordered = tuple(key for key in FIELD_ORDER if key in action)
    if tuple(action.keys()) != ordered:
        problems.append(f"{prefix} keys out of order: {list(action.keys())}")

    extra = set(action) - set(FIELD_ORDER)
    if extra:
        problems.append(f"{prefix} unexpected keys {sorted(extra)}")

    required = REQUIRED_FIELDS_BY_TASK.get(task, REQUIRED_FIELDS_BY_TASK["invoice"]).get(
        kind, ()
    )
    optional = OPTIONAL_FIELDS.get(kind, ())
    allowed_keys = {"action"} | set(required) | set(optional)
    unexpected = set(action) - allowed_keys
    if unexpected:
        problems.append(f"{prefix} keys not allowed for {kind}: {sorted(unexpected)}")

    for field in required:
        if field not in action:
            problems.append(f"{prefix} missing required {field}")

    if kind in BARE_ACTIONS and set(action) != {"action"}:
        problems.append(f"{prefix} {kind} must not carry a payload")

    if any(value is None for value in action.values()):
        problems.append(f"{prefix} contains a null value")

    percent = action.get("discountPercent")
    amount = action.get("discountAmount")
    if percent is not None and amount is not None:
        problems.append(f"{prefix} both item discount kinds set")
    if percent is not None and not (0 <= percent <= 100):
        problems.append(f"{prefix} discountPercent out of range: {percent}")

    inv_percent = action.get("invoiceDiscountPercent")
    inv_amount = action.get("invoiceDiscountAmount")
    if inv_percent is not None and inv_amount is not None:
        problems.append(f"{prefix} both invoice discount kinds set")
    if inv_percent is not None and not (0 <= inv_percent <= 100):
        problems.append(f"{prefix} invoiceDiscountPercent out of range: {inv_percent}")

    if kind == "SET_ITEM_DISCOUNT" and percent is None and amount is None:
        problems.append(f"{prefix} SET_ITEM_DISCOUNT needs percent or amount")
    if kind == "SET_INVOICE_DISCOUNT" and inv_percent is None and inv_amount is None:
        problems.append(f"{prefix} SET_INVOICE_DISCOUNT needs percent or amount")

    date = action.get("invoiceDate")
    if date is not None and (not isinstance(date, str) or not date.strip()):
        problems.append(f"{prefix} invoiceDate is empty")
    if isinstance(date, str):
        abbrevs = {
            abbrev.lower()
            for names in MONTH_ABBREVIATIONS.values()
            for abbrev in names
        }
        for token in re.findall(r"[A-Za-z]+", date):
            if token.lower() in abbrevs:
                problems.append(
                    f"{prefix} invoiceDate uses abbreviated month {token!r}; "
                    f"expected full name (e.g. {canonicalize_invoice_date(date)!r})"
                )
                break

    return problems


def check_row(row: Dict[str, Any], index: int, source: str) -> List[str]:
    where = f"{source}:{index}"
    problems: List[str] = []

    for key in ("lastModified", "userInput", "agentOutput"):
        if key not in row:
            problems.append(f"{where} missing key {key}")
    if problems:
        return problems

    output = row["agentOutput"]
    if not isinstance(output, list) or not output:
        problems.append(f"{where} agentOutput must be a non-empty array")
        return problems

    if not isinstance(row["userInput"], str) or not row["userInput"].strip():
        problems.append(f"{where} empty userInput")

    last = row["lastModified"]
    if last is not None and not isinstance(last, list):
        problems.append(f"{where} lastModified must be an array or null")

    tags = row.get("meta", {}).get("tags", [])
    task = row.get("meta", {}).get("task", "invoice")
    if task not in TASK_ACTIONS:
        problems.append(f"{where} unknown task {task!r}")
    if "combo" in tags and len(output) < 2:
        problems.append(f"{where} combo row has fewer than 2 actions")

    kinds = [action.get("action") for action in output]
    if sum(1 for kind in kinds if kind in BARE_ACTIONS) > 1:
        problems.append(f"{where} more than one control action")
    if any(kind in BARE_ACTIONS for kind in kinds) and len(output) != 1:
        problems.append(f"{where} control action mixed with a payload")

    inherited = None
    if task == "invoice":
        inherited = remembered_item_name(last if isinstance(last, list) else None)

    for action_index, action in enumerate(output):
        if not isinstance(action, dict):
            problems.append(f"{where} action[{action_index}] is not an object")
            continue
        problems.extend(check_action(action, where, action_index, task=task))

        name = action.get("name")
        if name:
            audible = _name_is_audible(name, row["userInput"])
            if not audible and name != inherited:
                problems.append(
                    f"{where} action[{action_index}] item {name!r} is neither "
                    f"in the transcript nor in context (context item: {inherited!r})"
                )

        updated = action.get("updatedItemName")
        if updated and not (
            _name_is_audible(updated, row["userInput"]) or updated == inherited
        ):
            # Rename targets are spoken as the new name, so they should be audible.
            if not _name_is_audible(updated, row["userInput"]):
                problems.append(
                    f"{where} action[{action_index}] updatedItemName {updated!r} "
                    "is not in the transcript"
                )

    return problems


def coverage(rows: List[Dict[str, Any]]) -> None:
    actions = Counter()
    tags = Counter()
    tasks = Counter()
    date_shapes = Counter()
    context = Counter()
    lengths = Counter()

    for row in rows:
        output = row["agentOutput"]
        lengths[len(output)] += 1
        tasks[row.get("meta", {}).get("task", "invoice")] += 1
        for action in output:
            actions[action.get("action")] += 1
            date = action.get("invoiceDate")
            if date:
                if re.fullmatch(r"\d{1,2}(st|nd|rd|th)", date):
                    date_shapes["bare day"] += 1
                elif re.search(r"\d{2,4}$", date):
                    date_shapes["day month year"] += 1
                elif re.search(r"[A-Za-z]", date) and re.search(r"\d", date):
                    date_shapes["day month"] += 1
                else:
                    date_shapes["relative"] += 1

        for tag in row.get("meta", {}).get("tags", []):
            tags[tag] += 1

        context["with context" if row["lastModified"] else "cold start"] += 1

    print(f"\nrows: {len(rows)}")
    print("\ntasks")
    for key, count in tasks.most_common():
        print(f"  {key:<34} {count:>5}  {count / len(rows):>6.1%}")

    print("\naction coverage")
    for key, count in actions.most_common():
        print(f"  {str(key):<34} {count:>5}  {count / len(rows):>6.1%}")

    print("\nactions per row")
    for length, count in sorted(lengths.items()):
        print(f"  {length:<34} {count:>5}  {count / len(rows):>6.1%}")

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
        seen[
            (
                row.get("meta", {}).get("task", "invoice"),
                json.dumps(row["lastModified"], sort_keys=True),
                row["userInput"],
            )
        ] += 1
    duplicates = sum(count - 1 for count in seen.values() if count > 1)
    if duplicates:
        problems.append(f"{duplicates} duplicate (task, lastModified, userInput) pairs")

    if args.holdout:
        with open(args.holdout, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = (
                    row.get("meta", {}).get("task", "invoice"),
                    json.dumps(row["lastModified"], sort_keys=True),
                    row["userInput"],
                )
                if key in seen:
                    problems.append(
                        f"holdout row leaked into training: {row['userInput']!r}"
                    )

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
