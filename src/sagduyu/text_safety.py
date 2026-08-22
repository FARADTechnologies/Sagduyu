from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field

from sagduyu.text_normalization import TurkishTextNormalizer


class CourtesyLevel(StrEnum):
    CLEAR = "clear"
    REVIEW = "review"
    HIGH_RISK = "high_risk"


class CourtesyCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5_000)


class CourtesyMatch(BaseModel):
    canonical_form: str
    category: str
    contribution: float = Field(ge=0.0, le=100.0)


class CourtesyAssessment(BaseModel):
    normalized_text: str
    transformations: tuple[str, ...]
    risk_score: float = Field(ge=0.0, le=100.0)
    level: CourtesyLevel
    should_warn: bool
    warning: str | None
    matches: list[CourtesyMatch]
    user_may_continue: bool = True
    method: str = "transparent_demo_baseline_v1"
    disclaimer: str = (
        "Bu sonuç açıklanabilir bir demo tabanıdır; bağlama duyarlı model başarımı veya "
        "otomatik yaptırım kararı değildir."
    )


@dataclass(frozen=True, slots=True)
class _LexiconEntry:
    canonical_form: str
    category: str
    weight: float


DEMO_LEXICON = (
    _LexiconEntry("aptal", "kişiye yönelik aşağılama", 0.58),
    _LexiconEntry("salak", "kişiye yönelik aşağılama", 0.58),
    _LexiconEntry("gerizekali", "ağır aşağılama", 0.82),
    _LexiconEntry("serefsiz", "ağır aşağılama", 0.82),
)


class CourtesyChecker:
    """Transparent non-blocking baseline for the courtesy interaction."""

    version = "0.1.0"

    def __init__(self, *, normalizer: TurkishTextNormalizer | None = None) -> None:
        self.normalizer = normalizer or TurkishTextNormalizer()

    def assess(self, text: str) -> CourtesyAssessment:
        normalization = self.normalizer.analyze(text)
        matches = [
            CourtesyMatch(
                canonical_form=entry.canonical_form,
                category=entry.category,
                contribution=round(entry.weight * 100, 2),
            )
            for entry in DEMO_LEXICON
            if _contains_term(normalization.normalized_text, entry.canonical_form)
        ]
        combined_risk = 1.0
        for match in matches:
            combined_risk *= 1.0 - (match.contribution / 100)
        risk_score = round((1.0 - combined_risk) * 100, 2) if matches else 0.0
        level = (
            CourtesyLevel.HIGH_RISK
            if risk_score >= 80.0
            else CourtesyLevel.REVIEW
            if risk_score >= 50.0
            else CourtesyLevel.CLEAR
        )
        should_warn = level is not CourtesyLevel.CLEAR
        warning = (
            "Bu ifade incitici algılanabilir. Paylaşmadan önce yeniden düzenlemek ister misiniz?"
            if should_warn
            else None
        )
        return CourtesyAssessment(
            normalized_text=normalization.normalized_text,
            transformations=normalization.transformations,
            risk_score=risk_score,
            level=level,
            should_warn=should_warn,
            warning=warning,
            matches=matches,
        )


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?:^| ){re.escape(term)}(?:$| )", text) is not None
