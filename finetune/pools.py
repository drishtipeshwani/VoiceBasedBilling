"""Vocabulary and surface-form renderers for the invoice command dataset.

Everything here answers one question: given a value the target JSON must carry,
what are all the ways an Indian shopkeeper might say it out loud, and what does
the speech recogniser hand us afterwards.
"""

from __future__ import annotations

import random
import re
from typing import List, Optional, Tuple

# --------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------

KIRANA_ITEMS = [
    "rice",
    "basmati rice",
    "atta",
    "wheat flour",
    "sugar",
    "toor dal",
    "moong dal",
    "chana dal",
    "refined oil",
    "mustard oil",
    "milk packets",
    "curd",
    "paneer",
    "biscuits",
    "parle g",
    "tea powder",
    "coffee powder",
    "salt",
    "jaggery",
    "besan",
    "poha",
    "maggi packets",
    "bread",
    "eggs",
    "onions",
    "potatoes",
    "tomatoes",
]

STATIONERY_ITEMS = [
    "pens",
    "pencils",
    "registers",
    "notebooks",
    "a4 sheets",
    "file covers",
    "markers",
    "staplers",
    "glue sticks",
    "chart paper",
    "erasers",
    "sketch pens",
]

ELECTRONICS_ITEMS = [
    "speaker",
    "bluetooth speaker",
    "earphones",
    "headphones",
    "charger",
    "fast charger",
    "mobile cover",
    "screen guard",
    "extension board",
    "led bulb",
    "table fan",
    "power bank",
    "usb cable",
    "microphone",
    "keyboard",
    "mouse",
]

HARDWARE_ITEMS = [
    "cement bags",
    "steel rods",
    "pvc pipes",
    "paint buckets",
    "nails",
    "screws",
    "door handles",
    "hinges",
    "tiles",
    "plywood sheets",
    "wire bundles",
    "switches",
]

TEXTILE_ITEMS = [
    "saree",
    "cotton saree",
    "kurta",
    "kurti",
    "dupatta",
    "shirt",
    "trousers",
    "bedsheet",
    "towels",
    "blanket",
    "school uniform",
    "socks",
]

ITEMS: List[str] = (
    KIRANA_ITEMS
    + STATIONERY_ITEMS
    + ELECTRONICS_ITEMS
    + HARDWARE_ITEMS
    + TEXTILE_ITEMS
)

# --------------------------------------------------------------------------
# Model and part codes
#
# In electronics and hardware the spoken identifier is usually the model, not
# the product: "add SL-253", "the AD-212 is 1200". The code is the item name,
# so it has to survive the trip through the recogniser, which renders it as
# "sl 253", "sl253" or "es el 253" depending on how it was said.
# --------------------------------------------------------------------------

MODEL_CODE_PREFIXES = [
    "AD", "SL", "SM", "MX", "BX", "CT", "GT", "HD", "JK", "KP",
    "LN", "NR", "PT", "QS", "RX", "TZ", "VN", "WD", "XL", "ZR",
]

# Built once with a private generator so the pool is fixed across runs and
# independent of the seed the dataset is generated with.
_code_rng = random.Random(20260726)
MODEL_CODES: List[str] = sorted(
    {
        f"{_code_rng.choice(MODEL_CODE_PREFIXES)}-"
        f"{_code_rng.randint(10, 9999)}"
        for _ in range(90)
    }
)

# Bases that plausibly carry a model number, so "speaker SL-253" reads right
# but "toor dal SL-253" never appears.
_CODED_BASES = ELECTRONICS_ITEMS + HARDWARE_ITEMS

CODED_ITEMS: List[str] = sorted(
    {
        f"{_code_rng.choice(_CODED_BASES)} {_code_rng.choice(MODEL_CODES)}"
        for _ in range(70)
    }
)

CODE_PATTERN = re.compile(r"\b([A-Z]{2})-(\d{2,4})\b")

# Spelled-out prefix letters, the way a shopkeeper reads a code aloud.
_LETTER_SOUNDS = {
    "A": "ay", "B": "bee", "C": "see", "D": "dee", "E": "ee", "F": "eff",
    "G": "jee", "H": "aitch", "I": "eye", "J": "jay", "K": "kay", "L": "el",
    "M": "em", "N": "en", "O": "oh", "P": "pee", "Q": "queue", "R": "aar",
    "S": "ess", "T": "tee", "U": "you", "V": "vee", "W": "double you",
    "X": "ex", "Y": "why", "Z": "zed",
}


def _render_code(prefix: str, digits: str, rng: random.Random) -> str:
    """One spoken rendering of a code. The digits always stay digits: a
    recogniser that heard the number will write it as one."""
    forms = [
        f"{prefix}-{digits}",
        f"{prefix} {digits}",
        f"{prefix.lower()} {digits}",
        f"{prefix.lower()}{digits}",
        f"{' '.join(prefix.lower())} {digits}",
        f"{prefix.lower()} dash {digits}",
        f"{' '.join(_LETTER_SOUNDS[c] for c in prefix)} {digits}",
        f"model {prefix} {digits}",
        f"model number {prefix.lower()} {digits}",
        f"{prefix.lower()} model {digits}",
    ]
    return rng.choice(forms)


def render_item(name: str, rng: random.Random) -> str:
    """The spoken form of an item name. Word names pass through untouched;
    model codes get one of their many possible transcriptions."""
    return CODE_PATTERN.sub(
        lambda match: _render_code(match.group(1), match.group(2), rng), name
    )


def pick_item(rng: random.Random) -> str:
    """An item name, occasionally identified by model code instead of words."""
    roll = rng.random()
    if roll < 0.85:
        return rng.choice(ITEMS)
    if roll < 0.94:
        return rng.choice(CODED_ITEMS)
    return rng.choice(MODEL_CODES)

# Plausible renames: the speaker corrects or refines the name they first gave.
RENAME_TARGETS = {
    "speaker": ["bluetooth speaker", "jbl speaker", "party speaker"],
    "charger": ["fast charger", "type c charger", "mobile charger"],
    "rice": ["basmati rice", "sona masoori rice"],
    "saree": ["cotton saree", "silk saree"],
    "pens": ["blue pens", "gel pens"],
    "notebooks": ["long notebooks", "ruled notebooks"],
    "earphones": ["wired earphones", "bluetooth earphones"],
    "tiles": ["floor tiles", "wall tiles"],
    "kurta": ["cotton kurta", "printed kurta"],
    "biscuits": ["glucose biscuits", "cream biscuits"],
}

GENERIC_RENAME_PREFIXES = [
    "premium",
    "local",
    "imported",
    "small",
    "large",
    "branded",
]

# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

COMPANY_NAMES = [
    "DHA Enterprises",
    "Sri Balaji Traders",
    "Sharma and Sons",
    "Kumar Kirana Store",
    "Raj Electronics",
    "New Bharat Agencies",
    "Annapurna Stores",
    "Gupta Hardware",
    "Krishna Textiles",
    "Modern Stationery Mart",
    "Venkateshwara Traders",
    "Al Noor Trading Company",
    "Singh Brothers",
    "Laxmi General Store",
    "Sai Ram Distributors",
    "Patel Agro Agencies",
    "Bombay Cloth House",
    "Jain Marketing",
    "Deccan Suppliers",
    "Ganesh Auto Parts",
    "Nandini Dairy Products",
    "Hind Paper Mart",
    "Royal Furniture House",
    "Vishnu Timber Depot",
]

CUSTOMER_NAMES = [
    "Rahul",
    "Prakash",
    "Meena Devi",
    "Venkatesh",
    "Fatima",
    "Iqbal",
    "Lakshmi",
    "Aditya",
    "Sunita",
    "Ramesh",
    "Kavita",
    "Arjun",
    "Divya",
    "Manoj Kumar",
    "Farhan",
    "Anita Sharma",
    "Suresh Babu",
    "Priya",
    "Harpreet",
    "Zoya",
    "Ravi Shankar",
    "Nisha",
    "Balaji",
    "Imran",
    "Deepak Verma",
    "Shalini",
    "Gopal",
    "Ayesha",
    "Raj Enterprises",
    "Mahesh Traders",
]

# --------------------------------------------------------------------------
# Numbers
# --------------------------------------------------------------------------

_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]

_TENS = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]

_ORDINALS = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
    13: "thirteenth",
    14: "fourteenth",
    15: "fifteenth",
    16: "sixteenth",
    17: "seventeenth",
    18: "eighteenth",
    19: "nineteenth",
    20: "twentieth",
    30: "thirtieth",
}


def number_to_words(value: int) -> str:
    """English words for 0..9,99,999, the range a bill realistically uses."""
    if value < 20:
        return _ONES[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return _TENS[tens] if ones == 0 else f"{_TENS[tens]} {_ONES[ones]}"
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        head = f"{_ONES[hundreds]} hundred"
        return head if rest == 0 else f"{head} {number_to_words(rest)}"
    if value < 100000:
        thousands, rest = divmod(value, 1000)
        head = f"{number_to_words(thousands)} thousand"
        return head if rest == 0 else f"{head} {number_to_words(rest)}"
    lakhs, rest = divmod(value, 100000)
    head = f"{number_to_words(lakhs)} lakh"
    return head if rest == 0 else f"{head} {number_to_words(rest)}"


def ordinal_words(day: int) -> str:
    if day in _ORDINALS:
        return _ORDINALS[day]
    tens, ones = divmod(day, 10)
    return f"{_TENS[tens]} {_ORDINALS[ones]}"


def ordinal_digits(day: int) -> str:
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }".replace(" ", "")


def spoken_number_forms(value: int) -> List[str]:
    """Every way a speaker might utter this number, digits included."""
    forms = [str(value), number_to_words(value)]

    # "twelve hundred" for 1200, the default way Indians say four-digit prices.
    if 1000 <= value <= 9900 and value % 100 == 0:
        forms.append(f"{number_to_words(value // 100)} hundred")

    # "two fifty" for 250, extremely common in shops.
    if 100 <= value <= 999 and value % 100 != 0 and value % 10 == 0:
        hundreds, rest = divmod(value, 100)
        forms.append(f"{_ONES[hundreds]} {number_to_words(rest)}")

    if value == 1500:
        forms.append("one and a half thousand")
    if value == 2500:
        forms.append("two and a half thousand")
    if value % 100000 == 0 and value >= 100000:
        forms.append(f"{number_to_words(value // 100000)} lakh")

    return forms


def render_number(value: int, rng: random.Random) -> str:
    return rng.choice(spoken_number_forms(value))


PRICE_VALUES = [
    5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45, 50, 60, 65, 70, 75, 80, 90,
    99, 100, 110, 120, 125, 140, 150, 160, 175, 180, 199, 200, 220, 240, 250,
    275, 299, 300, 350, 375, 400, 450, 499, 500, 550, 600, 650, 700, 750, 800,
    850, 900, 950, 999, 1000, 1100, 1200, 1250, 1500, 1800, 2000, 2200, 2500,
    3000, 3500, 4000, 4500, 5000, 6000, 7500, 10000, 12000, 15000, 25000,
]

QUANTITY_VALUES = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 24, 25, 30, 36, 40, 45, 50,
    60, 75, 100, 120, 144, 200, 250, 500,
]

DISCOUNT_PERCENT_VALUES = [2, 3, 5, 7, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 50]

DISCOUNT_AMOUNT_VALUES = [
    5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 100, 120, 150, 200, 250, 300,
    400, 500, 750, 1000,
]

# --------------------------------------------------------------------------
# Currency phrasing
# --------------------------------------------------------------------------

_PRICE_PATTERNS = [
    "{n}",
    "{n} rupees",
    "rupees {n}",
    "rs {n}",
    "{n} rupees each",
    "{n} per piece",
    "{n} rupees per piece",
    "{n} each",
    "{n} per kg",
    "{n} rupees only",
    "at {n}",
    "at {n} rupees",
]


def render_price(value: int, rng: random.Random) -> str:
    return rng.choice(_PRICE_PATTERNS).format(n=render_number(value, rng))


_QUANTITY_PATTERNS = [
    "{n}",
    "{n} pieces",
    "{n} nos",
    "{n} packets",
    "{n} kg",
    "{n} boxes",
    "{n} units",
    "{n} pieces only",
    "{n} dozen",
]


def render_quantity(value: int, rng: random.Random) -> str:
    pattern = rng.choice(_QUANTITY_PATTERNS)
    # "dozen" would change the number's meaning, so keep it for bare counts.
    if pattern == "{n} dozen":
        pattern = "{n} pieces"
    return pattern.format(n=render_number(value, rng))


# --------------------------------------------------------------------------
# Discount phrasing
# --------------------------------------------------------------------------

_PERCENT_PATTERNS = [
    "{n} percent",
    "{n}%",
    "{n} percent discount",
    "{n} percent off",
    "{n} percentage",
    "{n} percent less",
]


def render_discount_percent(value: int, rng: random.Random) -> str:
    n = str(value) if rng.random() < 0.6 else number_to_words(value)
    return rng.choice(_PERCENT_PATTERNS).format(n=n)


_AMOUNT_PATTERNS = [
    "{n} rupees",
    "rupees {n}",
    "rs {n}",
    "{n} rupees off",
    "flat {n} rupees",
    "{n} rupees discount",
]


def render_discount_amount(value: int, rng: random.Random) -> str:
    return rng.choice(_AMOUNT_PATTERNS).format(n=render_number(value, rng))


# --------------------------------------------------------------------------
# Dates
#
# Spoken forms may use abbreviations ("Jun", "Aug 3rd"). The target always
# uses a full month name with a digit ordinal day: "25th June", "14th".
# Year is left as spoken when present; the app resolves to DD/MM/YYYY.
# --------------------------------------------------------------------------

MONTHS_FULL = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

MONTH_ABBREVIATIONS = {
    "January": ["Jan"],
    "February": ["Feb"],
    "March": ["Mar"],
    "April": ["Apr"],
    "June": ["Jun"],
    "July": ["Jul"],
    "August": ["Aug"],
    "September": ["Sept", "Sep"],
    "October": ["Oct"],
    "November": ["Nov"],
    "December": ["Dec"],
}

MONTH_ALIAS_TO_FULL = {
    abbrev.lower(): full
    for full, abbrevs in MONTH_ABBREVIATIONS.items()
    for abbrev in abbrevs
}
MONTH_ALIAS_TO_FULL.update({name.lower(): name for name in MONTHS_FULL})

RELATIVE_DATES = ["today", "yesterday", "tomorrow"]


def canonicalize_invoice_date(value: Optional[str]) -> Optional[str]:
    """Expand any month token to its full English name; leave other text as-is."""
    if value is None:
        return None

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        full = MONTH_ALIAS_TO_FULL.get(word.lower())
        return full if full is not None else word

    return re.sub(r"[A-Za-z]+", repl, value)


def _spoken_day(day: int, rng: random.Random) -> str:
    """How the day is uttered: '25th', '25', or 'twenty fifth'."""
    roll = rng.random()
    if roll < 0.55:
        return ordinal_digits(day)
    if roll < 0.8:
        return str(day)
    return ordinal_words(day)


def render_date(rng: random.Random) -> Tuple[str, str]:
    """Return (spoken phrase, target string).

    Spoken may use abbreviations; target always uses a full month name.
    """
    roll = rng.random()
    day = rng.randint(1, 28) if rng.random() < 0.85 else rng.randint(29, 31)

    if roll < 0.55:
        month = rng.choice(MONTHS_FULL)
        spoken_month = month
        if rng.random() < 0.25 and month in MONTH_ABBREVIATIONS:
            spoken_month = rng.choice(MONTH_ABBREVIATIONS[month])

        spoken_day = _spoken_day(day, rng)
        order = rng.random()
        if order < 0.6:
            spoken = f"{spoken_day} {spoken_month}"
        elif order < 0.8:
            spoken = f"{spoken_day} of {spoken_month}"
        else:
            spoken = f"{spoken_month} {spoken_day}"
        return spoken, f"{ordinal_digits(day)} {month}"

    if roll < 0.85:
        spoken_day = _spoken_day(day, rng)
        return spoken_day, ordinal_digits(day)

    if roll < 0.97:
        month = rng.choice(MONTHS_FULL)
        spoken_month = month
        if rng.random() < 0.3 and month in MONTH_ABBREVIATIONS:
            spoken_month = rng.choice(MONTH_ABBREVIATIONS[month])
        year = rng.choice(["2025", "2026", "25", "26"])
        spoken_day = _spoken_day(day, rng)
        spoken = f"{spoken_day} {spoken_month} {year}"
        return spoken, f"{ordinal_digits(day)} {month} {year}"

    relative = rng.choice(RELATIVE_DATES)
    return relative, relative


# --------------------------------------------------------------------------
# Non-command speech
# --------------------------------------------------------------------------

UNKNOWN_UTTERANCES = [
    "what time is it",
    "how is the weather today",
    "what is the score of the match",
    "India needs forty runs in three overs",
    "did you watch the news yesterday",
    "call me back in ten minutes",
    "hello hello can you hear me",
    "have you eaten your lunch yet",
    "where did you keep the phone",
    "please subscribe to our channel",
    "the train is running late again",
    "switch on the fan please",
    "what time will you come",
    "my head is paining since morning",
    "tell mummy I will come by eight",
    "traffic is very bad near the signal",
    "what is your good name",
    "load shedding again in our area",
    "send me the photo on whatsapp",
    "tomorrow is a holiday right",
    "who is speaking please",
    "the wifi is not working properly",
    "put the ac on twenty four",
    "did the courier boy come",
    "I am going to the temple in the evening",
    "how much does this cost",
    "sorry wrong number",
    "he is not picking up the phone",
    "book two tickets for saturday",
    "the milk has gone bad",
    "ok fine I will hang up now",
    "battery is about to die",
    "let me check and tell you",
    "how much time will it take to reach",
    "tell him to come tomorrow morning",
    "the shop is closed on sunday",
    "it is very hot today",
    "did you have your lunch",
    "the light went off suddenly",
    "give me one cutting chai",
]

INCOMPLETE_UTTERANCES = [
    "add uh",
    "add item",
    "make the price",
    "the price of",
    "discount of",
    "give discount",
    "customer uh",
    "customer name is",
    "company name",
    "make company",
    "bill date",
    "date should be",
    "the date is",
    "quantity of",
    "set quantity",
    "change the",
    "make it",
    "remove the",
    "rename the",
    "add item with price",
    "put the",
    "total discount",
    "on the whole bill",
    "and then",
    "one more",
    "wait wait",
    "no no not that",
    "uh",
    "hmm",
    "so the",
    "please make",
    "I want to",
    "can you",
    "let me see the",
    "actually the",
]


def rename_target(item_name: str, rng: random.Random) -> str:
    match = CODE_PATTERN.search(item_name)
    if match:
        # Correcting a misheard digit is the usual reason a code gets renamed:
        # "no it is SL-254".
        prefix, digits = match.group(1), match.group(2)
        corrected = digits
        while corrected == digits:
            corrected = str(rng.randint(10, 10 ** len(digits) - 1)).zfill(len(digits))
        return CODE_PATTERN.sub(f"{prefix}-{corrected}", item_name, count=1)

    options = RENAME_TARGETS.get(item_name)
    if options:
        return rng.choice(options)
    return f"{rng.choice(GENERIC_RENAME_PREFIXES)} {item_name}"


def pick_other_item(item_name: Optional[str], rng: random.Random) -> str:
    while True:
        candidate = pick_item(rng)
        if candidate != item_name:
            return candidate
