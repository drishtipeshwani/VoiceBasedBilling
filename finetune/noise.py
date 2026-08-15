"""Speech-recogniser noise, applied to the utterance only.

The target JSON is always the correct reading of what the speaker meant, so
these corruptions teach the model to recover intent from a bad transcript
rather than to reproduce the mistake. Every substitution here was either
observed in the app's own logs or is a known Indian English ASR confusion.
"""

from __future__ import annotations

import random
import re
from typing import Dict, List

# Whole-word swaps. The observed "Make company name" -> "Main company name"
# failure lives here, alongside the "as" -> "has" that turned a price command
# into an unparseable one in the logs.
WORD_SWAPS: Dict[str, List[str]] = {
    "make": ["main", "mag", "mike", "made"],
    "add": ["ad", "add the", "at"],
    "as": ["has", "is", "was"],
    "is": ["his", "as"],
    "price": ["prize", "pries", "rice"],
    "customer": ["custom", "customers", "costumer"],
    "company": ["compny", "companies", "comapny"],
    "quantity": ["quality", "quantities", "quantity of"],
    "discount": ["discounts", "the scount", "discount of"],
    "percent": ["per cent", "percentage", "person"],
    "rupees": ["rupee", "rupess", "rs"],
    "item": ["it um", "eyetem"],
    "name": ["nam", "names"],
    "bill": ["build", "bil"],
    "date": ["dates", "data", "det"],
    "remove": ["remo", "remove the", "move"],
    "total": ["totel", "total of"],
    "change": ["chnge", "change the"],
    "invoice": ["in voice", "invoices"],
    "june": ["joon", "jun"],
    "july": ["jully", "jul"],
    "august": ["agust", "aug"],
    "march": ["merch", "mar"],
    "april": ["aprill", "apr"],
    # Number homophones such as four/for are deliberately absent: they change
    # the value the target carries rather than just the wording around it.
    "set": ["sat", "said"],
    "put": ["but", "pot"],
    "each": ["ich"],
    "off": ["of"],
    "of": ["off"],
}

# Fillers a continuous recogniser happily transcribes.
LEADING_FILLERS = [
    "uh",
    "um",
    "so",
    "ok",
    "actually",
    "listen",
    "and",
    "then",
    "right",
    "well",
]

TRAILING_FILLERS = [
    "only",
    "please",
    "ok",
    "hmm",
    "right",
    "yeah",
    "no",
    "also",
]


def _swap_words(text: str, rng: random.Random, probability: float) -> str:
    tokens = text.split(" ")
    out: List[str] = []
    for token in tokens:
        bare = re.sub(r"[^a-z0-9%]", "", token.lower())
        options = WORD_SWAPS.get(bare)
        if options and rng.random() < probability:
            out.append(rng.choice(options))
        else:
            out.append(token)
    return " ".join(out)


def _drop_ordinal_suffix(text: str, rng: random.Random) -> str:
    """'25th June' heard as '25 June'."""
    return re.sub(
        r"\b(\d{1,2})(st|nd|rd|th)\b",
        lambda m: m.group(1) if rng.random() < 0.7 else m.group(0),
        text,
    )


def _drop_article(text: str, rng: random.Random) -> str:
    tokens = text.split(" ")
    kept = [
        token
        for token in tokens
        if not (token.lower() in {"the", "a", "an"} and rng.random() < 0.6)
    ]
    return " ".join(kept) if kept else text


_NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
    "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",
    "thousand", "lakh", "half",
}


def _double_a_word(text: str, rng: random.Random) -> str:
    tokens = text.split(" ")
    # Never double a number, digits or words. "twenty twenty five" reads as a
    # different value, which would make the target wrong rather than noisy.
    candidates = [
        i
        for i, token in enumerate(tokens)
        if not re.search(r"\d", token)
        and re.sub(r"[^a-z]", "", token.lower()) not in _NUMBER_WORDS
    ]
    if len(tokens) < 2 or not candidates:
        return text
    index = rng.choice(candidates)
    tokens.insert(index, tokens[index])
    return " ".join(tokens)


def _add_filler(text: str, rng: random.Random) -> str:
    if rng.random() < 0.6:
        return f"{rng.choice(LEADING_FILLERS)} {text}"
    return f"{text} {rng.choice(TRAILING_FILLERS)}"


def _recapitalise(text: str, rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.4:
        return text.lower()
    if roll < 0.7 and text:
        return text[0].upper() + text[1:]
    return text


def apply_noise(
    text: str,
    rng: random.Random,
    intensity: float = 0.5,
    protect_ordinals: bool = False,
) -> str:
    """Corrupt a clean utterance the way the recogniser would.

    `intensity` is the chance that any single corruption fires, so a row can
    come through untouched, lightly mangled, or badly mangled.

    `protect_ordinals` keeps the "th" on utterances such as "make it 14th",
    where the suffix is the only thing separating a date from a quantity.
    Dropping it there would make the target wrong rather than noisy.
    """
    noisy = text

    if rng.random() < intensity:
        noisy = _swap_words(noisy, rng, probability=0.35)
    if not protect_ordinals and rng.random() < intensity * 0.5:
        noisy = _drop_ordinal_suffix(noisy, rng)
    if rng.random() < intensity * 0.5:
        noisy = _drop_article(noisy, rng)
    if rng.random() < intensity * 0.25:
        noisy = _double_a_word(noisy, rng)
    if rng.random() < intensity * 0.5:
        noisy = _add_filler(noisy, rng)

    noisy = _recapitalise(noisy, rng)
    noisy = re.sub(r"\s+", " ", noisy).strip()
    return noisy
