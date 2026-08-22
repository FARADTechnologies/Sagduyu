from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

ZERO_WIDTH_PATTERN = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
SPACED_RUN_PATTERN = re.compile(
    r"(?<!\w)(?:[a-zçğıöşü0-9@$][\s._*·-]+){2,}[a-zçğıöşü0-9@$](?!\w)",
    flags=re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
REPEATED_PATTERN = re.compile(r"(.)\1{2,}")

TURKISH_CASE_MAP = str.maketrans({"I": "ı", "İ": "i"})
TURKISH_ASCII_MAP = str.maketrans({"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c"})
CONFUSABLE_MAP = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "х": "x",
        "і": "i",
        "Α": "a",
        "Β": "b",
        "Ε": "e",
        "Ι": "i",
        "Κ": "k",
        "Μ": "m",
        "Ν": "n",
        "Ο": "o",
        "Ρ": "p",
        "Τ": "t",
        "Χ": "x",
    }
)
LEET_MAP: Mapping[str, str] = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
}


class NormalizationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    normalized_text: str
    transformations: tuple[str, ...]
    original_length: int = Field(ge=0)
    normalized_length: int = Field(ge=0)


class TurkishTextNormalizer:
    """Deterministic canonicalization for common Turkish masking patterns."""

    version = "0.1.0"

    def analyze(self, text: str) -> NormalizationResult:
        transformations: list[str] = []
        value = unicodedata.normalize("NFKC", text)
        transformations.extend(_changed(text, value, "unicode_nfkc"))

        without_invisible = ZERO_WIDTH_PATTERN.sub("", value)
        transformations.extend(_changed(value, without_invisible, "invisible_characters"))
        value = without_invisible.translate(TURKISH_CASE_MAP).lower()

        without_confusables = value.translate(CONFUSABLE_MAP)
        transformations.extend(_changed(value, without_confusables, "unicode_confusables"))
        value = without_confusables

        joined = SPACED_RUN_PATTERN.sub(_join_spaced_run, value)
        transformations.extend(_changed(value, joined, "separated_letters"))
        value = joined

        decomposed = unicodedata.normalize("NFKD", value.translate(TURKISH_ASCII_MAP))
        without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
        transformations.extend(_changed(value, without_marks, "turkish_diacritics"))

        tokens: list[str] = []
        leet_changed = False
        repetition_changed = False
        for match in TOKEN_PATTERN.finditer(without_marks):
            token = match.group()
            if any(char.isalpha() for char in token):
                translated = "".join(LEET_MAP.get(char, char) for char in token)
                leet_changed = leet_changed or translated != token
                token = translated
            collapsed = REPEATED_PATTERN.sub(r"\1", token)
            repetition_changed = repetition_changed or collapsed != token
            tokens.append(collapsed)

        if leet_changed:
            transformations.append("leetspeak")
        if repetition_changed:
            transformations.append("character_repetition")
        normalized = " ".join(tokens)
        if normalized != without_marks.strip() and "punctuation_spacing" not in transformations:
            transformations.append("punctuation_spacing")

        return NormalizationResult(
            normalized_text=normalized,
            transformations=tuple(dict.fromkeys(transformations)),
            original_length=len(text),
            normalized_length=len(normalized),
        )

    def normalize(self, text: str) -> str:
        return self.analyze(text).normalized_text


def generate_masked_variants(term: str) -> dict[str, str]:
    canonical = TurkishTextNormalizer().normalize(term).replace(" ", "")
    if not canonical:
        raise ValueError("term must contain at least one letter or number")
    reverse_leet = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"})
    middle = len(canonical) // 2
    repeated = canonical[:middle] + (canonical[middle] * 4) + canonical[middle + 1 :]
    return {
        "plain": canonical,
        "spaced": " ".join(canonical),
        "dotted": ".".join(canonical),
        "starred": "*".join(canonical),
        "zero_width": "\u200b".join(canonical),
        "leetspeak": canonical.translate(reverse_leet),
        "repeated": repeated,
    }


def _join_spaced_run(match: re.Match[str]) -> str:
    return re.sub(r"[\s._*·-]+", "", match.group())


def _changed(before: str, after: str, label: str) -> tuple[str, ...]:
    return (label,) if before != after else ()
