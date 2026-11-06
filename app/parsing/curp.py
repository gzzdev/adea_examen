import re
from collections import Counter
from datetime import date

from app.parsing.catalogs import CURP_CHECK_ALPHABET, CURP_ENTITIES


PATTERN = re.compile(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d")
TO_DIGIT = {"O": "0", "I": "1", "L": "1", "S": "5", "B": "8"}
TO_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B"}


def fix_by_position(value: str) -> str:
    chars = list(value)
    for index, char in enumerate(chars):
        if index in {*range(4, 10), 17}:
            chars[index] = TO_DIGIT.get(char, char)
        elif index in {*range(4), 10, *range(11, 16)}:
            chars[index] = TO_LETTER.get(char, char)
    return "".join(chars)


def is_valid(value: str) -> bool:
    if not PATTERN.fullmatch(value) or value[11:13] not in CURP_ENTITIES:
        return False
    try:
        year = int(value[4:6])
        date(2000 + year if value[16].isalpha() else 1900 + year,
             int(value[6:8]), int(value[8:10]))
    except ValueError:
        return False
    checksum = sum(CURP_CHECK_ALPHABET.index(char) * (18 - index)
                   for index, char in enumerate(value[:17]))
    return (10 - checksum % 10) % 10 == int(value[17])


def extract(lines: list[str]) -> str | None:
    candidates = Counter()
    for line in lines:
        compact = re.sub(r"[^A-Z0-9]", "", line.upper())
        for start in range(len(compact) - 17):
            candidate = fix_by_position(compact[start:start + 18])
            if is_valid(candidate):
                candidates[candidate] += 1
    return candidates.most_common(1)[0][0] if candidates else None
