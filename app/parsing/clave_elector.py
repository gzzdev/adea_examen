import re
from collections import Counter


PATTERN = re.compile(r"[A-Z]{6}\d{8}[HM]\d{3}")
TO_DIGIT = {"O": "0", "I": "1", "L": "1", "S": "5", "B": "8"}
TO_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B"}


def fix_by_position(value: str) -> str:
    chars = list(value)
    for index, char in enumerate(chars):
        if index in {*range(6, 14), *range(15, 18)}:
            chars[index] = TO_DIGIT.get(char, char)
        elif index in {*range(6), 14}:
            chars[index] = TO_LETTER.get(char, char)
    return "".join(chars)


def extract(lines: list[str]) -> str | None:
    candidates = Counter()
    for line in lines:
        compact = re.sub(r"[^A-Z0-9]", "", line.upper())
        for start in range(len(compact) - 17):
            candidate = fix_by_position(compact[start:start + 18])
            if PATTERN.fullmatch(candidate):
                candidates[candidate] += 1
    return candidates.most_common(1)[0][0] if candidates else None
